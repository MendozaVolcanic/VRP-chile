# -*- coding: utf-8 -*-
"""Cobertura del reproceso historico con K contra la serie operacional, por volcan, sensor y dia (A108).

POR QUE (S157): antes de leer el ensayo de `scripts/reemplazar_ventana_reproceso.py` hay que saber si el reproceso
trae las mismas pasadas que la operacional. Un trozo verde puede haber quedado con pasadas de menos por un corte
de NASA (A64, A108), y en ese caso el reemplazo conservaria la pasada vieja (C0) sin avisar mas que en un conteo
global. Este script cuenta, dia por dia y sensor por sensor, las claves (datetime_utc, sensor) de cada archivo
dentro de la ventana, con la misma regla de fecha que el script de reemplazo (`datetime_utc[:10]`), y ubica cada
dia con deficit en el trozo del run 39125546355 que lo cubria.

Los trozos se rearman con `scripts/split_date_window.split_window(desde, hasta, 37)` y se comparan contra los
nombres de los jobs del run guardados en `jobs_run_39125546355.tsv` (bajados con `gh api .../jobs`). Si no
coinciden, el script se detiene.

Uso (desde la raiz del repo):
    python experiments/_s154_reproc_k/ensayo_s157/cobertura.py
Salida: experiments/_s154_reproc_k/ensayo_s157/cobertura.json y cobertura.md
"""
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "scripts"))
from split_date_window import split_window  # noqa: E402

AQUI = Path(__file__).resolve().parent
DESDE, HASTA, MAX_DIAS = "2025-02-15", "2026-09-17", 37
VOLCANES = ["Chaiten", "Copahue", "Isluga", "Lascar", "Lastarria", "Llaima", "PlanchonPeteroa",
            "PuyehueCordonCaulle", "Tupungatito", "Villarrica"]  # los 11 Tier A menos NevadosDeChillan


def trozos_verificados() -> list[dict]:
    trozos = split_window(DESDE, HASTA, MAX_DIAS)
    jobs = {}
    for linea in (AQUI / "jobs_run_39125546355.tsv").read_text(encoding="utf-8").splitlines():
        m = re.match(r"reproc \((\w+), (\d+), (\d{4}-\d\d-\d\d), (\d{4}-\d\d-\d\d)\)\t(\w+)", linea)
        if m:
            jobs[(m.group(1), int(m.group(2)))] = (m.group(3), m.group(4), m.group(5))
    for v in VOLCANES:
        for t in trozos:
            j = jobs.get((v, t["idx"]))
            if j is None or (j[0], j[1]) != (t["start"], t["end"]):
                raise SystemExit(f"el trozo {v} {t} no coincide con el job del run: {j}")
            if j[2] != "success":
                raise SystemExit(f"el trozo {v} {t['idx']} no termino verde en el run: {j[2]}")
    return trozos


def trozo_de(dia: str, trozos: list[dict]):
    for t in trozos:
        if t["start"] <= dia <= t["end"]:
            return t["idx"]
    return None


def claves(path: Path) -> tuple[dict, int]:
    """{(dia, sensor): set(datetime_utc)} dentro de la ventana, y cuantas claves repetidas hay."""
    recs = json.loads(path.read_text(encoding="utf-8"))["records"]
    por = defaultdict(set)
    n_ventana = 0
    for r in recs:
        dia = (r.get("datetime_utc") or "")[:10]
        if DESDE <= dia <= HASTA:
            n_ventana += 1
            por[(dia, r.get("sensor"))].add(r.get("datetime_utc"))
    unicas = sum(len(s) for s in por.values())
    return por, n_ventana - unicas


def main() -> int:
    trozos = trozos_verificados()
    salida = {"desde": DESDE, "hasta": HASTA, "trozos": trozos, "volcanes": {}}
    for v in VOLCANES:
        op, dup_op = claves(RAIZ / "data" / "mirova_equivalent" / f"{v}.json")
        re_, dup_re = claves(RAIZ / "data" / "_s154_reproc_k_historico" / f"{v}.json")
        por_sensor = defaultdict(Counter)
        deficit, exceso = [], []
        for k in sorted(set(op) | set(re_)):
            dia, sensor = k
            a, b = op.get(k, set()), re_.get(k, set())
            c = por_sensor[sensor]
            c["operacional"] += len(a)
            c["reproceso"] += len(b)
            c["comunes"] += len(a & b)
            c["solo_operacional"] += len(a - b)
            c["solo_reproceso"] += len(b - a)
            if a - b:
                deficit.append({"dia": dia, "sensor": sensor, "operacional": len(a), "reproceso": len(b),
                                "faltan": sorted(a - b), "trozo": trozo_de(dia, trozos)})
            if b - a:
                exceso.append({"dia": dia, "sensor": sensor, "operacional": len(a), "reproceso": len(b),
                               "sobran": sorted(b - a), "trozo": trozo_de(dia, trozos)})
        salida["volcanes"][v] = {
            "claves_repetidas_operacional": dup_op, "claves_repetidas_reproceso": dup_re,
            "por_sensor": {s: dict(c) for s, c in sorted(por_sensor.items())},
            "dias_con_deficit": deficit, "dias_con_exceso": exceso,
        }
    (AQUI / "cobertura.json").write_text(json.dumps(salida, indent=2, ensure_ascii=False), encoding="utf-8")

    md = [f"# Cobertura del reproceso con K contra la operacional, {DESDE} a {HASTA}", "",
          "Generado por `experiments/_s154_reproc_k/ensayo_s157/cobertura.py`. Una pasada es una clave "
          "(datetime_utc, sensor) con fecha dentro de la ventana.", "",
          "| Volcan | Sensor | Operacional | Reproceso | Comunes | Solo operacional | Solo reproceso |",
          "|---|---|---:|---:|---:|---:|---:|"]
    for v, d in salida["volcanes"].items():
        for s, c in d["por_sensor"].items():
            md.append(f"| {v} | {s} | {c['operacional']} | {c['reproceso']} | {c['comunes']} | "
                      f"{c['solo_operacional']} | {c['solo_reproceso']} |")
    md += ["", "## Dias con menos pasadas en el reproceso", "",
           "| Volcan | Dia | Sensor | Operacional | Reproceso | Trozo | Horas que faltan |", "|---|---|---|---:|---:|---:|---|"]
    for v, d in salida["volcanes"].items():
        for x in d["dias_con_deficit"]:
            md.append(f"| {v} | {x['dia']} | {x['sensor']} | {x['operacional']} | {x['reproceso']} | {x['trozo']} | "
                      f"{', '.join(h[11:] for h in x['faltan'])} |")
    md += ["", "## Dias con pasadas que solo trae el reproceso", "",
           "| Volcan | Dia | Sensor | Operacional | Reproceso | Trozo | Horas que sobran |", "|---|---|---|---:|---:|---:|---|"]
    for v, d in salida["volcanes"].items():
        for x in d["dias_con_exceso"]:
            md.append(f"| {v} | {x['dia']} | {x['sensor']} | {x['operacional']} | {x['reproceso']} | {x['trozo']} | "
                      f"{', '.join(h[11:] for h in x['sobran'])} |")
    md += ["", "## Claves repetidas dentro de un mismo archivo", ""]
    for v, d in salida["volcanes"].items():
        md.append(f"- {v}: operacional {d['claves_repetidas_operacional']}, reproceso {d['claves_repetidas_reproceso']}")
    (AQUI / "cobertura.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    for v, d in salida["volcanes"].items():
        so = sum(c["solo_operacional"] for c in d["por_sensor"].values())
        sr = sum(c["solo_reproceso"] for c in d["por_sensor"].values())
        print(f"{v}: {len(d['dias_con_deficit'])} dias-sensor con deficit ({so} pasadas), "
              f"{len(d['dias_con_exceso'])} con exceso ({sr} pasadas)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
