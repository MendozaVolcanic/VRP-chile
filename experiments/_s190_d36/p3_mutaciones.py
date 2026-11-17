# -*- coding: utf-8 -*-
# FICHA (SDA, CPLT 372): mutaciones de medición (D36 punto 3). Muta el código sólo en este worktree y lo restaura.
"""D36 punto 3: ¿alguna prueba atrapa el corte de 5 km al centro (VIIRS 375 y MODIS), el mínimo de 100 píxeles y el
recorte de 45 km?

POR QUÉ: una decisión que ninguna prueba vigila puede cambiar sin que nadie lo note. Se rompe el código a propósito y
se mira si alguna prueba falla POR UNA ASERCIÓN (una que cae por excepción no comprobó nada: S152, S156). Instrumento
copiado de experiments/_s164_modis_codigo/mutaciones.py (clasificador y controles), con el conjunto de pruebas de hoy:
todo archivo de tests/ que importa pipeline.mirova_v750_codigo.
Controles: sin mutación tiene que salir «viva»; una mutación que sólo levanta una excepción tiene que salir «caida».
Uso (árbol quieto, A112): python experiments/_s190_d36/p3_mutaciones.py > experiments/_s190_d36/p3_mutaciones_salida.txt
"""
from __future__ import annotations

import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MOD = "pipeline/mirova_v750_codigo.py"
PRUEBAS = sorted(str(p.relative_to(REPO)).replace("\\", "/") for p in (REPO / "tests").glob("test_*.py")
                 if "mirova_v750_codigo" in p.read_text(encoding="utf-8", errors="ignore"))
# Fase 1 (D36_PRUEBAS=núcleo): los archivos que prueban la vía directamente; la suite de los 16 tarda 22 min por
# corrida. Fase 2: las mutaciones que quedan vivas en la fase 1, contra los 16 (D36_SOLO=nombre,nombre).
if os.environ.get("D36_PRUEBAS"):
    PRUEBAS = os.environ["D36_PRUEBAS"].split(",")

MUTACIONES = [
    ("control_sin_mutacion", None, None, "viva"),
    ("control_caida", '    """Distancia en km (R = 6371)',
     '    raise RuntimeError("control de caida")\n    """Distancia en km (R = 6371)', "caida"),
    ("modis_sin_corte_5km", '              "dist_max_centro_km": 5.0},', '              "dist_max_centro_km": None},', "?"),
    ("modis_corte_10km", '              "dist_max_centro_km": 5.0},', '              "dist_max_centro_km": 10.0},', "?"),
    ("modis_corte_2km", '              "dist_max_centro_km": 5.0},', '              "dist_max_centro_km": 2.0},', "?"),
    ("v375_sin_corte_5km", '"dist_max_centro_km": 5.0, "roi1_half_m"', '"dist_max_centro_km": None, "roi1_half_m"', "?"),
    ("v375_corte_10km", '"dist_max_centro_km": 5.0, "roi1_half_m"', '"dist_max_centro_km": 10.0, "roi1_half_m"', "?"),
    ("corte_5km_ignorado", 'if cfg["dist_max_centro_km"] is not None and dist[i0] > cfg["dist_max_centro_km"]:',
     'if False:', "?"),
    ("min_100_a_1", "    if sel.sum() < 100:\n", "    if sel.sum() < 1:\n", "?"),
    ("min_100_a_2000", "    if sel.sum() < 100:\n", "    if sel.sum() < 2000:\n", "?"),
    ("recorte_45_a_30", "RADIO_RECORTE_KM = 45.0 ", "RADIO_RECORTE_KM = 30.0 ", "?"),
    ("recorte_45_a_60", "RADIO_RECORTE_KM = 45.0 ", "RADIO_RECORTE_KM = 60.0 ", "?"),
    ("recorte_seleccion_45_a_20", "    sel = np.isfinite(dist) & (dist < RADIO_RECORTE_KM)\n",
     "    sel = np.isfinite(dist) & (dist < 20.0)\n", "?"),
]


def correr(nombre):
    xml = REPO / f"experiments/_s190_d36/_junit_{nombre}.xml"
    # Temporales en D: (regla de disco de S190, 2026-11-17): C: no recibe nada de la batería.
    tmp = Path(os.environ.get("D36_TMP", "D:/vrp-trabajo/temporales/s190_d36/pytest")) / nombre
    tmp.parent.mkdir(parents=True, exist_ok=True)
    env = dict(os.environ, PYTHONIOENCODING="utf-8", VRP_PROFILE="mirova_equivalent", TEMP=str(tmp.parent),
               TMP=str(tmp.parent))
    turno = os.environ.get("D36_TURNO")   # fase 2: la cola global de S190 (una suite a la vez en el computador)
    if turno:
        salida = REPO / f"experiments/_s190_d36/_turno_{nombre}.txt"
        subprocess.run(["bash", turno, str(REPO), str(salida), *PRUEBAS, f"--junitxml={xml}"], env=env,
                       capture_output=True, text=True, encoding="utf-8")
        salida.unlink(missing_ok=True)
    else:
        subprocess.run([sys.executable, "-m", "pytest", *PRUEBAS, "-q", "-p", "no:cacheprovider",
                        f"--junitxml={xml}", f"--basetemp={tmp}"], cwd=REPO, env=env, capture_output=True,
                       text=True, encoding="utf-8")
    raiz = ET.parse(xml).getroot()
    xml.unlink()
    aserciones, excepciones, n = [], [], 0
    for caso in raiz.iter("testcase"):
        n += 1
        for f in list(caso.findall("failure")) + list(caso.findall("error")):
            msg = (f.get("message") or "")
            quien = f"{caso.get('classname')}::{caso.get('name')}: {msg[:100]!r}"
            (aserciones if msg.startswith(("AssertionError", "assert")) else excepciones).append(quien)
    if aserciones:
        return "atrapada", aserciones, excepciones, n
    return ("caida" if excepciones else "viva"), aserciones, excepciones, n


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    print(f"pruebas ({len(PRUEBAS)}): {', '.join(PRUEBAS)}\n", flush=True)
    original = (REPO / MOD).read_bytes()
    try:
        solo = set(filter(None, os.environ.get("D36_SOLO", "").split(",")))
        for nombre, a, b, esperado in MUTACIONES:
            if solo and nombre not in solo and (not nombre.startswith("control") or os.environ.get("D36_SIN_CONTROLES")):
                continue
            if a is not None:
                s = original.decode("utf-8")
                crlf = "\r\n" in s
                s = s.replace("\r\n", "\n")
                assert s.count(a) == 1, f"{nombre}: el texto original aparece {s.count(a)} veces"
                s = s.replace(a, b)
                (REPO / MOD).write_bytes((s.replace("\n", "\r\n") if crlf else s).encode("utf-8"))
            try:
                clase, asc, exc, n = correr(nombre)
            finally:
                (REPO / MOD).write_bytes(original)
            marca = "" if esperado == "?" else (" OK" if clase == esperado else " NO (control)")
            print(f"{nombre:26s} resultado={clase:9s} casos={n}{marca}", flush=True)
            for q in (asc[:3] + exc[:2]):
                print("    ", q, flush=True)
    finally:
        (REPO / MOD).write_bytes(original)


if __name__ == "__main__":
    main()
