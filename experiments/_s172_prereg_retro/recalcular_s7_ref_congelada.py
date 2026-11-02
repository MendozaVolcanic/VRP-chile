# -*- coding: utf-8 -*-
"""Recalcula las cifras del §7 y la composicion y los cenit del §3.3 de PREREGISTRO_RETRO_PAQUETE.md con la
referencia congelada del §4.1 (la de MOD-D fase 4: consolidado de Mirova-v1 en el commit cb91eb506c37..., OCR en
cfc57c4d8bc5...; sha256 811c4c07... y 01c9478d..., S165 referencia_salida.txt), sobre un git archive de origin/main.

Vara (la del pre-registro y la del segundo verificador, contar_f26.py de experiments/_s173_aud/vpr/): etiquetador de
scripts/banco_paridad.py del export, tabla sola (source == "CONS", todas sus capas de cargar_referencia_unificada),
noche por elevacion solar del proyecto, regla SN (D-9), lectura A, pareo +-120 s, Tupungatito solo desde el 2026-02-23;
"publica" = predicado de frontend/index.html del export ejecutado con node. K = data/mirova_equivalent del export.

Las dos preguntas del instrumento:
 1. Si el script no viera lo que dice ver: corre DOS referencias. La "control" es el snapshot de origin/main (mismo blob
    00feeebc que uso el segundo verificador) y tiene que reproducir sus cifras (contar_f26_F26_salida.txt:
    26 / 30 / 32 protegidas, 48 / 18 / 13 bloques; F26M MODIS 9 protegidas y 7 bloques). Ademas, control positivo: las
    tres pasadas MODIS de Lascar de S159 tienen que salir "K no publica" con bajo1, bajo1, protegida.
 2. Si estuviera muerto: imprime filas indexadas y records; un cero aborta (assert).
Uso: python -I recalcular_s7_ref_congelada.py <export_root> <cons_congelado.csv> <ocr_congelado.csv>
"""
import collections
import hashlib
import os
import statistics
import sys
from pathlib import Path

EXPORT = Path(sys.argv[1]).resolve()
CONS_CONG, OCR_CONG = Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve()
os.environ["VRP_PROFILE"] = "mirova_equivalent"
sys.path.insert(0, str(EXPORT))
sys.path.insert(0, str(EXPORT / "scripts"))
import banco_paridad as BP  # noqa: E402
from clase_mirova import alerta_protegida  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

assert BP.ROOT == EXPORT, (BP.ROOT, EXPORT)


def sha256_lf(p):
    return hashlib.sha256(Path(p).read_bytes().replace(b"\r", b"")).hexdigest()


print("export", EXPORT, "| origin/main", (EXPORT / "COMMIT_ORIGIN_MAIN.txt").read_text().strip())
print("index.html blob", BP.sha_git(BP.HTML), "sha256 LF", sha256_lf(BP.HTML))
print("congelada: cons sha256 LF", sha256_lf(CONS_CONG), "| ocr sha256 LF", sha256_lf(OCR_CONG))
print("control (snapshot de origin/main): cons blob", BP.sha_git(BP.SNAP_CONS), "sha256 LF", sha256_lf(BP.SNAP_CONS),
      "| ocr blob", BP.sha_git(BP.SNAP_OCR), "sha256 LF", sha256_lf(BP.SNAP_OCR))
print("control identidad predicado:", BP.control_identidad_predicado())

coords = BP._coords_por_volcan()
inner = BP.inner_desde_html()


def sat(r):
    s = r["sensor"] or ""
    return "NOAA21" if "NOAA21" in s else "NOAA20" if "NOAA20" in s else "SNPP" if "SNPP" in s else "MODIS"


def med(xs):
    xs = [x for x in xs if x is not None]
    return ("%.1f" % statistics.median(xs)) if xs else "NA"


def correr(nombre, cons, ocr, inicio, fin, etiq):
    ventana = (inicio, fin)
    filas_union = cargar_referencia_unificada(cons, ocr)
    filas_tabla = [f for f in filas_union if f["source"] == "CONS"]
    por_vb, noche_sensor, noche_volcan, n_ref = BP.indexar_referencia(filas_tabla, coords, ventana, regla_minimas="SN")
    recs = BP.cargar_nuestros(coords, inner, ventana)
    BP.etiquetar(recs, por_vb, noche_sensor, noche_volcan)
    assert n_ref > 0 and len(recs) > 0, "instrumento muerto"
    recs = [r for r in recs if not (r["vol"] == "Tupungatito" and r["noche"] < "2026-02-23")]
    print("\n######## referencia %s | tramo %s %s a %s" % (nombre, etiq, inicio, fin))
    print("filas union", len(filas_union), "| tabla", len(filas_tabla), "| capas tabla",
          dict(collections.Counter(f["origen"] for f in filas_tabla)), "| filas ref nocturnas indexadas", n_ref,
          "| records nocturnos", len(recs))
    for r in recs:
        filas = BP.parear(por_vb.get((r["vol"], r["b"]), []), r["dt"])
        if r["lab"] == "pos":
            r["fina"] = ("protegida" if any(alerta_protegida(f, lectura="A") for f in filas if BP.es_alerta(f["tipo"]))
                         else "bajo1")
        else:
            r["fina"] = r["lab"]
        r["vrp_ref"] = max([f["vrp_mw"] or 0 for f in filas] or [0])
    for b in BP.BUCKETS:
        sel = [r for r in recs if r["b"] == b]
        c = collections.Counter(r["fina"] for r in sel)
        pub = collections.Counter((r["fina"], bool(r["pub"])) for r in sel)
        print("%-9s n=%5d | protegida %3d (K publica %3d) | bajo1 %3d (K publica %3d) | neg_limpio %4d (K publica %3d)"
              " | far_ref %3d | sin_info %4d (%.0f %%)" % (
                  b, len(sel), c["protegida"], pub[("protegida", True)], c["bajo1"], pub[("bajo1", True)],
                  c["neg_limpio"], pub[("neg_limpio", True)], c["far_ref"], c["sin_info"],
                  100.0 * c["sin_info"] / max(len(sel), 1)))
        pv = collections.defaultdict(collections.Counter)
        for r in sel:
            pv[r["vol"]][r["fina"]] += 1
        print("    protegidas por volcan:", {v: pv[v]["protegida"] for v in BP.VOLS if pv[v]["protegida"]})
        if b != "MODIS":
            print("    por satelite: etiquetadas (fila de la tabla, no sin_info) y sin fila, con cenit mediano (grados):")
            for s in ("NOAA20", "SNPP", "NOAA21"):
                et = [r for r in sel if sat(r) == s and r["fina"] != "sin_info"]
                sf = [r for r in sel if sat(r) == s and r["fina"] == "sin_info"]
                print("      %-6s etiquetadas %4d (cenit %s) | sin fila %4d (cenit %s)" % (
                    s, len(et), med(r["z"] for r in et), len(sf), med(r["z"] for r in sf)))
            nv = collections.Counter((r["vol"], r["noche"]) for r in sel if r["fina"] != "sin_info")
            print("    noches-volcan con 2 o mas pasadas etiquetadas:", sum(1 for v in nv.values() if v >= 2))
        bloques = collections.defaultdict(collections.Counter)
        for r in sel:
            k = (r["vol"], r["noche"])
            if r["fina"] == "bajo1" and not r["pub"]:
                bloques[k]["bajo1_perdida"] += 1
            if r["fina"] == "neg_limpio" and r["pub"]:
                bloques[k]["neg_publicado"] += 1
            if r["fina"] == "protegida" and not r["pub"]:
                bloques[k]["protegida_perdida"] += 1
        tot = collections.Counter()
        for d in bloques.values():
            tot.update(d)
        p2 = sum(1 for d in bloques.values() if d["bajo1_perdida"] or d["neg_publicado"])
        print("    bloques noche-volcan donde K yerra: %d (de P2, con bajo1 perdida o negativo publicado: %d) | eventos %s"
              % (len(bloques), p2, dict(tot)))
        for r in sorted(sel, key=lambda x: x["dt"]):
            if (r["fina"] in ("bajo1", "protegida") and not r["pub"]) or (r["fina"] == "neg_limpio" and r["pub"]):
                if b == "MODIS" or r["fina"] == "protegida":
                    print("      %s %s %s %s pub=%s pc_vrp=%s MIROVA %.2f" % (
                        r["vol"], r["dt"].strftime("%Y-%m-%d %H:%M"), r["sensor"], r["fina"], int(bool(r["pub"])),
                        r["pc_vrp"], r["vrp_ref"]))
    print("volcan-dia con record nocturno:", len({(r["vol"], r["noche"]) for r in recs}))


for nombre, cons, ocr in (("CONTROL snapshot origin/main", BP.SNAP_CONS, BP.SNAP_OCR),
                          ("CONGELADA cb91eb50 / cfc57c4d", CONS_CONG, OCR_CONG)):
    correr(nombre, cons, ocr, "2026-02-01", "2026-03-31", "F26")
    correr(nombre, cons, ocr, "2026-02-01", "2026-02-28", "F26M")
