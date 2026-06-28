#!/usr/bin/env python3
"""
sync_kanban.py — atomarer Kanban-Sync: erst LINTEN, dann GENERIEREN. Bricht laut ab,
wenn BACKLOG.md inkonsistent ist (statt still die veraltete Quelle zu bevorzugen).

Aufruf:  python3 FotoAlert/tools/sync_kanban.py <outputs-dir>
Danach:  mcp__cowork__update_artifact (id: fotoalert-kanban, html_path = ausgegebener Pfad)

Der Push (update_artifact) bleibt der MCP-Call des Agenten — dieser Wrapper stellt nur
sicher, dass NIE generiert/gepusht wird, solange der Lint rot ist.
"""
import sys, os, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
out_dir = sys.argv[1] if len(sys.argv) > 1 else "."
backlog = os.path.join(HERE, "..", "BACKLOG.md")

print("→ Lint BACKLOG.md …")
r = subprocess.run([sys.executable, os.path.join(HERE,"lint_backlog.py"), backlog])
if r.returncode != 0:
    print("\n⛔ Lint rot — KEIN Generieren, KEIN Push. Erst BACKLOG.md korrigieren.", file=sys.stderr)
    sys.exit(1)
print("✓ Lint sauber. → Generiere …")
r = subprocess.run([sys.executable, os.path.join(HERE,"gen_kanban.py"), out_dir])
if r.returncode != 0:
    sys.exit(r.returncode)
html = os.path.join(out_dir, "fotoalert-kanban.html")
print(f"\n✓ Fertig: {html}")
print("→ Jetzt: mcp__cowork__update_artifact (id: fotoalert-kanban, html_path = oben).")
