from __future__ import annotations

from dataclasses import dataclass

from src.parser import ParsedMaterial, PdfVisualPage


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

SECTION_DISPLAY_TITLES = {
    "Overview": "课程概览",
    "Learning Objectives": "学习目标",
    "Key Concepts": "核心知识点",
    "Key Terms": "核心术语",
    "Lecture Highlights": "课件与课堂重点",
    "Professor Emphasis": "教授特别强调",
    "Examples from Lecture": "课堂案例",
    "Possible Exam Focus": "值得复习的重点",
    "Key Takeaways": "复习要点",
}


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


def collect_visual_pages(materials: list[ParsedMaterial]) -> list[PdfVisualPage]:
    """Return the capped parser-selected pages; never render a whole PDF blindly."""
    return [page for item in materials if item.kind == "pdf" for page in item.visual_pages][:4]


def source_registry(materials: list[ParsedMaterial]) -> dict[str, SourceReference]:
    registry: dict[str, SourceReference] = {}
    for kind, label in (("pdf", "课件"), ("txt", "课堂字幕")):
        matching = [item for item in materials if item.kind == kind and (item.text or item.visual_pages)]
        excerpts = [item.text[:900].strip() for item in matching if item.text]
        if matching:
            if not excerpts and kind == "pdf":
                image_pages = [str(page.page_number) for item in matching for page in item.visual_pages]
                excerpts = [f"已导入图片内容的课件页面：第 {'、'.join(image_pages)} 页。"]
            registry[kind] = SourceReference(
                source_type=kind,
                label=label,
                excerpt="\n\n".join(excerpts),
                note="这里展示的是材料原文片段；当前结果尚未提供精确页码或时间戳。",
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
    return clean or "学习笔记", clean or "学习笔记"


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
                title=SECTION_DISPLAY_TITLES.get(key, display_title),
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
            "结构化课程总结与学习目标",
            "便于复习的核心概念与术语",
            "有材料依据时的教授强调与课堂案例",
            "不夸大、不臆测的复习重点",
        ],
        "quiz": [
            "材料充足时生成 8–12 道英文测验题",
            "每道题独立显示答案与选项解析",
        ],
        "reading": [
            "按课程讲授顺序组织的精读稿",
            "中英对照阅读内容",
            "保留定义、案例与重点表达的上下文",
        ],
    }
    return [item for tool in selected_tools for item in output_map.get(tool, [])]
