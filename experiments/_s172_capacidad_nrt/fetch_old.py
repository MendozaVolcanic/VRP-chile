import json,subprocess,os
from concurrent.futures import ThreadPoolExecutor
r=json.load(open('runs_old.json'))
r=[x for x in r if x['createdAt']<'2026-06-05T00:00:00Z' and x['conclusion'] in ('success','failure')]
def go(x):
    f=f"jobs_old/{x['databaseId']}.json"
    if os.path.exists(f): return
    out=subprocess.run(['gh','run','view',str(x['databaseId']),'--repo','MendozaVolcanic/VRP-chile','--json','jobs,createdAt,startedAt,updatedAt,event,conclusion'],capture_output=True,text=True,encoding='utf-8').stdout
    open(f,'w',encoding='utf-8').write(out)
with ThreadPoolExecutor(6) as ex: list(ex.map(go,r))
print(len(r))
