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

- **Prove di banco del numero identificativo.** Provato il 2026-09-01 sulla
  macchina con firmware `0.1.5c` e scheda 1900: **tutte le vie di ritorno in
  standby funzionano** — connesso e fermo, dopo una peak detection conclusa,
  dopo Start/Stop in singola, dopo Start/Stop in multiscan. La multiscan è il
  caso più severo: cinque sweep, quindi il peggiore per il drain e per `'Q'`.
  Provata anche la **strada di riserva** su scheda degradata a `0.1.5b-TEST`: lì
  `'Q'` non viene mandato — su un firmware che non lo conosce partirebbe una
  scansione da 0 Hz — e **il solo drain basta**, 7172 byte drenati, con risposta
  corretta in singola, in multiscan e dopo una peak detection.
  Provata poi la scheda degradata a **`0.1.5a-TEST`**, che `'S'` non lo conosce
  affatto: non risponde nulla e l'avviso dice *serve firmware più recente*, che è
  la sola cosa che deve dire. ⚠️ Non basta `0.1.5b` per questa prova: quello `'S'`
  lo conosce già.
  ⚠️ **Falso allarme già chiuso, da non riaprire.** In quel log la riga
  `Board number response: '' (raw '')` compare **due volte** dopo una sola
  connessione, e sembra un doppione. Non lo è: le due chiamate distano **2,24 s**
  e sono l'interrogazione automatica alla connessione e il controllo manuale da
  `Tools` che la procedura chiede subito dopo. Si somigliano solo perché una
  scheda `0.1.5a` non risponde a nessuna delle due. Da qui l'etichetta
  `[auto]`/`[menu]` accanto alla risposta, che è rimasta. `actionSerialNumber` è
  connessa **una volta sola**, non esiste nessun `trigger()` nel repository,
  l'azione non ha scorciatoia né `MenuRole` e la menu bar non è nativa: quella
  voce non può partire se non da un clic.
  Provata infine la **EEPROM azzerata** su `0.1.5c-TEST`: `NO_SERIAL` alla
  connessione e dal menu, sidebar `S/N not programmed`, titolo senza numero.
  Lo sketch usa-e-getta che azzera il magic byte **non sta nel repository** di
  proposito — uno strumento che cancella l'identità di una scheda non va lasciato
  in giro — e va riscritto ogni volta (venti righe, `EEPROM.write(0, 0x00)`, gli
  indirizzi sono in `HANDOFF.md`).
  ⚠️ **Resta da provare `'Q'`, e le prove fatte finora non contano.** Fino al
  2026-09-01 la scrittura di `'Q'` stava nel ramo `except` di
  `_reacquire_serial_lock`, quindi non è **mai** partita: quello che il banco ha
  misurato è sempre stato il drain. Il segnale che l'ha smascherata è nel log —
  `Drained 7172 bytes` su una scheda `0.1.5c-TEST`, lo stesso conteggio **al
  byte** di una `0.1.5b`, che è il firmware a cui `'Q'` è negato apposta.
  Rimesso sul percorso giusto e riprovato: la riga
  `Stop-sweep sent to firmware 0.1.5c-TEST` **compare**, quindi la lettera esce
  davvero dall'host — ma il drain resta **7172 byte, identico al byte**. Il poll
  nel firmware è al posto giusto e consuma solo la riga `'Q'`, quindi l'ipotesi in
  piedi non è più che `'Q'` venga ignorato: è che **quando arriva lo sweep è già
  finito** e quei 7172 byte siano arretrato già trasmesso, seduto nel buffer del
  sistema operativo, che nessuna lettera può richiamare indietro.
  **Misurato, e l'esito è il primo caso: 414 ms totali di cui 268 di sola
  finestra di silenzio.** I 7172 byte sono usciti in ~146 ms, sette giri di un
  loop che campiona ogni 20 ms: su USB CDC vuol dire che erano già nel buffer.
  Una scheda ancora in sweep avrebbe superato i 1500 ms.
  ⚠️ **Quindi `'Q'` non accorcia niente dopo uno Stop, e la colpa non è del
  firmware** — il poll è corretto e al posto giusto. È la sequenza: il genitore
  riprende la porta solo dopo che il figlio l'ha rilasciata, e il figlio la
  rilascia a sweep concluso, quindi `'Q'` trova sempre una scheda ferma. Un `'Q'`
  tempestivo dovrebbe partire **dal figlio**, e il suo intero premio sono quei
  ~146 ms: la finestra di silenzio da 250 ms è incondizionata e resta comunque.
  Non vale la ristrutturazione del percorso di Stop.
  `'Q'` resta — è la primitiva giusta, costa una scrittura, non fa danno — ma
  **il meccanismo che recupera davvero la porta è il drain**, ed è sempre stato
  lui. Questa prova è chiusa: quello che restava da verificare era la promessa,
  e la promessa era sbagliata.
  ⚠️ **Scheda occupata oltre i 6 s** (*The board is still sending measurement
  data*) non si forza al banco: il tetto è 6 s contro uno sweep di ~1.8 s. È
  verificato in simulazione. Se un giorno compare davvero, la scheda è appesa.
- ⚠️ **Firmware: tre coppie in `firmware/`.** La corrente è **`0.1.5c`** (`'S'` e
  `'Q'`); `0.1.5b` e `0.1.5a` sono superate e **vanno cancellate** quando nessuna
  scheda le monta più. La variante `-TEST` senza TEC resta finché la scheda
  prototipo è in uso.
- ⚠️ **`firmware_update/` spedisce l'immagine `0.1.5`**, due versioni indietro:
  chi usa l'updater incluso finisce su un firmware che il software gli chiede
  subito di aggiornare.
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
