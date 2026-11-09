# Build e test

Prerequisiti verificati nei manifest: omniclient/go.mod dichiara Go 1.26.0; gateway Python usa CI 3.11 e desktop CI 3.12. Leggere i file di dipendenze reali, non installare vecchie versioni da guide storiche. [Stato corrente](docs/CURRENT_STATUS.md).

## Go, dalla directory omniclient

```sh
go mod verify
go vet ./...
go test -count=1 ./...
```

Recovery CI Linux aggiunge -race e build. Su Windows -race richiede CGO e un compilatore C funzionante; non basta imporre CGO_ENABLED=1. Per un binario locale scegliere un percorso di output fuori dai file tracciati. Compilare non significa avviare o distribuire un servizio.

## Gateway, ambiente virtuale dedicato

In un venv gia attivato, dalla directory node1-gateway:

```sh
python -m pip install -r requirements-test.txt
python -m playwright install chromium
python -m pytest -v
```

In CI Linux si usa --with-deps per i prerequisiti di sistema; non applicare installazioni di sistema sul PC senza approvazione. requirements-test.txt include requirements.txt e dichiara plugin asyncio/Playwright. Non installare globalmente a caso.

## Desktop ed estensione

Le dipendenze Windows sono in desktop/requirements-windows.txt e non vanno installate nel venv del gateway. L'installer le gestisce nel proprio runtime, soltanto con --apply. I test desktop usano backend simulati e immagini generate. Il test native-browser e opt-in Linux e non esercita il consenso Windows.

Dalla root, nel contesto Linux usato dalla CI:

```sh
node --test omniclient/extension/*.test.cjs
```

Per il test nativo sintetico usare esclusivamente l'ambiente isolato descritto in [CI_NATIVE_DIAG](desktop/CI_NATIVE_DIAG.md); il vecchio Chromium vincolato al test non e un browser da usare per account reali.

## Limiti di release

Non eseguire automaticamente tag, restart, deploy, pkill, pulizia di modcache o reset per risolvere errori. build.yml e una pipeline storica separata: Go 1.21 e matrice runner devono essere revisionati prima di main/tag. I check verdi della PR non certificano quella pipeline o tutte le piattaforme.
