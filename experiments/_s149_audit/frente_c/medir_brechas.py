# -*- coding: utf-8 -*-
"""S149, FRENTE C. Estado de la replica EN PRODUCCION (data/mirova_equivalent) contra MIROVA, por
sensor y por volcan, en los tres errores, y variabilidad de MIROVA contra si misma.

Reusa SIN copiar: el predicado del dashboard ejecutado con node, el etiquetador y el indexador de
scripts/banco_paridad.py (A97), y la referencia unificada del snapshot del repo (sin red).

LAS DOS PREGUNTAS DEL INSTRUMENTO
 P1 (si lo medido estuviera roto, lo veria): controles todo_publica / nada_publica sobre los mismos
    denominadores tienen que dar 1 y 0 en E1 y E2; identidad del predicado contra los 7 casos del guard.
 P2 (instrumento muerto): toda tasa lleva su n; n = 0 se imprime SIN DATO, nunca 0 %. Barajar las
    etiquetas alerta/rutina de MIROVA dentro de cada volcan y sensor tiene que llevar la repeticion de
    MIROVA entre pasadas a la tasa base (control del bloque de variabilidad).

Uso: python medir_brechas.py DESDE HASTA salida.json
"""
import collections, io, json, math, random, statistics, sys
from datetime import timedelta
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "scripts")); sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "experiments" / "_s146_ab_sin_test1"))
import evaluar as ev  # noqa: E402
bp = ev.bp

DESDE, HASTA, OUT = sys.argv[1], sys.argv[2], sys.argv[3]
TRAMOS = [(0, .05, "<0,05"), (.05, .1, "0,05-0,10"), (.1, .2, "0,10-0,20"), (.2, .5, "0,20-0,50"), (.5, 1e9, ">=0,50")]
TOL = timedelta(seconds=bp.TOL_S)


def tramo(v):
    if v is None or v <= 0:
        return "sin_mag"
    return next(n for a, b, n in TRAMOS if a <= v < b)


def zona(z):
    return "z?" if z is None else ("nadir" if z < 36 else ("medio" if z < 52 else "borde"))


def wilson(k, n):
    if not n:
        return None
    p, z = k / n, 1.96
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [round(100 * (c - h), 1), round(100 * (c + h), 1)]


def tasa(k, n):
    return {"k": k, "n": n, "pct": (round(100 * k / n, 1) if n else None), "ic95": wilson(k, n)}


def cuantiles(xs):
    if not xs:
        return {"n": 0}
    xs = sorted(xs)
    q = lambda p: xs[min(len(xs) - 1, int(p * len(xs)))]
    return {"n": len(xs), "mediana": round(statistics.median(xs), 3), "p25": round(q(.25), 3),
            "p75": round(q(.75), 3), "p10": round(q(.10), 3), "p90": round(q(.90), 3)}


# ---------------------------------------------------------------- carga
ventana = (DESDE, HASTA)
coords = bp._coords_por_volcan(); inner = bp.inner_desde_html()
identidad = bp.control_identidad_predicado()
filas = ev.cargar_referencia_unificada(bp.SNAP_CONS, bp.SNAP_OCR)
por_vb, ns, nv, n_ref = bp.indexar_referencia(filas, coords, ventana)
recs = ev.cargar_brazo(bp.DATA, coords, inner, ventana)
bp.etiquetar(recs, por_vb, ns, nv); ev.anotar_vrp_mirova(recs, por_vb)

# ---------------------------------------------------------------- pasadas de MIROVA (unidad propia)
# Una pasada de MIROVA = filas del mismo volcan y sensor a menos de 120 s. Alerta si alguna fila es
# ALERTA; fp si alguna es FALSO_POSITIVO y ninguna ALERTA; rutina0 si hay fila CONS RUTINA con VRP 0.
pasadas = []
for (vol, b), lista in por_vb.items():
    grupo = []
    for dt, f in lista:
        if grupo and dt - grupo[0][0] > TOL:
            pasadas.append((vol, b, grupo)); grupo = []
        grupo.append((dt, f))
    if grupo:
        pasadas.append((vol, b, grupo))
nuestros = collections.defaultdict(list)
for r in recs:
    nuestros[(r["vol"], r["b"])].append(r)
P = []
for vol, b, g in pasadas:
    fs = [f for _, f in g]
    al = [f for f in fs if bp.es_alerta(f["tipo"])]
    al.sort(key=lambda f: f["source"] != "CONS")
    en_tabla = any(f["source"] == "CONS" for f in fs)
    p = {"vol": vol, "b": b, "dt": g[0][0], "noche": g[0][1]["fecha_utc"][:10],
         "alerta": bool(al), "fp": (not al) and any(bp.es_fp(f["tipo"]) for f in fs),
         "rutina0": any(f["tipo"] == "RUTINA" and f["source"] == "CONS" and (f["vrp_mw"] or 0) == 0 for f in fs),
         "vrp": al[0]["vrp_mw"] if al else None, "en_tabla": en_tabla,
         "solo_ocr": bool(al) and all(f["source"] != "CONS" for f in al)}
    mios = [r for r in nuestros.get((vol, b), []) if abs(r["dt"] - p["dt"]) <= TOL + TOL]
    mios = [r for r in mios if any(abs(r["dt"] - dt) <= TOL for dt, _ in g)]
    p["con_record"] = bool(mios); p["pub"] = int(any(r["pub"] for r in mios))
    p["disp"] = max([r["disp"] or 0 for r in mios], default=None)
    p["z"] = mios[0]["z"] if mios else None
    P.append(p)
noche_alerta = collections.defaultdict(bool); noche_fp = collections.defaultdict(bool)
for p in P:
    noche_alerta[(p["vol"], p["b"], p["noche"])] |= p["alerta"]
    noche_fp[(p["vol"], p["b"], p["noche"])] |= p["fp"]


def errores(sel, forzar=None):
    """Los tres errores sobre una seleccion de pasadas de MIROVA. forzar = 1/0 para los controles."""
    pub = (lambda p: p["pub"]) if forzar is None else (lambda p: forzar if p["con_record"] else 0)
    o = {}
    # E1: MIROVA listo la pasada con VRP 0, noche y sensor sin alerta ni fp, y tenemos record
    neg = [p for p in sel if p["rutina0"] and not p["alerta"] and not p["fp"] and p["con_record"]
           and not noche_alerta[(p["vol"], p["b"], p["noche"])] and not noche_fp[(p["vol"], p["b"], p["noche"])]]
    o["E1_pub_en_neg_limpio"] = tasa(sum(pub(p) for p in neg), len(neg))
    o["E1_por_zona"] = {z: tasa(sum(pub(p) for p in neg if zona(p["z"]) == z), sum(1 for p in neg if zona(p["z"]) == z))
                        for z in ("nadir", "medio", "borde")}
    # estrato RUTINA en noche con alerta del mismo sensor
    rna = [p for p in sel if p["rutina0"] and not p["alerta"] and not p["fp"] and p["con_record"]
           and noche_alerta[(p["vol"], p["b"], p["noche"])]]
    o["E1b_pub_en_rutina_noche_con_alerta"] = tasa(sum(pub(p) for p in rna), len(rna))
    # E2: alertas de MIROVA. Dos denominadores: con record nuestro, y todas (sin record = no publicamos)
    pos = [p for p in sel if p["alerta"]]
    o["E2_recall_con_record"] = tasa(sum(pub(p) for p in pos if p["con_record"]), sum(1 for p in pos if p["con_record"]))
    o["E2_recall_todas"] = tasa(sum(pub(p) for p in pos), len(pos))
    o["E2_alertas_sin_record"] = sum(1 for p in pos if not p["con_record"])
    o["E2_recall_tabla_sola"] = tasa(sum(pub(p) for p in pos if p["con_record"] and not p["solo_ocr"]),
                                     sum(1 for p in pos if p["con_record"] and not p["solo_ocr"]))
    o["E2_por_tramo"] = {}
    for _, _, n in TRAMOS + [(0, 0, "sin_mag")]:
        s = [p for p in pos if tramo(p["vrp"]) == n]
        o["E2_por_tramo"][n] = {"con_record": tasa(sum(pub(p) for p in s if p["con_record"]), sum(1 for p in s if p["con_record"])),
                                "sin_record": sum(1 for p in s if not p["con_record"])}
    # E3: magnitud pareada, solo real (no tiene sentido en los controles)
    if forzar is None:
        rz = [p["disp"] / p["vrp"] for p in pos if p["pub"] and p["vrp"] and p["disp"]]
        o["E3_razon_nuestra_sobre_mirova"] = cuantiles(rz)
        if rz:
            o["E3_razon_nuestra_sobre_mirova"]["factor_tipico_exp_mediana_abs_ln"] = round(
                math.exp(statistics.median([abs(math.log(x)) for x in rz])), 2)
            o["E3_razon_nuestra_sobre_mirova"]["frac_entre_0,5_y_2"] = tasa(sum(1 for x in rz if .5 <= x <= 2), len(rz))
        o["E3_por_tramo"] = {n: cuantiles([p["disp"] / p["vrp"] for p in pos if p["pub"] and p["vrp"] and p["disp"] and tramo(p["vrp"]) == n])
                             for _, _, n in TRAMOS}
    return o


res = {"meta": {"ventana": ventana, "n_filas_ref_nocturnas": n_ref, "n_records_nocturnos": len(recs),
                "n_pasadas_mirova": len(P), "sha_index_html": bp.sha_git(bp.HTML),
                "sha_cons": bp.sha_git(bp.SNAP_CONS), "sha_ocr": bp.sha_git(bp.SNAP_OCR),
                "identidad_predicado_ok": identidad == ([0, 1, 1, 1, 0], [1, 0]),
                "etiquetas_banco": dict(collections.Counter(r["lab"] for r in recs))},
       "por_sensor": {}, "por_volcan": {}, "controles": {}}
for b in bp.BUCKETS:
    sel = [p for p in P if p["b"] == b]
    res["por_sensor"][b] = errores(sel)
    res["controles"][b] = {"todo_publica": {k: v for k, v in errores(sel, 1).items() if k in ("E1_pub_en_neg_limpio", "E2_recall_con_record")},
                           "nada_publica": {k: v for k, v in errores(sel, 0).items() if k in ("E1_pub_en_neg_limpio", "E2_recall_con_record")}}
    for vol in bp.VOLS:
        res["por_volcan"].setdefault(vol, {})[b] = errores([p for p in sel if p["vol"] == vol])

# cruce con el etiquetador del banco (unidad = record nuestro): tiene que dar casi lo mismo
res["cruce_banco"] = {}
for b in bp.BUCKETS:
    s = [r for r in recs if r["b"] == b]
    res["cruce_banco"][b] = {"pos": tasa(sum(r["pub"] for r in s if r["lab"] == "pos"), sum(1 for r in s if r["lab"] == "pos")),
                             "neg_limpio": tasa(sum(r["pub"] for r in s if r["lab"] == "neg_limpio"), sum(1 for r in s if r["lab"] == "neg_limpio")),
                             "rutina_noche_alerta": tasa(sum(r["pub"] for r in s if r["lab"] == "sin_info" and r["rutina_pasada"] and r["noche_con_alerta_sensor"]),
                                                         sum(1 for r in s if r["lab"] == "sin_info" and r["rutina_pasada"] and r["noche_con_alerta_sensor"]))}


# ---------------------------------------------------------------- MIROVA contra si misma
def repeticion(Ps, b, rng=None):
    """Para cada pasada con alerta i, las OTRAS pasadas j de la misma noche y sensor que estan en la
    tabla (en_tabla): fraccion de j que tambien alerta. rng: baraja alerta dentro de volcan (control)."""
    sel = [dict(p) for p in Ps if p["b"] == b and (p["en_tabla"] or p["alerta"]) and not p["fp"]]
    if rng is not None:
        porv = collections.defaultdict(list)
        for p in sel:
            porv[p["vol"]].append(p)
        for ps in porv.values():
            et = [p["alerta"] for p in ps]; rng.shuffle(et)
            for p, e in zip(ps, et):
                p["alerta"] = e
    nn = collections.defaultdict(list)
    for p in sel:
        nn[(p["vol"], p["noche"])].append(p)
    k = n = 0; porz = collections.defaultdict(lambda: [0, 0]); port = collections.defaultdict(lambda: [0, 0]); porvol = collections.defaultdict(lambda: [0, 0])
    lnr = []
    noches_multi = noches_todas_alerta = 0
    for (vol, _), ps in nn.items():
        al = [p for p in ps if p["alerta"]]
        if not al or len(ps) < 2:
            continue
        noches_multi += 1; noches_todas_alerta += int(len(al) == len(ps))
        for i in al:
            for j in ps:
                if j is i:
                    continue
                n += 1; k += j["alerta"]
                porz[zona(j["z"])][1] += 1; porz[zona(j["z"])][0] += j["alerta"]
                port[tramo(i["vrp"])][1] += 1; port[tramo(i["vrp"])][0] += j["alerta"]
                porvol[vol][1] += 1; porvol[vol][0] += j["alerta"]
        for x in range(len(al)):
            for y in range(x + 1, len(al)):
                if al[x]["vrp"] and al[y]["vrp"]:
                    lnr.append(abs(math.log(al[x]["vrp"] / al[y]["vrp"])))
    base = sum(p["alerta"] for p in sel)
    o = {"tasa_base_alerta_por_pasada": tasa(base, len(sel)), "repite_en_otra_pasada": tasa(k, n),
         "noches_con_alerta_y_2_o_mas_pasadas": noches_multi, "de_esas_todas_las_pasadas_alertan": noches_todas_alerta}
    if rng is None:
        o["por_zona_de_la_otra_pasada"] = {z: tasa(*v) for z, v in sorted(porz.items())}
        o["por_tramo_de_la_alerta"] = {t: tasa(*v) for t, v in port.items()}
        o["por_volcan"] = {v: tasa(*x) for v, x in sorted(porvol.items())}
        o["magnitud_entre_pasadas_misma_noche"] = {"n_pares": len(lnr),
            "factor_mediano": round(math.exp(statistics.median(lnr)), 2) if lnr else None,
            "factor_p90": round(math.exp(sorted(lnr)[int(.9 * len(lnr))]), 2) if lnr else None}
    return o


res["mirova_vs_mirova"] = {}
for b in bp.BUCKETS:
    o = repeticion(P, b)
    rng = random.Random(11)
    bar = [repeticion(P, b, rng)["repite_en_otra_pasada"]["pct"] for _ in range(30)]
    bar = [x for x in bar if x is not None]
    o["control_barajado_repite_pct_media"] = round(statistics.mean(bar), 1) if bar else None
    res["mirova_vs_mirova"][b] = o

# misma escena, dos resoluciones: VIIRS 375 y VIIRS 750 del mismo instante (+-120 s)
idx750 = collections.defaultdict(list)
for p in P:
    if p["b"] == "VIIRS750":
        idx750[p["vol"]].append(p)
tab = collections.Counter(); rz = []; port = collections.defaultdict(lambda: [0, 0]); port750 = collections.defaultdict(lambda: [0, 0])
for p in P:
    if p["b"] != "VIIRS375" or p["fp"] or not (p["en_tabla"] or p["alerta"]):
        continue
    q = next((x for x in idx750[p["vol"]] if abs(x["dt"] - p["dt"]) <= TOL and not x["fp"]), None)
    if q is None:
        tab["375_sin_750"] += 1; continue
    tab[("A" if p["alerta"] else "0") + ("A" if q["alerta"] else "0")] += 1
    if p["alerta"]:
        port[tramo(p["vrp"])][1] += 1; port[tramo(p["vrp"])][0] += q["alerta"]
    if q["alerta"]:
        port750[tramo(q["vrp"])][1] += 1; port750[tramo(q["vrp"])][0] += p["alerta"]
    if p["alerta"] and q["alerta"] and p["vrp"] and q["vrp"]:
        rz.append(q["vrp"] / p["vrp"])
res["mirova_375_vs_750_mismo_instante"] = {
    "tabla_375x750": {str(k): v for k, v in tab.items()},
    "P(750 alerta | 375 alerta)": tasa(tab["AA"], tab["AA"] + tab["A0"]),
    "P(375 alerta | 750 alerta)": tasa(tab["AA"], tab["AA"] + tab["0A"]),
    "P(750 alerta | 375 en 0)": tasa(tab["0A"], tab["0A"] + tab["00"]),
    "P(375 alerta | 750 en 0)": tasa(tab["A0"], tab["A0"] + tab["00"]),
    "P(750 alerta | 375 alerta) por tramo de la 375": {t: tasa(*v) for t, v in port.items()},
    "P(375 alerta | 750 alerta) por tramo de la 750": {t: tasa(*v) for t, v in port750.items()},
    "razon_750_sobre_375": cuantiles(rz),
    "factor_tipico": round(math.exp(statistics.median([abs(math.log(x)) for x in rz])), 2) if rz else None}

# noche: si VIIRS 375 alerta, alerta MODIS esa noche? (la regla del dueno: solo MODIS pierde sub-pixel)
nn = collections.defaultdict(lambda: collections.defaultdict(lambda: {"n": 0, "a": 0, "vmax": 0}))
for p in P:
    if p["fp"]:
        continue
    e = nn[(p["vol"], p["noche"])][p["b"]]; e["n"] += 1; e["a"] += p["alerta"]; e["vmax"] = max(e["vmax"], p["vrp"] or 0)
cr = collections.defaultdict(lambda: [0, 0])
for k, d in nn.items():
    if d["VIIRS375"]["a"]:
        for b in ("MODIS", "VIIRS750"):
            if d[b]["n"]:
                t = tramo(d["VIIRS375"]["vmax"])
                cr[(b, t)][1] += 1; cr[(b, t)][0] += int(d[b]["a"] > 0)
                cr[(b, "TODAS")][1] += 1; cr[(b, "TODAS")][0] += int(d[b]["a"] > 0)
res["mirova_noche_375_alerta_entonces_otro_sensor"] = {"%s|%s" % k: tasa(*v) for k, v in sorted(cr.items())}

Path(OUT).write_text(json.dumps(res, indent=1, ensure_ascii=False, default=str), encoding="utf-8")


# ---------------------------------------------------------------- impresion
def f(t):
    return "SIN DATO (n 0)" if not t["n"] else "%5.1f %% (%d/%d) IC95 %s" % (t["pct"], t["k"], t["n"], t["ic95"])


print("VENTANA", ventana, "| filas ref", n_ref, "| records", len(recs), "| pasadas MIROVA", len(P), "| identidad predicado", res["meta"]["identidad_predicado_ok"])
for b in bp.BUCKETS:
    o = res["por_sensor"][b]
    print("\n=====", b)
    print(" E1 publica en negativo limpio:        ", f(o["E1_pub_en_neg_limpio"]))
    print("    por zona:", {z: f(t) for z, t in o["E1_por_zona"].items()})
    print(" E1b publica en RUTINA de noche c/alerta:", f(o["E1b_pub_en_rutina_noche_con_alerta"]))
    print(" E2 recall (alertas con record):        ", f(o["E2_recall_con_record"]), "| tabla sola:", f(o["E2_recall_tabla_sola"]))
    print(" E2 recall (todas, sin record = no):    ", f(o["E2_recall_todas"]), "| sin record:", o["E2_alertas_sin_record"])
    for t, v in o["E2_por_tramo"].items():
        print("      tramo %-10s %s | sin record %d" % (t, f(v["con_record"]), v["sin_record"]))
    print(" E3 razon nuestra/MIROVA:", o["E3_razon_nuestra_sobre_mirova"])
    for t, v in o["E3_por_tramo"].items():
        print("      tramo %-10s %s" % (t, v))
    print(" controles:", {k: {kk: vv["pct"] for kk, vv in v.items()} for k, v in res["controles"][b].items()})
    print(" cruce con el banco (unidad record):", {k: f(v) for k, v in res["cruce_banco"][b].items()})
    print(" -- por volcan: E1 | E1b | E2 con record | E3 mediana (n)")
    for vol in bp.VOLS:
        v = res["por_volcan"][vol][b]
        e3 = v["E3_razon_nuestra_sobre_mirova"]
        print("    %-20s %-34s | %-30s | %-34s | %s" % (vol, f(v["E1_pub_en_neg_limpio"]), f(v["E1b_pub_en_rutina_noche_con_alerta"]),
              f(v["E2_recall_con_record"]), ("%.2f (n %d)" % (e3["mediana"], e3["n"])) if e3["n"] else "SIN DATO"))
print("\n===== MIROVA CONTRA SI MISMA")
for b in bp.BUCKETS:
    o = res["mirova_vs_mirova"][b]
    print("\n", b, "| tasa base de alerta por pasada:", f(o["tasa_base_alerta_por_pasada"]))
    print("   si una pasada alerta, otra pasada de la misma noche y sensor alerta:", f(o["repite_en_otra_pasada"]),
          "| control barajado: %s %%" % o["control_barajado_repite_pct_media"])
    print("   noches con alerta y >=2 pasadas:", o["noches_con_alerta_y_2_o_mas_pasadas"], "| todas las pasadas alertan:", o["de_esas_todas_las_pasadas_alertan"])
    print("   por zona de la otra pasada:", {z: f(t) for z, t in o["por_zona_de_la_otra_pasada"].items()})
    print("   por tramo de la alerta:", {z: f(t) for z, t in o["por_tramo_de_la_alerta"].items()})
    print("   por volcan:", {z: f(t) for z, t in o["por_volcan"].items()})
    print("   magnitud entre pasadas de la misma noche:", o["magnitud_entre_pasadas_misma_noche"])
print("\n MISMO INSTANTE, 375 contra 750:")
for k, v in res["mirova_375_vs_750_mismo_instante"].items():
    print("   ", k, ":", f(v) if isinstance(v, dict) and "ic95" in v else ({a: f(c) for a, c in v.items()} if isinstance(v, dict) and v and all(isinstance(c, dict) and "ic95" in c for c in v.values()) else v))
print("\n NOCHE: 375 alerta, entonces el otro sensor alerta esa noche:")
for k, v in res["mirova_noche_375_alerta_entonces_otro_sensor"].items():
    print("   ", k, f(v))
