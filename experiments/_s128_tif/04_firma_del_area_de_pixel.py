# -*- coding: utf-8 -*-
"""S128 — ¿el deficit de magnitud tiene la FIRMA del area de pixel? Test decisivo.

El fenomeno. Un sensor que barre de lado no ve un pixel cuadrado: la huella se
estira hacia el borde del barrido. Pero VIIRS I-band no la deja crecer libremente
— agrega muestras a bordo (3x cerca del nadir, 2x despues, 1x en el extremo), asi
que el crecimiento real es mucho menor que el sec3 de un barredor sin agregacion.
Schroeder et al. 2014 p.86, verbatim y verificado:

    "the effective footprint ranges from the nominal 375 m resolution
     (383 x 360 m) at the sub-satellite point to 795 x 784 m at a maximum
     scan angle of 56.28 deg"

Eso es 4,52x de area en el extremo, no 25x.

MIROVA neutraliza ese efecto remuestreando a una malla de paso fijo: el pixel
elongado se parte en varias celdas de area nominal, y la energia se conserva
porque crece el NUMERO de celdas (Coppola 2014 §2.2). Nosotros usamos area nadir
constante SIN remuestrear, asi que perdemos esa multiplicidad.

PREDICCION PRE-REGISTRADA (derivada del modelo de Schroeder ANTES de mirar estos
bins, en `docs/s128/PAPERS_SCHROEDER2014_VIIRS375.md`):

    razon del ratio entre cenit 0-15 y 35-50  =  1,57x   con agregacion a bordo
                                                 2,27x   sec3 crudo, sin agregacion
                                                 1,00x   si el area no es la causa

Y una segunda firma, mas exigente: el area no crece suave sino en DIENTE DE
SIERRA, porque cae de golpe en cada cambio de zona de agregacion. Ningun otro
mecanismo — ni el fondo autorreferente ni la topografia — tiene razon para saltar
en un angulo de barrido especifico.

Read-only. Solo VIIRS I-band, que es de quien habla Schroeder.
"""
import io
import json
import os
import statistics as st
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, os.path.join(ROOT, "experiments"))
from _s126_lib import VENTS, bucket, cargar_mirova, ic95      # noqa: E402

VENTANA = ("2026-01-01", "2026-08-30")
PRED = {"con_agregacion": 1.57, "sec3_crudo": 2.27, "sin_efecto": 1.00}


def pares_por_cenit(bins):
    """[(ratio, cenit)] -> acumulado por bin. Un par por NOCHE, maximo de ambos lados."""
    mir, _ = cargar_mirova(VENTANA)
    ac = {b: [] for b in bins}
    for vol in sorted(VENTS):
        p = os.path.join(ROOT, "data", "mirova_equivalent", vol + ".json")
        if not os.path.exists(p):
            continue
        mejor = {}
        for r in json.load(open(p, encoding="utf-8"))["records"]:
            d = r.get("datetime_utc", "")[:10]
            sz = r.get("solar_zenith_deg")
            if not (VENTANA[0] <= d <= VENTANA[1]) or (sz is not None and sz < 90):
                continue
            if bucket(r.get("sensor")) != "v375":
                continue
            v = (r.get("primary_cluster") or {}).get("vrp_mw") or 0
            z = r.get("sensor_zenith_deg")
            if v <= 0 or z is None:
                continue
            if v > mejor.get(d, (0, 0))[0]:
                mejor[d] = (v, abs(z))
        for d, (v, z) in mejor.items():
            m = (mir.get(vol) or {}).get((d, "v375"))
            if not m or m <= 0:
                continue
            for lo, hi in bins:
                if lo <= z < hi:
                    ac[(lo, hi)].append(v / m)
                    break
    return ac


# ── 1. La prueba cuantitativa, en los bins de la prediccion ───────────────
gruesos = [(0, 15), (35, 50)]
g = pares_por_cenit(gruesos)
a, b = g[(0, 15)], g[(35, 50)]
med_a, med_b = st.median(a), st.median(b)
ic_a, ic_b = ic95(a), ic95(b)
razon = med_a / med_b
solido = ic_a[0] > ic_b[1]

# ── 2. La firma de diente de sierra, en bins finos ───────────────────────
finos = [(x, x + 5) for x in range(0, 70, 5)]
f = pares_por_cenit(finos)
serie = []
for bn in finos:
    r = f[bn]
    serie.append({"bin": "%d-%d" % bn, "n": len(r),
                  "mediana": round(st.median(r), 3) if len(r) >= 5 else None,
                  "ic95": ic95(r) if len(r) >= 5 else None})

# Los saltos hacia ARRIBA son la firma buscada; se juzgan contra su IC, no a ojo.
saltos = []
prev = None
for s in serie:
    if s["mediana"] is None:
        prev = None
        continue
    if prev is not None and s["mediana"] > prev["mediana"]:
        # ¿el salto sobrevive a los IC, o cabe dentro del ruido?
        separado = s["ic95"][0] > prev["ic95"][1]
        saltos.append({"de": prev["bin"], "a": s["bin"],
                       "delta": round(s["mediana"] - prev["mediana"], 3),
                       "n_de": prev["n"], "n_a": s["n"],
                       "significativo": separado})
    prev = s

R = {"_meta": {"ventana": VENTANA, "sensor": "VIIRS375 (I-band)",
               "prediccion_pre_registrada": PRED,
               "fuente": "Schroeder et al. 2014 RSE p.86 (footprint 4,52x) + "
                         "Coppola 2014 §2.2 (el remuestreo parte el pixel)"},
     "prueba_cuantitativa": {
         "cenit_0_15": {"n": len(a), "mediana": round(med_a, 3), "ic95": ic_a},
         "cenit_35_50": {"n": len(b), "mediana": round(med_b, 3), "ic95": ic_b},
         "razon_medida": round(razon, 2),
         "ic_no_se_solapan": solido},
     "firma_diente_de_sierra": {"serie": serie, "saltos_hacia_arriba": saltos,
                                "alguno_significativo": any(s["significativo"]
                                                            for s in saltos)}}
json.dump(R, open(os.path.join(AQUI, "04_firma_area.json"), "w", encoding="utf-8"),
          indent=1, ensure_ascii=False)

print("== 1. La prueba cuantitativa (bins de la prediccion) ==")
print("  cenit 0-15 : n=%-4d mediana=%.3f  IC%s" % (len(a), med_a, ic_a))
print("  cenit 35-50: n=%-4d mediana=%.3f  IC%s" % (len(b), med_b, ic_b))
print("\n  RAZON MEDIDA            = %.2fx" % razon)
for k, v in PRED.items():
    print("  %-23s = %.2fx" % (k, v))
print("\n  los IC95 %s se solapan -> la caida %s es solida"
      % ("NO" if solido else "SI", "SI" if solido else "NO"))

print("\n== 2. La firma de diente de sierra (bins de 5 grados) ==")
print("  %-10s %5s %9s %20s" % ("cenit", "n", "mediana", "IC95"))
for s in serie:
    print("  %-10s %5d %9s %20s" % (s["bin"], s["n"],
                                    "%.3f" % s["mediana"] if s["mediana"] else "-",
                                    s["ic95"] or "-"))
print("\n  saltos hacia arriba detectados: %d" % len(saltos))
for s in saltos:
    print("    %s -> %s  %+.3f  (n %d->%d)  %s"
          % (s["de"], s["a"], s["delta"], s["n_de"], s["n_a"],
             "SIGNIFICATIVO" if s["significativo"] else "dentro del ruido"))
print("\n  VEREDICTO firma: %s"
      % ("CONFIRMADA" if any(s["significativo"] for s in saltos)
         else "NO ESTABLECIDA — n insuficiente por bin, los IC se solapan"))
