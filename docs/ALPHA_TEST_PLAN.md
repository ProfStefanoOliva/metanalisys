# Alpha Test Plan

## Finalità

Questo piano definisce come raccogliere contributi di alpha testing per `metanalisys` in modo prudente, riproducibile e coerente con la natura sperimentale del progetto.

## Chi può contribuire come tester

Possono contribuire come tester:

- sviluppatori Python;
- tecnici di digital forensics;
- revisori di qualita software;
- utenti tecnici interessati alla robustezza del parsing Office;
- manutentori o collaboratori open source.

I contributi sono particolarmente utili quando includono osservazioni riproducibili e limiti tecnici chiaramente descritti.

## Quali tipi di file usare

Per l'alpha testing usare solo:

- file temporanei creati localmente;
- campioni sintetici minimali;
- pacchetti OOXML generati in modo controllato;
- file non sensibili espressamente preparati per test.

Possono essere utili campioni che simulano:

- metadati base in `core.xml`;
- macro placeholder controllate;
- relationships con path sintetici;
- immagini incorporate sintetiche;
- archivi corrotti creati intenzionalmente per test di errore.

## Divieto di inviare file reali, sensibili o provenienti da casi concreti

Non devono essere inviati, caricati o allegati:

- file Office reali;
- documenti operativi o aziendali;
- evidenze digitali;
- file contenenti dati personali;
- campioni provenienti da casi concreti o da attivita investigative reali.

Per issue pubbliche, pull request e discussioni aperte usare solo campioni sintetici o descrizioni testuali sufficienti a riprodurre il problema.

## Come segnalare bug

Le segnalazioni dovrebbero essere formulate in modo riproducibile e tecnico. E utile indicare:

- comportamento atteso;
- comportamento osservato;
- passaggi per riprodurre il problema;
- eventuali messaggi di errore;
- impatto pratico del problema sul caso di test.

Quando possibile, allegare solo script, snippet o descrizioni che permettano di rigenerare un campione sintetico equivalente.

## Informazioni da includere in una segnalazione

Ogni segnalazione tecnica dovrebbe includere almeno:

- sistema operativo;
- versione Python;
- comando usato;
- formato del file testato;
- origine sintetica del campione;
- output ottenuto;
- output atteso;
- eventuali warning o stack trace.

## Come indicare contesto operativo minimo

Per favorire la riproducibilità, è consigliato usare una traccia come questa:

- OS: `Windows 11` / `Ubuntu 24.04`
- Python: `3.11.x`
- Comando: `python .\src\metanalisys.py <campione>`
- Formato file: `.docx` / `.xlsx` / `.pptx` / altro
- Tipo campione: sintetico ZIP OOXML / file temporaneo / placeholder legacy
- Output ottenuto: breve estratto o descrizione
- Output atteso: breve estratto o descrizione

## Protezione dei dati personali

Prima di aprire una issue o condividere materiale:

- rimuovere ogni dato personale;
- evitare nomi reali, percorsi reali e identificativi reali;
- usare nomi fittizi e metadati sintetici;
- non copiare contenuti da documenti reali.

Se un problema emerge durante test privati su dati non condivisibili, è preferibile creare un campione sintetico equivalente che riproduca il comportamento osservato senza esporre dati sensibili.

## Come proporre campioni sintetici

Un buon campione sintetico dovrebbe:

- essere il più piccolo possibile;
- avere ground truth chiara;
- essere costruito con metadati intenzionali e documentati;
- essere facilmente rigenerabile;
- non contenere dati personali o contenuti protetti.

Quando si propone un campione sintetico, è utile descrivere:

- come è stato generato;
- quali metadati o strutture interne contiene;
- quale comportamento del software intende esercitare;
- quale esito ci si aspetta.

## Nota finale

L'alpha testing serve a migliorare il software e a documentarne limiti e comportamenti osservati. Non sostituisce procedure autorizzate, analisi professionali o valutazioni forensi operative su casi reali.
