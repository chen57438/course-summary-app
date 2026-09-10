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
    describe_pdf_visuals,
    generate_quiz_material,
    generate_reading_guide_material,
    summarize_course_material,
)
from src.workspace import SourceReference, collect_visual_pages, combine_materials, expected_outputs, parse_summary_sections, source_registry


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
            content: "学习";
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
            <div class="eyebrow">课程学习工作台</div>
            <h1 class="hero-title">课程总结生成器</h1>
            <p class="hero-subtitle">
                把课件、字幕和课堂材料整理成更可读、更可复习的输出。
                它应该像一张有呼吸感的工作台，而不是一张死板的表格。
            </p>
            <div class="note-grid">
                <div class="note-chip">
                    <strong>结构化笔记</strong>
                    结构化中文总结，强调知识框架、案例与重点术语。
                </div>
                <div class="note-chip">
                    <strong>随时自测</strong>
                    可选生成英文单选题，适合课后练习与教学评估。
                </div>
                <div class="note-chip">
                    <strong>导出与归档</strong>
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
                <div class="panel-kicker">导入材料</div>
                <h2 class="panel-title">上传材料，生成可直接复习与分发的课程内容</h2>
                <p class="panel-copy">
                    你可以上传 PDF、TXT，或者两者一起。系统会自动提炼知识结构、教授强调、术语框架与练习题，
                    同时兼容纯中文文档、中英混合讲义和常见课程字幕。
                </p>
            </div>
            <aside class="side-note-panel">
                <div class="panel-kicker">支持能力</div>
                <h3 class="panel-title">当前支持的工作流</h3>
                <ul class="micro-list">
                    <li>纯中文课件与字幕总结</li>
                    <li>中英混合管理课程资料整理</li>
                    <li>课程总结与英文测验一体化复习</li>
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
            <div class="panel-kicker">学习方式</div>
            <h2 class="panel-title">三个主功能并列放在输入区下面，上传后立刻启动</h2>
            <p class="action-copy">
                课程总结、英文 Quiz 和精读翻译稿现在是三个独立入口。
                你可以只触发其中一个功能，不需要再把 Quiz 或翻译当作附带选项。
            </p>
            <div class="action-pills">
                <span class="action-pill">课程总结</span>
                <span class="action-pill">英文测验</span>
                <span class="action-pill">精读翻译</span>
                <span class="action-pill">重置</span>
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
    st.sidebar.title("课程学习工作台")
    st.sidebar.markdown("导入材料、选择学习方式，再把结果转成可复习的学习资产。")
    st.sidebar.divider()
    st.sidebar.markdown("**使用流程**")
    st.sidebar.markdown("1. 导入课件或字幕\n2. 确认解析状态\n3. 选择学习方式\n4. 阅读、练习与复习")
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
            <strong>学习闭环</strong><span class="nav-arrow">→</span>
            <span>阅读</span><span class="nav-arrow">→</span><span>复习</span>
            <span class="nav-arrow">→</span><span>测验</span><span class="nav-arrow">→</span>
            <span>查看错题</span><span class="nav-arrow">→</span><span>再次复习</span>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_material_card(material: ParsedMaterial) -> None:
    class_name = ""
    if material.status == "警告":
        class_name = " warning"
    elif material.status == "失败":
        class_name = " failed"
    badge_class = ""
    if material.status == "警告":
        badge_class = " warning"
    elif material.status == "失败":
        badge_class = " failed"
    metadata = ["PDF 课件" if material.kind == "pdf" else "TXT 课堂字幕"]
    if material.page_count is not None:
        metadata.append(f"{material.page_count} 页")
    if material.char_count:
        metadata.append(f"已提取 {material.char_count:,} 个字符")
    if material.visual_pages:
        metadata.append(f"已保留 {len(material.visual_pages)} 页图片")
    st.markdown(
        f"""
        <section class="material-card{class_name}">
            <div class="status-kicker">材料</div>
            <h3 class="material-title">{html.escape(material.name)}</h3>
            <span class="status-badge{badge_class}">{html.escape(material.status)}</span>
            <p class="material-meta">{' · '.join(metadata)}</p>
            <p class="material-meta">{html.escape(material.message)}</p>
            {f'<p class="material-meta"><strong>提示：</strong> {html.escape(material.warning)}</p>' if material.warning else ''}
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_materials(materials: list[ParsedMaterial]) -> None:
    st.markdown("### 材料")
    if not materials:
        st.info("请先上传至少一份 PDF 课件或 TXT 课堂字幕。两种材料都支持多文件上传。")
        return
    for material in materials:
        render_material_card(material)
    if any(material.status == "失败" for material in materials):
        st.warning("解析失败的文件不会参与生成。你可以删除后重新上传，不会影响其他已成功解析的材料。")


TOOL_CONFIG = {
    "summary": {
        "title": "课程总结",
        "class_name": "summary",
        "fit": "适合：考试复习、快速掌握整节课",
        "output": "输出：章节结构、重点知识、核心术语、教授强调内容",
    },
    "quiz": {
        "title": "英文测验",
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
    st.markdown("### 学习工具")
    st.caption("可选择一种或组合多种学习方式。选择只影响生成结果，不会改动你上传的材料。")
    selected: list[str] = []
    columns = st.columns(3)
    for column, (key, config) in zip(columns, TOOL_CONFIG.items()):
        with column:
            st.markdown(
                f"""
                <section class="tool-card {config['class_name']}">
                    <div class="tool-eyebrow">学习方式</div>
                    <h3 class="tool-title">{config['title']}</h3>
                    <p class="tool-copy">{config['fit']}</p>
                    <p class="tool-output">{config['output']}</p>
                </section>
                """,
                unsafe_allow_html=True,
            )
            if st.checkbox(f"选择{config['title']}", key=f"select_{key}"):
                selected.append(key)
    return selected


def render_expectation(selected_tools: list[str], has_valid_material: bool) -> None:
    st.markdown('<section class="expectation-panel">', unsafe_allow_html=True)
    if not selected_tools:
        st.markdown("**请选择学习方式，查看将获得的结果。**")
        st.caption("你可以只专注一种任务，也可以组合成完整复习流程。")
    else:
        labels = " + ".join(TOOL_CONFIG[tool]["title"] for tool in selected_tools)
        st.markdown(f"**你选择了：{labels}**")
        st.markdown("**你将获得：**")
        for item in expected_outputs(selected_tools):
            st.markdown(f"- {item}")
        if not has_valid_material:
            st.caption("请先上传可读取的 PDF 或 TXT 文件，再开始生成。")
    st.markdown("</section>", unsafe_allow_html=True)


def _run_generation(selected_tools: list[str], materials: list[ParsedMaterial], course_name: str) -> None:
    pdf_text = combine_materials(materials, "pdf")
    transcript_text = combine_materials(materials, "txt")
    visual_pages = collect_visual_pages(materials)
    if not pdf_text and not transcript_text and not visual_pages:
        st.error("上传材料中没有可读取的文字或图像页面。请确认 PDF 不是损坏文件，或重新上传 UTF-8 编码的 TXT。")
        return

    with st.status("正在准备学习材料", expanded=True) as status:
        status.write("1. 正在读取材料")
        status.write("2. 正在确认已解析的课程内容")

        def update_stage(stage: str) -> None:
            status.write(f"• {stage}")
            status.update(label=stage, state="running")

        try:
            visual_context = ""
            if visual_pages:
                status.write(f"3. 正在分析 {len(visual_pages)} 页图表、扫描页或图片文字")
                visual_context = describe_pdf_visuals(visual_pages, on_stage=update_stage)
            for tool in selected_tools:
                if tool == "summary":
                    result = summarize_course_material(pdf_text, transcript_text, course_name, visual_context=visual_context, on_stage=update_stage)
                    st.session_state.summary_markdown = result
                    st.session_state.bilingual_pairs = parse_bilingual_pairs(result)
                    st.session_state.summary_overrides = {}
                elif tool == "quiz":
                    result = generate_quiz_material(pdf_text, transcript_text, course_name, visual_context=visual_context, on_stage=update_stage)
                    st.session_state.quiz_markdown = result
                    st.session_state.quiz_items = parse_quiz_markdown(result)
                    st.session_state.quiz_revealed = set()
                    st.session_state.quiz_attempts = {}
                elif tool == "reading":
                    result = generate_reading_guide_material(pdf_text, transcript_text, course_name, visual_context=visual_context, on_stage=update_stage)
                    st.session_state.reading_markdown = result
            status.update(label="学习材料已生成", state="complete", expanded=False)
        except ValueError as exc:
            status.update(label="生成未能完成", state="error")
            st.error(f"生成失败。已上传的文件仍保留在当前页面。{exc}")
        except Exception:  # noqa: BLE001 - detailed error stays out of the student UI
            status.update(label="生成未能完成", state="error")
            st.error("生成失败。已上传的文件仍保留在当前页面，请稍后重试。")


def _copy_button(value: str, key: str) -> None:
    safe_value = json.dumps(value).replace("</", "<\\/")
    components.html(
        f"""<button id=\"{key}\" style=\"border:1px solid #ead7cb;border-radius:10px;background:#fffaf6;color:#4a3025;padding:8px 11px;cursor:pointer;font:600 13px system-ui\">复制</button>
        <script>document.getElementById({json.dumps(key)}).onclick = async () => {{ await navigator.clipboard.writeText({safe_value}); document.getElementById({json.dumps(key)}).textContent = '已复制'; }};</script>""",
        height=42,
    )


def _render_source_reference(source_labels: list[str]) -> None:
    if not source_labels:
        return
    labels = " · ".join(source_labels)
    st.markdown(f'<div class="source-note"><span class="source-badge">来源</span><strong>{html.escape(labels)}</strong><p>下方可查看材料原文片段。当前结果没有精确页码或时间戳，因此不会显示虚假定位。</p></div>', unsafe_allow_html=True)
    sources = st.session_state.sources
    for source in sources.values():
        if isinstance(source, SourceReference) and source.label in source_labels:
            with st.expander(f"查看原文片段 · {source.label}"):
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
    st.markdown('<section class="section-card"><div class="section-label">学习结果</div><h2 class="section-title">课程总结</h2></section>', unsafe_allow_html=True)
    st.caption("每个部分均可单独阅读、复制或编辑，不会影响其他学习内容。")
    sections = parse_summary_sections(st.session_state.summary_markdown, st.session_state.sources)
    if not sections:
        st.warning("总结已生成，但暂时无法识别结构。你仍可在下方下载原始 Markdown。")
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
                    st.caption("来源：" + " · ".join(section.source_labels))
            with action_col:
                edit_col, regen_col, copy_col = st.columns(3)
                with edit_col:
                    if st.button("编辑", key=f"edit-{section_id}"):
                        st.session_state.editing_section = section_id
                with regen_col:
                    if st.button("重新生成", key=f"regen-{section_id}"):
                        st.info("已为模块级生成预留入口。当前后端只支持整节课生成，因此此操作不会悄悄覆盖你的其他笔记。")
                with copy_col:
                    _copy_button(content, f"copy-{section_id}")

            if st.session_state.editing_section == section_id:
                draft = st.text_area("编辑此学习模块", value=content, height=220, key=f"draft-{section_id}")
                save_col, cancel_col = st.columns(2)
                with save_col:
                    if st.button("保存模块", key=f"save-{section_id}", type="primary"):
                        st.session_state.summary_overrides[section_id] = draft.strip()
                        st.session_state.editing_section = ""
                        st.rerun()
                with cancel_col:
                    if st.button("取消", key=f"cancel-{section_id}"):
                        st.session_state.editing_section = ""
                        st.rerun()
            else:
                st.markdown(content)
            _render_source_reference(section.source_labels)

    exported_summary = _materialize_summary()
    pdf_bytes = build_summary_pdf(exported_summary, course_name or "课程总结")
    download_col1, download_col2 = st.columns(2)
    with download_col1:
        st.download_button("下载 Markdown", exported_summary, "课程总结.md", "text/markdown", use_container_width=True)
    with download_col2:
        st.download_button("下载 PDF", pdf_bytes, "课程总结.pdf", "application/pdf", use_container_width=True)


def render_reading_results() -> None:
    if not st.session_state.reading_markdown:
        return
    st.markdown('<section class="section-card"><div class="section-label">精读</div><h2 class="section-title">精读翻译稿</h2></section>', unsafe_allow_html=True)
    pairs = parse_bilingual_pairs(st.session_state.reading_markdown)
    if not pairs:
        st.markdown(st.session_state.reading_markdown)
    else:
        st.caption("中英文对照阅读，核心术语会保留在原本的上下文中。")
        for index, pair in enumerate(pairs, start=1):
            with st.container(border=True):
                st.caption(f"第 {index:02d} 部分 · {pair['section'] or '精读内容'}")
                left, right = st.columns(2)
                with left:
                    st.markdown("**中文整理**")
                    st.markdown(pair["cn"])
                with right:
                    st.markdown("**English**")
                    st.markdown(pair["en"])
        _render_source_reference([source.label for source in st.session_state.sources.values()])
    st.download_button("下载精读翻译 Markdown", st.session_state.reading_markdown, "精读翻译稿.md", "text/markdown", use_container_width=True)


def render_quiz_section() -> None:
    if not st.session_state.quiz_markdown:
        return
    st.markdown('<section class="section-card"><div class="section-label">练习</div><h2 class="section-title">英文测验</h2></section>', unsafe_allow_html=True)
    items = st.session_state.quiz_items
    if not items:
        st.warning("测验已生成，但暂时无法转为交互题目。你仍可下载完整的测验 Markdown。")
        st.download_button("下载测验 Markdown", st.session_state.quiz_markdown, "英文测验.md", "text/markdown", use_container_width=True)
        return

    attempts = st.session_state.quiz_attempts
    for index, item in enumerate(items, start=1):
        with st.container(border=True):
            st.markdown(f"**第 {index} 题** · {item['question']}")
            options = [f"{letter}. {item['options'][letter]}" for letter in ("A", "B", "C", "D")]
            selected = st.radio("你的答案", options, index=None, key=f"quiz-answer-{index}", label_visibility="collapsed")
            check_col, answer_col, status_col = st.columns([0.26, 0.26, 0.48])
            with check_col:
                if st.button("检查答案", key=f"check-{index}"):
                    if selected:
                        attempts[index] = selected[0] == item["answer"]
                    else:
                        st.warning("请先选择一个答案。")
            with answer_col:
                if st.button("显示答案", key=f"reveal-{index}"):
                    st.session_state.quiz_revealed.add(index)
            with status_col:
                if index in attempts:
                    if attempts[index]:
                        st.success("回答正确，可以在下方标记为已掌握。")
                    else:
                        st.error("还差一点，建议阅读解析并标记为稍后复习。")
            if index in st.session_state.quiz_revealed:
                st.info(f"答案：{item['answer']}")
                for letter in ("A", "B", "C", "D"):
                    explanation = item["explanations"].get(letter, "此选项暂未返回解析。")
                    st.markdown(f"- **{letter}.** {explanation}")
    if attempts:
        score = sum(attempts.values())
        st.caption(f"已检查 {len(attempts)} 题，其中答对 {score} 题。")
    _render_source_reference([source.label for source in st.session_state.sources.values()])
    st.download_button("下载测验 Markdown", st.session_state.quiz_markdown, "英文测验.md", "text/markdown", use_container_width=True)


def render_learning_loop() -> None:
    if not any((st.session_state.summary_markdown, st.session_state.quiz_markdown, st.session_state.reading_markdown)):
        return
    st.markdown('<section class="section-card"><div class="section-label">学习闭环</div><h2 class="section-title">安排下一次复习</h2></section>', unsafe_allow_html=True)
    st.markdown('<section class="study-loop"><span class="study-step">阅读</span><span class="study-step">复习</span><span class="study-step">测验</span><span class="study-step">查看错题</span><span class="study-step">再次复习</span></section>', unsafe_allow_html=True)
    st.caption("这些轻量标记只保存在当前会话，未来可自然扩展为掌握度、间隔复习和跨课程关联。")
    record = st.session_state.learning_record
    left, middle, right = st.columns(3)
    with left:
        if st.button("标记为已掌握", use_container_width=True):
            record["understood"].add("current_lecture")
            record["review_later"].discard("current_lecture")
            record["needs_practice"].discard("current_lecture")
    with middle:
        if st.button("稍后复习", use_container_width=True):
            record["review_later"].add("current_lecture")
            record["understood"].discard("current_lecture")
    with right:
        if st.button("需要更多练习", use_container_width=True):
            record["needs_practice"].add("current_lecture")
            record["understood"].discard("current_lecture")
    if "current_lecture" in record["understood"]:
        st.success("已在当前会话中标记为已掌握。")
    elif "current_lecture" in record["needs_practice"]:
        st.warning("已标记为需要更多练习。可重新做测验，或在未来模块级生成可用后生成针对性练习。")
    elif "current_lecture" in record["review_later"]:
        st.info("已在当前会话中标记为稍后复习。")


def render_debug_previews() -> None:
    if st.session_state.pdf_text_preview:
        with st.expander("查看已解析的课件文字"):
            st.text_area("PDF 文字", st.session_state.pdf_text_preview[:5000], height=240, disabled=True)
    if st.session_state.transcript_text_preview:
        with st.expander("查看已解析的课堂字幕"):
            st.text_area("课堂字幕文字", st.session_state.transcript_text_preview[:5000], height=240, disabled=True)


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
        pdf_files = st.file_uploader("添加 PDF 课件", type=["pdf"], accept_multiple_files=True, help="可提取文字的 PDF 效果最佳。扫描版、图表和图片文字会在检测到时交给视觉模型补充理解。")
    with upload_col2:
        txt_files = st.file_uploader("添加 TXT 课堂字幕", type=["txt"], accept_multiple_files=True, help="支持 UTF-8、UTF-8 with BOM、GB18030 和 Big5 编码。")
    course_name = st.text_input("课程名称 / 讲座主题（可选）", placeholder="例如：项目管理——利益相关者分析")
    st.markdown("</section>", unsafe_allow_html=True)
    materials = sync_materials(pdf_files, txt_files)
    render_materials(materials)
    valid_materials = [material for material in materials if material.text or material.visual_pages]
    if valid_materials:
        st.session_state.pdf_text_preview = combine_materials(materials, "pdf")
        st.session_state.transcript_text_preview = combine_materials(materials, "txt")

    selected_tools = render_tool_picker()
    render_expectation(selected_tools, bool(valid_materials))
    action_col, reset_col = st.columns([0.76, 0.24])
    with action_col:
        generate_clicked = st.button("生成已选学习材料", type="primary", use_container_width=True, disabled=not selected_tools or not valid_materials)
    with reset_col:
        reset_clicked = st.button("重置工作台", use_container_width=True)
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
