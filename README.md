# metanalisys

`metanalisys` e uno strumento Python di supporto tecnico all'analisi preliminare dei metadati di file Microsoft Office. Il progetto include una versione a riga di comando e una GUI basata su `customtkinter`.

## Development status: Alpha

Il software e attualmente in fase `Alpha`. In questo stato e adatto a valutazione tecnica, test e sperimentazione controllata, ma non deve essere usato come unica base per conclusioni forensi, decisioni procedurali o valutazioni probatorie.

L'uso del software e sotto la responsabilita dell'utilizzatore. Chi lo impiega deve operare solo entro procedure autorizzate, lecite e documentate, tenendo conto dei limiti tecnici del progetto e della necessita di valutazione professionale del caso concreto.

Il progetto beneficia di tester e revisori tecnici. Eventuali test pubblici, issue o contributi devono usare solo file sintetici o comunque non sensibili, senza caricare file Office reali, evidenze o dati personali.

## Scopo

Il software aiuta a:

- identificare il file analizzato e i suoi hash;
- estrarre metadati da documenti Office moderni basati su Open XML;
- evidenziare alcuni indicatori tecnici utili a una prima revisione;
- produrre report testuali e JSON per uso entro procedura autorizzata.

## Avvertenza forense

Il progetto e pensato come supporto tecnico all'analisi dei metadati. Non dichiara conformita forense assoluta, non sostituisce catena di custodia, verbali, autorizzazioni, valutazione professionale o normativa processuale applicabile.

Per un inquadramento prudente dell'uso:

- vedere [docs/FORENSIC_SCOPE.md](docs/FORENSIC_SCOPE.md)
- vedere [docs/LEGAL_LIMITS.md](docs/LEGAL_LIMITS.md)
- vedere [docs/CHAIN_OF_CUSTODY.md](docs/CHAIN_OF_CUSTODY.md)
- vedere [docs/RISK_SCORING.md](docs/RISK_SCORING.md)
- vedere [docs/TESTING_AND_VALIDATION.md](docs/TESTING_AND_VALIDATION.md)
- vedere [docs/SCIENTIFIC_VALIDATION_PROTOCOL.md](docs/SCIENTIFIC_VALIDATION_PROTOCOL.md)
- vedere [docs/ALPHA_TEST_PLAN.md](docs/ALPHA_TEST_PLAN.md)
- vedere [docs/RELEASE_READINESS.md](docs/RELEASE_READINESS.md)
- vedere [docs/RELEASE_NOTES_v0.1.0-alpha.1.md](docs/RELEASE_NOTES_v0.1.0-alpha.1.md)

## Formati supportati

### OOXML con supporto metadati `full`

- Word: `.docx`, `.docm`, `.dotx`, `.dotm`
- Excel: `.xlsx`, `.xlsm`, `.xltx`, `.xltm`, `.xlam`
- PowerPoint: `.pptx`, `.pptm`, `.potx`, `.potm`, `.ppsx`, `.ppsm`
- Visio: `.vsdx`, `.vsdm`, `.vstx`, `.vstm`

Per questi formati il tool calcola hash, legge informazioni file system e prova a estrarre metadati Office Open XML, relationships, file incorporati, immagini e alcuni indicatori tecnici.

### Legacy con supporto `limited`

- Word: `.doc`, `.dot`
- Excel: `.xls`, `.xlt`
- PowerPoint: `.ppt`, `.pot`, `.pps`

Per i formati legacy il parser completo non e implementato. Il tool mostra comunque hash, informazioni base del file e un messaggio esplicito di supporto limitato, senza dichiarare estrazione completa dei metadati interni.

## Installazione

Prerequisiti:

- Python 3.11

Creazione ambiente virtuale in PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install Pillow customtkinter
```

## Testing

Installazione dipendenze runtime:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r .\requirements.txt
```

Installazione dipendenze di test:

```powershell
python -m pip install -r .\requirements-dev.txt
```

Esecuzione test:

```powershell
.\.venv\Scripts\python.exe -m pytest .\tests
```

Per dettagli sulla suite automatica e sui suoi limiti:

- vedere [docs/TESTING_AND_VALIDATION.md](docs/TESTING_AND_VALIDATION.md)

## Continuous integration

Il repository include una workflow GitHub Actions che esegue automaticamente:

- `py_compile` sui principali file Python del progetto;
- `pytest` sulla cartella `tests`.

La CI usa i test sintetici gia presenti nel repository e non richiede file Office reali. Anche quando la pipeline termina con esito positivo, l'esito resta una verifica tecnica del software e non costituisce validazione probatoria o valutazione forense professionale.

## Uso CLI

Avvio con percorso file come argomento:

```powershell
.\.venv\Scripts\python.exe .\src\metanalisys.py C:\percorso\documento.docx
```

Avvio interattivo:

```powershell
.\.venv\Scripts\python.exe .\src\metanalisys.py
```

La CLI consente di scegliere tra:

- stampa del report a schermo;
- salvataggio del report TXT.

Il report JSON viene generato dal tool con naming automatico.

## Uso GUI

```powershell
.\.venv\Scripts\python.exe .\src\metanalisysGUI.py
```

Flusso operativo:

1. selezionare un file Office;
2. avviare l'analisi;
3. consultare il report nella finestra;
4. salvare il report testuale se necessario.

## Output generati

Il progetto puo generare:

- report testuale mostrato a schermo;
- report TXT con suffisso `_forensic_report.txt`;
- report JSON con suffisso `_forensic_report.json`.

Le prime sezioni del report includono:

- hash del file, con `sha256` e `sha512`;
- informazioni del file;
- stato del supporto formato.

## Esempio di report

```text
======================================================================
OFFICE FORENSIC ANALYSIS REPORT
======================================================================

[FILE HASH]

sha256: ...
sha512: ...

[FILE INFO]

filename: example.docx
path: C:\path\example.docx
extension: .docx

[FORMAT SUPPORT]

extension: .docx
family: Word
label: Word Document
container: ooxml
metadata_support: full
```

## Dati di test e contenuti sensibili

Nel repository non devono essere caricati:

- file Office reali;
- evidenze digitali;
- documenti provenienti da casi reali;
- dati personali o dati particolari;
- allegati sensibili nelle issue pubbliche.

Usare solo campioni sintetici, anonimizzati e privi di riferimenti personali.

## Autore

Progetto sviluppato e mantenuto da Stefano Oliva.

Repository: ProfStefanoOliva/metanalisys

## Licenza

Il progetto e distribuito sotto licenza GNU General Public License v3.0. Per il testo completo fare riferimento al file [LICENSE](LICENSE).
