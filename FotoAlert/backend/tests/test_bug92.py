"""BUG-92 — Kalender zeigt nicht denselben Terminbestand wie der Feed.

Ticket: BACKLOG.md ### BUG-92. Root Cause: Der Feed filtert Foto-Chancen effektiv ab
Score 0.35 (main.get_opportunities Default), waehrend beide Kalender-Pfade bislang
0.40 verlangten:
- Live-On-Demand-Pfad (main._compute_location_month/_compute_month_all_locations/
  get_calendar, aktiv bei FOTOALERT_ONDEMAND=1)
- Hintergrund-Batch-Pfad (precompute.py _compute_calendar_for_location, schreibt
  main._calendar_cache)

Termine mit Score in [0.35, 0.40) waren dadurch im Feed sichtbar, im Kalender aber
nicht. Fix (Option A, Weg-Gate-Entscheidung, Zielwert 0.35): alle vier bekannten
Kalender-Fundstellen auf 0.35 angeglichen:
1. precompute.py _compute_calendar_for_location(): find_opportunities(..., min_score=0.35)
2. main.py _compute_month_all_locations() Parameter-Default 0.35
3. main.py get_calendar() Parameter-Default min_score 0.35
4. main.py get_calendar() Fallback-Vergleichsliteral `if min_score != 0.35`

Diese Tests pruefen NICHT die astronomische Berechnung selbst (an anderer Stelle
abgedeckt, siehe test_astronomy_regression.py/test_ephemeris_engine.py) — sie pruefen
die Schwellenwert-KONSISTENZ zwischen Feed- und Kalender-Filterlogik. Die interne
Astronomie-Berechnung (find_opportunities/find_opportunities_multi_day) wird dabei
durch einen Fake ersetzt, der sich exakt wie der echte Vertrag verhaelt: Kandidaten
werden nur zurueckgegeben, wenn overall_score >= dem uebergebenen min_score-Parameter
ist (Muster wie test_task86.py TestCalendarCacheNormalizationAndSize). So wird echt
geprueft, WELCHER Schwellenwert an welcher Stelle ankommt, ohne Skyfield/Netzwerk.

Python-3.9-kompatibel (kein `X | None`).
"""
from __future__ import annotations

import asyncio
from datetime import date, datetime, timedelta, timezone

import pytest


# Score im Luecken-Bereich [0.35, 0.40) — vorher vom Kalender faelschlich ausgeblendet.
_SCORE_IN_GAP = 0.37
# Score unterhalb der NEUEN Schwelle — muss weiterhin ueberall ausgeblendet bleiben (AK-4).
_SCORE_BELOW_THRESHOLD = 0.30

_TEST_LOCATION_ID = "berliner_dom_spree"  # echte, bestehende Location (data/locations.py)


def _synthetic_event(score: float, location_id: str = _TEST_LOCATION_ID) -> dict:
    """Minimaler, selbst-angelegter Event-Dict (Pattern 12 aus fotoalert-impl: keine
    fremde Fixture-ID, alles hier selbst erzeugt) mit frei waehlbarem overall_score.
    Enthaelt bewusst kein "composition_analysis" -> _passes_alignment_filter()
    (precompute.py) laesst den Event automatisch passieren (kein Alignment-Datensatz
    vorhanden -> True), der Test bleibt so auf die Score-Schwelle fokussiert."""
    now = datetime.now(timezone.utc) + timedelta(hours=2)
    return {
        "id": f"bug92-test-{score}-{location_id}",
        "location_id": location_id,
        "location_name": "BUG-92 Test-Location",
        "event_type": "sunset",
        "title": "BUG-92 Testtermin",
        "description": "",
        "shoot_time": now.isoformat(),
        "shoot_window_start": now.isoformat(),
        "shoot_window_end": (now + timedelta(minutes=30)).isoformat(),
        "overall_score": score,
        "astronomy_score": score,
        "weather_score": 1.0,
        "location_score": 1.0,
        "alert_priority": 1,
        "camera_hints": [],
    }


# ---------------------------------------------------------------------------
# Test 1 — Score in [0.35, 0.40) wird jetzt sowohl vom Feed- als auch von BEIDEN
# Kalender-Berechnungspfaden (On-Demand-Default + Hintergrund-Batch) erfasst.
# ---------------------------------------------------------------------------

@pytest.mark.offline
@pytest.mark.regression
class TestGapScoreCapturedByFeedAndCalendarPaths:
    def test_feed_default_threshold_accepts_gap_score(self, client, monkeypatch):
        """Feed-Pfad: main._filter_feed() mit dem Feed-Default (0.35) zeigt einen
        Termin mit Score 0.37."""
        import main

        ev = _synthetic_event(_SCORE_IN_GAP)
        monkeypatch.setattr(main, "_feed_cache", [ev])
        result = main._filter_feed(0.35, None, None, 14, None)
        assert any(e["id"] == ev["id"] for e in result), (
            "Feed-Default (0.35) muss einen Termin mit Score 0.37 zeigen."
        )

    def test_ondemand_calendar_default_accepts_gap_score(self, client, monkeypatch):
        """Live-On-Demand-Pfad (main._compute_month_all_locations OHNE explizites
        min_score) muss jetzt den NEUEN Default 0.35 verwenden statt 0.40 — sonst
        waere der 0.37-Termin weiterhin ausgeblendet."""
        import main

        async def _fake_compute_location_month(loc, year, month, min_score):
            ev = _synthetic_event(_SCORE_IN_GAP, location_id=loc.id)
            return [ev] if ev["overall_score"] >= min_score else []

        monkeypatch.setattr(main, "_compute_location_month", _fake_compute_location_month)
        main._ondemand_month_cache.clear()
        try:
            events = asyncio.run(main._compute_month_all_locations(2033, 1))
        finally:
            main._ondemand_month_cache.clear()
        assert any(e["overall_score"] == _SCORE_IN_GAP for e in events), (
            "_compute_month_all_locations() ohne explizites min_score muss den neuen "
            "Default 0.35 nutzen und den 0.37-Termin zeigen (vorher 0.40 haette ihn "
            "ausgeblendet)."
        )

    def test_background_batch_precompute_uses_035_and_accepts_gap_score(self, monkeypatch):
        """Hintergrund-Batch-Pfad: precompute._compute_calendar_for_location() ruft
        find_opportunities() jetzt mit min_score=0.35 auf (vorher 0.40) — verifiziert
        ueber einen Fake, der wie die echte Funktion anhand des uebergebenen
        min_score-Parameters filtert, PLUS eine Aufzeichnung des tatsaechlich
        uebergebenen Werts."""
        import precompute
        from data.locations import LOCATIONS

        loc = LOCATIONS[0]
        captured_min_scores = []

        async def _fake_find_opportunities(loc_, d, forecast=None, min_score=0.0,
                                            astronomy_only=False):
            captured_min_scores.append(min_score)
            ev = _synthetic_event(_SCORE_IN_GAP, location_id=loc_.id)
            return [ev] if ev["overall_score"] >= min_score else []

        monkeypatch.setattr(precompute, "find_opportunities", _fake_find_opportunities)
        # Fakes sind bereits fertige Dicts -> _serialize() unveraendert durchreichen.
        monkeypatch.setattr(precompute, "_serialize", lambda o: o)

        today_str = date.today().isoformat()
        invalidate, dates_needed, new_events, meta_entry = asyncio.run(
            precompute._compute_calendar_for_location(loc, {today_str}, {}, 0, 1)
        )

        assert captured_min_scores == [0.35], (
            f"_compute_calendar_for_location() muss find_opportunities() mit "
            f"min_score=0.35 aufrufen (Fundstelle 1) — tatsaechlich uebergeben: "
            f"{captured_min_scores}"
        )
        assert any(e["overall_score"] == _SCORE_IN_GAP for e in new_events), (
            "Der Hintergrund-Batch-Pfad muss einen Termin mit Score 0.37 jetzt in "
            "new_events_for_loc aufnehmen."
        )


# ---------------------------------------------------------------------------
# Test 2 — get_calendar() mit FOTOALERT_ONDEMAND=1 liefert fuer den Luecken-Score
# dasselbe Ergebnis wie get_opportunities() (Feed). Echter Aufrufpfad: TestClient
# gegen die echten HTTP-Endpunkte /opportunities und /calendar.
# ---------------------------------------------------------------------------

@pytest.mark.api
@pytest.mark.regression
class TestOnDemandCalendarConsistentWithFeed:
    def test_get_calendar_ondemand_matches_get_opportunities_for_gap_score(
        self, client, monkeypatch
    ):
        import main

        monkeypatch.setenv("FOTOALERT_ONDEMAND", "1")
        ev = _synthetic_event(_SCORE_IN_GAP)
        monkeypatch.setattr(main, "_feed_cache", [ev])

        async def _fake_compute_location_month(loc, year, month, min_score):
            e = _synthetic_event(_SCORE_IN_GAP, location_id=loc.id)
            return [e] if e["overall_score"] >= min_score else []

        monkeypatch.setattr(main, "_compute_location_month", _fake_compute_location_month)

        feed_resp = client.get(
            "/opportunities", params={"location_id": _TEST_LOCATION_ID}
        )
        assert feed_resp.status_code == 200, feed_resp.text
        feed_events = feed_resp.json()

        cal_resp = client.get(
            "/calendar",
            params={"location_id": _TEST_LOCATION_ID, "month": 5, "year": 2033},
        )
        assert cal_resp.status_code == 200, cal_resp.text
        cal_body = cal_resp.json()
        assert cal_body["on_demand"] is True

        feed_has_event = any(e["overall_score"] == _SCORE_IN_GAP for e in feed_events)
        cal_has_event = any(
            e["overall_score"] == _SCORE_IN_GAP for e in cal_body["events"]
        )
        assert feed_has_event, "Vorbedingung: Feed muss den 0.37-Termin zeigen."
        assert cal_has_event, (
            "Kalender (On-Demand-Pfad, FOTOALERT_ONDEMAND=1) muss denselben Termin "
            "mit Score 0.37 zeigen wie der Feed — vorher fehlte er wegen min_score=0.40."
        )


# ---------------------------------------------------------------------------
# Test 3 — Derselbe Konsistenz-Test OHNE FOTOALERT_ONDEMAND (Fallback-/Batch-Pfad
# ueber main._calendar_cache, so wie ihn der periodische Hintergrund-Job befuellt).
# ---------------------------------------------------------------------------

@pytest.mark.api
@pytest.mark.regression
class TestBatchCalendarConsistentWithFeedWithoutOnDemand:
    def test_get_calendar_fallback_matches_get_opportunities_for_gap_score(
        self, client, monkeypatch
    ):
        import main

        monkeypatch.delenv("FOTOALERT_ONDEMAND", raising=False)
        ev = _synthetic_event(_SCORE_IN_GAP)
        monkeypatch.setattr(main, "_feed_cache", [ev])
        # _calendar_cache so befuellt, wie precompute.py ihn nach dem Fix (Fundstelle 1,
        # min_score=0.35) tatsaechlich schreiben wuerde: der 0.37-Termin ist bereits
        # enthalten (kein separates Re-Filtern in get_calendar() bei Default-min_score,
        # siehe Fundstelle 4 — die eigentliche Schwelle wird beim Schreiben angewendet).
        monkeypatch.setattr(main, "_calendar_cache", [ev])
        monkeypatch.setattr(main, "_precompute_running", False)

        feed_resp = client.get(
            "/opportunities", params={"location_id": _TEST_LOCATION_ID}
        )
        assert feed_resp.status_code == 200, feed_resp.text
        feed_events = feed_resp.json()

        cal_resp = client.get("/calendar", params={"location_id": _TEST_LOCATION_ID})
        assert cal_resp.status_code == 200, cal_resp.text
        cal_body = cal_resp.json()

        feed_has_event = any(e["overall_score"] == _SCORE_IN_GAP for e in feed_events)
        cal_has_event = any(
            e["overall_score"] == _SCORE_IN_GAP for e in cal_body["events"]
        )
        assert feed_has_event, "Vorbedingung: Feed muss den 0.37-Termin zeigen."
        assert cal_has_event, (
            "Kalender (Fallback-/Batch-Pfad, KEIN FOTOALERT_ONDEMAND) muss denselben "
            "Termin mit Score 0.37 zeigen wie der Feed."
        )


# ---------------------------------------------------------------------------
# Test 4 — Regression (AK-4): Termine UNTERHALB der neuen Schwelle (Score 0.30)
# bleiben weiterhin ausgeschlossen — Feed, On-Demand-Pfad UND Hintergrund-Batch-Pfad.
# ---------------------------------------------------------------------------

@pytest.mark.api
@pytest.mark.regression
class TestBelowThresholdStillExcluded:
    def test_feed_excludes_score_below_threshold(self, client, monkeypatch):
        import main

        ev = _synthetic_event(_SCORE_BELOW_THRESHOLD)
        monkeypatch.setattr(main, "_feed_cache", [ev])
        resp = client.get("/opportunities", params={"location_id": _TEST_LOCATION_ID})
        assert resp.status_code == 200, resp.text
        assert not any(e["overall_score"] == _SCORE_BELOW_THRESHOLD for e in resp.json()), (
            "Ein Termin mit Score 0.30 (< 0.35) darf im Feed weiterhin NICHT erscheinen."
        )

    def test_ondemand_calendar_excludes_score_below_threshold(self, client, monkeypatch):
        import main

        monkeypatch.setenv("FOTOALERT_ONDEMAND", "1")

        async def _fake_compute_location_month(loc, year, month, min_score):
            e = _synthetic_event(_SCORE_BELOW_THRESHOLD, location_id=loc.id)
            return [e] if e["overall_score"] >= min_score else []

        monkeypatch.setattr(main, "_compute_location_month", _fake_compute_location_month)
        resp = client.get(
            "/calendar",
            params={"location_id": _TEST_LOCATION_ID, "month": 6, "year": 2033},
        )
        assert resp.status_code == 200, resp.text
        events = resp.json()["events"]
        assert not any(e["overall_score"] == _SCORE_BELOW_THRESHOLD for e in events), (
            "Ein Termin mit Score 0.30 (< 0.35) darf im On-Demand-Kalenderpfad "
            "weiterhin NICHT erscheinen."
        )

    def test_background_batch_precompute_excludes_score_below_threshold(self, monkeypatch):
        import precompute
        from data.locations import LOCATIONS

        loc = LOCATIONS[0]

        async def _fake_find_opportunities(loc_, d, forecast=None, min_score=0.0,
                                            astronomy_only=False):
            e = _synthetic_event(_SCORE_BELOW_THRESHOLD, location_id=loc_.id)
            return [e] if e["overall_score"] >= min_score else []

        monkeypatch.setattr(precompute, "find_opportunities", _fake_find_opportunities)
        monkeypatch.setattr(precompute, "_serialize", lambda o: o)

        today_str = date.today().isoformat()
        _invalidate, _dates_needed, new_events, _meta_entry = asyncio.run(
            precompute._compute_calendar_for_location(loc, {today_str}, {}, 0, 1)
        )
        assert not any(
            e["overall_score"] == _SCORE_BELOW_THRESHOLD for e in new_events
        ), (
            "Der Hintergrund-Batch-Pfad darf einen Termin mit Score 0.30 weiterhin "
            "NICHT in new_events_for_loc aufnehmen."
        )


# ---------------------------------------------------------------------------
# Test 5 (Nachbesserungsrunde 2026-07-31, nach unabhaengiger Verifikation) —
# Fallback-Vergleichsliteral `if min_score != 0.35:` (main.py get_calendar(),
# Fundstelle 4) wird durch einen EXPLIZITEN, vom neuen Default (0.35) abweichenden
# min_score-Parameter tatsaechlich durchlaufen. Alle bisherigen Fallback-Tests
# (Test 3 oben) riefen /calendar nur mit dem impliziten Default min_score=0.35 auf
# -> der Vergleich `min_score != 0.35` war dabei immer False, das serverseitige
# Nachfiltern lief nie. Dieser Test ruft get_calendar() direkt mit einem expliziten
# min_score=0.40 auf und prueft, dass ein gecachter Termin mit Score 0.37 (der beim
# impliziten Default 0.35 durchgehen wuerde) dann korrekt herausgefiltert wird.
# Eine Regression genau an dieser Zeile (z.B. versehentliches Zuruecksetzen des
# Vergleichswerts auf 0.40, oder ein Tippfehler im Literal) wuerde diesen Test rot
# werden lassen: bliebe der Vergleich bei `!= 0.40`, waere 0.40 != 0.40 False, das
# Nachfiltern liefe nicht, und der 0.37-Termin bliebe faelschlich sichtbar.
# ---------------------------------------------------------------------------

@pytest.mark.offline
@pytest.mark.regression
class TestFallbackExplicitMinScoreOverridesDefault:
    def test_get_calendar_fallback_explicit_min_score_filters_gap_score(self, monkeypatch):
        """Fallback-Pfad (main._calendar_cache, KEIN FOTOALERT_ONDEMAND), explizit
        angefordertes min_score=0.40: ein gecachter Termin mit Score 0.37 muss
        herausgefiltert werden (er wuerde beim impliziten Default 0.35 durchgehen).
        Exerziert damit gezielt die Vergleichszeile `if min_score != 0.35:` in
        main.py get_calendar() (Fundstelle 4), die von keinem der bestehenden Tests
        in dieser Datei mit einem vom Default abweichenden Wert aufgerufen wird."""
        import main

        monkeypatch.delenv("FOTOALERT_ONDEMAND", raising=False)
        ev = _synthetic_event(_SCORE_IN_GAP)
        monkeypatch.setattr(main, "_calendar_cache", [ev])
        monkeypatch.setattr(main, "_precompute_running", False)

        result = asyncio.run(
            main.get_calendar(location_id=_TEST_LOCATION_ID, min_score=0.40)
        )

        assert result["status"] == "ok", result
        assert not any(
            e["overall_score"] == _SCORE_IN_GAP for e in result["events"]
        ), (
            "Bei explizit angefordertem min_score=0.40 muss ein gecachter Termin mit "
            "Score 0.37 herausgefiltert werden (`if min_score != 0.35:`-Zweig in "
            "main.py get_calendar(), Fundstelle 4). Bliebe er sichtbar, liefe die "
            "Vergleichszeile entweder gar nicht durch (z.B. Reset des Literals auf "
            "0.40) oder falsch."
        )
