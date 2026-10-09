#!/usr/bin/env python3
"""Build the downloadable textbooks from the site pages.

Each markdown page is the only source for that language. This script writes:

- docs/Entropianism_Textbook.txt and .pdf from docs/textbook.md
- docs/ru/Entropianism_Textbook.txt and .pdf from docs/textbook.ru.md

MkDocs calls on_pre_build() and refreshes the text files on every build.
The PDFs are written when the script is run directly (deploy does this).
"""

import re
import sys
from html.parser import HTMLParser
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parent
EDITIONS = (
    {
        "source": ROOT / "docs" / "textbook.md",
        "text": ROOT / "docs" / "Entropianism_Textbook.txt",
        "html": ROOT / "docs" / "Entropianism_Textbook_temp.html",
        "pdf": ROOT / "docs" / "Entropianism_Textbook.pdf",
        "lang": "en",
        "title": "Textbook of Entropianism",
    },
    {
        "source": ROOT / "docs" / "textbook.ru.md",
        "text": ROOT / "docs" / "ru" / "Entropianism_Textbook.txt",
        "html": ROOT / "docs" / "ru" / "Entropianism_Textbook_temp.html",
        "pdf": ROOT / "docs" / "ru" / "Entropianism_Textbook.pdf",
        "lang": "ru",
        "title": "Учебник Энтропианства",
    },
)

EXTENSIONS = [
    "markdown.extensions.tables",
    "markdown.extensions.admonition",
    "markdown.extensions.sane_lists",
    "markdown.extensions.attr_list",
    "markdown.extensions.md_in_html",
]


def read_markdown(path):
    if not path.is_file():
        print(f"Error: {path} not found")
        sys.exit(1)
    return path.read_text(encoding="utf-8")


def render_html_body(source):
    return markdown.markdown(source, extensions=EXTENSIONS)


class TextExtractor(HTMLParser):
    """Turn the rendered textbook HTML into readable plain text."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.blocks = []
        self.stack = []
        self.buf = []
        self.lists = []
        self.table = None
        self.row = None

    def result(self):
        text = "\n\n".join(block for block in self.blocks if block.strip())
        return text.strip() + "\n"

    def handle_starttag(self, tag, attrs):
        classes = set(dict(attrs).get("class", "").split())
        if tag == "div" and "admonition" in classes:
            self.stack.append("admonition")
            return
        if tag == "p" and "admonition-title" in classes:
            self._push("admonition-title")
            return
        if tag in {"h1", "h2", "h3", "h4"}:
            self._push(tag)
            return
        if tag == "p":
            if self._inside("li") or self._inside("cell"):
                return
            self._push("p")
            return
        if tag == "blockquote":
            self._push("blockquote")
            return
        if tag == "li":
            self._push("li")
            if self.lists and self.lists[-1]["kind"] == "ol":
                self.lists[-1]["n"] += 1
            return
        if tag == "ul":
            self.lists.append({"kind": "ul", "n": 0, "items": []})
            return
        if tag == "ol":
            self.lists.append({"kind": "ol", "n": 0, "items": []})
            return
        if tag == "table":
            self.table = []
            return
        if tag == "tr" and self.table is not None:
            self.row = []
            return
        if tag in {"td", "th"} and self.row is not None:
            self._push("cell")
            return
        if tag == "br":
            self.buf.append("\n")
            return
        if tag == "hr":
            self.blocks.append("—")

    def handle_endtag(self, tag):
        if tag in {"h1", "h2", "h3", "h4"} and self._pop(tag):
            text = self._take_text()
            if tag in {"h1", "h2"}:
                text = text.upper()
            self.blocks.append(text)
            return
        if tag == "p" and self._pop("admonition-title"):
            self.blocks.append(self._take_text())
            return
        if tag == "p" and self._pop("p"):
            self.blocks.append(self._take_text())
            return
        if tag == "blockquote" and self._pop("blockquote"):
            self.blocks.append(self._take_text())
            return
        if tag == "li" and self._pop("li"):
            text = self._take_text()
            if not self.lists:
                self.blocks.append("• " + text)
                return
            kind = self.lists[-1]["kind"]
            if kind == "ol":
                prefix = f"{self.lists[-1]['n']}. "
            else:
                prefix = "• "
            self.lists[-1]["items"].append(prefix + text)
            return
        if tag in {"ul", "ol"} and self.lists:
            items = self.lists.pop()["items"]
            if items:
                self.blocks.append("\n".join(items))
            return
        if tag in {"td", "th"} and self._pop("cell"):
            if self.row is not None:
                self.row.append(self._take_text())
            return
        if tag == "tr" and self.row is not None and self.table is not None:
            self.table.append(self.row)
            self.row = None
            return
        if tag == "table" and self.table is not None:
            lines = [" | ".join(cell for cell in row) for row in self.table]
            lines = [line for line in lines if line.strip(" |")]
            if lines:
                self.blocks.append("\n".join(lines))
            self.table = None
            return
        if tag == "div":
            self._pop("admonition")

    def handle_data(self, data):
        if self.stack:
            self.buf.append(data)

    def _push(self, tag):
        self.stack.append(tag)
        self.buf = []

    def _inside(self, tag):
        return tag in self.stack

    def _pop(self, tag):
        if self.stack and self.stack[-1] == tag:
            self.stack.pop()
            return True
        return False

    def _take_text(self):
        text = "".join(self.buf)
        self.buf = []
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.split("\n")]
        return "\n".join(line for line in lines if line).strip()


def markdown_to_text(source):
    parser = TextExtractor()
    parser.feed(render_html_body(source))
    return parser.result()


def write_text(edition, source):
    edition["text"].parent.mkdir(parents=True, exist_ok=True)
    edition["text"].write_text(markdown_to_text(source), encoding="utf-8")
    return edition["text"]


PRINT_CSS = """
@page { size: A4; margin: 1.8cm; }
body {
    font-family: "Segoe UI", Arial, sans-serif;
    font-size: 11pt;
    line-height: 1.45;
    color: #111;
}
h1 { font-size: 22pt; margin: 0 0 0.6em; }
h2 { font-size: 16pt; margin: 1.3em 0 0.4em; page-break-after: avoid; }
h3 { font-size: 13pt; margin: 1.1em 0 0.3em; page-break-after: avoid; }
p { margin: 0.45em 0; }
ul, ol { margin: 0.4em 0 0.4em 1.2em; padding: 0; }
li { margin: 0.15em 0; }
table { border-collapse: collapse; width: 100%; margin: 0.7em 0; page-break-inside: avoid; }
th, td { border: 1px solid #ccc; padding: 4px 8px; vertical-align: top; text-align: left; }
th { background: #f6f6f6; }
.admonition {
    border-left: 4px solid #e65100;
    background: #fff3e0;
    padding: 8px 12px;
    margin: 0.8em 0;
    page-break-inside: avoid;
}
.admonition-title { font-weight: 700; margin: 0 0 0.3em; }
hr { border: 0; border-top: 1px solid #ddd; margin: 1.2em 0; }
"""


def write_html(edition, source):
    body = render_html_body(source)
    document = f"""<!DOCTYPE html>
<html lang="{edition['lang']}">
<head>
    <meta charset="utf-8">
    <title>{edition['title']}</title>
    <style>{PRINT_CSS}</style>
</head>
<body>
{body}
</body>
</html>
"""
    edition["html"].parent.mkdir(parents=True, exist_ok=True)
    edition["html"].write_text(document, encoding="utf-8")
    return edition["html"]


def write_pdf(page, html_file, pdf_file):
    page.goto(html_file.resolve().as_uri())
    page.pdf(
        path=str(pdf_file),
        format="A4",
        margin={"top": "1.8cm", "right": "1.6cm", "bottom": "1.8cm", "left": "1.6cm"},
        print_background=True,
    )
    return pdf_file


def write_texts():
    written = []
    for edition in EDITIONS:
        source = read_markdown(edition["source"])
        written.append(write_text(edition, source))
    return written


def on_pre_build(config):
    """MkDocs hook: refresh the downloadable text before each build."""
    for path in write_texts():
        print(f"Textbook text: {path.relative_to(ROOT)}")


def main():
    from playwright.sync_api import sync_playwright

    sources = [(edition, read_markdown(edition["source"])) for edition in EDITIONS]
    for edition, source in sources:
        print(f"Wrote {write_text(edition, source).relative_to(ROOT)}")

    html_files = [write_html(edition, source) for edition, source in sources]
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page()
            for edition, html_file in zip(EDITIONS, html_files):
                pdf_path = write_pdf(page, html_file, edition["pdf"])
                print(f"Wrote {pdf_path.relative_to(ROOT)}")
            browser.close()
    except ImportError:
        print("Playwright is not installed. Install it with: pip install playwright")
        print("Then run: playwright install chromium")
        sys.exit(1)
    except Exception as error:
        print(f"Could not write the PDF: {error}")
        sys.exit(1)
    finally:
        for html_file in html_files:
            html_file.unlink(missing_ok=True)


if __name__ == "__main__":
    main()
