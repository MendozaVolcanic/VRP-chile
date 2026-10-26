"""S159, pre-registro de MxD03 v2: en el log del probe M, cuánto de cada record es proceso y cuánto es buscar y bajar.

POR QUÉ. La v1 costeó con 38 s por record sin separar descarga de proceso, y no pudo costear los brazos extra (R con
varias semillas). El probe imprime `[diag ...] DOWNLOAD_DONE` al terminar cada archivo (L1B y MxD03) y una línea por
record terminado (`probe_m.py:243`). Entre el último DOWNLOAD_DONE y la línea del record corre SÓLO proceso: la
geometría en el cráter (`comparar` de S151, dos veces) y tres veces `calculate_vrp` + `append_record` (A, A2, B).
El resto del intervalo entre dos records es búsqueda en CMR (con reintentos) y descarga.

Las dos preguntas del instrumento:
1. Si el log no tuviera los marcadores, ¿se vería? Sí: cuenta records con y sin DOWNLOAD_DONE previo en su parte.
2. Si el corte estuviera mal, ¿se vería distinto? Sí: proceso + resto tiene que dar el intervalo entre records; se
   imprime la suma de cada parte contra la del intervalo total. El proceso es una cota ALTA del costo de 3 corridas
   (incluye la geometría de S151, que el A/B no necesita en todos los gránulos).

Uso: python tiempo_proceso_vs_descarga_m.py RUTA_log.txt
"""
import re
import statistics
import sys
from datetime import datetime

REC = re.compile(r"^probe \((\d)\)\t[^\t]*\t(\S+Z) \S+ M[OY]D021KM\.\S+ S\S+ A:")
DL = re.compile(r"^probe \((\d)\)\t[^\t]*\t(\S+Z) \[diag [^\]]*\] DOWNLOAD_DONE")


def ts(s):
    return datetime.strptime(s[:26], "%Y-%m-%dT%H:%M:%S.%f")


def main():
    ult_dl, ult_rec = {}, {}
    proceso, resto, sin_dl = [], [], 0
    for l in open(sys.argv[1], encoding="utf-8", errors="replace"):
        l = l.rstrip("\n")
        m = DL.match(l)
        if m:
            ult_dl[m.group(1)] = ts(m.group(2))
            continue
        m = REC.match(l)
        if not m:
            continue
        p, t = m.group(1), ts(m.group(2))
        d = ult_dl.get(p)
        if d is None or (p in ult_rec and d < ult_rec[p]):
            sin_dl += 1  # record de un granulo ya bajado (o sin marcador): no se usa
        else:
            proceso.append((t - d).total_seconds())
            if p in ult_rec:
                resto.append((d - ult_rec[p]).total_seconds())
        ult_rec[p] = t
    q = lambda v: statistics.quantiles(v, n=10)
    print(f"records con DOWNLOAD_DONE propio: {len(proceso)}; sin marcador propio: {sin_dl}")
    print(f"proceso (geometria S151 x2 + 3 corridas): mediana {statistics.median(proceso):.1f} s, "
          f"media {statistics.mean(proceso):.1f}, p10 {q(proceso)[0]:.1f}, p90 {q(proceso)[-1]:.1f}, max {max(proceso):.1f}")
    print(f"busqueda CMR + descarga entre records: mediana {statistics.median(resto):.1f} s, "
          f"media {statistics.mean(resto):.1f}, p90 {q(resto)[-1]:.1f}, max {max(resto):.1f}, n {len(resto)}")
    print(f"por corrida (cota alta, proceso/3): mediana {statistics.median(proceso)/3:.2f} s, "
          f"media {statistics.mean(proceso)/3:.2f} s")


if __name__ == "__main__":
    main()
