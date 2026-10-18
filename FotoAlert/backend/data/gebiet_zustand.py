"""US-141, Baustein 2: Wer ist aktiv, wer ist pausiert? - die Anbindung der zentralen Regel
(data/aktiv_regel.py) an die gespeicherten Schalter (Tabelle area_states) und an die Orte.

Dieses Modul ist die EINE Stelle, die alle Dienste fragen (Feed, Wetter, Kalender, Entdecken,
Vorberechnung). Es kennt:
  - den Zustand der Schalter (über eine beim Start registrierte Lesefunktion; jeder Aufruf liest
    frisch, damit ein Umschalten sofort überall wirkt und Tests eine andere Datenbank einsetzen können),
  - die Zuordnung eines Orts zu Land und Region (gespeichert am Ort; fehlt sie, wird sie aus den
    Koordinaten vorgeschlagen und gemerkt),
  - die Auflistung der Gebiete für das Host-Menü (Ortszahlen, Sammelschalter).

Ohne registrierte Lesefunktion (z. B. im Vorberechnungs-Prozess vor dem Laden) gilt "alles an".

Nur Standardbibliothek, Python 3.9-kompatibel.
"""
from __future__ import annotations

import threading
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

from data import aktiv_regel as _regel
from data import regionen as _reg

_quelle: Optional[Callable[[], dict]] = None
_vorschlag_cache: Dict[Tuple[float, float], Tuple[str, Optional[str]]] = {}
_cache_sperre = threading.Lock()


def registriere_quelle(funktion: Optional[Callable[[], dict]]) -> None:
    """Legt fest, woher der gespeicherte Zustand gelesen wird (liefert {"laender":..., "regionen":...})."""
    global _quelle
    _quelle = funktion


def _roh() -> dict:
    if _quelle is None:
        return {"laender": {}, "regionen": {}}
    try:
        z = _quelle() or {}
    except Exception:
        return {"laender": {}, "regionen": {}}
    return {"laender": dict(z.get("laender") or {}), "regionen": dict(z.get("regionen") or {})}


def wirksame_zustaende(roh: Optional[dict] = None) -> dict:
    """Der gespeicherte Zustand, ergänzt um die Zeile „Ohne Region“ je Land, falls sie fehlt:
    sie gilt dann als an, solange irgendeine Region des Landes an ist (Sammelschalter-Regel)."""
    z = _roh() if roh is None else {"laender": dict(roh.get("laender") or {}),
                                    "regionen": dict(roh.get("regionen") or {})}
    for land, regionen in _reg.REGIONEN.items():
        if not regionen or (land, _reg.OHNE_REGION) in z["regionen"]:
            continue
        z["regionen"][(land, _reg.OHNE_REGION)] = any(bool(z["regionen"].get((land, r), True)) for r in regionen)
    return z


def zustaende() -> dict:
    """Aktueller, wirksamer Zustand aller Schalter."""
    return wirksame_zustaende()


# ── Zuordnung eines Orts ─────────────────────────────────────────────────────

def normiere(land: Optional[str], region: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Land/Region in die gespeicherte Form: Länder ohne Regionen haben keine Region, Länder mit
    Regionen immer eine (fehlend -> „Ohne Region“)."""
    if not land:
        return None, None
    if not _reg.REGIONEN.get(land):
        return land, None
    return land, region or _reg.OHNE_REGION


def vorschlag(lat: Any, lon: Any, name: Any = None) -> _reg.Zuordnung:
    """Vorschlag aus den Koordinaten (wirft nie)."""
    try:
        z = _reg.schlage_region_vor(lat, lon, name)
    except Exception:
        return _reg.Zuordnung(_reg.SONSTIGE, None, False)
    land, region = normiere(z.land, z.region)
    return _reg.Zuordnung(land, region, z.unsicher)


def _vorschlag_gemerkt(lat: Any, lon: Any) -> Tuple[str, Optional[str]]:
    try:
        schluessel = (round(float(lat), 6), round(float(lon), 6))
    except (TypeError, ValueError):
        z = vorschlag(None, None)
        return z.land, z.region
    with _cache_sperre:
        treffer = _vorschlag_cache.get(schluessel)
    if treffer is None:
        z = vorschlag(lat, lon)
        treffer = (z.land, z.region)
        with _cache_sperre:
            if len(_vorschlag_cache) > 5000:
                _vorschlag_cache.clear()
            _vorschlag_cache[schluessel] = treffer
    return treffer


def _merkmal(ort: Any, name: str) -> Any:
    return ort.get(name) if isinstance(ort, dict) else getattr(ort, name, None)


def gebiet_des_ortes(ort: Any) -> Tuple[str, Optional[str]]:
    """(Land, Region) eines Orts: gespeicherte Angabe, sonst Vorschlag aus den Koordinaten."""
    land = _merkmal(ort, "land")
    if land:
        return normiere(land, _merkmal(ort, "region"))
    return _vorschlag_gemerkt(_merkmal(ort, "observer_lat"), _merkmal(ort, "observer_lon"))


def als_regelort(ort: Any) -> dict:
    """Der Ort in der Form, die data.aktiv_regel erwartet."""
    land, region = gebiet_des_ortes(ort)
    return {"id": _merkmal(ort, "id"), "land": land, "region": region}


def ist_aktiv(ort: Any, z: Optional[dict] = None) -> bool:
    """Darf dieser Ort berechnet werden? (Gruppe B)"""
    return _regel.ist_aktiv(als_regelort(ort), zustaende() if z is None else z)


def ist_pausiert(ort: Any, z: Optional[dict] = None) -> bool:
    return not ist_aktiv(ort, z)


def pausierte_ids(orte: Iterable[Any], z: Optional[dict] = None) -> set:
    z = zustaende() if z is None else z
    return {_merkmal(o, "id") for o in orte if not ist_aktiv(o, z)}


def aktive_orte(orte: Iterable[Any], z: Optional[dict] = None) -> List[Any]:
    z = zustaende() if z is None else z
    return [o for o in orte if ist_aktiv(o, z)]


def gebiet_ist_an(land: Optional[str], region: Optional[str], z: Optional[dict] = None) -> bool:
    """Ist dieses Gebiet (Land + Region) eingeschaltet? Für neue Orte."""
    land, region = normiere(land, region)
    z = zustaende() if z is None else z
    return _regel.ist_aktiv({"land": land, "region": region}, z)


# ── Liste für das Host-Menü ─────────────────────────────────────────────────

def de_schluessel(name: str) -> str:
    return (name.lower().replace("ä", "a").replace("ö", "o").replace("ü", "u").replace("ß", "ss"))


def _an_aus(wert: Any) -> str:
    return _regel.ZUSTAND_AN if bool(wert) else _regel.ZUSTAND_AUS


def gebietsliste(orte: Iterable[Any], z: Optional[dict] = None) -> dict:
    """Alle Länder mit Regionen, Zustand und Ortszahlen („aktiv von gesamt“).

    Land: zustand an/aus/teilweise; Region: an/aus. „Ohne Region“ erscheint am Ende der Regionen
    eines Landes, sobald dort ein Ort ohne Region liegt. Länder ohne Regionen („Sonstige“) haben
    nur ihren eigenen Schalter."""
    z = zustaende() if z is None else z
    zaehler: Dict[Tuple[str, str], List[int]] = {}
    for o in orte:
        land, region = gebiet_des_ortes(o)
        eintrag = zaehler.setdefault((land, region or ""), [0, 0])
        eintrag[1] += 1
        if _regel.ist_aktiv({"land": land, "region": region}, z):
            eintrag[0] += 1
    laender = []
    for land, regionen in _reg.REGIONEN.items():
        if regionen:
            liste = []
            for r in sorted(regionen, key=de_schluessel):
                a, g = zaehler.get((land, r), [0, 0])
                liste.append({"name": r, "zustand": _an_aus(z["regionen"].get((land, r), True)),
                              "aktiv": a, "gesamt": g})
            a, g = zaehler.get((land, _reg.OHNE_REGION), [0, 0])
            if g > 0:
                liste.append({"name": _reg.OHNE_REGION,
                              "zustand": _an_aus(z["regionen"].get((land, _reg.OHNE_REGION), True)),
                              "aktiv": a, "gesamt": g})
            zust = _regel.land_zustand(land, [r["name"] for r in liste], z)
            aktiv, gesamt = sum(r["aktiv"] for r in liste), sum(r["gesamt"] for r in liste)
        else:
            liste = []
            zust = _regel.land_zustand(land, [], z)
            aktiv, gesamt = zaehler.get((land, ""), [0, 0])
        laender.append({"name": land, "zustand": zust, "aktiv": aktiv, "gesamt": gesamt, "regionen": liste})
    return {"laender": laender}


def eintraege_fuer_land(land: str, an: bool) -> List[Tuple[str, str, bool]]:
    """Was in die Tabelle geschrieben wird, wenn das Land (Sammelschalter) umgeschaltet wird:
    Land mit Regionen -> alle seine Regionen (+ „Ohne Region“); ein vorhandener Land-Eintrag wird auf
    „an“ gesetzt (ein Land-Eintrag „aus“ würde einzeln eingeschaltete Regionen blockieren).
    Land ohne Regionen -> sein eigener Zustand. Unbekanntes Land -> KeyError."""
    regionen = _reg.REGIONEN.get(land)
    if regionen is None:
        raise KeyError(land)
    if not regionen:
        return [(land, "", bool(an))]
    eintraege = [(land, r, bool(an)) for r in regionen]
    eintraege.append((land, _reg.OHNE_REGION, bool(an)))
    eintraege.append((land, "", True))
    return eintraege


def eintraege_fuer_region(land: str, region: str, an: bool) -> List[Tuple[str, str, bool]]:
    """Unbekanntes Land/Region (oder Land ohne Regionen) -> KeyError."""
    regionen = _reg.REGIONEN.get(land)
    if not regionen:
        raise KeyError(land)
    if region != _reg.OHNE_REGION and region not in regionen:
        raise KeyError(region)
    return [(land, region, bool(an))]
