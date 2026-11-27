"""Publication-grade figure generator for the S1 Dual-Channel Screening Study.

Generates five 300-DPI PNG figures from ``summary.json`` produced by
``research/dual_channel_s1/run_experiments.py`` without mutating experiment outputs:
1. ``fig1_dual_channel_architecture.png``
2. ``fig2_e1_sentiment_and_divergence.png``
3. ``fig3_e2_risk_coverage_and_abstention.png``
4. ``fig4_e3_partial_observation_triage.png``
5. ``fig5_e4_policy_and_invariance.png``
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")

from matplotlib.gridspec import GridSpec, GridSpecFromSubplotSpec  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch, Rectangle  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

# Colorblind-safe academic palette specified by study guidelines
NAVY = "#1f4e79"
STEEL = "#2e75b6"
ORANGE = "#d95f02"
TEAL = "#1b9e77"
PURPLE = "#7570b3"
SLATE = "#666666"
FIREWALL_RED = "#b2182b"

RC_STYLE: dict[str, Any] = {
    "font.family": "sans-serif",
    "font.sans-serif": ["DejaVu Sans", "Arial", "Helvetica"],
    "font.size": 9.5,
    "axes.titlesize": 10.2,
    "axes.titleweight": "bold",
    "axes.labelsize": 9.2,
    "axes.labelweight": "bold",
    "axes.edgecolor": "#333333",
    "axes.linewidth": 0.9,
    "xtick.labelsize": 8.3,
    "ytick.labelsize": 8.3,
    "legend.fontsize": 7.8,
    "figure.facecolor": "white",
    "axes.facecolor": "white",
    "savefig.facecolor": "white",
}


def _style_data_axis(ax: plt.Axes, *, grid_axis: str = "y") -> None:
    """Apply crisp academic spine and subtle background grid styling."""
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.set_axisbelow(True)
    if grid_axis in ("x", "y", "both"):
        ax.grid(
            axis=grid_axis, linestyle="--", linewidth=0.6, color="#cccccc", alpha=0.65
        )


def _draw_rounded_box(
    ax: plt.Axes,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    title: str,
    body: str,
    facecolor: str,
    edgecolor: str,
    lw: float = 1.6,
    linestyle: str = "-",
    title_color: str | None = None,
    title_size: float = 9.2,
    body_size: float = 7.9,
    align: str = "left",
    pad: float = 0.45,
) -> None:
    """Render a crisp rounded FancyBboxPatch with separated header and body text."""
    patch = FancyBboxPatch(
        (x + pad, y + pad),
        w - 2 * pad,
        h - 2 * pad,
        boxstyle=f"round,pad={pad},rounding_size=1.15",
        facecolor=facecolor,
        edgecolor=edgecolor,
        linewidth=lw,
        linestyle=linestyle,
        zorder=2,
    )
    ax.add_patch(patch)

    t_col = title_color or edgecolor
    if align == "center":
        tx = x + w / 2.0
        ha = "center"
    else:
        tx = x + 1.45
        ha = "left"

    ax.text(
        tx,
        y + h - 1.35,
        title,
        ha=ha,
        va="top",
        fontsize=title_size,
        fontweight="bold",
        color=t_col,
        zorder=3,
    )
    ax.text(
        tx,
        y + h - 3.35,
        body,
        ha=ha,
        va="top",
        fontsize=body_size,
        color="#222222",
        linespacing=1.32,
        zorder=3,
    )


def _draw_arrow(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    color: str = "#333333",
    lw: float = 1.5,
    linestyle: str = "-",
    rad: float = 0.0,
    mutation_scale: float = 13.0,
) -> None:
    """Draw a directional FancyArrowPatch between two diagram coordinates."""
    arrow = FancyArrowPatch(
        start,
        end,
        connectionstyle=f"arc3,rad={rad}",
        arrowstyle="-|>,head_length=0.55,head_width=0.35",
        mutation_scale=mutation_scale,
        linewidth=lw,
        linestyle=linestyle,
        edgecolor=color,
        facecolor=color,
        zorder=4,
    )
    ax.add_patch(arrow)


# ==============================================================================
# FIGURE 1: Dual-Channel Preliminary Screening Chatbot Architecture
# ==============================================================================
def _render_fig1_architecture(outdir: Path) -> Path:
    fig, ax = plt.subplots(figsize=(14.0, 8.2), dpi=300)
    fig.subplots_adjust(left=0.015, right=0.985, bottom=0.015, top=0.985)
    ax.set_xlim(0, 140)
    ax.set_ylim(0, 82)
    ax.set_aspect("equal")
    ax.axis("off")

    # Title banner
    ax.text(
        70.0,
        79.6,
        "Dual-Channel Preliminary Screening Chatbot Architecture",
        ha="center",
        va="top",
        fontsize=13.5,
        fontweight="bold",
        color=NAVY,
    )
    ax.text(
        70.0,
        76.7,
        "Parallel Affective Sensing (Left Ear) & Evidence-Grounded PHQ-8 Extraction (Right Ear) with Deterministic Score-Invariance Firewall",
        ha="center",
        va="top",
        fontsize=9.0,
        color="#444444",
    )

    # --- Row 1: Input & Pre-API Demo Safety Guard (y = 63.0 .. 73.5) ---
    _draw_rounded_box(
        ax,
        3.0,
        63.0,
        30.5,
        10.5,
        title="1. User Turn Input",
        body="• Bilingual free text (zh / en)\n• Multi-domain natural prose\n• Session-only memory",
        facecolor="#f4f7fb",
        edgecolor=NAVY,
    )
    _draw_arrow(ax, (33.7, 68.25), (39.3, 68.25), color=NAVY, lw=1.7)

    _draw_rounded_box(
        ax,
        39.5,
        63.0,
        49.5,
        10.5,
        title="2. Pre-API Demo Safety Guard (safety_guard.py)",
        body=(
            "• Runs BEFORE any LLM / API invocation\n"
            "• Exact demo markers ([DEMO_INTERRUPT], [DEMO_REVIEW])\n"
            "  or guard fault -> immediate state wipe & pause"
        ),
        facecolor="#fdf6ef",
        edgecolor=ORANGE,
    )
    _draw_arrow(
        ax, (89.2, 68.25), (97.3, 68.25), color=FIREWALL_RED, lw=1.6, linestyle="--"
    )
    ax.text(
        93.25,
        69.5,
        "non-normal",
        ha="center",
        va="bottom",
        fontsize=7.5,
        fontweight="bold",
        color=FIREWALL_RED,
    )

    _draw_rounded_box(
        ax,
        97.5,
        63.0,
        39.5,
        10.5,
        title="Guard Block & Wipe (PAUSED)",
        body=(
            "• Wipes messages, candidates & trace\n"
            "• Zero downstream LLM calls; blocks score\n"
            "• Demo markers only (not crisis detector)"
        ),
        facecolor="#fff5f5",
        edgecolor=FIREWALL_RED,
        linestyle="--",
    )

    # Normal flow into BilingualConversationProvider
    _draw_arrow(ax, (64.25, 62.8), (64.25, 57.9), color=STEEL, lw=1.8)
    ax.text(
        65.6,
        60.35,
        "decision == 'normal'",
        ha="left",
        va="center",
        fontsize=7.8,
        fontweight="bold",
        color=STEEL,
    )

    # --- Row 2: BilingualConversationProvider (y = 48.2 .. 57.7) ---
    _draw_rounded_box(
        ax,
        22.0,
        48.2,
        84.5,
        9.5,
        title="3. Parallel Dual-Channel Processing — BilingualConversationProvider (zh / en)",
        body=(
            "Single schema-constrained turn proposal {reply, sentiment, updates} conditioned on\n"
            "session dialogue history, past-14-day assessment window, and provisional evidence table"
        ),
        facecolor="#eef5fb",
        edgecolor=STEEL,
        align="center",
    )

    # Split arrows to Left Ear and Right Ear
    _draw_arrow(ax, (43.0, 48.0), (31.0, 43.7), color=ORANGE, lw=1.8)
    ax.text(
        34.0,
        46.4,
        "Affect stream",
        ha="right",
        va="center",
        fontsize=7.8,
        fontweight="bold",
        color=ORANGE,
    )
    _draw_arrow(ax, (85.5, 48.0), (99.0, 43.7), color=TEAL, lw=1.8)
    ax.text(
        95.0,
        46.4,
        "Evidence stream",
        ha="left",
        va="center",
        fontsize=7.8,
        fontweight="bold",
        color=TEAL,
    )

    # --- Bold Red Dashed Score-Invariance Firewall (x = 63.5) ---
    ax.plot(
        [63.5, 63.5],
        [2.2, 46.2],
        color=FIREWALL_RED,
        linewidth=2.8,
        linestyle=(0, (6, 3.2)),
        zorder=5,
    )
    ax.text(
        63.5,
        26.8,
        "SCORE-INVARIANCE FIREWALL  (No Affect -> Score Path)",
        ha="center",
        va="center",
        rotation=90,
        fontsize=8.3,
        fontweight="bold",
        color=FIREWALL_RED,
        bbox={
            "boxstyle": "round,pad=0.36",
            "facecolor": "#fff5f5",
            "edgecolor": FIREWALL_RED,
            "linewidth": 1.3,
        },
        zorder=6,
    )

    # --- Left Column: Left Ear — Affective Sensing Channel (S) ---
    _draw_rounded_box(
        ax,
        3.0,
        27.0,
        54.0,
        16.5,
        title="Left Ear — Affective Sensing Channel (S)",
        body=(
            "• Turn-level polarity: negative | neutral | positive | unclear\n"
            "• Appended to session-only sentiment_trace (turn_id + polarity)\n"
            "• Calibrates conversational warmth & tone ONLY\n"
            "• Strictly ZERO path into candidates or score_phq8\n"
            "• Never infers, imputes, or alters PHQ-8 item frequencies"
        ),
        facecolor="#fdf6ef",
        edgecolor=ORANGE,
        lw=1.8,
    )

    # Left Ear -> Empathetic Conversational Reply
    _draw_arrow(ax, (24.0, 26.8), (24.0, 22.8), color=ORANGE, lw=1.6)
    _draw_rounded_box(
        ax,
        3.0,
        13.5,
        42.5,
        9.1,
        title="Empathetic Conversational Reply",
        body=(
            "• Brief affective acknowledgment when negative\n"
            "• Paired with <= 1 focused follow-up question"
        ),
        facecolor="#f7f5fb",
        edgecolor=PURPLE,
        lw=1.5,
    )

    # sentiment_trace -> Non-Scoring Alignment (bypassing Empathetic box on x = 51.5)
    _draw_arrow(ax, (51.5, 26.8), (51.5, 11.7), color=PURPLE, lw=1.6, linestyle="--")
    ax.text(
        52.4,
        18.2,
        "sentiment_trace",
        ha="left",
        va="center",
        rotation=90,
        fontsize=7.5,
        fontweight="bold",
        color=PURPLE,
    )

    _draw_rounded_box(
        ax,
        3.0,
        2.0,
        54.0,
        9.5,
        title="Non-Scoring Alignment (analyze_affect_symptom_alignment)",
        body=(
            "• Post-confirmation 4-quadrant diagnostic readout (never alters score):\n"
            "  Congruent Low | Situational Distress | Masked Somatic | Congruent Elevated"
        ),
        facecolor="#f5f4fa",
        edgecolor=PURPLE,
        lw=1.6,
    )

    # --- Right Column: Right Ear — Symptom Grounding Channel (N) ---
    _draw_rounded_box(
        ax,
        70.0,
        27.0,
        67.0,
        16.5,
        title="Right Ear — Symptom Grounding Channel (N)",
        body=(
            "• 8 PHQ-8 domains; requires timeframe == 'past_14_days' for integer 0–3\n"
            "• Deterministic gate (validate_proposal): exact user substring quote + turn_id\n"
            "• R1 day-count mapping: 0–1 -> 0,   2–6 -> 1,   7–11 -> 2,   12–14 -> 3\n"
            "• Selective abstention (frequency = None) on vague quantifiers,\n"
            "  older time windows, cross-boundary ranges, or affect-only turns"
        ),
        facecolor="#eef8f5",
        edgecolor=TEAL,
        lw=1.8,
    )

    # Right Ear -> Human-in-the-Loop Batch Review (when all 8 domains resolved)
    _draw_arrow(ax, (88.0, 26.8), (88.0, 22.8), color=NAVY, lw=1.6)
    ax.text(
        87.2,
        24.8,
        "8/8 resolved",
        ha="right",
        va="center",
        fontsize=7.4,
        fontweight="bold",
        color=NAVY,
    )
    _draw_rounded_box(
        ax,
        70.0,
        13.5,
        35.5,
        9.1,
        title="Human-in-the-Loop Review",
        body=(
            "• User inspects/edits 8 items (0–3)\n• Explicit consent (confirm_review)"
        ),
        facecolor="#f4f7fb",
        edgecolor=NAVY,
        lw=1.6,
    )

    # Right Ear -> Focused Clarification Turn (when frequency=None)
    _draw_arrow(ax, (122.0, 26.8), (122.0, 22.8), color=STEEL, lw=1.6, linestyle="--")
    ax.text(
        123.0,
        24.8,
        "frequency=None",
        ha="left",
        va="center",
        fontsize=7.4,
        fontweight="bold",
        color=STEEL,
    )
    _draw_rounded_box(
        ax,
        107.5,
        13.5,
        29.5,
        9.1,
        title="Focused Clarification Turn",
        body=("• Abstains from guessing\n• Requests past-14-day count"),
        facecolor="#eef5fb",
        edgecolor=STEEL,
        lw=1.5,
    )

    # Batch Review -> Deterministic score_phq8
    _draw_arrow(ax, (88.0, 13.3), (88.0, 11.7), color=NAVY, lw=1.8)
    _draw_rounded_box(
        ax,
        70.0,
        2.0,
        67.0,
        9.5,
        title="Deterministic PHQ-8 Engine (score_phq8)",
        body=(
            "• Accepts 8 unique ConfirmedAnswer(item_id, 0–3) integers ONLY\n"
            "• Computes PHQ-8 Total (0–24) + Severity Band (100% Affect-Invariant)"
        ),
        facecolor="#e8f1f8",
        edgecolor=NAVY,
        lw=2.0,
    )

    # Post-scoring read-only indicator from score_phq8 -> Alignment (strictly Right -> Left)
    _draw_arrow(ax, (69.8, 5.2), (57.2, 5.2), color=SLATE, lw=1.4, linestyle=":")
    ax.text(
        63.5,
        3.1,
        "read-only total>=10",
        ha="center",
        va="center",
        fontsize=6.9,
        fontweight="bold",
        color=SLATE,
        bbox={
            "boxstyle": "round,pad=0.22",
            "facecolor": "white",
            "edgecolor": "#bbbbbb",
            "linewidth": 0.8,
        },
        zorder=7,
    )

    out_path = outdir / "fig1_dual_channel_architecture.png"
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    return out_path


# ==============================================================================
# FIGURE 2: Experiment 1 — TweetEval Baselines & 48-Case Quadrant Divergence
# ==============================================================================
def _render_fig2_e1(summary: dict, outdir: Path) -> Path:
    e1 = summary["e1"]
    e1a = e1["e1a_tweeteval"]
    e1b = e1["e1b_quadrant_divergence"]

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(12.0, 4.8), dpi=300)
    fig.subplots_adjust(left=0.065, right=0.985, bottom=0.18, top=0.74, wspace=0.23)

    # --- Panel (a): Official TweetEval Held-Out Test ---
    _style_data_axis(ax_a)
    n_test = int(e1a["dataset_counts"]["test"])
    model_order = [
        ("majority", "Majority\nBaseline"),
        ("tfidf_multinomial_nb", "TF-IDF +\nMultinomial NB"),
        ("tfidf_logistic_regression", "TF-IDF +\nLogistic Reg."),
        ("tfidf_linear_svm", "TF-IDF +\nLinear SVM"),
    ]
    metrics_a = [
        ("accuracy", "Accuracy", NAVY),
        ("macro_f1", "Macro-F1", ORANGE),
        ("macro_recall", "Macro-Recall", TEAL),
    ]

    x_a = np.arange(len(model_order), dtype=float)
    width_a = 0.25
    offsets_a = [-width_a, 0.0, width_a]

    max_a = 0.0
    for offset, (mkey, mlabel, color) in zip(offsets_a, metrics_a):
        vals = [float(e1a["test_models"][m][mkey]) for m, _ in model_order]
        max_a = max(max_a, max(vals))
        bars = ax_a.bar(
            x_a + offset,
            vals,
            width=width_a * 0.92,
            color=color,
            edgecolor="white",
            linewidth=0.6,
            label=mlabel,
        )
        for rect, val in zip(bars, vals):
            ax_a.text(
                rect.get_x() + rect.get_width() / 2.0,
                val + 0.016,
                f"{val:.3f}",
                ha="center",
                va="bottom",
                fontsize=7.2,
                fontweight="bold",
                color="#222222",
                rotation=90,
            )

    ax_a.set_xticks(x_a)
    ax_a.set_xticklabels([lbl for _, lbl in model_order])
    ax_a.set_ylim(0.0, max(0.88, max_a + 0.22))
    ax_a.set_ylabel("Score")
    ax_a.set_title(f"(a) Official TweetEval Held-Out Test (N={n_test:,})", pad=28)
    ax_a.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, 1.015),
        ncol=3,
        frameon=True,
        facecolor="white",
        framealpha=0.95,
        fontsize=7.6,
    )

    # --- Panel (b): E1B 48-Case Bilingual Screening Benchmark ---
    _style_data_axis(ax_b)
    e1b_models = e1b["models"]
    n_cases = int(e1b.get("n_cases", 48))

    classical_key = (
        "tfidf_linear_svm"
        if "tfidf_linear_svm" in e1b_models
        else "tfidf_logistic_regression"
    )
    classical_label = (
        "Linear SVM" if classical_key == "tfidf_linear_svm" else "Logistic Reg."
    )

    selected_b: list[tuple[str, str, str]] = [(classical_key, classical_label, STEEL)]
    if "live_gpt_terra" in e1b_models:
        selected_b.append(("live_gpt_terra", "Live GPT-Terra", TEAL))
    elif (
        "tfidf_logistic_regression" in e1b_models
        and classical_key != "tfidf_logistic_regression"
    ):
        selected_b.append(("tfidf_logistic_regression", "Logistic Reg.", PURPLE))
    elif "majority" in e1b_models:
        selected_b.append(("majority", "Majority", SLATE))
    selected_b.append(("oracle_polarity_ceiling", "Oracle Polarity (100%)", ORANGE))

    metric_extractors = [
        ("EN Polarity\nAcc. (↑)", lambda d: float(d["en_polarity"]["accuracy"])),
        ("ZH Polarity\nAcc. (↑)", lambda d: float(d["zh_polarity"]["accuracy"])),
        (
            "Situational Distress\nProxy FP Rate (↓)",
            lambda d: float(
                d["naive_negative_implies_elevated_phq8"][
                    "situational_distress_false_positive_rate"
                ]
            ),
        ),
        (
            "Masked Somatic\nProxy FN Rate (↓)",
            lambda d: float(
                d["naive_negative_implies_elevated_phq8"][
                    "masked_somatic_false_negative_rate"
                ]
            ),
        ),
    ]

    ax_b.axvspan(1.5, 3.55, color="#fff3e8", alpha=0.65, zorder=0)
    ax_b.axvline(1.5, color=ORANGE, linestyle="--", linewidth=1.0, alpha=0.75, zorder=1)

    x_b = np.arange(len(metric_extractors), dtype=float)
    n_m = len(selected_b)
    width_b = 0.25 if n_m == 3 else 0.34
    offsets_b = (np.arange(n_m) - (n_m - 1) / 2.0) * width_b

    for offset, (mkey, mlabel, color) in zip(offsets_b, selected_b):
        mdict = e1b_models[mkey]
        vals = [fn(mdict) for _, fn in metric_extractors]
        bars = ax_b.bar(
            x_b + offset,
            vals,
            width=width_b * 0.92,
            color=color,
            edgecolor="white",
            linewidth=0.6,
            label=mlabel,
        )
        for rect, val in zip(bars, vals):
            ax_b.text(
                rect.get_x() + rect.get_width() / 2.0,
                val + 0.018,
                f"{val:.2f}",
                ha="center",
                va="bottom",
                fontsize=7.2,
                fontweight="bold",
                color="#222222",
                rotation=90,
            )

    ax_b.text(
        2.5,
        1.27,
        "Naive Proxy Trap: 100% Oracle Sentiment\nStill Yields 1.00 SD-FP & 1.00 MS-FN",
        ha="center",
        va="center",
        fontsize=7.3,
        fontweight="bold",
        color="#8c3b00",
        bbox={
            "boxstyle": "round,pad=0.25",
            "facecolor": "#fffaf5",
            "edgecolor": ORANGE,
            "linewidth": 0.9,
        },
    )

    ax_b.set_xlim(-0.55, 3.55)
    ax_b.set_xticks(x_b)
    ax_b.set_xticklabels([lbl for lbl, _ in metric_extractors])
    ax_b.set_ylim(0.0, 1.42)
    ax_b.set_yticks([0.0, 0.25, 0.50, 0.75, 1.00])
    ax_b.set_ylabel("Accuracy / Naive Proxy Error Rate")
    ax_b.set_title(f"(b) E1B Bilingual 4-Quadrant Divergence (N={n_cases})", pad=28)
    ax_b.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, 1.015),
        ncol=len(selected_b),
        frameon=True,
        facecolor="white",
        framealpha=0.95,
        fontsize=7.3,
        columnspacing=0.9,
        handletextpad=0.4,
    )

    fig.suptitle(
        "Experiment 1 (Left Ear): Sentiment Polarity Performance vs. Affect–Symptom Proxy Divergence",
        fontsize=11.6,
        fontweight="bold",
        color=NAVY,
        y=0.965,
    )

    out_path = outdir / "fig2_e1_sentiment_and_divergence.png"
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    return out_path


# ==============================================================================
# FIGURE 3: Experiment 2 — Risk-Coverage & Category-Level Selective Abstention
# ==============================================================================
def _place_non_overlapping_callouts(
    fig: plt.Figure,
    ax: plt.Axes,
    items: list[dict[str, Any]],
    curve_xy: list[tuple[float, float]],
) -> None:
    """Place scatter callout boxes using exact renderer pixel extents to guarantee zero overlap."""
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    ax_bb = ax.get_window_extent(renderer=renderer)

    marker_px = [tuple(ax.transData.transform((it["x"], it["y"]))) for it in items]
    curve_px = [tuple(ax.transData.transform((cx, cy))) for cx, cy in curve_xy]

    # Measure exact rendered box sizes (width_px, height_px) at origin first
    box_sizes_px: list[tuple[float, float]] = []
    for it in items:
        probe = ax.text(
            0.5,
            0.5,
            it["label"],
            transform=ax.transAxes,
            ha="center",
            va="center",
            fontsize=7.1,
            fontweight="bold",
            bbox={"boxstyle": "round,pad=0.25"},
        )
        fig.canvas.draw()
        t_bb = probe.get_window_extent(renderer=renderer)
        # Include rounded bbox padding around text glyph extent
        box_sizes_px.append((t_bb.width + 18.0, t_bb.height + 16.0))
        probe.remove()

    cand_u = np.linspace(0.06, 0.94, 30)
    cand_v = np.linspace(0.08, 0.93, 26)

    placed_px: list[tuple[float, float, float, float]] = []
    order = sorted(
        range(len(items)), key=lambda idx: (items[idx]["y"], items[idx]["x"])
    )

    for idx in order:
        it = items[idx]
        mx, my = marker_px[idx]
        bw, bh = box_sizes_px[idx]

        best_score = float("inf")
        best_center_px: tuple[float, float] | None = None

        for cu in cand_u:
            cx = ax_bb.x0 + cu * ax_bb.width
            left, right = cx - bw / 2.0, cx + bw / 2.0
            if left < ax_bb.x0 + 8.0 or right > ax_bb.x1 - 8.0:
                continue

            for cv in cand_v:
                cy = ax_bb.y0 + cv * ax_bb.height
                bot, top = cy - bh / 2.0, cy + bh / 2.0
                if bot < ax_bb.y0 + 8.0 or top > ax_bb.y1 - 8.0:
                    continue

                dist_px = float(np.hypot(cx - mx, cy - my))
                if dist_px < 32.0:
                    continue

                ux_dir = (cx - mx) / dist_px
                uy_dir = (cy - my) / dist_px
                tip_x = mx + 22.0 * ux_dir
                tip_y = my + 22.0 * uy_dir
                hl = min(left, tip_x)
                hr = max(right, tip_x)
                hb = min(bot, tip_y)
                ht = max(top, tip_y)

                # Strict rejection against already placed annotation + leader-arrow hulls
                pad_box = 6.0
                overlap = False
                for pl, pr, pb, pt in placed_px:
                    if not (
                        hr + pad_box < pl
                        or hl - pad_box > pr
                        or ht + pad_box < pb
                        or hb - pad_box > pt
                    ):
                        overlap = True
                        break
                if overlap:
                    continue

                # Strict rejection against covering any scatter marker (16px radius)
                pad_mk = 16.0
                for jx, jy in marker_px:
                    if (
                        left - pad_mk <= jx <= right + pad_mk
                        and bot - pad_mk <= jy <= top + pad_mk
                    ):
                        overlap = True
                        break
                if overlap:
                    continue

                # Do not straddle horizontally across a nearby unplaced marker's x-column
                for j_idx, (jx, jy) in enumerate(marker_px):
                    if j_idx == idx:
                        continue
                    if abs(jy - my) < 80.0 and abs(jx - mx) < 140.0:
                        if jx > mx and hr > jx - 10.0:
                            overlap = True
                            break
                        if jx < mx and hl < jx + 10.0:
                            overlap = True
                            break
                        if jx == mx and idx < j_idx and hl < mx + 6.0:
                            overlap = True
                            break
                if overlap:
                    continue

                # Soft penalty for crossing curve vertices
                curve_pen = 0.0
                for qx, qy in curve_px:
                    if left - 4.0 <= qx <= right + 4.0 and bot - 4.0 <= qy <= top + 4.0:
                        curve_pen += 55.0

                score = dist_px + curve_pen
                if score < best_score:
                    best_score = score
                    best_center_px = (cx, cy)

        if best_center_px is None:
            best_center_px = (
                float(np.clip(mx, ax_bb.x0 + bw / 2 + 10, ax_bb.x1 - bw / 2 - 10)),
                float(
                    np.clip(
                        my + bh + 28, ax_bb.y0 + bh / 2 + 10, ax_bb.y1 - bh / 2 - 10
                    )
                ),
            )

        bx, by = best_center_px
        tx, ty = ax.transData.inverted().transform((bx, by))
        ann = ax.annotate(
            it["label"],
            xy=(it["x"], it["y"]),
            xytext=(float(tx), float(ty)),
            ha="center",
            va="center",
            fontsize=7.1,
            fontweight="bold",
            color=it["text_color"],
            bbox={
                "boxstyle": "round,pad=0.25",
                "facecolor": it.get("bg", "white"),
                "edgecolor": it["color"],
                "linewidth": 0.95,
                "alpha": 0.96,
            },
            arrowprops={
                "arrowstyle": "-",
                "color": it["color"],
                "lw": 1.0,
                "shrinkA": 2,
                "shrinkB": 6,
            },
            zorder=7,
        )
        fig.canvas.draw()
        ann_bb = ann.get_window_extent(renderer=renderer)
        placed_px.append((ann_bb.x0, ann_bb.x1, ann_bb.y0, ann_bb.y1))


def _render_fig3_e2(summary: dict, outdir: Path) -> Path:
    e2 = summary["e2"]
    methods = e2["methods"]
    curve = e2["ml_risk_coverage_curve"]

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(12.0, 4.8), dpi=300)
    fig.subplots_adjust(left=0.065, right=0.985, bottom=0.19, top=0.74, wspace=0.22)

    # --- Panel (a): Selective Classification Coverage vs. Selective Risk ---
    _style_data_axis(ax_a, grid_axis="both")

    ax_a.axvspan(0.46, 0.54, color="#e8f7f1", alpha=0.75, zorder=0)
    ax_a.axvline(0.50, color=TEAL, linestyle=":", linewidth=1.3, zorder=1)

    curve_sorted = sorted(curve, key=lambda r: float(r["coverage"]))
    c_cov = [float(r["coverage"]) for r in curve_sorted]
    c_risk = [float(r["selective_risk"]) for r in curve_sorted]
    ax_a.plot(
        c_cov,
        c_risk,
        color=STEEL,
        linewidth=2.0,
        linestyle="--",
        marker="o",
        markersize=4.2,
        label="Calibrated TF-IDF+LR Curve (τ∈[0, 0.90])",
        zorder=3,
    )

    ax_a.scatter(
        [0.50],
        [0.00],
        s=210,
        facecolors="none",
        edgecolors=TEAL,
        linewidths=2.2,
        marker="o",
        label="Ideal Point (0.50, 0.00)",
        zorder=5,
    )

    point_specs = [
        ("naive_keyword_heuristic", "Naive Keyword", ORANGE, "X", 85),
        ("tfidf_calibrated_lr_forced", "Calib. LR\nForced", SLATE, "P", 85),
        ("rule_provider_screening", "RuleProvider\n(Screening)", NAVY, "s", 75),
        (
            "rule_provider_clarification_ctx",
            "RuleProvider\n(Clarif. Ctx)",
            PURPLE,
            "^",
            85,
        ),
    ]
    if "live_dual_channel_chatbot" in methods:
        point_specs.append(
            ("live_dual_channel_chatbot", "Live Dual-\nChannel", TEAL, "D", 85)
        )

    callout_items: list[dict[str, Any]] = [
        {
            "x": 0.50,
            "y": 0.00,
            "label": "Ideal Target\n(0.50, 0.00)",
            "color": TEAL,
            "text_color": "#0e5a43",
            "bg": "#eefaf5",
        }
    ]

    max_risk = max(c_risk + [0.55])
    for mkey, short_lbl, color, marker, size in point_specs:
        if mkey not in methods:
            continue
        cx = float(methods[mkey]["coverage"])
        cy = float(methods[mkey]["selective_risk"])
        max_risk = max(max_risk, cy)
        ax_a.scatter(
            [cx],
            [cy],
            s=size,
            color=color,
            edgecolor="white",
            linewidths=0.9,
            marker=marker,
            zorder=6,
        )
        callout_items.append(
            {
                "x": cx,
                "y": cy,
                "label": f"{short_lbl}\n({cx:.2f}, {cy:.2f})",
                "color": color,
                "text_color": "#222222",
                "bg": "white",
            }
        )

    ax_a.set_xlim(-0.04, 1.06)
    ax_a.set_xticks([0.0, 0.25, 0.50, 0.75, 1.00])
    ax_a.set_ylim(-0.06, min(1.02, max(0.74, max_risk + 0.18)))
    ax_a.set_xlabel("Coverage (Fraction of Utterances Assigned Integer 0–3)")
    ax_a.set_ylabel("Selective Risk (Error Rate | Accepted)")
    ax_a.set_title("(a) Coverage vs. Selective Risk (32/64 Resolvable)", pad=28)
    ax_a.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, 1.015),
        ncol=2,
        frameon=True,
        facecolor="white",
        framealpha=0.95,
        fontsize=7.3,
        columnspacing=0.9,
    )

    _place_non_overlapping_callouts(fig, ax_a, callout_items, list(zip(c_cov, c_risk)))

    # --- Panel (b): Category-Level Accuracy across 8 Diagnostic Categories ---
    _style_data_axis(ax_b)
    categories = [
        ("R1_canonical", "R1\nCanon."),
        ("R2_exact_days", "R2\nDays"),
        ("R3_colloquial_contextual", "R3\nColloq."),
        ("R4_window_contrast_resolved", "R4\nContrast"),
        ("A1_vague_quantifier", "A1\nVague"),
        ("A2_wrong_timeframe", "A2\nWindow"),
        ("A3_cross_boundary_range", "A3\nRange"),
        ("A4_affect_only_no_frequency", "A4\nAffect"),
    ]

    cat_methods: list[tuple[str, str, str]] = [
        ("tfidf_calibrated_lr_tau_060", "Calib. LR (τ=0.60)", STEEL),
        ("rule_provider_screening", "RuleProvider", NAVY),
    ]
    if "live_dual_channel_chatbot" in methods:
        cat_methods.append(("live_dual_channel_chatbot", "Live Dual-Channel", TEAL))
    else:
        cat_methods.append(("naive_keyword_heuristic", "Naive Keyword", ORANGE))

    ax_b.axvspan(3.5, 7.55, color="#f6f4fb", alpha=0.65, zorder=0)
    ax_b.axvline(3.5, color=PURPLE, linestyle="--", linewidth=1.0, alpha=0.8, zorder=1)

    x_b = np.arange(len(categories), dtype=float)
    n_cm = len(cat_methods)
    width_b = 0.26
    offsets_b = (np.arange(n_cm) - (n_cm - 1) / 2.0) * width_b

    for offset, (mkey, mlabel, color) in zip(offsets_b, cat_methods):
        by_cat = methods[mkey]["by_category"]
        vals = [float(by_cat[ckey]["accuracy"]) for ckey, _ in categories]
        bars = ax_b.bar(
            x_b + offset,
            vals,
            width=width_b * 0.90,
            color=color,
            edgecolor="white",
            linewidth=0.5,
            label=mlabel,
        )
        for rect, val in zip(bars, vals):
            ax_b.text(
                rect.get_x() + rect.get_width() / 2.0,
                val + 0.018,
                f"{val:.2f}",
                ha="center",
                va="bottom",
                fontsize=6.4,
                fontweight="bold",
                color="#222222",
                rotation=90,
            )

    ax_b.text(
        1.5,
        1.25,
        "Resolvable (Exact 0–3)",
        ha="center",
        va="center",
        fontsize=7.8,
        fontweight="bold",
        color=NAVY,
    )
    ax_b.text(
        5.5,
        1.25,
        "Must Abstain (frequency=None)",
        ha="center",
        va="center",
        fontsize=7.8,
        fontweight="bold",
        color=PURPLE,
    )

    ax_b.set_xlim(-0.55, 7.55)
    ax_b.set_xticks(x_b)
    ax_b.set_xticklabels([lbl for _, lbl in categories], fontsize=7.8)
    ax_b.set_ylim(0.0, 1.36)
    ax_b.set_yticks([0.0, 0.25, 0.50, 0.75, 1.00])
    ax_b.set_ylabel("Category Accuracy / Abstention Recall")
    ax_b.set_title(
        "(b) Accuracy Across 8 Bilingual Diagnostic Categories (N=64)", pad=28
    )
    ax_b.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, 1.015),
        ncol=3,
        frameon=True,
        facecolor="white",
        framealpha=0.95,
        fontsize=7.2,
        columnspacing=0.8,
        handletextpad=0.4,
    )

    fig.suptitle(
        "Experiment 2 (Right Ear): Bilingual Symptom Extraction & Selective Abstention",
        fontsize=11.6,
        fontweight="bold",
        color=NAVY,
        y=0.965,
    )

    out_path = outdir / "fig3_e2_risk_coverage_and_abstention.png"
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    return out_path


# ==============================================================================
# FIGURE 4: Experiment 3 — Partial-Observation Early Risk Triage
# ==============================================================================
def _render_fig4_e3(summary: dict, outdir: Path) -> Path:
    e3 = summary["e3"]
    depths = e3["depths"]
    n_test = int(e3.get("n_test", 80))

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(12.0, 4.8), dpi=300)
    fig.subplots_adjust(left=0.065, right=0.985, bottom=0.18, top=0.75, wspace=0.22)

    channels = [
        ("S_affect_only", "S_k: Affect Only (Left Ear)", ORANGE, "s", "--"),
        ("N_partial_symptom", "N_k: Partial Symptom (Right Ear)", STEEL, "^", "-."),
        ("F_dual_fusion", "F_k: Dual-Channel Fusion (N_k + S_k)", TEAL, "o", "-"),
    ]

    # --- Panel (a): Held-Out Test AUROC across k in {2, 4, 6} ---
    _style_data_axis(ax_a, grid_axis="both")
    ks = [2, 4, 6]

    series_auroc: dict[str, list[float]] = {}
    all_auc: list[float] = []
    legend_handles: list[Line2D] = []
    for ckey, clabel, color, marker, ls in channels:
        ys = [float(depths[str(k)][ckey]["logistic_regression"]["auroc"]) for k in ks]
        series_auroc[ckey] = ys
        all_auc.extend(ys)
        (line,) = ax_a.plot(
            ks,
            ys,
            color=color,
            marker=marker,
            linestyle=ls,
            linewidth=2.3 if ckey == "F_dual_fusion" else 1.9,
            markersize=7.0,
            label=clabel,
            zorder=4 if ckey == "F_dual_fusion" else 3,
        )
        legend_handles.append(line)

    y_min = max(0.42, min(all_auc) - 0.10)
    y_max = min(1.07, max(all_auc) + 0.10)
    y_span = y_max - y_min
    ax_a.set_ylim(y_min, y_max)
    ax_a.set_xlim(1.50, 6.55)
    ax_a.set_xticks(ks)
    ax_a.set_xticklabels(
        [
            "k = 2 turns\n(25% window)",
            "k = 4 turns\n(50% window)",
            "k = 6 turns\n(75% window)",
        ]
    )

    min_sep = 0.082 * y_span
    for idx_k, k in enumerate(ks):
        pts = sorted(
            [
                (series_auroc[ckey][idx_k], ckey, color)
                for ckey, _, color, _, _ in channels
            ],
            key=lambda t: t[0],
        )
        adj_y = [pts[0][0] - 0.03 * y_span, pts[1][0], pts[2][0] + 0.03 * y_span]
        for j in range(1, len(adj_y)):
            if adj_y[j] - adj_y[j - 1] < min_sep:
                adj_y[j] = adj_y[j - 1] + min_sep
        overflow = adj_y[-1] - (y_max - 0.045 * y_span)
        if overflow > 0:
            adj_y = [y_val - overflow for y_val in adj_y]
            for j in range(len(adj_y) - 2, -1, -1):
                if adj_y[j + 1] - adj_y[j] < min_sep:
                    adj_y[j] = adj_y[j + 1] - min_sep

        x_nudge = -0.20 if k == 6 else 0.20
        ha_align = "right" if k == 6 else "left"
        for (raw_y, _ckey, color), ty in zip(pts, adj_y):
            ax_a.annotate(
                f"{raw_y:.3f}",
                xy=(k, raw_y),
                xytext=(k + x_nudge, ty),
                ha=ha_align,
                va="center",
                fontsize=7.5,
                fontweight="bold",
                color=color,
                bbox={
                    "boxstyle": "round,pad=0.16",
                    "facecolor": "white",
                    "edgecolor": color,
                    "linewidth": 0.7,
                    "alpha": 0.95,
                },
                arrowprops={"arrowstyle": "-", "color": color, "lw": 0.8, "shrinkB": 3},
                zorder=6,
            )

    ax_a.set_ylabel("Held-Out Test AUROC (Logistic Regression)")
    ax_a.set_title(f"(a) Partial-Observation Early Triage AUROC (N={n_test})", pad=10)

    # --- Panel (b): k=2 and k=4 Brier Score & Divergent-Quadrant Error Rates ---
    _style_data_axis(ax_b)
    group_defs = [
        ("2", "brier_score", "Brier\nScore"),
        ("2", "situational_distress_fp_rate", "Sit. Dist.\nFP Rate"),
        ("2", "masked_somatic_fn_rate", "Masked\nFN Rate"),
        ("4", "brier_score", "Brier\nScore"),
        ("4", "situational_distress_fp_rate", "Sit. Dist.\nFP Rate"),
        ("4", "masked_somatic_fn_rate", "Masked\nFN Rate"),
    ]

    ax_b.axvspan(2.5, 5.55, color="#f4f7fb", alpha=0.75, zorder=0)
    ax_b.axvline(2.5, color=SLATE, linestyle="--", linewidth=1.0, alpha=0.75, zorder=1)

    x_b = np.arange(len(group_defs), dtype=float)
    width_b = 0.25
    offsets_b = [-width_b, 0.0, width_b]

    max_b = 0.0
    for offset, (ckey, clabel, color, _marker, _ls) in zip(offsets_b, channels):
        vals = [
            float(depths[k_str][ckey]["logistic_regression"][m_field])
            for k_str, m_field, _ in group_defs
        ]
        max_b = max(max_b, max(vals))
        bars = ax_b.bar(
            x_b + offset,
            vals,
            width=width_b * 0.90,
            color=color,
            edgecolor="white",
            linewidth=0.55,
            label=clabel,
        )
        for rect, val in zip(bars, vals):
            ax_b.text(
                rect.get_x() + rect.get_width() / 2.0,
                val + 0.018,
                f"{val:.2f}",
                ha="center",
                va="bottom",
                fontsize=6.6,
                fontweight="bold",
                color="#222222",
                rotation=90,
            )

    y_ceil_b = max(1.16, max_b + 0.34)
    ax_b.text(
        1.0,
        y_ceil_b * 0.92,
        "Early Depth: k = 2 Turns",
        ha="center",
        va="center",
        fontsize=8.0,
        fontweight="bold",
        color=NAVY,
    )
    ax_b.text(
        4.0,
        y_ceil_b * 0.92,
        "Mid Depth: k = 4 Turns",
        ha="center",
        va="center",
        fontsize=8.0,
        fontweight="bold",
        color=NAVY,
    )

    ax_b.set_xlim(-0.55, 5.55)
    ax_b.set_xticks(x_b)
    ax_b.set_xticklabels([lbl for _, _, lbl in group_defs], fontsize=8.0)
    ax_b.set_ylim(0.0, y_ceil_b)
    ax_b.set_ylabel("Calibration / Divergent Error Rate (↓)")
    ax_b.set_title(
        "(b) Brier Score & Divergent-Quadrant Errors (k = 2 vs. k = 4)", pad=10
    )

    # Shared figure legend between suptitle and panel titles
    fig.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.905),
        ncol=3,
        frameon=True,
        facecolor="white",
        framealpha=0.95,
        fontsize=8.0,
    )
    fig.suptitle(
        "Experiment 3 (Two Ears Combined): Multi-Turn Partial-Observation Early Risk Triage",
        fontsize=11.6,
        fontweight="bold",
        color=NAVY,
        y=0.968,
    )

    out_path = outdir / "fig4_e3_partial_observation_triage.png"
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    return out_path


# ==============================================================================
# FIGURE 5: Experiment 4 — Dialogue Policy Comparison & Safety/Invariance Audits
# ==============================================================================
def _render_fig5_e4(summary: dict, outdir: Path) -> Path:
    e4 = summary["e4"]
    pol = e4["e4a_policy_comparison"]
    live_sessions = e4.get("e4b_live_sessions") or []
    audits = e4["e4c_architectural_audits"]

    fig = plt.figure(figsize=(12.0, 4.8), dpi=300)
    outer = GridSpec(
        1,
        2,
        figure=fig,
        width_ratios=[1.18, 1.0],
        left=0.058,
        right=0.985,
        bottom=0.18,
        top=0.72,
        wspace=0.29,
    )

    gs_a = GridSpecFromSubplotSpec(
        1, 2, subplot_spec=outer[0], width_ratios=[1.0, 2.45], wspace=0.32
    )
    ax_a_turns = fig.add_subplot(gs_a[0])
    ax_a_rates = fig.add_subplot(gs_a[1])
    ax_b = fig.add_subplot(outer[1])

    policies = [
        ("P0_rigid_rule_questionnaire", "P0: Rigid Rule", SLATE),
        ("P1_greedy_unclarified", "P1: Greedy Unclarified", ORANGE),
        ("P2_selective_dual_channel", "P2: Selective Dual-Channel", TEAL),
    ]

    # --- Panel (a, left): Mean User Turns ---
    _style_data_axis(ax_a_turns)
    x_t = np.arange(len(policies), dtype=float)
    turn_vals = [float(pol[pk]["mean_user_turns"]) for pk, _, _ in policies]
    turn_stds = [float(pol[pk].get("std_user_turns", 0.0)) for pk, _, _ in policies]
    bars_t = ax_a_turns.bar(
        x_t,
        turn_vals,
        yerr=turn_stds,
        capsize=3.0,
        width=0.62,
        color=[c for _, _, c in policies],
        edgecolor="white",
        linewidth=0.6,
        error_kw={"elinewidth": 1.0, "ecolor": "#333333"},
    )
    for rect, val, std in zip(bars_t, turn_vals, turn_stds):
        ax_a_turns.text(
            rect.get_x() + rect.get_width() / 2.0,
            val + std + 0.35,
            f"{val:.1f}",
            ha="center",
            va="bottom",
            fontsize=7.6,
            fontweight="bold",
            color="#222222",
        )
    ax_a_turns.set_xticks(x_t)
    ax_a_turns.set_xticklabels(["P0", "P1", "P2"])
    ax_a_turns.set_ylim(0.0, max(turn_vals) * 1.34 + 1.2)
    ax_a_turns.set_ylabel("Mean User Turns (↓)")
    ax_a_turns.set_title("Turn Burden", fontsize=9.0, pad=5)

    # --- Panel (a, right): Pre-Review MAE, Silent-Error Rate, 4-Quadrant Accuracy ---
    _style_data_axis(ax_a_rates)
    rate_metrics = [
        ("mean_pre_review_item_mae", "Pre-Review\nItem MAE (↓)"),
        ("personas_with_silent_error_rate", "Silent-Error\nPersona Rate (↓)"),
        ("quadrant_detection_accuracy", "4-Quadrant\nDetect. Acc. (↑)"),
    ]
    x_r = np.arange(len(rate_metrics), dtype=float)
    width_r = 0.25
    offsets_r = [-width_r, 0.0, width_r]

    for offset, (pkey, plabel, color) in zip(offsets_r, policies):
        vals = [float(pol[pkey][m_field]) for m_field, _ in rate_metrics]
        bars_r = ax_a_rates.bar(
            x_r + offset,
            vals,
            width=width_r * 0.92,
            color=color,
            edgecolor="white",
            linewidth=0.6,
            label=plabel,
        )
        for rect, val in zip(bars_r, vals):
            ax_a_rates.text(
                rect.get_x() + rect.get_width() / 2.0,
                val + 0.02,
                f"{val:.2f}",
                ha="center",
                va="bottom",
                fontsize=7.1,
                fontweight="bold",
                color="#222222",
                rotation=90,
            )

    ax_a_rates.set_xticks(x_r)
    ax_a_rates.set_xticklabels([lbl for _, lbl in rate_metrics], fontsize=8.0)
    ax_a_rates.set_ylim(0.0, 1.25)
    ax_a_rates.set_yticks([0.0, 0.25, 0.50, 0.75, 1.00])
    ax_a_rates.set_ylabel("Item MAE / Proportion")
    ax_a_rates.set_title("Accuracy & Alignment (N=32 Personas)", fontsize=9.0, pad=5)

    pos_l = ax_a_turns.get_position()
    pos_r = ax_a_rates.get_position()
    panel_a_cx = (pos_l.x0 + pos_r.x1) / 2.0

    legend_handles = [
        Rectangle((0, 0), 1, 1, facecolor=c, edgecolor="white", label=lbl)
        for _, lbl, c in policies
    ]
    fig.legend(
        handles=legend_handles,
        loc="center",
        bbox_to_anchor=(panel_a_cx, 0.822),
        ncol=3,
        frameon=True,
        facecolor="white",
        framealpha=0.95,
        fontsize=7.3,
        columnspacing=0.9,
        handletextpad=0.4,
    )
    fig.text(
        panel_a_cx,
        0.875,
        "(a) E4A: 32-Persona Bilingual Dialogue Policy Comparison",
        ha="center",
        va="bottom",
        fontsize=10.2,
        fontweight="bold",
        color="#111111",
    )

    # --- Panel (b): End-to-End Architectural Safety & Invariance Verification ---
    _style_data_axis(ax_b, grid_axis="x")
    inv = audits["affect_score_invariance"]
    adv = audits["adversarial_quote_and_schema_audit"]
    grd = audits["pre_api_safety_guard_audit"]

    inv_total = int(inv["configurations_tested"])
    inv_pass = inv_total - int(inv["violations"])
    adv_total = int(adv["adversarial_payloads_tested"])
    adv_rej = int(adv["rejected_count"])
    grd_total = int(grd["cases_tested"])
    grd_pass = int(grd["passed_state_wipe_count"])

    audit_rows: list[tuple[str, float, str, str]] = [
        (
            "Affect Score-Invariance\nPass Rate",
            float(inv["pass_rate"]),
            f"{inv['pass_rate'] * 100:.1f}% ({inv_pass}/{inv_total})",
            NAVY,
        ),
        (
            "Adversarial Quote/Schema\nRejection Rate",
            float(adv["rejection_rate"]),
            f"{adv['rejection_rate'] * 100:.1f}% ({adv_rej}/{adv_total})",
            STEEL,
        ),
        (
            "Pre-API Safety Guard\nState-Wipe Pass Rate",
            float(grd["pass_rate"]),
            f"{grd['pass_rate'] * 100:.1f}% ({grd_pass}/{grd_total}, {grd['downstream_llm_calls_triggered']} API)",
            PURPLE,
        ),
    ]

    if live_sessions:
        n_live = len(live_sessions)
        q_ok = sum(1 for s in live_sessions if s.get("all_quotes_exact_substring"))
        s_ok = sum(1 for s in live_sessions if s.get("score_invariance_verified"))
        q_rate = q_ok / n_live
        s_rate = s_ok / n_live
        audit_rows.append(
            (
                "Live Session Exact-Quote\nSubstring Rate",
                float(q_rate),
                f"{q_rate * 100:.1f}% ({q_ok}/{n_live})",
                TEAL,
            )
        )
        audit_rows.append(
            (
                "Live Session Score-\nInvariance Rate",
                float(s_rate),
                f"{s_rate * 100:.1f}% ({s_ok}/{n_live})",
                ORANGE,
            )
        )

    y_b = np.arange(len(audit_rows), dtype=float)[::-1]
    rates_b = [r[1] for r in audit_rows]
    colors_b = [r[3] for r in audit_rows]
    bars_b = ax_b.barh(
        y_b,
        rates_b,
        height=0.58,
        color=colors_b,
        edgecolor="white",
        linewidth=0.6,
    )
    ax_b.axvline(1.0, color="#222222", linestyle=":", linewidth=1.0, zorder=2)

    for rect, (_lbl, val, badge, _col) in zip(bars_b, audit_rows):
        ax_b.text(
            val + 0.02,
            rect.get_y() + rect.get_height() / 2.0,
            badge,
            ha="left",
            va="center",
            fontsize=7.5,
            fontweight="bold",
            color="#222222",
        )

    ax_b.set_yticks(y_b)
    ax_b.set_yticklabels([r[0] for r in audit_rows], fontsize=8.0)
    ax_b.set_xlim(0.0, 1.46)
    ax_b.set_xticks([0.0, 0.25, 0.50, 0.75, 1.00])
    ax_b.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax_b.set_xlabel("Verification Pass / Rejection Rate")

    pos_b = ax_b.get_position()
    fig.text(
        (pos_b.x0 + pos_b.x1) / 2.0,
        0.875,
        "(b) E4B/C: Safety, Provenance & Score-Invariance Audits",
        ha="center",
        va="bottom",
        fontsize=10.2,
        fontweight="bold",
        color="#111111",
    )

    fig.suptitle(
        "Experiment 4 (End-to-End Chatbot): Selective Clarification Policy & Deterministic Invariants",
        fontsize=11.6,
        fontweight="bold",
        color=NAVY,
        y=0.968,
    )

    out_path = outdir / "fig5_e4_policy_and_invariance.png"
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    return out_path


def generate_all_figures(summary: dict, outdir: Path) -> list[Path]:
    """Render all 5 publication-grade 300-DPI PNG figures into ``outdir``."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    with plt.rc_context(RC_STYLE):
        paths = [
            _render_fig1_architecture(outdir),
            _render_fig2_e1(summary, outdir),
            _render_fig3_e2(summary, outdir),
            _render_fig4_e3(summary, outdir),
            _render_fig5_e4(summary, outdir),
        ]
    return paths


def _render_clean_fig1(outdir: Path) -> Path:
    """Clean, large-font workflow diagram without Python function or variable names."""
    fig, ax = plt.subplots(figsize=(11.5, 5.0))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 56)
    ax.axis("off")

    ax.text(
        50,
        53.2,
        "Dual-Channel Bilingual Preliminary Screening Chatbot Workflow",
        ha="center",
        va="center",
        fontsize=14.0,
        fontweight="bold",
        color=NAVY,
    )

    def box(x, y, w, h, title, body, fc, ec, title_color=NAVY):
        p = FancyBboxPatch(
            (x, y),
            w,
            h,
            boxstyle="round,pad=0.6,rounding_size=1.4",
            facecolor=fc,
            edgecolor=ec,
            linewidth=1.8,
        )
        ax.add_patch(p)
        ax.text(
            x + w / 2,
            y + h - 3.2,
            title,
            ha="center",
            va="top",
            fontsize=11.0,
            fontweight="bold",
            color=title_color,
        )
        ax.text(
            x + w / 2,
            y + (h - 4.2) / 2,
            body,
            ha="center",
            va="center",
            fontsize=9.6,
            color="#222222",
            linespacing=1.32,
        )

    def arrow(x1, y1, x2, y2, col=NAVY, style="-|>"):
        ax.add_patch(
            FancyArrowPatch(
                (x1, y1),
                (x2, y2),
                arrowstyle=style,
                mutation_scale=15,
                linewidth=1.8,
                color=col,
            )
        )

    # Left column: Input & Safety Filter
    box(
        2,
        29,
        20,
        19,
        "1. User Message",
        "Natural Cantonese,\nTraditional Chinese,\nor English chat\n(multi-topic allowed)",
        "#f3f7fc",
        STEEL,
    )
    box(
        2,
        5,
        20,
        18,
        "2. Safety Filter",
        "Pre-API check blocks\ndemo interrupt markers\nand clears session\nbefore model call",
        "#fdf3ef",
        ORANGE,
        title_color="#9c3d00",
    )
    arrow(12, 29, 12, 23.4, col=NAVY)

    # Middle column: Two Channels
    box(
        28,
        31,
        36,
        17,
        "3A. Affect Channel (Left Ear)",
        "• Tracks turn-level emotional tone\n• Guides brief, polite empathy in reply\n• Never supplies or alters symptom scores",
        "#eef6fb",
        STEEL,
    )
    box(
        28,
        5,
        36,
        19,
        "3B. Symptom Channel (Right Ear)",
        "• Extracts 8 PHQ-8 items (past 14 days)\n• Verifies exact word-for-word user quote\n• Maps day counts (0–1→0, 2–6→1, 7–11→2, 12–14→3)\n• Abstains & asks follow-up when vague",
        "#edf8f4",
        TEAL,
        title_color="#0f6b50",
    )
    arrow(22.3, 15.5, 27.6, 38.0, col=STEEL)
    arrow(22.3, 13.0, 27.6, 14.5, col=TEAL)

    # Scoring boundary line between 3A and 3B/4
    ax.plot([27, 98], [27.2, 27.2], linestyle="--", linewidth=2.0, color=FIREWALL_RED)
    ax.text(
        63,
        28.1,
        "Scoring Boundary: Emotional Tone Never Enters PHQ-8 Calculation",
        ha="center",
        va="bottom",
        fontsize=9.6,
        fontweight="bold",
        color=FIREWALL_RED,
        bbox={
            "boxstyle": "round,pad=0.2",
            "facecolor": "white",
            "edgecolor": FIREWALL_RED,
            " lw": 0.8,
        }
        if False
        else {
            "boxstyle": "round,pad=0.22",
            "facecolor": "#fff7f7",
            "edgecolor": FIREWALL_RED,
            "linewidth": 0.9,
        },
    )

    # Right column: Review, Scoring & Post-Session Note
    box(
        70,
        5,
        28,
        19,
        "4. User Review & Score",
        "• User checks all 8 quotes\n  and can edit 0–3 options\n• Explicit confirmation sums\n  confirmed 0–24 PHQ-8 score",
        "#eef3fa",
        NAVY,
    )
    box(
        70,
        31,
        28,
        17,
        "5. Tone–Symptom Note",
        "• Compares session tone\n  with confirmed total\n• Flags Situational Distress\n  or Masked Somatic pattern",
        "#f5f2fa",
        PURPLE,
        title_color="#4b4584",
    )
    arrow(64.4, 14.5, 69.6, 14.5, col=NAVY)
    arrow(64.4, 39.5, 69.6, 39.5, col=PURPLE)
    arrow(84, 24.3, 84, 30.6, col=PURPLE)

    out_path = outdir / "fig1_clean_architecture.png"
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return out_path


def _render_clean_fig2(summary_v2: dict, outdir: Path) -> Path:
    """Two-panel E1 chart where ALL bars in both panels represent Accuracy / Score (higher is better ↑)."""
    e1a = summary_v2["e1"]["e1a_tweeteval"]["test_models"]
    e1b = summary_v2["e1"]["e1b_quadrant_divergence"]["models"]

    fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(12.2, 4.7))
    fig.subplots_adjust(left=0.06, right=0.98, bottom=0.18, top=0.80, wspace=0.24)

    # Panel (a): TweetEval (all higher = better)
    models_a = [
        ("majority", "Majority", SLATE),
        ("tfidf_multinomial_nb", "Multinomial NB", TEAL),
        ("tfidf_logistic_regression", "Logistic Reg.", STEEL),
        ("tfidf_linear_svm", "Linear SVM", NAVY),
    ]
    metrics_a = [
        ("accuracy", "Accuracy ↑"),
        ("macro_f1", "Macro-F1 ↑"),
        ("macro_recall", "Macro-Recall ↑"),
    ]
    xa = np.arange(len(metrics_a))
    wa = 0.19
    for idx, (mkey, mlbl, col) in enumerate(models_a):
        vals = [float(e1a[mkey][mk]) for mk, _ in metrics_a]
        offs = (idx - 1.5) * wa
        bars = ax_a.bar(xa + offs, vals, width=wa * 0.92, color=col, label=mlbl)
        for r in bars:
            v = r.get_height()
            ax_a.text(
                r.get_x() + r.get_width() / 2,
                v + 0.015,
                f"{v:.2f}",
                ha="center",
                va="bottom",
                fontsize=8.0,
                fontweight="bold",
            )
    ax_a.set_xticks(xa)
    ax_a.set_xticklabels([lbl for _, lbl in metrics_a], fontsize=9.8)
    ax_a.set_ylim(0, 0.74)
    ax_a.set_ylabel("Score on Held-Out Test Split (Higher = Better ↑)", fontsize=9.8)
    ax_a.set_title(
        "(a) Public TweetEval Sentiment Benchmark (N = 12,284)", fontsize=10.6, pad=24
    )
    ax_a.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, 1.01),
        ncol=4,
        fontsize=8.2,
        frameon=True,
    )
    ax_a.grid(True, axis="y", linestyle=":", alpha=0.5)

    # Panel (b): E1B — ALL ACCURACY (Higher = Better ↑)!
    models_b = [
        ("tfidf_linear_svm", "TweetEval Linear SVM", STEEL),
        ("live_gpt_terra", "Connected LLM (Terra)", NAVY),
        ("oracle_polarity_ceiling", "100% Perfect Sentiment", ORANGE),
    ]
    cats_b = [
        ("EN Sentiment\nAccuracy ↑", lambda d: float(d["en_polarity"]["accuracy"])),
        ("ZH Sentiment\nAccuracy ↑", lambda d: float(d["zh_polarity"]["accuracy"])),
        (
            "Situational Distress\nScreening Acc ↑",
            lambda d: float(
                d["naive_negative_implies_elevated_phq8"]["by_quadrant"][
                    "situational_distress"
                ]["naive_screening_accuracy"]
            ),
        ),
        (
            "Masked Somatic\nScreening Acc ↑",
            lambda d: float(
                d["naive_negative_implies_elevated_phq8"]["by_quadrant"][
                    "masked_somatic"
                ]["naive_screening_accuracy"]
            ),
        ),
    ]
    ax_b.axvspan(1.5, 3.55, color="#fff3e8", alpha=0.65, zorder=0)
    ax_b.axvline(1.5, color=ORANGE, linestyle="--", linewidth=1.2)
    xb = np.arange(len(cats_b))
    wb = 0.25
    for idx, (mkey, mlbl, col) in enumerate(models_b):
        vals = [fn(e1b[mkey]) for _, fn in cats_b]
        offs = (idx - 1.0) * wb
        bars = ax_b.bar(xb + offs, vals, width=wb * 0.92, color=col, label=mlbl)
        for r in bars:
            v = r.get_height()
            ax_b.text(
                r.get_x() + r.get_width() / 2,
                v + 0.02,
                f"{v * 100:.0f}%",
                ha="center",
                va="bottom",
                fontsize=7.8,
                fontweight="bold",
            )
    ax_b.text(
        2.5,
        0.82,
        "Using 'Negative => PHQ-8 ≥ 10'\nCollapses to 0%–8% Accuracy!",
        ha="center",
        va="center",
        fontsize=8.6,
        fontweight="bold",
        color="#8c3b00",
        bbox={"boxstyle": "round,pad=0.28", "facecolor": "white", "edgecolor": ORANGE},
    )
    ax_b.set_xlim(-0.55, 3.55)
    ax_b.set_xticks(xb)
    ax_b.set_xticklabels([lbl for lbl, _ in cats_b], fontsize=9.2)
    ax_b.set_ylim(0, 1.16)
    ax_b.set_yticks([0.0, 0.25, 0.50, 0.75, 1.00])
    ax_b.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    ax_b.set_ylabel("Accuracy (Higher = Better ↑)", fontsize=9.8)
    ax_b.set_title(
        "(b) Controlled Bilingual Stress Test (N = 48)", fontsize=10.6, pad=24
    )
    ax_b.legend(
        loc="lower center",
        bbox_to_anchor=(0.5, 1.01),
        ncol=3,
        fontsize=8.0,
        frameon=True,
    )
    ax_b.grid(True, axis="y", linestyle=":", alpha=0.5)

    fig.suptitle(
        "Experiment 1: Public Sentiment Baselines and Why Sentiment Alone Fails as a Screening Rule",
        fontsize=12.0,
        fontweight="bold",
        color=NAVY,
        y=0.96,
    )
    out_path = outdir / "fig2_clean_e1_sentiment.png"
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    return out_path


def _render_clean_fig4_walkthrough(outdir: Path) -> Path:
    """Four-stage visual walkthrough of the Bilingual Chatbot UI (Input -> Follow-Up -> Review -> Result)."""
    fig, axes = plt.subplots(2, 2, figsize=(11.8, 5.8))
    fig.subplots_adjust(
        left=0.03, right=0.97, bottom=0.04, top=0.89, wspace=0.08, hspace=0.14
    )
    fig.suptitle(
        "Four-Stage Chatbot Screening Walkthrough (Scenario 2: Matter-of-Fact Somatic Case)",
        fontsize=12.4,
        fontweight="bold",
        color=NAVY,
        y=0.96,
    )

    stages = [
        (
            "Stage 1: Natural Multi-Symptom Input",
            STEEL,
            "#f4f8fc",
            [
                (
                    "Assistant:",
                    "Over the past two weeks, how have your sleep, energy, and daily focus been?",
                ),
                (
                    "User:",
                    '"Fragmented sleep under 4 hours on 12 nights, low energy on 13 days, reduced appetite on 9 days, focus trouble on 8 days, and restlessness was just occasionally."',
                ),
                (
                    "System State:",
                    "• 7 items linked to exact quotes  |  • Item 8 ('occasionally') -> Unresolved",
                ),
            ],
        ),
        (
            "Stage 2: Selective Abstention & Clarification",
            TEAL,
            "#f1faf7",
            [
                (
                    "Assistant:",
                    '"Thank you for sharing those clear counts. For feeling fidgety or restless, roughly how many days in the past two weeks did that happen?"',
                ),
                (
                    "User:",
                    '"To clarify that last restlessness item for the past two weeks: it was 0 days."',
                ),
                (
                    "System State:",
                    "• Item 8 updated to 0 ('Not at all') with quote \"0 days\"  |  • 8/8 Ready",
                ),
            ],
        ),
        (
            "Stage 3: Quote-Backed Batch Review & Edit",
            NAVY,
            "#f2f5fa",
            [
                ("Review Table (All 8 Items Editable Before Scoring):", ""),
                (
                    "• Sleep trouble: Nearly every day (3)",
                    'Quote: "12 nights"   [Dropdown: 0..3]',
                ),
                (
                    "• Tired / low energy: Nearly every day (3)",
                    'Quote: "13 days"     [Dropdown: 0..3]',
                ),
                (
                    "• Restlessness: Not at all (0)",
                    'Quote: "0 days"      [☑ I confirm all 8 answers]',
                ),
            ],
        ),
        (
            "Stage 4: Confirmed PHQ-8 Total & Tone Note",
            PURPLE,
            "#f6f3fb",
            [
                (
                    "Confirmed PHQ-8 Questionnaire Total:",
                    "11 / 24   (Moderate range: 10–14)",
                ),
                (
                    "Session Affect Trace (Sidebar):",
                    "0 Negative  ·  4 Neutral  ·  0 Positive  (Not used in score)",
                ),
                (
                    "Dual-Channel Observation Note:",
                    "Masked / Matter-of-Fact Somatic Pattern — calm neutral tone alongside elevated 2-week symptom burden (>= 10).",
                ),
            ],
        ),
    ]

    for ax, (title, border_col, bg_col, lines) in zip(axes.flat, stages):
        ax.set_xlim(0, 100)
        ax.set_ylim(0, 50)
        ax.axis("off")
        card = FancyBboxPatch(
            (1.5, 1.5),
            97,
            47,
            boxstyle="round,pad=0.5,rounding_size=1.8",
            facecolor=bg_col,
            edgecolor=border_col,
            linewidth=1.8,
        )
        ax.add_patch(card)
        hdr = FancyBboxPatch(
            (1.5, 39.5),
            97,
            9.0,
            boxstyle="round,pad=0.3,rounding_size=1.5",
            facecolor=border_col,
            edgecolor=border_col,
            linewidth=1.0,
        )
        ax.add_patch(hdr)
        ax.text(
            50,
            44.0,
            title,
            ha="center",
            va="center",
            fontsize=10.5,
            fontweight="bold",
            color="white",
        )

        y_cursor = 34.5
        for prefix, body in lines:
            ax.text(
                5.0,
                y_cursor,
                prefix,
                ha="left",
                va="top",
                fontsize=9.0,
                fontweight="bold",
                color=NAVY,
            )
            if body:
                ax.text(
                    5.0,
                    y_cursor - 4.2,
                    body,
                    ha="left",
                    va="top",
                    fontsize=8.6,
                    color="#222222",
                    wrap=True,
                )
                y_cursor -= 11.2
            else:
                y_cursor -= 5.5

    out_path = outdir / "fig4_chatbot_4stage_flow.png"
    fig.savefig(out_path, dpi=300)
    plt.close(fig)
    return out_path


def generate_v2_figures(summary_v2: dict, outdir: Path) -> list[Path]:
    """Render all 4 reader-friendly figures for the polished Undergraduate S1 Report."""
    outdir = Path(outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    with plt.rc_context(RC_STYLE):
        p1 = _render_clean_fig1(outdir)
        p2 = _render_clean_fig2(summary_v2, outdir)

        fig, (ax_a, ax_b) = plt.subplots(1, 2, figsize=(12.2, 4.6))
        fig.subplots_adjust(left=0.07, right=0.98, bottom=0.19, top=0.81, wspace=0.25)

        e2 = summary_v2["e2"]
        curve = e2["ml_risk_coverage_curve"]
        cov_c = [float(r["coverage"]) for r in curve]
        risk_c = [float(r["selective_risk"]) for r in curve]
        ax_a.plot(
            cov_c,
            risk_c,
            color=STEEL,
            linewidth=2.2,
            marker="o",
            markersize=4.8,
            label="TF-IDF + Calibrated LR (threshold sweep)",
        )
        ax_a.scatter(
            [0.50],
            [0.0],
            s=130,
            marker="*",
            color=TEAL,
            zorder=5,
            label="Ideal Point (50% coverage, 0% risk)",
        )

        m80 = e2["methods"]
        pts = [
            ("Naive Keyword", m80["naive_keyword_heuristic"], ORANGE, "D", (-22, 11)),
            (
                "Forced LR (τ=0)",
                m80["tfidf_calibrated_lr_forced"],
                PURPLE,
                "s",
                (-76, -20),
            ),
            ("Connected Chatbot", m80["live_dual_channel_chatbot"], NAVY, "P", (8, 12)),
        ]
        for lbl, md, col, mk, ofs in pts:
            cx, cy = float(md["coverage"]), float(md["selective_risk"])
            ax_a.scatter([cx], [cy], s=80, color=col, marker=mk, zorder=6)
            ax_a.annotate(
                f"{lbl}\n({cx * 100:.0f}% cov, {cy * 100:.0f}% risk)",
                xy=(cx, cy),
                xytext=ofs,
                textcoords="offset points",
                fontsize=8.0,
                fontweight="bold",
                color=col,
                bbox={
                    "boxstyle": "round,pad=0.22",
                    "facecolor": "white",
                    "edgecolor": col,
                    "alpha": 0.94,
                },
            )
        ax_a.text(
            0.03,
            0.22,
            "Note: Offline Rule Baseline accepted\n0/80 free-form sentences (Risk = N/A)",
            fontsize=8.0,
            color=SLATE,
            bbox={
                "boxstyle": "round,pad=0.24",
                "facecolor": "#f7f7f7",
                "edgecolor": "#cccccc",
            },
        )
        ax_a.set_xlim(-0.04, 1.08)
        ax_a.set_ylim(-0.06, 0.85)
        ax_a.set_xlabel("Coverage — Accepted Share of 80 Utterances", fontsize=9.6)
        ax_a.set_ylabel("Selective Risk — Wrong Share Among Accepted (↓)", fontsize=9.6)
        ax_a.set_title(
            "(a) Risk–Coverage Trade-Off on 80 Bilingual Turns", fontsize=10.5, pad=12
        )
        ax_a.legend(loc="upper left", fontsize=8.0, framealpha=0.95)
        ax_a.grid(True, linestyle=":", alpha=0.5)

        labels_b = [
            "Naive\nKeyword",
            "TF-IDF+LR\n(Forced)",
            "TF-IDF+LR\n(τ = 0.60)",
            "Rule\nBaseline",
            "Connected\nChatbot",
        ]
        core_vals = [
            0.5469,
            0.3594,
            0.5938,
            0.5000,
            float(m80["live_dual_channel_chatbot"]["core_64_joint_accuracy"]),
        ]
        hard_vals = [
            0.5000,
            0.1250,
            0.4375,
            0.5000,
            float(m80["live_dual_channel_chatbot"]["hard_16_joint_accuracy"]),
        ]
        xb = np.arange(len(labels_b))
        wb = 0.35
        b1 = ax_b.bar(
            xb - wb / 2,
            core_vals,
            width=wb,
            color=STEEL,
            label="Standard Bilingual Set (N=64)",
        )
        b2 = ax_b.bar(
            xb + wb / 2,
            hard_vals,
            width=wb,
            color=ORANGE,
            label="HK Code-Switched & Stress Set (N=16)",
        )
        for bars in (b1, b2):
            for rect in bars:
                v = rect.get_height()
                ax_b.text(
                    rect.get_x() + rect.get_width() / 2.0,
                    v + 0.02,
                    f"{v * 100:.1f}%",
                    ha="center",
                    va="bottom",
                    fontsize=7.8,
                    fontweight="bold",
                )
        ax_b.set_xticks(xb)
        ax_b.set_xticklabels(labels_b, fontsize=9.2)
        ax_b.set_ylim(0.0, 1.18)
        ax_b.set_yticks([0.0, 0.25, 0.50, 0.75, 1.00])
        ax_b.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
        ax_b.set_ylabel("End-to-End Accuracy (Higher = Better ↑)", fontsize=9.6)
        ax_b.set_title(
            "(b) Standard Set vs. HK Code-Switched Stress Set", fontsize=10.5, pad=12
        )
        ax_b.legend(loc="upper left", fontsize=8.0, framealpha=0.95)
        ax_b.grid(True, axis="y", linestyle=":", alpha=0.5)

        fig.suptitle(
            "Experiment 2: Bilingual Symptom Extraction, Selective Abstention, and HK Stress-Test Results",
            fontsize=11.8,
            fontweight="bold",
            color=NAVY,
            y=0.95,
        )
        p3 = outdir / "fig3_clean_e2_extraction.png"
        fig.savefig(p3, dpi=300)
        plt.close(fig)

        p4 = _render_clean_fig4_walkthrough(outdir)
    return [p1, p2, p3, p4]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Render 5 publication-grade S1 Dual-Channel figures from summary.json."
    )
    parser.add_argument(
        "--summary",
        type=Path,
        default=Path("results/dual-channel-s1-20261127/summary.json"),
        help="Path to summary.json generated by run_experiments.py",
    )
    parser.add_argument(
        "--outdir",
        type=Path,
        default=Path("docs/semester1_final/figures"),
        help="Output directory for 300-DPI PNG figures",
    )
    args = parser.parse_args(argv)

    summary = json.loads(args.summary.read_text(encoding="utf-8"))
    written = generate_all_figures(summary, args.outdir)
    for path in written:
        print(f"[OK] Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
