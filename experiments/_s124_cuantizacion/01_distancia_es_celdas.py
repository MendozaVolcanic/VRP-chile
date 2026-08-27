# -*- coding: utf-8 -*-
"""S124 — El `Distancia_km` de MIROVA esta CUANTIZADO a celdas de su grilla.

ORIGEN: Nicolas pregunto "las distancias que me das de MIROVA, respecto a que
punto son?" y yo habia ASUMIDO que median desde el GVP. Auditando en vez de
asumir aparecio algo mejor.

HIPOTESIS: si MIROVA resamplea a una grilla regular ANTES de detectar (Coppola
2016a ~L162; Campus 2022 §3.2), entonces la distancia entre el hotspot y la
referencia no puede ser continua: es un offset ENTERO de celdas. Cada valor
publicado deberia ser sqrt(i^2 + j^2) * celda con i, j enteros.

RESULTADO (consolidado completo, 2026-08-27):
    MODIS     celda 1.000 km -> 10085/10085 = 100.0%   (40 valores distintos)
    VIIRS375  celda 0.375 km -> 11810/11810 = 100.0%  (450 valores distintos)

Los valores MODIS crudos lo muestran a simple vista:
    0, 1, 1.41, 2, 2.24, 3.16, 3.61, 6.40, 7.81, 8.06, 9.06, 9.49, 10.63...
  = 0, 1, sqrt2, 2, sqrt5, sqrt10, sqrt13, sqrt41, sqrt61, sqrt65, sqrt82,
    sqrt90, sqrt113

CONTROL: con celdas arbitrarias el ajuste baja (VIIRS375 a 0.5 km da 89%), asi
que el test no es trivial. Para MODIS discrimina menos (40 valores, tolerancia)
pero la lista de raices de arriba no deja lugar a duda.

QUE SIGNIFICA
  1. Confirmacion INDEPENDIENTE del frente F70, sacada de los datos publicados
     de MIROVA y no de sus papers: su grilla existe y sus celdas son
     exactamente 1 km (MODIS) y 375 m (VIIRS I-band), que es lo que F70.2
     implemento.
  2. La referencia es una CELDA, no un punto. "Distancia 0.00 km" NO significa
     "en el crater": significa "en la misma celda que la referencia", o sea en
     cualquier lugar de un cuadrado de 375 m.
  3. Toda comparacion de distancias contra MIROVA arrastra +-media celda de
     incertidumbre. Un ratio de distancias sub-celda no significa nada.

Fuente de verdad de los numeros del informe (regla S91).
"""
import collections
import csv
import io
import math
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = Path(__file__).resolve().parents[2]


def compatible(D, celda, tol=0.006, nmax=120):
    """existe (i,j) entero con |sqrt(i^2+j^2)*celda - D| < tol?"""
    n = D / celda
    for i in range(0, min(nmax, int(n) + 2)):
        j2 = n * n - i * i
        if j2 < 0:
            break
        j = round(math.sqrt(j2))
        if abs(math.hypot(i, j) * celda - D) < tol:
            return True
    return False


if __name__ == "__main__":
    vals = collections.Counter()
    with open(ROOT / "latest_consolidado.csv", encoding="utf-8", errors="replace") as fh:
        for r in csv.DictReader(fh):
            sen = (r.get("Sensor") or "").strip().upper()
            try:
                vals[(sen, round(float(r.get("Distancia_km")), 2))] += 1
            except (TypeError, ValueError):
                pass

    print("HIPOTESIS: Distancia_km = offset ENTERO de celdas en la grilla MIROVA\n")
    for sen, celda in (("VIIRS375", 0.375), ("VIIRS750", 0.75), ("MODIS", 1.0)):
        ds = [(d, n) for (s, d), n in vals.items() if s == sen]
        if not ds:
            continue
        tot = sum(n for _, n in ds)
        ok = sum(n for d, n in ds if compatible(d, celda))
        print(f"  {sen:9s} celda {celda:5.3f} km -> {ok:6d}/{tot:6d} = "
              f"{100*ok/tot:5.1f}%  ({len(ds)} valores distintos)")

    print("\n  CONTROL (celdas arbitrarias: el test no debe dar alto con cualquiera)")
    for sen, celda in (("VIIRS375", 0.5), ("VIIRS375", 0.25), ("MODIS", 0.7)):
        ds = [(d, n) for (s, d), n in vals.items() if s == sen]
        tot = sum(n for _, n in ds)
        ok = sum(n for d, n in ds if compatible(d, celda))
        print(f"  {sen:9s} celda {celda:5.3f} km -> {100*ok/tot:5.1f}%")

    print("\n  MODIS, los valores crudos (deben ser raices de suma de cuadrados):")
    md = sorted(d for (s, d) in vals if s == "MODIS")[:14]
    print("   ", md)
    print("    =", [f"√{round(d*d)}" if abs(d - round(d)) > 0.01 else f"{d:.0f}" for d in md])
