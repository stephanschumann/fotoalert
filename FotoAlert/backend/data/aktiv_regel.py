"""US-141 / BUG-118, Baustein 1: die EINE zentrale Regel „Wird dieser Ort berechnet?“.

Alle Dienste (Vorberechnung, Feed, Kalender, Entdecken, Wetter ...) fragen diese Stelle, statt
eigene Ausschlusslisten zu führen. Die Funktionen sind rein: kein Zugriff auf Datenbank, Dateien
oder Server; Eingabe sind Orte und der gespeicherte Zustand von Land und Region.

Begriffe (Ticket US-141, Entscheidungen vom 2026-10-11):
  - gelöscht   : Lösch-Markierung (BUG-118). Ein gelöschter Ort erscheint nirgends und wird nie berechnet.
  - aktiv      : nicht gelöscht UND Land an UND Region an. Fehlende Angabe heißt „an“ (Rückwärts-
                 verträglichkeit, AK-56): Orte ohne Land/Region und Gebiete ohne gespeicherten Zustand
                 sind aktiv — vor dem ersten Schalten verhält sich alles wie bisher.
  - pausiert   : nicht gelöscht, aber Land oder Region aus. Pausierte Orte bleiben sichtbar, suchbar und
                 bearbeitbar; es ruhen nur die Berechnungsdienste (Gruppe B). Die Ortsdaten-Dienste
                 (Höhe, Sichtachse, Qualitätsprüfung; Gruppe A) laufen weiter.

Form des Zustands (`zustaende`), alles optional:
    {"laender":  {"Deutschland": True, "Sonstige": False},
     "regionen": {("Deutschland", "Berlin"): True, ("Deutschland", "Brandenburg"): False}}
Der Zustand des Landes wird aus seinen Regionen abgeleitet (Sammelschalter, Frage 25: an / aus /
teilweise, siehe land_zustand); einen eigenen Land-Eintrag brauchen nur Länder ohne Regionen
(„Sonstige“) oder ein ausdrücklich ausgeschaltetes Land.

Orte dürfen Wörterbücher oder Objekte sein (z. B. PhotoLocation mit den Merkmalen land/region/
deleted); reine Nummern (Text) gelten als Ort ohne Angaben, also als aktiv und nicht gelöscht.

Nur Standardbibliothek, Python 3.9-kompatibel.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

ZUSTAND_AN = "an"
ZUSTAND_AUS = "aus"
ZUSTAND_TEILWEISE = "teilweise"


def _merkmal(ort: Any, name: str, standard: Any = None) -> Any:
    if ort is None or isinstance(ort, str):
        return standard
    if isinstance(ort, dict):
        return ort.get(name, standard)
    return getattr(ort, name, standard)


def _ist_an(wert: Any) -> bool:
    """Fehlende Angabe (None) heißt „an“."""
    return True if wert is None else bool(wert)


def ist_geloescht(zustand: Any) -> bool:
    """Trägt dieser Ort / dieses Korrektur-Objekt die Lösch-Markierung (`deleted`)?"""
    return bool(_merkmal(zustand, "deleted", False))


def geloeschte_ids(ueberschreibungen: Optional[Iterable[dict]]) -> set:
    """Nummern aller Orte mit Lösch-Markierung, aus den Korrekturen (Zeilen mit `id` und `deleted`)."""
    return {u.get("id") for u in (ueberschreibungen or []) if isinstance(u, dict) and ist_geloescht(u) and u.get("id")}


def ist_aktiv(ort: Any, zustaende: Optional[dict] = None) -> bool:
    """Darf dieser Ort berechnet werden? (aktiv = nicht gelöscht, Land an, Region an; fehlend = an)."""
    if ort is None:
        return True
    if ist_geloescht(ort):
        return False
    zustaende = zustaende or {}
    land = _merkmal(ort, "land")
    region = _merkmal(ort, "region")
    if land and not _ist_an((zustaende.get("laender") or {}).get(land)):
        return False
    if land and region and not _ist_an((zustaende.get("regionen") or {}).get((land, region))):
        return False
    return True


def ids_fuer_berechnung(orte: Iterable[Any], zustaende: Optional[dict] = None) -> List[Any]:
    """Gruppe B (Feed, Wetter, Kalender, Entdecken): nur aktive Orte, Reihenfolge bleibt erhalten.
    Gibt die Einträge der Eingabe zurück (Orte bzw. Nummern), nicht neu gebaute Werte."""
    return [o for o in orte if ist_aktiv(o, zustaende)]


def ids_fuer_ortsdaten(orte: Iterable[Any], zustaende: Optional[dict] = None) -> List[Any]:
    """Gruppe A (Höhe, Sichtachse, Qualitätsprüfung): alle nicht gelöschten Orte, auch pausierte.
    Der Zustand von Land und Region spielt hier bewusst keine Rolle (pausiert heißt nicht versteckt)."""
    return [o for o in orte if not ist_geloescht(o)]


def startzustand_pausiert(land_pausiert: bool = False, region_pausiert: bool = False) -> bool:
    """Ein neuer Ort startet pausiert, wenn sein Land ODER seine Region aus ist (AK-40, AK-44)."""
    return bool(land_pausiert) or bool(region_pausiert)


def land_zustand(land: str, regionen: Iterable[str], zustaende: Optional[dict] = None) -> str:
    """Sammelschalter (Frage 25): „an“, „aus“ oder „teilweise“ für ein Land.

    Ist das Land ausdrücklich aus, ist es „aus“ (auch wenn Regionen einzeln an gespeichert wären).
    Hat das Land Regionen, entscheidet deren Mischung; hat es keine (z. B. „Sonstige“), gilt sein
    eigener Zustand (fehlend = an)."""
    zustaende = zustaende or {}
    if not _ist_an((zustaende.get("laender") or {}).get(land)):
        return ZUSTAND_AUS
    regionen = list(regionen)
    if not regionen:
        return ZUSTAND_AN
    gespeichert = zustaende.get("regionen") or {}
    an = [_ist_an(gespeichert.get((land, r))) for r in regionen]
    if all(an):
        return ZUSTAND_AN
    if not any(an):
        return ZUSTAND_AUS
    return ZUSTAND_TEILWEISE
