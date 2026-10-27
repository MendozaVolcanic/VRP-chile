# -*- coding: utf-8 -*-
"""S165 (V165-03): mutaciones sobre el registro de la pasada «sin dato», con control de caída (patrón de
experiments/_s165_mxd03_flag/mutaciones.py).

POR QUÉ. Una prueba verde no dice que vigile algo: hay que romper el código a propósito y ver que alguna prueba lo
note. Una mutación que hace CAER una prueba con una excepción no cuenta como atrapada (S152, S156):
  atrapada  al menos una prueba falla por una aserción (AssertionError);
  caida     sólo fallan pruebas por excepciones que no son aserciones;
  viva      todo pasa.
Controles del instrumento: (a) sin mutación todo pasa; (b) una mutación que sólo levanta una excepción sale «caida»,
no «atrapada» (el arnés en subproceso levanta RuntimeError, no assert, cuando el subproceso muere).

Uso (árbol quieto, nada más corriendo sobre el repo, A112):
    python experiments/_s165_v165_03/mutaciones.py > experiments/_s165_v165_03/mutaciones_salida.txt
"""
from __future__ import annotations

import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PM = "pipeline/process_modis.py"
FE = "pipeline/fetch.py"
RP = "scripts/run_pipeline.py"
PRUEBAS = ["tests/test_crater_sin_dato_incidencia_s165.py", "tests/test_cobertura_incidencias_s159.py",
           "tests/test_guard_mxd03_flags_s165.py"]

_ANOTAR = ('        fetch.registrar_incidencia("crater_sin_dato", volcano["name"], date.strftime("%Y-%m-%d"), platform, '
           'motivo)')
_AVISO = ('        if al_sin_dato is not None:\n'
          '            al_sin_dato(f"cráter sin posición en el gránulo (borde o relleno del MxD03): {hdf_path.name}")\n')
_JUICIO = "    if sin_dato_de_geolocalizacion(lat, lon, _ancla_lat, _ancla_lon, geo_fuente):\n"

# (nombre, archivo, texto original, texto mutado, esperado)
MUTACIONES = [
    ("control_sin_mutacion", None, None, None, "viva"),
    ("control_caida", RP, '    import json\n    from collections import defaultdict\n    plataformas = plataformas or {}',
     '    raise RuntimeError("control de caida")\n    import json\n    from collections import defaultdict\n'
     '    plataformas = plataformas or {}', "caida"),
    # el tipo
    ("tipo_cuenta_en_estricto", FE, '                    "crater_sin_dato": False}',
     '                    "crater_sin_dato": True}', "atrapada"),
    ("tipo_borrado", FE, ', "dia_parcial": True,\n                    "crater_sin_dato": False}',
     ', "dia_parcial": True}', "atrapada"),
    # calculate_vrp
    ("aviso_no_se_llama", PM, _AVISO, "", "atrapada"),
    ("aviso_en_toda_pasada", PM, _JUICIO,
     '    if al_sin_dato is not None:\n        al_sin_dato("x")\n' + _JUICIO, "atrapada"),
    ("aviso_sin_granulo", PM, ": {hdf_path.name}\")\n", "\")\n", "atrapada"),
    # run_pipeline
    ("run_pipeline_no_pasa_aviso", RP, "al_sin_dato=_crater_sin_dato(volcano, date, platform),  # S165 (V165-03)",
     "al_sin_dato=None,", "atrapada"),
    ("anota_otro_tipo", RP, _ANOTAR, _ANOTAR.replace('"crater_sin_dato"', '"sin_geolocalizacion"'), "atrapada"),
    ("anota_sin_plataforma", RP, _ANOTAR, _ANOTAR.replace(", platform, motivo)", ", None, motivo)"), "atrapada"),
    ("anota_otro_volcan", RP, _ANOTAR, _ANOTAR.replace('volcano["name"]', '"?"'), "atrapada"),
    ("titulo_borrado", RP,
     ',\n               "crater_sin_dato": "cráter sin posición en el gránulo MODIS (sin dato, no se escribió record)"}',
     "}", "atrapada"),
]


def correr(nombre):
    xml = REPO / f"experiments/_s165_v165_03/_junit_{nombre}.xml"
    env = dict(os.environ, PYTHONIOENCODING="utf-8", VRP_PROFILE="mirova_equivalent")
    subprocess.run([sys.executable, "-m", "pytest", *PRUEBAS, "-q", "-p", "no:cacheprovider", f"--junitxml={xml}"],
                   cwd=REPO, env=env, capture_output=True, text=True, encoding="utf-8")
    raiz = ET.parse(xml).getroot()
    xml.unlink()
    aserciones, excepciones = [], []
    for caso in raiz.iter("testcase"):
        for f in list(caso.findall("failure")) + list(caso.findall("error")):
            msg = (f.get("message") or "")
            quien = f"{caso.get('name')}: {msg[:110]!r}"
            (aserciones if msg.startswith(("AssertionError", "assert")) else excepciones).append(quien)
    if aserciones:
        return "atrapada", aserciones, excepciones
    return ("caida" if excepciones else "viva"), aserciones, excepciones


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    originales = {a: (REPO / a).read_bytes() for a in (PM, FE, RP)}
    resumen = []
    try:
        for nombre, arch, a, b, esperado in MUTACIONES:
            if arch is not None:
                # con core.autocrlf=true el checkout trae CRLF; se muta sobre LF y se vuelve al final original (V164-03)
                s = originales[arch].decode("utf-8")
                crlf = "\r\n" in s
                s = s.replace("\r\n", "\n")
                assert s.count(a) == 1, f"{nombre}: el texto original aparece {s.count(a)} veces"
                s = s.replace(a, b)
                (REPO / arch).write_bytes((s.replace("\n", "\r\n") if crlf else s).encode("utf-8"))
            try:
                clase, asc, exc = correr(nombre)
            finally:
                for k, v in originales.items():
                    (REPO / k).write_bytes(v)
            ok = clase == esperado
            resumen.append((nombre, esperado, clase, ok))
            print(f"{nombre:30s} esperado={esperado:11s} resultado={clase:9s} {'OK' if ok else 'NO'}", flush=True)
            for q in (asc[:2] + exc[:2]):
                print("    ", q, flush=True)
    finally:
        for k, v in originales.items():
            (REPO / k).write_bytes(v)
    reales = [r for r in resumen if r[1] == "atrapada"]
    print(f"\nmutaciones reales atrapadas por aserción: {sum(r[2] == 'atrapada' for r in reales)} de {len(reales)}")
    print(f"controles: sin mutación {resumen[0][2]}, caída {resumen[1][2]}")
    print("todo como se esperaba" if all(r[3] for r in resumen) else "HAY DIFERENCIAS CON LO ESPERADO")


if __name__ == "__main__":
    main()
