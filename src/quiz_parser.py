from __future__ import annotations

import re


QUESTION_PATTERN = re.compile(r"^\d+\.\s+(.*)$")
OPTION_PATTERN = re.compile(r"^-\s+([A-D])\.\s+(.*)$")
ANSWER_PATTERN = re.compile(r"^-\s+Answer:\s*([A-D])\s*$")
EXPLANATION_HEADER_PATTERN = re.compile(r"^-\s+Option Explanations:\s*$")
OPTION_EXPLANATION_PATTERN = re.compile(r"^-\s+([A-D]):\s+(.*)$")


def parse_quiz_markdown(quiz_markdown: str) -> list[dict]:
    questions: list[dict] = []
    current: dict | None = None
    in_option_explanations = False

    for raw_line in quiz_markdown.splitlines():
        line = raw_line.strip()
        if not line or line == "## Quiz":
            continue

        question_match = QUESTION_PATTERN.match(line)
        if question_match:
            if current:
                questions.append(current)
            current = {
                "question": question_match.group(1).strip(),
                "options": {},
                "answer": "",
                "explanations": {},
            }
            in_option_explanations = False
            continue

        if current is None:
            continue

        option_match = OPTION_PATTERN.match(line)
        if option_match and not in_option_explanations:
            current["options"][option_match.group(1)] = option_match.group(2).strip()
            continue

        answer_match = ANSWER_PATTERN.match(line)
        if answer_match:
            current["answer"] = answer_match.group(1)
            in_option_explanations = False
            continue

        if EXPLANATION_HEADER_PATTERN.match(line):
            in_option_explanations = True
            continue

        option_explanation_match = OPTION_EXPLANATION_PATTERN.match(line)
        if option_explanation_match and in_option_explanations:
            current["explanations"][option_explanation_match.group(1)] = option_explanation_match.group(2).strip()

    if current:
        questions.append(current)

    return [
        question
        for question in questions
        if question["question"] and len(question["options"]) == 4 and question["answer"] in {"A", "B", "C", "D"}
    ]
