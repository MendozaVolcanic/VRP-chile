# -*- coding: utf-8 -*-
"""I-07. Que pasadas nuestras NO tienen fila en la referencia, y si esa ausencia es al azar.

Si la tabla de MIROVA omitiera pasadas de forma ligada al estado termico (por ejemplo solo las
frias, o solo las de angulo alto), los negativos limpios serian una muestra sesgada.
P1: si la ausencia dependiera del angulo, la hora o de si publicamos, las tasas por estrato difieren.
P2: el total de pasadas sin fila debe coincidir con `sin_info(sin fila)` de i05 (556).
"""
import sys, io, json, collections
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
A = Path(__file__).parent
RECS = json.load(open(A / "_cache_recs.json", encoding="utf-8"))
REF = [f for f in json.load(open(A / "_cache_ref.json", encoding="utf-8")) if not f["diurna"]]
claves = {(f["volcano"], f["sensor_bucket"], f["fecha_utc"][:16]) for f in REF}
ult = max(f["fecha_utc"] for f in REF if f["source"] == "CONS")[:16]
for r in RECS:
    r["con_fila"] = (r["vol"], r["b"], r["dt"][:16].replace("T", " ")) in claves
    r["tarde"] = r["dt"][:16].replace("T", " ") > ult
print("pasadas sin fila:", sum(1 for r in RECS if not r["con_fila"]), "| de ellas posteriores a la ultima fila de la tabla:", sum(1 for r in RECS if not r["con_fila"] and r["tarde"]))
R = [r for r in RECS if not r["tarde"]]


def tabla(nombre, clave):
    c = collections.defaultdict(lambda: [0, 0])
    for r in R:
        k = clave(r)
        c[k][1] += 1
        c[k][0] += r["con_fila"]
    print(f"\n{nombre}: con fila / total")
    for k in sorted(c, key=str):
        print(f"   {str(k):28s} {c[k][0]:4d}/{c[k][1]:4d} = {100 * c[k][0] / c[k][1]:5.1f}%")


tabla("por plataforma", lambda r: r["sensor"])
tabla("SNPP I-band por fecha", lambda r: r["dt"][:10] if r["sensor"] == "VIIRS_SNPP" else "(otras)")
tabla("SNPP I-band por hora UTC", lambda r: r["dt"][11:13] if r["sensor"] == "VIIRS_SNPP" else "(otras)")


def zb(z):
    return "z?" if z is None else "z<30" if z < 30 else "z30-50" if z < 50 else "z50-60" if z < 60 else "z>=60"


tabla("VIIRS I-band por angulo cenital", lambda r: zb(r["z"]) if r["b"] == "VIIRS375" else "(otras)")
tabla("VIIRS I-band segun si publicamos", lambda r: ("publica" if r["pub"] else "no publica") if r["b"] == "VIIRS375" else "(otras)")
tabla("VIIRS I-band por version de producto nuestra", lambda r: str(r["pv"]) if r["b"] == "VIIRS375" else "(otras)")
tabla("VIIRS I-band por volcan", lambda r: r["vol"] if r["b"] == "VIIRS375" else "(otras)")
