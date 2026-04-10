from __future__ import annotations

import os

from dotenv import load_dotenv
import google.generativeai as genai
import streamlit as st
from google.api_core.exceptions import ResourceExhausted

from src.prompts import build_summary_prompt


DEFAULT_MODEL = "gemini-2.5-flash"
MAX_PDF_CHARS = 18000
MAX_TRANSCRIPT_CHARS = 18000


def _clip_text(text: str, limit: int) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[:limit] + "\n\n[内容过长，已截断以适配免费层配额限制。]"


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


def summarize_course_material(pdf_text: str, transcript_text: str, course_name: str = "") -> str:
    if not pdf_text.strip():
        raise ValueError("PDF 提取结果为空，无法生成总结。")

    if not transcript_text.strip():
        raise ValueError("TXT 字幕内容为空，无法生成总结。")

    _configure_client()

    model_name = os.getenv("GEMINI_MODEL", DEFAULT_MODEL).strip() or DEFAULT_MODEL
    model = genai.GenerativeModel(model_name)
    clipped_pdf_text = _clip_text(pdf_text, MAX_PDF_CHARS)
    clipped_transcript_text = _clip_text(transcript_text, MAX_TRANSCRIPT_CHARS)
    prompt = build_summary_prompt(
        pdf_text=clipped_pdf_text,
        transcript_text=clipped_transcript_text,
        course_name=course_name,
    )

    try:
        response = model.generate_content(prompt)
    except ResourceExhausted as exc:
        raise ValueError(
            "当前超过 Gemini 免费层的速率或输入配额限制。"
            "请等待约 1 分钟后重试，或缩短上传内容，或改用付费层项目。"
        ) from exc

    text = getattr(response, "text", "").strip()

    if not text:
        raise ValueError("模型没有返回可用内容，请稍后重试。")

    return text
