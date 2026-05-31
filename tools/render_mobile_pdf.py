#!/usr/bin/env python3
"""Render the EMF proposal markdown to a narrow, mobile-friendly PDF."""

from __future__ import annotations

import re
import sys
import textwrap
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import inch
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch as INCH
from reportlab.platypus import (
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
)


PAGE_SIZE = (4.2 * inch, 7.5 * inch)


def clean_inline(text: str) -> str:
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"`([^`]+)`", r"<font name='Courier'>\1</font>", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)
    return text


def flush_paragraph(lines: list[str], story: list, style: ParagraphStyle) -> None:
    if not lines:
        return
    text = " ".join(line.strip() for line in lines).strip()
    if text:
        story.append(Paragraph(clean_inline(text), style))
        story.append(Spacer(1, 0.07 * INCH))
    lines.clear()


def flush_bullets(items: list[str], story: list, bullet_style: ParagraphStyle) -> None:
    if not items:
        return
    for item in items:
        story.append(Paragraph(clean_inline("- " + item), bullet_style))
        story.append(Spacer(1, 0.025 * INCH))
    story.append(Spacer(1, 0.07 * INCH))
    items.clear()


def flush_code(lines: list[str], story: list, code_style: ParagraphStyle) -> None:
    if not lines:
        return
    wrapped: list[str] = []
    for line in lines:
        if not line:
            wrapped.append("")
            continue
        chunks = textwrap.wrap(
            line,
            width=58,
            replace_whitespace=False,
            drop_whitespace=False,
            break_long_words=True,
            break_on_hyphens=False,
        )
        wrapped.extend(chunks or [""])
    for start in range(0, len(wrapped), 32):
        story.append(
            Preformatted(
                "\n".join(wrapped[start : start + 32]),
                code_style,
                newLineChars="\n",
            )
        )
        story.append(Spacer(1, 0.08 * INCH))
    lines.clear()


def build_story(markdown: str) -> list:
    base = getSampleStyleSheet()
    styles = {
        "h1": ParagraphStyle(
            "h1",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=20,
            spaceAfter=10,
            textColor=colors.HexColor("#111827"),
        ),
        "h2": ParagraphStyle(
            "h2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12.5,
            leading=15,
            spaceBefore=8,
            spaceAfter=5,
            textColor=colors.HexColor("#111827"),
            keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.8,
            leading=12.2,
            alignment=TA_LEFT,
            textColor=colors.HexColor("#1f2937"),
        ),
        "bullet": ParagraphStyle(
            "bullet",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=8.5,
            leading=11.5,
            leftIndent=10,
            firstLineIndent=-8,
            textColor=colors.HexColor("#1f2937"),
        ),
        "code": ParagraphStyle(
            "code",
            parent=base["Code"],
            fontName="Courier",
            fontSize=6.2,
            leading=8,
            leftIndent=4,
            rightIndent=0,
            textColor=colors.HexColor("#111827"),
        ),
    }

    story: list = []
    paragraph: list[str] = []
    bullets: list[str] = []
    code_lines: list[str] = []
    in_code = False

    for raw_line in markdown.splitlines():
        line = raw_line.rstrip()

        if line.startswith("```"):
            if in_code:
                flush_code(code_lines, story, styles["code"])
                in_code = False
            else:
                flush_paragraph(paragraph, story, styles["body"])
                flush_bullets(bullets, story, styles["bullet"])
                in_code = True
            continue

        if in_code:
            code_lines.append(line)
            continue

        if not line.strip():
            flush_paragraph(paragraph, story, styles["body"])
            flush_bullets(bullets, story, styles["bullet"])
            continue

        if bullets and line.startswith("  "):
            bullets[-1] = f"{bullets[-1]} {line.strip()}"
            continue

        if line.startswith("# "):
            flush_paragraph(paragraph, story, styles["body"])
            flush_bullets(bullets, story, styles["bullet"])
            story.append(Paragraph(clean_inline(line[2:].strip()), styles["h1"]))
            continue

        if line.startswith("## "):
            flush_paragraph(paragraph, story, styles["body"])
            flush_bullets(bullets, story, styles["bullet"])
            if story:
                story.append(Spacer(1, 0.05 * INCH))
            story.append(Paragraph(clean_inline(line[3:].strip()), styles["h2"]))
            continue

        if line.startswith("- "):
            flush_paragraph(paragraph, story, styles["body"])
            bullets.append(line[2:].strip())
            continue

        flush_bullets(bullets, story, styles["bullet"])
        paragraph.append(line)

    flush_paragraph(paragraph, story, styles["body"])
    flush_bullets(bullets, story, styles["bullet"])
    return story


def add_footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 6.5)
    canvas.setFillColor(colors.HexColor("#6b7280"))
    canvas.drawRightString(
        doc.pagesize[0] - 0.32 * INCH,
        0.18 * INCH,
        f"EMF mission proposal - {doc.page}",
    )
    canvas.restoreState()


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: render_mobile_pdf.py input.md output.pdf", file=sys.stderr)
        return 2

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    output_path.parent.mkdir(parents=True, exist_ok=True)

    markdown = input_path.read_text(encoding="utf-8")
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=PAGE_SIZE,
        rightMargin=0.32 * INCH,
        leftMargin=0.32 * INCH,
        topMargin=0.35 * INCH,
        bottomMargin=0.32 * INCH,
        title="EMF Mission Proposal",
        author="Codex",
    )
    doc.build(build_story(markdown), onFirstPage=add_footer, onLaterPages=add_footer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
