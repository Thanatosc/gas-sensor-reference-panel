"""Build an Elsevier elsarticle LaTeX submission from the Markdown sources.

Inputs
------
- `manuscript/cils_draft.md`        body text (drafting notes are stripped)
- `manuscript/uci360_tables.md`     tables, converted to LaTeX tabulars
- `artifacts/UCI360_FIGURE_PACKAGE.md`  figure captions, claim/limitation fields
- `latex/figures/*.pdf`             vector figures

Output
------
- `latex/cils_manuscript.tex`  and a compiled PDF via pdflatex

Design notes
------------
pdflatex is targeted rather than xelatex because Elsevier's system is most
reliable with it, so every non-ASCII character is mapped to a LaTeX command
(see UNICODE below). The bibliography is a manual `thebibliography`: there are
30 references and this avoids shipping a .bib whose keys would have to be kept
in sync with the Markdown's numeric citations.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DRAFT = ROOT / "manuscript/cils_draft.md"
TABLES = ROOT / "manuscript/uci360_tables.md"
PACKAGE = ROOT / "artifacts/UCI360_FIGURE_PACKAGE.md"
OUT_DIR = ROOT / "latex"

TITLE = ("The Exactly-Determined Reference Panel: Why Two-Sample Slope-and-Bias "
         "Recalibration Cannot Be Checked, and Why Larger Panels Are Not Reliably "
         "Safe Either")

# Order matters: longer sequences first where they overlap.
UNICODE: list[tuple[str, str]] = [
    ("\u207b\u00b3", "$^{-3}$"),   # superscript minus-three, as in m^-3
    ("\u207b\u00b9", "$^{-1}$"),
    ("\u00b5g m$^{-3}$", r"\si{\micro\gram\per\cubic\metre}"),
    ("\u00b5g/m\u00b3", r"\si{\micro\gram\per\cubic\metre}"),
    ("\u00b5", r"\textmu{}"),
    ("\u2082", "$_2$"),
    ("\u2083", "$_3$"),
    ("\u00b3", "$^3$"),
    ("\u00b9", "$^1$"),
    ("\u2013", "--"),
    ("\u2014", "---"),
    ("\u00d7", r"$\times$"),
    ("\u2212", "$-$"),
    ("\u0394", r"$\Delta$"),
    ("\u00f6", r'\"o'),
    ("\u00fc", r'\"u'),
    ("\u00e9", r"\'e"),
    ("\u010d", r"\v{c}"),
    ("\u2265", r"$\geq$"),
    ("\u2264", r"$\leq$"),
    ("\u2248", r"$\approx$"),
]


def demojibake(text: str) -> str:
    for src, dst in UNICODE:
        text = text.replace(src, dst)
    leftover = sorted({c for c in text if ord(c) > 127})
    if leftover:
        print("  WARNING unmapped non-ASCII: "
              + ", ".join(f"U+{ord(c):04X}" for c in leftover), file=sys.stderr)
    return text


def strip_notes(md: str) -> str:
    """Remove the drafting-notes block and the working-draft banner."""
    md = re.sub(r"\n---\n\n## Drafting notes.*$", "\n", md, flags=re.S)
    md = re.sub(r"^> Working draft.*?\n\n", "", md, flags=re.S | re.M)
    return md


# Markdown headers are written to be readable in Markdown; in a LaTeX tabular the
# long ones overflow the text block. These abbreviations are applied to header
# cells only, and the full meaning stays in each caption.
HEADER_SHORT: list[tuple[str, str]] = [
    ("Distinct reference values per window", r"Distinct ref.\ values"),
    ("Held-out rows per window", "Held-out rows"),
    ("Lightweight mean ratio", "Mean ratio"),
    ("Lightweight median ratio", "Median ratio"),
    ("Lightweight cells > 2×", r"Cells $>2\times$"),
    ("Lightweight inverted", "Inverted"),
    ("Lightweight improved", "Improved"),
    ("Target-only refit", "Target-only"),
    ("Full retraining", "Full retrain"),
    ("Worst nRMSE ratio", "Worst nRMSE"),
    ("Worst MAE ratio", "Worst MAE"),
    ("Calibrator coefficient", r"Calib.\ coef."),
    ("Held-out calibration slope", "Held-out slope"),
    ("Reference values", r"Ref.\ values"),
    ("Frozen predictions", "Frozen pred."),
    ("Rank agreement", r"Rank agr."),
    ("Median panel residual", r"Med.\ residual"),
    ("Minimum rank agreement", r"Min rank agr."),
    ("Residual d.f.", r"Res.\ d.f."),
    ("Distinct values", "Distinct"),
    (">1.5× nRMSE", r"$>1.5\times$"),
    (">2.0× nRMSE", r"$>2\times$"),
    (">3.0× nRMSE", r"$>3\times$"),
    (">5.0× nRMSE", r"$>5\times$"),
    (">2× MAE", r"$>2\times$ MAE"),
    (">2× on MAE", r"$>2\times$ MAE"),
    ("Rule-fitting windows 4--9", "Rule-fitting 4--9"),
    ("Held-out windows 10--13", "Held-out 10--13"),
    ("First clean N", r"First clean $N$"),
    ("Target windows", "Windows"),
    ("Rows per window", "Rows/window"),
]

# Tables whose natural width exceeds the text block: rotate onto their own page.
ROTATE = {"tab:table2", "tab:table3", "tab:table5", "tab:table6",
          "tab:tables1"}

# Tables with prose cells, which need fixed-width wrapping columns.
COLSPEC: dict[str, str] = {
    "tab:table4": ("p{0.13\\textwidth}p{0.24\\textwidth}p{0.20\\textwidth}"
                   "p{0.22\\textwidth}p{0.11\\textwidth}"),
    "tab:table1": "llrrp{0.11\\textwidth}p{0.13\\textwidth}p{0.11\\textwidth}",
    "tab:tables2": "lp{0.13\\textwidth}p{0.17\\textwidth}rrrr",
    "tab:tables3": "lrlp{0.15\\textwidth}rrrr",
}


def shorten_header(cell: str) -> str:
    for long, short in HEADER_SHORT:
        if cell == long:
            return short
    return cell


def md_table_to_latex(block: list[str], caption: str, label: str) -> str:
    """Convert one pipe table to a booktabs tabular inside a table float."""
    rows = [r.strip() for r in block if r.strip().startswith("|")]
    if len(rows) < 2:
        return ""

    def cells(row: str) -> list[str]:
        return [c.strip() for c in row.strip().strip("|").split("|")]

    header = cells(rows[0])
    align_row = cells(rows[1])
    body = [cells(r) for r in rows[2:]]
    spec = "".join("r" if ":" in a and a.endswith(":") else "l" for a in align_row)

    def fix(cell: str) -> str:
        cell = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", cell)
        cell = re.sub(r"(?<!\w)\*(.+?)\*(?!\w)", r"\\emph{\1}", cell)
        cell = re.sub(r"`(.+?)`", r"\\texttt{\1}", cell)
        cell = cell.replace("%", r"\%").replace(r"\%\%", r"\%")
        # Escape underscores in text only. Inside $...$ an underscore is a
        # subscript and escaping it breaks the expression.
        parts = re.split(r"(\$[^$]*\$)", cell)
        cell = "".join(p if p.startswith("$") else p.replace("_", r"\_")
                       for p in parts)
        return cell

    spec = COLSPEC.get(label, spec)
    rotate = label in ROTATE
    env = "sidewaystable" if rotate else "table"

    lines = [f"\\begin{{{env}}}[htbp]", "\\centering",
             "\\caption{" + caption + "}", "\\label{" + label + "}"]
    lines.append("\\footnotesize" if len(header) > 7 else "\\small")
    if len(header) > 8:
        lines.append("\\setlength{\\tabcolsep}{3pt}")
    # A rotated float still typesets at \textwidth, so after rotation the usable
    # measure is \textheight. adjustbox's max width shrinks only when the tabular
    # actually overflows, so tables that already fit keep their natural size.
    measure = "\\textheight" if rotate else "\\textwidth"
    lines.append("\\begin{adjustbox}{max width=" + measure + "}")
    lines += ["\\begin{tabular}{" + spec + "}", "\\toprule",
              " & ".join(shorten_header(fix(h)) for h in header) + " \\\\",
              "\\midrule"]
    for row in body:
        row = (row + [""] * len(header))[:len(header)]
        lines.append(" & ".join(fix(c) for c in row) + " \\\\")
    lines += ["\\bottomrule", "\\end{tabular}", "\\end{adjustbox}"]
    lines += [f"\\end{{{env}}}", ""]
    return "\n".join(lines)


def extract_tables(md: str) -> tuple[dict[str, str], dict[str, str]]:
    """Return {label: latex float} and {label: caption text} from the tables file."""
    floats: dict[str, str] = {}
    captions: dict[str, str] = {}
    sections = re.split(r"^## (Table [A-Z0-9]+)\s*$", md, flags=re.M)[1:]
    for name, chunk in zip(sections[0::2], sections[1::2]):
        label = "tab:" + name.lower().replace(" ", "")
        lines = chunk.splitlines()
        caption_parts: list[str] = []
        table_block: list[str] = []
        for line in lines:
            if line.strip().startswith("|"):
                table_block.append(line)
            elif not table_block and line.strip():
                caption_parts.append(line.strip())
        caption = " ".join(caption_parts)
        caption = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", caption)
        caption = re.sub(r"(?<!\w)\*(.+?)\*(?!\w)", r"\\emph{\1}", caption)
        caption = re.sub(r"`(.+?)`", r"\\texttt{\1}", caption)
        caption = caption.replace("%", r"\%")
        captions[label] = caption
        if table_block:
            floats[label] = md_table_to_latex(table_block, caption, label)
    return floats, captions


def extract_figure_captions() -> dict[int, str]:
    """Pull figure captions from the figure package so they are never retyped."""
    md = PACKAGE.read_text(encoding="utf-8")
    out: dict[int, str] = {}
    for m in re.finditer(r"^### Figure (\d+).*?^\*\*Caption\.\*\* (.+?)\n\n",
                         md, flags=re.S | re.M):
        number = int(m.group(1))
        caption = " ".join(m.group(2).split())
        caption = re.sub(r"^Figure \d+\.\s*", "", caption)
        caption = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", caption)
        caption = re.sub(r"(?<!\w)\*(.+?)\*(?!\w)", r"\\emph{\1}", caption)
        caption = re.sub(r"`(.+?)`", r"\\texttt{\1}", caption)
        caption = caption.replace("%", r"\%")
        out[number] = caption
    return out


def pandoc(md: str) -> str:
    proc = subprocess.run(
        ["pandoc", "-f", "markdown+tex_math_dollars", "-t", "latex",
         "--wrap=preserve", "--top-level-division=section"],
        input=md, capture_output=True, text=True, encoding="utf-8",
    )
    if proc.returncode != 0:
        print(proc.stderr[-3000:], file=sys.stderr)
        raise SystemExit("pandoc failed")
    return proc.stdout


PREAMBLE = r"""% Generated by scripts/build_latex.py -- do not edit by hand.
% Regenerate with:  python scripts/build_latex.py
\documentclass[preprint,12pt,number]{elsarticle}

\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{textcomp}
\usepackage{amsmath}
\usepackage{amssymb}
\usepackage{graphicx}
\usepackage{booktabs}
\usepackage{siunitx}
\usepackage{rotating}
\usepackage{adjustbox}
\usepackage[hidelinks]{hyperref}
\usepackage{url}

\graphicspath{{figures/}}
\sisetup{detect-all}
\biboptions{numbers,sort&compress}

% Pandoc emits these for tightlist and passthrough spans.
\providecommand{\tightlist}{\setlength{\itemsep}{0pt}\setlength{\parskip}{0pt}}
\providecommand{\passthrough}[1]{#1}

\journal{Chemometrics and Intelligent Laboratory Systems}

\begin{document}

\begin{frontmatter}

\title{TITLE_PLACEHOLDER}

%% Author block withheld for double-anonymised review; supplied in the
%% separate title-page file.
\author{}
\address{}

\begin{abstract}
ABSTRACT_PLACEHOLDER
\end{abstract}

\begin{keyword}
KEYWORDS_PLACEHOLDER
\end{keyword}

\end{frontmatter}
"""


def build() -> str:
    md = strip_notes(DRAFT.read_text(encoding="utf-8"))

    # --- split off abstract and keywords, which live in the frontmatter
    abstract_m = re.search(r"^## Abstract\s*\n\n(.+?)\n\n\*\*Keywords:\*\*(.+?)\n\n",
                           md, flags=re.S | re.M)
    if not abstract_m:
        raise SystemExit("could not locate abstract/keywords block")
    abstract = " ".join(abstract_m.group(1).split())
    keywords = "; ".join(k.strip() for k in
                         abstract_m.group(2).replace("\n", " ").split(";") if k.strip())
    md = md[abstract_m.end():]

    # --- split off references, rendered as a manual thebibliography
    body_md, refs_md = md.split("## References", 1)

    # --- drop the H1 title line if pandoc would duplicate it
    body_md = re.sub(r"^# .*?\n", "", body_md, flags=re.M, count=1)

    body = pandoc(body_md)
    body = re.sub(r"\\hypertarget\{.*?\}\{%\n", "", body)
    body = re.sub(r"\\label\{[^}]*\}\}?", "", body)
    body = body.replace("\\tightlist", "\\tightlist")

    # --- figures, inserted after the paragraph that first cites each
    fig_captions = extract_figure_captions()
    fig_files = {
        1: "figure_01_budget_curves", 2: "figure_02_tail_decay",
        3: "figure_03_slope_convergence", 4: "figure_04_diagnostic",
        5: "figure_05_draw_sensitivity",
    }
    figure_floats = []
    for number, stem in fig_files.items():
        caption = fig_captions.get(number, f"Figure {number}.")
        figure_floats.append(
            "\\begin{figure}[htbp]\n\\centering\n"
            f"\\includegraphics[width=\\textwidth]{{{stem}.pdf}}\n"
            f"\\caption{{{caption}}}\n\\label{{fig:{number}}}\n\\end{{figure}}\n")

    tables_md = TABLES.read_text(encoding="utf-8")
    table_floats, _ = extract_tables(tables_md)

    # --- cross-reference the Markdown's plain "Figure n"/"Table n" mentions
    body = re.sub(r"\bFigure (\d)([ab])\b", r"Fig.~\\ref{fig:\1}\2", body)
    body = re.sub(r"\bFigure (\d)\b", r"Fig.~\\ref{fig:\1}", body)
    body = re.sub(r"\bTable (S?\d)\b", lambda m: f"Table~\\ref{{tab:table{m.group(1).lower()}}}", body)

    main_labels = [f"tab:table{i}" for i in range(1, 7)]
    supp_labels = [k for k in table_floats if k not in main_labels]

    parts = [PREAMBLE
             .replace("TITLE_PLACEHOLDER", TITLE)
             .replace("ABSTRACT_PLACEHOLDER", abstract)
             .replace("KEYWORDS_PLACEHOLDER", keywords)]
    parts.append(body)
    parts.append("\n\\clearpage\n\n%% ---- Figures ----\n")
    parts.extend(figure_floats)
    parts.append("\n\\clearpage\n\n%% ---- Main tables ----\n")
    for label in main_labels:
        if label in table_floats:
            parts.append(table_floats[label])
    parts.append("\n\\clearpage\n\n%% ---- Supplementary tables ----\n")
    for label in sorted(supp_labels):
        if label in table_floats:
            parts.append(table_floats[label])

    # --- bibliography
    entries = re.findall(r"^\[(\d+)\]\s+(.+?)(?=\n\n\[|\Z)", refs_md, flags=re.S | re.M)
    bib = ["\n\\clearpage\n", "\\begin{thebibliography}{99}"]
    for number, text in entries:
        text = " ".join(text.split())
        text = re.sub(r"https://doi\.org/(\S+?)\.?$",
                      lambda m: r"\newblock \doi{" + m.group(1).rstrip(".") + "}", text)
        bib.append(f"\\bibitem{{ref{number}}} {text}")
    bib.append("\\end{thebibliography}\n")
    parts.append("\n".join(bib))
    parts.append("\\end{document}\n")

    # numeric citations: [12,13] -> \cite{ref12,ref13}; ranges expanded.
    # Applied to the body only: the preamble contains \providecommand{..}[1]{#1},
    # whose [1] must not become a citation.
    def cite(match: re.Match[str]) -> str:
        inner = match.group(1)
        keys: list[str] = []
        for piece in inner.split(","):
            piece = piece.strip().replace("--", "-")
            if "-" in piece:
                a, b = piece.split("-")
                if a.strip().isdigit() and b.strip().isdigit():
                    keys += [f"ref{n}" for n in range(int(a), int(b) + 1)]
                    continue
            if piece.isdigit():
                keys.append(f"ref{piece}")
        return "\\cite{" + ",".join(keys) + "}" if keys else match.group(0)

    preamble, rest = parts[0], "\n".join(parts[1:])
    rest = re.sub(r"\[\s*(\d[\d,\-\s]*)\s*\]", cite, rest)
    tex = demojibake(preamble + rest)
    tex = tex.replace(r"\doi{", r"\href{https://doi.org/")
    tex = re.sub(r"\\href\{https://doi\.org/([^}]+)\}", r"\\href{https://doi.org/\1}{\1}", tex)
    return tex


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--no-compile", action="store_true")
    args = parser.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    tex_path = OUT_DIR / "cils_manuscript.tex"
    tex = build()
    tex_path.write_text(tex, encoding="utf-8")
    print(f"wrote {tex_path}  ({len(tex.splitlines())} lines)")

    if args.no_compile:
        return 0
    for pass_no in (1, 2, 3):
        proc = subprocess.run(
            ["pdflatex", "-interaction=nonstopmode", "-halt-on-error",
             tex_path.name],
            cwd=OUT_DIR, capture_output=True, text=True, encoding="utf-8",
            errors="replace")
        if proc.returncode != 0:
            tail = [ln for ln in proc.stdout.splitlines()
                    if ln.startswith("!") or "Error" in ln or ".tex:" in ln]
            print(f"pdflatex pass {pass_no} FAILED", file=sys.stderr)
            print("\n".join(tail[-25:] or proc.stdout.splitlines()[-40:]),
                  file=sys.stderr)
            return 1
        print(f"  pdflatex pass {pass_no} ok")
    pdf = OUT_DIR / "cils_manuscript.pdf"
    print(f"built {pdf}  ({pdf.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
