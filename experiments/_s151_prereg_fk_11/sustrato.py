# -*- coding: utf-8 -*-
"""Tarea 1.6 del loop. SUSTRATO del A/B "F y K contra produccion en los 11 Tier A": cuantas alertas
protegidas, cuantas alertas Muy Bajo y cuantos negativos limpios hay por sensor y por volcan en la ventana, y
cuantas de ellas publica hoy produccion. Sin esto no se sabe si el A/B tiene poder para decir algo (A114).

POR QUE CON LOS RECORDS DE PRODUCCION. El A/B cuenta por PASADA nuestra, etiquetada contra MIROVA. El universo
de pasadas lo pone el reproceso, que aun no corrio; la mejor estimacion previa son los records de produccion
de la misma ventana (`data/mirova_equivalent/*.json`), que son el brazo C0 corrido por el NRT. La etiqueta y el
predicado de publicacion son los del evaluador (banco_paridad y el tablero ejecutado con node, A97); la
referencia es la union de `scripts/referencia_mirova_unificada.cargar_referencia_unificada()` sobre la copia
congelada; la alerta protegida es `scripts/clase_mirova.alerta_protegida` (lecturas A y B, issue #782).

CONTROLES (las dos preguntas del instrumento, A110):
  C1 positivo, referencia: sobre la union historica completa, `pasadas_protegidas` tiene que dar los
     denominadores de docs/S151_CRITERIO_CLASE_MIROVA.md §3 y §5 (439 con la lectura A, 992 con la B).
  C2 consistencia por dos caminos: las pasadas protegidas (A) de la ventana contadas DESDE LA REFERENCIA tienen
     que ser las protegidas con record nuestro mas las que no tienen record; las contadas DESDE NUESTROS RECORDS
     tienen que ser exactamente las primeras.
  C3 negativo: la misma cuenta con la referencia corrida 7 dias tiene que derrumbarse a un cuarto o menos (si el
     pareo diera lo mismo con las horas equivocadas, no estaria pareando nada). No llega a cero: donde MIROVA
     alerta casi todas las noches, la pasada de otro satelite una semana despues cae a menos de 2 min por azar.

Las dos ventanas (V1 posterior a #535, decide tabla y OCR; V2 anterior al 2026-06-13, decide la tabla sola y se
reetiqueta de verdad quitando las filas del OCR) estan en VENTANAS. En V2 los records de produccion los escribio
el codigo de esa epoca (antes de #535), asi que "lo que produccion publica" ahi es una estimacion gruesa del C0
de hoy: sirve para el orden de magnitud del poder, no para predecir el resultado.
  C4 sobre el run real de Nevados de Chillan (opcional, --control-ndc DIR): con el C0 de ese run y su referencia
     congelada, tiene que reproducir el sustrato que imprimio experiments/_s150_ndc/medir_ndc.py (§0 de
     resultado_38560317428/salida_ndc.txt).

Uso:
  python sustrato.py > sustrato_salida.txt
  python sustrato.py --control-ndc <dir con _s146_ab_control/NevadosDeChillan.json del run 38560317428>
"""
from __future__ import annotations

import argparse, collections, io, sys
from datetime import datetime, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")  # reconfigure y no un TextIOWrapper nuevo: importado dos veces, cerraria el flujo
AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[1]
for _p in (str(RAIZ), str(RAIZ / "scripts"), str(RAIZ / "experiments" / "_s146_ab_sin_test1")):
    sys.path.insert(0, _p)
import evaluar as ev  # noqa: E402
import clase_mirova as cm  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402
from calidad_referencia_mirova import etiqueta_que_decide  # noqa: E402
bp = ev.bp

# Las dos ventanas del pre-registro (§3): ninguna cruza #535 (2026-08-28 23:00 UTC, A104). V2 es anterior al
# 2026-06-13, asi que en ella decide la tabla sola (A119); V1 es posterior y decide tabla y OCR.
VENTANAS = {"V1": ("2026-08-29", "2026-10-08", AQUI / "_congelado_v1", False),
            "V2": ("2026-03-01", "2026-06-12", AQUI / "_congelado_v2", True)}
INICIO_ACTIVIDAD_NDC = "2026-09-28"
INICIO_VIIRS_POR_PASADA = "2026-04-01"
SENS = ("MODIS", "VIIRS375", "VIIRS750")
# Denominadores publicados en docs/S151_CRITERIO_CLASE_MIROVA.md §3 y §5 (union historica, todas las fechas).
ESPERADO_HISTORICO = {"A": 439, "B": 992}
# experiments/_s150_ndc/resultado_38560317428/salida_ndc.txt, seccion 0 (C0 del run, etiqueta del evaluador).
ESPERADO_NDC = {("MODIS", "reposo"): (0, 0, 28), ("MODIS", "actividad"): (4, 3, 11),
                ("VIIRS375", "reposo"): (3, 0, 32), ("VIIRS375", "actividad"): (20, 13, 10),
                ("VIIRS750", "reposo"): (0, 0, 44), ("VIIRS750", "actividad"): (13, 11, 15)}


def es_snpp(rec):
    return "SNPP" in (rec.get("plataforma") or "")


def anotar_proteccion(recs, por_vb):
    """Por pasada: protegida con la lectura A y con la B, y si la A descansa SOLO en filas del OCR de una pasada
    de Suomi NPP (tramo con la distancia y la clase de otra pasada hasta el 2026-10-09, A119 y Mirova-v1#20)."""
    for r in recs:
        filas = bp.parear(por_vb.get((r["vol"], r["b"]), []), r["dt"])
        pa = [f for f in filas if cm.alerta_protegida(f, lectura="A")]
        r["prot_A"] = bool(pa)
        r["prot_B"] = any(cm.alerta_protegida(f, lectura="B") for f in filas)
        r["prot_A_solo_ocr_snpp"] = bool(pa) and all(f["source"] == "OCR" for f in pa) and es_snpp(r)


def etiquetar_todo(datos, filas, ventana, vols):
    coords = bp._coords_por_volcan(); inner = bp.inner_desde_html()
    por_vb, ns, nv, n_ref = bp.indexar_referencia(filas, coords, ventana)
    recs = [r for r in ev.cargar_brazo(Path(datos), coords, inner, ventana) if r["vol"] in vols]
    bp.etiquetar(recs, por_vb, ns, nv); ev.anotar_vrp_mirova(recs, por_vb); anotar_proteccion(recs, por_vb)
    return recs, por_vb


def protegidas_desde_referencia(por_vb, vols):
    """Camino independiente del de los records: pasadas nocturnas de la referencia con fila protegida (A)."""
    out = set()
    for (vol, b), lista in por_vb.items():
        if vol not in vols:
            continue
        for dt, f in lista:
            if cm.alerta_protegida(f, lectura="A"):
                out.add((vol, b, dt))
    return out


def tiene_record(recs_por_vb, vol, b, dt):
    return any(abs((t - dt).total_seconds()) <= bp.TOL_S for t in recs_por_vb.get((vol, b), []))


def tabla(recs, clave):
    c = collections.defaultdict(collections.Counter)
    for r in recs:
        k = clave(r); c[k]["pasadas"] += 1
        if r["lab"] == "pos":
            c[k]["alertas"] += 1
            c[k]["prot_A"] += r["prot_A"]; c[k]["prot_A_pub"] += r["prot_A"] and r["pub"]
            c[k]["prot_A_snpp_ocr"] += r["prot_A_solo_ocr_snpp"]
            c[k]["prot_A_pub_decide"] += r["prot_A"] and r["pub"] and not r["prot_A_solo_ocr_snpp"]
            c[k]["muy_bajo_A"] += not r["prot_A"]; c[k]["muy_bajo_A_pub"] += (not r["prot_A"]) and r["pub"]
        c[k]["prot_B"] += r["prot_B"]; c[k]["prot_B_pub"] += r["prot_B"] and r["pub"]
        if r["lab"] == "neg_limpio":
            c[k]["neg"] += 1; c[k]["neg_pub"] += r["pub"]
        if r["lab"] in ("sin_info", "far_ref"):
            c[k]["otras"] += 1; c[k]["otras_pub"] += r["pub"]
    return c


def imprimir(c, claves, titulo):
    print("\n== " + titulo)
    print("   %-30s %6s %5s | %4s %4s %4s | %5s %5s | %4s %4s | %5s %5s | %5s %5s" % (
        "", "pasad", "alert", "pA", "pApu", "snpp", "MBajo", "MBpub", "pB", "pBpu", "negl", "negpu", "otras", "otpub"))
    for k in claves:
        x = c.get(k, collections.Counter())
        print("   %-30s %6d %5d | %4d %4d %4d | %5d %5d | %4d %4d | %5d %5d | %5d %5d" % (
            "|".join(k) if isinstance(k, tuple) else k, x["pasadas"], x["alertas"], x["prot_A"], x["prot_A_pub"],
            x["prot_A_snpp_ocr"], x["muy_bajo_A"], x["muy_bajo_A_pub"], x["prot_B"], x["prot_B_pub"], x["neg"],
            x["neg_pub"], x["otras"], x["otras_pub"]))


def poder(n):
    """Probabilidad de ver al menos una perdida si el candidato perdiera una fraccion p de las protegidas que el
    control publica, y la fraccion que se veria con 80 % de probabilidad (veto de cero perdidas)."""
    if n == 0:
        return "n 0: SIN PODER, el veto no puede fallar"
    pr = " ".join("p=%d%%: %.2f" % (100 * p, 1 - (1 - p) ** n) for p in (0.01, 0.02, 0.05, 0.10))
    return "n %d | %s | fraccion detectable al 80 %%: %.1f %%" % (n, pr, 100 * (1 - 0.2 ** (1 / n)))


def control_ndc(dir_ndc):
    ref = RAIZ / "experiments" / "_s150_ndc" / "_congelado_ndc"
    filas = cargar_referencia_unificada(ref / "registro_vrp_consolidado.csv", ref / "registro_vrp_ocr.csv")
    recs, _ = etiquetar_todo(Path(dir_ndc) / "_s146_ab_control", filas, ("2026-09-14", "2026-10-07"), {"NevadosDeChillan"})
    ok = True
    print("\n== C4. Sobre el C0 del run de Nevados de Chillan, contra la seccion 0 de medir_ndc.py")
    for (s, fase), esp in ESPERADO_NDC.items():
        sel = [r for r in recs if r["b"] == s and ((r["noche"] >= INICIO_ACTIVIDAD_NDC) == (fase == "actividad"))]
        obt = (sum(r["lab"] == "pos" for r in sel), sum(r["lab"] == "pos" and (r["vrp_ref"] or 0) >= 1 for r in sel),
               sum(r["lab"] == "neg_limpio" for r in sel))
        ok &= obt == esp
        print("   %-8s %-9s alertas, de 1 MW o mas, negativos limpios: %s | esperado %s | %s" % (s, fase, obt, esp, "OK" if obt == esp else "DIFIERE"))
    print("   C4:", "OK" if ok else "FALLA")
    return ok


def cargar_filas(ref, solo_tabla):
    """Referencia unificada de la copia congelada. Con `solo_tabla`, se queda con las filas del consolidado
    (principal, historico y respaldo), que es el reetiquetado DE VERDAD que A119 pide antes del 2026-06-13:
    una alerta solo del OCR no es positiva y tampoco saca a la pasada de los negativos (S150, hallazgo H7)."""
    ref = Path(ref)
    # Las dos capas (historica de la union y respaldo) tambien CONGELADAS y explicitas (verificador del PR #797,
    # punto 2): el cargador las leeria del repo, y audit-weekly.yml reescribe la historica cada semana.
    hist, resp = ref / "consolidado_filas_perdidas.csv", ref / "respaldo_20260408.csv"
    if not (hist.exists() and resp.exists()):
        raise SystemExit("%s no trae las capas congeladas: correr congelar.py capas" % ref)
    filas = cargar_referencia_unificada(ref / "registro_vrp_consolidado.csv", ref / "registro_vrp_ocr.csv",
                                        historico_path=hist, respaldo_path=resp)
    return [f for f in filas if f["source"] == "CONS"] if solo_tabla else filas


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--datos", default=str(RAIZ / "data" / "mirova_equivalent"))
    ap.add_argument("--control-ndc", default=None)
    a = ap.parse_args()
    vols = set(bp.VOLS)

    # C1: denominadores historicos
    hist = cargar_referencia_unificada()
    c1 = {l: len(cm.pasadas_protegidas(hist, lectura=l)) for l in "AB"}
    ok1 = c1 == ESPERADO_HISTORICO
    print("== C1. union historica completa: protegidas %s | esperado %s | %s" % (c1, ESPERADO_HISTORICO, "OK" if ok1 else "FALLA"))
    ok4 = control_ndc(a.control_ndc) if a.control_ndc else None
    oks = [ok1, ok4 is not False]
    for nombre, (desde, hasta, ref, solo_tabla) in VENTANAS.items():
        oks.append(una_ventana(nombre, desde, hasta, ref, solo_tabla, a.datos, vols))
    print("\n== CONTROLES: C1 %s | C4 %s | C2 y C3 por ventana %s" % (ok1, ok4, oks[2:]))
    return 0 if all(oks) else 1


def una_ventana(nombre, desde, hasta, ref, solo_tabla, datos, vols):
    ventana = (desde, hasta)
    filas = cargar_filas(ref, solo_tabla)
    print("\n\n######## VENTANA %s: %s a %s | 11 Tier A | referencia %s%s | decide la etiqueta: %s" % (
        nombre, desde, hasta, Path(ref).name, " (SOLO TABLA)" if solo_tabla else "", etiqueta_que_decide(desde)))
    recs, por_vb = etiquetar_todo(datos, filas, ventana, vols)
    print("   records nocturnos en la ventana: %d (de %s)" % (len(recs), datos))

    # C2: dos caminos
    rv = collections.defaultdict(list)
    for r in recs:
        rv[(r["vol"], r["b"])].append(r["dt"])
    desde_ref = protegidas_desde_referencia(por_vb, vols)
    con_rec = {k for k in desde_ref if tiene_record(rv, *k)}
    desde_recs = sum(r["prot_A"] for r in recs)
    ok2 = len(con_rec) == desde_recs
    print("== C2. protegidas (A) desde la referencia %d = con record nuestro %d + sin record %d | desde los records %d | %s" % (
        len(desde_ref), len(con_rec), len(desde_ref) - len(con_rec), desde_recs, "OK" if ok2 else "FALLA"))
    for vol, b, dt in sorted(desde_ref - con_rec):
        print("      protegida sin record nuestro (cobertura, aparte): %s %s %s" % (vol, b, dt.strftime("%Y-%m-%d %H:%M")))

    # C3: referencia corrida 7 dias
    corridas = [dict(f, fecha_utc=(datetime.strptime(f["fecha_utc"][:19], "%Y-%m-%d %H:%M:%S") + timedelta(days=7)).strftime("%Y-%m-%d %H:%M:%S")) for f in filas]
    recs3, _ = etiquetar_todo(datos, corridas, ventana, vols)
    pos_real, pos_3 = sum(r["lab"] == "pos" for r in recs), sum(r["lab"] == "pos" for r in recs3)
    # Umbral del INSTRUMENTO, no del A/B: el corrimiento no llega a cero porque, donde MIROVA alerta casi todas
    # las noches (Lascar, Lastarria, Tupungatito en VIIRS de marzo a junio), la pasada de otro satelite una
    # semana despues cae a menos de 2 minutos de una fila por azar. Lo que se exige es que el pareo se derrumbe.
    # El 25 % lo ELEGI yo, sin nulo medido (verificador del PR #797, 6e), y C3 no decide nada del A/B: solo dice
    # si este conteo pareaba por hora y no por casualidad.
    ok3 = pos_real > 0 and pos_3 <= 0.25 * pos_real
    print("== C3. alertas pareadas con la referencia real %d, con la corrida 7 dias %d (%.1f %%) | %s (exige 25 %% o menos)" % (
        pos_real, pos_3, 100 * pos_3 / max(pos_real, 1), "OK" if ok3 else "FALLA"))

    # Sustrato
    c_sens = tabla(recs, lambda r: (r["b"],))
    imprimir(c_sens, [(s,) for s in SENS], "SUSTRATO POR SENSOR (pA: protegidas lectura A; pApu: las que produccion publica; "
             "snpp: pA solo por OCR de Suomi NPP; MBajo: alertas bajo 1 MW; pB: protegidas lectura B; negl: negativos limpios; "
             "otras: sin_info y far_ref)")
    c_vs = tabla(recs, lambda r: (r["b"], r["vol"]))
    imprimir(c_vs, [(s, v) for s in SENS for v in bp.VOLS], "POR SENSOR Y VOLCAN")
    c_ndc = tabla([r for r in recs if r["vol"] == "NevadosDeChillan"],
                  lambda r: (r["b"], "actividad" if r["noche"] >= INICIO_ACTIVIDAD_NDC else "reposo"))
    imprimir(c_ndc, [(s, f) for s in SENS for f in ("reposo", "actividad")], "NEVADOS DE CHILLAN POR FASE (actividad desde 2026-09-28)")
    c_fuera = tabla([r for r in recs if r["vol"] != "Lascar"], lambda r: (r["b"],))
    imprimir(c_fuera, [(s,) for s in SENS], "SIN LASCAR (S150 midio MODIS solo en Lascar)")

    if desde < INICIO_VIIRS_POR_PASADA:
        # A119 (b): una tasa VIIRS por pasada anterior a abril no se compara; en V2 VIIRS decide desde abril.
        c_sens = tabla([r for r in recs if r["b"] == "MODIS" or r["noche"] >= INICIO_VIIRS_POR_PASADA], lambda r: (r["b"],))
        imprimir(c_sens, [(s,) for s in SENS], "LO QUE DECIDE: MODIS toda la ventana, VIIRS desde %s (A119)" % INICIO_VIIRS_POR_PASADA)
        imprimir(tabla([r for r in recs if r["b"] == "MODIS" or r["noche"] >= INICIO_VIIRS_POR_PASADA], lambda r: (r["b"], r["vol"])),
                 [(s, v) for s in SENS for v in bp.VOLS], "LO QUE DECIDE, POR SENSOR Y VOLCAN")
    print("\n== PODER DEL VETO (cero perdidas de protegidas que el control publica; produccion como estimacion del control)")
    for s in SENS:
        x = c_sens[(s,)]
        print("   %-8s lectura A: %s" % (s, poder(x["prot_A_pub_decide"])))
        print("   %-8s lectura B: %s" % (s, poder(x["prot_B_pub"])))
    return ok2 and ok3


if __name__ == "__main__":
    sys.exit(main())
