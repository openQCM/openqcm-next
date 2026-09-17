<!--
Italian on purpose, like docs/SESSION_PROMPT.md: this is the literal text to paste as the first message
of the next session on the impedance-analysis branch. Everything it points at is in English.
Written 2026-09-17, after commit 8e0e35f. The previous prompt of this series,
SESSION_PROMPT_liquid_frequency_excess.md, is done: its question (the liquid frequency excess) is
answered and the estimator it led to ships as an experimental mode.
-->

# openQCM NEXT — prompt per ripartire sul ramo `impedance-analysis`

Incolla tutto quello che segue come primo messaggio di una chat nuova aperta in
`/Users/marco/claude_code/openqcm-next`.

---

Lavoriamo su **openQCM NEXT**, ramo `impedance-analysis`, worktree
`/Users/marco/claude_code/openqcm-next-impedance`.

Questa sessione riparte da una precedente che si è saturata. **Prima di tutto leggi la documentazione del
progetto per sapere che cosa abbiamo fatto e a che punto siamo**, così da continuare con continuità dallo
stato attuale. Leggi nell'ordine:

1. `docs/SESSION_PROMPT.md` — come lavoro con te e le regole del repo (i due rami, il cherry-pick, il push).
   Valgono tutte.
2. `HANDOFF.md` §4 (ramo impedenza: catena, stimatore pubblicato, pannello, finestre, piano) e §6
   (convenzioni e trappole), poi §1 (moduli condivisi).
3. Le voci sotto `## [Unreleased]` in `CHANGELOG.md`: sono la cronologia recente, la più nuova in alto.
4. `docs/impedance-analysis/PLAN_psl_live_estimator.md` — il piano dello stimatore live: che cosa è fatto
   (T1–T6), che cosa resta (T7, al banco, mio), le decisioni D1–D11 già prese.
5. `docs/impedance-analysis/ALGORITHM.md` §7.1 per la matematica dello stimatore pubblicato, e
   `research/air-ipa-water-1920-2026-09-11/synthesis-two-lorentzians.md` per il risultato di ricerca da cui
   discende.

**Non fidarti della memoria che hai del codice: leggi il file prima di toccarlo.** I test si lanciano con
`cd software && PYTHONPATH=. python -m unittest discover tests` (62 al 2026-09-17, uno saltato offscreen).

Quando hai letto, **riportami in breve lo stato** (dieci righe bastano: che cosa pubblica il processo, che
cosa mostrano pannello e finestre, che cosa è aperto) **e poi fermati**: decido io che cosa fare e su cosa
lavorare. Le "cose aperte" che troverai nei documenti sono un inventario, non una coda di lavoro; non
propormi un programma dedotto da lì.
