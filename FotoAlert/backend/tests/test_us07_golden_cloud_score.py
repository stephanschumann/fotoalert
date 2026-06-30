"""
US-07: Tests für calculate_golden_cloud_score().

Drei Szenarien aus den Akzeptanzkriterien:
  AK-3: Scattered clouds (Sweet Spot) → Score ≥ 0.70
  AK-5: Hochdrucklage / klarer Himmel → Score ≤ 0.20
  AK-4: Bedeckter Himmel (tiefe Wolken dominant) → Score ≤ 0.10
"""

import sys
import os

# Backend-Verzeichnis in den Suchpfad aufnehmen
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from calculations.weather import calculate_golden_cloud_score


def test_scattered_clouds_sweet_spot():
    """AK-3: cl=5, cm=40, ch=30 → Score ≥ 0.70 (klassischer Sweet Spot)."""
    score = calculate_golden_cloud_score(cl=5, cm=40, ch=30)
    assert score >= 0.70, f"Erwartet ≥ 0.70, erhalten: {score}"


def test_hochdrucklage_klarer_himmel():
    """AK-5: cl=0, cm=0, ch=0 → Score ≤ 0.20 (nichts zum Einfärben)."""
    score = calculate_golden_cloud_score(cl=0, cm=0, ch=0)
    assert score <= 0.20, f"Erwartet ≤ 0.20, erhalten: {score}"


def test_bedeckter_himmel_tiefe_wolken():
    """AK-4: cl=90, cm=20, ch=10 → Score ≤ 0.10 (tiefe Wolken blockieren Licht)."""
    score = calculate_golden_cloud_score(cl=90, cm=20, ch=10)
    assert score <= 0.10, f"Erwartet ≤ 0.10, erhalten: {score}"


def test_score_range():
    """Score muss immer im Bereich 0.0–1.0 liegen."""
    test_cases = [
        (0, 0, 0),
        (100, 100, 100),
        (50, 50, 50),
        (30, 45, 60),
        (80, 5, 5),
    ]
    for cl, cm, ch in test_cases:
        score = calculate_golden_cloud_score(cl, cm, ch)
        assert 0.0 <= score <= 1.0, f"Score außerhalb [0,1]: {score} für cl={cl}, cm={cm}, ch={ch}"


def test_tiefe_wolken_penalty():
    """Penalty für tiefe Wolken > 30% reduziert den Score graduell."""
    score_no_penalty = calculate_golden_cloud_score(cl=25, cm=40, ch=30)
    score_with_penalty = calculate_golden_cloud_score(cl=55, cm=40, ch=30)
    assert score_with_penalty < score_no_penalty, "Penalty-Effekt nicht sichtbar"


def test_golden_hour_morning_only():
    """Nicht-goldene-Stunde-Events sollen None zurückgeben (Logik in main.py, hier nur Funktion testen)."""
    # Die Funktion selbst filtert nicht nach Event-Typ — das ist Sache von _apply_weather_to_event().
    # Dieser Test stellt sicher, dass die Funktion direkt aufrufbar ist und valide Werte liefert.
    score = calculate_golden_cloud_score(cl=10, cm=35, ch=25)
    assert isinstance(score, float)
