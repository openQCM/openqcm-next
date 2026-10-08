# -*- coding: utf-8 -*-
"""
md2tex.py — converts the manuscript and the Supporting Information (the constrained Markdown subset used in
manuscript/*.md) to LaTeX for arXiv, without pandoc.

    python md2tex.py            → arxiv/main.tex, arxiv/si.tex, arxiv/figures/*.pdf|png, arxiv/references.bib

Supported: YAML front matter (title, date, abstract); # / ## headings; paragraphs; **bold**, *italic*; $...$ and $$...$$
with \tag{n}; [@key; @key2] and [@key, Eq. 13] citations (natbib \citep); ![caption](path) figures (one per paragraph);
pipe tables (converted to tabularx / small longtable); numbered and bulleted lists; `code`; Unicode symbols mapped to
LaTeX where pdflatex needs it. Everything else is passed through.
"""
import os, re, shutil, glob

HERE = os.path.dirname(os.path.abspath(__file__)); P = os.path.normpath(os.path.join(HERE, ".."))
MS, AX, FIG = os.path.join(P, "manuscript"), os.path.join(P, "arxiv"), os.path.join(P, "figures_v2")

UNI = {"−": "$-$", "…": "\\ldots{}", "→": "$\\rightarrow$", "≈": "$\\approx$", "≤": "$\\le$", "≥": "$\\ge$", "×": "$\\times$", "±": "$\\pm$", "°": "\\textdegree{}",
       "Γ": "$\\Gamma$", "Δ": "$\\Delta$", "φ": "$\\varphi$", "δ": "$\\delta$", "ρ": "$\\rho$", "η": "$\\eta$", "μ": "$\\mu$", "σ": "$\\sigma$", "ε": "$\\epsilon$", "ω": "$\\omega$", "π": "$\\pi$", "τ": "$\\tau$",
       "√": "$\\surd$", "Ω": "$\\Omega$", "⁻": "$^{-}$", "¹": "$^{1}$", "²": "$^{2}$", "³": "$^{3}$", "⁶": "$^{6}$", "ᐟ": "/", "·": "$\\cdot$", "∝": "$\\propto$", "≠": "$\\ne$", "≫": "$\\gg$", "’": "'", "“": "``", "”": "''", "–": "--", "—": "---", "\u00a0": "~", "\u202f": "\\,", "½": "$\\tfrac12$"}


SUP = {"⁻": "-", "⁰": "0", "¹": "1", "²": "2", "³": "3", "⁴": "4", "⁵": "5", "⁶": "6", "⁷": "7", "⁸": "8", "⁹": "9", "ᐟ": "/"}


def esc_text(t):
    """Escape LaTeX specials in prose (outside math), map Unicode."""
    t = re.sub("[" + "".join(SUP) + "]+", lambda m: "\x01" + "".join(SUP[c] for c in m.group(0)) + "\x02", t)
    out = []; i = 0
    while i < len(t):
        c = t[i]
        if c == "\x01":
            j = t.index("\x02", i); out.append("$^{" + t[i + 1:j] + "}$"); i = j + 1; continue
        if c in "%&#_":
            out.append("\\" + c)
        elif c == "~":
            out.append("\\textasciitilde{}")
        elif c == "^":
            out.append("\\textasciicircum{}")
        elif c in UNI:
            out.append(UNI[c])
        else:
            out.append(c)
        i += 1
    return "".join(out)


def math_fix(m):
    """Inside math: a few Unicode symbols that may appear."""
    rep = {"−": "-", "Γ": "\\Gamma ", "Δ": "\\Delta ", "φ": "\\varphi ", "ρ": "\\rho ", "η": "\\eta ", "μ": "\\mu ", "π": "\\pi ", "√": "\\sqrt", "×": "\\times ", "·": "\\cdot ", "°": "^\\circ ", "≤": "\\le ", "≥": "\\ge ", "≈": "\\approx ", "…": "\\ldots "}
    for a, b in rep.items():
        m = m.replace(a, b)
    return m


def cites(t):
    def one(m):
        body = m.group(1)
        keys = [k.strip() for k in body.split(";")]
        ks, post = [], []
        for k in keys:
            mm = re.match(r"@([A-Za-z0-9_:-]+)(.*)", k.strip())
            if not mm:
                return m.group(0)
            ks.append(mm.group(1))
            if mm.group(2).strip(" ,"):
                post.append(mm.group(2).strip(" ,"))
        return "\\citep%s{%s}" % (("[%s]" % esc_text("; ".join(post))) if post else "", ", ".join(ks))
    return re.sub(r"\[(@[^\]]+)\]", one, t)


def inline(t):
    """Prose with inline math, citations, bold, italic, code."""
    parts = re.split(r"(\$[^$]+\$)", t)
    out = []
    for k, p in enumerate(parts):
        if k % 2 == 1:
            out.append("$" + math_fix(p[1:-1]) + "$")
        else:
            p = cites(p)
            segs = re.split(r"(\\citep(?:\[[^\]]*\])?\{[^}]*\}|`[^`]+`)", p)
            for j, s in enumerate(segs):
                if j % 2 == 1:
                    if s.startswith("`"):
                        out.append("\\texttt{" + esc_text(s[1:-1]).replace("\\_", "\\_") + "}")
                    else:
                        out.append(s)
                else:
                    s = esc_text(s)
                    s = re.sub(r"\*\*(.+?)\*\*", r"\\textbf{\1}", s)
                    s = re.sub(r"(?<![\w\\])\*(?!\s)(.+?)(?<!\s)\*(?!\w)", r"\\emph{\1}", s)
                    out.append(s)
    return "".join(out)


def table_tex(lines, caption=None):
    rows = [[c.strip() for c in l.strip().strip("|").split("|")] for l in lines if not re.match(r"^\s*\|?\s*-{3,}", l)]
    rows = [r for r in rows if not all(set(c) <= set("-: ") for c in r)]
    ncol = max(len(r) for r in rows)
    small = ncol > 7; wide = ncol >= 8
    env = "longtable" if len(rows) > 25 or wide else "tabular"
    spec = "l" * ncol if not small else "@{}" + "l" * ncol + "@{}"
    L = []
    if env == "tabular":
        # main-text tables: tabularx with wrapping columns so that long cells never overflow the line
        L.append("\\begin{table}[htbp]\\centering" + ("\\scriptsize\\setlength{\\tabcolsep}{2.5pt}" if ncol >= 7 else "\\footnotesize"))
        if caption: L.append("\\caption{%s}" % caption)
        if ncol >= 5:
            L.append("\\begin{tabularx}{\\linewidth}{%s}\\toprule" % (">{\\raggedright\\arraybackslash}X" * ncol))
            env = "tabularx"
        else:
            L.append("\\begin{tabular}{%s}\\toprule" % spec)
    else:
        L.append(("\\begin{landscape}" if wide else "") + "{" + ("\\scriptsize\\setlength{\\tabcolsep}{2pt}" if small else "\\small"))
        L.append("\\begin{longtable}{%s}" % spec)
        if caption: L.append("\\caption{%s}\\\\" % caption)
        L.append("\\toprule")
    L.append(" & ".join(inline(c) for c in rows[0]) + " \\\\\\midrule" + ("\\endhead" if env == "longtable" else ""))
    for r in rows[1:]:
        r = r + [""] * (ncol - len(r))
        L.append(" & ".join(inline(c) for c in r) + " \\\\")
    L.append("\\bottomrule")
    L.append("\\end{%s}" % env + (("}" + ("\\end{landscape}" if wide else "")) if env == "longtable" else "\\end{table}"))
    return "\n".join(L)


def convert(md_path, figprefix="figures/", si=False):
    s = open(md_path).read()
    meta = {}
    if s.startswith("---"):
        end = s.index("\n---", 3); fm = s[3:end]; s = s[end + 4:]
        m = re.search(r'title:\s*"(.*)"', fm); meta["title"] = m.group(1) if m else ""
        m = re.search(r'date:\s*"(.*)"', fm); meta["date"] = m.group(1) if m else ""
        m = re.search(r"abstract:\s*\|\n((?:  .*\n?)+)", fm); meta["abstract"] = " ".join(l.strip() for l in m.group(1).splitlines()) if m else ""
    out = []
    blocks = re.split(r"\n\s*\n", s.strip())
    pending_caption = None
    for b in blocks:
        b = b.strip()
        if not b:
            continue
        if b.startswith("# "):
            t = b[2:].strip(); t = re.sub(r"^(\d+|S\d+)\.\s*", "", t)
            if t.lower().startswith("references"):
                continue
            star = "*" if t.lower().startswith(("data and code", "references")) else ""
            out.append("\\section%s{%s}" % (star, inline(t)))
        elif b.startswith("## "):
            t = b[3:].strip(); t = re.sub(r"^\d+\.\d+\s*", "", t)
            out.append("\\subsection{%s}" % inline(t))
        elif b.startswith("$$"):
            body = b.strip("$").strip()
            tag = re.search(r"\\tag\{([^}]*)\}", body)
            body = re.sub(r"\s*\\tag\{[^}]*\}", "", body)
            body = math_fix(body)
            if tag:
                out.append("\\begin{equation}\\tag{%s}\n%s\n\\end{equation}" % (tag.group(1), body))
            else:
                out.append("\\[\n%s\n\\]" % body)
        elif b.startswith("!["):
            m = re.match(r"!\[(.*)\]\((.*)\)", b, re.S)
            cap, path = m.group(1), m.group(2)
            cap = re.sub(r"^Fig\.\s*S?\d+\.\s*", "", cap)
            fn = os.path.basename(path)
            if fn.endswith(".svg"): fn = fn[:-4] + ".png"
            if fn.endswith(".png") and os.path.exists(os.path.join(os.path.dirname(os.path.join(MS, path)), fn[:-4] + ".pdf")):
                fn = fn[:-4] + ".pdf"
            sub = "si/" if "/si/" in path else ""
            out.append("\\begin{figure}[htbp]\\centering\n\\includegraphics[width=\\linewidth]{%s%s%s}\n\\caption{%s}\n\\end{figure}" % (figprefix, sub, fn, inline(cap)))
        elif b.startswith("|"):
            out.append(table_tex(b.splitlines(), pending_caption)); pending_caption = None
        elif re.match(r"^\*\*Table S?\d+\.\*\*", b):
            pending_caption = inline(re.sub(r"^\*\*Table S?\d+\.\*\*\s*", "", b))
        elif re.match(r"^(\d+\.|-)\s", b):
            items = re.split(r"\n(?=(?:\d+\.|-)\s)", b)
            env = "enumerate" if b[0].isdigit() else "itemize"
            out.append("\\begin{%s}\n" % env + "\n".join("\\item " + inline(re.sub(r"^(\d+\.|-)\s+", "", it.replace("\n", " "))) for it in items) + "\n\\end{%s}" % env)
        elif b.startswith("*") and b.endswith("*") and not b.startswith("**"):
            out.append("\\noindent\\emph{" + inline(b[1:-1].replace("\n", " ")) + "}")
        else:
            out.append(inline(b.replace("\n", " ")))
    return meta, "\n\n".join(out)


PREAMBLE = r"""\documentclass[11pt,a4paper]{article}
%% Generated from research/paper/manuscript/%s by research/paper/analysis/md2tex.py (no pandoc); not compiled in the authoring environment.
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{lmodern}
\usepackage{textcomp}
\usepackage{amsmath,amssymb}
\usepackage{graphicx}
\usepackage{booktabs,longtable,array,pdflscape,tabularx}
\usepackage[margin=2.3cm]{geometry}
\usepackage[numbers,sort&compress]{natbib}
\usepackage{xcolor}
\usepackage{hyperref}
\hypersetup{colorlinks=true,linkcolor=blue!50!black,citecolor=blue!50!black,urlcolor=blue!50!black}
\setlength{\tabcolsep}{3pt}
\setlength{\emergencystretch}{3em}
\title{%s}
\author{openQCM NEXT impedance-analysis working group\thanks{Author list and affiliations to be finalised.}}
\date{%s}
\begin{document}
\maketitle
"""


def write(md, tex, figprefix="figures/", si=False):
    meta, body = convert(md, figprefix, si)
    title = inline(meta.get("title", ""))
    head = PREAMBLE % (os.path.basename(md), title, esc_text(meta.get("date", "")))
    if meta.get("abstract"):
        head += "\\begin{abstract}\n" + inline(meta["abstract"]) + "\n\\end{abstract}\n"
    tail = "\n\n\\bibliographystyle{unsrtnat}\n\\bibliography{references}\n\\end{document}\n"
    open(tex, "w").write(head + "\n" + body + tail)
    print("wrote", tex)


if __name__ == "__main__":
    os.makedirs(os.path.join(AX, "figures", "si"), exist_ok=True)
    for old in glob.glob(os.path.join(AX, "figures", "*.pdf")) + glob.glob(os.path.join(AX, "figures", "si", "*.pdf")):
        os.remove(old)
    for f in glob.glob(os.path.join(FIG, "*.pdf")) + glob.glob(os.path.join(FIG, "*.png")):
        shutil.copy(f, os.path.join(AX, "figures", os.path.basename(f)))
    for f in glob.glob(os.path.join(FIG, "si", "*.pdf")):
        shutil.copy(f, os.path.join(AX, "figures", "si", os.path.basename(f)))
    shutil.copy(os.path.join(P, "literature", "references.bib"), os.path.join(AX, "references.bib"))
    write(os.path.join(MS, "manuscript.md"), os.path.join(AX, "main.tex"))
    write(os.path.join(MS, "supporting_information.md"), os.path.join(AX, "si.tex"), si=True)
