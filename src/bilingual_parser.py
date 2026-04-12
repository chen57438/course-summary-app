from __future__ import annotations


def parse_bilingual_pairs(summary_markdown: str) -> list[dict[str, str]]:
    pairs: list[dict[str, str]] = []
    current_section = ""
    current_module = ""
    pending_cn = ""

    for raw_line in summary_markdown.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        if line.startswith("## "):
            current_section = line[3:].strip()
            current_module = ""
            continue

        if line.startswith("### "):
            current_module = line[4:].strip()
            continue

        if line.startswith("- CN:"):
            pending_cn = line[5:].strip()
            continue

        if line.startswith("- EN:") and pending_cn:
            pairs.append(
                {
                    "section": current_section,
                    "module": current_module,
                    "cn": pending_cn,
                    "en": line[5:].strip(),
                }
            )
            pending_cn = ""

    return pairs
