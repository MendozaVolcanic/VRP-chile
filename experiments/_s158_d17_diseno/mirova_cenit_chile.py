# -*- coding: utf-8 -*-
"""S158: ¿el VRP que publica MIROVA en VIIRS 375 depende del cenit? Versión normalizada en el tiempo, por volcán.

POR QUÉ: S130 (`docs/s130/GRADIENTE_CENITAL.md`) concluyó que la magnitud de MIROVA es plana con el ángulo mirando
medianas por tramo sobre una población que mezcla volcanes. En Vulcano (`jepv6_cenit.py`) el VRP de MIROVA, relativo
a la mediana móvil de su serie, cae de ~1,25 a ~0,72 entre nadir y > 50°. Si en Chile pasa lo mismo, la parte del
déficit que D17 podría cerrar es menor de lo que se suponía: replicar MIROVA es replicar también su caída.

Método: alertas VIIRS 375 de MIROVA (consolidado vivo + OCR del snapshot), VRP > 0,05 MW (regla SN, D-9), noche
(03 a 09 UTC, A76), desde el 2026-03-01 (A119). Cenit: el de nuestro record de la misma pasada (|Δt| ≤ 3 min,
I-band). Cruce: donde el OCR trae Zenith_Sat_deg se compara. VRP relativo = VRP / mediana móvil de 61 días del mismo
volcán (mínimo 5 alertas). Sesgo conocido: cerca del umbral de detección, en oblicuo sólo pasan las pasadas fuertes,
lo que sube el VRP oblicuo; una caída observada es entonces una cota inferior de la caída real.
Uso: python -I mirova_cenit_chile.py <raiz del repo> [--solo-tabla] [--v750]
Con --v750 mide VIIRS 750 (en el CSV de MIROVA se llama "VIIRS"; en nuestros records, sensor *_750, y se publica el
cúmulo, sin núcleo F5').
Con --solo-tabla se lee sólo el consolidado (A119: antes del 2026-06-13 decide la tabla; el OCR se informa aparte).
"""
import csv, json, os, sys
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

ROOT = sys.argv[1]
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from calidad_referencia_mirova import avisar  # noqa: E402

DESDE, HASTA = "2026-03-01", "2026-10-20"
V750 = "--v750" in sys.argv
SENSOR_MIROVA = "VIIRS" if V750 else "VIIRS375"
def es_nuestro(s):
    s = str(s or "").upper()
    return "VIIRS" in s and (("750" in s) == V750)
print("sensor:", "VIIRS 750" if V750 else "VIIRS 375")
avisar(DESDE, HASTA)
ALIAS = {"Nevados de Chillan": "NevadosDeChillan", "Puyehue-Cordon Caulle": "PuyehueCordonCaulle",
         "Planchon-Peteroa": "PlanchonPeteroa"}
filas = {}
FUENTES = ["latest_consolidado.csv"] + ([] if "--solo-tabla" in sys.argv else ["data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv"])
print("fuentes:", FUENTES)
for f in FUENTES:
    for r in csv.DictReader(open(os.path.join(ROOT, f), encoding="utf-8", errors="replace")):
        if (r.get("Sensor") or "").strip() != SENSOR_MIROVA or "ALERTA" not in (r.get("Tipo_Registro") or ""):
            continue
        t = (r.get("Fecha_Satelite_UTC") or "").strip()
        if not (DESDE <= t[:10] <= HASTA) or not (3 <= int(t[11:13] or 12) <= 9):
            continue
        try:
            v = float(r["VRP_MW"])
        except (TypeError, ValueError):
            continue
        if v <= (0.0 if V750 else 0.05):   # la regla SN (D-9) es de VIIRS 375
            continue
        vol = ALIAS.get(r["Volcan"].strip(), r["Volcan"].strip())
        z_ocr = r.get("Zenith_Sat_deg")
        k = (vol, t[:16])
        prev = filas.get(k)
        zo = float(z_ocr) if z_ocr not in (None, "", "nan") else None
        if prev is None or v > prev["vrp"]:
            filas[k] = {"vol": vol, "t": datetime.strptime(t[:16], "%Y-%m-%d %H:%M"), "vrp": v,
                        "z_ocr": zo if zo is not None else (prev or {}).get("z_ocr")}
        elif zo is not None and prev.get("z_ocr") is None:
            prev["z_ocr"] = zo

cen = {}
for vol in {f["vol"] for f in filas.values()}:
    p = os.path.join(ROOT, "data", "mirova_equivalent", f"{vol}.json")
    if not os.path.exists(p):
        continue
    d = json.load(open(p, encoding="utf-8"))
    recs = d.get("records", d) if isinstance(d, dict) else d
    lst = []
    for r in recs:
        if not es_nuestro(r.get("sensor")) or r.get("sensor_zenith_deg") is None:
            continue
        try:
            lst.append((datetime.strptime(str(r.get("datetime_utc") or r.get("datetime"))[:16], "%Y-%m-%d %H:%M"),
                        float(r["sensor_zenith_deg"])))
        except ValueError:
            continue
    cen[vol] = sorted(lst)

out = []
for f in filas.values():
    lst = cen.get(f["vol"], [])
    best = min(lst, key=lambda x: abs(x[0] - f["t"]), default=None)
    if best and abs(best[0] - f["t"]) <= timedelta(minutes=3):
        out.append({**f, "cenit": best[1]})
df = pd.DataFrame(out).sort_values("t")
print(f"alertas nocturnas con cenit pareado: {len(df)} de {len(filas)}")
chk = df.dropna(subset=["z_ocr"])
if len(chk):
    print(f"cruce con Zenith_Sat_deg del OCR: n {len(chk)}, |diferencia| mediana {np.median(np.abs(chk.cenit - chk.z_ocr)):.2f} grados, p95 {np.percentile(np.abs(chk.cenit - chk.z_ocr), 95):.2f}")
partes = []
for vol, g in df.groupby("vol"):
    s = g.set_index("t")["vrp"]
    g = g.copy()
    g["rel"] = (s / s.rolling("61D", center=True, min_periods=5).median()).values
    partes.append(g)
df = pd.concat(partes)
cortes = [0, 20, 40, 50, 75]
df["tramo"] = pd.cut(df["cenit"], cortes)
cats = df["tramo"].cat.categories
print("\nvolcán | n | " + " | ".join(str(c) for c in cats) + " | Spearman cenit-rel")
for vol, g in list(df.groupby("vol")) + [("TODOS", df)]:
    g = g.dropna(subset=["rel"])
    if len(g) < 20:
        continue
    med = []
    for c in cats:
        x = g.rel[g.tramo == c]
        med.append(f"{x.median():.2f} ({len(x)})" if len(x) >= 5 else f"-- ({len(x)})")
    print(f"{vol:20s} | {len(g):4d} | " + " | ".join(med) + f" | {g.cenit.corr(g.rel, method='spearman'):+.3f}")

# --- Nuestra magnitud publicada en las mismas pasadas (detector K: #883 reemplazó todo el histórico) ---
# Aproximación declarada de `mirovaEqVrpCore` (frontend/index.html l. 1162 y 1295): cúmulo de cumbre con centroide
# dentro de inner_radius_km; se publica f5_core_vrp_mw si existe, si no primary_cluster.vrp_mw. No decide qué se
# publica (eso pide node, A97): sólo da la magnitud de las pasadas que ya tienen alerta de MIROVA.
import yaml
inner = {v["name"]: v.get("inner_radius_km", 10) for v in yaml.safe_load(open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8"))["volcanoes"]}
pub = {}
for vol in df.vol.unique():
    d = json.load(open(os.path.join(ROOT, "data", "mirova_equivalent", f"{vol}.json"), encoding="utf-8"))
    recs = d.get("records", d) if isinstance(d, dict) else d
    lst = []
    for r in recs:
        pc = r.get("primary_cluster") or {}
        if not es_nuestro(r.get("sensor")) or not pc:
            continue
        if r.get("distance_class") != "summit" or (pc.get("centroid_dist_km") or 0) > inner.get(vol, 10):
            continue
        v = r.get("f5_core_vrp_mw") if (not V750 and isinstance(r.get("f5_core_vrp_mw"), (int, float))) else pc.get("vrp_mw")
        if v and v > 0:
            lst.append((datetime.strptime(str(r.get("datetime_utc") or r.get("datetime"))[:16], "%Y-%m-%d %H:%M"), float(v)))
    pub[vol] = lst
def nuestro(row):
    lst = pub.get(row["vol"], [])
    b = min(lst, key=lambda x: abs(x[0] - row["t"]), default=None)
    return b[1] if b and abs(b[0] - row["t"]) <= timedelta(minutes=3) else np.nan
df["nuestro"] = df.apply(nuestro, axis=1)
df["razon"] = df["nuestro"] / df["vrp"]
print(f"\npasadas con alerta de MIROVA donde publicamos magnitud: {df.nuestro.notna().sum()} de {len(df)}")
print("razón nuestra/MIROVA mediana por tramo de cenit (n)")
print("volcán | " + " | ".join(str(c) for c in cats) + " | S = R(>40)/R(<=40)")
for vol, g in list(df.groupby("vol")) + [("TODOS", df)]:
    g = g.dropna(subset=["razon"])
    if len(g) < 20:
        continue
    med = [f"{g.razon[g.tramo == c].median():.2f} ({(g.tramo == c).sum()})" if (g.tramo == c).sum() >= 5 else f"-- ({(g.tramo == c).sum()})" for c in cats]
    lo, hi = g.razon[g.cenit <= 40].median(), g.razon[g.cenit > 40].median()
    print(f"{vol:20s} | " + " | ".join(med) + f" | {hi / lo:.2f}")
