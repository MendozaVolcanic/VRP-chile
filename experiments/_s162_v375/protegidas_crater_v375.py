# -*- coding: utf-8 -*-
"""V375-A al lado de la lectura A: cuáles de las protegidas de los lotes de V375-B, C y E son «de cráter», con la
función `protegida_de_crater` de #903 (`scripts/clase_mirova.py` de main, 744d8190b).

POR QUÉ. Una protegida es una alerta de MIROVA de 1 MW o más; que el port no la publique se cuenta como pérdida (P1).
Pero la distancia de una alerta que sólo trae el OCR puede no ser de esa pasada (antes del 2026-06-13 no se medía; en
Suomi NPP, hasta el 2026-10-09, venía de otra pasada), y entonces no se sabe si MIROVA vio el cráter o una fuente
lejana. La etiqueta lo dice; NO cambia la lectura A ni ningún veredicto (PREREGISTRO_C §4, PREREGISTRO_E §5): se
imprime al lado de las protegidas perdidas.

Qué hace. Para cada protegida de los objetivos arma su pasada con `resumir_pasadas` (canal unión, regla SN) sobre las
filas de MIROVA que el propio objetivo guardó al seleccionarse (`mirova`), y le aplica `protegida_de_crater` con el
`inner_radius_km` del tablero y la plataforma del objetivo (que es la del record).

POR QUÉ esas filas y no la referencia entera: son las que clasificaron los lotes sellados. La primera versión usó la
referencia del checkout y 4 protegidas de Nevados de Chillán (15 y 16 de octubre, alertas de tabla de 13,7 a 19,1 MW a
menos de 1,2 km) no encontraron pasada: ese snapshot perdió las filas de la tabla y sólo trae OCR sin geometría. La
función se toma de main sin cambios (`--modulo`).
Uso: python -I protegidas_crater_v375.py --modulo <clase_mirova.py de origin/main>
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import sys
from datetime import datetime
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "scripts"))
import banco_paridad as bp  # noqa: E402

TOL_S = 180


def objetivos():
    out = []
    for f in (AQUI / "objetivos_v375_bc.json", AQUI / "b2" / "objetivos_v375_b2.json"):
        out += [o for o in json.loads(f.read_text(encoding="utf-8"))["pasadas"] if o["clase"] == "pos_prot"]
    out += [{**o, "lote": "S159"} for o in json.loads((RAIZ / "experiments/_s159/portes/objetivos_portes.json")
                                                      .read_text(encoding="utf-8"))
            if o.get("b") == "VIIRS375" and o["clase"] == "pos_prot"]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modulo", required=True)
    ap.add_argument("--salida", default=str(AQUI / "protegidas_crater_v375.json"))
    a = ap.parse_args()
    spec = importlib.util.spec_from_file_location("clase_mirova_main", a.modulo)
    cm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cm)
    sha = hashlib.sha256(Path(a.modulo).read_bytes()).hexdigest()
    print("protegida_de_crater de", a.modulo, "sha256", sha[:16])
    inner = bp.inner_desde_html()
    out, sin_pasada = {}, []
    for o in objetivos():
        t = datetime.strptime(o["hora_utc"], "%Y-%m-%d %H:%M")
        filas = [{**f, "volcano": o["volcan"], "sensor_bucket": "VIIRS375"} for f in (o.get("mirova") or [])]
        cand = [p for p in cm.resumir_pasadas(filas) if abs((p.instante - t).total_seconds()) <= TOL_S]
        cand = [p for p in cand if cm.es_protegida(p)]
        if len(cand) != 1:
            sin_pasada.append((o["id"], o["lote"], o["volcan"], o["hora_utc"], len(cand)))
            continue
        p = cand[0]
        ok, mot = cm.protegida_de_crater(p, inner[o["volcan"]], o.get("sensor"))
        out[str(o["id"])] = {"lote": o["lote"], "volcan": o["volcan"], "hora_utc": o["hora_utc"], "sensor": o["sensor"],
                             "de_crater": ok, "motivos": list(mot), "fuente": p.fuente, "dist_km": p.dist_km,
                             "vrp_mirova_mw": p.vrp_mw, "inner_km": inner[o["volcan"]]}
    n = len(out)
    print(f"protegidas de los objetivos: {n + len(sin_pasada)}; con su pasada protegida en la referencia: {n}; "
          f"de cráter {sum(v['de_crater'] for v in out.values())}")
    from collections import Counter
    print("  por lote y de_cráter:", dict(Counter((v["lote"], v["de_crater"]) for v in out.values())))
    print("  motivos:", dict(Counter(m for v in out.values() for m in v["motivos"])))
    print("  sin una sola pasada protegida a 180 s (no se etiquetan):", sin_pasada)
    Path(a.salida).write_text(json.dumps({"funcion": {"modulo_sha256": sha, "commit": "744d8190b"}, "tol_s": TOL_S,
                                          "protegidas": out, "sin_pasada": sin_pasada}, indent=1, ensure_ascii=False),
                              encoding="utf-8")
    print("escrito", a.salida)


if __name__ == "__main__":
    main()
