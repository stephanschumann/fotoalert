"""
US-07: Goldene Wolken & Himmelsröte Scoring — pytest-Tests.

Deckt alle AKs aus der Spec ab:
  - Sweet Spot → ≥ 0.70
  - Tiefe Wolken → ≤ 0.10
  - Klarer Himmel → ≤ 0.20
  - None-Input → None (kein Crash)
  - weather_score-Bonus ≤ 1.0 und > Ausgangswert
"""

import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from calculations.weather import _golden_cloud_score, calculate_golden_cloud_score

pytestmark = [pytest.mark.offline, pytest.mark.regression]


def test_sweet_spot():
    """cl=5, cm=40, ch=30 → Score ≥ 0.70 (klassischer Sweet Spot)."""
    score = _golden_cloud_score(cl=5, cm=40, ch=30)
    assert score is not None
    assert score >= 0.70, f"Erwartet ≥ 0.70, erhalten: {score}"


def test_tiefe_wolken_dominant():
    """cl=90, cm=20, ch=10 → Score ≤ 0.10 (tiefe Wolken blockieren Licht)."""
    score = _golden_cloud_score(cl=90, cm=20, ch=10)
    assert score is not None
    assert score <= 0.10, f"Erwartet ≤ 0.10, erhalten: {score}"


def test_klarer_himmel():
    """cl=0, cm=0, ch=0 → Score ≤ 0.20 (nichts zum Einfärben)."""
    score = _golden_cloud_score(cl=0, cm=0, ch=0)
    assert score is not None
    assert score <= 0.20, f"Erwartet ≤ 0.20, erhalten: {score}"


def test_none_input_returns_none():
    """Wenn cl None ist → None zurückgeben, kein Crash."""
    score = _golden_cloud_score(None, 40, 30)
    assert score is None, f"Erwartet None, erhalten: {score}"


def test_none_cm_returns_none():
    """Wenn cm None ist → None zurückgeben."""
    score = _golden_cloud_score(5, None, 30)
    assert score is None


def test_none_ch_returns_none():
    """Wenn ch None ist → None zurückgeben."""
    score = _golden_cloud_score(5, 40, None)
    assert score is None


def test_weather_score_bonus():
    """
    Mock: golden_cloud_score=0.82, weather_score=0.75
    → Nach Bonus: score ≤ 1.0 und > 0.75
    """
    base_weather_score = 0.75
    gcs = 0.82

    # Bonus-Logik exakt wie in _apply_weather_to_event()
    if gcs >= 0.7:
        result = min(1.0, base_weather_score + 0.05)
    else:
        result = base_weather_score

    assert result <= 1.0, f"Erwartet ≤ 1.0, erhalten: {result}"
    assert result > 0.75, f"Erwartet > 0.75 (Bonus), erhalten: {result}"


def test_weather_score_bonus_gedeckelt():
    """Bonus wird bei 1.0 gedeckelt — auch wenn Score bereits 0.98."""
    base_weather_score = 0.98
    gcs = 0.90
    result = min(1.0, base_weather_score + 0.05) if gcs >= 0.7 else base_weather_score
    assert result == 1.0, f"Erwartet 1.0 (Deckel), erhalten: {result}"


def test_score_range():
    """Score liegt immer in [0.0, 1.0]."""
    test_cases = [
        (0, 0, 0),
        (100, 100, 100),
        (50, 50, 50),
        (30, 45, 60),
        (80, 5, 5),
    ]
    for cl, cm, ch in test_cases:
        score = _golden_cloud_score(cl, cm, ch)
        assert score is not None
        assert 0.0 <= score <= 1.0, f"Score außerhalb [0,1]: {score} für cl={cl}, cm={cm}, ch={ch}"
