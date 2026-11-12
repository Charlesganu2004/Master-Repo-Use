"""Text extraction and chunking for the local knowledge base. No models."""

import re
from pathlib import Path

SUPPORTED = {".md", ".markdown", ".txt", ".rst", ".log", ".csv", ".docx", ".pdf"}
MAX_CHARS = 1200
HEADING = re.compile(r"^(#{1,6})\s+(.+)$")


def _docx_text(path: Path) -> str:
    from docx import Document
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    doc = Document(str(path))
    out = []
    for child in doc.element.body.iterchildren():
        tag = child.tag.rsplit("}", 1)[-1]
        if tag == "p":
            para = Paragraph(child, doc)
            text = para.text.strip()
            if not text:
                continue
            style = (para.style.name if para.style is not None else "").lower()
            level = re.match(r"heading (\d)", style)
            if level:
                text = "#" * min(int(level.group(1)), 6) + " " + text
            elif style == "title":
                text = "# " + text
            out.append(text)
        elif tag == "tbl":
            for row in Table(child, doc).rows:
                cells = [c.text.strip() for c in row.cells]
                if any(cells):
                    out.append(" | ".join(cells))
    return "\n\n".join(out)


def extract_sections(path: Path) -> list[tuple[str | None, str]]:
    ext = path.suffix.lower()
    if ext == ".pdf":
        from pypdf import PdfReader

        return [(f"page {i + 1}", page.extract_text() or "") for i, page in enumerate(PdfReader(str(path)).pages)]
    if ext == ".docx":
        return [(None, _docx_text(path))]
    return [(None, path.read_text(encoding="utf-8", errors="replace").lstrip("\ufeff"))]


def _split_long(text: str) -> list[str]:
    parts = []
    while len(text) > MAX_CHARS:
        cut = text.rfind(". ", 0, MAX_CHARS)
        if cut < MAX_CHARS // 2:
            cut = text.rfind(" ", 0, MAX_CHARS)
        if cut < MAX_CHARS // 2:
            cut = MAX_CHARS
        parts.append(text[: cut + 1].strip())
        text = text[cut + 1 :]
    if text.strip():
        parts.append(text.strip())
    return parts


def chunk_sections(sections: list[tuple[str | None, str]]) -> list[dict]:
    """Paragraph-packed chunks of up to MAX_CHARS, each tagged with its heading trail."""
    chunks = []
    for base, text in sections:
        trail: list[tuple[int, str]] = []
        buf: list[str] = []
        size = 0

        def heading() -> str | None:
            return " > ".join([h for h in [base, *[t for _, t in trail]] if h]) or None

        current = heading()

        def flush() -> None:
            nonlocal buf, size, current
            body = "\n\n".join(buf).strip()
            if body:
                chunks.append({"heading": current, "text": body})
            buf, size, current = [], 0, heading()

        for raw in re.split(r"\n\s*\n", text.replace("\r\n", "\n").replace("\r", "\n")):
            block = raw.strip()
            match = HEADING.match(block.split("\n", 1)[0]) if block else None
            if match:
                flush()
                level = len(match.group(1))
                while trail and trail[-1][0] >= level:
                    trail.pop()
                trail.append((level, match.group(2).strip()))
                current = heading()
                block = block.split("\n", 1)[1].strip() if "\n" in block else ""
            if not block:
                continue
            for piece in _split_long(block):
                if buf and size + len(piece) + 2 > MAX_CHARS:
                    flush()
                buf.append(piece)
                size += len(piece) + 2
        flush()
    return chunks
