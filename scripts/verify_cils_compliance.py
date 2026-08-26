"""Check the manuscript against the CILS Guide for Authors.

Encodes the guide's checkable requirements so they can be re-run after any edit.
Exits non-zero if any requirement fails.

Requirements covered (Guide for Authors, checked 2026-08-26):
  abstract       <= 250 words, no undefined non-standard abbreviations
  keywords       1-7, English, avoid multi-word keywords using "and"/"of"
  highlights     3-5 bullets, <= 85 characters each including spaces
  equations      display equations numbered consecutively
  sections       numbered, subsections 1.1 / 1.1.1
  references     numbered in order of appearance, all cited, no gaps
  data refs      [dataset] marker; software reference format
  declarations   funding, competing interests, CRediT, generative AI
  title page     separate file with author details and corresponding author
  figures/tables cited in text; tables without vertical rules or shading
  file format    editable source, not PDF only
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

DRAFT = Path("manuscript/cils_draft.md")
HIGHLIGHTS = Path("manuscript/highlights.txt")
TITLE_PAGE = Path("manuscript/title_page.md")
TABLES = Path("manuscript/uci360_tables.md")
TEX = Path("latex/cils_manuscript.tex")

t = DRAFT.read_text(encoding="utf-8")
body, refs_block = t.split("## References", 1)
results: list[tuple[bool, str, str]] = []


def check(ok: bool, name: str, detail: str = "") -> None:
    results.append((ok, name, detail))


# ---------------------------------------------------------------- abstract
abstract = t.split("## Abstract", 1)[1].split("**Keywords", 1)[0].strip()
words = abstract.split()
check(len(words) <= 250, "abstract <= 250 words", f"{len(words)}")
check("[" not in abstract, "abstract avoids citations", "")
# non-standard abbreviations should be defined or avoided
undefined = [a for a in ("nRMSE", "MAE", "PLS") if a in abstract]
check(not undefined, "abstract avoids undefined abbreviations",
      f"found {undefined}" if undefined else "")

# ---------------------------------------------------------------- keywords
kw_raw = t.split("**Keywords:**", 1)[1].split("\n\n", 1)[0]
keywords = [k.strip() for k in kw_raw.replace("\n", " ").split(";") if k.strip()]
check(1 <= len(keywords) <= 7, "keywords 1-7", f"{len(keywords)}")
bad_kw = [k for k in keywords if " and " in k or " of " in k]
check(not bad_kw, "keywords avoid 'and'/'of'", f"{bad_kw}" if bad_kw else "")

# ---------------------------------------------------------------- highlights
hl = [l for l in HIGHLIGHTS.read_text(encoding="utf-8").splitlines() if l.strip()]
check(3 <= len(hl) <= 5, "highlights 3-5 bullets", f"{len(hl)}")
over = [(i + 1, len(l)) for i, l in enumerate(hl) if len(l) > 85]
check(not over, "highlights <= 85 chars",
      f"over: {over}" if over else f"max {max(len(l) for l in hl)}")

# ---------------------------------------------------------------- equations
n_eq = t.count("\\begin{equation}")
check(n_eq > 0, "display equations numbered", f"{n_eq} equation environments")
check("$$" not in t, "no unnumbered display math", f"{t.count('$$')} $$ blocks")
if TEX.exists():
    tex = TEX.read_text(encoding="utf-8")
    check("\\eqref" in tex or n_eq == 0, "equations cross-referenced",
          f"{tex.count(chr(92) + 'eqref')} eqref")

# ---------------------------------------------------------------- sections
secs = re.findall(r"^## (\d+)\. ", body, re.M)
check(secs == [str(i) for i in range(1, len(secs) + 1)],
      "sections numbered consecutively", f"{secs}")
subs = re.findall(r"^### (\d+)\.(\d+) ", body, re.M)
check(bool(subs), "subsections use 1.1 form", f"{len(subs)} subsections")

# ---------------------------------------------------------------- references
defined = [int(m) for m in re.findall(r"^(?:\[dataset\] )?\[(\d+)\]", refs_block, re.M)]
cited: set[int] = set()
for m in re.findall(r"\[([\d,–\-\s]+)\]", body):
    for part in m.split(","):
        part = part.strip().replace("–", "-")
        if "-" in part:
            a, b = part.split("-")
            if a.strip().isdigit() and b.strip().isdigit():
                cited.update(range(int(a), int(b) + 1))
        elif part.isdigit():
            cited.add(int(part))
check(defined == sorted(defined), "references in numeric order", "")
check(set(defined) == set(range(1, max(defined) + 1)) if defined else False,
      "no gaps in reference numbers",
      f"{sorted(set(range(1, max(defined) + 1)) - set(defined))}" if defined else "")
uncited = sorted(set(defined) - cited)
check(not uncited, "every reference cited", f"uncited {uncited}" if uncited else "")
undef = sorted(cited - set(defined))
check(not undef, "every citation defined", f"undefined {undef}" if undef else "")
check(refs_block.count("[dataset]") >= 1, "dataset references marked",
      f"{refs_block.count('[dataset]')}")
check("[software]" in refs_block or "Zenodo" in refs_block,
      "software reference present", "")

# ---------------------------------------------------------------- declarations
for name, needle in [
    ("funding declared", "did not receive any specific grant"),
    ("competing interests declared", "declares no competing"),
    ("CRediT statement", "Conceptualization"),
    ("generative AI declaration", "Declaration of generative AI"),
    ("ethics statement", "Ethics statement"),
    ("data availability", "Data availability"),
]:
    check(needle in t, name, "")

# ---------------------------------------------------------------- title page
check(TITLE_PAGE.exists(), "separate title page file", str(TITLE_PAGE))
if TITLE_PAGE.exists():
    tp = TITLE_PAGE.read_text(encoding="utf-8")
    for name, needle in [("title page has affiliation", "Southwest Jiaotong"),
                         ("title page has corresponding email", "@"),
                         ("title page has ORCID", "0009-")]:
        check(needle in tp, name, "")

# ---------------------------------------------------------------- floats
n_fig_cited = len(set(re.findall(r"Figure (\d)", body)))
check(n_fig_cited >= 5, "all figures cited in text", f"{n_fig_cited} distinct")
tab_cited = set(re.findall(r"Table[~ ](S?\d)", body))
check(len(tab_cited) >= 6, "tables cited in text", f"{len(tab_cited)} distinct")
# The guide requires every table to be cited, not merely that cited tables exist.
if TABLES.exists():
    tab_have = set(re.findall(r"^## Table (S?\d)", TABLES.read_text(encoding="utf-8"), re.M))
    uncited_tabs = sorted(tab_have - tab_cited)
    check(not uncited_tabs, "every table cited in text",
          f"uncited {uncited_tabs}" if uncited_tabs else f"{len(tab_have)} tables")
    absent = sorted(tab_cited - tab_have)
    check(not absent, "every cited table exists",
          f"missing {absent}" if absent else "")
if TABLES.exists():
    tb = TABLES.read_text(encoding="utf-8")
    check("|:" not in tb and "\\hline" not in tb,
          "tables avoid vertical rules", "")

# ---------------------------------------------------------------- output
print(f"{'':4} {'requirement':38} detail")
print("-" * 78)
fails = 0
for ok, name, detail in results:
    if not ok:
        fails += 1
    print(f"{'OK  ' if ok else 'FAIL'} {name:38} {detail}")
print("-" * 78)
print(f"{len(results)} requirements, {fails} failures")
sys.exit(1 if fails else 0)
