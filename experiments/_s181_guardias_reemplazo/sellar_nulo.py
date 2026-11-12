# -*- coding: utf-8 -*-
"""Sella el nulo de las tres guardias K (MODIS, VIIRS 375, VIIRS 750) antes de reemplazar la historia con la vía (S181).

POR QUÉ. El nulo de cada guardia compara, en los 14 días previos al encendido de la vía, lo que publican la guardia (K)
y producción (K entonces) en las mismas pasadas: es el control de que la guardia mide lo mismo que medía producción
(A110). El reemplazo de la historia (#987) deja esos 14 días con la vía, y el nulo vivo baja a 0 pares: la vigilancia
queda ciega sin que nada haya cambiado en el tramo medido. Este script corre las tres vigilancias sobre los datos de
hoy, ANTES del reemplazo, y guarda su nulo con el encendido al que pertenece. `nulo_vigente` lo usa sólo cuando el nulo
vivo no tiene pares y el encendido coincide.

Se rehúsa si alguna vigilancia ya no tiene pares K (el reemplazo ya se aplicó, o el nulo nunca se midió): sellar 0 pares
sería sellar «no medí»; y se rehúsa si hay pasadas distintas (pedían INVESTIGAR, y un
sello no puede taparlas). Ningún número se transcribe a mano (S91): el JSON lo escribe este script.

Uso (sobre un checkout de main sin el reemplazo aplicado):
    python experiments/_s181_guardias_reemplazo/sellar_nulo.py
"""
import io
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

import vigilancia_guardia_modis as vg  # noqa: E402
import vigilancia_guardia_viirs as vv  # noqa: E402


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    hoy = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    commit = subprocess.run(["git", "log", "-1", "--format=%H", "--", "data/mirova_equivalent"], cwd=ROOT,
                            capture_output=True, text=True, check=True).stdout.strip()
    salidas = {"MODIS": vg.evaluar(hoy), "VIIRS375": vv.evaluar(hoy, "v375"), "VIIRS750": vv.evaluar(hoy, "v750")}
    sello = {}
    for sensor, out in salidas.items():
        enc = out.get("encendido_modis_utc") if sensor == "MODIS" else out.get("encendido_utc")
        n = out.get("nulo") or {}
        if not enc or n.get("sellado") or not n.get("pares") or n.get("distintas") != 0:
            print(f"REHUSADO {sensor}: encendido {enc}, nulo {n.get('pares')} pares (sellado: {n.get('sellado')})",
                  file=sys.stderr)
            return 2
        limite = datetime.strptime(enc, "%Y-%m-%d %H:%M:%S")
        sello[sensor] = {"encendido_utc": enc, "pares": n["pares"], "distintas": n["distintas"],
                         "detalle": n.get("detalle", []),
                         "ventana_utc": [(limite - timedelta(days=vg.DIAS_NULO)).strftime("%Y-%m-%d %H:%M:%S"), enc],
                         "medido_en_commit": commit,
                         "medido_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")}
        print(f"{sensor}: encendido {enc}, nulo {n['distintas']} distintas de {n['pares']} pares")
    with open(vg.NULO_SELLADO, "w", encoding="utf-8", newline="\n") as f:
        json.dump(sello, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print("escrito", vg.NULO_SELLADO)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
