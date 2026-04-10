from __future__ import annotations

import streamlit as st

from src.exporter import build_summary_pdf
from src.parser import extract_pdf_text, read_txt_file
from src.quiz_parser import parse_quiz_markdown
from src.summarizer import generate_quiz_material, summarize_course_material


st.set_page_config(
    page_title="课程总结生成器",
    page_icon="📘",
    layout="wide",
)


def render_sidebar() -> None:
    st.sidebar.title("使用说明")
    st.sidebar.markdown(
        """
        1. 上传 PDF 课件、TXT 字幕，或两者之一
        2. 可选勾选英文 Quiz
        3. 填写课程名称或主题（可选）
        4. 点击生成总结
        """
    )
    st.sidebar.info("支持仅 PDF、仅 TXT，或 PDF + TXT 融合生成总结。")


def main() -> None:
    render_sidebar()

    st.title("课程总结生成器")
    st.caption("基于课件与讲课字幕，生成结构化中文讲义式总结")

    col1, col2 = st.columns(2)

    with col1:
        pdf_file = st.file_uploader("上传 PDF 课件", type=["pdf"])

    with col2:
        txt_file = st.file_uploader("上传 TXT 字幕", type=["txt"])

    course_name = st.text_input("课程名称 / 本次主题（可选）", placeholder="例如：Project Management - Stakeholder Analysis")
    generate_quiz = st.checkbox("同时生成英文单选题 Quiz", value=False)

    if st.button("生成课程总结", type="primary", use_container_width=True):
        if not pdf_file and not txt_file:
            st.error("请至少上传一个 PDF 课件或 TXT 字幕文件。")
            return

        with st.spinner("正在提取内容并生成总结..."):
            try:
                pdf_text = extract_pdf_text(pdf_file) if pdf_file else ""
                transcript_text = read_txt_file(txt_file) if txt_file else ""

                summary = summarize_course_material(
                    pdf_text=pdf_text,
                    transcript_text=transcript_text,
                    course_name=course_name.strip(),
                )
                quiz_markdown = ""
                if generate_quiz:
                    quiz_markdown = generate_quiz_material(
                        pdf_text=pdf_text,
                        transcript_text=transcript_text,
                        course_name=course_name.strip(),
                    )
            except ValueError as exc:
                st.error(str(exc))
                return
            except Exception as exc:  # noqa: BLE001
                st.error("生成总结时发生未预期错误，请稍后重试。")
                st.exception(exc)
                return

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

        if generate_quiz and quiz_markdown:
            quiz_items = parse_quiz_markdown(quiz_markdown)
            st.subheader("English Quiz")

            if not quiz_items:
                st.warning("Quiz 已生成，但暂时无法解析成交互式题目。")
                st.download_button(
                    label="下载 Quiz Markdown",
                    data=quiz_markdown,
                    file_name="course_quiz.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
            else:
                with st.form("quiz_form"):
                    user_answers: list[str] = []
                    for index, item in enumerate(quiz_items, start=1):
                        st.markdown(f"**{index}. {item['question']}**")
                        labels = [
                            f"{option}. {item['options'][option]}"
                            for option in ("A", "B", "C", "D")
                        ]
                        answer = st.radio(
                            f"Select your answer for Question {index}",
                            labels,
                            index=None,
                            key=f"quiz_q_{index}",
                            label_visibility="collapsed",
                        )
                        user_answers.append(answer[0] if answer else "")

                    submitted = st.form_submit_button("提交 Quiz")

                if submitted:
                    score = 0
                    for index, item in enumerate(quiz_items, start=1):
                        selected = user_answers[index - 1]
                        correct = item["answer"]
                        is_correct = selected == correct
                        if is_correct:
                            score += 1

                        st.markdown(f"### Question {index}")
                        if selected:
                            if is_correct:
                                st.success(f"Your answer: {selected}  |  Correct answer: {correct}")
                            else:
                                st.error(f"Your answer: {selected}  |  Correct answer: {correct}")
                        else:
                            st.warning(f"You did not select an answer. Correct answer: {correct}")

                        for option in ("A", "B", "C", "D"):
                            option_text = item["options"].get(option, "")
                            explanation = item["explanations"].get(option, "")
                            prefix = "Correct" if option == correct else "Option"
                            st.markdown(f"- **{option}. {option_text}**")
                            if explanation:
                                st.markdown(f"  {prefix} explanation: {explanation}")

                    st.info(f"Quiz score: {score} / {len(quiz_items)}")

                st.download_button(
                    label="下载 Quiz Markdown（含答案）",
                    data=quiz_markdown,
                    file_name="course_quiz.md",
                    mime="text/markdown",
                    use_container_width=True,
                )

        if pdf_text:
            with st.expander("提取到的课件文本预览"):
                st.text_area("PDF 内容", pdf_text[:5000], height=240)

        if transcript_text:
            with st.expander("提取到的字幕文本预览"):
                st.text_area("TXT 内容", transcript_text[:5000], height=240)


if __name__ == "__main__":
    main()
