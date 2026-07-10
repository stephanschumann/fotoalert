"""US-129 — Filter "Hat Beispielbild" für Locations (Locations-Tab + Karte).

Die eigentliche Filterlogik ist reines Frontend-JS (Filter.applyToLocations()
und MapView.applyFilter() in web/index.html) und daher nicht per pytest
testbar — das ist Aufgabe des manuellen Testplans im Ticket (BACKLOG.md).

Was hier automatisiert abgesichert wird, ist der Datenvertrag, auf dem der
neue Filter aufbaut: GET /locations muss für JEDE Location (Standard- und
Custom-Location) ein `image_url`-Feld liefern, das entweder `null` ist
(kein Beispielbild hochgeladen) oder ein String, der mit `/location-images/`
beginnt (Beispielbild vorhanden, siehe backend/main.py::_loc_to_out()).
Bricht dieser Vertrag, filtert der neue Chip im Frontend lautlos falsch
(z. B. alle Locations als "ohne Bild", obwohl Bilder existieren).

Konvention (vgl. test_bug-61.py): Jeder Test nennt im Docstring die
Ticket-ID, deren AK er absichert. API-Tests laufen gegen den
FastAPI-TestClient (conftest.py, client-Fixture).
"""
from __future__ import annotations

import pytest

pytestmark = [pytest.mark.api, pytest.mark.regression]


class TestUS129ImageUrlContract:
    """US-129 AK: Der Filter "Hat Bild" baut auf `image_url` in GET /locations auf.

    AK: Jede Location im Response-Array hat den Schlüssel `image_url`.
    AK: `image_url` ist entweder null oder ein String, der mit
        `/location-images/` beginnt (nie leerer String, nie fehlender Key).
    AK: Standard- UND Custom-Locations liefern das Feld gleichermaßen
        (kein struktureller Unterschied je nach Location-Art).
    """

    def test_all_locations_have_image_url_key(self, client):
        """US-129: GET /locations liefert für jede Location den Schlüssel image_url."""
        r = client.get("/locations")
        assert r.status_code == 200, f"GET /locations fehlgeschlagen: {r.text}"
        locations = r.json()
        assert len(locations) > 0, "GET /locations lieferte keine Locations — Test nicht aussagekräftig"

        missing = [l["id"] for l in locations if "image_url" not in l]
        assert not missing, (
            f"image_url fehlt bei {len(missing)} Location(s): {missing}. "
            "Der neue 'Hat Bild'-Filter (US-129) kann ohne dieses Feld nicht "
            "zwischen Locations mit/ohne Beispielbild unterscheiden."
        )

    def test_image_url_shape_is_null_or_location_images_path(self, client):
        """US-129: image_url ist null ODER beginnt mit /location-images/ (nie leerer String)."""
        locations = client.get("/locations").json()

        invalid = [
            (l["id"], l.get("image_url"))
            for l in locations
            if l.get("image_url") is not None
            and not str(l.get("image_url")).startswith("/location-images/")
        ]
        assert not invalid, (
            f"image_url mit unerwartetem Format gefunden: {invalid}. "
            "Erwartet: null oder ein Pfad, der mit /location-images/ beginnt."
        )

        empty_string = [l["id"] for l in locations if l.get("image_url") == ""]
        assert not empty_string, (
            f"image_url ist bei {empty_string} ein leerer String statt null — "
            "der Frontend-Filter würde das fälschlich als 'hat Bild' werten."
        )

    def test_custom_and_standard_locations_both_expose_image_url(self, client):
        """US-129: Standard- und Custom-Locations liefern image_url strukturell gleich."""
        locations = client.get("/locations").json()
        custom = [l for l in locations if str(l["id"]).startswith("custom_")]
        standard = [l for l in locations if not str(l["id"]).startswith("custom_")]

        assert all("image_url" in l for l in custom), (
            "image_url fehlt bei mindestens einer Custom-Location."
        )
        assert all("image_url" in l for l in standard), (
            "image_url fehlt bei mindestens einer Standard-Location."
        )
