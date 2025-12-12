# plot_style.py
# -------------------------------------------------
# Paper-grade Matplotlib style configuration
# Suitable for academic papers (IEEE / ACM / security / blockchain)
# macOS + Chinese/English mixed text supported
# -------------------------------------------------

import matplotlib.pyplot as plt
from matplotlib import rcParams


def set_paper_style(
    font_size: int = 12,
    dpi: int = 300,
    use_latex: bool = False
):
    """
    Configure Matplotlib for paper-quality figures.

    Args:
        font_size (int): Base font size
        dpi (int): Figure DPI (300 recommended for papers)
        use_latex (bool): Whether to use LaTeX rendering
    """

    # ---------------- Font configuration ----------------
    rcParams["font.family"] = "serif"
    rcParams["font.serif"] = [
        "Times New Roman",
        "STSong",
        "Songti SC",
        "PingFang SC"
    ]
    rcParams["font.sans-serif"] = [
        "PingFang SC",
        "Heiti SC",
        "Arial Unicode MS"
    ]

    # Correct minus sign rendering
    rcParams["axes.unicode_minus"] = False

    # ---------------- Figure quality ----------------
    rcParams["figure.dpi"] = dpi
    rcParams["savefig.dpi"] = dpi
    rcParams["savefig.bbox"] = "tight"
    rcParams["savefig.pad_inches"] = 0.02

    # ---------------- Font sizes ----------------
    rcParams["font.size"] = font_size
    rcParams["axes.titlesize"] = font_size + 2
    rcParams["axes.labelsize"] = font_size
    rcParams["xtick.labelsize"] = font_size - 1
    rcParams["ytick.labelsize"] = font_size - 1
    rcParams["legend.fontsize"] = font_size - 1

    # ---------------- Axes & ticks ----------------
    rcParams["axes.linewidth"] = 1.0
    rcParams["xtick.major.width"] = 1.0
    rcParams["ytick.major.width"] = 1.0
    rcParams["xtick.minor.width"] = 0.8
    rcParams["ytick.minor.width"] = 0.8

    rcParams["xtick.direction"] = "in"
    rcParams["ytick.direction"] = "in"
    rcParams["xtick.top"] = True
    rcParams["ytick.right"] = True

    # ---------------- Grid ----------------
    rcParams["axes.grid"] = True
    rcParams["grid.linestyle"] = "--"
    rcParams["grid.linewidth"] = 0.6
    rcParams["grid.alpha"] = 0.6

    # ---------------- Lines & markers ----------------
    rcParams["lines.linewidth"] = 2.0
    rcParams["lines.markersize"] = 6

    # ---------------- Legend ----------------
    rcParams["legend.frameon"] = False
    rcParams["legend.loc"] = "best"

    # ---------------- Color cycle (paper friendly) ----------------
    rcParams["axes.prop_cycle"] = plt.cycler(
        color=[
            "#1f77b4",  # blue
            "#ff7f0e",  # orange
            "#2ca02c",  # green
            "#d62728",  # red
            "#9467bd",  # purple
            "#8c564b",  # brown
        ]
    )

    # ---------------- LaTeX (optional) ----------------
    if use_latex:
        rcParams["text.usetex"] = True
        rcParams["text.latex.preamble"] = r"\usepackage{amsmath}"

    # ---------------- Math rendering ----------------
    rcParams["mathtext.fontset"] = "stix"
    rcParams["mathtext.rm"] = "serif"

    print("[PlotStyle] Paper style enabled.")


def save_figure(fig, filename: str):
    """
    Save figure with paper-quality settings.
    """
    fig.savefig(filename)
    print(f"[PlotStyle] Figure saved to {filename}")