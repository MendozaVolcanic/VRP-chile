# -*- coding: utf-8 -*-
"""Informativo del re-sello S196: qué respaldo tienen las publicaciones diurnas de Nevados de Chillán en desarrollo.

POR QUÉ. Hasta el re-sello, la caja de NHI-v1 de Chillán estaba a 61 km, junto a Antuco, y sus publicaciones sólo
podían ser R por la cumbre de MIROVA a ±12 h (respaldo b). Con la caja corregida (NHI-v1 en 4d24515abe1e) también puede
respaldarlas SWIR (respaldo a). Las etiquetas no cambian (`salida_desarrollo.txt` sale igual), pero este script cuenta,
con las mismas funciones del evaluador sellado y sin modificarlo, cuántas tienen cada respaldo, para que el número del
PREREGISTRO no se transcriba a mano (S91). No decide nada.

Uso: mismos argumentos que `evaluar.py evaluar --fase desarrollo ...` (ver PREREGISTRO §8); escribe en pantalla.
"""
import collections
import importlib.util
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("evaluar_vdia", AQUI / "evaluar.py")
E = importlib.util.module_from_spec(_spec)
sys.modules["evaluar_vdia"] = E
_spec.loader.exec_module(E)
_ORIGINAL = E.evaluar_fase


def _con_conteo(recs, prod, pasadas, cajas, nhi, inner, ventanas, vols):
    v, det = _ORIGINAL(recs, prod, pasadas, cajas, nhi, inner, ventanas, vols)
    pidx = E.indexar_pasadas(pasadas)
    pvol = collections.defaultdict(list)
    for p in pasadas:
        pvol[p["vol"]].append(p)
    c = collections.Counter()
    vol = "NevadosDeChillan"
    for r in recs:
        if not (r["es_dia"] and r["b"] in E.SENSORES_VIIRS and r["vol"] == vol and r["pub"]
                and E.en_ventanas(r["dt"].date().isoformat(), ventanas)):
            continue
        pas = E.pasada_de(pidx, r)
        cumbre = E.cumbre_alertada_cerca(pvol[vol], r["dt"], inner[vol])
        e = E.etiquetar(r, pas, inner[vol], cajas.get(vol), nhi.get(vol), cumbre)
        sw = E.respaldo_swir(r, cajas.get(vol), nhi.get(vol))
        c[(e, "swir" if sw else "-", "cumbre" if (pas is None and cumbre) else "-",
           "en_caja" if E.en_caja(r.get("lat"), r.get("lon"), cajas[vol]) else "fuera_caja")] += 1
    print("CHILLAN (etiqueta, respaldo SWIR, respaldo cumbre de MIROVA sin pasada, posicion en caja NHI): publicaciones")
    for k, n in sorted(c.items()):
        print("  %s %d" % (k, n))
    print("caja NHI de Chillán usable: %s; commit de las cajas: %s" % (
        cajas[vol]["usable"], E.json.loads((AQUI / "nhi_cajas.json").read_text(encoding="utf-8"))["commit_nhi"]))
    return v, det


if __name__ == "__main__":
    E.evaluar_fase = _con_conteo
    sys.exit(E.main(sys.argv[1:]))
