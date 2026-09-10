from __future__ import annotations

from dataclasses import dataclass

from src.parser import ParsedMaterial


SUMMARY_SECTION_ORDER = [
    "Overview",
    "Learning Objectives",
    "Key Concepts",
    "Key Terms",
    "Lecture Highlights",
    "Professor Emphasis",
    "Examples from Lecture",
    "Possible Exam Focus",
    "Key Takeaways",
]


@dataclass(frozen=True)
class SourceReference:
    """A safe, extensible pointer back to uploaded material.

    ``page`` and ``timestamp`` intentionally stay ``None`` until the parsing and
    generation pipeline can return a verified location. The UI must never infer
    either value from model text.
    """

    source_type: str
    label: str
    page: int | None = None
    timestamp: str | None = None
    excerpt: str = ""
    note: str = ""


@dataclass
class ResultSection:
    key: str
    title: str
    markdown: str
    source_labels: list[str]


def combine_materials(materials: list[ParsedMaterial], kind: str) -> str:
    successful = [item for item in materials if item.kind == kind and item.text]
    return "\n\n".join(f"[{item.name}]\n{item.text}" for item in successful).strip()


def source_registry(materials: list[ParsedMaterial]) -> dict[str, SourceReference]:
    registry: dict[str, SourceReference] = {}
    for kind, label in (("pdf", "Slides"), ("txt", "Lecture transcript")):
        excerpts = [item.text[:900].strip() for item in materials if item.kind == kind and item.text]
        if excerpts:
            registry[kind] = SourceReference(
                source_type=kind,
                label=label,
                excerpt="\n\n".join(excerpts),
                note="General source context - precise page or timestamp metadata is not available for this result yet.",
            )
    return registry


def _normalise_section_title(title: str) -> tuple[str, str]:
    clean = title.replace("📌", "").replace("💡", "").replace("🎓", "").replace("📋", "").replace("📝", "").replace("🧩", "").strip()
    lowered = clean.lower()
    aliases = {
        "overview": "Overview",
        "课程概览": "Overview",
        "learning objectives": "Learning Objectives",
        "学习目标": "Learning Objectives",
        "key concepts": "Key Concepts",
        "核心知识点": "Key Concepts",
        "key terms": "Key Terms",
        "专业词汇表": "Key Terms",
        "lecture highlights": "Lecture Highlights",
        "教授的“金句”与强调": "Lecture Highlights",
        "professor's insights": "Lecture Highlights",
        "professor emphasis": "Professor Emphasis",
        "教授特别强调": "Professor Emphasis",
        "教授强调": "Professor Emphasis",
        "examples from lecture": "Examples from Lecture",
        "课堂案例": "Examples from Lecture",
        "lecture examples": "Examples from Lecture",
        "possible exam focus": "Possible Exam Focus",
        "exam focus": "Possible Exam Focus",
        "quiz 备考提示": "Possible Exam Focus",
        "quiz preparation notes": "Possible Exam Focus",
        "可能的考试重点": "Possible Exam Focus",
        "key takeaways": "Key Takeaways",
        "课件与讲稿补充点": "Key Takeaways",
        "slides vs. transcript additions": "Key Takeaways",
    }
    for alias, canonical in aliases.items():
        if alias in lowered or alias in clean:
            return canonical, clean
    return clean or "Study notes", clean or "Study notes"


def _sources_for_section(key: str, sources: dict[str, SourceReference]) -> list[str]:
    available = [value.label for value in sources.values()]
    if key in {"Lecture Highlights", "Professor Emphasis", "Examples from Lecture"} and "txt" in sources:
        return [sources["txt"].label]
    if key == "Key Terms" and "pdf" in sources:
        return [sources["pdf"].label]
    return available


def parse_summary_sections(markdown: str, sources: dict[str, SourceReference]) -> list[ResultSection]:
    """Split real model markdown into UI modules without inventing citations."""
    sections: list[ResultSection] = []
    current_title = "Overview"
    current_lines: list[str] = []

    def flush() -> None:
        nonlocal current_lines, current_title
        body = "\n".join(current_lines).strip()
        if not body:
            return
        key, display_title = _normalise_section_title(current_title)
        sections.append(
            ResultSection(
                key=key,
                title=display_title,
                markdown=body,
                source_labels=_sources_for_section(key, sources),
            )
        )

    for line in markdown.splitlines():
        if line.startswith("## "):
            flush()
            current_title = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)
    flush()

    ordered: list[ResultSection] = []
    for key in SUMMARY_SECTION_ORDER:
        ordered.extend(section for section in sections if section.key == key)
    ordered.extend(section for section in sections if section.key not in SUMMARY_SECTION_ORDER)
    return ordered


def expected_outputs(selected_tools: list[str]) -> list[str]:
    output_map = {
        "summary": [
            "Structured lecture summary and learning objectives",
            "Key concepts and terminology for revision",
            "Professor-emphasized points and lecture examples when the uploaded materials support them",
            "Possible exam focus without unsupported exam claims",
        ],
        "quiz": [
            "8-12 English quiz questions when the material supports that depth",
            "Independent answers and explanations for each option",
        ],
        "reading": [
            "A guided reading draft that follows the material's teaching order",
            "Chinese and English paired for side-by-side reading",
            "Definitions, examples and key expressions kept in context",
        ],
    }
    return [item for tool in selected_tools for item in output_map.get(tool, [])]
