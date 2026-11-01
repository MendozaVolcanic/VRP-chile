# -*- coding: utf-8 -*-
"""S159, negativo limpio con crater: cuantos negativos limpios y cuantas publicaciones de K cambian con la regla NLC.

Las dos preguntas del instrumento (comunes a todo el script):
P1 (si lo que mido estuviera roto, lo veria?): la regla depende de que el indicador de anillo diga donde esta el
   crater. §1 lo valida contra la referencia (tasa de alerta de MIROVA por tramo de f) y contra una medicion
   independiente (posicion del cumulo); si el indicador fuera ruido, la tasa de alerta seria plana en f.
P2 (instrumento muerto?): se imprime cuantas cadenas de dos hay, cuantas f indeterminadas y cuantos records solos;
   si el campo estuviera muerto todo seria «indet» y la regla no sacaria nada: eso se veria como indet masivo, no
   como cero limpio. Controles positivos en §5 (casos que tienen que salir) y nulo (records solos: se quedan todos).

Uso: python -I medir.py <espejo de origin/main> [--n D:\\vrp-trabajo\\temporales\\s159_n]
"""
import argparse
import collections
import json
import os
import statistics
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
ap = argparse.ArgumentParser()
ap.add_argument("raiz")
ap.add_argument("--n", default=None)
A = ap.parse_args()
RAIZ = Path(A.raiz)
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(RAIZ)); sys.path.insert(0, str(RAIZ / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import banco_paridad as bp  # noqa: E402
import auto_audit_weekly as aw  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada, SNAP_CONS, SNAP_OCR  # noqa: E402
import nlc  # noqa: E402

assert Path(bp.DATA).resolve().is_relative_to(RAIZ.resolve()), f"banco lee otro data: {bp.DATA}"
print("banco lee:", bp.DATA)
NBG, COMP, LARGOS = nlc.indice_anillo(bp.DATA, bp.VOLS)
print("P2: cadenas por largo (toda la historia, 11 Tier A, todos los sensores):", dict(LARGOS))
print("P2: records con diag_n_bg_anillo None:", sum(v is None for v in NBG.values()), "de", len(NBG))
COORDS = aw._coords_por_volcan()
INNER = bp.inner_desde_html()
FILAS = cargar_referencia_unificada(SNAP_CONS, SNAP_OCR)
print("referencia: filas", len(FILAS), "ultima fecha", max(f["fecha_utc"] for f in FILAS))


def clave(r):
    return (r["vol"], r["sensor"], r["dt"].strftime("%Y-%m-%d %H:%M"))


def filas_dt(por_vb, r, tol):
    lista = por_vb.get((r["vol"], r["b"]), [])
    return [t for t, _ in lista if abs((t - r["dt"]).total_seconds()) <= tol]


def banco(ventana, regla="original", tol=bp.TOL_S):
    por_vb, ns, nv, n = bp.indexar_referencia(FILAS, COORDS, ventana, regla_minimas=regla)
    recs = bp.cargar_nuestros(COORDS, INNER, ventana)
    orig = bp.parear
    if tol != bp.TOL_S:
        bp.parear = lambda lista, t, tol_=tol: orig(lista, t, tol_)
    try:
        bp.etiquetar(recs, por_vb, ns, nv)
    finally:
        bp.parear = orig
    return recs, por_vb


def aplicar_nlc(recs, por_vb, tol=bp.TOL_S, corte=0.5):
    idx = {clave(r): r for r in recs}
    for r in recs:
        r["nlc"] = None
        if r["lab"] != "neg_limpio":
            continue
        queda, motivo = nlc.crater_en_granulo_mirova(clave(r), filas_dt(por_vb, r, tol), r["dt"], NBG, COMP, corte)
        r["nlc"], r["nlc_motivo"] = queda, motivo
        q = COMP.get(clave(r))
        r["pub_comp"] = idx[q]["pub"] if q in idx else None
    return recs


def tabla(recs, filtro, titulo):
    print(f"\n--- {titulo}")
    print(f"{'sensor':<9} {'neg viejo':>9} {'pub viejo':>9} {'%':>6} | {'neg nuevo':>9} {'pub nuevo':>9} {'%':>6} | "
          f"{'salen':>5} {'pub que sale':>12} {'pub del compañero':>17} | motivos de los que salen")
    out = {}
    for b in bp.BUCKETS:
        neg = [r for r in recs if r["b"] == b and r["lab"] == "neg_limpio" and filtro(r)]
        nue = [r for r in neg if r["nlc"]]
        sal = [r for r in neg if not r["nlc"]]
        pv, pn, ps = sum(r["pub"] for r in neg), sum(r["pub"] for r in nue), sum(r["pub"] for r in sal)
        pc = sum(1 for r in sal if r.get("pub_comp"))
        mot = collections.Counter(r["nlc_motivo"] for r in sal)
        print(f"{b:<9} {len(neg):>9} {pv:>9} {100*pv/max(len(neg),1):>6.2f} | {len(nue):>9} {pn:>9} "
              f"{100*pn/max(len(nue),1):>6.2f} | {len(sal):>5} {ps:>12} {pc:>17} | {dict(mot)}")
        quedan = collections.Counter(r["nlc_motivo"] for r in nue)
        print(f"{'':<9} quedan por motivo: {dict(quedan)}")
        for r in sal:
            if r["pub"] or r.get("pub_comp"):
                print(f"{'':<9}   sale con publicacion: {r['vol']} {r['sensor']} {r['dt']:%Y-%m-%d %H:%M} "
                      f"pub_propio={r['pub']} pub_compañero={r.get('pub_comp')} motivo={r['nlc_motivo']} "
                      f"f={nlc.fraccion(clave(r), NBG, COMP)}")
        out[b] = {"neg_viejo": len(neg), "pub_viejo": pv, "neg_nuevo": len(nue), "pub_nuevo": pn,
                  "salen": len(sal), "pub_que_sale": ps, "pub_compañero_de_los_que_salen": pc}
    return out


RES = {}

# ---------------------------------------------------------------- §1 el corte contra la referencia (A115)
print("\n=== §1 corte: tasa de alerta de MIROVA por tramo de f (cadenas de dos con UN solo granulo listado a +-120 s)")
print("Ventana 2026-01-10 a 2026-10-21, regla original, nocturnas. P1: si f no dijera donde esta el crater, la tasa"
      " seria plana en f.")
recs1, por_vb1 = banco(("2026-01-10", "2026-10-21"))
idx1 = {clave(r): r for r in recs1}
tramos = [(0, .2), (.2, .4), (.4, .5), (.5, .6), (.6, .8), (.8, 1.0001)]
cont = collections.defaultdict(lambda: collections.Counter())
fmin_alerta = collections.defaultdict(list)
for r in recs1:
    k = clave(r)
    q = COMP.get(k)
    if q is None or q not in idx1:
        continue
    mia = bp.parear(por_vb1.get((r["vol"], r["b"]), []), r["dt"])
    suya = bp.parear(por_vb1.get((r["vol"], r["b"]), []), idx1[q]["dt"])
    if not mia or suya:          # r es el unico miembro listado
        continue
    f = nlc.fraccion(k, NBG, COMP)
    if f in (None, "indet"):
        cont[r["b"]]["indet"] += 1
        continue
    al = any(bp.es_alerta(x["tipo"]) for x in mia)
    for lo, hi in tramos:
        if lo <= f < hi:
            cont[r["b"]][(lo, "n")] += 1
            cont[r["b"]][(lo, "al")] += al
    if al:
        fmin_alerta[r["b"]].append(round(f, 3))
for b in bp.BUCKETS:
    c = cont[b]
    print(b, " | ".join(f"[{lo:.1f},{min(hi,1):.1f}) {c[(lo,'al')]}/{c[(lo,'n')]}" for lo, hi in tramos),
          "| indet", c["indet"], "| f de las alertas, ordenadas:", sorted(fmin_alerta[b])[:8], "...")
# P1 independiente: miembro de partida con cumulo con VRP > 0 a menos de 3 km -> f >= 0,5?
ok = collections.Counter()
for r in recs1:
    k = clave(r)
    f = nlc.fraccion(k, NBG, COMP)
    if f in (None, "indet"):
        continue
    if (r["pc_vrp"] or 0) > 0 and r["pc_dist"] is not None and r["pc_dist"] < 3:
        ok[(r["b"], f >= 0.5)] += 1
print("P1 independiente (cumulo con VRP>0 a <3 km en un miembro de partida): f>=0,5 en",
      {b: f"{ok[(b, True)]} de {ok[(b, True)] + ok[(b, False)]}" for b in bp.BUCKETS})

# ---------------------------------------------------------------- §2 ventana del verificador (contexto)
aplicar_nlc(recs1, por_vb1)
RES["verificador_0110_original"] = tabla(recs1, lambda r: True,
                                         "§2 ventana 2026-01-10 a 2026-10-21, regla D-9 original, todos los detectores")
for corte in (0.4, 0.6):
    aplicar_nlc(recs1, por_vb1, corte=corte)
    RES[f"verificador_0110_original_corte{corte}"] = tabla(recs1, lambda r: True, f"§2b sensibilidad, corte {corte}")
aplicar_nlc(recs1, por_vb1)

# ---------------------------------------------------------------- §3 ventana del auto-audit (falsas de K)
fr = aw.leer_frontera_k(str(RAIZ / "frontend" / "cambio_detector.js"))
print("\nfrontera K del tablero:", fr, "| REGLA_MINIMAS del auto-audit:", aw.REGLA_MINIMAS,
      "| INICIO_REGIMEN_FALSAS:", aw.INICIO_REGIMEN_FALSAS)
for fin in ("2026-10-19", "2026-10-21"):
    w = (aw.INICIO_REGIMEN_FALSAS, fin)
    recs3, por_vb3 = banco(w, regla=aw.REGLA_MINIMAS)
    aplicar_nlc(recs3, por_vb3)
    for r in recs3:
        r["det"] = aw._detector_banco(r, fr)
    print("detectores en la ventana:", dict(collections.Counter(r["det"] for r in recs3)))
    RES[f"autoaudit_{w[0]}_{fin}_K"] = tabla(recs3, lambda r: r["det"] == "K",
                                             f"§3 ventana del auto-audit {w[0]} a {fin}, regla {aw.REGLA_MINIMAS}, detector K")

# ---------------------------------------------------------------- §4 frente N (V750, 2026-04-01 a 2026-10-21 sin 18 y 19)
if A.n:
    NDIR = Path(A.n)
    nbg_n, comp_n, _ = nlc.indice_anillo(NDIR / "data_main", bp.VOLS)
    pob = json.load(open(AQUI.parent / "n" / "poblacion_completa.json", encoding="utf-8"))["pasadas"]
    censo = json.load(open(AQUI.parent / "n" / "objetivos_censo.json", encoding="utf-8"))
    neg = [p for p in pob if p["lab"] == "neg_limpio" and p["hora_utc"][:10] not in ("2026-10-18", "2026-10-19")]
    print(f"\n=== §4 frente N: negativos limpios V750 (sin 18 y 19 oct) {len(neg)}, K publica {sum(p['pub_prod'] for p in neg)}")
    idx_pob = {(p["volcan"], p["sensor"], p["hora_utc"]): p for p in pob}

    def nlc_n(p):
        k = (p["volcan"], p["sensor"], p["hora_utc"])
        t = datetime.strptime(p["hora_utc"], "%Y-%m-%d %H:%M")
        ts = [datetime.strptime(m["fecha_utc"][:19], "%Y-%m-%d %H:%M:%S") for m in p["mirova"]]
        return nlc.crater_en_granulo_mirova(k, ts, t, nbg_n, comp_n)
    sal = [p for p in neg if not nlc_n(p)[0]]
    print("salen:", len(sal), dict(collections.Counter(nlc_n(p)[1] for p in sal)),
          "| quedan por motivo:", dict(collections.Counter(nlc_n(p)[1] for p in neg if nlc_n(p)[0])))
    print("K publica en los que salen:", sum(p["pub_prod"] for p in sal),
          "| K negativos nuevos:", len(neg) - len(sal), "publica", sum(p["pub_prod"] for p in neg) - sum(p["pub_prod"] for p in sal))
    for p in sal:
        q = comp_n.get((p["volcan"], p["sensor"], p["hora_utc"]))
        pq = idx_pob.get(q)
        if p["pub_prod"]:
            print("   sale y K publica:", p["volcan"], p["hora_utc"], p["sensor"])
    # F: enciende los 60 cumulos de cumbre en 0,0 MW (censo); cuantos de esos estan en los que salen
    ks_sal = {(p["volcan"], p["hora_utc"]) for p in sal}
    cum = [c for c in censo if c.get("clase") == "cumbre_0mw" and c["hora_utc"][:10] not in ("2026-10-18", "2026-10-19")]
    far = [c for c in censo if c.get("clase") == "far" and c["hora_utc"][:10] not in ("2026-10-18", "2026-10-19")]
    print("censo F: cumbre_0mw", len(cum), "de ellos en pasadas que salen:",
          sorted((c["volcan"], c["hora_utc"]) for c in cum if (c["volcan"], c["hora_utc"]) in ks_sal),
          "| far", len(far), "en las que salen:", sum((c["volcan"], c["hora_utc"]) in ks_sal for c in far))
    # oraculo: negativos del lote (tabla_por_pasada.csv) donde algun oraculo tiene pixeles
    import csv
    lote = list(csv.DictReader(open(AQUI.parent / "n" / "tabla_por_pasada.csv", encoding="utf-8")))
    cols = [c for c in lote[0] if c.startswith("O_") and c.endswith("_npix")]
    negl = [x for x in lote if x["clase"].startswith("neg")]
    con_o = [x for x in negl if any(float(x[c] or 0) > 0 for c in cols) or x.get("O_pub") in ("1", "True")]
    print("lote: negativos", len(negl), "| con pixeles de algun oraculo u O_pub:", len(con_o),
          "| de ellos en pasadas que salen:", [(x["volcan"], x["hora_utc"]) for x in con_o if (x["volcan"], x["hora_utc"]) in ks_sal])
    print("lote: negativos del lote en pasadas que salen:", [(x["volcan"], x["hora_utc"], x["clase"]) for x in negl if (x["volcan"], x["hora_utc"]) in ks_sal])
    # Chaiten N-8 (control positivo 3)
    for h in ("2026-06-30 06:12", "2026-05-15 04:24"):
        for p in neg:
            if p["volcan"] == "Chaiten" and p["hora_utc"] == h:
                k = (p["volcan"], p["sensor"], p["hora_utc"])
                print("control 3 Chaiten N-8:", h, p["sensor"], "f =", nlc.fraccion(k, nbg_n, comp_n),
                      "nbg", nbg_n.get(k), "companero", comp_n.get(k), "->", nlc_n(p))
    RES["frente_N"] = {"neg_viejo": len(neg), "pub_viejo": sum(p["pub_prod"] for p in neg), "salen": len(sal),
                       "pub_que_sale": sum(p["pub_prod"] for p in sal)}
else:
    print("\n§4 sin --n: datos del frente N no usados")

# ---------------------------------------------------------------- §5 controles
print("\n=== §5 controles")
for tol in (120, 390):
    rc, pv = banco(("2026-01-10", "2026-10-21"), tol=tol)
    aplicar_nlc(rc, pv, tol=tol)
    for vol, s, h in (("NevadosDeChillan", "MODIS_TERRA", "2026-01-19 02:40"), ("Isluga", "VIIRS_NOAA20", "2026-02-04 05:54")):
        r = [x for x in rc if x["vol"] == vol and x["sensor"] == s and x["dt"].strftime("%Y-%m-%d %H:%M") == h]
        for x in r:
            print(f"tol {tol}: {vol} {s} {h} lab={x['lab']} nlc={x['nlc']} motivo={x.get('nlc_motivo')} pub={x['pub']} "
                  f"f={nlc.fraccion(clave(x), NBG, COMP)} filas MIROVA a ±{tol}s: "
                  f"{[t.strftime('%H:%M') for t in filas_dt(pv, x, tol)]}")
    solos = [x for x in rc if x["lab"] == "neg_limpio" and COMP.get(clave(x)) is None]
    print(f"tol {tol}: nulo, records solos en neg_limpio {len(solos)}, salen {sum(not x['nlc'] for x in solos)}"
          f" (con tol 120 tienen que ser 0; con 390 salen sólo los que parean con el vecino)")
    if tol == 390:
        RES["orbita_390_0110_original"] = tabla(rc, lambda r: True, "§5b pareo ±390 s (incluye el granulo vecino), regla original")

json.dump(RES, open(AQUI / "medir_salida.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("\nescrito medir_salida.json")
