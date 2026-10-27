# -*- coding: utf-8 -*-
"""S165: baja la copia de HOY de la referencia de MIROVA (consolidado y OCR de Mirova-v1, fijados a su sha) a
D:\\vrp-trabajo\\temporales\\s165_regla_posicion\\ref y deja la procedencia. Sólo lectura sobre el repo.

POR QUÉ. El consolidado ganó 2.648 filas hoy a las 12:41 UTC (D-39): los censos se etiquetaron con copias anteriores,
pero el cotejo de distancias se hace con la de hoy, y hay que poder decir cuál se usó (sha del commit, fecha y sha256).
Uso: python referencia.py  (escribe referencia_salida.txt)
"""
import io
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
import comun as C  # noqa: E402
from referencia_mirova_unificada import REPO_MIROVA, RUTA_REMOTA, bajar_remoto, cargar_referencia_unificada  # noqa

L = []


def pr(*x):
    s = " ".join(str(v) for v in x)
    L.append(s)
    print(s, flush=True)


info = bajar_remoto(C.REF_DIR)
proc = {"bajado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
for nombre, d in info.items():
    fecha = subprocess.run(["gh", "api", f"repos/{REPO_MIROVA}/commits/{d['sha']}", "-q", ".commit.committer.date"],
                           capture_output=True, text=True).stdout.strip()
    n = sum(1 for _ in open(d["path"], encoding="utf-8")) - 1
    proc[nombre] = {"sha_commit": d["sha"], "fecha_commit": fecha, "sha256": C.sha256(d["path"]), "filas": n,
                    "ruta": d["path"], "url": f"https://github.com/{REPO_MIROVA}/blob/{d['sha']}/{RUTA_REMOTA}/{nombre}"}
(C.REF_DIR / "procedencia.json").write_text(json.dumps(proc, indent=1, ensure_ascii=False), encoding="utf-8")
pr(json.dumps(proc, indent=1, ensure_ascii=False))
filas = cargar_referencia_unificada(C.REF_DIR / "registro_vrp_consolidado.csv", C.REF_DIR / "registro_vrp_ocr.csv")
import collections  # noqa: E402
pr("unión cargada:", len(filas), "filas;", dict(collections.Counter((f["source"], f["origen"]) for f in filas)))
pr("con Distancia_km y VRP > 0:", dict(collections.Counter(
    (f["source"], f["sensor_bucket"]) for f in filas if f["dist_km"] is not None and (f["vrp_mw"] or 0) > 0)))
Path(C.AQUI / "referencia_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")
