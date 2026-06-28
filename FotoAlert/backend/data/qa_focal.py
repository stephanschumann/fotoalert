"""
FotoAlert – Auto-Ableitung der Brennweiten-Empfehlung (TASK-47)

Leitet für Locations ohne kuratierte Brennweiten-Empfehlung automatisch eine
passende Objektiv-Brennweite ab — aus Motivhöhe und Entfernung.

Strategie (Option A — bestehende Geometrie wiederverwenden):
  • Nutzt exakt dieselbe Rechnung wie der Laufzeit-Fallback im Chancen-Code
    (`calculations.opportunity._focal_for_location`): die verifizierte Geometrie
    `calculate_focal_length_for_subject(höhe, entfernung, frame_fill=0.25)` und
    die bekannte Brennweiten-Staffel `_FOCAL_STEPS`. Ein Rechenweg, ein
    Verhalten — Auto-Wert und Live-Fallback driften nicht auseinander.
  • **Eine** gerasterte Empfehlung (Annahme A2): das Ergebnis ist eine
    einelementige Liste, z.B. [135].
  • **0-Guard (Annahme A1/A3, Pre-Mortem):** Die Standalone-Geometrie hat keinen
    eigenen Schutz gegen Division durch null. Dieses Modul prüft Höhe > 0 und
    Entfernung > 0, BEVOR es rechnet — fehlt etwas oder ist die Entfernung 0,
    wird nichts berechnet und nichts geschrieben (None), niemals ein Crash.
  • **Still degradierend:** Fehlende Daten → None, keine Exception nach außen.

Schreib-Regel (kompatibel zum Azimut-Muster, TASK-45):
  • Schreibt nur, wenn das focal_length_lock NICHT gesetzt ist UND noch keine
    kuratierte Empfehlungs-Liste vorliegt — der Auto-Wert drängt sich nie
    zwischen gepflegte/gesperrte Werte.

Konvention: Vollformat (36 mm Sensorbreite) und Meter — unverändert aus dem
Bestand übernommen.

Python-3.9-kompatibel.
"""

from __future__ import annotations

import logging
from typing import List, Optional

from calculations.astronomy import calculate_focal_length_for_subject
from calculations.opportunity import _FOCAL_STEPS

logger = logging.getLogger(__name__)

# Bildfüllung wie der bestehende Location-Fallback (Annahme A3), damit Auto-Wert
# und Laufzeit-Fallback identische Zahlen ergeben.
DEFAULT_FRAME_FILL_PCT: float = 0.25


def _snap_to_steps(raw_mm: float) -> int:
    """Rastert eine rohe Brennweite auf die bekannte Staffel (_FOCAL_STEPS).

    Begrenzt damit auch absurd lange Werte (Mini-Entfernung / Riesen-Motiv) auf
    das sinnvolle Raster — der nächstgelegene Wert gewinnt, das Maximum der
    Staffel ist die Obergrenze.
    """
    return min(_FOCAL_STEPS, key=lambda step: abs(step - raw_mm))


def compute_focal_suggestion(
    subject_height_m: Optional[float],
    distance_m: Optional[float],
    frame_fill_pct: float = DEFAULT_FRAME_FILL_PCT,
) -> Optional[List[int]]:
    """Leitet aus Motivhöhe und Entfernung eine gerasterte Brennweite ab.

    - Fehlt Höhe ODER Entfernung, oder ist eine davon <= 0 → None (kein Wert,
      kein Schreiben, kein Zufallswert). Schützt vor Division durch null.
    - Sonst: bestehende Geometrie (25 % Bildfüllung) → Rasterung auf
      `_FOCAL_STEPS`. Ergebnis ist eine einelementige Liste (Annahme A2).

    Deterministisch. Gibt nie eine Exception nach außen.
    """
    if subject_height_m is None or distance_m is None:
        return None
    if subject_height_m <= 0 or distance_m <= 0:
        return None

    raw = calculate_focal_length_for_subject(
        subject_height_m,
        distance_m,
        desired_frame_fill_pct=frame_fill_pct,
    )
    return [_snap_to_steps(raw)]


def update_location_focal(
    store,
    location_id: str,
    subject_height_m: Optional[float],
    distance_m: Optional[float],
    frame_fill_pct: float = DEFAULT_FRAME_FILL_PCT,
) -> Optional[List[int]]:
    """Berechnet die Brennweiten-Empfehlung und schreibt sie in die QA-Werte.

    Respektiert focal_length_lock und eine bereits vorhandene kuratierte Liste:
    - Ist das Lock gesetzt → nichts schreiben, gesperrter Bestand bleibt.
    - Liegt schon eine kuratierte focal_length_suggestions-Liste vor → nichts
      schreiben, der Auto-Wert drängt sich nicht dazwischen.

    Rückgabe:
      - [mm]: geschriebene, gerasterte Empfehlung (einelementige Liste)
      - None: nichts geschrieben (Lock ODER kuratierte Liste ODER fehlende/
        ungültige Daten). In keinem Fall fliegt eine Exception.
    """
    state = store.get_qa_state(location_id)
    if state and state.get("focal_length_lock"):
        logger.info("Brennweite für %s gesperrt — kein Auto-Update", location_id)
        return None

    existing = store.get_qa_values(location_id)
    if existing and existing.get("focal_length_suggestions"):
        logger.info(
            "Brennweite für %s bereits kuratiert — kein Auto-Update", location_id
        )
        return None

    suggestion = compute_focal_suggestion(
        subject_height_m, distance_m, frame_fill_pct=frame_fill_pct
    )
    if suggestion is None:
        return None

    store.set_qa_values(location_id, focal_length_suggestions=suggestion)
    return suggestion
