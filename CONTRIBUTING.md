# Contributing

Grazie per l'interesse nel progetto.

## Regole generali per i contributi

- Mantieni le modifiche mirate e leggibili.
- Evita refactoring estesi non richiesti dal task.
- Aggiorna la documentazione quando il comportamento visibile cambia.
- Non modificare la `LICENSE` senza esplicita richiesta del maintainer.

## Campioni e dati di test

Non caricare nel repository:

- file Office reali;
- evidenze o materiale proveniente da casi reali;
- dati personali;
- documenti aziendali o riservati.

Usa solo campioni sintetici, minimali e privi di riferimenti personali.

## Stile dei commit

Quando proponi una modifica, preferisci messaggi di commit brevi e descrittivi, per esempio:

- `docs: clarify forensic scope`
- `core: add hash reporting section`
- `gui: align about dialog license text`

## Test manuali minimi richiesti

Per modifiche che toccano il comportamento del tool, indica almeno:

- un test CLI su un formato OOXML supportato;
- un test su formato legacy o supporto limitato, se rilevante;
- un test GUI se la modifica tocca l'interfaccia;
- l'eventuale esito della compilazione Python (`py_compile`) se utile.

## Issue e pull request

- Descrivi il problema in modo riproducibile.
- Spiega l'impatto atteso della modifica.
- Non allegare file sensibili nelle issue pubbliche.
- Se usi campioni sintetici, spiega come sono stati generati.

## Call for testers

Tester, tecnici e revisori sono invitati a contribuire con:

- bug report;
- casi riproducibili;
- campioni sintetici;
- indicazioni sui limiti riscontrati.

Non devono essere caricati file reali, sensibili o provenienti da casi concreti. Per test pubblici e discussioni aperte usare solo contenuti sintetici o comunque non sensibili.
