from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import BinaryIO


@dataclass
class PdfVisualPage:
    """A deliberately small set of image-heavy PDF pages for vision analysis."""

    page_number: int
    image_bytes: bytes
    source_name: str = ""


@dataclass
class ParsedMaterial:
    """A parsed upload plus only the metadata the UI can state truthfully."""

    kind: str
    name: str
    text: str = ""
    status: str = "已上传"
    message: str = "等待解析"
    char_count: int = 0
    page_count: int | None = None
    warning: str = ""
    visual_pages: list[PdfVisualPage] = field(default_factory=list)

    @property
    def source_label(self) -> str:
        return "课件" if self.kind == "pdf" else "课堂字幕"


def _read_upload_bytes(upload: BinaryIO) -> bytes:
    if hasattr(upload, "getvalue"):
        return upload.getvalue()
    upload.seek(0)
    return upload.read()


def extract_pdf_text(pdf_file: BinaryIO) -> str:
    import fitz

    pdf_bytes = _read_upload_bytes(pdf_file)
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


def parse_pdf_upload(pdf_file: BinaryIO, name: str) -> ParsedMaterial:
    """Extract text and preserve only image-heavy pages for an optional vision pass."""
    import fitz

    material = ParsedMaterial(kind="pdf", name=name, status="解析中", message="正在提取课件文字与图像页")
    try:
        pdf_bytes = _read_upload_bytes(pdf_file)
        if not pdf_bytes:
            raise ValueError("PDF 文件为空。")
        document = fitz.open(stream=pdf_bytes, filetype="pdf")
        material.page_count = len(document)
        pages: list[str] = []
        visual_candidates: list[int] = []
        for index, page in enumerate(document):
            page_text = page.get_text("text").strip()
            pages.append(page_text)
            # Avoid sending every decorative slide image. These pages either have
            # little selectable text or are likely image/diagram-led.
            if page.get_images(full=True) and len(page_text) < 180:
                visual_candidates.append(index)

        for index in visual_candidates[:4]:
            pixmap = document.load_page(index).get_pixmap(matrix=fitz.Matrix(1.25, 1.25), alpha=False)
            png_bytes = pixmap.tobytes("png")
            if png_bytes:
                material.visual_pages.append(PdfVisualPage(page_number=index + 1, image_bytes=png_bytes, source_name=name))
        document.close()
        material.text = "\n\n".join(page for page in pages if page).strip()
        material.char_count = len(material.text)
        if not material.text:
            if not material.visual_pages:
                raise ValueError("未找到可读取文字或图像页面，请确认 PDF 文件完整可打开。")
            material.status = "警告"
            material.message = f"未提取到可选文字；已保留 {len(material.visual_pages)} 页图像内容用于视觉分析"
            material.warning = "这可能是扫描版 PDF。生成时会尝试通过视觉模型理解已保留的页面。"
            return material
        low_text_threshold = max(180, (material.page_count or 1) * 45)
        if material.char_count < low_text_threshold:
            material.warning = "提取到的文字较少，可能是扫描版 PDF，生成质量可能受影响。"
            if material.visual_pages:
                material.warning += f" 已保留 {len(material.visual_pages)} 页图像内容用于视觉分析。"
            material.status = "警告"
            material.message = "已解析，但建议结合图像分析"
        else:
            material.status = "解析成功"
            material.message = "课件文字提取成功"
            if material.visual_pages:
                material.message += f"；另有 {len(material.visual_pages)} 页图像内容等待视觉分析"
    except Exception as exc:  # noqa: BLE001 - surfaced as student-friendly status in the app
        material.status = "失败"
        material.message = str(exc) or "无法解析此 PDF。"
        material.text = ""
        material.char_count = 0
    return material


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
    raw_bytes = _read_upload_bytes(txt_file)
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


def parse_txt_upload(txt_file: BinaryIO, name: str) -> ParsedMaterial:
    """Decode a transcript and retain its actual length for UI feedback."""
    material = ParsedMaterial(kind="txt", name=name, status="解析中", message="正在读取课堂字幕")
    try:
        material.text = read_txt_file(txt_file)
        material.char_count = len(material.text)
        material.status = "解析成功"
        material.message = "课堂字幕读取成功"
    except Exception as exc:  # noqa: BLE001
        material.status = "失败"
        material.message = str(exc) or "无法读取此 TXT 文件。"
    return material


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
