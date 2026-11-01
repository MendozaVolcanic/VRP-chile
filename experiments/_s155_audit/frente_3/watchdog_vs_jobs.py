"""F3: ¿el criterio 'colgada' del reproc-watchdog (edad del RUN > 7 h desde created_at) mide un job colgado?
Lee por gh api (sólo lectura) los jobs del run y compara: edad del run vs duración máxima de un job vs
techo de 6 h por JOB. P1: si un job estuviera colgado, su duración superaría 6 h y se vería. P2: si la API
no devuelve jobs, imprime n = 0 (SIN DATO), no 'sano'. Control: el run de A/B S146 38648773684 (que sí
reportó 'queued' 21-25 h; se mide igual)."""
import json, subprocess, sys
from datetime import datetime, timezone
sys.stdout.reconfigure(encoding="utf-8")
def api(path):
    out = subprocess.run(["gh", "api", "--paginate", path], capture_output=True, text=True, check=True).stdout
    # --paginate concatena objetos JSON; separar
    objs, dec, i = [], json.JSONDecoder(), 0
    out = out.strip()
    while i < len(out):
        o, j = dec.raw_decode(out, i); objs.append(o); i = j
        while i < len(out) and out[i].isspace(): i += 1
    return objs
P = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00")) if s else None
now = datetime.now(timezone.utc)
for rid in sys.argv[1:]:
    run = api(f"repos/MendozaVolcanic/VRP-chile/actions/runs/{rid}")[0]
    jobs = [j for o in api(f"repos/MendozaVolcanic/VRP-chile/actions/runs/{rid}/jobs?per_page=100") for j in o["jobs"]]
    durs, estados = [], {}
    for j in jobs:
        estados[j["status"]] = estados.get(j["status"], 0) + 1
        s, e = P(j.get("started_at")), P(j.get("completed_at"))
        if s and j["status"] != "queued":
            durs.append(((e or now) - s).total_seconds() / 3600)
    edad = (now - P(run["created_at"])).total_seconds() / 3600
    print(f"run {rid} status={run['status']} conclusion={run['conclusion']} edad_run_h={edad:.1f} "
          f"n_jobs={len(jobs)} estados={estados} job_max_h={max(durs) if durs else 'SIN DATO':.2f} "
          f"jobs>6h={sum(d > 6 for d in durs)} watchdog_diria_colgada={run['status'] != 'completed' and edad > 7}")
