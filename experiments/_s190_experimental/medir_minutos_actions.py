# -*- coding: utf-8 -*-
"""S190: minutos de Actions por workflow y concurrencia, para el plan de reactivar `experimental`.

POR QUE. El plan tiene que decir cuanto cuesta el laboratorio frente al NRT y las tandas que ya ocupan
runners. El repo es publico: los minutos de runners estandar no se cobran, el limite real es la cantidad de
jobs simultaneos de la cuenta. Por eso mide dos cosas: minutos-job por workflow y el pico de jobs a la vez.

Uso: python experiments/_s190_experimental/medir_minutos_actions.py [dias]   (por defecto 7)
Lee la API con `gh` (sin credenciales propias). Escribe salida_minutos_actions.json junto al script.
"""
import json, subprocess, sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = "MendozaVolcanic/VRP-chile"
DIAS = int(sys.argv[1]) if len(sys.argv) > 1 else 7


def gh(path):
    out = subprocess.run(["gh", "api", "--paginate", path], capture_output=True, text=True, encoding="utf-8", check=True).stdout
    # --paginate concatena objetos JSON; se separan a mano
    dec, i, objs = json.JSONDecoder(), 0, []
    while i < len(out):
        while i < len(out) and out[i].isspace():
            i += 1
        if i >= len(out):
            break
        o, i = dec.raw_decode(out, i)
        objs.append(o)
    return objs


def t(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


ahora = datetime.now(timezone.utc)
desde = ahora - timedelta(days=DIAS)
runs = []
for page in gh(f"repos/{REPO}/actions/runs?per_page=100&created=>={desde:%Y-%m-%dT%H:%M:%SZ}"):
    runs += page["workflow_runs"]

por_wf = defaultdict(lambda: {"runs": 0, "jobs": 0, "min_job": 0.0})
intervalos = []
errores = []
for r in runs:
    if r["status"] != "completed":
        continue
    w = por_wf[r["name"]]
    w["runs"] += 1
    try:
        paginas = gh(f"repos/{REPO}/actions/runs/{r['id']}/jobs?per_page=100")
    except subprocess.CalledProcessError:
        errores.append(r["id"])  # se informa: un run sin jobs leidos no cuenta como cero minutos
        continue
    for page in paginas:
        for j in page["jobs"]:
            if not j.get("started_at") or not j.get("completed_at"):
                continue
            a, b = t(j["started_at"]), t(j["completed_at"])
            if b <= a:
                continue
            w["jobs"] += 1
            w["min_job"] += (b - a).total_seconds() / 60
            intervalos.append((a, b, r["name"]))

# pico de jobs simultaneos (todos los workflows) y cuanto pesa cada uno en ese pico
eventos = sorted([(a, 1) for a, _, _ in intervalos] + [(b, -1) for _, b, _ in intervalos])
vivo = pico = 0
for _, d in eventos:
    vivo += d
    pico = max(pico, vivo)

salida = {
    "ventana": {"desde": desde.isoformat(), "hasta": ahora.isoformat(), "dias": DIAS},
    "pico_jobs_simultaneos": pico,
    "runs_sin_jobs_legibles": errores,
    "por_workflow": {k: {"runs": v["runs"], "jobs": v["jobs"], "min_job": round(v["min_job"]),
                         "min_job_por_dia": round(v["min_job"] / DIAS)}
                     for k, v in sorted(por_wf.items(), key=lambda kv: -kv[1]["min_job"])},
}
salida["total_min_job_por_dia"] = round(sum(v["min_job"] for v in por_wf.values()) / DIAS)
Path(__file__).with_name("salida_minutos_actions.json").write_text(json.dumps(salida, ensure_ascii=False, indent=1), encoding="utf-8")
print(json.dumps({"pico": pico, "errores": len(errores), "total_dia": salida["total_min_job_por_dia"],
                  "top": {k: v["min_job_por_dia"] for k, v in list(salida["por_workflow"].items())[:10]}}, ensure_ascii=False))
