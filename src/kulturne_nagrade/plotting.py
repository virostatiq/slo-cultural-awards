"""Shared matplotlib style and output for analysis plots.

Figures are written to ``plots/<theme>/<name>.png`` at the repo root. Labels and
titles are in Slovenian. The palette is the validated reference palette (light mode):
categorical hues in fixed order, one-hue sequential, blue↔red diverging with a gray
midpoint.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

from kulturne_nagrade import PROJECT_ROOT

PLOTS_DIR = PROJECT_ROOT / "plots"

SURFACE = "#fcfcfb"
TEXT = "#0b0b0b"
TEXT_2 = "#52514e"
GRID = "#e1e0d9"
MUTED = "#a8a69d"  # de-emphasis gray for context marks

# Categorical slots in fixed order; never cycle past the list.
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
GENDER = {"f": SERIES[1], "m": SERIES[0]}
GENDER_LABEL = {"f": "ženske", "m": "moški"}
ROLE_LABEL = {"winner": "nagrajenci", "jury": "žirija"}
# Roles never use the gender hues (blue = men, orange = women).
ROLE_COLOR = {"winner": SERIES[2], "jury": SERIES[6]}

SEQUENTIAL = LinearSegmentedColormap.from_list(
    "seq_blue", ["#cde2fb", "#86b6ef", "#3987e5", "#256abf", "#184f95", "#0d366b"])
DIVERGING = LinearSegmentedColormap.from_list(
    "div_blue_red", ["#184f95", "#6da7ec", "#f0efec", "#ec8a89", "#a32e2e"])


def apply_style() -> None:
    plt.rcParams.update({
        "figure.facecolor": SURFACE, "axes.facecolor": SURFACE, "savefig.facecolor": SURFACE,
        "figure.dpi": 110, "savefig.dpi": 160, "savefig.bbox": "tight",
        "font.family": "DejaVu Sans", "font.size": 10,
        "text.color": TEXT, "axes.labelcolor": TEXT_2,
        "xtick.color": TEXT_2, "ytick.color": TEXT_2,
        "axes.edgecolor": GRID, "axes.linewidth": 1,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.8, "grid.linestyle": "-",
        "axes.axisbelow": True,
        "axes.titlesize": 13, "axes.titleweight": "bold", "axes.titlelocation": "left",
        "axes.titlepad": 12,
        "axes.prop_cycle": matplotlib.cycler(color=SERIES),
        "lines.linewidth": 2, "lines.solid_capstyle": "round", "lines.markersize": 6,
        "legend.frameon": False, "legend.fontsize": 9,
    })


def figure(width: float = 8, height: float = 4.8, **kwargs):
    apply_style()
    return plt.subplots(figsize=(width, height), **kwargs)


def subtitle(ax, text: str) -> None:
    """Secondary line under the title (method, coverage, caveat). Call after set_title."""
    n_lines = text.count("\n") + 1
    ax.set_title(ax.get_title(loc="left"), loc="left", pad=12 + 13 * n_lines)
    ax.annotate(text, xy=(0, 1), xycoords="axes fraction", xytext=(0, 8),
                textcoords="offset points", fontsize=9, color=TEXT_2, va="bottom")


def source_note(fig, text: str = "Vir: zbirka Kulturne nagrade") -> None:
    """Footer line. Call last, after all axes content is in place."""
    fig.tight_layout()
    fig.text(0.01, 0, text, fontsize=8, color=TEXT_2, ha="left", va="top")


def save(fig, theme: str, name: str) -> Path:
    path = PLOTS_DIR / theme / f"{name}.png"
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
    return path


# --- Slovenian number formatting -------------------------------------------------------
# Decimal comma, a space before %, and a true minus sign.

def dec(x: float, digits: int = 1, sign: bool = False) -> str:
    s = f"{x:+.{digits}f}" if sign else f"{x:.{digits}f}"
    return s.replace(".", ",").replace("-", "−")


def pct(x: float, digits: int = 0) -> str:
    return dec(100 * x, digits) + " %"


def pct_fmt(v, _pos=None) -> str:
    """Axis tick formatter for shares (0–1)."""
    return pct(v)
