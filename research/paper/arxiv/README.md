# arXiv source

`main.tex` (main text) and `si.tex` (Supporting Information) are generated from `../manuscript/manuscript.md` and `../manuscript/supporting_information.md` by `../analysis/md2tex.py` (no pandoc); `references.bib` is a copy of `../literature/references.bib`; `figures/` holds the PDF/PNG figures of `../figures_v2/` (main) and `figures/si/` those of the SI.

Build (done on 2026-10-08 with TeX Live 2026 via TinyTeX; `main.pdf` and `si.pdf` are the compiled outputs, `build/` the logs):

```
pdflatex main && bibtex main && pdflatex main && pdflatex main
pdflatex si   && bibtex si   && pdflatex si   && pdflatex si
```

Suggested arXiv categories: `physics.ins-det` (primary), `eess.SP` (cross-list). The SI is a separate document; wide SI tables are set in landscape. Author list, affiliations and funding are placeholders.
