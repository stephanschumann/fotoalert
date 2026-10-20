"""BUG-110 -- Jahreskalender zeigt fuer den gesamten aktuellen Monat keine Eintraege.

Ticket: BACKLOG.md ### BUG-110.

Code-verifizierter Befund (Pre-Mortem, fotoalert-analyze, 2026-08-25):
Die im Ticket geaeusserte Praemisse ("der fuer die Kalenderberechnung zustaendige
Hintergrund-Job ist fuer den aktuellen Monat noch nie gelaufen") trifft auf den in
Produktion tatsaechlich aktiven Code-Pfad NICHT zu -- siehe Pre-Mortem-Abschnitt im
Ticket. `deploy/fotoalert.service` setzt FOTOALERT_ONDEMAND=1; bei aktivem Flag UND
gesetzten month+year-Parametern (das Frontend sendet beide IMMER, web/index.html
CalendarView.loadMonth()) liest main.get_calendar() NIE aus dem Batch-Cache
(_calendar_cache/precompute.py), sondern berechnet live ueber
main._compute_month_all_locations()/_compute_location_month() (Window-Engine,
calculations/window_engine.py). Der "calendar"-Job in /job-status bleibt in diesem
Modus by design "idle"/last_run=null -- das ist KEIN Fehlersignal.

Diese Tests decken stattdessen den waehrend der Code-Verifikation gefundenen,
tatsaechlich verifizierten Architektur-Defekt ab: main._compute_month_all_locations()
(main.py ~Z. 3357-3379) cached JEDES Ergebnis bedingungslos in
main._ondemand_month_cache -- auch ein Ergebnis, das nur deshalb leer ist, weil fuer
JEDE Location eine Exception geworfen und (main.py, per-Location try/except) nur
geloggt, nicht weitergereicht wurde. Ein einmal so entstandenes leeres Ergebnis fuer
einen Monat bleibt fuer die gesamte Laufzeit des Prozesses gecacht -- der bestehende
Admin-Endpoint POST /refresh-calendar wirkt NICHT dagegen, da er ausschliesslich den
(im On-Demand-Betrieb ungenutzten) Batch-Pfad neu anstoesst.

Root Cause des konkreten Produktions-Vorfalls (2026-08-25) ist NICHT abschliessend
bestaetigt (kein Log-Zugriff aus der Analyse-Sandbox moeglich, siehe Ticket-Frage 1)
-- diese Tests pruefen die Architektur-Schwachstelle unabhaengig vom genauen Ausloeser.

Astronomie-Berechnung wird komplett gefaked (main._compute_location_month), Pattern
aus test_bug92.py -- kein Skyfield/Netzwerk noetig.

ROT-NACHWEIS-HINWEIS (Transparenz, siehe Ticket-Handover): Dieser Test konnte in der
Analyse-Sandbox NICHT tatsaechlich ausgefuehrt werden (backend/venv/bin/python ist
ein toter Symlink auf einen macOS-Homebrew-Pfad, der aus der Sandbox-VM heraus nicht
existiert; kein Internetzugang in der Sandbox-VM fuer eine frische Installation).
Der erwartete Fehlschlag von test_all_locations_failing_then_recovering_still_returns_events_on_next_call
ist ausschliesslich durch Code-Lektuere (main.py Z. 3367-3369) hergeleitet, NICHT
durch einen echten pytest-Lauf bestaetigt. Bitte vor Implementierungsstart einmal
lokal echt ausfuehren: `cd backend && venv/bin/python -m pytest tests/test_bug110.py -v`
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone

import pytest

_TEST_YEAR = 2026
_TEST_MONTH = 8  # August -- der im Ticket beschriebene, betroffene aktuelle Monat


def _synthetic_event(location_id: str, score: float = 0.6) -> dict:
    now = datetime(_TEST_YEAR, _TEST_MONTH, 15, 19, 0, tzinfo=timezone.utc)
    return {
        "id": f"bug110-test-{location_id}",
        "location_id": location_id,
        "location_name": "BUG-110 Test-Location",
        "event_type": "golden_hour_evening",
        "title": "BUG-110 Testtermin",
        "description": "",
        "shoot_time": now.isoformat(),
        "shoot_window_start": now.isoformat(),
        "shoot_window_end": (now + timedelta(minutes=30)).isoformat(),
        "overall_score": score,
        "astronomy_score": score,
        "weather_score": 0.0,
        "location_score": 1.0,
        "alert_priority": 0,
        "camera_hints": [],
    }


@pytest.fixture(autouse=True)
def _clear_ondemand_cache():
    """Isoliert jeden Test vom In-Memory-Cache (main._ondemand_month_cache ist ein
    Modul-globaler OrderedDict, der sonst zwischen Testfaellen 'nachwirkt')."""
    import main
    main._ondemand_month_cache.clear()
    yield
    main._ondemand_month_cache.clear()


@pytest.mark.offline
@pytest.mark.regression
class TestEmptyResultIsNotPermanentlyCached:
    def test_all_locations_failing_then_recovering_still_returns_events_on_next_call(self, monkeypatch):
        """AK-1 / Kernszenario: Beim ERSTEN Aufruf schlaegt die Berechnung fuer JEDE
        Location fehl (z.B. durch einen transienten Fehler beim Server-Start-Prewarm,
        main._prewarm_calendar()) -> aktuelles main.py cached dafuer bedingungslos
        eine leere Liste unter dem Monats-Schluessel.

        Ist die zugrunde liegende Ursache beim NAECHSTEN Aufruf nicht mehr vorhanden
        (Fehler war transient), MUSS ein erneuter Request wieder echte Events liefern
        -- nicht die inzwischen veraltete leere Liste aus main._ondemand_month_cache.

        Aktuell (vor dem Fix) FAILT dieser Test voraussichtlich: main.py cached
        unbedingt (main.py Z. 3367-3369: `if key in _ondemand_month_cache: return
        _ondemand_month_cache[key]` -- unabhaengig davon, ob der Eintrag leer ist)."""
        import main

        async def _always_failing(loc, year, month, min_score):
            raise RuntimeError("BUG-110-Testfehler: simulierter transienter Ausfall")

        async def _working(loc, year, month, min_score):
            return [_synthetic_event(loc.id)]

        # 1. Aufruf: alle Locations werfen -> Ergebnis ist leer (main.py faengt die
        #    Exception pro Location, loggt sie nur -> events bleibt [])
        monkeypatch.setattr(main, "_compute_location_month", _always_failing)
        first = asyncio.run(main._compute_month_all_locations(_TEST_YEAR, _TEST_MONTH))
        assert first == [], (
            "Erwartetes Ausgangsszenario: bei ausnahmslos fehlschlagenden Locations "
            "ist das ERSTE Ergebnis leer (Exceptions werden aktuell nur geloggt)."
        )

        # 2. Aufruf: derselbe Monat, aber die zugrunde liegende Ursache ist jetzt weg
        #    (Locations liefern wieder echte Events). OHNE main._ondemand_month_cache
        #    manuell zu leeren -- genau das passiert in Produktion zwischen zwei
        #    echten HTTP-Requests auch nicht automatisch.
        monkeypatch.setattr(main, "_compute_location_month", _working)
        second = asyncio.run(main._compute_month_all_locations(_TEST_YEAR, _TEST_MONTH))

        assert len(second) > 0, (
            "AK-1 verletzt: main._compute_month_all_locations() liefert fuer denselben "
            "Monat weiterhin die veraltete LEERE Liste aus main._ondemand_month_cache, "
            "obwohl die Ursache (fake) nicht mehr besteht -- der Jahreskalender bleibt "
            "damit dauerhaft leer, bis der Serverprozess neu gestartet wird."
        )

    def test_refresh_calendar_endpoint_has_no_effect_on_ondemand_cache(self):
        """AK-2 / Dokumentations-Regressionstest: haelt fest, dass POST
        /refresh-calendar (main.trigger_calendar_refresh) im On-Demand-Betrieb NICHT
        geeignet ist, einen vergifteten main._ondemand_month_cache-Eintrag zu
        reparieren -- er stoesst ausschliesslich main._run_precompute('calendar')
        an, was main._calendar_cache betrifft, nicht main._ondemand_month_cache.
        Dieser Test dokumentiert den IST-Zustand. Wird main.trigger_calendar_refresh()
        im Zuge des Fixes bewusst um eine _ondemand_month_cache-Invalidierung
        erweitert, bitte diesen Test bewusst mit aktualisieren, nicht nur gruen
        schalten lassen."""
        import inspect
        import main

        src = inspect.getsource(main.trigger_calendar_refresh)
        assert "_ondemand_month_cache" not in src, (
            "main.trigger_calendar_refresh() referenziert jetzt _ondemand_month_cache "
            "-- bitte pruefen ob das eine bewusste Fix-Entscheidung war und diesen "
            "Test entsprechend aktualisieren."
        )


@pytest.mark.offline
@pytest.mark.regression
class TestPartialLocationFailureDoesNotEmptyWholeMonth:
    def test_single_failing_location_does_not_suppress_other_locations_events(self, monkeypatch):
        """AK-3 / bestehendes, bereits korrektes Verhalten absichern: schlaegt NUR
        eine einzelne Location fehl, duerfen die Events der uebrigen Locations
        trotzdem im Monat erscheinen (main.py haelt die Fehlerbehandlung bereits
        pro Location, nicht pro Monat) -- dieser Test soll vor UND nach dem Fix
        gruen bleiben, grenzt aber den Bug bewusst von einem Totalausfall ab."""
        import main
        from data.locations import LOCATIONS

        assert len(LOCATIONS) >= 2, "Testannahme: mindestens 2 Locations vorhanden."
        failing_id = LOCATIONS[0].id

        async def _mixed(loc, year, month, min_score):
            if loc.id == failing_id:
                raise RuntimeError("BUG-110-Testfehler: eine einzelne Location faellt aus")
            return [_synthetic_event(loc.id)]

        monkeypatch.setattr(main, "_compute_location_month", _mixed)
        events = asyncio.run(main._compute_month_all_locations(_TEST_YEAR, _TEST_MONTH))

        assert any(e["location_id"] != failing_id for e in events), (
            "Eine einzelne fehlschlagende Location darf die Events der uebrigen "
            "Locations im Monat nicht unterdruecken."
        )
        assert all(e["location_id"] != failing_id for e in events), (
            "Die fehlschlagende Location selbst darf keine (halben/fehlerhaften) "
            "Events beisteuern."
        )
