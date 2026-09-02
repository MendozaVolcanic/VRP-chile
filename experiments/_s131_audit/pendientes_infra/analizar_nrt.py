import json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from datetime import datetime, timezone

runs = json.load(open("experiments/_s131_audit/pendientes_infra/nrt_runs.json", encoding="utf-8"))
now = datetime(2026,9,2,20,8,43, tzinfo=timezone.utc)

def parse(s):
    return datetime.fromisoformat(s.replace("Z","+00:00"))

completed = [r for r in runs if r["status"]=="completed"]
last7 = [r for r in completed if (now - parse(r["createdAt"])).days < 7]
print(f"Total runs traidos: {len(runs)}")
print(f"Completados: {len(completed)}")
print(f"Ultimos 7 dias (completados): {len(last7)}")

ok = [r for r in last7 if r["conclusion"]=="success"]
fail = [r for r in last7 if r["conclusion"] not in ("success",)]
print(f"Exito ultimos 7d: {len(ok)}/{len(last7)} = {100*len(ok)/len(last7):.1f}%")
print("Conclusiones no-success:", [ (r['conclusion'], r['createdAt']) for r in fail])

durs = []
for r in completed:
    d = (parse(r["updatedAt"]) - parse(r["createdAt"])).total_seconds()/60
    durs.append((d, r["createdAt"], r["conclusion"]))
durs_sorted = sorted(durs)
n = len(durs_sorted)
med = durs_sorted[n//2][0]
mx = max(durs_sorted)
print(f"\nDuracion (min) sobre {n} runs completados en la ventana de 40:")
print(f"  mediana: {med:.1f} min")
print(f"  maxima: {mx[0]:.1f} min ({mx[1]}, conclusion={mx[2]})")
print(f"  top 5:", [(round(d,1), c) for d,ts,c in durs_sorted[-5:]])
