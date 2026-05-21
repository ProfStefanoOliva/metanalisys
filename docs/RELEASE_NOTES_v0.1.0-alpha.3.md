# Release notes v0.1.0-alpha.3

## Stato della release

`v0.1.0-alpha.3` è una pre-release `alpha` di `metanalisys`, orientata a rendere più leggibile e più prudente l'interpretazione del `risk score` nel report testuale e nella documentazione tecnica.

Questa versione non trasforma il punteggio in una conclusione forense automatica. Il `risk score` resta un supporto tecnico alla revisione preliminare del file analizzato.

## Novità principali

Questa versione:

- aggiunge nel report testuale la sezione `[DETTAGLIO ASSEGNAZIONE PUNTEGGIO]`;
- mostra la composizione progressiva del `risk score`, mantenendo l'ordine originale degli indicatori rilevati;
- ridefinisce il `risk score` come indice tecnico di anomalia documentale;
- riduce i pesi degli indicatori deboli per limitare i falsi positivi su file Office innocui o di uso ordinario;
- distingue tra macro rilevate in formati macro-enabled e macro rilevate in formati non macro-enabled;
- aggiunge controlli temporali sui metadati OOXML;
- introduce il livello `CRITICO`;
- aggiorna la documentazione [docs/RISK_SCORING.md](docs/RISK_SCORING.md);
- mantiene compatibili i campi JSON `suspicious_indicators` e `risk_score`.

## Dettaglio funzionale

Il report testuale ora espone in modo più trasparente il modo in cui viene composto il punteggio:

- numero progressivo dell'indicatore;
- testo dell'indicatore;
- punteggio assegnato;
- totale progressivo dopo ogni indicatore.

Il modello di scoring è stato reso più prudente:

- gli indicatori deboli o frequenti in contesti legittimi hanno ora un peso inferiore;
- la presenza di macro in un formato che normalmente le prevede viene distinta da una presenza di macro incoerente con l'estensione dichiarata;
- sono stati introdotti controlli cronologici tecnici sui metadati OOXML, utili come elementi da verificare e non come esiti conclusivi.

## Compatibilità

La release mantiene la compatibilità con i campi JSON già esposti:

- `suspicious_indicators`
- `risk_score`

Questo consente di preservare l'integrazione con eventuali flussi già basati sull'output strutturato del progetto.

## Limiti

- Il punteggio non prova automaticamente una manomissione.
- I livelli `ALTO` e `CRITICO` indicano necessità di approfondimento tecnico e contestualizzazione, non certezza sul significato del caso.
- Il confronto tra date OOXML e date filesystem è intenzionalmente prudente.
- Copie, trasferimenti e sincronizzazioni possono alterare le date del filesystem senza implicare, da sole, un'anomalia del contenuto documentale.

## Verifica

- `py_compile`: OK
- `pytest`: 40 passed
