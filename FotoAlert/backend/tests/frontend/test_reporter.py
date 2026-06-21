"""TASK-20 — Reporter-Selbsttests (Marker frontend), laufen OHNE Browser.

Decken die pure-Python-Akzeptanzkriterien ab:
  - AK5: Dedup-Idempotenz (2 identische Läufe ⇒ 1 Ticket, kein Duplikat).
  - AK6: Bug-Feld-Vollständigkeit (alle Pflichtfelder gerendert).
  - AK7: Grün-Lauf ohne Schreibvorgang (kein findings.json, kein BACKLOG-Schreiben).
  - AK9 / Pre-Mortem: Fingerprint-Stabilität gegen volatile Felder.

Operiert IMMER auf einer temporären BACKLOG-Testkopie (tmp_path), nie auf der echten
Datei. Browser-Tests (run_frontend_check) sind hier bewusst nicht enthalten.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import reporter as R  # noqa: E402

pytestmark = [pytest.mark.frontend, pytest.mark.regression]


# --- Fixtures ----------------------------------------------------------------------
_BACKLOG_TEMPLATE = """# BACKLOG

## 📥 Inbox

(leer)

## Ready for Analysis

### TASK-99 · Beispiel  `[ ]`
"""


def _make_finding(actual="Selektor nicht gefunden: #map", ts="2026-06-20T10:00:00Z",
                  sha="abc123", shot="docs/qa-screenshots/run1/map.png"):
    return R.Finding(
        view="map",
        assertion_id="required_element",
        expected="Pflicht-Element vorhanden: #map .leaflet-container",
        actual=actual,
        message="missing required selector #map .leaflet-container in view map",
        screenshot_path=shot,
        timestamp=ts,
        commit_sha=sha,
    )


@pytest.fixture
def backlog_copy(tmp_path):
    """Temporäre BACKLOG-Kopie — niemals die echte Datei."""
    p = tmp_path / "BACKLOG_test.md"
    p.write_text(_BACKLOG_TEMPLATE, encoding="utf-8")
    return p


# --- Fingerprint-Stabilität (Pre-Mortem / AK5-Grundlage) ---------------------------
class TestFingerprint:
    def test_stable_across_volatile_fields(self):
        # Gleiche Aussage, andere Koordinaten/Timestamp/SHA → gleicher Fingerprint.
        f1 = _make_finding(actual="erwartet 52.5163, war 13.3777", ts="2026-06-20T10:00:00Z", sha="aaa")
        f2 = _make_finding(actual="erwartet 48.1351, war 11.5820", ts="2026-06-21T23:59:00Z", sha="bbb")
        assert f1.fingerprint == f2.fingerprint

    def test_differs_on_view_or_assertion(self):
        base = R.compute_fingerprint("map", "required_element", "missing #map")
        assert base != R.compute_fingerprint("feed", "required_element", "missing #map")
        assert base != R.compute_fingerprint("map", "view_active", "missing #map")

    def test_normalize_strips_numbers(self):
        a = R.normalize_message("missing at 52.5163,13.3777")
        b = R.normalize_message("missing at 48.1,11.5")
        assert a == b


# --- AK6: Bug-Feld-Vollständigkeit -------------------------------------------------
class TestBugFieldCompleteness:
    def test_all_required_fields_present(self, backlog_copy):
        finding = _make_finding()
        res = R.report([finding], backlog_path=str(backlog_copy), findings_json_path=None)
        text = backlog_copy.read_text(encoding="utf-8")
        assert res.created == 1
        # AK6: View, erwartet, tatsächlich, Screenshot-Pfad, Timestamp, Commit-SHA, Fingerprint.
        for needle in ("**View:** map", "**Erwartet:**", "**Tatsächlich:**",
                       finding.screenshot_path, finding.timestamp, finding.commit_sha,
                       finding.fingerprint):
            assert needle in text, "fehlt im Bug-Block: {0}".format(needle)
        assert "### BUG-1 " in text


# --- AK5: Dedup-Idempotenz ---------------------------------------------------------
class TestDedupIdempotency:
    def test_two_identical_runs_one_ticket(self, backlog_copy):
        finding = _make_finding()
        # Lauf 1 → neuer Bug.
        r1 = R.report([finding], backlog_path=str(backlog_copy), findings_json_path=None)
        assert (r1.created, r1.updated) == (1, 0)
        text1 = backlog_copy.read_text(encoding="utf-8")
        assert text1.count("### BUG-") == 1

        # Lauf 2, identischer Defekt (nur volatile Felder anders) → Update, KEIN Duplikat.
        finding2 = _make_finding(actual="anderer wert 99.9", ts="2026-06-22T08:00:00Z", sha="zzz")
        r2 = R.report([finding2], backlog_path=str(backlog_copy), findings_json_path=None)
        assert (r2.created, r2.updated) == (0, 1)
        text2 = backlog_copy.read_text(encoding="utf-8")
        assert text2.count("### BUG-") == 1  # genau 1 Ticket (AK5)
        # Update hat die neuen volatilen Werte übernommen.
        assert "zzz" in text2

    def test_distinct_findings_get_distinct_tickets(self, backlog_copy):
        f_map = _make_finding()
        f_feed = R.Finding(
            view="feed", assertion_id="view_active",
            expected="#page-feed aktiv", actual="nicht aktiv",
            message="view feed did not become active",
            screenshot_path="x.png", timestamp="2026-06-20T10:00:00Z", commit_sha="abc",
        )
        R.report([f_map, f_feed], backlog_path=str(backlog_copy), findings_json_path=None)
        text = backlog_copy.read_text(encoding="utf-8")
        assert text.count("### BUG-") == 2
        assert "### BUG-1 " in text and "### BUG-2 " in text


# --- AK7: Grün-Lauf ohne Schreibvorgang --------------------------------------------
class TestGreenRunNoWrite:
    def test_no_findings_no_json(self, tmp_path):
        out = tmp_path / "findings.json"
        wrote = R.export_findings_json([], out)
        assert wrote is False
        assert not out.exists()

    def test_no_findings_no_backlog_write(self, backlog_copy):
        before = backlog_copy.read_text(encoding="utf-8")
        R.report([], backlog_path=str(backlog_copy), findings_json_path=None)
        after = backlog_copy.read_text(encoding="utf-8")
        assert after == before  # unverändert (AK7)

    def test_findings_do_write_json(self, tmp_path):
        out = tmp_path / "findings.json"
        wrote = R.export_findings_json([_make_finding()], out)
        assert wrote is True
        data = json.loads(out.read_text(encoding="utf-8"))
        assert data["count"] == 1
        assert data["findings"][0]["fingerprint"]
