#!/usr/bin/env python3
"""Install only the pinned official portable runtime inside this Git workspace."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
LOCK_PATH = ROOT / "housing/toolchain.lock.json"


def sha256(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def fetch(url, path):
    # No credentials, package manager, shell pipe or service upload.
    part = path.with_name(path.name + ".partial")
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "sMove-FreeCAD-bootstrap"})
            with urllib.request.urlopen(req, timeout=90) as response, part.open("wb") as output:
                while chunk := response.read(4 * 1024 * 1024):
                    output.write(chunk)
            part.replace(path)
            return
        except Exception:
            if attempt == 2:
                raise
            time.sleep(2 ** attempt)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true", help="offline archive/receipt verification; never downloads")
    args = parser.parse_args()
    lock = json.loads(LOCK_PATH.read_text())
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        raise SystemExit("This lock supports Linux x86_64 only; do not substitute an unpinned binary.")
    cache = ROOT / ".tools/freecad" / lock["version"]
    runtime = ROOT / lock["runtime_relative_path"]
    archive = cache / lock["filename"]
    receipt_path = cache / "verified-runtime.json"
    if args.verify_only:
        if not archive.is_file() or sha256(archive) != lock["sha256"]:
            raise SystemExit("Missing or changed archive; rerun bootstrap.")
        receipt = json.loads(receipt_path.read_text())
        if receipt["lock_sha256"] != sha256(LOCK_PATH) or not (runtime / "AppRun").exists():
            raise SystemExit("Runtime/lock mismatch; inspect local cache.")
        print(json.dumps(receipt, indent=2))
        return
    cache.mkdir(parents=True, exist_ok=True)
    metadata_path = cache / "official-release.json"
    fetch(lock["release_api_url"], metadata_path)
    metadata = json.loads(metadata_path.read_text())
    if metadata["tag_name"] != lock["version"] or metadata["draft"] or metadata["prerelease"]:
        raise SystemExit("Official release metadata does not match stable version lock.")
    asset = next(a for a in metadata["assets"] if a["name"] == lock["filename"])
    for key, expected in (("id", lock["asset_id"]), ("size", lock["size_bytes"]),
                          ("digest", "sha256:" + lock["sha256"]), ("browser_download_url", lock["url"])):
        if asset[key] != expected:
            raise SystemExit(f"Official asset {key} differs from lock; refusing download/execution.")
    checksum_path = cache / (lock["filename"] + "-SHA256.txt")
    fetch(lock["checksum_url"], checksum_path)
    if sha256(checksum_path) != lock["checksum_file_sha256"]:
        raise SystemExit("Publisher checksum file hash differs from pin.")
    if checksum_path.read_text().split()[0] != lock["sha256"]:
        raise SystemExit("Publisher checksum and locked archive hash disagree.")
    if not archive.exists():
        print(f"Downloading official {lock['filename']} ({lock['size_bytes']} bytes)", flush=True)
        fetch(lock["url"], archive)
    if archive.stat().st_size != lock["size_bytes"] or sha256(archive) != lock["sha256"]:
        raise SystemExit("Archive integrity failed. Inspect/remove only the local archive, then retry.")
    # Only execute after the complete archive passes both publisher and pinned hashes.
    archive.chmod(0o755)
    if runtime.exists() and not receipt_path.exists():
        raise SystemExit("Incomplete/unverified extraction; remove only this version's squashfs-root and retry.")
    if not runtime.exists():
        with (cache / "extract.log").open("wb") as log:
            subprocess.run([str(archive), "--appimage-extract"], cwd=cache,
                           stdout=log, stderr=subprocess.STDOUT, check=True, timeout=600)
    if not (runtime / "AppRun").exists():
        raise SystemExit("Extracted AppRun missing.")
    receipt = {"version": lock["version"], "asset_id": lock["asset_id"],
               "archive_sha256": sha256(archive), "lock_sha256": sha256(LOCK_PATH),
               "runtime_relative_path": lock["runtime_relative_path"],
               "official_release_url": lock["release_url"],
               "verification": "publisher sidecar + pinned SHA256 + official release API; extraction without FUSE",
               "scope": "workspace-local only; extracted files must be treated as read-only runtime"}
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps(receipt, indent=2))


if __name__ == "__main__":
    main()
