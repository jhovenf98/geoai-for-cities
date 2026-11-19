# Spatial methods, and where GeoAI would come in

I went back through my own app and data to check what it actually does with location. The honest answer is
spatial data science of a simple, rule-based kind. **There is no trained model or AI component yet.** Everything
below is built unless marked as a plan.

## Built: geometry on the phone

- **Distance and direction to a friend.** Great-circle (haversine) distance and compass bearing from my position
  to a friend's last shared spot. The phone's heading is subtracted so an arrow points at them. The app also warns
  when the spot is a few minutes old.
- **Places described in words.** A position becomes "at the north gate" or "300 ft NE of the info tent" by finding
  the nearest named place and its direction. People who are tired, stressed or reading a dim screen act on words
  faster than on coordinates.
- **Walk time.** Distance at a fixed crowd walking speed of about 1 m/s.
- **Time spent near places.** GPS fixes are cleaned first. The app drops fixes with poor accuracy, fixes far from
  the site and jumps too fast for walking, then counts time spent within a set distance of each place. This stays
  on the phone.
- **Site outlines.** Site boundaries come from OpenStreetMap as longitude–latitude rings, and the map is fitted to
  them.

## Built: a venue map audit

While building for the festival setting, I checked the official site maps for 97 large U.S. events
(snapshot 11 November 2026). Only totals are published here (`../data/venue_map_audit.json`).

| | Count |
|---|---|
| Events checked | 97 |
| Official map found (any edition) | 24 |
| Maps with geographic calibration established | 0 |
| Events that confirmed app or offline reuse | 0 |
| Candidate points of interest | 55 |
| With published coordinates | 2 |

Organizer maps are drawings, not GPS maps. The first spatial problem is therefore **georeferencing**: turning a
drawing of a site into coordinates, with a known error and with permission. Until that exists, every model below
rests on guessed positions.

## Not built: no prediction yet

The app does not predict crowd density, does not suggest meeting points and does not estimate where a lost person
has moved. The walking speed, distance thresholds and GPS cut-offs are values I set by hand. I have not measured or
fitted them.

## Plan: where GeoAI could come in

These are research directions, not results.

1. **A lost person's likely position.** Replace "last seen at X, N minutes ago" with a probability area. It would
   grow over time at a measured walking speed, stay inside the site boundary, and be pulled toward places where
   people are likely to go at that time. The test is calibration: does the true position fall inside the area as
   often as claimed?
2. **Crowd density over time.** Timetables and site layouts already say roughly where people will be. Opt-in,
   on-phone counts of time near places could be pooled to test and correct that. This needs privacy protection
   before any pooling, and I have not designed that yet.
3. **Meeting points.** Suggest a point that is equally reachable for the group, away from places about to fill up,
   and near a landmark that is easy to describe.
4. **Feeding the relay.** Message delivery depends on where carriers walk. The same crowd-movement estimates could
   replace random walking in the simulation (`SIMULATION.md`). They could also tell phones which messages are
   worth carrying toward which part of a site.

Each would have to beat the simple rule it replaces (last-seen point, timetable only, fixed meeting point) on
held-out sites or days. That is the same test I used in my Salton Sea dust work, where the model had to beat the
monthly average.
