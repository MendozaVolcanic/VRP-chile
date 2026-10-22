# -*- coding: utf-8 -*-
"""Estabilidad de la referencia de MIROVA: cuanto reescribe su pasado (S159, solo lectura).

POR QUE. Toda evaluacion de la replica se mide contra los CSV del scraper Mirova-v1. Si la
referencia cambia filas de pasadas ya ocurridas, un A/B evaluado un dia y releido otro puede
cambiar de veredicto sin que cambie nada nuestro. Este script recorre la historia commiteada en
NUESTRO repo (sin red):
  - consolidado (tabla latest.php): `latest_consolidado.csv`, copia horaria de sync-mirova-csv.yml
  - OCR: `data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv`, copia horaria desde S146
y compara cada version con la anterior.

Clave de fila: (Volcan normalizado, sensor normalizado, Fecha_Satelite_UTC al minuto), igual que
`scripts/referencia_mirova_unificada.clave` sin el canal (el canal es el archivo).
Contenido comparado: Tipo_Registro, VRP_MW (float), distancia (CONS: Distancia_km; OCR:
Distancia_km si >0, si no la de Nota_Validacion, igual que leer_pasadas), Clasificacion Mirova.
Metadatos que NO cuentan como reescritura: Ultima_Actualizacion*, Fecha_Proceso*, Editado,
Ruta Foto, timestamp. Se cuentan aparte.

LIMITES DEL INSTRUMENTO (declarados):
  - Muestreo horario: Mirova-v1 commitea cada 5 min; un cambio que va y vuelve dentro de la hora
    es invisible.
  - El OCR tiene un guard en sync-mirova-csv.yml que RECHAZA una version con menos lineas que la
    previa: las bajas netas del OCR no entran a nuestra copia (las vemos solo si vienen con altas).
  - Una hora sin commit = archivo identico o workflow que no corrio; no se distingue aqui.

Uso:
  python historia_referencia.py --desde 2026-08-22 [--autotest]
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import subprocess
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(r"C:\vrp-trabajo\s159-pruebas")
sys.path.insert(0, str(REPO))
from pipeline.mirova_csv_loader import (normalize_sensor, normalize_volcano_name,  # noqa: E402
                                        parse_ocr_distance)

OUT = Path(__file__).resolve().parent
RUTAS = {
    "CONS": "latest_consolidado.csv",
    "OCR": "data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv",
}
CAMPOS = ("tipo", "vrp", "dist", "clase")


def git(*args) -> str:
    return subprocess.run(["git", "-C", str(REPO), *args], capture_output=True, text=True,
                          check=True, encoding="utf-8").stdout


def commits(ruta: str, desde: str, ref: str = "origin/main", hasta: str = None) -> list[tuple[str, str]]:
    """(sha, fecha ISO) en orden cronologico, mas la ultima version anterior a `desde` como base."""
    # OJO: historia_previa.json se genero ANTES de este arreglo; su --hasta no se aplico y cubre
    # desde la primera copia (2026-05-23) hasta 2026-10-21. Se lee como "historia completa".
    extra = [f"--until={hasta}T00:00:00Z"] if hasta else []
    dentro = git("log", ref, f"--since={desde}T00:00:00Z", *extra, "--format=%H %cI", "--", ruta).split("\n")
    dentro = [tuple(l.split()) for l in dentro if l.strip()][::-1]
    base = git("log", ref, f"--until={desde}T00:00:00Z", "-1", "--format=%H %cI", "--", ruta).split()
    return ([tuple(base)] if base else []) + dentro


class Blobs:
    """Lector de blobs por `git cat-file --batch` (un solo proceso)."""

    def __init__(self):
        self.p = subprocess.Popen(["git", "-C", str(REPO), "cat-file", "--batch"],
                                  stdin=subprocess.PIPE, stdout=subprocess.PIPE)

    def leer(self, spec: str) -> bytes:
        self.p.stdin.write((spec + "\n").encode())
        self.p.stdin.flush()
        cab = self.p.stdout.readline().decode().split()
        if len(cab) < 3 or cab[1] == "missing":
            raise KeyError(spec)
        n = int(cab[2])
        data = self.p.stdout.read(n)
        self.p.stdout.read(1)
        return data


def _f(v):
    try:
        return round(float(str(v).strip()), 4)
    except (TypeError, ValueError):
        return None


def parsear(texto: str, canal: str):
    """dict clave -> contenido; mas contadores de duplicados y filas no Tier A."""
    filas, dup, crudas, no_tier = {}, 0, Counter(), 0
    raw_por_norm = defaultdict(set)
    for r in csv.DictReader(io.StringIO(texto)):
        vol = normalize_volcano_name(r.get("Volcan"))
        fecha = (r.get("Fecha_Satelite_UTC") or "").strip()
        if vol is None or len(fecha) < 16:
            no_tier += 1
            continue
        k = (vol, normalize_sensor(r.get("Sensor")), fecha[:16])
        raw_por_norm[k].add(((r.get("Volcan") or "").strip(), (r.get("Sensor") or "").strip()))
        if canal == "OCR":
            d = _f(r.get("Distancia_km"))
            if not (d and d > 0):
                d = parse_ocr_distance(r.get("Nota_Validacion", ""))
                d = round(d, 4) if d is not None else None
        else:
            d = _f(r.get("Distancia_km"))
        c = {"tipo": (r.get("Tipo_Registro") or "").strip(), "vrp": _f(r.get("VRP_MW")), "dist": d,
             "clase": (r.get("Clasificacion Mirova") or "").strip(),
             "meta": (r.get("Ultima_Actualizacion") or "").strip()}
        if k in filas:
            dup += 1
            if c["meta"] <= filas[k]["meta"]:
                continue  # misma regla que leer_pasadas: gana la Ultima_Actualizacion mas reciente
        filas[k] = c
    variantes = {k: v for k, v in raw_por_norm.items() if len(v) > 1}
    return filas, dup, no_tier, variantes


def diff(a: dict, b: dict):
    alta = [k for k in b if k not in a]
    baja = [k for k in a if k not in b]
    cambio, meta = [], 0
    for k in a.keys() & b.keys():
        campos = [c for c in CAMPOS if a[k][c] != b[k][c]]
        if campos:
            cambio.append((k, campos))
        elif a[k]["meta"] != b[k]["meta"]:
            meta += 1
    return alta, baja, cambio, meta


def estrato(c: dict) -> str:
    """Clase de la fila para medir que tipo de cosa se reescribe."""
    if c is None:
        return "?"
    t = c["tipo"]
    if t.startswith("ALERTA"):
        if t == "ALERTA_SIN_GEOMETRIA_OCR":
            return "alerta_sin_geometria"
        return "alerta_>=1MW" if (c["vrp"] or 0) >= 1.0 else "alerta_<1MW"
    if t.startswith("FALSO"):
        return "falso_positivo"
    if t == "RUTINA":
        return "rutina"
    return t or "vacio"


def ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc)


def recorrer(canal: str, desde: str, blobs: Blobs, hasta: str = None):
    ruta = RUTAS[canal]
    lista = commits(ruta, desde, hasta=hasta)
    prev, prev_blob = None, None
    por_version, eventos = [], []
    primera_vista = {}
    variantes_total = {}
    dups = []
    for sha, fecha in lista:
        blob = git("rev-parse", f"{sha}:{ruta}").strip()
        if blob == prev_blob:
            por_version.append({"sha": sha[:9], "fecha": fecha, "identica": True})
            continue
        texto = blobs.leer(blob).decode("utf-8", errors="replace")
        filas, dup, no_tier, variantes = parsear(texto, canal)
        dups.append(dup)
        variantes_total.update(variantes)
        t = ts(fecha)
        if prev is None:
            for k in filas:
                primera_vista[k] = None  # ya existia en la base: no sabemos cuando llego
            por_version.append({"sha": sha[:9], "fecha": fecha, "base": True, "n": len(filas)})
        else:
            alta, baja, cambio, meta = diff(prev, filas)
            for k in alta:
                sat = datetime.fromisoformat(k[2] + ":00").replace(tzinfo=timezone.utc)
                edad_h = (t - sat).total_seconds() / 3600
                vuelve = k in primera_vista
                eventos.append({"canal": canal, "ev": "reaparece" if vuelve else "alta", "k": k,
                                "commit": sha[:9], "t": fecha, "edad_h": round(edad_h, 2),
                                "estrato": estrato(filas[k]), "nuevo": filas[k]})
                primera_vista.setdefault(k, fecha)
            for k in baja:
                sat = datetime.fromisoformat(k[2] + ":00").replace(tzinfo=timezone.utc)
                eventos.append({"canal": canal, "ev": "baja", "k": k, "commit": sha[:9], "t": fecha,
                                "edad_h": round((t - sat).total_seconds() / 3600, 2),
                                "estrato": estrato(prev[k]), "viejo": prev[k]})
            for k, campos in cambio:
                sat = datetime.fromisoformat(k[2] + ":00").replace(tzinfo=timezone.utc)
                eventos.append({"canal": canal, "ev": "cambio", "k": k, "commit": sha[:9], "t": fecha,
                                "edad_h": round((t - sat).total_seconds() / 3600, 2),
                                "campos": campos, "estrato": estrato(prev[k]),
                                "estrato_nuevo": estrato(filas[k]), "viejo": prev[k], "nuevo": filas[k]})
            por_version.append({"sha": sha[:9], "fecha": fecha, "n": len(filas), "alta": len(alta),
                                "baja": len(baja), "cambio": len(cambio), "solo_meta": meta,
                                "dup": dup, "no_tier": no_tier})
        prev, prev_blob = filas, blob
    return {"versiones": por_version, "eventos": eventos, "ultima": prev,
            "variantes": {"|".join(k): sorted(map(list, v)) for k, v in variantes_total.items()},
            "dups_max": max(dups) if dups else 0}


def autotest(blobs: Blobs) -> dict:
    """Nulo (version consigo misma = 0) y control positivo sintetico (mutaciones conocidas)."""
    ruta = RUTAS["CONS"]
    sha = git("log", "origin/main", "-1", "--format=%H", "--", ruta).strip()
    texto = blobs.leer(git("rev-parse", f"{sha}:{ruta}").strip()).decode("utf-8")
    a, *_ = parsear(texto, "CONS")
    nulo = diff(a, a)
    lineas = texto.splitlines(keepends=True)
    # mutacion 1: cambiar VRP de la linea 100; mutacion 2: borrar la linea 200; 3: cambiar tipo
    filas = list(csv.reader(io.StringIO(texto)))
    cab = filas[0]
    iv, it = cab.index("VRP_MW"), cab.index("Tipo_Registro")
    filas[100][iv] = str((_f(filas[100][iv]) or 0) + 7.5)
    filas[300][it] = "ALERTA_TERMICA" if filas[300][it] != "ALERTA_TERMICA" else "RUTINA"
    del filas[200]
    s = io.StringIO()
    csv.writer(s, lineterminator="\n").writerows(filas)
    b, *_ = parsear(s.getvalue(), "CONS")
    alta, baja, cambio, meta = diff(a, b)
    return {"sha": sha[:9], "n": len(a),
            "nulo": {"alta": len(nulo[0]), "baja": len(nulo[1]), "cambio": len(nulo[2]), "meta": nulo[3]},
            "positivo_esperado": {"alta": 0, "baja": 1, "cambio": 2},
            "positivo_medido": {"alta": len(alta), "baja": len(baja), "cambio": len(cambio),
                                "campos": sorted(c for _, cs in cambio for c in cs)}}


def main(argv=None):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", default="2026-08-22")
    ap.add_argument("--hasta", default=None)
    ap.add_argument("--salida", default="historia.json")
    a = ap.parse_args(argv)
    blobs = Blobs()
    res = {"desde": a.desde, "ref": git("rev-parse", "origin/main").strip(), "autotest": autotest(blobs)}
    print("AUTOTEST", json.dumps(res["autotest"], ensure_ascii=False))
    for canal in ("CONS", "OCR"):
        r = recorrer(canal, a.desde, blobs, a.hasta)
        vs = r["versiones"]
        print(f"\n== {canal}: {len(vs)} commits ({sum(1 for v in vs if v.get('identica'))} identicos al previo), "
              f"duplicados max por version {r['dups_max']}, variantes de nombre {len(r['variantes'])}")
        res[canal] = {k: v for k, v in r.items() if k != "ultima"}
    def _ser(o):
        if isinstance(o, tuple):
            return list(o)
        raise TypeError
    ev = res["CONS"]["eventos"] + res["OCR"]["eventos"]
    for e in ev:
        e["k"] = list(e["k"])
    (OUT / a.salida).write_text(json.dumps(res, ensure_ascii=False, default=_ser), encoding="utf-8")
    print("eventos:", Counter((e["canal"], e["ev"]) for e in ev))


if __name__ == "__main__":
    main()
