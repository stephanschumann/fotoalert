"""
BUG-63 — "Alignments berechnen" (`POST /preview-alignment`) aktiviert vor der
Berechnungsschleife eine `WindowEphemeris`-Fenster-Engine
(`calculations.astronomy.set_active_window()`, `backend/main.py` ~Zeile 2940-2946)
und muss sie per `try/finally` IMMER wieder zurücksetzen
(`calculations.astronomy.clear_active_window()`) — auch wenn während der
Berechnung eine Exception auftritt.

Spec-Bezug (BACKLOG.md, Ticket BUG-63, Abschnitt "Analyse & Spec", Testplan +
Pre-Mortem-Szenario 4):
  "Regressionstest 'Kalender-Request nach preview_alignment()-Aufruf liefert
  unveränderte Ergebnisse' (Szenario 4), Marker offline/regression."
  Pre-Mortem-Szenario 4 (BACKLOG.md): "Seiteneffekt auf bestehende
  Fenster-Engine-Nutzer (Kalender, On-Demand-Monatsübersicht), falls
  set_active_window/clear_active_window in preview_alignment() fehlerhaft
  verschachtelt wird (z. B. finally fehlt, Exception vor dem Clear)."

Referenz-Endpoint (verifiziert per Grep, nicht geraten): `GET /plan`
(`backend/main.py` Zeile 2335-2389, `get_plan()`) nutzt exakt denselben
Fenster-Mechanismus wie `preview_alignment()` — `_astro.set_active_window(
WindowEphemeris(...))` vor der Berechnung, `finally: _astro.clear_active_window()`
danach (Zeile 2381/2385). Es ist der einfachste (kein Location-Seed nötig,
`days` frei wählbar, `elevation_difference_m` als Parameter direkt überreichbar
-> kein Netzwerk-Mock nötig) von den beiden in BUG-63 genannten
Fenster-Engine-Konsumenten ("Kalender oder On-Demand-Monatsübersicht"); der
andere (`GET /calendar` mit `FOTOALERT_ONDEMAND=1`, `main._compute_location_month()`,
Zeile 2456-2473) nutzt strukturell denselben `set_active_window()`/
`clear_active_window()`-Mechanismus.

`elevation_difference()` wird für den `preview-alignment`-Aufruf per
`monkeypatch` gemockt (kein echter HTTP-Call gegen opentopodata.org); der
Referenz-Endpoint `/plan` bekommt `elevation_difference_m` direkt als
Query-Parameter mit, sodass er den Elevation-Provider gar nicht erst aufruft.

Python-3.9-kompatibel (kein `X | None`).
"""
from __future__ import annotations

import asyncio

import pytest

import calculations.astronomy as astro

pytestmark = [pytest.mark.offline, pytest.mark.regression]

# Babelsberg -> Belvedere (Pfingstberg), dasselbe Beispiel wie im Docstring von
# calculate_subject_angular_profile()/find_precise_alignment_times()
# (calculations/astronomy.py Zeile 652/746) und in test_bug66.py verwendet -
# bekannt dafür, plausible Sonnen-/Mond-Alignments zu liefern.
_OBSERVER_LAT, _OBSERVER_LON = 52.3975, 13.0976
_SUBJECT_LAT, _SUBJECT_LON = 52.4158, 13.0688
_ELEVATION_DIFF_M = 50.0


def _login_as_host(client):
    """TASK-83: /preview-alignment liest nur noch das Sitzungscookie (kein
    Authorization-Header-Fallback mehr) — ein direkt via auth.issue_token('host')
    gebauter Bearer-Header (der bisherige BUG-63-Testplan-Ansatz, kein /login-
    Roundtrip) authentifiziert seit dem Umbau nicht mehr. Ein echter /login-Aufruf
    setzt das Cookie auf dem geteilten `client` für alle Folge-Requests dieses Tests."""
    r = client.post("/login", json={"password": "test-host-pw"})
    assert r.status_code == 200, r.text


def _preview_payload(**overrides):
    payload = {
        "observer_lat": _OBSERVER_LAT,
        "observer_lon": _OBSERVER_LON,
        "subject_lat": _SUBJECT_LAT,
        "subject_lon": _SUBJECT_LON,
        "subject_name": "Unbenannt",  # save=False -> wird nie gespeichert
        "subject_height_m": 15.0,
        "subject_width_m": 10.0,
        "days": 3,
        "save": False,
    }
    payload.update(overrides)
    return payload


def _plan_params(**overrides):
    params = {
        "observer_lat": _OBSERVER_LAT,
        "observer_lon": _OBSERVER_LON,
        "subject_lat": _SUBJECT_LAT,
        "subject_lon": _SUBJECT_LON,
        "subject_name": "Referenz-Motiv",
        "subject_height_m": 15.0,
        "subject_width_m": 10.0,
        "elevation_difference_m": _ELEVATION_DIFF_M,  # explizit -> kein Elevation-Netzwerkcall
        "observer_floor_height_m": 0.0,
        "days": 3,
        "min_score": 0.0,
    }
    params.update(overrides)
    return params


@pytest.fixture(autouse=True)
def _mock_elevation(monkeypatch):
    """Kein echter Netzwerkaufruf gegen opentopodata.org: elevation_difference()
    (genutzt von preview_alignment(), Zeile 2889-2890) wird für die gesamte
    Testdatei deterministisch gemockt."""
    from data.elevation import provider

    async def _fake_elevation_difference(*args, **kwargs):
        return _ELEVATION_DIFF_M, False

    monkeypatch.setattr(provider, "elevation_difference", _fake_elevation_difference)


def _reference_plan_result(client, **overrides):
    r = client.get("/plan", params=_plan_params(**overrides))
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["status"] == "ok"
    return body


class TestReferenceEndpointUnaffectedByPreviewAlignmentWindowState:
    """Testplan BUG-63 / Pre-Mortem-Szenario 4: Ein Request an den geteilten
    Fenster-Engine-Konsumenten (`GET /plan`) liefert nach einem
    `preview_alignment()`-Aufruf exakt dasselbe Ergebnis wie vorher - kein
    "verschmutzter" `_active_window`-State."""

    def test_plan_result_identical_before_and_after_preview_alignment(self, client):
        assert astro._active_window.get() is None, (
            "Ausgangszustand vor dem Test: kein aktives Fenster erwartet."
        )

        before = _reference_plan_result(client)

        _login_as_host(client)
        payload = _preview_payload()
        r = client.post("/preview-alignment", json=payload)
        assert r.status_code == 200, r.text

        # Kernaussage BUG-63: clear_active_window() wurde im finally aufgerufen -
        # das globale Fenster ist NACH preview_alignment() wieder None.
        assert astro._active_window.get() is None, (
            "calculations.astronomy._active_window blieb nach preview_alignment() "
            "gesetzt - clear_active_window() wurde nicht (im finally) aufgerufen "
            "(BUG-63-Regression)."
        )

        after = _reference_plan_result(client)
        assert after == before, (
            "GET /plan liefert nach einem preview_alignment()-Aufruf ein anderes "
            "Ergebnis als vorher - Hinweis auf verschmutzten Fenster-State "
            "(BUG-63-Regression, Pre-Mortem-Szenario 4)."
        )

    def test_active_window_cleared_even_when_alignment_loop_raises(self, client, monkeypatch):
        """Pre-Mortem-Szenario 4 explizit: eine Exception WÄHREND der
        `await asyncio.to_thread(_compute_alignments)`-Berechnung darf
        `clear_active_window()` im `finally` nicht verhindern."""
        assert astro._active_window.get() is None

        async def _boom(*args, **kwargs):
            raise RuntimeError("BUG-63-Testinjektion: simulierte Exception in der Alignment-Schleife")

        monkeypatch.setattr(asyncio, "to_thread", _boom)

        _login_as_host(client)
        payload = _preview_payload()
        with pytest.raises(RuntimeError):
            client.post("/preview-alignment", json=payload)

        assert astro._active_window.get() is None, (
            "Nach einer Exception in der Alignment-Berechnung blieb "
            "calculations.astronomy._active_window gesetzt - das finally hat den "
            "State nicht zurückgesetzt (BUG-63-Regression, Pre-Mortem-Szenario 4)."
        )

        # Nachfolgender Referenz-Request funktioniert unverändert (kein Folgeschaden).
        after_crash = _reference_plan_result(client)
        baseline = _reference_plan_result(client)
        assert after_crash == baseline


class TestAlignmentsOnePerDayAndBodyPassage:
    """AK-5 (Option A, Weg-Gate-Entscheidung 2026-07-15): Nach Aktivierung der
    Fenster-Engine zeigt die Vorschau pro Tag/Himmelskörper-Passage genau einen
    Treffer am Qualitätsmaximum statt mehrerer eng beieinanderliegender
    Minuten-Treffer.

    Geometrie bewusst synthetisch konstruiert (Motiv ~100m südwestlich des
    Fotografen, Azimut ~213°, Höhenwinkel Spitze ~55°) statt der
    Babelsberg->Pfingstberg-Koordinaten aus test_bug66.py: diese Passage trifft
    für das reale Testdatum verlässlich sowohl Sonne (nahe Sonnenhöchststand)
    als auch Mond mit hoher Qualität (empirisch verifiziert, kein geratener
    Wert) - unabhängig vom Kalenderdatum, an dem dieser Test läuft, robust
    genug für mind. einen Treffer über 10 Tage."""

    def test_no_duplicate_day_body_pairs_in_alignments(self, client, monkeypatch):
        from data.elevation import provider

        async def _fake_elevation_difference(*args, **kwargs):
            return 100.0, False

        monkeypatch.setattr(provider, "elevation_difference", _fake_elevation_difference)

        _login_as_host(client)
        payload = _preview_payload(
            subject_lat=52.39674661285668, subject_lon=13.096798178332305,
            subject_height_m=44.0, subject_width_m=20.0,
            days=10,
        )
        r = client.post("/preview-alignment", json=payload)
        assert r.status_code == 200, r.text

        alignments = r.json()["alignments"]
        assert alignments, (
            "Erwartete mindestens einen Alignment-Treffer für die bekannte "
            "Babelsberg->Pfingstberg-Testlocation über 10 Tage - leere Liste "
            "deutet auf ein Problem in der Testaufsetzung hin."
        )

        seen = set()
        duplicates = []
        for a in alignments:
            key = (a["time"][:10], a["body"])
            if key in seen:
                duplicates.append(key)
            seen.add(key)

        assert not duplicates, (
            f"Doppelte (Tag, Himmelskörper)-Paare in den Alignments gefunden: {duplicates} - "
            "AK-5 verlangt genau einen Top-Treffer pro Tag/Himmelskörper-Passage "
            "statt mehrerer eng beieinanderliegender Minuten-Treffer."
        )


class TestActiveWindowConcurrencyIsolation:
    """BUG-63-Nachbesserung (Race-Fix, Stephan 2026-07-16): `_active_window` war
    ein einziger, prozessweiter Modul-Global (kein Lock, keine Anfrage-Trennung).
    Bei echter Nebenläufigkeit (zwei gleichzeitige Requests, unterschiedliche
    Standorte) konnte Request B das Fenster von Request A überschreiben, während
    A's Hintergrund-Berechnung (`await asyncio.to_thread(...)` in
    `preview_alignment()`) noch lief - Folge: A fiel für die Rest-Iterationen
    unbemerkt auf den langsamen Pfad zurück (kein Crash, keine Datenkorruption,
    aber die BUG-63-Performance-Zusage wurde unterlaufen).

    Fix: `_active_window` ist jetzt ein `contextvars.ContextVar` statt eines
    einfachen Globals. Jeder eingehende Request läuft in FastAPI/Starlette als
    eigener `asyncio.Task`, der beim Erzeugen eine KOPIE des aktuellen Kontexts
    erbt - `ContextVar.set()` innerhalb eines Tasks ist für andere gleichzeitig
    laufende Tasks unsichtbar. `asyncio.to_thread()` kopiert den Kontext explizit
    in den Thread (`contextvars.copy_context()` + `ctx.run()`, Python 3.9+
    dokumentiertes Verhalten) - die Isolation bleibt also auch über den
    `to_thread`-Aufruf hinweg erhalten.

    Beide Tests nutzen echte Nebenläufigkeit über `asyncio.gather()` - NICHT den
    sequenziellen Starlette-`TestClient` (der reiht Requests einfach hintereinander
    und würde die Race-Bedingung nie erzeugen)."""

    def test_context_isolation_under_real_task_overlap(self):
        """Mechanismus-Test (deterministisch, ohne Timing-Glück): zwei echte
        asyncio.Tasks (via gather) setzen je ein eigenes Fenster-Sentinel und
        werden per asyncio.Event so verzahnt, dass Task B sein Fenster GARANTIERT
        setzt, WÄHREND Task A noch "in Arbeit" ist (zwischen set_active_window()
        und dem Rücklesen) - exakt das Szenario aus der Bug-Beschreibung. Mit dem
        alten Modul-Global hätte Task A danach fälschlich Task B's Fenster
        gesehen; mit ContextVar sieht jeder Task ausschließlich sein eigenes."""
        import calculations.astronomy as astro

        assert astro._active_window.get() is None, "Ausgangszustand: kein aktives Fenster erwartet."

        window_a = object()  # Sentinel statt echter WindowEphemeris - Mechanismus-Test
        window_b = object()
        results: dict = {}

        async def _task(name, own_window, signal_own_ready, wait_for_other):
            astro.set_active_window(own_window)
            signal_own_ready.set()
            # Erzwingt echte Überlappung: wartet, bis der jeweils andere Task
            # sein Fenster ebenfalls gesetzt hat, bevor zurückgelesen wird.
            await wait_for_other.wait()
            seen = astro._active_window.get()
            results[name] = seen is own_window
            astro.clear_active_window()

        async def _run():
            ev_a_ready = asyncio.Event()
            ev_b_ready = asyncio.Event()
            await asyncio.gather(
                _task("A", window_a, ev_a_ready, ev_b_ready),
                _task("B", window_b, ev_b_ready, ev_a_ready),
            )

        asyncio.run(_run())

        assert results["A"] is True, (
            "Task A sah nach der erzwungenen Überlappung NICHT sein eigenes Fenster "
            "(BUG-63-Race: Task B hat das globale Fenster überschrieben)."
        )
        assert results["B"] is True, (
            "Task B sah nach der erzwungenen Überlappung NICHT sein eigenes Fenster "
            "(BUG-63-Race: Task A hat das globale Fenster überschrieben)."
        )
        assert astro._active_window.get() is None, "Nach Testende sollte kein Fenster mehr aktiv sein."

    def test_two_concurrent_preview_alignment_calls_use_own_window_only(self, monkeypatch):
        """Integrationsnaher Test auf dem echten Produktionspfad: zwei ECHT
        gleichzeitige `preview_alignment()`-Coroutinen (asyncio.gather, kein
        TestClient) für zwei garantiert unterschiedliche Standorte (Babelsberg/
        Potsdam vs. München, >500 km auseinander). `_win_for()` wird
        instrumentiert (monkeypatch auf das Modul-Attribut, wirkt daher auch für
        den innerhalb astronomy.py aufgerufenen Namen `_win_for`): für jeden
        Aufruf wird geprüft, dass ein zurückgegebenes Fenster-Objekt IMMER zu den
        angefragten Koordinaten passt (WindowEphemeris.lat/.lon == observer_lat/
        lon des jeweiligen Requests) - nie das Fenster des jeweils anderen,
        gleichzeitig laufenden Requests (BUG-63-Regression: 'A fällt unbemerkt
        auf den langsamen Pfad zurück' wäre die einzig SICHTBARE Folge einer
        Kontamination, weil covers() bei falschen Koordinaten sauber ablehnt -
        die Instrumentierung macht die interne Zuordnung trotzdem sichtbar)."""
        import calculations.astronomy as astro
        import main

        from data.elevation import provider

        async def _fake_elevation_difference(*args, **kwargs):
            return 50.0, False

        monkeypatch.setattr(provider, "elevation_difference", _fake_elevation_difference)

        mismatches = []
        unexpected_none = []
        orig_win_for = astro._win_for

        def _is_a(lat, lon):
            return abs(lat - _OBSERVER_LAT) < 1e-6 and abs(lon - _OBSERVER_LON) < 1e-6

        def _is_b(lat, lon):
            return abs(lat - 48.1351) < 1e-6 and abs(lon - 11.5820) < 1e-6

        def _spy_win_for(lat, lon, d):
            w = orig_win_for(lat, lon, d)
            if w is not None and (abs(w.lat - lat) > 1e-6 or abs(w.lon - lon) > 1e-6):
                # Fenster zurückgegeben, das NICHT zu den angefragten Koordinaten passt.
                mismatches.append((lat, lon, w.lat, w.lon))
            if w is None and (_is_a(lat, lon) or _is_b(lat, lon)):
                # BUG-63-Race-Symptom: eigenes Fenster ist aktiv gesetzt, aber durch
                # den jeweils anderen Request überschrieben -> covers() lehnt ab ->
                # _win_for() liefert None -> stiller Rückfall auf den langsamen Pfad,
                # obwohl für exakt diese Koordinaten ein eigenes Fenster existieren sollte.
                unexpected_none.append((lat, lon))
            return w

        monkeypatch.setattr(astro, "_win_for", _spy_win_for)

        req_a = main.PreviewAlignmentRequest(
            observer_lat=_OBSERVER_LAT, observer_lon=_OBSERVER_LON,
            subject_lat=_SUBJECT_LAT, subject_lon=_SUBJECT_LON,
            subject_height_m=15.0, subject_width_m=10.0, days=14, save=False,
        )
        # München - garantiert andere Koordinaten (>500 km von Babelsberg/Potsdam entfernt).
        req_b = main.PreviewAlignmentRequest(
            observer_lat=48.1351, observer_lon=11.5820,
            subject_lat=48.1500, subject_lon=11.6000,
            subject_height_m=100.0, subject_width_m=30.0, days=14, save=False,
        )

        async def _run():
            return await asyncio.gather(
                main.preview_alignment(req_a, _role="host"),
                main.preview_alignment(req_b, _role="host"),
            )

        result_a, result_b = asyncio.run(_run())

        assert not mismatches, (
            f"_win_for() lieferte mindestens einmal ein Fenster zurück, dessen "
            f"Koordinaten NICHT zum anfragenden Request passten: {mismatches} - "
            "BUG-63-Race: ein gleichzeitig laufender Request hat das globale "
            "Fenster kontaminiert."
        )
        assert not unexpected_none, (
            f"_win_for() lieferte für eigene, aktiv gesetzte Koordinaten unerwartet "
            f"None zurück (stiller Rückfall auf den langsamen Pfad): {unexpected_none} - "
            "BUG-63-Race: der jeweils andere gleichzeitig laufende Request hat das "
            "globale Fenster überschrieben, bevor covers() für die eigenen "
            "Koordinaten geprüft wurde."
        )
        assert result_a["profile"]["azimuth_deg"] != result_b["profile"]["azimuth_deg"], (
            "Testaufsetzung fragwürdig: beide Requests lieferten dasselbe Profil - "
            "die beiden Standorte sind nicht wie erwartet unterschiedlich eingeflossen."
        )
        assert astro._active_window.get() is None, (
            "Nach beiden abgeschlossenen preview_alignment()-Aufrufen sollte kein "
            "Fenster mehr aktiv sein (beide finally-Blöcke müssen gelaufen sein)."
        )
