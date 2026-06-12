#!/usr/bin/env python3
"""Radar chart generator for the 5-dimension company health evaluation framework.

All chart labels are in English to avoid CJK font rendering issues.
Filenames may include Chinese characters (passed via --output).

Usage:
  python3 radar_chart.py --data /tmp/input.json --output docs/examples/company_health_radar.png

JSON format:
  {
    "company": "Papergames",
    "scores": {"Cash Flow Quality": 84, ...},
    "weights": {"Cash Flow Quality": 0.45, ...},
    "total_score": 79.2,
    "grade": "Moderate-High",
    "grade_label": "Medium-High"
  }
"""

import argparse
import json
import math
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np


# -- Color palette ------------------------------------------------
BG_COLOR = "#0f1117"
GRID_COLOR = "#2a2d3a"
AXIS_COLOR = "#5a5f7a"
FILL_COLOR_MAIN = "#7c3aed"       # purple
FILL_COLOR_EDGE = "#a78bfa"       # light purple
SCORE_DOT_COLOR = "#f59e0b"       # amber
CENTER_SCORE_COLOR = "#ffffff"
CENTER_LABEL_COLOR = "#a78bfa"
TEXT_COLOR = "#e2e8f0"
DIM_LABEL_COLOR = "#94a3b8"
WEIGHT_COLOR = "#f59e0b"

GRADE_COLORS = {
    "Excellent": "#22c55e",
    "Moderate-High": "#eab308",
    "Moderate": "#f97316",
    "Moderate-Low": "#ef4444",
    "High-Risk": "#7f1d1d",
}


def hex_to_rgba(hex_color, alpha=1.0):
    rgb = mcolors.hex2color(hex_color)
    return (*rgb, alpha)


def build_chart(data, output_path):
    company = data["company"]
    scores = data["scores"]
    weights = data.get("weights", {})
    total_score = data["total_score"]
    grade = data["grade"]
    grade_label = data.get("grade_label", grade)

    dims = list(scores.keys())
    values = [scores[d] for d in dims]
    n = len(dims)

    # Angle for each axis (start from top, clockwise)
    angles = np.linspace(math.pi / 2, math.pi / 2 - 2 * math.pi, n, endpoint=False)

    # Close the polygon
    values_closed = values + [values[0]]
    angles_closed = np.concatenate([angles, [angles[0]]])

    # -- Figure setup ---------------------------------------------
    fig, ax = plt.subplots(
        figsize=(8, 8),
        subplot_kw={"projection": "polar"},
        facecolor=BG_COLOR,
    )
    ax.set_facecolor(BG_COLOR)

    # -- Grid circles ---------------------------------------------
    grid_levels = [20, 40, 60, 80, 100]
    for level in grid_levels:
        circle = np.full(n, level)
        angles_circle = np.concatenate([angles, [angles[0]]])
        values_circle = np.append(circle, circle[0])
        ax.fill(angles_circle, values_circle, alpha=0, edgecolor=GRID_COLOR, linewidth=1.2, zorder=1)

    # Fill grid area with subtle alternating bands
    band_pairs = [(0, 20), (40, 60), (80, 100)]
    for lo, hi in band_pairs:
        ax.fill_between(
            np.linspace(0, 2 * math.pi, 200),
            lo, hi,
            color=GRID_COLOR, alpha=0.15, linewidth=0, zorder=1,
        )

    # -- Data fill ------------------------------------------------
    ax.fill(
        angles_closed, values_closed,
        color=hex_to_rgba(FILL_COLOR_MAIN, 0.28),
        edgecolor=FILL_COLOR_EDGE,
        linewidth=2.5,
        zorder=3,
    )

    # -- Score dots -----------------------------------------------
    ax.scatter(
        angles, values,
        c=SCORE_DOT_COLOR, s=70, zorder=5,
        edgecolors="white", linewidths=1.2,
    )

    # -- Score labels at each dot ---------------------------------
    for angle, val in zip(angles, values):
        offset_radius = val + 7
        label_angle_deg = math.degrees(angle)
        ax.annotate(
            str(val),
            xy=(angle, val),
            xytext=(angle, offset_radius),
            fontsize=10,
            fontweight="bold",
            color=TEXT_COLOR,
            ha="center",
            va="center",
            zorder=6,
        )

    # -- Axis lines -----------------------------------------------
    for angle in angles:
        ax.plot([angle, angle], [0, 100], color=AXIS_COLOR, linewidth=0.8, alpha=0.6, zorder=0)

    # -- Axis labels (dimension names + weights) ------------------
    dim_name_map = {
        "Cash Flow Quality": "Cash Flow\nQuality",
        "Profitability": "Profitability",
        "Debt Solvency": "Debt\nSolvency",
        "Operational Efficiency": "Operational\nEfficiency",
        "Sustainability": "Sustainability",
    }

    for i, (angle, dim) in enumerate(zip(angles, dims)):
        label_radius = 118
        label_angle_deg = math.degrees(angle)

        display_name = dim_name_map.get(dim, dim)

        # Dimension name
        ax.annotate(
            display_name,
            xy=(angle, label_radius),
            fontsize=9.5,
            fontweight="bold",
            color=DIM_LABEL_COLOR,
            ha="center",
            va="center",
            linespacing=1.2,
            zorder=6,
        )

        # Weight badge
        weight = weights.get(dim, 0)
        ax.annotate(
            f"(wt: {int(weight * 100)}%)",
            xy=(angle, label_radius - 8),
            fontsize=7.5,
            color=WEIGHT_COLOR,
            ha="center",
            va="center",
            alpha=0.85,
            zorder=6,
        )

    # -- Center display: total score + grade ----------------------
    ax.annotate(
        f"{total_score:.0f}",
        xy=(0, 0),
        fontsize=42,
        fontweight="bold",
        color=CENTER_SCORE_COLOR,
        ha="center",
        va="center",
        zorder=10,
    )
    ax.annotate(
        f"/ 100",
        xy=(0, -8),
        fontsize=11,
        color=DIM_LABEL_COLOR,
        ha="center",
        va="top",
        zorder=10,
    )

    # Grade label line 1
    grade_word_map = {
        "Excellent": "EXCELLENT",
        "Moderate-High": "MODERATE-HIGH",
        "Moderate": "MODERATE",
        "Moderate-Low": "MODERATE-LOW",
        "High-Risk": "HIGH RISK",
    }
    grade_short = grade_word_map.get(grade, grade.upper())
    grade_color = GRADE_COLORS.get(grade, "#94a3b8")

    ax.annotate(
        grade_short,
        xy=(0, -18),
        fontsize=11,
        fontweight="bold",
        color=grade_color,
        ha="center",
        va="top",
        zorder=10,
        bbox=dict(
            boxstyle="round,pad=0.3",
            facecolor=hex_to_rgba(grade_color, 0.15),
            edgecolor=grade_color,
            linewidth=1.2,
        ),
    )

    # -- Title: company name --------------------------------------
    fig.suptitle(
        company.upper(),
        y=0.96,
        fontsize=20,
        fontweight="bold",
        color=TEXT_COLOR,
        fontstretch="expanded",
    )

    # Subtitle
    fig.text(
        0.5, 0.91,
        "Five-Dimension Health Radar  ·  Company Health Evaluation Framework",
        ha="center",
        fontsize=9,
        color=DIM_LABEL_COLOR,
        alpha=0.8,
    )

    # -- Styling --------------------------------------------------
    ax.set_ylim(0, 125)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.spines["polar"].set_visible(False)

    # Remove polar frame
    ax.grid(False)

    # -- Footer watermark -----------------------------------------
    fig.text(
        0.98, 0.02,
        "company-health-eval · claude.ai",
        ha="right",
        fontsize=7,
        color=DIM_LABEL_COLOR,
        alpha=0.4,
    )

    # -- Save -----------------------------------------------------
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        str(path),
        dpi=150,
        bbox_inches="tight",
        facecolor=BG_COLOR,
        edgecolor="none",
        pad_inches=0.3,
    )
    plt.close(fig)

    print(f"Radar chart saved → {path.resolve()}")
    return path


def main():
    parser = argparse.ArgumentParser(description="Generate 5-dimension health radar chart")
    parser.add_argument("--data", required=True, help="Path to JSON input file")
    parser.add_argument("--output", required=True, help="Output PNG path")
    args = parser.parse_args()

    with open(args.data, "r") as f:
        data = json.load(f)

    required_keys = ["company", "scores", "total_score", "grade"]
    for key in required_keys:
        if key not in data:
            print(f"Error: missing required key '{key}' in input JSON", file=sys.stderr)
            sys.exit(1)

    if len(data["scores"]) != 5:
        print("Error: 'scores' must contain exactly 5 dimensions", file=sys.stderr)
        sys.exit(1)

    build_chart(data, args.output)


if __name__ == "__main__":
    main()
