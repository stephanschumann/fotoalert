#!/usr/bin/env python3
"""US-141 Baustein 1: baut backend/data/regionen_grenzen.json (Grenzdaten für Land und Region).

Wird NICHT zur Laufzeit gebraucht, sondern nur, wenn die Grenzdaten erneuert werden sollen.
Reine Standardbibliothek, Python 3.9-kompatibel, kein Netzwerkzugriff (die Quelldateien
werden vorher von Hand heruntergeladen, siehe unten).

Quellen (Abruf 2026-10-14, am 2026-10-15 erneut abgerufen; beide Dateien hatten dieselbe SHA-256-Prüfsumme):
  1. Natural Earth, "Admin 1 – States, Provinces", Maßstab 1:10 Mio., Version 5.2.0-pre
     (GitHub nvkelso/natural-earth-vector, geojson/ne_10m_admin_1_states_provinces.geojson).
     Gemeinfrei (Public Domain). Genutzt für Deutschland (16), Österreich (9), Schweiz (26),
     Italien (20, aus den Provinzen nach Feld "region"), Niederlande (12), Frankreich (18: 13 auf dem
     Festland einschließlich Korsika plus die fünf Übersee-Regionen Guadeloupe, Martinique,
     Französisch-Guayana, La Réunion und Mayotte, aus den Départements nach Feld "region";
     Entscheidung Stephan 2026-10-15 „Frankreich mit Übersee“) und das Vereinigte Königreich
     (4, nach Feld "geonunit").
  2. Kartverket / robhop "fylker-og-kommuner", Fylker-L.geojson, Stand 2024 (15 Provinzen),
     Lizenz CC BY 4.0 (Namensnennung: Kartverket). Genutzt für Norwegen.

Aufruf:
  python3 tools/build_regionen_grenzen.py NE_ADMIN1.geojson NORWEGEN_FYLKER.geojson backend/data/regionen_grenzen.json

Genauigkeit: Die Quelle ist für Weltkarten gedacht (Grenzen können örtlich um einen bis wenige
Kilometer abweichen). Das Ergebnis wird zusätzlich vereinfacht (Toleranz EPSILON_M). Deshalb
arbeitet data/regionen.py im Grenzraum mit einem Unsicher-Hinweis statt einer stillen Entscheidung.
"""
import hashlib
import io
import json
import math
import sys

EPSILON_M = 120.0          # Vereinfachungs-Toleranz in Metern
MIN_RING_DIAGONALE_M = 400.0   # kleinere Polygone/Löcher (Mini-Inseln) fallen weg
NACHKOMMA = 4              # Koordinaten auf 4 Stellen (ca. 11 m)

# --- Namen: Quelle -> deutsche Anzeigenamen -----------------------------------------------
IT = {
    "Lombardia": "Lombardei", "Toscana": "Toskana", "Emilia-Romagna": "Emilia-Romagna",
    "Sicily": "Sizilien", "Piemonte": "Piemont", "Sardegna": "Sardinien", "Veneto": "Venetien",
    "Apulia": "Apulien", "Marche": "Marken", "Calabria": "Kalabrien", "Campania": "Kampanien",
    "Lazio": "Latium", "Liguria": "Ligurien", "Friuli-Venezia Giulia": "Friaul-Julisch Venetien",
    "Abruzzo": "Abruzzen", "Trentino-Alto Adige": "Trentino-Südtirol", "Molise": "Molise",
    "Basilicata": "Basilicata", "Umbria": "Umbrien", "Valle d'Aosta": "Aostatal",
}
FR = {
    "Occitanie": "Okzitanien", "Auvergne-Rhône-Alpes": "Auvergne-Rhône-Alpes",
    "Nouvelle-Aquitaine": "Nouvelle-Aquitaine", "Grand Est": "Grand Est",
    "Bourgogne-Franche-Comté": "Bourgogne-Franche-Comté", "Île-de-France": "Île-de-France",
    "Provence-Alpes-Côte-d'Azur": "Provence-Alpes-Côte d'Azur",
    "Centre-Val de Loire": "Centre-Val de Loire", "Hauts-de-France": "Hauts-de-France",
    "Pays de la Loire": "Pays de la Loire", "Normandie": "Normandie", "Bretagne": "Bretagne",
    "Corse": "Korsika",
    # Übersee-Regionen (Entscheidung Stephan 2026-10-15); links der Wert des Feldes "region" in Natural Earth
    "Guyane française": "Französisch-Guayana", "Guadeloupe": "Guadeloupe",
    "Martinique": "Martinique", "Réunion": "La Réunion", "Mayotte": "Mayotte",
}
NL = {
    "Groningen": "Groningen", "Drenthe": "Drenthe", "Overijssel": "Overijssel",
    "Gelderland": "Gelderland", "Limburg": "Limburg", "Zeeland": "Seeland",
    "Noord-Brabant": "Nordbrabant", "Zuid-Holland": "Südholland", "Noord-Holland": "Nordholland",
    "Friesland": "Friesland", "Flevoland": "Flevoland", "Utrecht": "Utrecht",
}
UK = {"England": "England", "Scotland": "Schottland", "Wales": "Wales",
      "Northern Ireland": "Nordirland"}
NO = {
    "Buskerud": "Buskerud", "Agder": "Agder", "Akershus": "Akershus", "Oslo": "Oslo",
    "Finnmark - Finnmárku - Finmarkku": "Finnmark", "Troms - Romsa - Tromssa": "Troms",
    "Østfold": "Østfold", "Vestland": "Vestland", "Møre og Romsdal": "Møre og Romsdal",
    "Telemark": "Telemark", "Vestfold": "Vestfold", "Rogaland": "Rogaland",
    "Trøndelag - Trööndelage": "Trøndelag", "Nordland - Nordlánnda": "Nordland",
    "Innlandet": "Innlandet",
}
LAND_UK = "Vereinigtes Königreich (UK)"


def zuordnen_ne(p):
    """(Land, Region) für ein Natural-Earth-Objekt oder None, wenn es nicht dazugehört."""
    a3 = p.get("adm0_a3")
    if a3 == "DEU":
        return "Deutschland", p["name"]
    if a3 == "AUT":
        return "Österreich", p["name"]
    if a3 == "CHE":
        n = p["name_de"]
        return "Schweiz", n[len("Kanton "):] if n.startswith("Kanton ") else n
    if a3 == "ITA":
        return "Italien", IT[p["region"]]
    if a3 == "FRA":
        return ("Frankreich", FR[p["region"]]) if p["region"] in FR else None   # mit Übersee (18)
    if a3 == "NLD":
        return ("Niederlande", NL[p["name"]]) if p["name"] in NL else None      # ohne Karibik
    if a3 == "GBR":
        return LAND_UK, UK[p["geonunit"]]
    return None


# --- Geometrie --------------------------------------------------------------------------
def _xy(pt, lat0):
    return (pt[0] * math.cos(math.radians(lat0)) * 111320.0, pt[1] * 110540.0)


def _dist_seg(p, a, b):
    ax, ay = a
    bx, by = b
    px, py = p
    dx, dy = bx - ax, by - ay
    l2 = dx * dx + dy * dy
    if l2 == 0.0:
        return math.hypot(px - ax, py - ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / l2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))


def rdp(punkte, eps):
    """Douglas-Peucker auf einer offenen Punktfolge (Liste von (x, y)); iterativ."""
    n = len(punkte)
    if n < 3:
        return list(range(n))
    keep = [False] * n
    keep[0] = keep[-1] = True
    stack = [(0, n - 1)]
    while stack:
        i, j = stack.pop()
        dmax, idx = 0.0, -1
        for k in range(i + 1, j):
            d = _dist_seg(punkte[k], punkte[i], punkte[j])
            if d > dmax:
                dmax, idx = d, k
        if dmax > eps and idx > 0:
            keep[idx] = True
            stack.append((i, idx))
            stack.append((idx, j))
    return [k for k in range(n) if keep[k]]


def vereinfache_ring(ring):
    """Vereinfacht einen geschlossenen Ring; gibt None zurück, wenn er zu klein wird."""
    pts = ring[:-1] if ring[0] == ring[-1] else list(ring)
    if len(pts) < 4:
        return None
    lat0 = sum(p[1] for p in pts) / len(pts)
    xy = [_xy(p, lat0) for p in pts]
    xs = [q[0] for q in xy]
    ys = [q[1] for q in xy]
    if math.hypot(max(xs) - min(xs), max(ys) - min(ys)) < MIN_RING_DIAGONALE_M:
        return None
    # Ring an zwei weit entfernten Ankerpunkten teilen und beide Hälften vereinfachen
    far = max(range(len(xy)), key=lambda k: (xy[k][0] - xy[0][0]) ** 2 + (xy[k][1] - xy[0][1]) ** 2)
    h1 = list(range(0, far + 1))
    h2 = list(range(far, len(xy))) + [0]
    keep = set()
    for h in (h1, h2):
        sel = rdp([xy[k] for k in h], EPSILON_M)
        keep.update(h[s] for s in sel)
    out = [pts[k] for k in sorted(keep)]
    if len(out) < 3:
        return None
    out = [[round(p[0], NACHKOMMA), round(p[1], NACHKOMMA)] for p in out]
    out.append(list(out[0]))
    return out


def polygone(geom):
    if geom["type"] == "Polygon":
        return [geom["coordinates"]]
    if geom["type"] == "MultiPolygon":
        return geom["coordinates"]
    return []


def bauen(ne_pfad, nor_pfad, ziel):
    with io.open(ne_pfad, "rb") as f:
        ne_roh = f.read()
    with io.open(nor_pfad, "rb") as f:
        nor_roh = f.read()
    ne = json.loads(ne_roh.decode("utf-8"))
    nor = json.loads(nor_roh.decode("utf-8"))
    eintraege = {}   # (land, region) -> Liste von Polygonen
    quellen = []
    for f in ne["features"]:
        z = zuordnen_ne(f["properties"])
        if z:
            quellen.append((z, f["geometry"]))
    for f in nor["features"]:
        n = f["properties"].get("fylkesnavn") or f["properties"].get("name")
        if n in NO:
            quellen.append((("Norwegen", NO[n]), f["geometry"]))
    for (land, region), geom in quellen:
        for poly in polygone(geom):
            ringe = []
            for i, ring in enumerate(poly):
                v = vereinfache_ring(ring)
                if v is None:
                    if i == 0:
                        ringe = []
                        break
                    continue
                ringe.append(v)
            if ringe:
                eintraege.setdefault((land, region), []).append(ringe)
    gebiete = [{"land": l, "region": r, "polygone": p} for (l, r), p in sorted(eintraege.items())]
    meta = {
        "zweck": "US-141: Land und Region eines Orts aus Koordinaten (data/regionen.py)",
        "format": "polygone = Liste von Polygonen; Polygon = [äußerer Ring, Loch, Loch ...]; Ring = [[Länge, Breite], ...]",
        "erzeugt_am": "2026-10-15",
        "epsilon_m": EPSILON_M,
        "quellen": [
            {"name": "Natural Earth 1:10m Admin 1 – States, Provinces, Version 5.2.0-pre",
             "lizenz": "Public Domain", "datei_sha256": hashlib.sha256(ne_roh).hexdigest(),
             "abruf": "2026-10-14, erneut 2026-10-15 (gleiche Prüfsumme)",
             "url": "https://github.com/nvkelso/natural-earth-vector (geojson/ne_10m_admin_1_states_provinces.geojson)"},
            {"name": "Norwegen, Fylker 2024 (Kartverket) über robhop/fylker-og-kommuner, Fylker-L.geojson",
             "lizenz": "CC BY 4.0, Namensnennung: Kartverket", "datei_sha256": hashlib.sha256(nor_roh).hexdigest(),
             "abruf": "2026-10-14, erneut 2026-10-15 (gleiche Prüfsumme)", "url": "https://github.com/robhop/fylker-og-kommuner"},
        ],
    }
    with io.open(ziel, "w", encoding="utf-8") as f:
        f.write(json.dumps({"meta": meta, "gebiete": gebiete}, ensure_ascii=False, separators=(",", ":")))
    n_poly = sum(len(g["polygone"]) for g in gebiete)
    n_pkt = sum(len(r) for g in gebiete for p in g["polygone"] for r in p)
    print("Gebiete: %d, Polygone: %d, Punkte: %d" % (len(gebiete), n_poly, n_pkt))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(2)
    bauen(sys.argv[1], sys.argv[2], sys.argv[3])
