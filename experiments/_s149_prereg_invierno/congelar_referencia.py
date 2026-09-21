# -*- coding: utf-8 -*-
"""S149. Congela la referencia de MIROVA de una ventana: recorta los dos CSV del snapshot del scraper a
[desde - 1 dia, hasta + 2 dias] y los deja en _congelado/<nombre>/ con su manifiesto (sha256, filas,
fecha del snapshot). POR QUE: una referencia viva mueve el denominador sola (A90), y el scraper
re-edita filas viejas (el OCR cambio de version el 2026-08-06). La referencia congelada de S146 esta
recortada a septiembre y no sirve para otra ventana (verificador del pre-registro, H5)."""
import csv, hashlib, json, sys
from datetime import datetime, timedelta
from pathlib import Path
AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[1]
SNAP = RAIZ / "data" / "mirova_reference" / "mirova_v1_snapshot"
nombre, desde, hasta = sys.argv[1:4]
a = datetime.strptime(desde, "%Y-%m-%d") - timedelta(days=1); b = datetime.strptime(hasta, "%Y-%m-%d") + timedelta(days=2)
out = AQUI / "_congelado" / nombre; out.mkdir(parents=True, exist_ok=True); man = {"ventana": [desde, hasta], "archivos": {}}
for f in ("registro_vrp_consolidado.csv", "registro_vrp_ocr.csv"):
    with open(SNAP / f, encoding="utf-8-sig", newline="") as fh:
        rd = csv.DictReader(fh); campos = rd.fieldnames
        col = next(c for c in campos if c.startswith("Fecha_Satelite"))
        filas = [r for r in rd if r[col] and a <= datetime.strptime(r[col][:19], "%Y-%m-%d %H:%M:%S") < b]
    with open(out / f, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos, lineterminator="\n"); w.writeheader(); w.writerows(filas)
    man["archivos"][f] = {"filas": len(filas), "sha256": hashlib.sha256((out / f).read_bytes()).hexdigest()}
(out / "MANIFIESTO.json").write_text(json.dumps(man, indent=1), encoding="utf-8")
print(nombre, {k: v["filas"] for k, v in man["archivos"].items()})
