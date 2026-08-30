# -*- coding: utf-8 -*-
"""S129 — ¿MIROVA suma TODOS los píxeles alertados, y nosotros publicamos uno solo?

EL FENÓMENO, primero. Una anomalía térmica volcánica rara vez cabe en un píxel. Un
domo, un campo fumarólico o un lago cratérico caliente calientan varios píxeles
vecinos, cada uno un poco por encima del fondo. La energía total del rasgo es la
suma de todos esos excesos — no el del más caliente, ni el de un subconjunto.

Coppola et al. 2019, el paper que describe el sistema MIROVA, escribe la magnitud
así (p. 3, verbatim del texto extraído):

    VRP = 18.9 · A_pixel · Σ_{i=1}^{npix} (L_MIR,alert − L_MIR,bk)_i

    "where npix is the number of alerted pixels … Apixel is the pixel size
     (1 km2 for the resampled MODIS pixels)"

Nosotros publicamos `primary_cluster.vrp_mw`: UN clúster, elegido por cercanía al
cráter. `ENABLE_SUM_VRP_REPORTING` está en False.

LA TENSIÓN CON A10. La regla A10 del proyecto (desde S60) dice lo contrario — que
`pc.vrp_mw` "es lo que MIROVA reporta" y que usar la suma scene-wide oculta
problemas. A10 no salió de la nada: la suma scene-wide de NUESTRO pipeline incluye
píxeles calientes a 20 km (salares, incendios, el valle tibio de A69) que el
criterio de alerta de MIROVA nunca habría marcado. Las dos cosas pueden ser ciertas
a la vez, y por eso hay que medir un TERCER brazo.

LOS TRES BRAZOS, pre-registrados antes de mirar el resultado:

  A · `pc.vrp_mw` — lo que publicamos hoy.        Esperado ~0,73 (medido en S128)
  B · suma de los píxeles anómalos dentro del      La lectura literal del paper,
      radio proximal (5 km, Coppola 2019 p.4)      pero acotada por distancia
  C · `record.vrp_mw` — suma scene-wide.           Esperado alto y ruidoso; es lo
                                                   que A10 prohíbe con razón

PREDICCIÓN: si la diferencia entre sumar y seleccionar explica parte del déficit,
B queda ENTRE A y C, y más cerca de 1,0 que A. Si B ≈ A, entonces nuestros clústeres
ya contienen casi toda la energía próxima y esta vía no explica nada — y hay que
decirlo así.

Read-only. Un par por noche, máximo de ambos lados; estratificado por volcán (S126).
"""
import io
import json
import math
import os
import statistics as st
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
from _s126_lib import VENTS, bucket, cargar_mirova, ic95, resumen   # noqa: E402

VENTANA = ("2026-01-01", "2026-08-30")
R_PROXIMAL_KM = 5.0        # Coppola 2019 p.4: el corte proximal/distal, uniforme


def dist_km(lat, lon, vlat, vlon):
    return 111.32 * math.hypot(lat - vlat, (lon - vlon) * math.cos(math.radians(vlat)))


mir, _ = cargar_mirova(VENTANA)
tabla, glob = {}, {"A": [], "B": [], "C": []}

for vol in sorted(VENTS):
    p = os.path.join(ROOT, "data", "mirova_equivalent", vol + ".json")
    if not os.path.exists(p):
        continue
    vlat, vlon = VENTS[vol]
    # Un par por noche: nos quedamos con la pasada de mayor VRP publicado.
    mejor = {}
    for r in json.load(open(p, encoding="utf-8"))["records"]:
        d = r.get("datetime_utc", "")[:10]
        sz = r.get("solar_zenith_deg")
        if not (VENTANA[0] <= d <= VENTANA[1]) or (sz is not None and sz < 90):
            continue
        b = bucket(r.get("sensor"))
        if b is None:
            continue
        a = (r.get("primary_cluster") or {}).get("vrp_mw") or 0.0
        c = r.get("vrp_mw") or 0.0
        # Brazo B: suma de los anómalos dentro del radio proximal.
        bsum = 0.0
        for q in (r.get("anomaly_pixels") or []):
            v = q.get("vrp_mw") or 0.0
            if v <= 0:
                continue
            dd = q.get("dist_km")
            if dd is None and q.get("lat") is not None:
                dd = dist_km(q["lat"], q["lon"], vlat, vlon)
            if dd is not None and dd <= R_PROXIMAL_KM:
                bsum += v
        k = (d, b)
        if a > mejor.get(k, (0, 0, 0))[0]:
            mejor[k] = (a, bsum, c)

    fila = {}
    for b in ("v375", "v750", "modis"):
        rs = {"A": [], "B": [], "C": []}
        for (d, bb), (a, bs, c) in mejor.items():
            if bb != b:
                continue
            m = (mir.get(vol) or {}).get((d, b))
            if not m or m <= 0:
                continue
            if a > 0:
                rs["A"].append(a / m)
            if bs > 0:
                rs["B"].append(bs / m)
            if c > 0:
                rs["C"].append(c / m)
        if len(rs["A"]) >= 5:
            fila[b] = {k: {**(resumen(v) or {}), "ic95": ic95(v)} for k, v in rs.items()
                       if len(v) >= 5}
            for k in ("A", "B", "C"):
                glob[k] += rs[k]
    if fila:
        tabla[vol] = fila

R = {"_meta": {"ventana": VENTANA, "radio_proximal_km": R_PROXIMAL_KM,
               "brazos": {"A": "primary_cluster.vrp_mw — lo que publicamos",
                          "B": "suma de anomaly_pixels dentro de %g km — lectura "
                               "literal de Coppola 2019 p.3, acotada por el corte "
                               "proximal de p.4" % R_PROXIMAL_KM,
                          "C": "record.vrp_mw — suma scene-wide (lo que A10 prohíbe)"}},
     "global": {k: {**(resumen(v) or {}), "ic95": ic95(v)} for k, v in glob.items()},
     "por_volcan_sensor": tabla}
os.makedirs(AQUI, exist_ok=True)
json.dump(R, open(os.path.join(AQUI, "01_suma_vs_cluster.json"), "w",
                  encoding="utf-8"), indent=1, ensure_ascii=False)

print("Ratio nuestro/MIROVA con tres definiciones de la magnitud\n")
print("%-46s %6s %9s %20s" % ("brazo", "n", "mediana", "IC95"))
for k, nom in (("A", "A · primary_cluster (lo que publicamos hoy)"),
               ("B", "B · suma de anómalos dentro de 5 km (el paper)"),
               ("C", "C · record.vrp_mw scene-wide (A10 lo prohíbe)")):
    g = R["global"][k]
    print("%-46s %6d %9.3f %20s" % (nom, g.get("n", 0), g.get("mediana", 0), g["ic95"]))

print("\nPor volcán, VIIRS375 (el sensor que domina el volumen):")
print("%-22s %22s %22s %22s" % ("volcán", "A cluster", "B suma<5km", "C scene-wide"))
for v, f in sorted(tabla.items()):
    d = f.get("v375")
    if not d:
        continue
    def c(k):
        x = d.get(k)
        return "-" if not x else "n=%-4d med=%6.3f" % (x["n"], x["mediana"])
    print("%-22s %22s %22s %22s" % (v, c("A"), c("B"), c("C")))
