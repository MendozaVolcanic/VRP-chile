import json,sys
for path in ["data/experimental_v2/PuyehueCordonCaulle.json","data/mirova_equivalent/PuyehueCordonCaulle.json"]:
    recs=json.load(open(path,encoding="utf-8"))["records"]
    for r in recs:
        dt=r.get("datetime_utc","")
        if dt.startswith("2026-10-10 05:"):
            r2={k:v for k,v in r.items() if k!="anomaly_pixels"}
            print("=====",path,r["sensor"],dt)
            print(json.dumps(r2,ensure_ascii=False))
            for p in r.get("anomaly_pixels") or []:
                print("  px",p)
