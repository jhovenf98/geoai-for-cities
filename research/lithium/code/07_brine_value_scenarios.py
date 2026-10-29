"""What could the lithium in Salton Sea geothermal brine be worth, and who would get it?

A scenario calculator, NOT a forecast. No Salton Sea project has published audited production costs,
and none is producing commercially (CalMatters, Sept 2026). Every input is a cited figure or a labeled assumption.

Inputs
  LITHIUM_IN_BRINE  127,000 t LCE/yr in brine already pumped by existing plants (LBNL 2023, Dobson et al., p. ii)
  SUSTAINABLE       115,000 t LCE/yr from current wells, sustainable >= 36 years (LBNL 2023, p. 18)
  recovery          share of lithium actually captured: 50 / 75 / 90 %  (assumption; CTR reports 95-97% at pilot scale)
  price             $10,000 / $15,000 / $22,400 per t LCE  (assumption range; $22,400 = Fastmarkets long-term curve used
                    in the Smackover Lithium DFS, Sept 2025; China futures were ~CNY 96,100/t on 29 Oct 2026, Trading Economics)
  cost              $6,000 / $9,000 / $12,000 per t LCE all-in operating cost (assumption; low end ~ Smackover DFS
                    all-in OPEX $5,924/t, a different brine; capital costs are NOT included)
  tax               California lithium excise tax: $400/t up to 20,000 t, $600 to 30,000 t, $800 above
                    (Rev. & Tax. Code 47010). Tiers applied per producer per year, with production split evenly
                    across three producers (assumption). 80% to Imperial County, of which >= 30% to affected
                    communities; 20% to the Salton Sea Restoration Fund (Rev. & Tax. Code 47100).
"""
import json, itertools
from _paths import OUT

LITHIUM_IN_BRINE = 127_000
SUSTAINABLE = 115_000
RECOVERY = {"low": 0.50, "mid": 0.75, "high": 0.90}
PRICE = {"low": 10_000, "mid": 15_000, "high": 22_400}
COST = {"low": 6_000, "mid": 9_000, "high": 12_000}
PRODUCERS = 3


def excise(tonnes):
    t1 = min(tonnes, 20_000); t2 = min(max(tonnes - 20_000, 0), 10_000); t3 = max(tonnes - 30_000, 0)
    return 400 * t1 + 600 * t2 + 800 * t3


def scenario(rec, price, cost):
    t = min(LITHIUM_IN_BRINE * rec, SUSTAINABLE)
    revenue = t * price
    op_cost = t * cost
    tax = PRODUCERS * excise(t / PRODUCERS)
    margin = revenue - op_cost - tax
    return {"tonnes_lce": round(t), "revenue_musd": round(revenue / 1e6), "operating_cost_musd": round(op_cost / 1e6),
            "excise_tax_musd": round(tax / 1e6, 1), "operating_margin_musd": round(margin / 1e6),
            "tax_share_of_revenue_pct": round(100 * tax / revenue, 1),
            "county_musd": round(0.8 * tax / 1e6, 1), "affected_communities_min_musd": round(0.24 * tax / 1e6, 1),
            "salton_sea_fund_musd": round(0.2 * tax / 1e6, 1)}


def main():
    grid = {f"rec_{r}|price_{p}|cost_{c}": scenario(RECOVERY[r], PRICE[p], COST[c])
            for r, p, c in itertools.product(RECOVERY, PRICE, COST)}
    headline = {k: grid[f"rec_{k}|price_{k}|cost_{'high' if k == 'low' else 'low' if k == 'high' else 'mid'}"]
                for k in ("low", "mid", "high")}   # pessimistic / middle / optimistic
    res = {"note": "Scenario calculator, not a forecast. Operating margin excludes capital costs, financing and income tax.",
           "inputs": {"lithium_in_brine_t_lce": LITHIUM_IN_BRINE, "sustainable_t_lce": SUSTAINABLE, "recovery": RECOVERY,
                      "price_usd_per_t": PRICE, "cost_usd_per_t": COST, "producers": PRODUCERS},
           "headline": {"pessimistic": headline["low"], "middle": headline["mid"], "optimistic": headline["high"]},
           "grid": grid}
    json.dump(res, open(OUT / "brine_value_scenarios.json", "w"), indent=1)
    for k, v in res["headline"].items():
        print(k, v)


if __name__ == "__main__":
    main()
