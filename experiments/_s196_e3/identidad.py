#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Prueba de identidad de la comparación diaria antes y después de separar el día de MODIS (S196, E3).

POR QUÉ. Agregar la franja diurna no puede mover los números nocturnos que ya se publicaron y que se citan (tabla del §2 E3
de docs/CAMINO_INDEPENDENCIA_MIROVA.md). Antes del primer record MODIS diurno (2026-11-15) no hay nada diurno que separar,
así que la versión nueva tiene que dar exactamente lo mismo que la de main en esos días. Después sí cambia, y a propósito:
la versión de main contaba alertas diurnas de MIROVA en la noche de la misma fecha. Esta prueba mide las dos cosas.

Corre las dos versiones con los mismos datos (records de producción, guardias, caché de K y la misma referencia de MIROVA
bajada una vez) y compara:
  A. `--hoy 2026-11-14`: salida completa (resultados y noches) idéntica, salvo `meta` (fechas de generación) y las claves
     nuevas (`dias`, `resultados[*|dia|*]`).
  B. `--hoy` de la corrida diaria: las ventanas «historia» (todas terminan antes del 15-nov) idénticas, y las filas de
     noches anteriores al 15-nov idénticas; se informa qué cambia desde el 15-nov.

Uso: python experiments/_s196_e3/identidad.py --viejo <comparacion_via_k.py de main> --cons C --ocr O --hoy AAAA-MM-DD
     --tmp <carpeta temporal> --out experiments/_s196_e3/identidad.json
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT), str(ROOT / "scripts")]
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import comparacion_via_k as nuevo  # noqa: E402

CORTE = "2026-11-15"   # primer record MODIS diurno de producción (auto_audit_weekly.inicio_dia_modis)


def cargar_viejo(path):
    spec = importlib.util.spec_from_file_location("comparacion_via_k_main", path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def correr(mod, out, hoy, cons, ocr):
    args = ["--prod", str(ROOT / "data" / "mirova_equivalent"), "--guardia-modis", str(ROOT / "data" / "guardia_k_modis"),
            "--guardia-viirs", str(ROOT / "data" / "guardia_k_viirs"),
            "--cache-k", str(ROOT / "data" / "audit_continuous" / "comparacion_k_historia_cache.json"),
            "--cons", cons, "--ocr", ocr, "--hoy", hoy, "--out", str(out)]
    assert mod.main(args) == 0
    return json.loads(Path(out).read_text(encoding="utf-8"))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--viejo", required=True)
    ap.add_argument("--cons", required=True)
    ap.add_argument("--ocr", required=True)
    ap.add_argument("--hoy", required=True)
    ap.add_argument("--tmp", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    tmp = Path(a.tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    viejo = cargar_viejo(a.viejo)
    # Sólo el nombre del archivo: la salida se commitea y no debe llevar rutas del computador de nadie. El sha de
    # Mirova-v1 de la referencia usada se anota a mano en IDENTIDAD.md y en identidad.json.
    inf = {"corte": CORTE, "hoy": a.hoy, "referencia": {"cons": Path(a.cons).name, "ocr": Path(a.ocr).name}}

    # A. Día de corte: todo idéntico.
    va = correr(viejo, tmp / "viejo_corte.json", "2026-11-14", a.cons, a.ocr)
    na = correr(nuevo, tmp / "nuevo_corte.json", "2026-11-14", a.cons, a.ocr)
    res_n = {k: v for k, v in na["resultados"].items() if "|dia|" not in k}
    inf["A_hoy_2026_11_14"] = {
        "resultados_identicos": va["resultados"] == res_n,
        "claves_resultados": len(res_n),
        "noches_identicas": va["noches"] == na["noches"], "n_noches": len(na["noches"]["filas"]),
        "dias_nuevo": len(na["dias"]["filas"]), "franjas_nuevo": na["meta"]["franjas"]}

    # B. Hoy: historia y noches previas al corte idénticas; lo posterior se informa.
    vb = correr(viejo, tmp / "viejo_hoy.json", a.hoy, a.cons, a.ocr)
    nb = correr(nuevo, tmp / "nuevo_hoy.json", a.hoy, a.cons, a.ocr)
    hist = [k for k in vb["resultados"] if "|historia|" in k]
    pre = lambda d: [f for f in d["noches"]["filas"] if f[3] < CORTE]  # noqa: E731
    post = lambda d: {tuple(f[:4]): f for f in d["noches"]["filas"] if f[3] >= CORTE}  # noqa: E731
    pv, pn = post(vb), post(nb)
    cambios = []
    for k in sorted(pv.keys() | pn.keys(), key=lambda x: (x[3], x[0], x[1])):
        if pv.get(k) != pn.get(k):
            cambios.append({"clave": list(k), "main": pv.get(k), "nuevo": pn.get(k)})
    adop = {}
    for k in vb["resultados"]:
        if "|adopcion|" in k:
            a_, b_ = vb["resultados"][k], nb["resultados"][k]
            adop[k] = {"igual": a_ == b_, "main": {"pares": a_["n_pasadas_pareadas"], "via": a_["via"], "k": a_["k"]},
                       "nuevo": {"pares": b_["n_pasadas_pareadas"], "via": b_["via"], "k": b_["k"]}}
    inf["B_hoy"] = {
        "historia_identica": all(vb["resultados"][k] == nb["resultados"][k] for k in hist), "claves_historia": len(hist),
        "noches_previas_identicas": pre(vb) == pre(nb), "n_noches_previas": len(pre(nb)),
        "noches_desde_corte": {"main": len(pv), "nuevo": len(pn), "filas_distintas": len(cambios)},
        "filas_distintas": cambios, "adopcion": adop,
        "dia": {k: v for k, v in nb["resultados"].items() if "|dia|" in k},
        "dias_filas": nb["dias"], "franjas": nb["meta"]["franjas"]}
    Path(a.out).write_text(json.dumps(inf, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps({"A": {k: v for k, v in inf["A_hoy_2026_11_14"].items() if k != "franjas_nuevo"},
                      "B": {k: inf["B_hoy"][k] for k in ("historia_identica", "claves_historia",
                                                         "noches_previas_identicas", "n_noches_previas",
                                                         "noches_desde_corte")}}, ensure_ascii=False, indent=1))
    ok = (inf["A_hoy_2026_11_14"]["resultados_identicos"] and inf["A_hoy_2026_11_14"]["noches_identicas"]
          and inf["B_hoy"]["historia_identica"] and inf["B_hoy"]["noches_previas_identicas"])
    print("IDENTIDAD", "OK" if ok else "FALLA")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
