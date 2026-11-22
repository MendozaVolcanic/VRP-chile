# -*- coding: utf-8 -*-
"""S195: el brazo s = 5,0 del barrido de la zona A tiene que ser el brazo de control, record a record.

POR QUÉ. El pre-registro sellado (experiments/_s194_lab_zona_a/PREREGISTRO.md §5) exige que el brazo s = 5,0 dé
exactamente las cuentas de producción; si no, la implementación cambia algo más que el multiplicador (geometría,
fondo, ancla). evaluar.py calibrar lo comprueba sobre las cuentas de publicación. Esto lo comprueba antes y más
fuerte: los dos brazos corren en el mismo job, sobre los mismos gránulos y con el mismo código, así que cada record
tiene que ser idéntico salvo los tres campos que el almacén agrega para describir la corrida (processed_utc,
first_processed_utc y regimen, que lleva el nombre del perfil; pipeline/store.py). Un record que esté en uno y no en
el otro también es falla (cobertura distinta, A108).

Uso: python experiments/_s195_lab_paso3/comparar_control.py --control <dir> --brazo <dir> [--out r.json]
Sale con 0 si los dos son iguales en todos los volcanes, 1 si no, 2 si falta una carpeta o no hay records que comparar
(un control que no puede fallar no prueba nada).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DESCRIPTIVOS = ("processed_utc", "first_processed_utc", "regimen")


def _records(ruta: Path) -> dict:
    d = json.loads(ruta.read_text(encoding="utf-8"))
    recs = d["records"] if isinstance(d, dict) else d
    out = {}
    for r in recs:
        clave = (r.get("granule"), r.get("sensor"), r.get("datetime_utc"))
        out[clave] = json.dumps({k: v for k, v in r.items() if k not in DESCRIPTIVOS}, sort_keys=True)
    return out


def comparar(control: Path, brazo: Path) -> dict:
    res = {"volcanes": {}, "n_records": 0, "n_distintos": 0, "n_solo_control": 0, "n_solo_brazo": 0}
    nombres = sorted({p.name for p in control.glob("*.json")} | {p.name for p in brazo.glob("*.json")})
    for nombre in nombres:
        a = _records(control / nombre) if (control / nombre).exists() else {}
        b = _records(brazo / nombre) if (brazo / nombre).exists() else {}
        distintos = sorted(str(k) for k in set(a) & set(b) if a[k] != b[k])
        solo_a, solo_b = sorted(str(k) for k in set(a) - set(b)), sorted(str(k) for k in set(b) - set(a))
        res["volcanes"][nombre] = {"n": len(set(a) & set(b)), "distintos": distintos[:20], "n_distintos": len(distintos),
                                   "solo_control": solo_a[:20], "solo_brazo": solo_b[:20]}
        res["n_records"] += len(set(a) & set(b))
        res["n_distintos"] += len(distintos)
        res["n_solo_control"] += len(solo_a)
        res["n_solo_brazo"] += len(solo_b)
    return res


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--control", required=True)
    ap.add_argument("--brazo", required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    control, brazo = Path(a.control), Path(a.brazo)
    if not control.is_dir() or not brazo.is_dir():
        print(f"FALTA CARPETA: control {control.is_dir()} brazo {brazo.is_dir()}")
        return 2
    res = comparar(control, brazo)
    if a.out:
        Path(a.out).write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    igual = res["n_distintos"] == 0 and res["n_solo_control"] == 0 and res["n_solo_brazo"] == 0
    print(("IDENTICOS" if igual else "DISTINTOS") + f": {res['n_records']} records pareados, {res['n_distintos']} "
          f"distintos, {res['n_solo_control']} solo en el control, {res['n_solo_brazo']} solo en el brazo")
    if res["n_records"] == 0:
        print("SIN RECORDS: no hay nada que comparar")
        return 2
    return 0 if igual else 1


if __name__ == "__main__":
    raise SystemExit(main())
