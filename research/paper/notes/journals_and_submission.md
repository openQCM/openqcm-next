# Journal shortlist and submission notes

Derived from `../literature/novelty_assessment.md` (2026-10-06, refreshed 2026-10-08) and from the scope of manuscript v0.2 (2026-10-08). Ranked for fit with the present scope (a measurement method with metrological validation on one open instrument, no analytical application).

| rank | journal | why it fits | what the reviewers will ask for | OA |
|---|---|---|---|---|
| 1 | **Measurement** (Elsevier) | metrological framing: estimator bias in closed form, forward-model validity bounds, uncertainty discussion; AD8302 impedance work already published there | an uncertainty budget per estimator; a reference-instrument comparison (listed as remaining experiment #1) | hybrid |
| 2 | **Sensors** (MDPI) | home of Johannsmann 2021 (the fit function), Fort 2024 (QCM-D validation), Leppin 2020; QCM instrumentation routinely published | careful citation of the Johannsmann/Arnau/Siena groups; the second board/sensor | full OA (APC) |
| 3 | **Review of Scientific Instruments** | classic venue for QCM electronics and resonator fitting; the paper is an instrument-plus-method paper | a complete instrument description (available: schematic, firmware, host); absolute accuracy against a reference | hybrid |
| 4 | **HardwareX** | open-source hardware with validation; two openQCM-derived papers already there | BOM, build and test instructions; novelty bar is "reproducible and validated" | full OA |
| 5 | **IEEE Trans. Instrum. Meas.** | estimator comparison, calibration, uncertainty | stronger uncertainty analysis; long review cycle | hybrid |
| 6 | **Measurement Science and Technology** (IOP) | resonator parameter estimation under damping published there | emphasis on the estimator-bias analysis | hybrid |
| 7 | **Sensors and Actuators A** | QCM electronics (Rodríguez-Pardo group) | sensor-performance characterisation (resolution, drift, noise over long plateaus) | hybrid |
| 8 | **IEEE Sensors Journal** | low-cost sensor systems with validation | as Sensors (MDPI) in IEEE format | hybrid |

Not recommended for this scope: *Analytical Chemistry* (requires an analytical application).

**arXiv.** Primary `physics.ins-det`, cross-list `eess.SP` (and optionally `physics.app-ph`). The arXiv source is in `../arxiv/` (`main.tex`, `si.tex`, `references.bib`, `figures/`); it is generated from `../manuscript/manuscript.md` and `supporting_information.md` by `../analysis/md2tex.py` and has **not been compiled in this environment** (no TeX installation): compile `main` and `si` with `pdflatex`/`bibtex` and check the long tables of the SI before upload. The SI is a separate document.

**Before any submission** (from `remaining_experiments.md`, in order of weight for a reviewer): reference-analyser measurement of the same crystal; a dedicated air → water acquisition on both instruments; second board and sensor; measured liquid temperature (or a glycerol series) and tabulated ρη for the glucose solutions; re-acquisition with firmware 0.1.5d; confirmation of the literature items graded I/U in `../literature/literature_review.md` (full texts were not retrievable in this session); author list, affiliations, funding and conflict-of-interest statements.

**Novelty statement (defensible, to be used in the cover letter)** — see `../literature/novelty_assessment.md` §(f), adjusted to the results: the method is a complete, documented and validated signal chain (exact divider inversion of an AD8302 gain/phase detector, resolution of the unsigned-phase fold at resonance, phase-shifted-Lorentzian estimation with the rotation angle identified as the board phase, closed-form biases of the simpler estimators, five-overtone validation in two liquids with released data). The fit function and the hardware blocks are prior art and are attributed.
