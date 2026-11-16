#!/usr/bin/env python
"""V2 S175: verificacion independiente de F2-201, F2-202, F2-203 (otro camino que el del auditor).

Reutiliza SOLO las funciones de la vara (banco_paridad.cargar_nuestros / indexar_referencia / parear / etiquetar,
clase_mirova.alerta_protegida) del arbol del commit 752d348bc; todos los conteos, estratos y pruebas son propios.

P1 (si lo medido estuviera roto, lo veria): control positivo: se fuerza pub=1 a las 5 perdidas y el recall tiene que
   subir a 171/171; control nulo: se permutan las etiquetas de cenit y la razon de perdidas debe perder la brecha.
P2 (instrumento muerto): cada denominador se imprime; un denominador 0 se escribe SIN DATO. Si cargar_nuestros
   devolviera 0 records, el script aborta.
Ventana: 2026-03-01 a 2026-11-07 (la de la afirmacion). Denominadores: pasadas V375 nocturnas con record nuestro.
Uso: python v2_indep_banco.py <arbol> <ini> <fin> <salida.txt>
"""
import collections, itertools, json, math, os, random, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ARBOL = Path(sys.argv[1]).resolve(); INI, FIN = sys.argv[2], sys.argv[3]; OUT = Path(sys.argv[4])
sys.path.insert(0, str(ARBOL / "scripts")); sys.path.insert(0, str(ARBOL))
os.environ["VRP_PROFILE"] = "mirova_equivalent"
import banco_paridad as bp  # noqa: E402
import clase_mirova as cm  # noqa: E402
from referencia_mirova_unificada import SNAP_CONS, SNAP_OCR, cargar_referencia_unificada  # noqa: E402
from scipy.stats import fisher_exact  # noqa: E402
assert Path(bp.__file__).resolve().is_relative_to(ARBOL)
L = []


def P(s=""):
    L.append(s); print(s)


def wilson(k, n, z=1.96):
    if n == 0:
        return (None, None)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (round(c - h, 4), round(c + h, 4))


coords = bp._coords_por_volcan(); inner = bp.inner_desde_html()
filas = cargar_referencia_unificada(SNAP_CONS, SNAP_OCR)
recs = bp.cargar_nuestros(coords, inner, (INI, FIN))
assert len(recs) > 1000, "instrumento muerto: pocos records"
por_vb, ns, nv, n_ref = bp.indexar_referencia(filas, coords, (INI, FIN), regla_minimas="SN")
bp.etiquetar(recs, por_vb, ns, nv)
v = [r for r in recs if r["b"] == "VIIRS375"]
P(f"records nocturnos {len(recs)} | V375 {len(v)} | filas ref nocturnas SN {n_ref} | ventana {INI}..{FIN}")

# --- identidad de la pasada: (vol, sensor, dt) debe ser unica
claves = collections.Counter((r["vol"], r["sensor"], r["dt"]) for r in v)
P(f"duplicados (vol,sensor,dt) entre records V375: {sum(1 for c in claves.values() if c > 1)}")
claves_t = collections.Counter((r["vol"], r["dt"]) for r in v)
P(f"pasadas (vol,dt) con 2 records de plataformas distintas: {sum(1 for c in claves_t.values() if c > 1)}")

# --- protegidas: fuentes de las filas que la hacen protegida
for r in v:
    par = bp.parear(por_vb.get((r["vol"], r["b"]), []), r["dt"])
    q = [f for f in par if cm.alerta_protegida(f)]
    r["q_src"] = sorted({f["source"] for f in q})
    r["n_filas_par"] = len(par)
prot = [r for r in v if r["q_src"]]
P(f"protegidas (record con fila protegida A pareada): {len(prot)}  (auditor: 171)  | con lab=='pos': {sum(1 for r in prot if r['lab']=='pos')}")
P(f"  publicadas {sum(r['pub'] for r in prot)}  recall {sum(r['pub'] for r in prot)}/{len(prot)}")
fuente = collections.Counter(tuple(r["q_src"]) for r in prot)
P(f"  fuentes de la fila protegida: {dict(fuente)}")
for k in fuente:
    sel = [r for r in prot if tuple(r["q_src"]) == k]
    P(f"    fuente {k}: n {len(sel)} publicadas {sum(r['pub'] for r in sel)} perdidas {sum(1-r['pub'] for r in sel)}")
solo_tabla = [r for r in prot if "CONS" in r["q_src"]]
P(f"  SOLO TABLA (alguna fila CONS protegida): n {len(solo_tabla)} publicadas {sum(r['pub'] for r in solo_tabla)} "
  f"-> perdidas {sum(1-r['pub'] for r in solo_tabla)}")
solo_ocr = [r for r in prot if r["q_src"] == ["OCR"]]
P(f"  SOLO OCR: n {len(solo_ocr)} perdidas {sum(1-r['pub'] for r in solo_ocr)} "
  f"tasa perdida {sum(1-r['pub'] for r in solo_ocr)}/{len(solo_ocr)}  Wilson {wilson(sum(1-r['pub'] for r in solo_ocr), len(solo_ocr))}")
P("  perdidas (vol, pasada, plataforma, cenit, fuente, tramo):")
for r in prot:
    if not r["pub"]:
        P(f"    {r['vol']:12s} {r['dt']:%Y-%m-%d %H:%M} {r['sensor']:13s} z {r['z']} src {r['q_src']} tramo {r['perfil']} n_filas_par {r['n_filas_par']}")

# --- control positivo: forzar publicadas las perdidas
prot_f = [dict(r, pub=1) if not r["pub"] else r for r in prot]
P(f"CONTROL positivo: forzando pub=1 en las perdidas, recall = {sum(r['pub'] for r in prot_f)}/{len(prot_f)}")

# --- noche: laxa (auditor) y estricta (pasada protegida publicada)
noches_l = collections.defaultdict(lambda: {"prot": False, "pub_any": 0, "pub_prot": 0})
for r in v:
    e = noches_l[(r["vol"], r["noche"])]
    if r["q_src"] and r["lab"] == "pos":
        e["prot"] = True
        e["pub_prot"] = max(e["pub_prot"], r["pub"])
    e["pub_any"] = max(e["pub_any"], r["pub"])
nn = [e for e in noches_l.values() if e["prot"]]
P(f"NOCHES con protegida: {len(nn)} | publicada si CUALQUIER pasada de la noche publica: {sum(e['pub_any'] for e in nn)} "
  f"| estricto (una pasada protegida publica): {sum(e['pub_prot'] for e in nn)}")
for k, e in noches_l.items():
    if e["prot"] and not e["pub_prot"]:
        P(f"   noche con protegida SIN pasada protegida publicada: {k} pub_any {e['pub_any']}")

# --- F2-202: cenit y plataforma
def tab(sel, pred):
    a = sum(1 for r in sel if pred(r) and not r["pub"]); b = sum(1 for r in sel if pred(r) and r["pub"])
    c = sum(1 for r in sel if not pred(r) and not r["pub"]); d = sum(1 for r in sel if not pred(r) and r["pub"])
    return a, b, c, d
for nombre, pred in (("z>=50", lambda r: (r["z"] or 0) >= 50), ("z>=60", lambda r: (r["z"] or 0) >= 60),
                     ("SNPP", lambda r: r["sensor"] == "VIIRS_SNPP")):
    a, b, c, d = tab(prot, pred)
    o2, p2 = fisher_exact([[a, b], [c, d]]); o1, p1 = fisher_exact([[a, b], [c, d]], alternative="greater")
    P(f"F2-202 {nombre}: perdidas/n dentro {a}/{a+b}  fuera {c}/{c+d} | Fisher dos colas p {p2:.4f} una cola p {p1:.4f} "
      f"| Wilson dentro {wilson(a,a+b)} fuera {wilson(c,c+d)}")
P("  tabla cenit x plataforma (perdidas/n) entre protegidas:")
for zb in ("z<50", "z>=50"):
    row = []
    for s in ("VIIRS_NOAA20", "VIIRS_NOAA21", "VIIRS_SNPP"):
        sel = [r for r in prot if r["sensor"] == s and (((r["z"] or 0) >= 50) == (zb == "z>=50"))]
        row.append(f"{s}: {sum(1-r['pub'] for r in sel)}/{len(sel)}")
    P(f"    {zb:6s} " + " | ".join(row))
# SNPP: distribucion de cenit de las protegidas (confusion cenit-plataforma)
for s in ("VIIRS_NOAA20", "VIIRS_NOAA21", "VIIRS_SNPP"):
    zs = sorted(r["z"] for r in prot if r["sensor"] == s and r["z"] is not None)
    P(f"    cenit protegidas {s}: n {len(zs)} mediana {zs[len(zs)//2]:.1f} fraccion >=50: {sum(1 for z in zs if z>=50)/len(zs):.2f}")
# permutacion: etiqueta de cenit permutada dentro de cada volcan (placebo nulo)
random.seed(175)
obs = tab(prot, lambda r: (r["z"] or 0) >= 50)[0]
ge = 0
N = 5000
for _ in range(N):
    by = collections.defaultdict(list)
    for r in prot:
        by[r["vol"]].append(r)
    cnt = 0
    for vol, lst in by.items():
        zs = [r["z"] for r in lst]; random.shuffle(zs)
        cnt += sum(1 for r, z in zip(lst, zs) if (z or 0) >= 50 and not r["pub"])
    ge += cnt >= obs
P(f"  permutacion de cenit DENTRO de cada volcan ({N}): P(perdidas con z>=50 >= {obs}) = {ge/N:.4f}")

# --- F2-203: sobre-publicacion en negativos limpios
neg = [r for r in v if r["lab"] == "neg_limpio"]
P(f"NEGATIVOS LIMPIOS pasadas: {len(neg)} publicadas {sum(r['pub'] for r in neg)} = {sum(r['pub'] for r in neg)/len(neg):.4f}  Wilson {wilson(sum(r['pub'] for r in neg), len(neg))}")
for vol in bp.VOLS:
    s = [r for r in neg if r["vol"] == vol]
    k = sum(r["pub"] for r in s)
    nights = {r["noche"] for r in s}
    P(f"  {vol:20s} n {len(s):4d} pub {k:3d} tasa {k/len(s) if s else None!s:.8} Wilson {wilson(k,len(s))} noches con neg_limpio {len(nights)}")
# noches: definicion del auditor y la estricta (solo pasadas neg_limpio cuentan para publicar)
nn2 = collections.defaultdict(lambda: {"labs": set(), "pub_any": 0, "pub_neg": 0})
for r in v:
    e = nn2[(r["vol"], r["noche"])]
    e["labs"].add(r["lab"]); e["pub_any"] = max(e["pub_any"], r["pub"])
    if r["lab"] == "neg_limpio":
        e["pub_neg"] = max(e["pub_neg"], r["pub"])
nev = {k: e for k, e in nn2.items() if "pos" not in e["labs"] and "neg_limpio" in e["labs"] and "far_ref" not in e["labs"]}
P(f"NOCHES negativas (def. auditor): {len(nev)} | pub si cualquier pasada publica: {sum(e['pub_any'] for e in nev.values())} "
  f"= {sum(e['pub_any'] for e in nev.values())/len(nev):.4f} | pub si la pasada neg_limpio publica: {sum(e['pub_neg'] for e in nev.values())} "
  f"= {sum(e['pub_neg'] for e in nev.values())/len(nev):.4f}")
for vol in ("Lastarria", "PuyehueCordonCaulle"):
    s = {k: e for k, e in nev.items() if k[0] == vol}
    P(f"  {vol}: noches {len(s)} cualquier {sum(e['pub_any'] for e in s.values())} ({sum(e['pub_any'] for e in s.values())/len(s):.4f}) "
      f"| pasada neg_limpio {sum(e['pub_neg'] for e in s.values())} ({sum(e['pub_neg'] for e in s.values())/len(s):.4f})")
P("  Lastarria por mes (pasadas neg_limpio pub/n):")
for m in sorted({r["noche"][:7] for r in neg if r["vol"] == "Lastarria"}):
    s = [r for r in neg if r["vol"] == "Lastarria" and r["noche"][:7] == m]
    P(f"    {m}: {sum(r['pub'] for r in s)}/{len(s)}")
P("  Lastarria publicados en neg_limpio: display MW y dc")
sd = collections.Counter()
for r in neg:
    if r["vol"] == "Lastarria" and r["pub"]:
        sd[(r["dc"], "disp<0.1" if (r["disp"] or 0) < .1 else "disp>=0.1")] += 1
P(f"    {dict(sd)}")
# control nulo del instrumento: si pub se permuta, la tasa de Lastarria debe converger a la global
random.seed(7)
pubs = [r["pub"] for r in neg]
tas = []
for _ in range(2000):
    random.shuffle(pubs)
    tas.append(sum(p for r, p in zip(neg, pubs) if r["vol"] == "Lastarria") / sum(1 for r in neg if r["vol"] == "Lastarria"))
P(f"CONTROL nulo: pub permutado entre neg_limpio, tasa Lastarria media {sum(tas)/len(tas):.4f} max {max(tas):.4f} (observada 0.2565): "
  f"P(>=observada) = {sum(1 for t in tas if t >= 49/191)/len(tas):.4f}")
OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
