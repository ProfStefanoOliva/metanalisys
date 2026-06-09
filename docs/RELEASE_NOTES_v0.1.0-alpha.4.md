# Release notes `v0.1.0-alpha.4`

## Sintesi

`v0.1.0-alpha.4` introduce una funzione di analisi riepilogativa di cartella Office nella CLI di `metanalisys`.

La release estende il flusso di analisi già esistente per il singolo file con una modalità cumulativa orientata al triage documentale tecnico. L'obiettivo è facilitare una prima revisione ordinata di insiemi di file Office supportati, senza trasformare il risultato in una valutazione forense autonoma o probatoria.

## Novità principali

- analisi non ricorsiva di cartelle contenenti file Office supportati;
- selezione dei soli file con estensioni registrate nel core del progetto;
- ordinamento alfabetico case-insensitive dei file trovati;
- esecuzione dell'analisi file per file tramite il motore già esistente;
- gestione robusta degli errori per singolo file senza interrompere l'intera elaborazione;
- produzione di un riepilogo tabellare con `status` `OK`, `LIMITED` ed `ERROR`;
- esportazione dei risultati in `TXT`, `CSV` e `JSON`;
- aggiornamento dei test automatici per coprire il nuovo flusso CLI e il riepilogo di cartella.

## Analisi riepilogativa di cartella

Quando alla CLI viene passato il percorso di una cartella, `metanalisys`:

1. valida che il percorso esista e sia una cartella;
2. cerca nella cartella corrente solo i file Office supportati;
3. non analizza ricorsivamente le sottocartelle in questa release;
4. ordina i file alfabeticamente in modo case-insensitive;
5. analizza i file uno per uno con il motore già esistente;
6. costruisce una riga riepilogativa per ciascun file;
7. continua l'elaborazione anche se un singolo file genera errore.

La tabella iniziale del report cumulativo espone almeno:

- nome file;
- famiglia Office;
- creatore;
- data creazione;
- ultimo modificatore;
- data ultima modifica;
- `risk score`;
- livello;
- `status`.

Il campo `status` viene assegnato in modo prudente:

- `OK` per i formati con supporto pieno analizzati correttamente;
- `LIMITED` per i formati legacy riconosciuti ma con supporto limitato;
- `ERROR` per i file riconosciuti che non possono essere analizzati correttamente.

## Output generati

La modalità di analisi riepilogativa di cartella genera:

- `TXT` riepilogativo cumulativo, con tabella iniziale e dettaglio dei report dei singoli file analizzati;
- `CSV` tabellare apribile con Excel o LibreOffice;
- `JSON` strutturato per uso tecnico.

I nomi dei file di output seguono il pattern:

- `<nomecartella>_folder_summary.txt`
- `<nomecartella>_folder_summary.csv`
- `<nomecartella>_folder_summary.json`

## Compatibilità

- il comportamento della CLI su singolo file resta invariato;
- la GUI non è stata modificata in questa release;
- la nuova funzione è disponibile dalla CLI quando viene passato il percorso di una cartella.

## Limiti

- l'analisi di cartella non è ricorsiva;
- i formati legacy restano a supporto limitato;
- il report di cartella è un supporto tecnico di triage documentale;
- il `risk score` resta un indice tecnico di anomalia documentale e non prova automatica di manomissione;
- gli errori sui singoli file sono sintetizzati come `status ERROR`.

## Verifica

- `py_compile`: `OK`
- `pytest`: `52` test passati nello stato corrente del repository

