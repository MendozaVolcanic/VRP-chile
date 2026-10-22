# -*- coding: utf-8 -*-
"""S159, frente «gemelo de D25». Cuenta, pasada por pasada, en cuántas el brazo A y el brazo B publican distinto en el
tablero, y en cuántas difiere la magnitud del cúmulo (primary_cluster.vrp_mw) o cualquier campo del record.

POR QUÉ. El P2 del pre-registro de D25 usa como ruido las pasadas discordantes entre K y su gemelo K'. Desde #877 los
brazos corren en el MISMO job (scripts/reproc_brazos.py), o sea en la misma máquina y sobre los mismos gránulos ya
bajados: si la única fuente de ruido es el desempate que depende de la CPU (S152), K y K' deberían salir idénticos por
construcción, y entonces el ruido de P2 es cero sin haber medido ruido.

LAS DOS PREGUNTAS DEL INSTRUMENTO.
1. Si la publicación de K' estuviera completamente cambiada, ¿esto lo vería? Sí: el predicado del tablero se ejecuta
   con node (banco_paridad.correr_node, A97) sobre cada record de cada brazo, y se compara por pasada. Se comprueba con
   el control de mutación (--mutar), que cambia un número conocido de records y exige exactamente ese conteo.
2. Si el instrumento estuviera muerto, ¿el resultado se vería distinto? Un cero sólo se acepta si (a) el pareo encontró
   pasadas (denominador > 0, impreso), (b) el control de mutación da el conteo exacto, y (c) un par de brazos con
   detector distinto da discordancia mayor que cero (control positivo real, se corre aparte con otros directorios).

Uso:
  python -I discordancia_gemelo.py --a DIR_K --b DIR_KP --desde 2026-08-29 --hasta 2026-10-18 [--excluir 2026-10-13,...]
                                   [--mutar N] [--out salida.json]
"""
from __future__ import annotations

import argparse
import collections
import copy
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "scripts"))
import banco_paridad as bp  # noqa: E402  (predicado del tablero con node, bucket, coords, filtro diurno)

VOLATILES = {"processed_utc", "first_processed_utc", "regimen"}


def tramo(z):
    if z is None:
        return "sin_cenit"
    return "<=40" if z <= 40 else ">40"


def cargar(dir_, desde, hasta, excluir):
    """Records nocturnos (filtro del evaluador) indexados por (volcan, sensor, granulo)."""
    coords = bp._coords_por_volcan()
    out, n_dup, vols = {}, 0, []
    for p in sorted(Path(dir_).glob("*.json")):
        vol = p.stem
        vols.append(vol)
        recs = json.load(open(p, encoding="utf-8"))["records"]
        for r in recs:
            b = bp.bucket(r.get("sensor"))
            dia = (r.get("datetime_utc") or "")[:10]
            if b is None or not (desde <= dia <= hasta) or dia in excluir:
                continue
            try:
                dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
            except (KeyError, ValueError):
                continue
            lat, lon = coords[vol]
            if bp.es_pasada_diurna_descartada(b, lat, lon, dt):
                continue
            k = (vol, r.get("sensor"), r.get("granule") or r.get("datetime_utc"))
            if k in out:
                n_dup += 1
            out[k] = (b, r)
    return out, n_dup, vols


def slim(r):
    """Mismo recorte de campos que banco_paridad.cargar_nuestros (CAMPOS_JS)."""
    s = {k: r.get(k) for k in bp.CAMPOS_JS if k != "anomaly_pixels"}
    if r.get("f5_core_vrp_mw") is None:
        s["anomaly_pixels"] = [{k: p.get(k) for k in ("lat", "lon", "vrp_mw", "bt_k")}
                               for p in (r.get("anomaly_pixels") or [])]
    return s


def publicar(idx, inner):
    keys = sorted(idx)
    pred = bp.correr_node([[slim(idx[k][1]), inner[k[0]]] for k in keys]) if keys else []
    return {k: (p[4], p[3]) for k, p in zip(keys, pred)}


def pc_vrp(r):
    return (r.get("primary_cluster") or {}).get("vrp_mw")


def sin_volatiles(r):
    return {k: v for k, v in r.items() if k not in VOLATILES}


def mutar(idx, pub, n, semilla=159):
    """Control de mutación: en una COPIA, apaga n records publicados (distance_class -> far) y sube en +0,5 MW el
    cúmulo de otros n records con cúmulo. Devuelve la copia y los conteos que el instrumento DEBE dar."""
    rng = random.Random(semilla)
    idx2 = copy.deepcopy(idx)
    pubs = [k for k in sorted(idx) if pub[k][0] == 1]
    con_pc = [k for k in sorted(idx) if pc_vrp(idx[k][1]) is not None and pub[k][0] == 0]
    a = rng.sample(pubs, min(n, len(pubs)))
    b = rng.sample(con_pc, min(n, len(con_pc)))
    for k in a:
        idx2[k][1]["distance_class"] = "far"
    for k in b:
        idx2[k][1]["primary_cluster"]["vrp_mw"] = pc_vrp(idx2[k][1]) + 0.5
    return idx2, {"pub_apagadas": len(a), "pc_cambiados": len(a) + len(b)}


def comparar(A, B, pubA, pubB):
    comunes = sorted(set(A) & set(B))
    est = collections.defaultdict(lambda: collections.Counter())
    ejemplos = []
    for k in comunes:
        b, ra = A[k]
        rb = B[k][1]
        for e in (b, "%s|%s" % (b, tramo(ra.get("sensor_zenith_deg"))), "TODOS"):
            c = est[e]
            c["pasadas"] += 1
            c["pub_A"] += pubA[k][0]
            c["pub_B"] += pubB[k][0]
            if pubA[k][0] != pubB[k][0]:
                c["pub_discordante"] += 1
            if pc_vrp(ra) != pc_vrp(rb):
                c["pc_vrp_distinto"] += 1
            if pubA[k][1] != pubB[k][1]:
                c["magnitud_tablero_distinta"] += 1
            if sin_volatiles(ra) != sin_volatiles(rb):
                c["record_distinto"] += 1
        if (pubA[k][0] != pubB[k][0] or pc_vrp(ra) != pc_vrp(rb)) and len(ejemplos) < 15:
            ejemplos.append({"clave": list(k), "pub": [pubA[k][0], pubB[k][0]], "pc_vrp": [pc_vrp(ra), pc_vrp(rb)],
                             "dc": [ra.get("distance_class"), rb.get("distance_class")]})
    solo = {"solo_A": collections.Counter(A[k][0] for k in set(A) - set(B)),
            "solo_B": collections.Counter(B[k][0] for k in set(B) - set(A))}
    return {e: dict(c) for e, c in sorted(est.items())}, {k: dict(v) for k, v in solo.items()}, ejemplos


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", required=True)
    ap.add_argument("--b", required=True)
    ap.add_argument("--desde", required=True)
    ap.add_argument("--hasta", required=True)
    ap.add_argument("--excluir", default="")
    ap.add_argument("--mutar", type=int, default=0)
    ap.add_argument("--out")
    a = ap.parse_args(argv)
    excl = {x for x in a.excluir.split(",") if x}
    inner = bp.inner_desde_html()
    A, dupA, volsA = cargar(a.a, a.desde, a.hasta, excl)
    B, dupB, volsB = cargar(a.b, a.desde, a.hasta, excl)
    vols = sorted(set(volsA) & set(volsB))
    A = {k: v for k, v in A.items() if k[0] in vols}
    B = {k: v for k, v in B.items() if k[0] in vols}
    pubA = publicar(A, inner)
    res = {"a": a.a, "b": a.b, "ventana": [a.desde, a.hasta], "excluidos": sorted(excl), "volcanes": vols,
           "duplicados": [dupA, dupB], "sha256_index_html": bp.sha_git(bp.HTML) if hasattr(bp, "sha_git") else None}
    if a.mutar:
        B, esperado = mutar(A, pubA, a.mutar)
        res["mutacion_esperada"] = esperado
    pubB = publicar(B, inner)
    est, solo, ej = comparar(A, B, pubA, pubB)
    res.update({"estratos": est, "no_pareadas": solo, "ejemplos": ej})
    print(json.dumps({k: res[k] for k in ("ventana", "excluidos", "volcanes", "duplicados")}, ensure_ascii=False))
    if a.mutar:
        print("MUTACION esperada", res["mutacion_esperada"])
    print("%-18s %8s %7s %7s %8s %8s %8s %8s" % ("estrato", "pasadas", "pub_A", "pub_B", "pub_disc", "pc_vrp", "mag_tab",
                                                "record"))
    for e, c in est.items():
        print("%-18s %8d %7d %7d %8d %8d %8d %8d" % (e, c.get("pasadas", 0), c.get("pub_A", 0), c.get("pub_B", 0),
                                                     c.get("pub_discordante", 0), c.get("pc_vrp_distinto", 0),
                                                     c.get("magnitud_tablero_distinta", 0),
                                                     c.get("record_distinto", 0)))
    print("no pareadas", solo)
    for x in ej[:8]:
        print("  ej", x)
    if a.out:
        Path(a.out).write_text(json.dumps(res, ensure_ascii=False, indent=1, default=str), encoding="utf-8")


if __name__ == "__main__":
    main()
