# -*- coding: utf-8 -*-
"""O2 MODIS (pedido de la coordinadora S163, 2026-10-26): paquete para correr el FONDO del código de MIROVA en MATLAB
sobre escenas MODIS reales con 1 a 4 píxeles alertados por nuestro port.

POR QUÉ. El VRP de MIROVA resta a la radiancia de los píxeles alertados un fondo que el .m estima rellenando el hueco
de la alerta con `fillmissing2(...,'linear')`, función que sólo existe en MATLAB. El O2 de S163 mostró que, en
alertas de un píxel, ningún modelo de fondo de nuestros ports es el de MATLAB (hasta 0,82 de diferencia relativa en
VIIRS 750). El port MODIS (`experiments/_s159/portes/mirova_port.py`) usa ese mismo fondo, así que su VRP de 1 a 4
píxeles hereda la ambigüedad. Aquí se arma la entrada para que MATLAB calcule el fondo de cada escena con la máscara
de alertas que el port ya decidió (la detección del port ya está validada contra Octave y MATLAB en S159 y S163).

QUÉ JUNTA. De los lotes con grilla 51 x 51 guardada (S159, run 39712862945; MOD-C, run 40120713181), toda pasada
MODIS donde una variante del port alertó entre 1 y 4 píxeles. Por escena: la matriz MIR en radiancia que el port usó
(`mir`, `mir_geo5` o `mir_b21` según la variante) y la lista de alertas como índices lineales de MATLAB (columna
primero, base 1). El .m de VRP no depende del sensor salvo por el coeficiente, que se reescala después con el delta L.

CONTROL DE IDENTIDAD (no se escribe el paquete si falla): para cada escena, `mirova_port.vrp(mir, mascara, cfg)`
sobre lo empaquetado tiene que dar el VRP que el port guardó en el lote, con diferencia relativa de 1e-5 o menos
(las grillas se guardaron en float32 y el port calculó en float64: medido, hasta 7e-7). Por eso la etiqueta trae
además `vrp_port_recalculado_mw`, el del port sobre la MISMA grilla que recibe MATLAB: con ese se compara. Si la grilla, la máscara o la
orientación estuvieran mal, no daría. Control negativo: con la máscara corrida una
columna, más de la mitad de las escenas tiene que alejarse más de 1e-3 (el redondeo no puede tapar un error).

Uso: python armar_paquete_o2_modis.py   (escribe entradas_o2_modis.mat, el json de etiquetas y MD5.txt aquí)
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
LOTES = {"s159": Path("D:/vrp-trabajo/temporales/s159_portes/run_39712862945"),
         "modc": Path("C:/vrp-trabajo/temporales/s162_negmodis/run_40120713181")}
PORT = Path("C:/vrp-trabajo/s162-modd/experiments/_s159/portes")   # blob 96769a89 (mirova_port.py)
VARIANTES = {"fisica": ("mir", "MODIS"), "sensible": ("mir", "MODIS"), "pixel": ("mir", "MODIS"),
             "fisica_geo5km": ("mir_geo5", "MODIS"), "fisica_b21": ("mir_b21", "MODIS_B21")}
NPIX_MAX = 4
TOL_REL = 1e-5          # las grillas del lote se guardaron en float32; el port calculo en float64 (medido: hasta 7e-7)
MIN_REL_CORRIDA = 1e-3  # la mascara corrida tiene que alejarse mucho mas que el redondeo


def md5(p):
    return hashlib.md5(Path(p).read_bytes()).hexdigest()


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    sys.path.insert(0, str(PORT))
    import mirova_port as MP
    escenas, etiquetas = [], []
    falta_grilla = 0
    for lote, raiz in LOTES.items():
        for jf in sorted(raiz.glob("*MODIS-*/resultados_MODIS_*.json")):
            for r in json.loads(jf.read_text(encoding="utf-8")):
                if r.get("estado") != "ok" or not r.get("port"):
                    continue
                g = jf.parent / ("grilla_%03d.npz" % r["id"])
                for var, (clave, sensor) in VARIANTES.items():
                    p = r["port"].get(var) or {}
                    if not p.get("npix") or p["npix"] > NPIX_MAX:
                        continue
                    if not g.exists():
                        falta_grilla += 1
                        continue
                    mir = np.load(g)[clave].astype(np.float64)
                    masc = np.zeros(mir.shape, bool)
                    for q in p["pixeles"]:
                        masc[q[0], q[1]] = True
                    v = MP.vrp(mir, masc, MP.SENSORES[sensor])
                    rel = abs(v["VRP_MW"] - p["vrp_mw"]) / abs(p["vrp_mw"])
                    ok = v["npix"] == p["npix"] and rel <= TOL_REL
                    corr = np.roll(masc, 1, axis=1)
                    vc = MP.vrp(mir, corr, MP.SENSORES[sensor])
                    n = mir.shape[0]
                    lin = sorted(int(c) * n + int(f) + 1 for f, c in zip(*np.nonzero(masc)))
                    escenas.append((mir, lin))
                    etiquetas.append({"k": len(escenas), "lote": lote, "id": r["id"], "volcan": r["volcan"],
                                      "hora_utc": r["hora_utc"], "variante": var, "grilla": clave, "npix": p["npix"],
                                      "vrp_port_mw": p["vrp_mw"], "vrp_port_recalculado_mw": v["VRP_MW"], "deltaL_port_recalculado": v["deltaL"],
                                      "dif_rel_lote": rel,
                                      "coef_area": MP.SENSORES[sensor]["coef"] * MP.SENSORES[sensor]["area"],
                                      "identidad_ok": bool(ok),
                                      "corrida_distinta": bool(not np.isfinite(vc.get("VRP_MW", np.nan)) or abs(vc["VRP_MW"] - v["VRP_MW"]) / abs(v["VRP_MW"]) > MIN_REL_CORRIDA)})
    malos = [e for e in etiquetas if not e["identidad_ok"]]
    distintas = sum(e["corrida_distinta"] for e in etiquetas)
    print("escenas:", len(etiquetas), "| por npix:", {k: sum(1 for e in etiquetas if e["npix"] == k) for k in range(1, 5)},
          "| por lote:", {l: sum(1 for e in etiquetas if e["lote"] == l) for l in LOTES},
          "| por variante:", {v: sum(1 for e in etiquetas if e["variante"] == v) for v in VARIANTES})
    print("pasadas distintas:", len({(e["lote"], e["id"]) for e in etiquetas}), "| sin grilla en disco:", falta_grilla)
    print("identidad (VRP recalculado = VRP del port, diferencia relativa <= 1e-5):", len(etiquetas) - len(malos), "de",
          len(etiquetas), "| maxima:", max(e["dif_rel_lote"] for e in etiquetas))
    print("control negativo (mascara corrida una columna se aleja mas de 1e-3):", distintas, "de", len(etiquetas))
    if malos or distintas < len(etiquetas) // 2 or not etiquetas:
        print("NO SE ESCRIBE EL PAQUETE:", malos[:5])
        sys.exit(1)
    from scipy.io import savemat
    K = len(escenas)
    M13 = np.stack([e[0] for e in escenas], axis=2)
    ALERTAS = np.empty((K, 1), dtype=object)
    for i, (_m, lin) in enumerate(escenas):
        ALERTAS[i, 0] = np.array(lin, dtype=np.float64).reshape(-1, 1)
    savemat(AQUI / "entradas_o2_modis.mat", {"M13": M13, "ALERTAS": ALERTAS}, do_compression=True)
    (AQUI / "entradas_o2_modis_etiquetas.json").write_text(json.dumps(etiquetas, indent=1, default=float),
                                                          encoding="utf-8")
    nombres = ("entradas_o2_modis.mat", "MIROVA_VIIRS750_VRP.m", "correr_o2_modis.m", "LICENSE.txt",
               "entradas_o2_modis_etiquetas.json")
    lineas = ["%s  %s" % (md5(AQUI / n), n) for n in nombres if (AQUI / n).exists()]
    (AQUI / "MD5.txt").write_text("\n".join(lineas) + "\n", encoding="utf-8")
    print("\n".join(lineas))


if __name__ == "__main__":
    main()
