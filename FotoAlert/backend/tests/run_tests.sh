#!/usr/bin/env bash
# Einstiegspunkt für das Test-Harness — das ruft die Test-Phase des Orchestrators auf.
#
# Standard: nur die deterministische Offline-Regression (schnell, netzunabhängig).
# Mit "--all" zusätzlich API-/Netzwerk-Tests (brauchen Stack + ggf. Netzwerk).
#
# Läuft IMMER gegen data_dev (FOTOALERT_ENV=dev), nie gegen Prod.
set -e
cd "$(dirname "$0")/.."   # → backend/
export FOTOALERT_ENV=dev

if [ "$1" == "--all" ]; then
  echo "→ Vollsuite (Offline-Regression + API/Netzwerk)"
  python3 -m pytest -v
else
  echo "→ Offline-Regression (deterministisch, Sandbox-sicher)"
  python3 -m pytest -m offline -v
fi
