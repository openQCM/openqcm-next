# Changelog

Reconstruction of the openQCM NEXT development history. Format inspired by
Conventional Commits. Versions are marked by Git tags.

## [v0.1.6G-test] — branch `impedance-analysis` (from v0.1.6-dev)
- Alternative impedance analysis via **conductance spectrum G(f)** derived from
  the AD8302 MAG/PHASE signals (software post-processing, same firmware).
- Core in `processors/Multiscan.py`; offline script `sweep_data/plot_conductance.py`.
- Note: approximate formula; development/DEBUG state. Not production-ready.

## [v0.1.6-dev-073] — `main`
- GUI: buttons reorganized into an "Add-On" menu, Temperature/PID tab widget.
- Robustness: fallback when reading `PeakFrequenciesRT.txt`; exit confirmation.
- `data_view/main.py` refactor. Measurement logic unchanged.
- Firmware updated to **0.1.5a** (POT_VALUE 240, noise reduction).

## [v0.1.6-dev] — `main`
- **Automatic peak detection**: fundamental + overtones [3,5,7,9], auto-classifies
  the quartz @5MHz/@10MHz.
- **TEC current monitoring** (serial command "A").
- **Dark UI + real-time plot** performance (setData, 50 ms timer, TEC SecondWindow).
- Multi-start bugfix; Linux path separator fix.

## [v0.1.5] — `main`
- Production baseline, working and stable.
