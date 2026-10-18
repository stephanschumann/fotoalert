"""US-141 — Neu angelegte Orte in ausgeschalteten Gebieten, „Jetzt aktivieren“ und Rechte (Backend).

Geprüft wird (Akzeptanzkriterien AK-40 bis AK-45, AK-63, AK-87; Entscheidungen 3, 20, 23):
  - Ein neuer Ort in einem ausgeschalteten Land ODER einer ausgeschalteten Region startet pausiert;
    in einem Gebiet, das an ist, läuft er sofort (AK-40, AK-44). Er hat dann auch keine Chancen im Feed.
  - Land und Region des neuen Orts kommen aus der Lage, nie aus dem Namen (AK-87, AK-34).
  - Der Ort bleibt aus, bis der Host gewählt hat; nichts anderes schaltet ihn ein (AK-45, Entscheidung 23).
    Der Hinweis selbst (nicht wegklickbar, zwei Knöpfe) ist Oberfläche -> Browser-Test.
  - „Jetzt aktivieren“ = die REGION des neuen Orts einschalten (Entscheidung 20); ist auch das Land aus,
    läuft danach nur diese Region, das Land zeigt „teilweise“ (AK-41, AK-83). Die Rückfrage mit der Ortszahl
    braucht die Ortszahl der Region aus der Gebietsliste (hier geprüft); der Dialog selbst ist Browser-Test.
  - Legt ein normaler Nutzer den Ort an, bleibt er pausiert; schalten darf nur der Host (AK-63; Annahme
    „Frage 17, Empfehlung“ — im Ticket noch als „wartet auf Bestätigung“ geführt).

Das Anlegen läuft über den vorhandenen Weg POST /preview-alignment (save=true); Reverse-Geocoding und
Geländehöhen sind abgeschaltet (kein Netz), gespeichert wird in die Test-Datenbank der Welt.
Python-3.9-kompatibel.
"""
from __future__ import annotations

import pytest

from us141_adapter import (  # noqa: F401  (welt/welt_z sind Fixtures)
    FELD_LAND, FELD_PAUSIERT, FELD_REGION, ZUSTAND_TEILWEISE,
    abgemeldet, aktive_ids, als_host, als_nutzer, feed_ids, host_schaltet_land, host_schaltet_region,
    lies_gebiete, lies_orte, pausierte_ids, schalte_region, termin, welt, welt_z,
)

pytestmark = [pytest.mark.api, pytest.mark.regression]


@pytest.fixture
def ohne_netz(monkeypatch):
    """Kein Reverse-Geocoding, keine Höhenabfrage, keine Hintergrundläufe beim Anlegen."""
    import main

    async def _kein_ort(lat, lon):
        return ""

    async def _keine_hoehe(*a, **k):
        return (0.0, False)

    monkeypatch.setattr(main, "_reverse_geocode", _kein_ort)
    monkeypatch.setattr(main._elevation_provider, "elevation_difference", _keine_hoehe)


def lege_an(client, lat, lon, name, rolle="host"):
    """Legt einen Ort über den vorhandenen Weg an (wie die Anlege-Maske) und liefert (Antwort, neue ID).
    Angemeldet wird als Host oder als normaler Nutzer (Anlegen darf jeder angemeldete Nutzer)."""
    (als_host if rolle == "host" else als_nutzer)(client)
    r = client.post("/preview-alignment", json={
        "observer_lat": lat, "observer_lon": lon,
        "subject_lat": lat + 0.004, "subject_lon": lon + 0.004,
        "subject_name": name, "subject_height_m": 50.0, "subject_width_m": 20.0,
        "days": 1, "save": True, "category": "SKYLINE",
    })
    assert r.status_code == 200, r.text
    daten = r.json()
    assert daten.get("saved") is True, "Ort wurde nicht gespeichert: %s" % daten
    return daten, daten["location_id"]


# ── Startzustand nach Land/Region ────────────────────────────────────────────

def test_neuer_ort_in_ausgeschalteter_region_startet_pausiert(client, welt_z, ohne_netz):
    """AK-40, AK-42: Region aus -> neuer Ort ist nach dem Speichern pausiert, hat Land und Region aus der Lage
    und keine Chancen im Feed; er bleibt in der Ortsliste sichtbar."""
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    _, neu = lege_an(client, 52.4000, 13.0700, "Neuer Ort Potsdam")
    ort = lies_orte(client)[neu]
    assert ort[FELD_PAUSIERT] is True
    assert (ort[FELD_LAND], ort[FELD_REGION]) == ("Deutschland", "Brandenburg")
    import main
    welt_z.setze_feed(welt_z.termine_fuer(["berlin1"]) + [termin(neu, lat=52.4, lon=13.07)])
    main._load_feed_cache()          # Chancen-Datei einlesen wie beim Start oder nach einem Rechenlauf
    assert neu not in feed_ids(client), "ein pausierter neuer Ort darf keine Chancen im Feed haben"


def test_neuer_ort_in_ausgeschaltetem_land_startet_pausiert(client, welt_z, ohne_netz):
    """AK-40: Auch ein ausgeschaltetes LAND (Region darunter noch an) pausiert den neuen Ort."""
    host_schaltet_land(client, "Italien", False)
    _, neu = lege_an(client, 46.9000, 11.4300, "Neuer Ort Südtirol")
    ort = lies_orte(client)[neu]
    assert ort[FELD_PAUSIERT] is True
    assert (ort[FELD_LAND], ort[FELD_REGION]) == ("Italien", "Trentino-Südtirol")


def test_neuer_ort_in_aktivem_gebiet_ist_sofort_aktiv(client, welt_z, ohne_netz):
    """AK-44: Land und Region an -> neuer Ort ist sofort aktiv, auch wenn eine andere Region aus ist."""
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    _, neu = lege_an(client, 48.1400, 11.5800, "Neuer Ort München")
    ort = lies_orte(client)[neu]
    assert ort[FELD_PAUSIERT] is False
    assert (ort[FELD_LAND], ort[FELD_REGION]) == ("Deutschland", "Bayern")


def test_neuer_ort_bekommt_land_und_region_nach_lage_nicht_nach_namen(client, welt_z, ohne_netz):
    """AK-87, AK-34: ‚Sächsische Schweiz‘ (Name mit ‚Schweiz‘) liegt in Deutschland/Sachsen, nicht in der Schweiz."""
    _, neu = lege_an(client, 50.9611, 14.0728, "Schweiz-Blick Sächsische Schweiz Bastei")
    ort = lies_orte(client)[neu]
    assert (ort[FELD_LAND], ort[FELD_REGION]) == ("Deutschland", "Sachsen")


# ── Der Ort bleibt aus, bis der Host gewählt hat ─────────────────────────────

def test_ort_bleibt_aus_bis_der_host_gewaehlt_hat(client, welt_z, ohne_netz):
    """AK-45, Entscheidung 23: Nichts außer der bewussten Wahl „Jetzt aktivieren“ (Region einschalten) macht den
    Ort aktiv — weder Bearbeiten, noch erneutes Einlesen des Feeds, noch erneutes Laden der Liste.
    (Dass der Hinweis nicht wegklickbar ist, ist Oberfläche -> Browser-Test.)"""
    import main
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    _, neu = lege_an(client, 52.4000, 13.0700, "Neuer Ort bleibt aus")
    als_host(client)
    r = client.patch("/locations/" + neu, json={"name": "Neuer Ort bleibt aus (umbenannt)"})
    assert r.status_code == 200, r.text
    main._load_feed_cache()
    assert lies_orte(client)[neu][FELD_PAUSIERT] is True
    assert lies_gebiete(client)["Deutschland"]["regionen"]["Brandenburg"]["zustand"] == "aus", \
        "‚Ausgeschaltet lassen‘ = keine Aktion: die Region bleibt aus"


# ── „Jetzt aktivieren“ ───────────────────────────────────────────────────────

def test_jetzt_aktivieren_schaltet_die_region_ein_nicht_das_land(client, welt_z, ohne_netz):
    """AK-41, Entscheidung 20: Land Deutschland aus, neuer Ort in Brandenburg (pausiert). Die Rückfrage nennt die
    Ortszahl der Region (hier 3 = 2 vorhandene + der neue). Nach „Jetzt aktivieren“ (Region Brandenburg einschalten)
    laufen alle 3 Orte der Region; Berlin, Bayern und ‚Ohne Region‘ bleiben aus; das Land zeigt „teilweise“."""
    host_schaltet_land(client, "Deutschland", False)
    _, neu = lege_an(client, 52.4000, 13.0700, "Neuer Ort Jetzt aktivieren")
    assert lies_orte(client)[neu][FELD_PAUSIERT] is True
    brandenburg = lies_gebiete(client)["Deutschland"]["regionen"]["Brandenburg"]
    assert brandenburg["gesamt"] == 3, "die Rückfrage braucht die Ortszahl der Region"
    host_schaltet_region(client, "Deutschland", "Brandenburg", True)
    assert aktive_ids(client) >= {welt_z.id("potsdam"), welt_z.id("cottbus"), neu}
    assert {welt_z.id("berlin1"), welt_z.id("berlin2"), welt_z.id("muenchen"), welt_z.id("ohne")} <= pausierte_ids(client)
    assert lies_gebiete(client)["Deutschland"]["zustand"] == ZUSTAND_TEILWEISE


# ── Normale Nutzer ───────────────────────────────────────────────────────────

def test_nutzer_legt_ort_in_pausierter_region_an_ort_bleibt_pausiert_und_nur_host_schaltet(client, welt_z, ohne_netz):
    """AK-63 (Annahme Frage 17): Legt ein normaler Nutzer einen Ort in einer pausierten Region an, bleibt er pausiert
    (der Host muss ihn freischalten). Der Nutzer kann die Region nicht selbst einschalten (403); der Host kann es.
    Der Hinweistext für den Nutzer ist Oberfläche -> Browser-Test."""
    host_schaltet_region(client, "Deutschland", "Brandenburg", False)
    _, neu = lege_an(client, 52.4000, 13.0700, "Ort vom Nutzer", rolle="nutzer")
    assert lies_orte(client)[neu][FELD_PAUSIERT] is True
    r = schalte_region(client, "Deutschland", "Brandenburg", True)
    assert r.status_code == 403, "%s %s" % (r.status_code, r.text)
    assert lies_orte(client)[neu][FELD_PAUSIERT] is True
    abgemeldet(client)
    host_schaltet_region(client, "Deutschland", "Brandenburg", True)
    assert lies_orte(client)[neu][FELD_PAUSIERT] is False
