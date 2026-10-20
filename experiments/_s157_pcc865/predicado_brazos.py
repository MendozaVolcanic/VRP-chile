# -*- coding: utf-8 -*-
"""S157 issue #865: el predicado del tablero (frontend/index.html, EJECUTADO con node, A97) sobre los cuatro brazos
del probe por etapa y sobre los dos records persistidos (K de producción y C0 de la sombra).

Uso: python predicado_brazos.py <probe_pcc865.json>
"""
import io
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
sys.path.insert(0, str(ROOT / "scripts"))
import banco_paridad as bp  # noqa: E402

VOL, SENSOR, DT = "PuyehueCordonCaulle", "VIIRS_NOAA21_750", "2026-10-10 05:54"


def persistido(sub):
    d = json.load(open(ROOT / "data" / sub / f"{VOL}.json", encoding="utf-8"))
    (r,) = [x for x in d["records"] if x.get("sensor") == SENSOR and x.get("datetime_utc") == DT]
    return r


def main():
    probe = json.load(open(sys.argv[1], encoding="utf-8"))
    inner = bp.inner_desde_html()[VOL]
    casos = {f"probe {n}": b["record"] for n, b in probe["brazos"].items()}
    casos["persistido K (data/mirova_equivalent)"] = persistido("mirova_equivalent")
    casos["persistido C0 (data/experimental_v2)"] = persistido("experimental_v2")
    nombres = list(casos)
    res = bp.correr_node([[{k: casos[n].get(k) for k in bp.CAMPOS_JS}, inner] for n in nombres])
    ident = bp.control_identidad_predicado()
    print(f"inner_radius_km de PCC en el tablero: {inner}")
    print(f"control de identidad del predicado (esperado ([0,1,1,1,0],[1,0]) como banco_paridad.controles): {ident}")
    print(f"{'caso':40s} summit valid artefacto magnitud_tablero PUBLICA")
    for n, r in zip(nombres, res):
        print(f"{n:40s} {r[0]:6d} {r[1]:5d} {r[2]:9d} {r[3]!s:>16s} {r[4]:7d}")


if __name__ == "__main__":
    main()
