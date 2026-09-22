#!/usr/bin/env python3
"""Render the project Markdown summary as a dependency-free, readable PDF."""

from __future__ import annotations

import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "docs" / "PROJECT_SUMMARY.md"
OUTPUT = ROOT / "docs" / "PROJECT_SUMMARY.pdf"


def pdf_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def markdown_lines(text: str) -> list[tuple[str, str]]:
    lines: list[tuple[str, str]] = []
    in_code = False
    for raw in text.splitlines():
        line = raw.rstrip()
        if line.startswith("```"):
            in_code = not in_code
            lines.append(("space", ""))
            continue
        if not line:
            lines.append(("space", ""))
            continue
        if in_code:
            lines.append(("code", line))
        elif line.startswith("# "):
            lines.append(("title", line[2:]))
        elif line.startswith("## "):
            lines.append(("h1", line[3:]))
        elif line.startswith("### "):
            lines.append(("h2", line[4:]))
        elif line.startswith("|"):
            if set(line.replace("|", "").replace("-", "").replace(":", "").replace(" ", "")):
                lines.append(("body", line.replace("|", "  ")))
        else:
            lines.append(("body", re.sub(r"[`*_]", "", line)))
    return lines


def wrap(text: str, width: int) -> list[str]:
    words = text.split()
    result: list[str] = []
    current = ""
    for word in words:
        if current and len(current) + len(word) + 1 > width:
            result.append(current)
            current = word
        else:
            current = word if not current else f"{current} {word}"
    if current:
        result.append(current)
    return result or [""]


def build_pdf(lines: list[tuple[str, str]]) -> bytes:
    pages: list[list[str]] = [[]]
    y = 750
    for kind, text in lines:
        height = {"title": 25, "h1": 19, "h2": 16, "body": 12, "code": 12, "space": 8}[kind]
        if kind == "space":
            if pages[-1] and y < 80:
                pages.append([])
                y = 750
            pages[-1].append("")
            y -= height
            continue
        font_size = {"title": 18, "h1": 13, "h2": 11, "body": 8.5, "code": 8}[kind]
        width = 82 if kind in {"body", "code"} else 70
        for part in wrap(text, width):
            if y < 55:
                pages.append([])
                y = 750
            pages[-1].append(f"{font_size}|{part}")
            y -= height if kind in {"title", "h1", "h2"} else 11

    objects: list[bytes] = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    page_refs = " ".join(f"{4 + index * 2} 0 R" for index in range(len(pages)))
    objects.append(f"<< /Type /Pages /Kids [{page_refs}] /Count {len(pages)} >>".encode())
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    for index, page in enumerate(pages):
        content_object = 5 + index * 2
        stream_lines = ["BT", "/F1 8.5 Tf", "50 750 Td"]
        for entry in page:
            if not entry:
                stream_lines.append("0 -8 Td")
                continue
            size, value = entry.split("|", 1)
            stream_lines.append(f"/F1 {size} Tf ({pdf_escape(value)}) Tj 0 -11 Td")
        stream_lines.append("ET")
        stream = "\n".join(stream_lines).encode("latin-1", "replace")
        objects.append(f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 3 0 R >> >> /Contents {content_object} 0 R >>".encode())
        objects.append(b"<< /Length " + str(len(stream)).encode() + b" >>\nstream\n" + stream + b"\nendstream")

    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for number, obj in enumerate(objects, start=1):
        offsets.append(len(output))
        output.extend(f"{number} 0 obj\n".encode() + obj + b"\nendobj\n")
    xref = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode())
    output.extend(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    return bytes(output)


def main() -> None:
    OUTPUT.write_bytes(build_pdf(markdown_lines(SOURCE.read_text(encoding="utf-8"))))
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    main()