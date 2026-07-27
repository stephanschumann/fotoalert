#!/usr/bin/env python3
"""
gate_check.py — deterministischer Schritt-Check VOR jedem Workflow-Schritt.

Prüft am Ticket (Gate-Status-Block, siehe docs/gate-status-konvention.md), ob die
Vorstufen erledigt oder von Stephan gültig übersprungen sind. Vorbild: lint_backlog.py.

Aufruf:
  python3 tools/gate_check.py <TICKET-ID> --phase <impl|test|refactor|verification|release|done|retro>
  python3 tools/gate_check.py <TICKET-ID> --all      # nur Status zeigen, kein Gating

Exit 0 = grün (Schritt darf starten).  Exit 1 = rot (blockieren, fehlenden Schritt anstoßen).
"""
import sys, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
BACKLOG = os.path.join(HERE, "..", "BACKLOG.md")
ARCHIVE = os.path.join(HERE, "..", "BACKLOG-ARCHIVE.md")

# kanonische Gate-Reihenfolge + Label->Key
GATE_ORDER = ["spec", "tests", "impl", "test_pass", "refactor", "product",
              "verification", "release", "retro"]
# Exakte, bekannte Tabellen-Labels je Gate (siehe docs/gate-status-konvention.md).
# Bewusst eine feste Liste literaler Labels statt Fragment-Substring-Matching:
# ein Substring-Check wuerde sowohl unbeteiligte Kopfzeilen-Tabellen (z.B.
# "Spec freigegeben am") faelschlich matchen, als auch bei zu kurzen Fragmenten
# ("refactor" vs. reales Label "Refactor-Check", "product" vs. reales Label
# "PRODUCT.md") am eigentlichen Label vorbeilaufen. Real gefunden bei TASK-86
# (2026-07-22): PRODUCT.md-Zeile wurde nach einem ersten Substring->Exact-Fix
# still nicht mehr erkannt, weil "product.md" != "product" ist.
LABEL_TO_KEY = {
    "spec": "spec",
    "tests definiert": "tests",
    "test bestanden": "test_pass",
    "implementierung": "impl",
    "refactor-check": "refactor",
    "product.md": "product",
    "release": "release",
}
GATE_LABEL = {"spec": "Spec", "tests": "Tests definiert", "impl": "Implementierung",
              "test_pass": "Test bestanden", "refactor": "Refactor-Check",
              "product": "PRODUCT.md", "verification": "Verifikation",
              "release": "Release", "retro": "Retro / Lernen"}
# welches Skill holt einen fehlenden Schritt nach
GATE_SKILL = {"spec": "fotoalert-analyze", "tests": "fotoalert-analyze",
              "impl": "fotoalert-impl", "test_pass": "fotoalert-test",
              "refactor": "fotoalert-refactor", "product": "fotoalert-impl (PRODUCT.md)",
              "verification": "Verifikations-Subagent (Dispatch, kein Skill-Paket)",
              "release": "fotoalert-release (Stephan-Gate)",
              "retro": "retrospective"}
# Vorstufen je Zielphase
REQUIRES = {
    "impl":         ["spec", "tests"],
    "test":         ["spec", "tests", "impl"],
    "refactor":     ["spec", "tests", "impl", "test_pass"],
    "verification": ["spec", "tests", "impl", "test_pass", "refactor", "product"],
    "release":      ["spec", "tests", "impl", "test_pass", "refactor", "product", "verification"],
    "done":         ["spec", "tests", "impl", "test_pass", "refactor", "product", "verification", "release"],
    "retro":        ["spec", "tests", "impl", "test_pass", "refactor", "product", "verification", "release"],
}

ID_RE = re.compile(r'^###\s+(~~)?\s*([A-Z]+-\d+[a-z]?)\s*[·:\-]')
WAIVER_RE = re.compile(r'Stephan\s+\d{4}-\d{2}-\d{2}\s*:')
# Freistehende Marker-Zeilen (Ticket-Fließtext), ergänzend zur Tabellen-Erkennung —
# siehe docs/2026-07-02-pipeline-gate-reliability-design.md §2.1
STANDALONE_RE = re.compile(
    r'^\*\*(Retro(?:\s*/\s*Lernen)?|Refactor-Check|Verifikation):\*\*\s*(✅|⬜|⤼)\s*(.*)$'
)
STANDALONE_KEY = {"retro": "retro", "retro / lernen": "retro",
                  "refactor-check": "refactor", "verifikation": "verification"}


def read_all():
    t = open(BACKLOG, encoding="utf-8").read()
    if os.path.exists(ARCHIVE):
        t += "\n\n" + open(ARCHIVE, encoding="utf-8").read()
    return t


def find_ticket_body(text, tid):
    lines = text.split("\n")
    n = len(lines)
    for i in range(n):
        m = ID_RE.match(lines[i])
        if m and m.group(2) == tid:
            j = i + 1
            while j < n and not ID_RE.match(lines[j]) and not lines[j].startswith("## "):
                j += 1
            return "\n".join(lines[i + 1:j])
    return None


def label_to_key(label):
    l = label.strip().rstrip(":").lower()
    return LABEL_TO_KEY.get(l)


def parse_gate_status(body):
    """liefert dict key -> (status_token, nachweis). status_token in {done,open,waived,waived_invalid}"""
    result = {}
    for ln in body.split("\n"):
        stripped = ln.strip()
        if stripped.startswith("|"):
            cells = [c.strip() for c in stripped.strip("|").split("|")]
            if len(cells) < 2:
                continue
            key = label_to_key(cells[0])
            if not key:
                continue
            status_cell = cells[1]
            nachweis = cells[2] if len(cells) >= 3 else ""
        else:
            m = STANDALONE_RE.match(stripped)
            if not m:
                continue
            key = STANDALONE_KEY.get(m.group(1).lower())
            if not key:
                continue
            status_cell = m.group(2)
            nachweis = m.group(3)
        if "✅" in status_cell:
            tok = "done"
        elif "⤼" in status_cell or "übersprung" in status_cell.lower():
            tok = "waived" if WAIVER_RE.search(nachweis) else "waived_invalid"
        else:
            tok = "open"
        result[key] = (tok, nachweis)
    return result


def main():
    if len(sys.argv) < 2:
        print("Aufruf: gate_check.py <TICKET-ID> --phase <impl|test|refactor|verification|release|done|retro> | --all", file=sys.stderr)
        sys.exit(2)
    tid = sys.argv[1]
    phase = None
    show_all = "--all" in sys.argv
    if "--phase" in sys.argv:
        phase = sys.argv[sys.argv.index("--phase") + 1]

    body = find_ticket_body(read_all(), tid)
    if body is None:
        print("❌ Ticket %s nicht gefunden (BACKLOG.md + ARCHIVE)." % tid)
        sys.exit(1)

    gates = parse_gate_status(body)
    icon = {"done": "✅", "open": "⬜", "waived": "⤼", "waived_invalid": "⚠️ungültig⤼"}

    print("Gate-Status für %s:" % tid)
    if not gates:
        print("  ⛔ Kein Gate-Status-Block gefunden — bitte gemäß docs/gate-status-konvention.md anlegen.")
    for k in GATE_ORDER:
        tok, nw = gates.get(k, ("open", ""))
        print("  %-16s %s  %s" % (GATE_LABEL[k], icon[tok], nw[:60]))

    if show_all or not phase:
        sys.exit(0)

    required = REQUIRES.get(phase)
    if required is None:
        print("\nUnbekannte Phase '%s'. Erlaubt: %s" % (phase, ", ".join(REQUIRES)), file=sys.stderr)
        sys.exit(2)

    missing = []
    for k in required:
        tok = gates.get(k, ("open", ""))[0]
        if tok not in ("done", "waived"):
            missing.append(k)

    print("\nZielphase: %s — verlangt: %s" % (phase, ", ".join(GATE_LABEL[k] for k in required)))
    if not missing:
        print("✅ GRÜN — alle Vorstufen erledigt/übersprungen. Schritt darf starten.")
        sys.exit(0)

    print("⛔ ROT — blockieren. Fehlende Vorstufe(n), zuerst anstoßen:")
    for k in missing:
        print("   • %-16s → nachholen via %s" % (GATE_LABEL[k], GATE_SKILL[k]))
    print("\nFehlende Schritte automatisch im Subagenten nachholen (Stephans Vorgabe),")
    print("außer der Schritt verlangt eine Stephan-Entscheidung (Weg-Gate/Release) → dann fragen.")
    sys.exit(1)


if __name__ == "__main__":
    main()
