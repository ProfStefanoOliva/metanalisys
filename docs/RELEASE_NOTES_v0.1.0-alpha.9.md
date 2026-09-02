# Release Notes - v0.1.0-alpha.9

## Sintesi

La versione `v0.1.0-alpha.9` prepara il progetto alla distribuzione Windows x64 portable della GUI. L'obiettivo e' consentire a utenti non tecnici di scaricare un archivio ZIP da GitHub Releases, estrarlo ed eseguire `metanalisys.exe` senza installare Python, dipendenze Python o sorgenti del repository.

Questa release mantiene invariato lo stato Alpha del software.

## Build Windows portable

Questa modifica introduce una procedura riproducibile basata su PyInstaller in modalita' `onedir`, con eseguibile GUI senza console e icona Windows del progetto.

Sono stati aggiunti:

- una configurazione PyInstaller dedicata;
- un file separato per le dipendenze di build;
- uno script PowerShell per generare la directory portable e lo ZIP finale;
- un README breve destinato all'utente finale della build portable.

## Ambito tecnico

La build portable e' destinata all'entry point GUI `src/metanalisysGUI.py`.

La configurazione include gli asset del progetto e i data file necessari a `customtkinter` tramite le funzioni standard di PyInstaller.

## Compatibilita' funzionale

Questa modifica non prevede cambiamenti agli algoritmi di analisi.

In particolare:

- nessuna modifica prevista allo scoring;
- nessuna modifica prevista ai parser Office;
- nessuna modifica prevista agli indicatori;
- nessuna modifica prevista al contenuto dei report;
- nessuna modifica prevista alla logica forense.

## Limiti noti

Restano validi i limiti gia' documentati per il progetto:

- il software e' in fase Alpha;
- il risk score resta un indice tecnico di anomalia documentale;
- il software non costituisce da solo una prova;
- il software non sostituisce procedure autorizzate, catena di custodia o valutazione professionale;
- l'analisi cartella resta non ricorsiva;
- i metadati dipendono da cio' che il file dichiara.

## Verifica

La build Windows x64 portable e' stata realmente costruita con PyInstaller in modalita' `onedir` ed e' stato generato il pacchetto `metanalisys-v0.1.0-alpha.9-Windows-x64.zip`.

La verifica manuale su Windows x64 ha confermato:

- presenza nel bundle di `metanalisys.exe`, directory `_internal`, asset icona `.ico` e `.png`, `LICENSE` e `README_PORTABLE.txt`;
- apertura reale della GUI dall'eseguibile, con corretta visualizzazione dell'interfaccia e dell'icona;
- analisi di un file DOCX reale con corretta estrazione dei metadati disponibili;
- analisi di un DOCX sintetico con corretta estrazione di autore, ultimo modificatore, date dichiarate di creazione e modifica, famiglia Office `Word` e formato `.docx`;
- salvataggio del report dalla GUI;
- estrazione dello ZIP in una directory esterna al repository;
- avvio e uso corretto dell'applicazione dalla copia estratta, senza dipendenza operativa dal repository sorgente o dalla `.venv`.

Questa verifica e' una validazione tecnica manuale della build portable e del flusso GUI principale. Non costituisce certificazione forense, validazione probatoria, garanzia di assenza di bug o conferma di idoneita' per tutti gli scenari d'uso. Lo stato del progetto resta Alpha.
