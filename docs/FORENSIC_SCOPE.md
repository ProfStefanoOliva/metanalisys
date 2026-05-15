# Forensic Scope

## Cosa fa il software

`metanalisys` fornisce supporto tecnico all'analisi preliminare dei metadati di file Microsoft Office. In particolare:

- calcola hash del file analizzato;
- raccoglie informazioni base del file system;
- prova a estrarre metadati interni dai formati Office Open XML supportati;
- produce report leggibili in formato testuale e JSON.

## Cosa non fa

Il software non:

- certifica autenticita, provenienza o paternita del documento;
- sostituisce imaging forense, acquisizione forense o conservazione probatoria;
- esclude da solo la possibilita di alterazioni pregresse;
- sostituisce l'analisi professionale del contenuto del documento;
- sostituisce procedure autorizzate, catena di custodia o verbalizzazione.

## Limiti dell'analisi dei metadati Office

I metadati Office possono:

- essere incompleti o assenti;
- essere stati sovrascritti da software diversi;
- riflettere conversioni, importazioni o esportazioni;
- dipendere dal sistema operativo, dalla suite Office o dal flusso di lavoro;
- non rappresentare da soli una prova affidabile del contesto fattuale.

Per i formati OOXML supportati il tool estrae metadati tecnici con copertura piu ampia. Per i formati legacy il supporto puo essere limitato a hash e informazioni base del file.

## Hash del file e validazione probatoria

L'hash del file e utile per identificare il file analizzato e confrontare copie o versioni. Tuttavia:

- il calcolo dell'hash non equivale da solo a validazione probatoria;
- l'integrita rilevante in un contesto forense richiede anche corretta acquisizione, registrazione del contesto, conservazione e verifica della procedura adottata.

## Copie controllate e supporti in sola lettura

Quando possibile, l'analisi dovrebbe avvenire:

- su copia controllata del file;
- in ambiente isolato;
- con supporti o procedure che riducano il rischio di alterazioni non intenzionali;
- entro procedura autorizzata e documentata.

L'uso di supporti in sola lettura o di workflow equivalenti puo contribuire a ridurre il rischio operativo, ma non sostituisce le regole procedurali applicabili.

## Nota su access time

La semplice lettura di un file puo influenzare l'`accessed time` a seconda del sistema operativo, del file system, della configurazione del sistema e degli strumenti impiegati. Questo campo va quindi interpretato con prudenza e nel contesto della procedura effettivamente seguita.

## Alpha status and user responsibility

Il progetto e in stato `Alpha` e non puo essere considerato validato sul campo per tutti i possibili scenari operativi o per tutte le varianti di file Microsoft Office.

L'utilizzatore resta responsabile dell'uso del software, della scelta del contesto operativo e dell'interpretazione dei risultati. Il report prodotto deve essere trattato come supporto tecnico all'analisi preliminare, non come conclusione forense autonoma.

Quando il contesto lo richiede, l'impiego del software dovrebbe avvenire entro procedura autorizzata, con adeguata catena di custodia e con successiva valutazione professionale dei dati raccolti e dei limiti del metodo adottato.
