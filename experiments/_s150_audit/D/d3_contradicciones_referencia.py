# -*- coding: utf-8 -*-
"""S150 auditor D, sonda 3: pasadas donde la TABLA y el OCR de MIROVA se contradicen, y que etiqueta
les pone banco_paridad.etiquetar.

PREGUNTAS DEL INSTRUMENTO
 1. Si el etiquetador resolviera mal una contradiccion, esta sonda lo veria? Si: agrupo las filas de
    referencia por pasada (volcan, sensor, +-120 s, mismo criterio que bp.parear) y cruzo el tipo de la
    fila CONS con el de la fila OCR, y luego llamo a bp.etiquetar sobre una pasada sintetica en ese
    mismo instante para ver la etiqueta que sale.
 2. Si la sonda estuviera muerta, se veria distinto? Control positivo: inyecto una fila OCR ALERTA
    sintetica sobre una pasada CONS RUTINA conocida y tiene que aparecer como contradiccion y salir "pos".

Uso: python d3_contradicciones_referencia.py <desde> <hasta> [dir_congelado]
"""
import collections, io, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "scripts"))
import banco_paridad as bp
from referencia_mirova_unificada import cargar_referencia_unificada

desde, hasta = sys.argv[1:3]
if len(sys.argv) > 3:
    d = Path(sys.argv[3]); filas = cargar_referencia_unificada(d / "registro_vrp_consolidado.csv", d / "registro_vrp_ocr.csv")
else:
    filas = cargar_referencia_unificada()
coords = bp._coords_por_volcan()


def tipo(f):
    return "ALERTA" if bp.es_alerta(f["tipo"]) else ("FP" if bp.es_fp(f["tipo"]) else ("RUTINA0" if (f["vrp_mw"] or 0) == 0 else "RUTINA>0"))


def medir(filas, etiqueta=""):
    por_vb, ns, nv, n = bp.indexar_referencia(filas, coords, (desde, hasta))
    cruce = collections.Counter(); ejemplos = collections.defaultdict(list)
    for (vol, b), lista in por_vb.items():
        for dt, f in lista:
            if f["source"] != "OCR":
                continue
            par = [g for g in bp.parear(lista, dt) if g["source"] == "CONS"]
            k = (b, "OCR " + tipo(f), "CONS " + (",".join(sorted({tipo(g) for g in par})) if par else "sin fila"))
            cruce[k] += 1
            # que etiqueta le pone el banco a una pasada nuestra en ese instante
            r = {"vol": vol, "b": b, "dt": dt, "noche": dt.strftime("%Y-%m-%d")}
            bp.etiquetar([r], por_vb, ns, nv)
            if len(ejemplos[k]) < 3:
                ejemplos[k].append((vol, f["fecha_utc"], f["vrp_mw"], r["lab"]))
    print("== %s ventana %s a %s, filas nocturnas %d" % (etiqueta, desde, hasta, n))
    for k, v in sorted(cruce.items()):
        print("  %-8s %-14s %-24s %4d | ej: %s" % (k[0], k[1], k[2], v, ejemplos[k]))
    return cruce


c = medir(filas, "REAL")
# control positivo: una fila OCR ALERTA sobre una pasada CONS RUTINA cualquiera
base = next(f for f in filas if f["source"] == "CONS" and f["tipo"] == "RUTINA" and desde <= f["fecha_utc"][:10] <= hasta
            and f["fecha_utc"][11:13] in ("05", "06") and f["sensor_bucket"] == "VIIRS375")
sint = dict(base, source="OCR", tipo="ALERTA_TERMICA_OCR", vrp_mw=0.123, fecha_utc=base["fecha_utc"][:17] + "30")
c2 = medir(filas + [sint], "CONTROL (+1 OCR ALERTA sintetica sobre %s %s)" % (base["volcano"], base["fecha_utc"]))
k = ("VIIRS375", "OCR ALERTA", "CONS RUTINA0")
print("CONTROL POSITIVO: %s pasa de %d a %d" % (k, c.get(k, 0), c2.get(k, 0)))
