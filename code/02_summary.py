"""Summary statistics: national totals without double counting, and breakdowns by status,
aquifer type, age and state. Run: .venv/bin/python -I code/02_summary.py"""
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio
from rasterio.features import geometry_mask

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data"
e = pd.read_csv(D / "landfill_exposure.csv")
ras = rasterio.open(D / "REM_map_2010.tif")
pop = ras.read(1).astype("float64"); pop[(pop < 0) | ~np.isfinite(pop)] = 0

g = gpd.GeoDataFrame(e, geometry=gpd.points_from_xy(e.Longitude, e.Latitude), crs="EPSG:4326").to_crs(ras.crs)
rows = []
for rkm in [1, 2, 5]:
    union = g.buffer(rkm * 1000).union_all()
    m = geometry_mask([union], out_shape=pop.shape, transform=ras.transform, invert=True)   # cell centres inside union
    rows.append(dict(radius_km=rkm, unique_population=round(pop[m].sum()), summed_population=round(e[f"wellpop_{rkm}km"].sum()),
                     landfills_with_any=int((e[f"wellpop_{rkm}km"] >= 1).sum()),
                     landfills_100plus=int((e[f"wellpop_{rkm}km"] >= 100).sum()),
                     landfills_1000plus=int((e[f"wellpop_{rkm}km"] >= 1000).sum())))
tot = pd.DataFrame(rows); tot.to_csv(D / "summary_totals.csv", index=False)

def grp(col):
    return e.groupby(col).agg(landfills=("Landfill ID", "size"), median_2km=("wellpop_2km", "median"),
                              mean_2km=("wellpop_2km", "mean"), total_2km=("wellpop_2km", "sum")).round(1).sort_values("landfills", ascending=False)

e["age_class"] = np.where(e["Year Landfill Opened"].isna(), "Unknown",
                          np.where(e["Year Landfill Opened"] < 1993, "Opened before 1993", "Opened 1993 or later"))
by_status, by_aq, by_age = grp("Current Landfill Status"), grp("ROCK_NAME"), grp("age_class")
by_state = grp("State").sort_values("total_2km", ascending=False)
for n, t in [("status", by_status), ("aquifer", by_aq), ("age", by_age), ("state", by_state)]:
    t.to_csv(D / f"summary_by_{n}.csv")

pri = e[e.priority]
pri.to_csv(D / "priority_landfills.csv", index=False)
top = e.head(20)[["Landfill Name", "State", "Current Landfill Status", "Year Landfill Opened", "ROCK_NAME", "wellpop_1km", "wellpop_2km", "wellpop_5km"]]
top.to_csv(D / "top20_landfills.csv", index=False)

# Rank stability: does the top-100 list depend on the radius?
t2, t5 = set(e.nlargest(100, "wellpop_2km")["Landfill ID"]), set(e.nlargest(100, "wellpop_5km")["Landfill ID"])
t1 = set(e.nlargest(100, "wellpop_1km")["Landfill ID"])
spear = e[["wellpop_1km", "wellpop_2km", "wellpop_5km"]].corr(method="spearman").round(3)
spear.to_csv(D / "rank_correlation.csv")

pd.set_option("display.width", 180)
print(tot.to_string(index=False))
print("\nBy status\n", by_status, "\nBy aquifer\n", by_aq, "\nBy age\n", by_age, "\nTop states\n", by_state.head(10))
print(f"\nPriority landfills (pre-1993, sand/gravel or carbonate aquifer, >=100 well users within 2 km): {len(pri)}; "
      f"well users within 2 km of them (summed): {pri.wellpop_2km.sum():,.0f}; states: {pri.State.nunique()}")
print("Top-100 overlap 2 km vs 5 km:", len(t2 & t5), " 1 km vs 2 km:", len(t1 & t2)); print(spear)
print("\nTop 20\n", top.to_string(index=False))
