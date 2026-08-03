"""Regressionssuite — BUG-93: Kalender-Vollneuberechnung nach ALGORITHM_VERSION-Bump
berechnet 0 Events statt vollständig neu.

Bug: In `_init_calendar_pass()` wird bei Versions-Mismatch die lokale Variable
`existing_meta` korrekt auf `{}` zurückgesetzt — dieser Reset wurde jedoch nicht an
den Aufrufer `compute_calendar_incremental()` zurückgegeben. Der Aufrufer arbeitete
weiterhin mit seiner eigenen, nie aktualisierten `existing_meta`-Kopie beim Aufruf von
`_compute_calendar_for_location()`, wodurch `dates_needed = []` für jede Location
entstand — 0 neu berechnete Events statt der vollen 365-Tage-Range.

Fix (Option A, freigegeben 2026-08-01): `_init_calendar_pass()` gibt das (ggf.
zurückgesetzte) `existing_meta` zusätzlich als 5. Tupel-Wert zurück
(`valid_events, locations_to_process, new_meta, target_range, existing_meta`).
`compute_calendar_incremental()` verwendet diesen zurückgegebenen Wert statt seiner
eigenen lokalen Kopie beim Aufruf von `_compute_calendar_for_location()`.

Diese Suite testet bewusst auf Ebene von `compute_calendar_incremental()` (nicht nur
der isolierten Helferfunktion `_init_calendar_pass()`) — genau die Lücke, die laut
Pre-Mortem (Szenario 1) einen "nur halb wirkenden" Fix früh entlarven soll. Pattern
und Test-Doubles analog zu `test_bug29_calendar_single_recompute.py` (gestubbtes
`find_opportunities` → kein Ephemeriden-/Netzzugriff, Sandbox-sicher).

Konvention (vgl. test_astronomy_regression.py): Docstring jedes Tests nennt das Ticket.
"""
from datetime import date, timedelta
from types import SimpleNamespace as NS

import asyncio
import json

import pytest

import precompute as P

pytestmark = [pytest.mark.offline, pytest.mark.regression]


# ── Test-Doubles (identisch zum Muster in test_bug29_calendar_single_recompute.py) ──

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
    loc = o.loc
    return {
        "id": f"{loc.id}-{o.d.isoformat()}",
        "location_id": loc.id,
        "location_name": loc.name,
        "observer_lat": loc.observer_lat,
        "observer_lon": loc.observer_lon,
        "subject_lat": loc.subject_lat,
        "subject_lon": loc.subject_lon,
        "subject_azimuth": 90.0,
        "celestial_azimuth": 90.0,
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

    def write_cache(*, algorithm_version, meta, events):
        (tmp_path / "calendar.json").write_text(
            json.dumps({
                "algorithm_version": algorithm_version,
                "computed_at": "x",
                "computed_locations": meta,
                "events": events,
            }),
            encoding="utf-8",
        )

    return NS(today=today, set_locations=set_locations, run=run, write_cache=write_cache)


def _events_of(events, loc_id):
    return [e for e in events if e["location_id"] == loc_id]


# ── BUG-93 Kernregression (AK1/AK2/AK5): Versions-Mismatch löst volle Neuberechnung
#    für ALLE Locations aus — nicht 0 Events wie live reproduziert (2026-07-30) ──────
def test_bug93_version_mismatch_recomputes_full_range_not_zero(patched):
    """BUG-93: Ein ALGORITHM_VERSION-Mismatch führt in compute_calendar_incremental()
    zu dates_needed = voller 365-Tage-Range für JEDE Location — nicht zu 0 Events.

    Simuliert exakt den live reproduzierten Fehlzustand: Der Cache behauptet, alle
    365 Tage seien bereits vollständig berechnet ("computed_dates" deckt die komplette
    target_range ab, coordinates_hash passt), enthält dabei aber 0 echte Events — und
    trägt eine andere algorithm_version als der aktuelle Code (Edge Case aus AK5).
    """
    a = _loc("loc_a", observer_lat=52.500000, observer_lon=13.400000)
    b = _loc("loc_b", observer_lat=52.600000, observer_lon=13.500000)
    patched.set_locations([a, b])

    target_range = {(patched.today + timedelta(days=i)).isoformat() for i in range(365)}

    stale_meta = {
        "loc_a": {"coordinates_hash": P._location_hash(a), "computed_dates": sorted(target_range)},
        "loc_b": {"coordinates_hash": P._location_hash(b), "computed_dates": sorted(target_range)},
    }
    patched.write_cache(algorithm_version="0.1-stale", meta=stale_meta, events=[])

    events, meta = patched.run()  # kein location_id, kein force_full → Versions-Check greift

    # Kern der Regression: NICHT 0 Events, sondern volle Range × Anzahl Locations.
    assert len(events) == 2 * len(target_range), (
        f"Erwartet {2 * len(target_range)} Events (volle Neuberechnung beider Locations "
        f"nach Versions-Mismatch), bekommen {len(events)} — BUG-93-Regression!"
    )
    assert len(_events_of(events, "loc_a")) == len(target_range)
    assert len(_events_of(events, "loc_b")) == len(target_range)
    assert set(meta["loc_a"]["computed_dates"]) == target_range
    assert set(meta["loc_b"]["computed_dates"]) == target_range


# ── BUG-93 AK3: Normaler täglicher Lauf ohne Versions-Differenz bleibt unverändert ──
def test_bug93_normal_incremental_run_unaffected(patched):
    """BUG-93 AK3: Ohne Versions-Differenz/force_full wird beim zweiten Lauf am
    selben Tag nichts neu berechnet — der Fix darf den schnellen Alltagsbetrieb
    nicht verlangsamen bzw. verändern."""
    a = _loc("loc_a", observer_lat=52.500000, observer_lon=13.400000)
    patched.set_locations([a])

    base_events, base_meta = patched.run()
    patched.write_cache(algorithm_version=P.ALGORITHM_VERSION, meta=base_meta, events=base_events)

    events, meta = patched.run()
    assert len(events) == len(base_events), (
        "Ohne Versions-Differenz darf beim erneuten Lauf am selben Tag nichts neu "
        "berechnet werden"
    )


# ── BUG-93 AK4 / BUG-29-Garantie: Single-Location-Pfad bleibt bei Versions-Differenz
#    unberührt von der Reset-Propagierung ────────────────────────────────────────────
def test_bug93_single_location_path_unaffected_by_version_mismatch(patched):
    """BUG-93 AK4: Bei gesetztem location_id findet auch bei einer
    ALGORITHM_VERSION-Differenz im Cache KEIN Voll-Reset statt — andere Locations
    (hier loc_b) behalten ihre echten, bereits berechneten Events unverändert
    (BUG-29-Garantie, darf durch den BUG-93-Fix nicht brechen)."""
    a = _loc("loc_a", observer_lat=52.500000, observer_lon=13.400000)
    b = _loc("loc_b", observer_lat=52.600000, observer_lon=13.500000)
    patched.set_locations([a, b])

    base_events, base_meta = patched.run()
    b_before = sorted(_events_of(base_events, "loc_b"), key=lambda e: e["id"])
    assert b_before, "Baseline muss loc_b-Events enthalten"

    # Cache trägt eine ANDERE (alte) algorithm_version als der aktuelle Code —
    # simuliert einen anstehenden Versions-Bump, während gleichzeitig ein
    # Single-Location-Recompute für loc_a läuft (z. B. nach einem Koordinaten-PATCH).
    patched.write_cache(algorithm_version="0.1-stale", meta=base_meta, events=base_events)
    a.observer_lat, a.observer_lon = 52.512345, 13.412345

    events, meta = patched.run(location_id="loc_a")

    b_after = sorted(_events_of(events, "loc_b"), key=lambda e: e["id"])
    assert b_after == b_before, (
        "loc_b darf durch die Versions-Differenz NICHT verworfen werden — der "
        "Single-Location-Pfad ist von der Reset-Propagierung ausgenommen"
    )
    assert _events_of(events, "loc_a"), "loc_a muss trotzdem neu berechnet werden (Koordinatenänderung)"
