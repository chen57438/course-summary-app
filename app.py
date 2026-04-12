from __future__ import annotations

import streamlit as st

from src.exporter import build_summary_pdf
from src.bilingual_parser import parse_bilingual_pairs
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
            --bg: #fcf7f2;
            --ink: #17171b;
            --muted: #68615d;
            --accent: #ea6b45;
            --accent-soft: #ffd7c6;
            --teal: #1f8a82;
            --violet: #7a6ff0;
            --line: rgba(23, 23, 27, 0.08);
            --card: rgba(255, 252, 248, 0.9);
            --shadow: 0 24px 60px rgba(44, 31, 23, 0.10);
            --shadow-soft: 0 10px 28px rgba(44, 31, 23, 0.05);
        }

        .stApp {
            background:
                radial-gradient(circle at 10% 10%, rgba(234, 107, 69, 0.18), transparent 22%),
                radial-gradient(circle at 84% 14%, rgba(122, 111, 240, 0.14), transparent 26%),
                radial-gradient(circle at 74% 68%, rgba(31, 138, 130, 0.12), transparent 20%),
                linear-gradient(180deg, #fffdfb 0%, var(--bg) 100%);
            color: var(--ink);
        }

        .main .block-container {
            max-width: 1220px;
            padding-top: 1.2rem;
            padding-bottom: 4rem;
        }

        [data-testid="stSidebar"] {
            background: rgba(252, 247, 242, 0.94);
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
            box-shadow: var(--shadow-soft);
        }

        div[data-testid="stFileUploader"] > section {
            padding: 0.8rem 0.8rem 0.3rem 0.8rem;
        }

        div[data-testid="stTextInput"] input {
            background: transparent !important;
            color: var(--ink) !important;
            font-size: 1.04rem;
        }

        div[data-testid="stTextInput"] label,
        div[data-testid="stFileUploader"] label,
        div[data-testid="stCheckbox"] label {
            color: #3f3b39 !important;
            font-weight: 600;
        }

        .stButton > button,
        .stDownloadButton > button,
        div[data-testid="stFormSubmitButton"] button {
            border-radius: 18px;
            border: 1px solid rgba(234, 107, 69, 0.14);
            background: linear-gradient(135deg, var(--accent) 0%, #ff946b 100%);
            color: #ffffff;
            font-weight: 600;
            letter-spacing: 0.01em;
            box-shadow: 0 16px 34px rgba(234, 107, 69, 0.20);
            min-height: 3.15rem;
        }

        .stDownloadButton > button {
            background: linear-gradient(135deg, #ffffff 0%, #fff7f0 100%);
            color: var(--ink);
            border: 1px solid rgba(23, 23, 27, 0.10);
            box-shadow: var(--shadow-soft);
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover,
        div[data-testid="stFormSubmitButton"] button:hover {
            border-color: rgba(234, 107, 69, 0.22);
        }

        [data-testid="stMarkdownContainer"] p {
            line-height: 1.8;
        }

        .hero-shell {
            background: linear-gradient(135deg, rgba(255, 251, 246, 0.96), rgba(252, 241, 231, 0.92));
            border: 1px solid var(--line);
            border-radius: 36px;
            padding: 2.35rem 2.2rem 2.05rem 2.2rem;
            box-shadow: var(--shadow);
            margin-bottom: 1.35rem;
            position: relative;
            overflow: hidden;
        }

        .hero-shell::before {
            content: "";
            position: absolute;
            width: 300px;
            height: 300px;
            top: -120px;
            right: -70px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(234, 107, 69, 0.16), transparent 66%);
        }

        .hero-shell::after {
            content: "";
            position: absolute;
            inset: auto auto -110px -80px;
            width: 280px;
            height: 280px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(122, 111, 240, 0.16), transparent 68%);
        }

        .eyebrow {
            text-transform: uppercase;
            letter-spacing: 0.22em;
            font-size: 0.72rem;
            color: rgba(23, 23, 27, 0.46);
            margin-bottom: 0.8rem;
        }

        .hero-title {
            font-size: clamp(3rem, 6vw, 5.5rem);
            line-height: 0.9;
            margin: 0;
            color: var(--ink);
            font-weight: 800;
            max-width: 8ch;
        }

        .hero-subtitle {
            margin-top: 1rem;
            max-width: 42rem;
            font-size: 1.02rem;
            color: var(--muted);
            line-height: 1.8;
        }

        .note-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.85rem;
            margin-top: 1.4rem;
        }

        .note-chip {
            background: rgba(255,255,255,0.66);
            border: 1px solid rgba(23,23,27,0.06);
            border-radius: 20px;
            padding: 1rem 1rem 0.95rem 1rem;
            color: var(--muted);
            backdrop-filter: blur(10px);
        }

        .note-chip strong {
            display: block;
            margin-bottom: 0.2rem;
            color: var(--ink);
        }

        .composer-shell,
        .input-shell {
            display: grid;
            gap: 1rem;
            margin-bottom: 1.3rem;
        }

        .composer-shell {
            grid-template-columns: 1.08fr 0.92fr;
        }

        .input-shell {
            grid-template-columns: 1.18fr 0.82fr;
            align-items: start;
        }

        .composer-panel,
        .side-note-panel,
        .input-stage,
        .action-stage,
        .section-card,
        .result-frame {
            background: linear-gradient(135deg, rgba(255,255,255,0.94), rgba(251,246,240,0.84));
            border: 1px solid var(--line);
            border-radius: 24px;
            box-shadow: var(--shadow-soft);
        }

        .composer-panel,
        .side-note-panel,
        .input-stage,
        .action-stage {
            padding: 1.2rem;
        }

        .composer-panel {
            position: relative;
            overflow: hidden;
        }

        .composer-panel::after {
            content: "STUDIO";
            position: absolute;
            right: 18px;
            top: 14px;
            font-size: 0.74rem;
            letter-spacing: 0.28em;
            color: rgba(234, 107, 69, 0.14);
        }

        .side-note-panel {
            background: linear-gradient(180deg, rgba(255,246,238,0.96), rgba(245,236,230,0.92));
            transform: translateY(20px);
        }

        .panel-kicker {
            font-size: 0.75rem;
            letter-spacing: 0.12em;
            text-transform: uppercase;
            color: var(--accent);
            margin-bottom: 0.35rem;
        }

        .panel-title {
            font-size: 1.55rem;
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

        .action-stage {
            position: relative;
            overflow: hidden;
        }

        .action-stage::after {
            content: "";
            position: absolute;
            width: 170px;
            height: 170px;
            right: -40px;
            top: -40px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(31, 138, 130, 0.14), transparent 70%);
        }

        .action-copy {
            color: var(--muted);
            line-height: 1.75;
            font-size: 0.96rem;
            margin: 0.4rem 0 1rem 0;
        }

        .action-pills {
            display: flex;
            flex-wrap: wrap;
            gap: 0.7rem;
            margin-top: 0.8rem;
            margin-bottom: 1rem;
        }

        .action-pill {
            background: rgba(234, 107, 69, 0.10);
            border: 1px solid rgba(234, 107, 69, 0.14);
            border-radius: 999px;
            padding: 0.46rem 0.8rem;
            font-size: 0.88rem;
            color: var(--ink);
        }

        .action-button-stack {
            display: grid;
            gap: 0.75rem;
        }

        .section-card {
            padding: 1.2rem 1.25rem 0.95rem 1.25rem;
            margin-top: 1rem;
            margin-bottom: 1rem;
            position: relative;
            overflow: hidden;
        }

        .section-card::after {
            content: "";
            position: absolute;
            inset: 0 auto 0 0;
            width: 8px;
            background: linear-gradient(180deg, var(--accent), var(--teal), var(--violet));
        }

        .section-label {
            font-size: 0.74rem;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            color: var(--accent);
            margin-bottom: 0.35rem;
        }

        .section-title {
            font-size: 1.42rem;
            margin: 0;
            color: #1d2830;
        }

        .result-frame {
            padding: 1.1rem 1.3rem 1.15rem 1.3rem;
            margin-top: 1rem;
        }

        .result-frame h3 {
            margin-top: 0.1rem;
            margin-bottom: 0.4rem;
        }

        .result-frame p,
        .result-frame li {
            font-size: 1.02rem;
            line-height: 1.92;
        }

        @media (max-width: 900px) {
            .note-grid, .composer-shell, .input-shell {
                grid-template-columns: 1fr;
            }

            .hero-shell {
                padding: 1.45rem 1.2rem 1.2rem 1.2rem;
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
            <div class="eyebrow">Course Studio</div>
            <h1 class="hero-title">课程总结生成器</h1>
            <p class="hero-subtitle">
                把课件、字幕和课堂材料整理成更可读、更可复习的输出。
                它应该像一张有呼吸感的工作台，而不是一张死板的表格。
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


def render_action_stage() -> None:
    st.markdown(
        """
        <section class="action-stage">
            <div class="panel-kicker">Action Stage</div>
            <h2 class="panel-title">把操作放到这一侧，但别让它压住整张页面</h2>
            <p class="action-copy">
                这里负责生成、重置和切换输出模式。材料输入留在左边，
                动作与节奏留在右边，让布局更自由，但依然顺手。
            </p>
            <div class="action-pills">
                <span class="action-pill">PDF / TXT / Mixed</span>
                <span class="action-pill">Summary</span>
                <span class="action-pill">Quiz</span>
                <span class="action-pill">Export</span>
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
        "_trigger_generate": False,
        "bilingual_pairs": [],
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
        "_trigger_generate",
        "bilingual_pairs",
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

    left_col, right_col = st.columns([1.18, 0.82], gap="large")

    with left_col:
        st.markdown('<section class="input-stage">', unsafe_allow_html=True)
        upload_col1, upload_col2 = st.columns(2)
        with upload_col1:
            pdf_file = st.file_uploader("上传 PDF 课件", type=["pdf"])
        with upload_col2:
            txt_file = st.file_uploader("上传 TXT 字幕", type=["txt"])
        course_name = st.text_input("课程名称 / 本次主题（可选）", placeholder="例如：Project Management - Stakeholder Analysis")
        st.markdown("</section>", unsafe_allow_html=True)

    with right_col:
        render_action_stage()
        st.markdown('<div class="action-button-stack">', unsafe_allow_html=True)
        generate_quiz = st.checkbox("同时生成英文单选题 Quiz", value=False)
        if st.button("生成课程总结", type="primary", use_container_width=True):
            st.session_state["_trigger_generate"] = True
        if st.button("重置页面", use_container_width=True):
            reset_state()
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    if st.session_state["_trigger_generate"]:
        st.session_state["_trigger_generate"] = False
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
                st.session_state.bilingual_pairs = parse_bilingual_pairs(summary)
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
        tab1, tab2 = st.tabs(["讲义版", "中英对照版"])
        with tab1:
            st.markdown('<section class="result-frame">', unsafe_allow_html=True)
            st.markdown(st.session_state.summary_markdown)
            st.markdown("</section>", unsafe_allow_html=True)

        with tab2:
            st.info("原生 Streamlit 不支持逐句选中后自动联动高亮；这里提供按条编号的中英对照视图，方便你快速对应。")
            if not st.session_state.bilingual_pairs:
                st.warning("当前总结暂时无法解析为中英对照条目。")
            else:
                for idx, item in enumerate(st.session_state.bilingual_pairs, start=1):
                    st.markdown(
                        f"""
                        <section class="result-frame">
                            <div class="section-label">{item['section']}</div>
                            <h3>{idx:02d}. {item['module'] or 'Bilingual Note'}</h3>
                            <p><strong>中文</strong><br>{item['cn']}</p>
                            <p><strong>English</strong><br>{item['en']}</p>
                        </section>
                        """,
                        unsafe_allow_html=True,
                    )

        pdf_bytes = build_summary_pdf(
            summary_markdown=st.session_state.summary_markdown,
            course_name=course_name.strip() or "课程总结",
        )

        download_col1, download_col2 = st.columns(2)
        with download_col1:
            st.download_button(
                label="下载 Markdown",
                data=st.session_state.summary_markdown,
                file_name="course_summary.md",
                mime="text/markdown",
                use_container_width=True,
            )
        with download_col2:
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
