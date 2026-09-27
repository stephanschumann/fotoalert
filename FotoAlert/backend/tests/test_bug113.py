"""BUG-113 — Neuen Standort anlegen: Alignment-Berechnung und Speichern dauern beim
zweiten und jedem weiteren Standort deutlich länger als beim ersten.

Diese Tests entstanden in der Analyse-Phase (test-first) und beschreiben die
ANFORDERUNG, nicht eine bestimmte Umsetzung: Nach dem Anlegen eines Standorts darf
die Nacharbeit im Hintergrund (Scout-Auswertung "Entdecken", Neuladen der
Vorberechnungs-Ergebnisse) den Server nicht für den nächsten Standort einfrieren.

Messgrundlage (Analyse 2026-09-19, Linux-VM auf Stephans Mac, echter Code, Netz gemockt):
  - ohne Hintergrundarbeit: Alignments berechnen ~0,3-0,5 s, Speichern ~0,3 s (6 Standorte
    hintereinander, keine Zunahme)
  - Scout-Lauf 90 s nach dem letzten Speichern: Server 17,5 s eingefroren, zweiter Standort
    brauchte 17,8 s (Berechnen) bzw. 11,8 s (Speichern)
  - Neuladen der Ergebnisse nach der Einzelberechnung: ~1,3-1,5 s Stillstand bei 150 MB
    Kalenderdatei (echte Datei 1,1 GB -> hochgerechnet ~8-11 s, Näherung)

Alle Tests laufen offline (kein Netz, kein Subprozess, kein precompute.py). Schwellwert
für "Server steht": 0,5 s (Basiswert ohne Hintergrundarbeit: <= 0,05 s).
"""
import asyncio
import json
import time

import pytest

import main

pytestmark = [pytest.mark.offline, pytest.mark.regression]

# Schwellwert: so lange darf der Server-Hauptstrang am Stück nicht stehen.
MAX_STILLSTAND_S = 0.5


async def _messe_stillstand(arbeit) -> float:
    """Führt `arbeit()` (Coroutine-Fabrik) aus, während ein Ticker alle 20 ms tickt.
    Rückgabe: größte zusätzliche Verzögerung des Tickers = längster Stillstand des
    Event-Loops in Sekunden."""
    tick = 0.02
    luecken: list = []
    stop = asyncio.Event()

    async def ticker():
        last = time.perf_counter()
        while not stop.is_set():
            await asyncio.sleep(tick)
            now = time.perf_counter()
            luecken.append(now - last - tick)
            last = now

    t = asyncio.create_task(ticker())
    await asyncio.sleep(0.1)  # Ticker einschwingen lassen
    try:
        await arbeit()
    finally:
        stop.set()
        await t
    return max(luecken) if luecken else 0.0


def _scout_offline_verkuerzt(monkeypatch, tmp_path):
    """Scout-Lauf ohne Netz und mit kurzem Zeitraum (2 statt 14 Tage), sonst echter Code."""
    from discover import pipeline, moon_pipeline, sun_pipeline

    orig = pipeline.run_pipeline

    async def kurz(days: int = 14):
        return await orig(days=2)

    async def kein_wetter(lat, lon):
        return None

    monkeypatch.setattr(pipeline, "run_pipeline", kurz)
    monkeypatch.setattr(moon_pipeline, "get_weather", kein_wetter)
    monkeypatch.setattr(sun_pipeline, "get_weather", kein_wetter)
    monkeypatch.setattr(pipeline, "filter_accessible_candidates", lambda cands: cands)
    monkeypatch.setattr(main, "_DISCOVER_CACHE", tmp_path / "discover.json")
    monkeypatch.setattr(main, "_discover_cache", main._discover_cache)  # nach dem Test zurücksetzen
    monkeypatch.setattr(main, "_scout_running", False)
    monkeypatch.setattr(main, "_scout_dirty", False)


# ---------------------------------------------------------------------------
# AK2 — Die "Entdecken"-Auswertung (Scout) friert die App nicht mehr ein
# ---------------------------------------------------------------------------

def test_scout_lauf_haelt_server_nicht_an(monkeypatch, tmp_path):
    """BUG-113 AK2: Während der Scout-Volllauf rechnet, antwortet der Server weiter
    (längster Stillstand <= 0,5 s). Vorher: mehrere Sekunden bis 17 s Stillstand."""
    _scout_offline_verkuerzt(monkeypatch, tmp_path)
    stillstand = asyncio.run(_messe_stillstand(main._refresh_discover))
    assert stillstand <= MAX_STILLSTAND_S, (
        f"Scout-Lauf hielt den Server {stillstand:.2f} s am Stück an "
        f"(erlaubt: {MAX_STILLSTAND_S} s) — BUG-113 AK2 nicht erfüllt."
    )


# ---------------------------------------------------------------------------
# AK3 — Neuladen der Ergebnisse nach dem Speichern friert die App nicht mehr ein
# ---------------------------------------------------------------------------

def _schreibe_kalenderdatei(pfad, ziel_mb: int) -> None:
    """Synthetische Kalenderdatei mit realistischer Ereignisform: viele verschiedene
    Zahlenwerte und Emoji-Texte (wie in der echten calendar.json), damit die Einlesezeit
    der echten Datei pro Megabyte nahekommt (kein künstlich schnell lesbarer Wiederholtext)."""
    vorlage = (
        '{"location_id": "custom_%d", "location_name": "Testmotiv", "event_type": "GOLDEN_HOUR", '
        '"shoot_time": "2026-10-01T05:%02d:00+00:00", "astronomy_score": %.4f, "overall_score": %.4f, '
        '"celestial_azimuth": %.3f, "celestial_altitude": %.3f, "azimuth_delta_deg": %.2f, '
        '"altitude_delta_deg": %.2f, "vertical_offset_m": %.1f, "lateral_offset_m": %.1f, '
        '"body_apparent_diameter_m": %.1f, "moon_earth_distance_km": %d, "size_ratio": %.2f, '
        '"altitude_label": "⬇️ Noch unterhalb der Motivspitze", "azimuth_label": "Zentral ausgerichtet", '
        '"ratio_label": "Himmelskörper sehr klein relativ zum Motiv", "body_name": "Mond", '
        '"notiz": "%s"}'
    )
    def ereignis(i: int) -> str:
        x = (i * 0.6180339887) % 1.0
        return vorlage % (
            i, i % 60, x, x * 0.9, 360 * x, 90 * x, x * 4, x * 3, x * 10, x * 5, x * 2,
            380000 + i % 30000, x * 0.5, "Notiz %d " % i + "x" * 180,
        )

    n = max(1, (ziel_mb * 1024 * 1024) // (len(ereignis(1)) + 2))
    with open(pfad, "w", encoding="utf-8") as f:
        f.write('{"algorithm_version": "1.5", "computed_locations": {}, "events": [')
        for i in range(n):
            f.write(("" if i == 0 else ", ") + ereignis(i))
        f.write("]}")


def test_neuladen_nach_einzelberechnung_haelt_server_nicht_an(monkeypatch, tmp_path):
    """BUG-113 AK3: Der Nachlauf nach dem Speichern (Einzel-Neuberechnung: Feed, Wetter,
    Kalender, jeweils Ergebnisse neu laden) lässt den Server nicht länger als 0,5 s am
    Stück stehen — auch nicht bei einer großen Kalenderdatei (Testgröße 200 MB; echte
    Datei aktuell ~1,1 GB). Ein reines Auslagern in einen Thread reicht dafür NICHT
    (das Einlesen hält den Python-Sperrmechanismus die ganze Zeit) — der Test trennt
    bewusst 'nur verschoben' von 'wirklich nicht mehr blockierend'."""
    kal = tmp_path / "calendar.json"
    _schreibe_kalenderdatei(kal, 200)
    opp = tmp_path / "opportunities.json"
    opp.write_text(json.dumps({"computed_at": "2026-09-19T00:00:00+00:00", "opportunities": []}),
                   encoding="utf-8")

    monkeypatch.setattr(main, "_CAL_CACHE", kal)
    monkeypatch.setattr(main, "_OPP_CACHE", opp)
    monkeypatch.setattr(main, "_ELEV_CACHE", tmp_path / "gibt_es_nicht.json")
    monkeypatch.setattr(main, "_feed_cache", [])
    monkeypatch.setattr(main, "_calendar_cache", [])

    async def subprozess_ok(loc_id, flag, tag):
        return 0

    async def wetter_ok(loc_id):
        return True

    monkeypatch.setattr(main, "_run_precompute_single_subproc", subprozess_ok)
    monkeypatch.setattr(main, "_weather_overlay_single", wetter_ok)

    stillstand = asyncio.run(_messe_stillstand(lambda: main._recompute_one("custom_test")))
    assert stillstand <= MAX_STILLSTAND_S, (
        f"Ergebnis-Neuladen nach der Einzelberechnung hielt den Server {stillstand:.2f} s am "
        f"Stück an (erlaubt: {MAX_STILLSTAND_S} s) — BUG-113 AK3 nicht erfüllt."
    )


# ---------------------------------------------------------------------------
# AK1 — Zweiter Standort ist genauso schnell wie der erste (Berechnen UND Speichern)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("speichern", [False, True], ids=["alignments_berechnen", "speichern"])
def test_zweiter_standort_waehrend_scout_lauf_nicht_langsamer(monkeypatch, tmp_path, speichern):
    """BUG-113 AK1: Läuft im Hintergrund gerade der Scout-Lauf (Auslöser: Speichern des
    ersten Standorts), dauern 'Alignments berechnen' bzw. 'Speichern' des nächsten
    Standorts trotzdem höchstens 1 s (Basiswert ohne Hintergrundarbeit: ~0,3-0,5 s bei
    gemocktem Netz). Vorher: 17,8 s bzw. 11,8 s."""
    _scout_offline_verkuerzt(monkeypatch, tmp_path)

    async def hoehe_ok(*a, **k):
        return 0.0, False

    async def kein_ort(lat, lon):
        return "Testkiez"

    monkeypatch.setattr(main._elevation_provider, "elevation_difference", hoehe_ok)
    monkeypatch.setattr(main, "_reverse_geocode", kein_ort)
    monkeypatch.setattr(main, "_save_custom_location", lambda loc: None)
    monkeypatch.setattr(main.backup, "backup_after_edit", lambda loc_id: None)
    monkeypatch.setattr(main, "_trigger_discover_debounced", lambda: None)
    locs_vorher = list(main.LOCATIONS)
    pending_vorher = set(main._recompute_pending)

    req = main.PreviewAlignmentRequest(
        observer_lat=52.5163, observer_lon=13.3777, subject_lat=52.5186, subject_lon=13.4010,
        subject_name="Testmotiv BUG-113", subject_height_m=50, subject_width_m=20,
        save=speichern, days=14,
    )

    async def szenario() -> float:
        t0 = time.perf_counter()
        scout = asyncio.create_task(main._refresh_discover())
        fertig_um: list = []

        async def anfrage():
            await main.preview_alignment(req, None, "host")
            fertig_um.append(time.perf_counter())

        await asyncio.gather(scout, anfrage())
        return fertig_um[0] - t0

    try:
        dauer = asyncio.run(szenario())
    except Exception as exc:  # z. B. Ephemeriden-Datei (de421.bsp) fehlt in Teil-Checkouts
        pytest.skip(f"Alignment-Berechnung nicht ausführbar in dieser Umgebung: {exc!r}")
    finally:
        main.LOCATIONS[:] = locs_vorher
        main._recompute_pending.clear()
        main._recompute_pending.update(pending_vorher)

    assert dauer <= 1.0, (
        f"{'Speichern' if speichern else 'Alignments berechnen'} dauerte {dauer:.2f} s, "
        "während im Hintergrund der Scout-Lauf rechnete (erlaubt: 1,0 s) — BUG-113 AK1 nicht erfüllt."
    )


# ---------------------------------------------------------------------------
# Regression (heute grün, muss nach dem Fix grün bleiben)
# ---------------------------------------------------------------------------

def test_scout_fehler_bleibt_folgenlos(monkeypatch, tmp_path):
    """BUG-113 AK6 (Fehlerfall): Schlägt der Scout-Lauf fehl, bleibt die Sperre nicht
    hängen und der Fehler wird nicht nach außen geworfen (bestehendes Verhalten)."""
    from discover import pipeline

    async def kaputt(cache_path):
        raise RuntimeError("Scout kaputt (Test)")

    monkeypatch.setattr(pipeline, "refresh_discover_cache", kaputt)
    monkeypatch.setattr(main, "_DISCOVER_CACHE", tmp_path / "discover.json")
    monkeypatch.setattr(main, "_scout_running", False)
    monkeypatch.setattr(main, "_scout_dirty", False)

    asyncio.run(main._refresh_discover())  # darf nicht werfen
    assert main._scout_running is False


def test_speichern_stoesst_weiterhin_nachberechnung_und_scout_an(monkeypatch):
    """BUG-113 AK4 (Regression, US-106): Ein gespeicherter Standort wird weiterhin für die
    Neuberechnung vorgemerkt (Banner 'wird aktualisiert') und der Scout wird weiterhin
    angestoßen — der Fix darf diese Zusagen nicht stillschweigend streichen."""
    ausgeloest: list = []

    async def kein_ort(lat, lon):
        return ""

    monkeypatch.setattr(main, "_reverse_geocode", kein_ort)
    monkeypatch.setattr(main, "_save_custom_location", lambda loc: None)
    monkeypatch.setattr(main.backup, "backup_after_edit", lambda loc_id: None)
    monkeypatch.setattr(main, "_trigger_discover_debounced", lambda: ausgeloest.append("scout"))
    locs_vorher = list(main.LOCATIONS)
    pending_vorher = set(main._recompute_pending)

    req = main.PreviewAlignmentRequest(
        observer_lat=52.5163, observer_lon=13.3777, subject_lat=52.5186, subject_lon=13.4010,
        subject_name="Testmotiv BUG-113 Regression", subject_height_m=50, subject_width_m=20, save=True,
    )
    profile = main.calculate_subject_angular_profile(
        observer_lat=req.observer_lat, observer_lon=req.observer_lon,
        subject_lat=req.subject_lat, subject_lon=req.subject_lon,
        subject_height_m=req.subject_height_m, subject_width_m=req.subject_width_m,
        elevation_difference_m=0.0,
    )

    async def lauf():
        loc_id = await main._save_alignment_as_location(req, profile, 135)
        await asyncio.sleep(0)  # angestoßene Hintergrundaufgaben kurz laufen lassen
        return loc_id

    try:
        loc_id = asyncio.run(lauf())
        assert loc_id and loc_id.startswith("custom_")
        assert loc_id in main._recompute_pending, "Standort nicht für die Neuberechnung vorgemerkt"
        assert ausgeloest == ["scout"], "Scout-Auffrischung wurde nicht angestoßen"
    finally:
        main.LOCATIONS[:] = locs_vorher
        main._recompute_pending.clear()
        main._recompute_pending.update(pending_vorher)
