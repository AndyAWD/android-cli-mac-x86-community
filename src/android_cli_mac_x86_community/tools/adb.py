"""Thin wrapper around the platform-tools `adb` binary."""
from __future__ import annotations

from pathlib import Path

from ..utils.android_home import tool_path
from ._subprocess import ToolResult, run


def _adb_path() -> Path:
    return tool_path("platform-tools/adb")


def _device_args(serial: str | None) -> list[str]:
    return ["-s", serial] if serial else []


def version() -> ToolResult:
    return run(_adb_path(), ["version"])


def devices() -> ToolResult:
    return run(_adb_path(), ["devices", "-l"])


def install(apks: list[str | Path], *, serial: str | None = None,
            replace: bool = True) -> ToolResult:
    args = _device_args(serial)
    apk_paths = [str(a) for a in apks]
    if len(apk_paths) > 1:
        args.append("install-multiple")
    else:
        args.append("install")
    if replace:
        args.append("-r")
    args.extend(apk_paths)
    return run(_adb_path(), args)


def shell(command: str, *, serial: str | None = None) -> ToolResult:
    args = _device_args(serial) + ["shell", command]
    return run(_adb_path(), args)


def start_activity(component: str, *, serial: str | None = None,
                   debug: bool = False) -> ToolResult:
    cmd = "am start"
    if debug:
        cmd += " -D"
    cmd += f" -n {component}"
    return shell(cmd, serial=serial)


def screencap_png(serial: str | None = None) -> bytes:
    """Return raw PNG bytes from `adb exec-out screencap -p`."""
    import subprocess

    exe = str(_adb_path())
    args = [exe, *_device_args(serial), "exec-out", "screencap", "-p"]
    proc = subprocess.run(args, capture_output=True)
    if proc.returncode != 0:
        raise RuntimeError(
            f"adb screencap failed (exit {proc.returncode}): "
            f"{proc.stderr.decode(errors='replace').strip()}"
        )
    return proc.stdout


def emu_kill(serial: str) -> ToolResult:
    return run(_adb_path(), ["-s", serial, "emu", "kill"])


def emu_avd_name(serial: str) -> str:
    """Return the AVD name reported by a running emulator at the given serial.

    `adb -s <serial> emu avd name` prints two lines: the AVD name, then "OK".
    """
    result = run(_adb_path(), ["-s", serial, "emu", "avd", "name"])
    if not result.ok:
        return ""
    first = result.stdout.splitlines()[0] if result.stdout else ""
    return first.strip()


def list_emulator_serials() -> list[str]:
    """Return serials of currently attached emulators (e.g. emulator-5554)."""
    result = devices()
    serials: list[str] = []
    for line in result.stdout.splitlines():
        line = line.strip()
        if not line or line.startswith("List of devices"):
            continue
        parts = line.split()
        if parts and parts[0].startswith("emulator-"):
            serials.append(parts[0])
    return serials


def find_emulator_serial_by_avd(avd_name: str) -> str | None:
    """Return the running emulator's serial whose AVD name matches, else None."""
    for serial in list_emulator_serials():
        if emu_avd_name(serial) == avd_name:
            return serial
    return None


def uiautomator_dump(*, serial: str | None = None,
                     remote_path: str = "/data/local/tmp/window_dump.xml"
                     ) -> ToolResult:
    """Dump UI hierarchy to `remote_path` on device.

    Defaults to /data/local/tmp/ because /sdcard/ is unreadable via `adb pull`
    on Android 14+ due to scoped storage; /data/local/tmp/ is shell-writable
    and shell-readable on every supported API level.
    """
    return shell(f"uiautomator dump {remote_path}", serial=serial)


def pull(remote: str, local: str | Path, *, serial: str | None = None) -> ToolResult:
    args = _device_args(serial) + ["pull", remote, str(local)]
    return run(_adb_path(), args)
