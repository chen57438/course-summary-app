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


def render_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --paper: #f7f1e8;
            --paper-deep: #efe4d3;
            --ink: #1f2430;
            --muted: #6d675f;
            --accent: #8c5e3c;
            --accent-deep: #603d24;
            --line: rgba(96, 61, 36, 0.18);
            --card: rgba(255, 251, 245, 0.78);
            --shadow: 0 20px 60px rgba(72, 48, 30, 0.10);
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(140, 94, 60, 0.10), transparent 30%),
                radial-gradient(circle at top right, rgba(93, 117, 92, 0.08), transparent 28%),
                linear-gradient(180deg, #fbf7f2 0%, var(--paper) 100%);
            color: var(--ink);
        }

        .main .block-container {
            max-width: 1120px;
            padding-top: 2.3rem;
            padding-bottom: 4rem;
        }

        h1, h2, h3 {
            color: var(--ink);
            letter-spacing: -0.02em;
        }

        [data-testid="stSidebar"] {
            background: rgba(250, 244, 236, 0.92);
            border-right: 1px solid var(--line);
        }

        [data-testid="stSidebar"] * {
            color: var(--ink);
        }

        div[data-testid="stFileUploader"] > section,
        div[data-testid="stTextInput"] > div,
        div[data-testid="stExpander"] {
            background: var(--card);
            border: 1px solid var(--line);
            border-radius: 22px;
            box-shadow: var(--shadow);
        }

        div[data-testid="stFileUploader"] > section {
            padding: 0.75rem 0.75rem 0.25rem 0.75rem;
        }

        div[data-testid="stTextInput"] input {
            background: transparent !important;
            color: var(--ink) !important;
            font-size: 1.05rem;
        }

        div[data-testid="stTextInput"] label,
        div[data-testid="stFileUploader"] label,
        div[data-testid="stCheckbox"] label {
            color: var(--accent-deep) !important;
            font-weight: 600;
        }

        .stButton > button,
        .stDownloadButton > button,
        div[data-testid="stFormSubmitButton"] button {
            border-radius: 999px;
            border: 1px solid rgba(96, 61, 36, 0.16);
            background: linear-gradient(135deg, #2f3f35 0%, #445649 100%);
            color: #f8f1e8;
            font-weight: 600;
            letter-spacing: 0.01em;
            box-shadow: 0 14px 34px rgba(47, 63, 53, 0.20);
            min-height: 3rem;
        }

        .stDownloadButton > button {
            background: linear-gradient(135deg, #8c5e3c 0%, #6d462b 100%);
            box-shadow: 0 14px 34px rgba(109, 70, 43, 0.18);
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover,
        div[data-testid="stFormSubmitButton"] button:hover {
            border-color: rgba(96, 61, 36, 0.22);
        }

        [data-testid="stMarkdownContainer"] p {
            line-height: 1.8;
        }

        .hero-shell {
            background:
                linear-gradient(135deg, rgba(255,255,255,0.55), rgba(255,255,255,0.18)),
                linear-gradient(180deg, rgba(255,250,243,0.95), rgba(244,236,224,0.85));
            border: 1px solid var(--line);
            border-radius: 32px;
            padding: 2rem 2rem 1.6rem 2rem;
            box-shadow: var(--shadow);
            margin-bottom: 1.4rem;
            position: relative;
            overflow: hidden;
        }

        .hero-shell::after {
            content: "";
            position: absolute;
            inset: auto -40px -40px auto;
            width: 180px;
            height: 180px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(140, 94, 60, 0.10), transparent 65%);
        }

        .eyebrow {
            text-transform: uppercase;
            letter-spacing: 0.16em;
            font-size: 0.76rem;
            color: var(--accent);
            margin-bottom: 0.8rem;
        }

        .hero-title {
            font-size: clamp(2.4rem, 4.8vw, 4.6rem);
            line-height: 0.95;
            margin: 0;
            color: #182028;
            font-weight: 700;
        }

        .hero-subtitle {
            margin-top: 1rem;
            max-width: 48rem;
            font-size: 1.08rem;
            color: var(--muted);
            line-height: 1.85;
        }

        .note-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.85rem;
            margin-top: 1.3rem;
        }

        .note-chip {
            background: rgba(255, 250, 243, 0.72);
            border: 1px solid var(--line);
            border-radius: 18px;
            padding: 0.95rem 1rem;
        }

        .note-chip strong {
            display: block;
            margin-bottom: 0.2rem;
            color: var(--accent-deep);
        }

        .section-card {
            background: rgba(255, 251, 245, 0.74);
            border: 1px solid var(--line);
            border-radius: 28px;
            padding: 1.3rem 1.35rem 1.1rem 1.35rem;
            box-shadow: var(--shadow);
            margin-top: 1rem;
            margin-bottom: 1rem;
        }

        .section-label {
            font-size: 0.78rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: var(--accent);
            margin-bottom: 0.35rem;
        }

        .section-title {
            font-size: 1.45rem;
            margin: 0;
            color: #1d2830;
        }

        @media (max-width: 900px) {
            .note-grid {
                grid-template-columns: 1fr;
            }

            .hero-shell {
                padding: 1.4rem 1.2rem 1.2rem 1.2rem;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    st.markdown(
        """
        <section class="hero-shell">
            <div class="eyebrow">Course Notes Atelier</div>
            <h1 class="hero-title">课程总结生成器</h1>
            <p class="hero-subtitle">
                把零散的课件与讲课字幕，整理成一份更像课堂讲义的复习笔记。
                你可以只上传一份材料，也可以把 PDF 与 TXT 一起交给系统，生成更完整的知识脉络与练习题。
            </p>
            <div class="note-grid">
                <div class="note-chip">
                    <strong>Lecture Notes</strong>
                    中文讲义式总结，强调结构、案例与术语。
                </div>
                <div class="note-chip">
                    <strong>English Quiz</strong>
                    可选生成英文单选题，适合课后自测。
                </div>
                <div class="note-chip">
                    <strong>Quiet Reading</strong>
                    更柔和的页面排版，适合长时间阅读与导出。
                </div>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def init_state() -> None:
    defaults = {
        "summary_markdown": "",
        "quiz_markdown": "",
        "pdf_text_preview": "",
        "transcript_text_preview": "",
        "quiz_items": [],
        "quiz_submitted": False,
        "quiz_score": 0,
        "quiz_feedback": [],
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_state() -> None:
    keys = [
        "summary_markdown",
        "quiz_markdown",
        "pdf_text_preview",
        "transcript_text_preview",
        "quiz_items",
        "quiz_submitted",
        "quiz_score",
        "quiz_feedback",
    ]
    for key in keys:
        if key in st.session_state:
            del st.session_state[key]
    init_state()


def render_quiz_section() -> None:
    if not st.session_state.quiz_markdown:
        return

    st.markdown(
        """
        <section class="section-card">
            <div class="section-label">Practice</div>
            <h2 class="section-title">English Quiz</h2>
        </section>
        """,
        unsafe_allow_html=True,
    )

    if not st.session_state.quiz_items:
        st.warning("Quiz 已生成，但暂时无法解析成交互式题目。")
        st.download_button(
            label="下载 Quiz Markdown（含答案）",
            data=st.session_state.quiz_markdown,
            file_name="course_quiz.md",
            mime="text/markdown",
            use_container_width=True,
        )
        return

    with st.form("quiz_form"):
        user_answers: list[str] = []
        for index, item in enumerate(st.session_state.quiz_items, start=1):
            st.markdown(f"**{index}. {item['question']}**")
            labels = [f"{option}. {item['options'][option]}" for option in ("A", "B", "C", "D")]
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
        feedback: list[dict] = []
        for index, item in enumerate(st.session_state.quiz_items, start=1):
            selected = user_answers[index - 1]
            correct = item["answer"]
            is_correct = selected == correct
            if is_correct:
                score += 1
            feedback.append(
                {
                    "selected": selected,
                    "correct": correct,
                    "is_correct": is_correct,
                    "item": item,
                }
            )
        st.session_state.quiz_submitted = True
        st.session_state.quiz_score = score
        st.session_state.quiz_feedback = feedback

    if st.session_state.quiz_submitted:
        for index, feedback in enumerate(st.session_state.quiz_feedback, start=1):
            item = feedback["item"]
            selected = feedback["selected"]
            correct = feedback["correct"]
            is_correct = feedback["is_correct"]
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
                st.markdown(f"- **{option}. {option_text}**")
                if explanation:
                    st.markdown(f"  Explanation: {explanation}")

        st.info(f"Quiz score: {st.session_state.quiz_score} / {len(st.session_state.quiz_items)}")

    st.download_button(
        label="下载 Quiz Markdown（含答案）",
        data=st.session_state.quiz_markdown,
        file_name="course_quiz.md",
        mime="text/markdown",
        use_container_width=True,
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
    init_state()
    render_theme()
    render_sidebar()
    render_header()

    top_col1, top_col2 = st.columns([3, 1])
    with top_col2:
        if st.button("重置页面", use_container_width=True):
            reset_state()
            st.rerun()

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
                st.session_state.summary_markdown = summary
                st.session_state.quiz_markdown = quiz_markdown
                st.session_state.pdf_text_preview = pdf_text
                st.session_state.transcript_text_preview = transcript_text
                st.session_state.quiz_items = parse_quiz_markdown(quiz_markdown) if quiz_markdown else []
                st.session_state.quiz_submitted = False
                st.session_state.quiz_score = 0
                st.session_state.quiz_feedback = []
            except ValueError as exc:
                st.error(str(exc))
                return
            except Exception as exc:  # noqa: BLE001
                st.error("生成总结时发生未预期错误，请稍后重试。")
                st.exception(exc)
                return

        st.success("总结生成完成。")

    if st.session_state.summary_markdown:
        st.markdown(
            """
            <section class="section-card">
                <div class="section-label">Summary</div>
                <h2 class="section-title">课程总结</h2>
            </section>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(st.session_state.summary_markdown)

        pdf_bytes = build_summary_pdf(
            summary_markdown=st.session_state.summary_markdown,
            course_name=course_name.strip() or "课程总结",
        )

        col_download_1, col_download_2 = st.columns(2)
        with col_download_1:
            st.download_button(
                label="下载 Markdown",
                data=st.session_state.summary_markdown,
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

    render_quiz_section()

    if st.session_state.pdf_text_preview:
        with st.expander("提取到的课件文本预览"):
            st.text_area("PDF 内容", st.session_state.pdf_text_preview[:5000], height=240)

    if st.session_state.transcript_text_preview:
        with st.expander("提取到的字幕文本预览"):
            st.text_area("TXT 内容", st.session_state.transcript_text_preview[:5000], height=240)


if __name__ == "__main__":
    main()
