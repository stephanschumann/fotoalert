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
if len(sys.argv) < 2 or not sys.argv[1].strip():
    print(
        "⛔ Fehlendes Ausgabeverzeichnis-Argument.\n"
        "Aufruf:  python3 sync_kanban.py <outputs-dir>\n"
        "Ohne explizites Verzeichnis würde früher still ins aktuelle Arbeitsverzeichnis\n"
        "geschrieben — das hat bereits einmal versehentlich eine getrackte Repo-Datei\n"
        "überschrieben (BUG-67). Bitte den Cowork-Outputs-Pfad angeben.",
        file=sys.stderr,
    )
    sys.exit(2)
out_dir = sys.argv[1]
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
