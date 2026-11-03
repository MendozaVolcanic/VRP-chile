# -*- coding: utf-8 -*-
"""C-via por trozo de la prueba retrospectiva del paquete (pre-registro SELLADO
experiments/_s172_prereg_retro/PREREGISTRO_RETRO_PAQUETE.md, tag s173-prereg-retro-sellado, §6 C-via y C-cobertura;
plan 2026-11-02-nrt-34-volcanes, Tarea 0.2 paso 7).

POR QUÉ. La vía «código MIROVA» vuelve a K en silencio cuando le falta algo (sin `pyproj`, sin grilla, sin MxD03): el
job sale verde y los records dicen K. Un CUMPLE leído sobre esos records mediría K contra K. Este script cuenta, por
sensor, cuántos records traen la marca `via_codigo_mirova` en True y deja el trozo en rojo si no llega al mínimo. Se
imprime en el log del runner y la lectura lo vuelve a calcular (un vigilante ciego da verde, S156).

Mínimo por régimen (§6): en F26 y DM, 100 % (un record sin la marca es rojo, como MOD-D §8.6). En R25 un record sin
la marca sale de los dos brazos a SIN DATO en la lectura, con tope de 10 % por clase; aquí, sin etiquetas de MIROVA,
el runner sólo avisa si el sensor entero baja de 90 % (`--minimo 0.90`): decide la lectura, no este paso.
En el brazo K-gemelo (`--esperado k`) es al revés: ningún record puede traer la marca en True.

LAS DOS PREGUNTAS DEL INSTRUMENTO. (1) Si la vía no corriera, un 0 % en el sensor lo deja rojo. (2) Si el trozo no
escribiera nada (artefacto vacío, carpeta equivocada), 0 records da rojo con salida 4, no verde.

Un sensor sin records en el trozo NO es rojo (VPR940-08, verificador de #940): en un trozo de 1 a 3 días (D1, D3) la
vía puede descartar sin record todas las pasadas de un sensor por su regla de cobertura (mirova_v750_codigo.py,
hallazgo 171-01), con datos válidos. Ese trozo se sube igual, con un aviso y la línea `SENSOR_VACIO <sensor>` en
controles_via.txt (que viaja con el log), y lo decide C-cobertura en la lectura, contando las pasadas de K.

Uso: python controles_via.py <carpeta_de_jsons> [--esperado via|k] [--minimo 1.0]
Salida: 0 bien (también con un sensor vacío, marcado); 3 C-via falla; 4 sin ningún record.
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib
import sys

SENSORES = ("MODIS", "V375", "V750")


def sensor(nombre):
    """MODIS_* = MODIS; VIIRS_*_750 = M-band; VIIRS_* sin sufijo = I-band 375 m (convención del proyecto, A48)."""
    nombre = nombre or ""
    if nombre.startswith("MODIS"):
        return "MODIS"
    if nombre.startswith("VIIRS"):
        return "V750" if nombre.endswith("_750") else "V375"
    return None


def contar(carpeta):
    """Counter[(sensor, marca)] sobre todos los records de los JSON de la carpeta. La marca se guarda como str:
    'True' (la vía corrió), 'sin_grilla', 'sin_mxd03', 'geo_distinta', 'None' (record sin la clave: es K)."""
    c = collections.Counter()
    for f in sorted(pathlib.Path(carpeta).glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        for r in d.get("records", []):
            s = sensor(r.get("sensor"))
            if s is None:
                continue
            c[(s, str(r.get("via_codigo_mirova")))] += 1
    return c


def revisar(c, esperado="via", minimo=1.0):
    """Devuelve (código de salida, líneas). Pura: la prueba la ejerce sin archivos."""
    lineas, codigo = [], 0
    total = sum(c.values())
    if total == 0:
        return 4, ["::error::C-via: el trozo no tiene ningún record (artefacto vacío o carpeta equivocada)"]
    for s in SENSORES:
        tot = sum(n for (ss, _), n in c.items() if ss == s)
        via = c[(s, "True")]
        otros = {e: n for (ss, e), n in sorted(c.items()) if ss == s and e != "True"}
        if tot == 0:
            lineas.append(f"{s}: 0 records")
            lineas.append(f"::warning::C-via: {s} sin records en el trozo (lo decide C-cobertura en la lectura)")
            lineas.append(f"SENSOR_VACIO {s}")
            continue
        frac = via / tot
        lineas.append(f"{s}: {via}/{tot} de la via ({frac:.1%}); otros: {otros}")
        if esperado == "via" and frac < minimo:
            lineas.append(f"::error::C-via falla en {s}: {tot - via} records sin la marca (minimo {minimo:.0%})")
            codigo = max(codigo, 3)
        if esperado == "k" and via > 0:
            lineas.append(f"::error::C-via (K-gemelo): {via} records de {s} con la via encendida")
            codigo = max(codigo, 3)
    return codigo, lineas


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("carpeta")
    ap.add_argument("--esperado", choices=("via", "k"), default="via")
    ap.add_argument("--minimo", type=float, default=1.0)
    a = ap.parse_args(argv)
    codigo, lineas = revisar(contar(a.carpeta), a.esperado, a.minimo)
    for x in lineas:
        print(x)
    return codigo


if __name__ == "__main__":
    sys.exit(main())
