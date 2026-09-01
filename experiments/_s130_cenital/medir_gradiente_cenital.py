# -*- coding: utf-8 -*-
"""S130 - El sub-reporte crece con el angulo cenital, y MIROVA es plano.

POR QUE. El bloque de arranque S130 hereda de S129 que "VIIRS375 va de 0,796 cerca
del nadir a 0,570 entre 35 y 50 grados". Regla de la etapa: no heredar afirmaciones
sin trazarlas. Este script las vuelve a medir con su definicion explicita, y de paso
agrega el CONTROL DE INSTRUMENTO que faltaba.

EL CONTROL ES LO QUE IMPORTA. Un ratio nuestro/MIROVA que cae con el angulo admite
dos lecturas opuestas: que nosotros perdemos senal en oblicuo, o que MIROVA la infla.
Separarlas necesita mirar los dos numerador y denominador por separado. Si MIROVA
resulta PLANO con el angulo y nosotros caemos, la conclusion es nuestra:

  Coppola 2014 seccion 2.2 describe que MIROVA REMUESTREA a una malla de area
  constante. Un pixel VIIRS a 50 grados es mucho mas grande que a nadir; al
  remuestrear, MIROVA reparte esa energia en celdas de area nominal y su magnitud
  no depende del angulo. La nuestra integra sobre el pixel tal como viene.

DEFINICIONES, dentro de la afirmacion (A90):
  · un par por (volcan, fecha, bucket de sensor), el maximo de cada lado;
  · nuestro valor = `primary_cluster.vrp_mw` (A10: NUNCA `record.vrp_mw`, que es
    suma scene-wide);
  · MIROVA = loader canonico CONS union OCR (A11);
  · solo pasadas NOCTURNAS (solar_zenith >= 90): el MIR diurno no se usa;
  · ventana 2026, los 11 Tier A;
  · el angulo es `sensor_zenith_deg` del record, en valor absoluto.

Cota superior por D2 (cobertura del CSV, 79,2 %), igual para todos los bins, asi
que la COMPARACION entre bins no se ve afectada — que es lo unico que se afirma.
"""
import io
import json
import os
import statistics as st
import sys
from collections import defaultdict

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "experiments"))

from _s126_lib import bucket, cargar_mirova                      # noqa: E402

OUT = os.path.join(HERE, "resultado_gradiente.json")
VOLS = ["Chaiten", "Copahue", "Isluga", "Lascar", "Lastarria", "Llaima",
        "NevadosDeChillan", "PlanchonPeteroa", "PuyehueCordonCaulle",
        "Tupungatito", "Villarrica"]
BINS = ["0-15", "15-25", "25-35", "35-50", "50+"]
MIN_N = 15          # por debajo de esto la mediana no se reporta


def bin_de(sz):
    a = abs(sz)
    if a < 15:
        return "0-15"
    if a < 25:
        return "15-25"
    if a < 35:
        return "25-35"
    if a < 50:
        return "35-50"
    return "50+"


def main():
    mir, _ = cargar_mirova(("2026-01-01", "2026-12-31"))
    # (bucket, bin) -> listas
    ratios = defaultdict(list)
    nuestro = defaultdict(list)
    mirova = defaultdict(list)

    for v in VOLS:
        p = os.path.join(ROOT, "data", "mirova_equivalent", v + ".json")
        if not os.path.exists(p):
            continue
        for r in json.load(open(p, encoding="utf-8"))["records"]:
            bk = bucket(r.get("sensor"))
            if bk is None:
                continue
            sol = r.get("solar_zenith_deg")
            if sol is not None and sol < 90:
                continue                       # el MIR diurno no se usa
            sen = r.get("sensor_zenith_deg")
            pcv = (r.get("primary_cluster") or {}).get("vrp_mw") or 0
            if sen is None or pcv <= 0:
                continue
            m = (mir.get(v) or {}).get((r.get("datetime_utc", "")[:10], bk))
            if not m or m <= 0:
                continue
            k = (bk, bin_de(sen))
            ratios[k].append(pcv / m)
            nuestro[k].append(pcv)
            mirova[k].append(m)

    def med(d, k):
        x = d.get(k, [])
        return round(st.median(x), 3) if len(x) >= MIN_N else None

    res = {
        "definicion": (
            "ratio = pc.vrp_mw nuestro / VRP MIROVA, un par por (volcan, fecha, "
            "bucket), maximo de cada lado, solo pasadas nocturnas, ventana 2026, "
            "11 Tier A. El angulo es |sensor_zenith_deg| del record. Medianas con "
            f"n >= {MIN_N}. Cota superior por D2, igual para todos los bins."
        ),
        "por_sensor_y_bin": {},
        "control_de_instrumento": {},
    }
    for bk in ("modis", "v750", "v375"):
        res["por_sensor_y_bin"][bk] = {
            b: {"n": len(ratios.get((bk, b), [])), "ratio": med(ratios, (bk, b))}
            for b in BINS
        }
        res["control_de_instrumento"][bk] = {
            b: {"n": len(nuestro.get((bk, b), [])),
                "nuestro_mediano_mw": med(nuestro, (bk, b)),
                "mirova_mediano_mw": med(mirova, (bk, b))}
            for b in BINS
        }

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=2, ensure_ascii=False)

    print("EL SUB-REPORTE CRECE CON EL ANGULO CENITAL")
    print()
    print("ratio nuestro/MIROVA por bin:")
    print(f"{'bin':10s} " + "".join(f"{s:>18s}" for s in ("MODIS", "VIIRS750", "VIIRS375")))
    for b in BINS:
        fila = f"{b:10s} "
        for bk in ("modis", "v750", "v375"):
            d = res["por_sensor_y_bin"][bk][b]
            fila += (f"{d['ratio']:>11.3f} (n{d['n']:>3d})" if d["ratio"] is not None
                     else f"{'n<' + str(MIN_N):>11s} (n{d['n']:>3d})")
        print(fila)

    print()
    print("CONTROL DE INSTRUMENTO - quien se mueve con el angulo (MW medianos):")
    for bk, nom in (("v375", "VIIRS375"), ("v750", "VIIRS750"), ("modis", "MODIS")):
        filas = [(b, res["control_de_instrumento"][bk][b]) for b in BINS]
        if not any(d["nuestro_mediano_mw"] is not None for _b, d in filas):
            continue
        print(f"\n  {nom}")
        print(f"    {'bin':10s} {'n':>6s} {'NUESTRO':>10s} {'MIROVA':>10s}")
        for b, d in filas:
            if d["nuestro_mediano_mw"] is None:
                continue
            print(f"    {b:10s} {d['n']:6d} {d['nuestro_mediano_mw']:10.3f} "
                  f"{d['mirova_mediano_mw']:10.3f}")

    print()
    print("Si MIROVA sale PLANO y lo nuestro cae, el sub-reporte es NUESTRO y la")
    print("explicacion es el remuestreo a malla de area constante (Coppola 2014 2.2).")
    print(f"\n-> {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
