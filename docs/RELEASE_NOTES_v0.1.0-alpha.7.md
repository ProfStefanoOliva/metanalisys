# Release Notes - v0.1.0-alpha.7

## Sintesi

La versione `v0.1.0-alpha.7` introduce una rilevante evoluzione della GUI di `metanalisys`, orientata a una consultazione piu leggibile e navigabile dei risultati. L'interfaccia non e piu centrata esclusivamente sul report testuale, ma su una dashboard applicativa con sidebar laterale, area centrale dinamica e navigazione contestuale dei file analizzati.

L'aggiornamento non modifica il core di analisi, lo scoring, la CLI o i formati di output. Il report tecnico completo resta disponibile e continua a rappresentare il riferimento testuale piu esteso dell'analisi corrente.

## Novita principali

- nuova GUI con layout a dashboard e sidebar laterale navigabile;
- schermata iniziale piu chiara, senza textbox vuota come vista predefinita;
- area centrale scrollabile e sidebar scrollabile indipendente;
- status bar fissa con messaggi operativi e supporto hover per filename lunghi;
- dashboard dedicata per analisi singolo file;
- dashboard dedicata per analisi cartella con tabella centrale dei file analizzati;
- navigazione dei file analizzati dalla sidebar e dalla tabella;
- dettaglio contestuale del file selezionato con accesso a metadati, hash, risk score, indicatori e report file;
- nuovo modulo [src/metanalisys_gui_helpers.py](../src/metanalisys_gui_helpers.py) per logica non grafica e testabile;
- aggiornamento dei test GUI non fragili.

## Nuova dashboard GUI

La GUI non e piu costruita come semplice contenitore di un report testuale principale. La dashboard diventa il punto principale di consultazione e organizza in viste distinte:

- schermata iniziale;
- dashboard del file;
- dashboard della cartella;
- report tecnico;
- dettaglio contestuale del file selezionato;
- viste di supporto per metadati, hash, risk score e indicatori.

Il report tecnico completo resta comunque disponibile e consultabile in modo esplicito dalla navigazione laterale.

## Sidebar navigabile

La sidebar usa voci iconiche testuali/emoji e consente accesso rapido a:

- azioni principali;
- dashboard dell'analisi corrente;
- report tecnico;
- elenco dei file analizzati dopo analisi cartella;
- viste contestuali del file selezionato.

Dopo un'analisi cartella, la sezione `FILE ANALIZZATI` mostra i file rilevati. Se l'utente seleziona un file, sotto quel file compaiono direttamente le voci di dettaglio contestuali, con struttura simile a un albero di navigazione.

## Analisi singolo file

Il comportamento di analisi resta coerente con le versioni precedenti: il file viene analizzato con lo stesso core e lo stesso scoring. Cambia la presentazione, che ora usa una dashboard piu leggibile.

Per il file singolo analizzato risultano accessibili dalla sidebar:

- `🧬 Metadati`
- `🔐 Hash`
- `⚠️ Risk score`
- `📋 Indicatori`
- `🧾 Report file`

## Analisi cartella

La dashboard cartella mostra:

- riepilogo sintetico dell'analisi;
- conteggi principali;
- tabella centrale dei file analizzati;
- report tecnico cumulativo dell'analisi corrente.

La sidebar mostra l'elenco dei file analizzati. Il click su file in sidebar o il doppio click su una riga della tabella apre il dettaglio del singolo file, mantenendo disponibile il report tecnico cumulativo della cartella.

## Dettaglio file selezionato

Le viste `Metadati`, `Hash`, `Risk score`, `Indicatori` e `Report file` sono contestuali al file selezionato.

In particolare:

- in analisi singolo file il contesto coincide con il file analizzato;
- in analisi cartella il contesto coincide con il file selezionato dall'utente;
- il nome del file non viene duplicato in una sezione separata in modalita cartella;
- le voci figlie di dettaglio compaiono sotto il file selezionato nella sezione `FILE ANALIZZATI`.

## Report tecnico e report file

La distinzione tra report resta esplicita:

- `Report tecnico`: report dell'analisi corrente
- in analisi singolo file: report del file
- in analisi cartella: report cumulativo

- `Report file`: report tecnico del singolo file selezionato nella navigazione contestuale

Questa distinzione permette di consultare sia il quadro generale della cartella sia il dettaglio di un singolo elemento senza ambiguita.

## Usabilita e leggibilita

Le principali migliorie di usabilita introdotte in questa release includono:

- sidebar e dashboard scrollabili separatamente;
- status bar sempre visibile;
- file lunghi troncati solo alla fine;
- icona `📄` sempre visibile;
- nome completo e percorso completo mostrati nella status bar al passaggio del mouse sulle voci file;
- consultazione piu leggibile del report tecnico e del report file.

## Compatibilita

Questa release mantiene invariati:

- core di analisi;
- scoring;
- CLI;
- formati di output `TXT`, `CSV`, `JSON`, `HTML`;
- comportamento di salvataggio dei report.

L'aggiornamento agisce principalmente sul livello GUI e sulla logica di navigazione/interazione associata.

## Limiti

- La dashboard e una vista di consultazione e non sostituisce il report tecnico completo.
- Il risk score resta un indice tecnico di anomalia documentale, non una prova automatica di manomissione.
- I metadati come `Creatore` e `Ultima modifica di` dipendono da cio che il file dichiara o da cio che il contenitore supportato rende disponibile.
- L'analisi cartella resta non ricorsiva.
- Alcune viste di dettaglio possono rimandare al report tecnico quando il dato non e disponibile in forma strutturata.

## Verifica

- `py_compile`: OK
- `pytest`: 86 test passati nello stato corrente del repository
