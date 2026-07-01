"""US-112: Wetter-Overlay aus echten Modelldaten als weicher Verlauf.

Datenquellen (alle gratis + kommerziell nutzbar):
  - DWD ICON-D2  (~2 km), Vorhersagestunden 0–48 h, GRIB2 von opendata.dwd.de
  - DWD ICON-EU  (~7 km), Vorhersagestunden 48–72 h, GRIB2 (deckt ganz Europa)
  - MET Norway Locationforecast 2.0 (Punkt-API, JSON) für Norwegen
    (ICON-D2/-EU-Schärfe für Norwegen bewusst über MET-Punkte ergänzt)

Felder:
  - Wolkendecke:  DWD CLCT (total cloud cover %)
  - Niederschlag: DWD TOT_PREC (akkumuliert mm → pro Stunde differenziert)
  - MET: cloud_area_fraction (%) + precipitation_amount (mm/h)

Ausgabe: pro Vorhersagestunde ein serverseitig interpoliertes PNG (IDW über die
zusammengeführten Stützpunkte), das im Frontend via L.imageOverlay als weicher
Verlauf eingeblendet wird. KEIN Kachelraster, kein fremder Tile-Provider.

Lizenz-/Pflicht-Hinweise:
  - Attribution Pflicht: "Daten: DWD · MET Norway (CC BY 4.0)" (Frontend).
  - MET Norway: eigener User-Agent mit App-Name + Kontakt, Caching gemäß
    Expires/If-Modified-Since, Rate-Limit respektieren.

Python 3.9-kompatibel (Prod läuft 3.9): kein `X | Y`, kein match-Statement.

GRIB-Verarbeitung braucht die eccodes-Bibliothek. Der reine Python-Pfad
(numpy + Pillow) erzeugt das PNG; eccodes wird nur zum Dekodieren der GRIB2-
Nachrichten benötigt und ist optional importiert, damit die App auch ohne
installierte GRIB-Toolchain startet (dann fällt das Overlay auf MET-only bzw.
"keine Daten" zurück, statt zu crashen).
"""

from __future__ import annotations

import asyncio
import bz2
import io
import logging
import math
import re
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple

import numpy as np

logger = logging.getLogger(__name__)

# eccodes ist optional — fehlt die GRIB-Toolchain, bleibt die App lauffähig.
try:
    import eccodes as _ec  # type: ignore
    HAVE_ECCODES = True
except Exception as _e:  # pragma: no cover - hängt von Server-Install ab
    _ec = None
    HAVE_ECCODES = False
    logger.warning("eccodes nicht verfügbar (%s) — GRIB-Wetter-Overlay deaktiviert.", _e)

try:
    from PIL import Image  # type: ignore
    HAVE_PIL = True
except Exception as _e:  # pragma: no cover
    Image = None
    HAVE_PIL = False
    logger.warning("Pillow nicht verfügbar (%s) — Wetter-PNG-Rendering deaktiviert.", _e)


# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------

DWD_OPENDATA = "https://opendata.dwd.de/weather/nwp"

# Geltungsbereich (Bounding-Box des Overlays): DE + AT + Norditalien + Norwegen.
# Süd 43.0 (Po-Ebene), Nord 71.5 (Nordnorwegen), West 3.0, Ost 21.0.
BBOX_S = 43.0
BBOX_N = 71.5
BBOX_W = 3.0
BBOX_E = 21.0

# Render-Auflösung des PNG (Pixel). Bewusst moderat — weicher Verlauf, kleine
# Dateien, schneller Render. Seitenverhältnis grob an die BBox angelehnt.
PNG_W = 360
PNG_H = 420

# IDW-Interpolation
_IDW_POWER = 2.0
_IDW_NEIGHBORS = 12

# MET Norway: Stützpunkte für Norwegen (ICON-D2/-EU deckt NO nicht in 2 km).
# Grobes Gitter über das norwegische Festland; bewusst sparsam (Rate-Limit).
MET_NORWAY_POINTS: List[Tuple[float, float]] = [
    (58.0, 7.5), (58.5, 6.0), (59.0, 9.0), (59.9, 10.7),   # Süden + Oslo
    (60.4, 5.3), (61.0, 8.5), (62.0, 6.5), (62.5, 11.0),   # Bergen-Region + Mitte
    (63.4, 10.4), (64.5, 12.0), (65.5, 13.5), (67.3, 14.4),# Trondheim + Norden
    (68.4, 17.4), (69.6, 18.9), (70.0, 23.0), (70.7, 25.0),# Nordnorwegen
]

MET_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"
# Pflicht-User-Agent (App-Name + Kontakt). Version wird vom Aufrufer gesetzt.
MET_USER_AGENT_DEFAULT = "FotoAlert/2.0 (https://github.com/ kontakt: stephanschumann@me.com)"

# Farb-Stopps spiegeln das Frontend (clouds / precip). [(wert, (r,g,b))].
_CLOUD_STOPS = [
    (0.0,   (200, 232, 255)),
    (25.0,  (176, 200, 216)),
    (50.0,  (140, 168, 184)),
    (75.0,  (96, 120, 136)),
    (100.0, (56, 72, 88)),
]
_PRECIP_STOPS = [
    (0.0,   (234, 244, 255)),
    (0.5,   (125, 196, 240)),
    (2.0,   (52, 152, 219)),
    (5.0,   (30, 95, 168)),
    (10.0,  (10, 45, 107)),
]


# ---------------------------------------------------------------------------
# Datenstruktur eines Stützpunktes
# ---------------------------------------------------------------------------

class SamplePoint:
    """Ein Stützpunkt mit Stundenreihen (gemeinsame 72-h-Achse)."""

    __slots__ = ("lat", "lon", "cloud", "precip")

    def __init__(self, lat: float, lon: float, n_hours: int):
        self.lat = lat
        self.lon = lon
        # NaN = kein Wert für diese Stunde (wird bei IDW ignoriert)
        self.cloud = np.full(n_hours, np.nan, dtype=np.float32)
        self.precip = np.full(n_hours, np.nan, dtype=np.float32)


# ---------------------------------------------------------------------------
# GRIB-Dekodierung (eccodes, Low-Level — kein xarray/scipy nötig)
# ---------------------------------------------------------------------------

def decode_grib_message(raw: bytes) -> Optional[dict]:
    """Dekodiert die ERSTE GRIB-Nachricht aus `raw` (regular_ll erwartet).

    Liefert dict mit lats, lons (1-D, Länge Ni bzw. Nj), values (Ni*Nj, row-major)
    und Geometrie. Gibt None zurück wenn eccodes fehlt oder das Dekodieren scheitert.
    """
    if not HAVE_ECCODES:
        return None
    gid = None
    try:
        gid = _ec.codes_new_from_message(raw)
        Ni = int(_ec.codes_get(gid, "Ni"))
        Nj = int(_ec.codes_get(gid, "Nj"))
        lat1 = float(_ec.codes_get(gid, "latitudeOfFirstGridPointInDegrees"))
        lat2 = float(_ec.codes_get(gid, "latitudeOfLastGridPointInDegrees"))
        lon1 = float(_ec.codes_get(gid, "longitudeOfFirstGridPointInDegrees"))
        lon2 = float(_ec.codes_get(gid, "longitudeOfLastGridPointInDegrees"))
        values = np.array(_ec.codes_get_values(gid), dtype=np.float32)
        # Längengrade > 180 auf -180..180 normalisieren (DWD nutzt teils 0..360)
        if lon1 > 180:
            lon1 -= 360.0
        if lon2 > 180:
            lon2 -= 360.0
        lats = np.linspace(lat1, lat2, Nj)
        lons = np.linspace(lon1, lon2, Ni)
        return {"Ni": Ni, "Nj": Nj, "lats": lats, "lons": lons, "values": values}
    except Exception as exc:  # pragma: no cover - GRIB-spezifisch
        logger.warning("GRIB-Dekodierung fehlgeschlagen: %s", exc)
        return None
    finally:
        if gid is not None:
            try:
                _ec.codes_release(gid)
            except Exception:
                pass


def maybe_bunzip(raw: bytes) -> bytes:
    """DWD liefert GRIB2 bz2-komprimiert (.grib2.bz2). Transparent entpacken."""
    if raw[:3] == b"BZh":
        try:
            return bz2.decompress(raw)
        except Exception:
            return raw
    return raw


def grib_to_samples(
    raw: bytes,
    hour_index: int,
    n_hours: int,
    field: str,
    samples: List[SamplePoint],
    point_index: Dict[Tuple[float, float], int],
    stride: int = 6,
) -> None:
    """Trägt die Werte EINER GRIB-Nachricht als Stützpunkte für `hour_index` ein.

    `field` ∈ {"cloud", "precip"}. Das DWD-Gitter wird per `stride` ausgedünnt
    (jeder n-te Punkt) — feines 2-km-Gitter über die ganze BBox wären sonst
    Hunderttausende Punkte. Stride ~6 hält die ~12 km-Stützweite (für den
    weichen Verlauf völlig ausreichend) bei tragbarer Last.
    """
    dec = decode_grib_message(maybe_bunzip(raw))
    if dec is None:
        return
    Ni, Nj = dec["Ni"], dec["Nj"]
    lats, lons, vals = dec["lats"], dec["lons"], dec["values"]
    vals = vals.reshape(Nj, Ni)
    for j in range(0, Nj, stride):
        la = float(lats[j])
        if la < BBOX_S or la > BBOX_N:
            continue
        for i in range(0, Ni, stride):
            lo = float(lons[i])
            if lo < BBOX_W or lo > BBOX_E:
                continue
            v = float(vals[j, i])
            if not math.isfinite(v):
                continue
            key = (round(la, 3), round(lo, 3))
            idx = point_index.get(key)
            if idx is None:
                idx = len(samples)
                point_index[key] = idx
                samples.append(SamplePoint(la, lo, n_hours))
            sp = samples[idx]
            if field == "cloud":
                sp.cloud[hour_index] = v
            else:
                sp.precip[hour_index] = v


# ---------------------------------------------------------------------------
# DWD-Download
# ---------------------------------------------------------------------------

def _latest_run(now_utc: datetime, step_hours: int, delay_hours: int) -> datetime:
    """Bestimmt den letzten verfügbaren Modelllauf (UTC, abgerundet auf step_hours).

    `delay_hours` = grober Bereitstellungs-Vorlauf (DWD braucht ~2–3 h nach Lauf).
    """
    t = now_utc - timedelta(hours=delay_hours)
    run_hour = (t.hour // step_hours) * step_hours
    return t.replace(hour=run_hour, minute=0, second=0, microsecond=0)


def _dwd_url(model: str, run: datetime, param: str, fchour: int) -> str:
    """Baut die DWD-Open-Data-URL für eine GRIB2-Datei.

    Beispiel ICON-D2:
      .../icon-d2/grib/00/clct/icon-d2_germany_regular-lat-lon_single-level_2026063000_006_2d_clct.grib2.bz2
    Die genauen Dateinamen variieren leicht je Parameter; der Download-Layer
    probiert daher mehrere Namensvarianten (siehe fetch_dwd_field).
    """
    rr = "%02d" % run.hour
    ymdh = run.strftime("%Y%m%d%H")
    # Reale DWD-Open-Data-Namensschemata (am Live-Verzeichnis verifiziert 2026-07-01):
    #   ICON-D2:  icon-d2_germany_regular-lat-lon_single-level_<run>_<fc>_2d_<param_klein>.grib2.bz2
    #   ICON-EU:  icon-eu_europe_regular-lat-lon_single-level_<run>_<fc>_<PARAM_GROSS>.grib2.bz2
    # Verzeichnis-Unterordner ist bei beiden Modellen kleingeschrieben (param).
    if model == "icon-d2":
        fname = "icon-d2_germany_regular-lat-lon_single-level_%s_%03d_2d_%s.grib2.bz2" % (
            ymdh, fchour, param,
        )
    else:  # icon-eu
        fname = "icon-eu_europe_regular-lat-lon_single-level_%s_%03d_%s.grib2.bz2" % (
            ymdh, fchour, param.upper(),
        )
    return "%s/%s/grib/%s/%s/%s" % (DWD_OPENDATA, model, rr, param, fname)


async def _http_get_bytes(client, url: str, headers: Optional[dict] = None) -> Optional[bytes]:
    try:
        resp = await client.get(url, headers=headers or {}, timeout=30.0)
        if resp.status_code == 200:
            return resp.content
        return None
    except Exception as exc:
        logger.debug("DWD/HTTP GET fehlgeschlagen (%s): %s", url, exc)
        return None


async def fetch_dwd_field(
    client,
    model: str,
    run: datetime,
    param: str,
    fc_hours: List[int],
    field: str,
    n_hours: int,
    hour_offset: int,
    samples: List[SamplePoint],
    point_index: Dict[Tuple[float, float], int],
) -> int:
    """Lädt für ein Modell/Parameter mehrere Vorhersagestunden und trägt sie ein.

    `fc_hours`     = Liste Vorhersagestunden des Modelllaufs (relativ zum Run).
    `hour_offset`  = wie viele Stunden der Run vor der Overlay-Achse-Stunde 0 liegt.
    Liefert die Anzahl erfolgreich geladener Stunden (für Diagnose/Null-Handling).
    """
    loaded = 0
    for fc in fc_hours:
        target_idx = fc - hour_offset
        if target_idx < 0 or target_idx >= n_hours:
            continue
        url = _dwd_url(model, run, param, fc)
        raw = await _http_get_bytes(client, url)
        if raw is None:
            continue
        grib_to_samples(raw, target_idx, n_hours, field, samples, point_index)
        loaded += 1
    return loaded


# ---------------------------------------------------------------------------
# MET Norway
# ---------------------------------------------------------------------------

async def fetch_met_norway(
    client,
    base_time: datetime,
    n_hours: int,
    samples: List[SamplePoint],
    point_index: Dict[Tuple[float, float], int],
    user_agent: str,
) -> int:
    """Holt MET-Norway-Punktvorhersagen für die Norwegen-Stützpunkte.

    Trägt cloud_area_fraction (%) und precipitation_amount (mm/h) auf die
    gemeinsame Stundenachse ein. Respektiert den Pflicht-User-Agent.
    Liefert die Anzahl erfolgreich abgefragter Punkte.
    """
    ok = 0
    headers = {"User-Agent": user_agent, "Accept": "application/json"}
    for (lat, lon) in MET_NORWAY_POINTS:
        url = "%s?lat=%.3f&lon=%.3f" % (MET_URL, lat, lon)
        try:
            resp = await client.get(url, headers=headers, timeout=20.0)
            if resp.status_code != 200:
                continue
            data = resp.json()
        except Exception as exc:
            logger.debug("MET Norway GET fehlgeschlagen (%s,%s): %s", lat, lon, exc)
            continue
        key = (round(lat, 3), round(lon, 3))
        idx = point_index.get(key)
        if idx is None:
            idx = len(samples)
            point_index[key] = idx
            samples.append(SamplePoint(lat, lon, n_hours))
        sp = samples[idx]
        try:
            ts = data["properties"]["timeseries"]
        except Exception:
            continue
        for entry in ts:
            try:
                t = datetime.fromisoformat(entry["time"].replace("Z", "+00:00"))
            except Exception:
                continue
            hidx = int(round((t - base_time).total_seconds() / 3600.0))
            if hidx < 0 or hidx >= n_hours:
                continue
            inst = entry.get("data", {}).get("instant", {}).get("details", {})
            cloud = inst.get("cloud_area_fraction")
            if cloud is not None:
                sp.cloud[hidx] = float(cloud)
            nxt1 = entry.get("data", {}).get("next_1_hours", {})
            precip = nxt1.get("details", {}).get("precipitation_amount")
            if precip is not None:
                sp.precip[hidx] = float(precip)
        ok += 1
    return ok


# ---------------------------------------------------------------------------
# Niederschlag akkumuliert → pro Stunde (DWD TOT_PREC)
# ---------------------------------------------------------------------------

def deaccumulate_precip(samples: List[SamplePoint], dwd_max_idx: int) -> None:
    """DWD TOT_PREC ist akkumuliert (mm seit Lauf-Start). Pro Stunde = Differenz
    aufeinanderfolgender Schritte. MET liefert bereits mm/h → nur DWD-Indizes
    (0..dwd_max_idx) differenzieren. NaN-Lücken bleiben NaN.
    """
    for sp in samples:
        prev = None
        for i in range(0, min(dwd_max_idx + 1, sp.precip.shape[0])):
            cur = sp.precip[i]
            if math.isnan(cur):
                prev = None
                continue
            if prev is None:
                hourly = cur  # erster bekannter Schritt: als-ist
            else:
                hourly = max(0.0, cur - prev)
            prev = cur
            sp.precip[i] = hourly


# ---------------------------------------------------------------------------
# IDW-Interpolation → 2-D-Feld → PNG
# ---------------------------------------------------------------------------

def _build_grids() -> Tuple[np.ndarray, np.ndarray]:
    """Pixel-Mittelpunkt-Koordinaten (lat, lon) des Ziel-PNG."""
    lats = np.linspace(BBOX_N, BBOX_S, PNG_H)   # oben = Nord
    lons = np.linspace(BBOX_W, BBOX_E, PNG_W)
    grid_lon, grid_lat = np.meshgrid(lons, lats)
    return grid_lat, grid_lon


def interpolate_idw(
    samples: List[SamplePoint],
    hour_index: int,
    field: str,
    grid_lat: np.ndarray,
    grid_lon: np.ndarray,
) -> Optional[np.ndarray]:
    """IDW-Interpolation der Stützpunkt-Werte einer Stunde auf das PNG-Gitter.

    Liefert ein 2-D-Array (PNG_H × PNG_W) mit Werten, NaN wo zu weit von jedem
    Stützpunkt entfernt (→ transparent). None wenn keine Stützpunkte vorhanden.
    """
    pts_lat = []
    pts_lon = []
    pts_val = []
    for sp in samples:
        v = sp.cloud[hour_index] if field == "cloud" else sp.precip[hour_index]
        if v is None or (isinstance(v, float) and math.isnan(v)) or math.isnan(float(v)):
            continue
        pts_lat.append(sp.lat)
        pts_lon.append(sp.lon)
        pts_val.append(float(v))
    if not pts_val:
        return None

    plat = np.array(pts_lat, dtype=np.float32)
    plon = np.array(pts_lon, dtype=np.float32)
    pval = np.array(pts_val, dtype=np.float32)

    flat_lat = grid_lat.reshape(-1)
    flat_lon = grid_lon.reshape(-1)
    out = np.full(flat_lat.shape, np.nan, dtype=np.float32)

    # Distanz-Cutoff: jenseits ~150 km vom nächsten Stützpunkt → transparent
    # (kein Wert "erfunden", keine Fehlfarben-Löcher, kein harter Block).
    max_dist2 = (1.5) ** 2  # in Grad² (~1.5° ≈ 150 km lat)

    # Blockweise, um Speicher zu schonen (Distanzmatrix = BLOCK × Stützpunkte).
    # Beim echten 2-km-Gitter entstehen ~35k Stützpunkte; BLOCK=4096 ergab eine
    # Matrix von mehreren GB → OOM auf dem Server (US-112, 2026-07-01). Kleinerer
    # BLOCK begrenzt den Spitzenspeicher hart, ohne das Ergebnis zu verändern.
    n_pix = flat_lat.shape[0]
    BLOCK = 256
    k = min(_IDW_NEIGHBORS, plat.shape[0])
    for start in range(0, n_pix, BLOCK):
        end = min(start + BLOCK, n_pix)
        gl = flat_lat[start:end][:, None]
        go = flat_lon[start:end][:, None]
        # Längengrad-Distanz mit cos(lat)-Korrektur grob gewichten
        coslat = np.cos(np.radians(gl))
        d2 = (gl - plat[None, :]) ** 2 + ((go - plon[None, :]) * coslat) ** 2
        nearest = np.min(d2, axis=1)
        # k nächste Nachbarn
        if k < d2.shape[1]:
            part = np.argpartition(d2, k, axis=1)[:, :k]
            rows = np.arange(d2.shape[0])[:, None]
            d2k = d2[rows, part]
            valk = pval[part]
        else:
            d2k = d2
            valk = np.broadcast_to(pval[None, :], d2.shape)
        d2k = np.maximum(d2k, 1e-9)
        w = 1.0 / np.power(d2k, _IDW_POWER / 2.0)
        interp = np.sum(w * valk, axis=1) / np.sum(w, axis=1)
        interp[nearest > max_dist2] = np.nan
        out[start:end] = interp

    return out.reshape(grid_lat.shape)


def _color_for(value: float, stops: List[Tuple[float, Tuple[int, int, int]]]) -> Tuple[int, int, int]:
    if value >= stops[-1][0]:
        return stops[-1][1]
    if value <= stops[0][0]:
        return stops[0][1]
    for i in range(len(stops) - 1):
        v0, c0 = stops[i]
        v1, c1 = stops[i + 1]
        if value <= v1:
            t = (value - v0) / (v1 - v0) if v1 > v0 else 0.0
            return (
                int(round(c0[0] + (c1[0] - c0[0]) * t)),
                int(round(c0[1] + (c1[1] - c0[1]) * t)),
                int(round(c0[2] + (c1[2] - c0[2]) * t)),
            )
    return stops[-1][1]


def field_to_png(
    arr: Optional[np.ndarray],
    field: str,
    alpha: int = 150,
) -> Optional[bytes]:
    """Wandelt ein interpoliertes 2-D-Feld in ein RGBA-PNG (weicher Verlauf).

    NaN-Pixel werden voll transparent (kein Loch mit Fehlfarbe). `alpha` ist die
    Deckkraft der gefüllten Pixel (Overlay-Transparenz). Liefert PNG-Bytes oder
    None wenn kein Feld / Pillow fehlt.
    """
    if arr is None or not HAVE_PIL:
        return None
    stops = _CLOUD_STOPS if field == "cloud" else _PRECIP_STOPS
    h, w = arr.shape
    rgba = np.zeros((h, w, 4), dtype=np.uint8)

    # Vektorisiert über die Farbstopps: pro Pixel den interpolierten RGB bestimmen.
    finite = np.isfinite(arr)
    if not finite.any():
        return None
    vals = np.clip(np.nan_to_num(arr, nan=0.0), stops[0][0], stops[-1][0])

    # Stop-Arrays
    sv = np.array([s[0] for s in stops], dtype=np.float32)
    sr = np.array([s[1][0] for s in stops], dtype=np.float32)
    sg = np.array([s[1][1] for s in stops], dtype=np.float32)
    sb = np.array([s[1][2] for s in stops], dtype=np.float32)
    r = np.interp(vals, sv, sr).astype(np.uint8)
    g = np.interp(vals, sv, sg).astype(np.uint8)
    b = np.interp(vals, sv, sb).astype(np.uint8)

    # Niederschlag: sehr trockene Pixel (≈0 mm) fast transparent lassen, damit
    # die Karte nicht flächig blau überzogen wird.
    a = np.where(finite, alpha, 0).astype(np.uint8)
    if field == "precip":
        dry = finite & (arr < 0.05)
        a = np.where(dry, 0, a).astype(np.uint8)

    rgba[..., 0] = r
    rgba[..., 1] = g
    rgba[..., 2] = b
    rgba[..., 3] = a

    img = Image.fromarray(rgba, mode="RGBA")
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Orchestrierung
# ---------------------------------------------------------------------------

def overlay_bounds() -> List[List[float]]:
    """Leaflet-Bounds [[S,W],[N,E]] des Overlay-Bildes (für L.imageOverlay)."""
    return [[BBOX_S, BBOX_W], [BBOX_N, BBOX_E]]


async def build_weather_overlay(
    client,
    n_hours: int = 72,
    user_agent: str = MET_USER_AGENT_DEFAULT,
    base_time: Optional[datetime] = None,
) -> dict:
    """Baut das komplette Overlay-Datenpaket (ohne PNG-Encoding).

    Lädt DWD ICON-D2 (0–48 h) + ICON-EU (48–72 h) + MET Norway, führt alles auf
    eine gemeinsame Stundenachse (base_time + 0..n_hours-1) zusammen und liefert
    die interpolierten 2-D-Felder je Stunde + Achse + Quellen-Status.

    Robust: fällt eine Quelle aus, bleiben die anderen gültig (kein Raise).
    """
    now = base_time or datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    samples: List[SamplePoint] = []
    point_index: Dict[Tuple[float, float], int] = {}

    sources = {"icon_d2": 0, "icon_eu": 0, "met": 0}

    if HAVE_ECCODES:
        # ICON-D2: 3-stündliche Läufe, stündlich bis +48 h.
        run_d2 = _latest_run(now, step_hours=3, delay_hours=3)
        off_d2 = int(round((now - run_d2).total_seconds() / 3600.0))
        fc_d2 = list(range(off_d2, off_d2 + min(n_hours, 48)))
        try:
            sources["icon_d2"] += await fetch_dwd_field(
                client, "icon-d2", run_d2, "clct", fc_d2, "cloud", n_hours, off_d2, samples, point_index)
            sources["icon_d2"] += await fetch_dwd_field(
                client, "icon-d2", run_d2, "tot_prec", fc_d2, "precip", n_hours, off_d2, samples, point_index)
        except Exception as exc:
            logger.warning("ICON-D2-Abruf fehlgeschlagen: %s", exc)

        # ICON-EU: 3-stündliche Läufe, für 48–72 h.
        if n_hours > 48:
            run_eu = _latest_run(now, step_hours=3, delay_hours=4)
            off_eu = int(round((now - run_eu).total_seconds() / 3600.0))
            fc_eu = list(range(off_eu + 48, off_eu + n_hours))
            try:
                sources["icon_eu"] += await fetch_dwd_field(
                    client, "icon-eu", run_eu, "clct", fc_eu, "cloud", n_hours, off_eu, samples, point_index)
                sources["icon_eu"] += await fetch_dwd_field(
                    client, "icon-eu", run_eu, "tot_prec", fc_eu, "precip", n_hours, off_eu, samples, point_index)
            except Exception as exc:
                logger.warning("ICON-EU-Abruf fehlgeschlagen: %s", exc)

        # DWD TOT_PREC akkumuliert → pro Stunde
        deaccumulate_precip(samples, dwd_max_idx=n_hours - 1)

    # MET Norway (Norwegen) — unabhängig von eccodes.
    try:
        sources["met"] = await fetch_met_norway(client, now, n_hours, samples, point_index, user_agent)
    except Exception as exc:
        logger.warning("MET-Norway-Abruf fehlgeschlagen: %s", exc)

    # Gemeinsame Stundenachse (UTC, ISO)
    hourly_times = [(now + timedelta(hours=h)).isoformat() for h in range(n_hours)]

    return {
        "now": now,
        "samples": samples,
        "hourly_times": hourly_times,
        "sources": sources,
        "n_points": len(samples),
    }


def render_all_pngs(overlay: dict, field: str) -> List[Optional[bytes]]:
    """Erzeugt pro Stunde ein PNG für `field` ∈ {"cloud","precip"}.

    Liefert eine Liste PNG-Bytes (oder None je Stunde ohne Daten).
    """
    samples = overlay["samples"]
    n_hours = len(overlay["hourly_times"])
    grid_lat, grid_lon = _build_grids()
    out: List[Optional[bytes]] = []
    for h in range(n_hours):
        arr = interpolate_idw(samples, h, field, grid_lat, grid_lon)
        out.append(field_to_png(arr, field))
    return out
