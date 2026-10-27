"""Checks on the Model 3 time-split result: which inputs matter, and does wind carry the skill?

Runs after 02, 04 and 05 (same inputs as 05). Reports:
  - permutation importance on the 2024-25 test set (rise in Brier score x 1e4 when one input is shuffled)
  - skill of the same model with all wind inputs removed (season + yesterday's PM10 only)
  - how common windy and westerly days are on bad days vs all days
"""
import json
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.inspection import permutation_importance
from sklearn.metrics import brier_score_loss
from _paths import OUT
import importlib
m5 = importlib.import_module("05_dust_model_baseline")

WIND = ["wind_mean_kt", "wind_max_kt", "gust_max_kt", "hours_ge_20kt", "share_west", "share_south"]


def fit(train, feats):
    gb = HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=300, random_state=0)
    return gb.fit(train[feats], train["y"])


def main():
    pm = pd.read_csv(OUT / "pm10_daily.csv", dtype={"site": str})
    wind = pd.read_csv(OUT / "wind_daily.csv")
    df = m5.build(pm, wind)
    train, test = df[df["date"] < "2024-01-01"], df[df["date"] >= "2024-01-01"]
    clim = m5.climatology(train, test)
    bref = brier_score_loss(test["y"], clim)

    gb = fit(train, m5.FEATS)
    pi = permutation_importance(gb, test[m5.FEATS], test["y"], scoring="neg_brier_score",
                                n_repeats=20, random_state=0)
    imp = {f: round(float(v) * 1e4, 2) for f, v in sorted(zip(m5.FEATS, pi.importances_mean), key=lambda t: -t[1])}

    nowind = [f for f in m5.FEATS if f not in WIND]
    p = fit(train, nowind).predict_proba(test[nowind])[:, 1]
    bad = df[df["y"] == 1]
    res = {
        "n_rows": int(len(df)), "train_rows": int(len(train)), "train_bad": int(train["y"].sum()),
        "test_base_rate": round(float(test["y"].mean()), 4),
        "permutation_importance_brier_x1e4": imp,
        "no_wind_model_skill_vs_climatology": round(1 - brier_score_loss(test["y"], p) / bref, 3),
        "share_with_20kt_hour": {"bad_days": round(float((bad["hours_ge_20kt"] > 0).mean()), 3),
                                 "all_days": round(float((df["hours_ge_20kt"] > 0).mean()), 3)},
        "mean_share_west": {"bad_days": round(float(bad["share_west"].mean()), 3),
                            "all_days": round(float(df["share_west"].mean()), 3)},
    }
    json.dump(res, open(OUT / "dust_model_feature_check_real.json", "w"), indent=1)
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
