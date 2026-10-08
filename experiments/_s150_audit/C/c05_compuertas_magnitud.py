"""C05: tres compuertas de magnitud en regimen fuerte (S150, frente C).

(1) Modo de un solo pixel: se llama a la funcion REAL pipeline.single_pixel_mode con el perfil
    resuelto, para mostrar la discontinuidad en 5 MW. Control positivo: con enabled=False debe
    devolver la suma.
(2) MODIS con MIROVA >= 2 MW: pc (magnitud focal publicada) contra suma de pixeles del crater y
    contra MIROVA, pasada por pasada.
(3) Tope D9: en cuantos records MODIS y V750 con pc.vrp_mw > 5 MW el tope NO actuo solo porque
    el fondo estaba tibio (t_bg >= 270 K) aunque no hubo pixel del camino NTI (n_nti == 0): son
    las senales que el mismo pipeline habria recortado a 5,0 una noche mas fria.
Instrumento: (3) si el tope estuviera roto (nunca recortara), no habria records con
d9_capped=True; hay 736 (c03), asi que el tope actua. Ventana: toda la historia de los 11 Tier A.
"""
import io
import json
import glob
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
sys.path.insert(0, ".")
import pipeline.profile as P  # noqa: E402
from pipeline.single_pixel_mode import apply_single_pixel_mode  # noqa: E402
import pandas as pd  # noqa: E402

print("(1) modo de un solo pixel, perfil:", P.ENABLE_SINGLE_PIXEL_SUB_MW_MODE,
      P.SUB_MW_REGIME_THRESHOLD_MW, P.SINGLE_PIXEL_MAX_CLUSTER_PIXELS)
for pix in ([1.6, 1.6, 1.6], [1.7, 1.7, 1.7], [2.45, 2.45], [2.55, 2.55], [4.9], [2.655, 1.828]):
    pc = {"vrp_mw": sum(pix), "n_pixels": len(pix)}
    on = apply_single_pixel_mode(pc, pix, enabled=P.ENABLE_SINGLE_PIXEL_SUB_MW_MODE,
                                 threshold_mw=P.SUB_MW_REGIME_THRESHOLD_MW,
                                 max_pixels=P.SINGLE_PIXEL_MAX_CLUSTER_PIXELS)["vrp_mw"]
    off = apply_single_pixel_mode(pc, pix, enabled=False, threshold_mw=5.0, max_pixels=3)["vrp_mw"]
    print(f"   pixeles {pix}: suma {sum(pix):.3f} -> publicado {on}  (control sin modo: {off})")

df = pd.read_csv("experiments/_s150_audit/C/c02_pares.csv")
df["m_cons"] = pd.to_numeric(df["m_cons"], errors="coerce")
print("\n(2) MODIS pareado a ALERTA de tabla con MIROVA >= 2 MW (desde 2026-03-01):")
m = df[(df["fam"] == "MODIS") & (df["m_cons"] >= 2)]
print(m[["volcan", "dt", "sensor", "pc_vrp", "pc_n", "focal", "focal_deg", "spm", "crater_sum",
         "crater_n", "n_anom", "m_cons"]].to_string())
print("   mediana pc/MIROVA:", round((m.pc_vrp / m.m_cons).median(), 3),
      "| mediana suma crater/MIROVA:", round((m.crater_sum / m.m_cons).median(), 3), "| n:", len(m))

print("\n(3) records con pc > 5 MW y n_nti == 0, por estado del tope (toda la historia):")
filas = []
for fn in glob.glob("data/mirova_equivalent/*.json"):
    if os.path.getsize(fn) < 3_000_000:
        continue
    v = os.path.basename(fn)[:-5]
    for r in json.load(open(fn, encoding="utf-8"))["records"]:
        pc = r.get("primary_cluster") or {}
        s = r["sensor"]
        fam = "MODIS" if s.startswith("MODIS") else ("V750" if s.endswith("_750") else "V375")
        filas.append(dict(v=v, dt=r["datetime_utc"], fam=fam, pc=pc.get("vrp_mw") or 0,
                          n=pc.get("n_pixels"), cd=pc.get("centroid_dist_km"),
                          cap=bool(pc.get("d9_capped")), nnti=r.get("diag_n_nti_path"),
                          tbg=r.get("t_bg_k"), dc=r.get("distance_class")))
h = pd.DataFrame(filas)
fuerte = h[(h.pc > 5) & (h.nnti == 0)]
print(fuerte.groupby(["fam", "cap"]).size())
libres = fuerte[~fuerte.cap]
print("   no recortados solo porque t_bg >= 270 K (pc > 5, n_nti == 0, cap False):", len(libres))
print(libres.sort_values("pc", ascending=False).head(15).to_string())
print("   de esos, con el cumulo dentro del inner (pc centroid <= 5 km):",
      int((libres.cd <= 5).sum()))
print("\n   pc > 5 MW con camino NTI encendido (el tope no podia actuar):",
      int(((h.pc > 5) & (h.nnti > 0)).sum()))
print("   fraccion de records MODIS con pc > 0 y n_nti == 0:",
      round(((h.fam == "MODIS") & (h.pc > 0) & (h.nnti == 0)).sum() / ((h.fam == "MODIS") & (h.pc > 0)).sum(), 3))
