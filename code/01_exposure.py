"""Private-well population near US municipal landfills, with aquifer and age context.

Inputs (data/):
  lmop_landfills.xlsx  EPA LMOP Landfill and Project Database, landfill-level data (Sept 2024)
  REM_map_2010.tif     USGS domestic-well population, 2010, road-enhanced method, 1 km grid
                       (Johnson and Belitz 2019, doi:10.5066/P9FSLU3B)
  aquifers/            USGS principal aquifers of the United States (us_aquifers.shp)
Run: .venv/bin/python -I code/01_exposure.py
"""
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import rasterio

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "data"
RADII_KM = [1, 2, 5]

lf = pd.read_excel(D / "lmop_landfills.xlsx", "LMOP Database")
n_all = len(lf)
lf = lf[lf.Latitude.notna() & lf.Longitude.notna() & ~lf.State.isin(["AK", "HI", "PR", "GU", "VI"])].copy()
n_conus = len(lf)
gdf = gpd.GeoDataFrame(lf, geometry=gpd.points_from_xy(lf.Longitude, lf.Latitude), crs="EPSG:4326")

ras = rasterio.open(D / "REM_map_2010.tif")
pop = ras.read(1).astype("float64")
pop[(pop < 0) | ~np.isfinite(pop)] = 0.0
gdf = gdf.to_crs(ras.crs)
inside = gdf.geometry.within(gpd.GeoSeries.from_xy([ras.bounds.left, ras.bounds.right, ras.bounds.right, ras.bounds.left],
                                                    [ras.bounds.bottom, ras.bounds.bottom, ras.bounds.top, ras.bounds.top], crs=ras.crs).union_all().envelope)
gdf = gdf[inside].copy()

# Sum population of 1 km cells whose centres lie within each radius of the landfill point
res = ras.res[0]
for rkm in RADII_KM:
    k = int(np.ceil(rkm * 1000 / res)) + 1
    vals = []
    for x, y in zip(gdf.geometry.x, gdf.geometry.y):
        row, col = ras.index(x, y)
        r0, r1, c0, c1 = max(row - k, 0), min(row + k + 1, pop.shape[0]), max(col - k, 0), min(col + k + 1, pop.shape[1])
        rr, cc = np.mgrid[r0:r1, c0:c1]
        cx, cy = rasterio.transform.xy(ras.transform, rr, cc)
        dist = np.hypot(np.asarray(cx).reshape(rr.shape) - x, np.asarray(cy).reshape(rr.shape) - y)
        vals.append(pop[r0:r1, c0:c1][dist <= rkm * 1000].sum())
    gdf[f"wellpop_{rkm}km"] = np.round(vals, 1)

# Principal aquifer at the landfill
aq = gpd.read_file(D / "aquifers/us_aquifers.shp").to_crs(ras.crs)[["ROCK_TYPE", "ROCK_NAME", "AQ_NAME", "geometry"]]
gdf = gpd.sjoin(gdf, aq, how="left", predicate="within").drop(columns="index_right")
gdf = gdf[~gdf.index.duplicated(keep="first")]
gdf["ROCK_NAME"] = gdf.ROCK_NAME.fillna("Outside principal aquifers")
gdf["AQ_NAME"] = gdf.AQ_NAME.fillna("None")

# Context flags (transparent, not weighted)
gdf["opened_pre1993"] = gdf["Year Landfill Opened"] < 1993     # before RCRA Subtitle D liner and monitoring rules took effect (Oct 1993)
gdf["permeable_aquifer"] = gdf.ROCK_TYPE.isin([100, 400])        # unconsolidated sand/gravel or carbonate rock
gdf["priority"] = gdf.opened_pre1993 & gdf.permeable_aquifer & (gdf.wellpop_2km >= 100)

keep = ["Landfill ID", "Landfill Name", "State", "County", "Latitude", "Longitude", "Current Landfill Status",
        "Year Landfill Opened", "Landfill Closure Year", "Waste in Place (tons)", "Does LF Recirculate Leachate?",
        "wellpop_1km", "wellpop_2km", "wellpop_5km", "ROCK_TYPE", "ROCK_NAME", "AQ_NAME",
        "opened_pre1993", "permeable_aquifer", "priority"]
out = pd.DataFrame(gdf[keep]).sort_values("wellpop_2km", ascending=False)
out.to_csv(D / "landfill_exposure.csv", index=False)
pd.Series({"landfills_in_database": n_all, "conus_with_coordinates": n_conus, "inside_raster": len(gdf),
           "domestic_well_population_conus_2010": round(pop.sum())}).to_csv(D / "provenance_counts.csv", header=["value"])
print(f"{n_all} landfills; {n_conus} CONUS with coordinates; {len(gdf)} analysed; raster total {pop.sum():,.0f}")
print(out[["wellpop_1km", "wellpop_2km", "wellpop_5km"]].describe().round(1))
