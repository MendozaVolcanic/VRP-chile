# -*- coding: utf-8 -*-
"""Mutaciones del lector de la retrospectiva (pre-registro SELLADO PREREGISTRO_RETRO_PAQUETE.md §11: «mutaciones
atrapadas por aserción con control de caída»).

POR QUÉ. Una batería en verde no dice que pueda ponerse roja. Cada mutación de abajo rompe una regla del pre-registro
en una copia del lector, y la batería tests/test_leer_retro_s172.py se corre contra esa copia (LEER_RETRO_MODULO).
Cuenta como ATRAPADA sólo si alguna prueba falla por AssertionError; si las fallas son excepciones (el código cae), es
CAE y no cuenta como atrapada (S152: una mutación que cae no fue vista por ninguna aserción). La mutación de control
introduce un NameError a propósito: tiene que salir CAE, y si sale ATRAPADA el contador está roto.

La copia vive al lado del original con un nombre que empieza por `_mut_` (el lector calcula la raíz del repo desde su
propia carpeta) y se borra al terminar. No se edita el lector mientras corre la batería (A112): cada mutación es otra
copia.

Uso: python mutar_leer_retro.py [--solo NOMBRE] > mutar_leer_retro_salida.txt
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
ORIGINAL = AQUI / "leer_retro.py"
BATERIA = RAIZ / "tests" / "test_leer_retro_s172.py"

MUTACIONES = [
    ("M1 fila 5 antes que la 4 (VPR172-03)",
     "    if f == 4 or motivos4:\n        return 4, NOMBRES_FILA[4], motivos4 + ([\"regla del sensor\"] if f == 4 else [])\n    if f == 5:\n        return 5, NOMBRES_FILA[5], []\n",
     "    if f == 5:\n        return 5, NOMBRES_FILA[5], []\n    if f == 4 or motivos4:\n        return 4, NOMBRES_FILA[4], motivos4 + ([\"regla del sensor\"] if f == 4 else [])\n"),
    ("M2 MODIS: el veto de P1 no cuenta",
     "\"_fila_regla\": (2 if x[\"p1\"][\"estado\"] == \"VETADO\" else",
     "\"_fila_regla\": (2 if x[\"p1\"][\"estado\"] == \"NUNCA\" else"),
    ("M3 C-via en F26 acepta records sin la marca",
     "        out[\"estado\"] = \"OK\" if not sin else f\"ROJO: {len(sin)} records de la vía sin la marca\"",
     "        out[\"estado\"] = \"OK\""),
    ("M4 VIIRS 375: SIN SUSTRATO de P2 pasa como CUMPLE (VPR2-02)",
     "    elif p2v == \"SIN SUSTRATO\":\n        fila = 5",
     "    elif p2v == \"NUNCA\":\n        fila = 5"),
    ("M5 C-K sin tope de excepciones (R-15)",
     "TOPE_EXCEPCIONES_CK = 3 ", "TOPE_EXCEPCIONES_CK = 30 "),
    ("M6 N-3 deshecho",
     "    return (\"SNPP\" in (f.get(\"sensor\") or \"\") and f[\"dt\"][:10] < HITO_N3",
     "    return (False and f[\"dt\"][:10] < HITO_N3"),
    ("M7 decide la unión con el OCR y no la tabla sola (§4.1)",
     "canales = {\"tabla\": [r for r in filas_ref_union if r[\"source\"] == \"CONS\"]",
     "canales = {\"tabla\": [r for r in filas_ref_union]"),
    ("M8 Tupungatito antes del 2026-02-23",
     "(vol == TUPUNGATITO and (t == \"R25\" or dia < INICIO_TUPUNGATITO))",
     "(vol == TUPUNGATITO and t == \"R25\")"),
    ("M9 V750-A sin sello no limita el techo (R-12)",
     "    elif p2[\"estado\"] == \"BLOQUEA\" or not sellado:",
     "    elif p2[\"estado\"] == \"BLOQUEA\":"),
    ("M10 el nulo del lector no exige el contador",
     "    ok3 = despues - antes == N_INYECTADOS", "    ok3 = True"),
    ("M11 cercano y radiante distintos no van a Nicolás (R-13)",
     "        extra[\"cercano_y_radiante_difieren\"] = rad[\"_fila_regla\"] != regla[\"_fila_regla\"]",
     "        extra[\"cercano_y_radiante_difieren\"] = False"),
    ("M12 la caja de VIIRS 750 no se comprueba (L2)",
     "                                      {\"estado\": \"OK\" if not malas else f\"ROJO: {len(malas)} records con otra caja\",",
     "                                      {\"estado\": \"OK\","),
    ("CONTROL de caída: NameError en regla_modis (tiene que salir CAE)",
     "    F4 = R.F4\n    x = {\"p1\": F4.p1(filas, b)", "    F4 = R.F4\n    x = {\"p1\": F4_NO_EXISTE.p1(filas, b)"),
]


def correr(nombre, viejo, nuevo):
    src = ORIGINAL.read_text(encoding="utf-8")
    if src.count(viejo) != 1:
        return "NO APLICA (el texto a mutar aparece %d veces)" % src.count(viejo), ""
    mut = AQUI / f"_mut_leer_retro_{os.getpid()}.py"
    fd, nombre_xml = tempfile.mkstemp(suffix=".xml")
    os.close(fd)                    # en Windows el descriptor abierto impide borrar el archivo despues
    xml = Path(nombre_xml)
    try:
        mut.write_text(src.replace(viejo, nuevo), encoding="utf-8")
        env = dict(os.environ, LEER_RETRO_MODULO=str(mut), PYTHONDONTWRITEBYTECODE="1")
        subprocess.run([sys.executable, "-m", "pytest", str(BATERIA), "-q", "-p", "no:cacheprovider",
                        f"--junitxml={xml}"], cwd=RAIZ, env=env, capture_output=True, text=True, timeout=3600)
        raiz = ET.parse(xml).getroot()
        fallas = [(c.get("name"), e.tag, e.get("message", "")[:120]) for c in raiz.iter("testcase")
                  for e in c if e.tag in ("failure", "error")]
        por_asercion = [x for x in fallas if x[1] == "failure" and x[2].startswith(("AssertionError", "assert"))]
        if por_asercion:
            return "ATRAPADA", ", ".join(x[0] for x in por_asercion)
        if fallas:
            return "CAE", ", ".join(f"{x[0]}:{x[2][:40]}" for x in fallas[:3])
        return "SOBREVIVE", ""
    finally:
        mut.unlink(missing_ok=True)
        xml.unlink(missing_ok=True)


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001
        pass
    solo = sys.argv[sys.argv.index("--solo") + 1] if "--solo" in sys.argv else None
    cuenta = {}
    for nombre, viejo, nuevo in MUTACIONES:
        if solo and not nombre.startswith(solo):
            continue
        estado, detalle = correr(nombre, viejo, nuevo)
        cuenta[estado] = cuenta.get(estado, 0) + 1
        print(f"{nombre}: {estado} | {detalle}", flush=True)
    reales = [m for m in MUTACIONES if not m[0].startswith("CONTROL") and (not solo or m[0].startswith(solo))]
    print("resumen:", cuenta, "| mutaciones reales:", len(reales), "| control de caida: 1")


if __name__ == "__main__":
    main()
