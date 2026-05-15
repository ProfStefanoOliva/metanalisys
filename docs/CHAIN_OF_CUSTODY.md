# Chain of Custody Guidance

## Finalita

Questa procedura operativa consigliata ha valore organizzativo e prudenziale. Serve a usare il software come supporto tecnico entro procedura autorizzata, senza sostituire regole interne o obblighi normativi applicabili.

## Procedura consigliata

1. Identificare il caso o l'attivita.
   Registrare codice caso, pratica, ticket o riferimento interno.

2. Identificare l'operatore.
   Annotare nominativo, ruolo, struttura di appartenenza e, se previsto, titolo autorizzativo o incarico.

3. Identificare il file.
   Registrare nome file, percorso o origine dichiarata, dimensione e ogni riferimento utile a ricondurre il campione alla fonte di lavoro.

4. Calcolare gli hash.
   Registrare almeno SHA-256 del file analizzato. Se disponibile, registrare anche SHA-512 e verificare che i valori riportati nel report corrispondano al file effettivamente esaminato.

5. Operare su copia controllata.
   Quando possibile, analizzare una copia di lavoro controllata e non il file originale. Preferire supporti o procedure che riducano il rischio di alterazione.

6. Registrare data e ora.
   Annotare data, ora, sistema utilizzato e contesto operativo dell'analisi.

7. Conservare il report.
   Archiviare il report testuale e JSON in un contenitore documentale appropriato, con controlli di accesso coerenti con la sensibilita del caso.

8. Evitare alterazioni del file originale.
   Non modificare, rinominare, aprire con software produttivo o trasferire inutilmente il file originale durante la fase di supporto tecnico.

## Limiti della procedura

Questa procedura:

- non sostituisce una catena di custodia formalmente valida secondo la disciplina applicabile;
- non sostituisce acquisizione forense, imaging o sigillatura;
- non elimina il rischio che alcuni metadati di file system, come l'access time, possano essere influenzati dal sistema o dall'ambiente operativo.
