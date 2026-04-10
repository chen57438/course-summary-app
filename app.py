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
            --bg: #f4f7fb;
            --bg-deep: #e9eff7;
            --ink: #101828;
            --muted: #5f6b7a;
            --accent: #1459c7;
            --accent-deep: #0f3f8f;
            --success: #0f766e;
            --line: rgba(16, 24, 40, 0.08);
            --card: rgba(255, 255, 255, 0.88);
            --shadow: 0 20px 48px rgba(15, 23, 42, 0.08);
            --shadow-soft: 0 8px 24px rgba(15, 23, 42, 0.05);
        }

        .stApp {
            background:
                radial-gradient(circle at top left, rgba(20, 89, 199, 0.10), transparent 26%),
                linear-gradient(180deg, #f8fbff 0%, var(--bg) 100%);
            color: var(--ink);
        }

        .main .block-container {
            max-width: 1180px;
            padding-top: 1.4rem;
            padding-bottom: 4rem;
        }

        h1, h2, h3 {
            color: var(--ink);
            letter-spacing: -0.02em;
        }

        [data-testid="stSidebar"] {
            background: rgba(248, 250, 252, 0.94);
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
            border-radius: 20px;
            box-shadow: var(--shadow-soft);
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
            color: #344054 !important;
            font-weight: 600;
        }

        .stButton > button,
        .stDownloadButton > button,
        div[data-testid="stFormSubmitButton"] button {
            border-radius: 14px;
            border: 1px solid rgba(20, 89, 199, 0.10);
            background: linear-gradient(180deg, #1663d6 0%, var(--accent) 100%);
            color: #ffffff;
            font-weight: 600;
            letter-spacing: 0.01em;
            box-shadow: 0 12px 28px rgba(20, 89, 199, 0.18);
            min-height: 3rem;
        }

        .stDownloadButton > button {
            background: #ffffff;
            color: var(--ink);
            border: 1px solid rgba(16, 24, 40, 0.10);
            box-shadow: var(--shadow-soft);
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover,
        div[data-testid="stFormSubmitButton"] button:hover {
            border-color: rgba(20, 89, 199, 0.22);
        }

        [data-testid="stMarkdownContainer"] p {
            line-height: 1.8;
        }

        .hero-shell {
            background:
                linear-gradient(135deg, rgba(16,24,40,0.96), rgba(19,67,149,0.92));
            border: 1px solid var(--line);
            border-radius: 28px;
            padding: 2.2rem 2.1rem 1.9rem 2.1rem;
            box-shadow: var(--shadow);
            margin-bottom: 1.4rem;
            position: relative;
            overflow: hidden;
        }

        .hero-shell::before {
            content: "";
            position: absolute;
            width: 260px;
            height: 260px;
            top: -100px;
            right: -40px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(255,255,255,0.10), transparent 68%);
        }

        .hero-shell::after {
            content: "";
            position: absolute;
            inset: auto auto -70px -50px;
            width: 240px;
            height: 240px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(255,255,255,0.08), transparent 70%);
        }

        .eyebrow {
            text-transform: uppercase;
            letter-spacing: 0.18em;
            font-size: 0.74rem;
            color: rgba(255,255,255,0.72);
            margin-bottom: 0.8rem;
        }

        .hero-title {
            font-size: clamp(2.8rem, 5.8vw, 4.8rem);
            line-height: 0.92;
            margin: 0;
            color: #ffffff;
            font-weight: 700;
            max-width: 10ch;
        }

        .hero-subtitle {
            margin-top: 1rem;
            max-width: 46rem;
            font-size: 1.02rem;
            color: rgba(255,255,255,0.78);
            line-height: 1.8;
        }

        .note-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.85rem;
            margin-top: 1.45rem;
        }

        .note-chip {
            background: rgba(255,255,255,0.10);
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 18px;
            padding: 1rem 1rem 0.95rem 1rem;
            color: rgba(255,255,255,0.78);
            backdrop-filter: blur(6px);
        }

        .note-chip strong {
            display: block;
            margin-bottom: 0.2rem;
            color: #ffffff;
        }

        .section-card {
            background: linear-gradient(180deg, rgba(255,255,255,0.92), rgba(252,253,255,0.82));
            border: 1px solid var(--line);
            border-radius: 22px;
            padding: 1.2rem 1.25rem 1rem 1.25rem;
            box-shadow: var(--shadow-soft);
            margin-top: 1rem;
            margin-bottom: 1rem;
            position: relative;
            overflow: hidden;
        }

        .section-card::after {
            content: "";
            position: absolute;
            inset: auto 0 0 0;
            height: 4px;
            background: linear-gradient(90deg, var(--accent), #4f8df0);
        }

        .section-label {
            font-size: 0.74rem;
            letter-spacing: 0.14em;
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
            grid-template-columns: 1fr 0.72fr;
            gap: 1rem;
            margin-bottom: 1.2rem;
        }

        .composer-panel,
        .side-note-panel,
        .result-frame {
            background: linear-gradient(180deg, rgba(255,255,255,0.90), rgba(250,252,255,0.84));
            border: 1px solid var(--line);
            border-radius: 20px;
            box-shadow: var(--shadow-soft);
        }

        .composer-panel {
            padding: 1.2rem 1.2rem 1rem 1.2rem;
            position: relative;
            overflow: hidden;
        }

        .side-note-panel {
            padding: 1.2rem;
            transform: none;
            background: linear-gradient(180deg, rgba(247,250,255,0.96), rgba(240,245,252,0.92));
        }

        .composer-panel::after {
            content: "WORKSPACE";
            position: absolute;
            right: 18px;
            top: 14px;
            font-size: 0.74rem;
            letter-spacing: 0.28em;
            color: rgba(20, 89, 199, 0.16);
        }

        .panel-kicker {
            font-size: 0.75rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: var(--accent);
            margin-bottom: 0.35rem;
        }

        .panel-title {
            font-size: 1.38rem;
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
            background: linear-gradient(180deg, rgba(255,255,255,0.94), rgba(248,250,253,0.86));
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
            <div class="eyebrow">Course Intelligence Workspace</div>
            <h1 class="hero-title">课程总结生成器</h1>
            <p class="hero-subtitle">
                将课件、字幕与课堂材料快速整理成结构化学习资产。
                支持生成讲义式总结、英文测验与可导出的复习材料，适合课程团队、学生与培训场景直接使用。
            </p>
            <div class="note-grid">
                <div class="note-chip">
                    <strong>Structured Notes</strong>
                    结构化中文总结，强调知识框架、案例与重点术语。
                </div>
                <div class="note-chip">
                    <strong>Assessment Ready</strong>
                    可选生成英文单选题，适合课后练习与教学评估。
                </div>
                <div class="note-chip">
                    <strong>Export Workflow</strong>
                    支持 Markdown 与 PDF 导出，方便归档、分享与打印。
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
                <h2 class="panel-title">上传材料，生成可直接复习与分发的课程内容</h2>
                <p class="panel-copy">
                    你可以上传 PDF、TXT，或者两者一起。系统会自动提炼知识结构、教授强调、术语框架与练习题，
                    同时兼容纯中文文档、中英混合讲义和常见课程字幕。
                </p>
            </div>
            <aside class="side-note-panel">
                <div class="panel-kicker">Capabilities</div>
                <h3 class="panel-title">当前支持的工作流</h3>
                <ul class="micro-list">
                    <li>纯中文课件与字幕总结</li>
                    <li>中英混合管理课程资料整理</li>
                    <li>Summary + Quiz 一体化复习输出</li>
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
