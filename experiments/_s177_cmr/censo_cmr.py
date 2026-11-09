"""S177: censo de cortes de CMR contra la carga propia en GitHub Actions.

POR QUE: el bloque S177 deja como SOSPECHA que nuestro reproceso (6 trabajos paralelos) aporte a los cortes de CMR
del 2026-11-08. La sospecha decide si D3 y D4 se despachan como estan. Antes de creerla o descartarla hay que poner
en la misma tabla, hora por hora, cuantas busquedas hicimos, cuantas fallaron y que estaba corriendo. Lee solo la API
de GitHub (metadatos y logs); ninguna llamada a NASA.

Salida (carpeta --out): jobs.jsonl (un trabajo por linea) y eventos.jsonl (una marca [diag] de busqueda por linea).

Uso: python experiments/_s177_cmr/censo_cmr.py --desde 2026-11-01 --out C:/Users/nmend/vrp-temporales/s177_cmr
"""
import argparse
import concurrent.futures as cf
import io
import json
import pathlib
import re
import subprocess
import sys
import zipfile

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)

REPO = "MendozaVolcanic/VRP-chile"
WORKFLOWS = ["nrt.yml", "sombra-34.yml", "sombra-codigo-mirova.yml", "guardia-k-modis.yml", "guardia-k-viirs.yml",
             "experimental-diario.yml", "reproc-retro-paquete.yml"]
# Solo lineas emitidas por _diag(): el resumen de cobertura repite los nombres y contaria doble (A92).
RE_EVENTO = re.compile(
    r"^(\S+Z) .*?\[diag \d\d:\d\d:\d\dZ\] "
    r"(SEARCH_CMR_TIMEOUT|SEARCH_VENTANA_ERR|SEARCH_VENTANA_OFF|SEARCH_VENTANA_TRUNCADA|SEARCH_VENTANA|SEARCH_SKIP"
    r"|SEARCH_START|SEARCH_DONE)(?![A-Z_])(.*)$")


def gh(path, binary=False):
    p = subprocess.run(["gh", "api", "-H", "Accept: application/vnd.github+json", path], capture_output=True)
    if p.returncode != 0:
        return None
    return p.stdout if binary else json.loads(p.stdout.decode("utf-8"))


def paginado(path, clave):
    fuera, page = [], 1
    while True:
        sep = "&" if "?" in path else "?"
        d = gh(f"{path}{sep}per_page=100&page={page}")
        if d is None or not d.get(clave):
            return fuera
        fuera.extend(d[clave])
        if len(d[clave]) < 100:
            return fuera
        page += 1


def eventos_de_texto(texto, base):
    fuera = []
    for linea in texto.splitlines():
        m = RE_EVENTO.match(linea.lstrip("\ufeff"))
        if m:
            fuera.append({**base, "ts": m.group(1)[:19] + "Z", "ev": m.group(2), "txt": m.group(3).strip()[:220]})
    return fuera


def procesar(wf, run, n):
    rid = run["id"]
    jobs = paginado(f"repos/{REPO}/actions/runs/{rid}/attempts/{n}/jobs", "jobs")
    filas = [{"wf": wf, "run": rid, "attempt": n, "job": j["id"], "name": j["name"], "started": j.get("started_at"),
              "completed": j.get("completed_at"), "status": j["status"], "conclusion": j.get("conclusion")} for j in jobs]
    evs = []
    sin_log = 0
    if wf == "reproc-retro-paquete.yml":
        # Con el run en curso el zip no existe: se pide el log de cada trabajo terminado.
        for j in jobs:
            if j["status"] != "completed":
                continue
            b = gh(f"repos/{REPO}/actions/jobs/{j['id']}/logs", binary=True)
            if b is None:
                sin_log += 1
                continue
            evs += eventos_de_texto(b.decode("utf-8", "replace"), {"wf": wf, "run": rid, "attempt": n, "name": j["name"]})
    else:
        b = gh(f"repos/{REPO}/actions/runs/{rid}/attempts/{n}/logs", binary=True)
        if b is None:
            sin_log += 1
        else:
            z = zipfile.ZipFile(io.BytesIO(b))
            nombres = z.namelist()
            # El zip trae un .txt por trabajo en la raiz y ademas carpetas por paso: leer solo una de las dos vistas.
            raiz = [x for x in nombres if "/" not in x and x.endswith(".txt")]
            for x in (raiz or [y for y in nombres if y.endswith(".txt")]):
                nombre = re.sub(r"^\d+_", "", x).removesuffix(".txt")
                evs += eventos_de_texto(z.read(x).decode("utf-8", "replace"),
                                        {"wf": wf, "run": rid, "attempt": n, "name": nombre})
    return filas, evs, sin_log


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    tareas = []
    for wf in WORKFLOWS:
        runs = paginado(f"repos/{REPO}/actions/workflows/{wf}/runs?created=%3E%3D{a.desde}", "workflow_runs")
        print(f"{wf}: {len(runs)} corridas", flush=True)
        for r in runs:
            for n in range(1, int(r.get("run_attempt") or 1) + 1):
                tareas.append((wf, r, n))
    print(f"intentos a leer: {len(tareas)}", flush=True)
    vistos, jobs_total, ev_total, sin_log, hechos = set(), 0, 0, 0, 0
    with open(out / "jobs.jsonl", "w", encoding="utf-8") as fj, open(out / "eventos.jsonl", "w", encoding="utf-8") as fe:
        with cf.ThreadPoolExecutor(max_workers=4) as ex:
            for filas, evs, sl in ex.map(lambda t: procesar(*t), tareas):
                for f in filas:
                    fj.write(json.dumps(f, ensure_ascii=False) + "\n")
                jobs_total += len(filas)
                sin_log += sl
                for e in evs:
                    # Un rerun --failed vuelve a listar los trabajos verdes: la misma linea no cuenta dos veces.
                    k = (e["run"], e["name"], e["ts"], e["ev"], e["txt"])
                    if k not in vistos:
                        vistos.add(k)
                        fe.write(json.dumps(e, ensure_ascii=False) + "\n")
                        ev_total += 1
                hechos += 1
                if hechos % 25 == 0:
                    print(f"{hechos}/{len(tareas)} jobs={jobs_total} eventos={ev_total} sin_log={sin_log}", flush=True)
    print(f"FIN intentos={len(tareas)} jobs={jobs_total} eventos={ev_total} sin_log={sin_log}", flush=True)


if __name__ == "__main__":
    main()
