# openQCM NEXT - progetto A4 su un solo foglio

Aprire `openQCM_NEXT_A4.kicad_pro` in KiCad 10 e quindi lo schematico omonimo. Questo progetto e indipendente dalla versione a sei fogli nella cartella `../kicad`.

Il foglio e A4 orizzontale, 297 x 210 mm, con tre colonne e sei blocchi funzionali: alimentazioni, DDS/filtro RF, pilotaggio QCM, rivelazione/uscite, Teensy/interfacce, controllo TEC. I simboli compatti e le etichette locali consentono di mantenere tutti i componenti su un solo foglio; le etichette con lo stesso nome rappresentano la stessa rete. I percorsi analogici principali sono disegnati con fili continui.

La libreria `openQCM.kicad_sym`, la tabella `sym-lib-table` e la cornice `A4_compact.kicad_wks` sono incluse nel progetto. Conservare insieme questi file. I simboli sono anche incorporati nello schematico.

## Verifiche

KiCad 10.0.6 ha esportato la netlist, confrontata con quella strutturata contenuta nel PDF originale:

- 85 componenti, tutti con i valori originali;
- 312 pin e 94 reti identici per collegamenti;
- nessuna rete mancante o aggiunta;
- ERC: zero errori e un avviso per `3V3_TEENSY`, collegata soltanto a P2-3 anche nell'originale.

Il rapporto e in `../verification/A4/netlist-check.json`; il PDF a pagina singola e in `../output/pdf/openQCM_NEXT_A4.pdf`. Stampare in A4 orizzontale al 100%. La versione multipagina conserva testi piu grandi per la consultazione dettagliata.

## Limiti ereditati dalla ricostruzione

I pin dei simboli sono dichiarati passivi, poiche il PDF non conteneva i tipi elettrici originali. L'ERC non sostituisce una verifica dei driver e dei livelli di alimentazione rispetto ai datasheet. I footprint originali sono conservati nel campo `Source_Footprint`, mentre il campo `Footprint` KiCad e vuoto. Rimane la nota originale sul footprint di U6: "FOOTPRINT SBAGLIATO - SOT 363".

`../scripts/build_a4.py` rigenera esclusivamente questo progetto; sovrascrive i suoi file generati. Non usarlo dopo modifiche manuali senza salvarne una copia.
