# -*- coding: utf-8 -*-
"""S126 — el piso VRP: ?suprime senal real o suprime el artefacto?

S125 dejo el diagnostico hecho y la decision pendiente. Lo que documento:

  · Los papers NO lo justifican: Coppola 2016a tiene una clase de alerta explicita
    "Low < 1 MW". El criterio de MIROVA es de CONTRASTE contra el fondo; el VRP es
    una salida, nunca una compuerta.
  · Esta MAL APLICADO: store.py:466 lo aplica a `record["vrp_mw"]` (suma de escena)
    y NO a `primary_cluster.vrp_mw`, que es lo que grafica el dashboard.
  · El de MODIS es codigo muerto (0 de 12.152 suprimidos).
  · La justificacion del YAML esta falsada: decia "minimo observado" con n=1 y n=2;
    con n=1000 el minimo real de MIROVA es 0,010 en V375 y 0,090 en V750, o sea que
    los dos pisos quedaron POR ENCIMA del minimo que MIROVA publica.

Todo eso apunta a QUITARLO. Pero falta la pregunta que decide, y que nadie hizo:
**?que hay adentro de lo que suprime?**

S126 mostro que en los nevados el pipeline reporta, en las noches quietas, una
fluctuacion del fondo a ~2,8 km del crater con VRP ~0,045 MW — justo el orden del
piso de VIIRS375 (0,02). Si lo que el piso corta es mayormente ESO, entonces esta
haciendo un trabajo util por accidente, y quitarlo destaparia artefacto. Si en
cambio corta noches que MIROVA confirma, es un generador de falsos negativos.

Las dos lecturas llevan a decisiones opuestas, asi que hay que medirlo antes.

Se mide sobre `data/mirova_equivalent/` (lo que esta vivo), por sensor:
  · cuantos records piso el suelo (tienen `diag_vrp_floor_mw`);
  · de esos, cuantos igual muestran `primary_cluster.vrp_mw > 0` — o sea que el
    piso no los saco del dashboard, que es la incoherencia de S125;
  · cuantos caen en noches que MIROVA SI publico (costo de recall real);
  · a que distancia del crater estan (firma del artefacto vs firma del foco).

Persiste en 01_que_suprime_el_piso.json.
"""
import csv, io, json, math, os, statistics as st, sys
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.join(os.path.dirname(__file__), "..", "..")

VENTANA = ("2026-05-01", "2026-08-28")     # ventana amplia: el piso se evalua en toda la serie
VOLS = {
    "Villarrica":          (-39.420227, -71.939876),
    "PlanchonPeteroa":     (-35.241099, -70.573345),
    "Lascar":              (-23.362930, -67.731416),
    "PuyehueCordonCaulle": (-40.525499, -72.146137),
    "NevadosDeChillan":    (-36.868000, -71.378000),
    "Copahue":             (-37.856000, -71.183000),
    "Llaima":              (-38.692000, -71.729000),
    "Lastarria":           (-25.168000, -68.507000),
    "Isluga":              (-19.150000, -68.833000),
    "Chaiten":             (-42.833000, -72.646000),
    "Tupungatito":         (-33.400000, -69.800000),
}
ALIAS = {
    "Villarrica": {"Villarrica"},
    "PlanchonPeteroa": {"PlanchonPeteroa", "Planchon-Peteroa", "Planchon Peteroa"},
    "Lascar": {"Lascar", "Láscar"},
    "PuyehueCordonCaulle": {"PuyehueCordonCaulle", "Puyehue-Cordon Caulle",
                            "Puyehue Cordon Caulle", "Puyehue-Cordón Caulle"},
    "NevadosDeChillan": {"NevadosDeChillan", "Nevados de Chillan", "Nevados de Chillán"},
    "Copahue": {"Copahue"}, "Llaima": {"Llaima"}, "Lastarria": {"Lastarria"},
    "Isluga": {"Isluga"}, "Chaiten": {"Chaiten", "Chaitén"},
    "Tupungatito": {"Tupungatito"},
}


def bucket(s):
    s = (s or "").upper()
    if "MODIS" in s:
        return "modis"
    if "750" in s:
        return "v750"
    if "VIIRS" in s:
        return "v375"
    return None


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
    return {"n": len(xs), "mediana": round(st.median(xs), 3),
            "p25": round(xs[len(xs) // 4], 3), "p75": round(xs[3 * len(xs) // 4], 3)}


def mirova_noches():
    """(volcan, fecha, bucket) donde MIROVA publico ALERTA nocturna."""
    out = set()
    for f in ("latest_consolidado.csv",
              "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv"):
        p = os.path.join(ROOT, f)
        if not os.path.exists(p):
            continue
        for r in csv.DictReader(open(p, encoding="utf-8", errors="replace")):
            nom = (r.get("Volcan") or "").strip()
            vol = next((v for v, al in ALIAS.items() if nom in al), None)
            if vol is None or "ALERTA" not in (r.get("Tipo_Registro") or ""):
                continue
            b = {"VIIRS375": "v375", "VIIRS": "v750", "MODIS": "modis"}.get(
                (r.get("Sensor") or "").strip().upper())
            fe = (r.get("Fecha_Satelite_UTC") or "")
            if not b or not (VENTANA[0] <= fe[:10] <= VENTANA[1]):
                continue
            if not (3 <= int(fe[11:13] or 12) <= 9):
                continue
            out.add((vol, fe[:10], b))
    return out


mir = mirova_noches()
por_sensor = defaultdict(lambda: {"total": 0, "pisados": 0, "pisados_con_pc": 0,
                                  "pisados_en_noche_mirova": 0, "dist": [],
                                  "vrp_raw": [], "pc_vrp": []})
por_volcan = defaultdict(lambda: {"pisados": 0, "en_noche_mirova": 0})

for vol, vent in VOLS.items():
    p = os.path.join(ROOT, "data", "mirova_equivalent", vol + ".json")
    if not os.path.exists(p):
        continue
    for r in json.load(open(p, encoding="utf-8"))["records"]:
        b = bucket(r.get("sensor"))
        f = r["datetime_utc"][:10]
        if b is None or not (VENTANA[0] <= f <= VENTANA[1]):
            continue
        d = por_sensor[b]
        d["total"] += 1
        if r.get("diag_vrp_floor_mw") is None:
            continue
        d["pisados"] += 1
        por_volcan[vol]["pisados"] += 1
        d["vrp_raw"].append(r.get("diag_vrp_raw_mw") or 0)
        pc = r.get("primary_cluster") or {}
        if pc.get("vrp_mw"):
            d["pisados_con_pc"] += 1
            d["pc_vrp"].append(pc["vrp_mw"])
            if pc.get("centroid_lat") is not None:
                d["dist"].append(hav((pc["centroid_lat"], pc["centroid_lon"]), vent))
        if (vol, f, b) in mir:
            d["pisados_en_noche_mirova"] += 1
            por_volcan[vol]["en_noche_mirova"] += 1

res = {"ventana": list(VENTANA), "pisos": {"v375": 0.02, "v750": 0.15, "modis": 0.05},
       "por_sensor": {}, "por_volcan": dict(por_volcan)}

print("QUE SUPRIME EL PISO VRP — data operacional, %s a %s\n" % VENTANA)
print("%-8s %8s %9s %9s %14s %16s" %
      ("sensor", "records", "pisados", "% del tot", "con pc.vrp>0", "en noche MIROVA"))
for b in ("v375", "v750", "modis"):
    d = por_sensor.get(b)
    if not d or not d["total"]:
        continue
    res["por_sensor"][b] = {
        "records": d["total"], "pisados": d["pisados"],
        "pct_pisados": round(100 * d["pisados"] / d["total"], 2),
        "pisados_con_pc_vrp": d["pisados_con_pc"],
        "pisados_en_noche_mirova": d["pisados_en_noche_mirova"],
        "vrp_raw_suprimido": resumen(d["vrp_raw"]),
        "pc_vrp_que_sobrevive": resumen(d["pc_vrp"]),
        "dist_al_crater_km": resumen(d["dist"]),
    }
    e = res["por_sensor"][b]
    print("%-8s %8d %9d %8.2f%% %14d %16d"
          % (b, e["records"], e["pisados"], e["pct_pisados"],
             e["pisados_con_pc_vrp"], e["pisados_en_noche_mirova"]))

print("\n" + "=" * 78)
print("LA INCOHERENCIA: el piso apaga record.vrp_mw pero NO primary_cluster.vrp_mw")
for b, e in res["por_sensor"].items():
    if not e["pisados"]:
        continue
    pct = 100 * e["pisados_con_pc_vrp"] / e["pisados"]
    print("  %-6s de %d records pisados, %d (%.1f%%) siguen con pc.vrp>0 → el dashboard los muestra igual"
          % (b, e["pisados"], e["pisados_con_pc_vrp"], pct))
    if e["pc_vrp_que_sobrevive"]:
        print("         pc.vrp que sobrevive: mediana %.3f MW   (el piso es %.2f)"
              % (e["pc_vrp_que_sobrevive"]["mediana"], res["pisos"][b]))

print("\n?SENAL O ARTEFACTO? — distancia al crater de lo pisado, y coincidencia con MIROVA")
for b, e in res["por_sensor"].items():
    if not e["pisados"]:
        continue
    pct_mir = 100 * e["pisados_en_noche_mirova"] / e["pisados"]
    print("  %-6s dist al crater: %s" % (b, e["dist_al_crater_km"]))
    print("         en noches que MIROVA publico: %d de %d (%.1f%%)"
          % (e["pisados_en_noche_mirova"], e["pisados"], pct_mir))

print("\nPOR VOLCAN (records pisados / de esos, en noche con alerta MIROVA)")
for vol, d in sorted(por_volcan.items(), key=lambda kv: -kv[1]["pisados"]):
    if d["pisados"]:
        print("  %-22s %5d   %d en noche MIROVA" % (vol, d["pisados"], d["en_noche_mirova"]))

dest = os.path.join(os.path.dirname(__file__), "01_que_suprime_el_piso.json")
json.dump(res, open(dest, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
print("\npersistido en", dest)
