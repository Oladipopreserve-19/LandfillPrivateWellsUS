"""Figures and tables for Preprint 6. Run: .venv/bin/python -I code/03_figures.py"""
from pathlib import Path
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import rasterio

ROOT = Path(__file__).resolve().parents[1]
D, F = ROOT / "data", ROOT / "figures"
plt.rcParams.update({"font.size": 9, "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 300})
e = pd.read_csv(D / "landfill_exposure.csv")
ras = rasterio.open(D / "REM_map_2010.tif")
g = gpd.GeoDataFrame(e, geometry=gpd.points_from_xy(e.Longitude, e.Latitude), crs="EPSG:4326").to_crs(ras.crs)
aq = gpd.read_file(D / "aquifers/us_aquifers.shp").to_crs(ras.crs)
outline = aq.dissolve().boundary

# Fig 1: well-population raster with landfills sized and coloured by users within 2 km
pop = ras.read(1).astype(float); pop[(pop <= 0) | ~np.isfinite(pop)] = np.nan
ext = [ras.bounds.left, ras.bounds.right, ras.bounds.bottom, ras.bounds.top]
fig, ax = plt.subplots(figsize=(7.5, 4.6))
ax.imshow(np.log10(pop), extent=ext, cmap="Greys", vmin=-1, vmax=3, alpha=0.55, interpolation="nearest")
s = g.sort_values("wellpop_2km")
sc = ax.scatter(s.geometry.x, s.geometry.y, c=s.wellpop_2km, s=4 + s.wellpop_2km / 40, cmap="viridis", vmin=0, vmax=800, edgecolor="none")
cb = fig.colorbar(sc, ax=ax, shrink=0.7); cb.set_label("Private-well users within 2 km")
ax.set_axis_off(); ax.set_title("US municipal landfills and private-well population (2010)", fontsize=9)
fig.tight_layout(); fig.savefig(F / "fig1_map.png"); plt.close(fig)

# Fig 2: distribution (CDF) at three radii
fig, ax = plt.subplots(figsize=(4.5, 3.2))
for r, c in [(1, "#E69F00"), (2, "#0072B2"), (5, "#009E73")]:
    v = np.sort(e[f"wellpop_{r}km"].values); ax.plot(v + 1, np.linspace(0, 1, len(v)), color=c, label=f"within {r} km")
ax.set(xscale="log", xlabel="Private-well users + 1 (log scale)", ylabel="Fraction of landfills"); ax.legend(frameon=False)
fig.tight_layout(); fig.savefig(F / "fig2_cdf.png"); plt.close(fig)

# Fig 3: by status and age
e["age_class"] = np.where(e["Year Landfill Opened"].isna(), "Unknown", np.where(e["Year Landfill Opened"] < 1993, "Before 1993", "1993 or later"))
fig, axes = plt.subplots(1, 2, figsize=(6.5, 3), sharey=True)
for ax, col, order in [(axes[0], "Current Landfill Status", ["Open", "Closed"]), (axes[1], "age_class", ["Before 1993", "1993 or later"])]:
    data = [e.loc[e[col] == k, "wellpop_2km"].values + 1 for k in order]
    ax.boxplot(data, showfliers=False); ax.set_xticks([1, 2], [f"{k}\n(n={len(d)})" for k, d in zip(order, data)])
    ax.set_yscale("log")
axes[0].set_ylabel("Private-well users within 2 km + 1"); axes[0].set_title("Status", fontsize=9); axes[1].set_title("Year opened", fontsize=9)
fig.tight_layout(); fig.savefig(F / "fig3_status_age.png"); plt.close(fig)

# Fig 4: by aquifer type
by = e.groupby("ROCK_NAME").agg(n=("wellpop_2km", "size"), med=("wellpop_2km", "median"), tot=("wellpop_2km", "sum")).sort_values("tot")
fig, ax = plt.subplots(figsize=(5.5, 3.2))
ax.barh([f"{k} (n={n})" for k, n in zip(by.index, by.n)], by.tot / 1000, color="#0072B2")
ax.set_xlabel("Private-well users within 2 km, summed over landfills (thousands)")
fig.tight_layout(); fig.savefig(F / "fig4_aquifer.png"); plt.close(fig)

# Fig 5: priority landfills map
p = g[g.priority]
fig, ax = plt.subplots(figsize=(7.5, 4.6))
outline.plot(ax=ax, color="#bbbbbb", lw=0.3)
aq[aq.ROCK_TYPE.isin([100, 400])].plot(ax=ax, color="#cfe3f3", edgecolor="none")
g[~g.priority].plot(ax=ax, color="#999999", markersize=1.5)
p.plot(ax=ax, color="#D55E00", markersize=6 + p.wellpop_2km / 60)
ax.set_xlim(ext[0], ext[1]); ax.set_ylim(ext[2], ext[3])
ax.set_axis_off(); ax.set_title(f"{len(p)} priority landfills: opened before 1993, over sand-and-gravel or carbonate aquifers,\n"
                                "and at least 100 private-well users within 2 km (blue: those aquifer types)", fontsize=8)
fig.tight_layout(); fig.savefig(F / "fig5_priority.png"); plt.close(fig)

# Tables for the draft
tot = pd.read_csv(D / "summary_totals.csv"); top = pd.read_csv(D / "top20_landfills.csv")
st = pd.read_csv(D / "summary_by_state.csv").head(10)
(ROOT / "draft").mkdir(exist_ok=True)
(ROOT / "draft/tables.md").write_text("Totals\n\n" + tot.to_markdown(index=False) + "\n\nTop 20\n\n" + top.to_markdown(index=False)
                                      + "\n\nStates\n\n" + st.to_markdown(index=False) + "\n")
print("figures done")
