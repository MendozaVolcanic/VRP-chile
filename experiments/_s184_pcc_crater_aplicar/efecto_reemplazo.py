# -*- coding: utf-8 -*-
"""Efecto del reemplazo de la serie VIIRS 750 de Cordón Caulle (S184): cuántas pasadas cambian y cómo.

POR QUÉ. Antes de pedir el sí para escribir en data/, se mide qué cambia: pares, potencia distinta, pasadas que ganan o
pierden detección, el caso que motivó #999 (2026-10-21 05:48 NOAA-21) y dos pasadas de ejemplo con su diagnóstico.
«Potencia distinta de 0» no es el predicado de publicación del tablero; es sólo el valor del record.

Uso: python efecto_reemplazo.py <serie publicada PuyehueCordonCaulle.json>
"""
import collections
import gzip
import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import aplicar_pcc_v750 as ap  # noqa: E402

sys.stdout.reconfigure(encoding="utf-8")
o = json.load(open(sys.argv[1], encoding="utf-8"))
u = json.loads(gzip.decompress(ap.UNION.read_bytes()))
pub = {ap._clave(r): r for r in o["records"] if ap.es_v750(r["sensor"])}
nue = {ap._clave(r): r for r in u["records"] if ap.es_v750(r["sensor"])}
com = [k for k in pub if k in nue]


def v(r):
    return r.get("vrp_mw") or 0


dif = [(k, v(pub[k]), v(nue[k]), pub[k].get("final_hotspot_dist_km"), nue[k].get("final_hotspot_dist_km"))
       for k in com if abs(v(pub[k]) - v(nue[k])) > 1e-9]
print("pares", len(com), "potencia distinta", len(dif))
print("de >0 a 0:", sum(1 for d in dif if d[1] > 0 and d[2] == 0), "| de 0 a >0:", sum(1 for d in dif if d[1] == 0 and d[2] > 0),
      "| baja:", sum(1 for d in dif if d[2] < d[1]), "| sube:", sum(1 for d in dif if d[2] > d[1]))
print("1 MW o mas antes:", sum(1 for k in com if v(pub[k]) >= 1), "despues:", sum(1 for k in com if v(nue[k]) >= 1))
k = ("2026-10-21 05:48", "VIIRS_NOAA21_750")
print("caso 2026-10-21 05:48 NOAA21:", v(pub[k]), "->", v(nue[k]), "km", pub[k].get("final_hotspot_dist_km"), "->",
      nue[k].get("final_hotspot_dist_km"))
print("cambio de clase:", collections.Counter((pub[k].get("distance_class"), nue[k].get("distance_class"))
                                              for k in com if pub[k].get("distance_class") != nue[k].get("distance_class")))
for d in sorted(dif, key=lambda d: -abs(d[2] - d[1]))[:8]:
    print(d)
# Por qué suben (README, «Lo que se comprobó»): `crater` hace sensibles celdas que `sens` dejaba fuera de su anillo
# (BOX 0). Se cuenta, en las que suben y en las que bajan, cuántas tienen un píxel alertado que no estaba en la serie
# publicada y que cae fuera del anillo `sens`.
sys.path.insert(0, str(AQUI.parents[1]))
from pipeline.mirova_v750_codigo import caja_roi  # noqa: E402

box_sens = caja_roi("sens")


def nuevos_fuera_de_sens(kk):
    antes = {(p.get("fila"), p.get("col")) for p in pub[kk].get("anomaly_pixels") or []}
    return [(p.get("fila"), p.get("col")) for p in nue[kk].get("anomaly_pixels") or []
            if (p.get("fila"), p.get("col")) not in antes and box_sens[p["fila"], p["col"]] == 0]


sube = [d[0] for d in dif if d[2] > d[1]]
baja = [d[0] for d in dif if d[2] < d[1]]
print("suben con pixel nuevo fuera del anillo sens:", sum(1 for kk in sube if nuevos_fuera_de_sens(kk)), "de", len(sube))
print("bajan con pixel nuevo fuera del anillo sens:", sum(1 for kk in baja if nuevos_fuera_de_sens(kk)), "de", len(baja))
print("----")
for k in [("2025-08-29 05:36", "VIIRS_NOAA20_750"), ("2026-02-04 05:36", "VIIRS_SNPP_750")]:
    for nom, r in (("pub", pub[k]), ("nue", nue[k])):
        d = r.get("diag_codigo_mirova") or {}
        s1 = d.get("s1") or {}
        print(k[0], nom, "roi", d.get("roi"), "n_abs", d.get("n_abs"), "n_p1", d.get("n_p1"), "n_p2", d.get("n_p2"),
              "npix", r.get("n_anomalous_pixels"),
              "p1", {x: s1.get("pasada1", {}).get(x) for x in ("mu_nti", "sd_nti", "u_nti2")},
              "p2", {x: s1.get("pasada2", {}).get(x) for x in ("mu_nti", "sd_nti", "u_nti2")})
