<!--
Italian on purpose, like docs/SESSION_PROMPT.md: this is the literal text to paste as the first message
of the session that takes over the liquid-frequency question after the 2026-09-11 measurements.
Everything it points at is in English. Written 2026-09-11, after commits 9e2a480, dfbb6fe, 3006d7e.
The previous prompt of this series, SESSION_PROMPT_fs_estimators.md, is done: its question is answered.
-->

# openQCM NEXT — prompt per la sessione che prende in carico l'eccesso di frequenza in liquido

Incolla tutto quello che segue come primo messaggio di una chat nuova aperta in
`/Users/marco/claude_code/openqcm-next`.

---

Lavoriamo su **openQCM NEXT**, ramo `impedance-analysis`, worktree
`/Users/marco/claude_code/openqcm-next-impedance`. Sessione di **sola analisi**: nessuna modifica al codice
che va in produzione senza il mio ok esplicito, e lo stimatore pubblicato nel datalog (`argmax` della
conduttanza esatta G) **resta quello** finché non decido io.

## Come lavoro

Valgono le regole di `docs/SESSION_PROMPT.md`, leggile: italiano in chat, inglese nel repo; risposte concise;
piano prima di ogni cosa non banale ed esecuzione dopo il mio ok; una modifica alla volta; **misura invece di
dedurre**, e se un risultato precedente si rivela sbagliato dillo con i numeri (è successo il 2026-09-11:
l'estrapolazione dell'asimmetria di G dall'aria al liquido era sbagliata di un fattore 3–8, ed è stata
corretta in loco). Gli artifact sono **file markdown con le figure incorporate**. Dopo ogni commit+push
allinea `HANDOFF.md` e `CHANGELOG.md` **sul ramo** (niente cherry-pick di documentazione). Push con:
`GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=credential.https://github.com.helper GIT_CONFIG_VALUE_0='!gh auth git-credential' git push origin impedance-analysis`.
Mai `git add -A`; `config.txt` è tracciato e modificato dal banco: non committarlo. Prima di versionare un
dataset chiedimi le condizioni di acquisizione.

Su un dataset nuovo voglio **prima** un documento che analizzi i dati così come sono stati acquisiti, solo
numeri e figure, senza interpretazioni; le ipotesi vengono dopo, **una per pagina**, e le giudico io dalle
figure. Riportami in breve lo stato letto dai file e poi **aspetta che ti dica io su cosa lavoriamo**: la
sezione "Cose aperte" qui sotto è un inventario, non una coda di lavoro.

## Leggi prima, in quest'ordine

1. `research/air-ipa-water-1920-2026-09-11/README.md` — il datalog del 2026-09-11 così com'è, contro
   Kanazawa–Gordon.
2. `research/air-ipa-water-1920-2026-09-11/raw-sweeps.md`, `fold-hypothesis.md`, `fs-estimators-liquid.md`
   — gli sweep grezzi, le tre regole di unfold della fase, i quattro stimatori di f_s con il verdetto.
3. `research/air-ipa-water-1920-2026-09-10/README.md` — la prima corsa e la correzione datata in fondo.
4. `HANDOFF.md` §4 (ramo impedenza: catena V_MAG/V_PHS → G, offset δ, decisione di fold, OSL parcheggiata e
   perché) e la voce 2026-09-11 in `CHANGELOG.md` `## [Unreleased]`.
5. `docs/impedance-analysis/ALGORITHM.md` se devi toccare la catena; `software/docs/DATA_FORMAT_sweep_data.md`
   prima di leggere un file grezzo (due convenzioni di scala, compensare due volte l'attenuatore è già successo).

## Dove sono i dati

- Datalog dei due giorni: `research/air-ipa-water-1920-2026-09-1{0,1}/data/` (impedenza e ampiezza, stesse
  righe).
- Dump degli sweep del 2026-09-11: **nel repo** come archivio compresso
  `research/air-ipa-water-1920-2026-09-11/data/sweep_dumps_2026-09-11.npz` (7.8 MB, i 45 `g<n>.txt`, orari di
  copia inclusi); `python scripts/load_dumps.py unpack <npz> <cartella>` ricrea le cartelle che gli script
  leggono. Gli originali sono in `~/Documents/openqcm-next-data_20260911/` — nove
  cartelle `air_{0,1,2}`, `wat_{0,1,2}`, `ipa_{0,1,2}`, ognuna con `g<n>.txt` (V_MAG/V_PHS in volt, attenuatore
  già tolto) e `<n>.txt` (dB/gradi, non compensato); orari delle copie nel README. Scheda 1920 (in specifica,
  125 MHz), stesso sensore 5 MHz del 2026-09-10, TEC 25 °C, aria → acqua → isopropanolo.
- Script: `research/air-ipa-water-1920-2026-09-11/scripts/`. Quelli che usano il processo si lanciano da
  `software/`: `cd software && PYTHONPATH=. python ../research/.../scripts/<nome>.py <cartella dati> <uscita>`
  (`MultiscanProcess` legge `openQCM/config.txt` con path relativo). `fit_admittance.py` si carica per path
  con `importlib`.

## Stato misurato (2026-09-10 e 2026-09-11, due corse, stesso sensore)

- **ΔΓ da D = 2Γ/f segue Kanazawa–Gordon entro ±8 % su n = 3–9**, in acqua e isopropanolo, entrambi i giorni.
- **|Δf| supera la teoria del 17–29 % su n = 3–9** (Δf/Δf_KG = 1.17–1.34); |Δf|/ΔΓ = 1.16–1.34 dove un liquido
  newtoniano dà 1.0. Pendenze in √n: −Δf 819 e 1108 Hz/√n contro 674 e 902 di teoria; ΔΓ 656 e 867.
- **Sul fondamentale è il contrario**: ΔΓ 29–35 % sopra la teoria, |Δf|/ΔΓ = 0.85–0.89; in aria D₁ = 26 ppm
  contro 9–10 sugli overtone.
- **Non è lo stimatore.** argmax, punto medio a metà altezza, lorentziana danno tutti 1.14–1.53; il cerchio BVD
  arriva a 1.0–1.14 solo con una rotazione libera θ = −25…−31° (uguale in aria) e si sovrappone male al
  luogo (5–18 % del raggio): giudicato debole. L'asimmetria di G in liquido è 0.02–0.10 Γ.
- **Non è la fase, per quanto si è potuto provare.** In liquido su n ≥ 3 la lettura non arriva a zero (minimo
  9–45°) e il minimo è liscio, non un fold: il ramo "no fold" è fisicamente giusto (attraversamento solo se
  R1 < 1/(2ωC0); R1 in acqua 0.7–3.3 kΩ contro soglie 4.8→0.54 kΩ). Invertire sempre il segno spezza il luogo
  in due archi e non tocca G; forzare il minimo a 0° peggiora il rapporto (1.2–1.9); l'offset misurato in
  aria (+4…+6°) applicato in liquido sposta il rapporto di −0.02…−0.05. Un offset costante è una mappa di
  Möbius: non può cambiare la rotondità del luogo.
- **G non è una lorentziana su questo strumento**, né in aria né in liquido: stesso residuo a S, 2–7 % di Gmax,
  in tutti i pannelli, sulle tre repliche.
- **Ripetibilità** su tre sweep per plateau: f 1–37 Hz, Γ 1–8 Hz, contro spostamenti di 1.4–3.4 kHz. Sufficiente.

## Cose aperte (inventario, non piano)

- **L'eccesso di |Δf| sugli overtone**, 20–30 %, con ΔΓ giusta. Non viene dallo stimatore né dalla catena di
  fase. Ipotesi **non verificate**, elencate perché qualcuno le proverà: (a) fisica della superficie —
  Kanazawa–Gordon assume superficie liscia, rugosità o liquido intrappolato aggiungono −Δf con poca ΔΓ, e la
  firma sarebbe proprio questa; si discrimina con un **secondo sensore** e con un liquido a viscosità diversa;
  (b) il luogo fuori tondo, 5–18 %, e il residuo a S di G — un errore di scheda che deforma G in modo
  asimmetrico sposterebbe l'argmax; l'OSL con tre standard **non** lo corregge (dimostrato, HANDOFF §4), serve un
  quarto standard dentro il range; (c) la finestra di sweep −12/+6 kHz tagliata a destra in isopropanolo su
  n ≥ 5 e la baseline presa sulla spalla della risonanza (HANDOFF §4, roadmap punto 6).
- **La soglia di fold 0.88** cade esattamente sul 3° overtone in acqua: il datalog è bistabile (105 Hz, 7.7 ppm)
  e il latch su due sweep lo blocca in uno dei due stati. Cambiarla, o sostituirla con il criterio
  R1 < 1/(2ωC0), tocca i valori pubblicati: decisione mia.
- **D in aria raddoppiata** fra il 10 e l'11 sullo stesso sensore (19→26, 5→10 ppm), f in aria 49–235 Hz più
  bassa: registrato, non spiegato. Sensore da controllare, o secondo sensore.
- **Righe duplicate nel datalog**: 95 su 486 (34 su 175 il giorno prima), scritte a raffica nello stesso
  secondo; abbassano ogni deviazione standard. Da trovare nel worker prima della prossima analisi di
  ripetibilità.
- **La rotazione θ del cerchio**, −25…−31° su n ≥ 5 in aria e in liquido: è una proprietà dello strumento,
  imparentata con il φ_b = −12…−20° del 2026-07-28 (HANDOFF §4). Nessuno sa ancora dove sta nel circuito.

## Cosa non rifare

- Non riproporre "fold sempre al massimo di V_PHS" né "minimo sempre a 0°": misurati, in `fold-hypothesis.md`.
- Non riproporre l'OSL come cura della rotondità: dimostrato invariante (Möbius), HANDOFF §4.
- Non cambiare lo stimatore pubblicato, la soglia di fold o la finestra di sweep senza il mio ok.
- Non versionare corse fatte fuori specifica (scheda a 150 MHz a 3.3 V): sono diagnostica.
