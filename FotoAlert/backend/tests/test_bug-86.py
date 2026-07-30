"""BUG-86 — Mondphasen-Bezeichnung passt nicht zum Beleuchtungsgrad
(z.B. "Halbmond" bei 96-99% Beleuchtung statt der für "Halbmond" erwarteten
~50%).

Root Cause (siehe BACKLOG.md BUG-86, "Code-Verifikation" / verifiziert gegen
docs/2026-07-27-fix-vorschlaege-audit-befunde.md, Befund 3):
`backend/calculations/astronomy.py`, `_moon_phase_name()`, Zeilen 250-266.
Die BUCKET-GRENZEN selbst (0.22/0.28/0.47/0.53/0.72/0.78) sind korrekt und
lückenlos -- falsch sind zwei BUCKET-NAMEN: das Bucket `fraction` 0.28-0.47
(astronomisch der zunehmende Dreiviertelmond, Beleuchtung ~59-99%) heisst
"Zunehmender Halbmond", und das spiegelbildliche Bucket 0.53-0.72 (Beleuchtung
~59-99%, abnehmend) heisst "Abnehmender Halbmond". Der tatsaechliche Halbmond
(50% Beleuchtung, fraction=0.25/0.75) liegt bereits in den korrekt benannten
Buckets "Erstes Viertel" / "Letztes Viertel".

Fix laut Audit-Dokument: nur die zwei Bucket-NAMEN aendern (Grenzen bleiben):
  - "Zunehmender Halbmond" -> "Zunehmender Dreiviertelmond"
  - "Abnehmender Halbmond" -> "Abnehmender Dreiviertelmond"

Einzige Stelle im Backend, die Phasennamen vergibt (Fundstellen-Sweep: Grep
nach `_moon_phase_name`/`phase_name`/`moon_phase` in backend/ und
web/index.html -- main.py, precompute.py und web/index.html reichen den
fertigen String nur durch, keine eigene Label-Logik).

Beleuchtungsformel repliziert aus `calculate_moon_info()`
(astronomy.py Zeile ~404-407), da dort inline berechnet und nicht als eigene
Funktion exportiert:
    elongation = (fraction * 360.0) % 360.0
    illumination = (1 - cos(radians(elongation))) / 2 * 100

Testmuster (Vorbild): die bestehende Plausibilitaets-Assertion fuer die
Erde-Mond-Distanz in `get_moon_earth_distance_km()`, Zeile ~214
(`assert 350_000 < dist_km < 410_000, ...`) -- hier uebertragen auf
"passt der Phasenname zum Beleuchtungsgrad".
"""
from __future__ import annotations

import math

import pytest

from calculations.astronomy import _moon_phase_name

pytestmark = [pytest.mark.offline, pytest.mark.regression]


def illumination_for_fraction(fraction: float) -> float:
    """Repliziert die Beleuchtungsformel aus calculate_moon_info() (astronomy.py
    Zeile ~407) -- dort inline berechnet, hier fuer Testzwecke nachgebildet."""
    elongation = (fraction * 360.0) % 360.0
    return (1 - math.cos(math.radians(elongation))) / 2 * 100


# Erwartete Beleuchtungs-Plausibilitaetsspannen je Phasenname NACH dem Fix
# (Audit-Dokument Befund 3). Ein Name, der hier nicht auftaucht (z.B. die
# aktuellen falschen "Halbmond"-Bucket-Namen), macht den Sweep-Test unten
# fehlschlagen -- das ist der gewuenschte Rot-Zustand vor dem Fix.
PLAUSIBLE_ILLUMINATION_RANGES = {
    "Neumond": (0, 2),
    "Zunehmende Sichel": (0, 42),
    "Erstes Viertel": (38, 62),
    "Zunehmender Dreiviertelmond": (55, 100),
    "Vollmond": (97, 100),
    "Abnehmender Dreiviertelmond": (55, 100),
    "Letztes Viertel": (38, 62),
    "Abnehmende Sichel": (0, 42),
}


class TestKonkreteBugReproduktion:
    """Reproduziert die im Ticket beschriebenen konkreten Beobachtungswerte."""

    def test_97_prozent_beleuchtung_ist_kein_halbmond(self):
        """fraction=0.45 -> Beleuchtung ~97.5% (entspricht dem im Ticket
        beschriebenen Bereich "96-99%"). Aktueller Code liefert faelschlich
        "Zunehmender Halbmond" -- ein Halbmond hat per Definition ~50%
        Beleuchtung, nicht ~97%."""
        fraction = 0.45
        illum = illumination_for_fraction(fraction)
        assert 96 <= illum <= 99, f"Testannahme verletzt: illum={illum:.1f}%"

        name = _moon_phase_name(fraction)
        assert "Halbmond" not in name, (
            f"_moon_phase_name({fraction}) liefert '{name}' bei {illum:.1f}% "
            f"Beleuchtung -- 'Halbmond' impliziert ~50%, nicht ~97%."
        )

    def test_90_prozent_beleuchtung_abnehmend_ist_kein_halbmond(self):
        """Spiegelbildliches Bucket auf der abnehmenden Seite (fraction=0.60,
        Beleuchtung ~90%). Aktueller Code liefert faelschlich
        "Abnehmender Halbmond"."""
        fraction = 0.60
        illum = illumination_for_fraction(fraction)
        assert 88 <= illum <= 92, f"Testannahme verletzt: illum={illum:.1f}%"

        name = _moon_phase_name(fraction)
        assert "Halbmond" not in name, (
            f"_moon_phase_name({fraction}) liefert '{name}' bei {illum:.1f}% "
            f"Beleuchtung -- 'Halbmond' impliziert ~50%, nicht ~90%."
        )


class TestEchterHalbmondBleibtKorrekt:
    """Regressionsschutz: die bereits korrekt benannten ~50%-Buckets duerfen
    durch den Fix nicht verschoben werden."""

    @pytest.mark.parametrize("fraction,expected_name", [
        (0.25, "Erstes Viertel"),   # zunehmender Halbmond, exakt 90 Grad Elongation
        (0.75, "Letztes Viertel"),  # abnehmender Halbmond, exakt 270 Grad Elongation
    ])
    def test_tatsaechlicher_halbmond_hat_ca_50_prozent_und_richtigen_namen(self, fraction, expected_name):
        illum = illumination_for_fraction(fraction)
        assert 45 <= illum <= 55, f"Testannahme verletzt: illum={illum:.1f}%"
        assert _moon_phase_name(fraction) == expected_name

    def test_vollmond_bleibt_vollmond(self):
        fraction = 0.5
        illum = illumination_for_fraction(fraction)
        assert illum > 99
        assert _moon_phase_name(fraction) == "Vollmond"

    def test_neumond_bleibt_neumond(self):
        illum = illumination_for_fraction(0.0)
        assert illum < 1
        assert _moon_phase_name(0.0) == "Neumond"


class TestPhasennameGegenBeleuchtungPlausibel:
    """Systemischer Test (im Ticket gefordert): Phasenname wird ueber den
    gesamten Wertebereich von `fraction` gegen den tatsaechlichen
    Beleuchtungsgrad plausibilisiert -- Vorbild: die Distanz-Assertion in
    get_moon_earth_distance_km() (astronomy.py Zeile ~214)."""

    def test_alle_bucket_grenzen_liefern_einen_bekannten_plausiblen_namen(self):
        unerwartet = []
        # Feine Abtastung ueber den vollen fraction-Bereich inkl. der exakten
        # Bucket-Grenzwerte (0.22/0.28/0.47/0.53/0.72/0.78/0.03/0.97).
        steps = [i / 1000 for i in range(0, 1000)]
        for fraction in steps:
            name = _moon_phase_name(fraction)
            illum = illumination_for_fraction(fraction)

            if name not in PLAUSIBLE_ILLUMINATION_RANGES:
                unerwartet.append(
                    f"fraction={fraction:.3f} illum={illum:.1f}% -> unbekannter/"
                    f"unplausibler Name '{name}'"
                )
                continue

            low, high = PLAUSIBLE_ILLUMINATION_RANGES[name]
            if not (low <= illum <= high):
                unerwartet.append(
                    f"fraction={fraction:.3f} illum={illum:.1f}% -> Name '{name}' "
                    f"erwartet Beleuchtung {low}-{high}%"
                )

        assert not unerwartet, (
            "Phasenname passt an folgenden Stellen nicht zum Beleuchtungsgrad:\n"
            + "\n".join(unerwartet[:10])
            + (f"\n... ({len(unerwartet)} Treffer insgesamt)" if len(unerwartet) > 10 else "")
        )
