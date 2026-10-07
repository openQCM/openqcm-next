# Air → water → glucose 5 / 7.5 / 10 % w/v, 2024-05-29: raw sweeps of a second instrument

*Added 2026-10-07 for the paper (`paper/`), from the archive Marco supplied on that date (`glucose_2024-05-29_part1.zip`,
`_part2.zip`, with `MANIFEST_glucose_2024-05-29.txt`). Nothing else under `research/` was touched. An identical copy lives in
`paper/data/glucose-2024-05-29/`; the loader reads this folder first and the copy if it is missing.*

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
| glucose | the 5 % w/v solution is a commercial glucose solution for infusion (Galenica Senese s.r.l., Italy, AIC 029863065): 55 g/L pharmaceutical-grade D-glucose monohydrate (= 50 g/L anhydrous glucose) in water for injections, theoretical osmolarity 277 mOsm/L, pH 3.5–6.5, sterile, pyrogen-free (endotoxins < 0.25 EU/mL), terminally sterilised by moist heat (Eur. Ph.). The 7.5 % and 10 % w/v solutions were prepared in the same way (Marco, 2026-10-07). |
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

**File mtimes are UTC; the datalog clock is local CEST (UTC+2).** The archive stores both for every file (DOS local time
14:49:34 and UTC 12:49:34 in the 0x5455 extra field, confirmed by Marco, 2026-10-07); the datalog writes the local time as
text without a time zone. With the +2 h every replica falls inside its phase of the datalog, and the last sweep of each
phase precedes the first frequency step of the next pour by the margin below (resolution ≈ 9 s, the datalog row spacing):

| phase | replica write times, local (UTC+2) | first datalog row of the next phase | margin [s] (±9) |
|---|---|---|---|
| air | 14:49:34, 14:54:17, 14:57:05 | 14:57:38 | 33 |
| water | 15:01:52, 15:11:44, 15:14:44 | 15:15:28 | 44 |
| glucose 5 % | 15:17:35, 15:25:32, 15:29:02 | 15:29:23 | 21 |
| glucose 7.5 % | 15:31:57, 15:39:37, 15:41:20 | 15:41:57 | 37 |
| glucose 10 % | 15:48:03, 15:52:11, 15:58:10 | (end of log 16:00:57) | — |

Write times are those of the last file of each replica set (`1.txt` … `9.txt` are written within 2 s of each other).

## Other material in the archive, not kept

`README_WATER_GLUCOSE_2024-05-27`: shift values of another day, taken with another chain — not a reference for this dataset
(Marco, 2026-10-07).

## Analysis

`paper/analysis/run_glucose.py` (all estimators of the paper, as-is and firmware-corrected), results in
`paper/analysis/results/glucose_*`; figures 5, 6, 12–14 of the paper.
