# -*- coding: utf-8 -*-
"""RA2 (S158 r2), afirmacion 2 (parte NRT): razon de magnitud contra la referencia NRT de MIROVA (latest_consolidado.csv,
solo la tabla, sin OCR) contra el cenit, por sensor y por volcan. La tabla no trae Npix, asi que aqui NO se
descompone; solo se mide si la razon cae con el cenit.

Ventana (A119): tabla sana desde 2026-03-01; VIIRS por pasada comparable desde 2026-04-01. Se usa 2026-04-01 a
2026-10-20 para los tres sensores (MODIS podria empezar en marzo; se deja igual para no mezclar ventanas).
Regimen: los records anteriores a la observacion del 2026-09-18 llevan regimen.codigo_sha 3695f675 (reproceso
historico con K, commit del 2026-10-18) y los posteriores 34cea39e (adopcion de K, #850): los DOS son el detector K.
Se separan igual por fecha como control de que no hay quiebre.
Pareo: volcan + familia de sensor + |dt| <= 10 min contra cualquier plataforma de la familia (la tabla no trae la
plataforma). 'VIIRS' = 750 m y 'VIIRS375' = 375 m segun pipeline/mirova_csv_loader.py:70-81.
Pregunta 1: si la razon cayera con el cenit lo veria el Spearman por estrato y la mediana por tramo.
Pregunta 2: si el pareo fallara, el histograma de dt no tendria pico en 0 y n seria 0.
Control positivo: la propia dependencia con el cenit de f_n medida en 02 contra el OSF; aqui se reporta ademas la
razon en z < 30 contra z >= 50 con sus n.
"""
from __future__ import annotations
import sys, io, json
import numpy as np, pandas as pd
from pathlib import Path
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
WT = Path(r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s158-audit-r2-0eeee2")
OUT = WT / "experiments/_s158_audit_r2/ra2"
sys.path.insert(0, str(WT / "scripts"))
import calidad_referencia_mirova as crm  # noqa: E402

DESDE, HASTA = "2026-04-01", "2026-10-20"
crm.avisar(DESDE, HASTA, archivo=sys.stdout)
NOM = {"Nevados de Chillan": "NevadosDeChillan", "Puyehue-Cordon Caulle": "PuyehueCordonCaulle"}
TIER = ["Lascar", "Chaiten", "PuyehueCordonCaulle", "Lastarria", "Villarrica", "NevadosDeChillan", "Isluga", "Copahue",
        "PlanchonPeteroa", "Llaima", "Tupungatito"]
FAM_CSV = {"VIIRS": "V750", "VIIRS375": "V375", "MODIS": "MODIS"}

ref = pd.read_csv(WT / "latest_consolidado.csv")
ref["t"] = pd.to_datetime(ref.Fecha_Satelite_UTC)
ref["vol"] = ref.Volcan.map(lambda s: NOM.get(s, s))
ref["fam"] = ref.Sensor.map(FAM_CSV)
ref = ref[(ref.t >= DESDE) & (ref.t < HASTA) & ref.vol.isin(TIER)]
print("filas de la tabla en ventana:", len(ref), ref.Tipo_Registro.value_counts().to_dict())
al = ref[(ref.Tipo_Registro == "ALERTA_TERMICA") & (ref.VRP_MW > 0)].copy()
print("alertas con VRP > 0:", len(al), al.fam.value_counts().to_dict())


def fam_of(s):
    return "MODIS" if s.startswith("MODIS") else ("V750" if s.endswith("_750") else "V375")


idx = defaultdict(list)
for vol in TIER:
    for r in json.load(open(WT / f"data/mirova_equivalent/{vol}.json", encoding="utf-8"))["records"]:
        if DESDE <= r["datetime_utc"] < HASTA:
            idx[(vol, fam_of(r["sensor"]))].append((pd.Timestamp(r["datetime_utc"]).value, r))
for k in idx:
    idx[k].sort(key=lambda x: x[0])
pares, dts = [], []
for _, row in al.iterrows():
    lst = idx.get((row.vol, row.fam), [])
    if not lst:
        continue
    ts = np.array([t for t, _ in lst])
    j = np.searchsorted(ts, row.t.value)
    cand = [jj for jj in (j - 1, j) if 0 <= jj < len(ts)]
    jj = min(cand, key=lambda q: abs(ts[q] - row.t.value))
    dt = (ts[jj] - row.t.value) / 60e9
    dts.append(dt)
    if abs(dt) > 10:
        continue
    r = lst[jj][1]
    pc = r.get("primary_cluster") or {}
    pub = r.get("f5_core_vrp_mw") if (row.fam == "V375" and r.get("f5_core_vrp_mw") is not None) else pc.get("vrp_mw")
    pares.append(dict(vol=row.vol, fam=row.fam, t=row.t, dt=dt, vrp_m=row.VRP_MW, dist_m=row.Distancia_km,
                      zen=r.get("sensor_zenith_deg"), solzen=r.get("solar_zenith_deg"), n_anom=r.get("n_anomalous_pixels"),
                      pc_n=pc.get("n_pixels"), pc_vrp=pc.get("vrp_mw"), rec_vrp=r.get("vrp_mw"), pub=pub,
                      sha=(r.get("regimen") or {}).get("codigo_sha", "?")[:8], fecha=r["datetime_utc"]))
dts = np.array(dts)
print("dt (min) nuestro - tabla: n =", len(dts), "| |dt|<=1:", int((abs(dts) <= 1).sum()), "| 1<|dt|<=10:", int(((abs(dts) > 1) & (abs(dts) <= 10)).sum()),
      "| >10:", int((abs(dts) > 10).sum()))
df = pd.DataFrame(pares)
df = df[df.solzen > 90]  # noche
df["reg"] = np.where(df.fecha >= "2026-09-18", "K_nrt(34cea39e)", "K_reproc(3695f675)")
print("pares nocturnos:", len(df), df.fam.value_counts().to_dict(), "| sha:", df.sha.value_counts().to_dict())
print("regimen por fecha:", df.groupby(["reg", "sha"]).size().to_dict())
det = df[df.pc_vrp.notna() & (df.pc_vrp > 0)].copy()
print("con deteccion nuestra (pc_vrp > 0):", len(det), det.fam.value_counts().to_dict(),
      "| MIROVA alerta y nosotros nada:", len(df) - len(det), df[~df.index.isin(det.index)].fam.value_counts().to_dict())
det["r_pc"] = det.pc_vrp / det.vrp_m
det["r_pub"] = det.pub / det.vrp_m
det["r_esc"] = det.rec_vrp / det.vrp_m
det["zbin"] = pd.cut(det.zen, [0, 20, 30, 40, 50, 60, 70, 90], right=False)
det.to_csv(OUT / "pares_nrt.csv", index=False)


def sp(g, c):
    g = g[[c, "zen"]].dropna()
    return round(float(g.corr(method="spearman").iloc[0, 1]), 3) if len(g) > 10 else None


for fam, g in det.groupby("fam"):
    print(f"\n=== {fam} (n={len(g)}) razon publicada (pub) / MIROVA por tramo de cenit ===")
    t = g.groupby("zbin", observed=True).agg(n=("r_pub", "size"), r_pub=("r_pub", "median"), r_pc=("r_pc", "median"), r_esc=("r_esc", "median"),
                                             n_anom=("n_anom", "median"), pc_n=("pc_n", "median"))
    print(t.round(3).to_string())
    print("  Spearman con el cenit: r_pub", sp(g, "r_pub"), "r_pc", sp(g, "r_pc"), "r_esc", sp(g, "r_esc"), "n_anom", sp(g, "n_anom"), "pc_n", sp(g, "pc_n"))
    for reg, gg in g.groupby("reg"):
        print(f"  regimen {reg}: n={len(gg)} r_pub mediana {gg.r_pub.median():.3f} Spearman r_pub-cenit {sp(gg, 'r_pub')}")
    print("  por volcan: n, mediana r_pub, Spearman r_pub-cenit, Spearman pc_n-cenit, r_pub z<30 (n) vs z>=50 (n)")
    for vol, gg in g.groupby("vol"):
        lo, hi = gg[gg.zen < 30], gg[gg.zen >= 50]
        print(f"    {vol:20s} n={len(gg):4d} r_pub {gg.r_pub.median():.3f} sp_r {sp(gg, 'r_pub')} sp_n {sp(gg, 'pc_n')} | "
              f"z<30 {lo.r_pub.median() if len(lo) else float('nan'):.3f} ({len(lo)}) z>=50 {hi.r_pub.median() if len(hi) else float('nan'):.3f} ({len(hi)})")
