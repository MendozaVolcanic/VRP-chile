# -*- coding: utf-8 -*-
"""Verificador S158. Revisa la inferencia de e_fondo_local.py sobre los records C0 test1_roi:
  a) cuántos records tienen 2 o más píxeles (la prueba de «coherencia» sólo discrimina con 2 o más);
  b) si los campos diag_L_bg_* del record (no usados por e_fondo_local) confirman el fondo despejado;
  c) dependencia del fondo despejado con el cenit usando el cenit del record K de la MISMA pasada cuando el
     record C0 no lo trae (696 de 1130 no lo traen);
  d) qué fondo reproduce el VRP de los píxeles de los records C0 ctx_cluster (debería ser t_bg_k).

Uso: python -I v3_fondo_local_c0.py <Tupungatito_pre883.json>
"""
import io
import json
import math
import os
import statistics as st
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[2]
sys.path.insert(0, str(ROOT))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
from pipeline.constants import C1_PLANCK, C2_PLANCK  # noqa: E402
from pipeline import process_viirs as pv  # noqa: E402

LAM, KW, AREA = pv.I04_LAMBDA, pv.WOOSTER_COEFF, pv.NADIR_PIXEL_AREA_M2
SENS = ("VIIRS_SNPP", "VIIRS_NOAA20", "VIIRS_NOAA21")


def L(t):
    return C1_PLANCK / (LAM ** 5 * (math.exp(C2_PLANCK / (LAM * t)) - 1.0))


def T_de_L(l):
    return C2_PLANCK / (LAM * math.log(1.0 + C1_PLANCK / (LAM ** 5 * l)))


def q(xs, p):
    xs = sorted(xs)
    return xs[min(len(xs) - 1, int(p * len(xs)))] if xs else None


out = []
P = out.append
P(f"constantes: lambda {LAM} um, WOOSTER_COEFF {KW}, area nadir {AREA} m2")
pre = json.load(open(sys.argv[1], encoding="utf-8"))["records"]
c0 = [r for r in pre if not (r.get("regimen") or {}).get("codigo_sha") and r["sensor"] in SENS]
post = {(r["sensor"], r["datetime_utc"]): r
        for r in json.load(open(ROOT / "data" / "mirova_equivalent" / "Tupungatito.json", encoding="utf-8"))["records"]}

for fuente in ("test1_roi", "ctx_cluster"):
    rs = [r for r in c0 if r.get("final_hotspot_source") == fuente and r.get("t_bg_k")]
    npix, rangos, dts, dts_diag, dts_diag_local, filas = Counter(), [], [], [], [], []
    for r in rs:
        pix = [p for p in (r.get("anomaly_pixels") or []) if p.get("dist_km") is not None and p["dist_km"] <= 7.0
               and p["vrp_mw"] > 0]
        if not pix:
            continue
        ts = []
        for p in pix:
            resto = L(p["bt_k"]) - p["vrp_mw"] * 1e6 / (KW * AREA)
            if resto > 0:
                ts.append(T_de_L(resto))
        if not ts:
            continue
        npix["1" if len(ts) == 1 else "2+"] += 1
        if len(ts) >= 2:
            rangos.append(max(ts) - min(ts))
        tl = st.median(ts)
        dts.append(r["t_bg_k"] - tl)
        if r.get("diag_L_bg_w_m2_sr_um"):
            dts_diag.append(T_de_L(r["diag_L_bg_w_m2_sr_um"]) - r["t_bg_k"])
        if r.get("diag_L_bg_local_w_m2_sr_um"):
            dts_diag_local.append(T_de_L(r["diag_L_bg_local_w_m2_sr_um"]) - tl)
        z = r.get("sensor_zenith_deg")
        zk = (post.get((r["sensor"], r["datetime_utc"])) or {}).get("sensor_zenith_deg")
        filas.append({"dt": r["datetime_utc"], "dT": r["t_bg_k"] - tl, "z": z if z is not None else zk,
                      "z_origen": "C0" if z is not None else ("K" if zk is not None else None)})
    P(f"\n== C0 {fuente}: {len(rs)} records con t_bg; con fondo despejable: {len(dts)}; "
      f"1 píxel {npix['1']}, 2+ píxeles {npix['2+']}")
    if rangos:
        P(f"   rango del T despejado entre píxeles del mismo record (2+): mediana {st.median(rangos):.3f} K, "
          f"p90 {q(rangos, 0.9):.3f}, máx {max(rangos):.3f}; < 0,3 K en {sum(1 for x in rangos if x < 0.3)} de {len(rangos)}")
    P(f"   t_bg - T despejado: mediana {st.median(dts):.2f} K, p10 {q(dts, 0.1):.2f}, p90 {q(dts, 0.9):.2f}")
    if dts_diag:
        P(f"   T(diag_L_bg) - t_bg_k: n {len(dts_diag)}, mediana {st.median(dts_diag):.3f}, máx |.| {max(abs(x) for x in dts_diag):.3f}")
    if dts_diag_local:
        P(f"   T(diag_L_bg_local) - T despejado: n {len(dts_diag_local)}, mediana {st.median(dts_diag_local):.3f}")
    g = defaultdict(list)
    for f in filas:
        if f["z"] is None:
            g[("sin cenit", None)].append(f["dT"]); continue
        b = "<30" if f["z"] < 30 else ("30-50" if f["z"] < 50 else ">=50")
        g[(b, f["z_origen"])].append(f["dT"])
    for k in sorted(g, key=str):
        P(f"   cenit {k[0]:9s} (cenit de {k[1]}): n {len(g[k]):4d}  mediana {st.median(g[k]):.2f} K")
    gb = defaultdict(list)
    for f in filas:
        if f["z"] is not None:
            gb["<30" if f["z"] < 30 else ("30-50" if f["z"] < 50 else ">=50")].append(f["dT"])
    P("   todas con cenit (C0 o K): " + "; ".join(f"{b} n {len(gb[b])} mediana {st.median(gb[b]):.2f}"
                                                 for b in ("<30", "30-50", ">=50") if gb[b]))
    ga = defaultdict(list)
    for f in filas:
        ga[f["dt"][:4]].append(f["dT"])
    P("   por año: " + "; ".join(f"{k} n {len(v)} mediana {st.median(v):.2f}" for k, v in sorted(ga.items())))
txt = "\n".join(out)
print(txt)
(AQUI / "v3_fondo_local_c0_salida.txt").write_text(txt + "\n", encoding="utf-8")
