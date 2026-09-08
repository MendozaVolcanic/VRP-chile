# -*- coding: utf-8 -*-
"""Fusiona los artefactos de los dos chunks del A/B en una sola ventana por volcán y brazo.

POR QUÉ. Cada job del A/B arranca de un checkout limpio, así que el artefacto que sube contiene
**sólo la ventana que ese chunk procesó**, aunque el segundo se haya lanzado con
`overwrite=false`: lo que ese flag preserva es el JSON del repo, no el resultado del chunk
anterior, que nunca se commitea. Sin fusionar, evaluar el chunk 2 mide medio experimento y el
número sale con el denominador equivocado.

QUÉ HACE. Une los records de los dos artefactos por (datetime_utc, sensor) —la clave de una
pasada— y avisa si un mismo par aparece en los dos chunks con contenido distinto, que sería
señal de que las ventanas se solapan y hay que mirarlo antes de confiar en el resultado.

Uso:
    python experiments/_s135_ab_d1d2/fusionar_chunks.py --c1 <dir chunk1> --c2 <dir chunk2> \
        --out <dir fusionado>
"""
import argparse
import io
import json
import os
import shutil
import sys

BRAZOS = ["_s135_ab_a_control", "_s135_ab_b_nokeeppeak", "_s135_ab_c_cond",
          "_s135_ab_d_ambos", "_s135_ab_e_sp_off"]
VOLCANES = ["Isluga", "Lascar", "Lastarria", "PuyehueCordonCaulle", "PlanchonPeteroa",
            "Tupungatito"]


def ruta(base, perfil, vol):
    for cand in (os.path.join(base, f"s135ab-{perfil}-{vol}", f"{vol}.json"),
                 os.path.join(base, perfil, f"{vol}.json")):
        if os.path.exists(cand):
            return cand
    return None


def main():
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--c1", required=True)
    ap.add_argument("--c2", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    total, conflictos, faltantes = 0, [], []
    print(f"{'volcán':<22}{'brazo':<16}{'chunk1':>8}{'chunk2':>8}{'fusión':>8}  ventana")
    for vol in VOLCANES:
        for perfil in BRAZOS:
            p1, p2 = ruta(args.c1, perfil, vol), ruta(args.c2, perfil, vol)
            if not p1 or not p2:
                faltantes.append(f"{perfil}/{vol} ({'sin chunk1' if not p1 else 'sin chunk2'})")
                continue
            d1 = json.load(open(p1, encoding="utf-8"))
            d2 = json.load(open(p2, encoding="utf-8"))
            r1, r2 = d1["records"], d2["records"]
            unido = {}
            for r in r1:
                unido[(r["datetime_utc"], r["sensor"])] = r
            for r in r2:
                k = (r["datetime_utc"], r["sensor"])
                if k in unido and json.dumps(unido[k], sort_keys=True) != json.dumps(r, sort_keys=True):
                    conflictos.append(f"{perfil}/{vol} {k[0]} {k[1]}")
                unido[k] = r      # el chunk 2 gana si hubiera solape
            recs = sorted(unido.values(), key=lambda r: (r["datetime_utc"], r["sensor"]))
            salida = dict(d1)
            salida["records"] = recs
            dest = os.path.join(args.out, f"s135ab-{perfil}-{vol}")
            os.makedirs(dest, exist_ok=True)
            json.dump(salida, open(os.path.join(dest, f"{vol}.json"), "w", encoding="utf-8"),
                      indent=1, ensure_ascii=False)
            f = sorted({r["datetime_utc"][:10] for r in recs})
            print(f"{vol:<22}{perfil.replace('_s135_ab_',''):<16}{len(r1):>8}{len(r2):>8}"
                  f"{len(recs):>8}  {f[0]}..{f[-1]}")
            total += 1
    print(f"\n{total} archivos fusionados en {args.out}")
    if faltantes:
        print("FALTAN:", ", ".join(faltantes))
    if conflictos:
        print(f"⚠ {len(conflictos)} pasadas presentes en LOS DOS chunks con contenido distinto "
              f"(ventanas solapadas): {conflictos[:5]}")
    else:
        print("Sin solape entre chunks: las ventanas son disjuntas, como deben.")


if __name__ == "__main__":
    main()
