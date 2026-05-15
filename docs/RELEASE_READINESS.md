# Release Readiness

## Finalità

Questa checklist supporta la preparazione della prima pubblicazione open source alpha di `metanalisys`. Il suo scopo è aiutare a verificare coerenza documentale, qualità minima del repository e chiarezza dei limiti d'uso del software.

La checklist non sostituisce una revisione tecnica o organizzativa più ampia. Va usata come supporto operativo per una pubblicazione prudente e trasparente.

## Checklist per pubblicazione open source alpha

### 1. Verifica branch `main` pulito

- Confermare che `main` non contenga modifiche locali non intenzionali.
- Verificare che il merge verso `main` sia stato revisionato.
- Evitare rilascio da un branch con file temporanei, report generati o artefatti non previsti.

### 2. Verifica test locali

- Eseguire `py_compile` sui file Python principali.
- Eseguire `pytest` sull'intera suite.
- Verificare che la suite passi senza dipendere da file Office reali o da campioni persistenti nel repository.

### 3. Verifica CI GitHub Actions

- Controllare che la workflow di test su GitHub Actions sia attiva.
- Verificare esito positivo su `push` e `pull_request` verso `main`.
- Confermare che la CI esegua solo controlli tecnici coerenti con lo stato alpha del progetto.

### 4. Verifica assenza di file Office reali tracciati

- Confermare che il repository non contenga file Office reali.
- Confermare che non siano stati aggiunti campioni binari permanenti.
- Verificare che i test usino solo campioni sintetici generati a runtime.

### 5. Verifica assenza di dati personali, evidenze digitali, report generati o percorsi locali

- Controllare che non siano tracciati dati personali.
- Controllare che non siano presenti evidenze digitali o materiali provenienti da casi concreti.
- Rimuovere eventuali report JSON/TXT generati localmente.
- Verificare che README e documentazione non contengano path locali impropri o riferimenti sensibili.

### 6. Verifica coerenza licenza GPLv3

- Confermare presenza del file `LICENSE`.
- Verificare coerenza tra testo della licenza e riferimenti documentali.
- Assicurarsi che README e documenti di supporto richiamino correttamente GPLv3 senza formulazioni fuorvianti.

### 7. Verifica README, SECURITY, CONTRIBUTING, CHANGELOG

- README aggiornato e coerente con lo stato alpha.
- SECURITY con indicazioni prudenti su file sospetti e issue pubbliche.
- CONTRIBUTING con divieto esplicito di campioni reali o sensibili.
- CHANGELOG aggiornato con le principali modifiche della release alpha.

### 8. Verifica documenti forensi e legali

- Presenza e coerenza di `FORENSIC_SCOPE.md`.
- Presenza e coerenza di `LEGAL_LIMITS.md`.
- Presenza e coerenza di `CHAIN_OF_CUSTODY.md`.
- Presenza di documenti su testing, validazione scientifica alpha e alpha test plan.

### 9. Verifica limiti alpha

- Chiarezza sul fatto che il software è in fase alpha.
- Chiarezza sui limiti noti, inclusi supporto legacy limitato e copertura non esaustiva dei casi reali.
- Assenza di formulazioni che suggeriscano affidabilità definitiva o uso autonomo in contesti probatori.

### 10. Verifica GitHub topics

- Valutare topics coerenti con il progetto, ad esempio:
  - `python`
  - `digital-forensics`
  - `metadata`
  - `ooxml`
  - `office-documents`
  - `alpha`
- Evitare topics che suggeriscano capacità o qualifiche non supportate.

### 11. Verifica release notes

- Preparare note di release chiare, sintetiche e prudenti.
- Evidenziare funzionalità principali, limiti noti e stato alpha.
- Includere un richiamo esplicito alla responsabilità dell'utilizzatore.

### 12. Verifica tag di release

- Usare un tag coerente con pre-release alpha, ad esempio `v0.1.0-alpha.1`.
- Verificare che il tag punti alla revisione corretta.
- Distinguere chiaramente la release alpha da una release stabile.

### 13. Verifica comprensione di responsabilità e limiti da parte dell'utente finale

- Confermare che README, release notes e documentazione chiariscano che il software è un supporto tecnico.
- Confermare che sia chiaro che non sostituisce procedura autorizzata, catena di custodia, verbali o valutazione professionale.
- Confermare che sia chiaro il divieto di usare issue pubbliche per file reali o sensibili.

## Nota finale

Una release alpha pubblica dovrebbe privilegiare trasparenza, riproducibilità e prudenza comunicativa. L'obiettivo è favorire sperimentazione controllata, revisione tecnica e miglioramento progressivo del progetto.
