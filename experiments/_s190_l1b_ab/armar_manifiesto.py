# FICHA (SDA, CPLT 372): experimento de solo lectura (A/B de fase de grilla en VIIRS 750); no es detección de producción.
"""Arma manifiesto_s190.json: las pasadas V750 del A/B de fase de grilla, elegidas por estratos con semilla fija.

POR QUÉ: el probe S185 (PR #1018) eligió la fase N/S mirando 10 pasadas de Tupungatito con margen cerca de 1; esa misma
elección no puede probarse con las mismas 10. Este manifiesto toma pasadas NUEVAS de los 11 Tier A, pareadas con la tabla
de MIROVA, y las reparte por estrato para medir a la vez lo que la fase gana (calladas que alerta, solo_via que apaga) y lo
que daña (rutinas que alerta, ambos que apaga). Reglas del pareo y de los estratos: PREREGISTRO.md §2.

Uso: python experiments/_s190_l1b_ab/armar_manifiesto.py  (lee data/ del árbol; escribe el manifiesto al lado).
"""
import csv
import json
import random
import subprocess
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

import yaml

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
VENTANA = ("2026-03-01", "2026-11-14")          # tabla de MIROVA sana desde marzo (A119); última noche cerrada antes del sello
SEMILLA = 190
TIER_A = ["Lascar", "Isluga", "NevadosDeChillan", "Llaima", "Villarrica", "Chaiten", "Lastarria", "PlanchonPeteroa",
          "Copahue", "Tupungatito", "PuyehueCordonCaulle"]
ALIAS = {"NevadosDeChillan": ["Nevados de Chillan"], "PuyehueCordonCaulle": ["Puyehue-Cordon Caulle"]}
# Las 10 pasadas del probe S185 (manifiesto_s185.json, proyecto tup): en muestra, no puntúan (se corren para replicar).
S185 = {m["l1b"] for m in json.load(open(ROOT / "experiments/_s185_l1b/manifiesto_s185.json", encoding="utf-8"))
        if m["proyecto"] == "tup"}
# Tamaño de muestra por estrato (None = todas). Estratos de rutina y ambos por el margen publicado de la celda decisiva.
MUESTRA = {"calla": None, "solo_via": None, "rut_>=0.9": None, "rut_0.8-0.9": 30, "rut_0.6-0.8": 30, "rut_0.3-0.6": 12,
           "rut_<0.3": 8, "amb_<1.2": 20, "amb_1.2-1.5": 10, "amb_>=1.5": 8}


def estrato(cat, m):
    if cat == "rutina":
        return "rut_" + (">=0.9" if m >= .9 else "0.8-0.9" if m >= .8 else "0.6-0.8" if m >= .6 else "0.3-0.6" if m >= .3 else "<0.3")
    if cat == "ambos":
        return "amb_" + ("<1.2" if m < 1.2 else "1.2-1.5" if m < 1.5 else ">=1.5")
    return cat


def censo():
    ref = defaultdict(list)
    for r in csv.DictReader(open(ROOT / "data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv", encoding="utf-8")):
        if r["Sensor"] == "VIIRS":
            ref[r["Volcan"]].append((datetime.strptime(r["Fecha_Satelite_UTC"], "%Y-%m-%d %H:%M:%S"), r))
    vy = {v["name"]: v for v in yaml.safe_load(open(ROOT / "volcanoes.yaml", encoding="utf-8"))["volcanoes"]}
    filas = []
    for v in TIER_A:
        fr = sum((ref.get(a, []) for a in [v] + ALIAS.get(v, [])), [])
        for r in json.load(open(ROOT / f"data/mirova_equivalent/{v}.json", encoding="utf-8"))["records"]:
            if not r["sensor"].endswith("_750") or not (VENTANA[0] <= r["datetime_utc"][:10] <= VENTANA[1]):
                continue
            dg = r.get("diag_codigo_mirova") or {}
            cd = (dg.get("s1") or {}).get("celda_decisiva")
            if dg.get("dayflag") != 0 or not r.get("via_codigo_mirova") or cd is None:
                continue
            dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M")
            fm = [x for t, x in fr if abs((t - dt).total_seconds()) <= 120]
            if not fm or fm[0]["Tipo_Registro"] not in ("ALERTA_TERMICA", "RUTINA"):
                continue
            det = (r.get("n_anomalous_pixels") or 0) > 0
            cat = {("ALERTA_TERMICA", True): "ambos", ("ALERTA_TERMICA", False): "calla",
                   ("RUTINA", True): "solo_via", ("RUTINA", False): "rutina"}[(fm[0]["Tipo_Registro"], det)]
            y = vy[v]
            filas.append({"volcan": v, "dt": r["datetime_utc"], "sensor": r["sensor"], "l1b": r["granule"], "cat": cat,
                          "estrato": estrato(cat, cd["margen"]), "s185": v == "Tupungatito" and r["granule"] in S185,
                          "vent": [y.get("vent_lat") or y["lat"], y.get("vent_lon") or y["lon"]], "inner_km": y["inner_radius_km"],
                          "ref": {"mirova_tipo": fm[0]["Tipo_Registro"], "mirova_vrp_mw": float(fm[0]["VRP_MW"] or 0),
                                  "mirova_dist_km": fm[0]["Distancia_km"], "publicado_n_pix": r.get("n_anomalous_pixels"),
                                  "publicado_vrp_mw": r.get("vrp_mw"), "publicado_celda_decisiva": cd}})
    return filas


def main():
    filas = censo()
    rng = random.Random(SEMILLA)
    por = defaultdict(list)
    for f in sorted(filas, key=lambda x: (x["estrato"], x["volcan"], x["dt"])):
        por[f["estrato"]].append(f)
    man, poblacion = [], {}
    for est, n in MUESTRA.items():
        fuera = [f for f in por.get(est, []) if not f["s185"]]
        poblacion[est] = len(fuera)
        elegidas = fuera if n is None or n >= len(fuera) else rng.sample(fuera, n)
        man += [dict(f, rol="puntua") for f in elegidas]
    man += [dict(f, rol="replica_s185") for f in filas if f["s185"]]
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    out = {"semilla": SEMILLA, "ventana": VENTANA, "arbol_datos": sha, "poblacion_por_estrato": poblacion,
           "muestra_por_estrato": dict(Counter(m["estrato"] for m in man if m["rol"] == "puntua")),
           "n_replica_s185": sum(m["rol"] == "replica_s185" for m in man), "pasadas": man}
    json.dump(out, open(AQUI / "manifiesto_s190.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    print("poblacion:", poblacion)
    print("muestra:", out["muestra_por_estrato"], "| replica S185:", out["n_replica_s185"], "| total:", len(man))


if __name__ == "__main__":
    main()
