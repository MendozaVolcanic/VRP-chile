# -*- coding: utf-8 -*-
"""S126 — que haria la corona de la Eq.6, estimado sobre los datos EN DISCO.

Coppola 2016a SP426.5, Eq.6, verbatim:

    "L4bk is estimated from the arithmetic mean of all the pixels surrounding
     the active one (or around the active cluster)."

O sea el fondo de MIROVA es la corona INMEDIATA al cluster activo. Nuestro
VIIRS375 usa en cambio un anillo fijo [1,5-3] km al crater que solapa el 75 %
del ROI que mide (fondo autorreferente, ver docs/S126_COSTO_FILTRO_CONTEXTUAL.md).
El helper `cluster_corona_background` (vrp_regimes.py:109) ya implementa la Eq.6
y esta cableado SOLO en MODIS (process_modis.py:1049).

POR QUE LA CORONA DEBERIA DISCRIMINAR (la prediccion, escrita antes de mirar):

  · Una FLUCTUACION DE FONDO tiene vecinos a su misma temperatura -> el fondo
    local sube hasta el propio pixel -> dL ~ 0 -> el artefacto se desploma.
  · Un FOCO SUB-PIXEL REAL tiene vecinos genuinamente mas frios -> dL sobrevive.

Es el eje ESPACIAL/contextual, el unico que A83 encontro capaz de separar
cat-b real de artefacto. Un anillo fijo al crater no puede hacerlo: mide lo
mismo tenga o no tenga foco debajo.

SESGO CONOCIDO DE ESTA ESTIMACION (declarado antes del resultado): la corona se
estima con los `anomaly_pixels` del brazo E, y esos son SOLO los pixeles con
vrp>0, o sea la mitad CALIENTE del disco (anomaly_pixels.py:31). El t_bk asi
estimado queda sesgado hacia arriba -> dL menor -> **la VRP que sale es una COTA
INFERIOR** de la que daria la corona real. Por eso:
  · si un foco REAL sobrevive incluso con esta cota, sobrevive de verdad;
  · si un artefacto se desploma, es consistente pero NO concluyente — eso lo
    decide el reproceso.

Persiste en 10_corona_eq6_estimacion.json.
"""
import csv, io, json, math, os, statistics as st, sys
from collections import defaultdict

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
from pipeline.process_viirs import bt_to_spectral_radiance, I04_LAMBDA, WOOSTER_COEFF

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
VENTANA = ("2026-06-25", "2026-08-24")
A_PIX_M2 = 140625.0        # I-band nadir (scan_geometry.py:208), nadir-fijo ON
K_MW = A_PIX_M2 * WOOSTER_COEFF / 1e6
CORONA_R_KM = 0.6          # 8-vecinos a 375 m: 0,375 lado / 0,53 diagonal
MIN_CORONA = 4             # igual que LOCAL_CLUSTER_MAG_MIN_CORONA

VOLS = {
    "Villarrica":          {"vent": (-39.420227, -71.939876), "reg": "nevado"},
    "PlanchonPeteroa":     {"vent": (-35.241099, -70.573345), "reg": "nevado"},
    "PuyehueCordonCaulle": {"vent": (-40.525499, -72.146137), "reg": "nevado"},
    "Lascar":              {"vent": (-23.362930, -67.731416), "reg": "desierto"},
}
ALIAS = {
    "Villarrica": {"Villarrica"},
    "PlanchonPeteroa": {"PlanchonPeteroa", "Planchon-Peteroa", "Planchon Peteroa"},
    "Lascar": {"Lascar", "Láscar"},
    "PuyehueCordonCaulle": {"PuyehueCordonCaulle", "Puyehue-Cordon Caulle",
                            "Puyehue Cordon Caulle", "Puyehue-Cordón Caulle"},
}


def hav(a, b):
    (la1, lo1), (la2, lo2) = a, b
    p = math.pi / 180.0
    h = (math.sin((la2 - la1) * p / 2) ** 2 +
         math.cos(la1 * p) * math.cos(la2 * p) * math.sin((lo2 - lo1) * p / 2) ** 2)
    return 2 * 6371.0 * math.asin(math.sqrt(h))


def resumen(xs):
    if not xs:
        return None
    xs = sorted(xs)
    return {"n": len(xs), "mediana": round(st.median(xs), 4),
            "p25": round(xs[len(xs) // 4], 4), "p75": round(xs[3 * len(xs) // 4], 4)}


def mirova_noches():
    out = defaultdict(dict)
    for fname in ("latest_consolidado.csv",
                  "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv"):
        p = os.path.join(ROOT, fname)
        if not os.path.exists(p):
            continue
        for r in csv.DictReader(open(p, encoding="utf-8", errors="replace")):
            nom = (r.get("Volcan") or "").strip()
            vol = next((v for v, al in ALIAS.items() if nom in al), None)
            if vol is None or "ALERTA" not in (r.get("Tipo_Registro") or ""):
                continue
            if (r.get("Sensor") or "").strip().upper() != "VIIRS375":
                continue
            f = (r.get("Fecha_Satelite_UTC") or "")
            if not (VENTANA[0] <= f[:10] <= VENTANA[1]):
                continue
            if not (3 <= int(f[11:13] or 12) <= 9):
                continue
            try:
                v = float(r.get("VRP_MW") or 0)
            except ValueError:
                continue
            if v > 0:
                out[vol][f[:10]] = max(out[vol].get(f[:10], 0), v)
    return out


def cargar(subdir, vol):
    recs = json.load(open(os.path.join(ROOT, "data", subdir, vol + ".json"),
                          encoding="utf-8"))["records"]
    out = {}
    for r in recs:
        s = (r.get("sensor") or "").upper()
        if "VIIRS" not in s or "750" in s or "MODIS" in s:
            continue
        if not (VENTANA[0] <= r["datetime_utc"][:10] <= VENTANA[1]):
            continue
        sz = r.get("solar_zenith_deg")
        if sz is not None and sz < 90:
            continue
        out[(r["datetime_utc"], r.get("sensor"))] = r
    return out


mir = mirova_noches()
res = {"ventana": list(VENTANA), "eq": "Coppola 2016a Eq.6",
       "sesgo": "cota INFERIOR (la corona se estima con la mitad caliente del disco)",
       "corona_r_km": CORONA_R_KM, "min_corona": MIN_CORONA, "por_volcan": {}}

print("ESTIMACION READ-ONLY DE LA CORONA Eq.6 — cota INFERIOR")
print("VIIRS375 nocturno, %s a %s   corona r<%.2f km, min %d px\n" % (VENTANA + (CORONA_R_KM, MIN_CORONA)))
print("%-22s %-16s %5s %11s %11s %10s %9s" %
      ("volcan", "noches", "n", "VRP hoy", "VRP corona", "corona/hoy", "n_corona"))

for vol, cfg in VOLS.items():
    c, e = cargar("_s125_mag_control", vol), cargar("_s125_viirs_e", vol)
    grupos = defaultdict(list)
    for k in sorted(set(c) & set(e)):
        pc = (c[k].get("primary_cluster") or {})
        ap_c = c[k].get("anomaly_pixels") or []
        if not pc.get("vrp_mw") or not ap_c:
            continue
        cluster = [(p["lat"], p["lon"], p["bt_k"]) for p in ap_c if p.get("bt_k")]
        if not cluster:
            continue
        pos_cluster = {(round(p[0], 5), round(p[1], 5)) for p in cluster}
        # corona: pixeles de E cercanos al cluster, excluyendo el cluster mismo
        corona = []
        for p in (e[k].get("anomaly_pixels") or []):
            if (round(p["lat"], 5), round(p["lon"], 5)) in pos_cluster:
                continue
            if p.get("bt_k") is None:
                continue
            if min(hav((p["lat"], p["lon"]), (q[0], q[1])) for q in cluster) <= CORONA_R_KM:
                corona.append(p["bt_k"])
        if len(corona) < MIN_CORONA:
            continue                                  # degradada: el caller cae al regional
        t_bk = float(np.mean(corona))
        L_bk = float(bt_to_spectral_radiance(np.float64(t_bk), I04_LAMBDA))
        vrp_corona = 0.0
        for (_, _, bt) in cluster:
            L = float(bt_to_spectral_radiance(np.float64(bt), I04_LAMBDA))
            vrp_corona += K_MW * max(L - L_bk, 0.0)
        g = "MIROVA confirma" if k[0][:10] in mir.get(vol, {}) else "sin alerta"
        grupos[g].append({"hoy": pc["vrp_mw"], "corona": vrp_corona,
                          "n_corona": len(corona),
                          "mirova": mir.get(vol, {}).get(k[0][:10])})

    d_vol = {}
    for g in ("MIROVA confirma", "sin alerta"):
        xs = grupos.get(g) or []
        if not xs:
            continue
        hoy = [x["hoy"] for x in xs]
        cor = [x["corona"] for x in xs]
        rat = [x["corona"] / x["hoy"] for x in xs if x["hoy"]]
        d_vol[g] = {"n": len(xs), "vrp_hoy": resumen(hoy), "vrp_corona": resumen(cor),
                    "corona_sobre_hoy": resumen(rat),
                    "n_corona": resumen([x["n_corona"] for x in xs]),
                    "pct_que_se_desploma_bajo_0_01MW": round(
                        100 * sum(1 for v in cor if v < 0.01) / len(cor), 1)}
        # contra MIROVA, solo donde hay referencia
        ref = [(x["corona"] / x["mirova"]) for x in xs if x.get("mirova")]
        if ref:
            d_vol[g]["ratio_corona_sobre_mirova"] = resumen(ref)
            d_vol[g]["ratio_hoy_sobre_mirova"] = resumen(
                [(x["hoy"] / x["mirova"]) for x in xs if x.get("mirova")])
        print("%-22s %-16s %5d %11.4f %11.4f %10.3f %9.1f"
              % (vol, g, len(xs), d_vol[g]["vrp_hoy"]["mediana"],
                 d_vol[g]["vrp_corona"]["mediana"],
                 d_vol[g]["corona_sobre_hoy"]["mediana"],
                 d_vol[g]["n_corona"]["mediana"]))
    res["por_volcan"][vol] = {"regimen": cfg["reg"], "grupos": d_vol}

print("\n" + "=" * 78)
print("?SE DESPLOMA EL ARTEFACTO Y SOBREVIVE EL FOCO? (%% de records bajo 0,01 MW)")
print("%-22s %18s %18s" % ("volcan", "MIROVA confirma", "sin alerta"))
for vol, d in res["por_volcan"].items():
    g = d["grupos"]
    a = g.get("MIROVA confirma", {}).get("pct_que_se_desploma_bajo_0_01MW")
    b = g.get("sin alerta", {}).get("pct_que_se_desploma_bajo_0_01MW")
    print("%-22s %17s%% %17s%%" % (vol, a, b))

print("\nRATIO CONTRA MIROVA en noches confirmadas (hoy -> corona, cota inferior)")
for vol, d in res["por_volcan"].items():
    g = d["grupos"].get("MIROVA confirma") or {}
    if "ratio_corona_sobre_mirova" in g:
        print("  %-22s %.3f -> %.3f  (n=%d)"
              % (vol, g["ratio_hoy_sobre_mirova"]["mediana"],
                 g["ratio_corona_sobre_mirova"]["mediana"],
                 g["ratio_corona_sobre_mirova"]["n"]))

dest = os.path.join(os.path.dirname(__file__), "10_corona_eq6_estimacion.json")
json.dump(res, open(dest, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("\npersistido en", dest)
