#!/usr/bin/env bash
# Installiert die Test-Abhängigkeiten im Sandbox-Interpreter.
# Idempotent: bereits vorhandene Pakete werden übersprungen.
#
# Offline-Regression (test_astronomy_regression.py) braucht nur: pytest, numpy, skyfield.
# Der API-Layer (test_api_smoke.py) braucht zusätzlich den FastAPI-Stack.
set -e

echo "→ Test-Basis (Offline-Regression): pytest skyfield numpy"
pip install --break-system-packages -q pytest skyfield numpy

echo "→ API-Stack (optional, für test_api_smoke.py)"
pip install --break-system-packages -q \
  fastapi pydantic pydantic-settings httpx sqlalchemy aiosqlite pytz || \
  echo "  (API-Stack nicht vollständig installierbar – API-Tests werden übersprungen)"

echo "✅ Bootstrap fertig."
