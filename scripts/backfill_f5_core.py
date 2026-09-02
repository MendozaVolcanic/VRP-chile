# -*- coding: utf-8 -*-
"""S132 - Escribe `f5_core_vrp_mw` en los records historicos (decision #3 de AUDIT_S131 §4).

POR QUE. Hasta hoy la magnitud que el dashboard publica para VIIRS375 se recalculaba en el
navegador y no quedaba en ningun JSON: la cifra publicada no era auditable. El campo ya se
persiste para los records nuevos (store.py); este script lo escribe para los viejos.

NO CAMBIA NINGUN NUMERO. El calculo se hace desde `anomaly_pixels`, que ya estan en el
record, con el mismo algoritmo que el navegador venia corriendo - la equivalencia con el
JS esta probada sobre 4.000 records reales en
tests/test_f5_core_python_s132.py::test_paridad_con_el_javascript.

Dry-run por defecto; `--apply` escribe. Reversible con el tag defensivo del commit.
No paralelizar (A47: race condition sobre data/mirova_equivalent/).
"""
import glob
import io
import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import yaml

from pipeline.f5_core import es_viirs_iband, f5_core_vrp_mw

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


def inner_radius_por_volcan():
    with open(os.path.join(ROOT, "volcanoes.yaml"), encoding="utf-8") as fp:
        vols = yaml.safe_load(fp)
    vols = vols.get("volcanoes", vols)
    it = vols if isinstance(vols, list) else vols.values()
    return {v["name"]: float(v.get("inner_radius_km") or 10.0)
            for v in it if isinstance(v, dict) and v.get("name")}


def main(dry_run=True):
    inner = inner_radius_por_volcan()
    escritos = sin_inner = iband = tot = archivos = 0
    sin_recompute = 0
    for p in sorted(glob.glob(os.path.join(ROOT, "data", "mirova_equivalent", "*.json"))):
        nombre = os.path.splitext(os.path.basename(p))[0]
        if nombre not in inner:
            sin_inner += 1
            continue
        ik = inner[nombre]
        raw = open(p, encoding="utf-8").read()
        d = json.loads(raw)
        recs = d.get("records", d)
        cambio = False
        for r in recs:
            tot += 1
            if not es_viirs_iband(r.get("sensor")):
                continue
            iband += 1
            core = f5_core_vrp_mw(r, ik)
            if core is None:
                # Sin cumulo validado o sin pixeles dentro del inner: el dashboard cae a
                # pc.vrp_mw y aca NO se inventa un campo (asimetria A46).
                sin_recompute += 1
                if r.pop("f5_core_vrp_mw", None) is not None:
                    cambio = True
                continue
            nuevo = round(float(core), 4)
            if r.get("f5_core_vrp_mw") != nuevo:
                r["f5_core_vrp_mw"] = nuevo
                escritos += 1
                cambio = True
        if cambio and not dry_run:
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                json.dump(d, f, indent=2, ensure_ascii=False)
                if raw.endswith("\n"):
                    f.write("\n")
            archivos += 1
    modo = "DRY-RUN (sin escribir)" if dry_run else "ESCRITO"
    print(f"{modo} | records: {tot} | I-band: {iband} | f5_core escritos: {escritos} | "
          f"I-band sin recompute (caen a pc.vrp_mw): {sin_recompute} | archivos: {archivos} | "
          f"volcanes sin inner_radius en yaml: {sin_inner}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--apply" not in sys.argv))
