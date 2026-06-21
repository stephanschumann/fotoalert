"""TASK-20 — Bug-Reporter mit stabilem Fingerprint, Dedup und Artefakt-Export.

Pure Python, Python-3.9-kompatibel (keine 3.10+-Syntax). Kein Browser, kein Git.

Aufgaben:
  * Finding-Datenstruktur (AK6: view, expected, actual, screenshot_path, timestamp,
    commit_sha, fingerprint).
  * Stabiler Fingerprint = Hash(view + assertion_id + normalisierte message).
    Volatile Felder (Timestamp, Koordinaten, Run-IDs) fließen NICHT ein
    → 2 identische Läufe ⇒ gleicher Fingerprint (AK5).
  * Dedup gegen eine BACKLOG-Textkopie: neuer Fingerprint → neuer '### BUG-XX'-Block
    in der Inbox; existierender offener Fingerprint → Update statt Duplikat.
  * Artefakt-Export: schreibt findings.json. Grüner Lauf (0 Findings) → kein Schreiben
    (AK7, Falsch-Positiv-Schutz).

WICHTIG: Selbsttests operieren immer auf einer temporären BACKLOG-Kopie, nie auf der
echten Datei (siehe test_reporter.py).
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List, Optional


# --- Normalisierung & Fingerprint --------------------------------------------------
# Zahlen mit Dezimalpunkt (Koordinaten, Distanzen, Headings) sind volatil und werden
# vor dem Hash durch einen Platzhalter ersetzt, damit minimale Wertänderungen keinen
# neuen Fingerprint erzeugen.
_FLOAT_RE = re.compile(r"-?\d+\.\d+")
_INT_RE = re.compile(r"\d+")
_WS_RE = re.compile(r"\s+")


def normalize_message(message: str) -> str:
    """Macht eine Assertion-Message dedup-stabil.

    - Floats → <NUM>, restliche Ziffernfolgen → <N> (Koordinaten/Headings raus).
    - Whitespace kollabiert, Trim, lowercase.
    """
    text = _FLOAT_RE.sub("<NUM>", message)
    text = _INT_RE.sub("<N>", text)
    text = _WS_RE.sub(" ", text).strip().lower()
    return text


def compute_fingerprint(view: str, assertion_id: str, message: str) -> str:
    """Stabiler Fingerprint aus (view + assertion_id + normalisierte message).

    Timestamp, commit_sha, Screenshot-Pfad und Koordinaten gehen bewusst NICHT ein.
    """
    basis = "|".join((view, assertion_id, normalize_message(message)))
    return hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]


# --- Finding-Datenstruktur ---------------------------------------------------------
@dataclass
class Finding:
    """Ein einzelner gefundener Defekt (AK6: alle Pflichtfelder)."""

    view: str
    assertion_id: str
    expected: str
    actual: str
    message: str
    screenshot_path: str
    timestamp: str
    commit_sha: str
    fingerprint: str = field(default="")

    def __post_init__(self) -> None:
        # Fingerprint deterministisch ableiten, falls nicht explizit gesetzt.
        if not self.fingerprint:
            self.fingerprint = compute_fingerprint(
                self.view, self.assertion_id, self.message
            )

    def to_dict(self) -> dict:
        return asdict(self)


# --- Inbox-/BACKLOG-Dedup ----------------------------------------------------------
# Wir parsen die BACKLOG-Textkopie zeilenbasiert. Ein Auto-Bug-Block hat die Form:
#   ### BUG-XX · <Titel>  `[ ]`
#   <!-- fp:<fingerprint> status:open -->
#   ... Felder ...
_BUG_HEADER_RE = re.compile(r"^### (BUG-\d+)\b")
_FP_RE = re.compile(r"<!--\s*fp:([0-9a-f]+)\s+status:(\w+)\s*-->")
_INBOX_HEADER_RE = re.compile(r"^##\s*📥?\s*Inbox\b", re.IGNORECASE)


def _next_bug_number(text: str) -> int:
    """Höchste vorhandene BUG-Nummer + 1 (über das ganze Dokument)."""
    nums = [int(m) for m in re.findall(r"### BUG-(\d+)\b", text)]
    return (max(nums) + 1) if nums else 1


def _render_block(bug_id: str, finding: Finding) -> str:
    """Rendert einen vollständigen Auto-Bug-Block (AK6-Felder + fp-Marker)."""
    return (
        "### {bug} · [Auto] {view}: {assertion}  `[ ]`\n"
        "<!-- fp:{fp} status:open -->\n"
        "- **View:** {view}\n"
        "- **Erwartet:** {expected}\n"
        "- **Tatsächlich:** {actual}\n"
        "- **Message:** {message}\n"
        "- **Screenshot:** `{shot}`\n"
        "- **Timestamp:** {ts}\n"
        "- **Commit:** {sha}\n"
        "- **Fingerprint:** `{fp}`\n"
    ).format(
        bug=bug_id,
        view=finding.view,
        assertion=finding.assertion_id,
        fp=finding.fingerprint,
        expected=finding.expected,
        actual=finding.actual,
        message=finding.message,
        shot=finding.screenshot_path,
        ts=finding.timestamp,
        sha=finding.commit_sha,
    )


def _split_blocks(text: str) -> List[str]:
    """Zerlegt den Text in '### '-Blöcke (Header + Body bis zum nächsten Header)."""
    parts: List[str] = []
    current: List[str] = []
    for line in text.splitlines(keepends=True):
        if line.startswith("### ") and current:
            parts.append("".join(current))
            current = [line]
        else:
            current.append(line)
    if current:
        parts.append("".join(current))
    return parts


def _block_fingerprint(block: str) -> Optional[str]:
    m = _FP_RE.search(block)
    return m.group(1) if m else None


def _block_is_open(block: str) -> bool:
    m = _FP_RE.search(block)
    return bool(m) and m.group(2) == "open"


@dataclass
class MergeResult:
    """Ergebnis eines dedup-Merges in die BACKLOG-Kopie."""

    text: str
    created: int = 0
    updated: int = 0


def merge_findings_into_backlog(backlog_text: str, findings: List[Finding]) -> MergeResult:
    """Fügt Findings dedupliziert in die BACKLOG-Textkopie ein.

    - Existierender, offener Block mit gleichem Fingerprint → ersetzt (Update).
    - Sonst → neuer '### BUG-XX'-Block, ans Ende der Inbox-Sektion gehängt
      (Fallback: ans Dokumentende).
    - Schreibt NICHT auf Platte; gibt den neuen Text zurück.
    """
    result = MergeResult(text=backlog_text)
    if not findings:
        return result

    # 1) Updates: bestehende offene Blöcke mit gleichem Fingerprint ersetzen.
    remaining: List[Finding] = []
    text = backlog_text
    for finding in findings:
        blocks = _split_blocks(text)
        replaced = False
        for i, block in enumerate(blocks):
            header = block.splitlines()[0] if block else ""
            m = _BUG_HEADER_RE.match(header)
            if not m:
                continue
            if _block_fingerprint(block) == finding.fingerprint and _block_is_open(block):
                bug_id = m.group(1)
                blocks[i] = _render_block(bug_id, finding)
                # Ursprüngliche Block-Trennzeilen am Ende erhalten.
                if not blocks[i].endswith("\n"):
                    blocks[i] += "\n"
                text = "".join(blocks)
                result.updated += 1
                replaced = True
                break
        if not replaced:
            remaining.append(finding)

    # 2) Neue Blöcke anlegen (fortlaufende BUG-Nummern).
    for finding in remaining:
        bug_no = _next_bug_number(text)
        bug_id = "BUG-{0}".format(bug_no)
        block = "\n" + _render_block(bug_id, finding)
        text = _insert_into_inbox(text, block)
        result.created += 1

    result.text = text
    return result


def _insert_into_inbox(text: str, block: str) -> str:
    """Hängt einen Block ans Ende der Inbox-Sektion an (Fallback: Dokumentende)."""
    lines = text.splitlines(keepends=True)
    inbox_start = None
    for idx, line in enumerate(lines):
        if _INBOX_HEADER_RE.match(line):
            inbox_start = idx
            break
    if inbox_start is None:
        # Keine Inbox-Sektion → ans Ende.
        sep = "" if text.endswith("\n") else "\n"
        return text + sep + block

    # Nächste '## '-Sektion nach der Inbox finden → davor einfügen.
    insert_at = len(lines)
    for idx in range(inbox_start + 1, len(lines)):
        if lines[idx].startswith("## "):
            insert_at = idx
            break
    head = "".join(lines[:insert_at])
    tail = "".join(lines[insert_at:])
    if head and not head.endswith("\n"):
        head += "\n"
    return head + block + "\n" + tail


# --- Artefakt-Export & Top-Level-API -----------------------------------------------
def export_findings_json(findings: List[Finding], out_path) -> bool:
    """Schreibt findings.json. Leere Liste → KEIN Schreibvorgang (AK7).

    Gibt True zurück, wenn geschrieben wurde.
    """
    if not findings:
        return False
    path = Path(out_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "count": len(findings),
        "findings": [f.to_dict() for f in findings],
    }
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return True


def report(
    findings: List[Finding],
    backlog_path=None,
    findings_json_path=None,
) -> MergeResult:
    """Kompletter Report-Schritt für einen Lauf.

    - Immer: Artefakt findings.json (außer grün → AK7).
    - Optional (lokal): Dedup-Merge in eine BACKLOG-Textkopie unter backlog_path.
      In CI wird backlog_path bewusst NICHT übergeben (keine Commits).
    - Grüner Lauf (0 Findings): kein JSON, kein BACKLOG-Schreibvorgang (AK7).
    """
    # Artefakt.
    if findings_json_path is not None:
        export_findings_json(findings, findings_json_path)

    # Optionaler lokaler BACKLOG-Merge (nie in CI).
    if backlog_path is not None and findings:
        bpath = Path(backlog_path)
        original = bpath.read_text(encoding="utf-8")
        merged = merge_findings_into_backlog(original, findings)
        if merged.created or merged.updated:
            bpath.write_text(merged.text, encoding="utf-8")
        return merged

    return MergeResult(text="", created=0, updated=0)
