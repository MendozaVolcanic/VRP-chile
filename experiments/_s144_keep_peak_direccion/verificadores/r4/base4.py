# Verificador v4 S144: pools de referencia y conteos. Solo lectura.
import os, sys, math, pickle, json
from datetime import datetime, timezone, timedelta
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
V3 = os.path.abspath(HERE + "/../v3")
sys.path.insert(0, V3)
from common3 import *  # noqa

R = ROOT
sys.path.insert(0, R); sys.path.insert(0, R + "/scripts")
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import banco_paridad as bp  # noqa
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa

VENTANA = ("2026-05-09", "2026-09-19")
CONS = TD + "referencia/3b18c772f65a_registro_vrp_consolidado.csv"
OCR = TD + "referencia/7e3438046ca1_registro_vrp_ocr.csv"

d3 = pickle.load(open(V3 + "/pool3.pkl", "rb"))
df = d3["df"]
geomP = pickle.load(open(V3 + "/geomP.pkl", "rb"))

idx = load_idx("VIIRS375")
idx_v = {v: g.sort_values("acquisition_utc").reset_index(drop=True) for v, g in idx.groupby("vol")}


def tif_de(vol, dt, tol=120):
    g = idx_v.get(vol)
    if g is None:
        return None
    dd = (g.acquisition_utc - pd.Timestamp(dt)).dt.total_seconds().abs()
    if not (dd <= tol).any():
        return None
    return g.loc[dd.idxmin()]


def pool_rutina_fila():
    """Lectura A (la que manda la v4 S4): pasadas RUTINA de la FILA de MIROVA,
    sin exigir record nuestro. Devuelve dict vol -> DataFrame(dt, path, own)."""
    coords = bp._coords_por_volcan()
    filas = cargar_referencia_unificada(CONS, OCR)
    por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, VENTANA)
    out = {}
    for (vol, b), lista in por_vb.items():
        if b != "VIIRS375" or vol not in VOLS:
            continue
        rows = []
        vistos = set()
        for dt, f in lista:
            if f["tipo"] != "RUTINA" or f["source"] != "CONS" or (f["vrp_mw"] or 0) != 0:
                continue
            noche = f["fecha_utc"][:10]
            s = ns.get((vol, b, noche), {"alerta": False, "fp": False})
            if s["alerta"] or s["fp"]:
                continue
            key = dt.strftime("%Y-%m-%d %H:%M")
            if key in vistos:
                continue
            vistos.add(key)
            t = tif_de(vol, dt)
            if t is None:
                continue
            rows.append(dict(vol=vol, dt=pd.Timestamp(dt), path=t["path"], own=bool(t["own"]),
                             noche=noche, lat_h=float(t["lat_h"])))
        if rows:
            out[vol] = pd.DataFrame(rows).sort_values("dt").reset_index(drop=True)
    return out


def pool_rutina_record():
    """Lectura B: pasadas neg_limpio segun nuestro record (exige record a +-120 s)."""
    out = {}
    sub = df[(df.lab == "neg_limpio") & df.tif.notna()].copy()
    for vol, g in sub.groupby("vol"):
        g = g.copy()
        g["dt"] = pd.to_datetime(g.dt, utc=True)
        out[vol] = g[["vol", "dt", "tif", "own", "noche"]].rename(
            columns={"tif": "path"}).sort_values("dt").reset_index(drop=True)
    return out


if __name__ == "__main__":
    pa = pool_rutina_fila()
    pb = pool_rutina_record()
    print("== pool RUTINA, lectura A (fila de MIROVA, con TIF pareado a +-120 s) ==")
    for v in VOLS:
        print("  %-22s A=%3d   B=%3d" % (v, len(pa.get(v, [])), len(pb.get(v, []))))
    pickle.dump({"A": pa, "B": pb}, open(HERE + "/pools4.pkl", "wb"))

    # --- muestra de M2 (conteos, sin abrir ningun raster en P)
    m2 = df[df.patron & df.pub & (df.lab == "neg_limpio") & (df.vol != "Lastarria")].copy()
    print("\n== M2 candidatas (patron+pub+neg_limpio fuera de Lastarria): %d ==" % len(m2))
    o = d3["o_neg"]
    fin = o[(o.estado == "ok") & o.dl0_P & o.dl0_Pp]
    print("   con TIF usable (embudo ronda 3): %d" % len(fin))
    print("   estados:", o.estado.value_counts().to_dict())
    # noches
    m2ok = m2[m2.tif.notna()].copy()
    print("\n   pasadas con TIF pareado: %d -> noches (vol,noche): %d"
          % (len(m2ok), m2ok.groupby(["vol", "noche"]).ngroups))
