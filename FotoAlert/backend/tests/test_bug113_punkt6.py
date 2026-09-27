"""BUG-113 Nachbesserung Punkt 6 (gate-auditor 2026-09-19, Freigabe Stephan 2026-09-27):
Scheitert nur das Schreiben der kleinen Übergabedatei, ist der Kalender trotzdem
korrekt berechnet und geschrieben. Das Protokoll muss das ehrlich sagen — statt
„Kalenderberechnung fehlgeschlagen" zu melden und die Erfolgszeile zu verschlucken.

Offline: keine Berechnung, kein Netz, keine großen Dateien.
"""
import asyncio
import logging
from datetime import date

import pytest

import precompute

pytestmark = [pytest.mark.offline, pytest.mark.regression]


def _lauf(monkeypatch, tmp_path, caplog, *, kalender_fehler=False, postfach_fehler=False):
    geschrieben = []

    async def fake_incremental(today, location_id=None):
        if kalender_fehler:
            raise RuntimeError("Kalender kaputt (Test)")
        return [{"location_id": location_id, "shoot_time": "2026-10-01T05:00:00+00:00"}], {}

    def fake_write_cache(path, calendar, meta, computed_at):
        geschrieben.append(path)

    def fake_delta(cal_path, location_id, calendar, computed_at):
        if postfach_fehler:
            raise OSError("Platte voll (Test)")
        return len(calendar)

    monkeypatch.setattr(precompute, "compute_calendar_incremental", fake_incremental)
    monkeypatch.setattr(precompute, "_write_calendar_cache", fake_write_cache)
    monkeypatch.setattr(precompute, "_write_calendar_single_delta", fake_delta)
    monkeypatch.setattr(precompute, "CACHE_DIR", tmp_path)
    with caplog.at_level(logging.INFO):
        asyncio.run(precompute._refresh_single_location_calendar(
            "loc_p6", date(2026, 10, 1), "2026-10-01T00:00:00+00:00"))
    return geschrieben, caplog.text


def test_postfach_fehler_meldet_nicht_kalender_fehlgeschlagen(monkeypatch, tmp_path, caplog):
    geschrieben, log = _lauf(monkeypatch, tmp_path, caplog, postfach_fehler=True)
    assert geschrieben, "calendar.json muss trotzdem geschrieben worden sein"
    assert "Kalenderberechnung fehlgeschlagen" not in log
    assert "✅ Kalender" in log, "Erfolgszeile für den Kalender fehlt"
    assert "Übergabedatei" in log and "nicht geschrieben" in log, "ehrliche Warnung zum Postfach fehlt"


def test_echter_kalender_fehler_wird_weiter_als_fehlgeschlagen_gemeldet(monkeypatch, tmp_path, caplog):
    geschrieben, log = _lauf(monkeypatch, tmp_path, caplog, kalender_fehler=True)
    assert not geschrieben
    assert "Kalenderberechnung fehlgeschlagen" in log
    assert "✅ Kalender" not in log


def test_normalfall_ohne_warnung(monkeypatch, tmp_path, caplog):
    geschrieben, log = _lauf(monkeypatch, tmp_path, caplog)
    assert geschrieben
    assert "✅ Kalender" in log
    assert "nicht geschrieben" not in log and "fehlgeschlagen" not in log
