"""US-141 (Phase A, 2026-10-14) — Land UND Region aus den Koordinaten, Regionslisten, Sortierung.

Ergänzt test_us141_regel.py (das nur das Land prüft, mit der Gebietsliste vor dem Umbau) um alles, was das
Ticket nach dem Umbau auf Land und Region für die Zuordnung verlangt. Reine Logik, ohne Server, ohne Netz.

Geprüft wird (Akzeptanzkriterien AK-28, AK-33, AK-34, AK-35, AK-56, AK-85 bis AK-89, AK-110 bis AK-112,
Entscheidungen 24 bis 30 vom 2026-10-11):
  - Die Region eines Orts kommt aus der Lage, nie aus dem Namen (Sächsische Schweiz, ‚Berlin‘ in Cottbus).
  - Das Vereinigte Königreich hat die vier Regionen England, Nordirland, Schottland, Wales; Cardiff und
    Glasgow sind nicht England; die heutigen 12 Londoner Orte liegen in der Region England.
  - Die Regionslisten sind die geprüften (Deutschland 16, Niederlande 12, Italien 20, Österreich 9,
    Schweiz 26, Norwegen 15, UK 4; Frankreich 13 oder 18 — Korsika-Frage ist offen).
  - Ein Ort an der Grenze zweier Regionen (Glienicker Brücke) löst eine Rückfrage aus statt einer stillen
    Entscheidung (AK-88).
  - Die Reihenfolge der Liste ist alphabetisch nach deutschem Namen, ‚Sonstige‘ am Ende.
  - Gegen die Ortszeit-Regel von US-138 (Rechteck) ändert sich nichts (AK-89, Frage 28).

ANNAHMEN dieser Datei (im Ticket nicht festgelegt, siehe backend/tests/README.md, Abschnitt US-141 Phase A):
  A1  data.regionen.schlage_region_vor(lat, lon, name=None) liefert Land UND Region — als Paar (land, region),
      als Wörterbuch {"land", "region"} oder als Objekt mit .land/.region. Die Form ist frei; nur der Inhalt zählt.
      Ein bloßer Text (alte Form: nur das Gebiet) gilt als ‚Schnittstelle noch nicht umgebaut‘ (rot).
  A2  Kann der Vorschlag unsicher sein, steht das in einem Feld/Element ‚unsicher‘ (bool) derselben Antwort.
  A3  data.regionen.REGIONEN ist ein geordnetes Wörterbuch {Land: [Regionen ...]} in Anzeigereihenfolge.
      ‚Sonstige‘ steht am Ende und hat eine leere Liste. ‚Ohne Region‘ ist KEIN Listeneintrag (Sonderfall).
  A4  Ort ohne Region (Sonstige, ungültig): Region ist None oder ‚‘ oder ‚Ohne Region‘.
Python-3.9-kompatibel. Offline, deterministisch.
"""
from __future__ import annotations

import importlib
import math

import pytest

pytestmark = [pytest.mark.offline, pytest.mark.regression]

MODUL = "data.regionen"
LAND_UK = "Vereinigtes Königreich (UK)"
SONSTIGE = "Sonstige"
LAENDER = ["Deutschland", "Frankreich", "Italien", "Niederlande", "Norwegen", "Österreich", "Schweiz", LAND_UK, SONSTIGE]


def _modul():
    try:
        return importlib.import_module(MODUL)
    except ModuleNotFoundError as e:
        if e.name == MODUL or MODUL.startswith(str(e.name) + "."):
            pytest.fail("Schnittstelle fehlt: Baustein '%s' ist noch nicht gebaut (Ticket US-141, "
                        "Schnittstellen-Entwurf Punkt 3; erwartet rot vor der Umsetzung)" % MODUL)
        raise


def _vorschlag(lat, lon, name=None):
    m = _modul()
    if not hasattr(m, "schlage_region_vor"):
        pytest.fail("Schnittstelle fehlt: schlage_region_vor() existiert nicht in %s" % MODUL)
    return m.schlage_region_vor(lat, lon, name=name)


def _land_region(res):
    """Annahme A1: Paar, Wörterbuch oder Objekt."""
    if isinstance(res, str):
        pytest.fail("Schnittstelle nicht umgebaut: schlage_region_vor() liefert nur ein Gebiet (%r); das Ticket "
                    "verlangt Land UND Region (Schnittstellen-Entwurf Punkt 3)" % (res,))
    if isinstance(res, dict):
        return res.get("land"), res.get("region")
    if isinstance(res, (tuple, list)) and len(res) >= 2:
        return res[0], res[1]
    if hasattr(res, "land") and hasattr(res, "region"):
        return res.land, res.region
    pytest.fail("Antwort von schlage_region_vor() hat keine erkennbare Form (Land, Region): %r" % (res,))


def _unsicher(res):
    """Annahme A2."""
    if isinstance(res, dict) and "unsicher" in res:
        return bool(res["unsicher"])
    if hasattr(res, "unsicher"):
        return bool(res.unsicher)
    if isinstance(res, (tuple, list)) and len(res) >= 3:
        return bool(res[2])
    pytest.fail("Schnittstelle fehlt: die Antwort von schlage_region_vor() sagt nicht, ob der Vorschlag unsicher "
                "ist (Ticket AK-88: im Grenzraum fragt das Menü nach)")


def _ohne_region(region) -> bool:
    return region in (None, "", "Ohne Region")


def _de(s: str) -> str:
    return s.lower().replace("ä", "a").replace("ö", "o").replace("ü", "u").replace("ß", "ss")


# ── Region nach Lage, nicht nach Namen ────────────────────────────────────────

# (Bezeichnung, Breite, Länge, Name, Land, Region) — Koordinaten sind allgemein bekannte Referenzpunkte,
# nicht aus der Ortsliste der App. Regionsnamen sind nur dort festgelegt, wo das Ticket sie nennt.
FAELLE = [
    ("Berlin-Mitte", 52.5200, 13.4050, None, "Deutschland", "Berlin"),                            # AK-81, AK-87
    ("Potsdam", 52.3906, 13.0645, None, "Deutschland", "Brandenburg"),                            # AK-87
    ("Cottbus mit Namen Berlin", 51.7563, 14.3329, "Berlin", "Deutschland", "Brandenburg"),       # Name zählt nie
    ("Sächsische Schweiz", 50.9611, 14.0728, "Sächsische Schweiz – Bastei", "Deutschland", "Sachsen"),  # AK-34
    ("München", 48.1374, 11.5755, None, "Deutschland", "Bayern"),
    ("Zürich mit deutschem Namen", 47.3769, 8.5417, "Deutschland-Blick", "Schweiz", "Zürich"),
    ("Südtirol, Sterzing", 46.8941, 11.4300, "Südtirol", "Italien", "Trentino-Südtirol"),          # keine eigene Region
    ("Venedig", 45.4408, 12.3155, None, "Italien", "Venetien"),
    ("Metz", 49.1193, 6.1757, None, "Frankreich", "Grand Est"),
    ("London", 51.5074, -0.1278, None, LAND_UK, "England"),                                        # AK-110
    ("Cardiff", 51.4816, -3.1791, None, LAND_UK, "Wales"),                                         # AK-111
    ("Glasgow", 55.8642, -4.2518, None, LAND_UK, "Schottland"),                                    # AK-111
    ("Edinburgh", 55.9533, -3.1883, None, LAND_UK, "Schottland"),
    ("Belfast", 54.5973, -5.9301, None, LAND_UK, "Nordirland"),
    ("Mitten im Atlantik", 0.0, -30.0, None, SONSTIGE, None),                                      # AK-35, AK-85
]


@pytest.mark.parametrize("bez,lat,lon,name,land,region", FAELLE, ids=[f[0] for f in FAELLE])
def test_land_und_region_nach_lage_nicht_nach_namen(bez, lat, lon, name, land, region):
    """AK-85/86/87/110/111: Land und Region eines Orts kommen aus seiner Lage. Der Name entscheidet nie
    (‚Sächsische Schweiz‘ = Deutschland/Sachsen, ‚Berlin‘ in Cottbus = Brandenburg, Cardiff/Glasgow sind nicht England)."""
    ist_land, ist_region = _land_region(_vorschlag(lat, lon, name=name))
    assert ist_land == land
    if region is None:
        assert _ohne_region(ist_region), "Orte in ‚Sonstige‘ haben keine Region, geliefert: %r" % (ist_region,)
    else:
        assert ist_region == region


@pytest.mark.parametrize("bez,lat,lon,land,teil", [
    ("Amsterdam", 52.3676, 4.9041, "Niederlande", "holland"),
    ("Rotterdam", 51.9244, 4.4777, "Niederlande", "holland"),
    ("Wien", 48.2082, 16.3738, "Österreich", "wien"),
    ("Innsbruck", 47.2692, 11.4041, "Österreich", "tirol"),
    ("Zermatt", 46.0207, 7.7491, "Schweiz", "wallis"),
    ("Oslo", 59.9139, 10.7522, "Norwegen", "oslo"),
    ("Bergen", 60.3913, 5.3221, "Norwegen", "vestland"),
], ids=lambda v: v if isinstance(v, str) else None)
def test_region_stimmt_in_weiteren_laendern(bez, lat, lon, land, teil):
    """Schreibweisen der Regionsnamen sind im Ticket nur für Deutschland, Italien, UK festgelegt; hier zählt, dass
    es eine Region des richtigen Landes ist und der Name die richtige Gegend trägt."""
    ist_land, ist_region = _land_region(_vorschlag(lat, lon))
    assert ist_land == land
    assert not _ohne_region(ist_region), "%s hat keine Region bekommen" % bez
    assert teil in _de(ist_region), "Region %r passt nicht zu %s" % (ist_region, bez)


def test_amsterdam_und_rotterdam_liegen_in_verschiedenen_provinzen():
    """Nord- und Südholland sind zwei Regionen (Ticket: Nordholland 9, Südholland 2 Orte im Entwicklungsstand)."""
    _, a = _land_region(_vorschlag(52.3676, 4.9041))
    _, r = _land_region(_vorschlag(51.9244, 4.4777))
    assert a != r and not _ohne_region(a) and not _ohne_region(r)


def test_die_zwoelf_heutigen_londoner_orte_liegen_alle_in_der_region_england():
    """AK-110: Alle 12 Londoner Orte stehen im Vereinigten Königreich, Region England. Stellvertreter: ein Raster
    über Groß-London (Breite 51,40 bis 51,60, Länge -0,35 bis 0,15)."""
    for i in range(5):
        for j in range(5):
            lat, lon = 51.40 + 0.05 * i, -0.35 + 0.125 * j
            land, region = _land_region(_vorschlag(lat, lon))
            assert (land, region) == (LAND_UK, "England"), "(%s, %s) liegt in %s/%s" % (lat, lon, land, region)


# ── Ungültig und unsicher ─────────────────────────────────────────────────────

@pytest.mark.parametrize("lat,lon", [(None, None), (float("nan"), 13.4), (999.0, 13.4), (52.5, 1e9)],
                         ids=["nichts", "nan", "breite-ungueltig", "laenge-ungueltig"])
def test_ungueltige_koordinaten_landen_in_sonstige_ohne_absturz(lat, lon):
    """AK-35 (Randfall ungültige Eingaben): keine Region, kein Absturz."""
    land, region = _land_region(_vorschlag(lat, lon))
    assert land == SONSTIGE and _ohne_region(region)


def test_grenzraum_zwischen_berlin_und_brandenburg_fragt_nach():
    """AK-88: An der Glienicker Brücke (Berlin/Potsdam) ist der Vorschlag unsicher — das Menü fragt nach, statt
    still zu entscheiden. Gegenprobe: Berlin-Mitte und Cottbus sind sicher."""
    assert _unsicher(_vorschlag(52.4133, 13.0937)) is True, "Glienicker Brücke müsste als unsicher gelten"
    assert _unsicher(_vorschlag(52.5200, 13.4050)) is False
    assert _unsicher(_vorschlag(51.7563, 14.3329)) is False


def test_dieselbe_lage_gibt_immer_dieselbe_antwort():
    """AK-87: Die Zuordnung ist stabil (keine Zufallsanteile, keine Reihenfolge-Abhängigkeit)."""
    a = _land_region(_vorschlag(52.3906, 13.0645))
    for _ in range(3):
        _vorschlag(48.1374, 11.5755)
    assert _land_region(_vorschlag(52.3906, 13.0645)) == a


# ── Listen ────────────────────────────────────────────────────────────────────

def _regionen():
    m = _modul()
    if not hasattr(m, "REGIONEN"):
        pytest.fail("Schnittstelle fehlt: %s.REGIONEN existiert nicht" % MODUL)
    r = m.REGIONEN
    if not isinstance(r, dict):
        pytest.fail("Annahme A3 nicht erfüllt: REGIONEN muss ein Wörterbuch {Land: [Regionen]} sein, ist %s" % type(r).__name__)
    return r


def test_laender_in_der_vereinbarten_reihenfolge_sonstige_am_ende():
    """AK-33, AK-112, Frage 30: Deutschland, Frankreich, Italien, Niederlande, Norwegen, Österreich, Schweiz,
    Vereinigtes Königreich (UK), Sonstige — alphabetisch nach deutschem Namen, ‚Sonstige‘ am Ende; England ist kein Land."""
    assert list(_regionen()) == LAENDER


DE16 = {"Baden-Württemberg", "Bayern", "Berlin", "Brandenburg", "Bremen", "Hamburg", "Hessen", "Mecklenburg-Vorpommern",
        "Niedersachsen", "Nordrhein-Westfalen", "Rheinland-Pfalz", "Saarland", "Sachsen", "Sachsen-Anhalt",
        "Schleswig-Holstein", "Thüringen"}
AT9 = {"Burgenland", "Kärnten", "Niederösterreich", "Oberösterreich", "Salzburg", "Steiermark", "Tirol", "Vorarlberg", "Wien"}
CH26 = {"Aargau", "Appenzell Ausserrhoden", "Appenzell Innerrhoden", "Basel-Landschaft", "Basel-Stadt", "Bern", "Freiburg",
        "Genf", "Glarus", "Graubünden", "Jura", "Luzern", "Neuenburg", "Nidwalden", "Obwalden", "Schaffhausen", "Schwyz",
        "Solothurn", "St. Gallen", "Tessin", "Thurgau", "Uri", "Waadt", "Wallis", "Zug", "Zürich"}
UK4 = {"England", "Nordirland", "Schottland", "Wales"}


@pytest.mark.parametrize("land,erwartet", [("Deutschland", DE16), ("Österreich", AT9), ("Schweiz", CH26), (LAND_UK, UK4)],
                         ids=["DE-16", "AT-9", "CH-26", "UK-4"])
def test_regionslisten_mit_amtlichen_deutschen_namen(land, erwartet):
    """Auflage (y), Ergebnis der Prüfung 2026-10-14 (Quellen im Ticket): Die Regionsliste ist die offizielle erste
    Gliederungsebene — Deutschland 16 Bundesländer, Österreich 9, Schweiz 26 Kantone, UK 4 Landesteile."""
    assert set(_regionen()[land]) == erwartet
    assert len(_regionen()[land]) == len(erwartet), "doppelte Einträge"


@pytest.mark.parametrize("land,anzahl", [("Niederlande", 12), ("Italien", 20), ("Norwegen", 15)])
def test_regionslisten_anzahl_niederlande_italien_norwegen(land, anzahl):
    """Auflage (y): Niederlande 12 Provinzen, Italien 20 Regionen, Norwegen 15 Provinzen (seit 2024-01-01).
    Die deutschen Schreibweisen sind hier bewusst nicht festgelegt (Vorschläge, kein Quellenbeleg)."""
    assert len(_regionen()[land]) == anzahl


def test_frankreich_hat_dreizehn_festland_regionen_oder_achtzehn_mit_uebersee():
    """Auflage (y), OFFEN: Frankreich zählt 18 Regionen mit Übersee, 13 auf dem Festland einschließlich Korsika
    (ohne Korsika 17 bzw. 12). Welche Zahl gilt, entscheidet Stephan; beides ist hier erlaubt, 17/12 nicht."""
    n = len(_regionen()["Frankreich"])
    assert n in (13, 18), "Frankreich hat %d Regionen — erwartet 13 (Festland mit Korsika) oder 18 (mit Übersee)" % n


def test_sonstige_hat_keine_regionen():
    """Entscheidung 26 / AK-85: ‚Sonstige‘ ist ein Land ohne Regionen (nur der Länder-Schalter)."""
    assert list(_regionen()[SONSTIGE]) == []


@pytest.mark.parametrize("land", [l for l in LAENDER if l != SONSTIGE])
def test_regionen_sind_alphabetisch_nach_deutschem_namen(land):
    """AK-112 / Frage 30: Unter jedem Land stehen die Regionen alphabetisch nach deutscher Sortierung
    (Umlaute wie der Grundbuchstabe)."""
    liste = list(_regionen()[land])
    assert liste == sorted(liste, key=_de), "nicht sortiert: %s" % liste


def test_ohne_region_ist_kein_listeneintrag_sondern_sonderfall():
    """Entscheidung 26 / AK-86: ‚Ohne Region‘ steht je Land am Ende, ist aber keine der amtlichen Regionen
    (Annahme A3: nicht in REGIONEN)."""
    for land, liste in _regionen().items():
        assert "Ohne Region" not in liste


# ── Altbestand und Ortszeit ───────────────────────────────────────────────────

def test_alle_eingebauten_standard_orte_bekommen_land_und_region():
    """AK-56: Nach dem Update hat jeder bisherige Ort ein gültiges Land und, wo es Regionen gibt, eine Region oder
    ‚Ohne Region‘. Es darf nichts abstürzen."""
    from data.locations import LOCATIONS
    assert len(LOCATIONS) > 0
    regionen = _regionen()
    for ort in LOCATIONS:
        land, region = _land_region(_vorschlag(ort.observer_lat, ort.observer_lon, name=ort.name))
        assert land in regionen, "%s: unbekanntes Land %r" % (ort.id, land)
        if land != SONSTIGE and not _ohne_region(region):
            assert region in regionen[land], "%s: Region %r gehört nicht zu %s" % (ort.id, region, land)


def test_schutz_ortszeit_london_haengt_weiter_am_rechteck_nicht_an_der_region():
    """AK-89 / Frage 28 (a), SCHUTZ-TEST (sofort grün erwartet): Ortszeit London und ‚England zuerst‘ bleiben beim
    Rechteck aus US-138, bis die neue Zuordnung ausdrücklich umgestellt wird. London ist England, Berlin nicht."""
    from calculations.ortszeit import is_england
    assert is_england(51.5074, -0.1278) is True
    assert is_england(52.5200, 13.4050) is False
    # Bekanntes, entschiedenes Auseinanderlaufen: das Rechteck zählt Cardiff heute noch zu England (Ticket, Zählung).
    assert is_england(51.4816, -3.1791) is True
