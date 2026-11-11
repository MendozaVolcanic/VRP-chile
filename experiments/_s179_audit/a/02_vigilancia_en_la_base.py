# -*- coding: utf-8 -*-
"""Re-corre la vigilancia de la guardia K de MODIS sobre la base (main 438a60a1e) y desglosa pasada por pasada.

Codigo y datos: D:\vrp-trabajo\temporales\s179-audit\a\base (extraido con git archive de 438a60a1e,
blobs comparados con git hash-object: 323 archivos de codigo, 0 distintos; sha256 de la referencia igual al declarado).

Las dos preguntas del instrumento:
1. Si la vigilancia estuviera rota, esto lo veria? En parte: reproduce el JSON que el sistema publico y ademas
   lista cada pasada con alerta de MIROVA; un veredicto VERDE con pasadas en que produccion calla se veria en la tabla.
   No prueba la logica de disparo: eso lo hace 04_mutaciones_vigilancia.py.
2. Si este instrumento estuviera muerto, se veria distinto? Si: imprime conteos de records cargados (prod, guardia,
   filas de referencia) y el control positivo: n_pasadas_alerta > 0 y protegidas vistas > 0.
Ventana: la del script (14 dias antes del encendido hasta HOY). HOY fijo = 2026-11-10 (fecha del commit base).
"""
import io, sys, json, os, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = r"D:\vrp-trabajo\temporales\s179-audit\a\base"
sys.path.insert(0, os.path.join(BASE, "scripts")); sys.path.insert(0, BASE)
os.chdir(BASE)
import vigilancia_guardia_modis as vg
assert os.path.normcase(vg.ROOT) == os.path.normcase(BASE), vg.ROOT
HOY = "2026-11-10"
out = vg.evaluar(HOY)
enc = vg.leer_encendido()
print("ROOT:", vg.ROOT)
print("encendido:", out["encendido_modis_utc"], "| primera observacion via:", out["primera_observacion_via"],
      "| flag produccion:", out["flag_produccion"], "| ventana:", out["ventana"])
print("veredicto:", out["veredicto"], "| avisos:", out["avisos"])
print("n_pasadas_alerta:", out["n_pasadas_alerta"], "| con guardia:", out["n_pasadas_alerta_con_guardia"])
for k in ("muy_bajo", "sobrepublicacion"):
    m = out[k]; print(k, "k", m["k"], "n", m["n"], "cota", m["cota"], "dispara", m["dispara"], m["pasadas"])
print("nulo:", {k: out["nulo"][k] for k in ("pares", "distintas", "sin_medir")})
print("borde_171_01:", out["borde_171_01"]["por_semana"], out["borde_171_01"]["pasadas"])
print("duracion:", out["duracion"])
print("caidas_a_k:", out["caidas_a_k"])
print("reversion:", out["reversion"], "| sin_record:", out["protegidas_sin_record_produccion"],
      "| calladas_por_k:", out["protegidas_calladas_por_k_de_produccion"], "| borde_enc:", out["borde_del_encendido"])

# Desglose: mismas funciones, sin tocar nada
win = tuple(out["ventana"])
filas, prod, guardia, n_via_g = vg.cargar_insumos(win, enc["via"], enc.get("caidas"))
print("\nrecords cargados: prod MODIS", len(prod), "| guardia MODIS", len(guardia), "| filas referencia", len(filas),
      "| records de la guardia con marca de via", n_via_g)
pas = vg.pasadas_modis(filas, prod, guardia, win, diurna=vg.vs._diurna_por_defecto())
E = out["encendido_modis_utc"]
print("\nPasadas nocturnas MODIS con alerta de MIROVA en la ventana (todas):")
print("volcan\tfecha_utc\tMW_mirova\tproteg\tprod_pub\tprod_via\tguardia_pub\tlado")
cnt = collections.Counter()
for p in sorted(pas, key=lambda x: x["instante_utc"]):
    lado = "pros" if p["instante_utc"] >= E else "retro"
    print(p["volcano"], p["fecha_utc"], p["vrp_mirova_mw"], p["protegida"], p["prod_pub"], p["prod_via"], p["guardia_pub"], lado, sep="\t")
    if lado == "pros":
        cnt[("alerta", p["volcano"])] += 1
        if p["protegida"]:
            cnt[("protegida", p["volcano"])] += 1
            cnt[("protegida_guardia_pub=%s" % p["guardia_pub"], p["volcano"])] += 1
            cnt[("protegida_prod_pub=%s" % p["prod_pub"], p["volcano"])] += 1
print("\nPosteriores al encendido, por volcan:")
for k in sorted(cnt): print(" ", k, cnt[k])
tot = collections.Counter()
for (k, v), n in cnt.items(): tot[k] += n
print("Totales posteriores al encendido:", dict(tot))

# Records de produccion MODIS posteriores a la primera observacion de la via, por etiqueta y publicacion
po = out["primera_observacion_via"]
c2 = collections.Counter()
for r in prod:
    if r["dt"].strftime("%Y-%m-%d %H:%M") >= po:
        c2[(r.get("lab"), "via" if r.get("via") else ("caida" if r.get("caida_k") else "K"), bool(r["pub"]))] += 1
print("\nProduccion MODIS desde la primera observacion de la via (etiqueta, detector, publica): n")
for k in sorted(c2, key=str): print(" ", k, c2[k])
json.dump({"out": out, "pasadas": pas}, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "02_vigilancia_en_la_base.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1, default=str)
