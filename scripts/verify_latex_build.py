"""Audit the built PDF for silent LaTeX damage.

Checks the compiled text layer for the failure modes that compile cleanly but
render wrongly: control characters swallowed by TeX, stray command names left as
prose, unrendered markup, and missing floats. Exits non-zero on any finding.

Run after scripts/build_latex.py.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pymupdf

PDF = Path("latex/cils_manuscript.pdf")
TEX = Path("latex/cils_manuscript.tex")
LOG = Path("latex/cils_manuscript.log")

# Command names that appear as bare prose when a backslash has been eaten.
ORPHANS = ["imes", "extbf", "extit", "mathrm", "extbackslash", "oprule",
           "idrule", "ottomrule", "egin{", "nd{", "extmu", "elta", "eq$",
           "extwidth", "extheight", "aggedright", "rraybackslash"]

# Markup that should never survive into the rendered text.
RAW_MARKUP = [r"\*\*", r"^\s*\|", r"\\textbf", r"\\emph", r"\\cite",
              r"\\ref\{", r"\$\$", r"``", r"\\begin", r"\\end"]

findings: list[str] = []
doc = pymupdf.open(PDF)
pages = [p.get_text() for p in doc]
full = "\n".join(pages)

print(f"PDF: {PDF}  pages={doc.page_count}  bytes={PDF.stat().st_size}")

print("\n=== orphaned command names (eaten backslash) ===")
for token in ORPHANS:
    hits = [(i + 1, m.start()) for i, t in enumerate(pages)
            for m in re.finditer(re.escape(token), t)]
    # 'imes' legitimately appears inside 'times'/'sometimes'; filter those
    if token == "imes":
        hits = [(pg, off) for pg, off in hits
                if not re.search(r"[a-z]imes", pages[pg - 1][max(0, off - 1):off + 5])]
    if hits:
        findings.append(f"orphan {token!r} on pages {sorted({p for p, _ in hits})}")
        print(f"  FAIL {token!r}: pages {sorted({p for p, _ in hits})}")
        pg, off = hits[0]
        print(f"       {pages[pg - 1][max(0, off - 60):off + 40]!r}")
if not any(f.startswith("orphan") for f in findings):
    print("  none")

print("\n=== unrendered markup in text layer ===")
for pattern in RAW_MARKUP:
    hits = [i + 1 for i, t in enumerate(pages) if re.search(pattern, t, re.M)]
    if hits:
        findings.append(f"raw markup {pattern!r} on pages {hits}")
        print(f"  FAIL {pattern!r}: pages {hits}")
if not any(f.startswith("raw markup") for f in findings):
    print("  none")

print("\n=== control characters in text layer ===")
ctrl = {c for c in full if ord(c) < 32 and c not in "\n\r\t"}
if ctrl:
    findings.append(f"control chars {[hex(ord(c)) for c in ctrl]}")
    print(f"  FAIL {[hex(ord(c)) for c in ctrl]}")
else:
    print("  none")

print("\n=== floats present ===")
tex = TEX.read_text(encoding="utf-8")
n_fig = len(re.findall(r"\\begin\{figure\*?\}", tex))
n_tab = len(re.findall(r"\\begin\{(?:sideways)?table\*?\}", tex))
n_lab = len(re.findall(r"\\label\{tab:", tex))
print(f"  figure floats {n_fig}, table floats {n_tab}, table labels {n_lab}")
if n_fig != 5:
    findings.append(f"expected 5 figures, found {n_fig}")
if n_tab != 11 or n_lab != 11:
    findings.append(f"expected 11 tables, found {n_tab} floats / {n_lab} labels")

print("\n=== log diagnostics ===")
log = LOG.read_text(encoding="utf-8", errors="replace")
for label, pattern, limit in [
    ("errors", r"^! ", 0),
    ("undefined references", r"Warning: Reference .* undefined", 0),
    ("undefined citations", r"Warning: Citation .* undefined", 0),
    ("missing files", r"File .* not found", 0),
]:
    n = len(re.findall(pattern, log, re.M))
    print(f"  {label:22}: {n}")
    if n > limit:
        findings.append(f"{label}: {n}")
boxes = [float(m.group(1)) for m in
         re.finditer(r"Overfull \\hbox \((\d+\.?\d*)pt too wide", log)]
over = sorted((b for b in boxes if b > 20), reverse=True)
print(f"  overfull hbox >20pt   : {len(over)}  {[round(b) for b in over[:6]]}")

print("\n=== figures rendered, not placeholders ===")
for i, page in enumerate(doc):
    imgs = page.get_images()
    drawings = len(page.get_drawings())
    if imgs or drawings > 40:
        print(f"  page {i + 1}: {len(imgs)} raster, {drawings} vector ops")

print()
if findings:
    print(f"{len(findings)} FINDINGS:")
    for f in findings:
        print("  -", f)
    sys.exit(1)
print("no findings")
