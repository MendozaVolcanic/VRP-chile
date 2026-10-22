# -*- coding: utf-8 -*-
"""S160, control del instrumento pedido por el coordinador (NO es regla sellada): ¿P2 de D-34 con la calibración de
D-42 aprueba un placebo SIN información?

Origen: la auditoría S160 (verificador V1a, experiments/_s160_audit/v1a/placebos_v1a.py en s159-pruebas, salida
salidas/placebos/resumen.txt) midió que una P2 con tolerancia 0 aprueba «D = K con la publicación del 1 % de los
records apagada al azar»: CUMPLE en 16 de 30 semillas en V1 y 5 de 10 en V2. Aquí: D = K con el 1 % de las
PUBLICACIONES de K apagadas al azar (magnitud del cúmulo a 0,0 MW, como `apagar` de probar_evaluar_d25.py; el tablero
no publica nada con 0 MW), con el evaluador entero (predicado del tablero con node, etiquetas, protección).

Criterio del control: P2 calibrada no puede dar GANA en más del 5 % de las semillas. Si lo da, el defecto es de la
métrica de P2 (premia publicar menos: apagar al azar quita más negativos limpios que alertas), no del azar, y la
calibración no lo puede ver, porque el efecto es real y repartido en muchas noches. No se inventa regla nueva.

Brazos desde records de PRODUCCIÓN (sustrato_k.unir_k: histórico con K antes del 2026-09-18, producción desde ahí),
nunca desde artefactos del A/B. Ventana tipo V1: 2026-09-18 a 2026-10-18 con K, K' y D, 7 volcanes (los de
probar_evaluar_d25.py), con los días de D-29 excluidos. Ventana tipo V2: 2026-04-01 a 2026-06-12, K y D, tabla sola,
6 volcanes. Las dos preguntas del instrumento: (1) si el placebo no apagara nada, ¿se vería? Sí: cada semilla cuenta
cuántas pasadas publica K y no D en la tabla (tiene que ser el 1 % pedido, salvo las de días excluidos); (2) si el
evaluador cayera, la semilla se marca CAIDO y no se cuenta.

Uso: python placebo_1pct.py <tmp> <ventana V1|V2> <n semillas> [salida.jsonl]
"""
import collections
import copy
import json
import math
import random
import shutil
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[3]
EVD = RAIZ / "experiments" / "_s157_prereg_d25"
sys.path.insert(0, str(EVD))
import evaluar_d25 as X  # noqa: E402
import sustrato_k as S  # noqa: E402

VOLS = ["Lascar", "Isluga", "NevadosDeChillan", "Lastarria", "Villarrica", "PuyehueCordonCaulle", "Tupungatito"]
VENT = {"V1": ("2026-09-18", "2026-10-18", ("K", "G", "D"), VOLS),
        "V2": ("2026-04-01", "2026-06-12", ("K", "D"), [v for v in VOLS if v != "NevadosDeChillan"])}
FRAC = 0.01


def cargar(datos, vols, desde, hasta):
    out = {}
    for v in vols:
        p = Path(datos) / (v + ".json")
        recs = json.load(open(p, encoding="utf-8"))["records"] if p.exists() else []
        out[v] = [r for r in recs if desde <= r["datetime_utc"][:10] <= hasta and X.bp.bucket(r.get("sensor")) in X.SENS]
    return out


def con_huella(recs):
    out = copy.deepcopy(recs)
    for v in out.values():
        for r in v:
            if r.get("primary_cluster"):
                r["diag_bg_vecinos_n_sin_vecinos"] = 0
    return out


def apagar(r):
    pc = r.get("primary_cluster") or {}
    if pc.get("vrp_mw") is not None:
        pc["vrp_mw"] = 0.0
    if r.get("f5_core_vrp_mw") is not None:
        r["f5_core_vrp_mw"] = 0.0


def buscar(recs, clave):
    vol, b, t = clave.split("|")
    return [r for r in recs[vol] if r["datetime_utc"][:16] == t and X.bp.bucket(r.get("sensor")) == b]


def escribir(raiz, arms):
    if raiz.exists():
        shutil.rmtree(raiz)
    (raiz / "logs").mkdir(parents=True)
    for n, recs in arms.items():
        (raiz / X.BRAZOS[n]).mkdir()
        for v, rr in recs.items():
            json.dump({"records": rr}, open(raiz / X.BRAZOS[n] / (v + ".json"), "w", encoding="utf-8"))
            fl = dict(X.DECLARADO[n], PROFILE_NAME=X.BRAZOS[n], DATA_SUBDIR=X.BRAZOS[n])
            (raiz / "logs" / ("%s_%s.log" % (X.BRAZOS[n], v))).write_text("FLAGS_BRAZO " + json.dumps(fl) + "\n",
                                                                          encoding="utf-8")


def correr(tmp, ventana, desde, hasta, vols, raiz):
    out = tmp / "out.json"
    cmd = [sys.executable, str(EVD / "evaluar_d25.py"), "--ventana", ventana, "--raiz", str(raiz), "--logs",
           str(raiz / "logs"), "--out", str(out), "--tmp", str(tmp / "t"), "--vols", ",".join(vols), "--desde", desde,
           "--hasta", hasta]
    p = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0 or not out.exists():
        return None, p.stderr[-1500:]
    return json.load(open(out, encoding="utf-8")), json.load(open(tmp / "t" / "t_K_D.json", encoding="utf-8"))["pasadas"]


def main():
    tmp, ventana, nsem = Path(sys.argv[1]).resolve(), sys.argv[2], int(sys.argv[3])
    jl = Path(sys.argv[4]) if len(sys.argv) > 4 else AQUI / ("placebo_1pct_%s.jsonl" % ventana)
    desde, hasta, brazos, vols = VENT[ventana]
    tmp.mkdir(parents=True, exist_ok=True)
    datos, _ = S.unir_k(tmp / "k")
    K = cargar(datos, vols, desde, hasta)
    # nulo: D = K (con la huella). Da la tabla con la publicación de K por pasada, de donde se sortea el 1 %.
    arms = {"K": K, "G": copy.deepcopy(K), "D": con_huella(K)}
    arms = {n: arms[n] for n in brazos}
    escribir(tmp / "raiz", arms)
    res0, t0 = correr(tmp / "nulo", ventana, desde, hasta, vols, tmp / "raiz")
    if res0 is None:
        raise SystemExit("el evaluador cayó en el nulo: %s" % t0)
    publicadas = sorted(k for k, v in t0.items() if k.split("|")[1] in X.SENS and (v.get("control") or {}).get("pub"))
    n_apagar = max(1, round(FRAC * len(publicadas)))
    print("ventana %s %s a %s | brazos %s | %d volcanes | publicaciones de K en la tabla %d | se apagan %d por semilla | "
          "nulo: estado %s" % (ventana, desde, hasta, brazos, len(vols), len(publicadas), n_apagar, res0["estado"]), flush=True)
    for s in range(nsem):
        rng = random.Random(1000 + s)
        elegidas = rng.sample(publicadas, n_apagar)
        D = con_huella(K)
        for k in elegidas:
            for r in buscar(D, k):
                apagar(r)
        arms = {"K": K, "G": copy.deepcopy(K), "D": D}
        arms = {n: arms[n] for n in brazos}
        escribir(tmp / "raiz", arms)
        res, t = correr(tmp / ("s%d" % s), ventana, desde, hasta, vols, tmp / "raiz")
        fila = {"ventana": ventana, "semilla": s, "apagadas_pedidas": n_apagar}
        if res is None:
            fila["caido"] = t
        else:
            excl = set(X.DIAS_EXCLUIDOS.get(ventana, ()))
            fila["apagadas_en_tabla"] = sum(1 for k, v in t.items() if len(v) == 2 and v["control"]["pub"]
                                            and not v["brazo"]["pub"] and k.split("|")[1] in X.SENS)
            fila["apagadas_en_dias_excluidos"] = sum(k.split("|")[2][:10] in excl for k in elegidas)
            fila["estado"] = res["estado"]
            fila["controles_ok"] = res["controles_ok"]
            for regla in res["por_regla"]:
                for sen in X.SENS:
                    i = res["por_regla"][regla]["info"]["P2|%s" % sen]
                    fila["P2|%s|%s" % (regla, sen)] = {
                        "calibrada": res["por_regla"][regla]["veredicto"]["P2|%s" % sen],
                        "sin_calibrar": i["resultado_sin_calibrar"], "neto": i["neto"], "n": i["n_discordantes"],
                        "noches": i["noches_discordantes"], "falsos_gana": i["falsos_gana"],
                        "falsos_pierde": i["falsos_pierde"], "ic95": i["ic95"]}
        with open(jl, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(fila, ensure_ascii=False) + "\n")
        print(json.dumps(fila, ensure_ascii=False)[:600], flush=True)
        for d in (tmp / ("s%d" % s),):
            shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
