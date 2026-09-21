# -*- coding: utf-8 -*-
"""S149, frente D. Re-evalua el A/B "sin el Test 1 integrado" (run 35521542153) con los criterios
corregidos: recall por tramo de magnitud (tabla sola y tabla+OCR), selectividad C8b, estrato RUTINA
en noche con alerta, y magnitud pareada abierta por dentro (mismo cumulo o no, fuente del ancla).

Control = _s146_ab_control (mirova_equivalent reprocesado, Test 1 ENCENDIDO).
Brazo   = _s146_ab_sin_test1 (Test 1 apagado).
Ventana 2026-09-01 a 2026-09-20, referencia congelada de S146. SOLO LECTURA.

Las dos preguntas del instrumento:
1. Si el brazo estuviera roto (no apagara nada), lo veria: la tasa en negativos limpios del brazo
   seria igual a la del control. Control positivo: se exige reproducir 86,1 -> 28,7 % y 135 de 141.
2. Si el instrumento estuviera muerto (tabla vacia), los n serian 0 y se imprimen todos los n.

Uso: python d1_reevaluar_sin_test1.py DIR_SALIDAS   (DIR con _s146_ab_control y _s146_ab_sin_test1)
"""
import sys, io, json, statistics, collections
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[2]
sys.path.insert(0, str(RAIZ / "experiments" / "_s146_ab_sin_test1"))
import evaluar as ev
bp = ev.bp

D = Path(sys.argv[1]); VENT = ("2026-09-01", "2026-09-20")
CONG = RAIZ / "experiments" / "_s146_ab_sin_test1" / "_congelado"
coords = bp._coords_por_volcan(); inner = bp.inner_desde_html()
filas = ev.cargar_referencia_unificada(CONG / "registro_vrp_consolidado.csv", CONG / "registro_vrp_ocr.csv")
por_vb, ns, nv, n_ref = bp.indexar_referencia(filas, coords, VENT)


def carga(d):
    recs = ev.cargar_brazo(d, coords, inner, VENT)
    bp.etiquetar(recs, por_vb, ns, nv); ev.anotar_vrp_mirova(recs, por_vb)
    for r in recs:
        ff = bp.parear(por_vb.get((r["vol"], r["b"]), []), r["dt"])
        al = [f for f in ff if bp.es_alerta(f["tipo"])]
        r["alerta_tabla"] = any(f["source"] == "CONS" for f in al)
        r["alerta_solo_ocr"] = bool(al) and not r["alerta_tabla"]
    return recs


C = carga(D / "_s146_ab_control"); B = carga(D / "_s146_ab_sin_test1")
ib = {ev.clave(r): r for r in B}
print("filas de referencia en ventana:", n_ref, "| pasadas control", len(C), "| brazo", len(B),
      "| comunes", sum(1 for c in C if ev.clave(c) in ib))

TRAMOS = [(0, .05), (.05, .1), (.1, .2), (.2, .5), (.5, 1e9)]
for S in ("VIIRS375", "VIIRS750", "MODIS"):
    print("\n" + "=" * 100 + "\n" + S)
    cs = [c for c in C if c["b"] == S and ev.clave(c) in ib]
    neg = [c for c in cs if c["lab"] == "neg_limpio"]
    if neg:
        print("CONTROL POSITIVO. negativos limpios n %d: control publica %.1f %% | sin Test 1 %.1f %%" % (
            len(neg), 100 * sum(bool(c["pub"]) for c in neg) / len(neg), 100 * sum(bool(ib[ev.clave(c)]["pub"]) for c in neg) / len(neg)))
    for nombre, filtro in (("tabla + OCR", lambda c: True), ("SOLO TABLA (consolidado)", lambda c: c["alerta_tabla"])):
        pos = [c for c in cs if c["lab"] == "pos" and filtro(c)]
        print("\n  Recall por pasada, positivas segun %s: n %d | control publica %d | sin Test 1 publica %d" % (
            nombre, len(pos), sum(bool(c["pub"]) for c in pos), sum(bool(ib[ev.clave(c)]["pub"]) for c in pos)))
        conv = [c for c in pos if c.get("vrp_ref")]
        for a, b in TRAMOS:
            s = [c for c in conv if a <= c["vrp_ref"] < b]
            if not s: continue
            nc = sum(bool(c["pub"]) for c in s); nb = sum(bool(ib[ev.clave(c)]["pub"]) for c in s)
            print("     MIROVA %-15s n %3d (%2.0f %%) | control %3d (%3.0f %%) | sin Test 1 %3d (%3.0f %%) | perdidas %d" % (
                ("%.2f a %.2f MW" % (a, b)) if b < 1e8 else "0,50 MW o mas", len(s), 100 * len(s) / len(conv), nc, 100 * nc / len(s), nb, 100 * nb / len(s), nc - nb))
    perd = [c for c in cs if c["lab"] == "pos" and c["pub"] and not ib[ev.clave(c)]["pub"]]
    gan = [c for c in cs if c["lab"] == "pos" and not c["pub"] and ib[ev.clave(c)]["pub"]]
    print("\n  Positivas que el control publica y el brazo no (%d), una por una:" % len(perd))
    for c in sorted(perd, key=lambda r: -(r.get("vrp_ref") or 0)):
        print("     %-20s %s  MIROVA %s MW  fuente ctrl %-12s t1 %s  solo_ocr %s  z %s" % (
            c["vol"], c["dt"].strftime("%Y-%m-%d %H:%M"), c.get("vrp_ref"), c["fuente"], c["t1"], c["alerta_solo_ocr"], c["z"]))
    print("  Positivas que el brazo publica y el control no: %d" % len(gan))

    # C8b
    r = ev.selectividad_supervivencia(C, B, 1000, 149, sensor=S)
    print("\n  C8b selectividad de supervivencia:", json.dumps(r, ensure_ascii=False))

    # RUTINA en noche con alerta (negativo de pasada que el negativo limpio esconde)
    rut = [c for c in cs if c["lab"] == "sin_info" and c.get("rutina_pasada") and c.get("noche_con_alerta_sensor")]
    if rut:
        pc_ = sum(bool(c["pub"]) for c in rut); pb_ = sum(bool(ib[ev.clave(c)]["pub"]) for c in rut)
        print("\n  RUTINA VRP 0 en noche con alerta del sensor: n %d | control publica %d (%.1f %%) | sin Test 1 %d (%.1f %%)" % (
            len(rut), pc_, 100 * pc_ / len(rut), pb_, 100 * pb_ / len(rut)))
    # supervivencia por estrato de lo que publica el control
    print("  Supervivencia de lo que publica el control, por estrato:")
    for lab, sel in (("positivas", [c for c in cs if c["lab"] == "pos"]), ("RUTINA en noche con alerta", rut), ("negativos limpios", neg)):
        p = [c for c in sel if c["pub"]]
        if p: print("     %-28s publicadas por control %3d | sobreviven %3d (%.0f %%)" % (lab, len(p), sum(bool(ib[ev.clave(c)]["pub"]) for c in p), 100 * sum(bool(ib[ev.clave(c)]["pub"]) for c in p) / len(p)))
    # todos los negativos de pasada (limpios + rutina en noche con alerta): la vara de "callar donde MIROVA calla"
    todos = neg + rut
    if todos:
        print("  Negativos de PASADA (limpios + RUTINA en noche con alerta) n %d: control %.1f %% | sin Test 1 %.1f %%" % (
            len(todos), 100 * sum(bool(c["pub"]) for c in todos) / len(todos), 100 * sum(bool(ib[ev.clave(c)]["pub"]) for c in todos) / len(todos)))

# ---------------- magnitud pareada, abierta por dentro
print("\n" + "=" * 100 + "\nMAGNITUD PAREADA (positivas que los dos publican), VIIRS 375")
par = [(c, ib[ev.clave(c)]) for c in C if c["b"] == "VIIRS375" and ev.clave(c) in ib and c["lab"] == "pos"
       and c["pub"] and ib[ev.clave(c)]["pub"] and c.get("vrp_ref")]
print("pares:", len(par))


def clase(c, r):
    d = ev._hav(c["pc_lat"], c["pc_lon"], r["pc_lat"], r["pc_lon"]) if None not in (c["pc_lat"], c["pc_lon"], r["pc_lat"], r["pc_lon"]) else None
    return d


filas_ = []
for c, r in par:
    d = clase(c, r)
    filas_.append(dict(vol=c["vol"], dt=c["dt"].strftime("%Y-%m-%d %H:%M"), ref=c["vrp_ref"], dc=c["disp"], db=r["disp"],
                       fc=c["fuente"], fb=r["fuente"], t1=c["t1"], mov=d, pcv_c=c["pc_vrp"], pcv_b=r["pc_vrp"]))
igual = [f for f in filas_ if abs(f["dc"] - f["db"]) < 1e-9]
print("misma magnitud publicada en los dos brazos: %d de %d" % (len(igual), len(filas_)))
cam = [f for f in filas_ if abs(f["dc"] - f["db"]) >= 1e-9]
print("cambia la magnitud: %d | de esas, baja %d, sube %d" % (len(cam), sum(f["db"] < f["dc"] for f in cam), sum(f["db"] > f["dc"] for f in cam)))
print("  de las que cambian: fuente del ancla en el control ->", dict(collections.Counter(f["fc"] for f in cam)))
print("  de las que cambian: fuente del ancla en el brazo   ->", dict(collections.Counter(f["fb"] for f in cam)))
print("  de las que cambian: cumulo movido <=100 m: %d | 100 a 500 m: %d | >500 m: %d" % (
    sum((f["mov"] or 0) <= .1 for f in cam), sum(.1 < (f["mov"] or 0) <= .5 for f in cam), sum((f["mov"] or 0) > .5 for f in cam)))
print("  de las que NO cambian: fuente del ancla en el control ->", dict(collections.Counter(f["fc"] for f in igual)))
for nombre, sel in (("todas", filas_), ("fuente control = test1_roi o test1", [f for f in filas_ if "test1" in str(f["fc"])]),
                    ("fuente control != test1", [f for f in filas_ if "test1" not in str(f["fc"])])):
    if len(sel) >= 3:
        print("  razon contra MIROVA, %-36s n %3d | control %.3f | sin Test 1 %.3f | distancia a 1: %.3f -> %.3f" % (
            nombre, len(sel), statistics.median(f["dc"] / f["ref"] for f in sel), statistics.median(f["db"] / f["ref"] for f in sel),
            statistics.median(abs(f["dc"] / f["ref"] - 1) for f in sel), statistics.median(abs(f["db"] / f["ref"] - 1) for f in sel)))
print("\n  por volcan (n>=5): mediana razon control -> brazo | cuantas cambian | fuentes control")
g = collections.defaultdict(list)
for f in filas_: g[f["vol"]].append(f)
for vol, sel in sorted(g.items()):
    if len(sel) < 5: continue
    print("     %-20s n %2d | %.3f -> %.3f | cambian %2d | %s" % (vol, len(sel), statistics.median(f["dc"] / f["ref"] for f in sel),
          statistics.median(f["db"] / f["ref"] for f in sel), sum(abs(f["dc"] - f["db"]) >= 1e-9 for f in sel), dict(collections.Counter(f["fc"] for f in sel))))
# pc.vrp_mw (el cumulo contextual, sin recomputo del Test 1) en el CONTROL contra la magnitud del brazo
ok = [f for f in cam if f["pcv_c"] is not None and f["pcv_b"] is not None]
print("\n  en las que cambia: pc.vrp_mw del control == pc.vrp_mw del brazo (tolerancia 1e-6): %d de %d" % (sum(abs(f["pcv_c"] - f["pcv_b"]) < 1e-6 for f in ok), len(ok)))
json.dump(filas_, open(AQUI / "d1_pares_magnitud.json", "w", encoding="utf-8"), ensure_ascii=False, indent=0)
