# -*- coding: utf-8 -*-
"""F3 (S158): descomposición física del déficit de magnitud contra MIROVA, pasada por pasada, OSF v2.5 de 2025.

POR QUÉ: el OSF trae, por pasada, Npix, la radiancia MIR sumada de los alertados (L_hot) y la de su fondo (L_bk).
Nuestros records traen la BT de cada píxel alertado (top 100) y su VRP. Con eso el déficit se parte en:
  (a) cuántos píxeles (Npix nuestro / Npix MIROVA),
  (b) cuán calientes son (L_hot medio por píxel),
  (c) qué fondo se resta (L_bk medio por píxel),
  (d) qué parte de lo que alertamos publicamos (selección: cúmulo, núcleo F5', inner).
Lo que es del OBJETO (oclusión del cráter, huella, nieve) cambia la radiancia que ven los dos sistemas por igual:
entra en (b) igual para ambos y se cancela en la razón. Lo que es del PROCESAMIENTO aparece como (a), (c) o (d).

Las dos preguntas del instrumento:
1. Si el pareo estuviera roto (pasadas distintas), el cenit nuestro y el de MIROVA no coincidirían: se imprime la
   diferencia de cenit como control. Si la descomposición estuviera rota, el producto de los factores no daría la razón:
   se imprime la identidad.
2. Si el instrumento estuviera muerto (no lee píxeles), n_listados = 0 en todas: se imprime cuántas pasadas tienen
   píxeles listados y cuántas quedan SIN DATO (MIROVA alertó y nosotros no tenemos ningún alertado).
Control positivo: VRP_MIROVA = k * A * (L_hot - L_bk) con k*A = 2.531.250 (V375) se verifica fila por fila.

Uso: python -B descomp_osf2025.py <raiz repo> <OSF csv> <salida csv>
Ventana: 2025-01-01 a 2025-12-31, noche (Dayflag 0), V375 y MODIS (V750 casi no existe en el OSF de Chile 2025).
"""
import json, os, sys
import numpy as np
import pandas as pd

ROOT, OSF, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
IDS = {358041: "Chaiten", 357070: "NevadosDeChillan", 357090: "Copahue", 355030: "Isluga", 355100: "Lascar",
       355120: "Lastarria", 357110: "Llaima", 357040: "PlanchonPeteroa", 357150: "PuyehueCordonCaulle",
       357120: "Villarrica"}
C1, C2 = 1.191042e8, 14388.0
LAM = {"V375": 3.740, "V750": 4.050, "MODIS": 3.959}
KA = {"V375": 18.0 * 140625, "V750": 19.7 * 562500, "MODIS": 18.9 * 1e6}
RES = {375: "V375", 750: "V750", 1000: "MODIS"}


def planck(bt, lam):
    bt = np.asarray(bt, float)
    return C1 / (lam ** 5 * (np.exp(C2 / (lam * bt)) - 1))


def bucket(s):
    s = str(s or "").upper()
    if "VIIRS" in s:
        return "V750" if "750" in s else "V375"
    return "MODIS"


import yaml
inner = {v["name"]: v.get("inner_radius_km", 10)
         for v in yaml.safe_load(open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8"))["volcanoes"]}

osf = pd.read_csv(OSF, encoding="latin-1")
osf = osf[osf.IDvolc.isin(IDS) & (osf.Dayflag == 0)].copy()
osf["t"] = pd.to_datetime(osf.timeUTC, format="%d/%m/%Y %H:%M", errors="coerce")
osf = osf[(osf.t >= "2025-01-01") & (osf.t < "2026-01-01")]
osf["vol"] = osf.IDvolc.map(IDS)
osf["b"] = osf.Resolution.map(RES)
osf["ka_chk"] = osf.VRP / (osf.Tot_Lmir_hot - osf.Tot_Lmir_bk)
print("control positivo k*A del OSF por sensor (min, max):")
print(osf.groupby("b").ka_chk.agg(["min", "max", "count"]))

rows = []
for vol in sorted(osf.vol.unique()):
    d = json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", f"{vol}.json"), encoding="utf-8"))
    recs = d.get("records", d) if isinstance(d, dict) else d
    by = {}
    for r in recs:
        t = pd.Timestamp(str(r.get("datetime_utc"))[:16])
        if t.year != 2025:
            continue
        by.setdefault(bucket(r.get("sensor")), []).append((t, r))
    for _, m in osf[osf.vol == vol].iterrows():
        cand = by.get(m.b, [])
        if not cand:
            continue
        t0, r = min(cand, key=lambda x: abs(x[0] - m.t))
        dt = abs((t0 - m.t).total_seconds()) / 60
        if dt > 5:
            rows.append({"vol": vol, "b": m.b, "t": m.t, "pareo": "sin_record", "N_M": m.Npix,
                         "Lhot_M": m.Tot_Lmir_hot, "Lbk_M": m.Tot_Lmir_bk, "VRP_M": m.VRP / 1e6,
                         "zen_M": m.SatZen, "maxd_M": m.Max_Dist, "cls": m["class"]})
            continue
        px = r.get("anomaly_pixels") or []
        bt = np.array([p["bt_k"] for p in px], float)
        vr = np.array([p["vrp_mw"] for p in px], float)
        Lh = planck(bt, LAM[m.b]) if len(bt) else np.array([])
        dL = vr * 1e6 / KA[m.b]
        pc = r.get("primary_cluster") or {}
        pub_ok = (r.get("distance_class") == "summit" and pc and (pc.get("centroid_dist_km") or 0) <= inner.get(vol, 10))
        if m.b == "V375" and isinstance(r.get("f5_core_vrp_mw"), (int, float)):
            pubv = r.get("f5_core_vrp_mw")
        else:
            pubv = pc.get("vrp_mw")
        dist = np.array([p.get("dist_km", np.nan) for p in px], float)
        rows.append({
            "vol": vol, "b": m.b, "t": m.t, "pareo": "ok", "dt_min": dt, "zen_M": m.SatZen,
            "zen_o": r.get("sensor_zenith_deg"), "cls": m["class"], "maxd_M": m.Max_Dist,
            "N_M": m.Npix, "Lhot_M": m.Tot_Lmir_hot, "Lbk_M": m.Tot_Lmir_bk, "VRP_M": m.VRP / 1e6,
            "n_all": r.get("n_anomalous_pixels") or 0, "n_list": len(px),
            "Lhot_o": float(Lh.sum()), "dL_o": float(dL.sum()), "n_clip": int((vr <= 0).sum()),
            "vrp_scene_o": r.get("vrp_mir_mw"), "vrp_o_rec": r.get("vrp_mw"),
            "pub_ok": bool(pub_ok), "pub_o": (pubv if pub_ok else 0.0) or 0.0, "pc_n": pc.get("n_pixels"),
            "pc_vrp": pc.get("vrp_mw"), "f5": r.get("f5_core_vrp_mw"),
            "Lbg_ring": r.get("diag_L_bg_w_m2_sr_um"), "Lbg_local": r.get("diag_L_bg_local_w_m2_sr_um"),
            "tbg": r.get("t_bg_k"), "n_in5": int((dist <= 5).sum()), "dist_med": float(np.nanmedian(dist)) if len(dist) else np.nan,
            "dclass": r.get("distance_class"), "src": r.get("final_hotspot_source"),
        })
df = pd.DataFrame(rows)
df.to_csv(OUT, index=False)
ok = df[df.pareo == "ok"]
print(f"\nfilas OSF nocturnas 2025 en los 10 volcanes: {len(df)}; pareadas a un record (|dt|<=5 min): {len(ok)}; sin record: {(df.pareo != 'ok').sum()}")
print("control de pareo: |cenit nuestro - cenit MIROVA| mediana y p95 por sensor:")
ok = ok.assign(dz=(ok.zen_o - ok.zen_M).abs())
print(ok.groupby("b").dz.describe(percentiles=[.5, .95])[["count", "50%", "95%", "max"]])
print("pasadas pareadas con 0 píxeles alertados nuestros (MIROVA alertó, nosotros nada):")
print(ok.assign(cero=ok.n_all == 0).groupby(["b", "vol"]).cero.agg(["sum", "count"]).to_string())
