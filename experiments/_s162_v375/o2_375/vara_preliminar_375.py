# -*- coding: utf-8 -*-
"""O2-375, vara PRELIMINAR: el fondo del VRP de MIROVA en las 422 escenas VIIRS 375 de 1 a 4 píxeles, con la regla de
`fillmissing2` que encontró la sesión S163 (rama s163-o2-alternativa, commit cd812c746,
experiments/_s163_o2alt/delaunay_perturbado.py: Delaunay con desempate simbólico estilo CGAL, x = fila, y = columna,
relleno lineal), en vez de MATLAB.

POR QUÉ PRELIMINAR. Esa regla reproduce a MATLAB en 166 de 166 escenas de O2 (67 x 67, VIIRS 750), pero (a) su verificador
limpio todavía no la confirma y (b) mi grilla de 134 x 134 y sus bordes son casos que O2 no cubrió. La prueba de oro es
el paquete `entradas_v375.mat` corrido en MATLAB (pendiente). Este número sirve para avanzar la tarea 2 (re-medir la
magnitud de V375-C), no para cerrarla.

Qué hace. El mismo `MIROVA_VIIRS750_VRP.m` del port (`mirova_v750_r2.vrp`): las alertas a NaN, el hueco dilatado 3 x 3
(1 a 4 alertas), relleno, suma; sólo cambia el relleno. VRP_375 = ΔL x 1,80e7 x 0,140625 / 1e6.

Las dos preguntas del instrumento. (1) Control positivo: la escena de Etna (la de O2), detectada con el port validado,
tiene que dar Tot_Lmir_bk 1,072886152 (OSF v2.5); si no, la regla no está bien aplicada aquí. Además, la triangulación
no puede dejar aristas ilegales (`info['ilegales']` 0 en cada escena). (2) Se informa cuántas escenas cambian respecto
del port: si la regla no cambiara nada, sería inútil para la pregunta; si cambiara todo de forma rara, sospechosa.
Uso: python -I vara_preliminar_375.py --modulo <ruta a delaunay_perturbado.py del commit cd812c746>
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
import sys
from pathlib import Path

import numpy as np
import scipy.io as sio
from scipy.ndimage import binary_dilation

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import brazos as BR  # noqa: E402

ORA = BR.ORA
N = 134
COEF_375 = 1.80e7 * 0.140625 / 1e6
COEF_750 = 1.97e7 * 0.5625 / 1e6


def vrp_regla(rad, mask, rellenar):
    enm = rad.copy()
    enm[mask] = np.nan
    npix = int(mask.sum())
    k = 3 if npix <= 4 else (5 if npix <= 30 else 7)
    excl = binary_dilation(np.isnan(enm), structure=np.ones((k, k), bool))
    enm[excl] = np.nan
    fondo, info = rellenar(enm, ejes="xy_fila_col")
    l_hot = float(np.nansum(rad[mask]))
    l_bk = float(np.nansum(fondo[mask]))
    return l_hot, l_bk, l_hot - l_bk, info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--modulo", required=True)
    ap.add_argument("--commit", default="cd812c746")
    ap.add_argument("--salida", default=str(AQUI / "vara_preliminar_375.json"))
    a = ap.parse_args()
    spec = importlib.util.spec_from_file_location("delaunay_perturbado", a.modulo)
    DP = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(DP)
    print("regla:", a.modulo, "sha256", hashlib.sha256(Path(a.modulo).read_bytes()).hexdigest()[:16], "commit", a.commit)
    S = sio.loadmat(AQUI / "entradas_v375.mat")
    E = json.loads((AQUI / "entradas_v375_etiquetas.json").read_text(encoding="utf-8"))["escenas"]
    # control de Etna
    em13, em15, ebox = S["ETNA_M13"].astype(float), S["ETNA_M15"].astype(float), S["ETNA_BOX"].astype(float)
    emask, _l, _d = ORA.detectar(em13, em15, ebox, float(np.ravel(S["ETNA_DAY"])[0]), float(np.ravel(S["ETNA_SG"])[0]),
                                 devolver_diag=True)
    lh, lb, dl, info = vrp_regla(em13, emask, DP.rellenar)
    print(f"Etna: npix {int(emask.sum())}, Tot_Lmir_hot {lh:.9f}, Tot_Lmir_bk {lb:.9f}, VRP {dl * COEF_750 * 1e6:.1f} W, "
          f"aristas ilegales {info['ilegales']}  (OSF v2.5: 5, 1.965342180, 1.072886152, 9889528.4 W)")
    assert int(emask.sum()) == 5 and abs(lb - 1.072886152) < 5e-10, "la regla no reproduce Etna: no se sigue"
    RAD, ALE, NAL = S["RAD"], S["ALE"], np.ravel(S["NAL"])
    out, ilegales, cambia = [], 0, 0
    for n, e in enumerate(E):
        idx = ALE[n, :NAL[n]].astype(int)
        mask = np.zeros((N, N), bool)
        mask[(idx - 1) % N, (idx - 1) // N] = True
        rad = RAD[:, :, n].astype(np.float64)
        lh, lb, dl, info = vrp_regla(rad, mask, DP.rellenar)
        ilegales += info["ilegales"]
        v = dl * COEF_375
        rel = abs(v - e["vrp_port_mw"]) / max(abs(e["vrp_port_mw"]), 1e-12)
        cambia += rel > 1e-6
        out.append({"posicion": e["posicion"], "id": e["id"], "brazos": e["brazos"], "npix": e["npix"],
                    "l_hot": lh, "l_bk": lb, "dl": dl, "vrp_vara_mw": v, "vrp_port_mw": e["vrp_port_mw"], "rel": rel})
        if (n + 1) % 50 == 0:
            print(f"  {n + 1} de {len(E)}", flush=True)
    rels = np.array([o["rel"] for o in out])
    print(f"escenas {len(out)}: aristas ilegales {ilegales}; cambian respecto del port (rel > 1e-6) {cambia}; "
          f"diferencia relativa mediana {np.median(rels):.4f}, p90 {np.percentile(rels, 90):.4f}, máx {rels.max():.4f}")
    for k in (1, 2, 3, 4):
        r = rels[[o["npix"] == k for o in out]]
        print(f"  {k} px: n {len(r)}, cambian {int((r > 1e-6).sum())}, mediana {np.median(r):.4f}, máx {r.max():.4f}")
    assert ilegales == 0
    Path(a.salida).write_text(json.dumps({"regla": {"modulo_sha256": hashlib.sha256(Path(a.modulo).read_bytes()).hexdigest(),
                                                    "commit": a.commit, "estado": "PRELIMINAR"},
                                          "escenas": out}, indent=0), encoding="utf-8")
    print("escrito", a.salida)


if __name__ == "__main__":
    main()
