# experiments/_historia_34/aplicar_historia_34.py
# -*- coding: utf-8 -*-
"""Escribe la historia de los 34 volcanes sin MIROVA con la vía en data/historia_34/<V>.json.

POR QUÉ. Nicolás pidió el 2026-11-13 tener hacia atrás los 34 que el tablero ya muestra desde la sombra diaria
(data/sombra_34/, desde el 2026-11-03). La historia va en archivos PROPIOS y no en los de la sombra: el tablero baja
completo el archivo de la sombra al cargar, y la sombra empuja con `git pull --rebase -X theirs`, que borraría la
historia si este commit entra mientras ella corre (plan docs/superpowers/plans/2026-11-13-historia-34-volcanos-via.md, §1).

REGLAS: sólo antes del CORTE (desde ahí manda la sombra); todo record con la vía y el perfil del brazo; sólo los 34;
un archivo existente se une por clave y gana lo que ya estaba (las tandas se aplican de a una y se pueden repetir).
Por defecto es ENSAYO. Lo llama aplicar_historia_34.sh desde .github/workflows/aplicar-reemplazo.yml.
"""
from __future__ import annotations

import argparse
import gzip
import io
import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(RAIZ / "experiments" / "_s180_reemplazo_via"))
from plan_trozos_historia import LOS_34  # noqa: E402

PERFIL = "_s172_retro_paquete"
CORTE = "2026-11-03 00:00"   # primer día de data/sombra_34 (scripts/ventana_sombra.py no devuelve nada antes)
UNION = RAIZ / "experiments" / "_historia_34" / "union"
DESTINO = RAIZ / "data" / "historia_34"


class Rehusado(Exception):
    pass


def _clave(r):
    return (r.get("datetime_utc"), r.get("sensor"))


def _minuto(dt):
    return (dt or "").replace("T", " ")[:16]


def aplicar(union: Path, destino: Path, aplicar: bool) -> dict:
    """Calcula todo antes de escribir: si un volcán se rehúsa, no se escribe ninguno."""
    informe, salida = {}, {}
    for gz in sorted(union.glob("*.json.gz")):
        v = gz.name[:-len(".json.gz")]
        if v not in LOS_34:
            raise Rehusado(f"REHUSADO: {v} no es de los 34")
        recs = json.loads(gzip.decompress(gz.read_bytes())).get("records", [])
        nuevos, tras = {}, 0
        for r in recs:
            if _minuto(r.get("datetime_utc")) >= CORTE:
                tras += 1
                continue
            if r.get("via_codigo_mirova") is not True:
                raise Rehusado(f"REHUSADO: {v} {_clave(r)} no es de la vía ({r.get('via_codigo_mirova')!r})")
            if (r.get("regimen") or {}).get("perfil") != PERFIL:
                raise Rehusado(f"REHUSADO: {v} {_clave(r)} no viene de {PERFIL}")
            nuevos[_clave(r)] = r
        previo = destino / f"{v}.json"
        ya = {}
        if previo.exists():
            ya = {_clave(r): r for r in json.loads(previo.read_text(encoding="utf-8"))["records"]}
        repetidos = sum(1 for k in nuevos if k in ya)
        todos = {**nuevos, **ya}   # gana lo que ya estaba
        lista = sorted(todos.values(), key=lambda r: (r.get("datetime_utc", ""), r.get("sensor", "")))
        salida[v] = {"volcano": v, "perfil": PERFIL, "hasta_utc": CORTE, "records": lista}
        informe[v] = {"en_union": len(recs), "tras_corte": tras, "nuevos": len(nuevos) - repetidos,
                      "ya_estaban": repetidos, "total": len(lista)}
    if aplicar:
        destino.mkdir(parents=True, exist_ok=True)
        for v, s in salida.items():
            with open(destino / f"{v}.json", "w", encoding="utf-8", newline="\n") as f:
                json.dump(s, f, indent=1, ensure_ascii=False)
    return informe


def main(argv=None) -> int:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--union", default=str(UNION))
    ap.add_argument("--destino", default=str(DESTINO))
    ap.add_argument("--informe", required=True)
    ap.add_argument("--aplicar", action="store_true")
    a = ap.parse_args(argv)
    try:
        inf = aplicar(Path(a.union), Path(a.destino), a.aplicar)
    except Rehusado as e:
        print(e, file=sys.stderr)
        return 2
    Path(a.informe).parent.mkdir(parents=True, exist_ok=True)
    Path(a.informe).write_text(json.dumps(inf, indent=1, ensure_ascii=False), encoding="utf-8")
    for v, i in inf.items():
        print(f"{v:22s} en la unión {i['en_union']:5d}  nuevos {i['nuevos']:5d}  ya estaban {i['ya_estaban']:5d}  "
              f"tras el corte {i['tras_corte']:3d}  total {i['total']:5d}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
