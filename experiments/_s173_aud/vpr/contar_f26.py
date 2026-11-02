# -*- coding: utf-8 -*-
"""Cuenta, con el etiquetador del proyecto (scripts/banco_paridad.py de origin/main exportado) y el predicado del
tablero ejecutado con node, lo que el pre-registro afirma en §3.2 y §7 sobre F26: protegidas por sensor y volcan,
bajo 1 MW, negativos limpios, lo que K publica, y los bloques noche-volcan donde K yerra.

Vara: tabla sola (source == "CONS", todas las capas de cargar_referencia_unificada), noche por elevacion solar del
proyecto, regla SN (D-9), lectura A (alerta del scraper con VRP >= 1 MW), pareo a +-120 s. Tupungatito solo desde
el 2026-02-23. Referencia: la copia del worktree (consolidado sha ab1a208c..., OCR d4ad8c44...), instalada en el
export. K: data/mirova_equivalent/ de origin/main (COMMIT_ORIGIN_MAIN.txt).

Las dos preguntas:
 1. Si K perdiera protegidas o publicara en negativos y esto no lo viera: el predicado es el del tablero via node, y el
    control positivo es que las tres pasadas MODIS de febrero que S159 nombro (Lascar 02-11 01:20, 02-11 07:00, 02-16
    01:20) salgan aqui como "K no publica" con sus etiquetas (bajo1, bajo1, protegida).
 2. Si el instrumento estuviera muerto: imprime el numero de records y de filas de referencia indexadas; un cero ahi
    delata; y el control de identidad del predicado (control_identidad_predicado) corre antes.
Uso: python contar_f26.py <export_root> <inicio> <fin> [etiqueta]
"""
import collections
import json
import os
import sys
from pathlib import Path

EXPORT = Path(sys.argv[1])
INICIO, FIN = sys.argv[2], sys.argv[3]
ETIQ = sys.argv[4] if len(sys.argv) > 4 else "ventana"
os.environ["VRP_PROFILE"] = "mirova_equivalent"
sys.path.insert(0, str(EXPORT))
sys.path.insert(0, str(EXPORT / "scripts"))
import banco_paridad as BP  # noqa: E402
from clase_mirova import alerta_protegida  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

assert BP.ROOT == EXPORT, (BP.ROOT, EXPORT)
assert BP.DATA == EXPORT / "data" / "mirova_equivalent"
print("export", EXPORT, "commit", (EXPORT / "COMMIT_ORIGIN_MAIN.txt").read_text().strip())
print("sha index.html", BP.sha_git(BP.HTML), "| cons", BP.sha_git(BP.SNAP_CONS), "| ocr", BP.sha_git(BP.SNAP_OCR))
ident = BP.control_identidad_predicado()
print("control identidad predicado:", ident)

ventana = (INICIO, FIN)
coords = BP._coords_por_volcan()
inner = BP.inner_desde_html()
filas_union = cargar_referencia_unificada(BP.SNAP_CONS, BP.SNAP_OCR)
filas_tabla = [f for f in filas_union if f["source"] == "CONS"]
print("filas union", len(filas_union), "| filas tabla (CONS, todas las capas)", len(filas_tabla),
      "| capas CONS:", dict(collections.Counter(f["origen"] for f in filas_tabla)))

por_vb, noche_sensor, noche_volcan, n_ref = BP.indexar_referencia(filas_tabla, coords, ventana, regla_minimas="SN")
recs = BP.cargar_nuestros(coords, inner, ventana)
BP.etiquetar(recs, por_vb, noche_sensor, noche_volcan)
print("filas ref nocturnas indexadas", n_ref, "| records nocturnos nuestros", len(recs))
assert n_ref > 0 and len(recs) > 0, "instrumento muerto"

# Tupungatito: la referencia no lo tiene antes del 02-14 y rotulaba con 5 km hasta el 02-23 (hitos A119)
recs = [r for r in recs if not (r["vol"] == "Tupungatito" and r["noche"] < "2026-02-23")]

# etiqueta fina: protegida / bajo1 / neg_limpio / far_ref / sin_info ; y que hace K
def etiqueta_fina(r):
    filas = BP.parear(por_vb.get((r["vol"], r["b"]), []), r["dt"])
    if r["lab"] == "pos":
        return "protegida" if any(alerta_protegida(f, lectura="A") for f in filas if BP.es_alerta(f["tipo"])) else "bajo1"
    return r["lab"]

for r in recs:
    r["fina"] = etiqueta_fina(r)
    r["vrp_ref"] = max([f["vrp_mw"] or 0 for f in BP.parear(por_vb.get((r["vol"], r["b"]), []), r["dt"])] or [0])

sat = lambda r: ("NOAA21" if "NOAA21" in (r["sensor"] or "") else "NOAA20" if "NOAA20" in (r["sensor"] or "")
                 else "SNPP" if "SNPP" in (r["sensor"] or "") else "MODIS")
print("\n== %s %s a %s | etiquetas por sensor (K de disco, predicado node) ==" % (ETIQ, INICIO, FIN))
for b in BP.BUCKETS:
    sel = [r for r in recs if r["b"] == b]
    c = collections.Counter(r["fina"] for r in sel)
    pub = collections.Counter((r["fina"], bool(r["pub"])) for r in sel)
    print("%-9s n=%5d | protegida %3d (K publica %3d) | bajo1 %3d (K publica %3d) | neg_limpio %4d (K publica %3d) | far_ref %3d | sin_info %4d" % (
        b, len(sel), c["protegida"], pub[("protegida", True)], c["bajo1"], pub[("bajo1", True)],
        c["neg_limpio"], pub[("neg_limpio", True)], c["far_ref"], c["sin_info"]))
    por_vol = collections.defaultdict(collections.Counter)
    for r in sel:
        por_vol[r["vol"]][r["fina"]] += 1
        if r["fina"] == "protegida" and r["pub"]:
            por_vol[r["vol"]]["protegida_pubK"] += 1
    for v in BP.VOLS:
        d = por_vol[v]
        if d["protegida"] or d["bajo1"]:
            print("    %-20s protegida %3d (K pub %3d) bajo1 %3d neg_limpio %4d sin_info %4d" % (
                v, d["protegida"], d["protegida_pubK"], d["bajo1"], d["neg_limpio"], d["sin_info"]))
    if b != "MODIS":
        cs = collections.Counter((sat(r), r["fina"] == "sin_info") for r in sel)
        print("    por satelite (sat, sin_info?):", dict(cs))
    # bloques donde K yerra (E de D-45: bajo1 no publicada + neg_limpio publicada; P1: protegida no publicada)
    bloques = collections.defaultdict(lambda: collections.Counter())
    for r in sel:
        k = (r["vol"], r["noche"])
        if r["fina"] == "bajo1" and not r["pub"]:
            bloques[k]["bajo1_perdida"] += 1
        if r["fina"] == "neg_limpio" and r["pub"]:
            bloques[k]["neg_publicado"] += 1
        if r["fina"] == "protegida" and not r["pub"]:
            bloques[k]["protegida_perdida"] += 1
    tot = collections.Counter()
    for k, d in bloques.items():
        tot.update(d)
    print("    bloques noche-volcan donde K yerra: %d | eventos: %s" % (len(bloques), dict(tot)))
    for r in sorted(sel, key=lambda x: x["dt"]):
        if r["fina"] == "protegida" and not r["pub"]:
            print("      K NO publica protegida: %s %s %s MIROVA %.2f MW pc_vrp=%s dc=%s pc_dist=%s" % (
                r["vol"], r["dt"].strftime("%Y-%m-%d %H:%M"), r["sensor"], r["vrp_ref"], r["pc_vrp"], r["dc"], r["pc_dist"]))
    if b == "MODIS":
        for r in sorted(sel, key=lambda x: x["dt"]):
            if r["fina"] in ("bajo1", "protegida") and not r["pub"]:
                print("      [control positivo S159] K no publica alerta: %s %s %s %s MIROVA %.2f" % (
                    r["vol"], r["dt"].strftime("%Y-%m-%d %H:%M"), r["sensor"], r["fina"], r["vrp_ref"]))
    # shas de codigo de K en el tramo
    print("    codigo_sha de los records:", dict(collections.Counter(r["sha"] for r in sel)))

# noches-volcan (unidad del operador), por sensor
print("\n== volcan-dia con record nocturno (cualquier sensor):", len({(r["vol"], r["noche"]) for r in recs}))
json.dump([{k: (v.isoformat() if hasattr(v, "isoformat") else v) for k, v in r.items()} for r in recs],
          open(Path(__file__).with_name("contar_f26_%s_recs.json" % ETIQ), "w", encoding="utf-8"))
