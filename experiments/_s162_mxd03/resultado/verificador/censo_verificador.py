# -*- coding: utf-8 -*-
"""Verificador con contexto limpio (S162, resultado del A/B MxD03): censo INDEPENDIENTE de los artefactos.

No importa evaluar_mxd03.py: recuenta por su cuenta, con codigo propio y mas simple, lo que R1 a R4 afirman,
cruzando las filas crudas de los jsonl contra poblacion.json del tag. Si la cifra del autor y la mia coinciden,
coinciden dos codigos distintos; si no, uno de los dos esta mal y hay que mirar cual.

Las dos preguntas del instrumento, por bloque, van impresas en la salida.

Uso: python -I censo_verificador.py <carpeta con los ab_parte*.jsonl> <poblacion.json> > censo_verificador_salida.txt
"""
import collections
import glob
import json
import math
import statistics
import sys
from pathlib import Path

ART = Path(sys.argv[1])
POB = Path(sys.argv[2])
NULOS = ["R%02d" % k for k in range(20)]
CC = "PuyehueCordonCaulle"


def dist_km(a, b):
    if not a or not b or a.get("pc_lat") is None or b.get("pc_lat") is None:
        return None
    dn = (a["pc_lat"] - b["pc_lat"]) * 111.32
    de = (a["pc_lon"] - b["pc_lon"]) * 111.32 * math.cos(math.radians(a["pc_lat"]))
    return math.hypot(dn, de)


pob = json.load(open(POB, encoding="utf-8"))
pobf = {}
for g in pob["granulos"]:
    for f in g["records"]:
        pobf.setdefault((f["vol"], f["dt"]), []).append(dict(f, clave_g=g["clave"]))
dup_pob = [k for k, v in pobf.items() if len(v) > 1]
print("== POBLACION (tag): records", sum(len(v) for v in pobf.values()), "claves (vol,dt) unicas", len(pobf),
      "duplicadas en poblacion", len(dup_pob), "| granulos", len(pob["granulos"]), "| partes", len(pob["partes"]),
      "| checkout", pob["checkout"], "| ventana", pob["ventana"], "| tol_s", pob.get("tol_s"), "| cenit_r", pob.get("cenit_r"))
pobf = {k: v[0] for k, v in pobf.items()}
parte_de_clave = {c: i for i, p in enumerate(pob["partes"]) for c in p}
print("   granulos asignados a partes:", len(parte_de_clave), "| suma records por parte:",
      sum(len(g["records"]) for g in pob["granulos"]))
lab_pob = collections.Counter(f["lab"] for f in pobf.values())
print("   etiquetas poblacion:", dict(sorted(lab_pob.items())), "| K publica (pub_guardada) por etiqueta:",
      dict(sorted(collections.Counter((f["lab"], f["pub_guardada"]) for f in pobf.values()).items())))
print("   r_nulos True:", sum(f["r_nulos"] for f in pobf.values()), "| z<=35:",
      sum(1 for f in pobf.values() if f["z"] is not None and f["z"] <= 35), "| z None:",
      sum(1 for f in pobf.values() if f["z"] is None))

# ---------------------------------------------------------------- filas crudas
cab, rec, pie, otros = [], [], [], []
archivo_de = {}
for p in sorted(glob.glob(str(ART / "**" / "ab_parte*.jsonl"), recursive=True)):
    nombre_parte = int(Path(p).stem.replace("ab_parte", ""))
    for i, l in enumerate(open(p, encoding="utf-8")):
        d = json.loads(l)
        d["_archivo_parte"] = nombre_parte
        t = d.get("tipo")
        (cab if t == "cabecera" else rec if t == "record" else pie if t == "pie" else otros).append(d)
print("\n== ARTEFACTOS: archivos", len(set(d["_archivo_parte"] for d in cab)), "cabeceras", len(cab), "records", len(rec),
      "pies", len(pie), "otros", len(otros))
print("   partes en cabeceras:", sorted(c["parte"] for c in cab))
print("   cabecera.parte == nombre de archivo en todas:", all(c["parte"] == c["_archivo_parte"] for c in cab))
print("   commits en cabeceras:", sorted({c["commit"] for c in cab}))
print("   refs (ramas) en cabeceras:", dict(collections.Counter(c["ref"] for c in cab)))
print("   poblacion_checkout en cabeceras:", sorted({c["poblacion_checkout"] for c in cab}))
print("   referencia sha256 cons/ocr en cabeceras:", sorted({(c["referencia"]["registro_vrp_consolidado.csv"]["sha256_lf"][:12],
                                                             c["referencia"]["registro_vrp_ocr.csv"]["sha256_lf"][:12]) for c in cab}))
print("   sal:", sorted({c["sal"] for c in cab}), "k_nulos:", sorted({c["k_nulos"] for c in cab}),
      "flag_DISTANCE_CLASS_FROM_CLUSTER:", sorted({c["flag_ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER"] for c in cab}),
      "flag_B22_PRIMARY:", sorted({c["flag_ENABLE_MODIS_B22_PRIMARY"] for c in cab}))
print("   sha256 frontend/index.html en cabeceras:", sorted({c["sha256_frontend_index"][:16] for c in cab}))
print("   n_granulos declarados por parte (suma):", sum(c["n_granulos"] for c in cab), "| esperado por poblacion:",
      sum(len(p) for p in pob["partes"]))
print("   pies: errores", [p["errores"] for p in pie], "| minutos min/max", min(p["minutos"] for p in pie), max(p["minutos"] for p in pie))

# ---------------------------------------------------------------- cobertura clave por clave (camino 1)
est = collections.Counter(r.get("estado") for r in rec)
print("\n== COBERTURA. estados:", dict(est))
claves = collections.Counter((r["vol"], r["dt"]) for r in rec)
dup = [k for k, n in claves.items() if n > 1]
print("   (vol,dt) unicas en artefactos:", len(claves), "| repetidas:", len(dup), dup[:5])
faltan = [k for k in pobf if k not in claves]
sobran = [k for k in claves if k not in pobf]
print("   en poblacion y no en artefactos:", len(faltan), faltan[:5], "| en artefactos y no en poblacion:", len(sobran), sobran[:5])
mal_parte = [(r["vol"], r["dt"]) for r in rec if parte_de_clave.get(r["clave"]) != r["_archivo_parte"]]
print("   records escritos en una parte distinta de la asignada en poblacion.partes:", len(mal_parte), mal_parte[:5])
mal_clave = [(r["vol"], r["dt"]) for r in rec if pobf.get((r["vol"], r["dt"]), {}).get("clave_g") != r["clave"]]
print("   records cuya clave de granulo no es la de la poblacion:", len(mal_clave), mal_clave[:5])
# consistencia de campos repetidos por el arnes contra la poblacion (camino: union)
dif_campos = collections.Counter()
for r in rec:
    pf = pobf.get((r["vol"], r["dt"]))
    if pf and r.get("estado") == "ok":
        for k in ("lab", "z", "r_nulos", "sensor", "tramo", "lado", "inner"):
            if r.get(k) != pf.get(k):
                dif_campos[k] += 1
print("   campos del arnes distintos de la poblacion (lab/z/r_nulos/sensor/tramo/lado/inner):", dict(dif_campos) or "ninguno")

ok = [dict(pobf[(r["vol"], r["dt"])], **{k: v for k, v in r.items() if k not in pobf[(r["vol"], r["dt"])]})
      for r in rec if r.get("estado") == "ok" and (r["vol"], r["dt"]) in pobf]
# OJO: aqui la POBLACION manda en los campos compartidos (igual que el evaluador); los dif_campos de arriba miden si importa
print("   filas ok unidas a la poblacion:", len(ok))

# ---------------------------------------------------------------- brazos presentes y None (camino 4, 29)
nones = collections.Counter()
falta_brazo = collections.Counter()
for f in ok:
    esperados = ["K", "K2", "X"] + (NULOS if f["r_nulos"] else [])
    for b in esperados:
        if b not in f["brazos"]:
            falta_brazo[b] += 1
        elif f["brazos"][b] is None:
            nones[b] += 1
        if b not in f["pub"]:
            falta_brazo["pub:" + b] += 1
    extra = set(f["brazos"]) - set(esperados)
    if extra:
        falta_brazo["brazos_de_mas"] += 1
print("\n== BRAZOS. brazos esperados ausentes:", dict(falta_brazo) or "ninguno")
print("   records con brazo None (calculate_vrp devolvio None) por brazo:", dict(sorted(nones.items())) or "ninguno")
print("   records con K None y X no None:", sum(1 for f in ok if f["brazos"]["K"] is None and f["brazos"]["X"] is not None),
      "| X None y K no None:", sum(1 for f in ok if f["brazos"]["X"] is None and f["brazos"]["K"] is not None))
print("   r_nulos True y z>35 o None:", sum(1 for f in ok if f["r_nulos"] and (f["z"] is None or f["z"] > 35)),
      "| r_nulos False y z<=35:", sum(1 for f in ok if not f["r_nulos"] and f["z"] is not None and f["z"] <= 35))
print("   n_fill_mxd03 > 0:", sum(1 for f in ok if (f.get("n_fill_mxd03") or 0) > 0), "| max:", max((f.get("n_fill_mxd03") or 0) for f in ok))

# ---------------------------------------------------------------- K2, control 4 (caminos 5, 6, 7)
print("\n== K2 = K: k2_igual True", sum(1 for f in ok if f.get("k2_igual") is True), "False", sum(1 for f in ok if f.get("k2_igual") is False),
      "None", sum(1 for f in ok if f.get("k2_igual") is None))
# que compara k2_igual: registros_iguales (json entero salvo marcas de hora). Repito a mano sobre el resumen:
dif_k2_resumen = sum(1 for f in ok if json.dumps(f["brazos"]["K"], sort_keys=True) != json.dumps(f["brazos"]["K2"], sort_keys=True))
print("   resumen K != resumen K2 (pc_vrp, pc_lat, dc, n_anom...):", dif_k2_resumen, "| pub K != pub K2:", sum(1 for f in ok if f["pub"]["K"] != f["pub"]["K2"]))
kd = collections.Counter((bool(f.get("decide")), bool(f.get("k_difiere_de_guardado"))) for f in ok)
print("   (decide, k_difiere_de_guardado):", dict(kd))
print("   retenido_para_sha:", sum(1 for f in ok if f.get("retenido_para_sha")))
# mi propia comparacion K del arnes contra data/ (pub y pc_vrp a 0,001), sin pasar por el campo del arnes
mio = 0
detalle_dif = collections.Counter()
for f in ok:
    k = f["brazos"]["K"] or {}
    a, b = k.get("pc_vrp"), f.get("pc_vrp_guardada")
    d = (f["pub"]["K"] != f["pub_guardada"]) or ((a is None) != (b is None)) or (a is not None and abs(a - b) > 0.001)
    mio += d
    if d:
        detalle_dif[("pub" if f["pub"]["K"] != f["pub_guardada"] else "vrp", f["lab"], (f.get("codigo_sha") or "?")[:9])] += 1
print("   K del arnes difiere de data/ (recalculo mio):", mio, "| por (motivo, lab, sha):", dict(detalle_dif))
print("   dc K del arnes != dc_guardada:", sum(1 for f in ok if (f["brazos"]["K"] or {}).get("dc") != f.get("dc_guardada")))
por_sha = collections.Counter((f.get("codigo_sha") or "?")[:9] for f in ok)
print("   codigo_sha de los records:", dict(por_sha.most_common()))

# ---------------------------------------------------------------- X realmente se aplica (caminos 12, 14, 29)
hk = sum(1 for f in ok if f["hash_grilla"]["X"] == f["hash_grilla"]["K"])
print("\n== X SE APLICA. hash X == hash K:", hk, "de", len(ok))
desp = [f["desplazamiento"]["km"] for f in ok]
print("   desplazamiento en el crater (km): min %.3f mediana %.3f p90 %.3f max %.3f | <=0,01 km: %d" % (
    min(desp), statistics.median(desp), sorted(desp)[int(0.9 * len(desp))], max(desp), sum(1 for d in desp if d <= 0.01)))
con_pc = [f for f in ok if (f["brazos"]["K"] or {}).get("pc_lat") is not None and (f["brazos"]["X"] or {}).get("pc_lat") is not None]
mov = [dist_km(f["brazos"]["K"], f["brazos"]["X"]) for f in con_pc]
print("   records con cumulo en K y en X:", len(con_pc), "| de ellos movidos >0,01 km:", sum(1 for d in mov if d > 0.01),
      "| movidos <=0,01 km:", sum(1 for d in mov if d <= 0.01))
print("   records con cumulo solo en K:", sum(1 for f in ok if (f["brazos"]["K"] or {}).get("pc_lat") is not None and (f["brazos"]["X"] or {}).get("pc_lat") is None),
      "| solo en X:", sum(1 for f in ok if (f["brazos"]["K"] or {}).get("pc_lat") is None and (f["brazos"]["X"] or {}).get("pc_lat") is not None))
if mov:
    print("   movimiento del cumulo K->X (km): mediana %.3f max %.3f" % (statistics.median(mov), max(mov)))
# control positivo: X difiere de K en algo
dif_x = sum(1 for f in ok if json.dumps(f["brazos"]["K"], sort_keys=True) != json.dumps(f["brazos"]["X"], sort_keys=True))
print("   resumen X != resumen K (cualquier campo):", dif_x, "| pub X != pub K:", sum(1 for f in ok if f["pub"]["K"] != f["pub"]["X"]))
print("   atribucion presente:", sum(1 for f in ok if f.get("atribucion")), "| identidades XF=K / XD=X:",
      collections.Counter((f["atribucion"].get("XF_id_igual_K"), f["atribucion"].get("XD_id_igual_X")) for f in ok if f.get("atribucion")))
ctl = [f["control_s151"] for f in ok if f.get("control_s151")]
print("   control_s151:", ctl, "| nulo_geo_crater_km max:", max(f.get("nulo_geo_crater_km") or 0 for f in ok))

# ---------------------------------------------------------------- nulos R (control 2 y camino 21)
rn = [f for f in ok if f["r_nulos"]]
malos = 0
for f in rn:
    ns = f["nulos"]
    ang = sorted(n["angulo_grados"] for n in ns)
    sep = [(b - a) % 360 for a, b in zip(ang, ang[1:] + ang[:1])]
    if len(ns) != 20 or any(abs(n["km_aplicado"] - n["km_pedido"]) > 0.01 for n in ns) or any(abs(s - 18) > 1e-3 for s in sep):
        malos += 1
hr = sum(1 for f in rn if len({f["hash_grilla"].get(b) for b in NULOS} | {f["hash_grilla"]["K"]}) != 21)
print("\n== NULOS R. records con R:", len(rn), "| modulo/rumbos malos:", malos, "| hashes repetidos:", hr)
mueve = 0
for f in rn:
    for b in NULOS:
        if f["pub"].get(b) == 1:
            d = dist_km(f["brazos"].get(b), f["brazos"]["K"])
            if d is not None and d > 0.5:
                mueve += 1
                break
print("   records con alguna Rk publicada cuyo cumulo se mueve >0,5 km respecto de K:", mueve)
pubR = sum(f["pub"].get(b, 0) for f in rn for b in NULOS)
print("   publicaciones totales en R (20 brazos x %d records):" % len(rn), pubR, "| publicaciones K en esos records:", sum(f["pub"]["K"] for f in rn),
      "| X:", sum(f["pub"]["X"] for f in rn))

# ---------------------------------------------------------------- P1, P1b (camino 19, 20, 28)
prot = [f for f in ok if f["lab"] == "protegida"]
print("\n== P1. protegidas ok:", len(prot), "| K publica:", sum(f["pub"]["K"] for f in prot), "| X publica:", sum(f["pub"]["X"] for f in prot))
perd = [(f["vol"], f["dt"], f["z"]) for f in prot if f["pub"]["K"] == 1 and f["pub"]["X"] == 0]
gan = [(f["vol"], f["dt"], f["z"]) for f in prot if f["pub"]["K"] == 0 and f["pub"]["X"] == 1]
print("   K publica y X no (veto):", perd, "| K no y X si:", gan)
print("   protegidas con cumulo movido >0,01 km:", sum(1 for f in prot if (dist_km(f["brazos"]["K"], f["brazos"]["X"]) or 0) > 0.01),
      "| con cambio de distance_class K->X:", [(f["vol"], f["dt"], (f["brazos"]["K"] or {}).get("dc"), (f["brazos"]["X"] or {}).get("dc")) for f in prot if (f["brazos"]["K"] or {}).get("dc") != (f["brazos"]["X"] or {}).get("dc")])
print("   protegidas expuestas (poblacion):", [(f["vol"], f["dt"]) for f in prot if f.get("expuesta")])
print("   fragilidad en R (protegidas con r_nulos): R que NO publican por protegida:", sorted(collections.Counter(sum(1 for b in NULOS if f["pub"].get(b) == 0) for f in prot if f["r_nulos"]).items()))
p1b = [(f["vol"], f["dt"], f["brazos"]["K"]["pc_vrp"], (f["brazos"]["X"] or {}).get("pc_vrp")) for f in prot
       if f["pub"]["K"] == 1 and f["pub"]["X"] == 1 and (f["brazos"]["K"] or {}).get("pc_vrp") is not None and f["brazos"]["K"]["pc_vrp"] >= 1.0
       and ((f["brazos"]["X"] or {}).get("pc_vrp") is None or f["brazos"]["X"]["pc_vrp"] < 1.0)]
print("   P1b (K >= 1 MW y X < 1 MW):", p1b)
print("   vrp_mirova minimo en protegidas:", min(f["vrp_mirova"] for f in prot), "| maximo en bajo1:", max(f["vrp_mirova"] for f in ok if f["lab"] == "bajo1"))

# ---------------------------------------------------------------- P2 (caminos 21 a 24, 29, 32)
def invisible(f):
    return f["lab"] == "neg_limpio" and bool(f.get("partida")) and "sin_info" in (f.get("hermanos_lab") or [])


base = [f for f in ok if f["lab"] in ("bajo1", "neg_limpio")]
inv = [f for f in base if invisible(f)]
base = [f for f in base if not invisible(f)]
le35 = [f for f in base if f["z"] is not None and f["z"] <= 35]
sobre = [f for f in base if f["z"] is None or f["z"] > 35]


def saldo(fs, b):
    return (sum(1 for f in fs if f["lab"] == "bajo1" and f["pub"].get(b, f["pub"]["K"]) == 0)
            + sum(1 for f in fs if f["lab"] == "neg_limpio" and f["pub"].get(b, f["pub"]["K"]) == 1))


def p2(fs, nombre):
    sk = saldo(fs, "K")
    dx = saldo(fs, "X") - sk
    dr = [saldo(fs, b) - sk for b in NULOS]
    a = sorted((abs(x) for x in dr), reverse=True)
    ruido = a[1] if len(a) > 1 else 0
    est = "GANA" if dx < -ruido else ("PIERDE" if dx > ruido else "EMPATE")
    sin_r = sum(1 for f in fs if not f["r_nulos"])
    print("   %-28s n=%d S_K=%d S_X=%d dX=%+d | dR=%s ruido=%d max|dR|=%d -> %s | filas sin R (dR forzado 0): %d" % (
        nombre, len(fs), sk, sk + dx, dx, dr, ruido, a[0] if a else 0, est, sin_r))
    cambios = [(f["vol"], f["dt"], f["lab"], f["z"], f["pub"]["K"], f["pub"]["X"]) for f in fs if f["pub"]["K"] != f["pub"]["X"]]
    print("      cambios K->X:", cambios)
    return dx


print("\n== P2. invisibles (neg_limpio partida con hermana sin_info) excluidos:", len(inv), "| de ellos con cambio K->X:",
      sum(1 for f in inv if f["pub"]["K"] != f["pub"]["X"]))
dx = p2(le35, "<=35 (decide)")
p2(sobre, ">35 (informa)")
dx_cc = p2([f for f in le35 if f["vol"] != CC], "<=35 sin Cordon Caulle")
p2([f for f in sobre if f["vol"] != CC], ">35 sin Cordon Caulle")
p2([f for f in le35 if f["vol"] == CC], "<=35 solo Cordon Caulle")
print("   S_K <=35 por volcan (bajo1 sin publicar + neg publicados):",
      dict(collections.Counter(f["vol"] for f in le35 if (f["lab"] == "bajo1" and f["pub"]["K"] == 0) or (f["lab"] == "neg_limpio" and f["pub"]["K"] == 1))))
print("   S_X <=35 por volcan:",
      dict(collections.Counter(f["vol"] for f in le35 if (f["lab"] == "bajo1" and f["pub"]["X"] == 0) or (f["lab"] == "neg_limpio" and f["pub"]["X"] == 1))))
# ruido por volcan
for vol in sorted({f["vol"] for f in le35}):
    fs = [f for f in le35 if f["vol"] == vol]
    sk = saldo(fs, "K")
    dr = [saldo(fs, b) - sk for b in NULOS]
    if any(dr) or saldo(fs, "X") != sk:
        print("   ruido por volcan %-22s S_K=%d dX=%+d dR=%s" % (vol, sk, saldo(fs, "X") - sk, dr))

# ---------------------------------------------------------------- P4 (camino 31)
movs = [(f, dist_km(f["brazos"]["K"], f["brazos"]["X"])) for f in ok]
mov = [(f, d) for f, d in movs if d is not None and d > 0.01]
dcs = [f for f in ok if (f["brazos"]["K"] or {}).get("dc") != (f["brazos"]["X"] or {}).get("dc")]
protP4 = sorted({(f["vol"], f["dt"]) for f, _ in mov if f["lab"] == "protegida"} | {(f["vol"], f["dt"]) for f in dcs if f["lab"] == "protegida"})
print("\n== P4. cumulos movidos >0,01 km:", len(mov), "de", sum(1 for f, d in movs if d is not None), "con cumulo en ambos",
      "| cambios de distance_class:", len(dcs), "| protegidas en P4:", len(protP4), "de", len(prot))
print("   movidos por etiqueta:", dict(collections.Counter(f["lab"] for f, _ in mov)))
print("   cambios de dc por (lab, K->X):", dict(collections.Counter((f["lab"], (f["brazos"]["K"] or {}).get("dc"), (f["brazos"]["X"] or {}).get("dc")) for f in dcs)))
print("   movimiento mediano (km) de las protegidas movidas: %.3f | max %.3f" % (
    statistics.median(d for f, d in mov if f["lab"] == "protegida"), max(d for f, d in mov if f["lab"] == "protegida")))
# distancia del cumulo al crater en K y en X para las protegidas: se acerca o se aleja?
acerca = sum(1 for f, d in mov if f["lab"] == "protegida" and f["brazos"]["X"]["pc_dist"] < f["brazos"]["K"]["pc_dist"])
print("   protegidas movidas cuyo cumulo queda MAS CERCA del crater en X:", acerca, "de", sum(1 for f, d in mov if f["lab"] == "protegida"))

# ---------------------------------------------------------------- M
pares = [(f["brazos"]["K"]["pc_vrp"], f["brazos"]["X"]["pc_vrp"], f["vrp_mirova"]) for f in ok
         if f["lab"] in ("protegida", "bajo1") and f["pub"]["K"] == 1 and f["pub"]["X"] == 1
         and (f["brazos"]["K"] or {}).get("pc_vrp") and (f["brazos"]["X"] or {}).get("pc_vrp") and f.get("vrp_mirova")]
d = [abs(math.log10(x / m)) - abs(math.log10(k / m)) for k, x, m in pares]
print("\n== M. pares:", len(pares), "| mediana d: %.4f | mediana X/K: %.4f | pares con X != K: %d" % (
    statistics.median(d), statistics.median(x / k for k, x, _ in pares), sum(1 for k, x, _ in pares if abs(x - k) > 1e-9)))
print("   K/MIROVA mediana: %.3f" % statistics.median(k / m for k, _, m in pares))

# ---------------------------------------------------------------- P6
p6 = [(f["vol"], f["dt"], f["lab"], f.get("partida"), f["pub"]["K"], f["pub"]["X"]) for f in ok
      if f["pub"]["K"] != f["pub"]["X"] and (f["lab"] in ("sin_info", "far_ref") or f.get("partida"))]
print("\n== P6:", p6)
print("\n== TODOS los cambios de publicacion K->X (%d):" % sum(1 for f in ok if f["pub"]["K"] != f["pub"]["X"]))
for f in ok:
    if f["pub"]["K"] != f["pub"]["X"]:
        print("   ", f["vol"], f["dt"], f["lab"], "z=%.1f" % f["z"], f["lado"], "K->X %d->%d" % (f["pub"]["K"], f["pub"]["X"]),
              "pc_vrp K/X:", (f["brazos"]["K"] or {}).get("pc_vrp"), (f["brazos"]["X"] or {}).get("pc_vrp"),
              "pc_dist K/X:", (f["brazos"]["K"] or {}).get("pc_dist"), (f["brazos"]["X"] or {}).get("pc_dist"),
              "dc K/X:", (f["brazos"]["K"] or {}).get("dc"), (f["brazos"]["X"] or {}).get("dc"),
              "partida:", f.get("partida"), "atrib XF/XD pub:", (f.get("atribucion") or {}).get("X_fondo", {}).get("pub"), (f.get("atribucion") or {}).get("X_det", {}).get("pub"))
