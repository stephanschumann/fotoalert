"""TASK-106 (Nachbesserung "Variante A") — die Gebäudeabfrage des Sichtachsen-Checks
darf den Server nicht anhalten.

Hintergrund: `compute_location_sightline()` rief `fetch_buildings_along_line()` bisher
direkt im Hauptstrang des Servers auf. Die Funktion sucht im lokalen Gebäude-Cache und
fragt bei einem Treffer-Fehlschlag blockierend im Netz nach (httpx.Client, time.sleep-
Drosselung). Das hielt den Server beim manuellen Sichtachsen-Check über Sekunden an
(gemessen auf dem Produktivserver: 14,6-17,7 s Antwortzeit von /health).

Abgedeckt:
- G1  Eine 1,5 s lang blockierende Gebäudeabfrage hält den Server nicht länger als 0,5 s
      am Stück an (Messung per mitlaufendem Ticker).
- G2  Das Ergebnis (Status) kommt unverändert korrekt zurück ("frei" bei leerer Liste).
- G3  Liefert die Abfrage None, bleibt das Ergebnis "nicht_geprueft".
- G4  Wirft die Abfrage eine Exception, bleibt das Ergebnis "nicht_geprueft" (kein Absturz).
- G5  Die Abfrage läuft tatsächlich in einem Nebenstrang (nicht im Hauptstrang).

Alle Tests laufen offline (Abfrage ersetzt, kein Netz). Python-3.9-kompatibel;
asyncio-Objekte werden nur innerhalb laufender Event-Loops erzeugt.
"""
from __future__ import annotations

import asyncio
import threading
import time
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from calculations import sightline as sl
from data.store import LocationStore

pytestmark = [pytest.mark.offline, pytest.mark.regression]

MAX_STILLSTAND_S = 0.5
BLOCK_DAUER_S = 1.5


class _Loc:
    id = "loc-task106-gebaeude"
    observer_lat = 52.50
    observer_lon = 13.40
    subject_lat = 52.51
    subject_lon = 13.41
    subject_height_m = 30.0
    observer_floor_height_m = 0.0
    distance_m = 1000.0


class _OkElevationProvider:
    """Flaches, vollständiges Höhenprofil (kein Hindernis); async ohne echte Wartezeit."""
    async def elevation_profile(self, *args, **kwargs):
        return [0.0, 0.0, 0.0, 0.0, 0.0], False


async def _messe_stillstand(arbeit):
    """Ticker alle 50 ms; Rückgabe = (Ergebnis der Arbeit, längster Stillstand in s)."""
    tick = 0.05
    luecken = []
    stop = asyncio.Event()

    async def ticker():
        last = time.perf_counter()
        while not stop.is_set():
            await asyncio.sleep(tick)
            now = time.perf_counter()
            luecken.append(now - last - tick)
            last = now

    t = asyncio.create_task(ticker())
    await asyncio.sleep(0.15)
    try:
        ergebnis = await arbeit()
    finally:
        stop.set()
        await t
    return ergebnis, (max(luecken) if luecken else 0.0)


def _blockierend(rueckgabe, dauer_s=BLOCK_DAUER_S, thread_ids=None):
    def _fake(*args, **kwargs):
        if thread_ids is not None:
            thread_ids.append(threading.get_ident())
        time.sleep(dauer_s)   # gibt den GIL frei, wie echtes Netz-Warten
        return rueckgabe
    return _fake


def test_g1_blockierende_gebaeudeabfrage_haelt_server_nicht_an(monkeypatch):
    monkeypatch.setattr("data.qa_azimuth.fetch_buildings_along_line", _blockierend([]))

    async def arbeit():
        return await sl.compute_location_sightline(_Loc(), _OkElevationProvider())

    _, stillstand = asyncio.run(_messe_stillstand(arbeit))
    assert stillstand <= MAX_STILLSTAND_S, (
        f"Gebäudeabfrage hielt den Server {stillstand:.2f} s am Stück an "
        f"(erlaubt: {MAX_STILLSTAND_S} s) — TASK-106 Variante A nicht erfüllt."
    )


def test_g2_ergebnis_bleibt_korrekt_frei_bei_leerer_gebaeudeliste(monkeypatch):
    monkeypatch.setattr("data.qa_azimuth.fetch_buildings_along_line", _blockierend([], 0.05))
    result = asyncio.run(sl.compute_location_sightline(_Loc(), _OkElevationProvider()))
    assert result["status"] == "frei"


def test_g3_none_von_der_abfrage_bleibt_nicht_geprueft(monkeypatch):
    monkeypatch.setattr("data.qa_azimuth.fetch_buildings_along_line", _blockierend(None, 0.05))
    result = asyncio.run(sl.compute_location_sightline(_Loc(), _OkElevationProvider()))
    assert result["status"] == "nicht_geprueft"


def test_g4_exception_der_abfrage_bleibt_nicht_geprueft(monkeypatch):
    def _kaputt(*args, **kwargs):
        raise RuntimeError("simulierter Fehler der Gebäudeabfrage")

    monkeypatch.setattr("data.qa_azimuth.fetch_buildings_along_line", _kaputt)
    result = asyncio.run(sl.compute_location_sightline(_Loc(), _OkElevationProvider()))
    assert result["status"] == "nicht_geprueft"


def test_g5_abfrage_laeuft_im_nebenstrang(monkeypatch):
    ids = []
    monkeypatch.setattr("data.qa_azimuth.fetch_buildings_along_line", _blockierend([], 0.05, ids))
    asyncio.run(sl.compute_location_sightline(_Loc(), _OkElevationProvider()))
    assert len(ids) == 1
    assert ids[0] != threading.get_ident()


def test_g6_update_speichert_ergebnis_trotz_nebenstrang(tmp_path, monkeypatch):
    monkeypatch.setattr("data.qa_azimuth.fetch_buildings_along_line", _blockierend([], 0.05))
    store = LocationStore(db_path=tmp_path / "t.db")
    result = asyncio.run(sl.update_location_sightline(store, _Loc(), _OkElevationProvider()))
    assert result["status"] == "frei"
    saved = store.get_qa_values(_Loc.id)
    assert saved is not None and saved["sightline_status"] == "frei"
