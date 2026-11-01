# -*- coding: utf-8 -*-
"""O2-375 (S163): paquete para correr el fondo del VRP de MIROVA en MATLAB sobre las escenas VIIRS 375 de 1 a 4 píxeles.

POR QUÉ. O2 (experiments/_s163_o2/RESULTADO_O2.md, rama s163-o2-paquete) mostró que en alertas de uno a cuatro píxeles
ningún port de `fillmissing2` reproduce a MATLAB (hasta 0,82 relativo): el hueco que deja la alerta se rellena con una
triangulación que sólo MATLAB define. El port de VIIRS 375 usa ese mismo fondo, así que la magnitud de V375-C en esas
escenas no se puede juzgar contra un port: la vara tiene que ser MATLAB.

Qué arma. Por cada pasada con resultado de los lotes S159, S162 y S162b (B2) y cada máscara de alertas DISTINTA de 1 a 4
píxeles que dio alguno de los diez brazos de `brazos.py`: la radiancia I4 remuestreada a la grilla de 134 x 134 de MIROVA
(la misma grilla guardada que usó el port, en float32) y los índices lineales de MATLAB de las alertas (columna mayor, base
1). MATLAB corre sólo el `.m` de VRP sin cambios: el fondo no depende del sensor; el coeficiente sí, y se reescala al
leer (VRP_375 = ΔL x 1,80e7 x 0,140625 / 1e6, CLAUDE.md «Reglas científicas»). Control: la escena de Etna de O2, re-detectada
en MATLAB con el `.m` de detección sin cambios; tiene que dar Tot_Lmir_bk 1,072886152 como en el OSF v2.5.

Las dos preguntas del instrumento. (1) Si los índices estuvieran mal (fila por columna, base 0), la radiancia caliente que
leería MATLAB no sería la del port: la prueba de `probar_paquete_375.py` lee el .mat como lo leería MATLAB y exige L_hot y
VRP iguales al port en las 422 escenas. (2) Una escena sin máscara no entra; el conteo por brazo se imprime.
Uso: python -I armar_paquete_375.py [caché de brazos del evaluador, opcional]
"""
from __future__ import annotations

import collections
import hashlib
import io
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import scipy.io as sio

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
V375 = AQUI.parent
RAIZ = V375.parents[1]
sys.path.insert(0, str(V375))
import brazos as BR  # noqa: E402
import evaluar as EV  # noqa: E402

ART = {"S159": Path(r"D:/vrp-trabajo/temporales/s159_portes/run_39712862945"),
       "S162": Path(r"C:/vrp-trabajo/temporales/s162_v375/run_40116289866"),
       "S162b": Path(r"C:/vrp-trabajo/temporales/s162_v375/run_40131572769"),
       "CTL": Path(r"C:/vrp-trabajo/temporales/s162_v375/run_40131572769")}
RAMA_O2, ARCH_O2 = "origin/s163-o2-paquete", "experiments/_s163_o2/entradas_o2.mat"
N = 134
MAXPIX = 4
CACHE_RUTA = Path(sys.argv[1]) if len(sys.argv) > 1 else None
CACHE = json.loads(CACHE_RUTA.read_text(encoding="utf-8")) if CACHE_RUTA and CACHE_RUTA.exists() else {}


def objetivos():
    obj = {}
    for o in json.loads((V375 / "objetivos_v375_bc.json").read_text(encoding="utf-8"))["pasadas"]:
        obj[o["id"]] = o
    for o in json.loads((V375 / "b2/objetivos_v375_b2.json").read_text(encoding="utf-8"))["pasadas"]:
        obj[o["id"]] = o
    for o in json.loads((RAIZ / "experiments/_s159/portes/objetivos_portes.json").read_text(encoding="utf-8")):
        if o["b"] == "VIIRS375" and o["hora_utc"][:10] not in EV.EXCLUIDOS:
            obj[o["id"]] = {**o, "lote": "S159"}
    return obj


def main():
    obj = objetivos()
    V = EV.volcanes()
    res = {}
    for lote, d in ART.items():
        for i, r in EV.leer_resultados(d).items():
            if i in obj and obj[i]["lote"] == lote and r.get("estado") == "ok":
                res[i] = r
    escenas, rads, cuenta = [], [], collections.Counter()
    for i in sorted(res):
        o, r = obj[i], res[i]
        g = EV.grilla_npz(ART[o["lote"]], i)
        assert g is not None, i
        mir, tir, sha = g
        arms = CACHE.get(f"{i}|{sha}")
        if arms is None:   # sin caché: se recalcula igual que el evaluador
            v = V[o["volcan"]]
            xc, yc = BR.crater_xy(o["grilla"], v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"]))
            arms = BR.correr_brazos(mir, tir, o["grilla"], o["grilla"]["X0"], o["grilla"]["Y0"], xc, yc,
                                    v["inner_radius_km"], o["volcan"], r["dayflag"], r["sunglint"], semillas=0)
        mascaras = {}
        for b, a in arms.items():
            if 1 <= a["npix"] <= MAXPIX:
                clave = tuple(sorted((p[0], p[1]) for p in a["pixeles"]))
                mascaras.setdefault(clave, {"brazos": [], "vrp_port": a["vrp_mw"]})["brazos"].append(b)
        for clave, m in sorted(mascaras.items()):
            ale = [c * N + f + 1 for f, c in clave]            # MATLAB: columna mayor, base 1
            l_hot = float(sum(mir[f, c] for f, c in clave))
            escenas.append({"k": len(escenas) + 2, "id": i, "lote": o["lote"], "volcan": o["volcan"],
                            "hora_utc": o["hora_utc"], "clase": o["clase"], "brazos": m["brazos"], "npix": len(clave),
                            "pixeles_fila_col": [list(p) for p in clave], "alertas_matlab": ale, "l_hot_port": l_hot,
                            "vrp_port_mw": m["vrp_port"], "mirova_vrp_mw": o.get("mirova_vrp"),
                            "pub_prod": o.get("pub_prod"), "pc_vrp_k": o.get("pc_vrp"), "f5_core_k": o.get("f5_core"),
                            "z": (r.get("geometria_centro") or {}).get("sensor_zenith"), "grilla_sha256": sha})
            rads.append(mir.astype(np.float32))
            for b in m["brazos"]:
                cuenta[b] += 1
    K = len(escenas)
    print(f"escenas de 1 a {MAXPIX} píxeles: {K} (en {len({e['id'] for e in escenas})} pasadas); por npix",
          dict(collections.Counter(e["npix"] for e in escenas)), "| por brazo", dict(cuenta))
    # la escena de Etna de O2 como control (escena 1)
    crudo = subprocess.run(["git", "show", f"{RAMA_O2}:{ARCH_O2}"], cwd=RAIZ, capture_output=True).stdout
    tmp = AQUI / "_etna_tmp.mat"
    tmp.write_bytes(crudo)
    o2 = sio.loadmat(tmp)
    tmp.unlink()
    RAD = np.stack(rads, axis=2)
    ALE = np.zeros((K, MAXPIX), dtype=np.int32)
    NAL = np.zeros(K, dtype=np.int32)
    for n, e in enumerate(escenas):
        ALE[n, :e["npix"]] = e["alertas_matlab"]
        NAL[n] = e["npix"]
    # Etna (escena 1 de O2): MATLAB la re-detecta con el .m de detección sin cambios, como en O2
    sio.savemat(AQUI / "entradas_v375.mat", {"RAD": RAD, "ALE": ALE, "NAL": NAL,
                                              "ETNA_M13": o2["M13"][:, :, 0], "ETNA_M15": o2["M15"][:, :, 0],
                                              "ETNA_BOX": o2["BOX"][:, :, 0],
                                              "ETNA_DAY": float(np.ravel(o2["DAY"])[0]),
                                              "ETNA_SG": float(np.ravel(o2["SG"])[0])},
                do_compression=True)
    (AQUI / "entradas_v375_etiquetas.json").write_text(json.dumps(
        {"nota": "escena k de MATLAB = posición en RAD (1 a K); la k guardada en cada etiqueta es k + 1 por la de Etna "
                 "del control, que va aparte en ETNA_*. Usar 'posicion' para indexar RAD.",
         "escenas": [{**e, "posicion": n + 1} for n, e in enumerate(escenas)]},
        ensure_ascii=False, indent=0), encoding="utf-8")
    print("escrito entradas_v375.mat y entradas_v375_etiquetas.json;", RAD.shape, RAD.dtype)


if __name__ == "__main__":
    main()
