# Course Summary App

一个使用 Streamlit、PyMuPDF 和 Google Generative AI SDK 的课程总结小工具。

## 功能

- 上传 PDF 课件与 TXT 字幕
- 提取并合并课件文本与讲课内容
- 调用 Gemini 生成中文课程总结
- 强制关键术语使用 `英文原文 (中文翻译)` 格式
- 支持将生成结果导出为 PDF

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
```

## 安装

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

在 `.env` 中填写 `GOOGLE_API_KEY`。

## 运行

```bash
streamlit run app.py
```

本地启动后通常访问：

- `http://localhost:8501`

## 输出要求

- 使用中文总结
- 关键专业词汇保持 `英文原文 (中文翻译)` 格式
- 输出分为：
  - 核心概念
  - 教授强调的重点
  - 课件与讲稿补充点
- 支持在页面中一键下载总结 PDF

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
GOOGLE_API_KEY="你的_google_api_key"
```

### 4. 部署完成后分享链接

部署成功后，你会拿到一个 `https://xxxx.streamlit.app` 的公网地址，可以直接发给朋友使用。

## 参考资料

- [Streamlit Community Cloud 部署文档](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy)
- [Streamlit Secrets 管理文档](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management)
