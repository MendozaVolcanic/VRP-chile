# -*- coding: utf-8 -*-
"""S126 — ?desde que pixel sale la magnitud que publicamos HOY?

Hallazgo colateral del A/B, en el CONTROL (o sea: en la configuracion
operacional, sin tocar ningun flag). En Villarrica el pixel que sobrevive al
filtro contextual y produce `primary_cluster.vrp_mw` esta a 2,79 km del crater
(p25 2,64 / p75 2,91), con rumbo 267 grados —al oeste—, y cae dentro del anillo
de fondo [1,5-3] km el 94 % de las noches. Su temperatura esta a ~0,5 K del
fondo de la escena, a veces por debajo.

Antes de darle peso hay que separar dos lecturas MUY distintas:

  · Si en las noches que MIROVA confirma el pixel esta EN el crater y solo se
    va a 2,8 km en las noches tranquilas, entonces el pipeline mide bien cuando
    hay senal, y lo que sobra son artefactos de noche quieta.
  · Si esta a 2,8 km TAMBIEN en las noches con actividad confirmada, entonces la
    magnitud de VIIRS375 en los nevados se esta midiendo fuera del crater
    siempre, y el ratio contra MIROVA es una coincidencia numerica.

Es la misma distincion de A72: artefacto que no deberiamos generar, contra senal
real sub-umbral. Y de A61: auditar deteccion exige el eje ESPACIAL, no solo el
numero.

Persiste en 08_donde_medimos_hoy.json.
"""
import csv, io, json, math, os, statistics as st, sys
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
VENTANA = ("2026-06-25", "2026-08-24")
VOLS = {
    "Villarrica":          {"vent": (-39.420227, -71.939876), "reg": "nevado", "inner": 5},
    "PlanchonPeteroa":     {"vent": (-35.241099, -70.573345), "reg": "nevado", "inner": 3},
    "PuyehueCordonCaulle": {"vent": (-40.525499, -72.146137), "reg": "nevado", "inner": 20},
    "Lascar":              {"vent": (-23.362930, -67.731416), "reg": "desierto", "inner": 5},
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


def noches_mirova():
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
            out[vol][f[:10]] = max(out[vol].get(f[:10], 0), v)
    return out


def resumen(xs):
    if not xs:
        return None
    xs = sorted(xs)
    return {"n": len(xs), "mediana": round(st.median(xs), 3),
            "p25": round(xs[len(xs) // 4], 3), "p75": round(xs[3 * len(xs) // 4], 3)}


mir = noches_mirova()
res = {"ventana": list(VENTANA), "profile": "control = flags operacionales", "por_volcan": {}}

print("?DESDE QUE PIXEL SALE LA MAGNITUD QUE PUBLICAMOS HOY?")
print("control (flags operacionales), VIIRS375 nocturno, %s a %s\n" % VENTANA)
print("%-22s %-16s %5s %9s %9s %9s %10s" %
      ("volcan", "noches", "n", "d_med km", "% >1.5km", "bt-t_bg K", "vrp MW"))

for vol, cfg in VOLS.items():
    recs = json.load(open(os.path.join(ROOT, "data", "_s125_mag_control", vol + ".json"),
                          encoding="utf-8"))["records"]
    grupos = {"MIROVA confirma": [], "sin alerta": []}
    for r in recs:
        s = (r.get("sensor") or "").upper()
        if "VIIRS" not in s or "750" in s or "MODIS" in s:
            continue
        f = r["datetime_utc"][:10]
        if not (VENTANA[0] <= f <= VENTANA[1]):
            continue
        sz = r.get("solar_zenith_deg")
        if sz is not None and sz < 90:
            continue
        pc = r.get("primary_cluster") or {}
        ap = r.get("anomaly_pixels") or []
        if not pc.get("vrp_mw") or not ap:
            continue
        # centroide del cluster que se publica
        d = hav((pc["centroid_lat"], pc["centroid_lon"]), cfg["vent"])
        # contraste del pixel mas caliente del cluster contra el fondo de esa noche
        tbg = r.get("t_bg_k")
        bts = [p["bt_k"] for p in ap if p.get("bt_k") is not None]
        contraste = (max(bts) - tbg) if (bts and tbg) else None
        g = "MIROVA confirma" if f in mir.get(vol, {}) else "sin alerta"
        grupos[g].append({"d": d, "c": contraste, "v": pc["vrp_mw"]})

    d_vol = {}
    for g, xs in grupos.items():
        if not xs:
            continue
        ds = [x["d"] for x in xs]
        cs = [x["c"] for x in xs if x["c"] is not None]
        vs = [x["v"] for x in xs]
        d_vol[g] = {"dist_km": resumen(ds), "contraste_k": resumen(cs), "vrp_mw": resumen(vs),
                    "pct_mas_de_1_5km": round(100 * sum(1 for x in ds if x > 1.5) / len(ds), 1),
                    "pct_dentro_1km": round(100 * sum(1 for x in ds if x <= 1.0) / len(ds), 1)}
        e = d_vol[g]
        print("%-22s %-16s %5d %9.2f %8.0f%% %9s %10s"
              % (vol, g, len(ds), e["dist_km"]["mediana"], e["pct_mas_de_1_5km"],
                 e["contraste_k"]["mediana"] if cs else "-", e["vrp_mw"]["mediana"]))
    res["por_volcan"][vol] = {"regimen": cfg["reg"], "grupos": d_vol}

print("\nLECTURA")
for vol, d in res["por_volcan"].items():
    g = d["grupos"]
    if "MIROVA confirma" not in g:
        continue
    dm = g["MIROVA confirma"]["dist_km"]["mediana"]
    print("  %-22s con actividad confirmada medimos a %.2f km del crater (%.0f%% mas alla de 1,5 km)"
          % (vol, dm, g["MIROVA confirma"]["pct_mas_de_1_5km"]))

dest = os.path.join(os.path.dirname(__file__), "08_donde_medimos_hoy.json")
json.dump(res, open(dest, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("\npersistido en", dest)
