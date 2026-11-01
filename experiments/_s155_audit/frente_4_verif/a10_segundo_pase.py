# F4-10/V4-02: publicaciones con el primer pase vacio (solo recaptura del segundo pase, D2), pareado C0 tag vs K main
# 18sep-17oct. P1: si el segundo pase no publicara nada solo, daria 0 en los dos. P2: diag None aparte.
import json, collections
L=lambda f:[json.loads(x) for x in open(f,encoding="utf-8")]
M={(r["vol"],r["dt"],r["sensor"]):r for r in L("main_jul_oct.jsonl")}
c=collections.Counter()
for t in L("tag_c0_ventana.jsonl"):
    if t["noche"]>"2026-10-17": continue
    m=M.get((t["vol"],t["dt"],t["sensor"]))
    if not m or m["reg"]!="K": continue
    for nom,r in (("C0",t),("K",m)):
        if not r["pub"]: continue
        fp=r["diag_n_first_pass_pixels"]; rc=r["diag_n_second_pass_recapture"]
        if fp is None or rc is None: c[(nom,r["b"],"diag_none")]+=1; continue
        c[(nom,r["b"],"pub")]+=1
        solo = fp==0 and rc>0 and not r["triggered_test1"]
        if solo: c[(nom,r["b"],"pub_solo_2pase")]+=1
        if solo and r.get("lab_SN")=="neg_limpio": c[(nom,r["b"],"pub_solo_2pase_neg")]+=1
        if solo and r.get("lab_SN")=="pos": c[(nom,r["b"],"pub_solo_2pase_pos")]+=1
for k in sorted(c): print(k,c[k])
