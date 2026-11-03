# -*- coding: utf-8 -*-
"""S162 V750-B, adenda 1: cobertura con las cajas del oráculo (compañero del analizador sellado, que no se edita).

POR QUÉ. El §4 del pre-registro sellado dice que una pasada con error de un brazo es SIN DATO y que con más del 2 % de
SIN DATO, o una protegida SIN DATO, no se lee el veredicto. El analizador sellado (`analizar_v750b.py` l. 208-209)
exige las cinco cajas del oráculo para contar una pasada como observada, pero si a una pasada «ok» le falta una caja
no la cuenta en ningún lado: sale del denominador sin nombre, y una protegida así deja la cobertura en SUFICIENTE. Con
el probe sellado eso no debería pasar (las cinco cajas se calculan juntas y cualquier excepción marca la pasada entera
como error), pero un relanzamiento con `SOLO` sobre otro código o un artefacto dañado lo harían posible, y en ese caso
el analizador callaría. Este compañero rehace la cuenta de cobertura del analizador, línea por línea, y le suma esas
pasadas como SIN DATO con nombre. No toca ninguna métrica ni la regla del §6.

Se corre ANTES del analizador con los mismos argumentos. Sale 0 si la cobertura con las cajas es SUFICIENTE, 3 si es
INSUFICIENTE (mismo código que la compuerta cerrada del analizador). Con 0 pasadas sin caja reproduce exactamente el
SIN DATO y el veredicto de cobertura del analizador (escenario A4 de `probar_adenda1.py`).
Uso: python cobertura_cajas_v750b.py --art <carpetas del run> --objetivos objetivos_v750b.json
     --sin-granulo sin_granulo_v750b.json
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import sys
from pathlib import Path

AQUI = Path('C:\\Users\\nmend\\OneDrive\\Escritorio\\claude\\Volcanologia\\VRP Chile\\.claude\\worktrees\\s162-viirs750-2-918174\\experiments\\_s162_v750b\\adenda1')
sys.path.insert(0, 'C:\\Users\\nmend\\OneDrive\\Escritorio\\claude\\Volcanologia\\VRP Chile\\.claude\\worktrees\\s162-viirs750-2-918174\\experiments\\_s162_v750b')
import analizar_v750b as AB  # noqa: E402  (sólo partida, cargar, CAJAS y MAX_SIN_DATO; nada de la regla)


def cajas_faltantes(r):
    """Cajas del oráculo que una pasada «ok» no trae, o trae vacías (una caja que no es un dict no tiene máscara)."""
    orc = r.get("oraculo") or {}
    return [c for c in AB.CAJAS if not isinstance(orc.get(c), dict)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--art", required=True, nargs="+")
    ap.add_argument("--objetivos", required=True)
    ap.add_argument("--sin-granulo", default=str(AB.AQUI / "sin_granulo_v750b.json"))
    a = ap.parse_args()
    obj = {o["id"]: o for o in json.loads(Path(a.objetivos).read_text(encoding="utf-8"))}
    res = AB.cargar(a.art)

    # copia de analizar_v750b.py l. 205-207 y 218-224, sin cambios
    part = {i: AB.partida(res.get(i) or {}) for i in obj}
    sin = [i for i in obj if part[i] is None or (part[i] == "observada" and res[i].get("dayflag") == 1)]
    no_obs = collections.Counter(part[i] for i in obj if part[i] in ("fuera", "sin_crater"))
    sg = Path(a.sin_granulo)
    sha_obj = hashlib.sha256(Path(a.objetivos).read_bytes()).hexdigest()
    sg_ok, sin_g = False, []
    if sg.exists():
        dsg = json.loads(sg.read_text(encoding="utf-8"))
        sg_ok = isinstance(dsg, dict) and dsg.get("objetivos_sha256") == sha_obj
        sin_g = dsg.get("pasadas", []) if sg_ok else []

    # lo que el analizador sellado deja caer: observada, nocturna y sin alguna caja
    falta = [i for i in obj if part[i] == "observada" and res[i].get("dayflag") == 0 and cajas_faltantes(res[i])]

    prot_sin = [(obj[i]["volcan"], obj[i]["hora_utc"]) for i in sin + falta if obj[i].get("protegida")]
    prot_sin += [(x["volcan"], x["hora_utc"]) for x in sin_g if x.get("protegida")]
    den = max(1, len(obj) + len(sin_g) - no_obs["fuera"] - no_obs["sin_crater"])
    n_sin = len(sin) + len(sin_g) + len(falta)
    cob_ok = sg_ok and n_sin <= AB.MAX_SIN_DATO * den and not prot_sin

    print(f"== cobertura (adenda 1): objetivos {len(obj)} | no observadas {dict(no_obs)} | denominador {den}")
    print(f"   SIN DATO total: {n_sin} (analizador sellado {len(sin)}, sin gránulo {len(sin_g)}, falta caja {len(falta)})"
          + ("" if sg_ok else f" | ARCHIVO SIN GRÁNULO {'AUSENTE' if not sg.exists() else 'DE OTRA LISTA'}: SIN DATO"))
    for i in falta:
        o = obj[i]
        print(f"   falta caja: id {i} {o['volcan']} {o['hora_utc']} {o['lab']}"
              f"{' PROTEGIDA' if o.get('protegida') else ''} cajas faltantes {cajas_faltantes(res[i])}")
    print("   protegidas SIN DATO:", prot_sin or "ninguna")
    print("== cobertura con las cajas:", "SUFICIENTE" if cob_ok else
          f"INSUFICIENTE (más de {AB.MAX_SIN_DATO:.0%} sin procesar o una protegida): relanzar con SOLO las faltantes")
    return 0 if cob_ok else 3


if __name__ == "__main__":
    sys.exit(main())
