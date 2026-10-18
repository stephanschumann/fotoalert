"""US-141 — Schalter für Länder und Regionen und die Rechte dazu (Backend, ohne Oberfläche).

Geprüft wird das Verhalten aus den Entscheidungen 15–21 und den Akzeptanzkriterien AK-27 bis AK-39,
AK-56 bis AK-58, AK-79 bis AK-90, AK-110 bis AK-112 des Tickets:
  - Land = Sammelschalter (an / aus / teilweise), gespeichert wird je Region (Entscheidung 21)
  - ein Ort läuft nur, wenn sein Land UND seine Region an sind
  - Länder ohne Regionen („Sonstige“), „Ohne Region“, Vereinigtes Königreich mit Region England
  - kein Schalter für einzelne Orte; unbekannte Ziele werden abgelehnt, ohne etwas zu ändern
  - nur der Host darf schalten; Nutzer (User-Passwort) und Nicht-Angemeldete nicht
  - Umhängen eines Orts in ein anderes Land / eine andere Region
  - Altbestand bleibt aktiv, bestehende Felder bleiben unverändert

Die Adresse und Form der Schalter-Aufrufe ist in us141_adapter.py ein VORSCHLAG dieser Tests
(das Ticket nennt sie nicht). Rot vor der Umsetzung heißt: „Schnittstelle fehlt“.

Als SCHUTZTEST gekennzeichnete Tests sind schon heute grün und sichern bestehendes Verhalten.
Python-3.9-kompatibel.
"""
from __future__ import annotations

import logging

import pytest

from us141_adapter import (  # noqa: F401  (welt/welt_z sind Fixtures)
    LAENDER_IN_REIHENFOLGE, LAND_UK, NAME_OHNE_REGION, NAME_SONSTIGE, REGION_ENGLAND,
    ZUSTAND_AN, ZUSTAND_AUS, ZUSTAND_TEILWEISE,
    FELD_LAND, FELD_PAUSIERT, FELD_REGION, ORTE,
    abgemeldet, aktive_ids, als_host, de_schluessel, host_schaltet_land, host_schaltet_region,
    lies_gebiete, lies_orte, ort_id, pausierte_ids, schalte_land, schalte_region, welt, welt_z,
)

pytestmark = [pytest.mark.api, pytest.mark.regression]

DE_ORTE = ("berlin1", "berlin2", "potsdam", "cottbus", "muenchen", "ohne")
ALLE = tuple(ORTE.keys())


# ── Die Liste im Host-Menü ────────────────────────────────────────────────────

def test_gebietsliste_laender_und_regionen_alphabetisch_sonstige_am_ende(client, welt_z):
    """AK-28, AK-33, AK-85, AK-112: feste Länderliste (mit UK, ohne England als Land), alphabetisch nach
    deutschem Namen, „Sonstige“ am Ende und ohne Regionen; Regionen alphabetisch, „Ohne Region“ am Ende;
    das Vereinigte Königreich hat (mindestens) England, Nordirland, Schottland, Wales."""
    g = lies_gebiete(client)
    assert list(g.keys()) == LAENDER_IN_REIHENFOLGE
    assert g[NAME_SONSTIGE]["regionen"] == {}, "‚Sonstige‘ hat keine Regionen, nur den Länder-Schalter"
    regionen_de = list(g["Deutschland"]["regionen"].keys())
    assert regionen_de[-1] == NAME_OHNE_REGION
    ohne_letzte = [r for r in regionen_de if r != NAME_OHNE_REGION]
    assert ohne_letzte == sorted(ohne_letzte, key=de_schluessel)
    assert {"Berlin", "Brandenburg", "Bayern"} <= set(regionen_de)
    assert {REGION_ENGLAND, "Nordirland", "Schottland", "Wales"} <= set(g[LAND_UK]["regionen"].keys())


def test_gebietsliste_zeigt_aktive_von_gesamten_orten(client, welt_z):
    """AK-28, AK-29: hinter Land und Region steht „aktive von gesamten Orten“; Länder ohne Orte zeigen 0."""
    g = lies_gebiete(client)
    de = g["Deutschland"]
    assert (de["aktiv"], de["gesamt"]) == (6, 6)
    assert (de["regionen"]["Berlin"]["aktiv"], de["regionen"]["Berlin"]["gesamt"]) == (2, 2)
    assert (de["regionen"]["Brandenburg"]["aktiv"], de["regionen"]["Brandenburg"]["gesamt"]) == (2, 2)
    assert (g["Italien"]["aktiv"], g["Italien"]["gesamt"]) == (2, 2)
    assert (g[NAME_SONSTIGE]["aktiv"], g[NAME_SONSTIGE]["gesamt"]) == (1, 1)
    assert g["Österreich"]["gesamt"] == 0, "Land ohne Orte erscheint mit 0 Orten (AK-29)"


# ── Land aus / Region aus / teilweise (Sammelschalter) ────────────────────────

def test_land_ausschalten_pausiert_alle_orte_des_landes_und_nur_diese(client, welt_z):
    """AK-80, AK-79: Land aus -> alle Orte des Landes ruhen, auch in Regionen, die vorher an waren;
    Orte anderer Länder bleiben aktiv; die Orte bleiben in der Ortsliste (pausiert, nicht versteckt)."""
    host_schaltet_land(client, "Deutschland", False)
    assert pausierte_ids(client) == welt_z.ids(*DE_ORTE)
    assert aktive_ids(client) == welt_z.ids(*[k for k in ALLE if k not in DE_ORTE])
    assert set(lies_orte(client)) == welt_z.ids(*ALLE), "pausierte Orte bleiben sichtbar (Entscheidung 4)"
    g = lies_gebiete(client)
    assert g["Deutschland"]["zustand"] == ZUSTAND_AUS
    assert all(r["zustand"] == ZUSTAND_AUS for r in g["Deutschland"]["regionen"].values())
    assert g["Deutschland"]["aktiv"] == 0 and g["Deutschland"]["gesamt"] == 6


def test_region_ausschalten_land_zeigt_teilweise(client, welt_z):
    """AK-81: Deutschland an, Brandenburg aus -> Berlin läuft weiter, Brandenburg ruht, Land „teilweise“."""
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    assert pausierte_ids(client) == welt_z.ids("potsdam", "cottbus")
    g = lies_gebiete(client)
    assert g["Deutschland"]["zustand"] == ZUSTAND_TEILWEISE
    assert (g["Deutschland"]["aktiv"], g["Deutschland"]["gesamt"]) == (4, 6)
    assert g["Deutschland"]["regionen"]["Brandenburg"]["zustand"] == ZUSTAND_AUS
    assert (g["Deutschland"]["regionen"]["Brandenburg"]["aktiv"],
            g["Deutschland"]["regionen"]["Brandenburg"]["gesamt"]) == (0, 2)
    assert g["Deutschland"]["regionen"]["Berlin"]["zustand"] == ZUSTAND_AN


def test_alle_regionen_einzeln_aus_land_zeigt_aus(client, welt_z):
    """AK-82: Sind alle Regionen eines Landes einzeln aus, zeigt das Land „aus“ (kein „an, aber nichts läuft“)."""
    for region in ("Berlin", "Brandenburg", "Bayern", NAME_OHNE_REGION):
        host_schaltet_region(client, "Deutschland", region, False)
    g = lies_gebiete(client)
    # Hinweis: Das Land hat laut Liste mehr Regionen als die vier mit Orten; „aus“ gilt, wenn ALLE aus sind.
    # Deshalb zusätzlich alle übrigen Regionen des Landes ausschalten.
    for region in list(g["Deutschland"]["regionen"].keys()):
        if g["Deutschland"]["regionen"][region]["zustand"] != ZUSTAND_AUS:
            host_schaltet_region(client, "Deutschland", region, False)
    assert lies_gebiete(client)["Deutschland"]["zustand"] == ZUSTAND_AUS
    assert pausierte_ids(client) == welt_z.ids(*DE_ORTE)


def test_region_einschalten_bei_ausgeschaltetem_land_nur_diese_region(client, welt_z):
    """AK-83: Land aus, dann eine Region ein -> nur diese Region läuft; das Land zeigt „teilweise“."""
    host_schaltet_land(client, "Deutschland", False)
    host_schaltet_region(client, "Deutschland", "Berlin", True)
    assert aktive_ids(client) >= welt_z.ids("berlin1", "berlin2")
    assert pausierte_ids(client) == welt_z.ids("potsdam", "cottbus", "muenchen", "ohne")
    assert lies_gebiete(client)["Deutschland"]["zustand"] == ZUSTAND_TEILWEISE


def test_land_wieder_einschalten_schaltet_alle_regionen_ein(client, welt_z):
    """AK-84 (Sammelschalter, Entscheidung 21): Land wieder an -> alle Regionen an, Land „an“,
    ein früheres Einzelmuster geht dabei verloren (von Stephan so akzeptiert)."""
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    host_schaltet_region(client, "Deutschland", "Bayern", False)
    host_schaltet_land(client, "Deutschland", False)
    host_schaltet_land(client, "Deutschland", True)
    assert pausierte_ids(client) == set()
    g = lies_gebiete(client)
    assert g["Deutschland"]["zustand"] == ZUSTAND_AN
    assert all(r["zustand"] == ZUSTAND_AN for r in g["Deutschland"]["regionen"].values())


def test_laender_ohne_orte_lassen_sich_schalten(client, welt_z):
    """AK-30: Österreich lässt sich als Land ausschalten und wieder einschalten, auch ohne Orte."""
    host_schaltet_land(client, "Österreich", False)
    assert lies_gebiete(client)["Österreich"]["zustand"] == ZUSTAND_AUS
    host_schaltet_land(client, "Österreich", True)
    assert lies_gebiete(client)["Österreich"]["zustand"] == ZUSTAND_AN
    assert pausierte_ids(client) == set(), "ohne Orte ändert sich an keinem Ort etwas"


# ── Länder ohne Regionen, „Sonstige“, „Ohne Region“ ──────────────────────────

def test_sonstige_hat_nur_den_laenderschalter(client, welt_z):
    """AK-36, AK-85: ‚Sonstige‘ hat einen eigenen Schalter (als Land) und keine Regionen; ein Regions-Schalter
    unter ‚Sonstige‘ wird abgelehnt."""
    host_schaltet_land(client, NAME_SONSTIGE, False)
    assert pausierte_ids(client) == welt_z.ids("reykjavik")
    assert lies_gebiete(client)[NAME_SONSTIGE]["zustand"] == ZUSTAND_AUS
    r = schalte_region(client, NAME_SONSTIGE, NAME_SONSTIGE, True)
    assert 400 <= r.status_code < 500, "Region unter ‚Sonstige‘ gibt es nicht: " + r.text
    assert pausierte_ids(client) == welt_z.ids("reykjavik"), "abgelehnter Aufruf darf nichts ändern"
    host_schaltet_land(client, NAME_SONSTIGE, True)
    assert pausierte_ids(client) == set()


def test_ohne_region_folgt_dem_land_und_hat_einen_eigenen_schalter(client, welt_z):
    """AK-86: ‚Ohne Region‘ folgt dem Länder-Schalter und lässt sich außerdem einzeln schalten;
    der Ort darunter wird von keinem anderen Schalter mitgerissen."""
    host_schaltet_land(client, "Deutschland", False)
    assert welt_z.id("ohne") in pausierte_ids(client)
    host_schaltet_land(client, "Deutschland", True)
    assert welt_z.id("ohne") in aktive_ids(client)
    host_schaltet_region(client, "Deutschland", NAME_OHNE_REGION, False)
    assert pausierte_ids(client) == welt_z.ids("ohne"), "nur der Ort unter ‚Ohne Region‘ ruht"


def test_vereinigtes_koenigreich_mit_region_england(client, welt_z):
    """AK-110: UK ist ein Land mit der Region England; die Londoner Orte stehen in England, Land und Region
    zeigen dieselbe Ortszahl; Land aus bzw. Region England aus pausiert dieselben Orte."""
    g = lies_gebiete(client)
    assert g[LAND_UK]["gesamt"] == g[LAND_UK]["regionen"][REGION_ENGLAND]["gesamt"] == 2
    assert g[LAND_UK]["aktiv"] == g[LAND_UK]["regionen"][REGION_ENGLAND]["aktiv"] == 2
    host_schaltet_land(client, LAND_UK, False)
    assert pausierte_ids(client) == welt_z.ids("london1", "london2")
    host_schaltet_land(client, LAND_UK, True)
    assert pausierte_ids(client) == set()
    host_schaltet_region(client, LAND_UK, REGION_ENGLAND, False)
    assert pausierte_ids(client) == welt_z.ids("london1", "london2")


# ── Ungültige Eingaben, kein Schalter pro Ort ────────────────────────────────

def test_unbekanntes_ziel_wird_abgelehnt_und_aendert_nichts(client, welt_z):
    """AK-39: unbekanntes Land, unbekannte Region, Region des falschen Landes, fehlender oder falscher Inhalt
    -> abgelehnt (4xx), danach ist kein Ort pausiert."""
    als_host(client)
    antworten = [
        schalte_land(client, "Atlantis", False),
        schalte_region(client, "Deutschland", "Nirgendwo", False),
        schalte_region(client, "Deutschland", REGION_ENGLAND, False),   # England gehört zum Vereinigten Königreich
        client.request("PUT", "/areas/Deutschland/Berlin", json={"enabled": "vielleicht"}),
        client.request("PUT", "/areas/Deutschland/Berlin", json={}),
    ]
    for r in antworten:
        assert 400 <= r.status_code < 500, "erwartet Ablehnung, bekam %s %s" % (r.status_code, r.text)
    assert pausierte_ids(client) == set()


def test_schutz_orts_felder_pausiert_wird_von_patch_nicht_angenommen(client, welt):
    """SCHUTZTEST, AK-90: Es gibt keinen Schalter für einzelne Orte — ein PATCH mit ‚paused‘ wird abgelehnt
    und der Ort ändert sich nicht (heute grün, weil das Feld unbekannt ist; muss es nach der Umsetzung bleiben,
    denn ‚paused‘ wird aus Land und Region abgeleitet)."""
    als_host(client)
    r = client.patch("/locations/" + welt.id("potsdam"), json={"paused": True})
    assert 400 <= r.status_code < 500, r.text
    ort = next(o for o in client.get("/locations").json() if o["id"] == welt.id("potsdam"))
    assert ort.get("paused", False) is False


def test_orts_nummer_als_region_wird_abgelehnt(client, welt_z):
    """AK-90: Auch über den Regions-Schalter lässt sich kein einzelner Ort schalten (Ort-ID statt Region)."""
    als_host(client)
    r = schalte_region(client, "Deutschland", welt_z.id("potsdam"), False)
    assert 400 <= r.status_code < 500, r.text
    assert pausierte_ids(client) == set()


# ── Host-Rechte ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("rolle,erwartet", [("nutzer", 403), ("niemand", 401)], ids=["nutzer-403", "ohne-anmeldung-401"])
@pytest.mark.parametrize("ziel", ["land", "region"])
def test_nur_der_host_darf_schalten(client, welt_z, rolle, erwartet, ziel):
    """AK-27: Ein Nutzer mit User-Passwort wird abgelehnt (403), ohne Anmeldung gilt 401; der Zustand bleibt."""
    from us141_adapter import als_nutzer
    if rolle == "nutzer":
        als_nutzer(client)
    else:
        abgemeldet(client)
    if ziel == "land":
        r = schalte_land(client, "Deutschland", False)
    else:
        r = schalte_region(client, "Deutschland", "Brandenburg", False)
    assert r.status_code == erwartet, "%s %s" % (r.status_code, r.text)
    als_host(client)
    assert pausierte_ids(client) == set(), "ein abgelehnter Schalter-Aufruf darf nichts ändern"


# ── Umhängen, Zuordnung bleibt, Altbestand, Protokoll ────────────────────────

def test_umhaengen_in_ausgeschaltetes_gebiet_pausiert_den_ort_und_umgekehrt(client, welt_z):
    """AK-35, AK-37: Hängt der Host einen aktiven Ort in eine ausgeschaltete Region (oder ein ausgeschaltetes
    Land) um, ruht er danach und bleibt sichtbar; umgekehrt läuft er wieder, ‚Sonstige‘-Orte folgen nach dem
    Umhängen dem Schalter ihres neuen Landes."""
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    host_schaltet_land(client, NAME_SONSTIGE, False)
    als_host(client)
    r = client.patch("/locations/" + welt_z.id("muenchen"), json={FELD_LAND: "Deutschland", FELD_REGION: "Brandenburg"})
    assert r.status_code == 200, r.text
    r = client.patch("/locations/" + welt_z.id("potsdam"), json={FELD_LAND: "Deutschland", FELD_REGION: "Berlin"})
    assert r.status_code == 200, r.text
    r = client.patch("/locations/" + welt_z.id("reykjavik"), json={FELD_LAND: "Deutschland", FELD_REGION: "Berlin"})
    assert r.status_code == 200, r.text
    orte = lies_orte(client)
    assert orte[welt_z.id("muenchen")][FELD_PAUSIERT] is True, "Umhängen in ausgeschaltete Region pausiert"
    assert orte[welt_z.id("potsdam")][FELD_PAUSIERT] is False, "Umhängen in aktive Region aktiviert"
    assert orte[welt_z.id("reykjavik")][FELD_PAUSIERT] is False, "folgt dem Schalter des neuen Landes"
    assert welt_z.id("muenchen") in orte, "der Ort bleibt sichtbar"


def test_zuordnung_bleibt_beim_schalten_unveraendert(client, welt_z):
    """AK-87: Land und Region eines Orts sind gespeichert und ändern sich durch Aus-/Einschalten nicht von selbst."""
    vorher = {i: (o[FELD_LAND], o[FELD_REGION]) for i, o in lies_orte(client).items()}
    host_schaltet_land(client, "Deutschland", False)
    host_schaltet_region(client, "Deutschland", "Berlin", True)
    host_schaltet_land(client, "Deutschland", True)
    host_schaltet_land(client, LAND_UK, False)
    host_schaltet_land(client, LAND_UK, True)
    nachher = {i: (o[FELD_LAND], o[FELD_REGION]) for i, o in lies_orte(client).items()}
    assert nachher == vorher
    assert vorher[welt_z.id("potsdam")] == ("Deutschland", "Brandenburg")
    assert vorher[welt_z.id("london1")] == (LAND_UK, REGION_ENGLAND)


def test_altbestand_bleibt_aktiv_und_hat_land_und_region(client):
    """AK-56: Nach dem Update sind alle bisherigen Orte weiter aktiv und haben ein Land und eine Region
    (Orte in ‚Sonstige‘ haben keine Region). Prüft den echten Bestand der Test-Datenbank beim Start."""
    orte = lies_orte(client)
    assert orte, "die Test-Datenbank enthält keine Orte"
    pausiert = [i for i, o in orte.items() if o[FELD_PAUSIERT]]
    ohne_land = [i for i, o in orte.items() if not o[FELD_LAND]]
    ohne_region = [i for i, o in orte.items() if o[FELD_LAND] != NAME_SONSTIGE and not o[FELD_REGION]]
    assert pausiert == [], "nach dem Update darf kein bisheriger Ort pausiert sein: %s" % pausiert[:5]
    assert ohne_land == [], "Orte ohne Land: %s" % ohne_land[:5]
    assert ohne_region == [], "Orte ohne Region (außer ‚Sonstige‘): %s" % ohne_region[:5]


_ALTE_ORTS_FELDER = [
    "id", "name", "description", "category", "category_key", "observer_lat", "observer_lon", "subject_lat",
    "subject_lon", "ideal_azimuth_range", "subject_name", "subject_height_m", "subject_width_m",
    "elevation_difference_m", "observer_floor_height_m", "distance_m", "focal_length_suggestions",
    "special_notes", "solar_alignment_note", "lunar_alignment_note", "access_note", "locationscout_url",
    "difficulty", "possible_bodies", "image_url", "image_focus_x", "image_focus_y", "sightline_status",
    "sightline_angle_deg",
]


def test_schutz_bestehende_ortsfelder_bleiben_unveraendert(client, welt):
    """SCHUTZTEST, AK-57: Die bisherigen Angaben von GET /locations bleiben erhalten (neue Angaben nur
    zusätzlich) — für Web-App und iOS-App."""
    ort = next(o for o in client.get("/locations").json() if o["id"] == welt.id("potsdam"))
    fehlend = [f for f in _ALTE_ORTS_FELDER if f not in ort]
    assert fehlend == [], "bisherige Felder fehlen: %s" % fehlend
    assert ort["name"] == "Potsdam" and ort["observer_lat"] == pytest.approx(52.3906)


def test_jedes_umschalten_steht_im_server_protokoll(client, welt_z, caplog):
    """AK-58: Jedes Umschalten wird mit Ziel (Land/Region) und Richtung (an/aus) im Server-Protokoll festgehalten;
    der Eintrag zum Ausschalten unterscheidet sich vom Eintrag zum Einschalten. (Die genaue Wortwahl ist nicht
    festgelegt; der Zeitpunkt steckt im Protokolleintrag selbst.)"""
    caplog.set_level(logging.INFO)
    caplog.clear()
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    aus = [r.getMessage() for r in caplog.records if "Brandenburg" in r.getMessage()]
    caplog.clear()
    host_schaltet_region(client, "Deutschland", "Brandenburg", True)
    an = [r.getMessage() for r in caplog.records if "Brandenburg" in r.getMessage()]
    assert aus, "kein Protokolleintrag zum Ausschalten von Brandenburg"
    assert an, "kein Protokolleintrag zum Einschalten von Brandenburg"
    assert set(aus) != set(an), "Ausschalten und Einschalten sind im Protokoll nicht zu unterscheiden"


# ── Nutzer- und Ortsdaten bleiben beim Aus- und Einschalten ──────────────────

def test_aus_und_wieder_einschalten_verliert_keine_nutzer_und_ortsdaten(client, welt_z):
    """AK-25, AK-26 (Regel 2: „pausiert, nicht gelöscht“): Bewertung, Bestätigung (Verifikation) sowie Korrekturen
    und Höhenwerte eines Orts sind nach Region aus -> Land aus -> Land an unverändert da; auch WÄHREND der Pause
    sind sie abrufbar. (Das Beispielbild ist Teil von AK-25, braucht aber einen Bild-Upload -> eigener Test, siehe
    Bericht.)"""
    pid = welt_z.id("potsdam")
    als_host(client)
    r = client.patch("/locations/" + pid, json={"name": "Potsdam korrigiert", "subject_height_m": 77.0,
                                                "observer_floor_height_m": 3.0})
    assert r.status_code == 200, r.text
    r = client.post("/locations/%s/ratings" % pid, json={"value": 4, "device_id": "gerät-us141"})
    assert r.status_code == 201, r.text
    r = client.post("/locations/%s/verifications" % pid,
                    json={"location_name": "Potsdam korrigiert", "status": "ok", "comment": "passt", "date": "2026-10-11"})
    assert r.status_code == 201, r.text

    def stand():
        ort = lies_orte(client)[pid]
        bewertung = client.get("/locations/%s/ratings" % pid, params={"device_id": "gerät-us141"}).json()
        bestaetigungen = [(v["status"], v["comment"]) for v in client.get("/locations/%s/verifications" % pid).json()]
        return (ort["name"], ort["subject_height_m"], ort["observer_floor_height_m"], bewertung, bestaetigungen)

    vorher = stand()
    assert vorher[0] == "Potsdam korrigiert" and vorher[3]["count"] == 1 and vorher[4] == [("ok", "passt")]
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    assert pid in pausierte_ids(client)
    assert stand() == vorher, "während der Pause sind Nutzer- und Ortsdaten nicht mehr unverändert"
    host_schaltet_land(client, "Deutschland", False)
    host_schaltet_land(client, "Deutschland", True)
    assert pid in aktive_ids(client)
    assert stand() == vorher, "nach Aus und Wieder-Ein sind Nutzer- oder Ortsdaten verändert"
