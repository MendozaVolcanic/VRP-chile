"""S159, pre-registro de MxD03: cuanto tarda un granulo MODIS en el runner, medido en el log del probe M.

Fuente: `gh run view 39681481914 --log` (probe M, 85 records MODIS, 4 partes). El probe imprime una linea por
record terminado (`probe_m.py:243`: volcan, granulo, estrato, «A:» ...). Cada record corre:
descarga del L1B + MxD03 (con reintento de CMR) y `calculate_vrp` + `store.append_record` tres veces (A, A2, B).
El intervalo entre dos lineas consecutivas de la misma parte es el costo de un granulo con 3 corridas.

Las dos preguntas del instrumento:
1. Si el log no tuviera esas lineas, ¿se veria? Si: imprime cuantas lineas encontro por parte (esperado 85 en total).
2. Si el parseo estuviera roto, ¿se veria distinto? Si: imprime el primer y ultimo intervalo crudo y la suma de
   intervalos contra la duracion del job (control: la suma no puede pasar la duracion).

Uso: python tiempo_modis_probe_m.py RUTA_log.txt
"""
import re
import statistics
import sys
from datetime import datetime

PAT = re.compile(r"^probe \((\d)\)\t[^\t]*\t(\S+Z) (\S+) (M[OY]D021KM\.\S+) (S\S+) A:")


def ts(s):
    return datetime.strptime(s[:26], "%Y-%m-%dT%H:%M:%S.%f")


def main():
    por_parte = {}
    lineas = open(sys.argv[1], encoding="utf-8", errors="replace").read().splitlines()
    for l in lineas:
        m = PAT.match(l)
        if m:
            por_parte.setdefault(m.group(1), []).append((ts(m.group(2)), m.group(3), m.group(5)))
    total = sum(len(v) for v in por_parte.values())
    print(f"lineas de record por parte: { {k: len(v) for k, v in sorted(por_parte.items())} }, total {total}")
    intervalos = []
    for k, v in sorted(por_parte.items()):
        v.sort()
        d = [(b[0] - a[0]).total_seconds() for a, b in zip(v, v[1:])]
        intervalos += d
        print(f"parte {k}: primer record {v[0][0]:%H:%M:%S}, ultimo {v[-1][0]:%H:%M:%S}, "
              f"suma de intervalos {sum(d)/60:.1f} min, n intervalos {len(d)}")
    if intervalos:
        q = statistics.quantiles(intervalos, n=10)
        print(f"segundos por granulo (3 corridas + descarga): mediana {statistics.median(intervalos):.1f}, "
              f"p10 {q[0]:.1f}, p90 {q[-1]:.1f}, max {max(intervalos):.1f}, n {len(intervalos)}")


if __name__ == "__main__":
    main()
