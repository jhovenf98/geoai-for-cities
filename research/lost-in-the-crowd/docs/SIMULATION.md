# The relay simulation

`code/relay_sim.py` is a small, deliberately simple simulation. I wrote it to test the evaluation pipeline in the
proposal (section 5) and to find out which assumptions change the answer before any field test. It does not stand
in for the full ONE simulator study planned in the proposal.

## Setup

| Thing | Value used | Where it comes from |
|---|---|---|
| Site | 900 × 600 m rectangle with 5 attractions | Made up; roughly a large park or fairground |
| Attraction popularity | 35%, 25%, 15%, 15%, 10% | Made up |
| Crowd spread around an attraction | 40 m (normal distribution) | Made up |
| Walking speed | 1 m/s | A common rough figure for walking in a crowd |
| Radio range | 30 m (sensitivity: 5–50 m) | Assumed; **the main unknown** |
| Time step | 20 s | Fine enough at 1 m/s |
| Length | 6 hours | |
| Groups | 10 groups of 4 | Made up |
| Messages | 5 per group, created at random in the first 4 hours | Made up |
| Expiry and hop limit | 4 hours, 8 hops | Example values for the simulation only |
| App users | 60, 120, 250, 500, 1,000 | What matters is how many people run the app, not the crowd size |
| Seeds | 3 per setting | |

**Movement models**

- *Random walking (random waypoint):* everyone walks to a random point, then picks another. This is the usual
  default in relay studies.
- *Walking between attractions on a timetable:* every hour each person picks an attraction, weighted by popularity,
  walks there and drifts a little. Start times are staggered. This stands in for stages, game times, parade routes
  or meal times.

**Forwarding schemes**

- *Copy to every app user (epidemic, with an expiry and hop limit):* the design under study.
- *Spray and Wait:* 8 copies are split in half at each meeting. After that, a phone holding a single copy hands it
  only to a recipient.
- *Own group only:* only the sender's group carries it. This is close to how Briar syncs between known contacts.

A message counts as delivered to a group member when that person first holds it.

## Results

Every setting is in `../data/sim_summary.md`. The short version is in the README.

## What it leaves out

- **Radio details:** interference, bodies blocking signal and discovery delays. Two phones in range for 20 s are
  assumed to swap everything.
- **Session limits and battery:** not modelled. Phones never sleep and the app is always open, which is the most
  optimistic case.
- **Storage limits:** not modelled. With only 50 messages they would never fill.
- **How real people behave:** group members here move independently. Real friends often move together, which would
  make own-group delivery look better than shown.
- **Entrances, exits, food and rest areas:** not modelled.

## What it is good for

It shows which inputs move the result. Those are what to measure first in the field: radio range in a crowd, and
how much people mix between attractions. It also gives the field study a baseline to beat.
