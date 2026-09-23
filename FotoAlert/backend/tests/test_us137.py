"""US-137 — "Nächstes Sonnen-Alignment über 30 Tage hinaus" + lokaler Ereignistyp-Filter
im Abschnitt "Nächste Events" der Standort-Detailansicht.

Spec-Bezug (BACKLOG.md, Ticket US-137, "Gewählte Umsetzung (Option A, von Stephan
entschieden)"): der bereits bestehende, bisher ungenutzte On-Demand-Endpunkt `GET /plan`
(`backend/main.py`, stateless für beliebige Koordinaten, `astronomy_only=True`) wird
gehärtet:
  - Rate-Limit analog zum bestehenden Vorbild `POST /preview-alignment`
    (`_preview_alignment_limiter`, 20 Aufrufe/60s) — AK11.
  - Harte Tages-Obergrenze von 365 Tagen, analog zum Cap-Muster aus BUG-63
    (`days = min(req.days, 14)` bei `/preview-alignment`) — hier `min(days, 365)`.

Dieser Test deckt ausschließlich den Backend-Teil von US-137 ab (Frontend-Umbau von
`LocationDetail._loadEvents()` + lokaler Filter sind rein clientseitig, siehe
BACKLOG.md-Testplan). Getestet wird:
  1. Tages-Cap (`days = min(days, 365)`) — verhindert einen unbegrenzt wachsenden
     `/plan`-Aufruf (z.B. days=999999), analog zur BUG-63-Absicherung bei
     `/preview-alignment`.
  2. Rate-Limit (AK11) — wiederholte, schnelle Aufrufe von `/plan` werden serverseitig
     abgebremst (429 + Retry-After), analog zum bestehenden Schutz von
     `/preview-alignment`.
  3. Grundfunktion (AK1, backend-seitig prüfbar): `/plan` liefert tatsächlich Events
     jenseits des bisherigen 30-Tage-Feed-Horizonts, wenn `days` entsprechend groß
     gewählt wird — das ist die Voraussetzung dafür, dass das Frontend (nach dem
     Umbau von `_loadEvents()` auf `/plan?days=365`) das nächste tatsächlich
     zukünftige Alignment auch über 30 Tage hinaus anzeigen kann.

`elevation_difference_m` wird bei jedem `/plan`-Aufruf explizit als Query-Parameter
mitgegeben (wie im Frontend nach dem US-137-Umbau: die Location kennt ihren eigenen
Höhenunterschied bereits) — dadurch entfällt der Elevation-Provider-Netzwerkaufruf
komplett, alle Tests bleiben offline/deterministisch (kein `monkeypatch` auf
`data.elevation.provider` nötig, anders als in test_bug63.py).

Python-3.9-kompatibel (kein `X | None`).
"""
from __future__ import annotations

from datetime import date, timedelta

import pytest

pytestmark = [pytest.mark.offline, pytest.mark.regression]

# Babelsberg -> Belvedere (Pfingstberg): dasselbe Referenzbeispiel wie in
# test_bug63.py/test_bug66.py, bekannt dafür plausible Sonnen-/Mond-Geometrie zu
# liefern (kein Kandidat für "keine Events" mangels Motiv/Sichtachse).
_OBSERVER_LAT, _OBSERVER_LON = 52.3975, 13.0976
_SUBJECT_LAT, _SUBJECT_LON = 52.4158, 13.0688
_ELEVATION_DIFF_M = 50.0


def _plan_params(**overrides):
    params = {
        "observer_lat": _OBSERVER_LAT,
        "observer_lon": _OBSERVER_LON,
        "subject_lat": _SUBJECT_LAT,
        "subject_lon": _SUBJECT_LON,
        "subject_name": "Referenz-Motiv",
        "subject_height_m": 15.0,
        "subject_width_m": 10.0,
        "elevation_difference_m": _ELEVATION_DIFF_M,  # explizit -> kein Elevation-Netzwerkcall
        "observer_floor_height_m": 0.0,
        "days": 14,
        "min_score": 0.0,
    }
    params.update(overrides)
    return params


class TestPlanDaysCap:
    """US-137: `/plan` deckelt `days` hart auf 365 (analog BUG-63 bei
    `/preview-alignment`, dort `min(req.days, 14)`) — verhindert einen unbegrenzt
    wachsenden On-Demand-Lauf (z.B. durch einen versehentlich riesigen `days`-Wert
    oder einen böswilligen Client)."""

    def test_days_beyond_cap_is_clamped_to_365(self, client):
        r = client.get("/plan", params=_plan_params(days=999999))
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["status"] == "ok"
        assert body["days"] == 365, (
            f"/plan liefert days={body['days']} zurück, erwartet den gedeckelten "
            "Wert 365 (US-137 AK: harte Tages-Obergrenze, analog BUG-63)."
        )

    def test_days_at_exactly_cap_unchanged(self, client):
        r = client.get("/plan", params=_plan_params(days=365))
        assert r.status_code == 200, r.text
        assert r.json()["days"] == 365

    def test_days_within_cap_unchanged(self, client):
        """Ein normaler, unterhalb der Obergrenze liegender Wert (z.B. 60 Tage, wie
        er bei einem über 30 Tage hinausgehenden Sonnen-Alignment realistisch
        vorkommen kann) wird NICHT künstlich verändert."""
        r = client.get("/plan", params=_plan_params(days=60, min_score=0.9))
        assert r.status_code == 200, r.text
        assert r.json()["days"] == 60


class TestPlanRateLimit:
    """AK11: wiederholte, schnelle `/plan`-Aufrufe werden serverseitig abgebremst,
    analog zum bestehenden Schutz von `POST /preview-alignment`
    (`_preview_alignment_limiter`, 20 Aufrufe/60s)."""

    def test_rate_limit_blocks_further_calls_from_same_address(self, client, monkeypatch):
        import rate_limit

        monkeypatch.setattr(
            "main._plan_limiter",
            rate_limit.SlidingWindowRateLimiter(max_calls=1, window_seconds=60),
        )

        r1 = client.get("/plan", params=_plan_params())
        assert r1.status_code == 200, r1.text

        r2 = client.get("/plan", params=_plan_params())
        assert r2.status_code == 429, r2.text
        assert "Retry-After" in r2.headers, (
            "429-Antwort von /plan liefert keinen Retry-After-Header — Muster aus "
            "rate_limit._raise_rate_limited() (analog /preview-alignment) nicht "
            "eingehalten."
        )
        assert int(r2.headers["Retry-After"]) > 0

    def test_rate_limit_is_per_client_address(self, client, monkeypatch):
        """Zwei unterschiedliche Absenderadressen (X-Forwarded-For) teilen sich das
        Limit nicht — analog zum bestehenden Verhalten von
        `_preview_alignment_limiter` (siehe rate_limit.client_identity())."""
        import rate_limit

        monkeypatch.setattr(
            "main._plan_limiter",
            rate_limit.SlidingWindowRateLimiter(max_calls=1, window_seconds=60),
        )

        r1 = client.get(
            "/plan", params=_plan_params(),
            headers={"x-forwarded-for": "10.0.0.1"},
        )
        assert r1.status_code == 200, r1.text

        r2 = client.get(
            "/plan", params=_plan_params(),
            headers={"x-forwarded-for": "10.0.0.2"},
        )
        assert r2.status_code == 200, (
            "Eine andere Absenderadresse wurde fälschlich vom Limit der ersten "
            f"Adresse mitgebremst: {r2.text}"
        )

    def test_direct_function_call_without_request_still_works(self):
        """Analog zur BUG-63/TASK-86-Absicherung bei `preview_alignment()`: ein
        direkter Funktionsaufruf ohne HTTP-Layer (z.B. aus einem zukünftigen
        internen Aufrufer oder einem Unit-Test) darf nicht an einem fehlenden
        `request`-Objekt scheitern — `request` muss einen Default von `None` haben
        und die Rate-Bremse dabei übersprungen werden."""
        import asyncio
        import main

        result = asyncio.run(main.get_plan(
            observer_lat=_OBSERVER_LAT, observer_lon=_OBSERVER_LON,
            subject_lat=_SUBJECT_LAT, subject_lon=_SUBJECT_LON,
            subject_name="Referenz-Motiv", subject_height_m=15.0, subject_width_m=10.0,
            elevation_difference_m=_ELEVATION_DIFF_M, observer_floor_height_m=0.0,
            days=5, min_score=0.0,
        ))
        assert result["status"] == "ok"


class TestPlanFindsEventsBeyond30DayHorizon:
    """US-137 AK1 (backend-seitiger Anteil): `/plan` liefert - anders als der
    bisherige feste 30-Tage-Feed-Horizont (`GET /opportunities?days=30`) - auch
    Events, die mehr als 30 Tage in der Zukunft liegen, wenn `days` entsprechend
    groß gewählt wird (bis zur neuen 365-Tage-Obergrenze). Das ist die
    Voraussetzung dafür, dass das Frontend nach dem Umbau von
    `LocationDetail._loadEvents()` (jetzt `/plan?days=365` statt
    `/opportunities?days=30`) das nächste tatsächlich zukünftige Sonnen-Alignment
    auch jenseits von 30 Tagen anzeigen kann.

    `min_score=0.0` bewusst gewählt: "Goldene Stunde" (o.ä. astronomie-basierte
    Ereignistypen) tritt praktisch täglich auf (sunrise/sunset-basiert) und ist
    damit ein robuster, ortsunabhängiger Nachweis für "Events jenseits Tag 30" -
    ohne auf einen selten auftretenden echten Sonnen-Alignment-Treffer als
    Testgrundlage angewiesen zu sein (der für ein beliebiges Testdatum nicht
    garantiert innerhalb eines 40-Tage-Fensters auftritt)."""

    def test_plan_returns_events_beyond_30_days_when_days_allows_it(self, client):
        r = client.get("/plan", params=_plan_params(days=40, min_score=0.0))
        assert r.status_code == 200, r.text
        body = r.json()
        events = body["events"]
        assert events, (
            "Erwartete mindestens ein Event über 40 Tage (min_score=0.0) für die "
            "Referenzgeometrie - leere Liste deutet auf ein Problem in der "
            "Testaufsetzung hin, nicht auf einen echten US-137-Befund."
        )

        cutoff = (date.today() + timedelta(days=30)).isoformat()
        beyond_30_days = [e for e in events if e["shoot_time"][:10] > cutoff]
        assert beyond_30_days, (
            "Kein einziges der von /plan (days=40) gelieferten Events liegt mehr "
            "als 30 Tage in der Zukunft - der neue On-Demand-Pfad müsste aber "
            "gerade DAS leisten (US-137 AK1: nächstes Alignment auch über den "
            "bisherigen 30-Tage-Horizont hinaus)."
        )

    def test_plan_does_not_return_events_beyond_requested_days(self, client):
        """Regressionsschutz: der gehärtete Endpunkt liefert weiterhin nur Events
        innerhalb des angefragten (bzw. gedeckelten) Fensters - kein stiller
        Überlauf über `days` hinaus."""
        req_days = 20
        r = client.get("/plan", params=_plan_params(days=req_days, min_score=0.0))
        assert r.status_code == 200, r.text
        events = r.json()["events"]
        assert events

        limit = (date.today() + timedelta(days=req_days)).isoformat()
        too_late = [e for e in events if e["shoot_time"][:10] > limit]
        assert not too_late, (
            f"/plan(days={req_days}) lieferte {len(too_late)} Event(s) jenseits "
            f"des angefragten Fensters ({limit}) - unerwarteter Überlauf."
        )
