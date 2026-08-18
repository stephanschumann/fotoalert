"""Regressionssuite — BUG-95: Pflichtfeld-Prüfung für "Motivname" (subject_name) beim
PATCH-Endpoint für Locations, plus Diagnose-Logging im Titel-Fallback-Zweig von
main._build_opportunity_title().

Root Cause (siehe BACKLOG.md BUG-95, Root-Cause-Analyse): weder das
Bearbeiten-Formular (Frontend) noch der PATCH-Endpoint (Backend) prüften "Motivname"
auf einen nicht-leeren Wert — anders als "Name", das bereits eine Client-seitige
Leer-Prüfung hatte. Ein versehentlich geleertes "Motivname"-Feld wurde ohne
Fehlermeldung übernommen und dauerhaft persistiert. Da die drei
Wolkenstimmungs-Events (Rote Wolken/Goldene Wolken/Himmelsröte) live bei jedem
3-Stunden-Wetter-Overlay-Lauf aus dem aktuellen Location-Zustand neu gebaut werden
(main._build_opportunity_title()), fiel ein so geleerter Motivname erst bei der
nächsten Kartenanzeige als Fallback-Titel (nur Event-Typ, kein Motivbezug) auf.

Freigegebene Option C (Stephans Freigabe-Protokoll 2026-08-16): Validierungsfix
(Backend PATCH + Frontend-Formular) UND Diagnose-Logging im Titel-Fallback-Zweig,
unabhängig voneinander.

Deckt die automatisierbaren Akzeptanzkriterien aus BACKLOG.md ab:
  - AK1 (Formular-Fehlermeldung) ist reines Frontend-JS (web/index.html,
    LocationDetail.saveEdit) und hier NICHT automatisiert abgedeckt (kein
    Browser-/DOM-Test in dieser Datei) — manuell/per Chrome-Subagent zu prüfen.
  - AK2 (Server lehnt direkten API-Aufruf mit leerem Motivnamen ab):
    TestPatchLehntLeerenMotivnamenAb.
  - AK3 (Diagnose-Logging bei leerem Motivnamen zur Laufzeit):
    TestDiagnoseLoggingImTitelFallback.
  - AK4 (bestehende, korrekt gepflegte Locations nicht rückwirkend betroffen):
    TestPatchMitGueltigemWertUnveraendert (Gegenprobe: gültiger Wert weiterhin
    unverändert übernehmbar; description/special_notes dürfen weiterhin leer sein).

Direktes Vorlagen-Muster: backend/tests/test_bug-84.py (PATCH-Validierungstest mit
eigener, isolierter Location-Fixture + API-Roundtrip über den TestClient, gleiches
host_headers-Muster seit TASK-103).
"""
from __future__ import annotations

import logging
import uuid

import pytest

pytestmark = [pytest.mark.offline, pytest.mark.regression]


# ---------------------------------------------------------------------------
# Fixture — eigene, isolierte Test-Location (kein Shared State, fotoalert-impl
# Pattern 12). "Standard"-Location (kein "custom_"-Präfix), da BUG-95s
# Root-Cause-Hypothese explizit den Override-Persistenzpfad betrifft.
# ---------------------------------------------------------------------------

@pytest.fixture
def standard_location_id(client):
    import main
    from data.locations import PhotoLocation, LocationCategory

    loc_id = f"standard_test_bug95_{uuid.uuid4().hex[:8]}"
    new_loc = PhotoLocation(
        id=loc_id, name="BUG-95-Test-Location",
        description="Testort für test_bug95.py",
        category=LocationCategory.WASSER,
        observer_lat=52.5, observer_lon=13.4,
        subject_lat=52.51, subject_lon=13.41, subject_name="Testmotiv",
        difficulty=2,
    )
    main.LOCATIONS.append(new_loc)

    yield loc_id

    main.LOCATIONS[:] = [l for l in main.LOCATIONS if l.id != loc_id]
    # Kein delete_override() im Code (nur upsert_override) -- Override-Zeile direkt
    # per Rohzugriff entfernen, damit kein Testartefakt in location_overrides bleibt
    # (gleiches Muster wie test_bug-84.py).
    try:
        with main._store._connect() as conn:
            conn.execute("DELETE FROM location_overrides WHERE id = ?", (loc_id,))
            conn.commit()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# AK2 — Server lehnt leeren/nur-Leerzeichen Motivnamen (und Namen) per direktem
# PATCH ab, statt ihn stillschweigend zu übernehmen.
# ---------------------------------------------------------------------------

class TestPatchLehntLeerenMotivnamenAb:

    @pytest.mark.parametrize("value", ["", "   ", "\t\n"])
    def test_empty_or_whitespace_subject_name_rejected(self, client, host_headers, standard_location_id, value):
        r = client.patch(
            f"/locations/{standard_location_id}",
            json={"subject_name": value},
            headers=host_headers,
        )
        assert r.status_code == 422, r.text
        assert "subject_name" in r.json()["detail"]

        # Kein stiller Teil-Erfolg: bestehender Wert bleibt unangetastet.
        single = client.get(f"/locations/{standard_location_id}").json()
        assert single["subject_name"] == "Testmotiv"

    @pytest.mark.parametrize("value", ["", "   "])
    def test_empty_or_whitespace_name_rejected(self, client, host_headers, standard_location_id, value):
        """Gleiche Prüfung greift auch für "name" (Ticket verlangt mindestens name +
        subject_name), auch wenn "Name" bereits vorher eine Client-Prüfung hatte —
        die serverseitige Lücke betraf beide Felder gleichermaßen."""
        r = client.patch(
            f"/locations/{standard_location_id}",
            json={"name": value},
            headers=host_headers,
        )
        assert r.status_code == 422, r.text
        assert "name" in r.json()["detail"]


# ---------------------------------------------------------------------------
# AK4 — Gegenprobe: ein gültiger, nicht-leerer Motivname wird weiterhin normal
# übernommen; legitim leere Felder (description/special_notes) bleiben erlaubt.
# ---------------------------------------------------------------------------

class TestPatchMitGueltigemWertUnveraendert:

    def test_valid_subject_name_still_persists(self, client, host_headers, standard_location_id):
        r = client.patch(
            f"/locations/{standard_location_id}",
            json={"subject_name": "Neues Motiv"},
            headers=host_headers,
        )
        assert r.status_code == 200, r.text
        assert r.json()["updated"]["subject_name"] == "Neues Motiv"

        single = client.get(f"/locations/{standard_location_id}").json()
        assert single["subject_name"] == "Neues Motiv"

    def test_description_may_stay_empty(self, client, host_headers, standard_location_id):
        """Negativ-Kontrolle: description/special_notes sind bewusst NICHT Teil der
        neuen Pflichtprüfung (dürfen legitim leer sein, siehe Ticket-Scope)."""
        r = client.patch(
            f"/locations/{standard_location_id}",
            json={"description": ""},
            headers=host_headers,
        )
        assert r.status_code == 200, r.text
        assert r.json()["updated"]["description"] == ""


# ---------------------------------------------------------------------------
# AK3 — Diagnose-Logging: tritt zur Laufzeit trotzdem eine Location ohne
# Motivnamen auf (z.B. Altdaten), wird das beim nächsten Titel-Bau-Aufruf mit
# Location-Kennung + Event-Typ auf INFO-Level geloggt.
# ---------------------------------------------------------------------------

class TestDiagnoseLoggingImTitelFallback:

    def test_fallback_for_unresolvable_location_id_logs_id_and_event_type(self, client, caplog):
        """Nicht auflösbare location_id (kein Treffer in LOCATIONS) — bereits vor
        BUG-95 der bestehende Fallback-Fall, jetzt zusätzlich geloggt."""
        import main

        with caplog.at_level(logging.INFO, logger="main"):
            title = main._build_opportunity_title("Himmelsröte", "nicht_existente_location_xyz")

        assert title == "Himmelsröte"  # unveränderter Fallback-Titel (kein Verhaltensbruch)
        matches = [rec for rec in caplog.records if "BUG-95" in rec.getMessage()]
        assert matches, f"Erwarte BUG-95-Diagnose-Logzeile, gefunden: {[r.getMessage() for r in caplog.records]}"
        msg = matches[0].getMessage()
        assert "nicht_existente_location_xyz" in msg
        assert "Himmelsröte" in msg
        assert matches[0].levelno == logging.INFO

    def test_fallback_for_location_with_empty_subject_name_logs_id_and_event_type(self, client, caplog):
        """Faithfulle Nachbildung des Ticket-Szenarios: eine tatsächlich existierende
        Location, deren subject_name (z.B. durch den in Teil 1 gefixten Editier-Weg
        VOR dem Fix, oder durch Altdaten) leer ist."""
        import main
        from data.locations import PhotoLocation, LocationCategory

        loc_id = f"standard_test_bug95_emptyname_{uuid.uuid4().hex[:8]}"
        broken_loc = PhotoLocation(
            id=loc_id, name="BUG-95-Test-Location (leerer Motivname)",
            description="Testort für test_bug95.py",
            category=LocationCategory.WASSER,
            observer_lat=52.5, observer_lon=13.4,
            subject_lat=52.51, subject_lon=13.41, subject_name="",
            difficulty=2,
        )
        main.LOCATIONS.append(broken_loc)
        try:
            with caplog.at_level(logging.INFO, logger="main"):
                title = main._build_opportunity_title("Goldene Wolken", loc_id)

            assert title == "Goldene Wolken"
            matches = [rec for rec in caplog.records if "BUG-95" in rec.getMessage()]
            assert matches, f"Erwarte BUG-95-Diagnose-Logzeile, gefunden: {[r.getMessage() for r in caplog.records]}"
            msg = matches[0].getMessage()
            assert loc_id in msg
            assert "Goldene Wolken" in msg
        finally:
            main.LOCATIONS[:] = [l for l in main.LOCATIONS if l.id != loc_id]

    def test_no_log_for_normal_call_with_valid_subject_name(self, client, caplog, standard_location_id):
        """Pre-Mortem-Gegenmaßnahme (Ticket): NUR im Fallback-Zweig loggen, kein
        Rauschen bei jedem normalen Aufruf mit korrekt gesetztem Motivnamen."""
        import main

        with caplog.at_level(logging.INFO, logger="main"):
            title = main._build_opportunity_title("Rote Wolken", standard_location_id)

        assert title == "Rote Wolken über Testmotiv"
        matches = [rec for rec in caplog.records if "BUG-95" in rec.getMessage()]
        assert not matches, f"Erwarte KEINE BUG-95-Logzeile beim Normalfall, gefunden: {[r.getMessage() for r in matches]}"
