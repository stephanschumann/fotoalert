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
        with TestClient(main.app) as c:
            yield c
    except Exception as exc:  # pragma: no cover - umgebungsabhängig
        pytest.skip(f"App-Startup im Sandbox nicht möglich: {exc}")


@pytest.fixture
def user_token(client):
    """US-66: gültiges User-Token für geschützte Endpoints."""
    r = client.post("/login", json={"password": "test-user-pw"})
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture
def host_token(client):
    """US-66: gültiges Host-Token (Admin-Routen)."""
    r = client.post("/login", json={"password": "test-host-pw"})
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture
def auth_headers(user_token):
    return {"Authorization": f"Bearer {user_token}"}


# ---------------------------------------------------------------------------
# Feste Test-Location custom_1781560330 (TASK-19-Seed-Ersatz)
# ---------------------------------------------------------------------------

_SEED_LOCATION_ID = "custom_1781560330"


def _seed_location_dict() -> dict:
    """Default-Felder für die feste Test-Location.

    Werte sind Platzhalter (Raum Berlin/Potsdam); die vier Testdateien patchen
    bzw. prüfen ohnehin ihre eigenen Felder, reale fotografische Genauigkeit
    ist für den Testzweck irrelevant.
    """
    return {
        "id": _SEED_LOCATION_ID,
        "name": "Test-Harness-Location (custom_1781560330)",
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


@pytest.fixture
def ensure_seed_location(client):
    """Stellt sicher, dass die feste Test-Location custom_1781560330 existiert.

    Historisch (TASK-19) wurde diese Location einmalig manuell in data_dev/
    geseedet; der Seed ging später verloren, wodurch test_bug-61.py,
    test_api_regression.py, test_patch_cache_consistency.py und
    test_us66_login.py (alle referenzieren sie als Modulkonstante `LOC`) mit
    404 fehlschlugen. Diese Fixture ersetzt den verlorenen manuellen
    Seed-Schritt idempotent, ohne main.py/data/store.py zu verändern.

    Zwei Ebenen müssen die Location beide kennen, weil main.py sie getrennt hält:
    - `main._store` (SQLite in data_dev/fotoalert.db) — Persistenzschicht,
      genutzt von PATCH über `_update_custom_location_file`.
    - `main.LOCATIONS` (In-Memory-Liste, geteiltes Objekt mit
      data.locations.LOCATIONS) — wird nur einmal beim App-Start aus der DB
      befüllt (`main._load_custom_locations`). Die `client`-Fixture ist
      session-scoped und startet die App vor dem ersten Testlauf einmal — ein
      reiner DB-Insert wäre für GET/PATCH in der laufenden TestClient-Session
      unsichtbar, weil LOCATIONS bereits geladen ist. Deshalb hängt diese
      Fixture die Location bei Bedarf zusätzlich direkt an `main.LOCATIONS`
      an — exakt das gleiche Konstruktionsmuster wie
      `main._load_custom_locations` für einen einzelnen Eintrag.

    Idempotent: prüft vor jedem Schritt den Ist-Zustand (DB via
    `load_all_custom`, In-Memory via IDs-Set) statt blind zu inserten —
    beliebig oft aufrufbar. Ein DB-Insert-Konflikt aus einem parallelen
    Testlauf (IntegrityError) wird abgefangen statt den Testlauf zu brechen.
    """
    import main as _main
    from data.locations import PhotoLocation, LocationCategory

    loc_dict = _seed_location_dict()

    # 1) DB-Ebene: nur inserten, wenn noch nicht vorhanden.
    existing_ids = {e["id"] for e in _main._store.load_all_custom()}
    if _SEED_LOCATION_ID not in existing_ids:
        try:
            _main._store.create_custom(loc_dict)
        except Exception:
            pass  # Race: paralleler Testlauf hat sie inzwischen angelegt.

    # 2) In-Memory-Ebene: nur anhängen, wenn noch nicht in LOCATIONS.
    if not any(l.id == _SEED_LOCATION_ID for l in _main.LOCATIONS):
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

    return _SEED_LOCATION_ID
