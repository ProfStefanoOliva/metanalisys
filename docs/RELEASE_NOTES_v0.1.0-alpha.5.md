# Release notes `v0.1.0-alpha.5`

## Sintesi

`v0.1.0-alpha.5` introduce un report HTML standalone per l'analisi riepilogativa di cartella Office in `metanalisys`.

La release amplia la leggibilità del flusso cumulativo già disponibile da CLI, mantenendo gli output tecnici esistenti e senza modificare la GUI. L'obiettivo resta prudente: supportare il triage documentale tecnico con formati complementari, senza attribuire al report valore forense conclusivo o probatorio autonomo.

## Novità principali

- generazione di un report HTML standalone per l'analisi riepilogativa di cartella;
- CSS interno, senza dipendenze esterne o JavaScript obbligatorio;
- impianto grafico sobrio e coerente con il progetto;
- box riepilogativi per totale file, `OK`, `LIMITED` ed `ERROR`;
- tabella principale con nome file, famiglia Office, creatore, date, `risk score`, livello e `status`;
- badge colorati per `risk level` e `status`;
- sezione `ERRORI DI ANALISI`;
- sezione `DETTAGLIO REPORT PER SINGOLO FILE` basata su elementi HTML nativi `details` e `summary`;
- riuso del report testuale già esistente nei dettagli, tramite blocchi `pre` escaped;
- aggiornamento della CLI: in analisi cartella vengono ora generati `TXT`, `CSV`, `JSON` e `HTML`;
- aggiornamento dei test automatici;
- aggiunta di `manual_test_folder/README.md` e regole `.gitignore` per evitare il caricamento accidentale di file personali e report generati.

## Report HTML riepilogativo

Il report HTML è pensato per una consultazione più leggibile rispetto al report `TXT`, soprattutto quando il numero di file analizzati cresce o quando il riepilogo cumulativo contiene più sezioni di dettaglio.

Il formato `CSV` resta utile per elaborazioni tabellari, ordinamenti, confronti e aperture in strumenti come Excel o LibreOffice. Il formato `JSON` resta utile per uso tecnico o strutturato, ad esempio in verifiche interne, parsing o integrazioni future.

L'output `HTML` non sostituisce gli altri formati: li affianca. In questa release il progetto continua quindi a produrre più rappresentazioni dello stesso contenuto, con finalità diverse ma complementari.

## Output generati

Quando la CLI analizza una cartella, `metanalisys` genera:

- `TXT` riepilogativo cumulativo;
- `CSV` tabellare;
- `JSON` strutturato;
- `HTML` standalone per consultazione leggibile.

Il report HTML include:

- titolo `OFFICE FOLDER FORENSIC SUMMARY`;
- cartella analizzata;
- data e ora di generazione;
- box riepilogativi;
- tabella principale con badge per livello e stato;
- sezione errori, quando necessaria;
- dettaglio dei singoli file in pannelli espandibili.

## Sicurezza dei dati locali

La cartella `manual_test_folder` è solo una cartella locale di appoggio per verifiche manuali controllate. Non deve essere usata per archiviare nel repository file Office reali, file personali, evidenze digitali o dati sensibili.

Nel repository non devono essere caricati:

- file Office reali;
- file personali;
- evidenze digitali;
- dati sensibili o dati particolari.

I report generati con pattern `*_folder_summary.*` sono ignorati da Git tramite `.gitignore`, insieme al contenuto locale di `manual_test_folder` salvo il relativo `README.md`.

## Compatibilità

- il comportamento sul singolo file resta invariato;
- la funzione di cartella continua a generare `TXT`, `CSV` e `JSON`;
- in questa release viene aggiunto anche `HTML`;
- la GUI non è stata modificata.

## Limiti

- il report HTML è standalone e non usa JavaScript;
- i dettagli espandibili si basano su `details` e `summary` nativi del browser;
- il report HTML è un supporto tecnico di triage documentale;
- il `risk score` resta indice tecnico di anomalia documentale e non prova automatica di manomissione;
- l'analisi di cartella resta non ricorsiva.

## Verifica

- `py_compile`: `OK`
- `pytest`: `54` test passati nello stato corrente del repository
