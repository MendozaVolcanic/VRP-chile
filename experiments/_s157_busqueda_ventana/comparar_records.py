"""S157: compara los records que produjo el codigo del tag con los que produjo la rama (busqueda por ventana).

POR QUE. El criterio A2 del plan: mismo volcan y misma ventana tienen que dar los MISMOS records. Clave
(datetime_utc, sensor), como pipeline/store.py. Se ignoran solo las marcas de escritura y de version del codigo:
`processed_utc` y `first_processed_utc` (hora de escritura) y `regimen.codigo_sha` / `regimen.origen` (sha del
checkout, distinto por construccion entre tag y rama).

Tres clases de diferencia, informadas aparte:
  - EXACTA: algun campo no numerico distinto, o un numero con diferencia relativa mayor que 1e-9.
  - SOLO REDONDEO: todos los campos distintos son floats con diferencia relativa <= 1e-9. Tag y rama corren en runners
    distintos, y la suma en punto flotante depende de la CPU (memoria S152 y S142: el argsort y los golden ya lo
    mostraron). No lo produce la busqueda: la busqueda solo decide QUE granulos entran.
  - SOLO EN UN LADO: la pasada falta en uno de los dos. Con --logs, se mira si el log de ese lado dice que la
    busqueda o la descarga de ese dia y plataforma fallo (SEARCH_SKIP, SEARCH_CMR_TIMEOUT, WARN: Failed); si lo dice,
    la falta queda EXPLICADA por un corte de NASA y no por el cambio.

Uso:
  python experiments/_s157_busqueda_ventana/comparar_records.py DIR_TAG DIR_RAMA [--logs] [--salida x.json]
Cada DIR trae <perfil>/<volcan>.json y logs/<perfil>_<volcan>.log (la salida de probe-s157-busqueda-ventana.yml).
Sale con 1 si hay diferencias EXACTAS o faltas sin explicar.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

IGNORAR = {("processed_utc",), ("first_processed_utc",), ("regimen", "codigo_sha"), ("regimen", "origen")}
TOL_REL = 1e-9


def _aplanar(x, pref=()):
    if isinstance(x, dict):
        for k, v in x.items():
            yield from _aplanar(v, pref + (k,))
    elif isinstance(x, list):
        yield pref + ("#len",), len(x)
        for i, v in enumerate(x):
            yield from _aplanar(v, pref + (i,))
    else:
        yield pref, x


def _igual(a, b) -> str:
    """'si', 'redondeo' o 'no'."""
    if a == b:
        return "si"
    if isinstance(a, float) and isinstance(b, float):
        if math.isnan(a) and math.isnan(b):
            return "si"
        if abs(a - b) <= TOL_REL * max(abs(a), abs(b)):
            return "redondeo"
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool):
        if abs(a - b) <= TOL_REL * max(abs(a), abs(b)):
            return "redondeo"
    return "no"


def diferencias(a: dict, b: dict) -> tuple[list, list]:
    fa = {k: v for k, v in _aplanar(a) if k not in IGNORAR}
    fb = {k: v for k, v in _aplanar(b) if k not in IGNORAR}
    exactas, redondeo = [], []
    for k in set(fa) | set(fb):
        nombre = ".".join(map(str, k))
        if k not in fa or k not in fb:
            exactas.append(nombre)
            continue
        e = _igual(fa[k], fb[k])
        if e == "no":
            exactas.append(nombre)
        elif e == "redondeo":
            redondeo.append(nombre)
    return sorted(exactas), sorted(redondeo)


def fallas_del_log(ruta: Path) -> set:
    """(fecha, plataforma) donde el log dice que la busqueda o la descarga fallo."""
    out, fecha, plataforma = set(), None, None
    if not ruta.exists():
        return out
    for linea in ruta.read_text(encoding="utf-8", errors="replace").splitlines():
        m = re.search(r">>> .* \| (\d{4}-\d{2}-\d{2})", linea)
        if m:
            fecha = m.group(1)
        m = re.search(r"SEARCH_START (\S+)", linea)
        if m:
            plataforma = m.group(1)
        m = re.search(r"WARN: Failed to fetch (\S+):", linea)
        if m and fecha:
            out.add((fecha, m.group(1)))
        if ("SEARCH_SKIP" in linea or "SEARCH_CMR_TIMEOUT" in linea or "DOWNLOAD_SKIP" in linea) and fecha and plataforma:
            out.add((fecha, plataforma))
    return out


def comparar(dir_a, dir_b, usar_logs: bool = False) -> dict:
    dir_a, dir_b = Path(dir_a), Path(dir_b)
    res = {"archivos": {}, "records": 0, "iguales": 0, "solo_redondeo": 0, "distintos": 0,
           "solo_tag": 0, "solo_rama": 0, "faltas_explicadas": 0, "faltas_sin_explicar": 0, "max_rel_redondeo": 0.0}
    # solo los stores de los brazos (<perfil>/<volcan>.json); logs/ trae la cobertura, que no es un store
    rutas = sorted({p.relative_to(dir_a) for p in dir_a.glob("*/*.json") if p.parent.name != "logs"} |
                   {p.relative_to(dir_b) for p in dir_b.glob("*/*.json") if p.parent.name != "logs"})
    for rel in rutas:
        pa, pb = dir_a / rel, dir_b / rel
        ra = {(r.get("datetime_utc"), r.get("sensor")): r
              for r in (json.loads(pa.read_text(encoding="utf-8"))["records"] if pa.exists() else [])}
        rb = {(r.get("datetime_utc"), r.get("sensor")): r
              for r in (json.loads(pb.read_text(encoding="utf-8"))["records"] if pb.exists() else [])}
        nombre_log = f"{rel.parent.name}_{rel.stem}.log"
        caidas = {"tag": fallas_del_log(dir_a / "logs" / nombre_log) if usar_logs else set(),
                  "rama": fallas_del_log(dir_b / "logs" / nombre_log) if usar_logs else set()}
        det = {"records_tag": len(ra), "records_rama": len(rb), "solo_tag": [], "solo_rama": [],
               "distintos": [], "solo_redondeo": 0}
        for lado, sobra, falta_en in (("solo_tag", set(ra) - set(rb), "rama"), ("solo_rama", set(rb) - set(ra), "tag")):
            for k in sorted(sobra):
                explicada = ((k[0] or "")[:10], k[1]) in caidas[falta_en]
                det[lado].append({"clave": list(k), "explicada_por_corte_en_" + falta_en: explicada})
                res["faltas_explicadas" if explicada else "faltas_sin_explicar"] += 1
        for k in sorted(set(ra) & set(rb)):
            exactas, redondeo = diferencias(ra[k], rb[k])
            if exactas:
                det["distintos"].append({"clave": list(k), "campos": exactas[:30]})
            elif redondeo:
                det["solo_redondeo"] += 1
                for c in redondeo:
                    va = dict(_aplanar(ra[k]))[tuple(int(x) if x.isdigit() else x for x in c.split("."))]
                    vb = dict(_aplanar(rb[k]))[tuple(int(x) if x.isdigit() else x for x in c.split("."))]
                    if va != vb:
                        res["max_rel_redondeo"] = max(res["max_rel_redondeo"],
                                                      abs(va - vb) / max(abs(va), abs(vb)))
            else:
                res["iguales"] += 1
        res["records"] += len(set(ra) | set(rb))
        res["solo_tag"] += len(det["solo_tag"])
        res["solo_rama"] += len(det["solo_rama"])
        res["distintos"] += len(det["distintos"])
        res["solo_redondeo"] += det["solo_redondeo"]
        res["archivos"][str(rel).replace("\\", "/")] = det
    return res


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("dir_tag")
    ap.add_argument("dir_rama")
    ap.add_argument("--logs", action="store_true", help="explicar las faltas con los logs de cada lado")
    ap.add_argument("--salida", default=None)
    a = ap.parse_args()
    res = comparar(a.dir_tag, a.dir_rama, usar_logs=a.logs)
    for rel, det in res["archivos"].items():
        print(f"{rel}: tag {det['records_tag']}, rama {det['records_rama']}, solo tag {len(det['solo_tag'])}, "
              f"solo rama {len(det['solo_rama'])}, distintos {len(det['distintos'])}, "
              f"solo redondeo {det['solo_redondeo']}")
    print(f"TOTAL: {res['records']} records; en los dos lados: {res['iguales']} iguales, {res['solo_redondeo']} solo "
          f"redondeo (max rel {res['max_rel_redondeo']:.1e}), {res['distintos']} distintos; faltas: "
          f"{res['solo_tag']} solo en el tag, {res['solo_rama']} solo en la rama, {res['faltas_explicadas']} "
          f"explicadas por un corte de NASA en el log, {res['faltas_sin_explicar']} sin explicar")
    if a.salida:
        Path(a.salida).write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    return 0 if (res["distintos"] + res["faltas_sin_explicar"]) == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
