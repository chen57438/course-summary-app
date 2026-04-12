from __future__ import annotations

import re
from typing import BinaryIO


def extract_pdf_text(pdf_file: BinaryIO) -> str:
    import fitz

    pdf_bytes = pdf_file.read()
    if not pdf_bytes:
        raise ValueError("上传的 PDF 文件为空。")

    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages: list[str] = []

    for page in document:
        text = page.get_text("text").strip()
        if text:
            pages.append(text)

    combined_text = "\n\n".join(pages).strip()
    if not combined_text:
        raise ValueError("无法从 PDF 中提取到文本，请确认课件不是纯图片扫描版。")

    return combined_text


def extract_pdf_outline(pdf_file: BinaryIO, max_pages: int = 12, max_chars_per_page: int = 1200) -> str:
    import fitz

    pdf_bytes = pdf_file.getvalue() if hasattr(pdf_file, "getvalue") else pdf_file.read()
    if not pdf_bytes:
        raise ValueError("上传的 PDF 文件为空。")

    document = fitz.open(stream=pdf_bytes, filetype="pdf")
    page_summaries: list[str] = []

    for index, page in enumerate(document):
        if index >= max_pages:
            break

        text = page.get_text("text").strip()
        if not text:
            continue

        compact_text = " ".join(text.split())
        clipped_text = compact_text[:max_chars_per_page]
        page_summaries.append(f"第 {index + 1} 页：{clipped_text}")

    outline = "\n".join(page_summaries).strip()
    if not outline:
        raise ValueError("无法从 PDF 中提取到课件骨架，请确认课件不是纯图片扫描版。")

    return outline


def read_txt_file(txt_file: BinaryIO) -> str:
    raw_bytes = txt_file.read()
    if not raw_bytes:
        raise ValueError("上传的 TXT 文件为空。")

    for encoding in ("utf-8", "utf-8-sig", "gb18030", "big5"):
        try:
            content = raw_bytes.decode(encoding).strip()
            if content:
                return content
        except UnicodeDecodeError:
            continue

    raise ValueError("TXT 文件编码无法识别，请保存为 UTF-8 后重试。")


def normalize_study_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def split_transcript_sentences(text: str) -> list[str]:
    normalized = normalize_study_text(text)
    if not normalized:
        return []

    raw_sentences = re.split(r"(?<=[.!?])\s+", normalized)
    sentences: list[str] = []
    previous = ""
    for sentence in raw_sentences:
        clean = sentence.strip(" -")
        if len(clean) < 8:
            continue
        if clean == previous:
            continue
        sentences.append(clean)
        previous = clean
    return sentences


def build_transcript_study_view(
    transcript_text: str,
    max_sentences: int = 180,
) -> tuple[str, str]:
    sentences = split_transcript_sentences(transcript_text)
    if not sentences:
        return "", ""

    low_signal_keywords = (
        "very good morning",
        "thank you",
        "public holiday",
        "presentation",
        "attendance",
        "group formation",
        "marks",
        "peer marking",
        "author declaration",
        "good weekend",
        "lockdown browser",
    )
    study_start_keywords = (
        "last week",
        "course introduction",
        "learning outcome",
        "planning",
        "scheduling",
        "scope",
        "stakeholder",
        "culture",
        "resource",
        "charter",
        "wbs",
        "critical path",
        "international project",
    )
    topic_keywords: list[tuple[str, tuple[str, ...]]] = [
        ("Planning and Scheduling", ("planning", "scheduling", "critical path", "gantt", "network", "estimate")),
        ("Scope and Definition", ("scope", "wbs", "work breakdown", "deliverable", "scope statement", "charter")),
        ("Stakeholder Management", ("stakeholder", "customer", "client", "supplier", "owner")),
        ("Culture and International Context", ("culture", "cultural", "international", "geographical", "country")),
        ("Resource Scheduling", ("resource", "manpower", "material", "supply chain", "labor")),
        ("Assignment and Quiz Notes", ("assignment", "quiz", "slide", "group", "presentation")),
    ]

    selected: list[str] = []
    topical_examples: dict[str, list[str]] = {name: [] for name, _ in topic_keywords}
    started = False
    for sentence in sentences:
        lowered = sentence.lower()
        if not started:
            started = any(keyword in lowered for keyword in study_start_keywords)
            if not started:
                continue
        if any(keyword in lowered for keyword in low_signal_keywords):
            continue

        matched = False
        for topic_name, keywords in topic_keywords:
            if any(keyword in lowered for keyword in keywords):
                if len(topical_examples[topic_name]) < 4:
                    topical_examples[topic_name].append(sentence)
                matched = True
        if matched or len(selected) < max_sentences:
            selected.append(sentence)
        if len(selected) >= max_sentences:
            break

    cleaned_transcript = " ".join(selected).strip()

    section_lines: list[str] = []
    for topic_name, _ in topic_keywords:
        examples = topical_examples[topic_name]
        if not examples:
            continue
        section_lines.append(f"### {topic_name}")
        for example in examples:
            section_lines.append(f"- {example}")

    return cleaned_transcript, "\n".join(section_lines).strip()
