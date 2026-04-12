from __future__ import annotations

import os

from dotenv import load_dotenv
import google.generativeai as genai
import streamlit as st
from google.api_core.exceptions import ResourceExhausted, RetryError, ServiceUnavailable

from src.prompts import build_quiz_prompt, build_reading_chunk_prompt, build_summary_prompt


DEFAULT_MODEL = "gemini-2.5-flash-lite"
MAX_PDF_CHARS = 18000
MAX_TRANSCRIPT_CHARS = 18000
READING_MAX_PDF_CHARS = 50000
READING_MAX_TRANSCRIPT_CHARS = 80000
READING_CHUNK_CHARS = 7000
READING_MAX_CHUNKS = 8
REQUEST_TIMEOUT_SECONDS = 60


def _get_api_key() -> str:
    secret_key = ""
    try:
        secret_key = str(st.secrets.get("GOOGLE_API_KEY", "")).strip()
    except Exception:  # noqa: BLE001
        secret_key = ""

    env_key = os.getenv("GOOGLE_API_KEY", "").strip()
    api_key = secret_key or env_key

    if not api_key:
        raise ValueError(
            "未检测到 GOOGLE_API_KEY。"
            "本地运行请在 .env 中配置；部署到 Streamlit Community Cloud 请在 Secrets 中配置。"
        )

    return api_key


def _configure_client() -> str:
    load_dotenv()
    api_key = _get_api_key()
    genai.configure(api_key=api_key)
    return api_key


def _get_model() -> genai.GenerativeModel:
    model_name = os.getenv("GEMINI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    return genai.GenerativeModel(model_name)


def _clip_text(text: str, limit: int) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[:limit] + "\n\n[内容过长，已截断以适配配额限制。]"


def _generate_text(model: genai.GenerativeModel, prompt: str) -> str:
    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.2,
                "max_output_tokens": 4096,
            },
            request_options={"timeout": REQUEST_TIMEOUT_SECONDS},
        )
    except ResourceExhausted as exc:
        raise ValueError(
            "当前超过 Gemini 的速率或输入配额限制。请等待约 1 分钟后重试，"
            "或减少上传内容，或改用付费层项目。"
        ) from exc
    except (ServiceUnavailable, RetryError) as exc:
        raise ValueError(
            "当前 Gemini 服务繁忙或响应超时。请稍后重试，或改用更稳定的付费层项目。"
        ) from exc

    text = getattr(response, "text", "").strip()
    if not text:
        raise ValueError("模型没有返回可用内容，请稍后重试。")
    return text


def _generate_text_with_limit(
    model: genai.GenerativeModel,
    prompt: str,
    max_output_tokens: int,
) -> str:
    try:
        response = model.generate_content(
            prompt,
            generation_config={
                "temperature": 0.2,
                "max_output_tokens": max_output_tokens,
            },
            request_options={"timeout": REQUEST_TIMEOUT_SECONDS},
        )
    except ResourceExhausted as exc:
        raise ValueError(
            "当前超过 Gemini 的速率或输入配额限制。请等待约 1 分钟后重试，"
            "或减少上传内容，或改用付费层项目。"
        ) from exc
    except (ServiceUnavailable, RetryError) as exc:
        raise ValueError(
            "当前 Gemini 服务繁忙或响应超时。请稍后重试，或改用更稳定的付费层项目。"
        ) from exc

    text = getattr(response, "text", "").strip()
    if not text:
        raise ValueError("模型没有返回可用内容，请稍后重试。")
    return text


def _split_text_into_chunks(text: str, max_chars: int, max_chunks: int) -> list[str]:
    paragraphs = [part.strip() for part in text.split("\n") if part.strip()]
    if not paragraphs:
        normalized = " ".join(text.split()).strip()
        return [normalized[:max_chars]] if normalized else []

    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for paragraph in paragraphs:
        clean = " ".join(paragraph.split()).strip()
        if not clean:
            continue

        if len(clean) > max_chars:
            if current:
                chunks.append("\n".join(current))
                current = []
                current_len = 0
                if len(chunks) >= max_chunks:
                    break

            start = 0
            while start < len(clean) and len(chunks) < max_chunks:
                chunks.append(clean[start : start + max_chars])
                start += max_chars
            continue

        projected = current_len + len(clean) + (1 if current else 0)
        if projected > max_chars:
            chunks.append("\n".join(current))
            current = [clean]
            current_len = len(clean)
            if len(chunks) >= max_chunks:
                break
        else:
            current.append(clean)
            current_len = projected

    if current and len(chunks) < max_chunks:
        chunks.append("\n".join(current))

    return chunks[:max_chunks]


def summarize_course_material(
    pdf_text: str,
    transcript_text: str,
    course_name: str = "",
) -> str:
    if not pdf_text.strip() and not transcript_text.strip():
        raise ValueError("请至少上传一个 PDF 课件或 TXT 字幕文件。")

    _configure_client()
    model = _get_model()
    clipped_pdf_text = _clip_text(pdf_text, MAX_PDF_CHARS)
    clipped_transcript_text = _clip_text(transcript_text, MAX_TRANSCRIPT_CHARS)
    prompt = build_summary_prompt(
        pdf_text=clipped_pdf_text,
        transcript_text=clipped_transcript_text,
        course_name=course_name,
    )

    return _generate_text(model, prompt)


def generate_quiz_material(
    pdf_text: str,
    transcript_text: str,
    course_name: str = "",
) -> str:
    if not pdf_text.strip() and not transcript_text.strip():
        raise ValueError("请至少上传一个 PDF 课件或 TXT 字幕文件来生成 quiz。")

    _configure_client()
    model = _get_model()
    clipped_pdf_text = _clip_text(pdf_text, MAX_PDF_CHARS)
    clipped_transcript_text = _clip_text(transcript_text, MAX_TRANSCRIPT_CHARS)
    prompt = build_quiz_prompt(
        pdf_text=clipped_pdf_text,
        transcript_text=clipped_transcript_text,
        course_name=course_name,
    )

    return _generate_text(model, prompt)


def generate_reading_guide_material(
    pdf_text: str,
    transcript_text: str,
    course_name: str = "",
) -> str:
    if not pdf_text.strip() and not transcript_text.strip():
        raise ValueError("请至少上传一个 PDF 课件或 TXT 字幕文件来生成精读翻译稿。")

    _configure_client()
    model = _get_model()
    clipped_pdf_text = _clip_text(pdf_text, READING_MAX_PDF_CHARS)
    clipped_transcript_text = _clip_text(transcript_text, READING_MAX_TRANSCRIPT_CHARS)

    if clipped_pdf_text and clipped_transcript_text:
        combined_text = (
            "[课件内容]\n"
            f"{clipped_pdf_text}\n\n"
            "[讲稿字幕]\n"
            f"{clipped_transcript_text}"
        )
    elif clipped_pdf_text:
        combined_text = f"[课件内容]\n{clipped_pdf_text}"
    else:
        combined_text = f"[讲稿字幕]\n{clipped_transcript_text}"

    chunks = _split_text_into_chunks(
        combined_text,
        max_chars=READING_CHUNK_CHARS,
        max_chunks=READING_MAX_CHUNKS,
    )
    if not chunks:
        raise ValueError("无法生成精读翻译稿：输入内容为空。")

    source_desc = []
    if clipped_pdf_text:
        source_desc.append("PDF 课件")
    if clipped_transcript_text:
        source_desc.append("TXT 字幕")
    source_label = " + ".join(source_desc) if source_desc else "课程材料"

    intro_text = (
        "## 📘 精读导览 (Reading Guide)\n"
        f"- CN: 本精读翻译稿基于{source_label}生成，目标是尽量按原始讲授顺序保留定义、案例、解释与提醒，帮助你更完整地读懂课程内容。\n"
        "- EN: This guided reading draft is generated from the provided course materials and aims to preserve definitions, examples, explanations, and instructor emphasis in a more complete reading flow.\n"
        "- CN: 为了覆盖更多内容，正文按多个 Part 顺序展开；每条先给中文整理，再给对应英文，便于边读边对照。\n"
        "- EN: To cover more of the source material, the main body is organized into multiple parts, with each note presented in Chinese first and English second for side-by-side reading.\n"
    )

    parts: list[str] = []
    total_chunks = len(chunks)
    for index, chunk in enumerate(chunks, start=1):
        chunk_prompt = build_reading_chunk_prompt(
            chunk_text=chunk,
            chunk_index=index,
            total_chunks=total_chunks,
            course_name=course_name,
        )
        part_text = _generate_text_with_limit(model, chunk_prompt, max_output_tokens=2048)
        parts.append(part_text.strip())

    return "\n\n".join([intro_text.strip(), *parts]).strip()
