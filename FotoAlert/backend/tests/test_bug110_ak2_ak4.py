"""BUG-110 -- Ergaenzung zu test_bug110.py: AK-2 (Sammel-Fehlerlog bei Totalausfall)
und AK-4 (echt leerer Monat wird genau einmal berechnet und dann gecacht)."""
from __future__ import annotations

import asyncio
import logging

import pytest

_Y, _M = 2026, 8


@pytest.fixture(autouse=True)
def _clear_cache():
    import main
    main._ondemand_month_cache.clear()
    yield
    main._ondemand_month_cache.clear()


@pytest.mark.offline
@pytest.mark.regression
class TestBug110Ak2Ak4:
    def test_total_failure_logs_one_summary_error(self, monkeypatch, caplog):
        """AK-2: Fallen alle Orte aus, gibt es zusaetzlich einen zusammenfassenden Eintrag."""
        import main

        async def _failing(loc, year, month, min_score):
            raise RuntimeError("BUG-110-Testfehler")

        monkeypatch.setattr(main, "_compute_location_month", _failing)
        with caplog.at_level(logging.ERROR):
            asyncio.run(main._compute_month_all_locations(_Y, _M))
        summary = [r for r in caplog.records if "ALLE" in r.getMessage() and "fehlgeschlagen" in r.getMessage()]
        assert len(summary) == 1

    def test_genuinely_empty_month_is_computed_once_then_cached(self, monkeypatch, caplog):
        """AK-4: Kein Fehler, aber 0 Events -> nur ein Rechenlauf, danach aus dem Cache,
        und kein Sammel-Fehlereintrag."""
        import main
        calls = {"n": 0}

        async def _empty(loc, year, month, min_score):
            calls["n"] += 1
            return []

        monkeypatch.setattr(main, "_compute_location_month", _empty)
        with caplog.at_level(logging.ERROR):
            asyncio.run(main._compute_month_all_locations(_Y, _M))
            after_first = calls["n"]
            asyncio.run(main._compute_month_all_locations(_Y, _M))
        assert after_first > 0
        assert calls["n"] == after_first, "Zweiter Aufruf darf nicht erneut rechnen."
        assert not [r for r in caplog.records if "ALLE" in r.getMessage()]
