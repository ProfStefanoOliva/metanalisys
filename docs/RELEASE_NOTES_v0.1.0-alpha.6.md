# Release notes `v0.1.0-alpha.6`

## Sintesi

`v0.1.0-alpha.6` estende alla GUI di `metanalisys` l'analisi riepilogativa di cartella già disponibile nel core e nella CLI.

La release migliora l'accessibilità operativa della funzione per utenti che preferiscono un flusso grafico, mantenendo invariati il modello di analisi, il significato del `risk score` e l'impostazione prudente del progetto. L'obiettivo resta fornire supporto tecnico di triage documentale, non una conclusione forense automatica.

## Novità principali

- pulsante `Apri Cartella` nella GUI;
- distinzione in GUI tra analisi di singolo file e analisi di cartella in base al percorso selezionato;
- visualizzazione del report `TXT` cumulativo nel textbox principale della GUI;
- salvataggio da GUI dei report di cartella in formato `TXT`, `CSV`, `JSON` e `HTML`;
- finestra secondaria `Riepilogo analisi cartella`;
- tabella visuale con colonne reali per una lettura più ordinata;
- colonne `File`, `Famiglia Office`, `Creatore`, `Ultima modifica di`, `Creato`, `Ultima modifica`, `Risk score`, `Livello`, `Stato`;
- riepilogo conteggi `OK`, `LIMITED` ed `ERROR`;
- colorazione prudente delle righe in funzione dello stato;
- nessun salvataggio automatico dopo l'analisi;
- test GUI non fragili, basati su helper non grafici.

## Analisi cartella nella GUI

La funzione di analisi riepilogativa di cartella, già disponibile da CLI, viene ora esposta anche nella GUI.

L'utente può selezionare una cartella tramite il nuovo pulsante dedicato. In fase di analisi, la GUI distingue automaticamente tra file e cartella in base al percorso selezionato, senza richiedere un cambio di modalità separato.

Quando viene analizzata una cartella, il report testuale cumulativo resta comunque disponibile nel textbox principale. Questo mantiene continuità con il flusso già noto e conserva un output tecnico completo immediatamente consultabile dentro l'interfaccia.

## Finestra riepilogativa visuale

La nuova finestra `Riepilogo analisi cartella` serve a rendere più leggibile il riepilogo per utenti meno tecnici o per scenari in cui la tabella testuale del report cumulativo risulta più difficile da consultare.

Il report `TXT` resta il report tecnico completo. La finestra visuale non sostituisce i report esportabili: li affianca come supporto di consultazione sintetica.

La colonna `Ultima modifica di` è distinta sia da `Creatore` sia dalla data `Ultima modifica`. Questa separazione è utile perché consente di leggere in modo più chiaro:

- chi risulta autore del documento;
- chi risulta ultimo modificatore nei metadati;
- quando il documento risulta modificato.

## Salvataggio report da GUI

Il salvataggio non è automatico. Dopo l'analisi, l'utente sceglie esplicitamente la cartella di destinazione.

Per l'analisi cartella, la GUI salva:

- `TXT`
- `CSV`
- `JSON`
- `HTML`

Il formato `HTML` è consigliato per consultazione leggibile. Il `CSV` resta utile per fogli di calcolo, ordinamenti e verifiche tabellari. Il `JSON` resta utile per uso tecnico o strutturato.

## Compatibilità

- il comportamento del singolo file resta invariato;
- il core non cambia modello di scoring;
- la CLI resta compatibile con le versioni precedenti;
- la GUI aggiunge funzionalità ma non cambia il significato del `risk score`.

## Limiti

- l'analisi cartella resta non ricorsiva;
- la finestra visuale mostra un sottoinsieme riepilogativo dei campi;
- il report `TXT` e il report `HTML` restano più completi;
- il `risk score` resta indice tecnico di anomalia documentale, non prova automatica di manomissione;
- i metadati `Creatore` e `Ultima modifica di` dipendono da ciò che il documento Office dichiara nei metadati.

## Verifica

- `py_compile`: `OK`
- `pytest`: `66` test passati nello stato corrente del repository
