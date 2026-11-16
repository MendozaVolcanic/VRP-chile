# Pregunta 1: si MODIS de produccion no corriera por la via, el conteo de via_codigo_mirova=true lo veria? Si (seria 0).
# Pregunta 2: si el instrumento estuviera muerto (no lee records), el resultado seria 0 y 0 records; se imprime el total para distinguir.
# Control positivo: total de records MODIS > 0. Ventana: lo que contenga Lascar.json en 752d348bc, 8 fechas por corrida.
import json,subprocess,sys,collections
raw=subprocess.run(["git","show","752d348bc:data/mirova_equivalent/Lascar.json"],capture_output=True,check=True).stdout
d=json.loads(raw)
recs=d if isinstance(d,list) else d.get("records",d)
print(type(d).__name__, len(recs))
c=collections.Counter(); mx=None
for r in recs:
    if not isinstance(r,dict): continue
    s=str(r.get("sensor",""))
    if "MODIS" in s.upper():
        c[(s,r.get("via_codigo_mirova"),r.get("via_marca") or r.get("via_codigo_mirova_marca"))]+=1
        t=r.get("acq_utc") or r.get("datetime_utc") or r.get("time_utc") or r.get("processed_utc")
        mx=max(mx,str(t)) if mx else str(t)
print("records MODIS:",sum(c.values()),"ultimo:",mx)
for k,v in sorted(c.items(),key=lambda kv:-kv[1])[:12]: print(k,v)
print("claves ejemplo:",sorted(recs[-1].keys())[:40] if isinstance(recs[-1],dict) else None)
