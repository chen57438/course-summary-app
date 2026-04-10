from __future__ import annotations


def build_summary_prompt(pdf_text: str, transcript_text: str, course_name: str = "") -> str:
    course_line = f"补充课程名称或主题：{course_name}\n" if course_name else ""
    pdf_section = pdf_text if pdf_text.strip() else "未提供 PDF 课件内容。"
    transcript_section = transcript_text if transcript_text.strip() else "未提供 TXT 字幕内容。"

    return f"""
# Role
你是一位拥有 PMP 认证和丰富教学经验的“项目管理”专业助教。你擅长将复杂的英文学术讲座转化为条理清晰、中英双语对照的学习笔记。

# Input Data
1. 【课件内容 (PDF)】: {pdf_section} (这是课程的骨架和视觉重点)
2. 【讲稿字幕 (TXT)】: {transcript_section} (这是教授口述的细节、案例和解释)

# Task
请根据已提供的材料生成总结：如果同时有课件和讲稿，就做融合总结；如果只提供其中一种材料，就基于该材料独立总结核心知识点。你的目标是让学生即便没看视频，也能掌握本节课的核心知识。
请把输出写成“高质量课程讲义式笔记”，而不是简短摘要。

# Constraint & Style (极其重要)
1. 语言逻辑：使用专业、简洁的中文进行总结。
2. 术语处理（中英对照）：
   - 所有的专业术语、核心框架、管理概念、以及关键动作词，必须保留“英文原文 (中文翻译)”的格式。
   - 示例：Critical Path Method (关键路径法)、Stakeholder Engagement (相关方参与)、Baseline (基准)。
   - 非专业词汇直接用中文，保持阅读流畅，不要全篇中英夹杂。
3. 结构化输出：使用 Markdown 标题、列表和表格，增加可读性。
4. 请优先整合：
   - 课件中的定义、框架、流程、视觉重点
   - 教授在字幕中补充的解释、案例、提醒、考试导向
5. 如果课件与讲稿信息存在补充、细化或轻微差异，请显式指出，不要简单重复。
6. 避免输出空泛结论；每个模块都要尽量体现“概念是什么、为什么重要、如何应用”。
7. “核心知识点”部分必须充分展开，不要只写简短提纲。
8. 对每个核心模块，尽量覆盖：
   - 概念定义
   - 为什么重要
   - 教授给出的案例、类比或应用场景
   - 容易混淆的点或考试提醒
9. 如果材料足够，请输出 4-8 个核心知识模块，而不是只列出 1-2 个大点。
10. 对每个核心模块，至少写 3 个以上有信息量的子要点，避免空泛句子。
11. 输出风格应接近“可直接复习的学习讲义”：
   - 每个模块先给出结论性标题
   - 再展开解释
   - 再补教授案例、提醒或类比
12. 优先保留教授在讲稿里对概念的口头解释，因为这通常比课件标题更有学习价值。
13. 如果课件只是列提纲，而教授补充了具体情境、案例或误区，请优先写教授补充内容。
14. 如果只提供一种材料，不要提及缺失材料，也不要假装引用另一种材料。

# Output Schema
请严格按以下结构输出：

## 📌 课程概览 (Executive Summary)
[用 3-5 句话总结本节课的核心主题和目标]

## 💡 核心知识点 (Key Knowledge Points)
[按逻辑模块排列，结合课件的结构和教授的解释]
- **模块名称 (英文原文)**：
  * 详细解释（记得应用中英对照规则）。
  * 为什么这个模块重要。
  * 教授提到的重点/案例/类比/应用提醒。
  * 如果有，补充常见误区、考试关注点或与其他概念的区别。
  * 如果教授有举例，请尽量展开到学生一看就能理解的程度。

## 🎓 教授的“金句”与强调 (Professor's Insights)
[提取讲稿中教授反复强调、课件上可能没有的实战经验、考试提醒或逻辑洞察]
- 请优先提炼那些“教授特意提醒学生不要犯错”或“教授用案例反复说明”的内容。

## 📋 专业词汇表 (Bilingual Glossary)
| 英文术语 | 中文翻译 | 上下文含义简述 |
| :--- | :--- | :--- |
| (例) Work Breakdown Structure | 工作分解结构 | 将项目团队工作分解为较小、更易管理的部分 |

## 🧩 课件与讲稿补充点 (Slides vs. Transcript Additions)
[说明哪些点主要来自课件，哪些点主要来自教授口述，哪些是两者互补后的结论]

# Additional Notes
- 如果课程名称可推断，请自然融入总结开头；如果无法判断，则不要编造。
- 如果材料不足以支持某个结论，请谨慎表述，例如使用“根据课件可推测”。
- 专业词汇表请优先收录本次课程中真正关键、重复出现或容易考核的术语，尽量给出 10-20 个词。
- 不要输出“我无法访问视频”等元信息。
- 不要把输出写成非常短的摘要；除非输入材料本身非常少，否则应尽量写得充实、便于复习。

{course_line}

# Execution
现在，请开始分析上方提供的数据。
""".strip()


def build_quiz_prompt(pdf_text: str, transcript_text: str, course_name: str = "") -> str:
    course_line = f"Course name or topic: {course_name}\n" if course_name else ""
    pdf_section = pdf_text if pdf_text.strip() else "No PDF slide content was provided."
    transcript_section = transcript_text if transcript_text.strip() else "No TXT transcript content was provided."

    return f"""
# Role
You are an experienced university teaching assistant in project management. Your task is to create a high-quality multiple-choice quiz in English based on the lecture slides and lecture transcript.

# Input Data
1. Slides content: {pdf_section}
2. Transcript content: {transcript_section}

# Task
Create an English-only single-choice quiz that helps students review the lecture. If both sources are provided, combine them. If only one source is provided, generate the quiz based only on that source.

# Requirements
1. The entire quiz must be in English.
2. Each question must have exactly 4 options: A, B, C, D.
3. Only one option can be correct.
4. Focus on meaningful understanding, not trivial wording details.
5. Prioritize:
   - key concepts and definitions
   - differences between similar ideas
   - frameworks, processes, and terms
   - examples mentioned by the professor
   - common mistakes or exam-style traps
6. Questions should be clear, concise, and academically useful.
7. Avoid duplicate questions.
8. Create 8-12 questions if the material supports it.
9. Do not mention missing sources in the output.

# Output Format
Return the quiz in Markdown using exactly this structure:

## Quiz

1. Question text
   - A. Option A
   - B. Option B
   - C. Option C
   - D. Option D
   - Answer: B
   - Explanation: Short explanation in English.

Repeat the same format for all questions.

{course_line}

# Execution
Now generate the quiz.
""".strip()
