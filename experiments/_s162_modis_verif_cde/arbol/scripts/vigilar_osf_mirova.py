# -*- coding: utf-8 -*-
"""Vigila los proyectos OSF del grupo MIROVA y avisa cuando publican algo nuevo (S158).

POR QUÉ: el 2026-07-24 MIROVA publicó en OSF zm62w su código operacional de VIIRS 750 y el proyecto se enteró tres
meses después, por casualidad (docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md). MIROVA no tiene canal de anuncios: el único
registro con fecha es el historial de actividad de cada proyecto OSF. Este script lo compara contra una línea base
versionada (scripts/osf_mirova_linea_base.json) y contra la lista de proyectos públicos de los autores.

Códigos de salida (lección S156: un vigilante que no puede leer su fuente no queda en verde):
  0  sin novedades;
  1  hay novedades (actividad posterior a la línea base, o un proyecto público nuevo de algún autor);
  2  CIEGO: no se pudo leer OSF (red, API, formato). Se avisa igual que una novedad.
No escribe en el repo: la línea base se actualiza a mano, en un PR, después de mirar la novedad
(`python scripts/vigilar_osf_mirova.py --generar-linea-base`).
"""
import json
import os
import sys
import time
import urllib.request

API = "https://api.osf.io/v2"
LINEA_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "osf_mirova_linea_base.json")
# Autores de zm62w (Coppola, Laiolo, Campus, Massimetti, Aveni), ids de OSF leídos el 2026-10-21.
AUTORES = ["ws5y3", "zvdyh", "safnj", "qj8bz", "rm7t4"]


def _get(url, intentos=4):
    err = None
    for i in range(intentos):
        try:
            with urllib.request.urlopen(url, timeout=60) as r:
                return json.load(r)
        except Exception as e:  # noqa: BLE001 - cualquier falla de lectura deja al vigilante ciego
            err = e
            time.sleep(2 + 2 * i)
    raise RuntimeError(f"no se pudo leer {url}: {err}")


def _todas(url, get=_get):
    while url:
        d = get(url)
        yield from d["data"]
        url = d["links"].get("next")


def leer_estado(get=_get):
    """Estado actual: proyectos públicos de los autores y fecha del último registro de actividad de cada uno."""
    nodos = {}
    for uid in AUTORES:
        for n in _todas(f"{API}/users/{uid}/nodes/?page%5Bsize%5D=100", get):
            a = n["attributes"]
            if a.get("public"):
                nodos[n["id"]] = {"titulo": a.get("title", ""), "ultimo_log": None}
    if not nodos:
        raise RuntimeError("OSF no devolvió ningún proyecto público de los autores: formato cambiado o API caída")
    for nid in nodos:
        logs = get(f"{API}/nodes/{nid}/logs/?page%5Bsize%5D=1")["data"]
        if logs:
            nodos[nid]["ultimo_log"] = logs[0]["attributes"]["date"]
            nodos[nid]["ultima_accion"] = logs[0]["attributes"]["action"]
    return {"nodos": nodos}


def comparar(base, actual):
    """Lista de novedades en lenguaje llano. Vacía si no hay nada nuevo."""
    nov = []
    bn, an = base.get("nodos", {}), actual.get("nodos", {})
    for nid, a in sorted(an.items()):
        b = bn.get(nid)
        if b is None:
            nov.append(f"proyecto OSF nuevo: {nid} «{a.get('titulo', '')}» (https://osf.io/{nid}/)")
        elif (a.get("ultimo_log") or "") > (b.get("ultimo_log") or ""):
            nov.append(f"actividad nueva en {nid} «{a.get('titulo', '')}»: {a.get('ultima_accion')} el "
                       f"{a.get('ultimo_log')} (antes {b.get('ultimo_log')}); historial: {API}/nodes/{nid}/logs/")
    for nid in sorted(set(bn) - set(an)):
        nov.append(f"proyecto que ya no aparece público: {nid} «{bn[nid].get('titulo', '')}»")
    return nov


def main(argv, get=_get, linea_base=LINEA_BASE):
    if "--generar-linea-base" in argv:
        estado = leer_estado(get)
        with open(linea_base, "w", encoding="utf-8") as f:
            json.dump(estado, f, ensure_ascii=False, indent=1, sort_keys=True)
        print(f"línea base escrita: {len(estado['nodos'])} proyectos")
        return 0
    try:
        base = json.load(open(linea_base, encoding="utf-8"))
        actual = leer_estado(get)
    except Exception as e:  # noqa: BLE001
        print(f"CIEGO: {e}")
        return 2
    nov = comparar(base, actual)
    if not nov:
        print(f"sin novedades en {len(actual['nodos'])} proyectos OSF del grupo MIROVA")
        return 0
    print("NOVEDADES en OSF del grupo MIROVA:")
    for n in nov:
        print(f"- {n}")
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
