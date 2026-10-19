# -*- coding: utf-8 -*-
"""Verificador F5, paso 4: si se multiplica la magnitud V375 por el area real del pixel (en vez de la
area de nadir), la razon contra MIROVA queda plana con el cenit?

Modelo de area (geometria de barrido, sin nada del pipeline): altura h = 829 km, R = 6371 km.
Angulo de barrido s desde el cenit z: sin s = R sin z / (R + h). Distancia oblicua rho.
Crecimiento a lo largo del vuelo g_t = rho / h; a lo ancho del barrido g_s = rho / (h cos z).
Agregacion a bordo VIIRS (Wolfe et al. 2013): 3 muestras hasta s = 31,59 deg, 2 hasta 44,68 deg, 1 mas alla.
Factor de area relativo al nadir = g_t * g_s * N(s) / 3.
CONTROL DEL MODELO: al final del barrido (z ~ 70 deg) tiene que dar del orden de 4,38x, la razon de areas
de la Tabla 2.2-1 del ATBD de geolocalizacion VIIRS citada en pipeline/scan_geometry.py (docstring de
viirs_pixel_areas). Si no se acerca, el modelo no sirve y se dice.

Pregunta 1: si el area no fuera la causa, la curva con area seguiria inclinada (o se invertiria): lo veria.
Pregunta 2: un factor que sea 1 en todo el barrido daria la misma curva que la publicada: instrumento vivo
solo si el factor varia (se imprime).
Limite: esto prueba COMPATIBILIDAD, no causa. Otra variable que crezca con el cenit (por ejemplo el numero
de pixeles que MIROVA suma por remuestreo, o el borde de nube) podria dar la misma forma.
"""
import io, json, math, os, sys, statistics
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
R, H = 6371.0, 829.0


def factor(z):
    zr = math.radians(z)
    s = math.asin(R * math.sin(zr) / (R + H))
    gamma = zr - s
    rho = math.sqrt(R ** 2 + (R + H) ** 2 - 2 * R * (R + H) * math.cos(gamma))
    gt, gs = rho / H, rho / (H * math.cos(zr))
    sd = math.degrees(s)
    n = 3 if sd <= 31.59 else (2 if sd <= 44.68 else 1)
    return gt * gs * n / 3, sd, n


def main():
    for z in (0, 20, 35, 40, 50, 55, 60, 65, 68, 70):
        f, sd, n = factor(z)
        print("cenit %4.1f  barrido %5.2f  agregacion %d  factor_area %.2f" % (z, sd, n, f))
    filas = json.load(open(os.path.join(AQUI, "v375_fondo.json"), encoding="utf-8"))
    e = [x for x in filas if x["f5"] > 0 and x["mir"] >= 1]
    print("\nn=%d pasadas V375 con MIROVA >= 1 MW" % len(e))
    print("banda    n  r_pub  r_pub*area  r_cero*area  factor_mediano")
    for lo, hi in ((0, 30), (30, 45), (45, 60), (60, 90)):
        b = [x for x in e if lo <= x["zen"] < hi]
        if not b:
            continue
        print("%2d-%2d %4d  %5.2f  %6.2f  %6.2f  %6.2f" % (lo, hi, len(b), statistics.median(x["f5"] / x["mir"] for x in b),
              statistics.median(x["f5"] * factor(x["zen"])[0] / x["mir"] for x in b),
              statistics.median(x["cero"] * factor(x["zen"])[0] / x["mir"] for x in b),
              statistics.median(factor(x["zen"])[0] for x in b)))


if __name__ == "__main__":
    main()
