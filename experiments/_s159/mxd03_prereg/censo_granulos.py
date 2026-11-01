"""S159, pre-registro de MxD03 v2: tamaño del censo en records y en gránulos, total y con cenit <= 35° (donde el
comparador R es comparable), y cuántos `codigo_sha` escribieron los records que deciden.

Lee los JSON de un directorio extraído con `git show` (no el checkout). Ventana de observación inclusive. Cuenta TODOS
los records MODIS de la ventana (el censo del arnés; el filtro diurno de banco_paridad no saca ninguno en MODIS
nocturno, y la población de la v1 dio 5.465, que este script tiene que reproducir: control).

Las dos preguntas del instrumento:
1. Si un JSON estuviera vacío, ¿se vería? Sí: imprime records MODIS por volcán.
2. Si el conteo de gránulos estuviera roto, ¿se vería distinto? Sí: tiene que dar 1.232 gránulos, el número del
   verificador medido con otro script (control cruzado).

Uso: python censo_granulos.py DIR_JSON [--desde 2026-03-01] [--hasta 2026-10-16]
"""
import collections
import json
import sys
from pathlib import Path

ONCE = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan", "Llaima",
        "Villarrica", "Copahue", "PuyehueCordonCaulle", "Chaiten"]


def arg(n, d):
    return sys.argv[sys.argv.index(n) + 1] if n in sys.argv else d


def main():
    d = Path(sys.argv[1])
    desde, hasta = arg("--desde", "2026-03-01"), arg("--hasta", "2026-10-16")
    recs, gran, gran35, rec35 = 0, set(), set(), 0
    shas = collections.Counter()
    por_vol = {}
    for v in ONCE:
        rr = json.load(open(d / f"{v}.json", encoding="utf-8"))["records"]
        m = [r for r in rr if str(r.get("sensor", "")).startswith("MODIS")
             and desde <= str(r.get("datetime_utc", ""))[:10] <= hasta]
        por_vol[v] = len(m)
        for r in m:
            recs += 1
            gran.add(r.get("granule"))
            shas[(r.get("regimen") or {}).get("codigo_sha", "?")[:9]] += 1
            z = r.get("sensor_zenith_deg")
            if z is not None and z <= 35:
                rec35 += 1
                gran35.add(r.get("granule"))
    print(f"ventana {desde} a {hasta}; records MODIS por volcán: {por_vol}")
    print(f"records {recs}; gránulos distintos {len(gran)}; records con cenit <= 35°: {rec35}; "
          f"gránulos con algún record <= 35°: {len(gran35)}")
    print(f"codigo_sha distintos: {len(shas)}; los 5 mayores: {shas.most_common(5)}")


if __name__ == "__main__":
    main()
