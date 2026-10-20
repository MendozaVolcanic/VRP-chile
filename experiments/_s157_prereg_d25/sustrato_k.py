# -*- coding: utf-8 -*-
"""S157, tarea 1.29. SUSTRATO del A/B de D25 sobre K, medido en disco ANTES de despachar (A108, A114, feedback S130).

POR QUÉ. D25 cambia el fondo que se resta al calcular la magnitud, y el tablero publica todo cúmulo del cráter con
magnitud mayor que cero. Así que D25 puede hacer tres cosas que hay que poder ver antes de correr nada:
  (1) CREAR publicaciones: un cúmulo `summit` dentro del inner que hoy queda en 0,0 MW (el cráter más frío que el
      anillo, A6, D25) pasa a tener magnitud. En el probe de S151 sobre la detección vieja (C0) eso publicó 268 de
      268 negativos limpios de VIIRS 750 (experiments/_s151_d25_v750_disco/README.md). Con K la detección cambió
      (conectiva `max`, sin Test 1), y su cierre quedó condicionado a eso: hay que contar de nuevo cuántos hay.
  (2) MOVER la magnitud de lo que ya publicamos, que es lo que se quiere arreglar (Chillán, PR #869).
  (3) APAGAR o bajar de 1 MW una protegida si los vecinos están más tibios que el anillo (Lastarria 0,91 en 1.14).
Este script cuenta el tamaño de cada población por ventana, sensor y tramo de cenit del sensor (A114: la curva de
magnitud de Chillán cae con el cenit, PR #869), con la etiqueta del evaluador (banco_paridad, lecturas A y SN) y el
predicado del tablero ejecutado con node (A97). No predice el resultado: el script clasifica, no corre el pipeline.

DE DÓNDE SALEN LOS RECORDS CON K. Producción (`data/mirova_equivalent/`) es K desde el 2026-09-18 (reproceso del
2026-09-18 en adelante, marca de S155); antes de esa fecha se usa el histórico reprocesado con K
(`data/_s154_reproc_k_historico/`, tarea 1.24), que no tiene a Nevados de Chillán salvo 2025-12-08 a 2026-01-10 (su
reproceso se está rearmando). Por eso Chillán sólo entra desde el 2026-09-18. Se arma una copia unida en un temporal
fuera del repo y se comprueba que ningún record lleve `triggered_test1` (la huella de C0).

CONTROLES (A110):
  C1 positivo: con la referencia CONGELADA de V2 de F/K, las protegidas A de 2026-03-01 a 2026-06-12 contadas desde
     la referencia tienen que ser 158, como en experiments/_s151_prereg_fk_11/sustrato_salida.txt:86. (La versión
     de F/K comparaba la unión histórica VIVA con 439 y 992; hoy da 478 y 1.053 porque el corpus crece, A90, y no
     hay fecha de corte que la reproduzca: el remoto también pierde y gana filas hacia atrás.)
  C2 dos caminos, por ventana: protegidas desde la referencia = con record K + sin record K (las sin record son
     cobertura y se listan).
  C3 negativo: con la referencia corrida 7 días las alertas pareadas se derrumban (25 % o menos, umbral del
     instrumento heredado de experiments/_s151_prereg_fk_11/sustrato.py, elegido y no medido).
  CK: 0 records con `triggered_test1` en la copia unida.

Uso: python sustrato_k.py [--tmp DIR] > sustrato_k_salida.txt
"""
from __future__ import annotations

import argparse
import collections
import json
import statistics
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
for _p in (str(RAIZ), str(RAIZ / "scripts"), str(RAIZ / "experiments" / "_s146_ab_sin_test1"),
           str(RAIZ / "experiments" / "_s151_prereg_fk_11")):
    sys.path.insert(0, _p)
import sustrato as fk  # noqa: E402  (experiments/_s151_prereg_fk_11/sustrato.py: etiquetado y referencia de F/K)
import clase_mirova as cm  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402

ev, bp = fk.ev, fk.bp
FRONTERA_K = "2026-09-18"
VENTANAS = {
    # nombre: (desde, hasta, congelado, solo_tabla). V1 = régimen actual con Chillán en erupción; V2 = poder del veto.
    "V1": ("2026-08-29", "2026-10-18", AQUI / "_congelado_v1", False),
    "V2": ("2026-04-01", "2026-06-12", RAIZ / "experiments" / "_s151_prereg_fk_11" / "_congelado_v2", True),
}
SENS = ("MODIS", "VIIRS375", "VIIRS750")


def tramo40(r):
    z = r.get("z")
    return "sin_cenit" if z is None else ("cenit<=40" if z <= 40 else "cenit>40")


def tramo3(r):
    z = r.get("z")
    return "sin_cenit" if z is None else ("<30" if z < 30 else ("30-50" if z < 50 else ">=50"))


def unir_k(tmp):
    """Copia unida: histórico K antes de FRONTERA_K, producción (K) desde FRONTERA_K. Devuelve (dir, n_t1)."""
    out = Path(tmp) / "k_unido"
    out.mkdir(parents=True, exist_ok=True)
    n_t1 = 0
    for vol in bp.VOLS:
        recs = []
        h = RAIZ / "data" / "_s154_reproc_k_historico" / ("%s.json" % vol)
        if h.exists():
            recs += [r for r in json.loads(h.read_text(encoding="utf-8"))["records"] if r["datetime_utc"][:10] < FRONTERA_K]
        p = RAIZ / "data" / "mirova_equivalent" / ("%s.json" % vol)
        recs += [r for r in json.loads(p.read_text(encoding="utf-8"))["records"] if r["datetime_utc"][:10] >= FRONTERA_K]
        n_t1 += sum(bool(r.get("triggered_test1")) for r in recs)
        (out / ("%s.json" % vol)).write_text(json.dumps({"records": recs}), encoding="utf-8")
    return out, n_t1


def rescatable(r, inner):
    """Cúmulo del cráter que el tablero no publica porque su magnitud es 0,0: lo que D25 puede encender."""
    return (not r["pub"]) and r["dc"] == "summit" and r["pc_dist"] is not None and r["pc_dist"] <= inner[r["vol"]] \
        and (r["pc_vrp"] or 0) == 0


def contar(recs, inner, clave):
    c = collections.defaultdict(collections.Counter)
    razones = collections.defaultdict(list)
    for r in recs:
        k = clave(r)
        c[k]["pasadas"] += 1
        if r["lab"] == "pos":
            c[k]["alertas"] += 1
            c[k]["pA"] += r["prot_A"]
            c[k]["pA_pub"] += r["prot_A"] and r["pub"]
            c[k]["pA_pub_1MW"] += r["prot_A"] and r["pub"] and (r.get("disp") or 0) >= 1
            # Verificador H6: las que descansan sólo en el OCR de Suomi NPP antes del 2026-10-09 no deciden (lectura A).
            c[k]["pA_pub_dec"] += r["prot_A"] and r["pub"] and not r["prot_A_solo_ocr_snpp"]
            c[k]["MB"] += not r["prot_A"]
            c[k]["MB_pub"] += (not r["prot_A"]) and r["pub"]
            c[k]["resc_pos"] += rescatable(r, inner)
            if r["pub"] and r.get("vrp_ref"):
                razones[k].append(r["disp"] / r["vrp_ref"])
        elif r["lab"] == "neg_limpio":
            c[k]["neg"] += 1
            c[k]["neg_pub"] += r["pub"]
            c[k]["resc_neg"] += rescatable(r, inner)
    return c, razones


def imprimir(c, razones, claves, titulo):
    print("\n== " + titulo)
    print("   %-26s %6s %5s | %4s %5s %5s %6s | %5s %5s | %5s %5s | %6s %6s | %4s %6s" % (
        "", "pasad", "alert", "pA", "pApub", "pAdec", "pA>=1", "MB", "MBpub", "negl", "negpu", "rescN", "rescP", "nR", "R_med"))
    for k in claves:
        x = c.get(k, collections.Counter())
        rr = razones.get(k, [])
        print("   %-26s %6d %5d | %4d %5d %5d %6d | %5d %5d | %5d %5d | %6d %6d | %4d %6s" % (
            "|".join(k), x["pasadas"], x["alertas"], x["pA"], x["pA_pub"], x["pA_pub_dec"], x["pA_pub_1MW"], x["MB"], x["MB_pub"],
            x["neg"], x["neg_pub"], x["resc_neg"], x["resc_pos"], len(rr),
            ("%.3f" % statistics.median(rr)) if rr else "-"))


def una_ventana(nombre, desde, hasta, ref, solo_tabla, datos):
    filas = fk.cargar_filas(ref, solo_tabla)
    vols = set(bp.VOLS)
    recs, por_vb = fk.etiquetar_todo(datos, filas, (desde, hasta), vols)
    excl = [r for r in recs if r["vol"] == "NevadosDeChillan" and r["noche"] < FRONTERA_K]
    recs = [r for r in recs if not (r["vol"] == "NevadosDeChillan" and r["noche"] < FRONTERA_K)]
    if solo_tabla:
        recs = [r for r in recs if r["b"] == "MODIS" or r["noche"] >= "2026-04-01"]
    inner = bp.inner_desde_html()
    print("\n\n######## VENTANA %s: %s a %s | referencia %s%s | records nocturnos con K: %d (Chillán antes de %s fuera: %d)" % (
        nombre, desde, hasta, Path(ref).name, " (SOLO TABLA)" if solo_tabla else "", len(recs), FRONTERA_K, len(excl)))
    rv = collections.defaultdict(list)
    for r in recs:
        rv[(r["vol"], r["b"])].append(r["dt"])
    desde_ref = {k for k in fk.protegidas_desde_referencia(por_vb, vols)
                 if (not solo_tabla or k[1] == "MODIS" or k[2].strftime("%Y-%m-%d") >= "2026-04-01")}
    con_rec = {k for k in desde_ref if fk.tiene_record(rv, *k)}
    print("== C2. protegidas A desde la referencia %d = con record K %d + sin record K %d | desde los records %d | %s" % (
        len(desde_ref), len(con_rec), len(desde_ref) - len(con_rec), sum(r["prot_A"] for r in recs),
        "OK" if len(con_rec) == sum(r["prot_A"] for r in recs) else "DIFIERE"))
    sin = collections.Counter((v, b) for v, b, _ in desde_ref - con_rec)
    if sin:
        print("   sin record K (cobertura; Chillán antes de %s no tiene K): %s" % (FRONTERA_K, dict(sin)))
    corridas = [dict(f, fecha_utc=(datetime.strptime(f["fecha_utc"][:19], "%Y-%m-%d %H:%M:%S") + timedelta(days=7)).strftime(
        "%Y-%m-%d %H:%M:%S")) for f in filas]
    recs3, _ = fk.etiquetar_todo(datos, corridas, (desde, hasta), vols)
    p_real, p_3 = sum(r["lab"] == "pos" for r in recs), sum(r["lab"] == "pos" for r in recs3)
    ok3 = p_real > 0 and p_3 <= 0.25 * p_real
    print("== C3. alertas pareadas %d, con la referencia corrida 7 días %d | %s" % (p_real, p_3, "OK" if ok3 else "FALLA"))
    leyenda = ("conteos con la regla ORIGINAL de alertas mínimas (la SN de D-9 la aplica el evaluador); pA protegidas A; "
               "pApub las que K publica; pAdec las que K publica sin las que descansan sólo en OCR de Suomi NPP (las que "
               "DECIDEN con la lectura A); pA>=1 las que K publica con 1 MW o más (veto de cruce); MB alertas "
               "bajo 1 MW; negl negativos limpios; rescN/rescP cúmulos del cráter en 0,0 MW que K no publica, en negativos y "
               "en alertas (lo que D25 puede ENCENDER); nR y R_med: pares publicados con VRP de MIROVA y su razón mediana")
    for f, nom, claves in ((lambda r: (r["b"],), "POR SENSOR", [(s,) for s in SENS]),
                           (lambda r: (r["b"], tramo40(r)), "POR SENSOR Y CENIT (corte 40°, D17)",
                            [(s, t) for s in SENS for t in ("cenit<=40", "cenit>40", "sin_cenit")]),
                           (lambda r: (r["b"], tramo3(r)), "POR SENSOR Y TRES TRAMOS DE CENIT (PR #869)",
                            [(s, t) for s in SENS for t in ("<30", "30-50", ">=50")]),
                           (lambda r: (r["b"], r["vol"]), "POR SENSOR Y VOLCÁN", [(s, v) for s in SENS for v in bp.VOLS])):
        c, rz = contar(recs, inner, f)
        imprimir(c, rz, claves, nom + " | " + leyenda if nom == "POR SENSOR" else nom)
    # Regla SN (D-9): las alertas de VIIRS 375 de 0,05 MW o menos cuentan como «MIROVA no vio nada». Se informa el
    # tamaño del cambio, no se reetiqueta acá (lo hace el evaluador del A/B con la función única).
    sn = sum(1 for r in recs if r["b"] == "VIIRS375" and r["lab"] == "pos" and (r.get("vrp_ref") or 0) <= 0.05)
    print("\n   alertas VIIRS 375 de 0,05 MW o menos (regla SN las pasa a «no vio nada»): %d" % sn)
    print("\n== PODER DEL VETO (cero pérdidas de protegidas A que K publica), por sensor")
    c, _ = contar(recs, inner, lambda r: (r["b"],))
    for s in SENS:
        print("   %-8s todas las que K publica: %s" % (s, fk.poder(c[(s,)]["pA_pub"])))
        print("   %-8s las que deciden (sin OCR de Suomi NPP): %s" % (s, fk.poder(c[(s,)]["pA_pub_dec"])))
    return ok3


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tmp", default=r"D:\vrp-trabajo\temporales\s157d25")
    a = ap.parse_args()
    ref_v2 = VENTANAS["V2"][2]
    por_vb, *_ = bp.indexar_referencia(fk.cargar_filas(ref_v2, True), bp._coords_por_volcan(), ("2026-03-01", "2026-06-12"))
    c1 = len(fk.protegidas_desde_referencia(por_vb, set(bp.VOLS)))
    ok1 = c1 == 158
    print("== C1. protegidas A de la referencia congelada de V2 (F/K), 2026-03-01 a 2026-06-12: %d | esperado 158 | %s" % (
        c1, "OK" if ok1 else "FALLA"))
    datos, n_t1 = unir_k(a.tmp)
    print("== CK. records con triggered_test1 en la copia unida (huella de C0): %d | %s" % (n_t1, "OK" if n_t1 == 0 else "FALLA"))
    oks = [ok1, n_t1 == 0]
    for nombre, (desde, hasta, ref, solo_tabla) in VENTANAS.items():
        oks.append(una_ventana(nombre, desde, hasta, ref, solo_tabla, datos))
    print("\n== CONTROLES: C1 %s | CK %s | C3 por ventana %s" % (oks[0], oks[1], oks[2:]))
    return 0 if all(oks) else 1


if __name__ == "__main__":
    sys.exit(main())
