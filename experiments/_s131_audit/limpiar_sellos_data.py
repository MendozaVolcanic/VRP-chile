# -*- coding: utf-8 -*-
"""S131 - Higiene del dato publicado: dos invariantes rotos por reprocesos parciales.

NO EJECUTADO en S131: queda como propuesta para el OK de Nicolas (A38). Antes de correrlo:
    git tag -a pre-s131-data-hygiene -m "snapshot defensivo" && git push origin pre-s131-data-hygiene
Reversible con `git checkout pre-s131-data-hygiene -- data/mirova_equivalent/`.

POR QUE. `store.py:99-103` escribe `diag_vrp_floor_mw` y `vrp_mw = 0.0` JUNTOS: el sello
significa "el piso actuo y la magnitud quedo en cero". El reproceso de S130 (piso retirado)
restauro la magnitud y dejo el sello pegado en 1.635 records: una auditoria futura leeria
"el piso piso 1.635 records" y seria falso (A87 + A90). Se quita el sello donde vrp_mw > 0.

Segundo: `vrp_tir_mw` (TIRVolcH/Aveni) esta apagado en el perfil operacional
(`ENABLE_VRP_TIR_OUTPUT = False`) y el README declara el campo publicado en 0; quedan 28
records de abril-2026 (18 volcanes fuera del cron NRT) con valor > 0, uno de 4.817 MW — la
clase de outlier que motivo apagarlo. Se ponen en 0.0.

Los guards que miden ambos invariantes (hoy xfail strict, quitar el xfail al limpiar):
tests/test_guard_declarado_vs_efectivo_s131.py G3 / G7.
"""
import glob
import io
import json
import os
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def main(dry_run=True):
    sellos = tir = tot = archivos = 0
    for p in sorted(glob.glob(os.path.join(ROOT, "data", "mirova_equivalent", "*.json"))):
        raw = open(p, encoding="utf-8").read()
        d = json.loads(raw)
        recs = d.get("records", d)
        cambio = False
        for r in recs:
            tot += 1
            if r.get("diag_vrp_floor_mw") is not None and (r.get("vrp_mw") or 0) > 0:
                r["diag_vrp_floor_mw"] = None
                sellos += 1
                cambio = True
            if (r.get("vrp_tir_mw") or 0) > 0:
                r["vrp_tir_mw"] = 0.0
                tir += 1
                cambio = True
        if cambio and not dry_run:
            with open(p, "w", encoding="utf-8", newline="\n") as f:
                json.dump(d, f, indent=2, ensure_ascii=False)
                if raw.endswith("\n"):
                    f.write("\n")
            archivos += 1
    modo = "DRY-RUN (sin escribir)" if dry_run else "ESCRITO"
    print(f"{modo} | records: {tot} | sellos de piso a quitar: {sellos} | vrp_tir_mw -> 0: {tir} | archivos: {archivos}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(dry_run="--apply" not in sys.argv))
