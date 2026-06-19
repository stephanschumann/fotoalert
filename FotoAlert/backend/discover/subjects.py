"""
Kuratierte Leitmotive für den Scout-Tab.

Jedes Motiv enthält:
  lat/lon         — GPS der Motivspitze / Hauptstruktur
  structure_height_m — Bauwerkshöhe (Fuß bis Spitze)
  terrain_offset_m   — Mehrere Meter wenn das Motiv auf erhöhtem Gelände steht
                        relativ zum Berliner Mittelniveau (~35m NN)
  apex_effective_m   — = structure_height_m + terrain_offset_m
                        Effektive Höhe über einem Beobachter am Boden (35m NN)

Höhenquellen: Wikipedia, Wikidata, amtliche Denkmallisten.
"""
from __future__ import annotations
from dataclasses import dataclass


@dataclass(frozen=True)
class DiscoverSubject:
    id: str
    name: str
    kategorie: str           # Emoji + Kurzname für UI
    lat: float
    lon: float
    structure_height_m: float   # Bauwerkshöhe vom Geländeniveau
    terrain_offset_m: float     # Geländeoffset gegenüber ~35m NN (Berliner Mittelniveau)
    subject_width_m: float      # Breite für Brennweiten-Berechnung
    hoehe_confidence: str       # "hoch" | "mittel" | "niedrig"

    @property
    def apex_effective_m(self) -> float:
        """Effektive Höhe über einem Beobachter auf Berliner Mittelniveau (35m NN)."""
        return self.structure_height_m + self.terrain_offset_m


SUBJECTS: list[DiscoverSubject] = [
    DiscoverSubject(
        id="fernsehturm_berlin",
        name="Berliner Fernsehturm",
        kategorie="🗼 Turm",
        lat=52.5208, lon=13.4094,
        structure_height_m=368.0,
        terrain_offset_m=0.0,    # Alexanderplatz ~35m NN ≈ Berliner Mittel
        subject_width_m=18.0,    # Kugel-Durchmesser
        hoehe_confidence="hoch",
    ),
    DiscoverSubject(
        id="siegessaeule_berlin",
        name="Siegessäule Berlin",
        kategorie="🏛 Denkmal",
        lat=52.5145, lon=13.3501,
        structure_height_m=67.0,
        terrain_offset_m=0.0,
        subject_width_m=8.0,
        hoehe_confidence="hoch",
    ),
    DiscoverSubject(
        id="berliner_dom",
        name="Berliner Dom",
        kategorie="⛪ Kirche",
        lat=52.5190, lon=13.4014,
        structure_height_m=114.0,
        terrain_offset_m=0.0,
        subject_width_m=70.0,
        hoehe_confidence="hoch",
    ),
    DiscoverSubject(
        id="schloss_sanssouci",
        name="Schloss Sanssouci",
        kategorie="🏰 Schloss",
        lat=52.4039, lon=13.0386,
        structure_height_m=14.0,
        terrain_offset_m=10.0,   # Terrasse auf ~45m NN (+10m über Berliner Mittel)
        subject_width_m=120.0,
        hoehe_confidence="mittel",
    ),
    DiscoverSubject(
        id="schloss_cecilienhof",
        name="Schloss Cecilienhof",
        kategorie="🏰 Schloss",
        lat=52.4156, lon=13.0657,
        structure_height_m=13.0,
        terrain_offset_m=0.0,
        subject_width_m=80.0,
        hoehe_confidence="mittel",
    ),
    DiscoverSubject(
        id="flatowturm_babelsberg",
        name="Flatowturm Babelsberg",
        kategorie="🗼 Turm",
        lat=52.3969, lon=13.1036,
        structure_height_m=34.0,
        terrain_offset_m=5.0,    # Hügelkuppe Babelsberg-Park ~40m NN
        subject_width_m=8.0,
        hoehe_confidence="hoch",
    ),
    DiscoverSubject(
        id="glienicker_bruecke",
        name="Glienicker Brücke",
        kategorie="🌉 Brücke",
        lat=52.4156, lon=13.0883,
        structure_height_m=9.0,
        terrain_offset_m=0.0,    # Fotograf steht ebenfalls am Havel-Ufer (~gleiche Höhe wie Brücken-Basis)
        subject_width_m=150.0,
        hoehe_confidence="hoch",
    ),
    DiscoverSubject(
        id="historische_muehle_sanssouci",
        name="Historische Mühle Sanssouci",
        kategorie="⚙️ Mühle",
        lat=52.4034, lon=13.0341,
        structure_height_m=12.0,
        terrain_offset_m=10.0,   # Windmühlenberg ~45m NN
        subject_width_m=10.0,
        hoehe_confidence="mittel",
    ),
    DiscoverSubject(
        id="schloss_babelsberg",
        name="Schloss Babelsberg",
        kategorie="🏰 Schloss",
        lat=52.3987, lon=13.1095,
        structure_height_m=27.0,
        terrain_offset_m=4.0,    # Hang über Tiefer See ~39m NN
        subject_width_m=40.0,
        hoehe_confidence="hoch",
    ),
    DiscoverSubject(
        id="nikolaikirche_potsdam",
        name="Nikolaikirche Potsdam",
        kategorie="⛪ Kirche",
        lat=52.3997, lon=13.0596,
        structure_height_m=94.0,
        terrain_offset_m=0.0,    # Stadtmitte Potsdam ~35m NN
        subject_width_m=45.0,
        hoehe_confidence="hoch",
    ),
    DiscoverSubject(
        id="biosphaere_potsdam",
        name="Biosphäre Potsdam",
        kategorie="🌿 Gebäude",
        lat=52.3923, lon=13.0759,
        structure_height_m=30.0,
        terrain_offset_m=0.0,
        subject_width_m=80.0,
        hoehe_confidence="hoch",
    ),
    DiscoverSubject(
        id="garnisonkirche_potsdam",
        name="Garnisonkirche Potsdam",
        kategorie="⛪ Kirche",
        lat=52.3992, lon=13.0643,
        structure_height_m=88.0,   # Geplante Wiederherstellung historische Höhe
        terrain_offset_m=0.0,
        subject_width_m=25.0,
        hoehe_confidence="niedrig",  # Wiederaufbau noch nicht vollständig
    ),
]

# Index für schnellen Zugriff
SUBJECT_BY_ID: dict[str, DiscoverSubject] = {s.id: s for s in SUBJECTS}
