from __future__ import annotations

import os

from dotenv import load_dotenv
import google.generativeai as genai
import streamlit as st
from google.api_core.exceptions import ResourceExhausted, RetryError, ServiceUnavailable

from src.prompts import build_quiz_prompt, build_reading_prompt, build_summary_prompt


DEFAULT_MODEL = "gemini-2.5-flash-lite"
MAX_PDF_CHARS = 18000
MAX_TRANSCRIPT_CHARS = 18000
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
    clipped_pdf_text = _clip_text(pdf_text, MAX_PDF_CHARS)
    clipped_transcript_text = _clip_text(transcript_text, MAX_TRANSCRIPT_CHARS)
    prompt = build_reading_prompt(
        pdf_text=clipped_pdf_text,
        transcript_text=clipped_transcript_text,
        course_name=course_name,
    )

    return _generate_text(model, prompt)
