"""Build the site for its public address and upload it over FTPS.

    uv run python scripts/deploy_site.py            # build + upload
    uv run python scripts/deploy_site.py --no-build # upload site/dist as it is
    uv run python scripts/deploy_site.py --no-build --from 3500   # resume after file 3500
    uv run python scripts/deploy_site.py --full     # upload every file, not only changed ones
    uv run python scripts/deploy_site.py --no-build --only 'favicon*' --only 'icon-*'
                                                    # upload only paths matching the globs

Only files that changed since the last upload are sent (site/.deploy-manifest.json keeps
a hash of each uploaded file; git-ignored).

The host's firewall (Imunify360) may block an IP that opens too many transfers too fast,
so the upload pauses briefly every 200 files. Files are uploaded in sorted order, so a
stopped upload can be resumed with --from.

Reads docs/deployment/remote_ftp.txt (git-ignored; never commit it). Expected lines:

    FTP naslov: <host>
    Uporabniško ime: <user>
    Geslo: <password>
    final site URL: https://example.com/subfolder/

The URL sets SITE_URL (origin) and SITE_BASE (subfolder) for the Astro build; the files go
to public_html/<subfolder> on the server. Credentials are never printed.
"""

from __future__ import annotations

import argparse
import ftplib
import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CONF = ROOT / "docs" / "deployment" / "remote_ftp.txt"
DIST = ROOT / "site" / "dist"
MANIFEST = ROOT / "site" / ".deploy-manifest.json"  # path -> sha1 of what is on the server


def digest(p: Path) -> str:
    return hashlib.sha1(p.read_bytes()).hexdigest()


def manifest(folder: Path) -> dict:
    return {p.relative_to(folder).as_posix(): digest(p) for p in folder.rglob("*") if p.is_file()}


def config() -> dict:
    t = CONF.read_text(encoding="utf-8")
    get = lambda label: re.search(label + r"\s*:\s*(\S+)", t, re.I).group(1)
    u = urlparse(get("final site URL"))
    base = u.path.rstrip("/")
    return {"host": get("FTP naslov"), "user": get("Uporabniško ime"), "password": get("Geslo"),
            "origin": f"{u.scheme}://{u.netloc}", "base": base or "/",
            "remote": "public_html" + base}


def build(c: dict) -> None:
    env = {**os.environ, "SITE_URL": c["origin"], "SITE_BASE": c["base"]}
    subprocess.run(["npm", "run", "data"], cwd=ROOT / "site", check=True)
    subprocess.run(["rm", "-rf", str(DIST)], check=True)
    subprocess.run(["npx", "astro", "build"], cwd=ROOT / "site", env=env, check=True)


def upload(c: dict, start: int = 0, pause: float = 10.0, full: bool = False,
           only: list[str] | None = None) -> None:
    def connect():
        f = ftplib.FTP_TLS(c["host"], timeout=60)
        f.login(c["user"], c["password"])
        f.prot_p()
        return f

    f, made = connect(), set()

    def mkdirs(path: str) -> None:
        parts = path.split("/")
        for i in range(1, len(parts) + 1):
            d = "/".join(parts[:i])
            if d not in made:
                try:
                    f.mkd(d)
                except ftplib.error_perm:
                    pass  # exists
                made.add(d)

    files = sorted(p for p in DIST.rglob("*") if p.is_file())
    done = json.loads(MANIFEST.read_text()) if MANIFEST.exists() and not full else {}
    files = [p for p in files if done.get(p.relative_to(DIST).as_posix()) != digest(p)]
    if only:
        from fnmatch import fnmatch
        files = [p for p in files if any(fnmatch(p.relative_to(DIST).as_posix(), g) for g in only)]
    print(f"{len(files)} files to upload" + ("" if full else " (changed since the last upload)"),
          flush=True)
    t0, failed = time.time(), []
    for i, p in enumerate(files, 1):
        if i <= start:
            continue
        if i % 200 == 0:
            time.sleep(pause)
        dest = f"{c['remote']}/{p.relative_to(DIST).as_posix()}"
        for _ in range(4):
            try:
                mkdirs(dest.rsplit("/", 1)[0])
                with open(p, "rb") as fh:
                    f.storbinary(f"STOR {dest}", fh)
                break
            except Exception as e:  # noqa: BLE001 - reconnect on any transfer error
                print(f"retry {dest}: {type(e).__name__}", flush=True)
                MANIFEST.write_text(json.dumps(done, indent=0, sort_keys=True))
                time.sleep(30)  # let the host's connection limit cool down
                try:
                    f.quit()
                except Exception:  # noqa: BLE001
                    pass
                try:
                    f = connect()
                except Exception as e2:  # noqa: BLE001
                    print(f"reconnect failed: {type(e2).__name__}", flush=True)
        else:
            failed.append(dest)
            if len(failed) >= 10:
                print("too many failures; stopping (rerun to resume)", flush=True)
                break
            continue
        done[p.relative_to(DIST).as_posix()] = digest(p)
        if i % 250 == 0 or i == len(files):
            MANIFEST.write_text(json.dumps(done, indent=0, sort_keys=True))  # resumable
            print(f"{i}/{len(files)} files, {time.time() - t0:.0f} s", flush=True)
    try:
        f.quit()
    except Exception:  # noqa: BLE001
        pass
    MANIFEST.write_text(json.dumps(done, indent=0, sort_keys=True))
    print(f"uploaded to {c['origin']}{c['base']}/" + (f"; {len(failed)} failed" if failed else ""))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-build", action="store_true")
    ap.add_argument("--full", action="store_true", help="upload every file, not only changed ones")
    ap.add_argument("--seed-manifest", metavar="DIR",
                    help="record DIR (a copy of what is on the server) as uploaded, then exit")
    ap.add_argument("--only", action="append", metavar="GLOB",
                    help="upload only changed paths matching GLOB (repeatable)")
    ap.add_argument("--from", dest="start", type=int, default=0,
                    help="skip the first N files (resume a stopped upload)")
    a = ap.parse_args()
    if a.seed_manifest:
        MANIFEST.write_text(json.dumps(manifest(Path(a.seed_manifest)), indent=0, sort_keys=True))
        print(f"manifest seeded from {a.seed_manifest}")
        return
    c = config()
    if not a.no_build:
        build(c)
    upload(c, a.start, full=a.full, only=a.only)


if __name__ == "__main__":
    main()
