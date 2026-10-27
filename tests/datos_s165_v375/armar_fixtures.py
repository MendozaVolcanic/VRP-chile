# -*- coding: utf-8 -*-
"""Arma las fixtures de tests/test_mirova_v375_codigo_s165.py desde el lote S162 de V375-C (run 40116289866).

POR QUÉ. La prueba de identidad tiene que comparar la vía de pipeline/ contra código INDEPENDIENTE de ella: el port de
`experiments/_s162_v375/brazos.py` (brazo C13, sobre el oráculo validado contra Octave) para la máscara y los números de
cada pase, y la salida de MATLAB R2026b (`o2_375/matlab_v375.json`) para el VRP de las escenas de 1 a 4 píxeles, donde
el fondo del port viejo no es el de MATLAB (adenda 1 de PREREGISTRO_E.md, §7.3). Sobre 4 píxeles la vara es el port.
Este script corre una sola vez, con el lote en disco; las pruebas leen lo que deja aquí y no necesitan el lote.

Selección (fija, sin mirar la vía): todas las pasadas del lote S162 cuya máscara C13 tiene de 1 a 4 píxeles y cuyo VRP
de MATLAB difiere del port (rel > 0), hasta 3; una de 1 a 4 píxeles donde coinciden; las 2 de más píxeles en C13 entre
las protegidas; y una pasada sin alertas en C13 de un volcán distinto. Uso:
    python tests/datos_s165_v375/armar_fixtures.py C:/vrp-trabajo/temporales/s162_v375/run_40116289866
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
V375 = RAIZ / "experiments/_s162_v375"
sys.path.insert(0, str(V375))
import brazos as BR  # noqa: E402


def main(lote):
    obj = {p["id"]: p for p in json.loads((V375 / "objetivos_v375_bc.json").read_text(encoding="utf-8"))["pasadas"]}
    res = {}
    for f in sorted(Path(lote).rglob("resultados_VIIRS375_*.json")):
        for r in json.loads(f.read_text(encoding="utf-8")):
            if r.get("estado") == "ok":
                res[r["id"]] = r
    mat = {e["id"]: e for e in json.loads((V375 / "o2_375/matlab_v375.json").read_text(encoding="utf-8"))["escenas"]
           if "C13" in e["brazos"]}
    grillas = {int(p.stem.split("_")[1]): p for p in Path(lote).rglob("grilla_*.npz")}
    ok = [i for i in sorted(res) if i in obj and i in grillas and "C13" in res[i].get("port", {})]

    def npix(i):
        return res[i]["port"]["C13"]["npix"]
    sel = [i for i in ok if i in mat and mat[i]["rel"] > 0][:3]
    sel += [i for i in ok if i in mat and mat[i]["rel"] == 0][:1]
    sel += sorted((i for i in ok if obj[i]["protegida"] and npix(i) > 4), key=npix, reverse=True)[:2]
    vistos = {obj[i]["volcan"] for i in sel}
    sel += [i for i in ok if npix(i) == 0 and obj[i]["volcan"] not in vistos][:1]

    import yaml
    V = {v["name"]: v for v in yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
    out = []
    for i in sel:
        o, r = obj[i], res[i]
        z = np.load(grillas[i])
        mir, tir = z["mir"].astype(np.float64), z["tir"].astype(np.float64)
        v = V[o["volcan"]]
        g = o["grilla"]
        xc, yc = BR.crater_xy(g, v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"]))
        box = BR.caja(g, "C13", g["X0"], g["Y0"], xc, yc, v["inner_radius_km"], o["volcan"])
        mask, _lista, d = BR.MP.detectar(mir, tir, box, r["dayflag"], r["sunglint"], BR.MP.SENSORES["VIIRS375"])
        p = BR.MP.vrp(mir, mask, BR.MP.SENSORES["VIIRS375"])
        n = int(mask.sum())
        assert n == npix(i), (i, n, npix(i))       # el recálculo es el del runner (control 2.1 de evaluar.py)
        if 1 <= n <= 4:
            m = mat[i]
            assert m["npix"] == n and abs(m["vrp_port_mw"] - p["VRP_MW"]) < 1e-9, i
            vrp_vara, fuente = m["vrp_vara_mw"], "matlab"
        else:
            vrp_vara, fuente = (None if n == 0 else float(p["VRP_MW"])), "port"
        shutil.copyfile(grillas[i], AQUI / f"grilla_{i}.npz")
        out.append({"id": i, "volcan": o["volcan"], "hora_utc": o["hora_utc"], "sensor": o["sensor"],
                    "protegida": bool(o["protegida"]), "grilla": g, "dayflag": r["dayflag"], "sunglint": r["sunglint"],
                    "box_c13": {"n2": int((box == 2).sum()), "n1": int((box == 1).sum())},
                    "mascara": [[int(a), int(b)] for a, b in zip(*np.nonzero(mask))], "npix": n,
                    "n_abs": d.get("n_abs"), "n_p1": d.get("n_p1"), "n_p2": d.get("n_p2"),
                    "vrp_port_mw": None if n == 0 else float(p["VRP_MW"]), "vrp_vara_mw": vrp_vara,
                    "fuente_vara": fuente})
        print(i, o["volcan"], o["hora_utc"], "npix", n, "port", out[-1]["vrp_port_mw"], "vara", vrp_vara, fuente)
    (AQUI / "esperado.json").write_text(json.dumps({"lote": str(lote), "pasadas": out}, indent=1, ensure_ascii=False),
                                       encoding="utf-8")


if __name__ == "__main__":
    main(sys.argv[1])
