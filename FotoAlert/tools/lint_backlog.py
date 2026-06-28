#!/usr/bin/env python3
"""
lint_backlog.py — Konsistenz-Check für BACKLOG.md VOR jedem Kanban-Push.
Exit 0 = sauber. Exit 1 = Divergenz gefunden (laut abbrechen, nicht still auflösen).
Prüft:
  E1 doppelte Ticket-IDs
  E2 Status-Feld vs. Heading-Marker widersprechen sich (Done<->[x], In Test/Progress<->[~], offen<->[ ])
  E3 Ticket steht in der 🚦 Board-Tabelle in einer anderen Lane als sein Status-Feld sagt
     (fängt die alte Divergenz, solange die Tabelle in der Markdown noch existiert)
  W1 aktives Ticket (nicht done, nicht inbox) ohne Status-Feld
"""
import re, sys, os
from collections import Counter
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

for e in errors: print("❌",e)
for w in warns: print("⚠️ ",w)
print(f"\n{len(ids)} Tickets · {len(errors)} Fehler · {len(warns)} Warnungen")
sys.exit(1 if errors else 0)
