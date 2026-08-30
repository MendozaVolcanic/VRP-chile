# -*- coding: utf-8 -*-
"""S128 Fase 2 · sonda P2 — CONTRASTE AL CRATER EN LA IMAGEN DE MIROVA.

El fenomeno primero. MIROVA publica, por volcan y sensor, la escena de radiancia
MIR de su ultima pasada. Si en el crater hubiera material caliente, ese pixel
tendria que destacar sobre el resto de la escena: mas radiancia MIR que el terreno
de alrededor. Si la escena de MIROVA NO muestra ningun realce sobre el crater y
nosotros, sobre esa MISMA pasada, publicamos un VRP > 0, entonces nuestro numero no
esta respaldado por la imagen de la referencia.

Es la primera vez en 127 sesiones que un falso positivo nuestro se puede afirmar con
evidencia EXTERNA en vez de con nuestro propio juicio.

CRITERIO PRE-REGISTRADO (se fija ANTES de mirar los resultados, A66):
  · La unidad de la banda del TIF NO esta declarada en ningun tag. Por eso el
    contraste se mide ADIMENSIONAL: z = (valor_crater - mediana_escena) / sigma_MAD.
    Asi la conclusion no hereda la incertidumbre de la unidad.
  · "Hay contraste al crater" := z >= 5 en la ventana 3x3 centrada en el crater.
    5 es el N-sigma summit nocturno de Coppola 2016a Tabla 1, que es el umbral con
    que la propia MIROVA decide que un pixel es anomalo. Usar el suyo, no uno nuevo.
  · Se reportan tambien z>=3 y z>=10 para que se vea la sensibilidad al corte.
  · Emparejamiento por PASADA (mismo volcan, mismo bucket de sensor, timestamp a
    menos de 45 min), no por noche: una noche puede tener 2-3 pasadas y mezclarlas
    es lo que inflo el deficit 2,5x en S126.

Read-only. Escribe solo su JSON.
"""
import collections
import csv
import datetime as dt
import io
import json
import math
import os
import re
import sys

import numpy as np
import rasterio
import yaml

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
ARCH = os.path.join(os.path.dirname(ROOT), "mirova-tif-archive")
sys.path.insert(0, os.path.join(ROOT, "experiments"))
from _s126_lib import VENTS, bucket                            # noqa: E402

ALIAS_TIF = {"ChillanNevadosde": "NevadosDeChillan"}
SEN_TIF = {"MODIS": "modis", "VIIRS750": "v750", "VIIRS375": "v375"}
VENTANA = ("2026-05-08", "2026-05-20")
Z_CORTES = (3.0, 5.0, 10.0)
TOL_MIN = 45


def ts_de_path(p):
    """20260508_214337_MODIS.tif -> datetime UTC."""
    m = re.search(r"(\d{8})_(\d{6})", os.path.basename(p))
    if not m:
        return None
    return dt.datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M%S")


# ── 1. Medir el contraste al crater en CADA escena de MIROVA ────────────────
escenas = []
rows = list(csv.DictReader(open(os.path.join(ARCH, "index.csv"), encoding="utf-8")))
vistos = set()
for r in rows:
    if r["tif_path"] in vistos:
        continue
    vistos.add(r["tif_path"])
    vol = ALIAS_TIF.get(r["volcano"], r["volcano"])
    if vol not in VENTS:
        continue
    p = os.path.join(ARCH, r["tif_path"].replace("/", os.sep))
    if not os.path.exists(p):
        continue
    ts = ts_de_path(p)
    if ts is None:
        continue
    try:
        with rasterio.open(p) as ds:
            a = ds.read(1).astype("float64")
            fila, col = ds.index(VENTS[vol][1], VENTS[vol][0])
    except Exception as e:                                     # noqa: BLE001
        escenas.append({"vol": vol, "sensor": SEN_TIF[r["sensor"]], "error": str(e)[:80]})
        continue
    fin = np.isfinite(a)
    if ds.nodata is not None:
        fin &= a != ds.nodata
    if fin.sum() < 50 or not (0 <= fila < a.shape[0] and 0 <= col < a.shape[1]):
        continue
    v = a[fin]
    med = float(np.median(v))
    mad = float(np.median(np.abs(v - med)))
    sig = 1.4826 * mad
    # Ventana 3x3 al crater: el pixel exacto puede caer en el borde del cono.
    f0, f1 = max(0, fila - 1), min(a.shape[0], fila + 2)
    c0, c1 = max(0, col - 1), min(a.shape[1], col + 2)
    ven = a[f0:f1, c0:c1]
    ven = ven[np.isfinite(ven)]
    if ven.size == 0:
        continue
    pico = float(ven.max())
    z = (pico - med) / sig if sig > 0 else (math.inf if pico > med else 0.0)
    # Donde esta el maximo de TODA la escena (¿el calor esta en otro lado?)
    idx = np.unravel_index(np.nanargmax(np.where(fin, a, -np.inf)), a.shape)
    mlon, mlat = ds.xy(int(idx[0]), int(idx[1]))
    escenas.append({
        "vol": vol, "sensor": SEN_TIF[r["sensor"]], "ts": ts.isoformat(),
        "fecha": ts.date().isoformat(),
        "med": round(med, 4), "sigma_mad": round(sig, 5),
        "pico_crater": round(pico, 4), "z_crater": round(z, 2),
        "max_escena": round(float(a[fin].max()), 4),
        "z_max_escena": round((float(a[fin].max()) - med) / sig, 2) if sig > 0 else None,
        "dist_max_al_crater_km": round(
            111.32 * math.hypot(mlat - VENTS[vol][0],
                                (mlon - VENTS[vol][1]) * math.cos(math.radians(mlat))), 2),
    })

ok = [e for e in escenas if "z_crater" in e]
print("escenas medidas:", len(ok), "| con error:", len(escenas) - len(ok))

# ── 2. Nuestras detecciones en la MISMA ventana ─────────────────────────────
nuestros = collections.defaultdict(list)
for vol in VENTS:
    p = os.path.join(ROOT, "data", "mirova_equivalent", vol + ".json")
    if not os.path.exists(p):
        continue
    for rec in json.load(open(p, encoding="utf-8"))["records"]:
        d = rec.get("datetime_utc", "")[:10]
        if not (VENTANA[0] <= d <= VENTANA[1]):
            continue
        b = bucket(rec.get("sensor"))
        if b is None:
            continue
        try:
            t = dt.datetime.fromisoformat(rec["datetime_utc"].replace("Z", "").split("+")[0])
        except Exception:                                      # noqa: BLE001
            continue
        nuestros[(vol, b)].append({
            "ts": t,
            "vrp": (rec.get("primary_cluster") or {}).get("vrp_mw") or 0.0,
            "clase": rec.get("final_hotspot_distance_class") or rec.get("distance_class"),
            "dist": rec.get("final_hotspot_dist_km"),
        })

# ── 3. El cruce, PASADA a PASADA ───────────────────────────────────────────
pares, sin_pareja = [], 0
for e in ok:
    cand = nuestros.get((e["vol"], e["sensor"]), [])
    te = dt.datetime.fromisoformat(e["ts"])
    mejor, dmin = None, None
    for c in cand:
        dd = abs((c["ts"] - te).total_seconds()) / 60.0
        if dmin is None or dd < dmin:
            mejor, dmin = c, dd
    if mejor is None or dmin > TOL_MIN:
        sin_pareja += 1
        continue
    pares.append({**{k: e[k] for k in ("vol", "sensor", "ts", "fecha", "z_crater",
                                       "z_max_escena", "dist_max_al_crater_km")},
                  "delta_min": round(dmin, 1), "vrp_nuestro": round(mejor["vrp"], 4),
                  "clase": mejor["clase"], "dist_km": mejor["dist"]})

# ── 4. El veredicto, estratificado por volcan (regla S126) ─────────────────
tabla = {}
for vol in sorted(VENTS):
    e_v = [e for e in ok if e["vol"] == vol]
    p_v = [p for p in pares if p["vol"] == vol]
    fila = {
        "escenas_mirova": len(e_v),
        "escenas_con_contraste_al_crater": {str(k): sum(1 for e in e_v if e["z_crater"] >= k)
                                            for k in Z_CORTES},
        "z_crater_max_observado": round(max((e["z_crater"] for e in e_v), default=0), 2),
        "nuestros_records_en_ventana": sum(len(v) for (vv, _), v in nuestros.items()
                                           if vv == vol),
        "nuestros_con_vrp_positivo": sum(1 for (vv, _), v in nuestros.items() if vv == vol
                                         for r in v if r["vrp"] > 0),
        "pasadas_emparejadas": len(p_v),
    }
    # El nudo: pasadas donde NOSOTROS publicamos VRP>0 y la imagen de MIROVA no
    # muestra contraste al crater ni siquiera al corte mas laxo (z>=3).
    sin_apoyo = [p for p in p_v if p["vrp_nuestro"] > 0 and p["z_crater"] < 3.0]
    con_apoyo = [p for p in p_v if p["vrp_nuestro"] > 0 and p["z_crater"] >= 5.0]
    fila["emparejadas_vrp_pos"] = sum(1 for p in p_v if p["vrp_nuestro"] > 0)
    fila["vrp_pos_SIN_contraste_z3"] = len(sin_apoyo)
    fila["vrp_pos_CON_contraste_z5"] = len(con_apoyo)
    fila["vrp_mediano_sin_apoyo"] = (round(float(np.median([p["vrp_nuestro"]
                                                            for p in sin_apoyo])), 4)
                                     if sin_apoyo else None)
    fila["vrp_mediano_con_apoyo"] = (round(float(np.median([p["vrp_nuestro"]
                                                            for p in con_apoyo])), 4)
                                     if con_apoyo else None)
    tabla[vol] = fila

R = {"_meta": {"ventana": VENTANA, "tolerancia_emparejado_min": TOL_MIN,
               "criterio": "z = (pico 3x3 al crater - mediana escena) / (1,4826*MAD); "
                           "corte principal z>=5 = N-sigma summit nocturno Coppola 2016a",
               "escenas_medidas": len(ok), "pares": len(pares),
               "escenas_sin_pasada_nuestra": sin_pareja},
     "por_volcan": tabla, "pares": pares, "escenas": ok}
out = os.path.join(AQUI, "02_contraste_al_crater.json")
json.dump(R, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("escrito:", out)

print("\n%-22s %5s %6s %6s %6s | %6s %7s %8s %8s" % (
    "volcan", "esc", "z>=3", "z>=5", "z>=10", "pares", "vrp>0", "SIN_ap", "CON_ap"))
for v, f in tabla.items():
    c = f["escenas_con_contraste_al_crater"]
    print("%-22s %5d %6d %6d %6d | %6d %7d %8d %8d" % (
        v, f["escenas_mirova"], c["3.0"], c["5.0"], c["10.0"],
        f["pasadas_emparejadas"], f["emparejadas_vrp_pos"],
        f["vrp_pos_SIN_contraste_z3"], f["vrp_pos_CON_contraste_z5"]))
print("\nz_crater maximo observado por volcan:")
for v, f in tabla.items():
    print("  %-22s %8.2f   vrp_med sin apoyo=%s  con apoyo=%s" % (
        v, f["z_crater_max_observado"], f["vrp_mediano_sin_apoyo"],
        f["vrp_mediano_con_apoyo"]))
