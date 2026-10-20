"""S157: compara los records que produjo el codigo del tag con los que produjo la rama (busqueda por ventana).

POR QUE. El criterio A2 del plan: mismo volcan y misma ventana tienen que dar los MISMOS records. Clave
(datetime_utc, sensor), como pipeline/store.py. Se ignoran solo las marcas de escritura y de version del codigo:
`processed_utc` (hora de escritura) y `regimen.codigo_sha` / `regimen.origen` (sha del checkout, distinto por
construccion entre tag y rama). Todo lo demas, incluidos los floats, se compara exacto.

Uso:
  python experiments/_s157_busqueda_ventana/comparar_records.py DIR_TAG DIR_RAMA [--salida x.json]
Cada DIR trae <perfil>/<volcan>.json (la salida de probe-s157-busqueda-ventana.yml). Sale con 1 si hay diferencias.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

IGNORAR = {("processed_utc",), ("regimen", "codigo_sha"), ("regimen", "origen")}


def _aplanar(x, pref=()):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from _aplanar(v, pref + (k,))
    else:
        yield pref, x


def diferencias(a: dict, b: dict) -> list:
    fa = {k: v for k, v in _aplanar(a) if k not in IGNORAR}
    fb = {k: v for k, v in _aplanar(b) if k not in IGNORAR}
    return sorted(".".join(map(str, k)) for k in set(fa) | set(fb) if fa.get(k, "<falta>") != fb.get(k, "<falta>"))


def comparar(dir_a, dir_b) -> dict:
    dir_a, dir_b = Path(dir_a), Path(dir_b)
    res = {"archivos": {}, "records": 0, "iguales": 0, "solo_tag": 0, "solo_rama": 0, "distintos": 0}
    rutas = sorted({p.relative_to(dir_a) for p in dir_a.glob("*/*.json")} |
                   {p.relative_to(dir_b) for p in dir_b.glob("*/*.json")})
    for rel in rutas:
        pa, pb = dir_a / rel, dir_b / rel
        ra = {(r.get("datetime_utc"), r.get("sensor")): r
              for r in (json.loads(pa.read_text(encoding="utf-8"))["records"] if pa.exists() else [])}
        rb = {(r.get("datetime_utc"), r.get("sensor")): r
              for r in (json.loads(pb.read_text(encoding="utf-8"))["records"] if pb.exists() else [])}
        det = {"records_tag": len(ra), "records_rama": len(rb), "solo_tag": sorted(map(list, set(ra) - set(rb))),
               "solo_rama": sorted(map(list, set(rb) - set(ra))), "distintos": []}
        for k in sorted(set(ra) & set(rb)):
            d = diferencias(ra[k], rb[k])
            if d:
                det["distintos"].append({"clave": list(k), "campos": d[:30]})
            else:
                res["iguales"] += 1
        res["records"] += len(set(ra) | set(rb))
        res["solo_tag"] += len(det["solo_tag"])
        res["solo_rama"] += len(det["solo_rama"])
        res["distintos"] += len(det["distintos"])
        res["archivos"][str(rel).replace("\\", "/")] = det
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dir_tag")
    ap.add_argument("dir_rama")
    ap.add_argument("--salida", default=None)
    a = ap.parse_args()
    res = comparar(a.dir_tag, a.dir_rama)
    for rel, det in res["archivos"].items():
        print(f"{rel}: tag {det['records_tag']}, rama {det['records_rama']}, solo tag {len(det['solo_tag'])}, "
              f"solo rama {len(det['solo_rama'])}, distintos {len(det['distintos'])}")
    print(f"TOTAL: {res['records']} records, {res['iguales']} iguales, {res['distintos']} distintos, "
          f"{res['solo_tag']} solo en el tag, {res['solo_rama']} solo en la rama")
    if a.salida:
        Path(a.salida).write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    return 0 if (res["distintos"] + res["solo_tag"] + res["solo_rama"]) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
