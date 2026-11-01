# -*- coding: utf-8 -*-
"""Verificador de D-29 (contexto limpio). Casos SINTETICOS para medir si la exclusion de dias llega a cada consumidor
de pasadas del evaluador de D25, por OTRO camino que el de las pruebas unitarias (que miran la funcion aislada y el
texto fuente). Solo datos de produccion del repo (data/mirova_equivalent, que es K desde FRONTERA_K) recortados a
2026-09-18..2026-10-18; ningun dato real del A/B.

Las dos preguntas del instrumento:
 1. Si la exclusion no llegara a un consumidor, ¿esto lo ve? Cada caso toca SOLO los dias excluidos en UN consumidor:
    R (crudos: cobertura entre brazos y P4 distance_class), cob (referencia de cobertura contra produccion),
    T (tabla K-brazo: P4 movidas y determinismo K'). Si el filtro no llega ahi, el numero cambia.
 2. Si el instrumento estuviera muerto, ¿se veria? Cada caso se corre tambien contra una copia del evaluador con
    DIAS_EXCLUIDOS vacio (control positivo): ahi el numero TIENE que cambiar.

Uso: python cobertura_sintetica.py --evaluador <ruta evaluar_d25.py> --tmp <dir> --out <json> [--casos a,b,...]
"""
from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[3]
assert (RAIZ / "volcanoes.yaml").exists(), RAIZ
REPO_EVAL = RAIZ / "experiments" / "_s157_prereg_d25" / "evaluar_d25.py"
VOLS = ["Lascar", "Isluga", "NevadosDeChillan", "Lastarria", "Villarrica", "PuyehueCordonCaulle", "Tupungatito"]
DESDE, HASTA = "2026-09-18", "2026-10-18"      # desde FRONTERA_K: produccion es K, no hace falta el historico
DIAS = ("2026-10-13", "2026-10-17", "2026-10-18")
MADRUGADA = "2026-10-13 01:30"                 # pasada sintetica: 13 en UTC, 12 en hora de Chile (UTC-3)


def cargar_x():
    """Helpers del evaluador del repo (bucket, SENS, BRAZOS, DECLARADO): convencion del proyecto, no inventada (A48)."""
    sys.path.insert(0, str(REPO_EVAL.parent))
    spec = importlib.util.spec_from_file_location("evaluar_d25_repo_verif", REPO_EVAL)
    X = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(X)
    return X


def base(X):
    out = {}
    for v in VOLS:
        recs = json.load(open(RAIZ / "data" / "mirova_equivalent" / (v + ".json"), encoding="utf-8"))["records"]
        out[v] = [r for r in recs if DESDE <= r["datetime_utc"][:10] <= HASTA and X.bp.bucket(r.get("sensor")) in X.SENS]
    return out


def con_huella(recs):
    out = copy.deepcopy(recs)
    for v in out.values():
        for r in v:
            if r.get("primary_cluster"):
                r["diag_bg_vecinos_n_sin_vecinos"] = 0
    return out


def escribir(X, tmp, caso, arms):
    raiz = tmp / caso / "raiz"
    if raiz.exists():
        shutil.rmtree(raiz)
    (raiz / "logs").mkdir(parents=True)
    for n, recs in arms.items():
        (raiz / X.BRAZOS[n]).mkdir()
        for v, rr in recs.items():
            json.dump({"records": rr}, open(raiz / X.BRAZOS[n] / (v + ".json"), "w", encoding="utf-8"))
            fl = dict(X.DECLARADO[n], PROFILE_NAME=X.BRAZOS[n], DATA_SUBDIR=X.BRAZOS[n])
            (raiz / "logs" / ("%s_%s.log" % (X.BRAZOS[n], v))).write_text("FLAGS_BRAZO " + json.dumps(fl) + "\n", encoding="utf-8")
    return raiz


def correr(evaluador, tmp, caso, raiz):
    out = tmp / caso / "out.json"
    cmd = [sys.executable, str(evaluador), "--ventana", "V1", "--out", str(out), "--tmp", str(tmp / caso / "tmp"),
           "--vols", ",".join(VOLS), "--desde", DESDE, "--hasta", HASTA, "--raiz", str(raiz), "--logs", str(raiz / "logs"),
           "--calibracion", "simetrica"]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    (tmp / (caso + ".txt")).write_text(p.stdout + "\n--- stderr ---\n" + p.stderr, encoding="utf-8")
    if p.returncode != 0:
        return None, p.stdout, p.stderr
    return json.load(open(out, encoding="utf-8")), p.stdout, p.stderr


def quitar_dias(recs, dias):
    return {v: [r for r in rr if r["datetime_utc"][:10] not in dias] for v, rr in recs.items()}


def medir(res, stdout):
    """Lo que cada consumidor deja ver: cobertura (R y cob), P4 (R: distance_class; T: movidas), determinismo (T),
    cabecera, y cualquier clave con fecha excluida en el JSON de salida (todos los consumidores a la vez)."""
    lineas = [l for l in stdout.splitlines() if l.strip()]
    idx = [i for i, l in enumerate(lineas) if l.startswith("== EVALUADO SIN")]
    det = {}
    for s in ("VIIRS375", "VIIRS750"):
        m = re.search(r"%s\s+(\d+) pasadas, misma decisión\s+(\d+)" % s, stdout)
        det[s] = [int(m.group(1)), int(m.group(2))] if m else None
    txt = json.dumps(res, ensure_ascii=False) if res else ""
    return {"cobertura_ok": None if res is None else res["cobertura_ok"],
            "lineas_cobertura": [l.strip() for l in stdout.splitlines() if "le faltan" in l or "faltan " in l and " de " in l],
            "P4_movidas": None if res is None else res["P4"]["movidas"],
            "P4_cambia_dc": None if res is None else len(res["P4"]["cambia_distance_class"]),
            "determinismo_ok": None if res is None else res["determinismo_ok"], "determinismo": det,
            "cabecera_linea_idx": idx, "primera_linea": lineas[0] if lineas else None,
            "dias_excluidos_en_json": None if res is None else res.get("dias_excluidos"),
            "claves_con_dia_excluido_en_json": {d: len(re.findall(r"\|%s \d\d:\d\d" % d, txt)) for d in DIAS},
            "madrugada_en_json": txt.count("|" + MADRUGADA), "estado": None if res is None else res["estado"]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--evaluador", default=str(REPO_EVAL))
    ap.add_argument("--tmp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--casos", default="nulo,d_sin_17,todos_sin_13_17_18,dc_17_en_D,mov_17_en_D,g_apagado,madrugada_13")
    a = ap.parse_args()
    X = cargar_x()
    tmp = Path(a.tmp).resolve(); tmp.mkdir(parents=True, exist_ok=True)
    K = base(X); D0 = con_huella(K)
    n_base = {v: len(r) for v, r in K.items()}
    print("evaluador:", a.evaluador); print("records base por volcan:", n_base, flush=True)
    resultados = {"evaluador": a.evaluador, "base": n_base, "casos": {}}
    for caso in a.casos.split(","):
        arms = {"K": copy.deepcopy(K), "G": copy.deepcopy(K), "D": copy.deepcopy(D0)}
        n_toc = 0
        if caso in ("d_sin_17", "d_sin_18", "d_sin_13"):   # consumidor R: cobertura entre brazos (D le faltan de K)
            arms["D"] = quitar_dias(arms["D"], ("2026-10-" + caso[-2:],)); n_toc = sum(len(r) for r in D0.values()) - sum(len(r) for r in arms["D"].values())
        elif caso == "todos_sin_13_17_18":           # consumidor cob: referencia de cobertura (produccion si los tiene)
            for n in arms:
                arms[n] = quitar_dias(arms[n], DIAS)
            n_toc = sum(len(r) for r in K.values()) - sum(len(r) for r in arms["K"].values())
        elif caso == "dc_17_en_D":                   # consumidor R: P4 cambia distance_class
            for v, rr in arms["D"].items():
                for r in rr:
                    if r["datetime_utc"][:10] == "2026-10-17":
                        r["distance_class"] = "far" if r.get("distance_class") == "summit" else "summit"; n_toc += 1
        elif caso == "mov_17_en_D":                  # consumidor T: P4 cumulos movidos (pc_lat de la tabla)
            for v, rr in arms["D"].items():
                for r in rr:
                    pc = r.get("primary_cluster")
                    if r["datetime_utc"][:10] == "2026-10-17" and pc and pc.get("centroid_lat") is not None:
                        pc["centroid_lat"] = pc["centroid_lat"] + 0.002; n_toc += 1
        elif caso == "g_apagado":                    # consumidor T: determinismo K' contra K (pasadas contadas)
            for v, rr in arms["G"].items():
                for r in rr:
                    pc = r.get("primary_cluster") or {}
                    if r["datetime_utc"][:10] in DIAS:
                        if pc.get("vrp_mw") is not None:
                            pc["vrp_mw"] = 0.0
                        if r.get("f5_core_vrp_mw") is not None:
                            r["f5_core_vrp_mw"] = 0.0
                        n_toc += 1
        elif caso == "madrugada_13":                 # fecha UTC contra hora local: una pasada a la 01:30 UTC del 13
            for n in arms:
                for v in ("Lascar", "Villarrica"):
                    src = [r for r in arms[n][v] if r["datetime_utc"][:10] == "2026-10-13"] or arms[n][v][:1]
                    arms[n][v].append(dict(copy.deepcopy(src[0]), datetime_utc=MADRUGADA)); n_toc += 1
        elif caso != "nulo":
            raise SystemExit("caso desconocido " + caso)
        raiz = escribir(X, tmp, caso, arms)
        res, so, se = correr(Path(a.evaluador), tmp, caso, raiz)
        m = medir(res, so); m["records_tocados"] = n_toc; m["fallo"] = None if res is not None else se[-800:]
        resultados["casos"][caso] = m
        print("%-20s tocados %4d | cobertura_ok %s | P4 mov %s dc %s | determ %s %s | cabecera idx %s | claves dias %s | madrugada %s%s" % (
            caso, n_toc, m["cobertura_ok"], m["P4_movidas"], m["P4_cambia_dc"], m["determinismo_ok"], m["determinismo"],
            m["cabecera_linea_idx"], m["claves_con_dia_excluido_en_json"], m["madrugada_en_json"],
            "" if res is not None else " | FALLO " + se[-300:].replace("\n", " ")), flush=True)
        shutil.rmtree(raiz, ignore_errors=True)
    Path(a.out).write_text(json.dumps(resultados, ensure_ascii=False, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
