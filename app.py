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
            --paper: #f8efe3;
            --paper-deep: #ecd8c2;
            --ink: #18161a;
            --muted: #665d56;
            --accent: #a14f2a;
            --accent-deep: #5f2f1e;
            --forest: #27453f;
            --wine: #6c2f3d;
            --line: rgba(95, 47, 30, 0.16);
            --card: rgba(255, 249, 242, 0.72);
            --shadow: 0 22px 70px rgba(69, 37, 24, 0.14);
        }

        .stApp {
            background:
                radial-gradient(circle at 12% 12%, rgba(161, 79, 42, 0.16), transparent 24%),
                radial-gradient(circle at 86% 16%, rgba(39, 69, 63, 0.18), transparent 26%),
                radial-gradient(circle at 78% 72%, rgba(108, 47, 61, 0.12), transparent 22%),
                linear-gradient(180deg, #fcf5eb 0%, var(--paper) 100%);
            color: var(--ink);
        }

        .main .block-container {
            max-width: 1180px;
            padding-top: 1.7rem;
            padding-bottom: 4rem;
        }

        h1, h2, h3 {
            color: var(--ink);
            letter-spacing: -0.02em;
        }

        [data-testid="stSidebar"] {
            background: rgba(249, 241, 231, 0.92);
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
            border-radius: 26px;
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
            background: linear-gradient(135deg, var(--forest) 0%, #496159 100%);
            color: #f8f1e8;
            font-weight: 600;
            letter-spacing: 0.01em;
            box-shadow: 0 16px 36px rgba(39, 69, 63, 0.22);
            min-height: 3rem;
        }

        .stDownloadButton > button {
            background: linear-gradient(135deg, var(--accent) 0%, var(--wine) 100%);
            box-shadow: 0 16px 36px rgba(108, 47, 61, 0.18);
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
                linear-gradient(135deg, rgba(255,255,255,0.52), rgba(255,255,255,0.08)),
                linear-gradient(120deg, rgba(255,250,243,0.94), rgba(240,228,214,0.88));
            border: 1px solid var(--line);
            border-radius: 40px;
            padding: 2.3rem 2.2rem 1.9rem 2.2rem;
            box-shadow: var(--shadow);
            margin-bottom: 1.4rem;
            position: relative;
            overflow: hidden;
        }

        .hero-shell::before {
            content: "";
            position: absolute;
            width: 220px;
            height: 220px;
            top: -80px;
            right: 90px;
            border-radius: 32px;
            transform: rotate(24deg);
            background: linear-gradient(135deg, rgba(39, 69, 63, 0.18), rgba(39, 69, 63, 0.02));
        }

        .hero-shell::after {
            content: "";
            position: absolute;
            inset: auto -36px -30px auto;
            width: 220px;
            height: 220px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(161, 79, 42, 0.14), transparent 65%);
        }

        .eyebrow {
            text-transform: uppercase;
            letter-spacing: 0.24em;
            font-size: 0.72rem;
            color: var(--wine);
            margin-bottom: 0.8rem;
        }

        .hero-title {
            font-size: clamp(3rem, 7vw, 6.3rem);
            line-height: 0.88;
            margin: 0;
            color: #16151a;
            font-weight: 800;
            max-width: 8ch;
        }

        .hero-subtitle {
            margin-top: 1rem;
            max-width: 42rem;
            font-size: 1.05rem;
            color: var(--muted);
            line-height: 1.9;
        }

        .note-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.85rem;
            margin-top: 1.45rem;
        }

        .note-chip {
            background: linear-gradient(180deg, rgba(255,250,244,0.78), rgba(250,241,230,0.62));
            border: 1px solid var(--line);
            border-radius: 20px;
            padding: 1rem 1rem 0.95rem 1rem;
        }

        .note-chip strong {
            display: block;
            margin-bottom: 0.2rem;
            color: var(--accent-deep);
        }

        .section-card {
            background: linear-gradient(135deg, rgba(255,252,247,0.82), rgba(248,238,226,0.68));
            border: 1px solid var(--line);
            border-radius: 30px;
            padding: 1.4rem 1.45rem 1.15rem 1.45rem;
            box-shadow: var(--shadow);
            margin-top: 1rem;
            margin-bottom: 1rem;
            position: relative;
            overflow: hidden;
        }

        .section-card::after {
            content: "";
            position: absolute;
            width: 140px;
            height: 140px;
            right: -40px;
            top: -40px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(161, 79, 42, 0.10), transparent 70%);
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

        .composer-shell {
            display: grid;
            grid-template-columns: 1.35fr 0.65fr;
            gap: 1rem;
            margin-bottom: 1.2rem;
        }

        .composer-panel,
        .side-note-panel,
        .result-frame {
            background: rgba(255, 251, 245, 0.76);
            border: 1px solid var(--line);
            border-radius: 28px;
            box-shadow: var(--shadow);
        }

        .composer-panel {
            padding: 1.35rem 1.3rem 1rem 1.3rem;
            position: relative;
            overflow: hidden;
        }

        .side-note-panel {
            padding: 1.2rem;
            transform: translateY(26px);
            background: linear-gradient(180deg, rgba(255,249,242,0.82), rgba(243,230,218,0.78));
        }

        .composer-panel::after {
            content: "NOTES";
            position: absolute;
            right: 18px;
            top: 14px;
            font-size: 0.74rem;
            letter-spacing: 0.28em;
            color: rgba(95, 47, 30, 0.22);
        }

        .panel-kicker {
            font-size: 0.75rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: var(--accent);
            margin-bottom: 0.35rem;
        }

        .panel-title {
            font-size: 1.6rem;
            margin: 0 0 0.35rem 0;
            color: #1c262d;
            line-height: 1.15;
        }

        .panel-copy {
            color: var(--muted);
            line-height: 1.8;
            font-size: 0.98rem;
            margin: 0;
        }

        .micro-list {
            margin: 0.8rem 0 0 0;
            padding-left: 1rem;
            color: var(--muted);
            line-height: 1.8;
        }

        .result-frame {
            padding: 1.15rem 1.35rem 1.2rem 1.35rem;
            margin-top: 1rem;
            background:
                linear-gradient(180deg, rgba(255,252,248,0.82), rgba(250,242,232,0.74));
        }

        .result-frame h3 {
            margin-top: 0.1rem;
            margin-bottom: 0.4rem;
        }

        .result-frame p, .result-frame li {
            font-size: 1.02rem;
            line-height: 1.95;
        }

        @media (max-width: 900px) {
            .note-grid {
                grid-template-columns: 1fr;
            }

            .hero-shell {
                padding: 1.4rem 1.2rem 1.2rem 1.2rem;
            }

            .composer-shell {
                grid-template-columns: 1fr;
            }

            .side-note-panel {
                transform: none;
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


def render_composer_intro() -> None:
    st.markdown(
        """
        <section class="composer-shell">
            <div class="composer-panel">
                <div class="panel-kicker">Input Studio</div>
                <h2 class="panel-title">把材料交给这一页，让它慢慢长成一份可以阅读的讲义</h2>
                <p class="panel-copy">
                    你可以上传 PDF、TXT，或者两者一起。系统会优先整理知识结构、教授强调与可复习的术语框架，
                    同时也兼容纯中文文档，不会为了格式感而硬塞不自然的英文表达。
                </p>
            </div>
            <aside class="side-note-panel">
                <div class="panel-kicker">Notes</div>
                <h3 class="panel-title">这一版适合什么材料</h3>
                <ul class="micro-list">
                    <li>纯中文课件与字幕</li>
                    <li>中英混合的管理课程资料</li>
                    <li>需要同时生成 summary 与 quiz 的复习场景</li>
                </ul>
            </aside>
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
    st.sidebar.info("支持仅 PDF、仅 TXT，或 PDF + TXT 融合生成总结，也兼容纯中文文档。")


def main() -> None:
    init_state()
    render_theme()
    render_sidebar()
    render_header()
    render_composer_intro()

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
        st.markdown('<section class="result-frame">', unsafe_allow_html=True)
        st.markdown(st.session_state.summary_markdown)
        st.markdown("</section>", unsafe_allow_html=True)

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
