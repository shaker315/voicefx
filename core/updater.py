import json
import os
import sys
import tempfile
import urllib.request
import subprocess
import time


def _parse_version(v):
    parts = []
    for p in str(v).split("."):
        if not p.isdigit():
            return ()
        parts.append(int(p))
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def _is_newer(remote, local):
    r = _parse_version(remote)
    l = _parse_version(local)
    if not r or not l:
        return False
    return r > l


def _fetch_text(url, timeout=10):
    final_url = url
    sep = "&" if "?" in url else "?"
    final_url = f"{url}{sep}_t={int(time.time())}"
    req = urllib.request.Request(
        final_url,
        headers={
            "User-Agent": "VoiceFX-Updater/1.0",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8")


def check_for_update(current_version, version_url):
    try:
        data = _fetch_text(version_url, timeout=10)
        info = json.loads(data)
        remote_version = info.get("version", "")
        url = info.get("url", "") or info.get("download_url", "")
        if not remote_version or not url:
            return None
        if _is_newer(remote_version, current_version):
            return {"version": remote_version, "url": url}
    except Exception:
        return None
    return None


def _download(url, dest_path, progress_cb=None, status_cb=None, cancel_event=None):
    try:
        if status_cb:
            status_cb("Pobieranie...")

        with urllib.request.urlopen(url, timeout=10) as r:
            total = int(r.headers.get("Content-Length", "0") or 0)
            downloaded = 0
            chunk_size = 64 * 1024
            started_at = time.monotonic()
            if progress_cb and total == 0:
                progress_cb(0, 0, 0, 0)

            with open(dest_path, "wb") as f:
                while True:
                    if cancel_event and cancel_event.is_set():
                        return False, "Anulowano"
                    chunk = r.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_cb and total > 0:
                        percent = int((downloaded / total) * 100)
                        elapsed = max(0.001, time.monotonic() - started_at)
                        speed = downloaded / elapsed
                        progress_cb(percent, downloaded, total, speed)

        if progress_cb:
            elapsed = max(0.001, time.monotonic() - started_at)
            speed = downloaded / elapsed
            progress_cb(100, downloaded, total, speed)
        return True, ""
    except Exception as e:
        return False, str(e)


def _is_installer(url):
    name = os.path.basename(url).lower()
    return name.endswith(".exe") and ("setup" in name or "installer" in name)


def start_update(url, progress_cb=None, status_cb=None, cancel_event=None):
    exe_path = sys.executable
    if not os.path.isfile(exe_path) or not exe_path.lower().endswith(".exe"):
        return False, "Uruchomione nie jako EXE", False

    if _is_installer(url):
        temp_installer = os.path.join(tempfile.gettempdir(), "VoiceFX-Setup.exe")
        if status_cb:
            status_cb("Pobieranie instalatora...")
        ok, err = _download(url, temp_installer, progress_cb, status_cb, cancel_event)
        if not ok:
            return False, err, False
        try:
            subprocess.Popen(
                [temp_installer, "/SILENT", "/NORESTART", "/SUPPRESSMSGBOXES"],
                close_fds=True,
            )
        except Exception as e:
            return False, str(e), False
        return True, "", True

    new_path = exe_path + ".new"
    if status_cb:
        status_cb("Pobieranie aktualizacji...")
    ok, err = _download(url, new_path, progress_cb, status_cb, cancel_event)
    if not ok:
        if err == "Anulowano" and os.path.exists(new_path):
            try:
                os.remove(new_path)
            except Exception:
                pass
        return False, err, False

    bat_path = os.path.join(tempfile.gettempdir(), "voicefx_update.bat")
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write("@echo off\n")
        f.write("set EXE=\"{}\"\n".format(exe_path))
        f.write("set NEW=\"{}\"\n".format(new_path))
        f.write("for /l %%i in (1,1,20) do (\n")
        f.write("  del /f /q %EXE% >nul 2>&1\n")
        f.write("  if not exist %EXE% goto done\n")
        f.write("  timeout /t 1 >nul\n")
        f.write(")\n")
        f.write(":done\n")
        f.write("move /y %NEW% %EXE% >nul 2>&1\n")
        f.write("start \"\" %EXE%\n")
        f.write("del \"%~f0\"\n")

    try:
        subprocess.Popen(["cmd", "/c", bat_path], close_fds=True)
    except Exception as e:
        return False, str(e), False

    return True, "", False
