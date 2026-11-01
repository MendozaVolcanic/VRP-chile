# -*- coding: utf-8 -*-
"""Control del port, sin red: el envoltorio mirova_port con la configuración de VIIRS 750 y la caja física,
corrido sobre las grillas lineales de GEO que guardó el frente N (grilla_NNN.npz, run 39682867040), tiene que dar
el mismo número de píxeles y el mismo VRP que el oráculo de N (campo oraculo.geo_linear de resultados_*.json).

Pregunta 1: si el envoltorio rompiera la detección, la caja o el coeficiente, ¿se vería? Sí: npix o VRP distintos en
alguna de las ~390 pasadas. Pregunta 2: si no leyera nada (npz o resultados vacíos), el conteo de pasadas
comparadas sería 0 y el script aborta. Control positivo: con la configuración de VIIRS 375 sobre las mismas grillas
(longitudes de onda y coeficiente distintos) los números TIENEN que cambiar en alguna pasada; se cuenta cuántas.
Uso: python -I 03_control_v750_sin_red.py --art D:\\vrp-trabajo\\temporales\\s159_n\\run_39682867040
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
import mirova_port as MP  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--art", required=True)
    a = ap.parse_args()
    obj = {o["id"]: o for o in json.loads((AQUI.parent / "n/objetivos_n.json").read_text(encoding="utf-8"))}
    res = {}
    for f in sorted(Path(a.art).rglob("resultados_*.json")):
        for r in json.loads(f.read_text(encoding="utf-8")):
            if r.get("estado") == "ok" and "geo_linear" in (r.get("oraculo") or {}):
                res[r["id"]] = r
    npz = {int(p.stem.split("_")[1]): p for p in Path(a.art).rglob("grilla_*.npz")}
    ids = sorted(set(res) & set(npz))
    assert ids, "instrumento muerto: no hay pasadas con grilla y oráculo"
    iguales_n = iguales_v = 0
    distintas, cambia_375 = [], 0
    for i in ids:
        o, r = obj[i], res[i]
        gn = o["grilla"]
        g = {"ul_x": gn["ul_x"], "ul_y": gn["ul_y"], "n": 67, "celda": 750.0}
        X0, Y0 = gn["ul_x_r2"] + 25187.5, gn["ul_y_r2"] - 25062.5
        z = np.load(npz[i])
        m = MP.correr(z["m13"], z["m15"], g, X0, Y0, r["dayflag"], r["sunglint"], MP.SENSORES["VIIRS750"], semillas=0)
        ref = r["oraculo"]["geo_linear"]
        okn = m["npix"] == ref["npix"]
        okv = (m["vrp_mw"] is None and ref["vrp_mw"] is None) or (
            m["vrp_mw"] is not None and ref["vrp_mw"] is not None and abs(m["vrp_mw"] - ref["vrp_mw"]) < 1e-9)
        iguales_n += okn
        iguales_v += okv
        if not (okn and okv):
            distintas.append((i, o["volcan"], o["hora_utc"], m["npix"], m["vrp_mw"], ref["npix"], ref["vrp_mw"]))
        m3 = MP.correr(z["m13"], z["m15"], g, X0, Y0, r["dayflag"], r["sunglint"], MP.SENSORES["VIIRS375"], semillas=0)
        cambia_375 += (m3["npix"] != m["npix"]) or (m3["vrp_mw"] != m["vrp_mw"])
    print(f"pasadas comparadas: {len(ids)} (grillas lineales de GEO del frente N, run 39682867040)")
    print(f"npix igual al oráculo de N: {iguales_n} de {len(ids)}; VRP igual a 1e-9 MW: {iguales_v} de {len(ids)}")
    print("distintas:", distintas[:20])
    print(f"control positivo (config de VIIRS 375 sobre las mismas grillas): cambia npix o VRP en {cambia_375} de {len(ids)}")


if __name__ == "__main__":
    main()
