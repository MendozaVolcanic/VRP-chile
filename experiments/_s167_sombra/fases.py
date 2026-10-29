import re,sys
from datetime import datetime
ts=lambda l: datetime.fromisoformat(l[:26]+"+00:00") if re.match(r"\d{4}-\d\d-\d\dT",l) else None
lines=open(sys.argv[1],encoding="utf-8",errors="replace").read().splitlines()
days=[];cur=None
for l in lines:
    t=ts(l)
    if t is None: continue
    if "AUTH_START" in l:
        if cur: days.append(cur)
        cur={"ini":t,"last_dl":t,"end":t}
    elif cur:
        if "DOWNLOAD_DONE" in l or "SEARCH_" in l or "DOWNLOAD_START" in l: cur["last_dl"]=t
        if "Cleaned up" in l: cur["end"]=t; days.append(cur); cur=None
if cur: days.append(cur)
tb=tp=0
for d in days:
    b=(d["last_dl"]-d["ini"]).total_seconds(); p=(d["end"]-d["last_dl"]).total_seconds(); tb+=b;tp+=p
print(f"{len(days)} dias  busqueda+descarga {tb/60:.1f} min  proceso {tp/60:.1f} min")
