# Predictive models and how they are tested

The chain from water to dust to people is a set of predictions. Each model answers one link; together they run
the scenarios (no new lithium; Hell's Kitchen with and without Colorado River cuts; full build-out with and
without mitigation; two revenue splits).

| # | Model | Predicts | Method | Test | Main drawback |
|---|---|---|---|---|---|
| 1 | Shoreline | Sea level and exposed lakebed by year, to 2050 | Water balance + elevation-area curve (not ML) | Hindcast 2000–2025 against satellite shorelines | Future inflows are policy choices |
| 2 | Surface | Crust / loose / wet / vegetated, per 10 m pixel | Random forest baseline, then U-Net if clearly better | Spatial-block CV (whole shoreline stretches held out); accuracy per class | Few labels; new lakebed may look unlike training data |
| 3 | Dust days | Daily PM10 and chance of a day over the standard, 1–3 days ahead | Gradient-boosted trees with probability output | Time split (test 2024–2025) and leave-one-monitor-out; must beat persistence and monthly climatology | Monitors can't tell sources apart; bad days are rare |
| 4 | Exposure | Extra dust days per person by tract and town, per scenario | Population-weighted exposure; asthma ER visits vs. exposure, adjusted for poverty, age, access | Compare with monitors and resident reports; report ranges | Tract data gives associations, not causes |
| 5 | Ground | Early warning on subsidence or seismicity changes | Anomaly detection on Sentinel-1 time series; earthquake rate vs. fluid volume | Backtest on past years; false-alarm rate | Pumping data comes from operators; an alert says *what* changed, not *why* |

## Rules every model follows

1. **Beat a simple baseline** (last year's shoreline, yesterday's dust, the monthly average) or it is not used.
2. **Test on places or years held out completely.** Random splits flatter spatial models because neighbors look alike
   (the main lesson of Part 3 of this series).
3. **Report uncertainty** as ranges, including the spread across water assumptions.
4. **Publish the errors** by class, monitor and year, including where models do badly.

## Model 3 starter code

`code/05_dust_model_baseline.py` implements the first version: wind features from `04_pull_wind_asos.py`
(daily mean and max wind, gusts, hours ≥ 20 knots, share of windy hours from the west and south), season,
and yesterday's PM10. It reports Brier score, Brier skill against climatology, and ROC AUC for both tests.
First real run (October 2026, 2023–2025 data; train 2023, test 2024–25): Brier skill 0.19 against monthly climatology, AUC 0.86;
persistence did worse than climatology. Leaving one monitor out, it beat climatology at 7 of 8 monitors (worse at Calexico,
about equal at El Centro). `06_feature_check.py` shows the skill comes from wind: without wind inputs, skill is about 0.
It uses same-day observed wind, so it explains bad days rather than forecasting them. Numbers: `data/processed/dust_model_results_real.json`.

Planned improvements: forecast wind in place of observed wind; more training years; upwind fetch over loose lakebed from Model 2; soil moisture
and recent rain; separate models for spring wind events and late-summer storm outflows; calibration plots.

## Why a dust forecast matters outside research

A tested 1–3 day dust warning lets schools move recess indoors, clinics prepare, and the county time dust
control on the patches that matter. It has to prove itself on past seasons first.
