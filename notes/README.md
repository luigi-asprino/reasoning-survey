# Notes

LaTeX notes and slides on Description Logic expressivity, OWL 2 profiles and
the entailment regimes of triplestores.

| Path | Description |
|---|---|
| `dl-owl-expressivity.tex` / `.pdf` | Notes on DL naming, OWL 2 profiles, GraphDB rulesets as Horn fragments, empirical results from [`reasoning-capability-test/`](../reasoning-capability-test/README.md), and available reasoners. |
| `slides/dl-owl-expressivity-slides.tex` / `.pdf` | Slide version of the notes. |

The empirical sections summarise the results in
`reasoning-capability-test/graphdb/results/` and
`loading-time-test/graphdb/results/`. Update them together when the
experiments are re-run.

## Building

```bash
cd notes && pdflatex dl-owl-expressivity.tex && pdflatex dl-owl-expressivity.tex
cd notes/slides && pdflatex dl-owl-expressivity-slides.tex && pdflatex dl-owl-expressivity-slides.tex
```

LaTeX auxiliary files (`.aux`, `.log`, `.out`, `.toc`, `.synctex.gz`, …) are
ignored by git.
