"""US-141 (Entscheidung Stephan, 2026-10-15) — „Frankreich mit Übersee“: 18 Regionen statt 13.

Neue Datei; bestehende Tests wurden nicht angefasst. Geprüft wird:
  - Frankreich hat genau 18 Regionen: die 13 des Festlands (mit Korsika) und die fünf Übersee-Regionen
    Französisch-Guayana, Guadeloupe, La Réunion, Martinique, Mayotte (Quellen im Ticket und in
    outputs/2026-10-11_US-141-umsetzung-kanban/regionslisten_geprueft.md).
  - Ein Ort in Fort-de-France, Saint-Denis (La Réunion), Cayenne, Pointe-à-Pitre, Mamoudzou, Paris und
    Ajaccio bekommt aus seiner Lage das richtige Land und die richtige Region — nie aus dem Namen.
  - Die Grenzdatei (regionen_grenzen.json) und die Regionsliste passen zusammen: zu jeder Region der Liste
    gibt es Grenzen, und zu jeder Grenze eine Region in der Liste (insgesamt 120).
  - Das Menü (gebiet_zustand.gebietsliste) führt alle 18 französischen Regionen, auch ohne Orte darin.
Reine Logik, offline, ohne Server. Python-3.9-kompatibel.
"""
import json
from pathlib import Path

import pytest

from data import gebiet_zustand, regionen

pytestmark = [pytest.mark.offline, pytest.mark.regression]

FESTLAND_13 = {
    "Auvergne-Rhône-Alpes", "Bourgogne-Franche-Comté", "Bretagne", "Centre-Val de Loire", "Grand Est",
    "Hauts-de-France", "Île-de-France", "Korsika", "Normandie", "Nouvelle-Aquitaine", "Okzitanien",
    "Pays de la Loire", "Provence-Alpes-Côte d'Azur",
}
UEBERSEE_5 = {"Französisch-Guayana", "Guadeloupe", "La Réunion", "Martinique", "Mayotte"}

# (Bezeichnung, Breite, Länge, Region, sicher). Koordinaten sind allgemein bekannte Stadtmitten.
# „sicher“ = der Vorschlag darf nicht „unsicher“ sein. Ajaccio und Mamoudzou sind Hafenstädte am Rand der
# vereinfachten Küstenlinie: die Region stimmt, der Vorschlag gilt aber nach der Küstenregel (bis 3 km neben den
# Grenzdaten) als „unsicher“, das Menü würde nachfragen. Das ist gewolltes Verhalten, deshalb dort nicht geprüft.
FAELLE = [
    ("Fort-de-France", 14.6161, -61.0588, "Martinique", True),
    ("Saint-Denis (La Réunion)", -20.8789, 55.4481, "La Réunion", True),
    ("Cayenne", 4.9224, -52.3135, "Französisch-Guayana", True),
    ("Pointe-à-Pitre", 16.2415, -61.5331, "Guadeloupe", True),
    ("Mamoudzou", -12.7806, 45.2279, "Mayotte", False),
    ("Paris", 48.8566, 2.3522, "Île-de-France", True),
    ("Ajaccio", 41.9192, 8.7386, "Korsika", False),
    ("Metz", 49.1193, 6.1757, "Grand Est", True),
]


def test_frankreich_hat_achtzehn_regionen_dreizehn_festland_und_fuenf_uebersee():
    liste = list(regionen.REGIONEN["Frankreich"])
    assert len(liste) == 18, "Frankreich hat %d Regionen, erwartet 18 (mit Übersee)" % len(liste)
    assert len(set(liste)) == 18, "doppelte Einträge: %s" % liste
    assert set(liste) == FESTLAND_13 | UEBERSEE_5


@pytest.mark.parametrize("bez,lat,lon,region,sicher", FAELLE, ids=[f[0] for f in FAELLE])
def test_ort_in_frankreich_bekommt_die_richtige_region(bez, lat, lon, region, sicher):
    z = regionen.schlage_region_vor(lat, lon)
    assert (z.land, z.region) == ("Frankreich", region), "%s: geliefert %s/%s" % (bez, z.land, z.region)
    if sicher:
        assert z.unsicher is False, "%s liegt mitten in der Region, der Vorschlag darf nicht unsicher sein" % bez
    assert regionen.ist_gueltig(z.land, z.region)


def test_der_name_entscheidet_nie_auch_nicht_in_uebersee():
    """Ein Ort namens „Berlin“ in Fort-de-France liegt in Martinique; ein Ort „Cayenne“ in Berlin in Berlin."""
    z = regionen.schlage_region_vor(14.6161, -61.0588, name="Berlin")
    assert (z.land, z.region) == ("Frankreich", "Martinique")
    z = regionen.schlage_region_vor(52.5200, 13.4050, name="Cayenne")
    assert (z.land, z.region) == ("Deutschland", "Berlin")


def test_offenes_meer_in_der_naehe_der_uebersee_gebiete_ist_sonstige():
    """Mitten im Atlantik zwischen Martinique und Barbados und im Indischen Ozean weit weg von Mayotte
    und La Réunion gehört nicht zu Frankreich (kein Ort wird still einer Region zugeschlagen)."""
    assert regionen.schlage_region_vor(14.0, -64.0).land == regionen.SONSTIGE
    assert regionen.schlage_region_vor(-17.0, 52.0).land == regionen.SONSTIGE


def test_festland_hat_sich_durch_uebersee_nicht_veraendert():
    """Schutz: Orte in Deutschland, Italien, UK usw. bekommen dieselbe Region wie vorher."""
    erwartet = [
        (52.5200, 13.4050, "Deutschland", "Berlin"),
        (51.5074, -0.1278, regionen.LAND_UK, "England"),
        (45.4408, 12.3155, "Italien", "Venetien"),
        (47.3769, 8.5417, "Schweiz", "Zürich"),
        (59.9139, 10.7522, "Norwegen", "Oslo"),
    ]
    for lat, lon, land, region in erwartet:
        z = regionen.schlage_region_vor(lat, lon)
        assert (z.land, z.region) == (land, region)


def test_grenzdatei_und_regionsliste_passen_zusammen():
    """Zu jeder Region der Liste gibt es Grenzen (sonst bliebe sie für immer leer), und zu jeder Grenze eine
    Region in der Liste. 16 + 18 + 20 + 12 + 15 + 9 + 26 + 4 = 120."""
    roh = json.loads((Path(regionen.__file__).with_name("regionen_grenzen.json")).read_text(encoding="utf-8"))
    aus_datei = {(g["land"], g["region"]) for g in roh["gebiete"]}
    aus_liste = {(l, r) for l, rs in regionen.REGIONEN.items() for r in rs}
    assert len(aus_liste) == 120
    assert aus_datei == aus_liste, "nur in der Datei: %s; nur in der Liste: %s" % (
        sorted(aus_datei - aus_liste), sorted(aus_liste - aus_datei))
    for g in roh["gebiete"]:
        assert g["polygone"], "%s/%s hat keine Grenzen" % (g["land"], g["region"])


def test_menue_fuehrt_alle_achtzehn_regionen_auch_ohne_orte():
    z = gebiet_zustand.gebietsliste([], {"laender": {}, "regionen": {}})
    frankreich = [l for l in z["laender"] if l["name"] == "Frankreich"][0]
    namen = [r["name"] for r in frankreich["regionen"]]
    assert set(namen) == FESTLAND_13 | UEBERSEE_5
    assert len(namen) == 18
    assert all(r["gesamt"] == 0 for r in frankreich["regionen"])
