"""v2: refina ramas.json cruzando cada rama con sus PRs (gh api pulls?head=...&state=all).
Una rama PENDIENTE por diff pero con PR MERGED es INTEGRADA_POR_PR (main la modifico despues: falso pendiente).
Sin PR o con PR abierto/cerrado-sin-merge y diff no vacio: PENDIENTE_REAL.
P1: si una rama con trabajo real sin PR existiera, quedaria PENDIENTE_REAL. Si.
P2: si gh fallara, se marca ERROR_GH (no se confunde con "sin PR"). Denominador: ramas remotas sin HEAD/main."""
import json, subprocess, sys, io
from collections import Counter
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
out = json.load(open("experiments/_s138_audit/eje6/ramas.json", encoding="utf-8"))
print("estados v1:", Counter(o["state"] for o in out))
for o in out:
    if o["state"] != "PENDIENTE":
        o["pr"] = None; o["state2"] = o["state"]; continue
    b = o["branch"].replace("origin/", "")
    p = subprocess.run(["gh", "api", f"repos/MendozaVolcanic/VRP-chile/pulls?head=MendozaVolcanic:{b}&state=all&per_page=5",
                        "--jq", "[.[] | {n: .number, merged: (.merged_at != null), state: .state}]"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if p.returncode != 0:
        o["pr"] = "ERROR_GH"; o["state2"] = "ERROR_GH"; continue
    prs = json.loads(p.stdout or "[]")
    o["pr"] = prs
    if any(x["merged"] for x in prs): o["state2"] = "INTEGRADA_POR_PR"
    elif any(x["state"] == "open" for x in prs): o["state2"] = "PR_ABIERTO"
    elif prs: o["state2"] = "PR_CERRADO_SIN_MERGE"
    else: o["state2"] = "PENDIENTE_REAL"
json.dump(out, open("experiments/_s138_audit/eje6/ramas.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False)
print("estados v2:", Counter(o["state2"] for o in out))
for st in ("PENDIENTE_REAL", "PR_ABIERTO", "PR_CERRADO_SIN_MERGE", "ERROR_GH"):
    xs = [o for o in out if o["state2"] == st]
    if xs:
        print(f"\n{st} ({len(xs)}): rama | fecha | archivos distintos de main (sin data/)")
        for o in sorted(xs, key=lambda o: o["date"]):
            print(f"  {o['branch']} | {o['date']} | {len(o['pending'])}: {', '.join(o['pending'][:5])} | pr={o['pr']}")
