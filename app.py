from __future__ import annotations

import hashlib
import html
import json

import streamlit as st
import streamlit.components.v1 as components

from src.exporter import build_summary_pdf
from src.bilingual_parser import parse_bilingual_pairs
from src.parser import ParsedMaterial, parse_pdf_upload, parse_txt_upload
from src.quiz_parser import parse_quiz_markdown
from src.summarizer import (
    generate_quiz_material,
    generate_reading_guide_material,
    summarize_course_material,
)
from src.workspace import SourceReference, combine_materials, expected_outputs, parse_summary_sections, source_registry


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

        .workbench-shell {
            display: grid;
            gap: 1rem;
            margin-bottom: 1.2rem;
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

        .action-toolbar {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.85rem;
            margin-top: 0.9rem;
        }

        .toolbar-note {
            color: var(--muted);
            line-height: 1.7;
            font-size: 0.95rem;
            margin: 0.15rem 0 0 0;
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

        .workspace-nav, .expectation-panel, .material-card, .tool-card, .study-loop, .source-note {
            border: 1px solid var(--line);
            background: rgba(255, 255, 255, 0.72);
            border-radius: 18px;
            box-shadow: var(--shadow-soft);
        }

        .workspace-nav {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            gap: 0.55rem;
            padding: 0.85rem 1rem;
            margin: 0.2rem 0 1.2rem;
            color: var(--muted);
            font-size: 0.9rem;
        }

        .workspace-nav strong { color: var(--ink); }
        .nav-arrow { color: var(--accent); font-weight: 800; }

        .material-card, .tool-card, .expectation-panel, .study-loop, .source-note {
            padding: 1rem 1.05rem;
            margin: 0.45rem 0;
        }

        .material-card { border-left: 5px solid var(--teal); }
        .material-card.warning { border-left-color: #d88b16; }
        .material-card.failed { border-left-color: #c7494d; }
        .status-kicker, .tool-eyebrow, .result-eyebrow {
            text-transform: uppercase;
            letter-spacing: 0.12em;
            color: var(--muted);
            font-size: 0.72rem;
            font-weight: 700;
        }

        .material-title, .tool-title { margin: 0.2rem 0; color: var(--ink); font-size: 1.08rem; }
        .material-meta, .tool-copy, .expectation-panel p, .source-note p { margin: 0.25rem 0; color: var(--muted); font-size: 0.9rem; line-height: 1.65; }
        .status-badge, .source-badge {
            display: inline-block;
            padding: 0.25rem 0.52rem;
            border-radius: 999px;
            font-size: 0.75rem;
            font-weight: 700;
            background: rgba(31, 138, 130, 0.13);
            color: #126f68;
            margin-right: 0.35rem;
        }
        .status-badge.warning { background: rgba(216, 139, 22, 0.14); color: #8a5700; }
        .status-badge.failed { background: rgba(199, 73, 77, 0.12); color: #a73034; }
        .tool-card { min-height: 215px; border-top: 4px solid var(--accent); }
        .tool-card.quiz { border-top-color: var(--violet); }
        .tool-card.reading { border-top-color: var(--teal); }
        .tool-output { color: var(--ink); font-size: 0.9rem; line-height: 1.6; margin: 0.6rem 0 0; }
        .expectation-panel { background: linear-gradient(135deg, rgba(255, 244, 237, 0.94), rgba(255, 252, 248, 0.9)); }
        .study-loop { display: flex; flex-wrap: wrap; gap: 0.5rem; align-items: center; }
        .study-step { padding: 0.38rem 0.6rem; border-radius: 999px; background: rgba(122, 111, 240, 0.09); color: #4f45b5; font-size: 0.86rem; }
        .source-note { background: rgba(31, 138, 130, 0.055); box-shadow: none; }

        div[data-testid="stStatusWidget"] { border-radius: 18px; border: 1px solid var(--line); }

        @media (max-width: 900px) {
            .note-grid, .composer-shell, .input-shell, .action-toolbar {
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
                    <li>英文材料精读翻译稿</li>
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
            <div class="panel-kicker">Primary Actions</div>
            <h2 class="panel-title">三个主功能并列放在输入区下面，上传后立刻启动</h2>
            <p class="action-copy">
                课程总结、英文 Quiz 和精读翻译稿现在是三个独立入口。
                你可以只触发其中一个功能，不需要再把 Quiz 或翻译当作附带选项。
            </p>
            <div class="action-pills">
                <span class="action-pill">Summary</span>
                <span class="action-pill">Quiz</span>
                <span class="action-pill">Reading Guide</span>
                <span class="action-pill">Reset</span>
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
        "bilingual_pairs": [],
        "reading_markdown": "",
        "materials": [],
        "material_signature": "",
        "sources": {},
        "summary_overrides": {},
        "editing_section": "",
        "quiz_revealed": set(),
        "quiz_attempts": {},
        "learning_record": {"understood": set(), "review_later": set(), "needs_practice": set()},
        "select_summary": True,
        "select_quiz": False,
        "select_reading": False,
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_state() -> None:
    for key in list(st.session_state.keys()):
        if key in st.session_state:
            del st.session_state[key]
    init_state()


def render_sidebar() -> None:
    st.sidebar.title("Study Workspace")
    st.sidebar.markdown("导入材料、选择学习方式，再把结果转成可复习的学习资产。")
    st.sidebar.divider()
    st.sidebar.markdown("**How it works**")
    st.sidebar.markdown("1. Add slides or a transcript\n2. Confirm parsing status\n3. Choose study tools\n4. Review, practise and revisit")
    st.sidebar.info("结果与学习标记保存在当前浏览器会话；不会上传到额外数据库。")


def _upload_signature(files: list[object]) -> str:
    digest = hashlib.sha256()
    for file in files:
        digest.update(str(getattr(file, "name", "")).encode("utf-8"))
        digest.update(getattr(file, "getvalue")())
    return digest.hexdigest()


def sync_materials(pdf_files: list[object], txt_files: list[object]) -> list[ParsedMaterial]:
    all_files = [*pdf_files, *txt_files]
    signature = _upload_signature(all_files) if all_files else ""
    if signature == st.session_state.material_signature:
        return st.session_state.materials

    materials: list[ParsedMaterial] = []
    for file in pdf_files:
        materials.append(parse_pdf_upload(file, str(file.name)))
    for file in txt_files:
        materials.append(parse_txt_upload(file, str(file.name)))
    st.session_state.material_signature = signature
    st.session_state.materials = materials
    st.session_state.sources = source_registry(materials)
    return materials


def render_workspace_nav() -> None:
    st.markdown(
        """
        <section class="workspace-nav">
            <strong>Learning flow</strong><span class="nav-arrow">→</span>
            <span>Read</span><span class="nav-arrow">→</span><span>Review</span>
            <span class="nav-arrow">→</span><span>Quiz</span><span class="nav-arrow">→</span>
            <span>Check mistakes</span><span class="nav-arrow">→</span><span>Review again</span>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_material_card(material: ParsedMaterial) -> None:
    class_name = ""
    if material.status == "Warning":
        class_name = " warning"
    elif material.status == "Failed":
        class_name = " failed"
    badge_class = ""
    if material.status == "Warning":
        badge_class = " warning"
    elif material.status == "Failed":
        badge_class = " failed"
    metadata = ["PDF slides" if material.kind == "pdf" else "TXT transcript"]
    if material.page_count is not None:
        metadata.append(f"{material.page_count} pages")
    if material.char_count:
        metadata.append(f"{material.char_count:,} characters extracted")
    st.markdown(
        f"""
        <section class="material-card{class_name}">
            <div class="status-kicker">Material</div>
            <h3 class="material-title">{html.escape(material.name)}</h3>
            <span class="status-badge{badge_class}">{html.escape(material.status)}</span>
            <p class="material-meta">{' · '.join(metadata)}</p>
            <p class="material-meta">{html.escape(material.message)}</p>
            {f'<p class="material-meta"><strong>Note:</strong> {html.escape(material.warning)}</p>' if material.warning else ''}
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_materials(materials: list[ParsedMaterial]) -> None:
    st.markdown("### Materials")
    if not materials:
        st.info("Add at least one PDF slide deck or TXT transcript to begin. You can upload multiple files of either type.")
        return
    for material in materials:
        render_material_card(material)
    if any(material.status == "Failed" for material in materials):
        st.warning("Files that failed parsing will not be included. You can remove them and upload a readable copy without losing the other materials.")


TOOL_CONFIG = {
    "summary": {
        "title": "课程总结",
        "class_name": "summary",
        "fit": "适合：考试复习、快速掌握整节课",
        "output": "输出：章节结构、重点知识、核心术语、教授强调内容",
    },
    "quiz": {
        "title": "Quiz",
        "class_name": "quiz",
        "fit": "适合：检查自己是否真正掌握",
        "output": "输出：英文选择题、用户作答、答案解析",
    },
    "reading": {
        "title": "精读翻译",
        "class_name": "reading",
        "fit": "适合：英文课程阅读、理解课堂原文",
        "output": "输出：英文原文整理、中文翻译、重点表达解释",
    },
}


def render_tool_picker() -> list[str]:
    st.markdown("### Study Tools")
    st.caption("Choose one learning mode, or combine several. Your choices only affect what will be generated - they do not change the uploaded materials.")
    selected: list[str] = []
    columns = st.columns(3)
    for column, (key, config) in zip(columns, TOOL_CONFIG.items()):
        with column:
            st.markdown(
                f"""
                <section class="tool-card {config['class_name']}">
                    <div class="tool-eyebrow">Study mode</div>
                    <h3 class="tool-title">{config['title']}</h3>
                    <p class="tool-copy">{config['fit']}</p>
                    <p class="tool-output">{config['output']}</p>
                </section>
                """,
                unsafe_allow_html=True,
            )
            if st.checkbox(f"Select {config['title']}", key=f"select_{key}"):
                selected.append(key)
    return selected


def render_expectation(selected_tools: list[str], has_valid_material: bool) -> None:
    st.markdown('<section class="expectation-panel">', unsafe_allow_html=True)
    if not selected_tools:
        st.markdown("**Choose a study tool to see your result plan.**")
        st.caption("You can select one tool for a focused task, or combine tools for a complete review session.")
    else:
        labels = " + ".join(TOOL_CONFIG[tool]["title"] for tool in selected_tools)
        st.markdown(f"**You selected: {labels}**")
        st.markdown("**You will receive:**")
        for item in expected_outputs(selected_tools):
            st.markdown(f"- {item}")
        if not has_valid_material:
            st.caption("Add a readable PDF or TXT file before generating.")
    st.markdown("</section>", unsafe_allow_html=True)


def _run_generation(selected_tools: list[str], materials: list[ParsedMaterial], course_name: str) -> None:
    pdf_text = combine_materials(materials, "pdf")
    transcript_text = combine_materials(materials, "txt")
    if not pdf_text and not transcript_text:
        st.error("We could not find readable text in your uploads. Try a text-based PDF or a UTF-8 TXT transcript, then generate again.")
        return

    with st.status("Preparing your study workspace", expanded=True) as status:
        status.write("1. Reading materials")
        status.write("2. Confirming parsed course content")

        def update_stage(stage: str) -> None:
            status.write(f"• {stage}")
            status.update(label=stage, state="running")

        try:
            for tool in selected_tools:
                if tool == "summary":
                    result = summarize_course_material(pdf_text, transcript_text, course_name, on_stage=update_stage)
                    st.session_state.summary_markdown = result
                    st.session_state.bilingual_pairs = parse_bilingual_pairs(result)
                    st.session_state.summary_overrides = {}
                elif tool == "quiz":
                    result = generate_quiz_material(pdf_text, transcript_text, course_name, on_stage=update_stage)
                    st.session_state.quiz_markdown = result
                    st.session_state.quiz_items = parse_quiz_markdown(result)
                    st.session_state.quiz_revealed = set()
                    st.session_state.quiz_attempts = {}
                elif tool == "reading":
                    result = generate_reading_guide_material(pdf_text, transcript_text, course_name, on_stage=update_stage)
                    st.session_state.reading_markdown = result
            status.update(label="Study materials ready", state="complete", expanded=False)
        except ValueError as exc:
            status.update(label="Generation could not be completed", state="error")
            st.error(f"Generation failed. Your uploaded files are still available. {exc}")
        except Exception:  # noqa: BLE001 - detailed error stays out of the student UI
            status.update(label="Generation could not be completed", state="error")
            st.error("Generation failed. Your uploaded files are still available. Please try again in a moment.")


def _copy_button(value: str, key: str) -> None:
    safe_value = json.dumps(value).replace("</", "<\\/")
    components.html(
        f"""<button id=\"{key}\" style=\"border:1px solid #ead7cb;border-radius:10px;background:#fffaf6;color:#4a3025;padding:8px 11px;cursor:pointer;font:600 13px system-ui\">Copy</button>
        <script>document.getElementById({json.dumps(key)}).onclick = async () => {{ await navigator.clipboard.writeText({safe_value}); document.getElementById({json.dumps(key)}).textContent = 'Copied'; }};</script>""",
        height=42,
    )


def _render_source_reference(source_labels: list[str]) -> None:
    if not source_labels:
        return
    labels = " · ".join(source_labels)
    st.markdown(f'<div class="source-note"><span class="source-badge">Source</span><strong>{html.escape(labels)}</strong><p>General source context is available below. Precise pages and timestamps are not available for this result, so none are shown.</p></div>', unsafe_allow_html=True)
    sources = st.session_state.sources
    for source in sources.values():
        if isinstance(source, SourceReference) and source.label in source_labels:
            with st.expander(f"View original context · {source.label}"):
                st.caption(source.note)
                st.text(source.excerpt)


def _materialize_summary() -> str:
    sections = parse_summary_sections(st.session_state.summary_markdown, st.session_state.sources)
    overrides = st.session_state.summary_overrides
    parts = []
    for index, section in enumerate(sections):
        section_id = f"{section.key}-{index}"
        parts.append(f"## {section.title}\n\n{overrides.get(section_id, section.markdown)}")
    return "\n\n".join(parts).strip() or st.session_state.summary_markdown


def render_summary_results(course_name: str) -> None:
    if not st.session_state.summary_markdown:
        return
    st.markdown('<section class="section-card"><div class="section-label">Study Results</div><h2 class="section-title">课程总结</h2></section>', unsafe_allow_html=True)
    st.caption("Each section is intentionally separated so you can read, copy or edit one study module without losing the rest of the result.")
    sections = parse_summary_sections(st.session_state.summary_markdown, st.session_state.sources)
    if not sections:
        st.warning("The summary was generated, but its structure could not be recognized. You can still download the original Markdown below.")
        st.markdown(st.session_state.summary_markdown)
        return

    for index, section in enumerate(sections):
        section_id = f"{section.key}-{index}"
        content = st.session_state.summary_overrides.get(section_id, section.markdown)
        with st.container(border=True):
            title_col, action_col = st.columns([0.65, 0.35])
            with title_col:
                st.markdown(f"#### {section.title}")
                if section.source_labels:
                    st.caption("Source: " + " · ".join(section.source_labels))
            with action_col:
                edit_col, regen_col, copy_col = st.columns(3)
                with edit_col:
                    if st.button("Edit", key=f"edit-{section_id}"):
                        st.session_state.editing_section = section_id
                with regen_col:
                    if st.button("Regenerate", key=f"regen-{section_id}"):
                        st.info("This module is ready for a future section-level API. The current generator only supports whole-course generation, so this action will not silently rerun or overwrite your other notes.")
                with copy_col:
                    _copy_button(content, f"copy-{section_id}")

            if st.session_state.editing_section == section_id:
                draft = st.text_area("Edit this study module", value=content, height=220, key=f"draft-{section_id}")
                save_col, cancel_col = st.columns(2)
                with save_col:
                    if st.button("Save module", key=f"save-{section_id}", type="primary"):
                        st.session_state.summary_overrides[section_id] = draft.strip()
                        st.session_state.editing_section = ""
                        st.rerun()
                with cancel_col:
                    if st.button("Cancel", key=f"cancel-{section_id}"):
                        st.session_state.editing_section = ""
                        st.rerun()
            else:
                st.markdown(content)
            _render_source_reference(section.source_labels)

    exported_summary = _materialize_summary()
    pdf_bytes = build_summary_pdf(exported_summary, course_name or "课程总结")
    download_col1, download_col2 = st.columns(2)
    with download_col1:
        st.download_button("Download Markdown", exported_summary, "course_summary.md", "text/markdown", use_container_width=True)
    with download_col2:
        st.download_button("Download PDF", pdf_bytes, "course_summary.pdf", "application/pdf", use_container_width=True)


def render_reading_results() -> None:
    if not st.session_state.reading_markdown:
        return
    st.markdown('<section class="section-card"><div class="section-label">Reading</div><h2 class="section-title">精读翻译稿</h2></section>', unsafe_allow_html=True)
    pairs = parse_bilingual_pairs(st.session_state.reading_markdown)
    if not pairs:
        st.markdown(st.session_state.reading_markdown)
    else:
        st.caption("Read Chinese and English in parallel. Key terminology remains in context rather than being detached into a separate translation list.")
        for index, pair in enumerate(pairs, start=1):
            with st.container(border=True):
                st.caption(f"Part {index:02d} · {pair['section'] or 'Guided reading'}")
                left, right = st.columns(2)
                with left:
                    st.markdown("**中文整理**")
                    st.markdown(pair["cn"])
                with right:
                    st.markdown("**English**")
                    st.markdown(pair["en"])
        _render_source_reference([source.label for source in st.session_state.sources.values()])
    st.download_button("Download guided reading Markdown", st.session_state.reading_markdown, "guided_translation.md", "text/markdown", use_container_width=True)


def render_quiz_section() -> None:
    if not st.session_state.quiz_markdown:
        return
    st.markdown('<section class="section-card"><div class="section-label">Practice</div><h2 class="section-title">English Quiz</h2></section>', unsafe_allow_html=True)
    items = st.session_state.quiz_items
    if not items:
        st.warning("Quiz was generated, but it could not be converted into interactive questions. You can still download the complete Quiz Markdown.")
        st.download_button("Download Quiz Markdown", st.session_state.quiz_markdown, "course_quiz.md", "text/markdown", use_container_width=True)
        return

    attempts = st.session_state.quiz_attempts
    for index, item in enumerate(items, start=1):
        with st.container(border=True):
            st.markdown(f"**Question {index}** · {item['question']}")
            options = [f"{letter}. {item['options'][letter]}" for letter in ("A", "B", "C", "D")]
            selected = st.radio("Your answer", options, index=None, key=f"quiz-answer-{index}", label_visibility="collapsed")
            check_col, answer_col, status_col = st.columns([0.26, 0.26, 0.48])
            with check_col:
                if st.button("Check", key=f"check-{index}"):
                    if selected:
                        attempts[index] = selected[0] == item["answer"]
                    else:
                        st.warning("Choose an answer before checking it.")
            with answer_col:
                if st.button("Show answer", key=f"reveal-{index}"):
                    st.session_state.quiz_revealed.add(index)
            with status_col:
                if index in attempts:
                    if attempts[index]:
                        st.success("Correct - mark this concept as understood below.")
                    else:
                        st.error("Not quite - review the explanation and consider saving it for later.")
            if index in st.session_state.quiz_revealed:
                st.info(f"Answer: {item['answer']}")
                for letter in ("A", "B", "C", "D"):
                    explanation = item["explanations"].get(letter, "Explanation was not returned for this option.")
                    st.markdown(f"- **{letter}.** {explanation}")
    if attempts:
        score = sum(attempts.values())
        st.caption(f"Checked answers: {score} correct out of {len(attempts)} attempted.")
    _render_source_reference([source.label for source in st.session_state.sources.values()])
    st.download_button("Download Quiz Markdown", st.session_state.quiz_markdown, "course_quiz.md", "text/markdown", use_container_width=True)


def render_learning_loop() -> None:
    if not any((st.session_state.summary_markdown, st.session_state.quiz_markdown, st.session_state.reading_markdown)):
        return
    st.markdown('<section class="section-card"><div class="section-label">Learning Loop</div><h2 class="section-title">Keep the next review visible</h2></section>', unsafe_allow_html=True)
    st.markdown('<section class="study-loop"><span class="study-step">Read</span><span class="study-step">Review</span><span class="study-step">Quiz</span><span class="study-step">Check mistakes</span><span class="study-step">Review again</span></section>', unsafe_allow_html=True)
    st.caption("These lightweight study markers are stored only in this session. The state shape is ready for future mastery, spaced-repetition and cross-lecture features.")
    record = st.session_state.learning_record
    left, middle, right = st.columns(3)
    with left:
        if st.button("Mark as understood", use_container_width=True):
            record["understood"].add("current_lecture")
            record["review_later"].discard("current_lecture")
            record["needs_practice"].discard("current_lecture")
    with middle:
        if st.button("Review later", use_container_width=True):
            record["review_later"].add("current_lecture")
            record["understood"].discard("current_lecture")
    with right:
        if st.button("Need more practice", use_container_width=True):
            record["needs_practice"].add("current_lecture")
            record["understood"].discard("current_lecture")
    if "current_lecture" in record["understood"]:
        st.success("Marked as understood for this session.")
    elif "current_lecture" in record["needs_practice"]:
        st.warning("Saved as needing more practice. Revisit the Quiz or regenerate a targeted set when module-level generation becomes available.")
    elif "current_lecture" in record["review_later"]:
        st.info("Saved for later review in this session.")


def render_debug_previews() -> None:
    if st.session_state.pdf_text_preview:
        with st.expander("Parsed slide text preview"):
            st.text_area("PDF text", st.session_state.pdf_text_preview[:5000], height=240, disabled=True)
    if st.session_state.transcript_text_preview:
        with st.expander("Parsed transcript preview"):
            st.text_area("Transcript text", st.session_state.transcript_text_preview[:5000], height=240, disabled=True)


def main() -> None:
    init_state()
    render_theme()
    render_sidebar()
    render_header()
    render_workspace_nav()
    render_composer_intro()

    st.markdown('<section class="input-stage">', unsafe_allow_html=True)
    upload_col1, upload_col2 = st.columns(2)
    with upload_col1:
        pdf_files = st.file_uploader("Add PDF slides", type=["pdf"], accept_multiple_files=True, help="Text-based PDFs work best. Scanned PDFs may be usable but can contain little extractable text.")
    with upload_col2:
        txt_files = st.file_uploader("Add TXT transcripts", type=["txt"], accept_multiple_files=True, help="UTF-8, UTF-8 with BOM, GB18030 and Big5 are supported.")
    course_name = st.text_input("Course name / lecture topic (optional)", placeholder="e.g. Project Management - Stakeholder Analysis")
    st.markdown("</section>", unsafe_allow_html=True)
    materials = sync_materials(pdf_files, txt_files)
    render_materials(materials)
    valid_materials = [material for material in materials if material.text]
    if valid_materials:
        st.session_state.pdf_text_preview = combine_materials(materials, "pdf")
        st.session_state.transcript_text_preview = combine_materials(materials, "txt")

    selected_tools = render_tool_picker()
    render_expectation(selected_tools, bool(valid_materials))
    action_col, reset_col = st.columns([0.76, 0.24])
    with action_col:
        generate_clicked = st.button("Generate selected study materials", type="primary", use_container_width=True, disabled=not selected_tools or not valid_materials)
    with reset_col:
        reset_clicked = st.button("Reset workspace", use_container_width=True)
    if reset_clicked:
        reset_state()
        st.rerun()
    if generate_clicked:
        _run_generation(selected_tools, materials, course_name.strip())

    render_learning_loop()
    render_summary_results(course_name.strip())
    render_reading_results()
    render_quiz_section()
    render_debug_previews()


if __name__ == "__main__":
    main()
