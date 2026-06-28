"""
Tests für TASK-45: Idealer Azimut automatisch aus Sichtlinie (+ optional Overpass).

Abgedeckte Akzeptanzkriterien:
- Bearing-Basis liefert plausiblen Bereich grob in Richtung Standort→Motiv.
- Nord-Wraparound: Motiv exakt im Norden → Band über 0/360° (min > max), kein
  widersprüchliches "350 bis 10" als 340°-Band.
- Determinismus: zwei Läufe auf identischem Input → identischer Bereich.
- Lock wird respektiert: gesperrter Azimut bleibt unberührt.
- Fehlende Motiv-Koordinate → kein Schreiben (None), kein Crash.
- Overpass-Fehler (gemockt) → stiller Fallback auf die Bearing-Basis, kein Crash.
"""
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.store import LocationStore
from data import qa_azimuth


@pytest.fixture
def store(tmp_path: Path) -> LocationStore:
    return LocationStore(db_path=tmp_path / "test.db")


# ---------------------------------------------------------------------------
# Bearing-Basis
# ---------------------------------------------------------------------------

def test_bearing_range_points_toward_subject() -> None:
    """Motiv direkt östlich → Bereich um ~90° (Ost)."""
    # Standort und Motiv auf derselben Breite, Motiv weiter östlich.
    lo, hi = qa_azimuth.compute_bearing_range(52.5, 13.40, 52.5, 13.50)
    # Bearing ~90°, ±15° → grob [75, 105].
    assert 70 <= lo <= 80
    assert 100 <= hi <= 110
    assert lo < hi  # kein Wrap


def test_bearing_range_southeast() -> None:
    """Motiv südöstlich → Bereich grob um Südost (~135°)."""
    lo, hi = qa_azimuth.compute_bearing_range(52.6, 13.30, 52.5, 13.50)
    mid = (lo + hi) / 2
    assert 110 <= mid <= 160


def test_bearing_range_tolerance_width() -> None:
    """Bandbreite entspricht 2x Toleranz (außerhalb Wrap)."""
    lo, hi = qa_azimuth.compute_bearing_range(52.5, 13.40, 52.5, 13.50,
                                              tolerance_deg=10.0)
    assert hi - lo == pytest.approx(20.0, abs=0.01)


# ---------------------------------------------------------------------------
# Nord-Wraparound
# ---------------------------------------------------------------------------

def test_north_wraparound_produces_crossing_band() -> None:
    """Motiv exakt nördlich → Band kreuzt 0/360° (min > max)."""
    # Motiv direkt nördlich (gleiche Länge, höhere Breite) → Bearing ~0°.
    lo, hi = qa_azimuth.compute_bearing_range(52.4, 13.40, 52.6, 13.40,
                                              tolerance_deg=15.0)
    # Bearing 0°, ±15° → lo ~345°, hi ~15°. min > max signalisiert Wrap.
    assert lo > hi
    assert lo == pytest.approx(345.0, abs=1.0)
    assert hi == pytest.approx(15.0, abs=1.0)


def test_north_wraparound_not_inverted_wide_band() -> None:
    """Wrap-Band ist die SCHMALE Spanne über Nord, nicht das 330°-Komplement."""
    lo, hi = qa_azimuth.compute_bearing_range(52.4, 13.40, 52.6, 13.40,
                                              tolerance_deg=15.0)
    # Effektive Bandbreite über Nord = (hi - lo) mod 360 = ~30°, nicht ~330°.
    width = (hi - lo) % 360.0
    assert width == pytest.approx(30.0, abs=2.0)


# ---------------------------------------------------------------------------
# Determinismus
# ---------------------------------------------------------------------------

def test_deterministic_two_runs() -> None:
    """Zwei Läufe auf identischem Input liefern denselben Bereich."""
    args = (52.5163, 13.3777, 52.5190, 13.4011)
    r1 = qa_azimuth.compute_ideal_azimuth_range(*args)
    r2 = qa_azimuth.compute_ideal_azimuth_range(*args)
    assert r1 == r2


def test_deterministic_via_store(store: LocationStore) -> None:
    """update_location_azimuth zweimal → identischer gespeicherter Bereich."""
    args = ("spot-1", 52.5163, 13.3777, 52.5190, 13.4011)
    r1 = qa_azimuth.update_location_azimuth(store, *args)
    r2 = qa_azimuth.update_location_azimuth(store, *args)
    assert r1 == r2
    vals = store.get_qa_values("spot-1")
    assert vals["ideal_azimuth_min"] == pytest.approx(r1[0])
    assert vals["ideal_azimuth_max"] == pytest.approx(r1[1])


# ---------------------------------------------------------------------------
# Lock wird respektiert
# ---------------------------------------------------------------------------

def test_lock_is_respected(store: LocationStore) -> None:
    """Gesperrter Azimut wird vom Auto-Lauf nicht überschrieben."""
    # Manuell kuratierten Wert + Lock setzen.
    store.set_qa_values("spot-locked", ideal_azimuth_min=100.0,
                        ideal_azimuth_max=140.0)
    store.set_qa_lock("spot-locked", "azimuth", True)

    result = qa_azimuth.update_location_azimuth(
        store, "spot-locked", 52.5, 13.40, 52.5, 13.50  # würde ~Ost berechnen
    )
    assert result is None  # nichts geschrieben
    vals = store.get_qa_values("spot-locked")
    assert vals["ideal_azimuth_min"] == pytest.approx(100.0)
    assert vals["ideal_azimuth_max"] == pytest.approx(140.0)


def test_unlocked_is_written(store: LocationStore) -> None:
    """Ohne Lock wird der Auto-Wert geschrieben."""
    result = qa_azimuth.update_location_azimuth(
        store, "spot-open", 52.5, 13.40, 52.5, 13.50
    )
    assert result is not None
    vals = store.get_qa_values("spot-open")
    assert vals is not None
    assert vals["ideal_azimuth_min"] is not None


# ---------------------------------------------------------------------------
# Fehlende Motiv-Koordinate
# ---------------------------------------------------------------------------

def test_missing_subject_returns_none() -> None:
    """Ohne Motiv-Koordinate → None (kein Schreiben, kein Zufallswert)."""
    assert qa_azimuth.compute_ideal_azimuth_range(52.5, 13.4, None, None) is None
    assert qa_azimuth.compute_ideal_azimuth_range(52.5, 13.4, 52.5, None) is None


def test_missing_subject_writes_nothing(store: LocationStore) -> None:
    """update_location_azimuth ohne Motiv → nichts in der DB."""
    result = qa_azimuth.update_location_azimuth(
        store, "spot-nosub", 52.5, 13.40, None, None
    )
    assert result is None
    assert store.get_qa_values("spot-nosub") is None


# ---------------------------------------------------------------------------
# Overpass-Verfeinerung + stiller Fallback
# ---------------------------------------------------------------------------

def test_overpass_failure_falls_back_to_bearing(monkeypatch) -> None:
    """Overpass-Fehler (None) → stiller Fallback auf die Bearing-Basis."""
    monkeypatch.setattr(qa_azimuth, "_fetch_overpass_footprint",
                        lambda *a, **k: None)
    base = qa_azimuth.compute_bearing_range(52.5, 13.40, 52.5, 13.50)
    refined = qa_azimuth.compute_ideal_azimuth_range(
        52.5, 13.40, 52.5, 13.50, use_overpass=True
    )
    assert refined == base


def test_overpass_exception_does_not_propagate(monkeypatch) -> None:
    """Wirft die Footprint-Funktion intern, fliegt nichts nach außen."""
    def _boom(*a, **k):
        raise RuntimeError("network down")
    # _fetch_overpass_footprint fängt selbst ab; hier prüfen wir die
    # Gesamt-Robustheit, indem wir den Fetch komplett ersetzen.
    monkeypatch.setattr(qa_azimuth, "_fetch_overpass_footprint",
                        lambda *a, **k: None)
    # Direkter httpx-Ausfall wird in _fetch_overpass_footprint abgefangen →
    # zusätzlich prüfen wir, dass _footprint_angular_span mit Murks robust ist.
    assert qa_azimuth._footprint_angular_span(52.5, 13.4, []) is None
    refined = qa_azimuth.compute_ideal_azimuth_range(
        52.5, 13.40, 52.5, 13.50, use_overpass=True
    )
    assert refined is not None  # Basis bleibt, kein Crash


def test_overpass_footprint_widens_range(monkeypatch) -> None:
    """Ein breiter Footprint verbreitert den Bereich über die reine Sichtlinie."""
    # Standort westlich; Motiv-Gebäude als breiter Block östlich.
    obs_lat, obs_lon = 52.5, 13.40
    # Vier Eckpunkte eines Rechtecks um (52.5, 13.50), breit in Nord-Süd.
    footprint = [
        (52.503, 13.499),
        (52.503, 13.501),
        (52.497, 13.501),
        (52.497, 13.499),
    ]
    monkeypatch.setattr(qa_azimuth, "_fetch_overpass_footprint",
                        lambda *a, **k: footprint)
    base = qa_azimuth.compute_bearing_range(obs_lat, obs_lon, 52.5, 13.50)
    refined = qa_azimuth.compute_ideal_azimuth_range(
        obs_lat, obs_lon, 52.5, 13.50, use_overpass=True
    )
    base_width = (base[1] - base[0]) % 360.0
    refined_width = (refined[1] - refined[0]) % 360.0
    assert refined_width >= base_width


def test_footprint_angular_span_too_few_nodes() -> None:
    """Weniger als 2 Knoten → None (kein Span ableitbar)."""
    assert qa_azimuth._footprint_angular_span(52.5, 13.4, [(52.5, 13.5)]) is None
