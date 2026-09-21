# -*- coding: utf-8 -*-
"""Desde cuando sirve cada canal de la referencia de MIROVA: UN solo lugar, consultable por codigo.

POR QUE EXISTE (A119, S149). La referencia contra la que se mide todo (los CSV del scraper Mirova-v1) no
tiene la misma calidad todo el ano: la tabla `latest.php` arranco incompleta y el OCR de las imagenes
estuvo inestable primero y mal calibrado despues. Eso se midio en S139
(docs/audit_s139/MAPA_BASES_MIROVA_V1.md, seccion 2) y aun asi en S149 se eligio una ventana de A/B sin
mirarlo, porque vivia solo en un informe. Un analisis que cruza uno de estos tramos sin saberlo no da
error: da un numero plausible y equivocado. Por eso el aviso lo da el cargador, no la memoria de nadie.

Cada hito cita su evidencia. Si el scraper cambia, se agrega un hito aca y en el documento de S139.
"""
from __future__ import annotations

import sys

# (fecha desde la cual el defecto YA NO aplica, canal, a quien afecta, que pasaba antes)
HITOS = [
    ("2026-01-16", "tabla", "todos", "antes los tipos de registro eran otros (17 filas RUTINA con VRP > 0; FALSO_POSITIVO no existia)"),
    ("2026-02-14", "tabla", "Tupungatito", "antes Tupungatito no tiene ninguna fila"),
    ("2026-02-23", "tabla", "Tupungatito", "antes su limite de alerta era 5 km y no 7"),
    ("2026-03-01", "tabla", "todos", "antes la cobertura nocturna de la tabla era 86 % (enero) y 95 % (febrero); desde marzo 99 a 100 %"),
    ("2026-03-01", "ocr", "VIIRS", "antes el OCR corrio con siete versiones y doce metodos de validacion distintos; capturo 0,26 a 0,29 alertas por alerta de la tabla contra 0,50 a 0,89 despues, y no hubo reproceso retroactivo"),
    ("2026-04-01", "tabla", "VIIRS por pasada", "antes la tabla exponia 1,6 a 1,8 granulos VIIRS por noche de volcan, contra 2,3 a 2,6 en abril a junio y 3,0 a 3,4 en agosto y septiembre: una TASA POR PASADA de VIIRS anterior a abril no es comparable con una posterior (MODIS es plano todo el ano)"),
    ("2026-06-11", "ocr", "VIIRS", "antes la geometria del OCR estaba mal calibrada (Tupungatito 5,1 km en vez de 7; formula de distancia invertida): la separacion alerta contra falso positivo lejano del OCR no es confiable"),
    ("2026-06-13", "ocr", "VIIRS", "antes el OCR no media la distancia (Distancia_km = 0 fijo) y sus notas quedaron en mojibake: el loader no les encuentra distancia"),
    ("2026-08-06", "ocr", "VIIRS", "cambio de version del OCR a 30.0 (no es un defecto, es un cambio de regimen dentro de una ventana)"),
]
FUENTE = "docs/audit_s139/MAPA_BASES_MIROVA_V1.md seccion 2"


def avisos_de_ventana(desde: str, hasta: str) -> list[str]:
    """Hitos que la ventana [desde, hasta] pisa: los que todavia no se cumplian al empezar la ventana."""
    return ["%s (%s, %s): %s" % (f, canal, quien, que) for f, canal, quien, que in HITOS if desde < f]


def etiqueta_que_decide(desde: str) -> str:
    """Que canal puede DECIDIR una etiqueta positiva en una ventana que empieza en `desde`."""
    return "tabla y OCR" if desde >= "2026-06-13" else "SOLO la tabla; el OCR se informa aparte"


def avisar(desde: str, hasta: str, archivo=None) -> list[str]:
    av = avisos_de_ventana(desde, hasta)
    if av:
        out = archivo or sys.stderr
        print("[referencia MIROVA] la ventana %s a %s pisa %d tramos con defectos conocidos (%s). Decide: %s" % (
            desde, hasta, len(av), FUENTE, etiqueta_que_decide(desde)), file=out)
        for a in av:
            print("   - " + a, file=out)
    return av
