# Drone operations plan

Drones cannot extract lithium: the brine comes from deep wells through closed pipes. Drones are the
independent monitoring layer on the surface.

## Missions

| Mission | Sensor | Output | Feeds |
|---|---|---|---|
| Shoreline and lakebed plots, each season | RGB (and multispectral if available) | Orthomosaics, surface-type labels | Model 2 training labels |
| Thermal surveys of ponds, pipelines, mudpots | Thermal camera | Surface temperature maps, leak flags | Monitoring |
| Downwind gas and particle sampling | Small PM and H2S sensors | Readings with GPS and height | Model 3 checks |
| Waste piles and well pads | RGB, photogrammetry | 3D models, volume change | Monitoring |
| Dust-control checks (Owens Lake style) | PM sensor, low flight | Whether treated ground still gives off dust | Solution checks |

Published tests of each sensor type elsewhere (camera, multispectral, particle, thermal, gas, LiDAR, water sampling) are listed in Table 2 of the proposal page, with sources. No hydrogen sulfide drone test was found; small drones cannot fly in the strongest dust winds.

Equipment: DJI Enterprise drones; processing in Drone2Map and Pix4D; ground control with GNSS; field forms in Esri Field Maps.

## Rules and permissions checklist

- [ ] FAA Part 107 certificate current; aircraft registered; Remote ID compliant
- [ ] Below 400 ft, visual line of sight, daylight rules
- [ ] Airspace checked (LAANC where needed); note Naval and airport airspace in the valley
- [ ] **No launching or landing on national wildlife refuges, including Sonny Bono Salton Sea NWR** (50 CFR 27.34); do not disturb birds
- [ ] Written permission from landowners and plant operators for each site
- [ ] Tribal consent before any flight near the Southeast Lake Cahuilla Active Volcanic Cultural District
- [ ] Wind limits for the aircraft: the dustiest days are often unflyable, so plan ground sensors for those
- [ ] QA/QC: ground control points, check points, accuracy report per flight

## Known drawbacks

Drones cover only a few plots per day, are grounded in high wind (exactly when dust is worst), and need many
permissions. Their value is detailed labels and independent checks, not wall-to-wall coverage.
