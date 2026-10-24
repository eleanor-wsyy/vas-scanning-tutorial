"""Build the handout in the source teaching handbook's typographic style."""
import re
from html import escape
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image

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
    canvas.setFont("Helvetica", 9)
    canvas.setFillColor(colors.black)
    canvas.drawCentredString(A4[0] / 2, 57, str(doc.page))
    canvas.restoreState()


def main():
    font, bold = "Times-Roman", "Times-Bold"
    windows_fonts = Path("C:/Windows/Fonts")
    if all((windows_fonts / name).exists() for name in ["times.ttf", "timesbd.ttf", "timesi.ttf", "timesbi.ttf"]):
        for name, file in [("HandbookTimes", "times.ttf"), ("HandbookTimes-Bold", "timesbd.ttf"),
                           ("HandbookTimes-Italic", "timesi.ttf"), ("HandbookTimes-BoldItalic", "timesbi.ttf")]:
            pdfmetrics.registerFont(TTFont(name, str(windows_fonts / file)))
        pdfmetrics.registerFontFamily("HandbookTimes", normal="HandbookTimes", bold="HandbookTimes-Bold",
                                      italic="HandbookTimes-Italic", boldItalic="HandbookTimes-BoldItalic")
        font, bold = "HandbookTimes", "HandbookTimes-Bold"
    body = ParagraphStyle("body", fontName=font, fontSize=10.5, leading=12.5, spaceAfter=6, alignment=TA_LEFT)
    styles = {
        "body": body,
        "title": ParagraphStyle("title", parent=body, fontName=bold, fontSize=11, leading=13.5,
                                alignment=TA_CENTER, spaceAfter=12),
        "author": ParagraphStyle("author", parent=body, alignment=TA_CENTER, spaceAfter=18),
        "heading": ParagraphStyle("heading", parent=body, fontName=bold, spaceBefore=8,
                                  spaceAfter=5, keepWithNext=True),
        "subheading": ParagraphStyle("subheading", parent=body, fontName=bold, spaceBefore=4,
                                     spaceAfter=4, keepWithNext=True),
        "bullet": ParagraphStyle("bullet", parent=body, leftIndent=9, firstLineIndent=-7),
        "caption": ParagraphStyle("caption", parent=body, fontSize=9.2, leading=10.7, spaceAfter=8),
        "figure_label": ParagraphStyle("figure_label", parent=body, spaceAfter=4, keepWithNext=True),
        "reference": ParagraphStyle("reference", parent=body, leftIndent=14, firstLineIndent=-14,
                                    spaceAfter=7),
    }
    story = []
    in_references = False
    for block in SOURCE.read_text(encoding="utf-8").strip().split("\n\n"):
        image_match = re.fullmatch(r"!\[([^]]*)\]\(([^)]+)\)", block)
        if image_match:
            image_path = (SOURCE.parent / image_match.group(2)).resolve()
            image_path.relative_to((SOURCE.parent / "assets").resolve())
            image = Image(str(image_path))
            width = A4[0] - 90 - 78
            image.drawHeight *= width / image.drawWidth
            image.drawWidth = width
            image.hAlign = "LEFT"
            image.keepWithNext = True
            story.extend([image, Spacer(1, 4)])
        elif block.startswith("*Figure "):
            story.append(Paragraph(inline(block), styles["caption"]))
        elif block.startswith(("**(a)", "**(b)")):
            story.append(Paragraph(inline(block), styles["figure_label"]))
        elif block.startswith("# "):
            story.append(Paragraph(inline(block[2:]), styles["title"]))
        elif block.startswith("### "):
            if block == "### References":
                in_references = True
            story.append(Paragraph(inline(block[4:]), styles["subheading"]))
        elif block.startswith("## "):
            if block.startswith(("## 3.", "## 5.")) or block == "## Resources":
                story.append(PageBreak())
            story.append(Paragraph(inline(block[3:]), styles["heading"]))
        elif block.startswith("- "):
            for line in block.splitlines():
                story.append(Paragraph(inline("• " + line[2:]), styles["bullet"]))
        else:
            style = styles["author"] if block.startswith("Prepared by") else styles["reference"] if in_references else body
            story.append(Paragraph(inline(block).replace("  \n", "<br/>").replace("\n", " "), style))
    doc = SimpleDocTemplate(str(OUTPUT), pagesize=A4, rightMargin=78, leftMargin=90,
                            topMargin=70, bottomMargin=78, title="3M VAS Scanning Tutorial",
                            author="Shuyuun Wang", subject="Architectural image comparison and scholarly references",
                            pageCompression=1, invariant=1)
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    print(OUTPUT)


if __name__ == "__main__":
    main()
