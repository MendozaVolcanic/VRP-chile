# -*- coding: utf-8 -*-
"""S150. Congela la referencia de MIROVA para la prueba de Nevados de Chillan, bajandola del repo
Mirova-v1 (la fuente del dueño), no del snapshot local de VRP Chile.

POR QUE: el 2026-10-08 el snapshot local (data/mirova_reference/mirova_v1_snapshot/) tenia su ultimo commit
el 2026-10-05, asi que le faltaban los ultimos dias de la erupcion. (Corregido S150, auditor A: ese snapshot
solo lo actualiza la auditoria semanal; la sincronizacion horaria no estaba detenida.) La referencia es del
remoto del dueño (feedback S139). Misma logica de recorte y manifiesto que
experiments/_s149_prereg_invierno/congelar_referencia.py: [desde - 1 dia, hasta + 2 dias], sha256, filas,
y ademas la hora de descarga y el commit de Mirova-v1 del que salio.

Uso: python congelar_desde_remoto.py <nombre> <desde> <hasta>
"""
import csv, hashlib, io, json, subprocess, sys, urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
URL = "https://raw.githubusercontent.com/MendozaVolcanic/Mirova-v1/{sha}/monitoreo_satelital/{f}"
nombre, desde, hasta = sys.argv[1:4]
sha = subprocess.run(["gh", "api", "repos/MendozaVolcanic/Mirova-v1/commits/main", "-q", ".sha"],
                     capture_output=True, text=True, check=True).stdout.strip()
a = datetime.strptime(desde, "%Y-%m-%d") - timedelta(days=1)
b = datetime.strptime(hasta, "%Y-%m-%d") + timedelta(days=2)
out = AQUI / ("_congelado_" + nombre); out.mkdir(parents=True, exist_ok=True)
man = {"ventana": [desde, hasta], "fuente": "MendozaVolcanic/Mirova-v1@" + sha,
       "descargado_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "archivos": {}}
for f in ("registro_vrp_consolidado.csv", "registro_vrp_ocr.csv"):
    texto = urllib.request.urlopen(URL.format(sha=sha, f=f), timeout=120).read().decode("utf-8-sig")
    rd = csv.DictReader(io.StringIO(texto)); campos = rd.fieldnames
    col = next(c for c in campos if c.startswith("Fecha_Satelite"))
    filas = [r for r in rd if r[col] and a <= datetime.strptime(r[col][:19], "%Y-%m-%d %H:%M:%S") < b]
    with open(out / f, "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=campos, lineterminator="\n"); w.writeheader(); w.writerows(filas)
    man["archivos"][f] = {"filas": len(filas), "sha256": hashlib.sha256((out / f).read_bytes()).hexdigest()}
(out / "MANIFIESTO.json").write_text(json.dumps(man, indent=1), encoding="utf-8")
print(nombre, man["fuente"], {k: v["filas"] for k, v in man["archivos"].items()})
