# -*- coding: utf-8 -*-
"""S126 - los dos canales del ground truth MIROVA salen del mismo snapshot.

POR QUE EXISTE: `scripts/build_c2ab_windows.py` tomaba el consolidado del directorio
`mirova_v1_snapshot/` y el OCR de una copia suelta un nivel mas arriba. Esa copia quedo
congelada el 2026-03-28 (236 filas) mientras el snapshot llega al 2026-08-24 (888),
porque `audit-weekly.yml` solo refresca la del snapshot. Resultado: las ventanas del A/B
se construian con cinco meses menos de canal OCR — 844 fechas ALERTA en vez de 903 sobre
los 11 Tier A.

El canal OCR es COMPLEMENTO del consolidado, no validacion (A11): MIROVA publica algunas
cosas en `latest.php` y otras solo como imagen por volcan, y el OCR extrae esas. Lo que
falta en un canal no aparece en el otro, asi que mezclar dos cortes temporales distintos
pierde datos en silencio.

Este test no fija rutas concretas: fija la INVARIANTE de que ambos canales vengan del
mismo directorio, que es lo que se rompio.
"""
import importlib.util
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


def _cargar(nombre, ruta):
    spec = importlib.util.spec_from_file_location(nombre, ruta)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[nombre] = mod
    spec.loader.exec_module(mod)
    return mod


def test_build_c2ab_toma_los_dos_canales_del_mismo_directorio():
    mod = _cargar("_s126_build_c2ab", REPO / "scripts" / "build_c2ab_windows.py")
    assert mod.CONS.parent == mod.OCR.parent, (
        "el consolidado y el OCR salen de directorios distintos "
        f"({mod.CONS.parent} vs {mod.OCR.parent}): se estarian mezclando dos cortes "
        "temporales del ground truth. Ver docs/S126_CLOUDMASK_YA_ESTA_VIVA.md para el "
        "patron general (intencion declarada != realidad).")


def test_el_snapshot_que_refresca_el_workflow_es_el_que_se_consume():
    """El canal que consume el script debe ser el que audit-weekly.yml actualiza."""
    wf = (REPO / ".github" / "workflows" / "audit-weekly.yml").read_text(encoding="utf-8")
    mod = _cargar("_s126_build_c2ab_b", REPO / "scripts" / "build_c2ab_windows.py")
    rel = mod.OCR.relative_to(REPO).as_posix()
    assert rel in wf, (
        f"{rel} no aparece en audit-weekly.yml: el script consume un CSV que nadie "
        "refresca, asi que se congela sin que nada avise.")
