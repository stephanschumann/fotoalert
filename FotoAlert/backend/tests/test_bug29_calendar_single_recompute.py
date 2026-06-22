"""Regressionssuite — BUG-29: Kalender-Snapshot nach Koordinaten-PATCH.

Bug: Der Single-Location-Recompute nach `PATCH /locations/{id}` lief mit
`--feed-only` und schrieb ausschließlich `opportunities.json`; `calendar.json`
behielt seinen denormalisierten Koordinaten-/Astronomie-Snapshot bis zum
nächtlichen Vollkalender. Chancendetails aus dem **Kalender** zeigten deshalb
alte GPS-Daten, obwohl die Location bereits korrigiert war.

Fix (Option A(a)): `compute_calendar_incremental(location_id=…)` regeneriert den
Kalender **nur** für die geänderte Location und merged ihn in den bestehenden
Cache — Events und Meta aller übrigen Locations bleiben unangetastet.

Diese Suite sichert die Kalender-Merge-Logik deterministisch ab (gestubbtes
`find_opportunities` → kein Ephemeriden-/Netzzugriff, Sandbox-sicher). Der Feed-
Pfad (AK1) und die Frontend-Anzeige werden manuell verifiziert (siehe Ticket-
Testplan); das `_precompute_running`-Gating (AK5) ist Bestand von main.py.

Konvention (vgl. test_astronomy_regression.py): Docstring jedes Tests nennt das
Ticket.
"""
from datetime import date
from types import SimpleNamespace as NS

import asyncio

import pytest

import precompute as P

pytestmark = [pytest.mark.offline, pytest.mark.regression]


# ── Test-Doubles ─────────────────────────────────────────────────────────────

def _loc(loc_id, *, observer_lat, observer_lon):
    """Minimale Location: _location_hash nutzt observer_lat/lon, _serialize den Rest."""
    return NS(
        id=loc_id,
        name=f"Loc {loc_id}",
        observer_lat=observer_lat,
        observer_lon=observer_lon,
        subject_lat=observer_lat + 0.001,
        subject_lon=observer_lon + 0.001,
    )


def _fake_serialize(o):
    """Baut ein Kalender-Event aus dem (loc, d)-Stub.

    `subject_azimuth`/`celestial_azimuth` werden deterministisch aus den
    Observer-Koordinaten abgeleitet — so ändern sie sich GENAU dann, wenn sich
    die Koordinaten ändern (Voraussetzung für die Astronomie-AK).
    """
    loc = o.loc
    az = round((loc.observer_lat * 1000.0) % 360.0, 4)
    return {
        "id": f"{loc.id}-{o.d.isoformat()}",
        "location_id": loc.id,
        "location_name": loc.name,
        "observer_lat": loc.observer_lat,
        "observer_lon": loc.observer_lon,
        "subject_lat": loc.subject_lat,
        "subject_lon": loc.subject_lon,
        "subject_azimuth": az,
        "celestial_azimuth": az,
        "celestial_altitude": 5.0,
        "event_type": "Mond-Alignment",
        "shoot_time": f"{o.d.isoformat()}T20:00:00+00:00",
        "overall_score": 0.9,
        "composition_analysis": None,  # → _passes_alignment_filter == True
    }


async def _fake_find_opportunities(loc, d, *args, **kwargs):
    """Ein deterministisches Event pro (Location, Tag), ohne Ephemeriden."""
    return [NS(loc=loc, d=d)]


@pytest.fixture
def patched(tmp_path, monkeypatch):
    """Isolierter CACHE_DIR + gestubbte Astronomie; gibt Helfer zurück."""
    monkeypatch.setattr(P, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(P, "find_opportunities", _fake_find_opportunities)
    monkeypatch.setattr(P, "_serialize", _fake_serialize)

    today = date(2026, 6, 22)

    def set_locations(locs):
        monkeypatch.setattr(P, "LOCATIONS", list(locs))

    def run(**kwargs):
        return asyncio.run(P.compute_calendar_incremental(today, **kwargs))

    def write_cache(events, meta):
        import json
        (tmp_path / "calendar.json").write_text(
            json.dumps({
                "algorithm_version": P.ALGORITHM_VERSION,
                "computed_at": "x",
                "computed_locations": meta,
                "events": events,
            }),
            encoding="utf-8",
        )

    return NS(today=today, set_locations=set_locations, run=run, write_cache=write_cache)


def _events_of(events, loc_id):
    return [e for e in events if e["location_id"] == loc_id]


# ── BUG-29 AK2: Geänderte Koordinaten landen im Kalender-Snapshot ─────────────
def test_bug29_single_recompute_writes_new_coordinates(patched):
    """BUG-29: Nach Single-Recompute trägt jedes Kalender-Event der Location die NEUEN Koordinaten."""
    a = _loc("loc_a", observer_lat=52.500000, observer_lon=13.400000)
    b = _loc("loc_b", observer_lat=52.600000, observer_lon=13.500000)
    patched.set_locations([a, b])

    # Baseline-Kalender (Volllauf über beide Locations)
    base_events, base_meta = patched.run()
    patched.write_cache(base_events, base_meta)

    # Koordinaten-PATCH simulieren: A bekommt neue Observer-Koordinaten
    a.observer_lat, a.observer_lon = 52.512345, 13.412345

    events, meta = patched.run(location_id="loc_a")

    a_events = _events_of(events, "loc_a")
    assert a_events, "loc_a muss nach Recompute Events haben"
    for e in a_events:
        assert abs(e["observer_lat"] - 52.512345) <= 1e-5, "observer_lat muss NEU sein"
        assert abs(e["observer_lon"] - 13.412345) <= 1e-5, "observer_lon muss NEU sein"


# ── BUG-29 AK3: Astronomie-abhängige Felder folgen den neuen Koordinaten ──────
def test_bug29_astronomy_fields_follow_new_coordinates(patched):
    """BUG-29: subject_azimuth/celestial_azimuth entsprechen NACH dem Recompute den neuen Koordinaten."""
    a = _loc("loc_a", observer_lat=52.500000, observer_lon=13.400000)
    patched.set_locations([a])

    base_events, base_meta = patched.run()
    patched.write_cache(base_events, base_meta)
    old_az = base_events[0]["subject_azimuth"]

    a.observer_lat, a.observer_lon = 52.512345, 13.412345
    events, _ = patched.run(location_id="loc_a")

    new_az = round((52.512345 * 1000.0) % 360.0, 4)
    for e in _events_of(events, "loc_a"):
        assert e["subject_azimuth"] == new_az
        assert e["celestial_azimuth"] == new_az
    assert new_az != old_az, "Azimut muss sich mit den Koordinaten geändert haben"


# ── BUG-29 AK6 / Pre-Mortem #2: Andere Locations bleiben unverändert ──────────
def test_bug29_other_locations_untouched(patched):
    """BUG-29: Single-Recompute von loc_a lässt Events UND Meta von loc_b exakt unverändert."""
    a = _loc("loc_a", observer_lat=52.500000, observer_lon=13.400000)
    b = _loc("loc_b", observer_lat=52.600000, observer_lon=13.500000)
    patched.set_locations([a, b])

    base_events, base_meta = patched.run()
    patched.write_cache(base_events, base_meta)
    b_before = sorted(_events_of(base_events, "loc_b"), key=lambda e: e["id"])

    a.observer_lat, a.observer_lon = 52.512345, 13.412345
    events, meta = patched.run(location_id="loc_a")

    b_after = sorted(_events_of(events, "loc_b"), key=lambda e: e["id"])
    assert b_after == b_before, "loc_b-Events dürfen sich nicht ändern (kein Schrumpfen, kein Recompute)"
    # Pre-Mortem #3: Meta beider Locations vorhanden, A aktualisiert
    assert set(meta.keys()) == {"loc_a", "loc_b"}, "Meta darf keine Location verlieren"
    assert meta["loc_b"]["coordinates_hash"] == base_meta["loc_b"]["coordinates_hash"]
    assert meta["loc_a"]["coordinates_hash"] == P._location_hash(a), "loc_a-Hash muss auf NEUE Koordinaten zeigen"


# ── BUG-29 AK4: Brandneue Location ohne bestehende Kalender-Events ────────────
def test_bug29_new_location_no_existing_events(patched):
    """BUG-29 Edge: Single-Recompute einer Location ohne Kalender-Historie legt Events an, kein Crash."""
    a = _loc("loc_a", observer_lat=52.500000, observer_lon=13.400000)
    c = _loc("custom_new", observer_lat=52.700000, observer_lon=13.300000)
    # Cache kennt nur loc_a; custom_new ist neu (z.B. frische Custom-Location)
    patched.set_locations([a])
    base_events, base_meta = patched.run()
    patched.write_cache(base_events, base_meta)

    # Jetzt existiert custom_new in LOCATIONS und wird einzeln berechnet
    patched.set_locations([a, c])
    events, meta = patched.run(location_id="custom_new")

    assert _events_of(events, "custom_new"), "Neue Location muss Events bekommen"
    assert _events_of(events, "loc_a"), "Bestehende Location darf nicht verschwinden"
    assert set(meta.keys()) == {"loc_a", "custom_new"}


# ── BUG-29 Root-Cause: precompute wendet persistierte Overrides an ────────────
def test_bug29_apply_location_overrides_changes_coordinates(monkeypatch):
    """BUG-29: _apply_location_overrides() überschreibt Basis-Koordinaten mit dem persistierten Override.

    Kern der echten Ursache: Ohne diesen Schritt rechnet der Recompute mit den alten
    Basis-Koordinaten, der coordinates_hash bleibt gleich und es wird nichts neu berechnet.
    """
    a = _loc("loc_a", observer_lat=52.500000, observer_lon=13.400000)
    b = _loc("loc_b", observer_lat=52.600000, observer_lon=13.500000)
    monkeypatch.setattr(P, "LOCATIONS", [a, b])

    hash_before = P._location_hash(a)

    class _FakeStore:
        def load_all_overrides(self):
            return [{"id": "loc_a", "observer_lat": 52.512345, "observer_lon": 13.412345,
                     "name": "Korrigiert"}]

    monkeypatch.setattr(P, "LocationStore", _FakeStore)

    applied = P._apply_location_overrides()

    assert applied == 1
    assert abs(a.observer_lat - 52.512345) <= 1e-9
    assert abs(a.observer_lon - 13.412345) <= 1e-9
    assert a.name == "Korrigiert"
    assert P._location_hash(a) != hash_before, "Hash MUSS sich ändern → triggert Neuberechnung"
    # Location ohne Override bleibt unverändert
    assert abs(b.observer_lat - 52.600000) <= 1e-9


def test_bug29_apply_overrides_survives_store_error(monkeypatch):
    """BUG-29: Fällt der Override-Store aus, rechnet precompute mit Basis-Koordinaten weiter (kein Crash)."""
    a = _loc("loc_a", observer_lat=52.5, observer_lon=13.4)
    monkeypatch.setattr(P, "LOCATIONS", [a])

    class _BrokenStore:
        def load_all_overrides(self):
            raise RuntimeError("db locked")

    monkeypatch.setattr(P, "LocationStore", _BrokenStore)
    assert P._apply_location_overrides() == 0
    assert a.observer_lat == 52.5  # unverändert, kein Crash


# ── BUG-29 Pre-Mortem #1: Single-Pfad rechnet NICHT alle Locations neu ────────
def test_bug29_single_recompute_only_touches_target(patched):
    """BUG-29: Im Single-Modus ruft der Kalender find_opportunities nur für die Ziel-Location auf."""
    a = _loc("loc_a", observer_lat=52.500000, observer_lon=13.400000)
    b = _loc("loc_b", observer_lat=52.600000, observer_lon=13.500000)
    patched.set_locations([a, b])
    base_events, base_meta = patched.run()
    patched.write_cache(base_events, base_meta)

    # Zähle Aufrufe pro Location-ID im Single-Lauf
    calls = {"loc_a": 0, "loc_b": 0}

    async def counting_find(loc, d, *args, **kwargs):
        calls[loc.id] = calls.get(loc.id, 0) + 1
        return [NS(loc=loc, d=d)]

    import pytest as _pt
    with _pt.MonkeyPatch.context() as mp:
        mp.setattr(P, "find_opportunities", counting_find)
        a.observer_lat = 52.512345  # Hash-Änderung erzwingt Neuberechnung von A
        patched.run(location_id="loc_a")

    assert calls["loc_a"] > 0, "Ziel-Location muss neu berechnet werden"
    assert calls["loc_b"] == 0, "andere Location darf NICHT neu berechnet werden (Pre-Mortem #1)"
