"""Model 3, first version: predict whether a monitor will record a day above the PM10 standard.

Inputs:  data/processed/pm10_daily.csv (02_pull_epa_pm10.py) and data/processed/wind_daily.csv (04_pull_wind_asos.py)
Target:  over = daily mean PM10 >= 155 ug/m3
Models:  two baselines and one machine-learning model
  - climatology:  that monitor's rate of bad days in that month, from training years only
  - persistence:  bad day yesterday -> predict bad day today
  - gradient boosting (scikit-learn HistGradientBoostingClassifier) on wind, season and yesterday's PM10
Tests:   (1) time split: train before 2024, test 2024 onward
         (2) leave one monitor out: can it predict a place it has never seen?
Scores:  Brier score (lower is better), Brier skill vs climatology (above 0 = better than the baseline), ROC AUC.
The model is only worth using if it beats BOTH baselines on BOTH tests.

Run with --synthetic to test the pipeline on made-up data (no downloads needed). Synthetic results mean nothing.
"""
import sys, json
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import brier_score_loss, roc_auc_score
from _paths import OUT

STATION_FOR = {"025": "IPL", "065": "TRM"}          # Imperial monitors -> Imperial airport; Riverside -> Thermal
FEATS = ["wind_mean_kt", "wind_max_kt", "gust_max_kt", "hours_ge_20kt", "share_west", "share_south",
         "month_sin", "month_cos", "pm10_lag1", "over_lag1"]

def synthetic(seed=0):
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2023-01-01", "2025-12-31").strftime("%Y-%m-%d")
    sites = ["025-0005", "025-0007", "025-4003", "025-4004", "065-2005"]
    w = pd.DataFrame([(st, d) for st in ("IPL", "TRM") for d in dates], columns=["station", "date"])
    w["wind_mean_kt"] = rng.gamma(2, 3, len(w)); w["wind_max_kt"] = w["wind_mean_kt"] * rng.uniform(1.3, 2.5, len(w))
    w["gust_max_kt"] = w["wind_max_kt"] * 1.3; w["hours_ge_20kt"] = (w["wind_max_kt"] > 20) * rng.integers(0, 6, len(w))
    w["share_west"] = rng.uniform(0, 1, len(w)); w["share_south"] = 1 - w["share_west"]
    p = []
    for s in sites:
        ww = w[w["station"] == STATION_FOR[s[:3]]].reset_index(drop=True)
        pm = 30 + 30 * ww["hours_ge_20kt"] * ww["share_west"] + rng.gamma(2, 10, len(ww))
        p.append(pd.DataFrame({"site": s, "date": ww["date"], "pm10": pm}))
    p = pd.concat(p); p["over"] = p["pm10"] >= 155
    return p, w

def build(pm, wind):
    pm = pm.sort_values(["site", "date"]).copy()
    pm["station"] = pm["site"].str[:3].map(STATION_FOR)
    pm["pm10_lag1"] = pm.groupby("site")["pm10"].shift(1)
    pm["over_lag1"] = pm.groupby("site")["over"].shift(1).astype(float)
    m = pd.to_datetime(pm["date"]).dt.month
    pm["month"] = m; pm["month_sin"] = np.sin(2 * np.pi * m / 12); pm["month_cos"] = np.cos(2 * np.pi * m / 12)
    df = pm.merge(wind, on=["station", "date"], how="inner").dropna(subset=["pm10_lag1"])
    df["y"] = df["over"].astype(int)
    return df

def climatology(train, test):
    rate = train.groupby(["site", "month"])["y"].mean()
    overall = train.groupby("month")["y"].mean()
    return np.array([rate.get((s, mo), overall.get(mo, train["y"].mean())) for s, mo in zip(test["site"], test["month"])])

def score(y, p, ref):
    b, bref = brier_score_loss(y, p), brier_score_loss(y, ref)
    auc = roc_auc_score(y, p) if 0 < y.sum() < len(y) else float("nan")
    return {"brier": round(b, 4), "skill_vs_climatology": round(1 - b / bref, 3), "auc": round(auc, 3)}

def evaluate(train, test):
    clim = climatology(train, test)
    pers = np.clip(test["over_lag1"].fillna(0).values, 0.02, 0.98)
    gb = HistGradientBoostingClassifier(max_depth=3, learning_rate=0.05, max_iter=300, random_state=0)
    gb.fit(train[FEATS], train["y"])
    pg = gb.predict_proba(test[FEATS])[:, 1]
    y = test["y"].values
    return {"n_test_days": int(len(y)), "bad_days_in_test": int(y.sum()),
            "climatology": score(y, clim, clim), "persistence": score(y, pers, clim), "boosting": score(y, pg, clim)}

def main():
    if "--synthetic" in sys.argv:
        pm, wind = synthetic(); tag = "synthetic"
    else:
        pm = pd.read_csv(OUT / "pm10_daily.csv", dtype={"site": str}); wind = pd.read_csv(OUT / "wind_daily.csv"); tag = "real"
    df = build(pm, wind)
    res = {"data": tag, "time_split": evaluate(df[df["date"] < "2024-01-01"], df[df["date"] >= "2024-01-01"]), "leave_one_monitor_out": {}}
    for s in sorted(df["site"].unique()):
        res["leave_one_monitor_out"][s] = evaluate(df[df["site"] != s], df[df["site"] == s])
    out = OUT / f"dust_model_results_{tag}.json"
    json.dump(res, open(out, "w"), indent=1)
    print(json.dumps(res["time_split"], indent=1)); print(f"-> {out}")

if __name__ == "__main__":
    main()
