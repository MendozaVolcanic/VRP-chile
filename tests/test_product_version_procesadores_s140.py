# -*- coding: utf-8 -*-
"""Fase 0 tarea 8b (S140): los tres procesadores etiquetan el producto con el detector de fetch.py.

POR QUE: MODIS marca sus granules NRT con el token `.NRT.` (MYD021KM.A2026247.0750.061.
2026247092322.NRT.hdf) y VIIRS con el prefijo `_NRT` (VNP02IMG_NRT...). S133 corrigio
`pipeline.fetch.product_version_from_granule` para reconocer los dos, pero los procesadores seguian
escribiendo `"nrt" if "_NRT" in nombre else "standard"`: todo record MODIS NRT quedaba como
"standard" y `store.py`, que solo reemplaza por la calibracion definitiva los records "nrt", nunca
lo actualizaba. En silencio (A37: el esquema de un sensor no se traslada al otro).

El guard busca la expresion vieja y la llamada nueva con frontera de palabra (A92): un assert por
subcadena pasaria aunque el nombre viejo quedara dentro de otro.
"""
import re
from pathlib import Path

from pipeline.fetch import product_version_from_granule

ROOT = Path(__file__).resolve().parents[1]
PROCESADORES = ["pipeline/process_modis.py", "pipeline/process_viirs.py", "pipeline/process_viirs_mod.py"]
LLAMADA = re.compile(r"(?<![A-Za-z0-9_])product_version_from_granule\s*\(")
VIEJA = re.compile(r"\"nrt\"\s+if\s+\"_NRT\"\s+in\b")


def test_detector_reconoce_los_dos_esquemas():
    assert product_version_from_granule("MYD021KM.A2026247.0750.061.2026247092322.NRT.hdf") == "nrt"
    assert product_version_from_granule("VNP02IMG_NRT.A2026247.0606.002.2026247081613.nc") == "nrt"
    assert product_version_from_granule("MOD021KM.A2026001.0225.061.2026001131216.hdf") == "standard"
    assert product_version_from_granule("VJ102IMG.A2026099.0554.021.2026099122413.nc") == "standard"


def test_la_expresion_vieja_desaparecio_de_los_procesadores():
    for rel in PROCESADORES:
        src = (ROOT / rel).read_text(encoding="utf-8")
        assert not VIEJA.search(src), f"{rel} todavia decide el producto con '_NRT' in nombre"


def test_los_procesadores_usan_el_detector():
    for rel in PROCESADORES:
        src = (ROOT / rel).read_text(encoding="utf-8")
        assert LLAMADA.search(src), f"{rel} no llama a product_version_from_granule"
