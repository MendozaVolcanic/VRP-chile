# -*- coding: utf-8 -*-
"""F3: los volcanes que el OSF 2025 no cubre (Tupungatito, Llaima, Chillán, Villarrica 2026) y VIIRS 750,
con la tabla del scraper (latest_consolidado.csv, sólo tabla: A119), 2026-03-01 a 2026-10-20, noche 03-09 UTC.
Sólo hay VRP de MIROVA (sin Npix ni L_bk), así que la descomposición es parcial:
  pub/M   magnitud publicada nuestra / MIROVA            (lo que ve el operador)
  esc/M   VRP de todos nuestros alertados / MIROVA       (sin selección; suma de anomaly_pixels si n <= 100)
  clip    fracción de nuestros alertados con ΔL recortado a 0 (fondo >= L_hot: indicio de fondo sobreestimado)
  bg_r/l  fondo de anillo / kernel local (cuando el volcán usa kernel)
  t_bg    temperatura del fondo del anillo
Instrumento: (1) se imprime cuántas alertas de MIROVA no tienen record nuestro a ±3 min (SIN DATO, no FALLA);
(2) control positivo: la misma lógica sobre Láscar V375 tiene que dar una razón del orden de la del OSF 2025 (0,6-0,8).
Uso: python -B scraper2026.py <raiz>
"""
import csv, json, os, sys
from datetime import datetime, timedelta
import numpy as np, pandas as pd
import yaml

ROOT = sys.argv[1]
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from calidad_referencia_mirova import avisar  # noqa
DESDE, HASTA = "2026-03-01", "2026-10-20"
avisar(DESDE, HASTA)
ALIAS = {"Nevados de Chillan": "NevadosDeChillan", "Puyehue-Cordon Caulle": "PuyehueCordonCaulle", "Planchon-Peteroa": "PlanchonPeteroa"}
SEN = {"VIIRS375": "V375", "VIIRS": "V750", "MODIS": "MODIS"}
KA = {"V375": 18.0 * 140625, "V750": 19.7 * 562500, "MODIS": 18.9 * 1e6}
inner = {v["name"]: v.get("inner_radius_km", 10) for v in yaml.safe_load(open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8"))["volcanoes"]}
alert = {}
for r in csv.DictReader(open(os.path.join(ROOT, "latest_consolidado.csv"), encoding="utf-8", errors="replace")):
    s = SEN.get((r.get("Sensor") or "").strip())
    if not s or "ALERTA" not in (r.get("Tipo_Registro") or ""):
        continue
    t = (r.get("Fecha_Satelite_UTC") or "").strip()
    if not (DESDE <= t[:10] <= HASTA) or not (3 <= int(t[11:13] or 12) <= 9):
        continue
    try:
        v = float(r["VRP_MW"])
    except (TypeError, ValueError):
        continue
    if v <= (0.05 if s == "V375" else 0.0):
        continue
    vol = ALIAS.get(r["Volcan"].strip(), r["Volcan"].strip())
    k = (vol, s, t[:16])
    alert[k] = max(alert.get(k, 0), v)
def bucket(x):
    x = str(x or "").upper()
    return ("V750" if "750" in x else "V375") if "VIIRS" in x else "MODIS"
rows, sin = [], 0
recs_by = {}
for vol in {k[0] for k in alert}:
    p = os.path.join(ROOT, "data", "mirova_equivalent", f"{vol}.json")
    if not os.path.exists(p):
        continue
    d = json.load(open(p, encoding="utf-8"))
    for r in (d.get("records", d) if isinstance(d, dict) else d):
        recs_by.setdefault((vol, bucket(r.get("sensor"))), []).append((datetime.strptime(str(r["datetime_utc"])[:16], "%Y-%m-%d %H:%M"), r))
for (vol, s, t), vM in alert.items():
    tt = datetime.strptime(t, "%Y-%m-%d %H:%M")
    c = recs_by.get((vol, s), [])
    b = min(c, key=lambda x: abs(x[0] - tt), default=None)
    if not b or abs(b[0] - tt) > timedelta(minutes=3):
        sin += 1
        continue
    r = b[1]
    pc = r.get("primary_cluster") or {}
    ok = r.get("distance_class") == "summit" and pc and (pc.get("centroid_dist_km") or 0) <= inner.get(vol, 10)
    f5 = r.get("f5_core_vrp_mw") if s == "V375" else None
    pub = (f5 if (isinstance(f5, (int, float)) and f5 > 0) else (pc.get("vrp_mw") or 0)) if ok else 0.0
    px = r.get("anomaly_pixels") or []
    n = r.get("n_anomalous_pixels") or 0
    esc = float(sum(p["vrp_mw"] for p in px)) if (px and len(px) == n) else np.nan
    rows.append({"vol": vol, "b": s, "zen": r.get("sensor_zenith_deg"), "M": vM, "pub": pub, "esc": esc, "n": n,
                 "clip": (sum(1 for p in px if p["vrp_mw"] <= 0) / len(px)) if px else np.nan,
                 "bg_r": r.get("diag_L_bg_w_m2_sr_um"), "bg_l": r.get("diag_L_bg_local_w_m2_sr_um"), "tbg": r.get("t_bg_k"),
                 "tmax": r.get("t_max_k"), "dclass": r.get("distance_class")})
D = pd.DataFrame(rows)
print(f"alertas nocturnas de MIROVA (tabla) {len(alert)}; pareadas {len(D)}; sin record a ±3 min {sin}")
D["tr"] = pd.cut(D.zen.astype(float), [0, 40, 75], labels=["<=40", ">40"])
pd.set_option("display.width", 250)
g = D.groupby(["b", "vol", "tr"], observed=True)
T = g.agg(n=("M", "size"), M_med=("M", "median"), pub_sum=("pub", "sum"), esc_sum=("esc", "sum"), M_sum=("M", "sum"),
          pub_med_ratio=("pub", lambda x: np.nan), clip=("clip", "median"), n_med=("n", "median"), tbg=("tbg", "median"),
          no_pub=("pub", lambda x: int((x <= 0).sum())))
T["pub/M"] = (T.pub_sum / T.M_sum).round(3)
T["esc/M"] = (T.esc_sum / T.M_sum).round(3)
med = D[D.pub > 0].assign(r=lambda x: x.pub / x.M).groupby(["b", "vol", "tr"], observed=True).r.median().round(3)
T["pub/M_med|pub"] = med
print(T.drop(columns=["pub_sum", "esc_sum", "M_sum", "pub_med_ratio"]).round(3).to_string())
D.to_csv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "scraper2026_filas.csv"), index=False)
