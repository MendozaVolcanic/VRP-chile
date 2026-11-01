# -*- coding: utf-8 -*-
"""RA2 (S158 r2), afirmaciones 1, 2 (parte OSF) y 4 sobre los pares de 01_pareo_osf.py (pares_osf.csv).

Unidades. OSF: VRP en W (03 lo confirma: k = 2.531.250 / 11.081.250 / 18.900.000 W por unidad de radiancia);
nuestros records en MW. Nuestra formula por pixel (process_viirs.py:1504-1507, process_viirs_mod.py:1055-1057):
vrp_i = A x k x max(L_i - L_bg, 0) / 1e6, con A nadir fijo (ENABLE_NADIR_FIXED_PIXEL_AREA_* = True).

Afirmacion 1, dos lecturas:
  A) sustituir en NUESTROS pixeles (los listados en anomaly_pixels, L_i = Planck(bt_k)) el fondo por el fondo medio
     por pixel de MIROVA en la misma pasada, bk_M = Tot_Lmir_bk / Npix, y recomputar la suma de escena.
  B) comparar directamente los fondos (nuestro anillo diag_L_bg_w_m2_sr_um, o el local cuando actua) con bk_M y
     traducir la diferencia a MW: n_ours x A x k x (L_bg_ours - bk_M) / 1e6, contra la brecha VRP_M - VRP_ours.
Afirmacion 2 (OSF): razon = (n_ours / Npix_M) x (dL_medio_ours / dL_medio_M); cada factor contra el cenit.
Afirmacion 4: n_anomalous_pixels (escena) y pc.n_pixels contra Npix_M.

Pregunta 1: si la magnitud estuviera rota (p. ej. k mal), la razon mediana no estaria cerca de 1 en ningun estrato.
Pregunta 2: todo denominador se imprime; un estrato sin pares sale como n = 0, no como razon.
Control positivo: al sustituir el fondo por uno 20 % mas alto que el nuestro, la razon tiene que BAJAR en todos los
pares con dL > 0 (se imprime la fraccion que baja; debe ser 1,0).
Ventana: 2025 (cobertura del OSF), pares con |dt| <= 10 min, noche (Dayflag = 0 y solar_zenith > 90).
"""
from __future__ import annotations
import sys, io, json, math
import numpy as np, pandas as pd
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
WT = Path(r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s158-audit-r2-0eeee2")
OUT = WT / "experiments/_s158_audit_r2/ra2"
sys.path.insert(0, str(WT))
from pipeline.process_viirs import C1, C2  # noqa: E402

LAMBDA = {"V375": 3.740, "V750": 4.050, "MODIS": 3.929}
AREA_M2 = {"V375": 375.0 ** 2, "V750": 750.0 ** 2, "MODIS": 1.0e6}
WOOSTER = {"V375": 18.0, "V750": 19.7, "MODIS": 18.9}
NOMBRE_OSF = {"Lascar": "Láscar", "Chaiten": "Chaitén", "PuyehueCordonCaulle": "Puyehue-Cordón Caulle",
              "NevadosDeChillan": "Chillán, Nevados de", "PlanchonPeteroa": "Planchón-Peteroa"}


def planck(bt, lam):
    return C1 / (lam ** 5 * (math.exp(C2 / (lam * bt)) - 1.0))


def q(s):
    s = s.dropna()
    return (len(s), round(float(s.median()), 3) if len(s) else None, round(float(s.quantile(.25)), 3) if len(s) else None,
            round(float(s.quantile(.75)), 3) if len(s) else None)


df = pd.read_csv(OUT / "pares_osf.csv", parse_dates=["t_osf", "t_ours"])
print("pares cargados:", len(df), "| dayflag=0:", int((df.dayflag == 0).sum()), "| solar_zenith>90:", int((df.solzen > 90).sum()))
df = df[(df.dayflag == 0) & (df.solzen > 90)].copy()
print("pares nocturnos:", len(df), df.fam.value_counts().to_dict())
df["vrp_m"] = df.osf_vrp_w / 1e6
df["bk_m"] = df.osf_bk / df.osf_npix          # fondo medio por pixel de MIROVA
df["hot_m"] = df.osf_hot / df.osf_npix        # radiancia media del pixel alertado de MIROVA
df["dl_m"] = (df.osf_hot - df.osf_bk) / df.osf_npix
df["A"] = df.fam.map(AREA_M2); df["k"] = df.fam.map(WOOSTER)
det = df[df.pc_vrp.notna() & (df.n_anom > 0)].copy()
print("pares con deteccion nuestra (pc no nulo y n_anom > 0):", len(det), det.fam.value_counts().to_dict())
print("pares SIN deteccion nuestra (MIROVA alerta, nosotros nada):", len(df) - len(det),
      (df[~df.index.isin(det.index)].groupby(["fam"]).size().to_dict()))

# ---- razones de magnitud, candidatos ----
det["pub"] = np.where(det.fam.eq("V375") & det.f5.notna(), det.f5, det.pc_vrp)  # lo que publica el tablero (A10 + matiz S132)
for c in ["rec_vrp", "pc_vrp", "pub", "sum_vrp_listed"]:
    det["r_" + c] = det[c] / det.vrp_m
print("\n=== razon nuestra / MIROVA (mediana, p25, p75) por familia; n ===")
for fam, g in det.groupby("fam"):
    print(fam, {c: q(g["r_" + c]) for c in ["rec_vrp", "pc_vrp", "pub", "sum_vrp_listed"]})
print("\nrazon rec_vrp (escena) por volcan y familia: (n, mediana, p25, p75)")
for (fam, vol), g in det.groupby(["fam", "vol"]):
    print(f"  {fam:5s} {vol:20s} escena {q(g.r_rec_vrp)}  pc {q(g.r_pc_vrp)}  pub {q(g.r_pub)}")
# cuantos records tienen mas pixeles que los listados (la lista se corta en 100)
print("\nrecords con n_anom > n_listed (lista truncada a 100):", int((det.n_anom > det.n_listed).sum()), "de", len(det))
print("records con rec_vrp != sum_vrp_listed (>1 %):", int(((det.rec_vrp - det.sum_vrp_listed).abs() > 0.01 * det.rec_vrp.clip(lower=1e-9)).sum()))

# ---- Afirmacion 1, lectura A: sustituir el fondo de MIROVA en nuestros pixeles ----
print("\n=== Afirmacion 1, lectura A: VRP' = sum_i A k max(L_i - bk_M, 0)/1e6 sobre nuestros pixeles listados ===")
recs_cache = {}
def pixeles(vol, sensor, t):
    key = vol
    if key not in recs_cache:
        recs_cache[key] = {(r["sensor"], r["datetime_utc"]): r for r in json.load(open(WT / f"data/mirova_equivalent/{vol}.json", encoding="utf-8"))["records"]}
    return recs_cache[key][(sensor, t.strftime("%Y-%m-%d %H:%M"))].get("anomaly_pixels") or []

rows = []
for i, p in det.iterrows():
    ap = pixeles(p.vol, p.sensor, p.t_ours)
    lam, A, k = LAMBDA[p.fam], AREA_M2[p.fam], WOOSTER[p.fam]
    L = np.array([planck(x["bt_k"], lam) for x in ap])
    v_lista = sum(x["vrp_mw"] for x in ap)
    v_A = float(np.sum(A * k * np.clip(L - p.bk_m, 0, None)) / 1e6)
    v_ctrl = float(np.sum(A * k * np.clip(L - (p.l_bg_ring * 1.2), 0, None)) / 1e6)  # control: fondo 20 % mas alto
    # fondo nuestro efectivo por pixel implicito en la lista: L_i - vrp_i*1e6/(A k)
    lbg_impl = L - np.array([x["vrp_mw"] for x in ap]) * 1e6 / (A * k)
    rows.append(dict(i=i, v_lista=v_lista, v_A=v_A, v_ctrl=v_ctrl, lbg_impl_med=float(np.median(lbg_impl)) if len(L) else np.nan,
                     L_mean=float(L.mean()) if len(L) else np.nan, L_max=float(L.max()) if len(L) else np.nan,
                     n_clip=int(np.sum(L - p.bk_m <= 0))))
aa = pd.DataFrame(rows).set_index("i")
det = det.join(aa)
det["r_lista"] = det.v_lista / det.vrp_m
det["r_A"] = det.v_A / det.vrp_m
det["r_ctrl"] = det.v_ctrl / det.vrp_m
con_dl = det[det.v_lista > 0]
print("control positivo (fondo nuestro x 1,2): fraccion de pares con v_lista > 0 en que la magnitud BAJA:",
      round(float((con_dl.v_ctrl < con_dl.v_lista).mean()), 4), "n =", len(con_dl))
print("\nrazon contra MIROVA ANTES (nuestro fondo) y DESPUES (fondo medio de MIROVA, misma pasada), por familia:")
for fam, g in det.groupby("fam"):
    print(f"  {fam}: n={len(g)} antes {q(g.r_lista)[1:]} despues {q(g.r_A)[1:]} | pares en que cambia >10 %: "
          f"{int(((g.r_A / g.r_lista.replace(0, np.nan) - 1).abs() > 0.1).sum())} | pixeles recortados a 0 con bk_M: {int(g.n_clip.sum())} de {int(g.n_listed.sum())}")
print("por volcan (V375):")
for vol, g in det[det.fam == "V375"].groupby("vol"):
    print(f"  {vol:20s} n={len(g):4d} antes {q(g.r_lista)[1:]} despues {q(g.r_A)[1:]}")

# ---- Afirmacion 1, lectura B: comparar fondos directamente ----
print("\n=== Afirmacion 1, lectura B: fondo nuestro vs fondo medio por pixel de MIROVA (radiancia W m-2 sr-1 um-1) ===")
det["lbg_ours"] = det.l_bg_local.where(det.l_bg_local.notna(), det.l_bg_ring)
det["lbg_fuente"] = np.where(det.l_bg_local.notna(), "local", "anillo")
det["dbg"] = det.lbg_ours - det.bk_m
det["dbg_impl"] = det.lbg_impl_med - det.bk_m
det["dbg_mw"] = det.n_listed * det.A * det.k * det.dbg_impl / 1e6   # MW que explica la diferencia de fondo (sobre nuestros n)
det["brecha_mw"] = det.vrp_m - det.v_lista
for fam, g in det.groupby("fam"):
    print(f"  {fam}: n={len(g)} fuente del fondo {g.lbg_fuente.value_counts().to_dict()}")
    print(f"     L_bg nuestro (implicito en la lista) mediana {g.lbg_impl_med.median():.4f} | bk_M mediana {g.bk_m.median():.4f} | "
          f"razon L_bg_ours/bk_M mediana {(g.lbg_impl_med / g.bk_m).median():.3f} p25 {(g.lbg_impl_med / g.bk_m).quantile(.25):.3f} p75 {(g.lbg_impl_med / g.bk_m).quantile(.75):.3f}")
    print(f"     L_hot nuestro medio {g.L_mean.median():.4f} | hot_M medio {g.hot_m.median():.4f} | razon mediana {(g.L_mean / g.hot_m).median():.3f}")
    print(f"     dL medio nuestro {((g.L_mean - g.lbg_impl_med)).median():.4f} | dL medio MIROVA {g.dl_m.median():.4f}")
    print(f"     MW que explica el fondo (n_ours x A k x dbg): mediana {g.dbg_mw.median():.4f} | brecha VRP_M - VRP_ours mediana {g.brecha_mw.median():.4f} | "
          f"fraccion de la brecha explicada por el fondo (mediana de dbg_mw/brecha donde brecha>0): "
          f"{(g[g.brecha_mw > 0].dbg_mw / g[g.brecha_mw > 0].brecha_mw).median():.3f} (n={int((g.brecha_mw > 0).sum())})")
print("por volcan (V375), razon L_bg_ours/bk_M y L_hot_ours/hot_M (medianas):")
for vol, g in det[det.fam == "V375"].groupby("vol"):
    print(f"  {vol:20s} n={len(g):4d} bg {(g.lbg_impl_med / g.bk_m).median():.3f} hot {(g.L_mean / g.hot_m).median():.3f} "
          f"n_ours/Npix {(g.n_anom / g.osf_npix).median():.2f} fuente {g.lbg_fuente.value_counts().to_dict()}")

# ---- Afirmacion 2 (OSF): descomposicion razon = (n_ours/Npix) x (dL_ours/dL_M) contra el cenit ----
print("\n=== Afirmacion 2 (OSF): razon de escena = f_n x f_dL contra el cenit ===")
det["f_n"] = det.n_anom / det.osf_npix
det["f_dl"] = (det.rec_vrp * 1e6 / (det.A * det.k * det.n_anom)) / det.dl_m
det["f_n_pc"] = det.pc_n / det.osf_npix
det["f_dl_pc"] = (det.pc_vrp * 1e6 / (det.A * det.k * det.pc_n)) / det.dl_m
det["zbin"] = pd.cut(det.zen, [0, 20, 30, 40, 50, 60, 70, 90], right=False)
print("cenit nuestro vs SatZen del OSF: mediana |dif| grados:", round(float((det.zen - det.osf_zen).abs().median()), 2),
      "p95:", round(float((det.zen - det.osf_zen).abs().quantile(.95)), 2))
for fam, g in det.groupby("fam"):
    print(f"\n{fam} (n={len(g)}): mediana por tramo de cenit nuestro")
    t = g.groupby("zbin", observed=True).agg(n=("r_rec_vrp", "size"), r_escena=("r_rec_vrp", "median"), f_n=("f_n", "median"),
                                             f_dl=("f_dl", "median"), r_pc=("r_pc_vrp", "median"), f_n_pc=("f_n_pc", "median"),
                                             f_dl_pc=("f_dl_pc", "median"), r_pub=("r_pub", "median"))
    print(t.round(3).to_string())
    sp = {c: round(float(g[[c, "zen"]].dropna().corr(method="spearman").iloc[0, 1]), 3) for c in ["r_rec_vrp", "f_n", "f_dl", "r_pc_vrp", "f_n_pc", "f_dl_pc", "r_pub"]}
    print("  Spearman con el cenit:", sp)
    # pendiente log-log por regresion: log(r) = a + b*log(sec z)
    sec = 1 / np.cos(np.radians(g.zen))
    for c in ["r_rec_vrp", "f_n", "f_dl", "r_pc_vrp"]:
        m = (g[c] > 0) & np.isfinite(g[c])
        if m.sum() > 10:
            b = np.polyfit(np.log(sec[m]), np.log(g[c][m]), 1)[0]
            print(f"  pendiente de log({c}) sobre log(sec z): {b:.3f}")
print("\npor volcan (V375 y MODIS), Spearman de razon de escena, f_n y f_dL con el cenit; n:")
for (fam, vol), g in det.groupby(["fam", "vol"]):
    if len(g) < 15:
        print(f"  {fam} {vol}: n={len(g)} (< 15, no se calcula)"); continue
    sp = {c: round(float(g[[c, "zen"]].dropna().corr(method="spearman").iloc[0, 1]), 2) for c in ["r_rec_vrp", "f_n", "f_dl", "r_pc_vrp"]}
    lo, hi = g[g.zen < 30], g[g.zen >= 50]
    print(f"  {fam:5s} {vol:20s} n={len(g):4d} {sp} | mediana r_escena z<30: {lo.r_rec_vrp.median() if len(lo) else float('nan'):.2f} (n={len(lo)}) z>=50: {hi.r_rec_vrp.median() if len(hi) else float('nan'):.2f} (n={len(hi)})"
          f" | f_n z<30 {lo.f_n.median() if len(lo) else float('nan'):.2f} z>=50 {hi.f_n.median() if len(hi) else float('nan'):.2f} | f_dl z<30 {lo.f_dl.median() if len(lo) else float('nan'):.2f} z>=50 {hi.f_dl.median() if len(hi) else float('nan'):.2f}")

# ---- Afirmacion 4: conteo de pixeles ----
print("\n=== Afirmacion 4: nuestro conteo contra Npix de MIROVA ===")
for fam, g in det.groupby("fam"):
    fn = g.n_anom / g.osf_npix
    fp = g.pc_n / g.osf_npix
    print(f"  {fam}: n={len(g)} | n_anom/Npix mediana {fn.median():.2f} p25 {fn.quantile(.25):.2f} p75 {fn.quantile(.75):.2f} | "
          f"n_anom > Npix {int((g.n_anom > g.osf_npix).sum())}, = {int((g.n_anom == g.osf_npix).sum())}, < {int((g.n_anom < g.osf_npix).sum())} | "
          f"pc_n/Npix mediana {fp.median():.2f} | pc_n > Npix {int((g.pc_n > g.osf_npix).sum())}, = {int((g.pc_n == g.osf_npix).sum())}, < {int((g.pc_n < g.osf_npix).sum())}")
    print(f"     Npix MIROVA mediana {g.osf_npix.median():.0f} max {g.osf_npix.max()} | n_anom nuestro mediana {g.n_anom.median():.0f} max {g.n_anom.max()} | pc_n mediana {g.pc_n.median():.0f}")
print("Npix de MIROVA en TODOS los pares (incluidos sin deteccion nuestra):", df.groupby("fam").osf_npix.describe()[["count", "50%", "max"]].to_string().replace("\n", " || "))
det.to_csv(OUT / "pares_osf_analizados.csv", index=False)
print("\nguardado pares_osf_analizados.csv")
