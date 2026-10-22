# -*- coding: utf-8 -*-
"""S159 frente N, paso 4 (R2.4, D17 fase 0): el oráculo de MIROVA con cada grilla e interpolador contra la tabla de
MIROVA, en las mismas pasadas del lote.

POR QUÉ. GEO (experiments/_s159/geo/INFORME.md H1) midió en los encabezados de los TIF que la grilla de 750 m de
MIROVA tiene su esquina 187,5 m al oeste y al sur de la de 375 m, y que la prueba con gránulos de R2 usó la de 375 m.
Si la grilla de GEO es la de MIROVA, el oráculo sobre ella tiene que reproducir lo que MIROVA publicó (detección y
magnitud) mejor que sobre la de R2. Es una predicción que puede fallar: el oráculo no mira la tabla de MIROVA.

Pregunta 1: si la grilla no importara, las variantes darían lo mismo; se imprime cuántas pasadas cambian.
Pregunta 2: si el oráculo estuviera muerto, no detectaría en las protegidas (Chillán 13 MW); se cuenta.
«Alerta del oráculo» (SUPUESTO declarado, no es la regla del scraper): al menos un píxel alertado, VRP > 0, y el
píxel alertado de mayor radiancia M13 a no más de inner_radius_km (el radio que el tablero y las láminas «Dist» de
MIROVA usan para el volcán, GEO H4) del centro de la grilla.
Uso: python 04_oraculo_grilla.py --art <carpeta del run>
"""
from __future__ import annotations

import argparse
import collections
import json
import statistics
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import banco_paridad as B  # noqa: E402

VARS = ("geo_linear", "geo_nearest", "geo_cubic", "r2_linear", "r2_nearest", "geo_linear_anillo_sensible")


def alerta(o, inner):
    if not o or not o.get("npix") or (o.get("vrp_mw") or 0) <= 0:
        return False
    return max(o["pixeles"], key=lambda p: p[4])[3] <= inner


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--art", required=True, nargs="+")
    a = ap.parse_args()
    obj = {o["id"]: o for o in json.loads((AQUI / "objetivos_n.json").read_text(encoding="utf-8"))}
    res = {}
    for d in a.art:
        for f in sorted(Path(d).rglob("resultados_*.json")):
            for r in json.loads(f.read_text(encoding="utf-8")):
                if r.get("estado") == "ok" or r["id"] not in res:   # un redisparo ok reemplaza a un SIN DATO
                    res[r["id"]] = r
    inner = B.inner_desde_html()
    ok = [i for i, r in res.items() if r.get("estado") == "ok" and r.get("oraculo") and obj[i]["clase"] != "diurna"]
    L = []
    pr = lambda *x: (print(*x), L.append(" ".join(str(y) for y in x)))
    pr(f"pasadas con oraculo ok (nocturnas): {len(ok)} de {sum(1 for o in obj.values() if o['clase'] != 'diurna')}")
    pos = [i for i in ok if obj[i]["lab"] == "pos" and obj[i]["decide"]]
    prot = [i for i in pos if obj[i]["protegida"]]
    neg = [i for i in ok if obj[i]["lab"] == "neg_limpio"]
    pr(f"alertas que deciden {len(pos)} (protegidas {len(prot)}), negativos limpios {len(neg)} (sin pesos)")
    pr("variante | alertas detectadas | protegidas detectadas | neg con alerta del oraculo (crudo y ponderado) | "
       "razon O/MIROVA en alertas detectadas: mediana [q1, q3] n, y fraccion entre 0,8 y 1,25")
    for v in VARS:
        det = [i for i in pos if alerta(res[i]["oraculo"].get(v), inner[obj[i]["volcan"]])]
        dp = [i for i in prot if i in det]
        dn = [i for i in neg if alerta(res[i]["oraculo"].get(v), inner[obj[i]["volcan"]])]
        wn = sum(obj[i]["peso"] for i in dn)
        wt = sum(obj[i]["peso"] for i in neg)
        rz = sorted(res[i]["oraculo"][v]["vrp_mw"] / obj[i]["mirova_vrp"] for i in det if obj[i]["mirova_vrp"])
        n = len(rz)
        cerca = sum(1 for x in rz if 0.8 <= x <= 1.25)
        pr(f"  {v:28s} {len(det):3d}/{len(pos)} | {len(dp):3d}/{len(prot)} | {len(dn):3d}/{len(neg)} "
           f"({wn:.1f} de {wt:.1f} ponderado) | "
           + (f"{statistics.median(rz):.3f} [{rz[n // 4]:.3f}, {rz[(3 * n) // 4]:.3f}] n={n}, "
              f"{cerca}/{n} entre 0,8 y 1,25" if n else "sin datos"))
    # por número de píxeles del oráculo (geo_linear y r2_linear)
    for v in ("geo_linear", "r2_linear"):
        for et, c in (("1 px", lambda n: n == 1), ("2-4 px", lambda n: 2 <= n <= 4), ("5+ px", lambda n: n >= 5)):
            rz = sorted(res[i]["oraculo"][v]["vrp_mw"] / obj[i]["mirova_vrp"] for i in pos
                        if alerta(res[i]["oraculo"].get(v), inner[obj[i]["volcan"]]) and obj[i]["mirova_vrp"]
                        and c(res[i]["oraculo"][v]["npix"]))
            n = len(rz)
            pr(f"  {v} {et}: " + (f"{statistics.median(rz):.3f} [{rz[n // 4]:.3f}, {rz[(3 * n) // 4]:.3f}] n={n}"
                                  if n else "sin datos"))
    # por cenit
    for v in ("geo_linear", "r2_linear"):
        for z in ("z<=40", "z>40"):
            ps = [i for i in pos if obj[i].get("estrato_z") == z]
            det = [i for i in ps if alerta(res[i]["oraculo"].get(v), inner[obj[i]["volcan"]])]
            rz = sorted(res[i]["oraculo"][v]["vrp_mw"] / obj[i]["mirova_vrp"] for i in det if obj[i]["mirova_vrp"])
            n = len(rz)
            pr(f"  {v} {z}: detecta {len(det)}/{len(ps)}; razon " + (f"{statistics.median(rz):.3f} n={n}" if n else "-"))
    # cambios entre grillas, pasada a pasada
    cam = collections.Counter()
    for i in pos + neg:
        g = alerta(res[i]["oraculo"].get("geo_linear"), inner[obj[i]["volcan"]])
        r = alerta(res[i]["oraculo"].get("r2_linear"), inner[obj[i]["volcan"]])
        cam[(obj[i]["lab"], g, r)] += 1
    pr("cambios de alerta geo_linear contra r2_linear (lab, geo, r2): n", dict(cam))
    # las dos alertas débiles de R2 y los casos de ROI
    for key in (("Lascar", "2026-09-26 05:48"), ("Chaiten", "2026-10-06 05:30"), ("Lascar", "2026-10-08 05:42"),
                ("PuyehueCordonCaulle", "2026-10-10 05:54"), ("PuyehueCordonCaulle", "2026-10-16 05:42"),
                ("Tupungatito", "2026-08-21 05:48"), ("Villarrica", "2026-09-19 05:48"),
                ("NevadosDeChillan", "2026-10-10 05:54")):
        for i, o in obj.items():
            if (o["volcan"], o["hora_utc"]) == key and i in res:
                orc = res[i].get("oraculo") or {}
                pr(f"  {key} MIROVA {o.get('mirova_vrp')} | estado {res[i].get('estado')} | " + " | ".join(
                    f"{n} {x.get('npix')}px {None if x.get('vrp_mw') is None else round(x['vrp_mw'], 3)}"
                    + (f" banda {[round(b, 3) for b in x['vrp_banda']]}" if x.get("vrp_banda") else "")
                    for n, x in orc.items()))
    # diurnas
    for i, o in obj.items():
        if o["clase"] == "diurna":
            r = res.get(i, {})
            pr(f"  diurna {o['volcan']} {o['hora_utc']} MIROVA {o.get('mirova_vrp')} estado {r.get('estado')} "
               f"dayflag {r.get('dayflag')} sunglint {r.get('sunglint')} | " + " | ".join(
                f"{n} {x.get('npix')}px {x.get('vrp_mw')} motivo {x.get('motivo_vacio')}"
                for n, x in (r.get("oraculo") or {}).items()))
    (AQUI / "04_oraculo_grilla_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
