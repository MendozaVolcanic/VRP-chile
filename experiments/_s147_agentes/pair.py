import sys, json, collections, datetime as dt
sys.path.insert(0,'.')
from common import *

TOL_MIN = 8
def build():
    recs = {v: [r for r in records(v) if is_iband(r.get("sensor",""))] for v in set(TIF2OURS.values())}
    out=[]
    for tr in tif_rows("VIIRS375"):
        vo = TIF2OURS[tr["volcano"]]
        best=None
        for r in recs[vo]:
            d = abs((r["_t"]-tr["_t"]).total_seconds())/60
            if best is None or d < best[0]: best=(d,r)
        out.append(dict(tif=tr["_abs"], rel=tr["tif_path"], vol=tr["volcano"], ours_vol=vo,
                        t_tif=tr["_t"].isoformat(), tsrc=tr["_tsrc"], md5=tr["md5"],
                        dmin=None if best is None else round(best[0],1),
                        rec=None if best is None or best[0]>TOL_MIN else best[1]))
    return out
if __name__=="__main__":
    p=build()
    ok=[x for x in p if x["rec"]]
    print("TIF VIIRS375 unicos:", len(p), "| pareados con record nuestro (<=%dmin):"%TOL_MIN, len(ok))
    print("delta minutos de los pareados:", collections.Counter(x["dmin"] for x in ok).most_common(10))
    print("sin pareo, delta mas chico:", sorted(x["dmin"] for x in p if not x["rec"])[:15])
    json.dump([{k:v for k,v in x.items() if k!="rec"} | {"zen": x["rec"]["sensor_zenith_deg"] if x["rec"] else None,
               "dt_rec": x["rec"]["datetime_utc"] if x["rec"] else None,
               "sensor": x["rec"]["sensor"] if x["rec"] else None} for x in p], open("pares.json","w"), indent=0)
