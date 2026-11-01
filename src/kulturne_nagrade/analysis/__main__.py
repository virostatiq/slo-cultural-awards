"""Run analyses: figures to plots/<theme>/, key numbers to results/<theme>.json.

    uv run python -m kulturne_nagrade.analysis            # all themes
    uv run python -m kulturne_nagrade.analysis gender age # selected themes
"""

import importlib
import sys
import time

from kulturne_nagrade.analysis.common import save_results

THEMES = ["coverage", "gender", "age", "juries", "power", "careers", "geography",
          "network", "transition", "pipeline",
          "dossier", "crown", "mobility", "overview", "influence", "awards"]


def main(argv: list[str]) -> None:
    themes = argv or THEMES
    unknown = set(themes) - set(THEMES)
    if unknown:
        raise SystemExit(f"unknown themes: {sorted(unknown)}; choose from {THEMES}")
    for theme in themes:
        t0 = time.perf_counter()
        module = importlib.import_module(f"kulturne_nagrade.analysis.{theme}")
        save_results(theme, module.run())
        print(f"{theme:10s} {time.perf_counter() - t0:5.1f}s")


if __name__ == "__main__":
    main(sys.argv[1:])
