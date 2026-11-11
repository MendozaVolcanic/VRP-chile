# -*- coding: utf-8 -*-
"""Corridas del NRT (nrt.yml) desde el merge de #934 y en que paso fallaron las rojas.
Fuente: GitHub API, 6 llamadas el 2026-11-11 ~00:50 UTC (gh run list; gh run view de 4 corridas; un log).
Para que: la regla (seccion 4.4 a) agrego el paso «Revisar errores de MODIS en el log», que deja rojo el job si la via
lanza una excepcion. Aqui se mira si ese paso fallo alguna vez. Limite: solo se abrieron 4 de las 8 corridas rojas."""
import io, sys, json, os, collections, glob
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
H = os.path.dirname(os.path.abspath(__file__))
d = json.load(open(os.path.join(H, "14_api_runs_nrt.json"), encoding="utf-8"))
print("corridas listadas:", len(d), "de", min(r["createdAt"] for r in d), "a", max(r["createdAt"] for r in d))
post = [r for r in d if r["createdAt"] >= "2026-11-02T17:18:17Z"]
pre = [r for r in d if r["createdAt"] < "2026-11-02T17:18:17Z"]
print("antes del merge:", len(pre), dict(collections.Counter(r["conclusion"] for r in pre)))
print("desde el merge :", len(post), dict(collections.Counter(r["conclusion"] for r in post)))
for r in sorted(post, key=lambda x: x["createdAt"]):
    if r["conclusion"] == "failure": print("   roja:", r["createdAt"], r["databaseId"])
for f in sorted(glob.glob(os.path.join(H, "14_api_run_*.json"))):
    j = json.load(open(f, encoding="utf-8"))["jobs"]
    for job in j:
        if job.get("conclusion") not in ("success", "skipped"):
            print("  ", os.path.basename(f), job["name"], "| paso que falla:", [s["name"] for s in job.get("steps", []) if s.get("conclusion") not in ("success", "skipped")])
log = open(os.path.join(H, "14_api_log_nrt_42016780200_copahue.txt"), encoding="utf-8", errors="replace").read()
print("log de Copahue en 42016780200: FileExistsError", log.count("FileExistsError"), "veces | linea del paso de MODIS:",
      [l.split("Z ", 1)[-1] for l in log.splitlines() if "con ERROR processing" in l][:1], "| timeout:", "has timed out after 50 minutes" in log)
