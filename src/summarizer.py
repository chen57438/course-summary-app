from __future__ import annotations

import os
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
import google.generativeai as genai
import streamlit as st
from google.api_core.exceptions import ResourceExhausted, RetryError, ServiceUnavailable

from src.parser import build_transcript_study_view, normalize_study_text
from src.prompts import build_quiz_prompt, build_reading_chunk_prompt, build_summary_prompt


DEFAULT_GEMINI_MODEL = "gemini-2.5-flash-lite"
DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"
DEFAULT_DEEPSEEK_MODEL = "deepseek-v4-flash"
DEEPSEEK_BASE_URL = "https://api.deepseek.com"
MAX_PDF_CHARS = 22000
MAX_TRANSCRIPT_CHARS = 32000
READING_MAX_PDF_CHARS = 50000
READING_MAX_TRANSCRIPT_CHARS = 80000
READING_CHUNK_CHARS = 7000
READING_MAX_CHUNKS = 8
REQUEST_TIMEOUT_SECONDS = 60


@dataclass(frozen=True)
class ProviderClient:
    provider: str
    model_name: str
    client: Any

    @property
    def display_name(self) -> str:
        return {"gemini": "Gemini", "openai": "OpenAI", "deepseek": "DeepSeek"}[self.provider]


def _setting(name: str) -> str:
    """Read a secret first, then allow a local .env value without exposing it."""
    secret_value = ""
    try:
        secret_value = str(st.secrets.get(name, "")).strip()
    except Exception:  # noqa: BLE001
        secret_value = ""
    return secret_value or os.getenv(name, "").strip()


def _get_provider() -> str:
    provider = (_setting("AI_PROVIDER") or "gemini").lower()
    if provider not in {"gemini", "openai", "deepseek"}:
        raise ValueError("AI_PROVIDER must be one of: gemini, openai, or deepseek.")
    return provider


def _get_api_key(provider: str) -> str:
    key_name = {
        "gemini": "GOOGLE_API_KEY",
        "openai": "OPENAI_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
    }[provider]
    api_key = _setting(key_name)
    if not api_key:
        raise ValueError(
            f"未检测到 {key_name}。本地运行请在 .env 中配置；"
            "部署到 Streamlit Community Cloud 请在 Secrets 中配置。"
        )
    return api_key


def _configure_client() -> ProviderClient:
    load_dotenv()
    provider = _get_provider()
    api_key = _get_api_key(provider)

    if provider == "gemini":
        model_name = _setting("GEMINI_MODEL") or DEFAULT_GEMINI_MODEL
        genai.configure(api_key=api_key)
        return ProviderClient(provider, model_name, genai.GenerativeModel(model_name))

    try:
        from openai import OpenAI
    except ImportError as exc:
        raise ValueError("OpenAI-compatible provider is not installed. Run pip install -r requirements.txt.") from exc

    if provider == "deepseek":
        model_name = _setting("DEEPSEEK_MODEL") or DEFAULT_DEEPSEEK_MODEL
        return ProviderClient(provider, model_name, OpenAI(api_key=api_key, base_url=DEEPSEEK_BASE_URL))

    model_name = _setting("OPENAI_MODEL") or DEFAULT_OPENAI_MODEL
    return ProviderClient(provider, model_name, OpenAI(api_key=api_key))


def _clip_text(text: str, limit: int) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[:limit] + "\n\n[内容过长，已截断以适配配额限制。]"


def _read_openai_compatible_response(provider: ProviderClient, prompt: str, max_output_tokens: int) -> str:
    request_kwargs: dict[str, Any] = {
        "model": provider.model_name,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "max_tokens": max_output_tokens,
        "timeout": REQUEST_TIMEOUT_SECONDS,
    }
    # DeepSeek V4 enables thinking by default. For a long course prompt, its
    # reasoning can consume the entire completion budget before a final answer
    # is emitted. This workspace needs the final study material, so keep the
    # response in non-thinking mode unless a separate reasoning workflow is
    # added later.
    if provider.provider == "deepseek":
        request_kwargs["extra_body"] = {"thinking": {"type": "disabled"}}
    try:
        response = provider.client.chat.completions.create(**request_kwargs)
    except Exception as exc:  # API SDKs surface many provider-specific exception types
        raise ValueError(
            f"{provider.display_name} could not complete the request. "
            "Check the API key, available balance and model setting, then try again."
        ) from exc

    choices = getattr(response, "choices", [])
    content = getattr(choices[0].message, "content", "") if choices else ""
    if not content or not content.strip():
        raise ValueError(f"{provider.display_name} did not return usable content. Please try again.")
    return content.strip()


def _generate_text(
    provider: ProviderClient,
    prompt: str,
    on_stage: Callable[[str], None] | None = None,
) -> str:
    if on_stage:
        on_stage("Generating study materials")
    if provider.provider != "gemini":
        return _read_openai_compatible_response(provider, prompt, max_output_tokens=4096)
    try:
        response = provider.client.generate_content(
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
    provider: ProviderClient,
    prompt: str,
    max_output_tokens: int,
    on_stage: Callable[[str], None] | None = None,
) -> str:
    if on_stage:
        on_stage("Generating study materials")
    if provider.provider != "gemini":
        return _read_openai_compatible_response(provider, prompt, max_output_tokens=max_output_tokens)
    try:
        response = provider.client.generate_content(
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
    on_stage: Callable[[str], None] | None = None,
) -> str:
    if not pdf_text.strip() and not transcript_text.strip():
        raise ValueError("请至少上传一个 PDF 课件或 TXT 字幕文件。")

    if on_stage:
        on_stage("Organizing knowledge")
    provider = _configure_client()
    clipped_pdf_text = _clip_text(normalize_study_text(pdf_text), MAX_PDF_CHARS)
    cleaned_transcript, transcript_topic_map = build_transcript_study_view(transcript_text)
    transcript_input = cleaned_transcript or transcript_text
    clipped_transcript_text = _clip_text(normalize_study_text(transcript_input), MAX_TRANSCRIPT_CHARS)
    prompt = build_summary_prompt(
        pdf_text=clipped_pdf_text,
        transcript_text=clipped_transcript_text,
        course_name=course_name,
        transcript_study_view=cleaned_transcript,
        transcript_topic_map=transcript_topic_map,
    )

    result = _generate_text(provider, prompt, on_stage=on_stage)
    if on_stage:
        on_stage("Finalizing results")
    return result


def generate_quiz_material(
    pdf_text: str,
    transcript_text: str,
    course_name: str = "",
    on_stage: Callable[[str], None] | None = None,
) -> str:
    if not pdf_text.strip() and not transcript_text.strip():
        raise ValueError("请至少上传一个 PDF 课件或 TXT 字幕文件来生成 quiz。")

    if on_stage:
        on_stage("Organizing knowledge")
    provider = _configure_client()
    clipped_pdf_text = _clip_text(pdf_text, MAX_PDF_CHARS)
    clipped_transcript_text = _clip_text(transcript_text, MAX_TRANSCRIPT_CHARS)
    prompt = build_quiz_prompt(
        pdf_text=clipped_pdf_text,
        transcript_text=clipped_transcript_text,
        course_name=course_name,
    )

    result = _generate_text(provider, prompt, on_stage=on_stage)
    if on_stage:
        on_stage("Finalizing results")
    return result


def generate_reading_guide_material(
    pdf_text: str,
    transcript_text: str,
    course_name: str = "",
    on_stage: Callable[[str], None] | None = None,
) -> str:
    if not pdf_text.strip() and not transcript_text.strip():
        raise ValueError("请至少上传一个 PDF 课件或 TXT 字幕文件来生成精读翻译稿。")

    if on_stage:
        on_stage("Organizing knowledge")
    provider = _configure_client()
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
        if on_stage:
            on_stage(f"Generating study materials - reading part {index} of {total_chunks}")
        chunk_prompt = build_reading_chunk_prompt(
            chunk_text=chunk,
            chunk_index=index,
            total_chunks=total_chunks,
            course_name=course_name,
        )
        part_text = _generate_text_with_limit(provider, chunk_prompt, max_output_tokens=2048)
        parts.append(part_text.strip())

    if on_stage:
        on_stage("Finalizing results")
    return "\n\n".join([intro_text.strip(), *parts]).strip()
