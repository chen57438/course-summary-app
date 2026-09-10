from __future__ import annotations


def build_summary_prompt(
    pdf_text: str,
    transcript_text: str,
    course_name: str = "",
    transcript_study_view: str = "",
    transcript_topic_map: str = "",
) -> str:
    course_line = f"补充课程名称或主题：{course_name}\n" if course_name else ""
    pdf_section = pdf_text if pdf_text.strip() else "未提供 PDF 课件内容。"
    transcript_section = transcript_text if transcript_text.strip() else "未提供 TXT 字幕内容。"
    study_view_section = transcript_study_view if transcript_study_view.strip() else "未提供处理后的字幕精读视图。"
    topic_map_section = transcript_topic_map if transcript_topic_map.strip() else "未提供字幕主题梳理。"

    return f"""
# Role
你是一位拥有 PMP 认证和丰富教学经验的“项目管理”专业助教。你擅长将复杂的课程材料，无论是英文学术讲座、双语资料，还是纯中文讲义，转化为条理清晰、适合复习的学习笔记。

# Input Data
1. 【课件内容 (PDF)】: {pdf_section} (这是课程的骨架和视觉重点)
2. 【讲稿字幕 (TXT)】: {transcript_section} (这是教授口述的细节、案例和解释)
3. 【字幕精读视图】: {study_view_section} (这是去掉明显口头噪音后，保留教学内容的字幕版本)
4. 【字幕主题梳理】: {topic_map_section} (这是根据字幕内容抽出的主题线索)

# Task
请根据已提供的材料生成总结：如果同时有课件和讲稿，就做有层次的融合总结；如果只提供其中一种材料，就基于该材料独立总结核心知识点。你的目标是让学生即便没看视频，也能掌握本节课的核心知识。
请把输出写成“高质量课程讲义式备考笔记”，而不是简短摘要。

# Constraint & Style (极其重要)
1. 语言逻辑：使用专业、简洁的中文进行总结。
2. 术语处理（中英对照）：
   - 如果材料中出现了明确的英文专业术语，或该术语在项目管理中有广泛使用的标准英文表达，则使用“英文原文 (中文翻译)”格式。
   - 示例：Critical Path Method (关键路径法)、Stakeholder Engagement (相关方参与)、Baseline (基准)。
   - 如果材料本身是纯中文，且没有可靠、自然的标准英文对应，不要生硬补英文；此时直接用自然中文表达即可。
   - 非专业词汇直接用中文，保持阅读流畅，不要全篇中英夹杂。
3. 结构化输出：使用 Markdown 标题、列表和表格，增加可读性。
4. 请优先整合：
   - 先以课件中的定义、框架、流程与视觉重点建立课程结构
   - 再用字幕补充教授解释、案例、提醒，以及课件没有展开的细节
   - 不要把两份材料简单拼接或重复改写；同一概念先说明课件骨架，再只写字幕新增信息
5. 如果课件与讲稿信息存在补充、细化或轻微差异，请在相关模块中清楚区分“课件内容”和“课堂补充”，不要简单重复。
6. 避免输出空泛结论；每个模块都要尽量体现“概念是什么、为什么重要、如何应用”。
7. “核心知识点”部分必须充分展开，不要只写简短提纲。
8. 对每个核心模块，尽量覆盖：
   - 概念定义
   - 为什么重要
   - 教授给出的案例、类比或应用场景
   - 容易混淆的点或考试提醒
9. 如果材料足够，请输出 6-10 个核心知识模块，而不是只列出 1-2 个大点。
10. 对每个核心模块，至少写 4 个以上有信息量的子要点，避免空泛句子。
11. 输出风格应接近“可直接复习的学习讲义”：
   - 每个模块先给出结论性标题
   - 再展开解释
   - 再补教授案例、提醒或类比
12. 只有当字幕中有明确依据（例如重复强调、提醒、对比、举例、或直接说明考试/作业）时，才可写成教授强调或课堂案例；不能把模型推测写成教授观点。
13. 如果课件只是列提纲，而教授补充了具体情境、案例或误区，请在保留课件结构的前提下，补充这些课堂信息。
14. 如果只提供一种材料，不要提及缺失材料，也不要假装引用另一种材料。
15. 如果输入材料是纯中文，请保持总结自然、准确、流畅，不要为了形式强行制造英文术语。
16. 请面向“做 quiz 备考”来写，重点补足以下信息：
   - 容易被拿来出题的定义
   - 相似概念之间的区别
   - 题干中的识别线索
   - 错误选项为什么错
   - 场景题中应如何判断
17. 不要只写宏观主题，必须尽量把知识拆到可以支持单选题判断的粒度。
18. 如果输入里同时提供了“字幕精读视图”或“字幕主题梳理”，请优先利用它们重建教学逻辑；不要被原始字幕中的寒暄、通知、重复口头语带偏。
19. 输出风格要更像“经过编辑整理的课堂讲义”，而不是“从头到尾压缩后的摘要”。
20. 请主动重建课程逻辑层次，例如：
   - 课程复盘 / 本节任务
   - 关键概念与流程
   - 国际项目中的新增维度
   - 教授特别强调的误区、应用与提醒

# Output Schema
请严格按下列二级标题输出，方便学习工作台拆分为可单独阅读、编辑和复习的模块。没有足够材料支撑时请简短说明，不要编造。

## Overview
本节课的核心主题、解决的问题与一段简洁中文概览。

## Learning Objectives
列出学生完成本节后应能理解、比较或应用的 3-5 项能力。

## Key Concepts
按逻辑模块展开核心概念。每个模块用三级标题；用中文解释“是什么、为什么重要、如何应用”，并在有可靠原文时保留关键英文术语（中文）。

## Key Terms
用 Markdown 表格列出真正关键、重复出现或容易考核的英文术语、中文翻译及简短上下文解释。

## Lecture Highlights
简要说明课件与字幕各自为本节课补充了什么，以及学生阅读时应如何把两者结合。若只上传一种材料，只概括该材料的学习脉络。

## Professor Emphasis
只收录课堂字幕中可明确识别的教授强调、提醒、误区或对比。每一点应说明为何值得注意。若未提供字幕、或没有明确证据，请如实说明，不要虚构教授观点。

## Examples from Lecture
只收录上传材料中实际出现的案例、情境或类比，并说明它说明了什么概念。没有可核实案例时请如实说明，不要自行补造示例。

## Possible Exam Focus
仅列出材料中明确提到 quiz、assessment、exam、作业要求，或由反复定义/对比而具有直接复习价值的知识点。不要把模型自己的猜测表述成“教授说会考”；措辞使用“值得复习”而非不确定的考试承诺。

## Key Takeaways
说明课件与字幕如何互补，并用 3-5 条可立即复习的结论收束。若只有一种材料，明确这是基于已上传材料的结论即可。

# Additional Notes
- 如果课程名称可推断，请自然融入总结开头；如果无法判断，则不要编造。
- 如果材料不足以支持某个结论，请谨慎表述，例如使用“根据课件可推测”。
- 专业词汇表请优先收录本次课程中真正关键、重复出现或容易考核的术语，尽量给出 10-20 个词。
- 不要输出“我无法访问视频”等元信息。
- 不要把输出写成非常短的摘要；除非输入材料本身非常少，否则应尽量写得充实、便于复习。
- 在不编造内容的前提下，尽量让总结足够细，使学生可以据此准备课堂 quiz。
- 除“专业词汇表”外，其余结构请严格采用 `- CN:` 与下一行 `- EN:` 成对输出，方便做中英对照。

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
1. Slides content: {pdf_section} (use this as the course structure, definitions, frameworks and process reference)
2. Transcript content: {transcript_section} (use this only to supplement the slides with spoken explanations, examples, clarifications and explicitly stated emphasis)

# Task
Create an English-only single-choice quiz that helps students review the lecture. If both sources are provided, first anchor each question in the slide framework, then use transcript-only detail only when it genuinely adds an explanation, example or clarification. Do not create duplicate questions by rephrasing the same material from both inputs. If only one source is provided, generate the quiz based only on that source.

# Requirements
1. The entire quiz must be in English.
2. Each question must have exactly 4 options: A, B, C, D.
3. Only one option can be correct.
4. Write questions in a polished university quiz style, similar to project management course quizzes.
5. Prioritize:
   - key concepts and definitions
   - differences between similar ideas
   - frameworks, processes, and terms
   - examples mentioned by the professor, especially when they can be turned into concept-check questions
   - common mistakes or exam-style traps tied to the lecture content
6. Questions should feel like review questions for lecture knowledge, not generic reasoning puzzles.
7. Avoid duplicate questions.
8. Create 8-12 questions if the material supports it.
9. Do not mention missing sources in the output.
10. Prefer asking about:
   - what a concept means
   - why it matters
   - how it differs from another concept
   - what step belongs to which process
   - which example best illustrates a specific knowledge point
11. Prefer the following question style:
   - short scenario + concept judgment
   - applied definition question
   - process or framework identification
   - conflict between similar choices where only one is best according to the lecture
12. Distractors should be plausible and academically meaningful, not obviously wrong.
13. Avoid making every question purely factual; mix direct concept checks with light scenario-based application.
14. However, scenarios must still clearly test lecture knowledge points rather than broad common sense.
15. Do not claim that something was "emphasized by the professor" or "will be examined" unless the uploaded transcript explicitly says so.
16. Every explanation must explain why the correct option fits the uploaded material and why each distractor does not; do not use generic textbook explanations that are unsupported by the lecture.

# Output Format
Return the quiz in Markdown using exactly this structure:

## Quiz

1. Question text
   - A. Option A
   - B. Option B
   - C. Option C
   - D. Option D
   - Answer: B
   - Option Explanations:
     - A: Explanation for why A is correct or incorrect.
     - B: Explanation for why B is correct or incorrect.
     - C: Explanation for why C is correct or incorrect.
     - D: Explanation for why D is correct or incorrect.

Repeat the same format for all questions.

# Style Reference
The target feel is similar to questions such as:
- identifying why a project manager classifies stakeholders by influence
- recognizing the correct Tuckman stage from team behavior
- deciding the PM's first step when change requests appear late
- identifying the conflict management strategy used in a short scenario
- choosing the correct project document for a given contracting situation

Questions should feel like that: crisp, knowledge-based, lightly situational, and exam-ready.

{course_line}

# Execution
Now generate the quiz.
""".strip()


def build_reading_prompt(pdf_text: str, transcript_text: str, course_name: str = "") -> str:
    course_line = f"补充课程名称或主题：{course_name}\n" if course_name else ""
    pdf_section = pdf_text if pdf_text.strip() else "未提供 PDF 课件内容。"
    transcript_section = transcript_text if transcript_text.strip() else "未提供 TXT 字幕内容。"

    return f"""
# Role
你是一位擅长双语课程整理的项目管理助教。你的任务不是做高度归纳，而是把课程材料整理成“适合精读的中文辅助讲义”，帮助英语不是母语的学生较完整地读完材料，同时尽量保留老师讲课中的细节。

# Input Data
1. 【课件内容 (PDF)】: {pdf_section}
2. 【讲稿字幕 (TXT)】: {transcript_section}

# Task
请根据已提供的材料生成一份“精读翻译稿”：
- 如果同时提供 PDF 和 TXT，请以课件结构作为阅读主线，再在对应位置补入字幕的解释、案例和提醒；不要把两份材料机械拼接。
- 如果只提供其中一种材料，请基于该材料独立生成精读翻译稿。
- 目标不是高度总结，而是帮助学生相对完整地读懂材料内容。

# Constraint & Style
1. 以中文为主，但每一条都保留对应英文，方便中英对照阅读。
2. 尽量按原文顺序展开，不要大幅改写结构。
3. 只做“小限度整理”：
   - 可以合并明显重复句
   - 可以删去口头语、停顿词、重复寒暄
   - 可以补一个很简短的说明帮助理解
   - 但不要把多个细节压缩成一句大而空的总结
4. 如果内容是字幕，请尽量保留教授举的例子、定义解释、提醒、转折和因果关系。
5. 如果内容是课件，请保留标题、要点、定义、流程、案例说明。
6. 专业术语尽量写成“英文原文 (中文翻译)”。
7. 如果原文本身是纯中文，则保持自然中文，不要强行补英文。
8. 每个片段都要形成清晰的中英对照：
   - `- CN:` 放中文整理后的内容
   - `- EN:` 放对应英文原文或英文整理稿
9. 内容要比普通总结更完整，读者应能用它“顺着读完整节课”。
10. 不要输出 quiz，不要输出词汇表，不要写成宏观摘要。

# Output Schema
请严格按以下结构输出：

## 📘 精读导览 (Reading Guide)
- CN: [用 2-4 句话说明本份精读稿覆盖什么内容、适合怎么读]
- EN: [对应英文翻译]

## 🧾 精读翻译稿 (Guided Translation)
### Part 1
- CN: [中文整理后的第一段内容]
- EN: [对应英文原文或英文整理稿]
- CN: [中文整理后的第二段内容]
- EN: [对应英文原文或英文整理稿]

### Part 2
- CN: [继续按原顺序整理]
- EN: [对应英文]

[根据材料长度继续扩展，尽量覆盖主要内容]

# Additional Notes
- 优先保证“完整理解材料”，而不是“压缩成最短结论”。
- 如果材料很长，请优先保留有信息量的定义、解释、案例、流程和提醒。
- 不要提及缺失材料，不要输出“我无法访问视频”等元信息。
- 保持 Markdown 结构清晰，方便在网页中阅读。

{course_line}

# Execution
现在，请开始生成精读翻译稿。
""".strip()


def build_reading_chunk_prompt(
    chunk_text: str,
    chunk_index: int,
    total_chunks: int,
    course_name: str = "",
) -> str:
    course_line = f"补充课程名称或主题：{course_name}\n" if course_name else ""

    return f"""
# Role
你是一位擅长双语课程整理的项目管理助教。你正在处理一份长材料中的其中一段，目标是把这一段做成适合精读的中英对照翻译稿。

# Task
当前正在处理第 {chunk_index} / {total_chunks} 段材料。请只针对这一段内容输出“轻整理、低归纳、尽量保留细节”的精读翻译结果。

# Source Chunk
{chunk_text}

# Requirements
1. 尽量保留原文顺序，不要大幅跳跃。
2. 只做轻整理：
   - 删除明显口头语、停顿词、寒暄
   - 合并明显重复句
   - 其他内容尽量保留
3. 优先保留：
   - 定义
   - 举例
   - 教授解释
   - 因果关系
   - 流程步骤
   - 提醒与误区
4. 每一条都要按中英对照输出：
   - `- CN:` 中文整理
   - `- EN:` 对应英文原文或英文整理
5. 不要写宏观摘要，不要输出 quiz，不要输出术语表。
6. 目标是让读者能顺着读完这段材料，而不是只看到结论。
7. 尽可能多覆盖这段中的有效信息，不要只挑极少数点。

# Output Format
请严格按以下结构输出：

### Part {chunk_index}
- CN: [中文整理后的内容]
- EN: [对应英文]
- CN: [中文整理后的内容]
- EN: [对应英文]
- CN: [中文整理后的内容]
- EN: [对应英文]

[继续扩展，直到充分覆盖这一段中的主要内容]

{course_line}

# Execution
现在开始输出这一段的精读翻译稿。
""".strip()
