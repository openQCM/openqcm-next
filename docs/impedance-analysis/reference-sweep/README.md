# Frozen reference sweep

`g1.txt` — one acquisition of the **fundamental**, water-loaded, 2026-07-28 17:58,
in the `g<n>.txt` format (frequency [Hz], `V_MAG` [V], `V_PHS` [V]; see
`software/docs/DATA_FORMAT_sweep_data.md`).

**Why it is here and not in `software/openQCM/sweep_data/`.** That directory is
runtime output: the application overwrites it on every sweep, and it is gitignored.
This copy is frozen on purpose, because the worked example in
[`../ALGORITHM.md`](../ALGORITHM.md) §11 walks through it sample by sample — index
12 011, `V_MAG` = 0.194775 V, `V_PHS` = 1.769985 V, down to a published half
bandwidth of 953.124 Hz. An implementation that reproduces those numbers from this
file is correct; one that does not is not. That check is worth 1.3 MB.

Do not overwrite it. If a better reference is ever acquired, add it beside this one
and update ALGORITHM.md §11 to match, so the numbers in the document and the file
they came from never drift apart.
