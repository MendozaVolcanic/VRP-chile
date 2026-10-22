# -*- coding: utf-8 -*-
"""Verificador S159 PORTES, v02: control A109 de la magnitud. ¿La coincidencia port/MIROVA es propia de la
pasada (mismo gránulo) o sólo refleja que el volcán emite parecido toda la noche?

Se compara, para cada alerta de la muestra que el port publica (caja física), tres razones:
  mismo  = VRP del port / VRP de MIROVA de la MISMA pasada (lo que informó el frente),
  otra   = VRP del port / VRP de MIROVA de OTRA pasada de la misma noche (otro gránulo, mismo volcán y sensor),
  nulo   = VRP de MIROVA de la misma pasada / VRP de MIROVA de la otra (variabilidad natural del volcán).
Si «mismo» es mucho más estrecha que «otra» y que «nulo», la coincidencia es de la pasada (el código replica el
cálculo); si las tres se parecen, la coincidencia de magnitud no prueba nada sobre el código.

Pregunta 1: si el port diera un número fijo cercano a la mediana de MIROVA, «mismo» y «otra» serían iguales: la
medición lo vería. Pregunta 2: sin pares de otra pasada, n = 0 y se dice SIN DATO.
Separación: VIIRS 375 de 30 a 180 min; MODIS de 60 min a 8 h (Terra y Aqua de la misma noche).
"""
from __future__ import annotations

import json
import math
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np

ROOT = Path(r"C:/vrp-trabajo/s159-n")
PORTES = ROOT / "experiments/_s159/portes"
ART = Path(r"D:/vrp-trabajo/temporales/s159_portes/run_39712862945")
REF = Path(r"D:/vrp-trabajo/temporales/s159_portes/ref")
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
import banco_paridad as B  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

SEP = {"VIIRS375": (30, 180), "MODIS": (60, 480)}


def resumen(nombre, rr):
    if not rr:
        print(f"   {nombre}: SIN DATO")
        return None
    a = np.abs(np.log(rr))
    q = np.percentile(rr, [25, 50, 75])
    out = {"n": len(rr), "med": float(q[1]), "q1": float(q[0]), "q3": float(q[2]),
           "med_abs_log": float(np.median(a)), "a5": int(sum(abs(r - 1) < 0.05 for r in rr)),
           "banda": int(sum(0.8 <= r <= 1.25 for r in rr))}
    print(f"   {nombre}: n {out['n']} mediana {out['med']:.3f} [{out['q1']:.3f}, {out['q3']:.3f}] "
          f"mediana|ln| {out['med_abs_log']:.3f}; a <5 %: {out['a5']} ({out['a5']/len(rr):.0%}); "
          f"en [0,8;1,25]: {out['banda']} ({out['banda']/len(rr):.0%})")
    return out


def main():
    obj = {o["id"]: o for o in json.loads((PORTES / "objetivos_portes.json").read_text(encoding="utf-8"))}
    res = {}
    for f in sorted(ART.rglob("resultados_*.json")):
        for r in json.loads(f.read_text(encoding="utf-8")):
            if r.get("estado") == "ok":
                res[r["id"]] = r
    coords = B._coords_por_volcan()
    filas = cargar_referencia_unificada(REF / "registro_vrp_consolidado.csv", REF / "registro_vrp_ocr.csv")
    por_vb, _ns, _nv, n_ref = B.indexar_referencia(filas, coords, ("2026-03-01", "2026-10-21"), regla_minimas="SN")
    print("filas de referencia nocturnas indexadas:", n_ref)
    salida = {}
    for b in ("VIIRS375", "MODIS"):
        for fuente in ("combinada", "tabla_sola"):
            mismo, otra, nulo = [], [], []
            for i, o in sorted(obj.items()):
                if o["b"] != b or o["lab"] != "pos" or i not in res:
                    continue
                p = res[i]["port"]["fisica"]
                if not p.get("npix") or not o["mirova_vrp"]:
                    continue
                al = [f for f in o["mirova"] if B.es_alerta(f["tipo"]) and (fuente == "combinada" or f["source"] == "CONS")]
                if not al:
                    continue
                m_same = max(f["vrp_mw"] or 0 for f in al)
                if not m_same:
                    continue
                t = datetime.strptime(o["hora_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
                cand = []
                for dt, f in por_vb.get((o["volcan"], b), []):
                    s = abs((dt - t).total_seconds()) / 60
                    if SEP[b][0] <= s <= SEP[b][1] and B.es_alerta(f["tipo"]) and (f["vrp_mw"] or 0) > 0 \
                            and (fuente == "combinada" or f["source"] == "CONS"):
                        cand.append((s, f["vrp_mw"]))
                if not cand:
                    continue
                s, m_other = min(cand)            # la otra pasada más cercana en el tiempo
                mismo.append(p["vrp_mw"] / m_same)
                otra.append(p["vrp_mw"] / m_other)
                nulo.append(m_same / m_other)
            print(f"\n== {b} ({fuente}), alertas que el port encuentra con otra pasada de MIROVA a {SEP[b]} min")
            salida[f"{b}|{fuente}"] = {"mismo": resumen("mismo (port/MIROVA misma pasada)", mismo),
                                        "otra": resumen("otra  (port/MIROVA otra pasada) ", otra),
                                        "nulo": resumen("nulo  (MIROVA/MIROVA)          ", nulo)}
    Path(__file__).with_suffix(".json").write_text(json.dumps(salida, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
