import subprocess, json, sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
from datetime import datetime, timezone

def run(cmd):
    return subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8').stdout

commits_raw = run('git log origin/main --oneline --grep="NRT update" -20 --format="%H|%cI|%s"')
rows = [l for l in commits_raw.strip().split("\n") if l]

results = []
for row in rows:
    h, cdate, subj = row.split("|", 2)
    stat = run(f'git show --stat --format="" {h}')
    # find data/*/<Vol>.json path
    paths = [l.strip().split(" ")[0] for l in stat.strip().split("\n") if l.strip().startswith("data/") and ".json" in l]
    if not paths:
        continue
    path = paths[0]
    content = run(f'git show {h}:{path}')
    try:
        d = json.loads(content)
    except Exception as e:
        results.append((subj, cdate, None, f"ERROR parse: {e}"))
        continue
    records = d.get("records", [])
    if not records:
        results.append((subj, cdate, None, "sin records"))
        continue
    max_dt = max(r["datetime_utc"] for r in records if "datetime_utc" in r)
    commit_dt = datetime.fromisoformat(cdate)
    rec_dt = datetime.fromisoformat(max_dt.replace("Z","+00:00"))
    if rec_dt.tzinfo is None:
        rec_dt = rec_dt.replace(tzinfo=timezone.utc)
    lag_min = (commit_dt - rec_dt).total_seconds()/60
    results.append((subj, cdate, max_dt, lag_min))

print(f"{'commit':45s} {'commit_time':22s} {'max_dt_record':22s} {'lag_min':>10s}")
lags = []
for subj, cdate, maxdt, lag in results:
    if isinstance(lag, float):
        lags.append(lag)
        print(f"{subj:45s} {cdate:22s} {str(maxdt):22s} {lag:10.1f}")
    else:
        print(f"{subj:45s} {cdate:22s} {str(maxdt):22s} {str(lag):>10s}")

if lags:
    lags_sorted = sorted(lags)
    n = len(lags_sorted)
    def pct(p):
        idx = min(n-1, int(round(p*(n-1))))
        return lags_sorted[idx]
    print(f"\nn={n}  p50={pct(0.5):.1f} min  p90={pct(0.9):.1f} min  max={max(lags_sorted):.1f} min  min={min(lags_sorted):.1f} min")
