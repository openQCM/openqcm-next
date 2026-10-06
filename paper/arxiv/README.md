# arXiv source

`main.tex` was generated from `../manuscript/manuscript.md` with `pandoc -t latex --natbib` and wrapped in a standard `article` preamble; `references.bib` is a copy of `../literature/references.bib` (62 entries; entries with unverified DOIs carry a `note` field — check them before upload). Figures are the PDF versions of `../figures/`.

Not compiled in the authoring environment (no TeX). Expected build:

```
pdflatex main && bibtex main && pdflatex main && pdflatex main
```

Suggested arXiv categories: `physics.ins-det` (primary), `eess.SP` (cross-list). Pandoc's `longtable` output for the two tables may need `\small` or a `tabular` rewrite for a single-column layout; equation `\tag` numbers are kept from the Markdown source.
