# Densidad radial de pixeles anomalos MODIS alrededor del crater (pixeles por km2 por pasada nocturna), en
# produccion y en dos brazos de A/B. Solo lectura.
#
# POR QUE: explica por que el patron de pixeles de produccion NO sirve para ver el corrimiento. Si la densidad
# salta en el borde de inner_radius_km y es plana afuera, los pixeles los pone el umbral de cumbre (que se
# aplica dentro de un circulo medido con nuestra propia geolocalizacion), no rasgos del terreno: el patron
# viaja con el error y lo esconde. En el brazo con banda 22, sin Test 1 y conectiva max, los pixeles son
# pocos y caen en el crater: ese es el que permite medir.
#
# Uso: python densidad_radial.py --cache <carpeta de brazos>
import argparse
import collections
import math
import sys

import comun

sys.stdout.reconfigure(encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    args = ap.parse_args()
    out = open(comun.SALIDAS / "densidad_radial.txt", "w", encoding="utf-8")

    def p(s=""):
        print(s)
        out.write(s + "\n")
    p("Pixeles anomalos MODIS por km2 y por pasada nocturna, por anillo de 2,5 km alrededor de vent_lat/lon")
    vents = comun.vents()
    for vol in ("Lascar", "Villarrica", "Copahue", "Llaima"):
        la, lo = vents[vol]
        for brazo in (None, "_s146_ab_sin_test1", "_s149_ab_sin_test1_b22_max"):
            h = collections.Counter()
            n = 0
            for r in comun.cargar_records(vol, brazo, args.cache):
                if not r["sensor"].startswith("MODIS") or (r.get("solar_zenith_deg") or 0) <= 90:
                    continue
                n += 1
                for q in r.get("anomaly_pixels") or []:
                    d = math.hypot(*comun.ne_km(la, lo, q["lat"], q["lon"]))
                    h[min(int(d // 2.5), 10)] += 1
            if n == 0:
                continue
            dens = []
            for k in range(10):
                area = math.pi * (((k + 1) * 2.5) ** 2 - (k * 2.5) ** 2)
                dens.append("%4.1f-%4.1f:%.3f" % (k * 2.5, (k + 1) * 2.5, h[k] / area / n))
            p("%-11s %-28s pasadas %4d | %s" % (vol, brazo or "produccion", n, "  ".join(dens)))
    out.close()


if __name__ == "__main__":
    main()
