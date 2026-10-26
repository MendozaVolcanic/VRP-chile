# V4-04: publicaciones de K en negativos limpios (SN), 18sep-19oct, por sensor y volcan, y MW del tablero.
# P1: el control nada_publica de a3 da 0; P2: denominador (negativos del estrato) impreso al lado.
import json, collections
M=[json.loads(x) for x in open("main_jul_oct.jsonl",encoding="utf-8")]
c=collections.Counter(); mw=collections.Counter(); n=collections.Counter()
for r in M:
    if r["reg"]!="K" or r.get("lab_SN")!="neg_limpio": continue
    n[(r["b"],r["vol"])]+=1
    if r["pub"]: c[(r["b"],r["vol"])]+=1; mw[(r["b"],r["vol"])]+=r["disp"]
for k in sorted(c): print(k, f"{c[k]}/{n[k]}", round(mw[k],3),"MW")
print("K >= 1 MW en negativos limpios:", [(r["vol"],r["dt"],r["sensor"],r["disp"]) for r in M if r["reg"]=="K" and r.get("lab_SN")=="neg_limpio" and r["pub"] and r["disp"]>=1])
