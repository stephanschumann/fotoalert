"""US-141, Baustein 1: Startzustand und einmalige Übernahme der Gebiets-Schalter (Migration).

Hier steht, WAS beim ersten Mal in die Tabelle `area_states` geschrieben wird (Entscheidung Frage 12):
  - Gebiete (Region bzw. Land ohne Regionen), in denen heute mindestens ein nicht gelöschter Ort
    liegt, sind AN — damit ändert sich für Stephan nichts Sichtbares.
  - Alle anderen Gebiete sind AUS (leere Länder/Regionen ruhen, bis dort ein Ort angelegt wird).

Die Übernahme ist beliebig oft wiederholbar: sie legt nur fehlende Zeilen an und überschreibt nie
einen Zustand, den jemand schon geschaltet hat. Vor dem ersten Schreiben wird die Datenbank
gesichert (nur wenn wirklich etwas zu schreiben ist).

Die Anbindung an den Serverstart und an die Schalter-Adressen gehört zu Baustein 2 und ist hier
absichtlich NICHT verdrahtet. Nur Standardbibliothek, Python 3.9-kompatibel.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Tuple

from data import regionen as _reg
from data.aktiv_regel import ist_geloescht

Eintrag = Tuple[str, str, bool]   # (Land, Region ("" = Land selbst), an?)


def _wert(ort: Any, name: str) -> Any:
    if isinstance(ort, dict):
        return ort.get(name)
    return getattr(ort, name, None)


def _gebiet_des_ortes(ort: Any) -> Tuple[str, str]:
    """Land und Region (Region "" bei Ländern ohne Regionen). Gespeicherte Angaben am Ort haben
    Vorrang; fehlen sie, wird sie aus den Koordinaten bestimmt."""
    land = _wert(ort, "land")
    region = _wert(ort, "region")
    if not land:
        z = _reg.schlage_region_vor(_wert(ort, "lat"), _wert(ort, "lon"), _wert(ort, "name"))
        land, region = z.land, z.region
    if not _reg.REGIONEN.get(land):
        return land, ""
    return land, region or _reg.OHNE_REGION


def standard_zustaende(orte: Iterable[Any]) -> List[Eintrag]:
    """Alle Gebiete der festen Liste mit ihrem Startzustand (siehe Kopf der Datei)."""
    belegt = set()
    for ort in orte or []:
        if ist_geloescht(ort):
            continue
        belegt.add(_gebiet_des_ortes(ort))
    ergebnis: List[Eintrag] = []
    for land, regionen in _reg.REGIONEN.items():
        if regionen:
            for r in regionen:
                ergebnis.append((land, r, (land, r) in belegt))
            if (land, _reg.OHNE_REGION) in belegt:
                ergebnis.append((land, _reg.OHNE_REGION, True))
        else:
            ergebnis.append((land, "", (land, "") in belegt))
    return ergebnis


def migriere_gebietszustand(store: Any, orte: Iterable[Any], sichern: bool = True) -> Dict[str, Any]:
    """Legt fehlende Gebiets-Zeilen an (idempotent) und sichert vorher die Datenbank.

    Rückgabe: {"neu": Anzahl neu angelegter Zeilen, "vorhanden": Zeilen vor dem Lauf,
               "sicherung": Pfad der Sicherung oder None}."""
    gewuenscht = standard_zustaende(orte)
    vorhanden = store.load_area_states()
    bekannt = set(vorhanden["laender"]) | set(vorhanden["regionen"])
    fehlend = [e for e in gewuenscht if ((e[0], e[1]) if e[1] else e[0]) not in bekannt]
    vorher = store.area_state_count()
    sicherung = None
    if fehlend and sichern:
        sicherung = store.sichere_datenbank()
    neu = store.seed_area_states(fehlend) if fehlend else 0
    return {"neu": neu, "vorhanden": vorher, "sicherung": str(sicherung) if sicherung else None}
