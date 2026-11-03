# -*- coding: utf-8 -*-
"""s02 (S173, cenit V750): razón de cada brazo de la ablación contra MIROVA por pasada, partida por cenit, en Chillán.

POR QUÉ. La pregunta es qué pieza produce la caída oblicua de la razón K / MIROVA. El brazo O (todas las piezas del
programa de MIROVA sobre la grilla GEO lineal) debería dar razón ~1 a todo cenit si el port es fiel; cada brazo que
mete una pieza de K muestra si esa pieza, sola, reintroduce la caída. K nativo (el record publicado) es el control
positivo: en estas mismas pasadas tiene que mostrar la caída que S172 midió; si no la muestra, el subconjunto no sirve
para atribuirla.

Vara: referencia del scraper (data/mirova_reference/mirova_v1_snapshot de origin/main, copia en repo/), unión CONS+OCR,
regla D-9 SN (banco_paridad.indexar_referencia regla_minimas="SN", que imprime los avisos A119 por stderr), pareo por
pasada a +-120 s (banco_paridad.parear, VENTANA_S), VRP de la fila CONS si es ALERTA, si no la del OCR (igual que
s02_pareo_por_pasada.py de S172). Cenit: sensor_zenith_deg del record K del runner (s01: igual al del centro de la
geometría, |dif| máx 0,86°).

P1 (si lo medido estuviera roto, ¿lo vería?): K nativo debe dar Spearman negativo fuera del barajado (control
    positivo); O debe dar ~1 (si O tampoco fuera ~1 el port no reproduce a MIROVA en Chillán y nada de la ablación se
    puede leer). Control de escala: x2 al brazo O dobla su mediana.
P2 (instrumento muerto): pareo con la referencia corrida +1 día: los pares deben caer casi a 0; y el barajado del
    cenit (200, semilla 173) da el rango de Spearman sin relación.
Ventana: la de las grillas de Chillán (s01: 2026-04-15 a 2026-10-17). Denominador: pasadas nocturnas de Chillán con
grilla y alerta de MIROVA pareada.
Uso: python -B s02_razon_por_cenit.py
"""
from __future__ import annotations

import collections
import csv
import io
import json
import math
import os
import random
import statistics
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
REPO = AQUI / "repo"
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import banco_paridad as bp  # noqa: E402

VOL = "NevadosDeChillan"
BRAZOS = ["O", "O_8vec", "O_regp1", "O_umbK", "O_comp", "O_comp1", "O_sens", "O_circ", "O_rec", "O_fanillo",
          "O_sinhalo", "O_todoK", "O_todoK_sincomp", "geo_nearest", "geo_cubic", "r2_linear", "r2_nearest"]
L = []


def pr(*x):
    s = " ".join(str(y) for y in x)
    print(s, flush=True)
    L.append(s)


def fl(x):
    try:
        v = float(x)
        return v if math.isfinite(v) else None
    except (TypeError, ValueError):
        return None


def rank(v):
    o = sorted(range(len(v)), key=lambda i: v[i])
    rk = [0.0] * len(v)
    i = 0
    while i < len(o):
        j = i
        while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
            j += 1
        for k in range(i, j + 1):
            rk[o[k]] = (i + j) / 2 + 1
        i = j + 1
    return rk


def spearman(x, y):
    pr_ = [(a, b) for a, b in zip(x, y) if a is not None and b is not None]
    if len(pr_) < 4:
        return None
    a, b = rank([p[0] for p in pr_]), rank([p[1] for p in pr_])
    ma, mb = statistics.mean(a), statistics.mean(b)
    num = sum((p - ma) * (q - mb) for p, q in zip(a, b))
    den = math.sqrt(sum((p - ma) ** 2 for p in a) * sum((q - mb) ** 2 for q in b))
    return num / den if den else None


def barajado(z, r, n=200, semilla=173):
    rng = random.Random(semilla)
    out = []
    for _ in range(n):
        zz = list(z)
        rng.shuffle(zz)
        s = spearman(zz, r)
        if s is not None:
            out.append(s)
    out.sort()
    return (out[int(0.025 * len(out))], out[int(0.975 * len(out)) - 1]) if out else (None, None)


def med(v):
    return statistics.median(v) if v else None


def q(v):
    if not v:
        return "sin datos"
    v = sorted(v)
    n = len(v)
    return f"{statistics.median(v):.3f} [{v[n // 4]:.3f}, {v[(3 * n) // 4]:.3f}] n={n} rango [{v[0]:.3f}, {v[-1]:.3f}]"


def vrp_mirova(fs):
    al = [f for f in fs if bp.es_alerta(f["tipo"])]
    if not al:
        return None, None
    c = [f for f in al if f["source"] == "CONS"]
    f = (c or al)[0]
    return f["vrp_mw"], f


def main():
    filas = list(csv.DictReader(open(AQUI / "s01_por_pasada.csv", encoding="utf-8")))
    ventana = ("2026-04-01", "2026-10-31")
    bp.VOLS = [VOL]
    coords = bp._coords_por_volcan()
    inner = bp.inner_desde_html()
    ref = bp.cargar_referencia_unificada(bp.SNAP_CONS, bp.SNAP_OCR)
    por_vb, ns, nv, n_ref = bp.indexar_referencia(ref, coords, ventana, regla_minimas="SN")
    lista = por_vb.get((VOL, "VIIRS750"), [])
    # K publicado hoy en main (predicado del tablero en node) para las mismas pasadas
    recs = bp.cargar_nuestros(coords, inner, ventana, data=REPO / "data" / "mirova_equivalent")
    kmain = {(r["sensor"], r["dt"].strftime("%Y-%m-%d %H:%M")): r for r in recs if r["b"] == "VIIRS750"}
    pr("== VARA")
    pr("referencia: filas nocturnas en ventana (todas las bandas):", n_ref, "| filas VIIRS750 de Chillán:", len(lista))
    pr("SNAP_CONS:", bp.SNAP_CONS)
    pr("records K VIIRS750 de Chillán en main (ventana):", len(kmain))

    P = []
    ctrl = collections.Counter()
    for f in filas:
        dt = datetime.strptime(f["hora_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        fs = bp.parear(lista, dt)
        vm, fm = vrp_mirova(fs)
        vsh, _ = vrp_mirova(bp.parear(lista, dt + timedelta(days=1)))
        km = kmain.get((f["k_sensor"], f["k_datetime"]))
        x = dict(f)
        x.update(vM=vm, srcM=(fm or {}).get("source"), fechaM=(fm or {}).get("fecha_utc"), tipoM=(fm or {}).get("tipo"),
                 vM_sh=vsh, z=fl(f["z_record_K"]), n_filas_par=len(fs),
                 k_main_disp=(km or {}).get("disp"), k_main_pub=(km or {}).get("pub"), k_main_z=(km or {}).get("z"),
                 k_main_dc=(km or {}).get("dc"))
        ctrl["con_alerta" if vm else "sin_alerta"] += 1
        if vm and f["lab"] != "pos":
            ctrl["alerta_pero_lab_no_pos"] += 1
        if not vm and f["lab"] == "pos":
            ctrl["lab_pos_sin_alerta_hoy"] += 1
        if vm and fl(f["obj_mirova_vrp"]) is not None and abs(vm - fl(f["obj_mirova_vrp"])) > 1e-6:
            ctrl["vM_distinto_de_objetivo"] += 1
        if vsh:
            ctrl["par_corrido_1d"] += 1
        if km is None:
            ctrl["k_main_no_encontrado"] += 1
        P.append(x)

    pos = [x for x in P if x["vM"] and x["vM"] > 0]
    pr("\n== CONTROLES DEL PAREO")
    pr("pasadas con grilla:", len(P), "| con alerta MIROVA pareada hoy:", ctrl["con_alerta"], "| sin:", ctrl["sin_alerta"])
    pr("alerta hoy pero lab del objetivo no 'pos':", ctrl["alerta_pero_lab_no_pos"],
       "| lab 'pos' sin alerta hoy:", ctrl["lab_pos_sin_alerta_hoy"])
    pr("VRP de MIROVA pareado distinto del guardado en el objetivo de N:", ctrl["vM_distinto_de_objetivo"])
    pr("P2: pares con la referencia corrida +1 día:", ctrl["par_corrido_1d"], "de", len(P))
    pr("record K de main no encontrado por (sensor, datetime):", ctrl["k_main_no_encontrado"])
    pr("fuente de la fila MIROVA de los positivos:", dict(collections.Counter(x["srcM"] for x in pos)))
    pr("ventana de los positivos:", min(x["hora_utc"] for x in pos), "a", max(x["hora_utc"] for x in pos),
       "| noches:", len({x["hora_utc"][:10] for x in pos}))
    zs = sorted(x["z"] for x in pos)
    pr("cenit de los positivos:", [round(z, 1) for z in zs])
    pr("n z<30:", sum(z < 30 for z in zs), "| n z>=30:", sum(z >= 30 for z in zs))
    pr("plataformas:", dict(collections.Counter(x["k_sensor"] for x in pos)))

    def razones(b, sel_pub):
        out = []
        for x in pos:
            v = fl(x[f"{b}_vrp"])
            ok = (x[f"{b}_pub"] == "True") if sel_pub else (v is not None and v > 0)
            if ok and v is not None and v > 0:
                out.append((x["z"], v / x["vM"], x))
        return out

    def linea(nombre, rz):
        z = [a for a, _, _ in rz]
        r = [b for _, b, _ in rz]
        lo = [b for a, b, _ in rz if a < 30]
        hi = [b for a, b, _ in rz if a >= 30]
        sp = spearman(z, r)
        bj = barajado(z, r)
        cociente = (med(hi) / med(lo)) if lo and hi else None
        pr(f"{nombre:16s} n={len(rz):2d} | z<30 {q(lo)} | z>=30 {q(hi)} | med(>=30)/med(<30) "
           + (f"{cociente:.3f}" if cociente else "-")
           + f" | Spearman {sp:+.3f}" if sp is not None else f"{nombre:16s} n={len(rz)} insuficiente")
        if sp is not None:
            pr(f"{'':16s} barajado 2.5-97.5 % [{bj[0]:+.3f}, {bj[1]:+.3f}] -> "
               + ("FUERA del barajado" if (sp < bj[0] or sp > bj[1]) else "dentro del barajado"))
        return {"n": len(rz), "n_lo": len(lo), "n_hi": len(hi), "med_lo": med(lo), "med_hi": med(hi),
                "cociente_hi_lo": cociente, "spearman": sp, "barajado": bj}

    resumen = {}
    pr("\n== CONTROL POSITIVO: K nativo en las mismas pasadas (razón K / MIROVA por pasada)")
    rk_main = [(x["z"], x["k_main_disp"] / x["vM"], x) for x in pos
               if x["k_main_pub"] == 1 and x["k_main_disp"] and x["k_main_disp"] > 0]
    resumen["K_main_publicado"] = linea("K main (tablero)", rk_main)
    rk_run = [(x["z"], fl(x["k_pc_vrp"]) / x["vM"], x) for x in pos if fl(x["k_pc_vrp"]) and fl(x["k_pc_vrp"]) > 0]
    resumen["K_runner_pc"] = linea("K runner pc.vrp", rk_run)
    pr("K main publica en", sum(1 for x in pos if x["k_main_pub"] == 1), "de", len(pos), "positivos")

    pr("\n== P1 control de escala: brazo O x2")
    o2 = [(a, 2 * b, x) for a, b, x in razones("O", False)]
    pr("O x2 mediana:", q([b for _, b, _ in o2]), "| O:", q([b for _, b, _ in razones("O", False)]))

    for sel, titulo in ((False, "MAGNITUD (brazo con VRP > 0, publique o no)"),
                        (True, "PUBLICA (predicado de N: >= 1 px, VRP > 0, píxel más radiante dentro del inner)")):
        pr(f"\n== RAZÓN BRAZO / MIROVA POR CENIT, {titulo}")
        for b in BRAZOS:
            resumen[f"{b}|{'pub' if sel else 'mag'}"] = linea(b, razones(b, sel))

    # subconjunto común: pasadas positivas donde TODOS los brazos (y K main) tienen VRP > 0
    com = [x for x in pos if all((fl(x[f"{b}_vrp"]) or 0) > 0 for b in BRAZOS)
           and x["k_main_pub"] == 1 and (x["k_main_disp"] or 0) > 0]
    pr(f"\n== SUBCONJUNTO COMÚN (todos los brazos y K main con VRP > 0): n = {len(com)}, "
       f"z<30 {sum(x['z'] < 30 for x in com)}, z>=30 {sum(x['z'] >= 30 for x in com)}")
    for b in ["K_main"] + BRAZOS:
        rz = [(x["z"], (x["k_main_disp"] if b == "K_main" else fl(x[f"{b}_vrp"])) / x["vM"], x) for x in com]
        resumen[f"{b}|comun"] = linea(b, rz)

    # mecanismo: cuántos píxeles y cuánta potencia por píxel; relación entre brazos
    pr("\n== DESCOMPOSICIÓN por cenit (positivos)")
    for nombre, fn in (
            ("npix O", lambda x: fl(x["O_npix"])),
            ("npix O_todoK", lambda x: fl(x["O_todoK_npix"])),
            ("npix K runner pc", lambda x: fl(x["k_pc_npix"])),
            ("O_fanillo/O (VRP)", lambda x: (fl(x["O_fanillo_vrp"]) / fl(x["O_vrp"]))
             if fl(x["O_fanillo_vrp"]) and fl(x["O_vrp"]) else None),
            ("O_sinhalo/O (VRP)", lambda x: (fl(x["O_sinhalo_vrp"]) / fl(x["O_vrp"]))
             if fl(x["O_sinhalo_vrp"]) and fl(x["O_vrp"]) else None),
            ("O_todoK/O (VRP)", lambda x: (fl(x["O_todoK_vrp"]) / fl(x["O_vrp"]))
             if fl(x["O_todoK_vrp"]) and fl(x["O_vrp"]) else None),
            ("K main/O_todoK", lambda x: (x["k_main_disp"] / fl(x["O_todoK_vrp"]))
             if x["k_main_pub"] == 1 and (x["k_main_disp"] or 0) > 0 and fl(x["O_todoK_vrp"]) else None),
            ("K main/O", lambda x: (x["k_main_disp"] / fl(x["O_vrp"]))
             if x["k_main_pub"] == 1 and (x["k_main_disp"] or 0) > 0 and fl(x["O_vrp"]) else None),
            ("Lbk/Lhot O", lambda x: (fl(x["O_Lbk"]) / fl(x["O_Lhot"])) if fl(x["O_Lhot"]) else None),
            ("Lbk/Lhot O_fanillo", lambda x: (fl(x["O_fanillo_Lbk"]) / fl(x["O_fanillo_Lhot"]))
             if fl(x["O_fanillo_Lhot"]) else None)):
        v = [(x["z"], fn(x)) for x in pos if fn(x) is not None]
        lo = [b for a, b in v if a < 30]
        hi = [b for a, b in v if a >= 30]
        sp = spearman([a for a, _ in v], [b for _, b in v])
        bj = barajado([a for a, _ in v], [b for _, b in v])
        pr(f"{nombre:20s} z<30 {q(lo)} | z>=30 {q(hi)} | Spearman vs z "
           + (f"{sp:+.3f} barajado [{bj[0]:+.3f}, {bj[1]:+.3f}]" if sp is not None else "-"))

    # detalle por pasada
    pr("\n== DETALLE por pasada positiva (orden de cenit)")
    pr("hora_utc          sensorK          z     vM     Kmain   O      O_fan  O_sinh O_todoK O_comp geo_nn r2_lin  "
       "npixO npixK")
    for x in sorted(pos, key=lambda y: y["z"]):
        def g(b):
            v = fl(x[f"{b}_vrp"])
            return f"{v / x['vM']:6.3f}" if v else "   -  "
        km = f"{x['k_main_disp'] / x['vM']:6.3f}" if x["k_main_pub"] == 1 and x["k_main_disp"] else "   -  "
        pr(f"{x['hora_utc']} {x['k_sensor']:16s} {x['z']:5.1f} {x['vM']:6.2f} {km} {g('O')} {g('O_fanillo')} "
           f"{g('O_sinhalo')} {g('O_todoK')}  {g('O_comp')} {g('geo_nearest')} {g('r2_linear')}  "
           f"{x['O_npix']:>4s} {x['k_pc_npix']:>4s}")

    json.dump(resumen, open(AQUI / "s02_resumen.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False,
              default=str)
    cols = list(P[0].keys())
    with open(AQUI / "s02_por_pasada.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        w.writerows(P)
    (AQUI / "s02_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
