<!--
Kept in Italian on purpose, unlike the rest of the repo: this file is not prose
about the code, it is the literal text to paste as the first message of a new
session, and the working language in chat is Italian. Everything it points at --
HANDOFF, CHANGELOG, the commit history -- is in English.

Keep it short and keep it true. It is a shortcut, not the source: HANDOFF.md
(§1 shared modules, §3 state on `main`, §6 conventions) and the `## [Unreleased]`
entries in CHANGELOG.md are.
-->

# openQCM NEXT — prompt per iniziare una nuova sessione

Incolla tutto quello che segue come primo messaggio della chat nuova, aprendola
nella cartella `/Users/marco/claude_code/openqcm-next`.

---

Lavoriamo su **openQCM NEXT**. Prima di toccare qualsiasi cosa leggi `HANDOFF.md`
(§1 moduli condivisi, §3 stato su `main`, §6 convenzioni) e le voci recenti di
`CHANGELOG.md` sotto `## [Unreleased]`. Non fidarti della tua memoria del codice:
leggi il file prima di modificarlo.

## Come lavoro

- **Parla italiano in chat, scrivi in inglese nel repo** — commit, documentazione,
  commenti.
- **Risposte concise.** Per modifiche non banali: prima il piano, poi esegui dopo
  il mio ok.
- **Misura invece di dedurre.** Se un tuo risultato precedente si rivela
  sbagliato, dillo esplicitamente con i numeri.
- Gli artifact che produci durante il lavoro sul codice devono essere **file
  markdown con le figure incorporate**.
- Dopo ogni commit+push su `main`, **allinea `HANDOFF.md` e `CHANGELOG.md`**.

## I due rami, e la regola che non si viola

Due worktree:

| | |
|---|---|
| `/Users/marco/claude_code/openqcm-next` | `main` |
| `/Users/marco/claude_code/openqcm-next-impedance` | `impedance-analysis` |

- ⚠️ **`main` NON deve contenere l'analisi di impedenza.** È già stato mergiato
  per errore due volte e revertito (`1b3fe81`). Il merge verso main avverrà in
  futuro ed è una mia decisione: **non proporlo** come "passo naturale" dopo un PR.
- ⚠️ **Mai `git merge main` dentro il branch.** Il codice condiviso si modifica su
  `main` e poi `git cherry-pick <sha>`, **un commit alla volta**.
- Il push richiede l'helper di `gh` (il token vive solo lì):
  `GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=credential.https://github.com.helper GIT_CONFIG_VALUE_0='!gh auth git-credential' git push origin <branch>`

## Trappole del repo

- ⚠️ `PeakFrequencies.txt` e `PeakFrequenciesRT.txt` sono **versionati di
  proposito** e non vanno scorporati: l'app non parte senza. Idem `config.txt`.
- ⚠️ Togliere un file dal tracking **lo cancella** su ogni altro clone che fa
  pull; `.gitignore` non protegge i file già tracciati.
- ⚠️ Prima di analizzare dati grezzi, **copiali fuori dal repo**: `sweep_data/`
  viene sovrascritta a ogni acquisizione e io riacquisisco spesso.
- ⚠️ Mai `git add -A`: i bit `skip-worktree` sono per-worktree e su un worktree
  possono non essere impostati.

## Ambiente

PyQt5 **5.9.2** / Qt 5.9.7 / Python 3.9.12 — namespace widget classico `QtGui`,
non "modernizzare". pyqtgraph 0.11.0 copia i membri di `QtWidgets` dentro `QtGui`,
quindi del codice funziona **per effetto collaterale** di un import di terze
parti: importa esplicitamente da `QtWidgets`.

Test headless con `QT_QPA_PLATFORM=offscreen`. Segfault noti: `QMainWindow.show()`,
un `QTabWidget` pieno di `GraphicsLayoutWidget`, due alberi openQCM nello stesso
processo Qt. I `QDialog` invece si mostrano e si catturano senza problemi.

## Cose aperte

### Tre interruttori da rimettere prima di una build di produzione

- ⚠️ **`Constants.environment = 3`** su entrambi i rami → **10**. Motivo ormai
  solo metrologico.
- ⚠️ **`Constants.accept_test_firmware = True`** → **`False`**. Fa passare il
  firmware `-TEST` della scheda prototipo; uno strumento spedito non deve
  accettarlo in silenzio.
- ⚠️ **`Constants.plot_reassert_yrange_freq_diss = False`** → **`True`** quando
  l'asse verticale di frequenza e dissipazione sarà sistemato. Ora i due
  pannelli non vengono più reinquadrati a ogni sweep, così uno zoom manuale
  resta.

### Il resto

- ⚠️ **Firmware: tre coppie in `firmware/`.** La corrente è **`0.1.5c`** (`'S'` e
  `'Q'`); `0.1.5b` e `0.1.5a` sono superate e **vanno cancellate** quando nessuna
  scheda le monta più. La variante `-TEST` senza TEC resta finché la scheda
  prototipo è in uso.
- ⚠️ **`firmware_update/` spedisce l'immagine `0.1.5`**, due versioni indietro:
  chi usa l'updater incluso finisce su un firmware che il software gli chiede
  subito di aggiornare.
- ⚠️ **`OPENQCM_SERIALNUMBER` diverge fra i due worktree**: 1900 su `main` (non
  committato) e 1920 sul ramo. Da decidere e allineare.
- ⚠️ **Sidebar tagliata**: il contenuto chiede **435 px**, il pannello ne concede
  260 al minimo e 400 al massimo. La scroll area è `widgetResizable` con la barra
  orizzontale spenta, quindi non scorre: **taglia**. Difetto preesistente.
- **Larghezza dei pill delle armoniche**: tentata **due volte** e revertita due
  volte. La seconda funzionava (chip fissi, gap elastici) ed è stata bocciata
  esteticamente: a sidebar larga cinque isolette. Quello che si è imparato sta in
  `HANDOFF.md` §3, "The overtone chips, and why they still stretch" — inclusa la
  variante mai provata: chip impaccati a sinistra con **un solo spaziatore in
  coda**, come i bottoni della temperatura.
- **`plot_color_multi_g`** (solo ramo): palette esadecimale dei grafici di
  conduttanza, copia di una lista blu più vecchia, mai allineata alle due rampe.
- Copia benigna di `savitzky_golay` in `sweep_data/plot_conductance.py` (ramo).
- `polyfit` in tre copie: `Multiscan.baseline_correction`,
  `Serial.baseline_correction`, `Calibration.baseline_estimation`.
- Zeri spinti ai grafici durante il warm-up del Multiscan.

## Una differenza fra i rami che è voluta

**N-SCALE** divide per l'ordine armonico: su `main` solo la frequenza, su
`impedance-analysis` **anche la dissipazione**. È specificato, non è deriva, e
**non va riconciliato** con un cherry-pick in nessuna delle due direzioni. La
suite di verifica legge dall'ambiente quale contratto sta controllando.
