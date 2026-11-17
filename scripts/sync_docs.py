#!/usr/bin/env python3
"""
Mirror the official Ren'Py documentation into references/docs/ as Markdown.

The docs at https://www.renpy.org/doc/html/ are the source of truth for this
skill. This script downloads every page linked from the documentation index,
converts the article body to compact Markdown, and writes:

    references/docs/<page>.md   one file per documentation page
    references/docs/INDEX.md    table of contents grouped by doc section

Only the Python standard library is used.

Usage:
    python scripts/sync_docs.py                 # sync everything
    python scripts/sync_docs.py screens config  # re-sync selected pages
    python scripts/sync_docs.py --base-url https://www.renpy.org/dev-doc/html/
"""

import argparse
import concurrent.futures
import html
import os
import re
import sys
import urllib.request
from html.parser import HTMLParser

DEFAULT_BASE = "https://www.renpy.org/doc/html/"
HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(os.path.dirname(HERE), "references", "docs")

# Pages that are large and rarely useful for game development. They are still
# listed in INDEX.md (linking to the website) but not mirrored.
SKIP_PAGES = {"changelog6", "credits", "sponsors", "license", "translating_renpy", "skins"}


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "renpy-skill-docs-sync"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")


# ---------------------------------------------------------------------------
# Index parsing
# ---------------------------------------------------------------------------

def parse_index(index_html):
    """Return (version, [(section, [(page, title), ...]), ...]) from index.html."""
    m = re.search(r">([\d.]+) Documentation<", index_html)
    version = m.group(1) if m else "unknown"

    # Only the first (sidebar) toctree; the article repeats it with subsections.
    body_start = index_html.find('itemprop="articleBody"')
    nav = index_html[:body_start] if body_start > 0 else index_html

    sections = []
    for cap in re.finditer(r'<span class="caption-text">(.*?)</span>(.*?)(?=<p class="caption"|</nav>|$)', nav, re.S):
        title = html.unescape(cap.group(1))
        pages = []
        for a in re.finditer(r'class="toctree-l1"><a class="reference internal" href="([\w\-]+)\.html">(.*?)</a>', cap.group(2)):
            pages.append((a.group(1), html.unescape(re.sub(r"<.*?>", "", a.group(2)))))
        if pages:
            sections.append((title, pages))
    return version, sections


# ---------------------------------------------------------------------------
# HTML -> Markdown
# ---------------------------------------------------------------------------

# Tags whose open/close are counted while skipping an ignored element.
SKIP_COUNTED = {"div", "span", "a", "p", "button", "footer", "nav", "script", "style"}


class MarkdownConverter(HTMLParser):
    """A small converter tuned for Sphinx (Read the Docs theme) output."""

    def __init__(self, page):
        super().__init__(convert_charrefs=True)
        self.page = page
        self.out = []          # list of strings
        self.in_body = False
        self.body_depth = 0    # div nesting inside articleBody
        self.skip = 0          # depth of ignored elements
        self.pre = False
        self.pre_buf = []
        self.pre_lang = ""
        self.lists = []        # stack of "ul"/"ol" counters
        self.heading = None
        self.link = None       # href while inside <a>
        self.link_text = []
        self.sig = False       # inside <dt class="sig ...">
        self.dt_depth = 0
        self.in_table = False
        self.row = None
        self.cell = None
        self.table_rows = []
        self.fresh_item = False  # just opened <li>/<dd>; next <p> continues it

    # -- helpers --
    def emit(self, s):
        if s.strip():
            self.fresh_item = False
        if self.cell is not None:
            self.cell.append(s)
        elif self.link is not None:
            self.link_text.append(s)
        else:
            self.out.append(s)

    def newline(self, n=1):
        if self.cell is not None:
            self.cell.append(" ")
            return
        self.out.append("\n" * n)

    def indent(self):
        return "  " * max(0, len(self.lists) - 1)

    # -- parser callbacks --
    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = a.get("class", "") or ""

        if not self.in_body:
            if tag == "div" and a.get("itemprop") == "articleBody":
                self.in_body = True
                self.body_depth = 1
            return

        if tag == "div":
            self.body_depth += 1

        if self.skip:
            if tag in SKIP_COUNTED:
                self.skip += 1
            return

        if tag in ("script", "style", "footer", "nav") or "headerlink" in cls or "admonition-title" in cls or "sphinx-tabs-tab" in cls:
            self.skip = 1
            return

        if self.pre:
            return

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.heading = int(tag[1])
            self.newline(2)
            self.emit("#" * self.heading + " ")
        elif tag == "div" and "highlight-" in cls:
            m = re.search(r"highlight-(\w+)", cls)
            lang = m.group(1) if m else ""
            self.pre_lang = {"default": "renpy", "none": "", "text": ""}.get(lang, lang)
        elif tag == "pre":
            self.pre = True
            self.pre_buf = []
        elif tag == "p":
            if self.fresh_item:
                self.fresh_item = False
            else:
                self.newline(2)
                if self.lists:
                    self.emit(self.indent() + "  ")
        elif tag == "br":
            self.newline()
        elif tag in ("ul", "ol"):
            self.lists.append(0 if tag == "ol" else None)
            self.newline()
        elif tag == "li":
            self.newline()
            if self.lists and self.lists[-1] is not None:
                self.lists[-1] += 1
                self.emit(self.indent() + "%d. " % self.lists[-1])
            else:
                self.emit(self.indent() + "- ")
            self.fresh_item = True
        elif tag == "dt":
            self.newline(2)
            if "sig" in cls:
                self.sig = True
                self.emit("**`")
            else:
                self.emit("**")
            self.dt_depth += 1
        elif tag == "dd":
            self.newline()
            self.emit(": ")
            self.fresh_item = True
        elif tag in ("em", "cite", "i"):
            if not self.sig:
                self.emit("*")
        elif tag in ("strong", "b"):
            if not self.sig:
                self.emit("**")
        elif tag == "code":
            if not self.sig:
                self.emit("`")
        elif tag == "a":
            href = a.get("href", "")
            if href and not self.sig and self.cell is None:
                self.link = href
                self.link_text = []
        elif tag == "img":
            alt = a.get("alt", "")
            if alt:
                self.emit("[image: %s]" % alt)
        elif tag == "table":
            self.in_table = True
            self.table_rows = []
        elif tag == "tr":
            self.row = []
        elif tag in ("td", "th"):
            self.cell = []
        elif tag == "div" and "admonition" in cls:
            self.newline(2)
            kind = "Note"
            for k in ("warning", "important", "seealso", "tip", "caution", "danger"):
                if k in cls:
                    kind = k.capitalize()
            self.emit("> **%s:** " % kind)

    def handle_endtag(self, tag):
        if not self.in_body:
            return

        if tag == "div":
            self.body_depth -= 1
            if self.body_depth == 0:
                self.in_body = False
                return

        if self.skip:
            if tag in SKIP_COUNTED:
                self.skip -= 1
            return

        if self.pre:
            if tag == "pre":
                self.pre = False
                code = "".join(self.pre_buf).rstrip("\n")
                ind = self.indent() + ("  " if self.lists else "")
                block = "\n".join(ind + line if line else line for line in code.split("\n"))
                self.newline(2)
                self.out.append("%s```%s\n%s\n%s```" % (ind, self.pre_lang, block, ind))
                self.newline(2)
                self.pre_lang = ""
            return

        if tag in ("h1", "h2", "h3", "h4", "h5", "h6"):
            self.heading = None
            self.newline(2)
        elif tag == "p":
            self.newline(2)
        elif tag in ("ul", "ol"):
            if self.lists:
                self.lists.pop()
            self.newline(2)
        elif tag == "dt":
            self.emit("`**" if self.sig else "**")
            self.sig = False
            self.dt_depth -= 1
        elif tag in ("em", "cite", "i"):
            if not self.sig:
                self.emit("*")
        elif tag in ("strong", "b"):
            if not self.sig:
                self.emit("**")
        elif tag == "code":
            if not self.sig:
                self.emit("`")
        elif tag == "a":
            if self.link is not None:
                href = self.link
                text = "".join(self.link_text).strip()
                self.link = None
                self.emit(self.format_link(text, href))
        elif tag in ("td", "th"):
            if self.row is not None and self.cell is not None:
                self.row.append(re.sub(r"\s+", " ", "".join(self.cell)).strip().replace("|", "\\|"))
            self.cell = None
        elif tag == "tr":
            if self.row is not None:
                self.table_rows.append(self.row)
            self.row = None
        elif tag == "table":
            self.in_table = False
            if self.table_rows:
                width = max(len(r) for r in self.table_rows)
                rows = [r + [""] * (width - len(r)) for r in self.table_rows]
                lines = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * width]
                lines += ["| " + " | ".join(r) + " |" for r in rows[1:]]
                self.newline(2)
                self.out.append("\n".join(lines))
                self.newline(2)
            self.table_rows = []

    def handle_data(self, data):
        if not self.in_body or self.skip:
            return
        if self.pre:
            self.pre_buf.append(data)
            return
        if self.cell is None:
            data = re.sub(r"\s+", " ", data)
        self.emit(data)

    def format_link(self, text, href):
        if not text:
            return ""
        if href.startswith("#"):
            return text
        if href.startswith("http"):
            return "[%s](%s)" % (text, href)
        m = re.match(r"([\w\-]+)\.html(#.*)?$", href)
        if m:
            target = m.group(1)
            if target == self.page:
                return text
            return "[%s](%s.md%s)" % (text, target, m.group(2) or "")
        return text

    def markdown(self):
        text = "".join(self.out)
        text = text.replace("¶", "")
        text = re.sub(r"[ \t]+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"\*\*\s*\*\*", "", text)
        text = re.sub(r"\*\*` +", "**`", text)
        text = re.sub(r"(?m)^: ", "  ", text)   # dd marker -> indent
        return text.strip() + "\n"


def convert(page, page_html):
    conv = MarkdownConverter(page)
    conv.feed(page_html)
    return conv.markdown()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pages", nargs="*", help="page names to sync (default: all)")
    ap.add_argument("--base-url", default=DEFAULT_BASE)
    ap.add_argument("--out", default=OUT_DIR)
    args = ap.parse_args()

    base = args.base_url if args.base_url.endswith("/") else args.base_url + "/"
    os.makedirs(args.out, exist_ok=True)

    version, sections = parse_index(fetch(base + "index.html"))
    all_pages = [(p, t) for _, pages in sections for p, t in pages]
    wanted = set(args.pages) if args.pages else {p for p, _ in all_pages if p not in SKIP_PAGES}

    def work(item):
        page, title = item
        md = convert(page, fetch(base + page + ".html"))
        header = "<!-- Source: %s%s.html (Ren'Py %s). Generated by scripts/sync_docs.py; do not edit. -->\n\n" % (base, page, version)
        with open(os.path.join(args.out, page + ".md"), "w", encoding="utf-8", newline="\n") as f:
            f.write(header + md)
        return page, len(md)

    todo = [(p, t) for p, t in all_pages if p in wanted]
    failures = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:
        futs = {ex.submit(work, it): it[0] for it in todo}
        for fut in concurrent.futures.as_completed(futs):
            try:
                page, size = fut.result()
                print("%-28s %7d chars" % (page, size))
            except Exception as e:  # noqa: BLE001
                failures.append(futs[fut])
                print("FAILED %s: %s" % (futs[fut], e), file=sys.stderr)

    # Always rebuild the index so it reflects the current upstream structure.
    lines = [
        "# Ren'Py %s Documentation Index" % version,
        "",
        "Mirrored from %s by `scripts/sync_docs.py`. Each entry links to the local Markdown copy;" % base,
        "pages marked *(web only)* were not mirrored and must be read online.",
        "",
    ]
    for title, pages in sections:
        lines.append("## " + title)
        lines.append("")
        for page, ptitle in pages:
            local = os.path.exists(os.path.join(args.out, page + ".md"))
            if local:
                size_kb = os.path.getsize(os.path.join(args.out, page + ".md")) // 1024
                lines.append("- [%s](%s.md) `%s` (%d KB)" % (ptitle, page, page, size_kb))
            else:
                lines.append("- %s *(web only)*: %s%s.html" % (ptitle, base, page))
        lines.append("")
    with open(os.path.join(args.out, "INDEX.md"), "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))

    print("\nRen'Py %s: %d pages synced, %d failed -> %s" % (version, len(todo) - len(failures), len(failures), args.out))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
