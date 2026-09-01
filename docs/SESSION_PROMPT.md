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

## Da dove si riparte

L'ultimo blocco di lavoro — **numero identificativo macchina** (sketch
programmatore, comando firmware `'S'`, lato host, voce di menu, sidebar, titolo
finestra) e **firmware 0.1.5c** — è **chiuso e verificato su hardware**. Non ci
sono prove pendenti. Le cose aperte qui sotto sono precedenti a quel lavoro,
tranne i tre interruttori di build.

## Come lavoro

- **Parla italiano in chat, scrivi in inglese nel repo** — commit, documentazione,
  commenti.
- **Risposte concise.** Per modifiche non banali: prima il piano, poi esegui dopo
  il mio ok.
- **Misura invece di dedurre.** Se un tuo risultato precedente si rivela
  sbagliato, dillo esplicitamente con i numeri.
- ⚠️ **Una funzione con un ripiego che produce lo stesso esito corretto va
  strumentata, o non è verificabile.** Il comando `'Q'` è rimasto codice morto
  per quattro sessioni di banco perché il drain rimediava da solo: la prova
  passava comunque. Se aggiungi qualcosa che ha una via di riserva, aggiungi
  anche l'osservabile che distingue le due strade — e che sia un **numero**, non
  un "ha funzionato": lì il numero era 7172 byte identici al byte, ed è l'unica
  cosa che ha tradito il buco.
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
  l'asse verticale di frequenza e dissipazione sarà sistemato.

### Il resto

- **Prove di banco del numero identificativo: finite.** Tutti e sette gli scenari
  girati su hardware il 2026-09-01, tabella in `HANDOFF.md` §3 *Bench
  verification*. Non c'è niente da rifare, e rifarli costa un downgrade di
  firmware e una cancellazione di EEPROM a testa.
  ⚠️ **Due esiti sembrano guasti e non lo sono**, così non si riaprono: la riga
  `Board number response: '' (raw '')` che compare **due volte** su una scheda
  `0.1.5a` sono l'interrogazione alla connessione e il controllo manuale dal
  menu, a 2,24 s di distanza — per questo la riga porta `[auto]` o `[menu]`; e la
  riga del drain **assente** è l'esito migliore, non uno mancante, perché si
  stampa solo se ha buttato via qualcosa.
  ⚠️ **`'Q'` non accorcia niente dopo uno Stop, ed è misurato**: 414 ms di drain
  di cui 268 di sola finestra di silenzio, i 7172 byte usciti in ~146 ms, cioè
  già in buffer. Non è colpa del firmware — è la sequenza: il genitore riprende
  la porta solo dopo che il figlio l'ha rilasciata, e il figlio la rilascia a
  sweep concluso, quindi la lettera trova sempre una scheda ferma. Un `'Q'`
  tempestivo dovrebbe partire dal figlio e varrebbe quei ~146 ms. **Il meccanismo
  vero è il drain**, e `'Q'` resta solo perché è la primitiva giusta e costa una
  scrittura. Se qualcuno si chiede perché sembra non fare niente, la risposta è
  qui e non è "il firmware lo ignora".
  ⚠️ **Scheda occupata oltre i 6 s** (*The board is still sending measurement
  data*) non si forza al banco: il tetto è 6 s contro uno sweep di ~1.8 s. È
  verificato in simulazione. Se un giorno compare davvero, la scheda è appesa.
- ⚠️ **Firmware: tre coppie in `firmware/`.** La corrente è **`0.1.5c`** (`'S'` e
  `'Q'`); `0.1.5b` e `0.1.5a` sono superate e **vanno cancellate** quando nessuna
  scheda le monta più. La variante `-TEST` senza TEC resta finché la scheda
  prototipo è in uso.
- ⚠️ **`firmware_update/` spedisce l'immagine `0.1.5`**, due versioni indietro.
- ⚠️ **Sidebar tagliata**: il contenuto chiede **435 px**, il pannello ne concede
  260 al minimo e 400 al massimo. La scroll area è `widgetResizable` con la barra
  orizzontale spenta, quindi non scorre: **taglia**. Difetto preesistente.
- **Larghezza dei pill delle armoniche**: tentata **due volte** e revertita due
  volte. Quello che si è imparato sta in `HANDOFF.md`, "The overtone chips, and
  why they still stretch", inclusa la variante mai provata: chip impaccati a
  sinistra con **un solo spaziatore in coda**.
- **`plot_color_multi_g`** (solo ramo): palette esadecimale dei grafici di
  conduttanza, copia di una lista blu più vecchia, mai allineata alle due rampe.
- Copia benigna di `savitzky_golay` in `sweep_data/plot_conductance.py` (ramo).
- `polyfit` in tre copie: `Multiscan.baseline_correction`,
  `Serial.baseline_correction`, `Calibration.baseline_estimation`.
- Zeri spinti ai grafici durante il warm-up del Multiscan.
- Due classi `DateAxis` in `constants.py`, la seconda oscura la prima.

## Una differenza fra i rami che è voluta

**N-SCALE** divide per l'ordine armonico: su `main` solo la frequenza, su
`impedance-analysis` **anche la dissipazione**. È specificato, non è deriva, e
**non va riconciliato** con un cherry-pick in nessuna delle due direzioni. La
suite di verifica legge dall'ambiente quale contratto sta controllando.
