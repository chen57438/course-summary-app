from __future__ import annotations

from typing import BinaryIO

import fitz


def extract_pdf_text(pdf_file: BinaryIO) -> str:
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
