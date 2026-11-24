# -*- coding: utf-8 -*-
# FICHA (SDA, CPLT 372): lectura del A/B de la caja de MODIS (S197), copia de experiments/_s190_d36/p1_analisis.py
# con los brazos A (caja def, producción) y C (caja en el cráter). Sólo lectura.
"""Lee el p1_resultados_0.json que escribe ab_caja.py y calcula las métricas de PREREGISTRO.md (las de D36).

Valor publicado = réplica de mirovaEqVrp (frontend/index.html, includeFar=false; copia de
experiments/_s184_cenit/cenit_via.py::publicado) sobre el resumen de cada brazo.
Uso: python experiments/_s190_d36/p1_analisis.py <raiz_repo> <carpeta_artefactos> <salida.json>
"""
import collections
import glob
import json
import math
import sys
from datetime import datetime, timedelta
from pathlib import Path

import yaml

ROOT, ART, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
DESDE = "2026-03-01"
BRAZOS = ("A", "C")
VENT, ESTRICTA = timedelta(minutes=60), timedelta(minutes=10)
INNER = {v["name"]: v.get("inner_radius_km") for v in yaml.safe_load(open(Path(ROOT) / "volcanoes.yaml",
                                                                        encoding="utf-8"))["volcanoes"]}


def t(s):
    return datetime.strptime(s[:16], "%Y-%m-%d %H:%M")


def noche(x):
    return (x - timedelta(hours=12)).date().isoformat()


def publicado(b, inner):
    if b is None:
        return 0.0
    if b.get("pc_vrp") is None:
        v = b.get("vrp_mw") or 0
        return 0.0 if v > 50000 else v
    if b.get("dc") and b["dc"] != "summit":
        return 0.0
    if b.get("pc_dist") is not None and b["pc_dist"] > inner:
        return 0.0
    v = b.get("pc_vrp") or 0
    return 0.0 if v > 50000 else v


def mediana(x):
    x = sorted(x)
    n = len(x)
    return None if not n else (x[n // 2] if n % 2 else 0.5 * (x[n // 2 - 1] + x[n // 2]))


pas = []
for f in sorted(glob.glob(str(Path(ART) / "*" / "p1_resultados_*.json"))):
    pas += json.load(open(f, encoding="utf-8"))["pasadas"]
ok = [p for p in pas if p.get("estado") == "ok"]
fallidas = [{k: p.get(k) for k in ("volcan", "dt", "granule", "estado")} for p in pas if p.get("estado") != "ok"]
sel = json.load(open(Path(ROOT) / "experiments/_s190_d36/p1_pasadas.json", encoding="utf-8"))["pasadas"]
estr = {(p["volcan"], p["granule"]): p["estratos"] for p in sel}
for p in fallidas:
    p["estratos"] = estr.get((p["volcan"], p["granule"]))

res = {"run": "local S197 sobre los recortes del run 44016042341", "n_seleccion": len(sel), "n_ok": len(ok), "fallidas": fallidas, "controles": {}}
res["controles"]["copia_igual"] = [sum(bool(p["control_copia_igual"]) for p in ok), len(ok)]
cp = [p for p in ok if p.get("control_produccion") is not None]
res["controles"]["produccion_igual"] = [sum(p["control_produccion"] == {} for p in cp), len(cp)]
res["controles"]["produccion_difiere_ejemplos"] = [
    {"volcan": p["volcan"], "dt": p["dt"], "dif": p["control_produccion"], "sha": p.get("guardado_codigo_sha")}
    for p in cp if p["control_produccion"]][:10]
res["controles"]["otro_granulo"] = sum(bool(p.get("otro_granulo")) for p in ok)

# valores publicados por brazo
for p in ok:
    inner = INNER[p["volcan"]]
    p["pub"] = {b: publicado(p["brazos"][b], inner) for b in BRAZOS}
    p["t"] = t(p["dt"])

# referencia MIROVA (dedupe por hora y sensor, preferir consolidado)
alertas = []
for v in sorted({p["volcan"] for p in sel}):
    ded = {}
    for a in json.load(open(Path(ROOT) / "data/mirova" / (v + ".json"), encoding="utf-8"))["records"]:
        k = (a["datetime_utc"][:16], a["sensor"])
        if k not in ded or (ded[k]["source"] != "consolidado" and a["source"] == "consolidado"):
            ded[k] = a
    for a in ded.values():
        if a["sensor"] == "MODIS" and (a.get("VRP_MW") or 0) > 0 and not a.get("dia") \
                and a["datetime_utc"][:10] >= DESDE:
            alertas.append({"volcan": v, "t": t(a["datetime_utc"]), "vrp": a["VRP_MW"], "src": a["source"]})
por_v = collections.defaultdict(list)
for p in ok:
    por_v[p["volcan"]].append(p)


def m1(umbral):
    """Recall por noche-volcán: alguna pasada nuestra a ±60 min de alguna alerta (>= umbral) con publicado > 0."""
    noches = collections.defaultdict(list)
    for a in alertas:
        if a["vrp"] >= umbral:
            noches[(a["volcan"], noche(a["t"]))].append(a)
    out = {b: 0 for b in BRAZOS}
    sin_pasada, detalle = 0, {}
    for (v, n), al in noches.items():
        cand = [p for p in por_v[v] if any(abs(p["t"] - a["t"]) <= VENT for a in al)]
        if not cand:
            sin_pasada += 1
            continue
        for b in BRAZOS:
            out[b] += any(p["pub"][b] > 0 for p in cand)
        detalle[f"{v} {n}"] = {b: any(p["pub"][b] > 0 for p in cand) for b in BRAZOS}
    distintas = {k: d for k, d in detalle.items() if len(set(d.values())) > 1}
    return {"noches": len(noches), "evaluables": len(noches) - sin_pasada, "sin_pasada_procesada": sin_pasada,
            "aciertos": out, "noches_que_cambian": distintas}


res["M1_protegidas_1MW"] = m1(1.0)
res["M1_todas"] = m1(1e-9)

# M2 razón en la misma pasada (consolidado)
m2 = {b: [] for b in BRAZOS}
for a in alertas:
    if a["src"] != "consolidado":
        continue
    cand = [p for p in por_v[a["volcan"]] if abs(p["t"] - a["t"]) <= ESTRICTA]
    if not cand:
        continue
    p = min(cand, key=lambda x: abs(x["t"] - a["t"]))
    for b in BRAZOS:
        if p["pub"][b] > 0:
            m2[b].append(p["pub"][b] / a["vrp"])
res["M2_razon"] = {b: {"n": len(r), "mediana": mediana(r), "mediana_abs_log": mediana([abs(math.log(x)) for x in r])}
                   for b, r in m2.items()}

# M3 sobre-publicación en negativas
neg = [p for p in ok if "negativa" in p["estratos"]]
res["M3_negativas"] = {"n": len(neg), **{b: sum(p["pub"][b] > 0 for p in neg) for b in BRAZOS},
                       "alguna_alerta_cualquier_clase": {b: sum((p["brazos"][b] or {}).get("n", 0) > 0 for p in neg)
                                                         for b in BRAZOS}}

# M4 cuánto cambia, todos los estratos y por volcán
m4 = {}
for b in ("C",):
    cambia = [p for p in ok if abs(p["pub"][b] - p["pub"]["A"]) > 1e-9]
    npix = [p for p in ok if (p["brazos"][b] or {}).get("n") != (p["brazos"]["A"] or {}).get("n")]
    far_nuevo = [p for p in ok if (p["brazos"][b] or {}).get("dc") == "far" and (p["brazos"]["A"] or {}).get("dc") != "far"]
    mn = [p for p in ok if ("mirova" in p["estratos"] or "nuestra" in p["estratos"])]
    m4[b] = {"pasadas_valor_publicado_distinto": len(cambia), "de": len(ok),
             "en_estratos_mirova_o_nuestra": [sum(1 for p in cambia if p in mn), len(mn)],
             "suma_abs_delta_publicado_mw": round(sum(abs(p["pub"][b] - p["pub"]["A"]) for p in cambia), 3),
             "suma_publicado_A_mw": round(sum(p["pub"]["A"] for p in ok), 3),
             "pasadas_con_n_pixeles_distinto": len(npix),
             "pasadas_con_alerta_far_nueva": len(far_nuevo),
             "publicado_nuevo_desde_cero": sum(1 for p in cambia if p["pub"]["A"] == 0),
             "publicado_a_cero": sum(1 for p in cambia if p[ "pub"][b] == 0),
             "por_volcan": dict(collections.Counter(p["volcan"] for p in cambia)),
             "npix_por_volcan": dict(collections.Counter(p["volcan"] for p in npix)),
             "ejemplos": [{"volcan": p["volcan"], "dt": p["dt"], "estratos": p["estratos"], "A": p["pub"]["A"],
                           b: p["pub"][b], "nA": (p["brazos"]["A"] or {}).get("n"), "n" + b: (p["brazos"][b] or {}).get("n"),
                           "dcA": (p["brazos"]["A"] or {}).get("dc"), "dc" + b: (p["brazos"][b] or {}).get("dc")}
                          for p in npix][:25]}
res["M4_cambios"] = m4

# punto 3: estrato borde
borde = [p for p in ok if "borde" in p["estratos"]]
res["P3_borde"] = [{"volcan": p["volcan"], "dt": p["dt"], "dist_i0_km": round(p["dist_i0_km"], 2) if p.get("dist_i0_km") is not None else None,
                    "n_sel_45km": p.get("n_sel_45km"), "prod": p["brazos"]["A"] is not None,
                    "sin_corte_A_publicado": publicado((p.get("brazos_sin_corte_5km") or {}).get("A"), INNER[p["volcan"]]),
                    "sin_corte_A_n": ((p.get("brazos_sin_corte_5km") or {}).get("A") or {}).get("n"),
                    "mirova_a_60min": [a["vrp"] for a in alertas if a["volcan"] == p["volcan"] and abs(a["t"] - p["t"]) <= VENT]}
                   for p in borde]
dist = [p["dist_i0_km"] for p in ok if p.get("dist_i0_km") is not None]
res["P3_dist_i0_todas"] = {"n": len(dist), "max": max(dist), "n_sobre_2km": sum(d > 2 for d in dist),
                           "n_sobre_5km": sum(d > 5 for d in dist), "min_n_sel_45km": min(p["n_sel_45km"] for p in ok)}
json.dump(res, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
for k in ("n_seleccion", "n_ok", "controles", "M1_protegidas_1MW", "M1_todas", "M2_razon", "M3_negativas"):
    print(k, json.dumps(res[k], default=str, ensure_ascii=False)[:900])
for b, d in m4.items():
    print("M4", b, json.dumps({k: v for k, v in d.items() if k != "ejemplos"}, ensure_ascii=False))
print("P3_dist_i0", res["P3_dist_i0_todas"])
for x in res["P3_borde"]:
    print("P3", x)
print("fallidas", fallidas)

# --- estratificado por volcán (encargo S190): M2 por volcán y detalle de las pasadas cuyo valor publicado cambia
m2v = collections.defaultdict(lambda: {b: [] for b in BRAZOS})
detalle = []
for a in alertas:
    cand = [p for p in por_v[a["volcan"]] if abs(p["t"] - a["t"]) <= ESTRICTA]
    if not cand:
        continue
    p = min(cand, key=lambda x: abs(x["t"] - a["t"]))
    if a["src"] == "consolidado":
        for b in BRAZOS:
            if p["pub"][b] > 0:
                m2v[a["volcan"]][b].append(p["pub"][b] / a["vrp"])
    if abs(p["pub"]["C"] - p["pub"]["A"]) > 1e-9:
        detalle.append({"volcan": p["volcan"], "dt": p["dt"], "mirova": a["vrp"], "src": a["src"],
                        "A": round(p["pub"]["A"], 3), "C": round(p["pub"]["C"], 3),
                        "z": (p["brazos"]["A"] or {}).get("sensor_zenith_deg")})
res["M2_por_volcan"] = {v: {b: {"n": len(r), "mediana": mediana(r),
                                "mediana_abs_log": mediana([abs(math.log(x)) for x in r])} for b, r in d.items()}
                        for v, d in m2v.items()}
res["cambios_con_mirova_misma_pasada"] = detalle
json.dump(res, open(OUT, "w", encoding="utf-8"), indent=1, ensure_ascii=False, default=str)
for v, d in res["M2_por_volcan"].items():
    print("M2v", v, "n", d["A"]["n"], "A", round(d["A"]["mediana"], 3) if d["A"]["mediana"] else None,
          "C", round(d["C"]["mediana"], 3) if d["C"]["mediana"] else None)
for x in detalle:
    print("CAMBIO", x)
