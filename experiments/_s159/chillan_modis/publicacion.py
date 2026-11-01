# -*- coding: utf-8 -*-
"""Predicado del tablero (frontend/index.html, ejecutado con node por banco_paridad.correr_node) sobre los records que
armo el probe en cada brazo (P, B21, SC, MIN, MINSC). Exploratorio (adenda del PREREGISTRO.md).

Las dos preguntas del instrumento:
1. Si el predicado no publicara nada por defecto, lo veria? Si: el brazo P tiene que dar pub=1 en C1, C2 y C3 y pub=0 en
   T1 y T2 (lo publicado hoy); si no, el instrumento esta roto.
2. Un brazo sin record (calculate_vrp devolvio None) sale como SIN RECORD, no como 0.
Uso: python publicacion.py <probe_chillan.jsonl> > publicacion_salida.txt
"""
import io
import json
import os
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
import banco_paridad as BP  # noqa: E402

BRAZOS = ("P", "B21", "SC", "MIN", "MINSC")


def main():
    filas = [json.loads(x) for x in open(sys.argv[1], encoding="utf-8")]
    inner = BP.inner_desde_html()["NevadosDeChillan"]
    casos, claves = [], []
    for r in filas:
        for b in BRAZOS:
            s = ((r.get(b) or {}).get("slim"))
            if s is not None:
                casos.append([s, inner])
                claves.append((r["tag"], b))
    pred = dict(zip(claves, BP.correr_node(casos)))
    print("identidad del predicado:", BP.control_identidad_predicado(), "(esperado ([0, 1, 1, 1, 0], [1, 0]))")
    print("tag  " + "  ".join(f"{b:>22}" for b in BRAZOS))
    for r in filas:
        celdas = []
        for b in BRAZOS:
            br = r.get(b) or {}
            if (r["tag"], b) not in pred:
                celdas.append(f"{'SIN RECORD':>22}")
                continue
            p = pred[(r["tag"], b)]
            pc = (br.get("rec") or {}).get("pc") or {}
            celdas.append(f"pub={p[4]} disp={p[3]:.3f} fp={br.get('n_fp_inner')}/{br.get('sp_n_nuevos_inner')} pc={pc.get('vrp_mw')}"[:22].rjust(22))
        print(f"{r['tag']:4} " + "  ".join(celdas))
    print()
    print("detalle (tag, brazo, pub, magnitud del tablero, primer pase dentro del inner, nuevos del segundo pase dentro, "
          "pc.vrp_mw, pc.n_pixels, pc.centroid_dist_km, vrp_mw del record, distance_class):")
    for r in filas:
        for b in BRAZOS:
            br = r.get(b) or {}
            rec = br.get("rec") or {}
            p = pred.get((r["tag"], b))
            pc = rec.get("pc") or {}
            print(r["tag"], b, p[4] if p else None, round(p[3], 4) if p else None, br.get("n_fp_inner"),
                  br.get("sp_n_nuevos_inner"), pc.get("vrp_mw"), pc.get("n_pixels"), pc.get("centroid_dist_km"),
                  rec.get("vrp_mw"), rec.get("distance_class"))


if __name__ == "__main__":
    main()
