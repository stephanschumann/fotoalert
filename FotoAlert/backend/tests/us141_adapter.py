"""US-141 — gemeinsamer Unterbau der Schalter-Tests (HILFSMODUL, enthält selbst keine Tests).

Warum es dieses Modul gibt: Das Ticket legt nur einen Teil der Schnittstelle fest
(Baustein data/regionen.py, /locations mit den Feldern land, region, paused). Wie der Host
einen Schalter setzt (Adresse, Methode, Inhalt) und wie die Gebietsliste für das Menü aussieht,
steht NICHT im Ticket (Abschnitt „Schnittstellen-Entwurf“, Punkt 6: nur „neue Host-Endpunkte
für Land und Region, keiner für Orte“). Damit die Tests trotzdem schreibbar sind, steht alles,
was nur ein VORSCHLAG dieser Tests ist, gesammelt im Block „SCHNITTSTELLEN-VORSCHLAG“ unten.
Wird beim Ready-for-Dev-Gate anders entschieden, ändern sich nur diese Konstanten und die
Aufruf-Helfer in diesem Modul — nicht die einzelnen Tests.

Was die Tests selbst prüfen, ist Verhalten aus dem Ticket (Akzeptanzkriterien, Entscheidungen),
über öffentlich sichtbare Wirkung: GET /locations (paused, land, region), /opportunities,
/opportunities/today, /daily-briefing, /calendar, /discover und die Aufrufe der Rechenprozesse.

Isolation: Jeder Test bekommt eine eigene Welt (eigene temporäre Datenbank, eigene Feed- und
Kalenderdatei, eigene Ortsliste). Die geteilte Entwicklungsdatenbank, die echten Cache-Dateien
und das Git-Repo werden nie angefasst (Sicherungsfunktionen sind abgeschaltet).

Python-3.9-kompatibel (Produktion/CI).
"""
from __future__ import annotations

import re
import threading
import time
from collections import OrderedDict
from datetime import date, datetime, timedelta, timezone
from urllib.parse import quote

import pytest

# ════════════════════════════════════════════════════════════════════════════
# AUS DEM TICKET (Schnittstellen-Entwurf, Beschreibung, Entscheidungen 15–19)
# ════════════════════════════════════════════════════════════════════════════
MODUL_REGIONEN = "data.regionen"          # Ticket: schlage_region_vor(lat, lon, name=None) -> Land + Region
FELD_LAND = "land"                        # Ticket Punkt 1/6: /locations liefert land, region, paused
FELD_REGION = "region"
FELD_PAUSIERT = "paused"

NAME_SONSTIGE = "Sonstige"                # Ticket Beschreibung 3/8, Entscheidung 19
NAME_OHNE_REGION = "Ohne Region"
LAND_UK = "Vereinigtes Königreich (UK)"   # Entscheidung 15/19 (Anzeigename)
REGION_ENGLAND = "England"
LAENDER_IN_REIHENFOLGE = [                # AK-33 + AK-112 (alphabetisch nach deutschem Namen, „Sonstige“ am Ende)
    "Deutschland", "Frankreich", "Italien", "Niederlande", "Norwegen",
    "Österreich", "Schweiz", LAND_UK, NAME_SONSTIGE,
]

# ════════════════════════════════════════════════════════════════════════════
# SCHNITTSTELLEN-VORSCHLAG DIESER TESTS (steht NICHT im Ticket — Freigabe offen)
# ════════════════════════════════════════════════════════════════════════════
PFAD_GEBIETE = "/areas"                       # GET: Länder mit Regionen, Zustand, „aktive von gesamten Orten“
PFAD_LAND = "/areas/{land}"                   # Land (Sammelschalter) an/aus
PFAD_REGION = "/areas/{land}/{region}"        # Region an/aus
METHODE_SCHALTEN = "PUT"
FELD_AN = "enabled"                           # Inhalt: {"enabled": true|false}
# Antwortform von GET /areas (auf diese Schlüssel greift nur lies_gebiete() zu):
KEY_LAENDER = "laender"                       # {"laender": [ {...Land...}, ... ]}
KEY_REGIONEN = "regionen"                     # im Land: Liste der Regionen
KEY_NAME = "name"
KEY_ZUSTAND = "zustand"                       # Land: "an" | "aus" | "teilweise" — Region: "an" | "aus"
KEY_AKTIV = "aktiv"                           # Anzahl aktiver Orte
KEY_GESAMT = "gesamt"                         # Anzahl aller Orte
ZUSTAND_AN, ZUSTAND_AUS, ZUSTAND_TEILWEISE = "an", "aus", "teilweise"

PW_HOST = "test-host-pw"                      # conftest.py
PW_NUTZER = "test-user-pw"

# ── Testorte (Koordinaten: allgemein bekannte Referenzpunkte, nicht aus der Ortsliste der App) ──
# key: (Name, Breite, Länge, Land, Region oder None)
ORTE = OrderedDict([
    ("berlin1",   ("Berlin Mitte",           52.5200,  13.4050, "Deutschland", "Berlin")),
    ("berlin2",   ("Berlin Kreuzberg",       52.4990,  13.4030, "Deutschland", "Berlin")),
    ("potsdam",   ("Potsdam",                52.3906,  13.0645, "Deutschland", "Brandenburg")),
    ("cottbus",   ("Cottbus",                51.7563,  14.3329, "Deutschland", "Brandenburg")),
    ("muenchen",  ("München",                48.1374,  11.5755, "Deutschland", "Bayern")),
    ("ohne",      ("Ort ohne Region",        51.0000,  10.0000, "Deutschland", NAME_OHNE_REGION)),
    ("london1",   ("London Zentrum",         51.5074,  -0.1278, LAND_UK, REGION_ENGLAND)),
    ("london2",   ("London Westminster",     51.5007,  -0.1246, LAND_UK, REGION_ENGLAND)),
    ("sterzing",  ("Sterzing",               46.8941,  11.4300, "Italien", "Trentino-Südtirol")),
    ("venedig",   ("Venedig",                45.4408,  12.3155, "Italien", "Venetien")),
    ("reykjavik", ("Reykjavik",              64.1466, -21.9426, NAME_SONSTIGE, None)),
])


def ort_id(key: str) -> str:
    return "custom_us141_" + key


def de_schluessel(name: str) -> str:
    """Alphabetische Ordnung nach deutschem Anzeigenamen (Ö wie O) — AK-112."""
    return (name.lower().replace("ä", "a").replace("ö", "o").replace("ü", "u").replace("ß", "ss"))


# ════════════════════════════════════════════════════════════════════════════
# Anmeldung
# ════════════════════════════════════════════════════════════════════════════

def als_host(client) -> None:
    client.cookies.clear()
    r = client.post("/login", json={"password": PW_HOST})
    assert r.status_code == 200, r.text


def als_nutzer(client) -> None:
    client.cookies.clear()
    r = client.post("/login", json={"password": PW_NUTZER})
    assert r.status_code == 200, r.text


def abgemeldet(client) -> None:
    client.cookies.clear()


# ════════════════════════════════════════════════════════════════════════════
# „Schnittstelle fehlt“ sauber melden (statt eines zufälligen 404)
# ════════════════════════════════════════════════════════════════════════════

def _normiere(pfad: str) -> str:
    return re.sub(r"\{[^}]+\}", "{}", pfad)


def route_vorhanden(pfad_vorlage: str, methode: str) -> bool:
    import main
    ziel = _normiere(pfad_vorlage)
    for r in main.app.routes:
        if _normiere(getattr(r, "path", "")) == ziel and methode.upper() in (getattr(r, "methods", None) or ()):
            return True
    return False


def brauche_route(pfad_vorlage: str, methode: str, was: str) -> None:
    if not route_vorhanden(pfad_vorlage, methode):
        pytest.fail("Schnittstelle fehlt: %s (%s %s) ist noch nicht gebaut — Vorschlag dieser Tests, "
                    "Ticket US-141 nennt nur ‚neue Host-Endpunkte für Land und Region‘; "
                    "erwartet rot vor der Umsetzung" % (was, methode, pfad_vorlage))


def brauche_patch_zuordnung() -> None:
    import main
    if FELD_LAND not in main.PATCHABLE_LOCATION_FIELDS or FELD_REGION not in main.PATCHABLE_LOCATION_FIELDS:
        pytest.fail("Schnittstelle fehlt: PATCH /locations/{id} nimmt die Felder 'land' und 'region' noch nicht an "
                    "(Ticket: Land und Region je Ort werden gespeichert, der Host kann sie ändern; "
                    "erwartet rot vor der Umsetzung)")


# ════════════════════════════════════════════════════════════════════════════
# Schalten und Lesen
# ════════════════════════════════════════════════════════════════════════════

def schalte_land(client, land: str, an: bool):
    brauche_route(PFAD_LAND, METHODE_SCHALTEN, "Land-Schalter")
    return client.request(METHODE_SCHALTEN, PFAD_LAND.format(land=quote(land, safe="")), json={FELD_AN: an})


def schalte_region(client, land: str, region: str, an: bool):
    brauche_route(PFAD_REGION, METHODE_SCHALTEN, "Regions-Schalter")
    return client.request(METHODE_SCHALTEN,
                          PFAD_REGION.format(land=quote(land, safe=""), region=quote(region, safe="")),
                          json={FELD_AN: an})


def host_schaltet_land(client, land: str, an: bool) -> None:
    als_host(client)
    r = schalte_land(client, land, an)
    assert r.status_code == 200, "Land %r %s schalten: %s %s" % (land, "an" if an else "aus", r.status_code, r.text)


def host_schaltet_region(client, land: str, region: str, an: bool) -> None:
    als_host(client)
    r = schalte_region(client, land, region, an)
    assert r.status_code == 200, "Region %r/%r %s schalten: %s %s" % (land, region, "an" if an else "aus",
                                                                       r.status_code, r.text)


def lies_gebiete(client) -> "OrderedDict":
    """GET /areas -> {Land: {zustand, aktiv, gesamt, regionen: {Region: {...}}}} (Reihenfolge bleibt erhalten)."""
    brauche_route(PFAD_GEBIETE, "GET", "Gebietsliste für das Host-Menü")
    als_host(client)        # das Menü ist Host-Sache; wer es liest, ist als Host angemeldet
    r = client.get(PFAD_GEBIETE)
    assert r.status_code == 200, r.text
    daten = r.json()
    laender = daten[KEY_LAENDER] if isinstance(daten, dict) else daten
    aus = OrderedDict()
    for land in laender:
        regionen = OrderedDict()
        for reg in land.get(KEY_REGIONEN, []) or []:
            regionen[reg[KEY_NAME]] = {"zustand": reg.get(KEY_ZUSTAND), "aktiv": reg.get(KEY_AKTIV),
                                       "gesamt": reg.get(KEY_GESAMT)}
        aus[land[KEY_NAME]] = {"zustand": land.get(KEY_ZUSTAND), "aktiv": land.get(KEY_AKTIV),
                               "gesamt": land.get(KEY_GESAMT), "regionen": regionen}
    return aus


def lies_orte(client) -> dict:
    """GET /locations -> {id: Ort}; meldet sauber, wenn land/region/paused noch nicht geliefert werden."""
    r = client.get("/locations")
    assert r.status_code == 200, r.text
    orte = {o["id"]: o for o in r.json()}
    for o in orte.values():
        for feld in (FELD_LAND, FELD_REGION, FELD_PAUSIERT):
            if feld not in o:
                pytest.fail("Schnittstelle fehlt: GET /locations liefert das Feld '%s' noch nicht "
                            "(Ticket: Schnittstelle Punkt 6, AK-77; erwartet rot vor der Umsetzung)" % feld)
        break
    return orte


def pausierte_ids(client) -> set:
    return {i for i, o in lies_orte(client).items() if o[FELD_PAUSIERT]}


def aktive_ids(client) -> set:
    return {i for i, o in lies_orte(client).items() if not o[FELD_PAUSIERT]}


def feed_ids(client, **params) -> set:
    r = client.get("/opportunities", params=params)
    assert r.status_code == 200, r.text
    return {e["location_id"] for e in r.json()}


# ════════════════════════════════════════════════════════════════════════════
# Termine (Feed/Kalender)
# ════════════════════════════════════════════════════════════════════════════

def termin(loc_id: str, tage: float = 1.0, typ: str = "GOLDEN_HOUR", score: float = 0.8,
           lat: float = 52.5, lon: float = 13.4, nr: int = 0, zeit: "datetime" = None) -> dict:
    """Ein vollständiger Feed-/Kalender-Termin (genug Felder für /opportunities, /opportunities/today,
    /daily-briefing und /calendar)."""
    t = zeit if zeit is not None else (datetime.now(timezone.utc) + timedelta(days=tage))
    return {
        "id": "ev_%s_%s_%s_%d" % (loc_id, typ, int(t.timestamp()), nr),
        "location_id": loc_id, "location_name": "Testort " + loc_id,
        "event_type": typ, "title": "Test %s %s" % (typ, loc_id), "description": "US-141-Testtermin",
        "shoot_time": t.isoformat(),
        "shoot_window_start": t.isoformat(),
        "shoot_window_end": (t + timedelta(minutes=30)).isoformat(),
        "overall_score": score, "astronomy_score": score, "weather_score": 0.0, "location_score": 1.0,
        "camera_hints": [], "subject_azimuth": None, "celestial_azimuth": None, "celestial_altitude": None,
        "alert_priority": 1, "weather_description": "",
        "observer_lat": lat, "observer_lon": lon,
    }


def termin_heute(loc_id: str, **kw) -> dict:
    mittag = datetime.combine(date.today(), datetime.min.time()).replace(hour=12, tzinfo=timezone.utc)
    return termin(loc_id, zeit=mittag, **kw)


# ════════════════════════════════════════════════════════════════════════════
# Die Welt (Fixtures)
# ════════════════════════════════════════════════════════════════════════════

class Welt:
    """Eine isolierte Testwelt: eigene Datenbank, Feed-, Kalender- und Ortsliste."""

    def __init__(self, store, tmp, feed_pfad, orte):
        self.store = store
        self.tmp = tmp
        self.feed = feed_pfad
        self.orte = orte            # key -> PhotoLocation

    def id(self, key: str) -> str:
        return ort_id(key)

    def ids(self, *keys: str) -> set:
        return {ort_id(k) for k in keys}

    def koord(self, key: str):
        o = self.orte[key]
        return o.observer_lat, o.observer_lon

    def setze_feed(self, termine: list) -> None:
        """Feed-Datei auf der Festplatte UND Arbeitsspeicher setzen (Zustand vor dem Schalten)."""
        import json
        import main
        self.feed.write_text(json.dumps({"computed_at": "2026-10-11T00:00:00+00:00",
                                         "opportunities": list(termine)}), encoding="utf-8")
        main._feed_cache = list(termine)

    def setze_kalender(self, termine: list) -> None:
        import main
        main._calendar_cache = list(termine)
        main._calendar_computed_at = "2026-10-11T00:00:00+00:00"

    def termine_fuer(self, keys, **kw) -> list:
        out = []
        for k in keys:
            lat, lon = self.koord(k)
            out.append(termin(ort_id(k), lat=lat, lon=lon, **kw))
        return out


def _photo_loc(key: str, spec: tuple):
    from data.locations import LocationCategory, PhotoLocation
    name, lat, lon, _land, _reg = spec
    return PhotoLocation(
        id=ort_id(key), name=name, description="US-141-Testort", category=LocationCategory.SKYLINE,
        observer_lat=lat, observer_lon=lon, subject_lat=lat + 0.005, subject_lon=lon + 0.005,
        subject_name="Motiv " + name, subject_height_m=60.0, subject_width_m=20.0, distance_m=700,
        focal_length_suggestions=[50], difficulty=1,
    )


def _custom_dict(loc) -> dict:
    return {
        "id": loc.id, "name": loc.name, "description": loc.description, "category": loc.category.name,
        "observer_lat": loc.observer_lat, "observer_lon": loc.observer_lon,
        "subject_lat": loc.subject_lat, "subject_lon": loc.subject_lon, "subject_name": loc.subject_name,
        "subject_height_m": loc.subject_height_m, "subject_width_m": loc.subject_width_m,
        "distance_m": loc.distance_m, "focal_length_suggestions": list(loc.focal_length_suggestions),
        "special_notes": "", "difficulty": 1, "observer_floor_height_m": 0.0,
    }


def baue_welt(monkeypatch, tmp_path) -> Welt:
    """Eigene Datenbank + Ortsliste (die geteilte Liste wird NUR für die Dauer des Tests getauscht
    und danach vom Aufräum-Schritt der Fixture zurückgesetzt) + leere Feed-/Kalender-/Scout-Caches."""
    import collections
    import main
    from data import backup as _backup
    from data import locations as _dl
    from data.store import LocationStore

    store = LocationStore(db_path=tmp_path / "us141.db")
    orte = OrderedDict((k, _photo_loc(k, spec)) for k, spec in ORTE.items())
    for o in orte.values():
        store.create_custom(_custom_dict(o))

    feed = tmp_path / "opportunities.json"
    feed.write_text('{"computed_at": "2026-10-11T00:00:00+00:00", "opportunities": []}', encoding="utf-8")

    monkeypatch.setattr(main, "_store", store)
    monkeypatch.setattr(main, "_OPP_CACHE", feed)
    monkeypatch.setattr(main, "_feed_cache", [])
    monkeypatch.setattr(main, "_calendar_cache", [])
    monkeypatch.setattr(main, "_calendar_computed_at", None)
    monkeypatch.setattr(main, "_discover_cache", {})
    monkeypatch.setattr(main, "_ondemand_month_cache", collections.OrderedDict())
    monkeypatch.setattr(main, "_recompute_pending", set())
    monkeypatch.setattr(main, "_precompute_running", False)
    monkeypatch.setattr(main, "_NO_BACKGROUND", True)
    # Nichts darf in ein Git-Repo oder auf die Festplatte außerhalb des Test-Ordners sichern.
    for fn in ("backup_after_edit", "backup_after_precompute", "snapshot_before_precompute"):
        if hasattr(_backup, fn):
            monkeypatch.setattr(_backup, fn, lambda *a, **k: None)

    # Ortsliste: dieselbe Liste, die main und die Scout-Pipeline benutzen — nur für diesen Test getauscht.
    gespeichert = list(_dl.LOCATIONS)
    _dl.LOCATIONS[:] = list(orte.values())
    welt = Welt(store, tmp_path, feed, orte)
    welt._gespeicherte_liste = gespeichert
    return welt


def baue_welt_zugeordnet(client, welt: Welt) -> Welt:
    """Gibt jedem Testort Land und Region (der Host ändert die Zuordnung per PATCH, Ticket Beschreibung 3)."""
    brauche_patch_zuordnung()
    als_host(client)
    for key, (_n, _la, _lo, land, region) in ORTE.items():
        body = {FELD_LAND: land}
        if region is not None:
            body[FELD_REGION] = region
        r = client.patch("/locations/" + ort_id(key), json=body)
        assert r.status_code == 200, "Zuordnung %s: %s %s" % (key, r.status_code, r.text)
    abgemeldet(client)
    return welt


def welt_aufraeumen(welt: Welt) -> None:
    from data import locations as _dl
    _dl.LOCATIONS[:] = welt._gespeicherte_liste


# ════════════════════════════════════════════════════════════════════════════
# Falscher Rechenprozess (für die Nachlade-Tests): nichts Echtes wird gestartet
# ════════════════════════════════════════════════════════════════════════════

class ProzessSpion:
    """Ersetzt asyncio.create_subprocess_exec: merkt sich jeden Start eines Rechenprozesses
    (precompute.py), zählt die gleichzeitig laufenden und kann künstlich langsam sein.
    Die Übergabe 'sperre' (threading.Event) hält Prozesse an, bis der Test sie freigibt."""

    def __init__(self):
        self.starts = []            # Liste von Argument-Listen (nur precompute.py)
        self.start_zeiten = []
        self.aktiv = 0
        self.max_aktiv = 0
        self.beendet = 0
        self.dauer_s = 0.0
        self.sperre = None          # threading.Event oder None
        self.beim_ende = None       # Funktion(args), z. B. Feed-Datei schreiben
        self.beendet_ids = []       # Ergebnis von beim_ende je Prozess
        self.rc = 0                 # Rückgabewert, mit dem die Prozesse enden (0 = Erfolg)
        self.abgebrochen = 0        # wie oft die Anwendung einen Prozess abgebrochen hat (kill/terminate)
        self._lock = threading.Lock()

    def ids_in_starts(self, ids) -> set:
        """Welche der Ort-IDs kommen in irgendeinem gestarteten Rechenprozess vor (egal in welcher Form
        übergeben: --location-id a, --location-ids a,b, ...)."""
        gefunden = set()
        for args in self.starts:
            text = " ".join(str(a) for a in args)
            for i in ids:
                if i in text:
                    gefunden.add(i)
        return gefunden

    async def fake_exec(self, *args, **kwargs):
        import asyncio
        spion = self
        if not any("precompute.py" in str(a) for a in args):
            raise AssertionError("Unerwarteter Prozessstart in einem Test: %r" % (args,))

        class _Proc:
            returncode = None

            async def communicate(self_inner):
                with spion._lock:
                    spion.aktiv += 1
                    spion.max_aktiv = max(spion.max_aktiv, spion.aktiv)
                try:
                    waited = 0.0
                    while (spion.sperre is not None and not spion.sperre.is_set()
                           and self_inner.returncode is None and waited < 20.0):
                        await asyncio.sleep(0.02)
                        waited += 0.02
                    if self_inner.returncode is not None:      # von der Anwendung abgebrochen
                        return b"", None
                    if spion.dauer_s:
                        await asyncio.sleep(spion.dauer_s)
                    if spion.beim_ende is not None:
                        spion.beendet_ids.append(spion.beim_ende(args))
                finally:
                    with spion._lock:
                        spion.aktiv -= 1
                        spion.beendet += 1
                self_inner.returncode = spion.rc
                return b"", None

            def kill(self_inner):
                spion.abgebrochen += 1
                self_inner.returncode = -9

            def terminate(self_inner):
                spion.abgebrochen += 1
                self_inner.returncode = -15

            async def wait(self_inner):
                return self_inner.returncode if self_inner.returncode is not None else 0

        with self._lock:
            self.starts.append(list(args))
            self.start_zeiten.append(time.time())
        return _Proc()


def warte_bis(bedingung, sekunden: float = 10.0, schritt: float = 0.05) -> bool:
    ende = time.time() + sekunden
    while time.time() < ende:
        if bedingung():
            return True
        time.sleep(schritt)
    return bedingung()


# ════════════════════════════════════════════════════════════════════════════
# Fixtures (werden in den Testdateien importiert: from us141_adapter import welt, welt_z)
# ════════════════════════════════════════════════════════════════════════════

@pytest.fixture
def welt(client, monkeypatch, tmp_path):
    """Eigene Welt mit 11 Testorten, noch OHNE Land/Region-Zuordnung."""
    w = baue_welt(monkeypatch, tmp_path)
    try:
        yield w
    finally:
        welt_aufraeumen(w)


@pytest.fixture
def welt_z(client, welt):
    """Wie `welt`, aber jeder Ort hat sein Land und seine Region (Zuordnung durch den Host)."""
    return baue_welt_zugeordnet(client, welt)
