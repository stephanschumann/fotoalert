#!/usr/bin/env python3
"""Splittet BACKLOG.md: Done-Tickets -> BACKLOG-ARCHIVE.md, Aktive bleiben.
Verlustfrei + Selbstverifikation: reparse(neu+archiv) muss id->lane == baseline(original) ergeben."""
import sys, os, re, importlib.util

ROOT = sys.argv[1]                      # FotoAlert dir
SRC  = os.path.join(ROOT, "BACKLOG.md")
NEW  = os.path.join(ROOT, "BACKLOG.md")            # in-place ersetzen
ARCH = os.path.join(ROOT, "BACKLOG-ARCHIVE.md")

ID_RE = re.compile(r'^###\s+(~~)?\s*([A-Z]+-\d+[a-z]?)\s*[·:\-]\s*(.*)$')

# gen_kanban Parser laden, um identische Klassifikation zu garantieren
spec = importlib.util.spec_from_file_location("gen", os.path.join(ROOT, "tools", "gen_kanban.py"))
gen = importlib.util.module_from_spec(spec); spec.loader.exec_module(gen)

text = open(SRC, encoding="utf-8").read()
lines = text.split("\n")
n = len(lines)

# Blockgrenzen: ein Ticketblock = reale ### Ticket-Zeile bis zur naechsten realen ### Ticket-Zeile oder ## Sektion
def is_real_ticket(ln): return bool(ID_RE.match(ln))

# Klassifikation done? (gen-Logik gespiegelt)
def block_is_done(header, body, section):
    m = ID_RE.match(header)
    struck = bool(m.group(1))
    mk = re.search(r'\[([ x~])\]\s*`?\s*$', header); marker = mk.group(1) if mk else None
    sm = re.search(r'^\|\s*\*\*Status\*\*\s*\|\s*(.*?)\s*\|', body, re.M)
    status = sm.group(1).strip() if sm else ""
    if status: return gen.status_to_key(status) == "done"
    sec_l = section.lower()
    if "erledigt" in sec_l or "✅" in section or struck or marker == "x": return True
    return False

# Segmente bauen
active_lines = []
archive_blocks = []
section = ""
i = 0
while i < n:
    ln = lines[i]
    if ln.startswith("## "):
        section = ln
        active_lines.append(ln); i += 1; continue
    if is_real_ticket(ln):
        # Block-Ende finden: naechste reale Ticket-### oder ## Zeile
        j = i + 1
        while j < n and not is_real_ticket(lines[j]) and not lines[j].startswith("## "):
            j += 1
        block = lines[i:j]
        body = "\n".join(block[1:])
        if block_is_done(ln, body, section):
            archive_blocks.append("\n".join(block))
        else:
            active_lines.extend(block)
        i = j; continue
    active_lines.append(ln); i += 1

new_text = "\n".join(active_lines)
arch_text = ("# FotoAlert – Backlog ARCHIV (erledigte Tickets)\n\n"
             "> Aus BACKLOG.md ausgelagert. Wird vom Kanban-Generator zusammen mit BACKLOG.md gelesen.\n"
             "> Nicht von Hand neu einsortieren; Lane-Quelle bleibt das `Status`-Feld bzw. Done-Marker.\n\n"
             "## ✅ Erledigt (Archiv)\n\n" + "\n\n".join(archive_blocks) + "\n")

# --- Selbstverifikation: reparse(neu + archiv) == baseline(original) ---
base = {t["id"]: t["lane"] for t in gen.parse_backlog(text)}
combo = gen.parse_backlog(new_text + "\n\n" + arch_text)
combo_map = {t["id"]: t["lane"] for t in combo}

errs = []
if len(base) != len(combo_map):
    errs.append(f"Anzahl: original {len(base)} vs neu {len(combo_map)}")
miss = set(base) - set(combo_map); extra = set(combo_map) - set(base)
if miss: errs.append(f"verlorene IDs: {sorted(miss)}")
if extra: errs.append(f"neue IDs: {sorted(extra)}")
changed = {k: (base[k], combo_map[k]) for k in base if k in combo_map and base[k] != combo_map[k]}
if changed: errs.append(f"Lane geaendert: {changed}")
# Dup-Check in der naiven Zaehlung (parse dedupt per dict -> separat zaehlen)
from collections import Counter
ids_all = [t["id"] for t in gen.parse_backlog(text)]
dups = [k for k,v in Counter(ids_all).items() if v>1]

print(f"Original-Tickets: {len(ids_all)} (unique {len(base)}), Done->Archiv: {len(archive_blocks)}")
if dups: print(f"  (Hinweis: doppelte IDs im Original: {dups})")
if errs:
    print("❌ VERIFIKATION FEHLGESCHLAGEN — NICHTS geschrieben:")
    for e in errs: print("   -", e)
    sys.exit(1)

if "--write" in sys.argv:
    open(ARCH, "w", encoding="utf-8").write(arch_text)
    open(NEW,  "w", encoding="utf-8").write(new_text)
    print(f"✅ geschrieben: BACKLOG.md ({len(new_text.splitlines())} Z.) + BACKLOG-ARCHIVE.md ({len(arch_text.splitlines())} Z.)")
else:
    print(f"✅ DRY-RUN ok — reparse identisch. BACKLOG.md neu: {len(new_text.splitlines())} Z., Archiv: {len(arch_text.splitlines())} Z.")
