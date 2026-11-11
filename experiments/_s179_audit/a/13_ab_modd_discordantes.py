# -*- coding: utf-8 -*-
"""El A/B de MOD-D que sostuvo la adopcion: veredicto, composicion por volcan y los discordantes que dan las cotas D1 y D2.
Fuente: git show origin/claude/s170-modd-f4-procedencia:experiments/_s168/modd_f4_candado/lectura_ab2/resultado_f4.json
(copia en D:\vrp-trabajo\temporales\s179-audit\a\resultado_f4.json). Control: su sha256 tiene que empezar por
312e2050c680, el prefijo que cita la regla sellada (seccion 4.4 i)."""
import io, sys, json, hashlib, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
P = r"D:\vrp-trabajo\temporales\s179-audit\a\resultado_f4.json"
raw = open(P, "rb").read()
print("sha256:", hashlib.sha256(raw).hexdigest(), "| empieza por 312e2050c680:", hashlib.sha256(raw).hexdigest().startswith("312e2050c680"))
d = json.loads(raw.decode("utf-8"))
V = d["brazos"]["V"]
print("veredicto:", d["veredicto"], "| controles en OK:", sum(1 for c in d["controles"].values() if c.get("estado") == "OK"), "de", len(d["controles"]))
print("P1:", V["p1"]["estado"], "| P2:", V["p2"]["estado"], "neto", V["p2"]["neto"], "B", V["p2"]["B"], "| M:", V["m"]["regla"], "n", V["m"]["n"])
print("P2 por tramo:", d["por_tramo"])
print("razon en protegidas:", V["razon_protegidas"])
print("M por volcan (n):", {k: v["n"] for k, v in V["m"]["dprima"]["g_hat_por_volcan"].items()})
c = collections.Counter((x["lab"], x["c"]) for x in V["p2"]["discordantes"])
print("discordantes (etiqueta, c): c=+1 es error solo de la via, c=-1 error solo de K ->", dict(c))
cv = collections.Counter((x["vol"], x["lab"], x["c"]) for x in V["p2"]["discordantes"])
for k in sorted(cv): print("   ", k, cv[k])
print("Chillan por tramo de cenit (protegidas, publica K, publica la via):", {k: (v["protegidas"], v["pub_K"], v["pub_b"]) for k, v in d["chillan_por_tramo"].items()})
