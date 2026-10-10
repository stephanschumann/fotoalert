"""US-138 (Schritt 3 von 3) — Entdecken-Tab (Scout) fuer London/England.

Vorher rechneten beide Scout-Rechenwege (discover/sun_pipeline.py, moon_pipeline.py) die
Lichtfenster (Blaue/Goldene Stunde) fuer ALLE Motive mit dem festen Berliner Bezugspunkt
52,52 N / 13,40 O. In London geht die Sonne rund 54 Minuten spaeter (UTC) auf, die Fenster
lagen dort also daneben.

Annahmen (Spec laesst sie offen):
  * Bezugspunkt fuer England-Motive = die Koordinaten des Motivs selbst (auf ein Viertelgrad-Raster
    gerundet). Das erfuellt AK16 (<= 15 min neben den Londoner Sonnenzeiten) auch fuer
    Cornwall/Norfolk, wo die Sonnenzeit bis zu ~30 min von London abweicht.
  * "England" = dieselbe Regel wie in Schritt 2 (calculations/ortszeit.py::is_england).
  * Alle anderen Motive (auch Norwegen) behalten den Berliner Bezugspunkt -> Ergebnisse
    unveraendert (AK16 zweiter Halbsatz).

  E1  AK16  Bezugspunkt je Motiv: Berlin/Norwegen unveraendert, England = eigene Koordinaten
  E2  AK16  Sonnen-Pipeline: Zeitpunkte eines London-Motivs liegen in den Londoner Lichtfenstern
  E3  AK16  Mond-Pipeline: dasselbe
  E4  AK16  Berliner Motiv liefert exakt die Berliner Zeitpunkte wie vorher (beide Pipelines)
  E5        Lichtfenster werden je Bezugspunkt nur einmal pro Tag berechnet (Laufzeit)
  E6        Die 54-Minuten-Verschiebung ist real (Sicherung gegen einen wirkungslosen Test)

Python 3.9-kompatibel.
"""
import asyncio
from datetime import date, datetime, timedelta, timezone

import pytest

pytestmark = [pytest.mark.offline, pytest.mark.regression]

pytest.importorskip("skyfield", reason="Scout-Pipelines brauchen skyfield")

from calculations.astronomy import CelestialPosition, calculate_sun_info  # noqa: E402
from discover import moon_pipeline, pipeline_base, sun_pipeline  # noqa: E402
from discover.subjects import DiscoverSubject  # noqa: E402

BERLIN = (52.52, 13.40)
SESSIONS = ("blue_morning", "golden_morning", "golden_evening", "blue_evening")


def _subject(sid, lat, lon):
    return DiscoverSubject(
        id=sid, name=sid, kategorie="Test", lat=lat, lon=lon,
        structure_height_m=65.0, terrain_offset_m=0.0, subject_width_m=60.0,
        hoehe_confidence="hoch",
    )


LONDON = _subject("us138-london", 51.5055, -0.0754)      # Tower Bridge
POTSDAM = _subject("us138-potsdam", 52.40, 13.06)
OSLO = _subject("us138-oslo", 59.91, 10.75)
CORNWALL = _subject("us138-cornwall", 50.10, -5.50)


def _fenster_zeitpunkte(ref_lat, ref_lon, tage):
    """Alle erlaubten Abtastzeitpunkte (als ISO-Text) fuer einen Bezugspunkt."""
    out = set()
    heute = date.today()
    for delta in range(tage):
        sun = calculate_sun_info(ref_lat, ref_lon, heute + timedelta(days=delta))
        for a, b in (
            (sun.blue_hour_morning_start, sun.blue_hour_morning_end),
            (sun.golden_hour_morning_start, sun.golden_hour_morning_end),
            (sun.golden_hour_evening_start, sun.golden_hour_evening_end),
            (sun.blue_hour_evening_start, sun.blue_hour_evening_end),
        ):
            for t in pipeline_base.sample_window(a, b):
                out.add(t.strftime("%Y-%m-%dT%H:%M:%SZ"))
    return out


def _patch_fest(monkeypatch, modul, subjects, alt, body):
    """Feste Himmelskoerper-Position (immer hoch genug), kein Wetter, eigene Motive."""
    async def kein_wetter(lat, lon):
        return None

    monkeypatch.setattr(modul, "SUBJECTS", subjects)
    monkeypatch.setattr(modul, "get_weather", kein_wetter)
    monkeypatch.setattr(modul, "get_body_position", lambda lat, lon, name, dt: _pos(alt))


def _pos(alt):
    fields = CelestialPosition.__dataclass_fields__
    kw = {}
    for name, f in fields.items():
        if name == "azimuth":
            kw[name] = 100.0
        elif name == "altitude":
            kw[name] = alt
        elif name == "name":
            kw[name] = "x"
        else:
            kw[name] = 1.0
    return CelestialPosition(**kw)


# ---------------------------------------------------------------------------
# E1
# ---------------------------------------------------------------------------

def test_e1_bezugspunkt_je_motiv():
    """AK16: Berliner/Brandenburger und norwegische Motive behalten Berlin, England nutzt eigene Koordinaten."""
    assert pipeline_base.light_reference(POTSDAM.lat, POTSDAM.lon) == BERLIN
    assert pipeline_base.light_reference(OSLO.lat, OSLO.lon) == BERLIN
    assert pipeline_base.light_reference(LONDON.lat, LONDON.lon) == (51.5, 0.0)
    assert pipeline_base.light_reference(CORNWALL.lat, CORNWALL.lon) == (50.0, -5.5)


# ---------------------------------------------------------------------------
# E2 / E3 / E4
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("modul,alt,body", [(sun_pipeline, 3.0, "sun"), (moon_pipeline, 20.0, "moon")])
def test_e2_e3_london_motiv_in_londoner_lichtfenstern(monkeypatch, modul, alt, body):
    """AK16: Alle Zeitpunkte eines London-Motivs liegen in den Londoner Lichtfenstern (nicht den Berliner)."""
    _patch_fest(monkeypatch, modul, [LONDON], alt, body)
    res = asyncio.run(modul.run(days=3))
    assert res, "Test braucht Treffer"
    london = _fenster_zeitpunkte(51.5, 0.0, 3)   # Bezugspunkt = Motiv auf ein Viertelgrad-Raster gerundet
    berlin = _fenster_zeitpunkte(*BERLIN, 3)
    zeiten = {o.dt_utc for o in res}
    assert zeiten <= london, f"Zeitpunkte ausserhalb der Londoner Fenster: {sorted(zeiten - london)[:5]}"
    # Londoner Fenster mit +-15 min Toleranz: keiner der Treffer darf nur in Berlins Fenstern liegen
    assert not (zeiten & (berlin - london))


@pytest.mark.parametrize("modul,alt,body", [(sun_pipeline, 3.0, "sun"), (moon_pipeline, 20.0, "moon")])
def test_e4_berliner_motiv_unveraendert(monkeypatch, modul, alt, body):
    """AK16: Berliner (und norwegische) Motive rechnen weiter mit den Berliner Lichtfenstern."""
    _patch_fest(monkeypatch, modul, [POTSDAM, OSLO], alt, body)
    res = asyncio.run(modul.run(days=3))
    assert res
    berlin = _fenster_zeitpunkte(*BERLIN, 3)
    assert {o.dt_utc for o in res} <= berlin


def test_e2_cornwall_innerhalb_15_minuten_um_eigene_sonnenzeit(monkeypatch):
    """AK16: Auch weit im Westen (Cornwall) liegt das erste Morgenfenster nahe der dortigen Sonnenzeit."""
    _patch_fest(monkeypatch, sun_pipeline, [CORNWALL], 3.0, "sun")
    res = asyncio.run(sun_pipeline.run(days=1))
    assert res
    sun = calculate_sun_info(CORNWALL.lat, CORNWALL.lon, date.today())
    fruehestes = min(datetime.strptime(o.dt_utc, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc) for o in res)
    assert abs((fruehestes - sun.blue_hour_morning_start).total_seconds()) <= 15 * 60


# ---------------------------------------------------------------------------
# E5 / E6
# ---------------------------------------------------------------------------

def test_e5_lichtfenster_je_bezugspunkt_einmal_pro_tag(monkeypatch):
    """Laufzeit: 3 Berliner Motive + 2 London-Motive -> je Tag nur 2 Sonnen-Berechnungen (Berlin + London-Punkt)."""
    aufrufe = []
    echt = sun_pipeline.calculate_sun_info

    def spion(lat, lon, d):
        aufrufe.append((lat, lon, d))
        return echt(lat, lon, d)

    london2 = _subject("us138-london2", 51.5055, -0.0754)   # gleicher gerundeter Punkt
    _patch_fest(monkeypatch, sun_pipeline, [POTSDAM, OSLO, POTSDAM, LONDON, london2], 3.0, "sun")
    monkeypatch.setattr(sun_pipeline, "calculate_sun_info", spion)
    asyncio.run(sun_pipeline.run(days=2))
    assert len(aufrufe) == 2 * 2, f"erwartet 4 Berechnungen (2 Bezugspunkte x 2 Tage), war {len(aufrufe)}"
    assert {(a[0], a[1]) for a in aufrufe} == {BERLIN, (51.5, 0.0)}


def test_e6_london_und_berlin_fenster_unterscheiden_sich():
    """Sicherung: Der Londoner Sonnenaufgang liegt > 40 min von Berlins (UTC) -> Test E2 ist nicht wirkungslos."""
    d = date.today()
    b = calculate_sun_info(*BERLIN, d).blue_hour_morning_start
    l = calculate_sun_info(LONDON.lat, LONDON.lon, d).blue_hour_morning_start
    assert abs((l - b).total_seconds()) > 40 * 60
