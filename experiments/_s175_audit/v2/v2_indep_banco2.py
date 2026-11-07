#!/usr/bin/env python
"""V2 S175, parte 2: estratos que el auditor no abrio. F2-201/202 por fuente de la fila protegida (tabla contra OCR) y
F2-203 por origen del negativo limpio (RUTINA siempre, o alerta minima D-9 convertida).

P1 (si lo medido estuviera roto, lo veria): control positivo: el conteo de negativos que vienen de D-9 se compara con la
   cifra del auditor para la regla "original" (pos->neg_limpio: 39+16=55 en total, pub 39): si no coincide, el script esta mal.
P2 (instrumento muerto): se imprime cada denominador; la comparacion original contra SN se hace por clave (vol,sensor,dt).
Ventana 2026-03-01..2026-11-07; denominadores: pasadas V375 nocturnas con record nuestro.
Uso: python v2_indep_banco2.py <arbol> <ini> <fin> <salida.txt>
"""
import collections, os, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
ARBOL = Path(sys.argv[1]).resolve(); INI, FIN = sys.argv[2], sys.argv[3]; OUT = Path(sys.argv[4])
sys.path.insert(0, str(ARBOL / "scripts")); sys.path.insert(0, str(ARBOL))
os.environ["VRP_PROFILE"] = "mirova_equivalent"
import banco_paridad as bp  # noqa: E402
import clase_mirova as cm  # noqa: E402
from referencia_mirova_unificada import SNAP_CONS, SNAP_OCR, cargar_referencia_unificada  # noqa: E402
from scipy.stats import fisher_exact  # noqa: E402
L = []


def P(s=""):
    L.append(s); print(s)


coords = bp._coords_por_volcan(); inner = bp.inner_desde_html()
filas = cargar_referencia_unificada(SNAP_CONS, SNAP_OCR)
base = bp.cargar_nuestros(coords, inner, (INI, FIN))
res = {}
for regla in ("SN", "original"):
    por_vb, ns, nv, n = bp.indexar_referencia(filas, coords, (INI, FIN), regla_minimas=regla)
    rr = [dict(r) for r in base]
    bp.etiquetar(rr, por_vb, ns, nv)
    for r in rr:
        par = bp.parear(por_vb.get((r["vol"], r["b"]), []), r["dt"])
        r["q_src"] = sorted({f["source"] for f in par if cm.alerta_protegida(f)})
    res[regla] = {(r["vol"], r["sensor"], r["dt"]): r for r in rr if r["b"] == "VIIRS375"}
sn, og = res["SN"], res["original"]
P(f"V375 records {len(sn)} (SN) {len(og)} (original)")

# --- F2-201/202 por fuente
prot = [r for r in sn.values() if r["q_src"]]
for nombre, sel in (("TODAS", prot), ("SOLO OCR", [r for r in prot if r["q_src"] == ["OCR"]]),
                    ("CON TABLA", [r for r in prot if "CONS" in r["q_src"]])):
    a = [r for r in sel if (r["z"] or 0) >= 50]; b = [r for r in sel if (r["z"] or 0) < 50]
    la, lb = sum(1 - r["pub"] for r in a), sum(1 - r["pub"] for r in b)
    P(f"{nombre}: n {len(sel)} | z>=50: {la}/{len(a)}  z<50: {lb}/{len(b)}"
      + (f" | Fisher p {fisher_exact([[la, len(a)-la],[lb, len(b)-lb]])[1]:.4f}" if len(sel) and len(a) and len(b) else " | SIN DATO"))
solo = [r for r in prot if r["q_src"] == ["OCR"]]
for s in ("VIIRS_NOAA20", "VIIRS_NOAA21", "VIIRS_SNPP"):
    x = [r for r in solo if r["sensor"] == s]
    P(f"  SOLO OCR {s}: perdidas {sum(1-r['pub'] for r in x)}/{len(x)}")
a = [r for r in solo if r["sensor"] == "VIIRS_SNPP"]; b = [r for r in solo if r["sensor"] != "VIIRS_SNPP"]
la, lb = sum(1 - r["pub"] for r in a), sum(1 - r["pub"] for r in b)
P(f"  SOLO OCR SNPP {la}/{len(a)} contra otras {lb}/{len(b)}: Fisher p {fisher_exact([[la,len(a)-la],[lb,len(b)-lb]])[1]:.4f}")
# antes y despues de las correcciones del OCR (2026-06-11 geometria, 2026-10-09 SNPP)
for corte in ("2026-06-11", "2026-10-09"):
    x = [r for r in solo if r["noche"] < corte]; y = [r for r in solo if r["noche"] >= corte]
    P(f"  SOLO OCR antes de {corte}: perdidas {sum(1-r['pub'] for r in x)}/{len(x)} | desde: {sum(1-r['pub'] for r in y)}/{len(y)}")
# la fila OCR perdida: VRP vs lo que publicamos (pc_vrp) y la distancia del OCR
P("  perdidas: vrp OCR y lo nuestro")
for r in solo:
    if not r["pub"]:
        par = bp.parear(bp.indexar_referencia(filas, coords, (INI, FIN), regla_minimas="SN")[0].get((r["vol"], "VIIRS375"), []), r["dt"])
        P(f"    {r['vol']} {r['dt']:%m-%d %H:%M} {r['sensor']} ocr_vrp {[f['vrp_mw'] for f in par]} dist_ocr {[f['dist_km'] for f in par]} "
          f"nuestro dc {r['dc']} pc_vrp {r['pc_vrp']} pc_dist {r['pc_dist']} inner {inner[r['vol']]}")

# --- F2-203: origen de los negativos limpios publicados
neg = [r for r in sn.values() if r["lab"] == "neg_limpio"]
tabla = collections.defaultdict(lambda: collections.Counter())
for r in neg:
    o = og[(r["vol"], r["sensor"], r["dt"])]
    origen = "RUTINA_original" if o["lab"] == "neg_limpio" else f"D9_desde_{o['lab']}"
    tabla[r["vol"]][origen] += 1
    tabla[r["vol"]][origen + "_pub"] += r["pub"]
P("NEGATIVOS LIMPIOS por origen (n / publicados):")
tot = collections.Counter()
for vol in bp.VOLS:
    c = tabla[vol]; tot.update(c)
    P(f"  {vol:20s} " + " | ".join(f"{k} {c[k]}/{c[k+'_pub']}" for k in sorted(c) if not k.endswith("_pub")))
P("  TOTAL " + " | ".join(f"{k} {tot[k]}/{tot[k+'_pub']}" for k in sorted(tot) if not k.endswith("_pub")))
orig_neg = [r for r in neg if og[(r["vol"], r["sensor"], r["dt"])]["lab"] == "neg_limpio"]
P(f"  sobre-publicacion solo con negativos limpios de la regla original: {sum(r['pub'] for r in orig_neg)}/{len(orig_neg)} = {sum(r['pub'] for r in orig_neg)/len(orig_neg):.4f}")
for vol in ("Lastarria", "PuyehueCordonCaulle"):
    x = [r for r in orig_neg if r["vol"] == vol]
    P(f"  {vol} con negativos de la regla original: {sum(r['pub'] for r in x)}/{len(x)} = {sum(r['pub'] for r in x)/len(x):.4f}")
# placebo: negativos limpios de volcan x tramo de calidad de tabla (tabla antes/desde 2026-04-01)
for vol in ("Lastarria", "PuyehueCordonCaulle"):
    for corte in ("2026-04-01", "2026-08-06"):
        x = [r for r in neg if r["vol"] == vol and r["noche"] < corte]; y = [r for r in neg if r["vol"] == vol and r["noche"] >= corte]
        P(f"  {vol} antes de {corte}: {sum(r['pub'] for r in x)}/{len(x)} | desde: {sum(r['pub'] for r in y)}/{len(y)}")
# control: la cifra del auditor para pos->neg_limpio (regla original) debe aparecer
cam = collections.Counter()
for k, r in sn.items():
    o = og[k]
    if o["lab"] != r["lab"]:
        cam[f"{o['lab']}->{r['lab']}|pub={r['pub']}"] += 1
P(f"CONTROL (cifra del auditor 39/16 pos->neg_limpio): {dict(cam)}")
OUT.write_text("\n".join(L) + "\n", encoding="utf-8")
