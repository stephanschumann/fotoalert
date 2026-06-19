"""
Scout-Tab Orchestrator: führt alle aktiven Scout-Pipelines aus und merged die Ergebnisse.

Aktive Pipelines:
  - moon_pipeline: Mond-Alignment-Chancen (US-70)
  - sun_pipeline:  Sonnen-Alignment-Chancen (US-81)

Neue Pipelines (Milchstraße, Kometen, …) hier registrieren:
  from discover import my_new_pipeline
  results = await asyncio.gather(..., my_new_pipeline.run(days), ...)
"""
from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from discover import moon_pipeline, sun_pipeline
from discover.pipeline_base import ScoutOpportunity, clear_weather_cache

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Kern-Pipeline
# ---------------------------------------------------------------------------

async def run_pipeline(days: int = 14) -> list[ScoutOpportunity]:
    """
    Führt alle Scout-Pipelines parallel aus.
    Gibt eine nach Score absteigende Gesamtliste zurück.
    Ein Fehler in einer Pipeline bricht die anderen nicht ab.
    """
    clear_weather_cache()

    moon_result, sun_result = await asyncio.gather(
        moon_pipeline.run(days),
        sun_pipeline.run(days),
        return_exceptions=True,
    )

    all_opportunities: list[ScoutOpportunity] = []

    if isinstance(moon_result, Exception):
        log.error("[Mond] Pipeline fehlgeschlagen: %s", moon_result)
    else:
        all_opportunities.extend(moon_result)

    if isinstance(sun_result, Exception):
        log.error("[Sonne] Pipeline fehlgeschlagen: %s", sun_result)
    else:
        all_opportunities.extend(sun_result)

    all_opportunities.sort(key=lambda o: o.score, reverse=True)

    moon_count = len(moon_result) if not isinstance(moon_result, Exception) else "ERR"
    sun_count  = len(sun_result)  if not isinstance(sun_result,  Exception) else "ERR"
    log.info("Orchestrator abgeschlossen: %d Chancen total (🌙 Mond: %s, ☀️ Sonne: %s)",
             len(all_opportunities), moon_count, sun_count)
    return all_opportunities


# ---------------------------------------------------------------------------
# Cache-Schreib-Funktion (wird von main.py aufgerufen)
# ---------------------------------------------------------------------------

async def refresh_discover_cache(cache_path: Path) -> list[dict]:
    """Führt alle Pipelines aus und schreibt discover.json."""
    opportunities = await run_pipeline()
    data = [asdict(o) for o in opportunities]
    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "generated_at": datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
                "count": len(data),
                "opportunities": data,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )
    log.info("discover.json geschrieben: %d Chancen", len(data))
    return data


# ---------------------------------------------------------------------------
# CLI-Schnelltest
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
        stream=sys.stdout,
    )

    async def _main():
        cache_path = Path(__file__).parent.parent / "cache" / "discover.json"
        data = await refresh_discover_cache(cache_path)
        print(f"\n=== Top 10 Scout-Chancen ===")
        for o in data[:10]:
            icon = "🌙" if o["body_name"] == "moon" else "☀️"
            illum = f" {o['body_illumination_pct']}%" if o["body_illumination_pct"] is not None else ""
            print(
                f"  {icon} {o['day']} {o['session']:18s} | {o['subject_name']:30s} | "
                f"{o['body_altitude_deg']:5.1f}° az {o['body_azimuth_deg']:5.1f}°{illum} | "
                f"d={o['distance_m']:6.0f}m | Score {o['score']:.3f} | "
                f"f={o['focal_length_equiv_mm']}mm"
            )

    asyncio.run(_main())
