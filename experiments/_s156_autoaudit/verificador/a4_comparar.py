import json
mine = json.load(open("a4_out.json", encoding="utf-8"))
aut = json.load(open("../out/latest.json", encoding="utf-8"))["alertas_protegidas"]["lista"]
def est(f):
    c = [c for c in f["cand"] if abs(c["dsec"]) <= 120]
    return "sin_record" if not c else ("publicada" if any(x["pub"] for x in c) else "sin_publicar")
m = {(f["vol"], f["b"], f["minuto"]): (est(f), round(f["vrp_max"], 3)) for f in mine if f["elev_sol"] < 0}
a = {(p["volcano"], p["sensor"], p["fecha_utc"]): (p["estado"], p["vrp_mirova_mw"]) for p in aut}
print("nocturnas mias:", len(m), " autor:", len(a))
print("solo mias:", sorted(set(m) - set(a)))
print("solo autor:", sorted(set(a) - set(m)))
print("distinto estado/vrp:", [(k, m[k], a[k]) for k in set(m) & set(a) if m[k] != a[k]])
print("diurnas mias (excluidas):", sum(1 for f in mine if f["elev_sol"] >= 0), " min |elev| nocturna:", min(-f["elev_sol"] for f in mine if f["elev_sol"] < 0))
