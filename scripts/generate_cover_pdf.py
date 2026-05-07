"""
Build COVER_LETTER.pdf from COVER_LETTER.md with embedded screenshot PNGs.

Usage (from project root):
    pip install fpdf2
    python scripts/generate_cover_pdf.py
"""
from __future__ import annotations

import re
from pathlib import Path

from fpdf import FPDF

ROOT = Path(__file__).resolve().parents[1]
MD_PATH = ROOT / "COVER_LETTER.md"
OUT_PATH = ROOT / "COVER_LETTER.pdf"

IMG_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")


def normalize(text: str) -> str:
    return (
        text.replace("\u2014", "-")
        .replace("\u2013", "-")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
        .replace("\u2019", "'")
        .replace("\u2026", "...")
    )


def strip_inline_markdown(s: str) -> str:
    s = re.sub(r"\*\*([^*]+)\*\*", r"\1", s)
    s = re.sub(r"`([^`]+)`", r"\1", s)
    return normalize(s)


class CoverPDF(FPDF):
    def __init__(self) -> None:
        super().__init__(format="Letter")
        self.set_auto_page_break(auto=True, margin=18)
        self.set_margins(18, 18, 18)

    def add_image_safe(self, path: Path, caption: str) -> None:
        if not path.is_file():
            self.set_font("Helvetica", "", 10)
            self.set_text_color(180, 0, 0)
            self.multi_cell(0, 5, f"[Missing image: {path}]")
            self.set_text_color(0, 0, 0)
            return
        self.ln(2)
        if caption.strip():
            self.set_font("Helvetica", "I", 9)
            self.multi_cell(0, 4, strip_inline_markdown(caption))
            self.ln(1)
        try:
            self.image(str(path), w=self.epw)
        except Exception as exc:  # pragma: no cover
            self.set_font("Helvetica", "", 10)
            self.multi_cell(0, 5, f"[Could not embed image: {exc}]")
        self.ln(4)
        self.set_x(self.l_margin)


def main() -> None:
    if not MD_PATH.is_file():
        raise SystemExit(f"Missing {MD_PATH}")

    lines = MD_PATH.read_text(encoding="utf-8").splitlines()
    pdf = CoverPDF()
    pdf.add_page()

    for raw in lines:
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped:
            pdf.ln(2)
            continue

        img_match = IMG_RE.fullmatch(stripped)
        if img_match:
            caption = img_match.group(1)
            rel = img_match.group(2).strip()
            rel_clean = rel[2:] if rel.startswith("./") else rel
            path = ROOT / rel_clean
            pdf.add_image_safe(path, caption)
            continue

        if stripped.startswith("# "):
            pdf.set_x(pdf.l_margin)
            pdf.set_font("Helvetica", "B", 18)
            pdf.multi_cell(0, 8, strip_inline_markdown(stripped[2:]))
            pdf.ln(4)
            continue
        if stripped.startswith("## "):
            pdf.set_x(pdf.l_margin)
            pdf.set_font("Helvetica", "B", 14)
            pdf.multi_cell(0, 7, strip_inline_markdown(stripped[3:]))
            pdf.ln(3)
            continue
        if stripped.startswith("### "):
            pdf.set_x(pdf.l_margin)
            pdf.set_font("Helvetica", "B", 11)
            pdf.multi_cell(0, 6, strip_inline_markdown(stripped[4:]))
            pdf.ln(2)
            continue

        pdf.set_x(pdf.l_margin)
        pdf.set_font("Helvetica", "", 11)
        pdf.multi_cell(0, 6, strip_inline_markdown(stripped))

    pdf.output(OUT_PATH)
    print(f"Wrote {OUT_PATH}")


if __name__ == "__main__":
    main()
