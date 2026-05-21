# Risk Scoring

## Finalità

Il `risk score` di `metanalisys` è un indice tecnico di anomalia documentale utile come supporto alla revisione preliminare del file analizzato.

Il punteggio:

- non costituisce prova automatica di manomissione;
- non è conclusivo;
- non sostituisce una valutazione professionale;
- rappresenta un insieme di indicatori tecnici da sottoporre a verifica nel contesto della procedura autorizzata adottata.

## Soglie attuali

Le soglie del livello di rischio sono configurate in modo prudente per ridurre i falsi positivi su file Office innocui o di uso ordinario:

| Punteggio | Livello |
| --- | --- |
| 0-24 | BASSO |
| 25-59 | MEDIO |
| 60-99 | ALTO |
| 100 o più | CRITICO |

Un livello `ALTO` o `CRITICO` non equivale a certezza di alterazione del file. Indica invece la presenza di più elementi che possono meritare approfondimento tecnico e contestualizzazione.

## Dettaglio nel report

Il report testuale mostra, dopo la sezione `[RISK SCORE]`, una sezione `[DETTAGLIO ASSEGNAZIONE PUNTEGGIO]`.

Questa tabella riporta:

- l'ordine degli indicatori rilevati;
- il punteggio associato a ciascun indicatore;
- il progressivo cumulato del punteggio.

L'obiettivo è rendere più leggibile e verificabile la composizione del `risk score`, senza trasformarlo in un esito conclusivo.

## Criteri attualmente implementati

La seguente tabella descrive i criteri di punteggio attualmente presenti nel codice:

| Criterio | Punteggio | Nota prudente |
| --- | ---: | --- |
| autori multipli rilevati | +10 | indicatore debole, frequente in collaborazione o uso di account diversi |
| percorsi utente multipli rilevati | +15 | utile per provenienza e attribuzione, ma non conclusivo |
| software multipli rilevati | +15 | possibile conversione o modifica legittima tra suite diverse |
| file incorporati rilevati | +15 | elemento da verificare, non automaticamente anomalo |
| immagini modificate con software differenti | +15 | anomalia documentale da approfondire, non conclusiva |
| macro VBA rilevate in formato macro-enabled | +15 | presenza attesa dal formato, ma comunque da evidenziare |
| macro VBA rilevate in formato non macro-enabled | +60 | anomalia strutturale più forte rispetto all'estensione dichiarata |
| incongruenza cronologica OOXML: data modifica precedente alla data creazione | +40 | elemento tecnico significativo se le date sono parseabili |
| scostamento significativo tra data modifica OOXML e data modifica filesystem | +20 | indicatore debole o medio, da leggere con prudenza perché copie e trasferimenti possono modificare le date filesystem |

## Controlli temporali documentati

Il progetto applica due controlli temporali prudenziali quando le date sono disponibili e parseabili:

1. `created` e `modified` nei metadati OOXML.
   Se la data di modifica risulta precedente alla data di creazione, viene segnalata un'incongruenza cronologica OOXML.
2. `modified` nei metadati OOXML rispetto alla data di modifica del filesystem.
   Se lo scostamento assoluto supera 365 giorni, viene segnalato uno scostamento significativo da sottoporre a verifica.

Questi controlli:

- non devono essere letti come dimostrazione autonoma di alterazione;
- non producono indicatori se i valori non sono presenti o non sono parseabili;
- restano supporto alla revisione preliminare e non sostituiscono la valutazione professionale del contesto.

## Nota operativa

Il `risk score` deve essere letto come supporto tecnico alla revisione preliminare. Gli indicatori elencati possono segnalare anomalie documentali, trasformazioni, collaborazioni multiple o elementi da approfondire, ma non producono da soli una conclusione forense.
