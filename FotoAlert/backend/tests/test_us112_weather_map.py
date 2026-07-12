"""US-112 — Wetter-Overlay aus echten Modelldaten (DWD ICON + MET Norway), weicher PNG-Verlauf.

Getestet (Python 3.9-kompatibel, Optional[...] statt X|Y):
  - GRIB-Dekodierung gegen ein kleines, im Test erzeugtes GRIB2-Fixture
    (kein Live-DWD-Abruf) → Stützpunkte mit Werten.
  - TOT_PREC akkumuliert → pro Stunde differenziert (deaccumulate_precip).
  - IDW-Interpolation liefert ein 2-D-Feld; PNG-Encoding ergibt gültiges PNG.
  - Quellen-Merge (DWD-GRIB + Norwegen-Punkte) auf EINER 72-h-Stundenachse.
  - Null-Handling: fällt eine Quelle aus, bleibt die andere gültig (kein Raise).
  - Endpoint-Schema /weather-map (bounds, hourly_times, frames, attribution).
  - Cache: zweiter /weather-map-Call ohne neuen Build (gleicher fetched_at).
"""
import asyncio
from datetime import datetime, timedelta, timezone
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from calculations import weather_grib as wg

pytestmark = [pytest.mark.regression]
# TASK-72: `regression` gilt datei-weit (US-112-AK-Bezug). `offline`/`api` sind gemischt
# (13 reine Berechnungstests vs. 3 echte Endpoint-Tests) und werden daher NICHT pauschal
# auf Modulebene vergeben, sondern einzeln je Testfunktion (siehe Klassifikationstabelle,
# BACKLOG.md TASK-72, Regel 2 Grenzfall).


# ---------------------------------------------------------------------------
# GRIB-Fixture (klein, regular_ll GRIB2, via eccodes-Sample erzeugt)
# ---------------------------------------------------------------------------

def _make_grib_fixture(const: float, Ni: int = 30, Nj: int = 28) -> bytes:
    """Erzeugt eine GRIB2-Nachricht mit konstantem Wert über die App-BBox."""
    import eccodes as ec
    gid = ec.codes_grib_new_from_samples("regular_ll_pl_grib2")
    ec.codes_set(gid, "Ni", Ni)
    ec.codes_set(gid, "Nj", Nj)
    ec.codes_set(gid, "latitudeOfFirstGridPointInDegrees", 58.0)
    ec.codes_set(gid, "longitudeOfFirstGridPointInDegrees", 4.0)
    ec.codes_set(gid, "latitudeOfLastGridPointInDegrees", 44.0)
    ec.codes_set(gid, "longitudeOfLastGridPointInDegrees", 20.0)
    ec.codes_set(gid, "iDirectionIncrementInDegrees", (20.0 - 4.0) / (Ni - 1))
    ec.codes_set(gid, "jDirectionIncrementInDegrees", (58.0 - 44.0) / (Nj - 1))
    ec.codes_set(gid, "jScansPositively", 0)
    ec.codes_set_values(gid, np.full(Ni * Nj, float(const)))
    raw = ec.codes_get_message(gid)
    ec.codes_release(gid)
    return raw


eccodes_required = pytest.mark.skipif(not wg.HAVE_ECCODES, reason="eccodes nicht installiert")
pillow_required = pytest.mark.skipif(not wg.HAVE_PIL, reason="Pillow nicht installiert")


# ---------------------------------------------------------------------------
# GRIB-Dekodierung → Stützpunkte
# ---------------------------------------------------------------------------

@pytest.mark.offline
@eccodes_required
def test_grib_decode_and_samples():
    raw = _make_grib_fixture(42.0)
    dec = wg.decode_grib_message(raw)
    assert dec is not None
    assert dec["Ni"] == 30 and dec["Nj"] == 28

    samples = []
    pidx = {}
    wg.grib_to_samples(raw, 0, 72, "cloud", samples, pidx, stride=4)
    assert len(samples) > 0
    # Werte landen auf der richtigen Stunde, alle == 42
    sp = samples[0]
    assert abs(float(sp.cloud[0]) - 42.0) < 1e-3
    assert np.isnan(sp.cloud[1])  # andere Stunden bleiben leer
    # Stützpunkte liegen innerhalb der BBox
    for s in samples:
        assert wg.BBOX_S <= s.lat <= wg.BBOX_N
        assert wg.BBOX_W <= s.lon <= wg.BBOX_E


@pytest.mark.offline
def test_deaccumulate_precip():
    sp = wg.SamplePoint(50.0, 10.0, 5)
    sp.precip[:5] = [0.0, 0.5, 0.5, 2.0, 2.0]  # akkumuliert
    wg.deaccumulate_precip([sp], dwd_max_idx=4)
    # pro Stunde = Differenz, nie negativ
    assert abs(float(sp.precip[0]) - 0.0) < 1e-5
    assert abs(float(sp.precip[1]) - 0.5) < 1e-5
    assert abs(float(sp.precip[2]) - 0.0) < 1e-5
    assert abs(float(sp.precip[3]) - 1.5) < 1e-5
    assert abs(float(sp.precip[4]) - 0.0) < 1e-5


@pytest.mark.offline
@pillow_required
def test_interpolate_and_png():
    samples = [
        wg.SamplePoint(52.0, 9.0, 4),
        wg.SamplePoint(48.0, 12.0, 4),
        wg.SamplePoint(55.0, 7.0, 4),
    ]
    for s in samples:
        s.cloud[0] = 60.0
    gl, go = wg._build_grids()
    arr = wg.interpolate_idw(samples, 0, "cloud", gl, go)
    assert arr is not None
    assert arr.shape == (wg.PNG_H, wg.PNG_W)
    assert np.isfinite(arr).any()
    png = wg.field_to_png(arr, "cloud")
    assert png is not None
    assert png[:8] == b"\x89PNG\r\n\x1a\n"


@pytest.mark.offline
def test_interpolate_no_points_returns_none():
    samples = [wg.SamplePoint(52.0, 9.0, 4)]  # alle NaN für Stunde 0
    gl, go = wg._build_grids()
    arr = wg.interpolate_idw(samples, 0, "cloud", gl, go)
    assert arr is None  # keine Stützwerte → kein Feld (kein Crash, kein Fehlfarben-Block)


# ---------------------------------------------------------------------------
# BUG-59 (Option E): Non-linearer Alpha-Verlauf statt fixem alpha=150.
# ---------------------------------------------------------------------------

@pillow_required
def _png_alpha(field: str, value: float) -> int:
    """Baut ein 1x1-Feld mit `value` und liest den Alpha-Kanal aus dem PNG zurück."""
    from PIL import Image
    import io as _io
    arr = np.full((2, 2), value, dtype=np.float32)
    png = wg.field_to_png(arr, field)
    assert png is not None
    img = Image.open(_io.BytesIO(png)).convert("RGBA")
    return img.getpixel((0, 0))[3]


@pytest.mark.offline
@pillow_required
def test_cloud_alpha_below_threshold_stays_faint():
    # Deutlich unter der Schwelle (15%) → nur Basis-Deckkraft, kein Fehlsignal.
    a = _png_alpha("cloud", 2.0)
    assert a == wg._CLOUD_ALPHA_BELOW


@pytest.mark.offline
@pillow_required
def test_cloud_alpha_jumps_at_threshold():
    # Direkt an der Schwelle → deutlicher Sprung auf die Mindest-Deckkraft.
    a = _png_alpha("cloud", wg._CLOUD_ALPHA_THRESHOLD)
    assert a >= wg._CLOUD_ALPHA_BASE
    assert a > wg._CLOUD_ALPHA_BELOW + 50  # klar wahrnehmbarer Sprung


@pytest.mark.offline
@pillow_required
def test_cloud_alpha_high_value_near_max_not_oversaturated():
    a = _png_alpha("cloud", 100.0)
    assert a == wg._CLOUD_ALPHA_MAX
    assert a < 255  # bewusst nie voll deckend (Bauhaus: Karte bleibt durchscheinend)


@pytest.mark.offline
@pillow_required
def test_precip_dry_limit_still_fully_transparent():
    # Unverändertes Verhalten aus Analyse 1: <0.05mm bleibt komplett transparent.
    a = _png_alpha("precip", 0.01)
    assert a == 0


@pytest.mark.offline
@pillow_required
def test_precip_alpha_jumps_above_dry_limit():
    # Zwischen Trockenheitsgrenze und Schwelle: sichtbar, aber moderat.
    a = _png_alpha("precip", 0.1)
    assert a == wg._PRECIP_ALPHA_BELOW
    assert a > 0


@pytest.mark.offline
@pillow_required
def test_precip_alpha_high_value_near_max_not_oversaturated():
    a = _png_alpha("precip", 10.0)
    assert a == wg._PRECIP_ALPHA_MAX
    assert a < 255


# ---------------------------------------------------------------------------
# Quellen-Merge auf einer Stundenachse + Null-Handling
# ---------------------------------------------------------------------------

class _FakeResp:
    def __init__(self, status, content=None, js=None):
        self.status_code = status
        self.content = content
        self._js = js

    def json(self):
        return self._js


def _met_payload(base_time, n=3):
    ts = []
    for h in range(n):
        t = (base_time + timedelta(hours=h)).isoformat().replace("+00:00", "Z")
        ts.append({
            "time": t,
            "data": {
                "instant": {"details": {"cloud_area_fraction": 70.0}},
                "next_1_hours": {"details": {"precipitation_amount": 0.4}},
            },
        })
    return {"properties": {"timeseries": ts}}


def _make_fake_client(dwd_ok=True, met_ok=True):
    base = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)

    class _Client:
        def __init__(self, *a, **k):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            return False

        async def get(self, url, headers=None, timeout=None):
            if "api.met.no" in url:
                if not met_ok:
                    raise Exception("MET down")
                return _FakeResp(200, js=_met_payload(base))
            # DWD GRIB
            if not dwd_ok:
                return _FakeResp(404)
            if "clct" in url:
                return _FakeResp(200, content=_make_grib_fixture(40.0))
            if "tot_prec" in url:
                return _FakeResp(200, content=_make_grib_fixture(1.0))
            return _FakeResp(404)

    return _Client()


@pytest.mark.offline
@eccodes_required
def test_merge_common_axis_both_sources():
    overlay = asyncio.run(
        wg.build_weather_overlay(_make_fake_client(True, True), n_hours=72, base_time=None)
    )
    assert len(overlay["hourly_times"]) == 72  # gemeinsame 72-h-Achse
    assert overlay["sources"]["met"] == len(wg.MET_NORWAY_POINTS)
    assert overlay["sources"]["icon_d2"] > 0
    assert overlay["n_points"] > len(wg.MET_NORWAY_POINTS)  # DWD-Punkte zusätzlich


@pytest.mark.offline
@eccodes_required
def test_dwd_fails_met_still_valid():
    """DWD-Abruf scheitert (404), MET liefert → andere Quelle bleibt gültig, kein Raise."""
    overlay = asyncio.run(
        wg.build_weather_overlay(_make_fake_client(dwd_ok=False, met_ok=True), n_hours=72)
    )
    assert len(overlay["hourly_times"]) == 72
    assert overlay["sources"]["icon_d2"] == 0
    assert overlay["sources"]["met"] == len(wg.MET_NORWAY_POINTS)
    assert overlay["n_points"] == len(wg.MET_NORWAY_POINTS)


@pytest.mark.offline
def test_all_sources_fail_no_crash():
    overlay = asyncio.run(
        wg.build_weather_overlay(_make_fake_client(dwd_ok=False, met_ok=False), n_hours=72)
    )
    assert len(overlay["hourly_times"]) == 72  # Achse bleibt, nur ohne Stützpunkte
    assert overlay["n_points"] == 0


# ---------------------------------------------------------------------------
# Endpoint /weather-map
# ---------------------------------------------------------------------------

@pytest.mark.api
def test_weather_map_endpoint_schema(client):
    """GET /weather-map → 200 mit US-112-Schema (bounds, hourly_times, frames, attribution)."""
    import main

    main._weather_map_cache = {
        "bounds": wg.overlay_bounds(),
        "hourly_times": ["2026-06-30T12:00:00+00:00"],
        "sources": {"icon_d2": 96, "icon_eu": 48, "met": 16},
        "n_points": 200,
        "attribution": "Daten: DWD · MET Norway (CC BY 4.0)",
        "attribution_url": "https://www.met.no/en/free-meteorological-data",
    }
    main._weather_map_png = {"cloud": [b"\x89PNG\r\n\x1a\nXX"], "precip": [None]}
    main._weather_map_updated_at = datetime.now(timezone.utc)

    r = client.get("/weather-map?hours=72")
    assert r.status_code == 200
    b = r.json()
    assert b["ready"] is True
    assert b["bounds"] == [[43.0, 3.0], [71.5, 21.0]]
    assert len(b["hourly_times"]) == 1
    assert b["frames"]["clouds"][0] == "/weather-map/png/cloud/0"
    assert b["frames"]["precip"][0] is None  # kein Bild → null, kein Fake-URL
    assert b["attribution"].startswith("Daten: DWD")
    assert "met.no" in b["attribution_url"]


@pytest.mark.api
def test_weather_map_png_serving(client):
    import main

    png_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20
    main._weather_map_png = {"cloud": [png_bytes], "precip": []}

    r = client.get("/weather-map/png/cloud/0")
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
    assert r.content[:8] == b"\x89PNG\r\n\x1a\n"

    assert client.get("/weather-map/png/cloud/5").status_code == 404   # idx out of range
    assert client.get("/weather-map/png/bogus/0").status_code == 404   # unknown field


@pytest.mark.api
def test_weather_map_cache_no_rebuild(client):
    """Zweiter /weather-map-Call bei frischem Cache → kein neuer Build (gleicher fetched_at)."""
    import main

    fresh = datetime.now(timezone.utc)
    main._weather_map_cache = {
        "bounds": wg.overlay_bounds(),
        "hourly_times": ["2026-06-30T12:00:00+00:00"],
        "sources": {"icon_d2": 1, "icon_eu": 1, "met": 1},
        "n_points": 10,
        "attribution": "Daten: DWD · MET Norway (CC BY 4.0)",
        "attribution_url": "https://www.met.no/en/free-meteorological-data",
    }
    main._weather_map_png = {"cloud": [None], "precip": [None]}
    main._weather_map_updated_at = fresh

    build_calls = {"n": 0}

    async def _fake_build():
        build_calls["n"] += 1

    with patch("main._build_weather_map", new=_fake_build):
        r1 = client.get("/weather-map")
        r2 = client.get("/weather-map")

    assert r1.status_code == 200 and r2.status_code == 200
    assert build_calls["n"] == 0  # fresh cache → kein Rebuild
    assert r1.json()["fetched_at"] == r2.json()["fetched_at"]
