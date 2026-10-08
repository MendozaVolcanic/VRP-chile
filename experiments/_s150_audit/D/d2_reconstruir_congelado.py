# -*- coding: utf-8 -*-
"""S150 auditor D, sonda 2: se puede RECONSTRUIR la referencia congelada de S149 desde git?

PREGUNTAS DEL INSTRUMENTO
 1. Si la reconstruccion estuviera rota, se veria? Si: comparo sha256 contra el MANIFIESTO de cada mes.
 2. Si la sonda estuviera muerta (siempre "no coincide"), se veria distinto? Control positivo: aplico la
    misma logica al CSV del disco (el congelado mismo, ya recortado) y tiene que reproducir su sha.

Recorre los commits del snapshot del scraper en git (consolidado y OCR) hasta la fecha del congelado y
regenera cada mes con la logica literal de congelar_referencia.py, en memoria.
"""
import csv, hashlib, io, json, subprocess, sys
from datetime import datetime, timedelta
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[3]
CONG = RAIZ / "experiments" / "_s149_prereg_invierno" / "_congelado"
SNAP = "data/mirova_reference/mirova_v1_snapshot/"


def recortar(texto, desde, hasta):
    a = datetime.strptime(desde, "%Y-%m-%d") - timedelta(days=1); b = datetime.strptime(hasta, "%Y-%m-%d") + timedelta(days=2)
    rd = csv.DictReader(io.StringIO(texto.lstrip("﻿"), newline="")); campos = rd.fieldnames
    col = next(c for c in campos if c.startswith("Fecha_Satelite"))
    filas = [r for r in rd if r[col] and a <= datetime.strptime(r[col][:19], "%Y-%m-%d %H:%M:%S") < b]
    out = io.StringIO(newline="")
    w = csv.DictWriter(out, fieldnames=campos, lineterminator="\n"); w.writeheader(); w.writerows(filas)
    return hashlib.sha256(out.getvalue().encode("utf-8")).hexdigest(), len(filas)


def git(*a):
    return subprocess.run(["git", *a], cwd=RAIZ, capture_output=True, check=True).stdout


meses = {d.name: json.loads((d / "MANIFIESTO.json").read_text(encoding="utf-8")) for d in sorted(CONG.iterdir()) if d.is_dir()}
# control positivo: el CSV del disco recortado otra vez da su propio sha
for m, man in meses.items():
    for f, info in man["archivos"].items():
        p = CONG / m / f
        if p.exists():
            sha, n = recortar(p.read_text(encoding="utf-8"), *man["ventana"])
            print("CONTROL POSITIVO %-13s %-30s %s" % (m, f, "reproduce" if sha == info["sha256"] else "NO reproduce"))
        else:
            print("CONTROL POSITIVO %-13s %-30s el archivo NO existe en disco" % (m, f))

for f in ("registro_vrp_consolidado.csv", "registro_vrp_ocr.csv"):
    commits = git("log", "--format=%H %cI", "--until=2026-09-22T00:00:00Z", "-n", "12", "--", SNAP + f).decode().split("\n")
    commits = [c.split() for c in commits if c.strip()]
    for h, fecha in commits:
        texto = git("show", "%s:%s%s" % (h, SNAP, f)).decode("utf-8")
        res = []
        for m, man in meses.items():
            sha, n = recortar(texto, *man["ventana"])
            res.append("%s:%s" % (m, "OK" if sha == man["archivos"][f]["sha256"] else "%d/%d" % (n, man["archivos"][f]["filas"])))
        print(f[:24], h[:9], fecha, " ".join(res))
