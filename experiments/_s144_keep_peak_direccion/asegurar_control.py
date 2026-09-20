# -*- coding: utf-8 -*-
"""S144: congela en el repo los records del brazo control del A/B S143 antes de que venzan en GitHub.

POR QUÉ. La Parte A del pre-registro `docs/PREREGISTRO_KEEP_PEAK_DIRECCION_S144.md` necesita los records
del brazo `_s142_ab_control` (los que el evaluador de S143 usó para declarar las 5 pérdidas), con el
centroide del cúmulo y el `final_hotspot` por separado. Sólo existen como artefactos de GitHub Actions
(runs 35266704955 y 35340495262), que vencen el 2026-10-02 y 03 (hallazgo 5 del verificador). Los JSON
resumidos de `experiments/_s143_evaluador/verificador_veredicto/` traen una sola posición y no sirven.

QUÉ HACE. Toma los JSON que `gh run download` dejó en `control_s143/<tramo>/<Volcan>/<Volcan>.json`, los
comprime a `control_s143/<tramo>/<Volcan>.json.gz` y escribe `control_s143/MANIFIESTO.json` con el run,
el nombre del artefacto y el sha256 del JSON sin comprimir. Borra los JSON sueltos.

USO: python experiments/_s144_keep_peak_direccion/asegurar_control.py
"""
import gzip
import hashlib
import json
import shutil
from pathlib import Path

HERE = Path(__file__).resolve().parent
BASE = HERE / "control_s143"
RUNS = {"t1": 35266704955, "t2": 35340495262}


def main():
    manifiesto = []
    for tramo, run in RUNS.items():
        for carpeta in sorted(p for p in (BASE / tramo).iterdir() if p.is_dir()):
            vol = carpeta.name
            crudo = (carpeta / f"{vol}.json").read_bytes()
            json.loads(crudo)  # falla si el artefacto está corrupto
            destino = BASE / tramo / f"{vol}.json.gz"
            with gzip.GzipFile(filename=f"{vol}.json", mode="wb", fileobj=open(destino, "wb"), mtime=0) as gz:
                gz.write(crudo)
            assert gzip.decompress(destino.read_bytes()) == crudo
            manifiesto.append({"tramo": tramo, "run": run, "artefacto": f"s143ab-{tramo}-_s142_ab_control-{vol}",
                               "volcan": vol, "sha256_json": hashlib.sha256(crudo).hexdigest(),
                               "bytes_json": len(crudo), "archivo": f"control_s143/{tramo}/{vol}.json.gz"})
            shutil.rmtree(carpeta)
    (BASE / "MANIFIESTO.json").write_text(json.dumps(manifiesto, indent=1, ensure_ascii=False) + "\n",
                                          encoding="utf-8", newline="\n")
    print(f"{len(manifiesto)} records del control congelados en {BASE}")


if __name__ == "__main__":
    main()
