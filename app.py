from __future__ import annotations

import streamlit as st

from src.exporter import build_summary_pdf
from src.parser import extract_pdf_outline, extract_pdf_text, read_txt_file
from src.summarizer import summarize_course_material


st.set_page_config(
    page_title="课程总结生成器",
    page_icon="📘",
    layout="wide",
)


def render_sidebar() -> None:
    st.sidebar.title("使用说明")
    st.sidebar.markdown(
        """
        1. 上传 PDF 课件
        2. 上传 TXT 字幕
        3. 填写课程名称或主题（可选）
        4. 点击生成总结
        """
    )
    st.sidebar.info("当前版本会优先分段解析字幕，再结合课件骨架生成总结。")


def main() -> None:
    render_sidebar()

    st.title("课程总结生成器")
    st.caption("基于课件与讲课字幕，生成结构化中文总结")

    col1, col2 = st.columns(2)

    with col1:
        pdf_file = st.file_uploader("上传 PDF 课件", type=["pdf"])

    with col2:
        txt_file = st.file_uploader("上传 TXT 字幕", type=["txt"])

    course_name = st.text_input("课程名称 / 本次主题（可选）", placeholder="例如：Project Management - Stakeholder Analysis")

    if st.button("生成课程总结", type="primary", use_container_width=True):
        if not pdf_file or not txt_file:
            st.error("请同时上传 PDF 课件和 TXT 字幕。")
            return

        status_box = st.empty()
        progress_bar = st.progress(0)

        def update_progress(current: int, total: int) -> None:
            base = 20
            span = 55
            value = min(base + int((current / max(total, 1)) * span), 90)
            progress_bar.progress(value)
            status_box.info(f"正在分析字幕内容：第 {current} / {total} 段")

        with st.spinner("正在提取内容并生成总结..."):
            try:
                status_box.info("正在提取 PDF 课件与 TXT 字幕内容")
                progress_bar.progress(10)
                pdf_text = extract_pdf_text(pdf_file)
                pdf_file.seek(0)
                pdf_outline = extract_pdf_outline(pdf_file)
                transcript_text = read_txt_file(txt_file)

                status_box.info("正在基于字幕生成分段笔记")
                summary = summarize_course_material(
                    pdf_outline=pdf_outline,
                    transcript_text=transcript_text,
                    course_name=course_name.strip(),
                    progress_callback=update_progress,
                )
            except ValueError as exc:
                progress_bar.empty()
                status_box.empty()
                st.error(str(exc))
                return
            except Exception as exc:  # noqa: BLE001
                progress_bar.empty()
                status_box.empty()
                st.error("生成总结时发生未预期错误，请稍后重试。")
                st.exception(exc)
                return

        progress_bar.progress(100)
        status_box.success("总结生成完成。")
        st.success("总结生成完成。")

        st.subheader("课程总结")
        st.markdown(summary)

        pdf_bytes = build_summary_pdf(
            summary_markdown=summary,
            course_name=course_name.strip() or "课程总结",
        )

        col_download_1, col_download_2 = st.columns(2)
        with col_download_1:
            st.download_button(
                label="下载 Markdown",
                data=summary,
                file_name="course_summary.md",
                mime="text/markdown",
                use_container_width=True,
            )

        with col_download_2:
            st.download_button(
                label="下载 PDF",
                data=pdf_bytes,
                file_name="course_summary.pdf",
                mime="application/pdf",
                use_container_width=True,
            )

        with st.expander("提取到的课件文本预览"):
            st.text_area("PDF 内容", pdf_text[:5000], height=240)

        with st.expander("提取到的课件骨架预览"):
            st.text_area("PDF 骨架", pdf_outline[:5000], height=220)

        with st.expander("提取到的字幕文本预览"):
            st.text_area("TXT 内容", transcript_text[:5000], height=240)


if __name__ == "__main__":
    main()
