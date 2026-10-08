# -*- coding: utf-8 -*-
"""S150 frente B. Resume tabla_ndc.json (produccion) y tabla_ndc_flag.json (contrafactual del
flag de etiqueta por cumulo) por sensor, en la unidad pasada (misma adquisicion, +-10 min).

Preguntas del instrumento:
1. Si el tablero ocultara toda alerta de MIROVA, 'alerta_oculta' = 'alertas_con_record'.
   Control positivo: 2026-10-01 08:35 MODIS debe estar en 'alerta_oculta' en produccion.
2. Si el pareo estuviera muerto, 'alertas_con_record' daria 0: se imprime el total de filas de
   MIROVA y cuantas parearon.
Ventana: 2026-09-20 00:00 a 2026-10-02 07:35 UTC (ultimo record del JSON remoto).
"""
import json, sys, collections
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent


def nivel(v):
    if not v or v <= 0:
        return "Sin datos"
    for lab, mx in (("Muy Bajo", 1), ("Bajo", 10), ("Moderado", 100), ("Alto", 1000)):
        if v < mx:
            return lab
    return "Muy Alto"


def resumir(nombre):
    t = json.load(open(AQUI / nombre, encoding="utf-8"))
    c = collections.defaultdict(collections.Counter)
    detalle = []
    for x in t["filas"]:
        b = x["b"]
        al = [m for m in x["mirova"] if m["tipo"].startswith("ALERTA")]
        rut = [m for m in x["mirova"] if m["tipo"] == "RUTINA"]
        pub = x["ix_chart"] > 0
        c[b]["records"] += 1
        c[b]["publicados_index"] += pub
        c[b]["tarjeta_elegible"] += x["ix_card"]
        if al:
            mv = max(m["vrp"] for m in al)
            c[b]["alertas_con_record"] += 1
            if pub:
                c[b]["alerta_publicada"] += 1
                r = x["ix_chart"] / mv
                c[b]["_ratios"] += 0  # placeholder
                detalle.append((b, x["dt"], x["sensor"], round(x["ix_chart"], 2), mv, round(r, 2), nivel(x["ix_chart"]), nivel(mv)))
                if nivel(x["ix_chart"]) != nivel(mv):
                    c[b]["nivel_distinto"] += 1
            else:
                c[b]["alerta_oculta"] += 1
                detalle.append((b, x["dt"], x["sensor"], 0, mv, None, "OCULTA", nivel(mv)))
        elif rut and pub:
            c[b]["publica_en_RUTINA"] += 1
            if x["ix_cens"]:
                c[b]["  de_ellas_censurado_5.00"] += 1
        elif not x["mirova"] and pub:
            c[b]["publica_sin_fila_MIROVA"] += 1
        if x["ix_chart"] != x["di_chart"]:
            c[b]["index!=diario"] += 1
        if x["ix_chart"] != x["mo_spark"]:
            c[b]["index!=mosaico_spark"] += 1
        if x["ix_card"] != x["mo_card"]:
            c[b]["index_tarjeta!=mosaico_tarjeta"] += 1
    print(f"== {nombre}")
    for b in ("MODIS", "VIIRS375", "VIIRS750"):
        print(" ", b, {k: v for k, v in c[b].items() if not k.startswith("_")})
    return detalle


d0 = resumir("tabla_ndc.json")
print("\nDETALLE produccion, pasadas con alerta MIROVA (CONS u OCR) en la misma adquisicion:")
print("sensor   fecha            plataforma          nuestro  MIROVA  razon  nivel_nuestro  nivel_MIROVA")
for r in sorted(d0, key=lambda r: (r[1], r[0])):
    print(f"{r[0]:<8} {r[1]} {r[2]:<18} {r[3]:>7} {r[4]:>7} {str(r[5]):>6}  {r[6]:<13} {r[7]}")
print()
resumir("tabla_ndc_flag.json")
