# -*- coding: utf-8 -*-
"""V4T, instrumento 4: inventario propio (no el TSV del auditor) de los workflows de 752d348bc que pasan el par
EARTHDATA_USERNAME/PASSWORD, si tienen cron, y si cortan con token vacío antes de correr Python.

Las dos preguntas del instrumento:
1. Si un workflow con el par y sin guarda existiera, ¿se vería? Sí: se lista por nombre con su línea.
2. Si el lector estuviera muerto (YAML que no parsea, patrón que no calza), ¿se vería distinto? Se cuentan los
   archivos leídos y los que no parsean; CONTROL POSITIVO: nrt.yml tiene que salir con guarda=True y cron=True
   (S160, l. 190-193), y CONTROL NEGATIVO: pages-deploy.yml sin el par.
La «guarda» se detecta por el texto `-z "$EARTHDATA_TOKEN"` seguido de `exit 1` en las 4 líneas siguientes, y se
cuenta por paso: un workflow con dos pasos que usan el par y sólo uno con guarda sale como parcial.
"""
from __future__ import annotations

import csv
import io
import re
import sys
from pathlib import Path

import yaml

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
WF = Path(r"C:\Users\nmend\vrp-temporales\s175_audit\v4t\repo_base\.github\workflows")
OUT = Path(__file__).with_name("salida_04_inventario.csv")
filas, no_parsea = [], []
for f in sorted(WF.glob("*.yml")):
    txt = f.read_text(encoding="utf-8")
    try:
        d = yaml.safe_load(txt)
    except Exception as e:  # noqa: BLE001
        no_parsea.append((f.name, str(e)[:80]))
        continue
    on = d.get("on", d.get(True)) or {}
    if isinstance(on, str):
        on = {on: None}
    elif isinstance(on, list):
        on = {k: None for k in on}
    cron = "schedule" in on
    dispatch = "workflow_dispatch" in on
    pasos_par, pasos_par_guardados = 0, 0
    for job in (d.get("jobs") or {}).values():
        for st in (job.get("steps") or []):
            env = st.get("env") or {}
            env_job = job.get("env") or {}
            usa_par = any("EARTHDATA_USERNAME" in str(v) or "EARTHDATA_PASSWORD" in str(v)
                          for v in list(env.values()) + list(env_job.values()))
            if not usa_par:
                continue
            pasos_par += 1
            run = st.get("run") or ""
            lineas = run.splitlines()
            guard = False
            for i, l in enumerate(lineas):
                if re.search(r'-z\s+"\$\{?EARTHDATA_TOKEN', l) and any("exit 1" in x for x in lineas[i:i + 5]):
                    guard = True
            pasos_par_guardados += guard
    usa_par_txt = bool(re.search(r"secrets\.EARTHDATA_(USERNAME|PASSWORD)", txt))
    filas.append({"workflow": f.name, "cron": cron, "dispatch": dispatch, "pasos_con_par": pasos_par,
                  "pasos_con_par_y_guarda": pasos_par_guardados, "par_en_texto": usa_par_txt,
                  "usa_run_pipeline": "run_pipeline.py" in txt})
with OUT.open("w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(filas[0]))
    w.writeheader()
    w.writerows(filas)
print(f"workflows leídos: {len(filas) + len(no_parsea)}; no parsean: {no_parsea}")
ctl = {r["workflow"]: r for r in filas}
print("CONTROL+ nrt.yml:", ctl.get("nrt.yml"))
print("CONTROL- pages-deploy.yml:", ctl.get("pages-deploy.yml"))
sin = [r for r in filas if r["pasos_con_par"] > 0 and r["pasos_con_par_y_guarda"] < r["pasos_con_par"]]
print(f"con el par en algún paso y algún paso sin guarda: {len(sin)}")
for r in sin:
    print(f"  {r['workflow']}: cron={r['cron']} dispatch={r['dispatch']} pasos_par={r['pasos_con_par']} "
          f"guardados={r['pasos_con_par_y_guarda']} run_pipeline={r['usa_run_pipeline']}")
print(f"  de ellos con cron: {sum(r['cron'] for r in sin)}; sólo despacho: {sum((not r['cron']) for r in sin)}")
txt_sin_env = [r["workflow"] for r in filas if r["par_en_texto"] and r["pasos_con_par"] == 0]
print(f"par en el texto pero no en env de un paso (otro mecanismo, revisar a mano): {txt_sin_env}")
