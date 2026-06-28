#!/usr/bin/env python3
"""
gen_kanban.py — erzeugt das fotoalert-kanban Artifact-HTML deterministisch aus BACKLOG.md.

Kanonische Lane-Quelle ist das `Status`-Feld des Tickets. Reihenfolge der Auflösung:
  1) Status-Feld vorhanden -> dessen Lane (die einzige hand-editierte Wahrheit)
  2) sonst: "✅ Erledigt"-Sektion / ~~durchgestrichener~~ Titel / Marker [x] -> done  (Archiv)
  3) sonst: Marker [~] -> in progress  (Legacy)
  4) sonst -> inbox
Die 🚦 Pipeline-Steuerung-Board-Tabelle ist KEINE Lane-Quelle mehr (A2): sie wird nicht
gelesen. Lane wird ausschließlich aus dem Status-Feld bzw. den Archiv-Markern abgeleitet.

Workflow (siehe Memory feedback_kanban_sync):
  1. In BACKLOG.md nur das Status-Feld des Tickets setzen
  2. python3 FotoAlert/tools/gen_kanban.py <out>  -> schreibt <out>/fotoalert-kanban.html
  3. mcp__cowork__update_artifact (id: fotoalert-kanban, html_path = die erzeugte Datei)
"""
import sys, os, re, json, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
BACKLOG  = os.path.join(HERE, "..", "BACKLOG.md")
ARCHIVE  = os.path.join(HERE, "..", "BACKLOG-ARCHIVE.md")  # erledigte Tickets, ausgelagert
TEMPLATE = os.path.join(HERE, "kanban_template.html")

def read_backlog():
    """BACKLOG.md + (falls vorhanden) BACKLOG-ARCHIVE.md zusammen lesen.
    Done-Tickets liegen im Archiv; der Generator braucht beide für die vollständige Done-Spalte."""
    t = open(BACKLOG, encoding="utf-8").read()
    if os.path.exists(ARCHIVE):
        t += "\n\n" + open(ARCHIVE, encoding="utf-8").read()
    return t

LANE_KEYS = ["inbox","analysis_ready","analysis","dev_ready","inprogress","test","done","retro","excluded"]

def status_to_key(status):
    s = (status or "").lower()
    if "done" in s:               return "done"
    if "in test" in s:            return "test"
    if "in progress" in s:        return "inprogress"
    if "ready for analysis" in s: return "analysis_ready"
    if "in analysis" in s:        return "analysis"
    if "ready for dev" in s:      return "dev_ready"
    if "excluded" in s:           return "excluded"
    # ToDo / offen / leer / unbekannt -> Inbox
    return "inbox"

ID_RE = re.compile(r'^###\s+(~~)?\s*([A-Z]+-\d+[a-z]?)\s*[·:\-]\s*(.*)$')

def parse_backlog(text):
    lines = text.split("\n")
    tickets = []
    i = 0; n = len(lines); section = ""
    while i < n:
        if lines[i].startswith("## "):
            section = lines[i]
        m = ID_RE.match(lines[i])
        if not m:
            i += 1; continue
        struck = bool(m.group(1)); tid = m.group(2); title = m.group(3).strip()
        mk = re.search(r'\[([ x~])\]\s*`?\s*$', lines[i])
        marker = mk.group(1) if mk else None
        title = re.sub(r'\s*`?\[[ x~]\]`?\s*$', '', title).strip()
        title = re.sub(r'~~\s*$', '', title).strip()
        j = i + 1; body_lines = []
        while j < n and not lines[j].startswith("### ") and not lines[j].startswith("## "):
            body_lines.append(lines[j]); j += 1
        body = "\n".join(body_lines).strip("\n")

        def field(label):
            mm = re.search(r'^\|\s*\*\*' + re.escape(label) + r'\*\*\s*\|\s*(.*?)\s*\|', body, re.M)
            return mm.group(1).strip() if mm else ""

        typ = field("Typ"); prio = field("Priorität"); status = field("Status")
        sec_l = section.lower()
        # Lane-Auflösung: Status-Feld kanonisch, sonst Archiv-Marker
        if status:
            lane = status_to_key(status)
        elif "erledigt" in sec_l or "✅" in section or struck or marker == "x":
            lane = "done"
        elif marker == "~":
            lane = "inprogress"
        else:
            lane = "inbox"

        tickets.append({"id": tid, "title": title, "type": typ,
                        "priority": prio, "lane": lane, "body": body})
        i = j
    return tickets

def main():
    out_dir = sys.argv[1] if len(sys.argv) > 1 else "."
    text = read_backlog()
    tickets = parse_backlog(text)
    template = open(TEMPLATE, encoding="utf-8").read()
    stamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    html = template.replace("__TICKETS_JSON__", json.dumps(tickets, ensure_ascii=False)).replace("__STAMP__", stamp)
    out_path = os.path.join(out_dir, "fotoalert-kanban.html")
    open(out_path, "w", encoding="utf-8").write(html)
    from collections import Counter
    c = Counter(t["lane"] for t in tickets)
    print("Tickets gesamt:", len(tickets), file=sys.stderr)
    for k in LANE_KEYS:
        if c.get(k):
            ids = [t["id"] for t in tickets if t["lane"] == k]
            print(f"  {k:14s} {c[k]:3d}  {', '.join(ids)}", file=sys.stderr)
    print("HTML geschrieben:", out_path, file=sys.stderr)

if __name__ == "__main__":
    main()
