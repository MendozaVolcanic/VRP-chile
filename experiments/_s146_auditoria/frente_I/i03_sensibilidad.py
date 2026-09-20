# -*- coding: utf-8 -*-
"""I-03. Sensibilidad de los tres numeros a cada definicion alternativa razonable.

Reimplementa el etiquetado del banco sobre el cache (mismas reglas, parametrizadas) y PRIMERO
comprueba que con los parametros por defecto reproduce al banco (identidad). Despues mueve una
definicion a la vez.

P1 (si lo medido estuviera roto, fallaria?): la identidad con el banco se verifica con assert;
    controles todo_publica/nada_publica dan 1 y 0 bajo cada variante.
P2 (instrumento muerto?): horas desplazadas +39 min y +180/+240 min (hora local) deben vaciar el
    pareo; barajar `pub` dentro de cada volcan-sensor debe igualar la tasa en pos y en neg.
"""
import sys, io, json, collections, bisect, random
from pathlib import Path
from datetime import datetime, timedelta
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
A = Path(__file__).parent
RECS = json.load(open(A / "_cache_recs.json", encoding="utf-8"))
REF = [f for f in json.load(open(A / "_cache_ref.json", encoding="utf-8")) if not f["diurna"]]
for r in RECS:
    r["t"] = datetime.fromisoformat(r["dt"]).replace(tzinfo=None)
for f in REF:
    f["t"] = datetime.strptime(f["fecha_utc"][:19], "%Y-%m-%d %H:%M:%S")
B = ["MODIS", "VIIRS375", "VIIRS750"]


def es_al(t):
    return t.startswith("ALERTA")


def es_fp(t):
    return t.startswith("FALSO")


def noche_utc(t):
    return t.strftime("%Y-%m-%d")


def noche_local(t):
    return (t - timedelta(hours=16)).strftime("%Y-%m-%d")


def correr(tol=120, neg="sensor", noche_fn=noche_utc, ref=None, recs=None, usar_ocr=True, umbral=0.0, shift=0):
    ref = REF if ref is None else ref
    recs = RECS if recs is None else recs
    if not usar_ocr:
        ref = [f for f in ref if f["source"] == "CONS"]
    idx = collections.defaultdict(list)
    ns = collections.defaultdict(lambda: [False, False])
    nv = collections.defaultdict(lambda: [False, False])
    for f in ref:
        idx[(f["volcano"], f["sensor_bucket"])].append(f)
        n = noche_fn(f["t"])
        for d in (ns[(f["volcano"], f["sensor_bucket"], n)], nv[(f["volcano"], n)]):
            d[0] |= es_al(f["tipo"])
            d[1] |= es_fp(f["tipo"])
    for v in idx.values():
        v.sort(key=lambda x: x["t"])
    out = []
    for r in recs:
        t = r["t"] + timedelta(minutes=shift)
        l = idx.get((r["vol"], r["b"]), [])
        ts = [x["t"] for x in l]
        i = bisect.bisect_left(ts, t - timedelta(seconds=tol))
        filas = []
        while i < len(l) and l[i]["t"] <= t + timedelta(seconds=tol):
            filas.append(l[i])
            i += 1
        n = noche_fn(r["t"])
        a = ns.get((r["vol"], r["b"], n), [False, False])
        v = nv.get((r["vol"], n), [False, False])
        if any(es_al(f["tipo"]) for f in filas):
            lab = "pos"
        elif any(es_fp(f["tipo"]) for f in filas):
            lab = "far_ref"
        elif any(f["tipo"] == "RUTINA" and f["source"] == "CONS" and (f["vrp_mw"] or 0) == 0 for f in filas):
            if neg == "todas":
                ok = True
            elif neg == "sensor":
                ok = not a[0] and not a[1]
            elif neg == "volcan":
                ok = not v[0] and not v[1]
            else:  # volcan3: tampoco la noche previa ni la siguiente
                ok = True
                for k in (-1, 0, 1):
                    vv = nv.get((r["vol"], noche_fn(r["t"] + timedelta(days=k))), [False, False])
                    ok = ok and not vv[0] and not vv[1]
            lab = "neg" if ok else "sin_info"
        else:
            lab = "sin_info"
        pub = r["pub"] if umbral == 0 else int(bool(r["pub"]) and (r["disp"] or 0) >= umbral)
        out.append({"vol": r["vol"], "b": r["b"], "noche": n, "lab": lab, "pub": pub,
                    "sensor": r["sensor"], "z": r["z"], "disp": r["disp"]})
    return out


def tasas(out, b=None, pub_noche="todas", filt=None):
    sel = [o for o in out if (b is None or o["b"] == b) and (filt is None or filt(o))]
    c = collections.Counter()
    for o in sel:
        c[o["lab"]] += 1
        c[o["lab"] + "_pub"] += o["pub"]
    noches = collections.defaultdict(lambda: {"labs": set(), "pub": 0, "pub_pos": 0, "pub_par": 0})
    for o in sel:
        e = noches[(o["vol"], o["noche"])]
        e["labs"].add(o["lab"])
        e["pub"] = max(e["pub"], o["pub"])
        if o["lab"] == "pos":
            e["pub_pos"] = max(e["pub_pos"], o["pub"])
        if o["lab"] != "sin_info":
            e["pub_par"] = max(e["pub_par"], o["pub"])
    clave = {"todas": "pub", "pos": "pub_pos", "pareadas": "pub_par"}[pub_noche]
    npos = sum(1 for e in noches.values() if "pos" in e["labs"])
    ndet = sum(e[clave] for e in noches.values() if "pos" in e["labs"])
    nneg = sum(1 for e in noches.values() if "pos" not in e["labs"] and "neg" in e["labs"] and "far_ref" not in e["labs"])
    nnegp = sum(e[clave if pub_noche != "pos" else "pub"] for e in noches.values()
                if "pos" not in e["labs"] and "neg" in e["labs"] and "far_ref" not in e["labs"])
    return {"pos": c["pos"], "pos_pub": c["pos_pub"], "neg": c["neg"], "neg_pub": c["neg_pub"],
            "noches_pos": npos, "noches_det": ndet, "noches_neg": nneg, "noches_neg_pub": nnegp}


def pct(a, n):
    return f"{100 * a / n:5.1f}% ({a}/{n})" if n else "  s/d (0/0)"


def linea(nombre, out, pub_noche="todas", filt=None):
    t = {b: tasas(out, b, pub_noche, filt) for b in B}
    g = tasas(out, None, pub_noche, filt)
    print(f"{nombre:54s} | noches {g['noches_det']}/{g['noches_pos']} | V375 {pct(t['VIIRS375']['neg_pub'], t['VIIRS375']['neg'])}"
          f" | V750 {pct(t['VIIRS750']['neg_pub'], t['VIIRS750']['neg'])} | MODIS {pct(t['MODIS']['neg_pub'], t['MODIS']['neg'])}"
          f" | recall pasada {pct(g['pos_pub'], g['pos'])}")
    return g, t


base = correr()
g, t = linea("BASE (= banco: tol 120 s, neg por noche-sensor)", base)
assert (g["noches_det"], g["noches_pos"]) == (78, 78), "no reproduce al banco"
assert (t["VIIRS375"]["neg_pub"], t["VIIRS375"]["neg"]) == (322, 373), "no reproduce al banco"
assert (t["VIIRS750"]["neg_pub"], t["VIIRS750"]["neg"]) == (133, 622) and t["MODIS"]["neg"] == 439
print("identidad con el banco (datos de hoy, ver i00_salida.txt): OK\n")

print("-- tolerancia del pareo")
for tol in (0, 60, 120, 300, 600):
    linea(f"tol {tol} s", correr(tol=tol))
print("-- definicion de negativo limpio")
linea("neg = toda RUTINA CONS pareada (sin excluir noches)", correr(neg="todas"))
linea("neg = sin ALERTA/FP esa noche y sensor (banco)", base)
linea("neg = sin ALERTA/FP esa noche, cualquier sensor", correr(neg="volcan"))
linea("neg = idem, y tampoco la noche previa ni la siguiente", correr(neg="volcan3"))
print("-- corte de la noche")
linea("noche = fecha local (UTC-4, corte a mediodia local)", correr(noche_fn=noche_local))
print("-- que cuenta como positivo y como noche detectada")
linea("positivos solo CONS (sin canal OCR)", correr(usar_ocr=False))
linea("noche detectada solo si publica una pasada POS", base, pub_noche="pos")
linea("noche detectada si publica una pasada con fila MIROVA", base, pub_noche="pareadas")
print("-- umbral de magnitud para 'publicamos'")
for u in (0.02, 0.05, 0.1, 0.2, 0.5):
    linea(f"publica solo si magnitud mostrada >= {u} MW", correr(umbral=u))
print("-- por plataforma")
for s in ("SNPP", "NOAA20", "NOAA21", "AQUA", "TERRA"):
    linea(f"solo plataforma {s}", base, filt=lambda o, s=s: s in o["sensor"])
print("-- por angulo cenital del sensor")
for nm, fz in (("z<30", lambda z: z is not None and z < 30), ("z 30-50", lambda z: z is not None and 30 <= z < 50),
               ("z>=50", lambda z: z is not None and z >= 50), ("z desconocido", lambda z: z is None)):
    linea(f"cenital {nm}", base, filt=lambda o, fz=fz: fz(o["z"]))
print("-- por mitad de la ventana")
linea("01 al 10 de septiembre", base, filt=lambda o: o["noche"] <= "2026-09-10")
linea("11 al 20 de septiembre", base, filt=lambda o: o["noche"] > "2026-09-10")

print("\n-- POR VOLCAN (base)")
macro = collections.defaultdict(list)
vols = sorted({o["vol"] for o in base})
for vol in vols:
    g, t = linea(f"  {vol}", base, filt=lambda o, vol=vol: o["vol"] == vol)
    for b in B:
        if t[b]["neg"] >= 5:
            macro[b].append(t[b]["neg_pub"] / t[b]["neg"])
for b in B:
    m = macro[b]
    print(f" {b}: promedio simple entre volcanes {100 * sum(m) / len(m):.1f}% | min {100 * min(m):.1f}% max {100 * max(m):.1f}% | volcanes con n>=5: {len(m)}")
print("\n-- dejando un volcan afuera (rango del agregado)")
for b in B:
    vals = []
    for vol in vols:
        x = tasas(base, b, filt=lambda o, vol=vol: o["vol"] != vol)
        vals.append(100 * x["neg_pub"] / x["neg"])
    print(f" {b}: {min(vals):.1f}% a {max(vals):.1f}%")

print("\n-- bootstrap por noche de volcan (2000 remuestreos, semilla 146): IC 95 % de la tasa en negativos")
rng = random.Random(146)
for b in B:
    grupos = collections.defaultdict(list)
    for o in base:
        if o["b"] == b and o["lab"] == "neg":
            grupos[(o["vol"], o["noche"])].append(o["pub"])
    ks = list(grupos)
    vals = []
    for _ in range(2000):
        a = n = 0
        for k in rng.choices(ks, k=len(ks)):
            a += sum(grupos[k])
            n += len(grupos[k])
        vals.append(a / n)
    vals.sort()
    print(f" {b}: {100 * vals[50]:.1f}% a {100 * vals[1949]:.1f}% (grupos {len(ks)})")

print("\n-- noches negativas (unidad noche de volcan): cuantas publican, segun que pasadas cuentan")
for modo in ("todas", "pareadas"):
    x = tasas(base, None, modo)
    print(f" pub de '{modo}': {pct(x['noches_neg_pub'], x['noches_neg'])}")

print("\n-- CONTROLES DE INSTRUMENTO")
for sh in (39, 180, 240):
    o = correr(shift=sh)
    print(f" horas nuestras +{sh} min: etiquetas {dict(collections.Counter(x['lab'] for x in o))}")
for val in (1, 0):
    falsos = [dict(r, pub=val) for r in RECS]
    o = correr(recs=falsos)
    x = tasas(o, "VIIRS375")
    y = tasas(o)
    print(f" todo pub={val}: V375 neg {x['neg_pub']}/{x['neg']}, noches {y['noches_det']}/{y['noches_pos']}")
rng = random.Random(7)
grupos = collections.defaultdict(list)
for i, r in enumerate(RECS):
    grupos[(r["vol"], r["b"])].append(i)
bar = [dict(r) for r in RECS]
for k, ii in grupos.items():
    p = [RECS[i]["pub"] for i in ii]
    rng.shuffle(p)
    for i, v in zip(ii, p):
        bar[i]["pub"] = v
x = tasas(correr(recs=bar), "VIIRS375")
print(f" pub barajado dentro de volcan-sensor: V375 pos {pct(x['pos_pub'], x['pos'])} ; neg {pct(x['neg_pub'], x['neg'])}")
x = tasas(base, "VIIRS375")
print(f" real:                                 V375 pos {pct(x['pos_pub'], x['pos'])} ; neg {pct(x['neg_pub'], x['neg'])}")

print("\n-- magnitud mostrada (MW) en V375: positivos contra negativos limpios, cuantiles de lo publicado")
for lab in ("pos", "neg"):
    v = sorted(o["disp"] for o in base if o["b"] == "VIIRS375" and o["lab"] == lab and o["pub"])
    q = lambda p: v[int(p * (len(v) - 1))]
    print(f" {lab}: n {len(v)} p10 {q(.1):.3f} p25 {q(.25):.3f} p50 {q(.5):.3f} p75 {q(.75):.3f} p90 {q(.9):.3f}")
v = sorted(f["vrp_mw"] for f in REF if es_al(f["tipo"]) and f["sensor_bucket"] == "VIIRS375")
print(f" VRP de las ALERTAS V375 de MIROVA en ventana: n {len(v)} min {v[0]} p10 {v[len(v) // 10]} p50 {v[len(v) // 2]} max {v[-1]}")
