"""S107 §1 — figura del blindaje D12: campo B21 MIR de MIROVA (Láscar, noche
2026-05-13 07:35 UTC) con el cluster al cráter vs el píxel suelto del Salar."""
import json, math, os
import numpy as np
import rasterio
from rasterio.warp import transform as rio_transform
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Circle

ARCH = r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/mirova-tif-archive"
REPO = r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
TIF = os.path.join(ARCH, "data/tif/Lascar/20260513_073500_MODIS.tif")
CRATER = (-23.36293, -67.731416)
OUT = os.path.join(REPO, "experiments/_s107_tif_verify/lascar_d12_blindaje.png")

with rasterio.open(TIF) as ds:
    a = ds.read(1).astype(float)
    b = ds.bounds
    extent = [b.left, b.right, b.bottom, b.top]

# record nuestro de esa noche
recs = [r for r in json.load(open(os.path.join(REPO, "data/mirova_equivalent/Lascar.json")))["records"]
        if str(r.get("sensor","")).startswith("MODIS") and r.get("datetime_utc","") == "2026-05-13 07:35"]
rec = recs[0] if recs else {}
pc = rec.get("primary_cluster") or {}
cl = (pc.get("centroid_lat"), pc.get("centroid_lon"))
loose = (rec.get("hotspot_lat") or rec.get("final_hotspot_lat"),
         rec.get("hotspot_lon") or rec.get("final_hotspot_lon"))

fig, ax = plt.subplots(figsize=(8.2, 7.6))
im = ax.imshow(a, extent=extent, origin="upper", cmap="inferno", aspect="auto")
cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
cb.set_label("Campo B21 (3.9 µm MIR) MIROVA — normalizado", fontsize=9)

# inner radius 5 km (aprox en grados)
dlat = 5/111.0; dlon = 5/(111.0*math.cos(math.radians(CRATER[0])))
ax.add_patch(Circle((CRATER[1], CRATER[0]), radius=(dlat+dlon)/2, fill=False,
                    edgecolor="cyan", ls="--", lw=1.4, label="inner_radius 5 km"))

ax.scatter([CRATER[1]], [CRATER[0]], marker="*", s=320, c="cyan",
           edgecolor="black", lw=0.6, zorder=5, label="Cráter Láscar (vent)")
if cl[0]:
    ax.scatter([cl[1]], [cl[0]], marker="o", s=150, facecolor="lime",
               edgecolor="black", lw=1.0, zorder=6,
               label=f"Nuestro cluster (0.92 km) → MIROVA ~1.4 km")
if loose[0]:
    ax.scatter([loose[1]], [loose[0]], marker="X", s=200, c="red",
               edgecolor="black", lw=0.8, zorder=6,
               label="Píxel suelto 'far' (Salar, ~23 km)")
# global max
gi = np.unravel_index(np.nanargmax(a), a.shape)
with rasterio.open(TIF) as ds:
    gx, gy = ds.xy(gi[0], gi[1])
ax.scatter([gx], [gy], marker="v", s=140, c="white", edgecolor="black", lw=0.8,
           zorder=6, label="Máx GLOBAL del campo MIR (Salar)")

ax.set_xlabel("Longitud", fontsize=9); ax.set_ylabel("Latitud", fontsize=9)
ax.set_title("Láscar MODIS B21 — noche 2026-05-13 07:35 UTC\n"
             "El cráter (★) tiene anomalía térmica local real; el máximo MIR-absoluto\n"
             "cae en el Salar (▼) — el confound A69 que arrastra el píxel 'far' (✗)",
             fontsize=10)
ax.legend(loc="lower left", fontsize=7.5, framealpha=0.85)
plt.tight_layout()
plt.savefig(OUT, dpi=130)
print("saved:", OUT)
print("cluster:", cl, "loose:", loose, "dc:", rec.get("distance_class"),
      "cl_dist:", pc.get("centroid_dist_km"))
