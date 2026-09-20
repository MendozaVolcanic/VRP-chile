# Embudo de M2 y pool RUTINA, con las reglas de la v3. Solo lectura.
import os, sys, json, math, pickle
from datetime import datetime, timezone, timedelta
import numpy as np, pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common3 import *  # noqa

R = ROOT
sys.path.insert(0, R); sys.path.insert(0, R + "/scripts")
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import banco_paridad as bp  # noqa
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa

VENTANA = ("2026-05-09", "2026-09-19")
CONS = TD + "referencia/3b18c772f65a_registro_vrp_consolidado.csv"
OCR = TD + "referencia/7e3438046ca1_registro_vrp_ocr.csv"

coords = bp._coords_por_volcan()
inner = bp.inner_desde_html()


def cargar():
    recs, casos = [], []
    for vol in VOLS:
        d = json.load(open(R + f"/data/mirova_equivalent/{vol}.json", encoding="utf-8"))
        for r in d["records"]:
            b = bp.bucket(r.get("sensor"))
            if b != "VIIRS375":
                continue
            if not (VENTANA[0] <= r.get("datetime_utc", "")[:10] <= VENTANA[1]):
                continue
            try:
                dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            except Exception:
                continue
            la, lo = coords[vol]
            if bp.es_pasada_diurna_descartada(b, la, lo, dt):
                continue
            pc = r.get("primary_cluster") or {}
            P = (pc.get("centroid_lat"), pc.get("centroid_lon"))
            F = (r.get("final_hotspot_lat"), r.get("final_hotspot_lon"))
            rec = {"vol": vol, "b": b, "dt": dt, "noche": dt.strftime("%Y-%m-%d"),
                   "npix": pc.get("n_pixels"), "P": P, "F": F,
                   "src": r.get("final_hotspot_source"), "dc": r.get("distance_class")}
            recs.append(rec)
            slim = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
            if r.get("f5_core_vrp_mw") is None:
                slim["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                                          for p in (r.get("anomaly_pixels") or [])]
            casos.append([slim, inner[vol]])
    pred = bp.correr_node(casos)
    for rec, p in zip(recs, pred):
        rec["pub"] = bool(p[4])
    return recs


import pickle as _pk
_c = os.path.dirname(os.path.abspath(__file__)) + "/recs.pkl"
if os.path.exists(_c):
    recs = _pk.load(open(_c, "rb"))
else:
    print("cargando records...", flush=True)
    recs = cargar()
    _pk.dump(recs, open(_c, "wb"))
filas = cargar_referencia_unificada(CONS, OCR)
por_vb, ns, nv, nref = bp.indexar_referencia(filas, coords, VENTANA)
bp.etiquetar(recs, por_vb, ns, nv)

for r in recs:
    P, F = r["P"], r["F"]
    r["ok_pf"] = None not in P and None not in F
    r["dPF"] = hav(P[0], P[1], F[0], F[1]) if r["ok_pf"] else np.nan
    r["rP"] = hav(P[0], P[1], *vent(r["vol"])) if None not in P else np.nan
    r["patron"] = bool(r["npix"] == 1 and r["ok_pf"] and r["dPF"] > 0.5)
    r["tramo"] = "post" if pd.Timestamp(r["dt"]) >= CUT else "pre"

df = pd.DataFrame(recs)
print("records V375 nocturnos:", len(df))
print(df.lab.value_counts().to_dict())
print("patron:", int(df.patron.sum()), " patron+pub:", int((df.patron & df.pub).sum()))

# ---- pareo con TIF
idx = load_idx("VIIRS375")
idx_v = {v: g.sort_values("acquisition_utc") for v, g in idx.groupby("vol")}


def tif_de(vol, dt, tol=120):
    g = idx_v.get(vol)
    if g is None:
        return None
    dd = (g.acquisition_utc - pd.Timestamp(dt)).dt.total_seconds().abs()
    if not (dd <= tol).any():
        return None
    return g.loc[dd.idxmin()]


rows = []
for r in recs:
    t = tif_de(r["vol"], r["dt"])
    r["tif"] = None if t is None else t["path"]
    r["own"] = None if t is None else bool(t["own"])
    r["lat_h"] = None if t is None else float(t["lat_h"])
df = pd.DataFrame(recs)
df["tramo"] = df.dt.map(lambda d: "post" if pd.Timestamp(d) >= CUT else "pre")

sub = df[df.patron & df.pub].copy()
print("\n== embudo M2 (patron + publicado) ==")
print("total:", len(sub))
for lab, g in sub.groupby("lab"):
    print("  ", lab, len(g), " con TIF pareado:", int(g.tif.notna().sum()))

neg = sub[sub.lab == "neg_limpio"].copy()
print("\nneg_limpio fuera de Lastarria:", (neg.vol != "Lastarria").sum())
print("  con TIF pareado:", int(neg[(neg.vol != 'Lastarria')].tif.notna().sum()))

# ---- usabilidad del TIF y dL0 en P y P'
def evaluar(g, etiqueta):
    out = []
    for _, r in g.iterrows():
        if pd.isna(r["tif"]):
            out.append((r["vol"], r["dt"], "sin_tif", None, None)); continue
        Rr, why = usable({"own": r["own"], "path": r["tif"]}, r["vol"])
        if Rr is None:
            out.append((r["vol"], r["dt"], why, None, None)); continue
        P = r["P"]
        Pp = reflejo(P, vent(r["vol"]))
        zp = Z(Rr, P)
        zpp = Z(Rr, Pp)
        out.append((r["vol"], r["dt"], "ok", zp is not None, zpp is not None))
    o = pd.DataFrame(out, columns=["vol", "dt", "estado", "dl0_P", "dl0_Pp"])
    print(f"\n== usabilidad TIF, {etiqueta} (n={len(o)}) ==")
    print(o.estado.value_counts().to_dict())
    ok = o[o.estado == "ok"]
    print("  con dL0 en P:", int(ok.dl0_P.sum()), " en P':", int(ok.dl0_Pp.sum()),
          " en los dos:", int((ok.dl0_P & ok.dl0_Pp).sum()))
    return o


negf = neg[neg.vol != "Lastarria"]
o_neg = evaluar(negf, "neg_limpio fuera de Lastarria")
o_neg["tramo"] = negf.tramo.values
o_neg["vol2"] = negf.vol.values
fin = o_neg[(o_neg.estado == "ok") & o_neg.dl0_P & o_neg.dl0_Pp]
print("\n MUESTRA FINAL M2 (veredicto):", len(fin))
print(fin.vol2.value_counts().to_dict())
print(fin.tramo.value_counts().to_dict())

pickle.dump({"df": df, "o_neg": o_neg}, open(os.path.dirname(os.path.abspath(__file__)) + "/pool3.pkl", "wb"))
print("\nlisto")
