#!/usr/bin/env python3
"""Convert the repository's fixed-width .txt manuals to Markdown.

The sources are plain text laid out in 79 columns: rule-enclosed PART and
CHAPTER headings, numbered sections, aligned tables and pseudo-code in
indented blocks. This converter keeps the layout where it matters (tables and
code stay in fenced blocks, so their alignment survives) and turns prose into
real Markdown paragraphs, with a GitHub-compatible clickable table of contents
generated from the headings.

Usage:
    python3 tools/txt2md.py                    # every *.txt in the repo root
    python3 tools/txt2md.py the-economics-of-fraud.txt

Each source file is rewritten next to itself with a .md extension.
"""

from __future__ import annotations

import re
import sys
import unicodedata
from pathlib import Path

RULE = re.compile(r"^([=-]){5,}$")
SECTION = re.compile(r"^\d+\.\d+\s+\S")
MAJOR = re.compile(r"^(?:CHAPTER|CHAPITRE|APPENDIX|ANNEXE)\b", re.I)
PART = re.compile(r"^(?:PART|PARTIE)\b", re.I)
END = re.compile(r"^(?:END OF MANUAL|FIN DU MANUEL|END OF DOCUMENT)\b", re.I)
LIST_ITEM = re.compile(r"^(\s*)[-*]\s+(.*)$")
TOC_LABELS = {
    "TABLE OF CONTENTS",
    "TABLE DES MATIÈRES",
    "TABLE DES MATIERES",
    "SOMMAIRE",
}


def is_rule(line: str) -> bool:
    return bool(RULE.match(line.strip()))


def rule_char(line: str) -> str:
    return line.strip()[0]


def slugify(text: str, seen: dict[str, int]) -> str:
    """GitHub heading anchor: lowercase, drop punctuation, spaces -> hyphens."""
    kept = []
    for ch in text.strip().lower():
        if ch in " -_":
            kept.append(ch)
        elif ch.isalnum() or unicodedata.category(ch).startswith("M"):
            kept.append(ch)
    slug = "".join(kept).replace(" ", "-").rstrip("-")
    if slug in seen:
        seen[slug] += 1
        slug = f"{slug}-{seen[slug]}"
    else:
        seen[slug] = 0
    return slug


class Converter:
    def __init__(self, title: str, subtitle: str = "") -> None:
        self.title = title
        self.subtitle = subtitle
        self.body: list[str] = []
        self.headings: list[tuple[int, str, str]] = []
        self.seen: dict[str, int] = {}

    def _separate(self) -> None:
        if self.body and self.body[-1] != "":
            self.body.append("")

    def heading(self, level: int, text: str) -> None:
        text = " ".join(text.split())
        if not text:
            return
        self._separate()
        self.body.extend([f"{'#' * level} {text}", ""])
        self.headings.append((level, text, slugify(text, self.seen)))

    def paragraph(self, text: str) -> None:
        self._separate()
        self.body.extend([" ".join(text.split()), ""])

    def bullets(self, items: list[tuple[int, str]]) -> None:
        self._separate()
        for depth, text in items:
            self.body.append(f"{'  ' * (depth - 1)}- {' '.join(text.split())}")
        self.body.append("")

    def fence(self, lines: list[str]) -> None:
        while lines and not lines[0].strip():
            lines.pop(0)
        while lines and not lines[-1].strip():
            lines.pop()
        if lines:
            self._separate()
            self.body.append("```text")
            self.body.extend(line.rstrip() for line in lines)
            self.body.extend(["```", ""])

    def render(self) -> str:
        floor = min((level for level, _, _ in self.headings), default=2)
        toc = ["## Table of contents", ""]
        toc += [
            f"{'  ' * (level - floor)}- [{text}](#{anchor})"
            for level, text, anchor in self.headings
        ]
        toc.append("")

        head = [f"# {self.title}", ""]
        if self.subtitle:
            head += [f"*{self.subtitle}*", ""]
        out = head + toc + self.body
        while out and out[-1] == "":
            out.pop()
        return "\n".join(out) + "\n"


def default_title(path: Path) -> str:
    words = [w for w in re.split(r"[-_ ]+", path.stem) if w]
    if not words:
        return path.stem
    first, *rest = words
    return " ".join([first[:1].upper() + first[1:], *rest])


def enclosed_block(lines: list[str], start: int) -> tuple[list[str], int]:
    """Return (lines enclosed by the rule, index after the closing rule).

    A decorative rule is any rule that does not enclose a short heading-like
    block: at most three short lines. That keeps prose paragraphs framed by
    stray dashes from being mistaken for headings.
    """
    char = rule_char(lines[start])
    for j in range(start + 1, min(start + 6, len(lines))):
        if is_rule(lines[j]):
            if rule_char(lines[j]) != char:
                return [], start
            enclosed = lines[start + 1 : j]
            if not enclosed or len(enclosed) > 3:
                return [], start
            if any(len(part.strip()) > 100 for part in enclosed):
                return [], start
            return enclosed, j + 1
    return [], start


def underlined_heading(lines: list[str], index: int) -> tuple[str, int] | None:
    """Detect a heading written as text on one line, dashes on the next."""
    line = lines[index].strip()
    if not line or is_rule(line) or index + 1 >= len(lines):
        return None
    underline = lines[index + 1].strip()
    if not underline or set(underline) != {"-"} or len(underline) < 3:
        return None
    if len(line) > 120:
        return None
    return line, index + 2


def block_kind(block: list[str]) -> str:
    if LIST_ITEM.match(block[0]):
        return "bullets"
    if any(line[:1].isspace() for line in block):
        return "fence"
    return "prose"


def emit_block(conv: Converter, block: list[str]) -> None:
    kind = block_kind(block)
    if kind == "bullets":
        items: list[list] = []
        for line in block:
            m = LIST_ITEM.match(line)
            if m:
                indent = len(m.group(1))
                depth = max(1, min(3, (indent - 2) // 4 + 1)) if indent else 1
                items.append([depth, m.group(2).strip()])
            elif items:
                items[-1][1] += " " + line.strip()
        conv.bullets([(depth, text) for depth, text in items])
    elif kind == "fence":
        conv.fence(list(block))
    else:
        conv.paragraph(" ".join(block))


def convert(path: Path) -> str:
    lines = [line.rstrip() for line in path.read_text(encoding="utf-8").splitlines()]
    conv = Converter(default_title(path))
    total = len(lines)

    i = 0
    while i < total and not lines[i].strip():
        i += 1

    # optional title block at the very top
    if i < total and is_rule(lines[i]) and rule_char(lines[i]) == "=":
        enclosed, after = enclosed_block(lines, i)
        parts = [part.strip() for part in enclosed if part.strip()]
        if parts and not PART.match(parts[0]) and not MAJOR.match(parts[0]):
            conv.title = parts[0]
            conv.subtitle = " ".join(parts[1:])
            i = after

    while i < total:
        line = lines[i]
        stripped = line.strip()

        if is_rule(line):
            enclosed, after = enclosed_block(lines, i)
            text = " ".join(part.strip() for part in enclosed if part.strip())
            if text and END.match(text):
                conv.paragraph(f"*{text}*")
                i = after
                continue
            if text:
                if rule_char(line) == "=":
                    level = 2
                elif SECTION.match(text):
                    level = 4
                else:
                    level = 3
                conv.heading(level, text)
                i = after
                continue
            i += 1
            continue

        if not stripped:
            i += 1
            continue

        # the source table of contents is replaced by the generated one
        if stripped.upper() in TOC_LABELS:
            i += 1
            if i < total and is_rule(lines[i]):
                i += 1  # skip the label's own underline
            while i < total:
                if is_rule(lines[i]) or underlined_heading(lines, i):
                    break
                i += 1
            continue

        if (
            not line[:1].isspace()
            and SECTION.match(stripped)
            and len(stripped) < 120
            and (i + 1 >= total or not lines[i + 1].strip())
        ):
            conv.heading(4, stripped)
            i += 1
            continue

        underlined = underlined_heading(lines, i)
        if underlined:
            text, after = underlined
            if SECTION.match(text):
                level = 4
            elif any(level_ == 2 for level_, _, _ in conv.headings):
                level = 3
            else:
                level = 2
            conv.heading(level, text)
            i = after
            continue

        j = i
        block: list[str] = []
        while j < total and lines[j].strip() and not is_rule(lines[j]):
            block.append(lines[j])
            j += 1
        emit_block(conv, block)
        i = j

    return conv.render()


def main(argv: list[str]) -> int:
    root = Path(__file__).resolve().parent.parent
    targets = [Path(a) if Path(a).is_absolute() else root / a for a in argv[1:]]
    if not targets:
        targets = sorted(root.glob("*.txt"))

    for src in targets:
        md = convert(src)
        dest = src.with_suffix(".md")
        dest.write_text(md, encoding="utf-8")
        print(f"{src.name} -> {dest.name} ({len(md.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
