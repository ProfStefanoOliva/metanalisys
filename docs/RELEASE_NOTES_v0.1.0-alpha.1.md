# Release notes `v0.1.0-alpha.1`

## Stato della release

Questa è una pre-release `alpha` di `metanalisys`. È destinata a valutazione tecnica, sperimentazione controllata e revisione del progetto in un contesto open source prudente.

## Scopo del software

`metanalisys` è un software Python per l'analisi tecnica dei metadati di file Microsoft Office. Il progetto produce report leggibili e strutturati come supporto tecnico a una analisi forense preliminare.

## Funzionalità principali

- analisi di file Microsoft Office moderni basati su Open XML;
- calcolo hash del file con `SHA-256` e `SHA-512`;
- raccolta di informazioni base del file system;
- estrazione di metadati Office quando supportata;
- generazione di report testuali e JSON;
- disponibilità di interfaccia CLI e GUI.

## Formati Office supportati

Supporto OOXML principale:

- Word: `.docx`, `.docm`, `.dotx`, `.dotm`
- Excel: `.xlsx`, `.xlsm`, `.xltx`, `.xltm`, `.xlam`
- PowerPoint: `.pptx`, `.pptm`, `.potx`, `.potm`, `.ppsx`, `.ppsm`
- Visio: `.vsdx`, `.vsdm`, `.vstx`, `.vstm`

Supporto legacy limitato:

- Word: `.doc`, `.dot`
- Excel: `.xls`, `.xlt`
- PowerPoint: `.ppt`, `.pot`, `.pps`

Per i formati legacy il supporto resta limitato e orientato soprattutto a hash, informazioni base del file e indicazioni di copertura ridotta.

## Hash SHA-256 e SHA-512

La release include il calcolo degli hash `SHA-256` e `SHA-512` in modalità streaming, con esposizione nel report testuale e nel report JSON.

## CLI e GUI

La release include:

- una versione a riga di comando in `src/metanalisys.py`
- una GUI basata su `customtkinter` in `src/metanalisysGUI.py`

Entrambe usano il core condiviso del progetto.

## Report testuale e JSON

Il software può produrre:

- report testuale leggibile;
- report JSON strutturato;
- sezioni dedicate a hash, informazioni file, metadati, indicatori tecnici e notice finale prudente.

## Documentazione forense prudente

La release include documentazione dedicata a:

- limiti forensi e di contesto;
- responsabilità dell'utilizzatore;
- profili legali e organizzativi;
- testing e validazione scientifica alpha;
- alpha testing e release readiness.

## Test automatici e CI

Il progetto include:

- suite automatica `pytest`;
- controllo `py_compile`;
- workflow GitHub Actions per eseguire i test su piattaforme supportate.

## Validazione alpha eseguibile con campioni sintetici

La release include una prima validazione scientifica alpha eseguibile con campioni sintetici generati a runtime.

Copertura attuale:

- `VAL-001` DOCX OOXML sintetico base;
- `VAL-002` XLSX OOXML sintetico base;
- `VAL-003` PPTX OOXML sintetico base;
- `VAL-004` DOCM/XLSM/PPTM con placeholder macro-enabled sintetici e innocui.

Non vengono usati file Office reali o macro reali. I casi coperti sono pensati per sperimentazione controllata e verifica tecnica riproducibile.

## Limiti noti

- stato alpha del progetto;
- copertura non esaustiva dei casi Office reali;
- supporto legacy limitato;
- copertura ancora parziale di file corrotti, cifrati o ostili;
- validazione eseguibile ancora parziale rispetto all'intera matrice metodologica;
- necessità di interpretazione professionale dei risultati.

## Avvertenza importante

Il software non sostituisce:

- autorizzazioni;
- catena di custodia;
- verbali;
- procedure operative;
- valutazione professionale del caso concreto.

L'uso del software resta sotto la responsabilità dell'utilizzatore e dovrebbe avvenire solo entro procedura autorizzata, lecita e documentata.

## Issue pubbliche e materiali sensibili

Nelle issue pubbliche non devono essere caricati:

- file Office reali;
- contenuti sensibili;
- dati personali;
- evidenze digitali;
- materiali provenienti da casi concreti.

Per segnalazioni e test usare solo campioni sintetici o descrizioni tecniche riproducibili.
