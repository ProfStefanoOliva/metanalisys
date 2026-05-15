# Testing and Validation

## Scopo della suite di test

La suite di test automatica del progetto ha lo scopo di stabilizzare il comportamento del modulo core e di ridurre regressioni nelle funzionalita principali gia implementate. In particolare, i test aiutano a verificare che:

- il calcolo degli hash resti coerente;
- il riconoscimento dei formati supportati non cambi in modo involontario;
- gli errori di input basilari siano gestiti in modo prevedibile;
- il rendering dei report e la serializzazione JSON continuino a produrre output attesi;
- una minima analisi OOXML sintetica possa essere eseguita senza crash.

La suite e un supporto tecnico alla qualita del software. Non sostituisce test manuali su casi d'uso reali autorizzati, ne una valutazione forense professionale.

## Uso di pytest

I test automatici correnti usano `pytest`, scelto perche leggero, diffuso e adatto a:

- eseguire test unitari sintetici;
- gestire file temporanei con fixture come `tmp_path`;
- esprimere facilmente casi parametrici e verifiche di eccezioni.

La dipendenza di test e dichiarata separatamente in [requirements-dev.txt](C:\Users\oliva\Documents\LavoriAI\metanalisys\requirements-dev.txt) per non appesantire le dipendenze runtime del progetto.

## Test automatici, test manuali e validazione forense professionale

### Test automatici

I test automatici verificano comportamenti tecnici mirati e ripetibili del codice. Sono utili per individuare regressioni e controllare output attesi in condizioni sintetiche.

### Test manuali

I test manuali servono a controllare aspetti operativi non coperti pienamente dai test automatici, per esempio:

- comportamento CLI end-to-end;
- comportamento GUI;
- leggibilita del report;
- gestione pratica di flussi di lavoro su file autorizzati o campioni sintetici.

### Validazione forense professionale

La validazione forense professionale e un livello diverso. Richiede contesto operativo, procedura autorizzata, catena di custodia, valutazione professionale e rispetto della disciplina applicabile. Una suite `pytest` che passa non equivale a validita probatoria o conformita legale assoluta.

## Struttura della cartella tests

La cartella [tests](C:\Users\oliva\Documents\LavoriAI\metanalisys\tests) contiene la suite automatica corrente. Al momento comprende:

- [tests/conftest.py](C:\Users\oliva\Documents\LavoriAI\metanalisys\tests\conftest.py)
- [tests/test_metanalisys_core.py](C:\Users\oliva\Documents\LavoriAI\metanalisys\tests\test_metanalisys_core.py)

## Ruolo di tests/conftest.py

`tests/conftest.py` prepara il contesto di esecuzione dei test aggiungendo `src/` al `sys.path`. Questo consente di importare il modulo `metanalisys_core` senza trasformare il progetto in un pacchetto Python piu complesso e senza modificare la logica applicativa.

## Ruolo di tests/test_metanalisys_core.py

`tests/test_metanalisys_core.py` raccoglie i test sintetici del modulo core. Il file esercita:

- hashing del file;
- riconoscimento formati;
- validazione del path;
- formattazione del report;
- salvataggio JSON;
- analisi minimale di un pacchetto OOXML sintetico.

## Perche i test usano file temporanei e campioni sintetici

I test usano file temporanei e campioni sintetici generati durante l'esecuzione per diverse ragioni:

- evitare dipendenza da documenti esterni;
- mantenere la suite ripetibile e portabile;
- ridurre il rischio di esporre dati sensibili;
- rispettare il principio di minimizzazione dei dati;
- isolare il comportamento tecnico da contenuti reali non necessari.

Nel caso OOXML, il test costruisce dinamicamente un archivio ZIP minimale con `docProps/core.xml` e `docProps/app.xml`, sufficiente a esercitare il parser senza introdurre documenti Office reali.

## Perche non devono essere usati file Office reali nel repository

Nel repository non devono essere inseriti file Office reali perche potrebbero contenere:

- dati personali;
- informazioni riservate;
- evidenze digitali;
- metadati non intenzionalmente divulgati;
- contenuti malevoli o non verificati.

Per questo motivo la suite di test deve continuare a usare solo contenuti sintetici, temporanei e privi di riferimenti personali.

## Cosa verificano i test attuali

La suite corrente verifica in modo automatico:

- hashing `SHA-256` e `SHA-512`;
- non alterazione del file durante il calcolo hash, almeno rispetto a contenuto, dimensione e `mtime`;
- riconoscimento dei formati supportati e distinzione tra `full` e `limited`;
- gestione di path non validi o mancanti;
- rendering del report testuale con le sezioni principali attese;
- salvataggio e rilettura del report JSON;
- analisi OOXML sintetica minimale con presenza di hash, supporto `full`, metadati di base e generazione del report senza crash.

## Cosa i test non dimostrano

Il fatto che la suite passi non dimostra:

- validita probatoria del report;
- assenza di alterazioni pregresse del file analizzato;
- completezza rispetto a tutti i possibili casi Office reali;
- copertura di file cifrati, corrotti, ostili o malevoli;
- correttezza di una procedura investigativa o di catena di custodia;
- conformita legale o processuale assoluta.

I risultati dei test vanno quindi letti come verifica tecnica del comportamento del software in scenari sintetici, non come attestazione forense definitiva.

## Comandi PowerShell

Installazione dipendenze runtime:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r .\requirements.txt
```

Installazione dipendenze dev:

```powershell
python -m pip install -r .\requirements-dev.txt
```

Esecuzione test:

```powershell
.\.venv\Scripts\python.exe -m pytest .\tests
```

Controllo sintattico opzionale:

```powershell
.\.venv\Scripts\python.exe -m py_compile .\src\metanalisys.py .\src\metanalisys_core.py .\src\metanalisysGUI.py .\tests\conftest.py .\tests\test_metanalisys_core.py
```

## Come interpretare un output tipo "14 passed"

Un output come:

```text
14 passed
```

significa che tutti i quattordici test raccolti da `pytest` sono stati eseguiti con esito positivo nell'ambiente corrente. Questo indica che, per gli scenari sintetici coperti, il comportamento osservato e coerente con le aspettative definite nei test.

Non significa invece che:

- ogni percorso applicativo sia coperto;
- tutti i file Office reali siano gestiti correttamente;
- il software sia adatto da solo a finalita probatorie.

## Regole per aggiungere nuovi test in futuro

Quando si aggiungono nuovi test, e consigliato:

- mantenere i test piccoli, mirati e leggibili;
- usare `tmp_path` o file temporanei invece di file persistenti nel repository;
- generare campioni sintetici minimi quando serve simulare file Office;
- non inserire file Office reali, evidenze o dati personali;
- verificare sia casi positivi sia errori attesi;
- preferire test deterministici e indipendenti dall'ambiente;
- documentare chiaramente eventuali limiti del test;
- aggiornare README e changelog se la strategia di testing cambia in modo visibile.
