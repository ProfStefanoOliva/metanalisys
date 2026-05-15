# Scientific Validation Protocol

## Finalità del documento

Questo documento definisce un protocollo iniziale di validazione scientifica `Alpha` per `metanalisys`, inteso come strumento Python di supporto tecnico all'analisi dei metadati di file Microsoft Office.

L'obiettivo non è presentare il software come qualificato ufficialmente, definitivamente affidabile o idoneo da solo a conclusioni forensi, ma predisporre una base di verifica riproducibile utile a tecnici, revisori e collaboratori del progetto.

## Scopo della validazione alpha

La validazione alpha serve a:

- verificare in modo controllato il comportamento atteso del software;
- confrontare output prodotti e output attesi su campioni noti;
- individuare limiti, regressioni e aree non ancora coperte;
- supportare una discussione tecnica documentata sull'evoluzione del progetto.

In questa fase, la validazione ha carattere sperimentale e progressivo.

## Test automatici, validazione scientifica e validazione forense operativa

### Test automatici

I test automatici verificano porzioni specifiche del codice in scenari sintetici e ripetibili. Sono utili per controllare regressioni e stabilità del comportamento tecnico.

### Validazione scientifica

La validazione scientifica confronta il comportamento del software con campioni preparati in modo controllato, con ground truth dichiarata e output attesi verificabili. Questo livello punta a produrre osservazioni riproducibili, non a sostituire il giudizio professionale o procedurale.

### Validazione forense operativa

La validazione forense operativa riguarda l'impiego del software in contesti reali autorizzati, con procedure documentate, catena di custodia, controlli organizzativi e valutazione professionale del caso concreto. È un livello distinto e non è sostituito da test automatici o da una validazione alpha.

## Perché usare campioni sintetici o non sensibili

La validazione deve usare solo campioni sintetici o comunque non sensibili per:

- evitare diffusione di dati personali o riservati;
- ridurre rischi legali, etici e organizzativi;
- rendere i casi ripetibili da terzi;
- favorire revisione aperta del comportamento del tool;
- impedire il caricamento di evidenze o materiale proveniente da casi concreti.

Nel repository non devono essere inseriti file Office reali, documenti operativi, evidenze digitali o contenuti provenienti da attivita investigative concrete.

## Ground truth

Per `ground truth` si intende l'insieme delle proprietà note del campione di validazione, definite prima dell'esecuzione del test. Esempi:

- metadati volutamente inseriti in un file sintetico;
- presenza controllata di una macro o di un indicatore;
- presenza di una relationship con percorso utente sintetico;
- assenza attesa di metadati in un campione corrotto o limitato.

Senza ground truth esplicita, il valore del confronto scientifico si riduce in modo significativo.

## Riproducibilità

Per `riproducibilità` si intende la possibilità che un altro revisore, usando lo stesso campione, la stessa versione del software e un ambiente comparabile, ottenga risultati compatibili con quelli documentati.

Per favorire la riproducibilità è opportuno registrare:

- versione del repository o release locale;
- sistema operativo;
- versione Python;
- comando usato;
- campione sintetico impiegato;
- output osservato;
- eventuali differenze rispetto all'output atteso.

## Expected output

Per `expected output` si intende il comportamento previsto del software per uno specifico caso di validazione. L'output atteso può includere:

- presenza delle chiavi `hashes` in JSON;
- presenza di sezioni del report testuale;
- riconoscimento corretto del formato;
- estrazione di metadati esplicitamente presenti nel campione;
- emissione di warning o errori attesi.

L'expected output non richiede necessariamente che ogni dettaglio del report coincida carattere per carattere, ma che gli elementi tecnicamente rilevanti siano coerenti con la ground truth del caso.

## Criteri PASS, WARNING, FAIL

### PASS

Il caso è `PASS` quando il comportamento osservato corrisponde in modo sostanziale all'obiettivo dichiarato e all'output atteso.

### WARNING

Il caso è `WARNING` quando:

- il software completa l'analisi ma con limiti inattesi;
- l'output è parziale ma non palesemente errato;
- emergono differenze minori che richiedono revisione tecnica;
- il risultato e interpretabile ma non pienamente allineato alla ground truth.

### FAIL

Il caso è `FAIL` quando:

- il software va in crash senza gestione attesa;
- l'output principale è assente o incompatibile con la ground truth;
- il formato viene classificato in modo errato;
- hash, report o JSON non vengono prodotti come previsto;
- l'esito osservato compromette l'utilità tecnica del caso.

## Limiti dell'attuale alpha

Nello stato attuale `Alpha`, il progetto presenta limiti che devono essere considerati esplicitamente:

- copertura non esaustiva dei casi Office reali;
- supporto legacy limitato;
- copertura ancora parziale di file corrotti, cifrati o ostili;
- assenza di validazione ampia su grandi collezioni di campioni sintetici;
- possibile variabilità di metadati di file system in base all'ambiente;
- differenza tra correttezza tecnica locale e adeguatezza in un contesto operativo reale.

## Responsabilità dell'utilizzatore

L'utilizzatore resta responsabile:

- della scelta del campione e del contesto di prova;
- dell'interpretazione dei risultati;
- della protezione dei dati trattati;
- del rispetto delle regole organizzative e normative applicabili.

Il software deve essere considerato un supporto tecnico sperimentale e non una base autonoma per conclusioni probatorie o procedurali.

## Necessità di procedure autorizzate in contesti reali

Quando si opera su casi reali o su materiale non pubblico, il software deve essere usato solo entro procedure autorizzate, lecite e documentate. Questo include, ove pertinente:

- controllo del contesto di acquisizione;
- catena di custodia;
- registrazione delle attivita svolte;
- valutazione professionale dei limiti del metodo impiegato.

## Matrice iniziale di validazione

| ID caso | Formato | Tipo campione | Obiettivo | Ground truth richiesta | Esito atteso | Stato |
| --- | --- | --- | --- | --- | --- | --- |
| VAL-001 | DOCX | OOXML sintetico base | Verificare lettura `core.xml` | `author` e/o `created` impostati intenzionalmente | Hash presenti, formato `full`, metadati coerenti | Planned |
| VAL-002 | XLSX | OOXML sintetico base | Verificare parsing metadati di base | `core.xml` con valori noti | Hash presenti, formato `full`, report senza crash | Planned |
| VAL-003 | PPTX | OOXML sintetico base | Verificare supporto OOXML PowerPoint | `core.xml` con metadati controllati | Hash presenti, formato `full`, JSON strutturato | Planned |
| VAL-004 | DOCM/XLSM/PPTM | OOXML sintetico con placeholder macro | Verificare rilevazione indicatore macro | Entry ZIP contenente riferimento `vba` controllato | Indicatore macro o warning coerente | Covered by synthetic automated tests |
| VAL-005 | OOXML corrotto | Archivio ZIP invalido o incompleto | Verificare gestione errore | Campione costruito per fallire il parsing package | Errore gestito senza crash non controllato | Planned |
| VAL-006 | DOC legacy | File sintetico legacy placeholder | Verificare supporto limitato | Estensione `.doc`, contenuto non trattato come OOXML | Hash presenti, supporto `limited`, warning esplicito | Planned |
| VAL-007 | Estensione non supportata | File sintetico non Office | Verificare rifiuto formato | Estensione fuori registry | `UnsupportedFormatError` o messaggio coerente | Planned |
| VAL-008 | File inesistente | Path mancante | Verificare gestione accesso | Percorso noto inesistente | Errore leggibile e controllato | Planned |
| VAL-009 | OOXML con immagine | Pacchetto sintetico con media | Verificare sezione immagini | Immagine minima incorporata nel pacchetto | Sezione immagini valorizzata o errore gestito | Planned |
| VAL-010 | OOXML con relationship | Pacchetto sintetico con `.rels` | Verificare rilevazione percorso utente sintetico | Relationship con path sintetico noto | `user_paths` o indicator coerenti | Planned |
| VAL-011 | JSON output | Campione sintetico qualsiasi | Verificare serializzazione | Presenza attesa di `hashes` e struttura base | File JSON leggibile con chiavi previste | Planned |
| VAL-012 | Text report | Dizionario risultati minimo o campione sintetico | Verificare rendering report | Sezioni richieste definite come expected output | Report con sezioni chiave e notice finale | Planned |
