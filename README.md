# Course Summary App

一个使用 Streamlit、PyMuPDF 和 Google Generative AI SDK 构建的 AI 课程复习工作台。

## 功能

- 支持上传一个或多个 PDF 课件、TXT 字幕，或两者组合
- 对文字较少、图表主导或扫描版 PDF，最多挑选 4 页图像内容交由 DeepSeek 视觉模型补充理解；不会把整份课件无差别转图上传
- 在生成前显示每份材料的真实解析状态、页数、提取字符数与扫描版 PDF 风险提示
- 以阶段式状态呈现真实流程：读取材料、确认解析、组织知识、生成学习材料、完成结果；不显示虚构百分比
- 可组合生成课程总结、英文 Quiz、精读翻译稿，并在生成前明确展示预期输出
- 将课程总结拆分为 Overview、Learning Objectives、Key Concepts、Key Terms、Lecture Highlights、Professor Emphasis、Examples from Lecture、Possible Exam Focus 与 Key Takeaways
- Quiz 支持逐题作答、检查答案、显示答案与解析
- 精读翻译稿以中英并列阅读卡展示
- 结果模块提供编辑、复制及为未来局部再生成预留的交互入口；当前后端仍只支持整节课生成
- 来源 UI 只显示真实可用的 Slides / Lecture transcript 与原始片段；未生成精确页码或时间戳时会明确说明
- 轻量学习标记（understood / review later / need more practice）保存在当前 Streamlit 会话，无需数据库
- 支持将课程总结导出为 Markdown 或 PDF

## 项目结构

```text
.
├── app.py
├── requirements.txt
├── .env.example
├── README.md
└── src
    ├── __init__.py
    ├── exporter.py
    ├── parser.py
    ├── prompts.py
    └── summarizer.py
    └── workspace.py
```

## 安装

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

在 `.env` 中选择一个生成服务，并填写它对应的 Key。默认仍为 Gemini；DeepSeek 通过 OpenAI-compatible API 接入。

```dotenv
AI_PROVIDER=deepseek
DEEPSEEK_API_KEY=your_deepseek_api_key_here
DEEPSEEK_MODEL=deepseek-v4-flash
DEEPSEEK_VISION_MODEL=deepseek-v4-flash-vision-exp
```

也可使用 `AI_PROVIDER=gemini` + `GOOGLE_API_KEY`，或 `AI_PROVIDER=openai` + `OPENAI_API_KEY`。完整示例见 [`.env.example`](.env.example)。

## 运行

```bash
streamlit run app.py
```

本地启动后通常访问：

- `http://localhost:8501`

## 学习工作流

1. 导入 PDF / TXT，并检查每份文件的解析状态
2. 选择一个或多个学习方式，并确认将获得的输出
3. 生成结构化学习内容
4. 在模块级别阅读、编辑或复制结果；查看可用的原始材料上下文
5. 完成 Quiz 后记录是否需要再次复习

## 输出要求

- 使用中文总结
- 关键专业词汇保持 `英文原文 (中文翻译)` 格式
- 课程总结分为 Overview、Learning Objectives、Key Concepts、Key Terms、Lecture Highlights、Professor Emphasis、Examples from Lecture、Possible Exam Focus 与 Key Takeaways
- 教授强调、课堂案例和“可能的考试重点”只在上传材料提供实际依据时显示；不会把模型推测写成讲授事实或考试承诺
- `SourceReference` 已预留 `source_type`、`page`、`timestamp` 与 `excerpt` 字段；精确 PDF 页码与字幕时间戳尚未在模型输出中生成，因此来源组件以真实材料类型与原文片段作为安全回退
- 支持下载 Markdown 与总结 PDF

## 部署到公网

推荐使用 Streamlit Community Cloud，和当前技术栈最匹配。

### 1. 推送代码到 GitHub

把当前项目上传到一个 GitHub 仓库，确保至少包含这些文件：

- `app.py`
- `requirements.txt`
- `src/`

不要把 `.env` 提交到仓库。

### 2. 在 Streamlit Community Cloud 创建应用

打开 [Streamlit Community Cloud](https://share.streamlit.io/) ，选择你的 GitHub 仓库，然后配置：

- Repository：你的 GitHub 仓库
- Branch：通常为 `main`
- Main file path：`app.py`

### 3. 配置密钥

在部署页面的 `Advanced settings` 里添加 Secrets：

```toml
# Gemini（默认）
AI_PROVIDER="gemini"
GOOGLE_API_KEY="你的_google_api_key"
GEMINI_MODEL="gemini-2.5-flash-lite"

# 或 DeepSeek
# AI_PROVIDER="deepseek"
# DEEPSEEK_API_KEY="你的_deepseek_api_key"
# DEEPSEEK_MODEL="deepseek-v4-flash"
# DEEPSEEK_VISION_MODEL="deepseek-v4-flash-vision-exp"

# 或 OpenAI
# AI_PROVIDER="openai"
# OPENAI_API_KEY="你的_openai_api_key"
# OPENAI_MODEL="gpt-4.1-mini"
```

### 4. 部署完成后分享链接

部署成功后，你会拿到一个 `https://xxxx.streamlit.app` 的公网地址，可以直接发给朋友使用。

## 参考资料

- [Streamlit Community Cloud 部署文档](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
- [Streamlit Secrets 管理文档](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management)
