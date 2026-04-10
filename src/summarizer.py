from __future__ import annotations

import os

from dotenv import load_dotenv
import google.generativeai as genai
import streamlit as st
from google.api_core.exceptions import ResourceExhausted

from src.chunking import chunk_text, normalize_text
from src.prompts import build_final_summary_prompt, build_transcript_chunk_prompt


DEFAULT_MODEL = "gemini-2.5-flash"
MAX_PDF_OUTLINE_CHARS = 12000
TRANSCRIPT_CHUNK_SIZE = 5500
TRANSCRIPT_CHUNK_OVERLAP = 300
MAX_TRANSCRIPT_CHUNKS = 8


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


def _generate_text(model: genai.GenerativeModel, prompt: str) -> str:
    try:
        response = model.generate_content(prompt)
    except ResourceExhausted as exc:
        raise ValueError(
            "当前超过 Gemini 的速率或输入配额限制。请等待约 1 分钟后重试，"
            "或减少上传内容，或改用付费层项目。"
        ) from exc

    text = getattr(response, "text", "").strip()
    if not text:
        raise ValueError("模型没有返回可用内容，请稍后重试。")
    return text


def _summarize_transcript_chunks(
    transcript_text: str,
    model: genai.GenerativeModel,
    course_name: str = "",
) -> str:
    chunks = chunk_text(
        transcript_text,
        max_chars=TRANSCRIPT_CHUNK_SIZE,
        overlap_chars=TRANSCRIPT_CHUNK_OVERLAP,
    )[:MAX_TRANSCRIPT_CHUNKS]

    if not chunks:
        raise ValueError("字幕内容为空，无法进行分段总结。")

    partial_notes: list[str] = []
    total_chunks = len(chunks)

    for index, chunk in enumerate(chunks, start=1):
        prompt = build_transcript_chunk_prompt(
            transcript_chunk=chunk,
            chunk_index=index,
            total_chunks=total_chunks,
            course_name=course_name,
        )
        partial_text = _generate_text(model, prompt)
        partial_notes.append(f"### 字幕片段 {index}\n{partial_text}")

    return "\n\n".join(partial_notes)


def summarize_course_material(pdf_outline: str, transcript_text: str, course_name: str = "") -> str:
    if not pdf_outline.strip():
        raise ValueError("PDF 提取结果为空，无法生成总结。")

    if not transcript_text.strip():
        raise ValueError("TXT 字幕内容为空，无法生成总结。")

    _configure_client()
    model = _get_model()

    transcript_notes = _summarize_transcript_chunks(
        transcript_text=transcript_text,
        model=model,
        course_name=course_name,
    )

    clipped_pdf_outline = normalize_text(pdf_outline)[:MAX_PDF_OUTLINE_CHARS]
    final_prompt = build_final_summary_prompt(
        pdf_outline=clipped_pdf_outline,
        transcript_notes=transcript_notes,
        course_name=course_name,
    )

    return _generate_text(model, final_prompt)
