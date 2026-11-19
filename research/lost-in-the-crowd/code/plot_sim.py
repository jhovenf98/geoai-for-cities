"""Summarise and plot data/sim_results.json (synthetic)."""
import json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
d = json.loads((ROOT / "data/sim_results.json").read_text())
runs = d["runs"]
schemes = [("epidemic", "Copy to every app user", "#2a6f97"),
           ("spray", "Spray and Wait (8 copies)", "#e07a1f"),
           ("friends_only", "Own group only", "#8a8a8a")]
fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)
summary = []
for ax, mob, title in zip(axes, ("waypoint", "schedule"), ("Random walking", "Walking between attractions on a timetable")):
    for key, label, col in schemes:
        rs = [r for r in runs if r["mobility"] == mob and r["scheme"] == key]
        ns = sorted({r["n_users"] for r in rs})
        med = [np.median([r["median_latency_min"] for r in rs if r["n_users"] == n]) for n in ns]
        dr = [np.mean([r["delivery_ratio"] for r in rs if r["n_users"] == n]) for n in ns]
        cp = [np.mean([r["mean_copies_per_message"] for r in rs if r["n_users"] == n]) for n in ns]
        ax.plot(ns, med, "o-", color=col, label=label)
        for n, m, x, c in zip(ns, med, dr, cp):
            summary.append((mob, key, n, x, m, c))
    ax.set_xscale("log"); ax.set_title(title, fontsize=11)
    ax.set_xlabel("App users on site"); ax.grid(alpha=.3)
axes[0].set_ylabel("Median minutes to reach a group member")
axes[0].legend(fontsize=8, frameon=False)
fig.suptitle("Synthetic simulation, not field data", fontsize=10, color="#a33")
fig.tight_layout()
(ROOT / "media").mkdir(exist_ok=True)
fig.savefig(ROOT / "media/sim_latency.png", dpi=150)

lines = ["| Mobility | Scheme | App users | Delivered | Median min | Phones holding each message |", "|---|---|---|---|---|---|"]
for mob, key, n, x, m, c in summary:
    lines.append(f"| {mob} | {key} | {n} | {x:.0%} | {m:.0f} | {c:.0f} |")
sens = d["range_sensitivity"]
lines += ["", "| Radio range (m) | Delivered | Median min |", "|---|---|---|"]
for rm in sorted({r["range_m"] for r in sens}):
    rs = [r for r in sens if r["range_m"] == rm]
    lines.append(f"| {rm} | {np.mean([r['delivery_ratio'] for r in rs]):.0%} | {np.median([r['median_latency_min'] for r in rs]):.0f} |")
(ROOT / "data/sim_summary.md").write_text("\n".join(lines) + "\n")
print("\n".join(lines))
