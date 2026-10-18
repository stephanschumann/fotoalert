"""US-141 (Weg-Gate: Option A, 2026-10-11) — die zentrale Regel ohne Oberfläche.

Diese Tests prüfen nur Verhalten, das sich OHNE Oberfläche und ohne Server über zwei kleine,
reine Bausteine festlegen lässt (Schnittstelle = VORSCHLAG im Ticket, Freigabe durch Stephan
beim Ready-for-Dev-Gate; die Namen stehen in den beiden Konstanten unten und sind mit einer
Zeile änderbar):
  - Länderliste und Land-Vorschlag aus Koordinaten (feste Liste: Deutschland, Frankreich, Italien,
    Niederlande, Norwegen, Österreich, Schweiz, Vereinigtes Königreich (UK), Sonstige; England ist
    eine Region in UK, kein Land) — AK-33, AK-34, AK-35, AK-112. Die Regionen je Land prüft
    test_us141_zuordnung.py. Der Name eines Orts darf NIE entscheiden (Namensfalle „Sächsische Schweiz“).
  - Aktiv-Regel „Darf dieser Ort berechnet werden?“ — gelöscht = nein; sonst nur, wenn sein Land
    UND seine Region an sind; fehlt die Angabe = aktiv (AK-56, AK-79); Ortsdaten laufen auch für
    pausierte Orte, nie für gelöschte (AK-46 bis AK-49, AK-G8); neuer Ort startet pausiert, wenn
    sein Land ODER seine Region aus ist (AK-40, AK-44).

Bewusst NICHT getestet: Verhalten der Ortsliste mit Mindest-Score (Annahme l), alles, was
Oberfläche, Server-Läufe oder Nachladen braucht. (Ein Schalter je Ort und das Zusammenspiel von
Regions- und Ortsschalter, Frage 11, entfallen seit dem Umbau auf Land und Region.)

Rot-Grund heute: Die beiden Bausteine existieren noch nicht. Der Test meldet das ausdrücklich
(„Schnittstelle fehlt“) und schlägt NICHT mit einem rohen Importfehler fehl. Offline, reine Logik.
"""
import importlib

import pytest

pytestmark = [pytest.mark.offline, pytest.mark.regression]

MODUL_REGIONEN = "data.regionen"      # Vorschlag: REGIONEN, schlage_region_vor(lat, lon, name=None)
MODUL_AKTIV = "data.aktiv_regel"      # Vorschlag: ist_geloescht, ist_aktiv, ids_fuer_berechnung,
                                      #   ids_fuer_ortsdaten, startzustand_pausiert


def _lade(modulname: str):
    try:
        return importlib.import_module(modulname)
    except ModuleNotFoundError as e:
        if e.name == modulname or modulname.startswith(str(e.name) + "."):
            pytest.fail(f"Schnittstelle fehlt: Baustein '{modulname}' ist noch nicht gebaut "
                        f"(Vorschlag im Ticket US-141, erwartet rot vor der Umsetzung)")
        raise


# ── Gebiet aus Koordinaten ────────────────────────────────────────────────────

ERWARTETE_LISTE = ["Deutschland", "Frankreich", "Italien", "Niederlande", "Norwegen",
                   "Österreich", "Schweiz", "Vereinigtes Königreich (UK)", "Sonstige"]


def test_laenderliste_ist_genau_die_feste_liste():
    """AK-33, AK-112: genau diese neun Länder in dieser Reihenfolge; England ist kein Land mehr
    (Region unter dem Vereinigten Königreich); die Regionen je Land prüft test_us141_zuordnung.py."""
    r = _lade(MODUL_REGIONEN)
    assert list(r.REGIONEN) == ERWARTETE_LISTE


# (Koordinaten sind allgemein bekannte Referenzpunkte, nicht aus der Ortsliste der App)
FAELLE = [
    ("Berlin", 52.5200, 13.4050, None, "Deutschland"),
    ("Bastei, Sächsische Schweiz", 50.9611, 14.0728, "Sächsische Schweiz – Bastei", "Deutschland"),  # AK-34
    ("Zürich mit deutschem Namen", 47.3769, 8.5417, "Deutschland-Blick", "Schweiz"),                 # Name zählt nie
    ("London", 51.5074, -0.1278, None, "Vereinigtes Königreich (UK)"),   # Region „England“ prüft test_us141_zuordnung.py
    ("Metz", 49.1193, 6.1757, None, "Frankreich"),
    ("Chamonix", 45.9237, 6.8694, None, "Frankreich"),
    ("Amsterdam", 52.3676, 4.9041, None, "Niederlande"),
    ("Oslo", 59.9139, 10.7522, None, "Norwegen"),
    ("Innsbruck", 47.2692, 11.4041, None, "Österreich"),
    ("Wien", 48.2082, 16.3738, None, "Österreich"),
    ("Zermatt", 46.0207, 7.7491, None, "Schweiz"),
    ("Südtirol, Sterzing", 46.8941, 11.4300, "Südtirol", "Italien"),   # nahe Österreich, trotzdem Italien
    ("Südtirol, Seiser Alm", 46.5417, 11.6167, None, "Italien"),
    ("Venetien, Venedig", 45.4408, 12.3155, None, "Italien"),
    ("Venetien, Cortina", 46.5405, 12.1357, None, "Italien"),
    ("Mitten im Atlantik", 0.0, -30.0, None, "Sonstige"),               # AK-35: unklar -> Sonstige
    ("Reykjavik", 64.1466, -21.9426, None, "Sonstige"),
]


@pytest.mark.parametrize("bez,lat,lon,name,erwartet", FAELLE, ids=[f[0] for f in FAELLE])
def test_gebiet_nach_lage_nicht_nach_namen(bez, lat, lon, name, erwartet):
    r = _lade(MODUL_REGIONEN)
    assert r.schlage_region_vor(lat, lon, name=name) == erwartet


@pytest.mark.parametrize("lat,lon", [(None, None), (float("nan"), 10.0), ("x", 5)])
def test_ungueltige_koordinaten_landen_in_sonstige(lat, lon):
    """Ungültige Eingabe stürzt nicht ab und rät nicht: Sonstige."""
    r = _lade(MODUL_REGIONEN)
    assert r.schlage_region_vor(lat, lon) == "Sonstige"


# ── Aktiv-Regel ───────────────────────────────────────────────────────────────

def test_aktiv_nur_wenn_nicht_geloescht_und_land_und_region_an():
    """AK-79: Es gibt kein Merkmal „pausiert“ je Ort. Aktiv = nicht gelöscht UND Land an UND Region an."""
    a = _lade(MODUL_AKTIV)
    z = {"laender": {"Deutschland": True, "Italien": False},
         "regionen": {("Deutschland", "Berlin"): True, ("Deutschland", "Brandenburg"): False}}
    assert a.ist_aktiv({"land": "Deutschland", "region": "Berlin"}, z) is True
    assert a.ist_aktiv({"land": "Deutschland", "region": "Brandenburg"}, z) is False   # Region aus
    assert a.ist_aktiv({"land": "Italien", "region": "Venetien"}, z) is False           # Land aus
    assert a.ist_aktiv({"land": "Deutschland", "region": "Berlin", "deleted": True}, z) is False


def test_fehlende_angabe_heisst_aktiv_abwaertskompatibel():
    """AK-56: Orte aus der Zeit vor dem Update haben weder Land noch Region und bleiben aktiv;
    ein Land oder eine Region ohne gespeicherten Zustand gilt als „an“; ein fehlender Ort stürzt nicht ab."""
    a = _lade(MODUL_AKTIV)
    assert a.ist_aktiv({"altes_feld": 1}, {}) is True
    assert a.ist_aktiv({"land": "Deutschland", "region": "Berlin"}, {}) is True      # kein Zustand gespeichert = an
    assert a.ist_aktiv(None, {}) is True


def test_berechnung_nimmt_nur_aktive_ortsdaten_nehmen_auch_pausierte():
    """Gruppe B (Feed, Wetter, Kalender, Entdecken) = aktive Orte; Gruppe A (Höhe, Sichtachse,
    Qualitätsprüfung) = alle nicht gelöschten, auch pausierte; gelöschte nie (AK-G8).
    „Pausiert“ ergibt sich aus Land und Region; Eingabe sind die Orte (mit Land, Region, gelöscht)
    und der Zustand von Land und Region."""
    a = _lade(MODUL_AKTIV)
    orte = [{"id": "a", "land": "Deutschland", "region": "Berlin"},
            {"id": "b", "land": "Deutschland", "region": "Brandenburg"},
            {"id": "c", "land": "Deutschland", "region": "Berlin", "deleted": True},
            {"id": "d", "land": "Italien", "region": "Venetien", "deleted": True},
            {"id": "e", "land": "Deutschland", "region": "Berlin"}]
    z = {"laender": {}, "regionen": {("Deutschland", "Brandenburg"): False}}
    assert [o["id"] for o in a.ids_fuer_berechnung(orte, z)] == ["a", "e"]
    assert [o["id"] for o in a.ids_fuer_ortsdaten(orte, z)] == ["a", "b", "e"]


def test_reihenfolge_und_unbekannte_ids_bleiben_stabil():
    """Die Reihenfolge bleibt erhalten; ein Zustand für ein Land oder eine Region, zu der kein Ort
    gehört, ändert nichts."""
    a = _lade(MODUL_AKTIV)
    orte = [{"id": "z", "land": "Deutschland", "region": "Berlin"},
            {"id": "y", "land": "Deutschland", "region": "Berlin"},
            {"id": "x", "land": "Deutschland", "region": "Berlin"}]
    assert [o["id"] for o in a.ids_fuer_berechnung(orte, {"laender": {"Norwegen": False}, "regionen": {}})] == ["z", "y", "x"]


def test_alles_pausiert_ergibt_leere_berechnung_aber_volle_ortsdaten():
    """AK-13, AK-82: Sind alle Länder aus (und damit alle Regionen), wird nichts berechnet; die
    Ortsdaten laufen für alle weiter. (Dass ein Land „aus“ zeigt, wenn alle seine Regionen einzeln
    aus sind, prüfen die Schalter-Tests, nicht diese Datei.)"""
    a = _lade(MODUL_AKTIV)
    orte2 = [{"id": "a", "land": "Deutschland", "region": "Berlin"},
             {"id": "b", "land": "Deutschland", "region": "Brandenburg"}]
    z = {"laender": {"Deutschland": False}, "regionen": {}}
    assert list(a.ids_fuer_berechnung(orte2, z)) == []
    assert [o["id"] for o in a.ids_fuer_ortsdaten(orte2, z)] == ["a", "b"]


def test_neuer_ort_uebernimmt_zustand_seines_gebiets():
    """AK-40 und AK-44: Ein neuer Ort startet pausiert, wenn sein Land ODER seine Region aus ist;
    er startet aktiv, wenn beides an ist."""
    a = _lade(MODUL_AKTIV)
    assert a.startzustand_pausiert(land_pausiert=True,  region_pausiert=False) is True
    assert a.startzustand_pausiert(land_pausiert=False, region_pausiert=True)  is True
    assert a.startzustand_pausiert(land_pausiert=True,  region_pausiert=True)  is True
    assert a.startzustand_pausiert(land_pausiert=False, region_pausiert=False) is False
