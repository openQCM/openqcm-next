<!-- DONE 2026-09-11: the question this prompt asks is answered in
     research/air-ipa-water-1920-2026-09-11/fs-estimators-liquid.md. The next session starts from
     SESSION_PROMPT_liquid_frequency_excess.md in this directory. -->
<!--
Kept in Italian on purpose, like docs/SESSION_PROMPT.md: it is the literal text to
paste as the first message of a dedicated session. Branch-only, research task.
Written 2026-09-11; results go into research/air-ipa-water-1920-2026-09-10/.
-->

# openQCM NEXT — sessione dedicata: stimatore di f_s sugli sweep in liquido

Incolla tutto quello che segue come primo messaggio della chat nuova, aprendola
nella cartella `/Users/marco/claude_code/openqcm-next-impedance` (ramo
`impedance-analysis`).

---

Lavoriamo su **openQCM NEXT**, ramo `impedance-analysis`, worktree
`/Users/marco/claude_code/openqcm-next-impedance`. Sessione **di sola analisi**:
nessuna modifica al codice che va in produzione senza il mio ok esplicito.

## Come lavoro

Valgono le regole di `docs/SESSION_PROMPT.md` (leggile): italiano in chat, inglese
nel repo; risposte concise; piano prima di ogni cosa non banale, esegui dopo il
mio ok; una modifica alla volta; **misura invece di dedurre** e, se un risultato
precedente si rivela sbagliato, dillo con i numeri; artifact come markdown con le
figure incorporate; dopo ogni commit+push allinea `HANDOFF.md` e `CHANGELOG.md`.
Push con:
`GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=credential.https://github.com.helper GIT_CONFIG_VALUE_0='!gh auth git-credential' git push origin impedance-analysis`.
Mai `git add -A`; `config.txt` è tracciato e modificato dal banco: non committarlo.
Copia i dati grezzi **fuori dal repo** prima di analizzarli. Prima di versionare un
dataset chiedimi le condizioni di acquisizione.

## Il problema

Il datalog del ramo pubblica come frequenza il **massimo campionato della
conduttanza esatta G** (`argmax`). Nella prima corsa aria → isopropanolo → acqua
(scheda 1920, 2026-09-10) la ΔΓ ricavata da D = 2Γ/f concorda con Kanazawa–Gordon
entro ±8 % sulle armoniche 3–9, mentre |Δf| **sovrastima del 22–31 %**
(|Δf|/ΔΓ = 1.2–1.35 dove un liquido newtoniano dà 1.0). In aria, sulla stessa G,
il punto medio degli attraversamenti a metà altezza e il fit lorentziano cadono
entrambi **0.25–0.33 Γ sotto** l'`argmax`: il picco è asimmetrico con la coda a
destra. Scalato alla Γ in liquido sono 200–600 Hz, l'ordine della sovrastima.
Ipotesi coerente, **non ancora confermata**: mancavano gli sweep in liquido.

Leggi prima, in quest'ordine:
1. `research/air-ipa-water-1920-2026-09-10/README.md` (tabelle KG e addendum
   sugli stimatori) e `scripts/fs_estimators.py`, `scripts/kanazawa_gordon.py`.
2. `docs/impedance-analysis/datalog-quantities-2026-09-10.md` (che cosa registra
   ogni colonna, catena esatta riprodotta offline).
3. `HANDOFF.md` §4 (ramo impedenza) per la catena V_MAG/V_PHS → G e il dump.

Candidati tutti aperti, nessuno escluso a priori: `argmax`, punto medio a metà
altezza, fit lorentziano, **e anche il fit del cerchio BVD** (`_fit_circle_taubin`
nel pannello live, il fit di `fit_admittance.py` offline). Il parametro `gamma` di
`sweep_data/fit_admittance.py::fit2_lorentzian` è la larghezza **intera** a metà
altezza (2Γ), non la semilarghezza.

## I dati che ti porto

Dump degli sweep (`OPENQCM_SWEEP_DUMP=1`, ultimo sweep per armonica, riscritto a
ogni sweep; file `g<n>.txt` = V_MAG/V_PHS grezzi in volt, `<n>.txt` = dB/gradi),
copiati **a mano durante un'unica acquisizione**, sul plateau di ogni liquido:
`~/Desktop/dump_liquidi/{aria,acqua,ipa}/`, con l'orario di ogni copia. Più i due datalog della giornata da
`software/logged_data` (`<ts>_multi.csv` e `<ts>_multi_amplitude.csv`) per i
plateau e la temperatura. Ti dirò io le condizioni (temperatura, scheda, sensore).

## Il lavoro

1. Sugli sweep in liquido calcola, sulla **stessa G esatta** e con le funzioni dei
   processi (non riscriverle), i quattro stimatori: `argmax`, punto medio a metà
   altezza, fit lorentziano su ±3Γ, fit del cerchio BVD. Stessa tabella dell'addendum, per aria, acqua e
   isopropanolo.
2. Per ciascun stimatore Δf rispetto all'aria della stessa sessione, ΔΓ, e il
   rapporto **|Δf|/ΔΓ** per armonica, confrontato con Kanazawa–Gordon a 25 °C
   (usa `scripts/kanazawa_gordon.py`). La domanda è una: **quale stimatore porta
   |Δf|/ΔΓ verso 1 sulle armoniche 3–9**, e di quanto resta lontano.
3. Verifica anche la stabilità: ripetibilità degli stimatori sui plateau del
   datalog non è misurabile dal dump (uno sweep per liquido) — dillo, e proponi
   come misurarla se serve.
4. Risultati come `research/air-ipa-water-1920-2026-09-10/fs-estimators-liquid.md`
   con figure incorporate (G con i tre marcatori per armonica, |Δf|/ΔΓ vs n per
   stimatore); dati grezzi in `data/`, script in `scripts/`. Commit, push,
   HANDOFF/CHANGELOG.

Qualunque cambio allo **stimatore pubblicato** nel datalog viene dopo questa
misura e dopo il mio ok: non anticiparlo.

Riportami prima in breve lo stato letto dai file, poi aspetta i dati.
