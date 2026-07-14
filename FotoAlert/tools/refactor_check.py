#!/usr/bin/env python3
"""
FotoAlert Refactoring-Check
============================
Statische Code-Qualitäts-Analyse für Backend (AST + pyflakes) und Frontend (Regex).

Usage:
  python3 tools/refactor_check.py --report        # JSON-Report ausgeben
  python3 tools/refactor_check.py --fix           # Auto-fixable Findings direkt anwenden
  python3 tools/refactor_check.py --fix --dry-run # Auto-Fixes anzeigen ohne Anwenden

Exit codes: 0 = clean, 1 = findings (auto-fixable or needs-ticket), 2 = error
"""

from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).parent.parent
BACKEND_ROOT = REPO_ROOT / "backend"
FRONTEND_FILE = REPO_ROOT / "web" / "index.html"

BACKEND_FILES = [
    f for f in [
        BACKEND_ROOT / "main.py",
        BACKEND_ROOT / "precompute.py",
        BACKEND_ROOT / "auth.py",
        BACKEND_ROOT / "scheduler.py",
        BACKEND_ROOT / "data" / "store.py",
        BACKEND_ROOT / "calculations" / "sun.py",
        BACKEND_ROOT / "calculations" / "moon.py",
        BACKEND_ROOT / "calculations" / "weather.py",
        BACKEND_ROOT / "discover" / "pipeline.py",
        BACKEND_ROOT / "discover" / "sun_pipeline.py",
        BACKEND_ROOT / "discover" / "moon_pipeline.py",
        BACKEND_ROOT / "discover" / "geometry.py",
        BACKEND_ROOT / "discover" / "subjects.py",
    ]
    if f.exists()
]

LONG_FN_THRESHOLD = 80   # Zeilen
ANNOTATION_MIN_RATIO = 0.5  # < 50% annotiert → Ticket

# Begründete Ausnahmen: Funktionen die bewusst nicht aufgeteilt werden.
# Format: (datei_suffix, funktionsname)
# _serialize: reines Dict-Literal ohne Verhalten — Split verschlechtert Lesbarkeit.
# sun_pipeline.run / moon_pipeline.run: State (pos_cache, body-Scores) zu eng verwoben.
LONG_FN_ALLOWLIST: set[tuple[str, str]] = {
    ("precompute.py", "_serialize"),
    ("sun_pipeline.py", "run"),
    ("moon_pipeline.py", "run"),
}

# ---------------------------------------------------------------------------
# Backend-Analyse
# ---------------------------------------------------------------------------

def _run_pyflakes(path: Path) -> list[dict]:
    """Führt pyflakes aus und parst die Ausgabe."""
    findings = []
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pyflakes", str(path)],
            capture_output=True, text=True
        )
        for line in result.stdout.splitlines():
            # Format: path:line:col: message
            parts = line.split(":", 3)
            if len(parts) >= 3:
                try:
                    lineno = int(parts[1].strip())
                except ValueError:
                    lineno = 0
                message = parts[-1].strip() if len(parts) == 4 else line
                findings.append({
                    "file": str(path.relative_to(REPO_ROOT)),
                    "line": lineno,
                    "message": message,
                    "raw": line,
                })
    except Exception as e:
        findings.append({"file": str(path), "line": 0, "message": f"pyflakes error: {e}", "raw": ""})
    return findings


def _analyze_ast(path: Path) -> tuple[list[dict], list[dict]]:
    """
    AST-Analyse: lange Funktionen + fehlende Return-Annotationen.
    Returns: (long_functions, missing_annotations)
    """
    long_fns = []
    missing_ann = []
    try:
        src = path.read_text()
        tree = ast.parse(src)
    except Exception as e:
        return [], [{"file": str(path), "line": 0, "message": f"parse error: {e}"}]

    rel = str(path.relative_to(REPO_ROOT))
    total = 0
    unannotated = 0

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        total += 1
        length = node.end_lineno - node.lineno

        if length > LONG_FN_THRESHOLD:
            file_base = Path(rel).name
            if (file_base, node.name) in LONG_FN_ALLOWLIST:
                pass  # begründete Ausnahme — kein Finding
            else:
                long_fns.append({
                    "file": rel,
                    "line": node.lineno,
                    "name": node.name,
                    "lines": length,
                    "message": f"Funktion `{node.name}()` ist {length} Zeilen lang (Threshold: {LONG_FN_THRESHOLD})",
                })

        if node.returns is None:
            unannotated += 1

    if total > 0 and unannotated / total > (1 - ANNOTATION_MIN_RATIO):
        missing_ann.append({
            "file": rel,
            "line": 0,
            "name": "__annotations__",
            "ratio": f"{total - unannotated}/{total}",
            "message": f"Nur {total - unannotated}/{total} Funktionen haben Return-Annotationen",
        })

    return long_fns, missing_ann


def analyze_backend() -> dict:
    """Vollständige Backend-Analyse. Returns dict mit auto_fixable + needs_ticket."""
    auto_fixable = []
    needs_ticket = []

    for path in BACKEND_FILES:
        # Pyflakes → meist auto-fixable (unused imports, tote globals)
        for finding in _run_pyflakes(path):
            msg = finding["message"].lower()
            is_unused_import = "imported but unused" in msg
            is_dead_global = "global" in msg and "unused" in msg
            if is_unused_import or is_dead_global:
                finding["category"] = "unused_import" if is_unused_import else "dead_global"
                finding["fix_hint"] = "Import / global-Statement entfernen"
                auto_fixable.append(finding)
            else:
                finding["category"] = "pyflakes_other"
                needs_ticket.append(finding)

        # AST → lange Funktionen (Ticket), fehlende Annotationen (Ticket, gebündelt)
        long_fns, missing_ann = _analyze_ast(path)
        for f in long_fns:
            f["category"] = "long_function"
            needs_ticket.append(f)
        for f in missing_ann:
            f["category"] = "missing_annotations"
            needs_ticket.append(f)

    return {"auto_fixable": auto_fixable, "needs_ticket": needs_ticket}


# ---------------------------------------------------------------------------
# Frontend-Analyse (Regex-Heuristiken)
# ---------------------------------------------------------------------------

def _strip_js_noncode(lines: list[str]) -> list[str]:
    """Entfernt String- und Kommentarinhalte aus JS-Quellzeilen (einfache State-
    Machine, behandelt auch mehrzeilige Block-Kommentare `/* ... */`), damit eine
    nachfolgende Klammer-Zählung nicht durch `{`/`}` innerhalb von Strings oder
    Kommentaren verfälscht wird. Kein echter Tokenizer (Template-Literal-
    Interpolationen `${...}` werden wie normaler String-Inhalt behandelt, nicht
    als eingebetteter Code) — für reine Klammer-Balance-Zwecke ausreichend genau."""
    out: list[str] = []
    in_block_comment = False
    for raw in lines:
        result: list[str] = []
        i = 0
        n = len(raw)
        in_string: str | None = None
        while i < n:
            ch = raw[i]
            if in_block_comment:
                if ch == '*' and i + 1 < n and raw[i + 1] == '/':
                    in_block_comment = False
                    i += 2
                    continue
                i += 1
                continue
            if in_string:
                if ch == '\\':
                    i += 2
                    continue
                if ch == in_string:
                    in_string = None
                i += 1
                continue
            if ch == '/' and i + 1 < n and raw[i + 1] == '/':
                break  # Rest der Zeile ist Line-Kommentar
            if ch == '/' and i + 1 < n and raw[i + 1] == '*':
                in_block_comment = True
                i += 2
                continue
            if ch in ("'", '"', '`'):
                in_string = ch
                i += 1
                continue
            result.append(ch)
            i += 1
        out.append(''.join(result))
    return out


def _function_real_length(code_only_lines: list[str], start_idx0: int) -> int | None:
    """Ermittelt die tatsächliche Länge einer Funktion ab ihrer Signaturzeile durch
    Klammer-Zählung auf bereits von Strings/Kommentaren bereinigten Zeilen
    (`_strip_js_noncode`) — statt der alten Heuristik "Abstand bis zur nächsten
    erkannten Funktion" (TASK-32-Limitation, erzeugte Falsch-Positive bis 1400
    Zeilen bei kurzen Utility-Funktionen/Closures neben anderen Funktionen, z.B.
    `haversineKm`, `localBoundsRadius`). `start_idx0` ist 0-basiert.
    Gibt die 1-basierte Zeilenanzahl bis zur schließenden `}` zurück, oder `None`
    wenn keine öffnende `{` gefunden wird (z.B. einzeilige Arrow-Function ohne
    Block-Body wie `const f = x => x + 1`) — dann greift der Aufrufer auf die
    alte Distanz-Heuristik als Fallback zurück."""
    depth = 0
    seen_open = False
    for offset, cleaned in enumerate(code_only_lines[start_idx0:]):
        for c in cleaned:
            if c == '{':
                depth += 1
                seen_open = True
            elif c == '}':
                depth -= 1
                if seen_open and depth <= 0:
                    return offset + 1
    return None


def analyze_frontend() -> dict:
    """Regex-basierte Analyse von web/index.html."""
    auto_fixable = []
    needs_ticket = []

    if not FRONTEND_FILE.exists():
        return {"auto_fixable": [], "needs_ticket": []}

    src = FRONTEND_FILE.read_text()
    lines = src.splitlines()
    rel = str(FRONTEND_FILE.relative_to(REPO_ROOT))

    # 1. console.log in Produktion
    for i, line in enumerate(lines, 1):
        if re.search(r'console\.log\(', line) and "//DEBUG" not in line:
            auto_fixable.append({
                "file": rel,
                "line": i,
                "category": "console_log",
                "message": f"console.log() in Zeile {i} (Prod-Code)",
                "fix_hint": "Zeile entfernen oder mit //DEBUG markieren",
                "raw": line.strip(),
            })

    # 2. Duplizierte Inline-Event-Handler (addEventListener für selben Typ > 3×)
    event_types: dict[str, list[int]] = {}
    for i, line in enumerate(lines, 1):
        m = re.search(r"addEventListener\(['\"](\w+)['\"]", line)
        if m:
            evt = m.group(1)
            event_types.setdefault(evt, []).append(i)
    for evt, linenos in event_types.items():
        if len(linenos) > 5:
            needs_ticket.append({
                "file": rel,
                "line": linenos[0],
                "category": "duplicate_event_listeners",
                "message": f"addEventListener('{evt}') erscheint {len(linenos)}× — ggf. delegieren",
                "occurrences": linenos,
            })

    # 3. Sehr lange JS-Funktionen im Frontend (>100 Zeilen realer Funktionskörper)
    #
    # FIX (US-117-Retro, 2026-07-05) — löst die TASK-32-Limitation an der Wurzel:
    # Die Länge wird jetzt per echter Klammer-Zählung ermittelt (`_function_real_length`
    # auf `_strip_js_noncode`-bereinigten Zeilen: Klammern in Strings/Kommentaren zählen
    # nicht mit), nicht mehr als "Abstand bis zur nächsten erkannten Funktion". Die alte
    # Distanz-Heuristik lief bei verschachtelten Closures/IIFEs oft bis in die nächste
    # Top-Level-Funktion oder Sektion und erzeugte Werte von 100–1400 Zeilen für
    # tatsächlich 1–12-zeilige Funktionen (z.B. `haversineKm`, `localBoundsRadius`).
    # Die Distanz-Heuristik dient nur noch als Fallback, wenn keine öffnende `{`
    # gefunden wird (z.B. einzeilige Arrow-Function ohne Block-Body).
    #
    # FRONTEND_LONG_FN_IGNORELIST bleibt als Sicherheitsnetz bestehen (z.B. falls die
    # Klammer-Zählung durch ein Template-Literal mit `${...}`-Interpolation doch einmal
    # danebenliegt) — mit der Klammer-Zählung sollte sie aber i.d.R. nicht mehr wachsen
    # müssen, da die zugrunde liegende Fehlmessung behoben ist.
    FRONTEND_LONG_FN_IGNORELIST: set[str] = {
        "_showError",   # lokale Arrow-Function in Feed.load() — tatsächlich 7 Zeilen
        "haversineKm",  # reine Berechnungsfunktion — tatsächlich 7 Zeilen
        "onUp",         # Closure in initDualSlider.drag() — tatsächlich 5 Zeilen
        "state3",       # Closure in FilterSheet._render() — tatsächlich 2 Zeilen
        "mkSec",        # Top-Level Template-Helper — tatsächlich 3 Zeilen
        "axisPhrase",   # Closure im Location-Detail IIFE — tatsächlich 10 Zeilen
        "local",        # IIFE-Variable in CameraFOV._loadProfile() — tatsächlich 1 Zeile (TASK-43)
        "row",          # lokale Arrow-Function in AstroMap.render() — tatsächlich 12 Zeilen (TASK-43)
        "ic",               # globale Top-Level Icon-Helper-Function — tatsächlich 4 Zeilen (TASK-49)
        "handler",          # Closure in ThemeManager.init() — tatsächlich 1 Zeile, komplett einzeilig (TASK-49)
        "verState",         # Closure in FilterSheet._render() — tatsächlich 5 Zeilen (TASK-49)
        "sectorPath",       # Closure in IIFE mkCloudCompassSvg() — tatsächlich 11 Zeilen (TASK-49)
        "azDiffFn",         # Closure in Location-Detail-IIFE — tatsächlich 1 Zeile, komplett einzeilig (TASK-49)
        "sunAlignmentLabel",  # globale Top-Level-Function — tatsächlich 9 Zeilen (TASK-49)
        "localBoundsRadius",  # reine Berechnungsfunktion neben haversineKm — tatsächlich 10 Zeilen (US-117)
    }

    fn_pattern = re.compile(r'^\s*(async\s+)?function\s+(\w+)|(\w+)\s*[:=]\s*(async\s+)?(?:function|\([^)]*\)\s*=>)')
    fn_starts: list[tuple[int, str]] = []
    for i, line in enumerate(lines, 1):
        m = fn_pattern.search(line)
        if m:
            name = m.group(2) or m.group(3) or "anonymous"
            fn_starts.append((i, name))

    code_only_lines = _strip_js_noncode(lines)

    for idx, (start, name) in enumerate(fn_starts):
        real_length = _function_real_length(code_only_lines, start - 1)
        if real_length is not None:
            length = real_length
        else:
            # Fallback: keine öffnende '{' gefunden (z.B. einzeilige Arrow-Function
            # ohne Block-Body) — alte Distanz-Heuristik als Notlösung.
            end = fn_starts[idx + 1][0] if idx + 1 < len(fn_starts) else len(lines)
            length = end - start
        if length > 100:
            if name in FRONTEND_LONG_FN_IGNORELIST:
                continue  # Sicherheitsnetz (siehe Kommentar oben) — sollte mit Klammer-Zählung kaum noch greifen
            needs_ticket.append({
                "file": rel,
                "line": start,
                "name": name,
                "lines": length,
                "category": "long_function",
                "message": f"JS-Funktion `{name}()` ist ~{length} Zeilen lang",
            })

    # 4. Sections-Default-Regression-Guard (TASK-40)
    #
    # BUG-40-Klasse: Eine aufklappbare Section wird gerendert, aber ihr Standardzustand
    # fehlt in Sections._def → sie bleibt stumm eingeklappt, ohne Fehler. Zusätzlich
    # erzwingt Option B die einheitliche Bauweise: jede Section MUSS über mkSec() gebaut
    # werden, nicht hand-gerollt via literalem Sections.toggle('id').
    #
    # Marker im Source:
    #   mkSec('id', ...)        → korrekt gebaute Section
    #   Sections.toggle('id')   → hand-gerollter Toggle-Header (Option B: verboten).
    #       Der mkSec-INTERNE toggle nutzt '${id}' und matcht das Literal-Pattern NICHT.
    #   Sections.isOpen('id')   → legitimer Lazy-Render-Check, KEIN Section-Marker.
    mksec_ids = set(re.findall(r"mkSec\(\s*'([^']+)'", src))
    handrolled_ids = set(re.findall(r"Sections\.toggle\('([a-z_]+)'\)", src))
    rendered_ids = mksec_ids | handrolled_ids

    def_keys: set[str] = set()
    def_match = re.search(r"_def:\s*\{(.*?)\}", src, re.S)
    if def_match:
        def_keys = set(re.findall(r"(\w+)\s*:", def_match.group(1)))

    # Rule A — gerenderte Section ohne _def-Eintrag (BUG-40-Klasse) → harter Fehler
    for sid in sorted(rendered_ids - def_keys):
        needs_ticket.append({
            "file": rel,
            "line": 0,
            "category": "section_missing_default",
            "message": f"Section '{sid}' wird gerendert, fehlt aber in Sections._def "
                       f"→ bliebe stumm eingeklappt (BUG-40-Klasse). _def-Eintrag ergänzen.",
        })

    # Rule B — hand-gerollte Section statt mkSec() (Option B: einheitliche Bauweise) → harter Fehler
    for sid in sorted(handrolled_ids):
        needs_ticket.append({
            "file": rel,
            "line": 0,
            "category": "section_handrolled",
            "message": f"Section '{sid}' wird hand-gerollt via Sections.toggle('{sid}') statt "
                       f"über mkSec() gebaut → auf mkSec() umstellen (TASK-40, Option B).",
        })

    return {"auto_fixable": auto_fixable, "needs_ticket": needs_ticket}


# ---------------------------------------------------------------------------
# Auto-Fix
# ---------------------------------------------------------------------------

def apply_auto_fixes(findings: list[dict], dry_run: bool = False) -> list[dict]:
    """
    Wendet auto-fixable Findings an (unused imports, tote globals, console.log).
    Returns Liste der angewendeten Fixes.
    """
    # Gruppiere nach Datei + Zeile, sortiere rückwärts (von unten nach oben, damit Zeilennummern stabil)
    by_file: dict[str, list[dict]] = {}
    for f in findings:
        by_file.setdefault(f["file"], []).append(f)

    applied = []
    for rel_path, file_findings in by_file.items():
        path = REPO_ROOT / rel_path
        if not path.exists():
            continue
        lines = path.read_text().splitlines(keepends=True)

        # Sortiere Findings rückwärts nach Zeile
        to_remove = sorted(
            [f for f in file_findings if f.get("line", 0) > 0],
            key=lambda x: x["line"],
            reverse=True
        )

        for finding in to_remove:
            lineno = finding["line"] - 1  # 0-indexed
            if 0 <= lineno < len(lines):
                original = lines[lineno]
                if dry_run:
                    print(f"[DRY-RUN] {rel_path}:{finding['line']} → entfernen: {original.rstrip()}")
                else:
                    lines[lineno] = ""  # Zeile leeren (statt löschen, um Zeilennummern zu erhalten)
                applied.append({**finding, "action": "removed_line", "original": original.rstrip()})

        if not dry_run and applied:
            path.write_text("".join(lines))

    return applied


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def build_report() -> dict:
    backend = analyze_backend()
    frontend = analyze_frontend()

    auto_fixable = backend["auto_fixable"] + frontend["auto_fixable"]
    needs_ticket = backend["needs_ticket"] + frontend["needs_ticket"]

    return {
        "summary": {
            "auto_fixable": len(auto_fixable),
            "needs_ticket": len(needs_ticket),
            "clean": len(auto_fixable) == 0 and len(needs_ticket) == 0,
        },
        "auto_fixable": auto_fixable,
        "needs_ticket": needs_ticket,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    import argparse
    parser = argparse.ArgumentParser(description="FotoAlert Code-Quality-Check")
    parser.add_argument("--report", action="store_true", help="JSON-Report ausgeben")
    parser.add_argument("--fix", action="store_true", help="Auto-Fixes anwenden")
    parser.add_argument("--dry-run", action="store_true", help="Fixes anzeigen ohne Anwenden")
    args = parser.parse_args()

    report = build_report()

    if args.report or not args.fix:
        if report["summary"]["clean"]:
            print(json.dumps({"status": "✅ Keine Smells gefunden"}, ensure_ascii=False, indent=2))
        else:
            print(json.dumps(report, ensure_ascii=False, indent=2))

    if args.fix:
        if not report["auto_fixable"]:
            print("Keine auto-fixable Findings.")
        else:
            applied = apply_auto_fixes(report["auto_fixable"], dry_run=args.dry_run)
            action = "Würde anwenden" if args.dry_run else "Angewendet"
            print(f"\n{action}: {len(applied)} Fix(es)")
            for f in applied:
                print(f"  ✏️  {f['file']}:{f['line']} — {f['message']}")

        if report["needs_ticket"]:
            print(f"\n{len(report['needs_ticket'])} Finding(s) brauchen ein Ticket:")
            for f in report["needs_ticket"]:
                print(f"  📋 [{f['category']}] {f['file']}:{f.get('line',0)} — {f['message']}")

    return 0 if report["summary"]["clean"] else 1


if __name__ == "__main__":
    sys.exit(main())
