"""Convierte los limites de zona de agregacion VIIRS (angulo de barrido, Geolocation ATBD 2014
p_idx 33/36/49: 31.589 y 44.680 grados) a cenit del satelite visto desde el suelo.
Geometria esferica: sin(cenit) = ((R+h)/R) * sin(barrido).
Pregunta 1 del instrumento: si la geometria estuviera rota (p.ej. invertir la razon), el control
positivo (barrido 0 -> cenit 0; barrido 56.063 borde -> ~70 grados conocido como borde VIIRS) lo delataria.
Pregunta 2: es un calculo cerrado, no hay instrumento que pueda estar muerto; se imprime todo."""
import math
R = 6371.0
for h in (824.0, 834.0):  # 824 km Campus 2022 Tabla 1; 834 km como sensibilidad
    k = (R + h) / R
    for scan in (0.0, 31.589, 44.680, 56.063):
        z = math.degrees(math.asin(min(1.0, k * math.sin(math.radians(scan)))))
        print(f"h={h:.0f} km  barrido={scan:7.3f}  ->  cenit={z:6.2f}")
