"""TASK-67 Etappe 2 — PRODUCT.md "Pflicht-Regression Feed" (Abschnitt 3), Teil-Automatisierung.

Deckt die Punkte aus PRODUCT.md Abschnitt 3 ("Pflicht-Regression Feed") ab, die sich laut
Regel 1 (Example Mapping, TASK-67-Analyse) rein über Daten/Zustände der `/opportunities`-
Filterlogik (`main._filter_feed` / `main._dedup_best_per_day`) prüfen lassen — ohne echte
Browser-Klick-Interaktion:

  - "Mindestens 1 Karte sichtbar (bei min_score 0.2)"          -> test_min_score_filter_*
  - "Karten nicht doppelt vorhanden"                            -> test_no_duplicate_events_*
  - "Feed enthält sowohl Goldene Stunde als auch Blaue Stunde   -> test_round_robin_*
     (nicht nur Mond-Events) — Round-Robin-Cap (BUG-48)"

Kein Overlap mit bestehenden Dateien: test_task67_backend_regression.py (Etappe 1) prüft nur,
dass /opportunities überhaupt eine Liste liefert (Struktur-Smoke-Test), nicht die interne
Filter-/Dedup-/Round-Robin-Logik selbst. Diese Logik (main._filter_feed) wurde bisher von
keiner bestehenden Testdatei direkt geprüft (siehe Analyse-Grep vor dieser Implementierung:
kein Treffer für `_filter_feed`/`round_robin`/`dedup_best_per_day` in backend/tests/*.py
außerhalb der Playwright-Dateien).

NICHT Teil dieser Etappe (siehe PRODUCT.md-Referenzen statt Duplikat):
  - "Score-Ring korrekt" — optische Beurteilung eines gefüllten Kreisrings, bleibt laut
    Regel 2 explizit manuell (das ist sogar das Negativ-Beispiel im Ticket selbst).
  - "Chance antippen -> Detail-Sheet öffnet" / "Overlay antippen -> Sheet schließt" /
    "Filter-Sheet öffnet und schließt" / "Routine-Events-Filter" / "Filter-Chips
    Mondaufgang/Monduntergang filtern Feed korrekt" — echte Klick-/DOM-Interaktion,
    Etappe 3 (Playwright).
  - "Mondaufgang-/Monduntergang-Events erscheinen als eigenständige Karten" — bereits
    automatisiert in test_us79_moon_rise_set.py (Event-Erzeugung + Serialisierung).
  - "Feed-Karten zeigen Sichtachsen-Check-Pille" / "Fehlen Höhen-/Gebäudedaten: Pille zeigt
    'Nicht geprüft', niemals 'Frei'" — die zugrunde liegende Daten-Garantie (sightline_status
    niemals stillschweigend 'frei' bei fehlenden Daten) ist bereits vollständig in
    test_us09_sightline.py automatisiert; die Pillen-Darstellung selbst ist UI (Etappe 3).

Python-3.9-kompatibel (kein `X | None`).
"""
from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import main  # noqa: E402

pytestmark = [pytest.mark.api, pytest.mark.regression]


def _fake_event(
    event_type: str,
    score: float,
    location_id: str = "loc-a",
    hours_from_now: float = 2.0,
    day_offset: int = 0,
) -> dict:
    """Baut ein minimales Feed-Event-Dict, wie main._filter_feed es erwartet.

    Nur die von _filter_feed/_dedup_best_per_day/Round-Robin gelesenen Felder werden
    gesetzt (shoot_time, shoot_window_end, overall_score, event_type, alert_priority,
    location_id) — reicht aus, um die reine Filterlogik ohne echte Astronomie-Berechnung
    zu testen (Pattern 12: eigenständig, keine externen Fixtures/IDs nötig).
    """
    now = datetime.now(timezone.utc)
    shoot_dt = now + timedelta(hours=hours_from_now, days=day_offset)
    return {
        "id": f"{location_id}-{event_type}-{shoot_dt.isoformat()}",
        "location_id": location_id,
        "event_type": event_type,
        "overall_score": score,
        "alert_priority": 1,
        "shoot_time": shoot_dt.isoformat(),
        "shoot_window_end": (shoot_dt + timedelta(minutes=30)).isoformat(),
    }


@pytest.fixture
def restore_feed_cache(monkeypatch):
    """Isoliert main._feed_cache für die Dauer eines Tests (Pattern 12: kein Zugriff auf
    echte, geteilte Cache-Daten; monkeypatch stellt den Ursprungszustand danach automatisch
    wieder her)."""
    def _set(events):
        monkeypatch.setattr(main, "_feed_cache", events, raising=False)
    return _set


# ---------------------------------------------------------------------------
# "Mindestens 1 Karte sichtbar (bei min_score 0.2)"
# ---------------------------------------------------------------------------

class TestMinScoreFilterYieldsAtLeastOneCard:
    def test_min_score_02_keeps_qualifying_events(self, restore_feed_cache):
        events = [
            _fake_event("Goldene Stunde Morgen", 0.1),   # unter Schwelle, fällt raus
            _fake_event("Blaue Stunde Abend", 0.35),      # über Schwelle, bleibt
        ]
        restore_feed_cache(events)
        result = main._filter_feed(min_score=0.2, event_type=None, priority=None,
                                    days=14, location_id=None)
        assert len(result) >= 1
        assert all(e["overall_score"] >= 0.2 for e in result)

    def test_min_score_02_excludes_events_below_threshold(self, restore_feed_cache):
        events = [_fake_event("Goldene Stunde Morgen", 0.05)]
        restore_feed_cache(events)
        result = main._filter_feed(min_score=0.2, event_type=None, priority=None,
                                    days=14, location_id=None)
        assert result == []


# ---------------------------------------------------------------------------
# "Karten nicht doppelt vorhanden"
# ---------------------------------------------------------------------------

class TestNoDuplicateEvents:
    def test_dedup_best_per_day_keeps_only_highest_score(self):
        day_events = [
            _fake_event("Goldene Stunde Morgen", 0.4, location_id="loc-x", hours_from_now=1.0),
            _fake_event("Goldene Stunde Morgen", 0.9, location_id="loc-x", hours_from_now=1.2),
        ]
        result = main._dedup_best_per_day(day_events)
        assert len(result) == 1
        assert result[0]["overall_score"] == 0.9

    def test_dedup_keeps_events_from_different_locations_or_types(self):
        events = [
            _fake_event("Goldene Stunde Morgen", 0.4, location_id="loc-x"),
            _fake_event("Goldene Stunde Morgen", 0.6, location_id="loc-y"),
            _fake_event("Blaue Stunde Abend", 0.5, location_id="loc-x"),
        ]
        result = main._dedup_best_per_day(events)
        assert len(result) == 3

    def test_filter_feed_end_to_end_has_no_duplicate_ids_per_location_type_day(
        self, restore_feed_cache
    ):
        events = [
            _fake_event("Goldene Stunde Morgen", 0.5, location_id="loc-z", hours_from_now=1.0),
            _fake_event("Goldene Stunde Morgen", 0.8, location_id="loc-z", hours_from_now=1.5),
        ]
        restore_feed_cache(events)
        result = main._filter_feed(min_score=0.2, event_type=None, priority=None,
                                    days=14, location_id=None)
        keys = [f"{e['location_id']}|{e['event_type']}|{e['shoot_time'][:10]}" for e in result]
        assert len(keys) == len(set(keys)), "Feed enthält doppelte Karten für dieselbe Location/Typ/Tag-Kombination"


# ---------------------------------------------------------------------------
# "Feed enthält sowohl Goldene Stunde als auch Blaue Stunde (nicht nur Mond-Events)
#  — Round-Robin-Cap (BUG-48)"
# ---------------------------------------------------------------------------

class TestRoundRobinCapKeepsAllEventTypesRepresented:
    def test_dominant_type_does_not_crowd_out_rare_type(self, restore_feed_cache):
        """BUG-48-Kernszenario: Ein Event-Typ hat sehr viele hochwertige Events (mehr als
        der interne Cap von main._filter_feed erlaubt), ein anderer Typ nur wenige.
        Ohne Round-Robin würde der :500-Cap ausschließlich vom dominanten Typ gefüllt."""
        # hours_from_now bleibt bewusst < 336h (14 Tage), sonst greift der Zeit-Cutoff
        # von _filter_feed schon vor dem Round-Robin und verfälscht den Test.
        many_golden = [
            _fake_event("Goldene Stunde Morgen", 0.9, location_id=f"loc-{i}",
                        hours_from_now=1.0 + (i % 300))
            for i in range(600)
        ]
        few_blue = [
            _fake_event("Blaue Stunde Abend", 0.85, location_id=f"blue-{i}",
                        hours_from_now=1.0 + i)
            for i in range(5)
        ]
        restore_feed_cache(many_golden + few_blue)

        result = main._filter_feed(min_score=0.1, event_type=None, priority=None,
                                    days=14, location_id=None)

        types_present = {e["event_type"] for e in result}
        assert "Goldene Stunde Morgen" in types_present
        assert "Blaue Stunde Abend" in types_present, (
            "Round-Robin-Cap (BUG-48) verletzt: der seltenere Event-Typ wurde vom "
            "dominanten Typ komplett aus dem gecappten Ergebnis verdrängt"
        )

    def test_result_stays_within_cap_of_500(self, restore_feed_cache):
        many_golden = [
            _fake_event("Goldene Stunde Morgen", 0.9, location_id=f"loc-{i}",
                        hours_from_now=1.0 + (i % 300))
            for i in range(700)
        ]
        restore_feed_cache(many_golden)
        result = main._filter_feed(min_score=0.1, event_type=None, priority=None,
                                    days=14, location_id=None)
        assert len(result) <= 500
