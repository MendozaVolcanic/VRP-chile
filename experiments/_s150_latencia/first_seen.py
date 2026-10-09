# Primera aparicion de cada (sensor, datetime_utc) en el historial git de data/mirova_equivalent/<V>.json
import json, subprocess, sys, time
import os; REPO=os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))  # S150: antes ruta fija
SINCE="2026-09-13"
def keys_at(sha, path):
    raw=subprocess.run(["git","-C",REPO,"show",f"{sha}:{path}"],capture_output=True).stdout
    d=json.loads(raw)
    return {(r.get('sensor'),r.get('datetime_utc')):(r.get('vrp_mw') or 0, r.get('distance_class'), r.get('product_version')) for r in d['records']}
out=[]
for v in sys.argv[1:]:
    t0=time.time(); path=f"data/mirova_equivalent/{v}.json"
    log=subprocess.run(["git","-C",REPO,"log","--reverse","--format=%H %cI %an",f"--since={SINCE}","--",path],capture_output=True,text=True).stdout.split("\n")
    log=[l.split(" ",2) for l in log if l.strip()]
    base=subprocess.run(["git","-C",REPO,"rev-list","-1",f"--before={SINCE}","HEAD","--",path],capture_output=True,text=True).stdout.strip()
    seen=set(keys_at(base,path))
    n=0
    for sha,ci,an in log:
        k=keys_at(sha,path)
        for key,val in k.items():
            if key not in seen:
                seen.add(key); n+=1
                out.append(dict(v=v,sensor=key[0],acq=key[1],first_commit=ci,author=an,sha=sha[:9],vrp=val[0],dc=val[1],pv=val[2]))
    print(v,len(log),"commits",n,"new keys",round(time.time()-t0),"s",flush=True)
json.dump(out,open(f"first_seen_{'_'.join(sys.argv[1:])}.json","w"))
