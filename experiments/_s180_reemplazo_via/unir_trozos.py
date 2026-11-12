# -*- coding: utf-8 -*-
"""Une los trozos de los despachos de la vía en un archivo por volcán, comprimido (S180, reemplazo de la historia).

POR QUÉ. Los reprocesos de la vía «código MIROVA» quedaron como artifacts de GitHub Actions, uno por trozo de 10 a 20
días, que vencen a los 30 días (D2 hacia el 2026-12-08). `aplicar-reemplazo.yml` corre sobre un checkout limpio de
main, así que la unión tiene que estar commiteada. Va FUERA de `data/` (GitHub Pages copia `data/` entera y tiene techo
de 1 GB; verificación limpia del plan, hallazgo 3) y comprimida con gzip (mtime 0, reproducible): pesa unas diez veces
menos que el JSON.

REGLAS, y por qué:
- De cada trozo se usa el intento más alto: un trozo se relanza sólo si el anterior falló (el workflow no sube el
  trozo de un intento en rojo), así que el último es el bueno.
- Sólo records con fecha de pasada dentro de la ventana del trozo: fuera de ella el trozo arrastra lo que el pipeline
  vio en los bordes, y dos trozos vecinos escribirían la misma pasada.
- Una clave (datetime_utc, sensor) repetida entre trozos se rehúsa: dos records por pasada, o ventanas solapadas.
- Todo record debe venir del perfil `_s172_retro_paquete` (el brazo de la vía; A117, A118).
- Informe por volcán: días cubiertos, huecos de calendario (un trozo que falta es un hueco, y el reemplazo apartaría
  como «sin par» pasadas que en verdad no se reprocesaron), intentos usados y conteos por familia y por marca.

Uso:
    python experiments/_s180_reemplazo_via/unir_trozos.py --salida <dir> --informe <json> <dir_run> [<dir_run> ...]
Cada <dir_run> es la carpeta de `gh run download <run>`, con subcarpetas `trozo-<V>-<i>-<a>_<b>-intento-<n>/<V>.json`.
"""
from __future__ import annotations

import argparse
import gzip
import io
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

PERFIL = "_s172_retro_paquete"
PAT = re.compile(r"^trozo-(?P<v>[A-Za-z]+)-(?P<i>\d+)-(?P<a>\d{4}-\d\d-\d\d)_(?P<b>\d{4}-\d\d-\d\d)-intento-(?P<n>\d+)$")


class Rehusado(Exception):
    pass


def familia(sensor) -> str:
    s = str(sensor or "")
    if s.startswith("MODIS"):
        return "MODIS"
    return "VIIRS750" if s.endswith("_750") else "VIIRS375"


def _dias(a: str, b: str) -> list[str]:
    d0, d1 = date.fromisoformat(a), date.fromisoformat(b)
    return [(d0 + timedelta(n)).isoformat() for n in range((d1 - d0).days + 1)]


def trozos_de(dirs: list[Path]) -> dict:
    """{(volcan, a, b): (ruta, intento, run)} con el intento más alto de cada trozo."""
    out = {}
    for base in dirs:
        for p in sorted(base.iterdir()):
            m = PAT.match(p.name)
            if not m:
                continue
            k = (m["v"], m["a"], m["b"])
            n = int(m["n"])
            if k in out and out[k][2] != base.name:
                raise Rehusado(f"REHUSADO: el trozo {k} viene de dos despachos ({out[k][2]} y {base.name})")
            if k not in out or n > out[k][1]:
                out[k] = (p / f"{m['v']}.json", n, base.name)
    return out


def unir(dirs: list[Path]) -> tuple[dict, dict]:
    """Devuelve ({volcan: store}, informe)."""
    tz = trozos_de(dirs)
    recs = defaultdict(dict)
    ventanas = defaultdict(list)
    fuera = Counter()
    for (v, a, b), (ruta, n, run) in sorted(tz.items()):
        ventanas[v].append([a, b, n, run])
        store = json.loads(ruta.read_text(encoding="utf-8"))
        if store.get("volcano") != v:
            raise Rehusado(f"REHUSADO: {ruta} dice ser de {store.get('volcano')!r}")
        for r in store.get("records", []):
            if not (a <= (r.get("datetime_utc") or "")[:10] <= b):
                fuera[v] += 1
                continue
            perfil = (r.get("regimen") or {}).get("perfil")
            if perfil != PERFIL:
                raise Rehusado(f"REHUSADO: record {r.get('datetime_utc')} {r.get('sensor')} de {v} viene de {perfil!r}")
            k = (r.get("datetime_utc"), r.get("sensor"))
            if k in recs[v]:
                raise Rehusado(f"REHUSADO: clave repetida entre trozos en {v}: {k}")
            recs[v][k] = r
    stores, informe = {}, {"volcanes": {}}
    for v in sorted(recs.keys() | ventanas.keys()):
        lista = sorted(recs[v].values(), key=lambda r: (r.get("datetime_utc", ""), r.get("sensor", "")))
        stores[v] = {"volcano": v, "perfil": PERFIL, "records": lista}
        dias = sorted({d for a, b, _, _ in ventanas[v] for d in _dias(a, b)})
        huecos = sorted(set(_dias(dias[0], dias[-1])) - set(dias)) if dias else []
        marcas = Counter()
        for r in lista:
            m = r.get("via_codigo_mirova")
            marcas[f"{familia(r.get('sensor'))}:{'true' if m is True else ('ausente' if m is None else str(m))}"] += 1
        informe["volcanes"][v] = {
            "trozos": len(ventanas[v]), "desde": dias[0] if dias else None, "hasta": dias[-1] if dias else None,
            "dias": len(dias), "huecos": huecos, "fuera_de_ventana": fuera[v], "records": len(lista),
            "marcas": dict(sorted(marcas.items())),
            "intentos_mayores_a_1": [w for w in ventanas[v] if w[2] > 1],
        }
    return stores, informe


def escribir_gz(path: Path, store: dict) -> None:
    """gzip con mtime 0: el mismo contenido da los mismos bytes (el diff de git no cambia sin motivo)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    crudo = json.dumps(store, indent=1, ensure_ascii=False).encode("utf-8")
    with open(path, "wb") as f, gzip.GzipFile(fileobj=f, mode="wb", mtime=0, compresslevel=9, filename="") as g:
        g.write(crudo)


def main(argv=None) -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--salida", required=True, help="carpeta de <Volcan>.json.gz")
    ap.add_argument("--informe", required=True)
    ap.add_argument("runs", nargs="+")
    a = ap.parse_args(argv)
    try:
        stores, inf = unir([Path(x) for x in a.runs])
    except Rehusado as e:
        print(e, file=sys.stderr)
        return 2
    for v, s in stores.items():
        escribir_gz(Path(a.salida) / f"{v}.json.gz", s)
        i = inf["volcanes"][v]
        print(f"{v:20s} {i['desde']}..{i['hasta']} {i['dias']} días, {len(i['huecos'])} huecos, "
              f"{i['records']} records, {i['trozos']} trozos")
    Path(a.informe).write_text(json.dumps(inf, indent=1, ensure_ascii=False), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
