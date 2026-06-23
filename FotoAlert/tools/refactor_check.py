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

    # 3. Sehr lange JS-Funktionen im Frontend (>100 Zeilen zwischen function/=> und })
    fn_pattern = re.compile(r'^\s*(async\s+)?function\s+(\w+)|(\w+)\s*[:=]\s*(async\s+)?(?:function|\([^)]*\)\s*=>)')
    fn_starts: list[tuple[int, str]] = []
    for i, line in enumerate(lines, 1):
        m = fn_pattern.search(line)
        if m:
            name = m.group(2) or m.group(3) or "anonymous"
            fn_starts.append((i, name))

    for idx, (start, name) in enumerate(fn_starts):
        end = fn_starts[idx + 1][0] if idx + 1 < len(fn_starts) else len(lines)
        length = end - start
        if length > 100:
            needs_ticket.append({
                "file": rel,
                "line": start,
                "name": name,
                "lines": length,
                "category": "long_function",
                "message": f"JS-Funktion `{name}()` ist ~{length} Zeilen lang",
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
