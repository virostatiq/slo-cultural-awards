"""A standalone, offline HTML page of the network map.

    uv run python -m kulturne_nagrade.network_page     # -> results/network/zemljevid.html

One file with everything inlined: graphology and sigma.js (downloaded once to
.cache/vendor/, pinned versions) and results/network/graph.json (run network_map
first). Opens from disk, without a server or a network connection. The website will
load the same graph.json; this page is the reference for how to present it.
"""

from __future__ import annotations

import json
import urllib.request
from pathlib import Path

from kulturne_nagrade import PROJECT_ROOT
from kulturne_nagrade.graph import OUT_DIR

TEMPLATE = Path(__file__).parent / "templates" / "network_page.html"
VENDOR = PROJECT_ROOT / ".cache" / "vendor"
LIBS = {
    "GRAPHOLOGY": ("graphology-0.25.4.umd.min.js",
                   "https://cdnjs.cloudflare.com/ajax/libs/graphology/0.25.4/graphology.umd.min.js"),
    "SIGMA": ("sigma-2.4.0.min.js",
              "https://cdnjs.cloudflare.com/ajax/libs/sigma.js/2.4.0/sigma.min.js"),
}
OUT = OUT_DIR / "zemljevid.html"


def _lib(name: str, url: str) -> str:
    path = VENDOR / name
    if not path.exists():
        VENDOR.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(url) as r:  # pinned version from cdnjs
            path.write_bytes(r.read())
    return path.read_text(encoding="utf-8")


def _safe(s: str) -> str:
    """Inline text must not close its <script> element."""
    return s.replace("</", "<\\/")


def main() -> None:
    data = json.loads((OUT_DIR / "graph.json").read_text(encoding="utf-8"))
    html = TEMPLATE.read_text(encoding="utf-8")
    for key, (name, url) in LIBS.items():
        html = html.replace(f"/*__{key}__*/", _safe(_lib(name, url)), 1)
    html = html.replace("/*__DATA__*/", _safe(json.dumps(data, ensure_ascii=False,
                                                         separators=(",", ":"))), 1)
    OUT.write_text(html, encoding="utf-8")
    print(f"{OUT.relative_to(PROJECT_ROOT)}: {OUT.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
