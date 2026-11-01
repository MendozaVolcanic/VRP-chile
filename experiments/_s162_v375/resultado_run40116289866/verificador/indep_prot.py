import io, sys, json, collections
from pathlib import Path
exec(open(Path(__file__).with_name("indep_decision.py"), encoding="utf-8").read().split("rows162 = ")[0].replace("sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=\"utf-8\")", "pass"))
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
print("\n== protegidas que C13 / M14 no publican")
for x in rows:
    if x["c"] == "pos_prot" and (not x["pub"]["C13"] or not x["pub"]["M14"]):
        o = obj[x["i"]]
        print(x["lote"], x["vol"], x["hora"], "sensor", o["sensor"], "tabla", o["alerta_tabla"], "K", x["K"], "M14", x["pub"]["M14"], "C13", x["pub"]["C13"],
              "mirova", [(m["vrp_mw"], m["dist_km"], m["source"], m["tipo"]) for m in o["mirova"]][:3], "z", o["z"])
print("\nprotegidas totales", sum(1 for x in rows if x["c"]=="pos_prot"), " tabla:", sum(1 for x in rows if x["c"]=="pos_prot" and obj[x["i"]]["alerta_tabla"]))
# recall bajo
W = pesos(rows)
import math
def wil(k,n,z=1.96):
    p=k/n; d=1+z*z/n; c=(p+z*z/(2*n))/d; h=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/d; return c-h,c+h
for b in ("M14","C13","K"):
    bajo=[x for x in rows if x["c"]=="pos_bajo"]
    w=np.array([W[id(x)] for x in bajo]); k=np.array([(x["K"] if b=="K" else x["pub"][b]) for x in bajo],float)
    p=(w*k).sum()/w.sum(); ne=w.sum()**2/(w**2).sum(); print(b,"recall bajo pond",round(p,4),"IC",[round(v,4) for v in wil(p*ne,ne)],"ne",round(ne,1),"crudo",int(k.sum()),len(bajo))
# bajo C13 que K no publica y viceversa
print("bajo: K publica y C13 no:", sum(1 for x in rows if x["c"]=="pos_bajo" and x["K"] and not x["pub"]["C13"]), "| C13 y K no:", sum(1 for x in rows if x["c"]=="pos_bajo" and not x["K"] and x["pub"]["C13"]))
# pesos neg_resto rango
w=[W[id(x)] for x in rows if x["c"]=="neg_resto"]; print("pesos neg_resto min/max", min(w), max(w))
w=[W[id(x)] for x in rows if x["c"]=="pos_bajo"]; print("pesos pos_bajo min/max", min(w), max(w))
