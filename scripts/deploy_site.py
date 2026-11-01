"""Build the site for its public address and upload it over FTPS.

    uv run python scripts/deploy_site.py            # build + upload
    uv run python scripts/deploy_site.py --no-build # upload site/dist as it is
    uv run python scripts/deploy_site.py --no-build --from 3500   # resume after file 3500

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
import os
import re
import subprocess
import time
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
CONF = ROOT / "docs" / "deployment" / "remote_ftp.txt"
DIST = ROOT / "site" / "dist"


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


def upload(c: dict, start: int = 0, pause: float = 5.0) -> None:
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
                time.sleep(3)
                try:
                    f.quit()
                except Exception:  # noqa: BLE001
                    pass
                f = connect()
        else:
            failed.append(dest)
        if i % 250 == 0 or i == len(files):
            print(f"{i}/{len(files)} files, {time.time() - t0:.0f} s", flush=True)
    f.quit()
    print(f"uploaded to {c['origin']}{c['base']}/" + (f"; {len(failed)} failed" if failed else ""))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-build", action="store_true")
    ap.add_argument("--from", dest="start", type=int, default=0,
                    help="skip the first N files (resume a stopped upload)")
    a = ap.parse_args()
    c = config()
    if not a.no_build:
        build(c)
    upload(c, a.start)


if __name__ == "__main__":
    main()
