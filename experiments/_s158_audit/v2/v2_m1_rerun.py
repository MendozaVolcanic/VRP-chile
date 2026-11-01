# -*- coding: utf-8 -*-
"""F5 (auditoria S158), medicion 1. Solo lectura: no escribe fuera de experiments/_s158_audit/f5/.

Sobre los records de PRODUCCION (detector K desde la observacion del 2026-09-18) y la referencia CONGELADA de V1
del pre-registro de D25 (experiments/_s157_prereg_d25/_congelado_v1/), ventana 2026-09-18 a 2026-10-18:

 (a) La metrica M del evaluador de D25 aplicada a un brazo PLACEBO: D = c * K (ganancia constante, sin fisica).
     Pregunta: ¿M distingue "un fondo mas fiel" de "una ganancia cualquiera"? Si M da MEJORA con c = 1,28 (el
     efecto medido de D25 en la tarea 1.14), M no puede atribuir una mejora al fondo.
     Instrumento 1: si M estuviera roto (siempre NEUTRO), c = 1,28 no daria MEJORA. Instrumento 2 / control
     positivo: c = 1 tiene que dar NEUTRO (d = 0 exacto) y c = 4 tiene que dar EMPEORA donde K < 1.
 (b) El criterio "dash" del auto-audit semanal (auto_audit_weekly.nuestros_por_noche) contra el predicado del
     tablero ejecutado con node (banco_paridad.cargar_nuestros, A97), record por record.
 (c) El criterio de libro_de_cuentas.r_recall_v750_dash (replica en Python de isValidDetection e
     isSummitDetection) contra el mismo predicado con node.
 (d) INNER del auto-audit contra el inner del tablero (frontend/index.html) y volcanoes.yaml.
"""
import collections, io, json, math, os, sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]  # V2: copia sin cambios de f5/m1, re-corrida
for p in (RAIZ, RAIZ / "scripts", RAIZ / "experiments" / "_s146_ab_sin_test1", RAIZ / "experiments" / "_s157_prereg_d25"):
    sys.path.insert(0, str(p))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import banco_paridad as bp  # noqa: E402
import auto_audit_weekly as aa  # noqa: E402
import evaluar as ev  # noqa: E402
import evaluar_d25 as D  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402
import yaml  # noqa: E402

VENT = ("2026-09-18", "2026-10-18")
CONG = RAIZ / "experiments" / "_s157_prereg_d25" / "_congelado_v1"

coords = bp._coords_por_volcan()
inner = bp.inner_desde_html()
filas = cargar_referencia_unificada(CONG / "registro_vrp_consolidado.csv", CONG / "registro_vrp_ocr.csv",
                                    respaldo_path=CONG / "respaldo_20260408.csv",
                                    historico_path=CONG / "consolidado_filas_perdidas.csv")
por_vb, ns, nv, n_ref = bp.indexar_referencia(filas, coords, VENT)
recs = bp.cargar_nuestros(coords, inner, VENT)
bp.etiquetar(recs, por_vb, ns, nv)
ev.anotar_vrp_mirova(recs, por_vb)
print("ventana", VENT, "| filas ref nocturnas", n_ref, "| records nocturnos", len(recs),
      "| etiquetas", dict(collections.Counter(r["lab"] for r in recs)))

# crudos para (b) y (c)
crudo = {}
for vol in bp.VOLS:
    for r in json.load(open(RAIZ / "data" / "mirova_equivalent" / (vol + ".json"), encoding="utf-8"))["records"]:
        t = r.get("datetime_utc", "")
        if VENT[0] <= t[:10] <= VENT[1]:
            crudo[(vol, r.get("sensor"), t[:16])] = r

# ---------------------------------------------------------------- (d) INNER
yml = {v["name"]: v.get("inner_radius_km") for v in yaml.safe_load((RAIZ / "volcanoes.yaml").read_text(encoding="utf-8"))["volcanoes"]}
print("\n(d) inner_radius_km: volcan | auto-audit INNER | tablero html | volcanoes.yaml")
for v in bp.VOLS:
    marca = "" if aa.INNER.get(v) == inner.get(v) == yml.get(v) else "   <-- DISTINTO"
    print("   %-20s %5s %5s %5s%s" % (v, aa.INNER.get(v), inner.get(v), yml.get(v), marca))

# ---------------------------------------------------------------- (b) y (c)
def dash_auto_audit(r):
    vrp = r["pc_vrp"] or 0.0
    return (0 < vrp <= aa.CAP) and (r["pc_dist"] is not None and r["pc_dist"] <= aa.INNER[r["vol"]]) and \
        (not r["dc"] or r["dc"] == "summit")


def libro_valida_summit(raw):
    v = raw.get("vrp_mw") or 0
    if not (v > 0 or raw.get("triggered_test1") is True):
        return False
    if v == 0 and raw.get("discarded_reason") and not raw.get("triggered_test1"):
        return False
    dc = raw.get("distance_class")
    if dc == "far":
        return False
    if dc != "summit" and not ((raw.get("vrp_vent_mw") or 0) > 0):
        return False
    return True


print("\n(b) criterio 'dash' del auto-audit contra el predicado del tablero (node), por record nocturno")
print("(c) criterio de libro_de_cuentas.r_recall_v750_dash contra el mismo predicado")
for b in bp.BUCKETS:
    sel = [r for r in recs if r["b"] == b]
    cb = collections.Counter((int(dash_auto_audit(r)), r["pub"]) for r in sel)
    cc = collections.Counter()
    ejemplos_c = []
    for r in sel:
        raw = crudo.get((r["vol"], r["sensor"], r["dt"].strftime("%Y-%m-%d %H:%M")))
        if raw is None:
            cc["sin_crudo"] += 1
            continue
        lv = int(libro_valida_summit(raw))
        cc[(lv, r["pub"])] += 1
        if lv == 1 and r["pub"] == 0 and len(ejemplos_c) < 4:
            ejemplos_c.append("%s %s %s vrp_mw=%s pc_vrp=%s dc=%s disp=%s" % (
                r["vol"], r["sensor"], r["dt"].strftime("%Y-%m-%d %H:%M"), raw.get("vrp_mw"),
                (raw.get("primary_cluster") or {}).get("vrp_mw"), raw.get("distance_class"), r["disp"]))
    print("  %-9s n=%5d | (b) dash&pub %4d dash&!pub %4d !dash&pub %4d ninguno %5d | (c) libro&pub %4d libro&!pub %4d !libro&pub %4d ninguno %5d sin_crudo %d" % (
        b, len(sel), cb[(1, 1)], cb[(1, 0)], cb[(0, 1)], cb[(0, 0)],
        cc[(1, 1)], cc[(1, 0)], cc[(0, 1)], cc[(0, 0)], cc["sin_crudo"]))
    for e in ejemplos_c:
        print("      libro valida y el tablero no publica:", e)
# en positivos (lo que el recall cuenta)
print("  solo pasadas 'pos' (alerta de MIROVA a +-2 min):")
for b in bp.BUCKETS:
    sel = [r for r in recs if r["b"] == b and r["lab"] == "pos"]
    cb = collections.Counter((int(dash_auto_audit(r)), r["pub"]) for r in sel)
    print("  %-9s n=%4d  dash&pub %4d dash&!pub %4d !dash&pub %4d ninguno %4d" % (
        b, len(sel), cb[(1, 1)], cb[(1, 0)], cb[(0, 1)], cb[(0, 0)]))

# ---------------------------------------------------------------- (a) placebo de M
pares = collections.defaultdict(list)
for r in recs:
    if r["lab"] != "pos" or not r.get("vrp_ref") or not r["pub"] or not (r["disp"] or 0) > 0:
        continue
    if r["b"] not in D.SENS:
        continue
    k = "|".join((r["vol"], r["b"], r["dt"].strftime("%Y-%m-%d %H:%M")))
    nom, modo = D.estrato(k, r["z"])
    pares[nom].append({"k": r["disp"], "m": r["vrp_ref"], "bloque": r["vol"] + "|" + r["dt"].strftime("%Y-%m-%d")})

print("\n(a) M del evaluador de D25 (regla_m, bootstrap por bloques noche-volcan, 10.000) con D = c*K")
print("    estrato | modo | n pares | noches | razon mediana K/MIROVA | c=1 | c=1.10 | c=1.28 | c=1.50 | c=2.0 | c=4.0")
for nom, modo in D.ESTRATOS:
    P = pares.get(nom, [])
    bl = [p["bloque"] for p in P]
    if len(P) < D.N_MIN_PARES or len(set(bl)) < D.N_MIN_NOCHES:
        print("    %-26s %-8s n=%3d noches=%3d  SIN SUSTRATO" % (nom, modo, len(P), len(set(bl))))
        continue
    K = np.array([p["k"] for p in P]); M = np.array([p["m"] for p in P])
    W = D.pesos_bloque(bl)
    out = []
    for c in (1.0, 1.10, 1.28, 1.50, 2.0, 4.0):
        d = np.array([D.d_par(k, c * k, m) for k, m in zip(K, M)])
        r_, lo, hi = D.regla_m(d, W)
        out.append("%s[%.3f,%.3f]" % (r_[:3], lo, hi))
    print("    %-26s %-8s n=%3d noches=%3d  %.3f  %s" % (nom, modo, len(P), len(set(bl)), float(np.median(K / M)), "  ".join(out)))
print("\n    lectura: MEJ = el intervalo al 95 % de la mediana de d queda bajo 0; EMP = sobre 0; NEU = cruza 0.")

# ---------------------------------------------------------------- (a2) el placebo con la calibracion y la regla
# de volcanes del evaluador (lo que contar() hace antes de dar el veredicto del estrato), en los dos modos.
print("\n(a2) placebo D = c*K con la calibracion del evaluador (sellada y simetrica de la adenda) y la regla de 2 volcanes")
for c in (1.10, 1.28):
    print("  c = %.2f" % c)
    for nom, modo in D.ESTRATOS:
        P = pares.get(nom, [])
        bl = [p["bloque"] for p in P]
        if len(P) < D.N_MIN_PARES or len(set(bl)) < D.N_MIN_NOCHES or modo == "informa":
            continue
        PP = [dict(p, d=c * p["k"]) for p in P]
        d = np.array([D.d_par(p["k"], p["d"], p["m"]) for p in PP])
        W = D.pesos_bloque(bl)
        r_, lo, hi = D.regla_m(d, W)
        fm, fe, pod = D.calibrar(PP, W, bl)
        cal_sell = fm + fe <= D.MAX_FALSOS_CALIB
        sm, se, spod = D.calibrar_simetrico(d, W, bl)
        cal_sim = (se <= D.MAX_FALSOS_CALIB) if modo == "bloquea" else (sm <= D.MAX_FALSOS_CALIB and se <= D.MAX_FALSOS_CALIB)
        vols = collections.defaultdict(list)
        for x, p in zip(d, PP):
            vols[p["bloque"].split("|")[0]].append(x)
        vneg = sum(1 for v, xs in vols.items() if len(xs) >= D.MIN_PARES_VOLCAN and float(np.median(xs)) < 0)
        def final(cal, simetrica):
            if not cal:
                return "INDECIDIBLE"
            if modo == "bloquea" and r_ == "MEJORA":
                return "NEUTRO"
            if simetrica and r_ == "MEJORA" and vneg < D.MIN_VOLCANES_MEJORA:
                return "NEUTRO(<2 volcanes)"
            return r_
        print("    %-26s %-8s regla %-7s | sellada: falsos MEJ %.3f EMP %.3f -> %s | simetrica: falsos MEJ %.3f EMP %.3f, volcanes con d<0 %d -> %s" % (
            nom, modo, r_, fm, fe, final(cal_sell, False), sm, se, vneg, final(cal_sim, True)))

# ---------------------------------------------------------------- V2 (verificador): agregado propio
# Por qué un placebo de ganancia da MEJORA: con D = c*K, d = |log(cK/M)| - |log(K/M)| vale exactamente -log10(c) en
# todo par con cK <= M. Si la mitad o más de los pares cumple cK <= M en (casi) todas las réplicas, la mediana es
# -log10(c) y el intervalo degenera en un punto. Se mide la fracción de pares con K/M <= 1/c y el placebo hacia abajo
# (c = 0,90), que debe dar EMPEORA donde K ya es bajo: si diera MEJORA, la métrica no castigaría alejarse.
print("\n(V2) fracción de pares con K/M <= 1/1,10 (d = -log10(1,10) exacto) y placebo hacia abajo c = 0,90")
for nom, modo in D.ESTRATOS:
    P = pares.get(nom, [])
    bl = [p["bloque"] for p in P]
    if len(P) < D.N_MIN_PARES:
        continue
    K = np.array([p["k"] for p in P]); M = np.array([p["m"] for p in P])
    W = D.pesos_bloque(bl)
    frac = float(np.mean(K / M <= 1 / 1.10))
    d09 = np.array([D.d_par(k, 0.90 * k, m) for k, m in zip(K, M)])
    r09 = D.regla_m(d09, W)
    vols = sorted({b.split("|")[0] for b in bl})
    print("   %-26s %-8s n=%3d volcanes=%d  frac K/M<=0,909: %.3f  | c=0,90 -> %s [%.3f, %.3f]" % (
        nom, modo, len(P), len(vols), frac, r09[0], r09[1], r09[2]))
