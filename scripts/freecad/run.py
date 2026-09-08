#!/usr/bin/env python3
"""Run a local CAD script with the pinned runtime's Python and native FreeCAD ABI."""
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]


def main():
    lock_path = ROOT / "housing/toolchain.lock.json"
    lock = json.loads(lock_path.read_text())
    runtime = ROOT / lock["runtime_relative_path"]
    receipt_path = runtime.parent / "verified-runtime.json"
    if not receipt_path.is_file():
        raise SystemExit("First run: /usr/bin/python3 scripts/freecad/bootstrap.py")
    receipt = json.loads(receipt_path.read_text())
    digest = hashlib.sha256(lock_path.read_bytes()).hexdigest()
    if receipt["lock_sha256"] != digest or receipt["archive_sha256"] != lock["sha256"]:
        raise SystemExit("Runtime lock differs from verified receipt; rerun bootstrap.")
    if len(sys.argv) < 2:
        raise SystemExit("Usage: /usr/bin/python3 scripts/freecad/run.py <local-script.py> [args ...]")
    script = (ROOT / sys.argv[1]).resolve()
    if not script.is_file() or not any(script.is_relative_to(ROOT / base) for base in ("housing", "scripts/freecad")):
        raise SystemExit("CAD entry script must be under housing/ or scripts/freecad/.")
    prefix = runtime / "usr"
    state = ROOT / ".tools/freecad-state"
    env = os.environ.copy()
    # Avoid user-site modules, global preferences, host Python 3.14 and unrelated Qt/Conda envs.
    for key in ("PYTHONPATH", "PYTHONHOME", "LD_PRELOAD", "QT_PLUGIN_PATH", "CONDA_PREFIX", "VIRTUAL_ENV"):
        env.pop(key, None)
    dirs = {"HOME": state / "home", "XDG_CONFIG_HOME": state / "config",
            "XDG_CACHE_HOME": state / "cache", "XDG_DATA_HOME": state / "data",
            "FREECAD_USER_HOME": state / "freecad", "TMPDIR": state / "tmp"}
    for key, directory in dirs.items():
        directory.mkdir(parents=True, exist_ok=True)
        env[key] = str(directory)
    env.update({"PYTHONHOME": str(prefix), "PYTHONPATH": os.pathsep.join((str(prefix / "lib"), str(ROOT / "housing"))),
                "PYTHONNOUSERSITE": "1", "PYTHONDONTWRITEBYTECODE": "1",
                "LD_LIBRARY_PATH": str(prefix / "lib"), "PATH_TO_FREECAD_LIBDIR": str(prefix / "lib"),
                "PREFIX": str(prefix), "QT_QPA_PLATFORM": "offscreen", "LC_ALL": "C.UTF-8",
                "SMOVE_ROOT": str(ROOT), "FONTCONFIG_FILE": "/etc/fonts/fonts.conf",
                "FONTCONFIG_PATH": "/etc/fonts"})
    executable = prefix / "bin/python"
    os.execve(str(executable), [str(executable), str(script), *sys.argv[2:]], env)


if __name__ == "__main__":
    main()
