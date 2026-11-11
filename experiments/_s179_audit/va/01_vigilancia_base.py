# -*- coding: utf-8 -*-
"""VA-01: re-corre la vigilancia de la guardia K de MODIS sobre MI base (git archive de 438a60a1e, sin autocrlf,
347 blobs de código comparados con git hash-object: 0 distintos; sha256 de la referencia igual al declarado).

Preguntas del instrumento:
1. Si la vigilancia estuviera rota, ¿esto lo vería? Sólo en parte: reproduce el veredicto y lista las pasadas. La lógica
   de disparo se prueba aparte con casos sintéticos (02_casos_sinteticos.py).
2. Si este instrumento estuviera muerto, ¿se vería distinto? Sí: imprime cuántos records y filas cargó; control positivo:
   tiene que haber pasadas con alerta y protegidas posteriores al encendido (Chillán en erupción).
Ventana: la del script (14 días antes del encendido hasta HOY). HOY = 2026-11-10 (día del commit base).
Además: (a) ritmo de protegidas MODIS nocturnas de MIROVA por mes desde 2026-03 (otro estrato que el del auditor);
(b) potencia del plazo de 29 si la guardia sólo publica una fracción de las protegidas.
"""
import io, sys, os, json, collections
from datetime import datetime, timezone, date, timedelta
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = r"D:\vrp-trabajo\temporales\s179-audit\va\base"
sys.path.insert(0, os.path.join(BASE, "scripts")); sys.path.insert(0, BASE)
os.chdir(BASE)
import vigilancia_guardia_modis as vg
assert os.path.normcase(vg.ROOT) == os.path.normcase(BASE), vg.ROOT
HOY = "2026-11-10"
out = vg.evaluar(HOY)
print("ROOT", vg.ROOT)
print("veredicto", out["veredicto"], "| fase", out["fase"], "| avisos", out["avisos"])
print("encendido", out["encendido_modis_utc"], "| primera obs via", out["primera_observacion_via"], "| flag", out["flag_produccion"], "| ventana", out["ventana"])
print("duracion", out["duracion"])
print("nulo", {k: out["nulo"][k] for k in ("pares", "distintas", "sin_medir")})
print("n_pasadas_alerta", out["n_pasadas_alerta"], "| con guardia", out["n_pasadas_alerta_con_guardia"])
print("protegidas_sin_publicar_produccion (l. 538):", [(p["volcano"], p["fecha_utc"]) for p in out["protegidas_sin_publicar_produccion"]])
E = out["encendido_modis_utc"]
enc = vg.leer_encendido()
win = tuple(out["ventana"])
filas, prod, guardia, n_via_g = vg.cargar_insumos(win, enc["via"], enc.get("caidas"))
print("cargados: prod MODIS", len(prod), "guardia MODIS", len(guardia), "filas ref", len(filas))
pas = vg.pasadas_modis(filas, prod, guardia, win, diurna=vg.vs._diurna_por_defecto())
pros = [p for p in pas if p["instante_utc"] >= E]
print("\nposteriores al encendido (volcan, fecha, MW, protegida, prod_pub, prod_via, guardia_pub):")
for p in sorted(pros, key=lambda x: x["instante_utc"]):
    print(" ", p["volcano"], p["fecha_utc"], p["vrp_mirova_mw"], p["protegida"], p["prod_pub"], p["prod_via"], p["guardia_pub"])
prot = [p for p in pros if p["protegida"]]
c = collections.Counter((p["guardia_pub"], p["prod_pub"]) for p in prot)
print("protegidas posteriores:", len(prot), "| volcanes:", dict(collections.Counter(p["volcano"] for p in prot)))
print("(guardia_pub, prod_pub) ->", dict(c))
mws = sorted(p["vrp_mirova_mw"] for p in prot)
print("MW de MIROVA de las protegidas posteriores (orden):", mws)

# (a) ritmo por mes de protegidas MODIS nocturnas de MIROVA, mismo predicado que la vigilancia
import clase_mirova as cm
diurna = vg.vs._diurna_por_defecto()
vistos, mes, mesvol = set(), collections.Counter(), collections.defaultdict(collections.Counter)
for f in filas:
    if f.get("sensor_bucket") != "MODIS" or not cm.alerta_protegida(f):
        continue
    if not (f["fecha_utc"][:7] >= "2026-03"):
        continue
    k = cm.clave_pasada(f)
    if k in vistos:
        continue
    vistos.add(k)
    dt = datetime.fromisoformat(f["fecha_utc"][:19]).replace(tzinfo=timezone.utc)
    if diurna("MODIS", f["volcano"], dt):
        continue
    mes[f["fecha_utc"][:7]] += 1
    mesvol[f["fecha_utc"][:7]][f["volcano"]] += 1
print("\nprotegidas MODIS nocturnas de MIROVA por mes (referencia del repo en 438a60a1e; noviembre hasta el 10):")
for m in sorted(mes):
    print(" ", m, mes[m], dict(mesvol[m]))
tot_sin_ch = sum(n for m in mes for v, n in mesvol[m].items() if v != "NevadosDeChillan" and m < "2026-11")
tot_ch = sum(n for m in mes for v, n in mesvol[m].items() if v == "NevadosDeChillan" and m < "2026-11")
dias = (date(2026, 10, 31) - date(2026, 3, 1)).days + 1
print(f"mar a oct ({dias} dias): sin Chillan {tot_sin_ch} ({tot_sin_ch/dias*120:.1f} en 120 dias); Chillan {tot_ch}")

# (b) potencia: con una perdida de la via de 1 de cada 10, la vigilancia sólo la ve si K publica esa protegida
for frac in (1.0, 8/11):
    pot = 1 - (1 - 0.1 * frac) ** 29
    print(f"potencia con 29 protegidas, perdida 10 %, K publica {frac:.2f}: {pot:.3f}")
json.dump({"out": out, "pasadas": pas}, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "01_vigilancia_base.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
