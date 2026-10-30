# -*- coding: utf-8 -*-
"""S162 V750-B, R4: controles del día que el analizador sellado no hace (auditoría de patrones S169, f1).

POR QUÉ. El texto sellado de V750-B es más estricto que su código en tres lugares, y en vez de tocar lo sellado se
controlan antes:
  datos    (P1-04) la fecha máxima de los records VIIRS 750 de `--data` tiene que llegar al `--hasta`: con datos
           atrasados el generador arma una lista más corta y no avisa (ensayo del 2026-10-30: la rama llegaba al 10-18).
  lectura  (VF1-01) la ruta de `--censo-art` existe y trae resultados: una ruta errada imprime «{} FALLA», igual que un
           censo distinto. (VF1-03) cada resultado del run calza con el objetivo de su id en volcán y hora: el
           analizador empareja sólo por id. (P1-05) deja un manifiesto con los sha256 de todo lo que entra a la
           lectura y de los argumentos, en un archivo nuevo (se niega a pisar uno existente).
Salida: 0 si todo bien; 1 si un control falla (no se genera o no se lee); 2 si el manifiesto ya existe.
Uso:
  python control_previo_v750b.py datos --data <data/mirova_equivalent de main del día> --hasta 2026-11-02
  python control_previo_v750b.py lectura --art <carpetas> --objetivos <objetivos_v750b.json> --censo-art <carpeta>
      --manifiesto <archivo nuevo> [--insumo <archivo> ...] [--argumentos "<línea de comando del lector>"]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path


def sha(ruta):
    return hashlib.sha256(Path(ruta).read_bytes()).hexdigest()


def datos(a):
    maxima, n = None, 0
    for f in sorted(Path(a.data).glob("*.json")):
        d = json.loads(f.read_text(encoding="utf-8"))
        rs = d.get("records", d) if isinstance(d, dict) else d
        for r in rs:
            if isinstance(r, dict) and str(r.get("sensor", "")).endswith("_750") and r.get("datetime_utc"):
                n += 1
                maxima = max(maxima or r["datetime_utc"], r["datetime_utc"])
    print(f"records VIIRS 750 en {a.data}: {n}; fecha máxima {maxima}; --hasta {a.hasta}")
    if maxima is None or maxima[:10] < a.hasta:
        print("FALLA: los datos no llegan al --hasta; no se genera (P1-04)")
        return 1
    print("OK")
    return 0


def lectura(a):
    malos = 0
    censo = sorted(Path(a.censo_art).rglob("resultados_*.json")) if Path(a.censo_art).is_dir() else []
    print(f"censo: {a.censo_art} | existe {Path(a.censo_art).is_dir()} | archivos de resultados {len(censo)}")
    if not censo:
        print("FALLA: la ruta del censo no existe o no trae resultados (VF1-01); corregir la ruta antes de leer")
        malos += 1
    obj = {o["id"]: o for o in json.loads(Path(a.objetivos).read_text(encoding="utf-8"))}
    arts = [f for d in a.art for f in sorted(Path(d).rglob("resultados_*.json"))]
    n, sin_obj, distintos = 0, [], []
    for f in arts:
        for r in json.loads(f.read_text(encoding="utf-8")):
            n += 1
            o = obj.get(r.get("id"))
            if o is None:
                sin_obj.append(r.get("id"))
            elif (r.get("volcan"), r.get("hora_utc")) != (o["volcan"], o["hora_utc"]):
                distintos.append((r.get("id"), r.get("volcan"), r.get("hora_utc"), o["volcan"], o["hora_utc"]))
    print(f"resultados: {len(arts)} archivos, {n} filas; sin objetivo {len(sin_obj)}; volcán u hora distintos "
          f"{len(distintos)} {distintos[:5]}")
    if not arts or sin_obj or distintos:
        print("FALLA: los resultados no calzan con estos objetivos (VF1-03); no se lee")
        malos += 1
    man = Path(a.manifiesto)
    if man.exists():
        print(f"el manifiesto {man} ya existe: no se pisa (P1-05)")
        return 2
    man.parent.mkdir(parents=True, exist_ok=True)
    m = {"hecho_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "argumentos": a.argumentos,
         "objetivos": {str(a.objetivos): sha(a.objetivos)}, "resultados": {str(f): sha(f) for f in arts},
         "censo_art": {"ruta": str(a.censo_art), "n": len(censo),
                       "sha256_de_la_lista": hashlib.sha256("\n".join(sha(f) for f in censo).encode()).hexdigest()},
         "insumos": {str(f): sha(f) for f in a.insumo}, "controles": "OK" if not malos else "FALLA"}
    with open(man, "x", encoding="utf-8") as fh:          # «x»: falla si alguien lo creó entre medio
        json.dump(m, fh, ensure_ascii=False, indent=1)
    print(f"manifiesto escrito: {man}")
    print("OK" if not malos else "FALLA")
    return 1 if malos else 0


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="modo", required=True)
    d = sub.add_parser("datos")
    d.add_argument("--data", required=True)
    d.add_argument("--hasta", required=True)
    le = sub.add_parser("lectura")
    le.add_argument("--art", required=True, nargs="+")
    le.add_argument("--objetivos", required=True)
    le.add_argument("--censo-art", required=True)
    le.add_argument("--manifiesto", required=True)
    le.add_argument("--insumo", nargs="*", default=[])
    le.add_argument("--argumentos", default="")
    a = ap.parse_args()
    return datos(a) if a.modo == "datos" else lectura(a)


if __name__ == "__main__":
    sys.exit(main())
