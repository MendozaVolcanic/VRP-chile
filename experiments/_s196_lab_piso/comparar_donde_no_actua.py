# -*- coding: utf-8 -*-
"""S196: cada brazo de piso tiene que ser el brazo sin zona en todos los records donde la zona A no actúa.

POR QUÉ. El pre-registro sellado (experiments/_s196_lab_piso/PREREGISTRO.md §5, «Control donde la zona no actúa») lo
exige porque es lo único que vigila una fuga del piso fuera de la zona: en el brazo de control el piso vale lo mismo
dentro y fuera (0,003), así que su identidad con el brazo sin zona no puede ver un piso que se aplique donde no debe.
La zona sólo actúa de noche, en la vía y fuera de Cordón Caulle (volcanes_fuera, D6). En los demás records (de día,
`diag_codigo_mirova.dayflag` 1; los que no pasan por la vía, `via_codigo_mirova` falso; y todos los de Cordón Caulle)
el brazo tiene que ser idéntico al sin zona, salvo los tres campos que el almacén agrega para describir la corrida
(processed_utc, first_processed_utc y regimen; pipeline/store.py), como en experiments/_s195_lab_paso3/comparar_control.py.
Un record de ese conjunto que esté en un brazo y no en el otro también es falla (cobertura distinta, A108). Los
records de noche en la vía no se comparan: ahí la palanca cambia el resultado a propósito.

Uso: python experiments/_s196_lab_piso/comparar_donde_no_actua.py --sin-zona <dir> --brazo <dir> [--out r.json]
Sale con 0 si son iguales donde la zona no actúa, 1 si alguno difiere o falta, 2 si falta una carpeta o no hay ningún
record donde la zona no actúe (un control que no puede fallar no prueba nada, A110).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

DESCRIPTIVOS = ("processed_utc", "first_processed_utc", "regimen")
VOLCANES_FUERA = ("PuyehueCordonCaulle",)   # los volcanes_fuera de los perfiles _s196_lab_* (D6: inner de 20 km)


def no_actua(rec: dict, volcan: str) -> bool:
    """La zona A no puede actuar en este record: volcán fuera, record fuera de la vía o pasada de día."""
    if volcan in VOLCANES_FUERA:
        return True
    if not rec.get("via_codigo_mirova"):
        return True
    return (rec.get("diag_codigo_mirova") or {}).get("dayflag") == 1


def _leer(ruta: Path, volcan: str) -> dict:
    """Todos los records del archivo por (gránulo, sensor, hora): (no actúa la zona, record sin los descriptivos)."""
    if not ruta.exists():
        return {}
    d = json.loads(ruta.read_text(encoding="utf-8"))
    recs = d["records"] if isinstance(d, dict) else d
    return {(r.get("granule"), r.get("sensor"), r.get("datetime_utc")):
            (no_actua(r, volcan), json.dumps({k: v for k, v in r.items() if k not in DESCRIPTIVOS}, sort_keys=True))
            for r in recs}


def comparar(sin_zona: Path, brazo: Path) -> dict:
    """El conjunto comparado son los records donde la zona no actúa en CUALQUIERA de los dos lados: un record de día en
    el sin zona que en el brazo pase a parecer de noche en la vía sigue entrando, y sale como distinto o faltante."""
    res = {"volcanes": {}, "n_records": 0, "n_distintos": 0, "n_solo_sin_zona": 0, "n_solo_brazo": 0}
    nombres = sorted({p.name for p in sin_zona.glob("*.json")} | {p.name for p in brazo.glob("*.json")})
    for nombre in nombres:
        volcan = nombre[:-5]
        a, b = _leer(sin_zona / nombre, volcan), _leer(brazo / nombre, volcan)
        claves = {k for k, v in a.items() if v[0]} | {k for k, v in b.items() if v[0]}
        distintos, solo_a, solo_b = [], [], []
        for k in sorted(claves, key=str):
            if k not in a:
                solo_b.append(str(k))
            elif k not in b:
                solo_a.append(str(k))
            elif a[k][1] != b[k][1]:
                distintos.append(str(k))
        n = len(claves) - len(solo_a) - len(solo_b)
        res["volcanes"][nombre] = {"n": n, "n_distintos": len(distintos), "distintos": distintos[:20],
                                   "solo_sin_zona": solo_a[:20], "solo_brazo": solo_b[:20]}
        res["n_records"] += n
        res["n_distintos"] += len(distintos)
        res["n_solo_sin_zona"] += len(solo_a)
        res["n_solo_brazo"] += len(solo_b)
    return res


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--sin-zona", required=True)
    ap.add_argument("--brazo", required=True)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    sin_zona, brazo = Path(a.sin_zona), Path(a.brazo)
    if not sin_zona.is_dir() or not brazo.is_dir():
        print(f"FALTA CARPETA: sin zona {sin_zona.is_dir()} brazo {brazo.is_dir()}")
        return 2
    res = comparar(sin_zona, brazo)
    if a.out:
        Path(a.out).write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
    total = res["n_records"] + res["n_solo_sin_zona"] + res["n_solo_brazo"]
    igual = res["n_distintos"] == 0 and res["n_solo_sin_zona"] == 0 and res["n_solo_brazo"] == 0
    print(("IDENTICOS" if igual else "DISTINTOS") + f" donde la zona no actúa: {res['n_records']} records pareados, "
          f"{res['n_distintos']} distintos, {res['n_solo_sin_zona']} solo en el sin zona, {res['n_solo_brazo']} solo "
          "en el brazo")
    if total == 0:
        print("SIN RECORDS: no hay ningún record donde la zona no actúe, nada que comparar")
        return 2
    return 0 if igual else 1


if __name__ == "__main__":
    raise SystemExit(main())
