"""S167: costo en tiempo del NRT y de experimental-diario, por job y por paso del pipeline, desde la API de GitHub.

POR QUÉ: antes de sumar un perfil de sombra hay que saber cuánto margen deja el paso del NRT (timeout 50 min, A15) y
cuánto tarda un workflow diario aparte que descarga y procesa lo mismo (experimental-diario, el molde de la sombra).

Uso: python experiments/_s167_sombra/medir_costo_nrt.py --cache <dir> [--bajar] --csv tiempos_jobs.csv
  --bajar consulta gh api (corridas verdes más recientes: 40 del NRT, 10 de experimental-diario) y guarda el JSON de
  jobs de cada corrida en --cache; sin --bajar lee lo que ya está ahí. El CSV queda como evidencia (la API borra los
  logs a los 90 días).
"""
import argparse
import csv
import glob
import json
import os
import statistics as st
import subprocess
from datetime import datetime

REPO = "MendozaVolcanic/VRP-chile"
FLUJOS = {"nrt.yml": ("NRT", "Run VRP pipeline \u2014 mirova", 40),  # el nombre del paso en nrt.yml
          "experimental-diario.yml": ("experimental-diario", "Run VRP pipeline", 10)}


def _t(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def bajar(cache):
    for wf, (nombre, _, n) in FLUJOS.items():
        os.makedirs(os.path.join(cache, nombre), exist_ok=True)
        ids = subprocess.run(["gh", "run", "list", "-R", REPO, "--workflow", wf, "--limit", str(n), "--json",
                              "databaseId,conclusion", "--jq", '.[]|select(.conclusion=="success")|.databaseId'],
                             capture_output=True, text=True, check=True).stdout.split()
        for r in ids:
            out = subprocess.run(["gh", "api", f"repos/{REPO}/actions/runs/{r}/jobs?per_page=50"],
                                 capture_output=True, text=True, check=True).stdout
            with open(os.path.join(cache, nombre, f"{r}.json"), "w", encoding="utf-8") as f:
                f.write(out)


def q(v, p):
    v = sorted(v)
    return v[min(len(v) - 1, int(p * len(v)))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cache", required=True)
    ap.add_argument("--bajar", action="store_true")
    ap.add_argument("--csv", required=True)
    a = ap.parse_args()
    if a.bajar:
        bajar(a.cache)
    filas = []
    for wf, (nombre, prefijo, _) in FLUJOS.items():
        for f in sorted(glob.glob(os.path.join(a.cache, nombre, "*.json"))):
            for j in json.load(open(f, encoding="utf-8"))["jobs"]:
                if j["conclusion"] != "success" or not j.get("started_at"):
                    continue
                for s in j["steps"]:
                    if s["name"].startswith(prefijo) and s["conclusion"] == "success":
                        filas.append({"flujo": nombre, "run": j["run_id"], "inicio": j["started_at"],
                                      "volcan": j["name"].split("(")[-1].rstrip(")"),
                                      "paso_min": round((_t(s["completed_at"]) - _t(s["started_at"])).total_seconds() / 60, 2),
                                      "job_min": round((_t(j["completed_at"]) - _t(j["started_at"])).total_seconds() / 60, 2)})
    with open(a.csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]))
        w.writeheader()
        w.writerows(filas)
    for nombre in ("NRT", "experimental-diario"):
        fs = [x for x in filas if x["flujo"] == nombre]
        paso, job = [x["paso_min"] for x in fs], [x["job_min"] for x in fs]
        ini = min(x["inicio"] for x in fs)
        fin = max(x["inicio"] for x in fs)
        print(f"{nombre}: {len({x['run'] for x in fs})} corridas, {len(fs)} jobs, jobs iniciados {ini} a {fin}")
        print(f"  paso del pipeline: mediana {st.median(paso):.1f} min, p90 {q(paso, .9):.1f}, máximo {max(paso):.1f}")
        print(f"  job entero:        mediana {st.median(job):.1f} min, p90 {q(job, .9):.1f}, máximo {max(job):.1f}")


if __name__ == "__main__":
    main()
