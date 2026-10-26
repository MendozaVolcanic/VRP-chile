# -*- coding: utf-8 -*-
"""Lee resultado_o2_modis.mat (MATLAB) y lo compara escena por escena con el port MODIS sobre la MISMA grilla.

POR QUÉ. La pregunta es si el fondo que calcula nuestro port (modelo en Python de `fillmissing2`) es el de MATLAB en
escenas MODIS de 1 a 4 píxeles. MATLAB devuelve el VRP con el coeficiente de VIIRS 750 del .m; se compara el delta L
(que no depende del coeficiente) reescalado con el de MODIS: VRP_MODIS = DL x 1,89e7 x 1,0 / 1e6 MW.

Las dos preguntas del instrumento:
1. Si MATLAB y el port coincidieran por construcción, ¿se vería? No pueden: MATLAB corre su propio `fillmissing2`;
   el control es que NPIX de MATLAB sea el de la máscara empaquetada en todas las escenas (si no, se le pasó otra).
2. Si el resultado estuviera vacío o fuera de otro paquete, ¿se vería? Sí: el número de escenas y el md5 de la
   entrada (MD5.txt) se comprueban antes de comparar.
Uso: python leer_o2_modis.py [resultado_o2_modis.mat]
"""
import json
import sys
from pathlib import Path

import numpy as np

AQUI = Path(__file__).resolve().parent


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    from scipy.io import loadmat
    ruta = Path(sys.argv[1]) if len(sys.argv) > 1 else AQUI / "resultado_o2_modis.mat"
    R = loadmat(ruta, squeeze_me=True)
    et = json.loads((AQUI / "entradas_o2_modis_etiquetas.json").read_text(encoding="utf-8"))
    K = len(et)
    print("MATLAB", R.get("version_matlab"), "| escenas en el resultado:", len(np.atleast_1d(R["DL"])), "de", K)
    assert len(np.atleast_1d(R["DL"])) == K, "el resultado no es de este paquete"
    npix = np.atleast_1d(R["NPIX"]).astype(int)
    malos = [e["k"] for e, n in zip(et, npix) if n != e["npix"]]
    print("NPIX de MATLAB = mascara empaquetada:", K - len(malos), "de", K, malos[:10])
    filas = []
    for e, dl in zip(et, np.atleast_1d(R["DL"])):
        v_m = float(dl) * e["coef_area"] / 1e6
        v_p = e["vrp_port_recalculado_mw"]
        filas.append((e, v_m, v_p, v_p / v_m if v_m else np.nan))
    for n in (1, 2, 3, 4):
        r = np.array([x[3] for x in filas if x[0]["npix"] == n])
        if len(r):
            print("npix %d: n %d | port/MATLAB mediana %.4f, p5 %.4f, p95 %.4f | |dif| > 1 %%: %d | iguales a 1e-6: %d" % (
                n, len(r), np.nanmedian(r), np.nanpercentile(r, 5), np.nanpercentile(r, 95),
                int(np.sum(np.abs(r - 1) > 0.01)), int(np.sum(np.abs(r - 1) <= 1e-6))))
    print("las 15 mas distintas (variante, volcan, hora, npix, VRP MATLAB MODIS, VRP port):")
    for e, v_m, v_p, q in sorted(filas, key=lambda x: -abs(np.log(x[3])) if x[3] and x[3] > 0 else 0)[:15]:
        print("  %-14s %-18s %s npix %d  MATLAB %.4f  port %.4f  (x%.3f)" % (e["variante"], e["volcan"], e["hora_utc"],
                                                                         e["npix"], v_m, v_p, q))


if __name__ == "__main__":
    main()
