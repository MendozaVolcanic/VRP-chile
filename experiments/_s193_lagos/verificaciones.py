"""S193: numeros del INFORME que no salen de resumir.py (salida: verificaciones.txt).

Uso: python -I verificaciones.py <raiz_repo> <dir_medicion>
"""
import json
import os
import sys

import numpy as np
import pandas as pd
import yaml

REPO, D = sys.argv[1], sys.argv[2]
out = []
P = out.append
rec = pd.read_csv(os.path.join(D, "records.csv"))
pix = pd.read_csv(os.path.join(D, "pixeles.csv"))

P("== Pico sobre agua: BT MIR (K), todos los volcanes ==")
a = rec[rec.clase_pico == "agua"]
P(a.bt_pico_k.describe(percentiles=[.1, .5, .9]).round(1).to_string())
P("== Laguna del Maule, pico sobre agua: BT MIR y t_bg (K) ==")
x = a[a.volcan == "LagunaDelMaule"]
P(pd.DataFrame({"bt": x.bt_pico_k.describe(), "t_bg": x.t_bg_k.describe()}).round(1).to_string())

P("== Lagos cratericos: pixeles alertados a <=5 km y su fraccion de agua ==")
for V in ["Tupungatito", "PlanchonPeteroa", "Copahue", "LagunaDelMaule", "CarranLosVenados"]:
    s = pix[(pix.volcan == V) & (pix.dist_km <= 5)]
    P(f"{V}: pixeles {len(s)}; celda >=50 % agua {int((s.frac_agua >= .5).sum())}; "
      f"0 < agua < 50 % {int(((s.frac_agua > 0) & (s.frac_agua < .5)).sum())}; "
      f"solo agua en el 3x3 {int(((s.frac_agua == 0) & (s.frac_agua_3x > 0)).sum())}")
    r = rec[rec.volcan == V]
    o = r[(r.clase_pico == "orilla")]
    P(f"   pasadas con pico a la orilla: {len(o)}; a <=5 km {int((o.dist_km <= 5).sum())}; "
      f">=1 MW {int((o.vrp_mw >= 1).sum())}; >=1 MW y <=5 km {int(((o.vrp_mw >= 1) & (o.dist_km <= 5)).sum())}")

P("== Agua alrededor del punto de cada volcan (JRC, ocurrencia >=50 %) ==")
with open(os.path.join(REPO, "volcanoes.yaml"), encoding="utf-8") as fh:
    vy = yaml.safe_load(fh)["volcanoes"]
for v in vy:
    f = os.path.join(D, "cache_jrc", f"{v['name']}.npz")
    if not os.path.exists(f):
        continue
    z = np.load(f)
    A = z["a"]; W, N, res = z["t"]
    la, lo = float(v["lat"]), float(v["lon"])
    rr = int((N - la) / res); cc = int((lo - W) / res)

    def fr(km):
        h = int(km / 2 / 0.0278)
        s = A[rr - h:rr + h, cc - h:cc + h]
        return ((s >= 50) & (s <= 100)).mean()
    f1, f10, fall = fr(1.0), fr(10.0), ((A >= 50) & (A <= 100)).mean()
    P(f"{v['name']:22s} celda 1 km {f1:.2f}  cuadro 10 km {f10:.2f}  ventana {fall:.3f}")

P("== Laguna del Maule: detector anterior (abril 2026) contra la via la misma semana ==")
d = json.load(open(os.path.join(REPO, "data/mirova_equivalent/LagunaDelMaule.json"), encoding="utf-8"))["records"]
det = [r for r in d if r.get("anomaly_pixels")]
vr = sorted(r.get("vrp_mw") or 0 for r in det)
P(f"anterior: via={set(bool(r.get('via_codigo_mirova')) for r in d)}; records {len(d)} "
  f"({min(r['datetime_utc'] for r in d)} a {max(r['datetime_utc'] for r in d)}); detecciones {len(det)}; "
  f"VRP mediana {np.median(vr):.1f} MW, max {max(vr):.1f}; pixeles max {max(len(r['anomaly_pixels']) for r in det)}")
h = json.load(open(os.path.join(REPO, "data/historia_34/LagunaDelMaule.json"), encoding="utf-8"))["records"]
s = json.load(open(os.path.join(REPO, "data/sombra_34/LagunaDelMaule.json"), encoding="utf-8"))["records"]
P(f"via historia: records {len(h)}, nocturnos {sum(1 for r in h if (r.get('solar_zenith_deg') or 0) > 90)}; "
  f"sombra: records {len(s)}, nocturnos {sum(1 for r in s if (r.get('solar_zenith_deg') or 0) > 90)}")
ab = [r for r in h if "2026-04-17" <= r["datetime_utc"] <= "2026-04-24 23:59" and r.get("anomaly_pixels")]
P("via 2026-04-17 a 2026-04-24: " + "; ".join(f"{r['datetime_utc']} {r['sensor']} {r['vrp_mw']} MW" for r in ab))
P("sombra con deteccion: " + "; ".join(f"{r['datetime_utc']} {r['sensor']} {r['vrp_mw']} MW "
                                         f"{r.get('final_hotspot_dist_km')} km" for r in s if r.get("anomaly_pixels")))

with open(os.path.join(D, "verificaciones.txt"), "w", encoding="utf-8") as fh:
    fh.write("\n".join(out))
print("\n".join(out))
