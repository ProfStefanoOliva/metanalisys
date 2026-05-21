# Risk Scoring

## Finalità

Il `risk score` di `metanalisys` è un indice tecnico di anomalia o di attenzione utile come supporto alla revisione preliminare del file analizzato.

Il punteggio:

- non costituisce prova automatica di manomissione;
- non è conclusivo;
- non sostituisce una valutazione professionale;
- rappresenta un elemento da sottoporre a verifica nel contesto della procedura autorizzata adottata.

## Significato prudente del livello di rischio

Un livello `ALTO` non equivale a:

- colpevolezza;
- dolo;
- alterazione certa;
- conclusione definitiva sul significato forense del file.

Indica invece la presenza di più elementi tecnici che possono meritare approfondimento.

## Trasparenza del report

Il report testuale mostra ora, dopo la sezione `[RISK SCORE]`, una sezione `[DETTAGLIO ASSEGNAZIONE PUNTEGGIO]`.

Questa tabella riporta:

- l'ordine degli indicatori rilevati;
- il punteggio associato a ciascun indicatore;
- il progressivo cumulato del punteggio.

L'obiettivo è rendere più leggibile e verificabile la composizione del `risk score`, senza modificarne il comportamento di calcolo.

## Criteri attualmente implementati

La seguente tabella descrive i criteri di punteggio attualmente presenti nel codice:

| Criterio | Punteggio |
| --- | ---: |
| autori multipli rilevati | +30 |
| percorsi utente multipli rilevati | +25 |
| software multipli rilevati | +35 |
| file incorporati rilevati | +10 |
| immagini modificate con software differenti | +20 |
| macro VBA rilevate | +15 |

## Nota operativa

Il `risk score` deve essere letto come supporto tecnico alla revisione preliminare. Gli indicatori elencati possono segnalare anomalie, trasformazioni, collaborazioni multiple o elementi da approfondire, ma non producono da soli una conclusione forense.
