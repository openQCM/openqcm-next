# Air → water → glucose 5 / 7.5 / 10 % w/v, 2024-05-29: raw sweeps of a second instrument

*Added 2026-10-07 for the paper (`paper/`), from the archive Marco supplied on that date (`glucose_2024-05-29_part1.zip`,
`_part2.zip`, with `MANIFEST_glucose_2024-05-29.txt`). Nothing else under `research/` was touched.*

## Acquisition (conditions of record)

| | |
|---|---|
| instrument | openQCM NEXT, **board not recorded** (serial, DDS clock unknown) |
| sensor | 5 MHz, **not recorded** |
| software / firmware | 0.1.5 (`main` of 2024) / firmware 0.1.5. The firmware has the sweep-average carry-over of 0.1.5a–c (`HANDOFF.md` §3, "Firmware 0.1.5d"): printed `v_i = m_i + v_(i−1)/500`, +0.2 % on the counts. Verified by Marco in the 0.1.5 sketch (lines 476–477, 897–904). |
| sequence | air → deionised water → glucose 5 % → 7.5 % → 10 % (w/v), poured in sequence, one acquisition |
| replicas | three raw sweep sets per phase, overtones 1, 3, 5, 7, 9; −12 kHz/+6 kHz at 1 Hz, 18 001 points; 75 sweeps |
| sensor temperature | 24.95–25.02 °C in the datalog (Peltier set-point 25 °C) |
| liquid temperature | **not measured** |
| glucose preparation, purity | **to be supplied by Marco** (not in the archive) |
| open/short/50 Ω sweeps of this board | none |

## Files

- `data/sweep_raw_2024-05-29.npz` — the 75 `<n>.txt` sweeps exactly as written by software 0.1.5 (18 001 × 3, byte-exact
  round trip with `np.savetxt(fmt='%.18e')` checked when packing), key `<phase>_<rr>/<n>`, phase in `air water gluc05 gluc075
  gluc10`, rr in `00 01 02`, n in `1 3 5 7 9`; `<phase>_<rr>/<n>/mtime` is the file's write time. Pack/unpack:
  `python paper/analysis/pack_glucose.py pack|unpack …`.
- `data/2024-May-29_14-21-38_multi_.csv` — the session's datalog, **production amplitude method of `main` 0.1.5** (f = maximum
  of the fitted magnitude; "Dissipation" = full width 0.3 dB below the maximum, in MHz). 541 rows, 14:22:29–16:00:57, 9 s
  spacing, 75 rows exact duplicates of the previous one.
- `data/2024-May-29_14-21-38_multi_2_extract.csv` — an extract of the same datalog (15:00:32–16:00:57, 386 rows), as
  supplied; kept for completeness, not analysed.

**`<n>.txt` format** (software 0.1.5, `software/docs/DATA_FORMAT_sweep_data.md`): column 1 frequency [Hz]; column 2
`(counts·3.3/4096/2 − 0.9)/0.03`, i.e. the magnitude channel in dB **with the INPB attenuator not undone**; column 3
`(counts·3.3/4096/1.5 − 0.9)/0.01 = 90 − |Δφ|`. The paper's loader (`paper/analysis/data.py`, `glucose_0529()`) converts
with `V_MAG = 0.9 + 0.03·col2 − 0.610692` and `V_PHS = 0.9 + 0.01·col3`; the firmware carry-over is undone on the quantities
proportional to the counts (`qcmchain.undo_firmware_carry`).

**Why the `g<n>.txt` of the archive are not kept.** In software 0.1.5 they are `[f, V_MAG_uncompensated − 0.600, V_PHS]` — the
same two channels with the *wrong* attenuator constant (0.600 V instead of 0.610692 V, corrected on 2026-07-28), not a
conductance. Verified on all 75 pairs: `g[:,1] = 0.9 + 0.03·col2 − 0.600` and `g[:,2] = V_PHS` to 2.2·10⁻¹⁶
(`data.check_g_identity_2024`). They carry no information beyond `<n>.txt` and would invite the 4 % error on M.

## Timing of the replicas against the datalog

The archive stores the write times in UTC (Finder-style zip with extended timestamps); local time on 2024-05-29 in Italy
(CEST) is +2 h. With that offset every replica falls inside its phase of the datalog, and the last replica of each phase is
12–30 s before the next pour:

| phase | replica write times, local (UTC+2) | datalog phase (steps of the fundamental) |
|---|---|---|
| air | 14:49:34, 14:54:17, 14:57:05 | start – 14:57:25 |
| water | 15:01:52, 15:11:44, 15:14:40 | 14:57:47 – 15:15:19 |
| glucose 5 % | 15:17:35, 15:25:32, 15:29:02 | 15:15:47 – 15:29:14 |
| glucose 7.5 % | 15:31:57, 15:39:37, 15:41:18 | 15:29:32 – 15:41:48 |
| glucose 10 % | 15:48:03, 15:52:11, 15:58:10 | 15:41:57 – 16:00:57 |

The +2 h inference is consistent with every phase boundary but is an inference, not a record.

## Other material in the archive, not kept

`README_WATER_GLUCOSE_2024-05-27`: shift values of another day, taken with another chain — not a reference for this dataset
(Marco, 2026-10-07).

## Analysis

`paper/analysis/run_glucose.py` (all estimators of the paper, as-is and firmware-corrected), results in
`paper/analysis/results/glucose_*`; figures 5, 6, 12–14 of the paper.
