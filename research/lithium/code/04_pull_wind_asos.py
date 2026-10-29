"""Pull hourly wind from airport weather stations and turn it into daily features for the dust model.

Stations (FAA IDs): IPL = Imperial County Airport, TRM = Jacqueline Cochran Regional Airport (Thermal).
Source: Iowa Environmental Mesonet ASOS archive (free, no key).
Output: data/processed/wind_daily.csv  (station, date, wind_mean_kt, wind_max_kt, gust_max_kt,
        hours_ge_20kt, share_west, share_south)
Usage:  python 04_pull_wind_asos.py 2023-01-01 2026-01-01

NOTE: written for this project but not yet run (the author's workspace could not reach this server).
Check the first rows of the output by hand before using it.
"""
import io, sys
import numpy as np
import pandas as pd
import requests
from _paths import OUT

URL = "https://mesonet.agron.iastate.edu/cgi-bin/request/asos.py"

def pull(start, end, stations=("IPL", "TRM")):
    s, e = pd.Timestamp(start), pd.Timestamp(end)
    params = [("station", st) for st in stations] + [("data", "sknt"), ("data", "drct"), ("data", "gust"),
              ("year1", s.year), ("month1", s.month), ("day1", s.day), ("year2", e.year), ("month2", e.month),
              ("day2", e.day), ("tz", "America/Los_Angeles"), ("format", "onlycomma"), ("latlon", "no"),
              ("missing", "M"), ("trace", "T"), ("direct", "no"), ("report_type", "3")]
    r = requests.get(URL, params=params, timeout=300)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text), na_values=["M"])
    df["valid"] = pd.to_datetime(df["valid"])
    return df

def daily_features(df):
    df = df.assign(date=df["valid"].dt.strftime("%Y-%m-%d"), hour=df["valid"].dt.floor("h"))
    hourly = df.groupby(["station", "hour"]).agg(sknt=("sknt", "max"), drct=("drct", "median"),
                                                 gust=("gust", "max"), date=("date", "first")).reset_index()
    windy = hourly["sknt"] >= 10
    hourly["west"] = windy & hourly["drct"].between(225, 315)    # SW-W-NW: from the sea toward Imperial towns
    hourly["south"] = windy & hourly["drct"].between(135, 225)
    out = hourly.groupby(["station", "date"]).agg(
        wind_mean_kt=("sknt", "mean"), wind_max_kt=("sknt", "max"), gust_max_kt=("gust", "max"),
        hours_ge_20kt=("sknt", lambda s: int((s >= 20).sum())),
        share_west=("west", "mean"), share_south=("south", "mean")).reset_index()
    out["gust_max_kt"] = out["gust_max_kt"].fillna(out["wind_max_kt"])
    return out

if __name__ == "__main__":
    a = sys.argv[1:] or ["2023-01-01", "2026-01-01"]
    w = daily_features(pull(a[0], a[1]))
    w.to_csv(OUT / "wind_daily.csv", index=False)
    print(f"{len(w)} station-days -> {OUT / 'wind_daily.csv'}")
