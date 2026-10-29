# Data sources and provenance

All data used so far is public. Snapshot dates are when the data was pulled for the published page.

## Used now

### CalEnviroScreen 4.0 (OEHHA, released October 2021)
- Service: https://services1.arcgis.com/PCHfdHz4GlDNAhBb/arcgis/rest/services/CalEnviroScreen_4_0_Results_/FeatureServer/0
- Pulled: 2026-10-21, 79 tracts intersecting lon −116.35 to −115.25, lat 32.62 to 33.72
- Geometry simplified on the server (`maxAllowableOffset=0.007`, `geometryPrecision=3`), so tract edges are approximate.
- Fields kept: `tract`, `ACS2019TotalPop`, `asthma` (age-adjusted ER visits per 10,000), `asthmaP` (statewide percentile),
  `pm` (annual mean PM2.5, µg/m³), `pmP`, `pov` (% below twice the federal poverty line), `povP`, `CIscoreP` (overall percentile).
- Missing values: tract 6025010101 has no poverty value and therefore no overall score; shown as gray.
- Indicator years are roughly 2015–2019 (asthma 2015–2017; poverty ACS 2015–2019).
- How it was pulled: in a browser, with the query in `code/01_pull_calenviroscreen.py`. Each tract was written as one
  compact line (`data/raw/ces_tracts_salton.txt`, format in `code/00_decode_browser_pull.py`) so it could be copied out.

### EPA AirData daily PM10 (parameter 81102)
- Files: https://aqs.epa.gov/aqsweb/airdata/daily_81102_2023.zip, `_2024.zip`, `_2025.zip`
- Pulled: 2026-10-21. 2025 data runs to December 31 at all sites except Indio 0500 (Dec 22).
- Rules in `code/02_pull_epa_pm10.py`. Summary in `data/raw/pm10_monitors_2023_2025.json`:
  for each monitor and year, `[days with data, mean daily PM10, days ≥ 155 µg/m³, highest day]`.
- Site notes: AQS site 06-065-0500 is listed by EPA as "29 Palms" with city Indio; it has partial data in 2024 (24 days)
  and 2025. Indio Amistad High School (06-065-2007) starts in 2024.
- Check: per-monitor totals (162 site-days over the standard) equal the monthly totals.

### Natural Earth
- Salton Sea: 1:10m lakes (`data/raw/salton_sea_ne10m.geojson`). Older, larger shoreline than today.
- State outlines: 1:110m admin-1 (`data/raw/states_ne110m.geojson`), for the locator inset only.

## Planned

| Data | Source | Used for |
|---|---|---|
| Landsat 5–9, 30 m, since 1984 | USGS / NASA | Shoreline history, surface classes |
| Sentinel-2, 10 m, since 2015 | ESA Copernicus | Surface classes |
| Sentinel-1 radar | ESA Copernicus | Surface moisture and roughness, ground motion |
| Salton Sea water levels, elevation-area curve | USGS and state agencies | Shoreline model |
| Hourly wind, airports IPL and TRM | NOAA ASOS via Iowa Environmental Mesonet | Dust-day model |
| CIMIS weather stations | California Dept. of Water Resources | Dust-day model |
| Community air sensors | Comité Cívico del Valle (IVAN), PurpleAir | Gaps between monitors (access to confirm) |
| Earthquake catalog | USGS / Southern California Seismic Network | Ground and seismicity model |
| Project filings, environmental reviews | Imperial County, state agencies | Scenarios, CAD to GIS |
| Drone orthomosaics | Own flights (see DRONE_OPS.md) | Training labels |
