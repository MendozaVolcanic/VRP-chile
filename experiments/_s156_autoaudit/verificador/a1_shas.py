import json, os, sys, subprocess
from collections import defaultdict
W = sys.argv[1]
VOLS = ["Lascar","Lastarria","Isluga","Llaima","Villarrica","Chaiten","Tupungatito","Copahue","PlanchonPeteroa","PuyehueCordonCaulle","NevadosDeChillan"]
rng = defaultdict(lambda: ["9", "0", 0, set()])
for v in VOLS:
    for r in json.load(open(os.path.join(W, "data/mirova_equivalent", v + ".json"), encoding="utf-8"))["records"]:
        sha = (r.get("regimen") or {}).get("codigo_sha")
        if not sha: continue
        x = rng[sha]; dt = r["datetime_utc"]
        x[0] = min(x[0], dt); x[1] = max(x[1], dt); x[2] += 1; x[3].add(r.get("sensor"))
for sha, (a, b, n, ss) in sorted(rng.items(), key=lambda kv: kv[1][0]):
    cd = subprocess.run(["git", "-C", W, "log", "-1", "--format=%ci %s", sha], capture_output=True, text=True, encoding="utf-8").stdout.strip()[:90]
    prof = subprocess.run(["git", "-C", W, "show", f"{sha}:pipeline/profiles/mirova_equivalent.yaml"], capture_output=True, text=True, encoding="utf-8").stdout
    flags = [l.strip() for l in prof.splitlines() if any(k in l for k in ("enable_test1_path:", "enable_tests_23_prose_branch:", "enable_modis_b22_primary:"))]
    print(sha[:8], n, a, "->", b, sorted(ss)[:3], "|", cd, "|", flags)
