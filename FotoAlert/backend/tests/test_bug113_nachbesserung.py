"""BUG-113 Nachbesserung (gate-auditor 2026-09-19, Punkte 2, 3 und 5).

Ergänzt `test_bug113.py` (Analyse, test-first, unverändert) und
`test_bug113_kalender_austausch.py` (unverändert) um die dort fehlenden Nachweise:

- AK3 stark: Der bisherige AK3-Test in `test_bug113.py` lief ohne Übergabedatei —
  der Austausch fand dort gar nicht statt, grün hieß nur "nichts getan". Hier
  existiert eine Übergabedatei in realistischer Größe (echte Datei 2026-09-19:
  ~4,4 MB, ~1 750 Termine à ~2,5 KB) und ein Kalender im Arbeitsspeicher in
  realistischer Größe (~1,1 GB calendar.json / ~2,5 KB je Termin ≈ 475 000
  Termine). Geprüft wird beides: der Austausch passiert inhaltlich korrekt UND
  der Server steht währenddessen nicht länger als 0,5 s am Stück.
- AK4: Die Nacharbeit nach dem Speichern stößt Feed-Neuladen und den
  Kalender-Austausch an (nicht mehr das Vollneuladen).
- AK5: 5 Standorte hintereinander, jeweils mit angestoßener Nacharbeit + Scout
  im Hintergrund — kein Anstieg (Näherung, Netz/Subprozesse gemockt).
- AK6: Fehler in einer Scout-Pipeline im Worker-Thread — die andere Pipeline
  läuft weiter, die Sperre bleibt nicht hängen, ein nächster Lauf ist möglich.
- gate-auditor Punkt 2: Leerer Kalender im Arbeitsspeicher darf nach dem
  Austausch nicht nur die Termine des einen Standorts enthalten.

Alle Tests laufen offline: kein Netz, kein echter Subprozess, kein precompute.py.
Python-3.9-kompatibel; asyncio-Objekte werden nur innerhalb laufender Loops erzeugt.
"""
import asyncio
import json
import threading
import time

import pytest

import main

pytestmark = [pytest.mark.offline, pytest.mark.regression]

MAX_STILLSTAND_S = 0.5
# Dateiname bewusst als Literal (nicht main._CAL_SINGLE_DELTA_NAME): so scheitert
# der Test gegen einen Stand ohne Austausch an der eigentlichen Anforderung
# (Stillstand/Inhalt), nicht bloß an einem fehlenden Namen.
POSTFACH = "calendar_single_last.json"
ZIEL = "custom_bug113_ziel"


async def _messe_stillstand(arbeit) -> float:
    """Wie in test_bug113.py: Ticker alle 20 ms, Rückgabe = längster Stillstand."""
    tick = 0.02
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
    await asyncio.sleep(0.1)
    try:
        await arbeit()
    finally:
        stop.set()
        await t
    return max(luecken) if luecken else 0.0


def _key(e):
    return (e.get("shoot_time", ""), -float(e.get("overall_score") or 0.0))


def _zeit(i: int, stunde: int = 5) -> str:
    return "2026-%02d-%02dT%02d:%02d:%02d+00:00" % (
        1 + (i // 40000) % 12, 1 + (i // 1500) % 28, (stunde + i // 60) % 24, (i // 7) % 60, i % 60)


def _bestand(n: int, ziel_alt: int, notiz: int = 0) -> list:
    """Kalender im Arbeitsspeicher: n Termine fremder Standorte + ziel_alt alte
    Termine von ZIEL, sortiert wie calendar.json. `notiz` = Länge eines
    Füllfelds je Termin, damit die zugehörige calendar.json auf der Platte eine
    Größe erreicht, deren Komplett-Einlesen spürbar blockiert."""
    fuell = "x" * notiz
    cal = [{"location_id": "loc_%d" % (i % 300), "event_type": "GOLDEN_HOUR",
            "shoot_time": _zeit(i), "overall_score": (i * 0.6180339887) % 1.0,
            "notiz": "Notiz %d %s" % (i, fuell)}
           for i in range(n)]
    cal += [{"location_id": ZIEL, "event_type": "MOONRISE", "shoot_time": _zeit(i * 97, 3),
             "overall_score": 0.11, "alt": True} for i in range(ziel_alt)]
    cal.sort(key=_key)
    return cal


def _voller_termin(i: int) -> dict:
    """Termin in der Form der echten calendar_single_last.json (45 Felder, ~2,5 KB)."""
    x = (i * 0.6180339887) % 1.0
    return {
        "id": "%s_%d" % (ZIEL, i), "location_id": ZIEL, "location_name": "Testmotiv BUG-113",
        "event_type": "GOLDEN_HOUR", "title": "🌅 Goldene Stunde am Testmotiv %d" % i,
        "shoot_time": _zeit(i * 13, 4), "shoot_window_start": _zeit(i * 13, 4),
        "shoot_window_end": _zeit(i * 13, 5), "overall_score": round(x, 4),
        "astronomy_score": round(x * 0.9, 4), "weather_score": None, "location_score": 0.7,
        "alert_priority": "normal", "celestial_azimuth": 360 * x, "celestial_altitude": 90 * x,
        "subject_azimuth": 120.5, "sightline_angle_deg": 1.2, "sightline_status": "frei",
        "elevation_difference_m": 12.0, "observer_lat": 52.5163, "observer_lon": 13.3777,
        "subject_lat": 52.5186, "subject_lon": 13.4010, "moon_illumination_pct": 55.0,
        "moon_phase": "Zunehmender Mond", "moonrise_azimuth": 80.1, "moonrise_utc": _zeit(i, 18),
        "moonset_azimuth": 280.2, "moonset_utc": _zeit(i, 6), "sunrise_azimuth": 70.3,
        "sunrise_utc": _zeit(i, 5), "sunset_azimuth": 290.4, "sunset_utc": _zeit(i, 17),
        "golden_hour_morning_start": _zeit(i, 5), "golden_hour_morning_end": _zeit(i, 6),
        "golden_hour_evening_start": _zeit(i, 16), "golden_hour_evening_end": _zeit(i, 17),
        "blue_hour_morning_start": _zeit(i, 4), "blue_hour_morning_end": _zeit(i, 5),
        "blue_hour_evening_start": _zeit(i, 17), "blue_hour_evening_end": _zeit(i, 18),
        "weather_description": "", "camera_hints": ["Stativ", "ND-Filter", "ISO 100"] * 6,
        "description": ("Sonne steht knapp über dem Motiv, weiches Seitenlicht. %d " % i) * 14,
        "composition_analysis": {"text": "Motiv zentral, Himmelskörper links oberhalb. " * 12,
                                 "ratio": x},
    }


def _schreibe_postfach(pfad, events: list, loc_id: str = ZIEL) -> None:
    pfad.write_text(json.dumps({"location_id": loc_id, "computed_at": "2026-09-27T00:00:00+00:00",
                                "events": events}, ensure_ascii=False), encoding="utf-8")


def _gemeinsame_mocks(monkeypatch, tmp_path, neue_events, aufrufe):
    """Subprozess (precompute.py) + Wetter gemockt. Der --calendar-only-Schritt
    schreibt wie der echte precompute.py die Übergabedatei (nach Laufbeginn)."""
    opp = tmp_path / "opportunities.json"
    opp.write_text(json.dumps({"computed_at": "2026-09-27T00:00:00+00:00", "opportunities": []}),
                   encoding="utf-8")

    async def subprozess(loc_id, flag, tag):
        aufrufe.append(flag)
        if flag == "--feed-only":
            opp.write_text(json.dumps({"computed_at": "2026-09-27T00:00:00+00:00", "opportunities": [
                {"location_id": loc_id, "shoot_time": _zeit(1), "event_type": "GOLDEN_HOUR",
                 "lat": 52.5, "lon": 13.4}]}), encoding="utf-8")
        elif flag == "--calendar-only":
            # Der echte Kalenderlauf dauert Sekunden bis Minuten. Ohne kurze Pause
            # läge die Änderungszeit der Datei (grober Kernel-Takt) u. U. VOR dem
            # time.time()-Laufbeginn und würde als "veraltet" verworfen.
            await asyncio.sleep(0.05)
            _schreibe_postfach(tmp_path / POSTFACH,
                               [dict(e, location_id=loc_id) for e in neue_events], loc_id)
        return 0

    async def wetter_ok(loc_id):
        return True

    monkeypatch.setattr(main, "_OPP_CACHE", opp)
    monkeypatch.setattr(main, "_ELEV_CACHE", tmp_path / "gibt_es_nicht.json")
    monkeypatch.setattr(main, "_run_precompute_single_subproc", subprozess)
    monkeypatch.setattr(main, "_weather_overlay_single", wetter_ok)
    monkeypatch.setattr(main, "_feed_cache", [])


# ---------------------------------------------------------------------------
# AK3 stark (gate-auditor Punkt 3)
# ---------------------------------------------------------------------------

def test_ak3_austausch_realistische_groesse_korrekt_und_ohne_stillstand(monkeypatch, tmp_path):
    """BUG-113 AK3: Übergabedatei ~4 MB + Kalender ~475 000 Termine im Arbeitsspeicher.
    Nach der Einzelberechnung sind die alten Termine des Standorts ersetzt, fremde
    unverändert, keine Dubletten, Sortierung erhalten — und der Server stand nie
    länger als 0,5 s am Stück. Auf der Platte liegt eine zum Endstand passende
    calendar.json (~370 MB; echte Datei ~1,1 GB): ein Weg, der sie komplett neu
    einliest — auch "nur" in einem Worker-Thread —, fällt am Stillstand durch."""
    bestand = _bestand(475_000, ziel_alt=1_500, notiz=600)
    fremd_vorher = [e for e in bestand if e["location_id"] != ZIEL]
    neue = [_voller_termin(i) for i in range(1_750)]
    endstand = sorted(fremd_vorher + neue, key=_key)

    kal = tmp_path / "calendar.json"
    with open(kal, "w", encoding="utf-8") as f:
        json.dump({"algorithm_version": "1.5", "computed_locations": {}, "events": endstand}, f,
                  ensure_ascii=False)
    del endstand

    aufrufe = []
    _gemeinsame_mocks(monkeypatch, tmp_path, neue, aufrufe)
    monkeypatch.setattr(main, "_CAL_CACHE", kal)
    monkeypatch.setattr(main, "_calendar_cache", bestand)

    stillstand = asyncio.run(_messe_stillstand(lambda: main._recompute_one(ZIEL)))

    postfach_mb = (tmp_path / POSTFACH).stat().st_size / 1e6
    assert postfach_mb >= 3.0, f"Übergabedatei unrealistisch klein ({postfach_mb:.1f} MB)"
    assert aufrufe == ["--feed-only", "--calendar-only"]

    cal = main._calendar_cache
    ziel = [e for e in cal if e["location_id"] == ZIEL]
    assert not any(e.get("alt") for e in ziel), "alte Termine des Standorts nicht ersetzt"
    assert len(ziel) == len(neue), f"{len(ziel)} statt {len(neue)} Termine des Standorts"
    assert len({e["id"] for e in ziel}) == len(neue), "Dubletten beim Standort"
    assert [e for e in cal if e["location_id"] != ZIEL] == fremd_vorher, \
        "fremde Standorte verändert/verloren"
    schluessel = [_key(e) for e in cal]
    assert schluessel == sorted(schluessel), "Sortierung (shoot_time, -score) verletzt"

    assert stillstand <= MAX_STILLSTAND_S, (
        f"Kalender-Austausch hielt den Server {stillstand:.2f} s am Stück an "
        f"(erlaubt: {MAX_STILLSTAND_S} s) — BUG-113 AK3 nicht erfüllt."
    )


# ---------------------------------------------------------------------------
# AK4 — Aufrufstelle im Nachrechnen
# ---------------------------------------------------------------------------

def test_ak4_nachrechnen_stoesst_feed_laden_und_kalender_austausch_an(monkeypatch, tmp_path):
    """BUG-113 AK4: Der Einstieg nach dem Speichern (_run_precompute_single) lädt nach
    dem Feed-Schritt den Feed neu (neuer Standort erscheint im Feed) und übergibt nach
    dem Kalender-Schritt an den Austausch — mit dem Laufbeginn als Frische-Grenze.
    Der Voll-Ladeweg (_load_caches) wird dabei nicht mehr benutzt."""
    aufrufe = []
    _gemeinsame_mocks(monkeypatch, tmp_path, [_voller_termin(1)], aufrufe)
    kal = tmp_path / "calendar.json"
    kal.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(main, "_CAL_CACHE", kal)
    monkeypatch.setattr(main, "_calendar_cache",
                        [{"location_id": "loc_a", "shoot_time": _zeit(1), "overall_score": 0.5}])
    monkeypatch.setattr(main, "_NO_BACKGROUND", False)
    monkeypatch.setattr(main, "_precompute_running", False)

    protokoll = []
    orig_feed = main._load_feed_cache
    orig_delta = main._apply_calendar_delta

    def feed_spion():
        protokoll.append(("feed", threading.get_ident()))
        return orig_feed()

    async def delta_spion(loc_id, min_mtime=0.0):
        protokoll.append(("delta", loc_id, min_mtime))
        return await orig_delta(loc_id, min_mtime=min_mtime)

    def voll_verboten():
        protokoll.append(("VOLL",))
        return True

    monkeypatch.setattr(main, "_load_feed_cache", feed_spion)
    monkeypatch.setattr(main, "_apply_calendar_delta", delta_spion)
    monkeypatch.setattr(main, "_load_caches", voll_verboten)
    pending_vorher = set(main._recompute_pending)
    # Nur ZIEL vormerken: Reste anderer Tests würden sonst vom Nachhol-Lauf
    # (_drain_recompute_pending) mitverarbeitet und die Aufrufzählung verfälschen.
    main._recompute_pending.clear()
    main._recompute_pending.add(ZIEL)
    t_start = time.time()
    try:
        asyncio.run(main._run_precompute_single(ZIEL))
        assert ("VOLL",) not in protokoll, "Voll-Ladeweg _load_caches() wurde benutzt"
        arten = [p[0] for p in protokoll]
        assert arten == ["feed", "delta"], f"Reihenfolge/Aufrufe: {arten}"
        assert protokoll[0][1] != threading.get_ident(), "Feed-Laden lief im Hauptstrang"
        assert protokoll[1][1] == ZIEL and protokoll[1][2] >= t_start - 1, \
            "Austausch ohne Frische-Grenze (min_mtime) aufgerufen"
        assert any(e["location_id"] == ZIEL for e in main._feed_cache), "Standort fehlt im Feed"
        assert any(e["location_id"] == ZIEL for e in main._calendar_cache), \
            "Standort fehlt im Kalender"
        assert any(e["location_id"] == "loc_a" for e in main._calendar_cache)
        assert main._precompute_running is False
        assert ZIEL not in main._recompute_pending, "Banner-Freigabe (US-106) fehlt"
    finally:
        main._recompute_pending.clear()
        main._recompute_pending.update(pending_vorher)


# ---------------------------------------------------------------------------
# gate-auditor Punkt 2 — leerer Kalender im Arbeitsspeicher
# ---------------------------------------------------------------------------

def test_punkt2_leerer_kalender_wird_voll_geladen_statt_nur_ein_standort(monkeypatch, tmp_path):
    """Ist der Kalender im Arbeitsspeicher leer (z. B. Einlesen beim Start gescheitert),
    darf er nach dem Austausch nicht nur die Termine des einen Standorts enthalten.
    Erwartet: calendar.json (von precompute.py im selben Lauf vollständig geschrieben)
    wird geladen — danach sind alle Standorte da."""
    voll = [
        {"location_id": "loc_a", "shoot_time": _zeit(1), "overall_score": 0.9},
        {"location_id": ZIEL, "shoot_time": _zeit(2), "overall_score": 0.8},
        {"location_id": "loc_b", "shoot_time": _zeit(3), "overall_score": 0.7},
    ]
    kal = tmp_path / "calendar.json"
    kal.write_text(json.dumps({"events": voll}), encoding="utf-8")
    _schreibe_postfach(tmp_path / POSTFACH, [voll[1]])
    monkeypatch.setattr(main, "_CAL_CACHE", kal)
    monkeypatch.setattr(main, "_calendar_cache", [])

    ok = asyncio.run(main._apply_calendar_delta(ZIEL))

    ids = sorted({e["location_id"] for e in main._calendar_cache})
    assert ids == sorted(["loc_a", "loc_b", ZIEL]), (
        f"Kalender nach Austausch in leeren Speicher enthält nur {ids} — "
        "übrige Standorte fehlen stillschweigend (gate-auditor Punkt 2)."
    )
    assert ok is True
    assert len(main._calendar_cache) == 3


def test_punkt2_leerer_kalender_und_unlesbare_datei_meldet_kein_ok(monkeypatch, tmp_path):
    """Scheitert auch das Vollneuladen (calendar.json kaputt), bleibt der Kalender
    unverändert leer und der Austausch meldet NICHT "ok" — statt eines Kalenders,
    der nur den einen Standort zeigt."""
    kal = tmp_path / "calendar.json"
    kal.write_text("{ kaputt", encoding="utf-8")
    _schreibe_postfach(tmp_path / POSTFACH,
                       [{"location_id": ZIEL, "shoot_time": _zeit(2), "overall_score": 0.8}])
    monkeypatch.setattr(main, "_CAL_CACHE", kal)
    monkeypatch.setattr(main, "_calendar_cache", [])

    ok = asyncio.run(main._apply_calendar_delta(ZIEL))

    assert ok is False
    assert main._calendar_cache == []


# ---------------------------------------------------------------------------
# AK6 — Fehlerpfad im Worker-Thread der Scout-Pipelines
# ---------------------------------------------------------------------------

def test_ak6_fehler_in_einer_scout_pipeline_im_worker_thread(monkeypatch, tmp_path, caplog):
    """BUG-113 AK6: Wirft die Mond-Pipeline in ihrem Worker-Thread, liefert die
    Sonnen-Pipeline trotzdem ihr Ergebnis; die Scout-Sperre bleibt nicht hängen und
    ein nächster Lauf startet normal."""
    from types import SimpleNamespace
    from discover import pipeline, moon_pipeline, sun_pipeline

    threads = {}
    haupt = threading.get_ident()

    async def mond_kaputt(days):
        threads["mond"] = threading.get_ident()
        raise RuntimeError("Mond kaputt (Test BUG-113 AK6)")

    async def sonne_ok(days):
        threads["sonne"] = threading.get_ident()
        return [SimpleNamespace(score=0.5, name="sonne")]

    monkeypatch.setattr(moon_pipeline, "run", mond_kaputt)
    monkeypatch.setattr(sun_pipeline, "run", sonne_ok)
    monkeypatch.setattr(pipeline, "filter_accessible_candidates", lambda c: c)

    ergebnis = asyncio.run(pipeline.run_pipeline(days=1))
    assert [o.name for o in ergebnis] == ["sonne"], "andere Pipeline lief nicht weiter"
    assert threads["mond"] != haupt and threads["sonne"] != haupt, \
        "Pipelines liefen nicht im Worker-Thread"
    assert "Pipeline fehlgeschlagen" in caplog.text

    # Über den Server-Einstieg: Sperre frei, zweiter Lauf läuft wieder an.
    async def sonne_leer(days):
        return []

    monkeypatch.setattr(sun_pipeline, "run", sonne_leer)
    monkeypatch.setattr(main, "_DISCOVER_CACHE", tmp_path / "discover.json")
    monkeypatch.setattr(main, "_discover_cache", main._discover_cache)
    monkeypatch.setattr(main, "_scout_running", False)
    monkeypatch.setattr(main, "_scout_dirty", False)
    for _ in range(2):
        asyncio.run(main._refresh_discover())
        assert main._scout_running is False, "Scout-Sperre blieb hängen"
    assert (tmp_path / "discover.json").exists(), "Scout-Lauf nach Pipeline-Fehler nicht fertig"


# ---------------------------------------------------------------------------
# AK5 — 5 Standorte hintereinander, kein Zähl-Effekt
# ---------------------------------------------------------------------------

def test_ak5_fuenf_standorte_hintereinander_ohne_anstieg(monkeypatch, tmp_path):
    """BUG-113 AK5 (Näherung, Netz + precompute.py gemockt): 5 Standorte werden
    hintereinander gespeichert; jedes Speichern stößt die echte Nacharbeit
    (_run_precompute_single → Feed-Neuladen, Kalender-Austausch bei ~200 000
    Terminen) und einen verkürzten echten Scout-Lauf an. Kein Speichern dauert
    länger als das erste + 1 s."""
    from discover import pipeline, moon_pipeline, sun_pipeline

    orig_run = pipeline.run_pipeline

    async def kurz(days=14):
        return await orig_run(days=2)

    async def kein_wetter(lat, lon):
        return None

    monkeypatch.setattr(pipeline, "run_pipeline", kurz)
    monkeypatch.setattr(moon_pipeline, "get_weather", kein_wetter)
    monkeypatch.setattr(sun_pipeline, "get_weather", kein_wetter)
    monkeypatch.setattr(pipeline, "filter_accessible_candidates", lambda c: c)
    monkeypatch.setattr(main, "_DISCOVER_CACHE", tmp_path / "discover.json")
    monkeypatch.setattr(main, "_discover_cache", main._discover_cache)
    monkeypatch.setattr(main, "_scout_running", False)
    monkeypatch.setattr(main, "_scout_dirty", False)

    aufrufe = []
    _gemeinsame_mocks(monkeypatch, tmp_path, [_voller_termin(i) for i in range(300)], aufrufe)
    kal = tmp_path / "calendar.json"
    kal.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(main, "_CAL_CACHE", kal)
    monkeypatch.setattr(main, "_calendar_cache", _bestand(200_000, ziel_alt=0))
    monkeypatch.setattr(main, "_NO_BACKGROUND", False)
    monkeypatch.setattr(main, "_precompute_running", False)

    async def hoehe_ok(*a, **k):
        return 0.0, False

    async def kein_ort(lat, lon):
        return "Testkiez"

    monkeypatch.setattr(main._elevation_provider, "elevation_difference", hoehe_ok)
    monkeypatch.setattr(main, "_reverse_geocode", kein_ort)
    monkeypatch.setattr(main, "_save_custom_location", lambda loc: None)
    monkeypatch.setattr(main.backup, "backup_after_edit", lambda loc_id: None)

    def scout_anstossen():
        asyncio.get_running_loop().create_task(main._refresh_discover())

    monkeypatch.setattr(main, "_trigger_discover_debounced", scout_anstossen)
    locs_vorher = list(main.LOCATIONS)
    pending_vorher = set(main._recompute_pending)
    main._recompute_pending.clear()  # Reste anderer Tests nicht mit nachrechnen

    async def szenario():
        dauern = []
        for i in range(5):
            req = main.PreviewAlignmentRequest(
                observer_lat=52.5163 + i * 0.001, observer_lon=13.3777,
                subject_lat=52.5186 + i * 0.001, subject_lon=13.4010,
                subject_name="Testmotiv BUG-113 AK5 Nr. %d" % (i + 1),
                subject_height_m=50, subject_width_m=20, save=True, days=14,
            )
            # Kurze Pause vor jedem weiteren Standort: Nacharbeit + Scout des
            # vorigen laufen im Hintergrund. Gemessen wird ab Pausenbeginn (minus
            # Pause) — hält die Nacharbeit den Server an, verlängert das die
            # Wartezeit des nächsten Standorts und fällt hier auf.
            pause = 0.3 if i else 0.0
            t0 = time.perf_counter()
            await asyncio.sleep(pause)
            await main.preview_alignment(req, None, "host")
            dauern.append(time.perf_counter() - t0 - pause)
        rest = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
        await asyncio.gather(*rest, return_exceptions=True)
        return dauern

    try:
        try:
            dauern = asyncio.run(szenario())
        except OSError as exc:  # nur fehlende Ephemeriden-Datei/kein Netz in Teil-Checkouts
            # Alle anderen Fehler (z. B. Speichern schlägt fehl) machen den Test rot,
            # statt ihn still zu überspringen (gate-auditor 2026-09-27, Punkt 2).
            pytest.skip(f"Alignment-Berechnung nicht ausführbar in dieser Umgebung: {exc!r}")
        neue_ids = [l.id for l in main.LOCATIONS if l not in locs_vorher]
    finally:
        main.LOCATIONS[:] = locs_vorher
        main._recompute_pending.clear()
        main._recompute_pending.update(pending_vorher)

    assert len(neue_ids) == 5
    assert aufrufe.count("--calendar-only") >= 1, "Nacharbeit wurde nicht angestoßen"
    ids_im_kalender = {e["location_id"] for e in main._calendar_cache}
    assert ids_im_kalender & set(neue_ids), "kein neuer Standort im Kalender angekommen"
    grenze = dauern[0] + 1.0
    assert max(dauern[1:]) <= grenze, (
        "Speicherdauern " + ", ".join("%.2f s" % d for d in dauern)
        + f" — ein späterer Standort lag über erster + 1 s ({grenze:.2f} s), BUG-113 AK5."
    )
