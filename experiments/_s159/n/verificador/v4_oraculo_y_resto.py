# -*- coding: utf-8 -*-
"""Verificador S159 N, paso 4: afirmaciones 2 a 5 desde los resultados crudos.

A2: razon O/MIROVA por variante sobre la INTERSECCION de alertas detectadas por todas las variantes (las 145 de
geo_linear no son las 113 de r2_linear); fuente de la cifra de MIROVA (tabla u OCR).
A3: el oraculo contado como brazo (predicado SUPUESTO del agente: pixel de mayor M13 a <= inner), ponderado igual que
los brazos, con geo_linear y con geo_linear_anillo_sensible; cuales protegidas pierde.
A4: C contra K, cumulos en 0,0 MW (mismos ids?), y si C cambia magnitud en alguna alerta.
A5: Chillan 2026-10-01 05:24.
Control positivo de A2: la razon de geo_nearest tiene que salir distinta de la de geo_linear sobre las MISMAS
pasadas (si saliera igual, la interseccion estaria mal armada). P2: si el oraculo no corriera, n=0 por variante.
"""
import collections, io, json, statistics, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent; N = AQUI.parent; ROOT = N.parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import banco_paridad as B
obj = {o["id"]: o for o in json.loads((N / "objetivos_n.json").read_text(encoding="utf-8"))}
V = json.load(open(AQUI / "v1_pub.json")); P = {(int(k.split("|")[0]), k.split("|")[1]): v for k, v in V["P"].items()}
ok = set(V["ok"]); pub = lambda i, b: P.get((i, b), False)
res = {}
for f in sorted((N / "run_39682867040").glob("*resultados_*.json")):
    for r in json.loads(f.read_text(encoding="utf-8")):
        if r.get("estado") == "ok" or r["id"] not in res:
            res[r["id"]] = r
inner = B.inner_desde_html()
def alerta(o, inn):
    if not o or not o.get("npix") or (o.get("vrp_mw") or 0) <= 0:
        return False
    return max(o["pixeles"], key=lambda p: p[4])[3] <= inn
VARS = ("geo_linear", "geo_nearest", "geo_cubic", "r2_linear", "r2_nearest", "geo_linear_anillo_sensible")
pos = [i for i in ok if obj[i]["lab"] == "pos" and obj[i]["decide"]]
det = {v: {i for i in pos if alerta((res[i].get("oraculo") or {}).get(v), inner[obj[i]["volcan"]])} for v in VARS}
inter = set.intersection(*(det[v] for v in VARS[:5]))
print("A2. alertas que deciden:", len(pos), "| detectadas por variante:", {v: len(det[v]) for v in VARS},
      "| interseccion de las 5 variantes (sin anillo):", len(inter))
def q(xs):
    xs = sorted(xs); n = len(xs)
    return f"{statistics.median(xs):.3f} [{xs[n//4]:.3f}, {xs[(3*n)//4]:.3f}] n={n}, en 0,8-1,25: {sum(0.8<=x<=1.25 for x in xs)}"
for v in VARS:
    print(f"   {v:28s} propia: {q([res[i]['oraculo'][v]['vrp_mw']/obj[i]['mirova_vrp'] for i in det[v]])}")
    print(f"   {'':28s} interseccion: {q([res[i]['oraculo'][v]['vrp_mw']/obj[i]['mirova_vrp'] for i in inter])}")
# fuente de la cifra de MIROVA en las 145 y redondeo
src = collections.Counter()
for i in det["geo_linear"]:
    o = obj[i]; m = [x for x in o["mirova"] if x["vrp_mw"] == o["mirova_vrp"]]
    src[m[0]["source"] if m else "?"] += 1
print("   fuente de mirova_vrp en las 145 de geo_linear:", dict(src))
# las 36 que geo_linear no detecta
nd = [i for i in pos if i not in det["geo_linear"]]
print("   no detectadas por geo_linear:", len(nd), collections.Counter(obj[i]["volcan"] for i in nd),
      "| motivo:", collections.Counter((res[i]["oraculo"]["geo_linear"].get("motivo_vacio") if not res[i]["oraculo"]["geo_linear"].get("npix") else "pico fuera de inner") for i in nd))
# A3 oraculo como brazo
print("\nA3. oraculo como brazo (ponderado como los brazos; E = bajo 1 MW perdidas + negativos publicados)")
base = [i for i in ok if obj[i]["peso"] > 0]
def cuenta(fx):
    c = collections.Counter()
    for i in base:
        o = obj[i]; w = o["peso"]; pk = pub(i, "K"); px = fx(i)
        if o["lab"] == "pos" and o["decide"]:
            if o["protegida"]:
                c["prot_perd"] += pk and not px; c["prot_n"] += 1
            else:
                c["mb_fn_K"] += w * (not pk); c["mb_fn_X"] += w * (not px)
                c["mb_gan"] += w * (px and not pk); c["mb_perd"] += w * (pk and not px)
        elif o["lab"] == "neg_limpio":
            c["neg_K"] += w * pk; c["neg_X"] += w * px; c["neg_X_crudo"] += px
            c["neg_X_en_negpub"] += px and o["clase"] == "neg_pub"
    c["dE"] = c["mb_fn_X"] + c["neg_X"] - c["mb_fn_K"] - c["neg_K"]
    return {k: round(v, 1) for k, v in c.items()}
for v in ("geo_linear", "geo_linear_anillo_sensible"):
    c = cuenta(lambda i, v=v: alerta(res[i]["oraculo"].get(v), inner[obj[i]["volcan"]]))
    print(f"   {v}: {c}")
    lost = [i for i in base if obj[i]["lab"] == "pos" and obj[i]["decide"] and obj[i]["protegida"] and pub(i, "K")
            and not alerta(res[i]["oraculo"].get(v), inner[obj[i]["volcan"]])]
    for i in lost:
        x = res[i]["oraculo"][v]
        pk = max(x["pixeles"], key=lambda p: p[4]) if x.get("npix") else None
        print(f"     pierde protegida id {i} {obj[i]['volcan']} {obj[i]['hora_utc']} MIROVA {obj[i]['mirova_vrp']} "
              f"dist MIROVA {[m.get('dist_km') for m in obj[i]['mirova']]} | O {x.get('npix')}px pico a {pk[3] if pk else None} km "
              f"(inner {inner[obj[i]['volcan']]}) motivo {x.get('motivo_vacio')}")
# A4
print("\nA4. C contra K")
print("   publica distinto:", sum(pub(i, "C") != pub(i, "K") for i in ok), "de", len(ok))
kz = {i for i in ok if ((res[i]["brazos"]["K"]["record"] or {}).get("primary_cluster") or {}).get("vrp_mw") == 0.0}
cz = {i for i in ok if ((res[i]["brazos"]["C"]["record"] or {}).get("primary_cluster") or {}).get("vrp_mw") == 0.0}
print("   K en 0,0 MW:", len(kz), "| C en 0,0 MW:", len(cz), "| mismos ids:", kz == cz)
ch = [i for i in ok if json.dumps((res[i]["brazos"]["C"]["record"] or {}).get("primary_cluster"), sort_keys=True)
      != json.dumps((res[i]["brazos"]["K"]["record"] or {}).get("primary_cluster"), sort_keys=True)]
for i in ch:
    k = res[i]["brazos"]["K"]["record"]["primary_cluster"]; c = res[i]["brazos"]["C"]["record"]["primary_cluster"]
    print(f"   cumulo cambia id {i} {obj[i]['volcan']} {obj[i]['hora_utc']} {obj[i]['clase']}: K {k.get('n_pixels')}px {k.get('vrp_mw')} -> C {c.get('n_pixels')}px {c.get('vrp_mw')} | pub K {pub(i,'K')} C {pub(i,'C')}")
# A5
print("\nA5.")
for i, o in obj.items():
    if (o["volcan"], o["hora_utc"]) == ("NevadosDeChillan", "2026-10-01 05:24") and i in res:
        r = res[i]; b = r["brazos"]
        print(f"   id {i} clase {o['clase']} protegida {o['protegida']} MIROVA {o['mirova']} | O geo_linear {r['oraculo']['geo_linear'].get('npix')}px {r['oraculo']['geo_linear'].get('vrp_mw')}")
        for n in ("K", "C", "F", "FC"):
            pc = (b[n]["record"] or {}).get("primary_cluster") or {}
            print(f"     {n}: pc {pc.get('n_pixels')}px {pc.get('vrp_mw')} d9 {pc.get('d9_capped')} | F_pc_central {b[n].get('F_pc_central')} banda {b[n].get('F_pc_banda')} | pub {pub(i, n)}")
# d9 en todo el lote
for n in ("K", "F", "FC"):
    cap = [(i, obj[i]["volcan"], obj[i]["hora_utc"], obj[i]["clase"]) for i in ok
           if ((res[i]["brazos"][n]["record"] or {}).get("primary_cluster") or {}).get("d9_capped")]
    print(f"   {n}: cumulos con d9_capped: {len(cap)} {cap[:6]}")
