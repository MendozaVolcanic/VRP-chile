# -*- coding: utf-8 -*-
"""S158: cuantas alertas perdidas de VIIRS 750 son noches perdidas para el operador (A94), sin red.

POR QUE. El operador vive la alerta por noche y por volcan, no por pasada: una pasada de VIIRS 750 perdida no deja al
volcan sin alerta si otra pasada de esa noche (VIIRS 750, VIIRS 375 o MODIS) si se publica. S145 midio, con el detector
anterior, que el rescate del crater en 0,0 MW no recuperaba ninguna noche. Con K hay que volver a medirlo.

Lee `perdidas_v750.json` (de listar_perdidas.py) y todos los records nocturnos de produccion con el predicado del
tablero (banco_paridad.cargar_nuestros, node). Noche = fecha UTC de la pasada, la misma unidad del banco.
"""
from __future__ import annotations

import collections
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import listar_perdidas  # noqa: E402,F401  (instala sys.path del repo y la salida utf-8)
import banco_paridad as bp  # noqa: E402

VENTANA = (bp.INICIO_DEFECTO, "2026-10-21")


def main():
    d = json.loads((HERE / "perdidas_v750.json").read_text(encoding="utf-8"))
    coords = bp._coords_por_volcan()
    recs = bp.cargar_nuestros(coords, bp.inner_desde_html(), VENTANA)
    pub = collections.defaultdict(set)   # (vol, noche) -> buckets que publican
    for r in recs:
        if r["pub"]:
            pub[(r["vol"], r["noche"])].add(r["b"])
    c = collections.Counter()
    noches_solas = set()
    for e in d["perdidas"]:
        k = (e["vol"], e["noche"])
        b = pub.get(k, set())
        if "VIIRS750" in b:
            c["otra_pasada_V750_publica"] += 1
        elif b:
            c["solo_otro_sensor_publica:" + "+".join(sorted(b))] += 1
        else:
            c["noche_sin_ninguna_publicacion"] += 1
            noches_solas.add(k)
    print(f"perdidas V750 {len(d['perdidas'])}, por cobertura de su noche-volcan:")
    for k, v in sorted(c.items()):
        print(f"  {k:55s} {v}")
    por_mec = collections.Counter(e["mecanismo"] for e in d["perdidas"] if (e["vol"], e["noche"]) in noches_solas)
    print(f"noches-volcan sin ninguna publicacion: {len(noches_solas)}; pasadas por mecanismo: {dict(por_mec)}")
    print("  por volcan:", dict(collections.Counter(v for v, _ in noches_solas)))
    # Verificador S158: la misma pasada en banda I (mismo satelite, sensor sin el sufijo _750, a +-2 min) publica.
    i_pub = collections.defaultdict(list)
    for r in recs:
        if r["b"] == "VIIRS375" and r["pub"]:
            i_pub[(r["vol"], r["sensor"])].append(r["dt"])
    misma = collections.Counter()
    for e in d["perdidas"]:
        t = datetime.strptime(e["dt"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        ok = any(abs((t - x).total_seconds()) <= bp.TOL_S
                 for x in i_pub.get((e["vol"], e["sensor"].replace("_750", "")), []))
        misma[f"{e['mecanismo']}|banda_I_publica={ok}"] += 1
    print("misma pasada en banda I publica, por mecanismo:", dict(sorted(misma.items())))
    for c_ in d["sin_record"]:
        k = (c_["vol"], c_["fecha_utc"][:10])
        print(f"alerta sin record: {c_['vol']} {c_['fecha_utc']} {c_['mirova_vrp_mw']} MW, protegida {c_['protegida']}; "
              f"sensores que publican esa noche: {sorted(pub.get(k, set()))}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
