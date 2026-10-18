"""US-141 Baustein 1 (AK-59 bis AK-61): sicheres Schreiben der gemeinsam benutzten Zwischenspeicher.

Der Schalter für Länder und Regionen löst deutlich öfter Nachlade-Läufe aus; dann schreiben mehrere
Prozesse (Vorberechnung als eigener Prozess, Server) dieselben Dateien (opportunities.json,
calendar.json). Bisher schrieb jeder die Zieldatei direkt und ohne Absprache. Jetzt gilt:

  - atomar_schreiben(): erst in eine Temp-Datei im selben Ordner schreiben, auf die Platte zwingen
    (fsync), dann mit os.replace austauschen. Bricht das Schreiben ab (Absturz, Platte voll), bleibt
    die bisherige Datei vollständig lesbar — nie eine halbe Datei. Leser brauchen keine Sperre.
  - datei_sperre(): gegenseitiger Ausschluss über eine Sperrdatei neben der Zieldatei (flock). Zwei
    Läufe, die gleichzeitig Termine verschiedener Orte einmischen, warten aufeinander — der zweite
    liest erst, nachdem der erste fertig geschrieben hat („zuletzt schreibt gewinnt“ entfällt).
  - pruefe_platz_fuer_atomar(): vorab prüfen, ob genug Platz für das atomare Neuschreiben da ist
    (Fehlermeldung statt Abbruch an der vollen Platte).
  - orte_aus_feed_entfernen(): löscht die Termine bestimmter Orte aus der Feed-Datei (BUG-118:
    beim Löschen eines Orts bleibt sonst die Datei auf der Platte unverändert).

Hinweis zum Speicherplatz: Während des Schreibens liegen alte und neue Datei gleichzeitig im Ordner
(bei calendar.json derzeit gut 1 GB je Datei). Die Temp-Datei heißt <Zieldatei>.tmp-<Prozess>-<Thread>;
übrig gebliebene Temp-Dateien eines abgebrochenen Laufs räumt der nächste Schreiber (unter der Sperre) auf.

Nur Standardbibliothek, Python 3.9-kompatibel. Ohne fcntl (kein Linux/macOS) gibt es keine Sperre,
aber weiterhin das atomare Schreiben.
"""
from __future__ import annotations

import contextlib
import json
import logging
import os
import shutil
import threading
import time
from pathlib import Path
from typing import Iterable, Iterator

try:  # pragma: no cover - auf Linux/macOS vorhanden
    import fcntl
except ImportError:  # pragma: no cover
    fcntl = None  # type: ignore[assignment]

logger = logging.getLogger(__name__)

SPERRE_TIMEOUT_S = 900.0      # so lange wartet ein Schreiber höchstens auf die Sperre
_POLL_S = 0.05


class SperreTimeout(RuntimeError):
    """Die Sperre blieb länger als SPERRE_TIMEOUT_S belegt."""


class ZuWenigPlatz(RuntimeError):
    """Auf der Platte ist nicht genug Platz, um die Datei sicher (atomar) neu zu schreiben."""


def _sperrdatei(pfad: Path) -> Path:
    return pfad.with_name(pfad.name + ".lock")


@contextlib.contextmanager
def datei_sperre(pfad, timeout_s: float = SPERRE_TIMEOUT_S) -> Iterator[None]:
    """Exklusive Sperre für `pfad` (gilt zwischen Prozessen UND zwischen Threads)."""
    pfad = Path(pfad)
    if fcntl is None:  # pragma: no cover
        yield
        return
    pfad.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(_sperrdatei(pfad)), os.O_RDWR | os.O_CREAT, 0o600)
    try:
        ende = time.monotonic() + timeout_s
        while True:
            try:
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                break
            except OSError:
                if time.monotonic() >= ende:
                    raise SperreTimeout("Sperre für %s nach %.0f s nicht frei" % (pfad.name, timeout_s))
                time.sleep(_POLL_S)
        try:
            yield
        finally:
            with contextlib.suppress(OSError):
                fcntl.flock(fd, fcntl.LOCK_UN)
    finally:
        os.close(fd)


def pruefe_platz_fuer_atomar(pfad, zusatz_bytes: int = 0, reserve_bytes: int = 256 * 1024 * 1024) -> None:
    """US-141 (Kalender beim Einschalten): Vorab-Prüfung, ob das atomare Neuschreiben von `pfad` gelingen kann.

    Atomar heißt: die neue Datei entsteht neben der alten (Temp-Datei), erst danach wird getauscht. Für einen
    Augenblick liegen also beide im Ordner — gebraucht wird die bisherige Dateigröße plus der Zuwachs
    (`zusatz_bytes`) plus eine Reserve. Reicht der freie Platz nicht, wird `ZuWenigPlatz` mit einem lesbaren
    Text geworfen — es wird NICHTS geschrieben (statt mitten im Schreiben an der vollen Platte zu scheitern).
    Kann der freie Platz nicht ermittelt werden, gilt die Prüfung als bestanden (das Schreiben selbst bleibt
    atomar und räumt bei einem Fehler seine Temp-Datei weg)."""
    pfad = Path(pfad)
    try:
        groesse = pfad.stat().st_size if pfad.exists() else 0
        frei = shutil.disk_usage(str(pfad.parent)).free
    except OSError:
        return
    # eine eventuell vorhandene verwaiste Temp-Datei wird vor dem Schreiben entfernt: sie zählt als frei
    verwaist = 0
    for t in pfad.parent.glob(pfad.name + ".tmp-*"):
        with contextlib.suppress(OSError):
            verwaist += t.stat().st_size
    benoetigt = groesse + max(0, int(zusatz_bytes)) + max(0, int(reserve_bytes))
    if frei + verwaist < benoetigt:
        raise ZuWenigPlatz(
            "zu wenig freier Speicherplatz für %s: gebraucht werden etwa %.1f GB, frei sind %.1f GB"
            % (pfad.name, benoetigt / 1e9, (frei + verwaist) / 1e9))


def _raeume_temp_dateien_auf(pfad: Path) -> None:
    """Entfernt Temp-Dateien abgebrochener Läufe. NUR unter der Sperre aufrufen (dann gibt es keinen
    anderen Schreiber, jede vorhandene Temp-Datei ist verwaist)."""
    for t in pfad.parent.glob(pfad.name + ".tmp-*"):
        try:
            t.unlink()
            logger.warning("Verwaiste Temp-Datei entfernt: %s", t.name)
        except OSError as exc:
            logger.warning("Verwaiste Temp-Datei %s nicht entfernbar: %s", t.name, exc)


def atomar_schreiben(pfad, text: str, encoding: str = "utf-8") -> None:
    """Schreibt `text` atomar nach `pfad` (Temp-Datei im selben Ordner, fsync, os.replace).

    Schlägt irgendein Schritt fehl, bleibt `pfad` unverändert und die Temp-Datei wird entfernt.
    Der Aufrufer hält bei Lese-Ändern-Schreiben-Abläufen selbst die datei_sperre()."""
    pfad = Path(pfad)
    tmp = pfad.with_name("%s.tmp-%d-%d" % (pfad.name, os.getpid(), threading.get_ident()))
    try:
        tmp.write_text(text, encoding=encoding)
        fd = os.open(str(tmp), os.O_RDONLY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)
        os.replace(str(tmp), str(pfad))
    except BaseException:
        with contextlib.suppress(OSError):
            tmp.unlink()
        raise
    # Verzeichniseintrag ebenfalls sichern (best effort)
    with contextlib.suppress(OSError):
        dfd = os.open(str(pfad.parent), os.O_RDONLY)
        try:
            os.fsync(dfd)
        finally:
            os.close(dfd)


def gesperrt_atomar_schreiben(pfad, text: str, encoding: str = "utf-8") -> None:
    """Sperre holen, verwaiste Temp-Dateien wegräumen, atomar schreiben."""
    pfad = Path(pfad)
    with datei_sperre(pfad):
        _raeume_temp_dateien_auf(pfad)
        atomar_schreiben(pfad, text, encoding)


@contextlib.contextmanager
def gesperrt_aendern(pfad) -> Iterator[Path]:
    """Sperre halten, verwaiste Temp-Dateien wegräumen; für Lesen-Ändern-Schreiben:

        with gesperrt_aendern(pfad):
            alt = pfad.read_text(...)
            atomar_schreiben(pfad, neu)
    """
    pfad = Path(pfad)
    with datei_sperre(pfad):
        _raeume_temp_dateien_auf(pfad)
        yield pfad


def orte_aus_feed_entfernen(feed_pfad, orts_ids: Iterable[str]) -> int:
    """Entfernt alle Termine der angegebenen Orte aus der Feed-Datei (BUG-118, AK1).

    Gibt die Zahl entfernter Termine zurück (0, wenn Datei fehlt, unlesbar ist oder nichts zu
    entfernen war — dann wird nichts geschrieben). Die übrigen Orte und die Felder der Datei
    (z. B. computed_at) bleiben unverändert."""
    feed_pfad = Path(feed_pfad)
    ids = {i for i in orts_ids if i}
    if not ids or not feed_pfad.exists():
        return 0
    with gesperrt_aendern(feed_pfad):
        if not feed_pfad.exists():
            return 0
        try:
            daten = json.loads(feed_pfad.read_text(encoding="utf-8"))
            termine = daten.get("opportunities", [])
        except Exception as exc:
            logger.warning("Feed-Datei %s nicht lesbar, Aufräumen übersprungen: %s", feed_pfad.name, exc)
            return 0
        rest = [e for e in termine if e.get("location_id") not in ids]
        entfernt = len(termine) - len(rest)
        if entfernt:
            daten["opportunities"] = rest
            atomar_schreiben(feed_pfad, json.dumps(daten, ensure_ascii=False))
            logger.info("BUG-118: %d Termine von %s aus %s entfernt", entfernt, sorted(ids), feed_pfad.name)
        return entfernt
