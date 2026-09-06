from __future__ import annotations

import json
import mimetypes
import os
import re
import sys
import threading
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
OVERLAY_DIR = ROOT / "overlay"
CONFIG_PATH = ROOT / "config.json"
DEMO_COUNTER_PATH = ROOT / "data" / "counter.json"

DEFAULT_CONFIG = {
    "port": 8765,
    "counter_file": "",
    "refresh_ms": 250,
}


def load_config() -> dict:
    config = DEFAULT_CONFIG.copy()
    try:
        config.update(json.loads(CONFIG_PATH.read_text(encoding="utf-8")))
    except FileNotFoundError:
        CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"[WARN] Nie udało się odczytać config.json: {exc}")
    return config


def steam_root_from_registry() -> Path | None:
    if os.name != "nt":
        return None
    try:
        import winreg

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
            value, _ = winreg.QueryValueEx(key, "SteamPath")
        return Path(value)
    except Exception:
        return None


def steam_libraries() -> list[Path]:
    libraries: list[Path] = []
    root = steam_root_from_registry()

    candidates = []
    if root:
        candidates.append(root)
    candidates.extend(
        [
            Path(r"C:\Program Files (x86)\Steam"),
            Path(r"C:\Program Files\Steam"),
        ]
    )

    seen: set[str] = set()
    for candidate in candidates:
        key = str(candidate).lower()
        if key in seen or not candidate.exists():
            continue
        seen.add(key)
        libraries.append(candidate)

        vdf = candidate / "steamapps" / "libraryfolders.vdf"
        if not vdf.exists():
            continue
        try:
            text = vdf.read_text(encoding="utf-8", errors="ignore")
            for match in re.finditer(r'"path"\s+"([^"]+)"', text):
                path = Path(match.group(1).replace(r"\\", "\\"))
                path_key = str(path).lower()
                if path_key not in seen and path.exists():
                    seen.add(path_key)
                    libraries.append(path)
        except Exception:
            pass

    return libraries


def auto_find_counter() -> Path | None:
    relative = Path(
        "steamapps/common/The Blood of Dawnwalker/"
        "Dawnwalker/Binaries/Win64/ue4ss/Mods/"
        "DawnwalkerDeathCounter/counter.txt"
    )

    for library in steam_libraries():
        candidate = library / relative
        if candidate.exists():
            return candidate

    # Awaryjne sprawdzenie popularnych bibliotek na innych dyskach.
    if os.name == "nt":
        for drive_letter in "CDEFGHIJKLMNOPQRSTUVWXYZ":
            drive = Path(f"{drive_letter}:/")
            for steam_dir in ("Steam", "SteamLibrary", "Games/Steam"):
                candidate = drive / steam_dir / relative
                if candidate.exists():
                    return candidate

    return None


def resolve_counter_path(config: dict) -> Path | None:
    configured = str(config.get("counter_file", "")).strip()
    if configured:
        path = Path(os.path.expandvars(os.path.expanduser(configured)))
        if path.exists():
            return path
        print(f"[WARN] counter_file z config.json nie istnieje: {path}")

    return auto_find_counter()


def read_death_count(path: Path | None) -> tuple[int, str]:
    if path and path.exists():
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
            match = re.search(r"-?\d+", text)
            if match:
                return max(0, int(match.group(0))), "game"
        except Exception:
            pass

    try:
        data = json.loads(DEMO_COUNTER_PATH.read_text(encoding="utf-8"))
        return max(0, int(data.get("deaths", 0))), "demo"
    except Exception:
        return 0, "demo"


CONFIG = load_config()
COUNTER_PATH = resolve_counter_path(CONFIG)
LAST_COUNTER_SCAN = 0.0
REFRESH_MS = max(100, int(CONFIG.get("refresh_ms", 250)))


def get_counter_path() -> Path | None:
    global COUNTER_PATH, LAST_COUNTER_SCAN

    if COUNTER_PATH and COUNTER_PATH.exists():
        return COUNTER_PATH

    now = time.monotonic()
    if now - LAST_COUNTER_SCAN >= 3.0:
        LAST_COUNTER_SCAN = now
        found = resolve_counter_path(CONFIG)
        if found:
            if COUNTER_PATH != found:
                print(f"[OK] Wykryto licznik gry: {found}")
            COUNTER_PATH = found

    return COUNTER_PATH


class OverlayHandler(BaseHTTPRequestHandler):
    server_version = "DawnwalkerOverlay/1.0"

    def log_message(self, format: str, *args) -> None:
        # Ograniczamy spam w konsoli OBS/servera.
        return

    def send_bytes(self, data: bytes, content_type: str, status: int = 200) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        route = parsed.path

        if route == "/api/counter":
            current_counter = get_counter_path()
            deaths, source = read_death_count(current_counter)
            payload = json.dumps(
                {
                    "deaths": deaths,
                    "source": source,
                    "refresh_ms": REFRESH_MS,
                    "counter_found": bool(current_counter and current_counter.exists()),
                },
                ensure_ascii=False,
            ).encode("utf-8")
            self.send_bytes(payload, "application/json; charset=utf-8")
            return

        if route in ("/", "/index.html"):
            requested = OVERLAY_DIR / "index.html"
        else:
            requested = OVERLAY_DIR / route.lstrip("/")

        try:
            requested = requested.resolve()
            overlay_root = OVERLAY_DIR.resolve()
            if overlay_root not in requested.parents and requested != overlay_root:
                raise ValueError("Path traversal")
            if not requested.is_file():
                self.send_bytes(b"Not found", "text/plain; charset=utf-8", 404)
                return

            mime, _ = mimetypes.guess_type(str(requested))
            self.send_bytes(requested.read_bytes(), mime or "application/octet-stream")
        except Exception:
            self.send_bytes(b"Not found", "text/plain; charset=utf-8", 404)


def main() -> None:
    port = int(CONFIG.get("port", 8765))
    address = ("127.0.0.1", port)

    print("=" * 58)
    print("  THE BLOOD OF DAWNWALKER - DEATH OVERLAY")
    print("=" * 58)
    if COUNTER_PATH:
        print(f"[OK] Licznik gry: {COUNTER_PATH}")
    else:
        print("[INFO] Nie znaleziono counter.txt - działa tryb DEMO.")
        print("       Ustaw counter_file w config.json lub uruchom grę z modem.")
    print(f"[OBS] http://127.0.0.1:{port}")
    print("[INFO] Zostaw to okno otwarte podczas streama.")
    print("[INFO] Ctrl+C zamyka serwer.")
    print("=" * 58)

    try:
        server = ThreadingHTTPServer(address, OverlayHandler)
    except OSError as exc:
        print(f"[BLAD] Nie można uruchomić portu {port}: {exc}")
        input("Enter, aby zamknąć...")
        return

    try:
        server.serve_forever(poll_interval=0.5)
    except KeyboardInterrupt:
        print("\n[INFO] Zamykam overlay...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
