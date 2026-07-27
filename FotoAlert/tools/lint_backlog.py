#!/usr/bin/env python3
"""
lint_backlog.py — Konsistenz-Check für BACKLOG.md VOR jedem Kanban-Push.
Exit 0 = sauber. Exit 1 = Divergenz gefunden (laut abbrechen, nicht still auflösen).
Prüft:
  E1 doppelte Ticket-IDs
  E2 Status-Feld vs. Heading-Marker widersprechen sich (Done<->[x], In Test/Progress<->[~], offen<->[ ])
  E3 Ticket steht in der 🚦 Board-Tabelle in einer anderen Lane als sein Status-Feld sagt
     (fängt die alte Divergenz, solange die Tabelle in der Markdown noch existiert)
  E4 Epic-Dach-Ticket fehlt ODER eine erwartete Kind-Verknüpfung (Epic-Feld) fehlt
     (Verlust-Wächter, siehe EXPECTED_EPICS unten)
  W1 aktives Ticket (nicht done, nicht inbox) ohne Status-Feld
"""
import re, sys, os
from collections import Counter

# --- Epic-Verlust-Wächter (E4) ---------------------------------------------
# Warum: Am 2026-07-23 hat ein Pipeline-Lauf das Security-Epic TASK-92 samt aller
# 12 Kind-Verknüpfungen aus BACKLOG.md überschrieben — der Verlust fiel erst manuell
# auf. Dieser Wächter macht denselben Verlust ab sofort SOFORT rot: er verlangt, dass
# das Dach-Ticket existiert (Typ trägt "Epic") und jedes gelistete Kind ein Epic-Feld
# mit exakt dieser Epic-ID trägt. WICHTIG: Diese Liste beim Anlegen neuer Epics pflegen
# (neues Epic + seine Kinder hier eintragen), sonst wacht der Wächter nur über TASK-92.
EXPECTED_EPICS = {"TASK-92": ["TASK-82","BUG-81","TASK-83","TASK-84","TASK-85","TASK-86","TASK-87","TASK-88","TASK-89","TASK-90","TASK-91","BUG-82"]}
_main = sys.argv[1] if len(sys.argv)>1 else "../../Foto Location Guide/FotoAlert/BACKLOG.md"
text = open(_main, encoding="utf-8").read()
# Archiv (ausgelagerte Done-Tickets) mitprüfen, damit E1-Dup-Check über beide Dateien spannt
_arch = os.path.join(os.path.dirname(os.path.abspath(_main)), "BACKLOG-ARCHIVE.md")
if os.path.exists(_arch):
    text += "\n\n" + open(_arch, encoding="utf-8").read()
lines = text.split("\n")

def lane_name_to_key(name):
    n=name.lower()
    for k,v in [("ready for analysis","analysis_ready"),("in analysis","analysis"),
                ("ready for dev","dev_ready"),("in progress","inprogress"),
                ("in test","test"),("retro","retro"),("excluded","excluded"),
                ("inbox","inbox"),("done","done")]:
        if k in n: return v
    return None
def status_to_key(s):
    s=(s or "").lower()
    for k,v in [("done","done"),("in test","test"),("in progress","inprogress"),
                ("ready for analysis","analysis_ready"),("in analysis","analysis"),
                ("ready for dev","dev_ready"),("excluded","excluded")]:
        if k in s: return v
    return "inbox"
def marker_to_key(mk):
    return {"x":"done","~":"inprogress"," ":"inbox"}.get(mk)

ID_RE=re.compile(r'^###\s+(~~)?\s*([A-Z]+-\d+[a-z]?)\s*[·:\-]')
# board table
board={}
for ln in lines:
    if ln.startswith("|") and "**" in ln:
        cells=[c.strip() for c in ln.strip().strip("|").split("|")]
        if len(cells)>=3:
            key=lane_name_to_key(cells[0])
            if key and key not in ("inbox","retro"):
                for tid in re.findall(r'\b([A-Z]+-\d+)\b', cells[-1]): board[tid]=key

errors=[]; warns=[]; ids=[]
meta={}  # tid -> {"typ":..., "epic":...}  für den Epic-Verlust-Wächter (E4)
i=0;n=len(lines)
while i<n:
    m=ID_RE.match(lines[i])
    if not m: i+=1; continue
    tid=m.group(2); struck=bool(m.group(1)); ids.append(tid)
    mk=re.search(r'\[([ x~])\]\s*`?\s*$', lines[i]); marker=mk.group(1) if mk else None
    j=i+1; body=[]
    while j<n and not lines[j].startswith("### ") and not lines[j].startswith("## "):
        body.append(lines[j]); j+=1
    b="\n".join(body)
    sm=re.search(r'^\|\s*\*\*Status\*\*\s*\|\s*(.*?)\s*\|', b, re.M)
    status=sm.group(1).strip() if sm else ""
    slane=status_to_key(status) if status else None
    # Typ- und Epic-Feld für den Epic-Verlust-Wächter (E4) erfassen
    tm=re.search(r'^\|\s*\*\*Typ\*\*\s*\|\s*(.*?)\s*\|', b, re.M)
    em=re.search(r'^\|\s*\*\*Epic\*\*\s*\|\s*(.*?)\s*\|', b, re.M)
    meta[tid]={"typ":(tm.group(1).strip() if tm else ""),
               "epic":(em.group(1).strip() if em else "")}
    # E2 Status vs Marker — nur Done-Widersprüche sind hart (Marker [ ]/[~] machen keine Lane-Aussage)
    if status:
        if slane=="done" and (marker in (" ","~")):
            errors.append(f"E2 {tid}: Status=Done, aber Marker [{marker}] (sollte [x] sein)")
        if marker=="x" and slane!="done":
            errors.append(f"E2 {tid}: Marker [x] (done), aber Status='{status}' ({slane})")
        if struck and slane!="done":
            errors.append(f"E2 {tid}: Titel ~~durchgestrichen~~ (done), aber Status='{status}' ({slane})")
    # E3 board vs status
    if tid in board and slane and board[tid]!=slane:
        errors.append(f"E3 {tid}: Board-Tabelle sagt {board[tid]}, Status-Feld sagt {slane}")
    # W1 aktiv ohne status
    if not status and not struck and marker!="x" and marker!="~":
        # offen ohne status -> inbox, ok; aber wenn in board aktiv gelistet -> warnen
        if tid in board:
            warns.append(f"W1 {tid}: in Board-Tabelle aktiv ({board[tid]}), aber kein Status-Feld -> landet im Generator in inbox")
    i=j
# E1 dupes
dupes=[k for k,v in Counter(ids).items() if v>1]
for d in dupes: errors.append(f"E1 doppelte ID: {d} ({Counter(ids)[d]}x)")
# E4 Epic-Dach + Kind-Verknüpfungen (Verlust-Wächter, siehe EXPECTED_EPICS oben)
for epic_id, children in EXPECTED_EPICS.items():
    einfo=meta.get(epic_id)
    if not einfo:
        errors.append(f"E4 Epic {epic_id}: Dach-Ticket-Block fehlt komplett (überschrieben/verloren?)")
    elif "epic" not in einfo["typ"].lower():
        errors.append(f"E4 Epic {epic_id}: Ticket existiert, aber Typ-Feld trägt kein 'Epic' (gefunden: '{einfo['typ'] or '—'}')")
    for c in children:
        cinfo=meta.get(c)
        if not cinfo:
            errors.append(f"E4 Epic {epic_id}: Kind-Ticket {c} nicht gefunden (Block fehlt)")
            continue
        ref=re.search(r'[A-Z]+-\d+', cinfo["epic"])
        if not ref or ref.group()!=epic_id:
            errors.append(f"E4 Epic {epic_id}: Kind {c} hat kein Epic-Feld mit {epic_id} (gefunden: '{cinfo['epic'] or '—'}')")

for e in errors: print("❌",e)
for w in warns: print("⚠️ ",w)
print(f"\n{len(ids)} Tickets · {len(errors)} Fehler · {len(warns)} Warnungen")
sys.exit(1 if errors else 0)
