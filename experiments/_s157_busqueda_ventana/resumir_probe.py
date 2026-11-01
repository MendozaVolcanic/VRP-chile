"""S157: tiempos y consultas a CMR de un intento del probe tag contra rama (probe-s157-busqueda-ventana.yml).

Lee <dir>/probe-s157-<codigo>-<volcan>/logs/: tiempos.txt (segundos medidos por el job) y los logs por brazo, donde
cuenta las consultas a CMR de cada lado: en el tag, una por SEARCH_START (L1B) y otra por cada busqueda de
geolocalizacion (sin marcador: se cuenta por cada linea "kept N of M" con N > 0, que es cuando el codigo la hace);
en la rama, las SEARCH_VENTANA mas las consultas por dia que quedaron (SEARCH_START de dias fuera de la ventana o
con la ventana apagada no se distinguen en el log: se cuentan aparte las SEARCH_START, que en la rama marcan cada
plataforma y dia aunque la respuesta salga de la cache). Tambien cuenta las fallas de busqueda.

Uso: python experiments/_s157_busqueda_ventana/resumir_probe.py DIR_DEL_INTENTO
"""
from __future__ import annotations

import re
import sys
from pathlib import Path


def resumir(d: Path) -> list[dict]:
    filas = []
    for job in sorted(d.glob("probe-s157-*")):
        m = re.match(r"probe-s157-(tag|rama)-(.+)$", job.name)
        if not m:
            continue
        tiempos = (job / "logs" / "tiempos.txt").read_text(encoding="utf-8") if (job / "logs" / "tiempos.txt").exists() else ""
        total = re.search(r"total \S+ \S+ (\d+) s", tiempos)
        cuenta = {"ventana": 0, "ventana_err": 0, "l1b_por_dia": 0, "geo_por_dia": 0, "skip": 0, "timeout": 0,
                  "warn": 0}
        for lg in sorted((job / "logs").glob("*.log")):
            for linea in lg.read_text(encoding="utf-8", errors="replace").splitlines():
                if "SEARCH_VENTANA [" in linea:
                    cuenta["ventana"] += 1
                elif "SEARCH_VENTANA_ERR" in linea:
                    cuenta["ventana_err"] += 1
                elif "SEARCH_START " in linea:
                    cuenta["l1b_por_dia"] += 1
                elif "SEARCH_SKIP" in linea:
                    cuenta["skip"] += 1
                elif "SEARCH_CMR_TIMEOUT" in linea:
                    cuenta["timeout"] += 1
                k = re.search(r"kept (\d+) of \d+ granules", linea)
                if k and int(k.group(1)) > 0:
                    cuenta["geo_por_dia"] += 1
                if "WARN: Failed to fetch" in linea:
                    cuenta["warn"] += 1
        filas.append({"codigo": m.group(1), "volcan": m.group(2), "segundos": int(total.group(1)) if total else None,
                      **cuenta})
    return filas


def main() -> int:
    filas = resumir(Path(sys.argv[1]))
    print("| codigo | volcan | segundos | consultas de ventana | SEARCH_START (marca por dia y plataforma) | "
          "busquedas geo por dia | SEARCH_SKIP | SEARCH_CMR_TIMEOUT | WARN Failed |")
    print("|---|---|---:|---:|---:|---:|---:|---:|---:|")
    for f in filas:
        print(f"| {f['codigo']} | {f['volcan']} | {f['segundos']} | {f['ventana']} (+{f['ventana_err']} fallidas) | "
              f"{f['l1b_por_dia']} | {f['geo_por_dia']} | {f['skip']} | {f['timeout']} | {f['warn']} |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
