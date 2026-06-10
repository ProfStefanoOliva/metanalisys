# Release Notes - v0.1.0-alpha.8

## Sintesi

La versione `v0.1.0-alpha.8` non introduce una nuova funzionalita' di rilievo, ma consolida la dashboard GUI introdotta nella `v0.1.0-alpha.7`. Questa release e' focalizzata su stabilizzazione, hardening del comportamento della GUI e maggiore coerenza nella navigazione tra analisi file singolo e analisi cartella.

L'obiettivo principale e' rendere la consultazione piu' robusta e prevedibile, preparando il terreno per sviluppi successivi dell'interfaccia, inclusi miglioramenti funzionali come `Salva tutti`.

## Stabilizzazione della dashboard GUI

In questa release e' stato svolto un lavoro di hardening della navigazione della dashboard. La GUI mantiene meglio la coerenza tra il flusso di analisi di un file singolo e quello di una cartella, evitando transizioni poco chiare tra vista generale, elenco dei file analizzati e dettaglio del file selezionato.

La consultazione dei dettagli resta contestuale al file selezionato, con una separazione piu' chiara tra contenuti globali dell'analisi corrente e contenuti riferiti a un singolo elemento della lista.

## Navigazione e stato interno

La sidebar mantiene in modo piu' coerente la distinzione tra analisi corrente, file analizzati e dettaglio del file selezionato. Le voci figlie sotto il file selezionato restano piu' stabili e coerenti durante la navigazione tra le viste disponibili.

E' stata inoltre ulteriormente verificata la distinzione tra `Report tecnico` e `Report file`, cosi' da ridurre ambiguita' nell'uso della dashboard dopo analisi file e analisi cartella.

## Sidebar piu' compatta

La sidebar e' stata rifinita per ridurre lo spazio vuoto a sinistra dei pulsanti. Le voci risultano piu' compatte e leggibili, mantenendo una piccola indentazione visiva per le voci figlie del file selezionato.

Restano invariati gli elementi di leggibilita' gia' introdotti nelle versioni precedenti, inclusi icone sempre visibili e troncamento finale dei nomi file troppo lunghi.

## Casi limite gestiti meglio

La dashboard gestisce in modo piu' robusto diversi casi limite che in precedenza potevano produrre viste poco chiare o stati incoerenti. In particolare:

- cartella vuota;
- cartella senza file analizzabili;
- file con supporto `LIMITED`;
- file con errore;
- valori mancanti normalizzati e visualizzati come `N/D`.

Questo miglioramento non cambia il motore di analisi, ma rende piu' coerente la presentazione dei risultati quando i dati disponibili sono incompleti o parziali.

## Report tecnico e report file

La distinzione tra i due livelli di report viene ribadita in modo esplicito:

- `Report tecnico` = report dell'analisi corrente;
- in analisi file singolo, il `Report tecnico` coincide con il report del file;
- in analisi cartella, il `Report tecnico` resta il report cumulativo;
- `Report file` = report del singolo file selezionato nella lista dei file analizzati.

Questa distinzione aiuta a evitare letture improprie del contenuto mostrato dalla dashboard durante la consultazione di analisi multiple.

## Compatibilita'

Questa release non modifica i componenti di base del progetto. In particolare:

- il core di analisi non cambia;
- lo scoring non cambia;
- la CLI non cambia;
- i formati `TXT`, `CSV`, `JSON`, `HTML` restano invariati;
- il comportamento di salvataggio report resta invariato.

## Limiti

Restano valide alcune limitazioni gia' note del progetto:

- il risk score resta un indice tecnico di anomalia documentale e non costituisce prova automatica di manomissione;
- la dashboard e' una vista di consultazione e non sostituisce il report tecnico;
- l'analisi cartella resta non ricorsiva;
- i metadati dipendono da cio' che il file dichiara;
- alcune viste di dettaglio possono mostrare informazioni parziali se il documento non contiene dati strutturati sufficienti.

## Verifica

- `py_compile`: OK
- `pytest`: 90 passed
