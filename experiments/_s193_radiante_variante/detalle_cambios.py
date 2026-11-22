# -*- coding: utf-8 -*-
"""Detalle de los cambios de publicación de la variante (lee resultado.json de medir_variante.py; ventana principal).

POR QUÉ: el corte del preregistro dice qué gana y qué pierde; aquí se mira de qué están hechos esos números: cuánto
publica la variante en las protegidas recuperadas contra lo que publica MIROVA (el número del tablero es la suma de
todos los alertados, que incluye el cúmulo lejano), y qué se publica nuevo donde MIROVA ubicó la fuente lejos.
Uso: python -B experiments/_s193_radiante_variante/detalle_cambios.py
"""
import json
import statistics
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
R = json.loads(Path(__file__).with_name("resultado.json").read_text(encoding="utf-8"))["principal"]


def resumen(xs):
    xs = [x for x in xs if x is not None]
    if not xs:
        return "sin datos"
    return f"n {len(xs)}, mediana {statistics.median(xs):.3f}, mín {min(xs):.3f}, máx {max(xs):.3f}"


for lectura in ("combinado", "tabla"):
    det = R[lectura]["detalle_cambios"]
    print(f"== {lectura}: grupos con cambio de publicación:", {k: len(v) for k, v in det.items()})
    for f in det.get("pos_protegida", []):
        cociente = f["disp_c"] / f["vrp_mirova"] if f["vrp_mirova"] else None
        print(f"   recuperada {f['vol']:20s} {f['sensor']:14s} {f['dt']} MIROVA {f['vrp_mirova']} MW | publica "
              f"{f['disp_c']:.3f} MW (cociente {cociente:.2f}) | alertados {f['npix']}, en el inner {f['n_dentro']} | "
              f"centroide radiante {f['d_rad']} km, cumbre {f['d_cum']} km")
    # A119 (hitos de scripts/calidad_referencia_mirova.py, impresos por el cargador): antes del 2026-06-13 el OCR no
    # medía la distancia (no se sabe si el calor estaba dentro del radio); antes del 2026-10-09, en Suomi NPP la
    # distancia y la clase del OCR pueden ser de otra pasada.
    tramos = {"OCR sin distancia (antes del 2026-06-13)": 0, "Suomi NPP, clase quizá de otra pasada (antes del 2026-10-09)": 0,
              "OCR con distancia propia": 0}
    for f in det.get("pos_protegida", []):
        if f["dt"] < "2026-06-13":
            tramos["OCR sin distancia (antes del 2026-06-13)"] += 1
        elif f["sensor"] == "VIIRS_SNPP" and f["dt"] < "2026-10-09":
            tramos["Suomi NPP, clase quizá de otra pasada (antes del 2026-10-09)"] += 1
        else:
            tramos["OCR con distancia propia"] += 1
    if det.get("pos_protegida"):
        print("   recuperadas por tramo de calidad del OCR:", tramos)
    far = det.get("far_ref", [])
    print("   far_ref nuevas, MW publicados:", resumen([f["disp_c"] for f in far]))
    print("   far_ref nuevas con 1 MW o más publicados:", sum(1 for f in far if (f["disp_c"] or 0) >= 1))
    print("   far_ref nuevas, distancia del centroide radiante (km):", resumen([f["d_rad"] for f in far]))
    print("   far_ref nuevas, alertados dentro del inner:", resumen([f["n_dentro"] for f in far]))
    si = det.get("sin_info", [])
    print("   sin_info nuevas, MW publicados:", resumen([f["disp_c"] for f in si]))
    pos = det.get("pos", [])
    print("   alertas no protegidas recuperadas, MW publicados:", resumen([f["disp_c"] for f in pos]),
          "| MIROVA:", resumen([f["vrp_mirova"] for f in pos]))
    emp = sum(f["empate"] for v in det.values() for f in v)
    print("   cambios con empate de temperatura en la semilla:", emp)
