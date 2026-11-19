"""Toy simulation of an offline crowd relay (store-carry-forward).

What it asks: if only some people in a crowd run the app, how often does a
sealed group message reach its group, and how long does it take, under two
ways of moving around a site?

Everything here is synthetic. The venue, crowd, radio range and walking
behaviour are assumptions chosen to be plausible, not measurements. The point
is to check the evaluation pipeline and see which assumptions matter, before
any field data exists. See ../docs/SIMULATION.md.

Relay rules (example values for this simulation, not those of any shipped app):
  - messages expire EXPIRY_S after creation
  - at most MAX_HOPS hand-offs
  - storage limits are not modelled (they never bind with this few messages)

Schemes compared:
  epidemic      copy to every app user met (the design)
  spray         binary Spray and Wait with 8 copies, then direct delivery only
  friends_only  only members of the sender's own group carry the message

Mobility models:
  waypoint   random waypoint inside the venue at ~1 m/s
  schedule   every hour people walk to an attraction (a stage, a game, a
             parade route), chosen by popularity, and drift around it

Run:  python relay_sim.py            (about 2-4 minutes)
      python relay_sim.py --quick    (one seed, fewer sizes)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy.spatial import cKDTree

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "data"

# ---- assumptions (all synthetic) ----
VENUE_W, VENUE_H = 900.0, 600.0           # metres (a made-up site)
ATTRACTIONS = np.array([[120, 120], [780, 110], [450, 300], [140, 500], [760, 490]], float)
ATTRACTION_POP = np.array([0.35, 0.25, 0.15, 0.15, 0.10])  # share of the crowd at each attraction
ATTRACTION_SPREAD = 40.0                        # metres; how far a crowd spreads around an attraction
RANGE_M = 30.0                             # assumed phone-to-phone radio range in a crowd
WALK = 1.0                                 # m/s through a crowd
DT = 20.0                                  # seconds per step
HOURS = 6.0
SLOT_MIN = 60.0                            # minutes before people move on
SEND_WINDOW_H = 4.0                        # messages are created in the first 4 hours
EXPIRY_S = 4 * 3600                        # example value
MAX_HOPS = 8                               # example value
GROUPS, GROUP_SIZE = 10, 4
MESSAGES_PER_GROUP = 5
SPRAY_COPIES = 8


def make_mobility(kind: str, n: int, rng: np.random.Generator):
    """Return a function step(t) -> positions (n x 2)."""
    pos = np.column_stack([rng.uniform(0, VENUE_W, n), rng.uniform(0, VENUE_H, n)])
    target = pos.copy()
    slot_of = np.full(n, -1)
    # people arrive at different times; this offsets each person's slot clock
    offset = rng.uniform(0, SLOT_MIN * 60, n) if kind == "schedule" else None

    def new_waypoints(idx):
        target[idx, 0] = rng.uniform(0, VENUE_W, idx.size)
        target[idx, 1] = rng.uniform(0, VENUE_H, idx.size)

    def step(t: float):
        nonlocal pos
        if kind == "waypoint":
            arrived = np.linalg.norm(target - pos, axis=1) < 1.0
            new_waypoints(np.flatnonzero(arrived))
        else:
            slot = ((t + offset) // (SLOT_MIN * 60)).astype(int)
            changed = np.flatnonzero(slot != slot_of)
            if changed.size:
                slot_of[changed] = slot[changed]
                choice = rng.choice(len(ATTRACTIONS), size=changed.size, p=ATTRACTION_POP)
                target[changed] = ATTRACTIONS[choice] + rng.normal(0, ATTRACTION_SPREAD, (changed.size, 2))
            # small drift while watching
            near = np.linalg.norm(target - pos, axis=1) < 1.0
            k = np.flatnonzero(near & (rng.random(n) < 0.05))
            if k.size:
                target[k] += rng.normal(0, 8, (k.size, 2))
        np.clip(target[:, 0], 0, VENUE_W, out=target[:, 0])
        np.clip(target[:, 1], 0, VENUE_H, out=target[:, 1])
        d = target - pos
        dist = np.linalg.norm(d, axis=1)
        move = np.minimum(dist, WALK * DT)
        with np.errstate(invalid="ignore", divide="ignore"):
            pos = pos + np.where(dist[:, None] > 0, d / dist[:, None], 0) * move[:, None]
        return pos

    return step


def run(n_users: int, mobility: str, scheme: str, seed: int, range_m: float = RANGE_M) -> dict:
    rng = np.random.default_rng(seed)
    step = make_mobility(mobility, n_users, rng)
    n_members = GROUPS * GROUP_SIZE
    group = np.full(n_users, -1)
    group[:n_members] = np.repeat(np.arange(GROUPS), GROUP_SIZE)

    # messages: sender, group, creation time
    k = GROUPS * MESSAGES_PER_GROUP
    p_group = np.repeat(np.arange(GROUPS), MESSAGES_PER_GROUP)
    p_sender = p_group * GROUP_SIZE + rng.integers(0, GROUP_SIZE, k)
    p_born = rng.uniform(0, SEND_WINDOW_H * 3600, k)

    has = np.zeros((n_users, k), bool)
    hops = np.zeros((n_users, k), np.int16)
    copies = np.zeros((n_users, k), np.int16)
    got_at = np.full((n_users, k), np.nan)  # first time each holder received it
    dest = group[:, None] == p_group[None, :]
    dest[p_sender, np.arange(k)] = False     # sender is not a recipient

    may_carry = np.ones((n_users, k), bool)
    if scheme == "friends_only":
        may_carry = group[:, None] == p_group[None, :]

    steps = int(HOURS * 3600 / DT)
    for s in range(steps):
        t = s * DT
        pos = step(t)
        born_now = (p_born <= t) & ~has[p_sender, np.arange(k)]
        if born_now.any():
            j = np.flatnonzero(born_now)
            has[p_sender[j], j] = True
            got_at[p_sender[j], j] = t
            copies[p_sender[j], j] = SPRAY_COPIES
        alive = (t - p_born) < EXPIRY_S
        pairs = cKDTree(pos).query_pairs(range_m, output_type="ndarray")
        if not len(pairs):
            continue
        a, b = pairs[:, 0], pairs[:, 1]
        snap_has, snap_hops = has.copy(), hops.copy()
        for x, y in ((a, b), (b, a)):
            give = snap_has[x] & ~has[y] & alive[None, :] & (snap_hops[x] < MAX_HOPS)
            if scheme == "spray":
                # spray phase: split copies; wait phase (1 copy): only hand to a recipient
                spray = copies[x] > 1  # live counts, so a giver cannot spend copies twice in one step
                give &= spray | dest[y]
            give &= may_carry[y] | dest[y]
            if not give.any():
                continue
            rows, cols = np.nonzero(give)
            ry, rx = y[rows], x[rows]
            if scheme == "spray":
                # one hand-off per giver, message and step, so copies are not double-spent
                _, first = np.unique(np.column_stack([rx, cols]), axis=0, return_index=True)
                first = np.sort(first)
                ry, rx, cols = ry[first], rx[first], cols[first]
                give[:] = False
                ok = ~has[ry, cols]
                ry, rx, cols = ry[ok], rx[ok], cols[ok]
            has[ry, cols] = True
            hops[ry, cols] = snap_hops[rx, cols] + 1
            got_at[ry, cols] = np.where(np.isnan(got_at[ry, cols]), t, got_at[ry, cols])
            if scheme == "spray":
                cur = copies[rx, cols]
                half = cur // 2
                copies[ry, cols] = np.maximum(half, 1)
                copies[rx, cols] = cur - half
    # per (recipient, message)
    r, c = np.nonzero(dest)
    delivered = has[r, c]
    lat = (got_at[r, c] - p_born[c])[delivered] / 60
    carriers = has.sum(0)
    return {
        "n_users": n_users, "range_m": range_m, "mobility": mobility, "scheme": scheme, "seed": seed,
        "delivery_ratio": float(delivered.mean()),
        "median_latency_min": float(np.median(lat)) if lat.size else None,
        "p90_latency_min": float(np.percentile(lat, 90)) if lat.size else None,
        "mean_copies_per_message": float(carriers.mean()),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    args = ap.parse_args()
    sizes = [60, 200, 800] if args.quick else [60, 120, 250, 500, 1000]
    seeds = [1] if args.quick else [1, 2, 3]
    rows = []
    for mob in ("waypoint", "schedule"):
        for scheme in ("epidemic", "spray", "friends_only"):
            for n in sizes:
                for sd in seeds:
                    r = run(n, mob, scheme, sd)
                    rows.append(r)
                    print(f"{mob:9} {scheme:12} n={n:5} seed={sd}  delivered={r['delivery_ratio']:.2f}  "
                          f"median={r['median_latency_min']}  copies={r['mean_copies_per_message']:.0f}")
    # sensitivity: how much does the assumed radio range matter? (epidemic, schedule mobility, 120 users)
    sens = []
    for rm in (5, 10, 20, 30, 50):
        for sd in seeds:
            r = run(120, "schedule", "epidemic", sd, range_m=rm)
            sens.append(r)
            print(f"range={rm:3} m seed={sd}  delivered={r['delivery_ratio']:.2f}  median={r['median_latency_min']}")
    OUT.mkdir(exist_ok=True)
    meta = {"note": "Synthetic simulation. Not field data. Assumptions in relay_sim.py and docs/SIMULATION.md.",
            "venue_m": [VENUE_W, VENUE_H], "range_m": RANGE_M, "dt_s": DT, "hours": HOURS,
            "groups": GROUPS, "group_size": GROUP_SIZE, "messages": GROUPS * MESSAGES_PER_GROUP,
            "max_hops": MAX_HOPS, "expiry_h": EXPIRY_S / 3600, "spray_copies": SPRAY_COPIES}
    (OUT / "sim_results.json").write_text(json.dumps({"meta": meta, "runs": rows, "range_sensitivity": sens}, indent=1))
    print("wrote", OUT / "sim_results.json")


if __name__ == "__main__":
    main()
