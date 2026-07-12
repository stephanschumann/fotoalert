"""TASK-67 Etappe 2 — PRODUCT.md "Pflicht-Regression Orte" (Abschnitt 7), Teil-Automatisierung.

Deckt genau den einen Punkt aus PRODUCT.md Abschnitt 7 ab, der sich laut Regel 1
(Example Mapping, TASK-67-Analyse) rein über einen API-Zähler prüfen lässt — ohne echte
Browser-Klick-Interaktion:

  - "≥15 Karten sichtbar"

Kein Overlap mit test_task67_backend_regression.py (Etappe 1): dort wird für den PRODUCT.md-
Abschnitt "Backend" nur `len(/locations) > 10` geprüft (der dortige, niedrigere Schnellcheck-
Schwellwert aus Abschnitt 11). Der Orte-Tab-Abschnitt (7) verlangt einen höheren, eigenen
Schwellwert (≥15) — dieser Test prüft genau diesen zusätzlichen Wert, statt den bestehenden
Backend-Test zu duplizieren oder seinen Schwellwert stillschweigend zu verändern.

Der weit überwiegende Rest von PRODUCT.md Abschnitt 7 ist entweder bereits an anderer Stelle
automatisiert (siehe Referenzen unten) oder braucht echte Browser-Klick-/DOM-Interaktion und
bleibt bewusst Etappe 3 (Playwright):

Bereits automatisiert (Referenz statt Duplikat):
  - "Edit -> Speichern -> Änderung sofort ... (kein Reload nötig)" (Datenebene: PATCH
    übersteht Neustart/precompute) -> test_us_128.py, test_bug_68.py, test_bug-61.py
  - "Location-Detail zeigt Sichtachsen-Check-Pille ... (US-09)" (Datengarantie
    "nicht_geprueft niemals frei") -> test_us09_sightline.py
  - "Abschnitt 'Ausrichtung' zeigt Sonnenaufgang/-untergang mit Azimut" (US-107,
    Datenebene) -> test_task67_detail_regression.py (dieselbe precompute._serialize()-Logik,
    Location-Detail nutzt denselben Astronomie-Datensatz wie das Chancen-Detail)
  - "Host kann Beispielbild hochladen/ersetzen/löschen" (US-120/US-125) -> test_us120.py
  - "Host kann Ausschnitt wählen (Fokuspunkt)" (US-126) -> test_us_126.py
  - "Bauwerkshöhe/-breite ... übersteht Neustart + precompute" (US-128) -> test_us_128.py
  - "Location mit/ohne Hinweise-Text: Sektion vorhanden/nicht vorhanden" (BUG-65,
    Datenebene special_notes) -> test_bug_68.py

Bewusst NICHT in dieser Etappe (Playwright, Etappe 3):
  - "Suche 'Babelsberg' filtert korrekt" (Live-Textsuche ist reines Frontend-JS)
  - "Location-Detail-Sheet öffnet und schließt" / "Close-Button erreichbar"
  - "Bearbeiten-Karte: Vollbild-Symbol öffnet Overlay, Pins setzbar" (US-87)
  - "Satellit/Straße-Umschalter" (US-123, reine Kartendarstellung)

Python-3.9-kompatibel (kein `X | None`).
"""
import pytest

pytestmark = [pytest.mark.api, pytest.mark.regression]


class TestLocationsTabHasAtLeast15Cards:
    def test_locations_endpoint_returns_at_least_15(self, client):
        r = client.get("/locations")
        assert r.status_code == 200, r.text
        data = r.json()
        assert isinstance(data, list)
        assert len(data) >= 15, (
            f"PRODUCT.md Abschnitt 7 verlangt >=15 Location-Karten im Orte-Tab, "
            f"/locations liefert aber nur {len(data)}"
        )
