"""
Kuratierte Foto-Locations für Berlin und Brandenburg.

Jede Location enthält:
- GPS-Koordinaten des optimalen Standpunkts
- GPS des Motivs (Gebäude/Landmark)
- Gebäudehöhe / Motivgröße
- Ideale Aufnahmerichtungen (Azimut)
- Beste Tageszeiten
- Brennweiten-Empfehlung
- Besonderheiten
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Optional


class LocationCategory(str, Enum):
    SCHLOSS = "Schloss & Historisch"
    SKYLINE = "Skyline & Architektur"
    NATUR = "Natur & Landschaft"
    WASSER = "Wasser & Spiegelung"
    AUSSICHT = "Aussichtspunkt"
    INDUSTRIE = "Industrie & Urban"
    MILCHSTRASSE = "Milchstraße & Astro"


class BestTime(str, Enum):
    GOLDEN_MORNING = "Goldene Stunde Morgen"
    GOLDEN_EVENING = "Goldene Stunde Abend"
    BLUE_HOUR = "Blaue Stunde"
    NIGHT = "Nacht / Astro"
    MIDDAY = "Mittagslicht"
    ANY = "Jederzeit"
    WINTER = "Winterlicht (tiefer Sonnenstand)"


@dataclass
class PhotoLocation:
    id: str
    name: str
    description: str
    category: LocationCategory

    # Standort des Fotografen
    observer_lat: float
    observer_lon: float

    # Motiv (Gebäude, Landmark, Natur)
    subject_lat: float
    subject_lon: float
    subject_name: str
    subject_height_m: Optional[float] = None    # Bauwerkshöhe (absolut, z.B. laut Wikipedia)
    subject_width_m: Optional[float] = None     # Breite (für Brennweite)
    elevation_difference_m: float = 0.0         # Niveauunterschied: Motiv-Basis minus Fotograf-Standort
                                                 # positiv = Motiv steht höher (z.B. Hügel)
                                                 # negativ = Fotograf steht höher
    observer_floor_height_m: float = 0.0        # US-62: vertikaler Offset wenn Fotograf nicht auf Bodenniveau
                                                 # z.B. 60.0 für Dach eines 6-Geschossers

    # Entfernung Fotograf → Motiv (m)
    distance_m: Optional[float] = None

    # Optimale Bedingungen
    best_times: list[BestTime] = field(default_factory=list)
    ideal_azimuth_range: Optional[tuple[float, float]] = None  # Sonne/Mond in diesem Bereich ideal
    focal_length_suggestions: list[int] = field(default_factory=list)  # mm

    # Besonderheiten / Alignments
    special_notes: str = ""
    solar_alignment_note: str = ""   # z.B. "Sonnenaufgang über dem Turm im April/August"
    lunar_alignment_note: str = ""

    # Zugang
    access_note: str = ""
    locationscout_url: str = ""

    # Schwierigkeit
    difficulty: int = 2  # 1=einfach, 3=schwer

    # US-120: Beispielbild (Dateiname im Bild-Verzeichnis, kein Base64/Pfad-Traversal)
    image_filename: Optional[str] = None


# ---------------------------------------------------------------------------
# BERLIN
# ---------------------------------------------------------------------------

LOCATIONS: list[PhotoLocation] = [

    # --- MITTE ---
    PhotoLocation(
        id="berliner_dom_spree",
        name="Berliner Dom vom Spreeufer",
        description="Blick vom nördlichen Spreeufer auf den Dom – Sichtachse von Nordwesten über die Spree. Besonders bei blauer Stunde mit beleuchtetem Dom und Spiegelung.",
        category=LocationCategory.SKYLINE,
        observer_lat=52.52161, observer_lon=13.39894,
        subject_lat=52.5190, subject_lon=13.4011,
        subject_name="Berliner Dom",
        subject_height_m=98, subject_width_m=73,  # 98m laut Wikipedia (Hauptkuppel inkl. Kreuz)
        distance_m=325,
        best_times=[BestTime.BLUE_HOUR, BestTime.GOLDEN_MORNING],
        ideal_azimuth_range=(133, 173),
        focal_length_suggestions=[50, 85, 135],
        solar_alignment_note="Sonnenaufgang hinter dem Dom: ca. November bis Januar (Azimut ~153°). Bestes Fenster 0–30 Min. nach Sonnenaufgang.",
        lunar_alignment_note="Mondaufgang hinter dem Dom: Vollmond Oktober bis Februar (Azimut ~140–160°), ca. 1–2 Std. nach Mondaufgang.",
        access_note="Nördliches Spreeufer / Lustgartenbereich, öffentlich",
        locationscout_url="https://www.locationscout.net/germany/22388-berliner-dom/50001",
        special_notes="Spiegelung nur bei ruhigem Wasser (Windstille). Beleuchtung ab Dämmerung.",
    ),

    PhotoLocation(
        id="tv_turm_alexanderplatz",
        name="Fernsehturm – Straßenperspektive",
        description="Der Fernsehturm überragt alles – perfekt für 'Sonne/Mond hinter der Kugel'-Shots.",
        category=LocationCategory.SKYLINE,
        observer_lat=52.5206, observer_lon=13.4095,
        subject_lat=52.5209, subject_lon=13.4094,
        subject_name="Berliner Fernsehturm",
        subject_height_m=368,
        distance_m=200,
        best_times=[BestTime.GOLDEN_MORNING, BestTime.GOLDEN_EVENING, BestTime.BLUE_HOUR],
        ideal_azimuth_range=(60, 120),
        focal_length_suggestions=[200, 300, 400, 600],
        solar_alignment_note="Sonnenaufgang hinter dem Turm: ca. März 21 und September 22 (Ost, Azimut ~95°). Sehr enge Toleranz – exaktes Datum wichtig!",
        lunar_alignment_note="Vollmond über dem Turm: bei Mondaufgang im Osten, ca. April–September",
        access_note="Alexanderplatz, öffentlich. Beste Position: Karl-Liebknecht-Straße südlich des Turms",
        locationscout_url="https://locationscout.net/germany/7-berlin-tv-tower",
        special_notes="Für Mondshots: Vollmond + Mondaufgang im Osten, Beobachter ~500m westlich des Turms = 200mm+",
        difficulty=3,
    ),

    PhotoLocation(
        id="brandenburger_tor_tiergarten",
        name="Brandenburger Tor – Tiergartenseite",
        description="Das Tor mit langer Straße des 17. Juni – Sunrise-Alignment möglich.",
        category=LocationCategory.SKYLINE,
        observer_lat=52.5163, observer_lon=13.3777,
        subject_lat=52.5163, subject_lon=13.3777,
        subject_name="Brandenburger Tor",
        subject_height_m=26, subject_width_m=65,
        distance_m=500,
        best_times=[BestTime.GOLDEN_MORNING, BestTime.BLUE_HOUR],
        ideal_azimuth_range=(80, 100),
        focal_length_suggestions=[70, 135, 200],
        solar_alignment_note="Sonnenaufgang durch das Tor Richtung Tiergarten: Ende März / Mitte September (Azimut ~90°)",
        access_note="17. Juni Straße, öffentlich, Stativ-Erlaubnis morgens meist ok",
        locationscout_url="https://locationscout.net/germany/6-berlin-gate-of-brandenburger",
        difficulty=1,
    ),

    # --- TREPTOW / KÖPENICK ---
    PhotoLocation(
        id="treptower_park_spree",
        name="Treptower Park – Spreepanorama",
        description="Breites Fluss-Panorama mit Brücken und Skyline in der Ferne.",
        category=LocationCategory.WASSER,
        observer_lat=52.4925, observer_lon=13.4696,
        subject_lat=52.4920, subject_lon=13.4700,
        subject_name="Spree / Brücke Treptow",
        distance_m=100,
        best_times=[BestTime.GOLDEN_MORNING, BestTime.GOLDEN_EVENING],
        focal_length_suggestions=[24, 35, 70],
        access_note="Treptower Park, frei zugänglich",
        difficulty=1,
    ),

    # --- PANKOW / PRENZLAUER BERG ---
    PhotoLocation(
        id="volkspark_friedrichshain_wasserturm",
        name="Volkspark Friedrichshain – Bunkerberg",
        description="Erhöhter Punkt mit Blick über die Stadt, nahe Fernsehturm-Sichtachse.",
        category=LocationCategory.AUSSICHT,
        observer_lat=52.5271, observer_lon=13.4360,
        subject_lat=52.5271, subject_lon=13.4360,
        subject_name="Berlin-Panorama Richtung Mitte",
        distance_m=0,
        best_times=[BestTime.GOLDEN_EVENING, BestTime.BLUE_HOUR],
        focal_length_suggestions=[35, 70, 135],
        access_note="Park frei zugänglich, Bunkerberg auch nachts oft offen",
        difficulty=1,
    ),

    # --- MÜGGELTURM ---
    PhotoLocation(
        id="muggelturm",
        name="Müggelsee & Müggelturm",
        description="Höchster natürlicher Aussichtspunkt Berlins, Blick über Müggelsee und Wälder.",
        category=LocationCategory.AUSSICHT,
        observer_lat=52.4052, observer_lon=13.6594,
        subject_lat=52.4052, subject_lon=13.6594,
        subject_name="Müggelsee & Berliner Umland",
        subject_height_m=115,
        distance_m=0,
        best_times=[BestTime.GOLDEN_MORNING, BestTime.GOLDEN_EVENING, BestTime.MILCHSTRASSE if False else BestTime.ANY],
        focal_length_suggestions=[24, 35, 70],
        solar_alignment_note="Sonnenaufgang über dem Müggelsee im Sommer – leuchtende Wasserfläche",
        access_note="Wanderweg zum Turm (geschlossen, Außengelände frei)",
        difficulty=2,
    ),

    # --- WANNSEE ---
    PhotoLocation(
        id="wannsee_strandbad",
        name="Wannsee – Großer Wannsee Ufer",
        description="Weiter Seespiegel, Segelboote, Abend-Panorama in warmes Licht getaucht.",
        category=LocationCategory.WASSER,
        observer_lat=52.4271, observer_lon=13.1724,
        subject_lat=52.4271, subject_lon=13.1724,
        subject_name="Großer Wannsee",
        distance_m=0,
        best_times=[BestTime.GOLDEN_EVENING, BestTime.GOLDEN_MORNING],
        ideal_azimuth_range=(240, 300),
        focal_length_suggestions=[24, 35, 70, 135],
        access_note="Öffentliches Ufer südlich des Strandbads",
        difficulty=1,
    ),

    # ---------------------------------------------------------------------------
    # POTSDAM
    # ---------------------------------------------------------------------------

    PhotoLocation(
        id="schloss_babelsberg_pfingstberg",
        name="Schloss Babelsberg → Pfingstberg Belvedere",
        description="Ikone: Von Schloss Babelsberg die Sichtachse zum Belvedere auf dem Pfingstberg. "
                    "Besonders bei Sonnenfinsternissen, Vollmond-Aufgang oder goldener Stunde spektakulär. "
                    "Das Beispiel-Szenario: 12. Aug, 20:09 Uhr, 135mm, partielle Sonnenfinsternis.",
        category=LocationCategory.SCHLOSS,
        observer_lat=52.3975, observer_lon=13.0976,
        subject_lat=52.4158, subject_lon=13.0688,
        subject_name="Belvedere auf dem Pfingstberg",
        subject_height_m=15,  # Turmhöhe Belvedere ~15m
        subject_width_m=40,
        elevation_difference_m=50,  # Pfingstberg ~90m NN, Babelsberg-Standort ~40m NN → Δ+50m
        distance_m=3200,
        best_times=[BestTime.GOLDEN_EVENING, BestTime.BLUE_HOUR],
        ideal_azimuth_range=(310, 340),
        focal_length_suggestions=[135, 200, 300, 400],
        solar_alignment_note="Sonnenuntergang nahe Belvedere: ca. Mitte November, Ende Januar (Azimut ~230°). "
                              "Partielle Sonnenfinsternis 12. Aug. 2026 um ~20:09 mit Finsternis über Pfingstberg.",
        lunar_alignment_note="Mondaufgang über Pfingstberg: bei östlichem Mondaufgang im Sommer (Vollmond April–Juli)",
        access_note="Park Babelsberg, Eingang Waldmüllerstraße. Freie Sicht vom Terrassenweg.",
        locationscout_url="https://locationscout.net/germany/potsdam",
        special_notes="Sichtachse ~NNW (ca. 320°). Distanz ~3,2 km → 135mm ideal für Belvedere im Vordergrund mit Himmelsereignis.",
        difficulty=2,
    ),

    PhotoLocation(
        id="schloss_sanssouci",
        name="Schloss Sanssouci – Weinbergterrassen",
        description="Klassische Frontalansicht auf das Rokoko-Schloss mit Weinbergterrassen. "
                    "Goldene Stunde lässt die Fassade leuchten.",
        category=LocationCategory.SCHLOSS,
        observer_lat=52.4040, observer_lon=13.0388,
        subject_lat=52.4047, subject_lon=13.0388,
        subject_name="Schloss Sanssouci",
        subject_height_m=12, subject_width_m=120,
        distance_m=200,
        best_times=[BestTime.GOLDEN_MORNING, BestTime.GOLDEN_EVENING],
        ideal_azimuth_range=(60, 110),
        focal_length_suggestions=[24, 35, 50, 70],
        solar_alignment_note="Sonnenaufgang hinter dem Schloss im Sommer (Ostseite), Licht fällt auf Terrassen",
        access_note="Park Sanssouci, kostenlos, Stativ erlaubt (keine kommerziellen Aufnahmen ohne Genehmigung)",
        locationscout_url="https://locationscout.net/germany/5-palace-sanssouci",
        difficulty=1,
    ),

    PhotoLocation(
        id="glienicker_brucke",
        name="Glienicker Brücke",
        description="Die legendäre Agentenbrücke zwischen Berlin und Potsdam. "
                    "Abendlicht über der Havel, Spiegelungen.",
        category=LocationCategory.SKYLINE,
        observer_lat=52.4152, observer_lon=13.1168,
        subject_lat=52.4152, subject_lon=13.1168,
        subject_name="Glienicker Brücke & Havel",
        subject_width_m=130,
        distance_m=150,
        best_times=[BestTime.GOLDEN_EVENING, BestTime.BLUE_HOUR],
        ideal_azimuth_range=(200, 260),
        focal_length_suggestions=[35, 70, 135],
        solar_alignment_note="Sonnenuntergang über der Havel Richtung Westen: Mai–Juli (Azimut ~280°)",
        access_note="Öffentlich, Uferweg auf beiden Seiten",
        difficulty=1,
    ),

    PhotoLocation(
        id="telegrafenberg_potsdam",
        name="Telegrafenberg – Einsteinturm",
        description="Art-Deco Einsteinturm auf dem Telegrafenberg, "
                    "umgeben von Kiefernwald. Einzigartiges Architekturmotiv.",
        category=LocationCategory.INDUSTRIE,
        observer_lat=52.3812, observer_lon=13.0653,
        subject_lat=52.3818, subject_lon=13.0644,
        subject_name="Einsteinturm",
        subject_height_m=20, subject_width_m=8,
        distance_m=80,
        best_times=[BestTime.GOLDEN_MORNING, BestTime.GOLDEN_EVENING, BestTime.WINTER],
        ideal_azimuth_range=(90, 180),
        focal_length_suggestions=[35, 50, 85],
        solar_alignment_note="Tiefer Wintersonnenstand wirft dramatische Schatten auf die expressionistische Fassade",
        access_note="Besichtigung nach Voranmeldung beim Alfred-Wegener-Institut, Außengelände teilweise frei",
        difficulty=3,
    ),

    PhotoLocation(
        id="nikolaisee_potsdam",
        name="Nikolaisee – Baumspiegelung",
        description="Kleiner See im Norden Potsdams, ruhiges Wasser, Kiefern-Silhouetten beim Sonnenuntergang.",
        category=LocationCategory.WASSER,
        observer_lat=52.4389, observer_lon=13.0545,
        subject_lat=52.4389, subject_lon=13.0545,
        subject_name="Nikolaisee & Waldsilhouette",
        distance_m=0,
        best_times=[BestTime.GOLDEN_EVENING, BestTime.GOLDEN_MORNING],
        focal_length_suggestions=[24, 35, 70],
        access_note="Frei zugängliches Naturschutzgebiet, Parkplatz Nikolaisee",
        difficulty=1,
    ),

    # ---------------------------------------------------------------------------
    # BRANDENBURG (Umland)
    # ---------------------------------------------------------------------------

    PhotoLocation(
        id="schweriner_see_havelland",
        name="Havelland – Storchnest & Felder",
        description="Typisch Brandenburg: Weite Felder, Windmühlen, Störche. "
                    "Goldene Stunde mit langen Schatten über den Äckern.",
        category=LocationCategory.NATUR,
        observer_lat=52.8027, observer_lon=12.5847,
        subject_lat=52.8027, subject_lon=12.5847,
        subject_name="Havelland Weite & Windmühlen",
        distance_m=0,
        best_times=[BestTime.GOLDEN_MORNING, BestTime.GOLDEN_EVENING, BestTime.WINTER],
        focal_length_suggestions=[24, 35, 70, 200],
        special_notes="Störche März–August. Rapsblüte April/Mai – gelbe Flächen explodieren im Gegenlicht.",
        access_note="Feldwege bei Rhinow, frei befahrbar",
        difficulty=1,
    ),

    PhotoLocation(
        id="spreewald_kanal",
        name="Spreewald – Kanal-Perspektive Lübbenau",
        description="Das Venedig Brandenburgs: verschlungene Kanäle, Erlen-Alleen, "
                    "Nebel am Morgen. Unvergleichliche Atmosphäre.",
        category=LocationCategory.NATUR,
        observer_lat=51.8671, observer_lon=13.9503,
        subject_lat=51.8671, subject_lon=13.9503,
        subject_name="Spreewald-Kanal",
        distance_m=0,
        best_times=[BestTime.GOLDEN_MORNING, BestTime.BLUE_HOUR],
        focal_length_suggestions=[24, 35, 85],
        special_notes="Morgennebel Oktober/November. Boot für beste Perspektiven (Kahnverleih ab 8 Uhr).",
        access_note="Lübbenau Zentrum, Bootsverleih oder Uferpfade",
        difficulty=2,
    ),

    PhotoLocation(
        id="stechlin_see",
        name="Stechlinsee – Dunkelster See Brandenburgs",
        description="Einer der klarsten Seen Deutschlands, extrem dunkle Nächte "
                    "(kein Lichtverschmutzung), ideal für Milchstraße.",
        category=LocationCategory.MILCHSTRASSE,
        observer_lat=53.1427, observer_lon=13.0269,
        subject_lat=53.1427, subject_lon=13.0269,
        subject_name="Stechlinsee & Milchstraße",
        distance_m=0,
        best_times=[BestTime.NIGHT],
        ideal_azimuth_range=(150, 220),  # Galaktisches Zentrum im Süden
        focal_length_suggestions=[14, 20, 24],
        special_notes="Bortle-Klasse ~3–4 (sehr dunkel). Galaktisches Zentrum April–September sichtbar. "
                      "Neumond empfohlen. Spiegelung im See für Komposit.",
        access_note="Naturschutzgebiet, Uferpfad nördlich des Sees, kein Stativ im Wasser",
        locationscout_url="",
        difficulty=3,
    ),

    PhotoLocation(
        id="schorfheide_herbst",
        name="Schorfheide – Herbstwald Uckermark",
        description="Buchenwald in Herbstfarben, Morgennebel zwischen Stämmen, "
                    "Hirsche in der Dämmerung.",
        category=LocationCategory.NATUR,
        observer_lat=52.9827, observer_lon=13.5764,
        subject_lat=52.9827, subject_lon=13.5764,
        subject_name="Schorfheide Buchenwald",
        distance_m=0,
        best_times=[BestTime.GOLDEN_MORNING, BestTime.WINTER],
        focal_length_suggestions=[85, 135, 200, 300],
        special_notes="Herbstblätter Oktober. Brunftzeit Rotwild September. Nebel bei Temperaturinversion.",
        access_note="Wanderparkplätze Schorfheide, Biosphärenreservat",
        difficulty=2,
    ),

    PhotoLocation(
        id="rheinsberg_see",
        name="Schloss Rheinsberg – Schlosssee",
        description="Barockschloss am See, perfekte Spiegelung, kein Massentourismus.",
        category=LocationCategory.SCHLOSS,
        observer_lat=53.1024, observer_lon=12.8913,
        subject_lat=53.1035, subject_lon=12.8920,
        subject_name="Schloss Rheinsberg",
        subject_height_m=20, subject_width_m=60,
        distance_m=300,
        best_times=[BestTime.GOLDEN_MORNING, BestTime.BLUE_HOUR],
        ideal_azimuth_range=(60, 110),
        focal_length_suggestions=[35, 70, 135],
        solar_alignment_note="Sonnenaufgang hinter dem Schloss im Sommer (Ostseite, Azimut ~80°)",
        access_note="Seeseite frei zugänglich, Bootssteg für Low-Angle",
        difficulty=1,
    ),

    PhotoLocation(
        id="elbtalaue_wittenberge",
        name="Elbtalaue Wittenberge – Gänsezug",
        description="Tausende von Kranichen und Gänsen im Herbst. Dramatische V-Formationen "
                    "vor Abendhimmel oder Vollmond.",
        category=LocationCategory.NATUR,
        observer_lat=53.0025, observer_lon=11.7381,
        subject_lat=53.0025, subject_lon=11.7381,
        subject_name="Kranichzug & Elbtalaue",
        distance_m=0,
        best_times=[BestTime.GOLDEN_EVENING, BestTime.GOLDEN_MORNING],
        focal_length_suggestions=[300, 400, 500, 600],
        special_notes="Kranichzug: Oktober–November, vor allem bei Frostnächten. "
                      "Graugänse das ganze Jahr. Vollmond erhellt Zugformationen.",
        access_note="Deichkrone bei Wittenberge, frei zugänglich",
        difficulty=2,
    ),

    PhotoLocation(
        id="rügen_kreidefelssen_jasmund",
        name="Rügen – Königsstuhl (Grenzgebiet)",
        description="Weiße Kreidefelsen über türkisblauem Wasser – "
                    "einer der spektakulärsten Naturphotospots Nordostdeutschlands.",
        category=LocationCategory.NATUR,
        observer_lat=54.5808, observer_lon=13.6397,
        subject_lat=54.5808, subject_lon=13.6397,
        subject_name="Rügen Kreidefelsen",
        subject_height_m=118,
        distance_m=0,
        best_times=[BestTime.GOLDEN_MORNING, BestTime.GOLDEN_EVENING],
        ideal_azimuth_range=(40, 130),
        focal_length_suggestions=[24, 35, 70],
        special_notes="Morgenröte über der Ostsee. Technisch außerhalb BB, aber oft lohnenswert für Wochenendtour.",
        access_note="Nationalpark Jasmund, Eintritt Königsstuhl €, Klippenweg frei",
        difficulty=2,
    ),

    # ---------------------------------------------------------------------------
    # BERLIN – WEITERE
    # ---------------------------------------------------------------------------

    PhotoLocation(
        id="tempelhofer_feld_landebahn",
        name="Tempelhofer Feld – Startbahn-Perspektive",
        description="Ex-Flughafen als Stadtlandschaft: endlose Weite, Skyline am Horizont, "
                    "dramatische Wolken über der Piste.",
        category=LocationCategory.INDUSTRIE,
        observer_lat=52.4734, observer_lon=13.4025,
        subject_lat=52.4734, subject_lon=13.4025,
        subject_name="THF Feld & Skyline",
        distance_m=0,
        best_times=[BestTime.GOLDEN_EVENING, BestTime.GOLDEN_MORNING],
        ideal_azimuth_range=(250, 300),
        focal_length_suggestions=[24, 35, 70, 135],
        solar_alignment_note="Sonnenuntergang über dem Feld Richtung West-Skyline: ganzjährig gut",
        access_note="Frei zugänglich, Stativ erlaubt, Fläche sehr windexponiert",
        difficulty=1,
    ),

    PhotoLocation(
        id="oberbaumbrucke_spree",
        name="Oberbaumbrücke – Spreepanorama",
        description="Die meistfotografierte Brücke Berlins. Hochbahnlinie und U-Bahn "
                    "auf zwei Etagen, East-Side-Gallery im Hintergrund.",
        category=LocationCategory.SKYLINE,
        observer_lat=52.5014, observer_lon=13.4445,
        subject_lat=52.5012, subject_lon=13.4439,
        subject_name="Oberbaumbrücke & Spree",
        subject_width_m=150,
        distance_m=80,
        best_times=[BestTime.BLUE_HOUR, BestTime.GOLDEN_EVENING],
        ideal_azimuth_range=(280, 330),
        focal_length_suggestions=[24, 35, 70],
        solar_alignment_note="Sonnenuntergang hinter der Brücke: Oktober und März (Azimut ~265°)",
        access_note="Spreeufer Treptow-Seite, frei zugänglich",
        difficulty=1,
    ),

    PhotoLocation(
        id="teufelsberg",
        name="Teufelsberg – Abhörstation Panorama",
        description="Künstlicher Trümmerberg mit verfallener NSA-Abhörstation. "
                    "360°-Panorama über Berlin, Graffiti-Kuppeln.",
        category=LocationCategory.INDUSTRIE,
        observer_lat=52.4978, observer_lon=13.2404,
        subject_lat=52.4978, subject_lon=13.2404,
        subject_name="Teufelsberg Aussicht",
        subject_height_m=120,
        distance_m=0,
        best_times=[BestTime.GOLDEN_EVENING, BestTime.GOLDEN_MORNING, BestTime.NIGHT],
        focal_length_suggestions=[24, 35, 70, 135],
        solar_alignment_note="Sonnenuntergang über Berlin-Mitte Richtung Osten: "
                              "Fernsehturm, Dom – im Oktober mit tief stehendem Licht",
        access_note="Eintritt ~8€, Guided Tours. Fotografen-Zugang besondere Zeiten.",
        locationscout_url="https://locationscout.net/germany/teufelsberg",
        difficulty=2,
    ),

    PhotoLocation(
        id="muggelspree_kopenick",
        name="Müggelspree Köpenick – Herbstreflexion",
        description="Breiter Flusslauf bei Köpenick, Herbstfarben der Uferbäume "
                    "spiegeln sich im Wasser.",
        category=LocationCategory.WASSER,
        observer_lat=52.4490, observer_lon=13.5795,
        subject_lat=52.4490, subject_lon=13.5795,
        subject_name="Müggelspree",
        distance_m=0,
        best_times=[BestTime.GOLDEN_MORNING, BestTime.GOLDEN_EVENING],
        focal_length_suggestions=[24, 35, 70],
        access_note="Uferpfade beidseitig frei",
        difficulty=1,
    ),

    # ── Neue Locations ──────────────────────────────────────────────────────────

    PhotoLocation(
        id="nikolaikirche_potsdam_west",
        name="Blick auf Nikolaikirche in Potsdam",
        description="Klassizistische Kuppelkirche Karl Friedrich Schinkels. "
                    "Standort nordwestlich der Kirche mit freier Sichtachse auf die Kuppel. "
                    "Abendlicht trifft die Kuppel aus Westen optimal.",
        category=LocationCategory.SCHLOSS,
        observer_lat=52.40409, observer_lon=13.04519,
        subject_lat=52.39970, subject_lon=13.06180,
        subject_name="Nikolaikirche Potsdam",
        subject_height_m=62,
        subject_width_m=50,
        distance_m=1750,
        best_times=[BestTime.GOLDEN_EVENING, BestTime.BLUE_HOUR],
        ideal_azimuth_range=(80, 120),
        focal_length_suggestions=[135, 200, 300],
        solar_alignment_note="Sonne hinter der Kuppel: März/September Äquinoktium ~18 Uhr (Azimut ~90°)",
        lunar_alignment_note="Vollmond steigt hinter Kuppel: Herbst-/Wintervollmonde (Azimut 80–120°)",
        access_note="Alter Markt / Lustgarten, öffentlich frei zugänglich",
        locationscout_url="https://locationscout.net/germany/potsdam-nikolaikirche",
        difficulty=1,
    ),

    PhotoLocation(
        id="kirche_bornstedt",
        name="Kirche Bornstedt – Nordoststandort",
        description="Neoromanische Dorfkirche im Schlosspark Bornstedt, direkt am "
                    "Fischteich. Turm spiegelt sich bei Windstille im Wasser. "
                    "Kurze Distanz für komprimierte Komposition.",
        category=LocationCategory.SCHLOSS,
        observer_lat=52.40979, observer_lon=13.03471,
        subject_lat=52.40934, subject_lon=13.02970,
        subject_name="Kirche Bornstedt",
        subject_height_m=30,
        subject_width_m=20,
        distance_m=340,
        best_times=[BestTime.GOLDEN_MORNING, BestTime.BLUE_HOUR],
        ideal_azimuth_range=(240, 290),
        focal_length_suggestions=[50, 85, 135],
        solar_alignment_note="Morgensonne hinter Turm: Sommer (Azimut ~60°), Standort Nordosten",
        lunar_alignment_note="Mond über Turm: Frühlingsvollmonde aus Nordosten",
        access_note="Schlosspark Bornstedt, frei zugänglich. Fischteich-Uferweg.",
        difficulty=1,
    ),

    PhotoLocation(
        id="insel_werder_nordost",
        name="Insel Werder – Stadtkirche vom Nordostufer",
        description="Stadtkirche Werder thront auf dem Fels der Havelinsel. "
                    "Vom Nordostufer der Havel mit Wasserreflexion. "
                    "Sonnenuntergang beleuchtet die Westfassade.",
        category=LocationCategory.WASSER,
        observer_lat=52.38577, observer_lon=12.95079,
        subject_lat=52.37735, subject_lon=12.94398,
        subject_name="Stadtkirche Werder (Havel)",
        subject_height_m=35,
        subject_width_m=30,
        distance_m=1290,
        best_times=[BestTime.GOLDEN_EVENING, BestTime.BLUE_HOUR],
        ideal_azimuth_range=(190, 230),
        focal_length_suggestions=[135, 200, 300],
        solar_alignment_note="Sonnenuntergang hinter Kirche: Oktober/März (~Azimut 250° — Standort nordöstlich)",
        lunar_alignment_note="Vollmond über Kirche: Sommer-Vollmonde aus Nordost (Azimut ~50°)",
        access_note="Havelufer Nordost, öffentliches Ufer mit Promenade",
        difficulty=1,
    ),

    PhotoLocation(
        id="insel_werder_westufer",
        name="Insel Werder – Stadtkirche vom Westufer",
        description="Blick von Westen über die Havel auf den Kirchenfelsen. "
                    "Morgensonne vergoldet die Ostfassade. "
                    "Ruderboote und Bäume als Vordergrund.",
        category=LocationCategory.WASSER,
        observer_lat=52.37549, observer_lon=12.93915,
        subject_lat=52.37735, subject_lon=12.94398,
        subject_name="Stadtkirche Werder (Havel)",
        subject_height_m=35,
        subject_width_m=30,
        distance_m=410,
        best_times=[BestTime.GOLDEN_MORNING, BestTime.BLUE_HOUR],
        ideal_azimuth_range=(60, 110),
        focal_length_suggestions=[50, 85, 135],
        solar_alignment_note="Morgensonne beleuchtet Ostfassade: ganzjährig bei Sonnenaufgang",
        lunar_alignment_note="Vollmond steigt hinter der Kirche: Winter-Vollmonde (östliche Mondaufgänge)",
        access_note="Westufer Havel, Uferpfad frei",
        difficulty=1,
    ),

    PhotoLocation(
        id="geltow_havelblick",
        name="Geltow – Havelblick auf Caputh",
        description="Offenes Haveltal zwischen Geltow und Caputh. "
                    "Weiter Horizont für Spiegelungen und Sonnenuntergänge über der Havel. "
                    "Ost-West-Achse durch das Haveltal.",
        category=LocationCategory.NATUR,
        observer_lat=52.36066, observer_lon=12.95013,
        subject_lat=52.36496, subject_lon=12.95605,
        subject_name="Havel bei Caputh",
        subject_height_m=0,
        distance_m=590,
        best_times=[BestTime.GOLDEN_EVENING, BestTime.GOLDEN_MORNING],
        ideal_azimuth_range=(60, 120),
        focal_length_suggestions=[24, 35, 70],
        solar_alignment_note="Sonnenaufgang über dem Haveltal: ganzjährig (Azimut ~80°)",
        access_note="Uferweg Geltow, öffentlich",
        difficulty=1,
    ),

    PhotoLocation(
        id="glienicker_bruecke_nord",
        name="Glienicker Brücke – Blick vom Nordufer",
        description="Legendäre Agentenbrücke zwischen Berlin und Potsdam. "
                    "Blick von der Havel-Nordseite auf die Stahlkonstruktion. "
                    "Abendlicht trifft Brücke aus Westen.",
        category=LocationCategory.SCHLOSS,
        observer_lat=52.42340, observer_lon=13.08040,
        subject_lat=52.41347, subject_lon=13.09042,
        subject_name="Glienicker Brücke",
        subject_height_m=8,
        subject_width_m=150,
        distance_m=1370,
        best_times=[BestTime.GOLDEN_EVENING, BestTime.BLUE_HOUR],
        ideal_azimuth_range=(160, 200),
        focal_length_suggestions=[135, 200, 300],
        solar_alignment_note="Sonnenuntergang hinter Brücke: Oktober/März (Azimut ~250°, Standort Nord)",
        lunar_alignment_note="Vollmond über Brücke: Herbstvollmonde steigen im Osten hinter der Brücke",
        access_note="Havel-Nordufer, Tiefer See. Öffentlicher Weg.",
        difficulty=2,
    ),

    PhotoLocation(
        id="glienicker_bruecke_ostufer",
        name="Glienicker Brücke – Ostufer Babelsberger Seite",
        description="Standort östlich der Brücke am Babelsberger Ufer. "
                    "Brücke als Diagonale im Bild, Spiegelung in der Havel. "
                    "Besonders gut bei ruhigem Wasser kurz nach Sonnenaufgang.",
        category=LocationCategory.SCHLOSS,
        observer_lat=52.42569, observer_lon=13.08693,
        subject_lat=52.41347, subject_lon=13.09042,
        subject_name="Glienicker Brücke",
        subject_height_m=8,
        subject_width_m=150,
        distance_m=1380,
        best_times=[BestTime.GOLDEN_MORNING, BestTime.BLUE_HOUR],
        ideal_azimuth_range=(150, 200),
        focal_length_suggestions=[70, 135, 200],
        solar_alignment_note="Morgensonne beleuchtet Brücke von Osten: ganzjährig",
        access_note="Babelsberger Uferweg östlich der Brücke, frei zugänglich",
        difficulty=2,
    ),

    PhotoLocation(
        id="heilandskirche_sacrow_sued",
        name="Heilandskirche Sacrow – Standort Südufer",
        description="Neuromanische Kirche direkt am Wasser des Jungfernsees. "
                    "Standort südlich auf dem Steg/Ufer: Kirchturm im Abendlicht "
                    "mit Spiegelung im See. Venezianische Anmutung.",
        category=LocationCategory.WASSER,
        observer_lat=52.425791, observer_lon=13.099694,
        subject_lat=52.424653, subject_lon=13.096472,
        subject_name="Heilandskirche Sacrow",
        subject_height_m=35,
        subject_width_m=25,
        distance_m=280,
        best_times=[BestTime.GOLDEN_EVENING, BestTime.BLUE_HOUR],
        ideal_azimuth_range=(240, 290),
        focal_length_suggestions=[50, 85, 135],
        solar_alignment_note="Sonnenuntergang hinter dem Kirchturm: April/September (~Azimut 270°)",
        lunar_alignment_note="Vollmond spiegelt sich im Jungfernsee, Kirche als Silhouette",
        access_note="Ufer zugänglich, aber Privatgelände teilweise – Pfad am Wasserrand nutzbar",
        difficulty=2,
    ),

    PhotoLocation(
        id="heilandskirche_sacrow_sw",
        name="Heilandskirche Sacrow – Standort Südwest",
        description="Zweite Perspektive auf die Heilandskirche vom Südwestufer. "
                    "Breiterer Blickwinkel auf den Jungfernsee, Schilf als Vordergrund. "
                    "Morgenlicht aus Osten vergoldet die Apsis.",
        category=LocationCategory.WASSER,
        observer_lat=52.422439, observer_lon=13.099083,
        subject_lat=52.424653, subject_lon=13.096472,
        subject_name="Heilandskirche Sacrow",
        subject_height_m=35,
        subject_width_m=25,
        distance_m=350,
        best_times=[BestTime.GOLDEN_MORNING, BestTime.BLUE_HOUR],
        ideal_azimuth_range=(310, 360),
        focal_length_suggestions=[50, 85, 135],
        solar_alignment_note="Morgensonne beleuchtet Ostfassade: ganzjährig Sonnenaufgang",
        access_note="Jungfernsee-Ufer Südwest, schmaler Uferweg",
        difficulty=3,
    ),

    PhotoLocation(
        id="kanal_neuer_garten",
        name="Kanal Neuer Garten – Marmorpalais Spiegelung",
        description="Verbindungskanal zwischen Heiligem See und Jungfernsee "
                    "mit Blick auf das Marmorpalais. "
                    "Stille Wasserfläche für Spiegelungen, westliche Abendsonne.",
        category=LocationCategory.WASSER,
        observer_lat=52.41620, observer_lon=13.08029,
        subject_lat=52.41464, subject_lon=13.07656,
        subject_name="Marmorpalais / Kanal Neuer Garten",
        subject_height_m=18,
        subject_width_m=40,
        distance_m=420,
        best_times=[BestTime.GOLDEN_EVENING, BestTime.BLUE_HOUR],
        ideal_azimuth_range=(200, 250),
        focal_length_suggestions=[50, 85, 135],
        solar_alignment_note="Abendlicht auf dem Palais: Mai–August bei Sonnenuntergang (~Azimut 280°)",
        lunar_alignment_note="Vollmond spiegelt sich im Kanal: Herbst-Vollmonde",
        access_note="Neuer Garten, frei zugänglich (Öffnungszeiten beachten)",
        difficulty=1,
    ),

    PhotoLocation(
        id="schloss_sanssouci_ostblick",
        name="Schloss Sanssouci – Weinbergterrassen Oststandort",
        description="Rokokoschloss Friedrichs des Großen auf sechs Weinbergterrassen. "
                    "Standort östlich der Terrassen: Blick auf gesamte Schlossfront "
                    "mit Fontäne im Vordergrund. Goldstunde von Osten.",
        category=LocationCategory.SCHLOSS,
        observer_lat=52.40848, observer_lon=13.03885,
        subject_lat=52.404193, subject_lon=13.038433,
        subject_name="Schloss Sanssouci",
        subject_height_m=20,
        subject_width_m=100,
        distance_m=480,
        best_times=[BestTime.GOLDEN_MORNING, BestTime.GOLDEN_EVENING, BestTime.WINTER],
        ideal_azimuth_range=(270, 320),
        focal_length_suggestions=[24, 35, 70],
        solar_alignment_note="Morgensonne beleuchtet Nordfassade: ganzjährig Sonnenaufgang Osten",
        lunar_alignment_note="Vollmond über Sanssouci: Herbst-Vollmonde aus östlichem Standort",
        access_note="Terrassenpark öffentlich, Schloss kostenpflichtig. Östlicher Zugang über Maulbeerallee.",
        locationscout_url="https://locationscout.net/germany/potsdam-sanssouci",
        difficulty=1,
    ),

    PhotoLocation(
        id="flatowturm_nordwest",
        name="Flatowturm Babelsberg – Nordweststandort",
        description="Neogotischer Wasserturm im Park Babelsberg (1856). "
                    "Standort Nordwest: Turm mit Havel-See im Hintergrund. "
                    "Teleaufnahme komprimiert Turm und Wasserfläche.",
        category=LocationCategory.SCHLOSS,
        observer_lat=52.40820, observer_lon=13.07849,
        subject_lat=52.403123, subject_lon=13.086669,
        subject_name="Flatowturm Babelsberg",
        subject_height_m=45,
        subject_width_m=15,
        distance_m=710,
        best_times=[BestTime.GOLDEN_EVENING, BestTime.BLUE_HOUR],
        ideal_azimuth_range=(130, 170),
        focal_length_suggestions=[135, 200, 300],
        solar_alignment_note="Abendlicht auf der Turmwestseite: ganzjährig Sonnenuntergang",
        lunar_alignment_note="Vollmond hinter Flatowturm: Sommer-Vollmonde (Azimut ~130°)",
        access_note="Park Babelsberg, Eintritt 4€. Wege befahrbar.",
        locationscout_url="https://locationscout.net/germany/potsdam-flatowturm",
        difficulty=2,
    ),

    PhotoLocation(
        id="flatowturm_west",
        name="Flatowturm Babelsberg – Weststandort",
        description="Direkter Westblick auf den Flatowturm vom Parkweg. "
                    "Kürzere Distanz, Turm füllt das Bild. Vordergrund: "
                    "Parkrasen und Bäume. Sonnenuntergang direkt hinter dem Turm.",
        category=LocationCategory.SCHLOSS,
        observer_lat=52.403888, observer_lon=13.076069,
        subject_lat=52.403123, subject_lon=13.086669,
        subject_name="Flatowturm Babelsberg",
        subject_height_m=45,
        subject_width_m=15,
        distance_m=760,
        best_times=[BestTime.GOLDEN_EVENING, BestTime.BLUE_HOUR],
        ideal_azimuth_range=(80, 120),
        focal_length_suggestions=[85, 135, 200],
        solar_alignment_note="Sonne direkt hinter Turm: April/September ~Azimut 270° — Silhouette-Effekt",
        lunar_alignment_note="Vollmond steigt hinter Turm: Frühlings-/Herbstvollmonde",
        access_note="Park Babelsberg Westeingang, Eintritt 4€",
        difficulty=2,
    ),

    PhotoLocation(
        id="flatowturm_sw",
        name="Flatowturm Babelsberg – Südweststandort",
        description="Weitwinkelperspektive auf Flatowturm vom Südwestzugang. "
                    "Tiefer Sonnenstand im Winter erzeugt lange Schatten und "
                    "dramatisches Seitenlicht auf dem Turm.",
        category=LocationCategory.SCHLOSS,
        observer_lat=52.40103, observer_lon=13.07345,
        subject_lat=52.403123, subject_lon=13.086669,
        subject_name="Flatowturm Babelsberg",
        subject_height_m=45,
        subject_width_m=15,
        distance_m=1050,
        best_times=[BestTime.WINTER, BestTime.GOLDEN_EVENING],
        ideal_azimuth_range=(40, 80),
        focal_length_suggestions=[135, 200, 300],
        solar_alignment_note="Wintersonnenuntergang südwestlich: flaches Licht auf Turmfassade",
        access_note="Südlicher Parkzugang Babelsberg, frei zugänglich",
        difficulty=2,
    ),

    PhotoLocation(
        id="bodemuseum_fernsehturm",
        name="Bodemuseum mit Fernsehturm – Spreebrücke",
        description="Klassische Berlin-Komposition: Bodemuseum-Kuppel im Vordergrund, "
                    "Fernsehturm dahinter. Standort auf der Spreebrücke nördlich "
                    "des Museums. Morgenlicht aus Osten ideal.",
        category=LocationCategory.SKYLINE,
        observer_lat=52.52250, observer_lon=13.39173,
        subject_lat=52.521692, subject_lon=13.394716,
        subject_name="Bodemuseum + Fernsehturm",
        subject_height_m=110,
        subject_width_m=80,
        distance_m=250,
        best_times=[BestTime.GOLDEN_MORNING, BestTime.BLUE_HOUR],
        ideal_azimuth_range=(80, 130),
        focal_length_suggestions=[35, 50, 85],
        solar_alignment_note="Morgensonne hinter Fernsehturm: Sommer (Azimut ~60–80°)",
        lunar_alignment_note="Vollmond über Fernsehturm: ganzjährig bei östlichem Mondaufgang",
        access_note="Monbijoubrücke / Am Kupfergraben, öffentlich",
        locationscout_url="https://locationscout.net/germany/berlin-bodemuseum",
        difficulty=1,
    ),

    PhotoLocation(
        id="brandenburger_tor_westblick",
        name="Brandenburger Tor – Weststandort Tiergarten",
        description="Ikonisches Brandenburger Tor von der Westseite aus dem Tiergarten. "
                    "Standort westlich des Tores: Quadriga leuchtet im Morgenlicht. "
                    "Fußgängerzone, langer Freiheitsblick.",
        category=LocationCategory.SKYLINE,
        observer_lat=52.51463, observer_lon=13.35192,
        subject_lat=52.51621, subject_lon=13.37661,
        subject_name="Brandenburger Tor",
        subject_height_m=26,
        subject_width_m=65,
        distance_m=1680,
        best_times=[BestTime.GOLDEN_MORNING, BestTime.BLUE_HOUR, BestTime.WINTER],
        ideal_azimuth_range=(75, 110),
        focal_length_suggestions=[200, 300, 400],
        solar_alignment_note="Sommersonnenwende: Sonne geht direkt durch das Tor auf (~Azimut 50°). "
                              "Winter: tiefer Sonnenstand beleuchtet Quadriga goldfarben.",
        lunar_alignment_note="Vollmond durch das Tor: Herbst/Winter-Vollmonde (Azimut 80–100°)",
        access_note="Tiergarten westlich des Tores, 17. Juni Straße. Öffentlich.",
        locationscout_url="https://locationscout.net/germany/berlin-brandenburger-tor",
        difficulty=1,
    ),

    PhotoLocation(
        id="fernsehturm_skyline_west",
        name="Fernsehturm Panorama – Weitsicht vom Westufer Wannsee",
        description="Extremteleobjektiv-Aufnahme: Berliner Skyline mit Fernsehturm "
                    "aus großer Distanz, komprimiert durch ca. 1500mm-Äquivalent. "
                    "Dunst-Lagen im Herbst/Winter erzeugen atmosphärische Schichtung.",
        category=LocationCategory.SKYLINE,
        observer_lat=52.50218, observer_lon=13.24795,
        subject_lat=52.520834, subject_lon=13.409420,
        subject_name="Berliner Fernsehturm (Skyline)",
        subject_height_m=368,
        subject_width_m=30,
        distance_m=12400,
        best_times=[BestTime.GOLDEN_MORNING, BestTime.WINTER],
        ideal_azimuth_range=(75, 95),
        focal_length_suggestions=[400, 600, 800],
        solar_alignment_note="Morgensonne hinter Fernsehturm: Herbst/Winter (Azimut ~90°), "
                              "Standort im Westen bei Nikolassee",
        lunar_alignment_note="Vollmond hinter Fernsehturm: Herbst-/Wintervollmonde (Azimut ~85°)",
        access_note="Uferbereich Wannsee / Nikolassee Westseite, frei zugänglich",
        difficulty=3,
    ),

    PhotoLocation(
        id="berliner_dom_lustgarten",
        name="Berliner Dom – Lustgarten Spreeseite",
        description="Berliner Dom vom Lustgarten und der Friedrichsbrücke aus. "
                    "Spreekanal im Vordergrund, Dom und seine Kuppel im Zentrum. "
                    "Morgensonne beleuchtet die Ostfassade, Blaue Stunde für Spiegelungen.",
        category=LocationCategory.SKYLINE,
        observer_lat=52.52120, observer_lon=13.39750,
        subject_lat=52.519132, subject_lon=13.401076,
        subject_name="Berliner Dom",
        subject_height_m=114,
        subject_width_m=73,
        distance_m=420,
        best_times=[BestTime.GOLDEN_MORNING, BestTime.BLUE_HOUR],
        ideal_azimuth_range=(110, 150),
        focal_length_suggestions=[35, 50, 85],
        solar_alignment_note="Morgensonne hinter dem Dom: Sommer (Azimut ~60°). "
                              "Herbst/Winter: Dom leuchtet in der tief stehenden Sonne.",
        lunar_alignment_note="Vollmond über dem Dom: Herbstvollmonde aus nördlichem Standort",
        access_note="Lustgarten und Friedrichsbrücke öffentlich; Spreeufer Am Lustgarten frei",
        locationscout_url="https://locationscout.net/germany/berlin-berliner-dom",
        difficulty=1,
    ),

    PhotoLocation(
        id="molecule_men_elsenbruecke",
        name="Molecule Men – Elsenbrücke",
        description="Drei 30 Meter hohe verschweißte Männerfiguren von Jonathan Borofsky "
                    "an der Spreemündung der Bezirksgrenzen. "
                    "Standort Elsenbrücke: Erhöhte Perspektive, Spree als Vordergrund, "
                    "Figuren im Gegenlicht des Sonnenuntergangs.",
        category=LocationCategory.INDUSTRIE,
        observer_lat=52.49940, observer_lon=13.45840,
        subject_lat=52.496958, subject_lon=13.458988,
        subject_name="Molecule Men",
        subject_height_m=30,
        subject_width_m=20,
        distance_m=270,
        best_times=[BestTime.GOLDEN_EVENING, BestTime.BLUE_HOUR],
        ideal_azimuth_range=(150, 200),
        focal_length_suggestions=[35, 50, 85],
        solar_alignment_note="Sonnenuntergang hinter den Figuren: April/September (Azimut ~250°–270°)",
        lunar_alignment_note="Vollmond über den Molecule Men: Herbst-Vollmonde aus Norden",
        access_note="Elsenbrücke (B96a), öffentliche Brücke – Gehsteig nutzbar",
        locationscout_url="https://locationscout.net/germany/berlin-molecule-men",
        difficulty=1,
    ),

    PhotoLocation(
        id="schloss_charlottenburg_ostblick",
        name="Schloss Charlottenburg – Ehrenhof Oststandort",
        description="Barockes Stadtschloss mit vergoldetem Fortunaturm. "
                    "Standort im Ehrenhof nördlich: Blick auf die gesamte Schlossfront "
                    "mit dem zentralen Turm. Abendsonne beleuchtet die Westfassade.",
        category=LocationCategory.SCHLOSS,
        observer_lat=52.52640, observer_lon=13.29485,
        subject_lat=52.520894, subject_lon=13.295755,
        subject_name="Schloss Charlottenburg",
        subject_height_m=48,
        subject_width_m=160,
        distance_m=620,
        best_times=[BestTime.GOLDEN_EVENING, BestTime.BLUE_HOUR, BestTime.WINTER],
        ideal_azimuth_range=(160, 200),
        focal_length_suggestions=[35, 50, 85],
        solar_alignment_note="Sonnenuntergang über dem Fortunaturm: Oktober/März (~Azimut 250°)",
        lunar_alignment_note="Vollmond hinter Turm: Herbst-Vollmonde (Azimut ~160–180°)",
        access_note="Ehrenhof Charlottenburg, tagsüber frei zugänglich",
        locationscout_url="https://locationscout.net/germany/berlin-schloss-charlottenburg",
        difficulty=1,
    ),
    PhotoLocation(
        id="berlin_skyline_from_fischerinsel_skyscra",
        name="Berlin Skyline from Fischerinsel Skyscraper",
        description="",
        category=LocationCategory.SKYLINE,
        observer_lat=52.51425, observer_lon=13.40739,
        subject_lat=52.51425,  subject_lon=13.40739,  # TODO: Motiv-GPS verfeinern
        subject_name="Berlin Skyline from Fischerinsel Skyscraper",
        subject_height_m=20.0,    # TODO: anpassen
        distance_m=200.0,         # TODO: anpassen
        focal_length_suggestions=[50, 85, 135, 200],
        special_notes="Locationscout-Import. Tags: Television Tower, Rooftop, River, Viewpoint, Architecture",
        solar_alignment_note="",
        lunar_alignment_note="",
        access_note="",
        locationscout_url="https://www.locationscout.net/germany/828-berlin-skyline-from-fischerinsel-skyscraper/24153",
        difficulty=2,
    ),
    PhotoLocation(
        id="brandenburg_gate_from_behind_berlin",
        name="Brandenburg Gate from behind, Berlin",
        description="",
        category=LocationCategory.SKYLINE,
        observer_lat=52.51623, observer_lon=13.37452,
        subject_lat=52.51623,  subject_lon=13.37452,  # TODO: Motiv-GPS verfeinern
        subject_name="Brandenburg Gate from behind, Berlin",
        subject_height_m=20.0,    # TODO: anpassen
        distance_m=200.0,         # TODO: anpassen
        focal_length_suggestions=[50, 85, 135, 200],
        special_notes="Locationscout-Import. Tags: City, History, Monument, traffic, Gate",
        solar_alignment_note="",
        lunar_alignment_note="",
        access_note="",
        locationscout_url="https://www.locationscout.net/germany/1839-brandenburg-gate-from-behind-berlin/3102",
        difficulty=2,
    ),
    PhotoLocation(
        id="haus_der_kulturen_der_welt_berlin",
        name="Haus der Kulturen der Welt, Berlin",
        description="",
        category=LocationCategory.SKYLINE,
        observer_lat=52.51753, observer_lon=13.36537,
        subject_lat=52.51753,  subject_lon=13.36537,  # TODO: Motiv-GPS verfeinern
        subject_name="Haus der Kulturen der Welt, Berlin",
        subject_height_m=20.0,    # TODO: anpassen
        distance_m=200.0,         # TODO: anpassen
        focal_length_suggestions=[50, 85, 135, 200],
        special_notes="Locationscout-Import. Tags: Architecture",
        solar_alignment_note="",
        lunar_alignment_note="",
        access_note="",
        locationscout_url="https://www.locationscout.net/germany/5165-haus-der-kulturen-der-welt-berlin/9220",
        difficulty=2,
    ),
    PhotoLocation(
        id="berlin_cathedral_berliner_dom",
        name="Berlin Cathedral (Berliner Dom)",
        description="",
        category=LocationCategory.SKYLINE,
        observer_lat=52.51823, observer_lon=13.39899,
        subject_lat=52.51823,  subject_lon=13.39899,  # TODO: Motiv-GPS verfeinern
        subject_name="Berlin Cathedral (Berliner Dom)",
        subject_height_m=20.0,    # TODO: anpassen
        distance_m=200.0,         # TODO: anpassen
        focal_length_suggestions=[50, 85, 135, 200],
        special_notes="Locationscout-Import. Tags: night photography, Sunset, Berlin Cathedral, Lustgarten, Berliner Dom",
        solar_alignment_note="",
        lunar_alignment_note="",
        access_note="",
        locationscout_url="https://www.locationscout.net/germany/467-berlin-cathedral-berliner-dom/17658",
        difficulty=2,
    ),
    PhotoLocation(
        id="tempodrom_berlin",
        name="Tempodrom, Berlin",
        description="",
        category=LocationCategory.SKYLINE,
        observer_lat=52.50110, observer_lon=13.38080,
        subject_lat=52.50110,  subject_lon=13.38080,  # TODO: Motiv-GPS verfeinern
        subject_name="Tempodrom, Berlin",
        subject_height_m=20.0,    # TODO: anpassen
        distance_m=200.0,         # TODO: anpassen
        focal_length_suggestions=[50, 85, 135, 200],
        special_notes="Locationscout-Import. Tags: Modern Architecture, Architecture, fineart",
        solar_alignment_note="",
        lunar_alignment_note="",
        access_note="",
        locationscout_url="https://www.locationscout.net/germany/1920-tempodrom-berlin/58331",
        difficulty=2,
    ),
    PhotoLocation(
        id="staircase_of_hotel_bristol_berlin",
        name="Staircase of Hotel Bristol Berlin",
        description="",
        category=LocationCategory.SKYLINE,
        observer_lat=52.50325, observer_lon=13.32719,
        subject_lat=52.50325,  subject_lon=13.32719,  # TODO: Motiv-GPS verfeinern
        subject_name="Staircase of Hotel Bristol Berlin",
        subject_height_m=20.0,    # TODO: anpassen
        distance_m=200.0,         # TODO: anpassen
        focal_length_suggestions=[50, 85, 135, 200],
        special_notes="Locationscout-Import. Tags: Urban Architecture, Minimalism, Modern Architecture, Architektur, Architecture",
        solar_alignment_note="",
        lunar_alignment_note="",
        access_note="",
        locationscout_url="https://www.locationscout.net/germany/37549-staircase-of-hotel-bristol-berlin/88898",
        difficulty=2,
    ),
    PhotoLocation(
        id="holocaust_memorial_berlin",
        name="Holocaust-Memorial, Berlin",
        description="",
        category=LocationCategory.SKYLINE,
        observer_lat=52.51442, observer_lon=13.37942,
        subject_lat=52.51442,  subject_lon=13.37942,  # TODO: Motiv-GPS verfeinern
        subject_name="Holocaust-Memorial, Berlin",
        subject_height_m=20.0,    # TODO: anpassen
        distance_m=200.0,         # TODO: anpassen
        focal_length_suggestions=[50, 85, 135, 200],
        special_notes="Locationscout-Import. Tags: War memorial, Cloudy, Monument, Concrete, Field",
        solar_alignment_note="",
        lunar_alignment_note="",
        access_note="",
        locationscout_url="https://www.locationscout.net/germany/804-holocaust-memorial-berlin/33485",
        difficulty=2,
    ),
    PhotoLocation(
        id="castle_fuerstlich_drehna",
        name="Castle Fürstlich Drehna",
        description="",
        category=LocationCategory.SKYLINE,
        observer_lat=51.75994, observer_lon=13.80340,
        subject_lat=51.75994,  subject_lon=13.80340,  # TODO: Motiv-GPS verfeinern
        subject_name="Castle Fürstlich Drehna",
        subject_height_m=20.0,    # TODO: anpassen
        distance_m=200.0,         # TODO: anpassen
        focal_length_suggestions=[50, 85, 135, 200],
        special_notes="Locationscout-Import. Tags: moat, Lake, reflection, Water, Castle",
        solar_alignment_note="",
        lunar_alignment_note="",
        access_note="",
        locationscout_url="https://www.locationscout.net/germany/10329-castle-fuerstlich-drehna/78266",
        difficulty=2,
    ),
    PhotoLocation(
        id="rostiger_nagel_rusty_nail",
        name="Rostiger Nagel - Rusty Nail",
        description="",
        category=LocationCategory.NATUR,
        observer_lat=51.52680, observer_lon=14.10003,
        subject_lat=51.52680,  subject_lon=14.10003,  # TODO: Motiv-GPS verfeinern
        subject_name="Rostiger Nagel - Rusty Nail",
        subject_height_m=20.0,    # TODO: anpassen
        distance_m=200.0,         # TODO: anpassen
        focal_length_suggestions=[50, 85, 135, 200],
        special_notes="Locationscout-Import. Tags: Monument, steel",
        solar_alignment_note="",
        lunar_alignment_note="",
        access_note="",
        locationscout_url="https://www.locationscout.net/germany/7054-rostiger-nagel-rusty-nail/13025",
        difficulty=2,
    ),
    PhotoLocation(
        id="schloss_steinhoefel",
        name="Schloss Steinhöfel",
        description="",
        category=LocationCategory.NATUR,
        observer_lat=52.39630, observer_lon=14.16663,
        subject_lat=52.39630,  subject_lon=14.16663,  # TODO: Motiv-GPS verfeinern
        subject_name="Schloss Steinhöfel",
        subject_height_m=20.0,    # TODO: anpassen
        distance_m=200.0,         # TODO: anpassen
        focal_length_suggestions=[50, 85, 135, 200],
        special_notes="Locationscout-Import. Tags: Lake, Castel, Landscape",
        solar_alignment_note="",
        lunar_alignment_note="",
        access_note="",
        locationscout_url="https://www.locationscout.net/germany/20093-schloss-steinhoefel/44379",
        difficulty=2,
    ),
    PhotoLocation(
        id="sunset_over_wittstock",
        name="Wittstock – Stadtmauer & Westskyline",
        description="Stadtmauer und historische Silhouette Wittstocks im Abendlicht. "
                    "Dramatische Wolkenformationen und weiter Horizont Richtung Westen.",
        category=LocationCategory.SKYLINE,
        observer_lat=53.15949, observer_lon=12.48728,
        subject_lat=53.15949,  subject_lon=12.48728,  # TODO: Motiv-GPS verfeinern
        subject_name="Wittstock Stadtmauer & Skyline",
        subject_height_m=20.0,    # TODO: anpassen
        distance_m=200.0,         # TODO: anpassen
        focal_length_suggestions=[50, 85, 135, 200],
        special_notes="Locationscout-Import. Tags: dramatic sky, dramatic, clouds, Citywall, Sunset",
        solar_alignment_note="",
        lunar_alignment_note="",
        access_note="",
        locationscout_url="https://www.locationscout.net/germany/31509-sunset-over-wittstock/73339",
        difficulty=2,
    ),
    PhotoLocation(
        id="brandenburg_landtag",
        name="Brandenburg Landtag",
        description="",
        category=LocationCategory.SKYLINE,
        observer_lat=52.39510, observer_lon=13.05949,
        subject_lat=52.39510,  subject_lon=13.05949,  # TODO: Motiv-GPS verfeinern
        subject_name="Brandenburg Landtag",
        subject_height_m=20.0,    # TODO: anpassen
        distance_m=200.0,         # TODO: anpassen
        focal_length_suggestions=[50, 85, 135, 200],
        special_notes="Locationscout-Import. Tags: Architecture, Potsdam, Church",
        solar_alignment_note="",
        lunar_alignment_note="",
        access_note="",
        locationscout_url="https://www.locationscout.net/germany/30185-brandenburg-landtag/70926",
        difficulty=2,
    ),
    # --- TASK-04: Neue Locations ---

    PhotoLocation(
        id="schloss_cecilienhof",
        name="Schloss Cecilienhof",
        description="Tudor-Revival-Schloss im Neuen Garten, Schauplatz der Potsdamer Konferenz 1945. "
                    "Weitläufiges Ensemble mit 55 Kaminen und steilem Giebeldach. "
                    "Mond- und Sonnenaufgang hinter der Ostfassade vom Parkweg aus besonders wirkungsvoll.",
        category=LocationCategory.SCHLOSS,
        observer_lat=52.4212, observer_lon=13.0730,
        subject_lat=52.4227,  subject_lon=13.0706,
        subject_name="Schloss Cecilienhof",
        subject_height_m=14.0,
        subject_width_m=80.0,
        distance_m=220.0,
        focal_length_suggestions=[85, 135, 200],
        solar_alignment_note="Sonnenaufgang über Ostfassade im Herbst/Winter möglich.",
        lunar_alignment_note="Vollmond-Aufgang hinter Dachfirst von Südost.",
        access_note="Neuer Garten, Potsdam. Eintritt Park frei.",
        difficulty=1,
    ),

    PhotoLocation(
        id="schloss_pfaueninsel",
        name="Schloss Pfaueninsel",
        description="Weißes romantisches Lustschlösschen auf der Pfaueninsel in der Havel, "
                    "zwei Rundtürme verbunden durch eine schmiedeeiserne Brücke. "
                    "Spiegelung im Wasser und Mond-Untergang hinter den Türmen von der Fähranlegestelle.",
        category=LocationCategory.SCHLOSS,
        observer_lat=52.4315, observer_lon=13.1100,
        subject_lat=52.4308,  subject_lon=13.1197,
        subject_name="Schloss Pfaueninsel – Rundtürme",
        subject_height_m=18.0,
        subject_width_m=30.0,
        distance_m=650.0,
        focal_length_suggestions=[200, 300, 400],
        solar_alignment_note="",
        lunar_alignment_note="Monduntergang im Westen hinter den Türmen (Havel-Perspektive).",
        access_note="Fähre Wannsee → Pfaueninsel (saisonal). Foto vom Festland-Ufer ohne Fährticket möglich.",
        difficulty=1,
    ),

    PhotoLocation(
        id="kloster_chorin",
        name="Kloster Chorin – Westfassade",
        description="Bedeutendste gotische Backsteinkirche Brandenburgs, ehem. Zisterzienserabtei (1258). "
                    "Ikonische turmlose Westfassade mit gestuften Giebeln und Maßwerkfenstern. "
                    "Ost-West-Kirchenachse: Sonnenuntergang hinter dem Westgiebel im Herbst dramatisch.",
        category=LocationCategory.SCHLOSS,
        observer_lat=52.8942, observer_lon=13.8720,
        subject_lat=52.8944,  subject_lon=13.8761,
        subject_name="Kloster Chorin – Westgiebel",
        subject_height_m=24.0,
        subject_width_m=35.0,
        distance_m=280.0,
        focal_length_suggestions=[50, 85, 135],
        solar_alignment_note="Sonnenuntergang hinter Westgiebel (~270°) im Herbst/Winter.",
        lunar_alignment_note="Mondaufgang hinter Ostabschluss (Chorpolygon).",
        access_note="Chorin, Barnim. Parkplatz am Kloster. ~60 km nordöstlich Berlin.",
        difficulty=1,
    ),

    PhotoLocation(
        id="dorfkirche_schoenermark",
        name="Dorfkirche Schönermark (Uckermark)",
        description="Romanische Feldsteinkirche auf dem Dorfanger bei Angermünde, Uckermark. "
                    "Markanter Westturm aus Feldsteinen, freistehend in idyllischer Landschaft. "
                    "Mond- und Sonnenaufgang hinter dem Turm besonders wirkungsvoll.",
        category=LocationCategory.SCHLOSS,
        observer_lat=53.0155, observer_lon=14.0388,
        subject_lat=53.0162,  subject_lon=14.0405,
        subject_name="Dorfkirche Schönermark – Westturm",
        subject_height_m=18.0,
        subject_width_m=12.0,
        distance_m=120.0,
        focal_length_suggestions=[50, 85, 135, 200],
        solar_alignment_note="Sonnenaufgang hinter dem Turm bei östlicher Perspektive.",
        lunar_alignment_note="Mondaufgang hinter Westturm vom Dorfanger.",
        access_note="Schönermark bei Angermünde, Uckermark. GPS-Koordinaten vor Ort bitte verifizieren.",
        difficulty=2,
    ),

    PhotoLocation(
        id="seelower_hoehen_ehrenmal",
        name="Seelower Höhen – Sowjetisches Ehrenmal",
        description="Sowjetisches Ehrenmal auf dem Plateau der Seelower Höhen, Gesamthöhe 9,9 m. "
                    "Monumentale Soldatenstatue über dem Oderbruch, eingeweiht 1945. "
                    "Sonnenaufgang über der weiten Oderbruch-Ebene hinter dem Monument: dramatisches Gegenlicht.",
        category=LocationCategory.SCHLOSS,
        observer_lat=52.5325, observer_lon=14.1665,
        subject_lat=52.5340,  subject_lon=14.1680,
        subject_name="Sowjetisches Ehrenmal Seelow",
        subject_height_m=10.0,
        subject_width_m=4.0,
        distance_m=180.0,
        focal_length_suggestions=[85, 135, 200, 300],
        solar_alignment_note="Sonnenaufgang über Oderbruch hinter dem Monument (~90°).",
        lunar_alignment_note="",
        access_note="Gedenkstätte Seelower Höhen, Seelow. ~80 km östlich Berlin. GPS vor Ort verifizieren.",
        difficulty=2,
    ),

]  # Ende LOCATIONS


def get_location_by_id(location_id: str) -> Optional[PhotoLocation]:
    for loc in LOCATIONS:
        if loc.id == location_id:
            return loc
    return None


def get_locations_by_category(cat: LocationCategory) -> list[PhotoLocation]:
    return [loc for loc in LOCATIONS if loc.category == cat]


def get_all_location_ids() -> list[str]:
    return [loc.id for loc in LOCATIONS]
