"""Pytest-Bootstrap für das FotoAlert-Test-Harness.

WICHTIG (TASK-19): Tests laufen IMMER gegen die Dev-Umgebung, nie gegen Prod-Daten.
`FOTOALERT_ENV=dev` zwingt den Store auf `backend/data_dev/`. Diese Zeile muss vor
jedem Import von `data.store` / `main` greifen — deshalb steht sie hier in conftest.py,
das pytest vor der Test-Collection lädt.
"""
import os
import sys
from pathlib import Path

import pytest

# Niemals Prod-Daten anfassen.
os.environ.setdefault("FOTOALERT_ENV", "dev")
# App-Startup im Test deterministisch & offline: kein Scheduler, Precompute, Netzwerk, Backup.
os.environ.setdefault("FOTOALERT_NO_BACKGROUND", "1")
# US-66: feste Test-Credentials (vor App-Import gesetzt).
os.environ.setdefault("FOTOALERT_HOST_PASSWORD", "test-host-pw")
os.environ.setdefault("FOTOALERT_USER_PASSWORD", "test-user-pw")
os.environ.setdefault("FOTOALERT_AUTH_SECRET", "test-secret")

# backend/ auf den Importpfad, damit `from calculations import ...` funktioniert,
# egal aus welchem Verzeichnis pytest gestartet wird.
sys.path.insert(0, str(Path(__file__).parent))


@pytest.fixture(scope="session", autouse=True)
def _isolate_job_run_inserts(tmp_path_factory):
    """BUG-107: Tests, die main._job_start()/_job_error()/_job_done() direkt
    aufrufen (aktuell ausschließlich backend/tests/test_us38.py), schrieben bisher
    ungemockt über den Modul-Singleton main._store in die geteilte
    backend/data_dev/fotoalert.db (FOTOALERT_ENV=dev, s.o.) — dieselbe Datei, aus
    der tools/job_history.py im Dev-Modus liest. Diese Fixture leitet für die
    GESAMTE Testsitzung ausschließlich die eine Methode
    `main._store.insert_job_run` auf die gleichnamige Methode einer frischen,
    temporären LocationStore-Instanz um (dieselbe Technik wie AK11 in US-38,
    dort pro Einzeltest über `LocationStore(db_path=tmp_path/...)` — hier
    session-weit über `tmp_path_factory`, NICHT `tmp_path`, da das nicht
    session-scoped ist). Alle anderen `_store`-Methoden (Locations, Bewertungen,
    QA-Daten usw.) bleiben unverändert gegen die echte data_dev/fotoalert.db
    bestehen — nur dieser eine Schreibpfad wird umgeleitet (Pre-Mortem
    Szenario 1, AK5 sichert das ab).

    Pre-Mortem Szenario 5: reines No-op, wenn `main` in dieser Umgebung nicht
    importierbar ist (z.B. FastAPI-Stack fehlt) — try/except statt
    `pytest.importorskip` auf Suite-Ebene, damit Tests, die main gar nicht
    brauchen, von einem fehlenden Import hier nicht betroffen sind.
    """
    try:
        import main as _main
    except Exception:
        yield
        return

    from data.store import LocationStore

    db_path = tmp_path_factory.mktemp("bug107_job_runs") / "job_runs_isolated.db"
    _throwaway_store = LocationStore(db_path=db_path)

    _main._store.insert_job_run = _throwaway_store.insert_job_run
    try:
        yield
    finally:
        del _main._store.insert_job_run


@pytest.fixture(scope="session")
def client():
    """TestClient gegen main:app — geteilt von allen API-Tests.

    Überspringt sauber (statt rot), wenn der FastAPI-Stack fehlt oder der App-Startup
    im Sandbox scheitert. So bleibt die Offline-Regression immer aussagekräftig.
    """
    pytest.importorskip("fastapi", reason="FastAPI-Stack nicht installiert – bootstrap_sandbox.sh ausführen")
    from fastapi.testclient import TestClient
    try:
        import main  # Import erst hier, damit importorskip vorher greift
        # TASK-83: base_url MUSS https sein, sonst verwirft httpx' Cookie-Jar das
        # Secure-Sitzungscookie stillschweigend bei jedem Folge-Request (Secure-Cookies
        # werden nur über https mitgeschickt; TestClient nutzt ohne explizites base_url
        # "http://testserver"). Ohne diesen Fix wären ALLE cookie-basierten Auth-Tests
        # (auch über user_token/host_token) unabhängig vom Server-Code rot.
        with TestClient(main.app, base_url="https://testserver") as c:
            yield c
    except Exception as exc:  # pragma: no cover - umgebungsabhängig
        pytest.skip(f"App-Startup im Sandbox nicht möglich: {exc}")


@pytest.fixture(autouse=True)
def _isolate_client_cookies(client):
    """TASK-83 Pflicht-Vorlauf (Pre-Mortem-Risiko 5): `client` ist session-scoped und
    teilt seine Cookie-Jar über ALLE Testdateien hinweg. Seit /login ein HttpOnly-Cookie
    setzt, würde ein Login in Test A das Cookie in Test B (der "ohne Auth -> 401" prüft)
    faelschlich am Leben halten. Autouse + function-scoped: läuft vor UND nach jedem
    einzelnen Test, unabhängig davon ob der Test `client` explizit anfordert oder nur
    über eine andere Fixture (z.B. user_token) transitiv nutzt — pytest instanziiert
    autouse-Fixtures vor explizit angeforderten Fixtures gleichen Scopes, d.h. der Login
    in user_token/host_token läuft garantiert NACH diesem Reset."""
    client.cookies.clear()
    yield
    client.cookies.clear()


@pytest.fixture
def user_token(client):
    """US-66/TASK-83: loggt als User auf dem geteilten `client` ein (setzt das neue
    Sitzungs-Cookie dort für alle Folge-Requests dieses Tests) und liefert zusätzlich
    einen gültig signierten "alten" Bearer-Token direkt aus auth.issue_token — die
    /login-JSON-Antwort enthält seit TASK-83 kein token-Feld mehr, manche Tests (z.B.
    TASK-83s eigener Zwangs-Logout-Test) brauchen aber weiterhin einen validen
    Token-String, um zu belegen, dass der alte Header-Pfad nicht mehr funktioniert."""
    r = client.post("/login", json={"password": "test-user-pw"})
    assert r.status_code == 200, r.text
    import auth
    return auth.issue_token("user")


@pytest.fixture
def host_token(client):
    """US-66/TASK-83: analog zu user_token, aber Host-Rolle."""
    r = client.post("/login", json={"password": "test-host-pw"})
    assert r.status_code == 200, r.text
    import auth
    return auth.issue_token("host")


@pytest.fixture
def auth_headers(user_token):
    """TASK-83: Der Authorization-Header wird serverseitig nicht mehr ausgewertet —
    die eigentliche Authentifizierung läuft über das Cookie, das user_token bereits auf
    dem geteilten `client` gesetzt hat. Der Header bleibt aus Kompatibilität zu
    bestehenden Testaufrufen bestehen (harmlos, wird ignoriert)."""
    return {"Authorization": f"Bearer {user_token}"}


@pytest.fixture
def host_headers(host_token):
    """TASK-103: Analog zu auth_headers, aber für die Host-Rolle. Seit TASK-103 ist
    PATCH /locations/{id} auf require_host beschränkt — bestehende PATCH-Tests, die
    inhaltlich nur die PATCH-Funktionalität prüfen (nicht die Auth-Rolle selbst),
    verwenden diese Fixture statt auth_headers, um weiterhin 200 zu erwarten. Der
    Authorization-Header wird wie bei auth_headers serverseitig nicht mehr ausgewertet
    (TASK-83) — die eigentliche Authentifizierung läuft über das Cookie, das host_token
    bereits auf dem geteilten `client` gesetzt hat."""
    return {"Authorization": f"Bearer {host_token}"}


# ---------------------------------------------------------------------------
# Feste Test-Locations (TASK-19-Seed-Ersatz + BUG-94-Nachbesserung 2026-07-31)
# ---------------------------------------------------------------------------

_SEED_LOCATION_ID = "test_bug94_seed_9f3a1c"

# BUG-94-Nachbesserung (2026-07-31, CI-Regression nach dem BUG-94-Kollisions-
# fix): fünf ältere Testdateien (test_api_regression.py, test_bug-61.py,
# test_patch_cache_consistency.py, test_task-83.py, test_us66_login.py)
# referenzieren weiterhin hart die alte ID `custom_1781560330` als eigene
# Modulkonstante `LOC` — diese Dateien selbst werden bewusst NICHT verändert
# (siehe Docstring von ensure_seed_location unten für die Root-Cause-Analyse).
_LEGACY_SEED_LOCATION_ID = "custom_1781560330"


def _seed_location_dict() -> dict:
    """Default-Felder für die BUG-94-eigene, kollisionsfreie Test-Location.

    Werte sind Platzhalter (Raum Berlin/Potsdam); test_bug-94.py patcht bzw.
    prüft ohnehin seine eigenen Felder, reale fotografische Genauigkeit ist
    für den Testzweck irrelevant.
    """
    return {
        "id": _SEED_LOCATION_ID,
        "name": "Test-Harness-Location (BUG-94 Seed)",
        "description": "",
        "category": "SKYLINE",
        "observer_lat": 52.3906,
        "observer_lon": 13.0645,
        "subject_lat": 52.3920,
        "subject_lon": 13.0700,
        "subject_name": "Test-Motiv",
        "subject_height_m": 20.0,
        "subject_width_m": 10.0,
        "distance_m": 500,
        "focal_length_suggestions": [50],
        "special_notes": "",
        "difficulty": 1,
        "observer_floor_height_m": 0.0,
    }


def _legacy_seed_location_dict() -> dict:
    """Default-Felder für die historische feste Test-Location custom_1781560330.

    Eigener, generischer Platzhalter (Raum Berlin/Potsdam) — bewusst NICHT
    identisch mit dem echten, gitignorten Produktiv-/Dev-Eintrag gleicher ID
    aus backend/data/custom_locations.json ("Belvedere Test"). Diese Test-
    Location lebt ausschließlich in der Test-DB (data_dev/, FOTOALERT_ENV=dev)
    und berührt data/custom_locations.json nie. Die fünf abhängigen Testdateien
    patchen bzw. prüfen ohnehin ihre eigenen Felder, reale fotografische
    Genauigkeit ist für den Testzweck irrelevant.
    """
    return {
        "id": _LEGACY_SEED_LOCATION_ID,
        "name": "Test-Harness-Location (Legacy-Seed custom_1781560330)",
        "description": "",
        "category": "SKYLINE",
        "observer_lat": 52.3906,
        "observer_lon": 13.0645,
        "subject_lat": 52.3920,
        "subject_lon": 13.0700,
        "subject_name": "Test-Motiv",
        "subject_height_m": 20.0,
        "subject_width_m": 10.0,
        "distance_m": 500,
        "focal_length_suggestions": [50],
        "special_notes": "",
        "difficulty": 1,
        "observer_floor_height_m": 0.0,
    }


def _ensure_location(loc_dict: dict) -> None:
    """Generische, wiederverwendbare Ensure-Logik für eine feste Test-Location
    (BUG-94-Nachbesserung 2026-07-31 — vormals hart auf eine einzige ID
    zugeschnitten, jetzt für beliebig viele feste Test-Location-IDs nutzbar).

    Zwei Ebenen müssen die Location beide kennen, weil main.py sie getrennt hält:
    - `main._store` (SQLite in data_dev/fotoalert.db) — Persistenzschicht,
      genutzt von PATCH über `_update_custom_location_file`.
    - `main.LOCATIONS` (In-Memory-Liste, geteiltes Objekt mit
      data.locations.LOCATIONS) — wird nur einmal beim App-Start aus der DB
      befüllt (`main._load_custom_locations`). Die `client`-Fixture ist
      session-scoped und startet die App vor dem ersten Testlauf einmal — ein
      reiner DB-Insert wäre für GET/PATCH in der laufenden TestClient-Session
      unsichtbar, weil LOCATIONS bereits geladen ist. Deshalb hängt diese
      Funktion die Location bei Bedarf zusätzlich direkt an `main.LOCATIONS`
      an — exakt das gleiche Konstruktionsmuster wie
      `main._load_custom_locations` für einen einzelnen Eintrag.

    Idempotent: prüft vor jedem Schritt den Ist-Zustand (DB via
    `load_all_custom`, In-Memory via IDs-Set) statt blind zu inserten —
    beliebig oft aufrufbar. Ein DB-Insert-Konflikt aus einem parallelen
    Testlauf (IntegrityError) wird abgefangen statt den Testlauf zu brechen.
    """
    import main as _main
    from data.locations import PhotoLocation, LocationCategory

    location_id = loc_dict["id"]

    # 1) DB-Ebene: nur inserten, wenn noch nicht vorhanden.
    existing_ids = {e["id"] for e in _main._store.load_all_custom()}
    if location_id not in existing_ids:
        try:
            _main._store.create_custom(loc_dict)
        except Exception:
            pass  # Race: paralleler Testlauf hat sie inzwischen angelegt.

    # 2) In-Memory-Ebene: nur anhängen, wenn noch nicht in LOCATIONS.
    if not any(l.id == location_id for l in _main.LOCATIONS):
        loc = PhotoLocation(
            id=loc_dict["id"], name=loc_dict["name"], description=loc_dict["description"],
            category=LocationCategory[loc_dict["category"]],
            observer_lat=loc_dict["observer_lat"], observer_lon=loc_dict["observer_lon"],
            subject_lat=loc_dict["subject_lat"], subject_lon=loc_dict["subject_lon"],
            subject_name=loc_dict["subject_name"], subject_height_m=loc_dict["subject_height_m"],
            subject_width_m=loc_dict["subject_width_m"], distance_m=loc_dict["distance_m"],
            focal_length_suggestions=list(loc_dict["focal_length_suggestions"]),
            special_notes=loc_dict["special_notes"], difficulty=loc_dict["difficulty"],
            observer_floor_height_m=loc_dict["observer_floor_height_m"],
        )
        _main.LOCATIONS.append(loc)


@pytest.fixture
def ensure_seed_location(client):
    """Stellt sicher, dass BEIDE festen Test-Locations existieren: die BUG-94-
    eigene, kollisionsfreie `test_bug94_seed_9f3a1c` (test_bug-94.py) UND die
    historische `custom_1781560330` (fünf ältere Testdateien, siehe unten).

    Root Cause (verifiziert per echtem Pytest-Lauf gegen eine frische
    data_dev/, ohne das gitignorte backend/data/custom_locations.json —
    2026-07-31): `custom_1781560330` existiert NICHT als committeter Seed.
    Bis zur vorherigen BUG-94-Kollisionsfix-Runde zeigte `_SEED_LOCATION_ID`
    selbst auf `custom_1781560330`, wodurch diese (damals einzige) Fixture in
    CI als Nebeneffekt genau die ID anlegte, die test_api_regression.py,
    test_bug-61.py, test_patch_cache_consistency.py, test_task-83.py und
    test_us66_login.py seit ihrer eigenen Entstehung hart als Modulkonstante
    `LOC` referenzieren. Die Kollisionsfix-Runde änderte `_SEED_LOCATION_ID`
    auf eine neue ID (`test_bug94_seed_9f3a1c`), um nicht mehr denselben
    Bezeichner wie der echte, gitignorte Dev-Eintrag "Belvedere Test"
    (backend/data/custom_locations.json, NICHT Teil des Git-Repos) zu
    verwenden — das war für sich genommen richtig, hat aber den ungewollten
    Nebeneffekt gekappt, auf den die fünf o.g. Dateien sich verlassen hatten.
    Lokal blieb das unbemerkt, weil `backend/data/custom_locations.json` auf
    Entwicklungsrechnern echt vorhanden ist und `main._load_custom_locations()`
    daraus automatisch nach data_dev/ migriert (Fallback bei leerer DB) — in
    einem frischen CI-Checkout fehlt diese Datei jedoch komplett (.gitignore),
    weshalb der Fallback dort nie greift und `custom_1781560330` seit der
    Kollisionsfix-Runde in CI mit 404 fehlschlug.

    Lösung: `_LEGACY_SEED_LOCATION_ID` (`custom_1781560330`) wird zusätzlich
    zur neuen BUG-94-ID über dieselbe generische `_ensure_location()`-Logik in
    der Test-DB (data_dev/, komplett getrennt von data/custom_locations.json
    und dem echten Dev-Eintrag) sichergestellt — die BUG-94-Kollisionslösung
    selbst bleibt unverändert bestehen (test_bug-94.py nutzt weiterhin
    ausschließlich die neue, kollisionsfreie ID). Die fünf abhängigen Test-
    dateien wurden inhaltlich NICHT verändert, nur diese Fixture repariert.
    """
    _ensure_location(_seed_location_dict())
    _ensure_location(_legacy_seed_location_dict())
    return _SEED_LOCATION_ID
