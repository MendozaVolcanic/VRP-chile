# -*- coding: utf-8 -*-
"""Verificador V750-C, tercera tanda: el brazo 'fondo de anillo' y la compuerta usan el anillo inner_radius_km..25 km
(oraculo_ablacion.py l. 177 y 222), pero K usa 5..25 km fijo (pipeline.profile BG_INNER_KM = 5.0, BG_OUTER_KM = 25.0,
process_viirs_mod.py l. 539). Aqui se recalcula la razon contra MIROVA con el anillo de K de verdad (5..25) en las
alertas que deciden, y se compara con la del auditor.

Pregunta 1: si el anillo no cambiara nada, las dos medianas coinciden exactamente en los volcanes con inner = 5
(Isluga, Lascar, Chillan) y difieren en PCC (20), Lastarria y PP (3), Tupungatito (7). Pregunta 2: control positivo,
PCC con anillo 20..25 contra 5..25 tiene que cambiar.
Uso: python medir3.py --insumos <carpeta> --grillas <dir>
"""
from __future__ import annotations

import argparse
import collections
import statistics
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import ablacion as A  # noqa: E402
import oraculo_ablacion as OA  # noqa: E402
import banco_paridad as B  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--insumos", required=True, type=Path)
    ap.add_argument("--grillas", required=True, type=Path)
    a = ap.parse_args()
    res, obj = A.cargar(a.insumos)
    inner = B.inner_desde_html()
    ids = [i for i, r in res.items() if r.get("estado") == "ok" and r.get("oraculo") and r.get("dayflag") == 0
           and obj[i]["clase"] != "diurna"]
    pos = [i for i in ids if obj[i]["lab"] == "pos" and obj[i].get("decide")]
    print("alertas que deciden:", len(pos))
    out = collections.defaultdict(lambda: collections.defaultdict(list))
    pub = collections.Counter()
    for i in pos:
        r, o = res[i], obj[i]
        z = np.load(A.buscar_grilla(a.grillas, i))
        m13, m15 = z["m13"], z["m15"]
        inn = inner[o["volcan"]]
        for b, ring, et in (("O_fanillo", inn, "inner..25 (auditor)"), ("O_fanillo", 5.0, "5..25 (K)"), ("O_comp1", inn, "inner..25 (auditor)"), ("O_comp1", 5.0, "5..25 (K)")):
            P = A.piezas(b)
            mask = OA.detectar(m13, m15, r["dayflag"], r["sunglint"], P, inner_km=ring)
            v = OA.vrp(m13, mask, P, inner_km=ring)
            rr, cc = np.nonzero(mask)
            pix = [(int(x), int(y), float(m13[x, y])) for x, y in zip(rr, cc)]
            key = f"{b} anillo {et}"
            if A.publica(v["npix"], v["VRP_MW"], pix, inn):
                pub[key] += 1
                if o["mirova_vrp"]:
                    out[key][o["volcan"]].append(v["VRP_MW"] / o["mirova_vrp"])
    q = lambda v: f"{statistics.median(v):.3f} [q1 {np.percentile(v, 25):.3f}, q3 {np.percentile(v, 75):.3f}] n={len(v)}"
    for key in sorted(out):
        todo = [x for v in out[key].values() for x in v]
        print(f"\n{key}: publica {pub[key]}/{len(pos)} | razon global {q(todo)} | entre 0,8 y 1,25: {sum(1 for x in todo if 0.8 <= x <= 1.25)}/{len(todo)}")
        for vol, v in sorted(out[key].items()):
            print(f"   {vol:22s} inner {inner[vol]:4.1f} razon {q(v)}")


if __name__ == "__main__":
    main()
