"""S157: atribucion del tiempo de un job de reproceso entre busqueda, descarga y proceso.

POR QUE. Un trozo de 37 dias de Nevados de Chillan tardo 151 min entre marcadores [diag] de
pipeline/fetch.py y ~51 min de eso caian entre el fin de una busqueda (SEARCH_DONE) y el
marcador siguiente, sin atribuir. Leyendo fetch.fetch_for_volcano: despues de SEARCH_DONE vienen
el filtro nocturno (python puro, sobre <= 5 granulos) y la busqueda del producto de
GEOLOCALIZACION, que va a CMR igual que la del L1B pero NO tiene marcador. Este script lo mide.

COMO ATRIBUYE. Cada intervalo entre dos marcadores consecutivos se etiqueta por el par
(marcador anterior, marcador siguiente) y por las lineas impresas entre ellos:
  AUTH_START -> AUTH_OK                    autenticacion
  SEARCH_START -> SEARCH_DONE              busqueda L1B (CMR)
  SEARCH_START -> SEARCH_CMR_TIMEOUT       busqueda L1B que fallo (CMR)
  SEARCH_DONE -> DOWNLOAD_START            filtro nocturno + busqueda GEO (CMR)
  SEARCH_DONE -> SEARCH_CMR_TIMEOUT        filtro nocturno + busqueda GEO que fallo (CMR)
  SEARCH_DONE -> otro, sin busqueda geo    control: n_l1b=0 o el filtro nocturno dejo 0
  DOWNLOAD_START -> DOWNLOAD_DONE          descarga
  * -> AUTH_START del dia siguiente / fin  procesamiento del dia (lo que imprime el proceso
                                           sale sin flush y aparece con la hora del marcador
                                           siguiente, por eso no se puede partir mas fino)
El control: los intervalos SEARCH_DONE -> siguiente en que NO hubo busqueda geo (n_l1b=0 o
"kept 0 of N") deben valer casi cero. Si valen casi cero, el tiempo de los otros es la busqueda.

Uso:
  python experiments/_s157_busqueda_ventana/medir_tiempos.py LOG [LOG ...] > salida.md
  python experiments/_s157_busqueda_ventana/medir_tiempos.py --compacto LOG [LOG ...]  (una fila por job)
Los logs de los jobs viven en experiments/_s157_busqueda_ventana/logs/ (bajados con
gh api repos/MendozaVolcanic/VRP-chile/actions/jobs/<id>/logs).
"""
from __future__ import annotations

import re
import statistics
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

TS = re.compile(r"^﻿?(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+)Z (.*)$")
DIAG = re.compile(r"\[diag [0-9:]+Z\] (\w+)(.*)$")
KEPT = re.compile(r"(\S+): kept (\d+) of (\d+) granules")
NL1B = re.compile(r"n_l1b=(\d+)")


def _ts(s: str) -> datetime:
    return datetime.strptime(s[:26], "%Y-%m-%dT%H:%M:%S.%f")


def leer(path: Path):
    """Devuelve (eventos, fin) con eventos = [(t, marcador, resto, lineas_entre)]."""
    eventos = []
    pend: list[str] = []
    fin = None
    for linea in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = TS.match(linea)
        if not m:
            continue
        t, txt = _ts(m.group(1)), m.group(2)
        d = DIAG.search(txt)
        if d:
            eventos.append([t, d.group(1), d.group(2), []])
            continue
        if eventos:
            eventos[-1][3].append(txt)
        if txt.strip() == "Done.":
            fin = t
    return eventos, fin


def atribuir(eventos, fin):
    cat = defaultdict(list)
    for i, (t, mk, resto, entre) in enumerate(eventos):
        if i + 1 < len(eventos):
            t2, mk2 = eventos[i + 1][0], eventos[i + 1][1]
        else:
            t2, mk2 = fin, "FIN"
        if t2 is None:
            continue
        dt = (t2 - t).total_seconds()
        if mk == "AUTH_START" and mk2 == "AUTH_OK":
            cat["autenticacion"].append(dt)
        elif mk == "SEARCH_START" and mk2 == "SEARCH_DONE":
            cat["busqueda L1B (CMR)"].append(dt)
        elif mk == "SEARCH_START" and mk2 == "SEARCH_CMR_TIMEOUT":
            cat["busqueda L1B fallida (CMR)"].append(dt)
        elif mk == "SEARCH_DONE":
            n = int(NL1B.search(resto).group(1)) if NL1B.search(resto) else None
            kept = None
            for x in entre:
                k = KEPT.search(x)
                if k:
                    kept = int(k.group(2))
            hubo_geo = bool(n) and (kept is None or kept > 0)
            if mk2 == "DOWNLOAD_START":
                cat["filtro nocturno + busqueda GEO (CMR)"].append(dt)
            elif mk2 == "SEARCH_CMR_TIMEOUT":
                cat["busqueda GEO fallida (CMR)"].append(dt)
            elif not hubo_geo and mk2 in ("SEARCH_START", "SEARCH_SKIP"):
                cat["CONTROL: tras SEARCH_DONE sin busqueda GEO"].append(dt)
            elif not hubo_geo and mk2 in ("AUTH_START", "FIN"):
                cat["procesamiento del dia"].append(dt)
            elif hubo_geo and mk2 in ("AUTH_START", "FIN"):
                cat["busqueda GEO sin descarga + procesamiento del dia"].append(dt)
            else:
                cat[f"otro SEARCH_DONE->{mk2} (geo={hubo_geo})"].append(dt)
        elif mk == "DOWNLOAD_START" and mk2 == "DOWNLOAD_DONE":
            cat["descarga"].append(dt)
        elif mk2 in ("AUTH_START", "FIN"):
            cat["procesamiento del dia"].append(dt)
        else:
            cat[f"entre marcadores {mk}->{mk2}"].append(dt)
    return cat


def compacto(paths):
    """Una fila por job: cuanto del job es espera a CMR, descarga y proceso."""
    print("| job | inicio (UTC) | dias | min | CMR min | CMR % | mediana busqueda (s) | descarga min | proceso min | fallas CMR |")
    print("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    filas = []
    for p in paths:
        p = Path(p)
        eventos, fin = leer(p)
        if not eventos:
            continue
        nombre = ""
        for linea in p.read_text(encoding="utf-8", errors="replace").splitlines()[:80]:
            if "Complete job name:" in linea:
                nombre = linea.split("Complete job name:")[1].strip()
        cat = atribuir(eventos, fin)
        span = ((fin or eventos[-1][0]) - eventos[0][0]).total_seconds() / 60
        cmr = sum(sum(v) for k, v in cat.items() if "CMR" in k) / 60
        busq = cat.get("busqueda L1B (CMR)", []) + cat.get("filtro nocturno + busqueda GEO (CMR)", [])
        med = statistics.median(busq) if busq else float("nan")
        fallas = sum(1 for e in eventos if e[1] == "SEARCH_CMR_TIMEOUT")
        fallas += sum(1 for e in eventos for x in e[3] if "WARN: Failed to fetch" in x)
        dias = sum(1 for e in eventos if e[1] == "AUTH_START")
        desc = sum(cat.get("descarga", [])) / 60
        proc = sum(sum(v) for k, v in cat.items() if "procesamiento" in k) / 60
        filas.append((cmr / span if span else 0))
        print(f"| {p.stem} {nombre} | {eventos[0][0]:%Y-%m-%d %H:%M} | {dias} | {span:.1f} | {cmr:.1f} | "
              f"{100*cmr/span:.0f} | {med:.1f} | {desc:.1f} | {proc:.1f} | {fallas} |")
    if filas:
        filas.sort()
        print()
        print(f"Jobs: {len(filas)}. Fraccion del job esperando a CMR: mediana "
              f"{100*statistics.median(filas):.0f} %, minimo {100*filas[0]:.0f} %, maximo {100*filas[-1]:.0f} %; "
              f"jobs con mas de 25 %: {sum(1 for f in filas if f > 0.25)}.")


def main(paths):
    total = defaultdict(list)
    print("# Atribucion del tiempo por job (salida de medir_tiempos.py)\n")
    for p in paths:
        p = Path(p)
        eventos, fin = leer(p)
        if not eventos:
            print(f"- {p.name}: sin marcadores\n")
            continue
        nombre = ""
        for linea in p.read_text(encoding="utf-8", errors="replace").splitlines()[:80]:
            if "Complete job name:" in linea:
                nombre = linea.split("Complete job name:")[1].strip()
        cat = atribuir(eventos, fin)
        span = ((fin or eventos[-1][0]) - eventos[0][0]).total_seconds() / 60
        n_busq = sum(1 for e in eventos if e[1] == "SEARCH_START")
        n_to = sum(1 for e in eventos if e[1] == "SEARCH_CMR_TIMEOUT")
        n_skip = sum(1 for e in eventos if e[1] == "SEARCH_SKIP")
        dias = sum(1 for e in eventos if e[1] == "AUTH_START")
        print(f"## {p.name}: {nombre}\n")
        print(f"Dias: {dias}. Del primer marcador al fin: {span:.1f} min. SEARCH_START: {n_busq}, "
              f"SEARCH_CMR_TIMEOUT: {n_to}, SEARCH_SKIP: {n_skip}.\n")
        print("| categoria | n | total (min) | mediana (s) | p90 (s) | % del job |")
        print("|---|---:|---:|---:|---:|---:|")
        for k in sorted(cat, key=lambda k: -sum(cat[k])):
            v = cat[k]
            p90 = sorted(v)[int(0.9 * (len(v) - 1))]
            print(f"| {k} | {len(v)} | {sum(v)/60:.1f} | {statistics.median(v):.1f} | {p90:.1f} | "
                  f"{100*sum(v)/60/span:.0f} |")
            total[k] += v
        cmr = sum(sum(v) for k, v in cat.items() if "CMR" in k) / 60
        print(f"\nTodo lo que espera a CMR (L1B + GEO, incluidas las fallidas): {cmr:.1f} min "
              f"({100*cmr/span:.0f} %).\n")
    print("## Los cuatro jobs juntos\n")
    print("| categoria | n | total (min) | mediana (s) |")
    print("|---|---:|---:|---:|")
    for k in sorted(total, key=lambda k: -sum(total[k])):
        v = total[k]
        print(f"| {k} | {len(v)} | {sum(v)/60:.1f} | {statistics.median(v):.1f} |")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if sys.argv[1:2] == ["--compacto"]:
        compacto(sys.argv[2:])
    else:
        main(sys.argv[1:])
