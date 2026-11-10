# -*- coding: utf-8 -*-
"""S178, P1 paso 3: las pasadas en que el K-gemelo (D3, run 42567518008) y K de disco (origin/main) no coinciden, para
escribir las excepciones nombradas de C-K ANTES de leer F26 (pre-registro sellado §6 C-K y §11, R-15).

POR QUÉ. C-K pregunta si el K que hay en disco es el K que corre hoy el código del tag. Si no lo es, comparar la vía
contra K de disco mediría también la deriva de K. El pre-registro admite a lo más 3 pasadas distintas por sensor, cada
una con el empate de argsort entre CPU (S152) mostrado en el record; con más, C-K cae.

QUÉ NO HACE: no carga la vía (se pasa vacía) ni calcula reglas, P1, P2 ni veredictos. Usa las funciones del lector
sellado (armar_pasadas, tabla_publica con el predicado del tablero por node, c_k, c_k_puro) tal cual, sin copiarlas.

Uso: python diferencias_ck.py --d3 C:/Users/nmend/vrp-temporales/s177_d3 --tmp DIR [--ref origin/main] --salida JSON
"""
from __future__ import annotations

import argparse
import collections
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

os.environ["MSYS_NO_PATHCONV"] = "1"
RAIZ = Path(__file__).resolve().parents[2]
LECTOR = RAIZ / "experiments" / "_s172_retro_paquete" / "leer_retro.py"


def cargar_lector():
    spec = importlib.util.spec_from_file_location("leer_retro_ck", LECTOR)
    L = importlib.util.module_from_spec(spec)
    sys.modules["leer_retro_ck"] = L
    spec.loader.exec_module(L)
    return L


def aplanar_trozos(d3, destino):
    """Un <volcán>.json por volcán con los records de todos sus trozos (último intento de cada trozo)."""
    destino.mkdir(parents=True, exist_ok=True)
    por_trozo = {}
    for d in sorted(Path(d3).glob("trozo-*")):
        base = d.name.rsplit("-intento-", 1)[0]
        n = int(d.name.rsplit("-intento-", 1)[1])
        if base not in por_trozo or n > por_trozo[base][0]:
            por_trozo[base] = (n, d)
    vols = collections.defaultdict(list)
    for base, (_, d) in sorted(por_trozo.items()):
        js = sorted(d.glob("*.json"))
        assert len(js) == 1, d
        vols[js[0].stem] += json.loads(js[0].read_text(encoding="utf-8"))["records"]
    for v, recs in vols.items():
        (destino / f"{v}.json").write_text(json.dumps({"volcano": v, "records": recs}), encoding="utf-8")
    return {v: len(r) for v, r in vols.items()}, sorted(por_trozo)


def exportar_k(ref, vols, destino):
    destino.mkdir(parents=True, exist_ok=True)
    for v in vols:
        b = subprocess.run(["git", "show", f"{ref}:data/mirova_equivalent/{v}.json"], cwd=RAIZ, capture_output=True,
                           check=True).stdout
        (destino / f"{v}.json").write_bytes(b)


def control_puede_fallar(L, filas, kg, k):
    """A116 y A110: un cero de C-K sólo vale si el mismo cálculo da distinto de cero cuando hay algo que ver. Sobre una
    copia, por sensor: (a) a la primera pasada con K-gemelo se le suma 0,01 MW al VRP del cúmulo del K-gemelo; (b) a la
    segunda se le invierte la publicación del K-gemelo. Tienen que aparecer exactamente esas 2 por sensor."""
    import copy
    f2 = copy.deepcopy(filas)
    esperadas = set()
    for s in L.SENSORES:
        con = [f for f in f2 if f["b"] == s and f.get("en_kgemelo") and f.get("k_rec") is not None]
        if len(con) < 2:
            return {"estado": f"SIN SUSTRATO en {s}"}
        pc = con[0]["kg_rec"].setdefault("primary_cluster", {}) or {}
        con[0]["kg_rec"]["primary_cluster"] = dict(pc, vrp_mw=float(pc.get("vrp_mw") or 0.0) + 0.01)
        con[1]["_t"]["KG"]["pub"] = 1 - con[1]["_t"]["KG"]["pub"]
        esperadas |= {(con[0]["vol"], con[0]["dt"], s), (con[1]["vol"], con[1]["dt"], s)}
    ck = L.c_k(f2, [], L.TIER_A, L.sobras_kgemelo(kg, k))
    vistas = set(map(tuple, ck["diferencias"]))
    ok = vistas == esperadas and not ck["estado"].startswith("OK")
    return {"estado": "OK: atrapa las 6 alteraciones" if ok else "ROJO: el control no atrapa lo inyectado",
            "esperadas": len(esperadas), "vistas": len(vistas), "c_k_alterado": ck["estado"][:120]}


def main(argv=None):
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--d3", required=True)
    ap.add_argument("--tmp", required=True)
    ap.add_argument("--ref", default="origin/main")
    ap.add_argument("--salida", required=True)
    a = ap.parse_args(argv)
    L = cargar_lector()
    tmp = Path(a.tmp)
    n_kg, trozos = aplanar_trozos(a.d3, tmp / "kgemelo")
    exportar_k(a.ref, L.TIER_A, tmp / "k")
    ref_sha = subprocess.run(["git", "rev-parse", a.ref], cwd=RAIZ, capture_output=True, text=True).stdout.strip()
    R = L.Reglas()
    import banco_paridad as bp
    k, rep_k = L.cargar_carpeta(tmp / "k")
    kg, rep_kg = L.cargar_carpeta(tmp / "kgemelo")
    coords = bp._coords_por_volcan()
    inner = bp.inner_desde_html()
    es_noche = lambda vol, b, dt: not bp.es_pasada_diurna_descartada(b, coords[vol][0], coords[vol][1], dt)  # noqa
    filas = [f for f in L.armar_pasadas({}, k, kg, es_noche, inner) if f["tramo"] != "R25"]
    L.tabla_publica(R, filas, L._predicado_por_defecto(R))
    ck = L.c_k(filas, [], L.TIER_A, L.sobras_kgemelo(kg, k))
    puro = L.c_k_puro(filas)
    idx = {(f["vol"], f["dt"], f["b"]): f for f in filas}
    detalle = []
    for vol, dt, b in ck["diferencias"]:
        f = idx[(vol, dt, b)]
        pv = lambda r: ((r or {}).get("primary_cluster") or {}).get("vrp_mw")  # noqa: E731
        detalle.append({"vol": vol, "dt": dt, "b": b, "sensor": f["sensor"], "tramo": f["tramo"],
                        "pub_k": f["_t"]["K"]["pub"], "pub_kg": f["_t"].get("KG", {}).get("pub"),
                        "vrp_k": pv(f["k_rec"]), "vrp_kg": pv(f["kg_rec"])})
    por_sensor = collections.Counter(d["b"] for d in detalle)
    control = control_puede_fallar(L, filas, kg, k)
    out = {"ref_k_disco": ref_sha, "d3": str(a.d3), "trozos_d3": trozos, "records_kgemelo_por_volcan": n_kg,
           "repetidas_k": len(rep_k), "repetidas_kgemelo": len(rep_kg),
           "pasadas_con_kgemelo": ck["n"], "diferencias_por_sensor": dict(por_sensor), "detalle": detalle,
           "c_k_sin_excepciones": ck["estado"], "cobertura_kgemelo": ck["cobertura_kgemelo"],
           "n_sobras_kgemelo": ck["n_sobras_kgemelo"], "sobras_kgemelo": ck["sobras_kgemelo"],
           "c_k_puro": puro["estado"], "tope_por_sensor": L.TOPE_EXCEPCIONES_CK, "control_puede_fallar": control}
    Path(a.salida).write_text(json.dumps(out, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    print("K de disco:", a.ref, ref_sha[:9], "| pasadas con K-gemelo:", ck["n"])
    print("diferencias por sensor:", dict(por_sensor), "| tope:", L.TOPE_EXCEPCIONES_CK)
    print("c_k sin excepciones:", ck["estado"])
    print("cobertura K-gemelo:", ck["cobertura_kgemelo"]["estado"], "| sobras K-gemelo:", ck["n_sobras_kgemelo"])
    print("c_k_puro:", puro["estado"])
    print("control (A116, A110):", control)
    for d in detalle[:40]:
        print("  ", d)
    return 0


if __name__ == "__main__":
    sys.exit(main())
