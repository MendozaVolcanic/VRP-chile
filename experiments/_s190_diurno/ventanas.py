# -*- coding: utf-8 -*-
"""S190 diurno: tamano de cada ventana candidata del A/B (pasadas diurnas de MIROVA, alertas y protegidas por sensor).

POR QUE. El pre-registro tiene que decir cuanto sustrato trae cada ventana antes de despacharla. Es un conteo
grueso para elegir ventanas (pasada = volcan, sensor, minuto; dia = elevacion solar > 0; OCR solo desde el
2026-06-13, A119); el sustrato que decide lo cuenta el evaluador sobre la referencia congelada.
Salida: ventanas_salida.txt.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import inventario as I  # noqa: E402

TIER_A = ["Lascar", "Lastarria", "Isluga", "NevadosDeChillan", "Llaima", "Villarrica", "Chaiten", "Copahue",
          "PlanchonPeteroa", "Tupungatito", "PuyehueCordonCaulle"]
VENTANAS = {"W2": ("2026-06-13", "2026-06-30"), "W3": ("2026-07-20", "2026-07-31"),
            "W4": ("2026-08-13", "2026-08-31"), "W5": ("2026-09-01", "2026-09-20"),
            "W6": ("2026-10-01", "2026-10-14"), "W7": ("2026-10-15", "2026-11-15")}


def main():
    co = I.coords()
    filas = I.RMU.cargar_referencia_unificada()
    tab = {}
    filas_tabla_por_dia = Counter()
    for f in filas:
        if f["volcano"] not in TIER_A:
            continue
        dia = f["fecha_utc"][:10]
        w = next((k for k, (a, b) in I_items() if a <= dia <= b), None)
        if w is None:
            continue
        if f["source"] == "OCR" and dia < I.OCR_DESDE:
            continue
        lat, lon = co[f["volcano"]]
        k = (w,) + I.clave_pasada(f)
        d = tab.setdefault(k, {"dia": I.es_dia(lat, lon, f["fecha_utc"]), "a": False, "p": False, "tabla": False})
        d["a"] |= f["tipo"] in I.TIPOS_ALERTA
        d["p"] |= I.alerta_protegida(f)
        d["tabla"] |= f["source"] == "CONS"
        if f["source"] == "CONS":
            filas_tabla_por_dia[(w, dia)] += 1
    print("Ventana  sensor     pasadas_dia  alertas_dia  protegidas_dia  rutina_dia_tabla  (pasadas noche)")
    for w in VENTANAS:
        for s in ("MODIS", "VIIRS375", "VIIRS750"):
            sel = [d for k, d in tab.items() if k[0] == w and k[2] == s]
            dia = [d for d in sel if d["dia"]]
            print("%-8s %-10s %11d %12d %15d %17d  (%d)" % (
                w, s, len(dia), sum(d["a"] for d in dia), sum(d["p"] for d in dia),
                sum(1 for d in dia if d["tabla"] and not d["a"]), len(sel) - len(dia)))
    print("\nDias de cada ventana sin ninguna fila de la tabla (latest.php) en los 11 Tier A:")
    from datetime import date, timedelta
    for w, (a, b) in VENTANAS.items():
        d0, d1 = date.fromisoformat(a), date.fromisoformat(b)
        faltan = []
        while d0 <= d1:
            if filas_tabla_por_dia[(w, d0.isoformat())] == 0:
                faltan.append(d0.isoformat())
            d0 += timedelta(days=1)
        print("  %s: %s" % (w, ", ".join(faltan) if faltan else "ninguno"))


def I_items():
    return VENTANAS.items()


if __name__ == "__main__":
    main()
