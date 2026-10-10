"""US-138 (Schritt 1 von 3) — Wetterkarte deckt England (London) ab.

Getestet (Python 3.9-kompatibel, keine X|Y-Typen, kein match):
  T1  AK1  Kartengrenzen enthalten London, Cornwall (Land's End), Great Yarmouth;
           Berlin, Muenchen, Oslo, Po-Ebene bleiben drin; Atlantik (9 W) liegt draussen.
  T2  AK1  GRIB-Gitter ueber England (Laenge -6..+2) liefert Stuetzpunkte westlich von 0 Grad,
           alle innerhalb der Kartengrenzen.
  T3  AK1  Bild: Pixel bei London ist mit Daten gefaerbt (nicht transparent).
  T3b AK4  Faellt die Quelle fuer England aus (nur Deutschland-Stuetzpunkte), bleibt England
           transparent ("keine Daten"), Deutschland bleibt gefaerbt.
  T4  AK3  Bewoelkungswerte an Berlin/Muenchen/Oslo weichen gegenueber dem alten Ausschnitt
           (3-21 Grad Ost, 360x420 px) hoechstens 2 Prozentpunkte ab.
  T5       Ersatz-Grenzen in web/index.html == Server-Grenzen (overlay_bounds()).
  T6  AK7/AK8 (Bestaetigung, kein Umbau) Wetter pro Ort: London-Termin in 2 Tagen plant einen
           Abruf mit den London-Koordinaten; Termin in 5 Tagen bekommt kein Wetter.
  T7  AK10 (Bestaetigung) Scheitert der Abruf nur fuer London, steht nur London in der
           Fehlerliste/-meldung; der deutsche Ort behaelt sein Wetter.
"""
import io
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pytest

from calculations import weather_grib as wg

pytestmark = [pytest.mark.regression]

eccodes_required = pytest.mark.skipif(not wg.HAVE_ECCODES, reason="eccodes nicht installiert")
pillow_required = pytest.mark.skipif(not wg.HAVE_PIL, reason="Pillow nicht installiert")

# Orte (Breite, Laenge) aus dem Ticket / den Akzeptanzkriterien
LONDON = (51.5, -0.12)
LANDS_END = (50.1, -5.5)          # AK1: Cornwall
GREAT_YARMOUTH = (52.6, 1.7)      # AK1: Ostkueste
BERLIN = (52.52, 13.40)
MUENCHEN = (48.14, 11.58)
OSLO = (59.91, 10.75)
PO_EBENE = (44.9, 11.0)
ATLANTIK = (51.5, -9.0)           # muss ausserhalb liegen

# Alter Kartenausschnitt (vor US-138) — Referenz fuer AK3
OLD_S, OLD_N, OLD_W, OLD_E = 43.0, 71.5, 3.0, 21.0
OLD_PNG_W, OLD_PNG_H = 360, 420


def _inside(point):
    lat, lon = point
    return wg.BBOX_S <= lat <= wg.BBOX_N and wg.BBOX_W <= lon <= wg.BBOX_E


def _pixel(point):
    """Pixelposition (x, y) eines Ortes im Bild des Servers (None wenn ausserhalb)."""
    lat, lon = point
    if not _inside(point):
        return None
    x = int(round((lon - wg.BBOX_W) / (wg.BBOX_E - wg.BBOX_W) * (wg.PNG_W - 1)))
    y = int(round((wg.BBOX_N - lat) / (wg.BBOX_N - wg.BBOX_S) * (wg.PNG_H - 1)))
    return x, y


def _alpha_at(png_bytes, xy):
    from PIL import Image
    img = Image.open(io.BytesIO(png_bytes)).convert("RGBA")
    return img.getpixel(xy)[3]


def _render(samples, hour=0, field="cloud"):
    gl, go = wg._build_grids()
    arr = wg.interpolate_idw(samples, hour, field, gl, go)
    return wg.field_to_png(arr, field)


def _sample(point, cloud, n_hours=1):
    sp = wg.SamplePoint(point[0], point[1], n_hours)
    sp.cloud[0] = cloud
    return sp


# ---------------------------------------------------------------------------
# T1 — Kartengrenzen
# ---------------------------------------------------------------------------

@pytest.mark.offline
def test_t1_england_liegt_in_den_kartengrenzen():
    """AK1: London, Cornwall, Great Yarmouth liegen im Kartenbild."""
    assert _inside(LONDON), "London liegt ausserhalb der Kartengrenzen"
    assert _inside(LANDS_END), "Cornwall (50,1 N / 5,5 W) liegt ausserhalb der Kartengrenzen"
    assert _inside(GREAT_YARMOUTH), "Great Yarmouth (52,6 N / 1,7 O) liegt ausserhalb der Kartengrenzen"


@pytest.mark.offline
def test_t1_bisheriges_gebiet_bleibt_und_atlantik_draussen():
    """AK3/Abwaertskompatibilitaet: Berlin, Muenchen, Oslo, Po-Ebene bleiben drin; 9 W bleibt draussen."""
    for name, p in (("Berlin", BERLIN), ("Muenchen", MUENCHEN), ("Oslo", OSLO), ("Po-Ebene", PO_EBENE)):
        assert _inside(p), "%s liegt nicht mehr in den Kartengrenzen" % name
    assert not _inside(ATLANTIK), "Atlantikpunkt (9 W) darf nicht im Kartenbild liegen"
    # Server-Grenzen im Leaflet-Format passen zu den Konstanten
    assert wg.overlay_bounds() == [[wg.BBOX_S, wg.BBOX_W], [wg.BBOX_N, wg.BBOX_E]]


# ---------------------------------------------------------------------------
# T2 — GRIB-Gitter ueber England
# ---------------------------------------------------------------------------

def _make_grib_england(const: float, Ni: int = 17, Nj: int = 13) -> bytes:
    """GRIB2-Nachricht ueber England: Laenge -6..+2, Breite 53..50, konstanter Wert."""
    import eccodes as ec
    gid = ec.codes_grib_new_from_samples("regular_ll_pl_grib2")
    ec.codes_set(gid, "Ni", Ni)
    ec.codes_set(gid, "Nj", Nj)
    ec.codes_set(gid, "latitudeOfFirstGridPointInDegrees", 53.0)
    ec.codes_set(gid, "longitudeOfFirstGridPointInDegrees", -6.0)
    ec.codes_set(gid, "latitudeOfLastGridPointInDegrees", 50.0)
    ec.codes_set(gid, "longitudeOfLastGridPointInDegrees", 2.0)
    ec.codes_set(gid, "iDirectionIncrementInDegrees", 8.0 / (Ni - 1))
    ec.codes_set(gid, "jDirectionIncrementInDegrees", 3.0 / (Nj - 1))
    ec.codes_set(gid, "jScansPositively", 0)
    ec.codes_set_values(gid, np.full(Ni * Nj, float(const)))
    raw = ec.codes_get_message(gid)
    ec.codes_release(gid)
    return raw


@pytest.mark.offline
@eccodes_required
def test_t2_grib_ueber_england_liefert_stuetzpunkte_westlich_von_null():
    raw = _make_grib_england(42.0)
    samples = []
    pidx = {}
    wg.grib_to_samples(raw, 0, 72, "cloud", samples, pidx, stride=2)
    assert len(samples) > 0
    assert any(s.lon < 0.0 for s in samples), "keine Stuetzpunkte westlich von 0 Grad (England fehlt)"
    for s in samples:
        assert wg.BBOX_S <= s.lat <= wg.BBOX_N
        assert wg.BBOX_W <= s.lon <= wg.BBOX_E
        assert abs(float(s.cloud[0]) - 42.0) < 1e-3


# ---------------------------------------------------------------------------
# T3 / T3b — Bild
# ---------------------------------------------------------------------------

@pytest.mark.offline
@pillow_required
def test_t3_pixel_bei_london_ist_gefaerbt():
    """AK1: Mit einem Stuetzpunkt bei London ist der Pixel dort nicht transparent."""
    xy = _pixel(LONDON)
    assert xy is not None, "London liegt nicht im Bildraster"
    png = _render([_sample(LONDON, 80.0)])
    assert png is not None
    assert _alpha_at(png, xy) > 0


@pytest.mark.offline
@pillow_required
def test_t3b_ausfall_england_bleibt_transparent_rest_gefaerbt():
    """AK4: Nur Deutschland-Stuetzpunkte -> England transparent, Deutschland gefaerbt, Atlantikrand transparent."""
    xy_london = _pixel(LONDON)
    assert xy_london is not None, "London liegt nicht im Bildraster"
    samples = [_sample(BERLIN, 70.0), _sample((51.0, 10.0), 70.0), _sample((53.0, 12.0), 70.0)]
    png = _render(samples)
    assert png is not None
    assert _alpha_at(png, _pixel(BERLIN)) > 0
    assert _alpha_at(png, xy_london) == 0
    rand = _pixel((51.5, wg.BBOX_W + 0.1))
    assert _alpha_at(png, rand) == 0


# ---------------------------------------------------------------------------
# T4 — Deutschland/Oesterreich/Norwegen bleiben gleich (AK3)
# ---------------------------------------------------------------------------

def _grid_samples():
    pts = []
    for lat in np.arange(44.0, 70.5, 1.0):
        for lon in np.arange(4.0, 20.5, 1.0):
            v = 50.0 + 30.0 * np.sin(lat * 0.7) * np.cos(lon * 0.5)
            pts.append(_sample((float(lat), float(lon)), float(v)))
    return pts


def _value_at_nearest_pixel(samples, grid_lat, grid_lon, point):
    j = int(np.argmin(np.abs(grid_lat[:, 0] - point[0])))
    i = int(np.argmin(np.abs(grid_lon[0, :] - point[1])))
    one_lat = grid_lat[j:j + 1, i:i + 1]
    one_lon = grid_lon[j:j + 1, i:i + 1]
    arr = wg.interpolate_idw(samples, 0, "cloud", one_lat, one_lon)
    assert arr is not None and np.isfinite(arr[0, 0])
    return float(arr[0, 0])


@pytest.mark.offline
def test_t4_werte_an_berlin_muenchen_oslo_aendern_sich_hoechstens_2_prozentpunkte():
    samples = _grid_samples()
    new_lat, new_lon = wg._build_grids()
    lons = np.linspace(OLD_W, OLD_E, OLD_PNG_W)
    lats = np.linspace(OLD_N, OLD_S, OLD_PNG_H)
    old_lon, old_lat = np.meshgrid(lons, lats)
    for name, p in (("Berlin", BERLIN), ("Muenchen", MUENCHEN), ("Oslo", OSLO)):
        v_new = _value_at_nearest_pixel(samples, new_lat, new_lon, p)
        v_old = _value_at_nearest_pixel(samples, old_lat, old_lon, p)
        assert abs(v_new - v_old) <= 2.0, "%s: neu %.2f vs. alt %.2f" % (name, v_new, v_old)


# ---------------------------------------------------------------------------
# T5 — Ersatz-Grenzen im Frontend == Server
# ---------------------------------------------------------------------------

@pytest.mark.offline
@pytest.mark.requires_full_checkout
def test_t5_ersatzgrenzen_in_index_html_gleich_serverGrenzen():
    html = (Path(__file__).resolve().parents[2] / "web" / "index.html").read_text(encoding="utf-8")
    m = re.search(
        r"_FALLBACK_BOUNDS:\s*\[\[\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\]\s*,\s*\[\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\]\]",
        html,
    )
    assert m is not None, "_FALLBACK_BOUNDS in web/index.html nicht gefunden"
    fe = [[float(m.group(1)), float(m.group(2))], [float(m.group(3)), float(m.group(4))]]
    assert fe == wg.overlay_bounds()


# ---------------------------------------------------------------------------
# T6 / T7 — Wetter pro Ort (Bestaetigung, kein Umbau)
# ---------------------------------------------------------------------------

def _event(name, lat, lon, shoot_time):
    return {
        "location_name": name,
        "observer_lat": lat,
        "observer_lon": lon,
        "event_type": "Sonnenaufgang",
        "shoot_time": shoot_time.isoformat(),
        "astronomy_score": 0.8,
    }


@pytest.mark.offline
@pytest.mark.api
def test_t6_london_termin_plant_abruf_mit_london_koordinaten():
    pytest.importorskip("fastapi", reason="FastAPI-Stack nicht installiert")
    import main

    now = datetime.now(timezone.utc)
    ev = _event("London Test", 51.507, -0.128, now + timedelta(days=2))
    tasks = main._plan_weather_fetch_tasks([ev])
    weather = [t for t in tasks if t[0] == "weather"]
    assert len(weather) == 1
    kind, key, lat, lon, name = weather[0]
    assert (lat, lon, name) == (51.507, -0.128, "London Test")
    assert key == "51.507,-0.128"

    # Termin in 5 Tagen: ausserhalb T+3 -> planmaessig kein Wetter
    late = _event("London Test", 51.507, -0.128, now + timedelta(days=5))
    cutoff = now + timedelta(days=3)
    assert main._apply_weather_to_event(late, object(), now, cutoff) is False
    assert late["weather_status"] == "none"
    assert late["weather_score"] == 0.0


@pytest.mark.offline
@pytest.mark.api
def test_t7_abruf_fehler_nur_london_andere_orte_behalten_wetter():
    pytest.importorskip("fastapi", reason="FastAPI-Stack nicht installiert")
    import main

    tasks_meta = [
        ("weather", "52.520,13.400", 52.52, 13.40, "Berlin Test"),
        ("weather", "51.507,-0.128", 51.507, -0.128, "London Test"),
    ]
    berlin_fc = object()
    results = [berlin_fc, RuntimeError("HTTP 429")]
    out = main._collect_weather_fetch_results(tasks_meta, results)
    loc_forecasts, failed_locations = out[0], out[5]
    assert loc_forecasts == {"52.520,13.400": berlin_fc}
    assert failed_locations == ["London Test"]
    msg = main._build_weather_error_message(failed_locations, [])
    assert msg is not None and "London Test" in msg and "Berlin Test" not in msg
