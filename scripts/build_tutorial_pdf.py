"""Build the two-page English handout from its Markdown source."""
import re
from html import escape
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs/VAS-Scanning-Tutorial.md"
OUTPUT = ROOT / "docs/VAS-Scanning-Tutorial.pdf"


def inline(text):
    text = escape(text)
    text = re.sub(r"\[([^]\n]+)\]\((https?://[^)]+)\)", r'<link href="\2" color="#222222"><u>\1</u></link>', text)
    text = re.sub(r"\[([^]\n]+)\]\(SOURCES.md\)", r"\1", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", text)
    return text


def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Times-Roman", 9)
    canvas.setFillColor(colors.HexColor("#555555"))
    canvas.drawString(44, 26, "VAS Scanning Tutorial  |  Shuyuun Wang  |  24 October 2026")
    canvas.drawRightString(A4[0] - 44, 26, str(doc.page))
    canvas.restoreState()


def main():
    body = ParagraphStyle("body", fontName="Times-Roman", fontSize=11.3, leading=14.2,
                          spaceAfter=7, alignment=TA_LEFT)
    styles = {
        "body": body,
        "title": ParagraphStyle("title", parent=body, fontName="Times-Bold", fontSize=23, leading=27, spaceAfter=10),
        "heading": ParagraphStyle("heading", parent=body, fontName="Times-Bold", fontSize=12.4, leading=15,
                                  spaceBefore=8, spaceAfter=6, keepWithNext=True),
        "bullet": ParagraphStyle("bullet", parent=body, leftIndent=11, firstLineIndent=-7),
        "small": ParagraphStyle("small", parent=body, fontSize=9.4, leading=11.6),
    }
    story = []
    for block in SOURCE.read_text(encoding="utf-8").strip().split("\n\n"):
        if block.startswith("# "):
            story.append(Paragraph(inline(block[2:]), styles["title"]))
        elif block.startswith("## "):
            if block.startswith("## 4 "):
                story.append(PageBreak())
            story.append(Paragraph(inline(block[3:]), styles["heading"]))
        elif block.startswith("- ") or re.match(r"^\d+\. ", block):
            for line in block.splitlines():
                if line.startswith("- "):
                    text = "• " + line[2:]
                else:
                    text = line
                story.append(Paragraph(inline(text), styles["bullet"]))
        else:
            style = styles["small"] if block.startswith(("**Sources:", "**Teaching context:")) else body
            story.append(Paragraph(inline(block).replace("  \n", "<br/>").replace("\n", " "), style))
    doc = SimpleDocTemplate(str(OUTPUT), pagesize=A4, rightMargin=44, leftMargin=44,
                            topMargin=36, bottomMargin=42, title="VAS Scanning Tutorial",
                            author="Shuyuun Wang", subject="Architectural image preparation and responsible VAS interpretation",
                            pageCompression=1, invariant=1)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(OUTPUT)


if __name__ == "__main__":
    main()
