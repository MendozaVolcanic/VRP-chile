# -*- coding: utf-8 -*-
"""Detector de producto NRT o Standard a partir del nombre del granule.

POR QUE vive aparte (S140, Fase 0 tarea 8b): los tres procesadores lo necesitan para etiquetar cada
record, pero `pipeline/fetch.py` importa earthaccess y carga el .env al importarse. Importarlo desde
ahi haria que cualquier `import pipeline.process_*` (incluidos los tests) arrastrara la red y las
credenciales. La funcion se movio sin cambios; `pipeline.fetch` la reexporta por compatibilidad.
"""
from __future__ import annotations


def product_version_from_granule(filename: str) -> str:
    """
    Return "nrt" if the granule filename corresponds to a LANCE-NRT product,
    "standard" otherwise.

    ⚠️ S133 — LOS DOS SENSORES LO MARCAN DISTINTO. Verificado contra el CMR el
    2026-09-04 (ver docs/s133/AUDITORIA_NRT_MODIS.md):

        VIIRS  VNP02IMG_NRT.A2026247.0606.002.2026247081613.nc   -> prefijo `_NRT`
        MODIS  MYD021KM.A2026247.0750.061.2026247092322.NRT.hdf  -> token `.NRT.`

    Esta función sólo miraba `_NRT`, así que TODO granule NRT de MODIS se guardaba como
    "standard". No es cosmético: `store.py` reemplaza por la calibración definitiva
    únicamente los records marcados "nrt", así que un NRT mal etiquetado se queda con la
    calibración provisional para siempre, y en silencio.

    Es la misma asimetría entre sensores que A37 (saturación) y que el bug de los
    short_name que destapó esto: el esquema de un sensor no se traslada al otro.

    Standard, para contraste — ninguno lleva la marca:
    MOD021KM.A2026001.0225.061.2026001131216.hdf
    VJ102IMG.A2026099.0554.021.2026099122413.nc

    Used by process_*.py to tag each record with its data source so the
    historical archive can be audited for NRT vs Standard provenance, and
    so the weekly auto-upgrade cron can identify records to replace when
    Standard becomes available.
    """
    base = filename.replace("\\", "/").rsplit("/", 1)[-1]
    # `.NRT.` se busca como token delimitado por puntos y no como subcadena suelta:
    # una ruta o un nombre que contenga esas letras por casualidad no debe contar (A92).
    return "nrt" if ("_NRT" in base or ".NRT." in base) else "standard"
