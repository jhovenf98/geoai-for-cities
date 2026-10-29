"""Download EPA AirData daily PM10 files and summarize the monitors around the Salton Sea.

Rules (same as the published page):
- PM10 parameter 81102, rows with Pollutant Standard 'PM10 24-hour 2006'
- Imperial (06-025) and Riverside (06-065) counties, east of -116.45 and south of 33.95
- Rows with Event Type 'Excluded' are dropped, so days flagged as exceptional events (e.g. high wind)
  are KEPT: people still breathed that air, even if EPA sets the day aside for compliance.
- Several instruments (POCs) at one site: keep the highest daily mean.
- A day is over the standard when the daily mean is >= 155 ug/m3 (150 standard, rounded to nearest 10).

Outputs: data/processed/pm10_daily.csv and data/processed/pm10_summary.json
Usage:  python 02_pull_epa_pm10.py 2023 2024 2025
"""
import io, json, sys, zipfile
import pandas as pd
import requests
from _paths import OUT

BASE = "https://aqs.epa.gov/aqsweb/airdata/daily_81102_{year}.zip"
OVER = 155

def load_year(year):
    r = requests.get(BASE.format(year=year), timeout=300)
    r.raise_for_status()
    z = zipfile.ZipFile(io.BytesIO(r.content))
    return pd.read_csv(z.open(z.namelist()[0]), dtype={"State Code": str, "County Code": str, "Site Num": str})

def filter_rows(df):
    df = df[(df["State Code"].str.zfill(2) == "06") & (df["County Code"].str.zfill(3).isin(["025", "065"]))]
    df = df[df["Pollutant Standard"] == "PM10 24-hour 2006"]
    df = df[(df["Latitude"] <= 33.95) & (df["Longitude"] >= -116.45)]
    df = df[df["Event Type"] != "Excluded"]
    df = df.assign(site=df["County Code"].str.zfill(3) + "-" + df["Site Num"].str.zfill(4))
    g = (df.groupby(["site", "Date Local"])
           .agg(pm10=("Arithmetic Mean", "max"), name=("Local Site Name", "first"),
                lat=("Latitude", "first"), lon=("Longitude", "first"))
           .reset_index().rename(columns={"Date Local": "date"}))
    g["over"] = g["pm10"] >= OVER
    return g

def summarize(daily):
    daily = daily.assign(year=daily["date"].str[:4])
    mons = []
    for site, d in daily.groupby("site"):
        y = {yr: [int(len(x)), round(float(x["pm10"].mean())), int(x["over"].sum()), round(float(x["pm10"].max()))]
             for yr, x in d.groupby("year")}
        mons.append({"id": "06-" + site, "name": d["name"].iloc[0], "lat": round(float(d["lat"].iloc[0]), 3),
                     "lon": round(float(d["lon"].iloc[0]), 3), "y": y})
    by_month = daily[daily["over"]].assign(m=daily["date"].str[5:7].astype(int)).groupby("m").size()
    return {"fields": "[days with data, mean daily PM10, days >= 155, max daily]", "monitors": mons,
            "site_days_over_by_month": [int(by_month.get(m, 0)) for m in range(1, 13)],
            "dates_any_site_over": int(daily.loc[daily["over"], "date"].nunique())}

def main(years):
    daily = pd.concat([filter_rows(load_year(y)) for y in years], ignore_index=True)
    daily.to_csv(OUT / "pm10_daily.csv", index=False)
    s = summarize(daily)
    json.dump(s, open(OUT / "pm10_summary.json", "w"), indent=1)
    print(f"{daily['site'].nunique()} monitors, {len(daily)} site-days, {s['dates_any_site_over']} dates over")

if __name__ == "__main__":
    main([int(a) for a in sys.argv[1:]] or [2023, 2024, 2025])
