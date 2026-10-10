"""US-138 (Schritt 2 von 3) — Ortszeit fuer Orte in England (London).

Freigabe Stephan 2026-10-10: Orte in England zeigen Londoner Ortszeit mit dem dezenten
Zusatz "London" direkt an der Uhrzeit (Variante A des Prototyps); alle anderen Orte
(Deutschland, Norwegen, ...) bleiben bei Berliner Zeit ohne Zusatz (AK15). Bei Zeitspannen
steht der Zusatz nur einmal am Ende. Erinnerung, Teilen-Text, Kalender und Entdecken-Karte
verwenden denselben Zusatz.

Pruefweg (T8 laut Testplan): Die Zeitfunktionen in web/index.html (zwischen
`function formatTime(` und `function pct(`) werden woertlich aus der Datei geschnitten und
unter Node.js ausgefuehrt (kein Browser, kein Server noetig; laeuft damit auch in CI und im
Sandbox). Die Anzeigestellen werden zusaetzlich per Quelltext-Pruefung darauf abgesichert,
dass sie die zentralen Funktionen nutzen und nicht mehr fest Berliner Zeit verdrahten.
Ein echter Browser-Durchlauf (Playwright) ist hier NICHT enthalten (siehe Bericht).

  T8a AK11  15.10.2026 05:30 UTC: London "06:30 Uhr London", Berlin "07:30 Uhr"
  T8b AK12  27.10.2026 05:30 UTC (nach Zeitumstellung): London "05:30 Uhr London", Berlin "06:30 Uhr"
  T8c AK12  Umstellungstag 25.10.2026 (01:00 UTC) in beiden Zonen
  T8d AK13  14.10.2026 22:30 UTC: London = 14.10./23:30 (Heute), Berlin = 15.10./00:30 (Morgen)
  T8e AK15  Norwegen-Orte (und Orte ohne Koordinaten) zeigen Berliner Zeit ohne Zusatz
  T8f       Zeitspanne: Zusatz nur einmal am Ende
  T8g AK14  Zusatz als Text (nicht nur Farbe) im HTML-Fall; Textfall fuer Erinnerung/Teilen
  T8h       Kalender: Tag und Uhrzeit nach Ort (London) bzw. unveraendert (andere Orte)
  R1        Regel "England-Ort": Punkttabelle (JS) und Paritaet zur Server-Regel (Python)
  S1        Anzeigestellen nutzen die zentralen Funktionen (Quelltext-Pruefung)
  P1        Serverseitige Beschreibungstexte: London-Zeit statt fester +2 h, Berlin unveraendert

Python 3.9-kompatibel (kein X | Y, kein match).
"""
import asyncio
import json
import re
import shutil
import subprocess
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

pytestmark = [pytest.mark.offline, pytest.mark.regression, pytest.mark.requires_full_checkout]

INDEX_HTML = Path(__file__).resolve().parents[2] / "web" / "index.html"

node_required = pytest.mark.skipif(shutil.which("node") is None, reason="Node.js nicht installiert")

# --------------------------------------------------------------------------- Fixtures
LON = {"observer_lat": 51.5081, "observer_lon": -0.0759}      # Tower Bridge
BER = {"observer_lat": 52.5163, "observer_lon": 13.3777}      # Berlin
OSLO = {"observer_lat": 59.9139, "observer_lon": 10.7522}
BERGEN = {"observer_lat": 60.3913, "observer_lon": 5.3221}


def _html():
    return INDEX_HTML.read_text(encoding="utf-8")


def _zeitblock():
    """Die Zeitfunktionen der App, woertlich aus web/index.html geschnitten."""
    html = _html()
    start = html.index("function formatTime(")
    end = html.index("function pct(")
    return html[start:end]


_PRELUDE = """
const RealDate = Date;
const FIXED = RealDate.parse(%(now)s);
globalThis.Date = class extends RealDate {
  constructor(...a) { if (a.length === 0) { super(FIXED); } else { super(...a); } }
  static now() { return FIXED; }
};
const Locations = { all: %(locs)s };
"""


def run_js(expr, now="2026-10-14T12:00:00Z", locs=None):
    """Fuehrt `expr` mit den echten App-Zeitfunktionen unter Node aus, liefert JSON-Ergebnis."""
    script = (
        _PRELUDE % {"now": json.dumps(now), "locs": json.dumps(locs or [])}
        + _zeitblock()
        + "\nconsole.log(JSON.stringify(" + expr + "));\n"
    )
    res = subprocess.run(["node", "-"], input=script, universal_newlines=True,
                         stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
    assert res.returncode == 0, "Node-Lauf fehlgeschlagen:\n" + res.stderr[-1500:]
    return json.loads(res.stdout.strip().splitlines()[-1])


def _o(d):
    return json.dumps(d)


# --------------------------------------------------------------------------- T8a-T8c
@node_required
def test_t8a_ak11_london_zeigt_londoner_zeit_berlin_berliner_zeit():
    iso = "2026-10-15T05:30:00Z"
    assert run_js("timeAt(%s, %s)" % (json.dumps(iso), _o(LON))) == "06:30 Uhr London"
    assert run_js("timeAt(%s, %s)" % (json.dumps(iso), _o(BER))) == "07:30 Uhr"


@node_required
def test_t8b_ak12_nach_der_zeitumstellung_stimmt_es_weiter():
    iso = "2026-10-27T05:30:00Z"
    assert run_js("timeAt(%s, %s)" % (json.dumps(iso), _o(LON))) == "05:30 Uhr London"
    assert run_js("timeAt(%s, %s)" % (json.dumps(iso), _o(BER))) == "06:30 Uhr"


@node_required
def test_t8c_ak12_umstellungstag_25_10_beide_zonen_springen_um_01_00_utc():
    vor, nach = "2026-10-25T00:30:00Z", "2026-10-25T01:30:00Z"
    assert run_js("timeAt(%s, %s)" % (json.dumps(vor), _o(LON))) == "01:30 Uhr London"   # BST
    assert run_js("timeAt(%s, %s)" % (json.dumps(nach), _o(LON))) == "01:30 Uhr London"  # GMT
    assert run_js("timeAt(%s, %s)" % (json.dumps(vor), _o(BER))) == "02:30 Uhr"          # CEST
    assert run_js("timeAt(%s, %s)" % (json.dumps(nach), _o(BER))) == "02:30 Uhr"         # CET


# --------------------------------------------------------------------------- T8d
@node_required
def test_t8d_ak13_tageszuordnung_nach_datum_am_ort():
    iso = "2026-10-14T22:30:00Z"   # London 14.10. 23:30, Berlin 15.10. 00:30
    # "jetzt" ist 14.10.2026 12:00 UTC -> der London-Termin liegt heute, der Berliner morgen
    assert run_js("dayAt(%s, %s)" % (json.dumps(iso), _o(LON))) == "Heute"
    assert run_js("dayAt(%s, %s)" % (json.dumps(iso), _o(BER))) == "Morgen"
    assert run_js("timeAt(%s, %s)" % (json.dumps(iso), _o(LON))) == "23:30 Uhr London"
    assert run_js("timeAt(%s, %s)" % (json.dumps(iso), _o(BER))) == "00:30 Uhr"


@node_required
def test_t8d2_ak13_datumsbeschriftung_nach_ort():
    iso = "2026-10-20T22:30:00Z"   # London 20.10. 23:30, Berlin 21.10. 00:30
    london = run_js("dayAt(%s, %s)" % (json.dumps(iso), _o(LON)))
    berlin = run_js("dayAt(%s, %s)" % (json.dumps(iso), _o(BER)))
    assert "20." in london and "21." not in london, london
    assert "21." in berlin and "20." not in berlin, berlin


@node_required
def test_t8d3_ak13_kalendertag_schluessel_nach_ort_london():
    assert run_js("dayKeyAt('2026-10-14T22:30:00Z', %s)" % _o(LON)) == "2026-10-14"
    # 14.10. 23:30 UTC = 15.10. 00:30 London (Sommerzeit bis 25.10.) -> schon der naechste Tag
    assert run_js("dayKeyAt('2026-10-14T23:30:00Z', %s)" % _o(LON)) == "2026-10-15"
    # im Winter (Londoner Zeit = UTC) bleibt der Tag gleich
    assert run_js("dayKeyAt('2026-11-14T23:30:00Z', %s)" % _o(LON)) == "2026-11-14"


# --------------------------------------------------------------------------- T8e
@node_required
def test_t8e_ak15_norwegen_und_unbekannte_orte_bleiben_berliner_zeit():
    iso = "2026-10-15T05:30:00Z"
    for ort in (OSLO, BERGEN, {}, {"location_id": "gibt-es-nicht"}, {"observer_lat": None, "observer_lon": None}):
        for html in ("false", "true"):
            out = run_js("timeAt(%s, %s, %s)" % (json.dumps(iso), _o(ort), html))
            assert out == "07:30 Uhr", (ort, out)
    assert run_js("timeAt(%s, null)" % json.dumps(iso)) == "07:30 Uhr"
    assert run_js("placeZone(undefined)") == "Europe/Berlin"


# --------------------------------------------------------------------------- T8f
@node_required
def test_t8f_zeitspanne_zusatz_nur_einmal_am_ende():
    a, b = "2026-10-15T05:41:00Z", "2026-10-15T06:48:00Z"
    london = run_js("timeRangeAt(%s, %s, %s)" % (json.dumps(a), json.dumps(b), _o(LON)))
    assert london == "06:41 \u2013 07:48 Uhr London"
    assert london.count("London") == 1
    html = run_js("timeRangeAt(%s, %s, %s, true)" % (json.dumps(a), json.dumps(b), _o(LON)))
    assert html.count("London") == 1 and html.endswith('<span class="zone">London</span>'), html
    berlin = run_js("timeRangeAt(%s, %s, %s)" % (json.dumps(a), json.dumps(b), _o(BER)))
    assert berlin == "07:41 Uhr \u2013 08:48 Uhr" and "London" not in berlin


# --------------------------------------------------------------------------- T8g
@node_required
def test_t8g_ak14_zusatz_ist_text_im_html_und_im_klartext():
    iso = "2026-10-15T05:30:00Z"
    assert run_js("timeAt(%s, %s, true)" % (json.dumps(iso), _o(LON))) == \
        '06:30 Uhr <span class="zone">London</span>'
    assert run_js("timeAt(%s, %s, true)" % (json.dumps(iso), _o(BER))) == "07:30 Uhr"
    # Klartext (Erinnerung/Teilen-Text): Wort steht in der Zeichenkette, kein Markup
    klar = run_js("timeAt(%s, %s)" % (json.dumps(iso), _o(LON)))
    assert "<" not in klar and klar.endswith(" London")


@node_required
def test_t8g2_ort_ueber_location_id_aufloesbar():
    locs = [{"id": "tower", "observer_lat": 51.5081, "observer_lon": -0.0759},
            {"id": "berlin1", "observer_lat": 52.5163, "observer_lon": 13.3777}]
    iso = "2026-10-15T05:30:00Z"
    assert run_js("timeAt(%s, {location_id:'tower'})" % json.dumps(iso), locs=locs) == "06:30 Uhr London"
    assert run_js("timeAt(%s, {location_id:'berlin1'})" % json.dumps(iso), locs=locs) == "07:30 Uhr"


@node_required
def test_t8g3_scout_standpunkt_wird_erkannt():
    iso = "2026-10-15T05:30:00Z"
    assert run_js("timeAt(%s, {standpoint_lat:51.5, standpoint_lon:-0.12})" % json.dumps(iso)) == "06:30 Uhr London"


# --------------------------------------------------------------------------- T8h
@node_required
def test_t8h_kalenderzeit_london_nach_ortszeit_andere_orte_unveraendert():
    # London: Londoner Zeit mit Zusatz, auch ueber die Tagesgrenze
    assert run_js("calTimeAt('2026-10-14T22:30:00Z', %s)" % _o(LON)) == \
        '23:30 Uhr <span class="zone">London</span>'
    # andere Orte: bisherige Anzeige (feste +2 h) unveraendert, AK15
    assert run_js("calTimeAt('2026-10-15T05:30:00Z', %s)" % _o(BER)) == "07:30 Uhr"
    assert run_js("calTimeAt('2026-10-15T05:30:00Z', %s)" % _o(OSLO)) == "07:30 Uhr"
    # andere Orte: Tagesschluessel wie bisher (UTC-Datum)
    assert run_js("dayKeyAt('2026-10-15T05:30:00Z', %s)" % _o(BER)) == "2026-10-15"


@node_required
def test_t8h2_datum_und_zeit_in_der_ortsliste_london_vs_andere():
    london = run_js("dateTimeAt('2026-10-15T05:30:00Z', %s)" % _o(LON))
    assert london.endswith("06:30 Uhr London") and "15." in london, london


# --------------------------------------------------------------------------- R1
ENGLAND_PUNKTE = [
    ("London", 51.5074, -0.1278, True),
    ("Tower Bridge", 51.5081, -0.0759, True),
    ("Land's End (Cornwall, AK1)", 50.0680, -5.7160, True),
    ("Cornwall-Punkt aus AK1", 50.1, -5.5, True),
    ("Great Yarmouth (AK1)", 52.6, 1.7, True),
    ("Manchester", 53.4808, -2.2426, True),
    ("Newcastle", 54.9783, -1.6178, True),
    ("Dover", 51.1279, 1.3134, True),
    ("Dungeness", 50.9130, 0.9770, True),
    ("Cardiff (Wales, gleiche Zeit)", 51.4816, -3.1791, True),
    ("Berlin", 52.52, 13.405, False),
    ("Muenchen", 48.1351, 11.5820, False),
    ("Oslo", 59.9139, 10.7522, False),
    ("Bergen", 60.3913, 5.3221, False),
    ("Stavanger", 58.9700, 5.7331, False),
    ("Calais", 50.9513, 1.8587, False),
    ("Boulogne-sur-Mer", 50.7264, 1.6147, False),
    ("Dieppe", 49.9229, 1.0770, False),
    ("Paris", 48.8566, 2.3522, False),
    ("Amsterdam", 52.3676, 4.9041, False),
    ("Dublin (Irland, nicht gewuenscht)", 53.3498, -6.2603, False),
    ("Belfast", 54.5973, -5.9301, False),
    ("Edinburgh (Schottland, ausserhalb)", 55.9533, -3.1883, False),
    ("Atlantik", 51.5, -9.0, False),
]


@node_required
def test_r1_england_regel_punkttabelle():
    ergebnis = run_js("[%s]" % ",".join(
        "zoneForCoords(%r, %r)" % (lat, lon) for _n, lat, lon, _e in ENGLAND_PUNKTE))
    for (name, _lat, _lon, erwartet_england), zone in zip(ENGLAND_PUNKTE, ergebnis):
        soll = "Europe/London" if erwartet_england else "Europe/Berlin"
        assert zone == soll, "%s: erwartet %s, bekommen %s" % (name, soll, zone)


@node_required
def test_r1_england_regel_fehlende_oder_ungueltige_werte_sind_berlin():
    out = run_js("[zoneForCoords(null,null), zoneForCoords(undefined,0), zoneForCoords('51.5','-0.1'), zoneForCoords(NaN,1)]")
    assert out == ["Europe/Berlin"] * 4


@node_required
def test_r1_paritaet_js_und_python_regel():
    from calculations import ortszeit
    js = run_js("[%s]" % ",".join(
        "zoneForCoords(%r, %r)" % (lat, lon) for _n, lat, lon, _e in ENGLAND_PUNKTE))
    py = ["Europe/London" if ortszeit.is_england(lat, lon) else "Europe/Berlin"
          for _n, lat, lon, _e in ENGLAND_PUNKTE]
    assert js == py


# --------------------------------------------------------------------------- S1
def _region(html, start_marker, end_marker):
    s = html.index(start_marker)
    return html[s:html.index(end_marker, s)]


def test_s1_keine_feste_berliner_zeit_mehr_an_ortsbezogenen_stellen():
    html = _html()
    # Alle Zeiten eines konkreten Termins/Ortes laufen ueber die zentralen Funktionen
    for verboten in (
        "formatTime(o.shoot_time)", "formatDate(o.shoot_time)",
        "formatTime(o.dt_utc)", "formatTime(a.time)", "formatDate(a.time)",
        "formatTime(o.sunrise_utc)", "formatTime(o.sunset_utc)",
        "formatTime(o.moonrise_utc)", "formatTime(o.moonset_utc)",
        "formatTime(o.shoot_window_start)", "formatTime(o.shoot_window_end)",
        "formatTime(o.blue_hour_morning_start)", "formatTime(o.golden_hour_evening_start)",
        "getUTCHours() + 2",
    ):
        # erlaubt ist nur die Definition der Hilfsfunktionen selbst (calTimeAt)
        if verboten == "getUTCHours() + 2":
            assert html.count(verboten) == 1, "feste +2 h darf nur noch in calTimeAt() stehen"
            assert verboten in _region(html, "function calTimeAt(", "function pct("), \
                "feste +2 h steht nicht in calTimeAt()"
            continue
        assert verboten not in html, "%s steht noch fest im Code (US-138 Schritt 2)" % verboten


def test_s1_feed_karte_detail_erinnerung_teilen_nutzen_zentrale_funktionen():
    html = _html()
    opp = _region(html, "function oppCard(", "function scoutCard(")
    assert "timeAt(o.shoot_time, o, true)" in opp
    scout = html[html.index("function scoutCard("):][:1500]
    assert "timeAt(o.dt_utc," in scout
    assert html.count("dayAt(o.shoot_time, o)") == 4      # Feed-Gruppen (2x), Chips, Heute-Zaehler
    detail_zeit = html[html.index("mkSec('ev_zeit'"):][:900]
    assert detail_zeit.count("timeAt(") == 3 and "formatTime(" not in detail_zeit
    assert "timeRangeAt(o.blue_hour_morning_start, o.golden_hour_morning_end, o, true)" in html
    assert "timeRangeAt(o.golden_hour_evening_start, o.blue_hour_evening_end, o, true)" in html
    assert "Erinnerung gesetzt f\u00fcr ${timeAt(o.shoot_time, o)}" in html
    share = _region(html, "const locName = Locations.nameFor(o.location_id, o.location_name) || o.title", "if (o.subject_lat != null")
    assert "timeZone:'Europe/Berlin'" not in share and "timeZone: placeZone(o)" in share
    assert "Uhrzeit: ${timeAt(o.shoot_time, o)}" in share


def test_s1_kalender_nutzt_ortsbezogenen_tag_und_zeit():
    html = _html()
    cal = _region(html, "const CalendarView = {", "// STANDORT-VERIFIKATION")
    assert "dayKeyAt(" in cal and "calTimeAt(" in cal
    assert "toISOString().slice(0, 10)" not in cal


def test_s1_zusatz_hat_stil_ohne_neue_farben():
    html = _html()
    m = re.search(r"\.zone\s*\{([^}]*)\}", html)
    assert m is not None, ".zone-Stil fehlt"
    stil = m.group(1)
    assert "var(--muted)" in stil and "#" not in stil, "Zusatz soll nur bestehende Farb-Token nutzen"


# --------------------------------------------------------------------------- P1 (Server)
def _utc(y, m, d, hh, mm):
    return datetime(y, m, d, hh, mm, tzinfo=timezone.utc)


class _Ort(object):
    def __init__(self, lat, lon):
        self.observer_lat = lat
        self.observer_lon = lon


def test_p1_server_london_uhrzeit_sommer_und_winter():
    from calculations.opportunity import _fmt_time
    london = _Ort(51.5081, -0.0759)
    assert _fmt_time(_utc(2026, 10, 15, 5, 30), london) == "06:30"
    assert _fmt_time(_utc(2026, 10, 27, 5, 30), london) == "05:30"
    # Umstellungstag: 00:30 UTC noch Sommerzeit, 01:30 UTC schon Winterzeit
    assert _fmt_time(_utc(2026, 10, 25, 0, 30), london) == "01:30"
    assert _fmt_time(_utc(2026, 10, 25, 1, 30), london) == "01:30"
    # Fruehjahr: 29.03.2026 00:30 UTC noch Winterzeit, 01:30 UTC schon Sommerzeit
    assert _fmt_time(_utc(2026, 3, 29, 0, 30), london) == "00:30"
    assert _fmt_time(_utc(2026, 3, 29, 1, 30), london) == "02:30"


def test_p1_server_andere_orte_und_ohne_ort_unveraendert():
    from calculations.opportunity import _fmt_time
    berlin = _Ort(52.5163, 13.3777)
    oslo = _Ort(59.9139, 10.7522)
    assert _fmt_time(_utc(2026, 10, 15, 5, 30)) == "07:30"
    assert _fmt_time(_utc(2026, 10, 15, 5, 30), berlin) == "07:30"
    assert _fmt_time(_utc(2026, 10, 15, 5, 30), oslo) == "07:30"
    assert _fmt_time(_utc(2026, 10, 15, 5, 30), None) == "07:30"


def test_p1_server_london_zeit_gleich_unabhaengiger_zoneinfo_referenz():
    from zoneinfo import ZoneInfo
    from calculations.opportunity import _fmt_time
    london = _Ort(51.5081, -0.0759)
    zi = ZoneInfo("Europe/London")
    for tage in range(0, 365, 7):
        tag = date.fromordinal(date(2026, 1, 1).toordinal() + tage)
        for stunde in (0, 1, 5, 12, 23):
            dt = datetime(tag.year, tag.month, tag.day, stunde, 30, tzinfo=timezone.utc)
            assert _fmt_time(dt, london) == dt.astimezone(zi).strftime("%H:%M"), dt


def test_p1_server_beschreibung_goldene_stunde_london():
    """Ende-zu-Ende: echte Astronomie (offline). London-Ort nennt Londoner Zeit + Zusatz,
    Berliner Ort behaelt den bisherigen Text mit '(Ortszeit)'."""
    from zoneinfo import ZoneInfo
    from calculations.astronomy import calculate_full_report
    from calculations.opportunity import find_opportunities
    from data.locations import PhotoLocation, LocationCategory

    def ort(lat, lon, name):
        return PhotoLocation(
            id="t_" + name, name=name, description="Test", category=LocationCategory.SKYLINE,
            observer_lat=lat, observer_lon=lon,
            subject_lat=lat + 0.003, subject_lon=lon + 0.003, subject_name="Motiv")

    tag = date(2026, 10, 20)
    lon_ort, ber_ort = ort(51.5081, -0.0759, "london"), ort(52.5163, 13.3777, "berlin")

    def golden(o):
        opps = asyncio.run(find_opportunities(o, tag, forecast=None, min_score=0.0, astronomy_only=True))
        return [x for x in opps if x.event_type.value == "Goldene Stunde Abend"][0].description

    sun = calculate_full_report(lon_ort.observer_lat, lon_ort.observer_lon, tag, include_planets=False).sun
    zi = ZoneInfo("Europe/London")
    erwartet = "Goldene Stunde von %s bis %s Uhr London (Ortszeit)." % (
        sun.golden_hour_evening_start.astimezone(zi).strftime("%H:%M"),
        sun.golden_hour_evening_end.astimezone(zi).strftime("%H:%M"))
    assert golden(lon_ort).startswith(erwartet), golden(lon_ort)
    assert re.match(r"Goldene Stunde von \d\d:\d\d bis \d\d:\d\d \(Ortszeit\)\.", golden(ber_ort)), golden(ber_ort)


def test_p1_server_zusatzwoerter_nach_ort():
    from calculations.opportunity import _ortszeit_zusatz, _fenster_zusatz
    london, berlin = _Ort(51.5081, -0.0759), _Ort(52.5163, 13.3777)
    assert _ortszeit_zusatz(london) == " Uhr London (Ortszeit)"
    assert _ortszeit_zusatz(berlin) == " (Ortszeit)"
    assert _fenster_zusatz(london) == " Uhr London"
    assert _fenster_zusatz(berlin) == " UTC"      # bisheriger Wortlaut bleibt (AK15)
