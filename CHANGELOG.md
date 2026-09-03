# Changelog

Reconstruction of the openQCM NEXT development history. Format inspired by
Conventional Commits. Versions are marked by Git tags.

## [Unreleased] — `impedance-analysis`

### Changed — the phase fold is decided by the depth of the peak, not by a threshold in degrees (2026-09-03)

`_phase_offset_fold` decided whether the phase folds by testing `min(r)` against
`FOLD_THRESHOLD_DEG_G = 5.0`. ⚠️ **That number cannot answer the question it was asked.** §4.2 of
`ALGORITHM.md` states `min(r) = −δ` at the vertex: it measures the channel **offset**, not whether
the argument crossed zero. The two coincide only while δ happens to be near zero.

- ⚠️ **And δ is not near zero, nor constant.** Measured on one in-specification board, in air, the
  phase baseline falls from **86.2° at the fundamental to 57.8° at the 9th** while δ ranges from
  **−0.90° to +6.67°**. An absolute threshold in degrees is being compared against a reference that
  moves by 28° across the overtones of a single sweep set.
- `_phase_fold_decision()` asks the question that has a physical answer. The AD8302 maps **1.8 V to
  0°** and **0.9 V to 90°**; off resonance the `C0` branch holds the reading near 90°, and the sign
  flips where it reaches **zero** — the peak of `V_PHS`, not 90°. The test is whether the peak gets
  there, normalised by the sweep's own excursion: `depth = (baseline − min) / baseline`, one when
  the phase reaches 0° exactly, more when it overshoots.
- Measured in air, 125 MHz board: depths **1.049 / 1.046 / 1.096 / 1.102 / 0.984**, peak
  0.14–0.42 Γ from the conductance resonance, circle residual 1.5–6.0 % of the radius. The frozen
  water reference from the old board gives 0.985. The documented isopropanol minima of 12–44°
  project to 0.48–0.86.
- `PHASE_FOLD_DEPTH_MIN = 0.88`, ⚠️ deliberately **not** the midpoint: the fold side is measured and
  the no-fold side is projected from files that no longer exist, so the measured side gets the
  wider margin.
- ⚠️ **The peak must BE the resonance**, within `PHASE_FOLD_PEAK_MAX_GAMMA`. A sweep can carry a
  spur that a bare `argmax` would latch onto; a synthetic spike 154 Γ from resonance is rejected.
- ⚠️ **Roundness is not the judge**, and that is deliberate: the note above `_phase_offset_fold`
  records an estimator reverted for buying roundness at the cost of the trajectory. *A continuous
  trajectory is not negotiable; roundness is a diagnostic.* The circle residual and the largest step
  in B are computed **for the log** so the bench can see whether the decision produced a circle;
  they decide nothing.
- `_fold_latched()` requires two consecutive sweeps to agree before the decision changes. Verified
  against an alternating sequence: six alternating sweeps do not move it, two agreeing ones do.
- **Compatibility, measured rather than argued.** On the in-specification board the old threshold
  and the new criterion give the **same answer on all five overtones**. The change removes a latent
  fragility — a criterion resting on a moving reference — without moving a single decision on
  hardware where the old one was right.
- The log prints the numbers behind the verdict, and is keyed on the **decision** as well as on a
  drift in δ past `PHASE_OFFSET_LOG_DEG`. Keying it on δ alone would hide a decision that flipped
  while δ barely moved; keying it on δ rounded to a tenth made one overtone reprint every sweep.
- ⚠️ **The damped-load branch is NOT validated.** Every sweep available comes out "fold", so nothing
  exercises the case where the answer must be "no fold" — the isopropanol run that did no longer
  exists. `Constants.PHASE_FOLD_BY_PEAK_DEPTH = False` restores the threshold exactly.
- The sweeps behind every number are in `research/board-125MHz-air-2026-09-03/`, saved outside
  `sweep_data/` on purpose.

### Fixed — the half-height markers sat on the floor of the plot (2026-09-02)

Two unit mismatches at once, and they compounded. `GBand.half_level` is `baseline + half` on the
**raw conductance in siemens**; what the panel receives is `(G − baseline) × 1000` — **millisiemens,
baseline removed**. Sending the raw level put the markers at **0.0134 on an axis reaching 26.85**,
which is **0.36 % of the plot height**: flat on the axis, invisible, and the header read
`G max 26.85 S | half 0.01341 S`, a pair that cannot both be true.

- `_shipped_half_level()` converts once, where the units are known — in `elaborate_multi`, which is
  the only place that knows both the ×1000 and the baseline it subtracted. The baseline is now kept
  in a name instead of being computed inline and discarded.
- The view's axes said **S** while the numbers were milli. Both are now labelled **mS**, as is the
  header. That mislabelling is what made 0.0134 look plausible rather than absurd.
- Measured end to end on a skewed peak in realistic units: the marker height goes from **0.36 %** to
  **50 %** of the plot span, and both markers intercept the drawn curve to within 0.05 mS.

### Fixed — the drawn band was a symmetric guess, not the measured one (2026-09-02)

Impedance Data View drew `f_r ∓ Γ`. The two half-height crossings Γ is measured from are **not**
symmetric about `f_r` — the peak is skewed by the residual C0 branch, which is the whole reason the
measurement went two-sided in July — so the markers sat off the half height even though the number
was right. On a real fundamental in air: **16.5 S and 10.2 S against a half height of 13.49 S**.

- `_half_bandwidth_G_exact` now returns a `GBand(bandwidth, f_left, f_right, half_level)` instead of
  a bare float. It already computed all four; three were discarded. **`bandwidth` is unchanged**, so
  no published value moves.
- The crossings and the half-height level (in raw G units — the search runs on the baseline-
  subtracted curve, so the level has to carry the baseline back) travel as three trailing fields on
  the GB message. ⚠️ The consumer's `len(data) > N` guards already existed for exactly this, and an
  8-field payload from an older producer still works: verified, the crossings stay NaN.
- The view draws the measured crossings and a dotted line at the half height, so the construction
  can be checked by eye. Where a side has no crossing in the window — damped loads, where Γ reaches
  kilohertz and the window is sized for air — that side alone falls back to `f_r ∓ Γ` and the header
  says which.
- Verified on a peak with two deliberately different half-widths (90 Hz left, 42 Hz right, so the
  crossings are known analytically): Γ comes out **65.7 Hz** against the exact 66.0, the crossings
  land within 0.3 Hz, and the markers sit on the half-height line to 1e-9. The old symmetric drawing
  on the same curve gives **17.59 S and 7.82 S against 13.54** — the shape of the reported symptom.
- ⚠️ A malformed band buffer now degrades to "no crossings" instead of aborting the whole pane
  update. Letting it escape to the outer handler blanked G and B as well, message included.

### Added — Tools > Impedance Data View (2026-09-02)

`ui/impedanceDataView.py`, a live view of the two impedance spectra, one tab per overtone, built to
the same rules as Raw Data View — it **pulls** on a 300 ms timer of its own, it re-resolves the
worker on every tick, it reads **memory only**, and a closed dialog costs nothing because the timer
stops. Sits in Tools directly under Raw Data View.

- **Top panel: conductance G**, with the published peak and band drawn on it — a diamond at `f_r`
  and two markers at `f_r ∓ Γ`, plus the shaded region between them.
- **Bottom panel: susceptance B**, X axis linked to the conductance.
- The header line carries `f_r`, `Γ`, `D = 2Γ/f_r` in ppm and `G max`, so the window agrees with the
  dissipation panel by construction.

⚠️ **It computes nothing, and that is the point.** Raw Data View re-runs the fit in the GUI thread
and has to be careful to use the very parameters the acquisition used; this one reads
`get_G_exact_buffer` / `get_B_exact_buffer` / `get_F_G_values_buffer` and the published
`get_fr_G_buffer` / `get_gamma_G_buffer` — the same arrays the live impedance panel draws — so it
*cannot* disagree with the instrument. The module imports neither `core.resonance` nor anything from
`processors`, and a test asserts it. Do not add a local inversion of the divider here.

⚠️ **`f_r ∓ Γ` is deliberately symmetric while the two real half-height crossings are not.** Γ is
published as their average and the crossings themselves are not published, so drawing them would
mean re-deriving them. The marker *heights* are read off the measured curve at those two
frequencies, which is a lookup rather than a second measurement — verified on a synthetic Lorentzian,
where they land at 0.00165 S against a peak of 0.0033 S, i.e. exactly half height.

- A band wider than the acquired window — which happens on damped loads, the window being sized for
  air — is called out in the header instead of being drawn pinned to the end of the array.

### Fixed — the dissipation cards read 10⁶ times the curve above them (2026-09-02)

`_update_indicator_D` and `_update_indicator_D_single` multiplied the value by `1e6` before printing
it. That was right only while the buffers held Γ in **MHz**, where it produced Hz. Since the pipeline
publishes D in units of 10⁻⁶ the same multiplication printed **26173228.8** on the card while the
curve directly above it drew **26.21** — and, with the panel switched to Γ, **65466132.9** against
65.5 Hz.

- Both indicators now share `_diss_indicator_text`, which formats the value handed to it — the
  **same array the curve is drawn from**, already converted and already n-scaled — with no factor at
  all: two decimals in ppm for D, one in Hz for Γ.
- ⚠️ The factor must not come back. A card that disagrees with its own plot is the defect this file
  keeps producing, and the docstring now says why the multiplication existed and why it is wrong.
- The two panels are the same measurement seen two ways, and now visibly so: Γ = 65.47 Hz at
  f_res = 5 MHz is D = 2Γ/f_res = **26.19 ppm**, which is what the other panel shows. Q ≈ 38 200,
  against the air validation figure of Γ = 62.8 Hz (D = 25.1 ppm) at the fundamental.

### Added — the dissipation panel chooses its quantity, and N-SCALE follows (2026-09-02)

A selector on the dissipation readout card switches the panel between **D (10⁻⁶)** and **Γ (Hz)**.
It answers the question the previous entry left open, because the right n-scaling depends on which
of the two is on screen:

| shown | N-SCALE off | N-SCALE on |
|---|---|---|
| frequency | ÷1 | **÷n** |
| Γ (Hz) | ÷1 | **÷n** |
| D (10⁻⁶) | ÷1 | **÷1, never** |

`D_n = 2Γ_n/(n f₀)` already carries the overtone scaling through the resonance frequency; dividing
again would give `2Γ/(n²f₀)`. `ΔΓ/n = (f₀/2)ΔD` is Johannsmann's Eq. (12). The rule is written out in
`research/qcm_overtone_normalization_note.md`.

- **The buffers and the datalog never change.** `Dissipation_n` is D whatever the screen shows — a
  log that depended on a combo box would be unreadable a week later. Γ is recovered at draw time,
  exactly, as `Γ[Hz] = D[ppm]·1e-6·f_res/2`, from the resonance frequency measured in the same
  sweep. No new queue, no worker plumbing.
- ⚠️ **With SET REF the reference is converted on its own terms and subtracted after.** Converting
  `D − D_ref` instead scales a *difference* by `f_res` and is wrong by `D_ref·(f − f_ref)/2`.
  Measured: **0.0013 Hz** for `D_ref` = 25.1 ppm over a 100 Hz shift, **0.97 Hz** for a liquid
  reference of 387 ppm over 5 kHz, against a Γ of order a kilohertz. Small, never zero.
- The axis caption and the card title follow the selector, and the caption only says `/ n` when the
  panel is actually divided — with D selected and N-SCALE on it does not, because it is not.
- The Δ cursor follows too: `ΔD … ppm` or `ΔΓ … Hz`.
- `_nscaled`/`_nscale_div` now take the channel they are scaling. Frequency is untouched in every
  combination: `Δf/n` is the standard normalisation and stays right.

### Changed — ⚠️ MEASURED VALUES — the dissipation is now D, as Johannsmann defines it (2026-09-02)

`Dissipation_n` used to hold `half_bandwidth/1e6`: **Γ itself** — a *half width*, dimensional, in
MHz — under a column named *Dissipation* and a panel labelled *ppm*. It now holds the **dissipation
factor**

```
D = Q⁻¹ = 2·Γ / f_res          published as D·1e6, i.e. in units of 10⁻⁶
```

following Johannsmann, Langhoff & Leppin, *Sensors* **2021**, 21, 3490, §2 (CC BY 4.0; the
transcribed sections are in `research/files_johannsmann_sensors-21-03490/`). Γ is unchanged and was
never wrong — it is exactly the paper's *half bandwidth at half height*, Eq. (8) — it simply is not
D. The panel's *ppm* label becomes correct without being touched.

- ⚠️ **No single constant rescales an old datalog.** The factor is `2e12/f_res`, so it depends on
  the overtone: **×400 000** at the fundamental, ×133 333, ×80 000, ×57 142, **×44 444** at the 9th.
- ⚠️ **This reconciles the instrument with its own validation.** The air/isopropanol tables further
  down this file were already written in D. Read back as `2Γ/f_res` they give Γ = 62.8 Hz at the
  fundamental in air and 2542 Hz at the 9th in isopropanol — which is what `HANDOFF.md` records
  independently ("isopropanol Γ reaches 2.5 kHz"; the 62 Hz band inside an 18 kHz span). Fed back
  through `parameters_finder_impedance_exact` and the new formula they return **25.12 / 5.60 / 5.40
  / 4.90 / 5.60** against the table's 25.1 / 5.6 / 5.4 / 4.9 / 5.6. The published column was not the
  quantity the instrument had been validated against.
- Verified against the paper's own conversion, Eq. (12) `ΔΓ/n = (f₀/2)·ΔD`: raising Γ by 2.5·n Hz on
  overtone n moves D by **+0.995 ppm** on n = 1, 3 and 9 alike. The missing 0.5 % is the documented
  liquid baseline bias, not the conversion.
- The Δ cursor drops its `×1e6`: the curve is already in ppm. ⚠️ **That line now differs from
  `main` deliberately** — there the curve is a bandwidth in MHz and the factor turns it into Hz —
  and must not be reconciled by a cherry-pick, like `_nscale_div` beside it.
- ⚠️ **`main` is not converted and must not be.** Its column is the *full width at −0.3 dB of the
  baseline-corrected magnitude*: another curve, another threshold, not a half width at half height,
  so `2Γ/f_res` cannot be formed from it. The two branches stay incomparable on that column — now
  for a reason of kind rather than of scale.
- ~~Open: N-SCALE~~ — **settled the same week**, see the entry above this one.
- Full reasoning, with the cross-checks: `docs/impedance-analysis/ALGORITHM.md` §9.

### Docs — the board number is 1900 here too (2026-08-31)

`OPENQCM_SERIALNUMBER` is **1900** (series 19, unit 00) in both worktrees. It arrived on this branch
with the `0.1.5c` cherry-pick, which is to say inside a commit about stopping a sweep — that commit
staged the whole firmware directory and says nothing about the number. The SESSION_PROMPT item
warning that the two worktrees diverge is therefore wrong and is removed.

### Carried from `main` — firmware 0.1.5c stops a sweep (2026-08-31)

`b79b066`. The board sweeps once per command and reads serial only at the top of `loop()`, so after
a Stop it kept sending for the rest of the sweep — about 1.8 s per overtone — and a question asked
in that window came back answered with `amplitude;phase` data, which the firmware check reported as
*Please update firmware version*.

New firmware pair `0.1.5c`, the `0.1.5b` one kept: `'Q'` ends the sweep in progress at the next
whole sample. ⚠️ It also gets a top-level no-op branch, because anything unrecognised falls into the
sweep parser where `atol("Q")` is 0 and the board starts a scan from 0 Hz.

Host: `_drain_serial()` waits for silence before every query, `_reacquire_serial_lock` sends `'Q'`
to a firmware that knows it, and `_board_busy()` reports a busy board as busy instead of as an old
one. A finished peak detection now gives the port back — its completion path never went through
`stop()`.

Verified here after the cherry-pick: both 0.1.5c sketches compile, `Constants.FW_VERSION` is
`0.1.5c`, the app imports.

### Carried from `main` — the device queries come back in standby (2026-08-31)

`24be1c2`. After a Stop or a finished peak detection the two Tools entries stayed greyed out, so
neither the firmware version nor the board number could be asked for again without reconnecting.

⚠️ `stop()` calls `_enable_ui` **before** `worker.stop()` and a second before
`_reacquire_serial_lock()`, so the menu state it computed was out of date. The refresh moves into
`_reacquire_serial_lock()`, where every path that regains the port ends. ⚠️ And `_serial_connected`
was the wrong test: `start()` hands the port over by **closing the handle without dropping the
reference**. `_can_query_device()` asks whether the handle is open and the worker idle, and drives
both the menu and the two guards.

Verified here after the cherry-pick across the six lifecycle states, and the app imports.

### Carried from `main` — disabled menu entries look disabled (2026-08-31)

`b9d1398`. The two device queries were unclickable and still painted like every other entry.
⚠️ Once a style sheet sets a colour on `QMenu`, Qt stops applying its own disabled palette to the
items, so `QMenu::item:disabled` has to be written out; `QMenu::item:selected:disabled` goes with it
so the highlight stops following the cursor over an entry that would do nothing. Applies to every
menu in the application.

### Carried from `main` — the device queries need an open port (2026-08-31)

`ff90b6b`. *Check Firmware Version* and *Check Board Serial Number* talk to the board over the
persistent handle. ⚠️ Disconnected, the firmware query ran anyway and came back empty, which that
code reads as "no firmware information" and answers with *Please update firmware version* — a closed
port reported as an out-of-date board.

Both entries are greyed out unless the port is open and the acquisition idle (while a measurement
runs the child process owns the port), and `get_firmware_version` gets the not-connected guard the
serial-number query already had. The runtime guards stay in both: a shortcut can reach a menu item,
and the automatic query on connect never goes through the menu.

Verified here after the cherry-pick on the three states, and the app imports.

### Carried from `main` — a board reply is its first non-empty line (2026-08-31)

`7a92f6d`. The firmware check kept raising the update warning on the prototype board even after the
`-TEST` version was accepted, and the cause was upstream of the comparison: the reply was parsed
with `rstrip('\r\n')`, which strips only the **trailing** terminator, so a leading blank line
survived and `'\r\n0.1.5b-TEST\r\n'` compared as `'\r\n0.1.5b-TEST'`.

`_first_reply_line()` is the single parsing rule now, for the firmware version and for the
identification number — the second already read replies this way, which is why that path never
showed the fault. ⚠️ The branches that raise the warning printed nothing, so a wrong answer and no
answer were indistinguishable; both log the raw reply now.

Verified here after the cherry-pick: `'0.1.5b-TEST\r\n'` and `'\r\n0.1.5b-TEST\r\n'` both parse
and pass, `'0.1.5a'` and `''` do not.

### Carried from `main` — the firmware check accepts the prototype build (2026-08-31)

`b890039`, code applied clean; only the changelog conflicted and the branch keeps its own. The
no-TEC board answers `0.1.5b-TEST` and the check was exact string equality, so it raised the
firmware-update warning on every connect — on a firmware that speaks the whole protocol, `'S'`
included.

The rule is now `_firmware_is_current()`, one function instead of the four copies it had in
`get_firmware_version`. ⚠️ `Constants.accept_test_firmware` is a **development switch, to set to
`False` before a production build**: a shipped instrument must not accept a prototype firmware
without saying so.

Verified here after the cherry-pick, on both positions: on, `0.1.5b` and `0.1.5b-TEST` pass and
`0.1.5a` does not; off, only `0.1.5b` passes. App imports.

### Carried from `main` — the menu bar is homologous with Q-1 v3.0 (2026-08-31)

`9ec5f2e`. One conflict, in `Tools`, and it is the good kind: `main` added *Check Firmware Version*
below a separator while this branch had already added *Conductance Data* and *Impedance Fit (live)*.
Resolved by keeping both — the branch's two impedance views join the viewer group, the firmware
check stays below the separator where Q-1 puts it. The two documentation files conflicted as usual
and the branch keeps its own.

`View` is reordered to Q-1's shape (panels, plot toggles, separator, Theme), `Help` becomes
*Website* · *Email Support* ― *Check for Updates…* ― *About*, and no objectName changed anywhere.

Verified here after the cherry-pick, dumping the menu tree at runtime:

```
Tools -> Raw Data View · Peak Data View · Raw Data (from sweep files) ·
         Conductance Data · Impedance Fit (live) · Tec Current ―
         Check Firmware Version
```

⚠️ The branch's two impedance entries have no Q-1 counterpart and are not meant to acquire one: they
sit with the viewers, which is where Q-1's grammar puts a view.

### Reverted — the overtone chips keep their 3 px gap (2026-08-28)

`847e87a` carried over, code only. Closing the gap bought 2 px of chip and was not worth how five
touching pills looked. Verified here after the revert: spacing 3, chips 50 / 64 / 78 at rows of
260 / 330 / 400, app imports.

This closes the overtone-chip work for now. The row is back exactly as it was this morning, and
everything the day's attempts measured is on `main` in HANDOFF §3.

### Carried from `main` — no gap between the overtone chips (2026-08-28)

`e247885`, code applied clean. `horizontalLayout_2` goes from 3 px of spacing to 0: the five chips
split whatever the row does not spend, so the four gaps were costing 2.4 px per chip. Verified here
after the cherry-pick: chips 52 / 60 / 66 / 80 at rows of 260 / 300 / 330 / 400, against 50 / 58 /
64 / 78 before, and the app imports.

That exhausts the row. What is left is the cards' margins and the sidebar width itself:
`chip = (sidebar - 48) / 5`.

### Reverted — the overtone chips stretch again (2026-08-28)

`ea105f8` carried over, code only; the documentation files conflicted as usual and the branch keeps
its own. Pinning the chips (`6949237`, widened in `15694d4`) is undone: they share the sidebar's
width again — 50 px at a 260 px row, 64 at 330, 78 at 400, gaps fixed at 3 — and `sidebarPane`'s
maximum is back to 400.

It worked mechanically and was rejected on looks: at a wide sidebar five fixed chips separated by
80 px read as five islands. Second attempt on this branch, second revert; the first was `f995a8e`.
What both attempts established is on `main` in HANDOFF §3, "The overtone chips, and why they still
stretch" — the style-sheet `min-width: 0px` that defeats `setFixedWidth`, the `5*W + 12 <= row`
rule, the sidebar's 48 px inset, the five-to-one cost of chip width against the container minimum,
and the variant nobody has tried yet: chips packed left behind a single trailing spacer.

Verified here after the revert: chips back to stretching on both themes, row minimum 387, container
minimum 435, app imports.

### Carried from `main` — the chips are 72 px wide (2026-08-28)

`e70af23`, code applied clean; the two documentation files conflicted, as they always do here, and
the branch keeps its own. `OVERTONE_CHIP_WIDTH` goes 64 → **72** and `sidebarPane`'s maximum
400 → **520**.

⚠️ **The second half is not optional.** The width is honoured only while `5*W + 12` fits the row:
72 px per chip needs a 372 px row, and behind a 400 px pane maximum the layout squeezed them
straight back down — raising the constant alone changed nothing on screen. Verified here after the
cherry-pick: chips 72 with gaps 3 and 20 at rows of 372 and 440, still 64 at 330 and 48 at 250.

⚠️ **520 is a maximum, not a default.** `mainSplitter.setSizes([280, 700, 380])` is unchanged, so
the sidebar opens at 280 px — a ~232 px row, chips at ~44 — and has to be dragged wider before the
72 px shows. The container's minimum is `row minimum + 48`, measured, so a sidebar of **420 px** is
what it takes to see them at full width without dragging.

### Carried from `main` — the overtone chips stop stretching (2026-08-28)

`1347bae`, applied clean. Each chip is pinned at 64 px with a **`Fixed`** size policy and a stretch
sits between one chip and the next, so widening the sidebar buys **spacing** rather than five wider
buttons. Verified here after the cherry-pick, on both themes, by driving the row layout directly:
chips 64 px with gaps of 3 / 15 / 25 / 35 at rows of 330 / 380 / 420 / 460, and the app imports.

⚠️ Pinning these was tried on this branch before (`22c7bff`, `22c249e`) and reverted in `f995a8e`.
What sank it was `setFixedWidth` on its own: `theme.qss` carries `min-width: 0px` on the chip rule
and a style-sheet min-width beats the widget's own minimum, so the layout item's minimum stays at
8 px however wide the button claims to be. The `Fixed` policy is what stops the row **stretching**
them, and below a 330 px row they are still allowed to shrink — which is why the narrow sidebar
does not clip any worse than before. The row's minimum falls from 387 px to 332 and the sidebar
container's from 435 to 380, so the clipping recorded on 2026-08-27 is 55 px smaller, not gone: the
pane still allows 260.

### Fixed — the impedance panel curves were built in two places (2026-08-28)

The previous two commits changed the conductance and locus series and nothing happened on screen.
⚠️ **They are created twice**: once in `start()` and once in `clear()` — and `start()` calls
`self.clear()` immediately after its own copy has run, so the `clear()` version wins every time.
Editing the other one is invisible by construction.

⚠️ **And `PlotItem.clear()` empties the legend.** `removeItem()` calls `legend.removeItem()` on
everything it removes, so the legend object survives as an empty, invisible box. Measured: two
entries before `clear()`, zero after, legend still alive. That is why the keys appeared when the
panel was built and vanished at the first acquisition.

Both copies are now one `_build_impedance_curves()`: it clears the two panels, re-adds the legend
keys, then creates the five conductance lines, the five locus sample series and the five dashed
circles. Starting from `clear()` every time is what keeps the count at exactly one and two keys —
adding them anywhere else appends a duplicate pair per acquisition. Verified across three
consecutive calls: 1 and 2 entries each time, locus with `symbol='o'` and no pen, conductance a
2 px line, fit dashed, `_pltGB_seq` reset, and an all-NaN `setData` still harmless.

### Fixed — the legends were anchored outside the plot (2026-08-28)

⚠️ **`addLegend(offset=(-10, 10))` freezes the legend where the panel was when it was created.**
A negative x anchors to the right edge, and the anchor is computed once, while the panel is still
its construction size — it does not follow the resize that the layout applies immediately after.
Measured: with the default offset the legend sits at x = 30 before and after a resize; with
`(-10, 10)` it sits at x = 68.6 both times, computed against a 265 px viewbox, so on the real
panels it landed outside the visible area and never appeared. The impedance panels and the three
panes of the live fit window all use the default anchor now, like `_legend_f` and `_legend_D`,
which is why those two were never affected.

### Changed — dots where there is a fit, lines where there is none (2026-08-28)

Refines the previous commit. The **admittance locus** keeps its samples plus the fitted circle as
the only line: the two have to be distinguishable. The **conductance** goes back to a line — it
carries no fit, so nothing needs telling apart, and a spectrum reads better as a curve. The live
fit window already followed this rule: G(f) and B(f) are curves, the locus is samples.

### Changed — ⚠️ temporary: the frequency and dissipation axes are left alone (2026-08-28)

`Constants.plot_reassert_yrange_freq_diss = False`, **to be restored when the vertical axis is
settled**. It is not the same switch as `plot_force_yrange`, which was already False: with that one
off, `_set_yrange_forced` still called `enableAutoRange` on **every sweep**, so a manual vertical
zoom or pan survived exactly one sweep before snapping back. The axis was not locked to a range, it
was locked to the data.

The two panels now go through `_yrange_freq_diss`, which skips the call entirely while the constant
is False. pyqtgraph then turns autorange off by itself the moment the user drags, so the zoom
stays, and **AUTO in Plot Controls brings the automatic framing back**. Temperature is unchanged.

### Changed — the impedance panels say which line is a fit (2026-08-28)

Both panels drew the measurement as a continuous line, and the admittance panel drew the fitted
circle as a second line in the same colour. Nothing on screen said which was which.

The measured series are **samples** now, in both panels: `pen=None` with a size-3 symbol, the same
way Raw Data View draws its raw sweep. The only line left in either panel is the fitted circle,
which is the point — a fit worth drawing over data has to be distinguishable from it.

Each panel carries a legend: *measured* in Conductance, *measured* and *BVD circle fit* in the
admittance locus. ⚠️ **The legend keys are empty proxy items created with the panels**, not the real
series: those are rebuilt on every START, so a legend fed from them would gain a duplicate entry per
acquisition. Verified that the entry count stays at two across a rebuild, and that an all-NaN
`setData` — the path a deselected overtone takes — still raises nothing now that the item is a
scatter.

There is no fit in the Conductance panel and none is added here: the Lorentzian (FIT 2) lives in the
live admittance-fit window, and this panel shows G(f) as measured.

### Fixed — the fit window's chrome ignored the dark theme (2026-08-28)

Its plots followed the theme after the previous commit; the frame around them did not. The window
is a plain `QWidget`, and the application sheet gives a background to `QMainWindow`, `QDialog` and
`#centralwidget` only — none of which it is.

⚠️ **A background rule that misses is not a neutral omission.** `QWidget {{ color: … }}` matched
anyway, so the window took the dark theme's pale text on the platform's light background: the
"freeze" label nearly invisible and the table unreadable, worse than either theme on its own.
Anything added as a top-level `QWidget` rather than a `QDialog` lands in the same hole.

Three changes:

- `ui/theme.py` names `QWidget#impedanceFitWindow` beside the other window classes, and the window
  sets the sheet on itself as well — the same belt-and-braces `ChevronComboBox` uses for its popup,
  which is a top-level container the window's sheet does not reach either.
- **Tables had no rule at all.** `QTableView` / `QTableWidget`, `QHeaderView::section` and
  `QTableCornerButton::section` are styled now, so a table keeps the panel colour instead of the
  platform's white base under inherited pale text. This is the only table in the application today.
- The green / amber / red of the `rms` and `masked` columns are **two sets, one per theme**: the
  inks chosen against white are muddy on the `#37393b` panel. One `_grade()` decides all of them.
  The status line and the footnote take `palette["muted"]` instead of a hard-coded `#888`.

### Changed — the live admittance-fit window follows the theme (2026-08-28)

`ui/impedanceFitWindow.py` was never connected to `ui/theme.py`. It drew on
`Constants.plot_background_color`, a fixed `(25, 25, 25)`, with the matplotlib
default palette — `#1f77b4` / `#2ca02c` / `#d62728` — while every other panel followed the
interface. Now it reads `theme.PLOT[theme]`: background `(43, 43, 43)` on dark and `#f2f4f7` on
light, axis pen and text pen from `palette["axis"]`, titles from `palette["title"]`, measured G, B
and locus in `Constants.plot_color_multi[n]` (the same blue ramp as the main plots), fits and the
`f_s` marker in `#f44336` — the red Raw Data View gives its peak, for the same reason: the derived
quantity drawn over the measurement.

⚠️ **The `parent` was the visible half.** It was opened as `ImpedanceFitWindow(worker, n)` with no
parent, so it inherited no application style sheet and its frame and table stayed in the platform's
own colours while the rest of the GUI was dark. It is now opened with `theme_name` and `parent=self`
plus `Qt.Window`, which is what keeps a parented widget a window of its own — the same construction
Raw Data View uses. It is not given `WA_DeleteOnClose`: unlike Raw Data View it is cached in
`self._window_fit` and reused, so deleting it on close would leave a dangling reference. Being
cached, it is now rebuilt on a theme switch as well as on a change in overtone count, since the
palette is read when the plots are built.

Numerically nothing moved: driven headless on the archived sweeps, the restyled window reports
R1 = 37.36 / 24.97 / 53.15 / 80.00 / 129.71 ohm, identical to an independent computation.

### Docs — the two circle fits, measured (2026-08-28)

`research/admittance-circle-fit/`: analysis, figures, the PDF, and
`compare_circle_fits.py`, which runs both estimators on one archived sweep so the numbers can be
reproduced.

The impedance panel and the fit window draw **different circles from the same buffers** — radius
0.9 % (n=5) to 10.1 % (n=1) apart, the panel's always smaller, so the R1 it implies would read up
to 11.3 % high. Both are kept on purpose.

⚠️ **The cause is the domain, not the algorithm**, and the comment in `_update_impedance_panel`
that guessed otherwise is corrected. Restricting the *geometric* estimator to the same `+-1` half
width gives -9.9 % of the -10.1 %; Taubin plus trimming on the whole band gives -3.8 %. The domain
matters only because the measured locus **is not a circle**: its radial residual is 1.5 % to 4.3 %
of the radius, smooth and systematic (+10 % at resonance, -7 % at `+-1` half width on the
fundamental, turning points exactly at the core boundary), and the disagreement scales with it
across the five overtones — R2 = 0.92, slope 3.0. Where the BVD circle describes the data the two
agree to 0.9 %.

⚠️ The same comment had claimed the core fit "reproduces the offline reference within a few
percent in both air and liquid". On the fundamental of this sweep it is 10 %, in air.

Neither estimate reaches the datalog: both views are display-only and the logged values still come
from the approximate formula in `MultiscanProcess`.

### Carried from `main` — the real-time time axis is the Q-1 one (2026-08-28)

`c13f45e`, applied clean on `constants.py`, `mainWindow.py` and `dataLogView.py`. The four live axes
print `0 / 45 / 2:00 / 5:00 / 1:02:05` under **`Time (hh:mm:ss)`** instead of bare seconds under
`Time (Sec)`. The plotted x values do not move — still epoch microseconds — so the buffers, the
datalog and the Δ cursors are untouched; only the tick labels are relative.

`Constants.DateAxis` is gone, replaced by `ElapsedTimeAxis` plus the shared
`format_elapsed_seconds`. ⚠️ **Checked here specifically**: no branch-only code referenced the
removed class, and the conductance views draw against frequency, not time, so nothing on this branch
loses an axis. Verified after the cherry-pick — `py_compile`, the app imports, and both axes produce
the same five tick strings as on `main`.

The defects that go out with the seconds axis: the raw epoch printed for the whole warm-up
(`1787904318`), no reference reset between runs, a NaN reference raising out of the paint path, and
a reference taken from `buffer[0]` — the **newest** sample, since `RingBuffer.get_all()` returns
newest-first — instead of `np.nanmin`. `self.start_time` is microseconds in both modes now.

### Carried from `main` — datalog file names follow the Q-1 rule (2026-08-28)

`00481a1`, applied clean: `switcher.py` was already identical on the two branches, and
`constants.py` / `worker.py` / `DATA_FORMAT_sweep_data.md` auto-merged around the impedance work.

`2026-Jul-29_17-03-49_multi_.csv` becomes `2026-08-28_09-56-55_multi.csv`, and a single-overtone run
`2026-Jul-28_19-34-16_fundamental.csv` becomes `..._F0.csv`. The prefix is `%Y-%m-%d_%H-%M-%S`, so
the alphabetical order of `logged_data/` is the chronological one — `Jul` sorted before `Jun` — and
the switcher labels are `F0 F3 F5 F7 F9`, which also takes the space out of the file name. The
multiscan label loses its trailing underscore, a separator with nothing after it; that part is not
from Q-1, which has no multiscan mode.

⚠️ Two copies of the name would have defeated the rename and are gone with it: `Worker.start()` held
its own copy of the format string, so editing the constant renamed nothing, and
`Constants.csv_filename` / `csv_sweeps_export_path` were `strftime` calls **in the class body**,
carrying the moment the module was imported rather than the moment START was pressed. The raw-sweep
dump path now derives from the run's own timestamp inside `store_data`.

Nothing on this branch reads a datalog file name — the conductance viewer works from `g<n>.txt` in
`sweep_data/`, which this does not touch. Verified here after the cherry-pick, not only on `main`:
`py_compile`, the app imports, no reference left to either removed constant anywhere in the
branch-only code, and the names recomposed for every mode.

### Carried from `main` — the sidebar width attempt, tried and reverted (2026-08-27)

`f995a8e` reverts it (one conflict again on the three-pane `setSizes`, back to `[280, 700, 380]`).
The chips share the row as they always did, and the pane is 260/400 again. What follows is kept
because the measurement is worth having, not because the code still does it.

`d61647e`, one conflict: the splitter has **three** panes here (sidebar | plots | impedance dock),
so `setSizes` keeps its three-way form with `SIDEBAR_MIN_WIDTH` in the first slot.

The sidebar's scroll area is `widgetResizable` with the horizontal bar **off**, so a container wider
than the viewport is not scrolled — it is silently **clipped**. The container's minimum is 371 px
and the pane's was 260, opened at 300, so the cards lost their right edge. `SIDEBAR_MIN_WIDTH` = 380
now, maximum 460. Numbers across the day's commits on `main`, CHANGELOG *Changed*.

### Carried from `main` — Plot Controls in two rows, chips that stop stretching (2026-08-27)

`45da71c`, applied clean. AUTO / CLEAR on one row and SET REF / N-SCALE on the next, in a
`QGridLayout` with the slack in an empty third column. **N-SCALE is brown while off and blue while
on** — the other way round from Connect and the temperature toggle, deliberately: it is a checkable
state, so brown means measured hertz and blue means divided by n. The overtone chips get the
temperature ON / RESET treatment, natural width plus a trailing spacer, instead of sharing whatever
width the sidebar has — ⚠️ **and they still do**: pinning them (`22c7bff`, `22c249e`) was reverted
in `f995a8e`, because a fixed width cannot both fit the narrowest sidebar and stay readable. ⚠️ `setFixedWidth` alone did not hold: `theme.qss`
carried `min-width: 0px` on the chip rule, and a style-sheet min-width overrides the widget's own
minimum — the buttons reported 75 and rendered at 42. Reasoning on `main`, CHANGELOG *Changed*.

Verified here with the same gates: the grid holds the four buttons one per cell with the stretch on
column 2, the chip row ends in an expanding spacer, and the unchecked N-SCALE renders 260 brown
pixels and no blue while the checked one renders 260 blue and no brown, on both themes.

### Changed — N-SCALE divides dissipation too, which `main` does not (2026-08-27)

`17a3561` carried clean; this commit is the branch's own behaviour on top of it.

The divisor reaches the four dissipation assignments in `_update_plot`, the Δ-cursor readout for
**both** channels, and the dissipation axis label, which gains "/ n" alongside the frequency one.

⚠️ **The difference from `main` is deliberate and specified, not drift**, and must not be reconciled
by a cherry-pick in either direction: what the dissipation panel holds is not the same quantity on
the two branches. The divisor's docstring says so at the point where someone would be tempted to
"fix" it, and the verification suite reads which contract it is checking from the environment — on
`main` all four dissipation assignments must be **unwrapped**, here all four must be **wrapped**, and
the same gates run on both worktrees.

### Carried from `main` — Plot Controls > N-SCALE (2026-08-27)

`17a3561`, applied clean. Each overtone's frequency is drawn divided by **n** (1, 3, 5, 7, 9) while
the button is held down, so the five can be read against one another. It scales whatever is drawn —
the shift when a reference is set, the absolute frequency when it is not. ⚠️ Display only: the
buffers, the datalog and the status bar keep the measured values. Details on `main`, CHANGELOG
*Changed* and HANDOFF §3.

### Carried from `main` — the plot right-click menu acted on the wrong plot (2026-08-27)

`3ef2e27` clean, `2b7db5a` with one conflict: this branch adds `_pltG` and `_pltGB` to the target
list and their two canvases to the connections. Resolved by keeping the six targets and taking
`main`'s consolidation around them.

The hit test compared a click against rectangles measured in **other scenes** — `sceneBoundingRect()`
is in the coordinates of the item's own scene, and every `GraphicsLayoutWidget` owns a separate one
whose origin is its own top-left corner. Full numbers on `main`, CHANGELOG *Changed* and HANDOFF §3.

⚠️ **This branch felt it hardest.** `main` has four plot targets over three scenes; here it is
**six over five**, because the impedance dock's conductance and admittance views joined the same
set. The Impedance Fit window is worse still: `PlotMenu` is attached per tab, so five tabs are five
more scenes in one target list, and every tab after the first was answering with tab 0's plots.

The main window also drops its own copy of the menu here, as on `main`: the defect existed twice
because the menu existed twice. Verified in this worktree with the same two suites — all panels
answer for themselves across the scenes, the cross-scene coincidences the layout contains are
asserted still present and all resolved correctly, the Δ-cursor item appears only where cursors
exist, and the phase twin still follows `_plt0`'s grid.

### Fixed — the conductance viewer called hide() on a window that no longer exists (2026-08-27)

`_conductance_data_plot` is branch-only and had copied `_raw_data_plot`'s opening line,
`self.window_pro.hide()`. That attribute went away with the matplotlib log viewer carried below,
and the call is the **first statement of the method, outside its `try`** — so `Tools > Conductance
Data` would have raised `AttributeError` before drawing anything. Removed rather than repaired:
hiding an unrelated window was never part of plotting conductance. `main` lost the same line from
`_raw_data_plot` in the same port; this copy was invisible to that commit, and the gate that caught
it was the one asserting `mainWindow.py` no longer mentions `window_pro`.

### Carried from `main` — the two-window log analysis, and the retirement of `data_view/` (2026-08-27)

`1a073d9`, `600a33b`, `6a8779f`, all three applied clean.

`Tools > Log Data` used to open a second, matplotlib viewer of the same log files. That entry is
**gone** (`bdb4b48`, `fbefaa8`, both applied — the first with two conflicts, this branch's two extra
Tools entries and its own copy of the handler): it opened the same Datalog View `File > Open Log…`
opens, so it was two menu items for one window. `openQCM/data_view/` is removed with it. Its two-window
analysis went first into `core/logAnalysis.py` and then into Datalog View's own panel, as draggable
bands rather than four spin boxes — that was the condition for deleting the package.

⚠️ **Four measured defects went out with the move**, and the numbers the old window printed for them
were wrong, not differently rounded: the 9th overtone reported the **7th's** Hadamard deviation
(0.03 where the answer is 1.30), the final window was normalised by the initial window's length, the
Hadamard loop folded the run's last sample into a window starting at sample 0, and a window reaching
past the end of the run lost its last sample. Full numbers on `main` — CHANGELOG *Changed*, HANDOFF
§1 — and not repeated here.

Verified here the same way as on `main`: the panel's text equals `format_report()` on the same
inputs character for character, moving the reference cursor leaves every reported number unchanged,
`openQCM.data_view.main` no longer imports, and this branch's `mainWindow.py` mentions neither the
package nor `window_pro` — which is how the conductance defect above surfaced.

### Changed — the two impedance views move into a card (2026-08-27)

The right-hand dock was the only plot area in this GUI still drawn on bare window background: a
loose label, then the splitter, no frame. `_build_impedance_panel` now puts the conductance
spectrum and the admittance locus in a **compact card** — the same one the frequency and
dissipation readouts wear above their own plots — and the floating "Impedance — exact formula"
label becomes the card's title, so the panel carries one label instead of two. The splitter is
unchanged: both views still collapse.

The look comes from the `cardCompact` property added to the shared style sheet on `main`
(`c43b5cf`, carried below), not from a name `theme.py` would have to know. ⚠️ The property is set
in the builder, which runs at `setupUi()`, **before** `_apply_theme()` puts the sheet on the
window: Qt evaluates property selectors at polish time and a later `setProperty` would do nothing.

Verified off the real builder rather than a mock: the card is the two plots' ancestor, the old
`impedanceHeader` label is **gone** rather than hidden, the title is not duplicated as a loose
label, the splitter still holds both views and both stay collapsible, and — rendered, on both
themes — the card with the property does not look like the same card without it.

### Carried from `main` — compact cards opt in by property (2026-08-27)

`c43b5cf`, applied clean. `QGroupBox[cardCompact="true"]` joins the two `#groupFreqReadout` /
`#groupDissReadout` rules in `theme.qss`, so a card built on this branch can take the compact look
without adding a dead `#name` selector to a file `main` also uses. Measured there on Qt 5.9.7: a
box that sets the property renders pixel-identical to one named `groupFreqReadout`.

### Carried from `main` — the two curve palettes and the grey plot panel (2026-08-27)

`8dc1cf7`. One whitespace conflict in `constants.py` (this branch has a bare blank line where `main`
has a line of spaces, and `plot_color_multi_g` sits between the two palettes); everything else
applied clean.

Dissipation gets its own brown ramp (`Constants.plot_color_multi_diss`), both ramps are now
specified in Rec. 709 luminance, and `theme.PLOT[*]["bg"]` reads the interface's own window colour
so the light plot panel is `#f2f4f7` instead of white. The reasoning is on `main` — CHANGELOG
*Changed*, HANDOFF §3 — and is not repeated here.

Verified here the same way as on `main`, by reading the pens and swatch stylesheets back out of a
live `DataLogViewDialog` rather than out of `Constants`: both ramps lightening, brown steps 35 ± 0,
minimum blue step 28, the three identity blues pinned, the dark panel still exactly `(43,43,43)`,
and both series' palest entry 33 from the light panel. This branch's `mainWindow.py` has all seven
`_pltD` sites on the brown and no live `_pltD` site left on the blues.

⚠️ **Known, not addressed here**: `Constants.plot_color_multi_g`, the hex palette the conductance
plots use (`sweep_data/plot_conductance.py`, 26 call sites), is branch-only and is a copy of an
**older** blue list — `#4663FF`, `#7AA0FF`, `#ADB6FF`, `#FFE4FF` are not, and never were, the
current `plot_color_multi`. It also colours the phase and the raw magnitude plots, not just the
conductance. Aligning it is a decision about those offline figures, not a port of this commit.

### Carried from `main` — combo and spin box restyle (2026-07-29)

`97e2caf`, `1c6bbab`, `b3f9760`, all applied clean. The platform arrow on a `QComboBox` — a square
button with a hard divider — is replaced by a chevron the widget paints itself (`ui/widgets.py`), and
the spin boxes get the same treatment; their buttons stay clickable, only the border and arrow are
removed. The popup is styled on its own objects because its container is a top-level window the main
window's style sheet does not reach, which also meant its colours ignored a theme switch.

Verified here: all five combos and all five spin boxes converted, the popup container takes the
palette's panel colour on both themes with its frame removed, and this branch's seven Tools entries are
untouched. `impedanceFitWindow.py` needed nothing — its overtone combo became the tab bar earlier
today.

⚠️ ~~**Known, not addressed** (same on `main`): the four `QSpinBox` in
`data_view/qt_designer_ui.py` keep the platform look.~~ Moot since 2026-08-27: that viewer was
retired and the package removed.

### Carried from `main` — status bar (2026-07-29)

`d0def43`, applied clean on all three files. The machine state now lives in the colour of **one dot**
(`statusIndicator`) with plain text beside it, as in Q-1 v3.0: NEXT used to say it three times — a
coloured pill, a `<font color>` tag inside every message, and the literal word "Infobar" in front of
each one. Messages are rewritten into Q-1's short register, the connection lifecycle finally reaches
the message line, and the multiscan branches now set a state colour, which neither the dot nor the old
pill ever did.

Checked here that nothing of the old scheme survived on this branch: no `_status_pill`, no
`● Program Status`, no `<font color>` in the bar, no `color_err`. All 19 live message texts match
`main`'s, so this branch had no message of its own left in the old verbose register, and the multiscan
conversion landed in all four branches. The dot cycles grey → green → red as expected and the extra
Tools entries are untouched.

### Carried from `main` — harmonic numbering (2026-07-29)

`78ef8fe`, applied clean. The main window called the fundamental `F0` in the pills, both readout
cards, the hidden radios and the plot legend, while the new views name overtones by harmonic order —
the same resonance read `F0` in one window and `F1` in another. Displayed text only: the widget names
keep the historical `F0` because the controller reaches them as strings. Verified on this branch that
the labels read `F1`/`D1`/`1st` and that `overtoneBtn_F0`, `radioBtn_F0`, `label_F0_col`, `F0` and
`D0` all still resolve.

### Carried from `main` — Datalog View (2026-07-29)

Four more cherry-picks, all clean: `dd5fb37`, `badd438`, `129471d`, `c0a1a92`. Details in `main`'s
CHANGELOG.

- **Datalog View** (`ui/dataLogView.py`, **File → Open Log…**, Ctrl/Cmd+O): opens a datalog and shows
  frequency and dissipation as the shift from a **movable reference cursor**, with a control panel
  carrying the reference readouts and the overtone pills, and temperature absolute in its own small
  panel. Verified here against this worktree's **own** 20 logs — all parse, and the largest
  five-overtone one gives F1..F9 pills, readouts equal to the mean of five samples at the cursor, and
  a cursor that stays in step across both panels.
- `QDialog` joins the theme's window-background rule, so Raw Data View, Peak Data View and Datalog
  View follow light/dark instead of leaving a platform-coloured frame around dark canvases.
- The Open Log handler imports `QFileDialog` explicitly: `mainWindow.py` has no `QtWidgets`, and the
  widgets are reachable as `QtGui.*` only because pyqtgraph injects them there.

⚠️ **Not ported:** `da81e2b`, which restores `Calibration.py`'s CRLF endings after a script normalised
them on `main`. The same mistake was caught here before committing, so this branch's file never lost
them and the patch has nothing to apply.

### Carried from `main` — Peak Data View (2026-07-29)

Two more cherry-picks, `8c40c58` and `c06963f`. Details in `main`'s CHANGELOG; what is specific here:

- **`Constants.BASELINE_POLY_ORDER`** replaces the literal `8` of the calibration baseline. Main had
  seven call sites; **this branch has two more that main could not know about** — `baseline_coeffs_Vmag()`
  in `Multiscan.py` and the same V_MAG baseline in `sweep_data/plot_conductance.py`. Both read the
  constant now: same order, same purpose, and leaving them behind would have recreated the divergence
  one file over. Value unchanged, so no measurement moves.
- **Peak Data View** (`ui/peakDataView.py`, **Tools → Peak Data View**) applied clean. It reconstructs
  the baseline from that constant and re-derives the phase peak, which is not recorded — see `main`'s
  entry. Verified on this branch against the same 5 MHz calibration: five peaks labelled F1..F9, phase
  peaks within their search window, amplitude-to-phase disagreement of −500, −500, +500, −2500 and
  −2000 Hz.

### Changed — Tools > "Impedance Fit (live)": one tab per overtone (2026-07-29)

The window now matches Raw Data View's shape. The overtone combo box is gone: a `QTabWidget` with
one tab per overtone is the selector, labelled from `rawDataView.OVERTONE_NAMES` so one list names
the overtones in both live windows.

Each tab owns its own three panels — G(f) with the FIT 2 Lorentzian, B(f) beneath it sharing the x
axis, and the aspect-locked admittance locus with the fitted circle and the `f_s` marker — so a tab
switch is instant and each overtone keeps its own zoom, which a single shared canvas could not do.
The cost is three empty plots per overtone.

**The cost profile is unchanged on purpose**: every overtone is still refitted on every tick, because
the table below shows them all, and only the visible tab's curves are updated. Switching tab redraws
from the cached fit rather than recomputing it. The table stays one overview across all overtones —
that is the point of it — and clicking a row raises that overtone's tab.

Verified offscreen against a synthetic series-RLC admittance with a C0 offset: five tabs, all five
overtones fitted in one tick and the table filled, only the visible tab drawn, the tab switch drawing
from cache, the row click selecting the tab, and freeze/hide still stopping the timer. The fits
recover `f_s`, `Gamma` and `R1` exactly on that input, at 0.00 % circle residual.

### Carried from `main` by cherry-pick (2026-07-29)

Nine commits, one at a time, `9694d89`..`b6061b0` plus `92ce817` on `main`. The full rationale and
the measured evidence are in `main`'s CHANGELOG; what matters here is how each one met the impedance
work. The per-commit reconciliation notes are in HANDOFF §2, "ported with conflict resolution".

- **`core/resonance.py`** — the filtering/fitting chain and the band walk in one module, imported by
  both acquisition processes and by every viewer. `savitzky_golay` and `parameters_finder` had three
  copies, and the one in `sweep_data/plot_sweep_spline.py` had already drifted: it returned the
  sample index instead of interpolating, overstating the band by up to 2%. On this branch
  `elaborate_multi` is where the two lines of work meet — **all five** Savitzky-Golay calls now go
  through the shared module (the impedance work added four beyond `main`'s one: the phase,
  `Vmag_corr`, `Vphase` and the raw `Vmag`), and the magnitude spline became
  `resonance.spline_fit`, verified **bit-identical** on the snapshot sweeps. The published frequency
  and bandwidth still come from the conductance path, untouched; the magnitude-path band survives
  only to raise the error flags.
- **`core/averaging.py`** — `robust_mean` replaces `scipy.stats.trim_mean` at the six averaging
  sites. `trim_mean` cut `int(proportiontocut * N)` per tail, which is zero below N=10, so outlier
  rejection was an accident of `Constants.environment == 10` rather than a property of the average.
  Bit-identical for N ≥ 10.
- ⚠️ **DEV ONLY — `Constants.environment` 10 → 3** so test runs reach steady state almost
  immediately. **Restore 10 before any production build**, on this branch as well as on `main`. The
  reason is now purely metrological — how many sweeps go into each logged point — because
  `core/averaging.py` removed the robustness dependency. Note the values logged at N=3 differ from
  those logged at N=10 by construction: fewer sweeps averaged.
- **`ui/rawDataView.py`** — Tools → **Raw Data View**: live amplitude and phase sweep per overtone,
  five tabs, with the peak, the dissipation band and the threshold taken from `resonance.py` at full
  sample resolution. Pull model with its own timer; reads memory only, never a file.
- **`common/sweepDump.py`** — the raw sweep dump becomes a development tool, off by default
  (`OPENQCM_SWEEP_DUMP=1` to enable). This branch's **second** series, `g<n>.txt` with the divider's
  raw `V_MAG`/`V_PHS`, goes through the same module via its `prefix` parameter, which was added on
  `main` first so this branch needs no copy of its own. `Tools → Raw Data (from sweep files)` is
  hidden while the dump is off.
- **Phase sweep into the GUI process** (`consume_queue_P_multi`), which also closed a `mp.Queue`
  that `MultiscanProcess` filled on every sweep and nobody drained. Both it and this branch's
  `consume_queue_GB_multi` are drained in `stop()` and in `_update_plot`.
- **Single-overtone warm-up fix** — `Serial.elaborate` raised `UnboundLocalError` on every sweep
  before the buffer filled, swallowed by a bare `except:`, so the first nine sweeps never reached
  the plots.

⚠️ **Known, not addressed:** `sweep_data/plot_conductance.py` still carries its own copy of
`savitzky_golay`. It differs from `core/resonance.py` only in the docstring and in the wording of
its exception messages — the numerical body is identical, so it is a benign duplicate rather than a
divergent one, unlike the `plot_sweep_spline.py` copy that was removed. Worth folding in next time
that file is touched.

### Added — `docs/impedance-analysis/ALGORITHM.md`, the reference for the whole measurement (2026-07-28)
- Every step from ADC counts to the logged frequency and bandwidth, with the code path, the derived
  constants, the reason each guard exists, and a **worked numerical example** on a committed
  `g<n>.txt` that a reimplementation can be checked against sample by sample.
- Preceded by a **verified** account of what this branch changes with respect to `main`: three lines
  in `elaborate_multi()` switch the published frequency and bandwidth from the magnitude channel to
  the conductance, plus one line that switches the sweep re-centring. `constants.py`, `worker.py`,
  `Parser.py` and `mainWindow_ui.py` are purely additive; `mainWindow.py` changes four lines, all
  adding the new plots to existing collections. The magnitude signal feeding `main`'s legacy
  measurement is **bit-identical** on both branches — proven over the whole ADC range, max deviation
  0.000e+00 — so that measurement still runs here unchanged, alongside the new one.
- Two real differences that are *not* the measurement, both documented: the phase channel conversion
  is mirrored (`main` reports `90 − |φ|`, this branch `|φ|`, which is the physical quantity), and
  this branch writes `g<n>.txt` on every sweep.
- ⚠️ Records that the CSV column named `Dissipation_n` is **not** a dissipation: it is
  `half_bandwidth/1e6`, a HALF width in MHz. `D = 2·half_bandwidth/f_r`.

### Fixed — ⚠️ MEASURED VALUES: global phase offset of the AD8302 phase channel (2026-07-28)
- **Root cause of the distorted admittance circles, and it is not what the first
  attempt said it was.** The detector's phase output carries a **global
  per-overtone offset** δ ≈ 7…17° (board + cable phase + detector offset):
  it reads `r(f) = |φ_true(f)| − δ`. Where the true phase crosses zero (air, low
  damping) the reading therefore **dives below zero**, down to −12°. That
  "impossible" negative reading is not a local overshoot — it is
  `min(r) = −δ`, the *signature* of the offset.
- **Two of my own earlier changes were wrong and are reverted.** The morning's
  "G from the folded phase" removed a real and necessary offset correction (the
  old `_phase_signed` shift by `−min(r)` was a crude but broadly correct
  estimator of δ). The afternoon's "fold-overshoot repair" (excision + PCHIP
  bridge) treated the *symptom* of a global offset as a local defect and, by
  pairing a raw G with a repaired B, made the displayed locus worse than before:
  circle residual 10–18 % of the radius against 1.6–3.1 % for the untouched old
  code. `_phase_repair` and the `PHASE_REPAIR_*` constants are gone.
- **The fix: estimate δ by requiring the locus to be a circle.** The
  Butterworth–Van Dyke model guarantees the admittance locus *is* a circle, so δ
  is simply the offset that makes it one — a coarse+fine search over closed-form
  Taubin fits on a decimated slice of the resonance band
  (`_phase_offset_deg`, ~3 ms per overtone against a multi-second sweep).
  This subsumes the old shift, its conditional fold threshold, and the offline
  reference fit's "rotation" parameter — which turned out to be the same physical
  quantity, found independently.

  Circle residual, as a fraction of the fitted radius, over five datasets:

  | strategy | air (4 datasets) | isopropanol |
  |---|---|---|
  | no correction (the reverted morning patch) | 4.1–14.6 % | 2.7–10.6 % |
  | `−min(r)` (the old shift) | 1.2–6.6 % | 4.5–17.6 % |
  | **δ from the circle fit** | **0.75–2.1 %** | **1.7–7.7 %** |

- **Guards, so the correction only applies where it is identifiable**: rejected if
  the best residual still exceeds `PHASE_OFFSET_MAX_RMS` (5 % of the radius) or
  if the optimum is pinned to a search bound. On the damped isopropanol overtones
  both fire, so those keep exactly their previously validated values; the
  fundamental there is corrected (δ = +7.5°, residual 1.8 %).
- **Validation.** On ideal synthetic data the estimator returns **−0.00°** and
  leaves accuracy untouched (err D −0.33 %, unchanged). With a **+12° offset
  injected** into the synthetic phase it recovers **+12.00°** and restores full
  accuracy (err f_r +0.0 Hz, err D −0.33 %); without the correction the same data
  gives err f_r −28 Hz and **err D +102 %**. Reproducibility across two
  independent acquisitions of the same hardware: δ within **0.5°**, f_r within
  **7 Hz**, R_m within **2.4 %**.
- **Effect on published values** (air, sensor S3): f_r moves −20…+2 Hz versus the
  broken intermediate state and now agrees with the offline Lorentzian fit to
  1–15 Hz; D = 9.3/2.8/3.6/4.3/5.0 ppm. Sensor S3 measures **0.89–1.07×** the S1
  reference R_m — a healthy crystal; the anomaly was entirely the phase channel.
- Diagnostics: the offset is printed once per overtone and again only on a drift
  above `PHASE_OFFSET_LOG_DEG` (3°), instead of the per-sweep flood the first
  attempt produced.
- **Known limit — δ is only weakly identifiable on some overtones.** On sensor S2
  (the partially recovered module) the reported δ oscillated between consecutive
  sweeps, alternating over 15.4-17.0° across seven consecutive log lines. Those
  lines are all the FUNDAMENTAL re-logging, not different overtones: an offline
  re-estimate on the same raw sweeps puts δ at 15.8-17.6° on the fundamental
  (depending on smoothing) but at 7.6/9.5/11.8/13.0° on the 3rd/5th/7th/9th, and
  no logged value is anywhere near those.
  This is not noise in the data but the shape of the objective: the
  residual-vs-δ valley is **1.25–1.75° wide** where the crystal is clean, and
  **3.5–6.5° wide** where the residual floor is high (S2's F0 floor is 2.4 % of
  the radius against 0.8 % on S1), so ±0.8° of sweep-to-sweep noise moves the
  minimum without meaningfully changing the fit. Consequences on published values
  over the observed 1.6° wander are small — **1 Hz** on `f_r`, **−2.5 %** on `D`,
  **+4.7 %** on `R_m` — and `f_r` still agrees with an independent Lorentzian fit
  to **0.007–0.32 ppm**. Averaging δ across sweeps would remove the jitter and is
  recorded as a roadmap item, not applied: it introduces cross-sweep state and
  shifts published values, so it needs a decision.

### Added, then DISABLED — saturation mask on the spectra shipped for display and fitting (2026-07-28)
> **Ships off** (`IMPEDANCE_PANEL_MASK_SATURATED = False`). At the floor below it
> removes 35–63 % of the band in water and 20 % on the 9th overtone in air, and
> throwing away half the signal to make the circle rounder is the wrong trade.
> The code, the constants and the measurements stay in place so the study can
> resume from here; with the flag off the behaviour is bit-identical to before
> (water residuals back to 4.1/18.1/9.9/6.4/5.5 %).
>
> Two directions the data suggests, for when it is revisited: **weight** the
> samples by their expected error instead of dropping them, and mask **only the
> circle fit** — which needs a clean arc — while leaving the Lorentzian the tails
> that pin its background. Fixing the root cause is better still: `R17 = 52.3 Ω`
> is far too small a reference for a liquid load, and a switchable reference
> resistor would put the whole sweep back inside the detector's window.

- **What it fixes.** On a liquid load the whole sweep sits in the AD8302's
  dynamic-range corner: against `R17 = 52.3 Ω` a water-loaded crystal reads
  `R1` = 0.6–3 kΩ, so the divider ratio is **−23 to −36 dB** with a resonance
  contrast of about 6 dB. On the 2026-07-28 water run **82 %** of the 3rd
  overtone's sweep is below `RATIO_DB_FLOOR`, and those samples are the straight
  tail that pulls the locus out of round. Dropping them takes the circle residual
  from **18.1 % to 4.7 %** of the radius and brings the two independent Γ
  estimators from −5.5 % to **−0.6 %** apart.
- Applied as a **contiguous interval**, not sample by sample. The divider ratio
  falls monotonically away from resonance so the usable region is one interval by
  construction, but the threshold test flickers where the ratio grazes the floor —
  up to 12 fragments with 1–4 sample holes on that run, which would zigzag the
  panel's line plots. A 5-sample majority filter kills the flicker, then the
  outermost survivors set the interval.
- **Display and fitting only.** The logged resonance frequency and half-bandwidth
  are computed *before* the mask, deliberately: masking removes exactly the
  off-resonance samples that `_half_bandwidth_G_exact` uses as its baseline, which
  is a separate defect (see below). So **no published value changes**.
- **The floor is −28 dB, not the nominal −30, and it is a compromise.** No single
  value is good everywhere; this is the one that fixes the case it was introduced
  for. Circle residual / disagreement between the two Γ estimators:

  | | no mask | −28 dB | −30 dB | −32 dB |
  |---|---|---|---|---|
  | water, 3rd | 18.1 % / −5.5 % | **4.7 % / −0.6 %** | 10.3 % / −4.5 % | 13.4 % / +22.7 % |
  | air, 9th | 7.9 % / −2.9 % | 5.8 % / +20.6 % | 6.6 % / +13.5 % | 7.9 % / −2.9 % |

  So it costs something in air on the 9th overtone: 20 % of that band goes, and
  with the tails gone FIT 2's background and FIT 1's rotation are less constrained
  even though the residual improves. That cost falls on diagnostic numbers only.
- The fit window gains a **`masked [%]` column**, coloured green below 10 %, orange
  below 20 %, red above — because the circle residual keeps looking fine while the
  arc gets too short to pin either fit. The dropped fraction is also printed once
  per overtone and again on a move of more than 10 points.

### Known — the liquid baseline is taken ON the resonance (2026-07-28)
- The sweep window is fixed and sized for air (**−12 kHz / +6 kHz**), while in
  water Γ_FWHM is 1.9–5.0 kHz. So the sweep starts only 2.4–6.3 half-widths below
  resonance and `G − average(G[:100])` subtracts a "baseline" that is **13 % of the
  peak on the 3rd overtone and 66 % on the 9th**.
- It does **not** distort the circle (subtracting a constant translates it, and the
  fit is translation-invariant: 18.2 % either way), but it biases the **published**
  half-bandwidth, because `_half_bandwidth_G_exact` looks for the half-height on
  that translated curve. Against the Lorentzian, which has a free background and is
  immune: Γ is low by **−2.5 % (n=1), −4.3 %, −4.3 %, −7.4 %, −13.9 % (n=9)**.
  D in liquid is therefore underestimated, and the error grows with overtone.
- Not fixed here — it changes published values. Options: take the width from a
  Lorentzian with a free background instead of a half-height crossing, or scale the
  sweep window with the measured Γ.

### Fixed — ⚠️ MEASURED VALUES: δ comes from the fold, not from a roundness fit (2026-07-28, later)
- **Reverts the circular-locus estimator of the same day.** Prompted by the user
  recalling that the published version behaved better, and confirmed by
  reproducing `c83a820`'s reconstruction on all 11 archived datasets.
- **Why it was wrong.** `_phase_offset_deg` minimised the out-of-roundness of the
  admittance point cloud, and applied the sign flip *inside* its own objective. So
  it could buy roundness by pushing δ past the value where the corrected phase
  reaches zero, until the flip landed on the antipode of the circle. It did:
  δ came out up to 12° beyond `−min(r)`, the corrected phase sat at +12° where it
  should be 0, and the flip made **B jump by up to 77 % of its own range**. In air
  that jump is a chord along the circle, so the cloud stayed round while B(f) was
  discontinuous; in water the flip fired with no fold at all and **split the locus
  into two disconnected arcs**, with a fitted circle four times too large.
- **The rms metric was misleading in both directions.** It reported the water
  fragmentation as an improvement (11.1 % against 19.8 %) — a circle through two
  disconnected arcs can have a small radial residual and no physical meaning.
- **δ is not a free parameter.** The reading is `r(f) = |φ(f) + φ_b| − δ`; where the
  argument crosses zero, `min(r) = −δ` exactly. `_phase_offset_fold` takes it from
  the minimum, and when there is **no fold** applies neither an offset nor a flip —
  the original `_phase_signed` behaviour, which was right.
- **Measured across 11 datasets, 55 overtones:**

  | | continuity: max step of B between adjacent samples, % of B range | circle residual, air | water |
  |---|---|---|---|
  | δ from the roundness fit | 20–86 % | 0.8–2.5 % | 3.1–11.1 % (meaningless) |
  | **δ from the fold** | **0.5–7.5 %** | 1.2–7.9 % | 3.8–19.8 % |

- **Independent check that does not involve circularity**: disagreement between the
  two Γ estimators (FIT 1 circle vs FIT 2 Lorentzian, which share nothing). Median
  over 55 overtones **3.78 %** from the fold against **5.03 %** from the roundness
  fit; on the fundamentals the roundness fit is catastrophic (0.37 % against
  37.6 %).
- Effect on published values versus the reverted state: Γ moves by −0.5…+16 %
  depending on the overtone. The attenuator correction, which is verified
  independently by a synthetic THRU, is **kept**.
- `--offset fold|circle|none` in `sweep_data/fit_admittance.py`; `phase_offset_deg`
  and `_phase_offset_deg` are retained, documented as superseded, because *how*
  they fail is the useful part.
- **Still open:** with δ pinned by the fold the air locus is 1.2–7.9 % out of round,
  systematically. A board phase φ_b inside the absolute value fits both channels
  4–5× better and reproduces to 0.2–0.4° across acquisitions, but applied as a
  post-unfold rotation it restores continuity without recovering roundness. See the
  2026-07-28 investigation report.

### Added — live admittance-fit window, Tools > "Impedance Fit (live)" (2026-07-28)
- Runs **FIT 1** (BVD circle, f_s and Γ off the arc geometry) and **FIT 2**
  (Levenberg–Marquardt Lorentzian on G) on every completed sweep, per overtone,
  and shows: **three views** for the selected overtone — G(f) with FIT 2, **B(f)**
  with FIT 1 under it and x-linked, and the B–G locus spanning both rows — plus a
  table for all of them
  with δ, f_s, Γ, D, R₁, L₁, the circle residual, and — the point of having two
  estimators — **FIT 2 minus FIT 1** on both f_s and Γ. Their disagreement is an
  honest error bar in a way a single fit's covariance is not.
- It imports `sweep_data/fit_admittance.py` **by file path** instead of
  reimplementing it. The offline script has to stay standalone (it is run straight
  from a directory of archived `g<n>.txt`), and importing the same file is what
  makes it impossible for the live and offline numbers to drift apart. Verified:
  the window reproduces the offline table to the 8th significant digit.
- Cost, measured on five overtones of a real air sweep: **123 ms** for the first
  fit, **13 ms** for every one after it, against a sweep that takes seconds; a
  timer tick with no new sweep costs 2 µs, and a closed window costs nothing (the
  timer stops on hide). Two things buy that: refitting only when the per-overtone
  revision counter moves, and reusing the previous sweep's rotation angle as a
  bracket instead of re-running the 181-point grid — with the golden search cut
  from 40 iterations to 14, since 40 on a 12° bracket resolves 0.007°, digits that
  do not exist.
- The measured phase offset δ now travels on the existing G/B channel, so the
  window shows it per overtone instead of the user reading the console. `0.00`
  means the estimate was rejected on that sweep.
- **B(f) matters more than it looks.** G is *even* in the phase, so a broken
  reconstruction can leave G and the fitted circle looking perfect while B is
  discontinuous — exactly what the reverted roundness-fitted offset did, stepping
  by up to 77 % of B's range. The B panel therefore reports that step explicitly
  (largest difference between adjacent samples, as a fraction of B's span); a
  continuous trajectory keeps it at a few per cent. The dashed FIT 1 line there
  comes from the circle's own geometry, so where it diverges from the measurement
  is where the circle model fails.
- **C0 is deliberately not shown.** The published spectra have a constant baseline
  removed before shipping, which *translates* the admittance circle — and
  translating it is precisely what C0 does, so the fitted offset is no longer
  ω·C0. f_s, Γ, D and R₁ are unaffected. Run the offline script on `g<n>.txt` when
  C0 is what you need.

### Added — `sweep_data/fit_admittance.py` draws the data it fits (2026-07-28)
- One row of three panels per overtone: the **raw** detector voltages as
  acquired (with the mask floor and the fit band marked), **G(f) with the FIT 2
  Lorentzian** on top, and the **admittance plane with the FIT 1 circle** —
  including the centre and the point the arc regression calls f_s, which makes
  the fitted rotation visible. `--save` writes it, `--no-plot` skips it. The
  frequency axis is detuning in kHz: at 1 Hz resolution on a 45 MHz carrier an
  absolute axis is all offset notation and no information.
- **The figure immediately showed the script was behind the pipeline**: a radial
  spur stuck out of the locus at f_r on every overtone, the signature of the
  uncorrected global phase offset. The offline path applied only the old
  conditional fold flip and relied on the arc-fit rotation to absorb the rest —
  which it cannot, because the offset rotates `(Z_q + R17)` about `-R17`, not the
  admittance locus. `phase_offset_deg()` is now a port of the pipeline's
  estimator; `--no-offset` reproduces the old behaviour for comparison. Circle
  residual on the 2026-07-28 air run: **3.9-7.7 % → 0.68-2.28 %** of the radius,
  and FIT 1 vs FIT 2 agreement on f_s tightens from 23-129 Hz to 2-52 Hz.
- One subtlety, found by measurement: the flip inside the estimator must be
  **unconditional**. Making it conditional on the corrected phase reaching zero
  puts a discontinuity inside the search and manufactures a false optimum — on
  the fundamental it returns +10.0° at 2.01 % residual instead of the true
  +15.8° at 1.17 %.

### Fixed — ⚠️ MEASURED VALUES (verification round, 2026-07-27)
- **Attenuator compensation was 0.600 V instead of 0.61069 V.** The ADC→V
  conversion has to undo the INPB R11/R19 attenuator, and that is **not** one
  clean decade: k = (47.0 + 4.99)/4.99 = 10.4188 = 20.3564 dB, which at
  30 mV/dB is 0.61069 V. The hardcoded 0.600 undid exactly 20.000 dB and left
  0.3564 dB uncompensated, underestimating M = |Z_q + R17| by **4.02 %**. The
  inversion amplifies that by (1 + R17/R_m), because `R_q = M·cosφ − R17` is a
  difference of close numbers at resonance: up to **−22 %** on R_m at the
  fundamental in air. Now derived from the schematic values in
  `Constants.V_MAG_DECADE_OFFSET` instead of hardcoded, and applied at **both**
  conversion sites — `_Vmag_bit_mag` (the published path) and the one inside
  `run()` that writes `g<n>.txt` (the offline reference), which had drifted apart.
  Confirmed by a synthetic THRU (Z_q = 0.001 Ω through the full forward model):
  M read **50.199 Ω** before and **52.301 Ω** after, against a true 52.30 Ω.
- **The conductance is no longer routed through the phase unfold.** G is *even*
  in φ, so it must be computed from the phase exactly as the AD8302 emits it —
  folded. `_phase_signed` does more than flip the sign: it also **shifts** the
  phase by its minimum, and that shift is not sign-symmetric. Sending G through
  it biased the published dissipation by **+6 to +20 %** in air while doing
  nothing about a sign ambiguity G is already immune to. B keeps the signed
  phase, which is the only quantity that genuinely needs it.

  **Combined effect on the published values**, measured on the frozen datasets.
  The two fixes push D the same way, they do not cancel:

  | n | D air before → after | D isopropanol before → after |
  |---|---|---|
  | 1 | 25.08 → 29.74 ppm | 387.1 → 380.1 ppm |
  | 3 | 5.58 → 6.89 ppm | 194.4 → 194.7 ppm |
  | 5 | 5.42 → 6.71 ppm | 146.1 → 146.3 ppm |
  | 7 | 4.86 → 5.65 ppm | 123.8 → 123.9 ppm |
  | 9 | 5.61 → 6.04 ppm | 112.6 → 112.7 ppm |

  `f_r` moves ≤ 13 Hz. R_m rises 7–11 % in air (the direction the underestimated
  M predicted). In liquid the unfold does not fire for n ≥ 3, so only the
  constant contributes there.

  Verification harness: synthetic BVD through the reference forward model
  (attenuator k, Z2_eff, AD8302 transfer functions, ×2/×1.5 buffers, 12-bit ADC)
  into the real `MultiscanProcess` methods. Isolating the formulas, air now gives
  **f_r 0.00 Hz, D −0.34 %, G_max −1.43 %** against analytic truth; the residual
  G_max offset is the R17-vs-Z2_eff item, still open.

### Changed — ⚠️ MEASURED VALUES
- **The published resonance frequency and dissipation now come from the EXACT
  complex-divider inversion.** `elaborate_multi` computes `Y_q = 1/(M·e^{-jφ} −
  R17)` once from the RAW absolute `V_MAG` and the signed phase, and reads f_r
  and Γ off that conductance via the new
  `parameters_finder_impedance_exact()`. The old
  `parameters_finder_impedance()` (approximate `G = cosφ/|Z|`, fed the
  baseline-corrected `V_MAG`) is no longer called. The panel and the datalog now
  share one computation, so they cannot disagree.
- **The half-bandwidth is measured two-sided and interpolated**
  (`_half_bandwidth_G_exact`). The old one returned `f_r − f_left`, correct only
  for a symmetric peak — the real one is skewed by the residual C0 branch — and
  snapped the crossing to the 1 Hz grid, which quantised D by a few percent when
  Γ is a few tens of hertz. Falls back to one-sided when the sweep window holds
  no crossing on a side, which happens on damped loads.

  **Impact, measured on real data.** `f_r` moves by at most 71 Hz (≤1.6 ppm).
  `D` changes a lot, and for the better:

  | | air, D before → after | isopropanol, D before → after |
  |---|---|---|
  | n=1 | 68.4 → 25.1 ppm | 386 → 387 ppm |
  | n=3 | 24.3 → 5.6 ppm | 227 → 194 ppm |
  | n=5 | 17.0 → 5.4 ppm | 183 → 146 ppm |
  | n=7 | 12.7 → 4.9 ppm | 152 → 124 ppm |
  | n=9 | 11.8 → 5.6 ppm | 140 → 113 ppm |

  In air the formula dominates (D falls 2–3×) and the two-sided window adds a
  further ~20 %; in liquid the formula contributes ~5 % and the window ~15–20 %.
  The new values are the physical ones: ~5 ppm on the overtones in air is
  textbook for a good 5 MHz crystal, and 387 ppm at the fundamental in
  isopropanol matches the Kanazawa–Gordon prediction (~400 ppm). The old
  approximate values were inflated 2–4× in air.
  **A pre-change and a post-change datalog are not comparable.**

### Performance
- **The impedance panel no longer dominates the GUI.** It was recomputing and
  redrawing on every `plot_update_ms` tick (20 Hz) data that only changes once
  per sweep. Three fixes: a per-overtone revision counter so the panel repaints
  only on new data (the selector state is part of the key, so toggling an
  overtone still responds at once); the list→array conversion moved to the
  consumer, done once per sweep instead of 20 times a second; and one overtone
  per queue message instead of re-sending all five lists on every
  `elaborate_multi` call, cutting the queue payload and pickling cost 5×.
  Measured on five overtones × 3000 points: steady-state cost per tick
  **≈5 ms → ≈1 µs**, i.e. from ~10 % of the 50 ms budget to nothing.

### Added
- **Live impedance panel** — a right-hand dock in the main window with two
  real-time views, both computed with the **exact** complex-divider inversion:
  - **Conductance G(f)**, all overtones overlaid, x plotted as the offset from
    the detected peak so every overtone shares one axis;
  - **Admittance circle B vs G**, all overtones overlaid, aspect-locked so a
    circle looks like a circle.

  Per-overtone colours match the frequency/dissipation plots, the scan selector
  is honoured (deselected overtones disappear here too), and both views join the
  existing right-click menu (grid, autoscale, reset zoom) and the light/dark
  theme. The panel is collapsible, and the two plots sit in their own vertical
  splitter so either can take the whole height.

  The exact formula (`_phase_signed` / `_RX_exact` / `_G_exact` / `_B_exact`,
  ported from `sweep_data/plot_conductance.py`) runs in `elaborate_multi` on a
  new RAW absolute `V_MAG` chain. It arrived as a display-only path — at that
  point `parameters_finder_impedance()` still published the logged values from
  the approximate formula, and the offline regression fixture confirmed nothing
  had moved. It is now also the **published** path: see "Changed — MEASURED
  VALUES" above.

  Data path mirrors the existing `A_multi` channel: `Multiscan` →
  `Parser.add_GB_multi` → `Worker.consume_queue_GB_multi` →
  `get_G_exact_buffer` / `get_B_exact_buffer` / `get_F_G_values_buffer` → GUI.
  The queue argument is optional, so an older `ParserProcess` call signature
  still works and `add_GB_multi` degrades to a no-op. The whole computation and
  the panel refresh are wrapped in try/except: a diagnostic view must never take
  down an acquisition.
- `Constants.FOLD_THRESHOLD_DEG_G` (5.0) — the air/liquid discriminator for the
  conditional phase unfold, previously hard-coded in the offline script.
- **Impedance panel tuned for damped (liquid) loads.** On an isopropanol
  acquisition the displayed circles came out visibly distorted. Three changes,
  all display-side:
  - **Adaptive window** (`IMPEDANCE_PANEL_BAND_GAMMA`, default 3.0): the
    producer now clips each spectrum to a few half-bandwidths around resonance
    before shipping it. In air the sweep spans ±50 to ±190 Γ and almost all of
    it piles onto one spot of the locus; in a liquid Γ grows to ~1–2.5 kHz and
    the far points are exactly the ones acquired deepest in the AD8302
    dynamic-range corner. Also cuts the queue payload and the redraw cost.
  - **Fitted-circle overlay** (`IMPEDANCE_PANEL_SHOW_FIT`): a dashed circle per
    overtone, so the circle the data supports stays visible even when the raw
    locus is out of round — and its diameter is a far more robust 1/R_m than
    the peak of G.
  - **The fit runs on the core, not on everything plotted**
    (`IMPEDANCE_PANEL_FIT_GAMMA`, default 1.0). Past about one half-bandwidth
    the deviation from a circle is *systematic*, not sporadic, so on a damped
    load a majority of a ±3 Γ window is off-circle and residual-based outlier
    rejection locks onto the wrong subset (measured: −36 % error on R_m at the
    3rd overtone). Fitting the core instead reproduces the offline reference
    within **+0.5 % to +6.6 %** in air and isopropanol alike. `f_r` and Γ now
    travel with the spectrum so the panel knows where the core is; both are
    optional in the payload, so an older producer still unpacks.

### Validated
- **The 5° conditional-unfold threshold is confirmed across the air→liquid
  transition** — the systematic test left open in the handoff. In isopropanol
  the fundamental sits at min|φ| = 2.04°, the critical intermediate case, and
  the rule correctly unfolds it (circle rms 0.52 % vs 33.4 % if left folded),
  while the 3rd to 9th (12.1° to 43.8°) are correctly left alone (e.g. 1.06 %
  vs 2.49 % on the 7th). Right call on all five overtones, in both regimes.

### Changed
- **Aligned with `main`** (merge of `main` @ 52a42a9, 47 commits; pre-merge state
  tagged `v0.1.6G-pre-merge`). The branch now carries the whole `main` line —
  `run.py` entry point, serial connection Steps 1–2, `requirements.txt` /
  `environment.yml`, the GUI redesign (programmatic UI builder + dark/light theme),
  robust trimmed-mean averaging, responsive calibration cancellation, firmware
  `0.1.5a` and `docs/DATA_FORMAT_sweep_data.md` — on top of the conductance feature.
- ⚠️ **Logged values will shift**: main's `trim_mean` replaces the
  Savitzky-Golay + `np.average` on the acquisition ring buffer, and now averages the
  **conductance-derived** frequency and dissipation. By design, not a regression —
  but a pre-merge and a post-merge `logged_data/*_multi_.csv` are not directly
  comparable.
- **G DATA VIEW moved to the menu bar**: **Tools → Conductance Data**
  (`actionConductance_Data`). The old sidebar button is gone — main's redesign
  removed that whole family of buttons in favour of the menu. The handler
  `_conductance_data_plot` is unchanged.
- **DEBUG state removed** (roadmap item, closed by the merge): `environment` back to
  `10`; `plot_autoscale_yaxis` dropped in favour of main's `plot_force_yrange`,
  which gates the same forced Y-range with inverted polarity.
- `Calibration_{5,10}MHz.txt` and `PeakFrequencies{,RT}.txt` now hold the **5 MHz**
  sensor module currently mounted (they previously described a 10 MHz crystal).
  These are runtime output, rewritten by `Calibration.py` on every calibration run.

### Added
- **`g<n>.txt` documented** in `software/docs/DATA_FORMAT_sweep_data.md`: the second
  sweep family written by this branch — same layout as `<n>.txt`, but columns 2–3 are
  the **raw AD8302 voltages** V_MAG / V_PHS instead of dB / degrees. Includes the ADC→V
  conversion, the divider inversion it feeds, and the two traps (never baseline-correct
  V_MAG before the exact inversion; column 3 is `|phase|`, sign folded).
- Example `g<n>.txt` sweeps versioned alongside main's `<n>.txt`, for the same reason
  main versions those: the Conductance Data view needs input on a fresh clone.

### Removed
- The three dead Qt-Designer UI files (`res/mainWindow_new.ui`,
  `res/mainWindow_new_ui.py`, `ui/mainWindow_new_ui.py`). Nothing has imported them
  since the GUI redesign; they only generated merge conflicts.

### Verified
- Offline path **byte-identical** across the merge (`plot_conductance.py`,
  `fileStorage.py`), and offline results identical to the pre-merge baseline to the
  last digit. `py_compile` clean across the package.
- ⏳ **Not yet verified**: on-device smoke test (acquisition, Tools → Conductance Data)
  and the logged-value comparison.

## [Unreleased] — `main`

### Added
- **The `0.1.5c` firmware images exist** — `firmware/openQCM_Next_py_0.1.5c_teensy/` and
  `..._0.1.5c_TEST_teensy/` now carry their `.ino.TEENSY40.hex`, built with the `teensy:avr 1.58.1`
  core (FLASH 55 120 B and 45 500 B). ⚠️ HANDOFF §5 claimed the 0.1.5c image was *already built*;
  it was not, and **no `-TEST` variant had ever been built** — only `0.1.5a` and `0.1.5b` non-TEST
  carried a hex. Without them the update procedure cannot put a current firmware on a board, and on
  a no-TEC prototype the only image in `firmware_update/` is the wrong variant as well as three
  versions old.

- **The two device queries log which path asked** — `[auto]` beside the reply when it is the
  handshake that runs at connection, `[menu]` when it is the operator's check from Tools. One word,
  and it is what distinguishes a board that answers nothing from a board nobody asked.
  - It settled the open question of 2026-09-01, when a bench run appeared to log the
    identification-number reply **twice for a single connection**. A temporary diagnostic printing
    the caller frames and the clock showed the two calls **2.24 s apart**, tagged `auto` and `menu`:
    the handshake, then the manual check that the bench procedure prescribes at that exact point. Two
    events, not one delivered twice. They read alike only because a `0.1.5a` board, which has no
    branch for `'S'`, answers nothing to either.
  - Ruled out along the way, and worth not re-deriving: `actionSerialNumber` is connected **once**,
    in `__init__`; the repository contains no `trigger()` call at all; the action carries no shortcut
    and no `MenuRole`, and the menu bar is not native. Nothing but a click can fire it.
- **Firmware 0.1.5c: `'Q'` ends a sweep in progress** — `firmware/openQCM_Next_py_0.1.5c_teensy/`
  and `..._0.1.5c_TEST_teensy/`, the 0.1.5b pair kept as the previous step. The board sweeps once per
  command and reads serial only at the top of `loop()`, so a sweep ran to completion whatever the
  host did; `'Q'` stops it at the next whole sample and the measurement still terminates with the
  contracted `temperature;status;error;s` line.
  - The poll sits at the **end** of a sweep iteration, so the break never lands mid-line, and it
    consumes only the `'Q'` line — any other character is left for the parser at the top of `loop()`.
  - `'Q'` also gets a **top-level no-op branch**, so the letter does not fall through to the sweep
    parser and silently overwrite `freq_start`. ⚠️ **Corrected 2026-09-01**: this entry first said an
    unrecognised letter sets the board off on a scan from 0 Hz. It does not — `message` is latched
    only after the **third** field, so a single letter never begins a sweep. That is Q-1's failure,
    not ours, and the hardware says so: a `0.1.5a` board, which has no branch for `'S'`, answers
    nothing and keeps working.
  - Both compile for `teensy:avr:teensy40`; `Constants.FW_VERSION` moves to `0.1.5c` with them.

### Fixed
- **UNSET REF wiped the plots and did not unset the reference** — two faults, and the first was
  hiding the second.
  - `reference_not()` called `clear()`, so pressing it emptied the panels of a run that was still
    going. `reference()` has had its own `clear()` commented out for a while; the pair is symmetric
    again.
  - ⚠️ **And it never reset the four `_reference_value_*` holders.** All four draw sites subtract
    them **unconditionally** — not one tests `_reference_flag` — so unsetting lowered the flag,
    wiped the panels, and redrew exactly the same offset curves from the same buffers. The wipe was
    what looked like a reset. They are now zeroed, to the same values and shapes `start()` uses, so
    a run that never had a reference and one that had it removed end up in the same state.
  - `_labelref1` / `_labelref2` go back to *not set*, which the info window prints beside
    *Ref. Frequency* and *Ref. Dissipation* and which had kept showing the stale reference.

- **Single-measurement plots started 4–6 s late** — the relative time axis called zero the first
  sweep *acquired*, not the first datum *displayed*.
  - `Serial.elaborate` pushes a timestamp on **every** sweep but a NaN value until
    `_k >= environment`, since no trimmed mean exists before the circular buffer has filled. The
    origin was `np.nanmin(t1_buffer)` — the oldest timestamp, belonging to sweep 0, a sample that is
    never drawn — so the first visible point sat at `environment × sweep_period`. **Measured 5.4 s**
    for `environment = 3` and a 1.8 s sweep, matching the reported 4–6 s; at the production value of
    **10** it would be 15–20 s.
  - `_first_valid_timestamp()` takes the oldest sample that actually carries a datum — the last of
    the leading non-NaN run, array order running backwards in time — and that becomes zero. First
    point: **+5.4 s → +0.0 s**.
  - It is retried each tick instead of firing once on `_ser_control == environment`: the counter and
    the samples reach the GUI on different queues, so the tick that sees the counter need not be the
    tick that sees the datum.
  - ⚠️ **This reverses a deliberate choice** recorded in `HANDOFF.md` §3, taken on the reading that
    zero means "acquisition started". Zero now means "first measurement shown". The section has been
    rewritten rather than edited, so the next reader does not restore `nanmin` as a fix.
  - ⚠️ **And the note claiming multiscan already used `nanmin` over the buffer was wrong.** Multiscan
    takes `buffer[0]`, the *newest* sample, **per overtone**, then `nanmin` **across overtones** — a
    minimum over overtones, not over time. That is why it never showed the offset. Single mode now
    behaves the same way; multiscan is untouched.

- **The sampling time read 0 for the whole of every single-frequency run** — `Worker.store_data()`
  updated `time_elapsed` **only in its multiscan branch**; the single branch never touched it, and
  carried a `# VER 0.1.4 TODO time controlled sampling time in sigle mode` where the work should
  have gone. The value stayed at its initial `0`, so the status bar's `S:` looked like a broken
  field rather than an unimplemented one.
  - Single mode writes a datalog row on **every** call — the time-controlled sampling of multiscan
    is still a TODO there — so the interval is simply the time since the previous write. The first
    write has no predecessor and leaves the value alone.
  - Measured against a simulated 1.8 s sweep: `0` before the first write, then **1.81, 1.81,
    1.80 s**. It was `0, 0, 0, 0`.
  - ⚠️ **And multiscan stops truncating it.** It computed `int((now - time_pre)/1e6)` while the GUI
    formats the value with `"{0:.1f}"` — a format that is only meaningful for a float — so a 1.8 s
    interval was reported as `1`, off by 45%. Display-only: the datalog's own relative-time column
    is computed separately and is untouched.
  - The new reference is `_last_datalog_write`, in **seconds**, and deliberately not multiscan's
    `time_pre`, which is epoch microseconds. Same trap as `_timestart`.

- **"Time elapsed" was showing the sampling interval, on its own row** — two changes that turned out
  to be one thing.
  - ⚠️ **The number was the wrong quantity.** `Worker.get_time_elapsed()` returns
    `(now - time_pre) / 1e6`, and `time_pre` is reset after **every datalog write** — so it is the
    interval between two samples, not how long the run has been going. The status bar's `S:` is the
    honest label for it; the sidebar's *Time elapsed (sec)* never was. New `get_run_elapsed()`
    returns seconds since START and feeds the sidebar; `S:` keeps the interval. Two labels, two
    quantities, where there had been one value under both.
  - ⚠️ It is measured from **START, not from the first datum**: the warm-up is 3 sweeps in
    development and 10 in production, and a readout frozen at 0 for the first 15–20 s of a run reads
    as broken rather than as warming up.
  - ⚠️ It does **not** reuse `_timestart`, which is seconds in single mode and epoch microseconds in
    multiscan — the same unit split `HANDOFF.md` §3 records for `start_time`. A readout that has to
    work in both modes cannot rest on a value whose unit depends on the mode, and unifying
    `_timestart` would move the datalog's relative-time column in both processors.
  - The readout now sits **on one row with its label**, right-aligned, using the same
    `QHBoxLayout` + `addStretch(1)` shape as the temperature readout. The two already shared a QSS
    rule; the layout was the only thing that still differed.

- **The datalog name in the sidebar was cut with room to spare** — `_show_log_filename` elided the
  text against `lblLogFile.width()`, but it runs while the label is still **hidden**, and a widget
  that has never been laid out carries Qt's default 100 px. So the width was always
  `max(140, 100 - 8)` = **140 px**, whatever the sidebar was doing.
  - Measured with the real font: `Log: 20260901_153045_multi.csv` is **224 px** and fits whole from
    **244 px**, while the sidebar pane is **260–400 px**. The name was being truncated inside a
    panel that had room for all of it, at every width.
  - The second half of the fault was that the width is not a constant either: the sidebar is a
    splitter pane, and nothing re-elided when it was dragged.
  - `ui/widgets.ElidedLabel` now owns it — it keeps the full string, re-elides on resize, on show
    (the label is filled while hidden, and being shown does not have to change the geometry) and on
    font change (the theme makes it bold, and bold is wider), and always carries the whole text in
    its tooltip. Horizontal size policy `Ignored`, for the same reason `label_COM_status` has it: a
    long name must not widen the sidebar.
  - ⚠️ The eliding must not come back to the caller. The caller cannot know the width — that is the
    whole defect, and it is now stated in `_show_log_filename`'s docstring.

- **A board that had just re-enumerated was reported as a board still sweeping** — after a
  firmware update the Teensy re-enumerates the USB device, so the handle the window is holding
  points at a device node that no longer exists and every read raises `OSError(6, 'Device not
  configured')`. `_drain_serial` caught that and returned the same `False` it returns for a board
  that never fell silent, `_board_busy` read the `False` and answered *The board is still sending
  measurement data. Wait a moment and try again.* — advice that cannot work, because waiting does
  not revive a dead handle. The only thing that did was Disconnect/Connect, which the message never
  mentions.
  - ⚠️ **The two failures were always distinguishable and the code threw the distinction away.**
    `_drain_serial` now returns one of three outcomes — `DRAIN_QUIET`, `DRAIN_BUSY`,
    `DRAIN_LINK_LOST` — and prints the elapsed time on the lost-link path. Measured against fake
    handles: a dead handle raises on the first `inWaiting()` in **0 ms**, a board that never stops
    burns the **whole 6 s timeout**. Same `False` before, four orders of magnitude apart on the
    clock.
  - `_board_busy` claims busy only for `DRAIN_BUSY`; the new `_link_lost()` covers the other case
    and `_report_link_lost()` gives it its own message — *the connection to the board was lost […]
    press Connect to reconnect* — and takes the window to Disconnected, so the state matches the
    port. Wired into both firmware-version blocks and the board-number query.
  - ⚠️ `_can_query_device()` could not have caught this and still cannot: pyserial's `isOpen()`
    returns the `is_open` flag, which stays `True` after the device node underneath it is gone.
    Only a real read finds out. That is why the menu entry was enabled and the query went ahead.
  - Verified on hardware on 2026-09-01, downgrading a prototype board to `0.1.5a-TEST` and updating
    it from the software. ⚠️ **The port name does not change across the re-enumeration** on macOS
    (`/dev/tty.usbmodem131313201` before and after), so a reconnect finds the same entry in the
    list — but the handle onto it is still dead, which is exactly what made the fault confusing.

- **The firmware updater is launched observably, and gives the port back** — three defects in
  `_run_firmware_updater`, all found by running the procedure rather than reading it.
  - The path was built from **`os.getcwd()`**, so the updater only opened when the application
    happened to be started from `software/`. Now resolved from the module, like `APP_ICON`.
  - The launch was **silent whichever way it went**: `os.startfile` raises and `open` returns a
    non-zero exit code, and neither was looked at, so a procedure that did nothing read exactly
    like one that worked. It now logs the target and whether it exists, and reports a failed launch
    instead of appearing to succeed.
  - It kept the serial handle across an operation that is **guaranteed** to invalidate it. The
    launcher returns as soon as the loader is on screen, not when the board has been flashed, so
    there is nothing to wait for and nothing to detect: the connection is forfeit the moment the
    operator starts. The window now says so and goes to Disconnected.
  - The disconnect body moved out of `_toggle_serial_connection` into `_disconnect_serial(message)`,
    because the button is no longer the only thing that can end a connection and eleven widgets
    have to move together.

- **The updater hands the loader the right image instead of opening it empty** — `firmware_update/`
  now carries both `0.1.5c` hex files, and `_firmware_image()` picks between them from the version
  the board has just reported: the `-TEST` suffix of a no-TEC prototype selects the TEST image, and
  anything else the production one. The file name is **derived from `Constants.FW_VERSION`**, never
  written out, because the image and the version the check demands are the same fact — spelling it
  twice is how the folder came to ship `0.1.5` while the dialog asked for `0.1.5c`, so the operator
  updated and was immediately asked to update again.
  - ⚠️ Before this, the loader opened with **no file** and the operator browsed a folder whose only
    `.hex` was three versions old and, on a prototype, the wrong variant as well: 172 890 B of TEST
    image against 201 707 B of TEC image, and nothing on screen to say which one belonged there.
  - `Teensy.app` declares **no** `CFBundleDocumentTypes`, so this was checked rather than assumed:
    the binary implements `application:openFile:`, which is what `open -a` sends. Verified against
    Teensy Loader 1.52 — `open` returns 0 and the loader comes up with the image loaded.
  - A missing image is not fatal: the loader still opens empty, exactly as before, and the log says
    which file was looked for. On macOS a non-zero `open -a` with the image retries without it, so
    the procedure can never end up worse than it was.
  - The disconnection is also **announced in a dialog** — *Disconnected from serial port. Firmware
    update in progress. Reconnect when it is done.* Redundant with the status bar and the Connect
    button by design: at that moment the operator is looking at the Teensy Loader in another
    application, and coming back to a window that quietly stopped being connected is how the next
    query gets blamed on the board. Non-blocking, because the loader is what needs the hands.
  - ⚠️ **Verified on macOS only.** The Windows branch drives `TyUploader.exe` with the image as an
    argument through `subprocess.Popen` instead of `os.startfile`, which cannot pass one, and that
    path has not been run. It has to be checked before a production build.

- **`'Q'` was never sent: the stop-sweep write sat in the wrong branch** — it was inside the
  `except` of `_reacquire_serial_lock`, so it could only run when re-opening the port **failed**, and
  a failed `_open_serial_lock` raises with the handle still closed, so even then the write itself
  would have failed. On the normal path — the port comes back, which is every real Stop — the letter
  never left the host. The whole of firmware 0.1.5c's stop-sweep branch was unreachable from the
  software.
  - It survived four bench sessions because the outcome was right anyway: the drain in
    `_serial_query` waits out the tail on its own, which is exactly what it was built to do for
    boards that do not know `'Q'`. The feature was dead and the symptom was cured by its fallback.
  - The bench log is what gave it away: `Drained 7172 bytes` on a `0.1.5c-TEST` board, the same
    count to the byte as on a `0.1.5b` board — the firmware `'Q'` is deliberately withheld from.
    A working `'Q'` cannot leave the tail the same length as no `'Q'` at all.
  - Moved to the success path, and it now prints `Stop-sweep sent to firmware <version>`. Without
    that line the fix is not observable at the bench: both states end with a correct answer, and only
    the drained byte count separates them.
  - ⚠️ **And with it working, `'Q'` turns out not to shorten anything here.** Same board, same
    Stop, `Stop-sweep sent` in the log: still 7172 bytes. The drain now reports its duration too, and
    that is what settles it — **414 ms, of which 268 ms is the unconditional quiet window**. The
    7172 bytes read out in ~146 ms, seven turns of a loop that polls every 20 ms, which on USB CDC
    means they were already in the buffer. A board still sweeping would have taken past 1500 ms.
  - The cause is the **sequence**, not the firmware, whose poll is correct and correctly placed. The
    parent regains the port only after the child releases it, and the child releases it once the
    board has finished, so `'Q'` always reaches an idle board. A timely one would have to be sent by
    the child, and its whole prize is those ~146 ms. The stop path is not being restructured for
    that. `'Q'` stays — right primitive, one write, harmless — but the claim that it turns waiting
    out a sweep into milliseconds was mine and the bench did not support it.

- **A question asked while the board is still talking is answered with sweep data** — after a Stop
  the board keeps sending for the rest of its sweep (~1.8 s per overtone), and
  `reset_input_buffer()` empties what has arrived, not what is still coming. The firmware check read
  `amplitude;phase` lines and reported them as *Please update firmware version*.
  - `_drain_serial()` waits for 250 ms of silence before every query, inside `_serial_query`, giving
    up after 6 s. `_reacquire_serial_lock` also sends `'Q'` now — but only to a firmware that knows
    it, since on an older one the letter would start a 0 Hz scan.
  - `_board_busy()` reports a busy board as busy: *The board is still sending measurement data* and
    not as a firmware to update. Two signs, either enough — the port never fell silent, or the answer
    carries a semicolon.
  - Simulated against a board streaming for 1.8 s: 1360 bytes drained and the real answer parsed; a
    board that never stops is reported busy after 6 s instead of answering with a sweep line.
- **A finished peak detection gives the port back** — its completion path calls only `_enable_ui`,
  never `stop()`, so the GUI never re-acquired the handle and the two device queries stayed greyed
  out until the user disconnected and reconnected.
- **Machine identification number: firmware 0.1.5b as its own folders, and the host side** —
  - `firmware/openQCM_Next_py_0.1.5b_teensy/` and `..._0.1.5b_TEST_teensy/` carry the `'S'` command.
    ⚠️ The **`0.1.5a` pair is restored to exactly what it was and kept**, to be deleted later: the
    previous commit had bumped `FW_VERSION` inside folders named `0.1.5a`, which left a sketch
    reporting a version its own directory contradicted.
  - **Host**: `Tools > Check Board Serial Number`, plus the same query run silently on connect.
    Three outcomes, distinguished on purpose — no valid answer is a firmware older than 0.1.5b,
    `NO_SERIAL` is an unprogrammed EEPROM, anything matching `^\d{3,5}$` within 100–25599 is the
    number. Shown under the brand (`lblSerialNumber`, themed) and in the window title.
  - ⚠️ The window title has **two independent suffixes** — the board number from connect, the
    datalog filename from START — so it is composed in one place, `_window_title()`. Writing either
    straight into `setWindowTitle` erases the other.
  - Verified: all five sketches compile for `teensy:avr:teensy40`; the restored 0.1.5a pair is
    byte-identical to its previous state; and `_query_serial_number` driven against a stub gives
    `1920` → S/N shown and title `openQCM NEXT [1920]`, `NO_SERIAL` → "not programmed",
    empty / `0.1.5b` / `99999` → treated as no answer, and a reply with a leading blank line still
    parses. With a log open the title composes as `openQCM NEXT [1920] — <file>.csv`.
- **Machine identification number: the `'S'` command, in both operational firmwares** — the board
  reports its number over serial, `1920`, or `NO_SERIAL` when the EEPROM has never been programmed.
  It only ever reads: an unprogrammed board is reported as such and nothing is written to it.
  - The branch sits beside `'F'` in both sketches — production and the no-TEC TEST variant, which is
    kept in step with production while the prototype board is in use. `'S'` was free: the protocol
    uses T C P I D X A L F E and a sweep command starts with a digit.
  - Both firmwares go to **`0.1.5b`** (`0.1.5b-TEST` for the variant), and ⚠️ **`Constants.FW_VERSION`
    moves with them**: the host compares the `'F'` reply against that string exactly and pops a
    firmware-update warning on any difference, so a bump that stopped at the sketch would warn on
    every connect.
  - `OPENQCM_SERIALNUMBER` is **1900** — series 19, unit 00. It read 1920 when the sketch was
    written and this entry said so until 2026-09-01; the current value reached this branch
    inside the `0.1.5c` cherry-pick, which staged the whole firmware directory and says
    nothing about the number. See the note at the top of this file.
  - Verified: all three sketches compile for `teensy:avr:teensy40` (programmer 35856 bytes,
    production 55056, TEST 45500).
- **Machine identification number: the programmer sketch** —
  `firmware/openQCM_Next_SerialNumber/`, ported from the Q-1 tool and written to the shared
  serial-number format specification. It writes four bytes into the Teensy EEPROM — magic `0xA5`,
  series, unit high, unit low, big-endian — **the Q-1 layout byte for byte**, so a board programmed
  by either tool reads correctly in both.
  - The format is **`SSNN`, one compact integer with no separator**: series 20 unit 52 is `2052`,
    and the board after `2099` is `2100`. The obsolete `SERIES-NNNN` form appears nowhere.
  - The operator sets **one macro**, `OPENQCM_SERIALNUMBER`; series and unit are derived at compile
    time, so they cannot disagree. A `#error` rejects anything outside 100–25599.
  - An existing number is never overwritten without a `Y` on the serial monitor.
  - Verified: compiles clean for `teensy:avr:teensy40`; the range guard fires at both 99 and 25600;
    and the format expressions, compiled and run on the host, give `100 / 2052 / 2099 / 2100 /
    25599` with the EEPROM round trip intact.
  - ⚠️ `OPENQCM_SERIALNUMBER` is currently the placeholder **100** — set it to the real number
    before programming the first board.
- ⚠️ **TEST-ONLY firmware variant (no-TEC board)** — _internal, temporary; to be removed._
  New Teensy sketch `firmware/openQCM_Next_py_0.1.5a_TEST_teensy/` (version `0.1.5a-TEST`)
  for a special openQCM NEXT board built for testing that **does not mount the
  temperature-control (TEC) section** (no MTD415T on Serial1, no MCP9808, no fan / enable /
  status / control-switch pins). It strips every Serial1/MTD415T interaction (which would
  otherwise block ~250 ms per query on a board with no TEC), keeps the DDS/ADC sweep engine
  identical to production, and **simulates the temperature** (stable `25.00 °C` baseline with
  a slow ±`0.05 °C` wobble; optional real Teensy die temperature via `#define USE_INTERNAL_TEMP`).
  The end-of-measurement line stays fully host-compatible — `temperature;status(0);error(0);s` —
  so **no software change is required**; TEC commands (`T/C/P/I/D/L/X/A/E`) are accepted as
  benign no-ops. Compiles clean for Teensy 4.0. **This is a throwaway variant for internal
  bench testing and will be deleted once the test board is retired — do not build on it.**
- **Pinned dependencies for reproducible setup**: `software/requirements.txt` (pip) and
  `software/environment.yml` (conda). Tested on Python 3.9.12; PyQt5 pinned to 5.9.2
  (the GUI relies on the classic QtGui widget namespace).
- **Serial connection as a separate feature (Step 1)**: dedicated **Connect / Disconnect**
  and **Refresh** buttons (in the Start/Stop row), decoupled from the operation-mode selection.
  - **Refresh** rescans connected devices (serial ports) on demand; disabled while connected.
  - Multi-instance protection via a per-port lock file (`fcntl` on Unix, skipped on
    Windows where COM ports are natively exclusive).
  - On connect the port is validated (open/close probe) and the **firmware version
    check runs here** (moved from the blind call at application startup).
  - **START is now gated on an active connection** (`_enable_ui`), and the port
    combo box is disabled while connected. Connection status shown in `label_COM_status`.
- **Serial connection — Step 2**: the connection now holds a **persistent, exclusive**
  serial handle (`_serial_lock`) while idle (Standby). The GUI serial queries (set
  temperature, TEC on/off, PID, firmware version) go through it via `_serial_write` /
  `_serial_query` instead of opening the port ad-hoc; the port is **handed over** to the
  acquisition process on START (handle closed) and **re-acquired** on STOP.
- **GUI theme system (dark/light)** — first phase (Phase 0) of the GUI redesign inspired by
  openQCM Q-1 v3.0. New `ui/theme.py` (`LIGHT`/`DARK` palettes + a parameterised Qt Style Sheet
  builder + per-theme pyqtgraph plot colors) and a **View → Theme → Light/Dark** menu in
  `ui/mainWindow.py` (`_setup_theme_menu`, `_apply_theme`, `_apply_plot_theme`). The whole window
  (controls, group boxes, tabs, menus, readout fields) and the plots (background, axes, titles)
  follow the active theme; accent blue `#008EC0` and dissipation brown `#DD8E6B` stay fixed on both.
  The choice persists in `QSettings('openQCM','NEXT')` (default light on first run). The per-overtone
  readout fields (`F0`..`D9`, temperature indicator) were migrated from hardcoded white inline styles
  to QSS objectName rules so they theme correctly.
- **GUI single-window shell (QSplitter)** — Phase 1 of the GUI redesign. `_build_shell()` in
  `ui/mainWindow.py` (called at the end of `__init__`) re-parents the fixed two-column grid into a
  horizontal `QSplitter`: a scrollable, collapsible left sidebar of control groups (brand, connection,
  F/D readouts, overtone selector, sampling, Temperature/PID tab, with the action row + status pinned
  to the bottom) and the plots on the right. Widgets are moved as-is (objectNames + signal wiring
  preserved), so it composes with the theme and all existing behaviour; commenting out the
  `_build_shell()` call reverts to the old layout. **⚠️ Visual layout tuning is still pending** (see
  HANDOFF §5): the action-button row is cramped in the narrow sidebar and needs rearranging.
- **Scientific menu wiring (GUI redesign Phase 5)** — completes the File/View/Tools/Help menu.
  `Help → Help` now opens the openQCM NEXT software webpage (replacing the `dummy` placeholder) and a
  new `Help → About openQCM NEXT` dialog shows name/version/description + link; `View` gained
  show/hide toggles for the **Sidebar** (`sidebarScroll`) and the bottom **Status bar**
  (`statusBarFrame`). File→Quit, View→Theme/Δ Cursors, Tools→Raw/Log/Tec, Help→Firmware/Software were
  already wired. This closes the phased GUI redesign (Phases 0–5).
- **GUI refinement pass (main window)** — visual/UX polish on top of the phased redesign:
  - Single **temperature ON/OFF toggle** replacing the two buttons: blue "ON" (enable) / brown "OFF"
    (disable), enabled only while the serial port is connected, kept in sync with the firmware TEC
    status during acquisition (`_toggle_temperature_control` / `_update_tec_toggle` / `_tec_on`).
  - Unified **"secondary" outline button style** (blue outline; brown for a toggle's deactivate state
    — Disconnect, temperature OFF; grey outline when disabled) applied to Connect/Disconnect, Refresh,
    the plot controls, T SET and TEC Reset; each sized to its label (trailing stretch) so it no longer
    fills the sidebar width.
  - **Renames**: Autoscale → AUTO, Set/Clear Reference → SET REF / UNSET REF, Clear Plots → CLEAR,
    Temperature Set → T SET.
  - **Card titles** rendered bold (set on the `QGroupBox` widget font — Qt ignores font-weight on the
    `::title` subcontrol — with the card content reset to normal weight).
  - **Start / Stop** button: larger (17 px, not bold) with minimalist outline glyphs (▷ play / □ stop).
  - **Plot Controls** card anchored just below Temperature (the sidebar stretch now sits between it
    and the Start/Stop button).
  - Removed redundant sidebar captions ("Serial COM Port", the "Connected: …" status label,
    "Operation mode", "Frequency (single mode)"); the **frequency selector is shown only in Single
    Measurement**.
  - **Sidebar**: correct default width (300 px), smoothly resizable (260–400 px); the rich-text brand
    label now wraps so it no longer forces a ~459 px minimum that clipped the column.
  - **Temperature card** redistributed: the setpoint spinbox and the live temperature indicator are
    aligned to the right margin with an expanding gap.
- **GUI System Log tab (Phase 2 of the GUI redesign)** — the center pane is now a `QTabWidget`
  (`centerTabs`) with **Plots** and **System Log** tabs. The plots are re-parented as-is into the
  Plots tab (no widget recreated); the System Log tab hosts a read-only `QTextEdit` (`systemLog`)
  fed by a new `LogStream` class that mirrors the **main process's** `stdout`/`stderr` into the
  widget with `[HH:MM:SS]` timestamps while still forwarding to the original streams (terminal +
  rotating log file unaffected). Installed in `__init__` right after `_build_shell()`, restored in
  `closeEvent`. Theme-aware, monospace (`QTextEdit#systemLog` rule added to `ui/theme.py`). Scope:
  captures main-process `print()`; child-process (Serial/Multiscan/Calibration) prints and
  `logging`-module messages are not intercepted (they keep going to terminal / log file). Adapted
  from openQCM Q-1 v3.0.
- **GUI single Start/Stop toggle (Phase 3a of the GUI redesign)** — the separate Start and Stop
  buttons are merged into one toggle on `pButton_Start`: it runs `_toggle_start_stop()` (Stop if
  acquiring, else Start), stays enabled while running (gated only on an active serial connection),
  and shows **Start** (green) / **Stop** (red) via a `running` dynamic property + `unpolish/polish`
  and theme QSS (`#pButton_Start` in `ui/theme.py`). The visual state flips inside `_enable_ui`, so
  it tracks every idle↔running transition (start / stop / normal completion / calibration cancel).
  The old `pButton_Stop` is hidden and the inline stylesheet on `pButton_Start` is dropped so the
  toggle follows the theme. Adapted from openQCM Q-1 v3.0.
- **GUI datalog filename display (Phase 3d of the GUI redesign)** — while acquiring, the active
  CSV filename is shown in the sidebar (new runtime `lblLogFile` label, middle-elided with the full
  name as tooltip, accent-colored via theme QSS) and appended to the window title; both are cleared
  on Stop. A new `Worker.get_csv_filename()` getter mirrors the names composed by the datalog loop
  (serial: `<ts>_<overtone>.csv`, multiscan: `<ts>_multi_.csv`; calibration returns an empty string
  → label hidden). Adapted from openQCM Q-1 v3.0.
- **GUI theme-aware program status pill (Phase 3c of the GUI redesign)** — the `infostatus` label
  is now styled through a `_status_pill(key)` helper (`standby`/`warn`/`err`/`ok`): the standby
  state follows the active theme palette (fixing the light pill stuck on the dark theme), while the
  warning/error/ok states keep their yellow/red/green backgrounds with forced dark text; all 15
  inline `setStyleSheet` call sites were converted. Status texts drop the hardcoded black
  `<font>` HTML in favour of a `● Program Status: …` prefix whose dot/text color comes from the
  pill stylesheet. A theme switch re-applies the current pill (`_apply_theme` remembers the last
  state via `_status_key`); the "Stanby" typo is fixed. `infobar` message colors are unchanged.
- **GUI overtone quick-select buttons F0–F9 (Phase 3b of the GUI redesign)** — five compact
  checkable buttons replace the legacy overtone radio row visually (the hidden radios remain the
  source of truth for `scan_selector`, so the plotting/readout logic is untouched). Behaviour by
  mode: **multiscan** = multi-select, purely-visual curve filter, live during acquisition (all
  overtones are always acquired); **serial** = exclusive selection that drives `cBox_Speed` (the
  combo lists the calibrated overtones in reverse order) with bidirectional sync, idle-only;
  **calibration** = disabled. Styled via `overtoneBtn` property QSS (accent when checked, kept on
  `:checked:disabled`). Adapted from openQCM Q-1 v3.0 with the NEXT-specific multiscan semantics.
- **GUI sidebar action-area layout (Phase 3e of the GUI redesign)** — resolves the cramped
  action row flagged in Phase 1: **Refresh + Connect** move into the connection card as its bottom
  row (`gridLayout`), styled by theme QSS objectName rules instead of their former inline
  stylesheets; in `_build_shell` the legacy action row is decomposed — the plot controls
  (Reference / Clear) keep the old row, while the **Start/Stop toggle gets its own prominent
  full-width row** (min-height 34) with the **progress bar underneath**, followed by the status
  labels at the sidebar bottom.
- **Responsive, clean cancellation of Peak Detection (calibration)** — ported and adapted
  from the more mature openQCM Q-1 v3.0. The peak-detection sweep can now be stopped mid-run
  without a hard process kill or a corrupt serial state, replacing the previous behaviour where
  the **Stop** button was disabled for the whole (~1 min) sweep.
  - `processors/Calibration.py`: the inner sweep-read loop now polls `self._exit`
    (`while not self._exit.is_set()`) with a short `0.1 s` serial read timeout, so a Stop
    interrupts within ~0.1 s instead of blocking on `serial_timeout_ms` (4 s). On cancellation
    mid-sweep (`_exit` set with `k < calib_sections` and no acquisition error) it emits a `-1`
    sentinel on `parser5` and returns, skipping peak detection / file storage. On start it drains
    any bytes left over from a previously interrupted run before sweeping.
  - `core/worker.py`: latches the `-1` sentinel in `_queue_data5` into `_calibration_cancelled`
    (exposed via `is_calibration_cancelled()`, reset each `start()`); `stop()` now shuts the
    peak-detection process down gracefully (`join` first, `terminate()` only as a fallback) so the
    serial port is released cleanly. Measurement modes (serial/multiscan) keep the direct terminate.
  - `ui/mainWindow.py`: the **Stop** button is no longer disabled during peak detection; the
    calibration branch of `_update_plot` checks `is_calibration_cancelled()` first and tears down
    once; `stop()` reports **"Peak Detection Cancelled"** when invoked during calibration.
    Fixed a latent `AttributeError` this exposed: `stop()`'s legend-removal loop read
    `self._overtones_number_all`, which was only set for serial/multiscan — undefined in
    calibration mode, where `stop()` was previously unreachable (Stop disabled). It is now
    initialised to `0` in `__init__` (and in the calibration `start()` branch), so the loop is a
    no-op. Without this, pressing Stop mid-peak-detection raised before `worker.stop()` ran and the
    sweep continued to completion.

### Added
- **GUI plot interactions (Phase 4 of the GUI redesign)** — adapted from openQCM Q-1 v3.0, on
  NEXT's **two separate** frequency / dissipation panels (single dual-axis panel explicitly
  rejected):
  - **Grid off by default** everywhere (the phase overlay's grid was the only one still on) with a
    per-plot **Show/Hide grid** toggle (`alpha 0.3`; the amplitude and phase-twin grids toggle
    together).
  - **Custom right-click menu** on all four plots (amplitude/phase, temperature, frequency,
    dissipation): Auto-scale, Reset zoom, mouse pan/select-zoom mode switch, grid toggle — one
    `sigMouseClicked` handler per pyqtgraph scene with viewbox hit-testing (the default pyqtgraph
    menus were already suppressed).
  - **Δ cursors on the frequency and dissipation panels**: two movable time cursors per panel
    (amber/green) with a live readout of `Δt` (the axis carries epoch µs → seconds) and `ΔF` (Hz)
    or `ΔD` (ppm) computed by nearest-sample lookup on the plotted buffers (multiscan → the
    fundamental, single mode → the measured overtone, same convention as the status bar). Toggled
    per-panel from the right-click menu or globally via the new **View → Δ Cursors (F / D)**
    checkable action (state kept in sync). Cursor items are parented to the ViewBox with
    `ignoreBounds` so they survive `clear()` and never drive the autorange.
  - Min-Y-scale enforcement deferred by decision.

### Changed
- **GUI palette reduction — Start/Stop toggle now blue/brown** — moving toward a two-color palette
  (openQCM blue `#008EC0` + brown `#DD8E6B`): the Start/Stop toggle is **blue when idle (Start)**
  and **brown when running (Stop)** instead of red. Added `brown` / `brown_hover` palette keys
  (`ui/theme.py`, `#DD8E6B` on both themes). The remaining state colors (status pill yellow/red/
  green) are left for a follow-up pass.
- **GUI center: collapsible amplitude/temperature pane + per-plot readout cards** — the Plots tab
  is now a vertical `QSplitter` (`plotSplitter`): the amplitude/phase-sweep + temperature canvases
  sit on top and can be **collapsed/hidden by dragging the handle** (`setCollapsible(0, True)`);
  the frequency and dissipation plots take the bottom pane. The per-overtone F/D readouts moved out
  of the sidebar "Current Readings" card into two **horizontal cards above their plots**:
  "Frequency (Hz)" above the frequency plot (F0..F9 + color swatches) and "Dissipation (ppm)" above
  the dissipation plot (D0..D9 + swatches). Readout widget names are unchanged (`F0..F9` / `D0..D9`
  / `label_F*_col`; new `label_D*_col` swatches wired into the controller), so the update logic is
  untouched. The now-empty sidebar "Current Readings" card was removed (also helps the sidebar stay
  narrow).
- **GUI Plot Controls card + Autoscale button** — the plot-control buttons moved from a plain
  row into a titled **"Plot Controls"** sidebar card holding **Autoscale**, **Set/Clear Reference**
  (the toggle) and **Clear Plots**. The new **Autoscale** button (`pButton_Autoscale` →
  `autoscale()` → `_autoscale_plot_all(True)`) re-enables **X and Y autorange on all four plots**
  (amplitude/sweep, frequency, dissipation, temperature); it follows the other plot controls'
  enable state (usable during acquisition). Styled as a card via `#groupPlotControls` QSS.
- **GUI Temperature card simplified — removed the inner tab container** — the Temperature card
  wrapped its controls in a single-tab `QTabWidget` whose bordered `::pane` drew a redundant box
  inside the card. The `QTabWidget` is gone; the Temperature Control widgets now sit directly in
  the `groupTempPID` card (borderless `tab` container + `gridLayout_4`, top separator `line_4`
  hidden). The PID widgets stay created on a hidden standalone `tab_2` (kept for the controller /
  future advanced-temperature window). The center Plots/System Log tab widget is unaffected.
- **GUI sidebar horizontal compaction (fine-tuning)** — several changes to narrow the sidebar:
  F0–F9 overtone chips shrunk to the minimum (tight padding, `min-width: 0`, 3px row spacing);
  the TEC **ON / OFF / RESET** buttons moved onto a single compact equal-width row (tight padding);
  **Set Reference / Clear Reference merged into one toggle** on `pButton_Reference`
  (`_toggle_reference` calls `reference()` / `reference_not()` by `_reference_flag` and relabels
  the button; the label is re-synced on Start; `pButton_Reference_Not` is hidden but kept alive);
  the Temperature Control state banner now word-wraps so its longer state strings no longer force
  the card wide; the sidebar scroll `minimumWidth` lowered 220 → 170. The current-readings F/D grid
  is deliberately left for a later pass (now the main remaining width driver).
- **GUI fine-tuning: hide datalog sampling time and the PID section** — the datalog
  sampling-time selector is hidden from the sidebar (kept created/functional — acquisition uses
  the default sampling time; "Time elapsed" stays). The Temperature card is simplified to
  Temperature Control only: the PID Control tab is removed and the now single-tab bar hidden, card
  renamed "Temperature". Everything is **hidden-only** — the PID widgets (`cBox_PID`,
  `spinBox_Cycling_Time/P/I/D_Share`, `pButton_PID_Set` on the still-alive `tab_2`) and
  `cBox_sampling_time` stay created and referenced by the controller, so no logic changed. Advanced
  temperature/PID control is planned as a **dedicated window** (see HANDOFF §5).
- **GUI: programmatic UI builder (redesign R1, structural parity)** — the Qt-Designer generated
  `ui/mainWindow_new_ui.py` is replaced by a hand-written `ui/mainWindow_ui.py` (same
  `Ui_MainWindow` class name, one-line import switch in `ui/mainWindow.py`), in the style of
  openQCM Q-1 v3.0. The builder constructs the single-window shell **directly** — splitter
  [scrollable sidebar | center tabs (Plots | System Log)] — making the whole `_build_shell()`
  re-parenting layer obsolete (method deleted). It also absorbs every widget previously created at
  runtime: Connect/Refresh (connection-card bottom row), the F0–F9 overtone quick-select buttons
  (legacy radios created hidden, still the `scan_selector` source of truth), `systemLog`,
  `lblLogFile`, and the hidden legacy `pButton_Stop`. New **File / View / Tools / Help menu
  skeleton** (File→Quit; Tools→Raw Data / Log Data / Tec Current; Help→Help / Firmware Info /
  Software Info; the theme submenu now populates the builder's View menu). The controller keeps
  all behaviour and only wires signals (`_setup_serial_connection_ui`, `_setup_overtone_buttons`,
  `_setup_log_filename_label`, `_install_system_log` reduced to wiring/aliases). Verified by an
  attribute-contract check (every `self.ui.<name>` the controller references exists on the new
  builder) plus an offscreen `QT_QPA_PLATFORM=offscreen` instantiation; widget properties
  (spinbox ranges/defaults, combo policies, texts, brand header, tab titles) replicated from the
  generated file, which stays in the repo as reference. Visual-style pass (mockup cards, bottom
  status bar) is the follow-up R2 step.
- **GUI: mockup style pass (redesign R2)** — on top of the R1 programmatic builder:
  - **Full-width bottom status bar** (`statusBarFrame`): the program-status pill (`infostatus`) and
    message (`infobar`) move out of the sidebar to the bar's left; compact live readings
    **F / D / T / S** (`statusFreqValue`/`statusDissValue`/`statusTempValue`/`statusSampValue`) and
    the **progress bar** (fixed 160 px) sit on the right. Readings are mirrored from the existing
    update paths: fundamental in multiscan / measured overtone in single mode
    (`_update_indicator_F/_D[_single]`), temperature via a new `_set_indicator_temperature`
    helper, elapsed time next to `time_indicator`; reset to `--` on Stop
    (`_reset_status_readings`).
  - **Card-style sidebar**: "Serial Connection" (COM row + Refresh/Connect) and "Measurement
    Setup" (mode, single-mode frequency, F0–F9 quick-select, datalog sampling + elapsed time)
    become titled group boxes; the readouts card and the Temperature/PID tabs follow; the datalog
    filename sits right above a prominent Start toggle at the sidebar bottom. Brand header
    restyled (left-aligned title + muted subtitle, no hardcoded black).
  - **Dark-theme fix**: the sidebar container and scroll-area viewport now follow the theme
    palette (they defaulted to the platform light palette, leaving gray-on-gray labels on dark).
- **GUI: R2 mockup-fidelity fixes** (after the first on-device check):
  - **Status-bar height bug fixed**: `statusBarFrame` had no fixed height and swallowed half the
    window (squeezing the sidebar into a scroll). Now `setFixedHeight(36)` + the splitter takes
    all extra vertical space (`outer.addWidget(mainSplitter, 1)`).
  - **Mockup styling**: card titles rendered **inside** the rounded cards (bold, objectName-scoped
    QSS); the Temperature/PID tabs wrapped in a **"Temperature & PID"** card; readouts card
    retitled "Current Readings — F (Hz) · D (ppm)"; Start toggle idle color switched to the
    **accent blue** of the mockup (running stays red); F0–F9 restyled as rounded chips;
    status-bar readings use full text color.
  - **Theme quick-toggle** in the menu-bar top-right corner (`themeToggleButton`, shows the theme
    it switches to), wired alongside the View → Theme menu.
  - **Plot canvas order** per the mockup: amplitude/phase sweep + temperature on top, then the
    resonance-frequency and dissipation time series.
- **GUI: dark-theme completeness fixes** (after the second on-device check): generic
  `QPushButton` base style (the untargeted buttons — TEC ON/OFF/RESET, PID Set, Reference/Clear —
  fell back to the native light style on dark), themed scroll bars, themed horizontal separator
  lines, themed splitter handle. **Menu bar forced in-window** (`setNativeMenuBar(False)`): on
  macOS the native system bar swallowed the File/View/Tools/Help row and the corner theme toggle
  (mockup layout restored). Fixed "Temperature _PID" card title — the `&` needed escaping (`&&`).
- **GUI: QSS refinement pass (mockup fidelity)** — refined light/dark palettes (softer window,
  borders and field fills), 10px rounded cards with 13px bold inside titles and wider sidebar
  spacing, restyled inputs (rounded, padded, min-height), **Connect primary / Refresh outline**
  button pair, larger Start toggle (40px, 14px bold), pill-shaped F0–F9 chips, **borderless bold
  readout values** (F/D grid, temperature, elapsed time), themed tabs (accent bold on the selected
  tab, rounded pane), slim rounded progress bar, padded in-window menu items, muted infobar. The
  TEC state banner's six inline styles are replaced by a theme-aware `_tec_state_pill` helper
  (off follows the theme; warn amber / active translucent accent / err red), re-applied on theme
  switch. Note: frequency and dissipation keep **two separate plot panels** by explicit decision.
- **Entry point unified into `run.py`**: added a thin `software/run.py` launcher and
  removed the duplicate root `software/app.py`; the `OPENQCM` class now lives only in
  `openQCM/app.py`. Launch with `python run.py` (or `python -m openQCM`).
- Firmware version check no longer runs automatically at startup; it runs on connect.
- **Robust anti-outlier averaging of the raw acquisition buffer**: every physical observable
  averaged from the 10-sample circular buffer — resonance frequency and dissipation (per
  overtone) and temperature — is now aggregated with `scipy.stats.trim_mean` (proportion
  `Constants.trim_mean_proportiontocut = 0.10`) instead of Savitzky-Golay + `np.average`,
  consistently across **both** acquisition processors (`processors/Multiscan.py`, multi-overtone,
  and `processors/Serial.py`, single-overtone). The former SG (window=3, order=1) was a linear
  3-point moving average with no outlier rejection — a single bad sweep leaked almost fully into
  the logged value (and was amplified at the buffer edges by the SG reflective padding).
  `trim_mean` drops the min/max sample before averaging, staying as smooth as the mean (no median
  "staircase"). The per-sweep Savitzky-Golay (sweep-curve smoothing, Stage A) is unchanged; the
  datalog-decimation average in `core/worker.py` is a separate, pending change.
- **Development: observable plots default to Y autorange** (`ui/mainWindow.py`,
  `core/constants.py`): the per-update forced (padded) Y-range on the frequency, dissipation and
  temperature plots is now gated behind `Constants.plot_force_yrange` (default `False`), applied
  through a new `_set_yrange_forced` helper. With the flag off the plots autoscale tight to the
  data; the forced range — introduced so autoscale would not over-emphasise small signal
  variations — can be restored and its paddings (`y_f_range` / `y_d_range` / `y_t_range`) tuned
  for distribution by setting the flag `True`. The sweep-spectrum plot's own fixed range is
  unchanged.

### Fixed
- **The device queries come back in standby** — after a Stop or a finished peak detection the two
  Tools entries stayed greyed out, so the firmware version and the board number could not be asked
  for again without disconnecting.
  - ⚠️ **Ordering**: `stop()` calls `_enable_ui` *before* `worker.stop()` and a full second before
    `_reacquire_serial_lock()`, so the menu state it computed was a second out of date. The refresh
    moves into `_reacquire_serial_lock()` — every path that regains the port ends there — and
    `start()` greys them the moment it hands the port over.
  - ⚠️ **`_serial_connected` was the wrong test**: `start()` hands the port over by **closing the
    handle without dropping the reference**, so `_serial_lock is not None` stays true while the child
    process owns the port. `_can_query_device()` asks whether the handle is **open** and whether the
    worker is idle, and it now drives both the menu state and the two methods' guards — a greyed
    entry and a refused query can no longer disagree.
  - The refusal message says what to do about either cause: *Connect to the device, and stop the
    acquisition first.*
  - Verified across the lifecycle: disconnected, acquiring, stopped-but-port-not-back and
    connected-without-a-handle all grey the entries; connected in standby and stopped-with-the-port-
    re-acquired enable them.
- **Disabled menu entries look disabled** — the two device queries were correctly unclickable and
  still painted like every other entry, which reads as a bug rather than as a state. ⚠️ Once a style
  sheet sets a colour on `QMenu`, Qt stops applying its own disabled palette to the items, so it has
  to be said: `QMenu::item:disabled` in `disabled_text` (`#9aa0a6` light, `#7c8085` dark), plus
  `QMenu::item:selected:disabled` so the highlight stops following the cursor over an entry that
  would do nothing — an item that lights up and then ignores the click is worse than one that never
  lights up. `QMenuBar::item:disabled` goes with them. It applies to every menu in the application,
  not only these two entries.
- **The two device queries are greyed out unless the board can answer them** — *Check Firmware
  Version* and *Check Board Serial Number* talk to the board over the persistent serial handle, so
  they need an open port and an idle acquisition; while a measurement runs, the child process owns
  the port.
  - ⚠️ Disconnected, the firmware query ran anyway and came back empty, which that code reads as "no
    firmware information" and answers with ***Please update firmware version*** — a closed port
    reported as an out-of-date board, and the wrong problem to go looking for. It now has the same
    not-connected guard the serial-number query already had.
  - `_enable_device_queries()` is called from `_enable_ui` and from both branches that move the
    connection state, so the menu follows Start.
  - The runtime guards stay: a menu item can be reached by a shortcut, and the automatic query on
    connect never goes through the menu.
  - Verified on the three states: disconnected and acquiring both grey the entries and both methods
    warn if reached anyway; connected and idle, the firmware query answers with its information
    popup.
- **A board reply is read as its first non-empty line, everywhere** — the firmware-version check used
  `read_serial.rstrip('\r\n')`, which strips only the **trailing** terminator. A leading blank line
  survives it, so `'\r\n0.1.5b-TEST\r\n'` compared as `'\r\n0.1.5b-TEST'` and raised the
  firmware-update warning; measured, the old rule fails on exactly that shape while the new one does
  not. `_first_reply_line()` is now the single parsing rule for the firmware version and for the
  identification number, which already read replies that way.
- ⚠️ **The branches that raise the update warning printed nothing**, so a wrong answer and no answer
  at all were indistinguishable from the outside. Both now log the raw reply, `repr()` included, and
  the serial-number query prints the raw bytes beside the parsed value.
- **`PopUp.info` does not exist in NEXT** — the board-number query raised `AttributeError` the first
  time the menu entry was clicked with a programmed board. `info()` is a Q-1 method; NEXT's
  equivalent is `info_not_blocking()`, and the call was ported without checking. ⚠️ The reason it
  survived verification: every path was exercised with `auto_mode=True`, which is precisely the mode
  that **skips all four popups**. The regression check now runs `auto_mode=False` with `PopUp`
  replaced by a recorder — `PopUp.warning` is modal and would otherwise hang a headless run — and
  asserts that every method it names exists on the real class: `info_not_blocking` on success,
  `warning` for a blank EEPROM, for no answer, for a closed port and for a running acquisition.
- **Application icon now loads on all platforms** — it was set from non-resolving paths:
  `app.py` used the Windows-only `'\icon\favicon.ico'`, and the window icon + sidebar brand logo
  used the cwd-relative `"favicon.png"`, so no icon appeared on macOS/Linux (or whenever the app
  was launched from another directory). All three now use an absolute, module-relative path to
  `openQCM/res/icon/favicon.png`: `QApplication.setWindowIcon` (dock / taskbar + default window
  icon), the `MainWindow` window icon, and the sidebar brand logo (guarded by `os.path.exists`).
- **Long serial-port name widened the sidebar** — on Connect, `label_COM_status` showed
  "Connected: <port>" and a long port name forced the whole (scroll-bar-off) sidebar wider. The
  label now has an `Ignored` horizontal size policy and `minimumWidth 0`, so its content never
  dictates the sidebar width (the full "Connected: <port>" is kept in its tooltip).
- **Peak-detection / calibration plot was invisible on the light theme** — the live amplitude
  sweep drawn during peak detection (and the serial-mode amplitude sweep and the temperature
  curve) used a hardcoded **white** pen (`Constants.plot_colors[0]` / `plot_color_temperature`),
  which vanished once the theme system set the light theme's plot background to white. These
  single curves now use a theme-aware foreground color (new `theme.PLOT[theme]["curve"]`, dark on
  light / light on dark) via a `_curve_color()` helper, applied at every plot/setData site and
  re-applied on theme switch in `_apply_plot_theme`. The colored multi-overtone
  frequency/dissipation curves were unaffected. Regression from the GUI theme system (Phase 0).

### Docs
- Rewrote `README.md` with a full structure (badges, TOC, features, architecture,
  version history, roadmap).
- Removed internal development references from the README.
- Expanded the Repository Structure (full software package tree) and aligned Quick Start /
  Features / Roadmap with the serial-connection flow (Connect/Disconnect/Refresh).
- Added a developer `HANDOFF.md` (architecture, branches incl. impedance-analysis, planned
  tasks, conventions/gotchas) so the project can be resumed from any clone.

## [v0.1.6G-test] — branch `impedance-analysis` (from v0.1.6-dev)
- Alternative impedance analysis via **conductance spectrum G(f)** derived from
  the AD8302 MAG/PHASE signals (software post-processing, same firmware).
- Core in `processors/Multiscan.py`; offline script `sweep_data/plot_conductance.py`.
- Note: approximate formula; development/DEBUG state. Not production-ready.

### Unreleased (impedance dev — 2026-07-21)
- **G DATA VIEW / `sweep_data/plot_conductance.py`** — offline-only additions
  (the live `Multiscan.py` pipeline is unchanged):
  - **Susceptance vs conductance (B–G) plots** — admittance locus per overtone.
    A raw `B = sin(phi)/|Z|` version (folded phase → "lens" shape), plus a
    **motional** version that reconstructs the *signed* phase (re-activated the
    unused `_phase_V_phase` unfold) and removes the baseline from G and B so the
    locus closes into the **admittance circle** (1:1 aspect via a new optional
    `_plot(..., aspect_equal=True)`).
  - **Exact complex-divider formula** (`_RX_exact`/`_G_exact`/`_B_exact`, from
    `docs/impedance-analysis/conductance-calculation.md`): inverts the divider
    `Z_q = M·e^{-j·phi} − R17` and computes `Y_q = 1/Z_q`. New "conductance
    (exact formula)" spectrum + exact admittance circle, side by side with the
    approximate ones. On real 5 MHz data the exact G_max is ~5× higher
    (physically plausible R_m), matching the synthetic prediction.
  - **Unit fix**: the "conductance shifted" plots were labelled mS but plotted S;
    now converted to mS.
  - ⚠️ **The "exact" formula is NOT yet validated against hardware** — the source
    doc `conductance-calculation.md` and its constants (R17, AD8302 slopes, V_CP,
    unfold heuristic) still need validation with known reference impedances; the
    synthetic test only proved algebraic self-consistency. See the doc's
    "VALIDATION STATUS" banner and `HANDOFF.md`.
  - ⏳ **Pending**: once validated, port the exact formula into
    `parameters_finder_impedance` (live pipeline) — this **will change the logged
    frequency/dissipation values**.
  - **Conditional phase unfold (liquid fix)** — new `_phase_signed()` used by the
    motional and exact B–G plots. The AD8302 outputs |phase| only; the previous
    always-unfold (`_phase_V_phase`: shift min→0 + flip after the minimum) is
    correct **only when the phase actually crosses zero** (air / low damping).
    In liquid the phase minimum stays 10–40° above zero (heavy damping, C0/stray
    dominated — no zero crossing): unfolding there subtracted a large real offset
    and inverted half the sweep, distorting the admittance locus into an **"S"**
    (observed on-device in liquid). `_phase_signed` unfolds only if
    `min|phase| < fold_threshold_deg` (default 5°; air minima ~0–2°, liquid
    ~10–40°), otherwise the raw phase already is the signed phase. Verified on
    synthetic BVD in both regimes: liquid exact G/B error 55%/121% → **0.000**,
    air unchanged. **Confirmed on-device**: the liquid B–G loci now close into
    circles (no more "S"). ⏳ A *systematic* test across the air→liquid transition
    (validating the `fold_threshold_deg` discrimination) is still to be run.
  - **Exact-formula fix + AIR VALIDATION (2026-07-23)** — root cause of the
    negative-resistance/negative-G circles found: the exact inversion was fed the
    **baseline-corrected** `V_MAG` (relative level; calibration polynomial
    subtracted), which scales `M = R17·10^((0.9−V)/0.6)` by `10^(Vb/0.6)` (0.55×
    at F0 → `M(res) < R17` → `R_q < 0` everywhere). **Fix**: new `amp_a_sp_raw`
    chain (same SG+spline, no baseline subtraction) feeds `_RX_exact`; the
    approximate path is untouched. The phase channel receives no baseline anywhere
    (verified offline + live) — correct for this method. Source PDFs confirm the
    divider topology and the INPB ×10 attenuation already compensated by the
    −0.6 V conversion offset. **On-device air validation (5 MHz)**: all exact
    circles at positive G; `R_m` = 10.6/12.1/40.5/76.5/132.6 Ω (F0→9th), `D` =
    3–10 ppm, circle-fit diameter = `G_max` within ±5% (rms 1–6%). The nominal
    constants are **rehabilitated**; remaining for metrology: phase systematics
    (esp. liquid) via reference-impedance calibration. Docs: rewritten
    "VALIDATION STATUS" banner in `conductance-calculation.md`.

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
