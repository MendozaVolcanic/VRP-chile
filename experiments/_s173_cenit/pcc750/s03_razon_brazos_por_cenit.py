# -*- coding: utf-8 -*-
"""s03 (S173, cenit PCC V750): razón de cada brazo (grilla de s02 y brazos nativos del runner N) contra MIROVA por
pasada, partida por cenit, en Puyehue-Cordón Caulle.

POR QUÉ. Para atribuir el déficit de K a una pieza hace falta una base que reproduzca a MIROVA (razón ~1 y plana con
el cenit). En PCC la base del ejemplo (O, caja 7 x 7 al centro) no alerta nada (s02); las candidatas son S (21 x 21
sensible, B1 de V750-B) y C (círculo de 20 km sensible, B3). Sobre la base que reproduzca a MIROVA se lee qué pieza de
K, sola, baja el nivel o mete pendiente. Los brazos nativos de N (K, F = K con el fondo y la suma del código de MIROVA
sin recorte, en el gránulo sin remuestrear) separan lo que es fondo de lo que es remuestreo.

Razón «con ceros»: denominador fijo = pasadas con alerta de MIROVA pareada; un brazo que no da VRP > 0 cuenta 0. Y
«publica»: sólo si el brazo pasa el predicado de N (píxel más radiante dentro del inner).

Vara: igual que s01 (scraper, CONS+OCR, D-9 SN, +-120 s, VRP de la fila CONS si es ALERTA).
P1: K nativo del runner = K del tablero de hoy en las que publican (control de que N reproduce producción); K2 = K;
    control de escala x2 sobre la base; F record contra F_pc_central.
P2: referencia corrida +1 día; barajado del cenit 200, semilla 173.
Uso: python -B s03_razon_brazos_por_cenit.py
"""
from __future__ import annotations

import collections
import csv
import io
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
REPO = AQUI / "repo"
sys.path.insert(0, str(REPO / "scripts"))
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(AQUI))
sys.path.insert(0, str(AQUI / "src" / "s162"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import banco_paridad as bp  # noqa: E402
import ablacion as AB  # noqa: E402
from _est import fl, linea, med, q  # noqa: E402

VOL = "PuyehueCordonCaulle"
INS = AQUI / "insumos"
L = []


def pr(*x):
    s = " ".join(str(y) for y in x)
    print(s, flush=True)
    L.append(s)


def vrp_mirova(fs):
    al = [f for f in fs if bp.es_alerta(f["tipo"])]
    if not al:
        return None, None
    c = [f for f in al if f["source"] == "CONS"]
    f = (c or al)[0]
    return f["vrp_mw"], f


def main():
    filas = list(csv.DictReader(open(AQUI / "s02_por_pasada.csv", encoding="utf-8")))
    ventana = ("2026-04-01", "2026-10-31")
    bp.VOLS = [VOL]
    coords = bp._coords_por_volcan()
    inner = bp.inner_desde_html()
    ref = bp.cargar_referencia_unificada(bp.SNAP_CONS, bp.SNAP_OCR)
    por_vb, ns, nv, n_ref = bp.indexar_referencia(ref, coords, ventana, regla_minimas="SN")
    lista = por_vb.get((VOL, "VIIRS750"), [])
    recs = bp.cargar_nuestros(coords, inner, ventana)
    kmain = {(r["sensor"], r["dt"].strftime("%Y-%m-%d %H:%M")): r for r in recs if r["b"] == "VIIRS750"}
    res, obj = AB.cargar(INS)
    brazos = [c[:-5] for c in filas[0] if c.endswith("_npix") and c[:-5] not in AB.RUNNER]
    pr("== VARA: filas VIIRS750 PCC en ventana", len(lista), "| records K VIIRS750 PCC en main:", len(kmain))
    pr("brazos de grilla:", brazos)
    P = []
    ctrl = collections.Counter()
    for f in filas:
        dt = datetime.strptime(f["hora_utc"], "%Y-%m-%d %H:%M").replace(tzinfo=timezone.utc)
        vm, fm = vrp_mirova(bp.parear(lista, dt))
        vsh, _ = vrp_mirova(bp.parear(lista, dt + timedelta(days=1)))
        km = kmain.get((f["k_sensor"], f["k_datetime"]))
        x = dict(f)
        r = res[int(f["id"])]
        br = r["brazos"]
        for b in ("K", "K2", "C", "F", "FC"):
            rec = (br.get(b) or {}).get("record") or {}
            pc = rec.get("primary_cluster") or {}
            x[f"N{b}_pc"] = pc.get("vrp_mw")
            x[f"N{b}_scene"] = rec.get("vrp_mw")
            x[f"N{b}_npc"] = pc.get("n_pixels")
            x[f"N{b}_nanom"] = rec.get("n_anomalous_pixels")
        x["NF_pc_central"] = (br.get("F") or {}).get("F_pc_central")
        x["NF_escena_central"] = (br.get("F") or {}).get("F_escena_central")
        x["NK_nhot"] = (br.get("K") or {}).get("n_hot")
        x.update(vM=vm, srcM=(fm or {}).get("source"), distM=(fm or {}).get("dist_km"), vM_sh=vsh,
                 z=fl(f["z_record_K"]), k_main_disp=(km or {}).get("disp"), k_main_pub=(km or {}).get("pub"))
        ctrl["con_alerta" if vm else "sin_alerta"] += 1
        if vm and f["lab"] != "pos":
            ctrl["alerta_pero_lab_no_pos"] += 1
        if not vm and f["lab"] == "pos":
            ctrl["lab_pos_sin_alerta_hoy"] += 1
        if vm and fl(f["obj_mirova_vrp"]) is not None and abs(vm - fl(f["obj_mirova_vrp"])) > 1e-6:
            ctrl["vM_distinto_obj"] += 1
        if vsh:
            ctrl["par_corrido_1d"] += 1
        if km is None:
            ctrl["k_main_no_encontrado"] += 1
        P.append(x)
    pos = [x for x in P if x["vM"] and x["vM"] > 0]
    pr("\n== CONTROLES DEL PAREO")
    pr("pasadas con grilla:", len(P), "| con alerta MIROVA:", ctrl["con_alerta"], "| sin:", ctrl["sin_alerta"])
    pr("alerta pero lab no pos:", ctrl["alerta_pero_lab_no_pos"], "| lab pos sin alerta hoy:",
       ctrl["lab_pos_sin_alerta_hoy"], "| VRP MIROVA distinto del objetivo:", ctrl["vM_distinto_obj"])
    pr("P2: pares con la referencia +1 día:", ctrl["par_corrido_1d"], "de", len(P))
    pr("record K de main no encontrado:", ctrl["k_main_no_encontrado"])
    pr("fuente MIROVA de los positivos:", dict(collections.Counter(x["srcM"] for x in pos)))
    pr("ventana de los positivos:", min(x["hora_utc"] for x in pos), "a", max(x["hora_utc"] for x in pos),
       "| noches:", len({x["hora_utc"][:10] for x in pos}))
    pr("cenit de los positivos:", sorted(round(x["z"], 1) for x in pos))
    pr("n z<30:", sum(x["z"] < 30 for x in pos), "| n z>=30:", sum(x["z"] >= 30 for x in pos))
    pr("plataformas:", dict(collections.Counter(x["k_sensor"] for x in pos)))
    d = sum(1 for x in pos if x["NK_pc"] != x["NK2_pc"] or x["NK_scene"] != x["NK2_scene"])
    pr("K2 distinto de K:", d, "de", len(pos))
    dm = [(fl(x["k_main_disp"]), x["NK_pc"]) for x in pos if x["k_main_pub"] == 1]
    pr("K main publica en", len(dm), "| |K main - K runner pc| > 0,006 MW:",
       sum(1 for a, b in dm if a and b is not None and abs(a - b) > 0.006), "| detalle:",
       [(x["hora_utc"], x["k_main_disp"], x["NK_pc"]) for x in pos if x["k_main_pub"] == 1 and
        x["NK_pc"] is not None and abs((fl(x["k_main_disp"]) or 0) - x["NK_pc"]) > 0.006])
    pr("K main no publica pero N K pc > 0:",
       [(x["hora_utc"], x["NK_pc"], x["k_dc"]) for x in pos if x["k_main_pub"] != 1 and (x["NK_pc"] or 0) > 0])
    cf = [(x["NF_pc"], x["NF_pc_central"]) for x in pos if x["NF_pc"] is not None and x["NF_pc_central"] is not None]
    pr("F record pc vs F_pc_central: n", len(cf), "| |dif| > 0,01:", sum(1 for a, b in cf if abs(a - b) > 0.01))

    def r0(x, v, pubcol=None):
        v = fl(v)
        if pubcol is not None and x.get(pubcol) not in ("True", True):
            return 0.0
        return max(v, 0.0) / x["vM"] if v else 0.0

    resumen = {}
    pr("\n== RAZÓN CON CEROS (n fijo = positivos), magnitud del brazo (publique o no)")
    nat = [("K main tablero", lambda x: (fl(x["k_main_disp"]) or 0) / x["vM"] if x["k_main_pub"] == 1 else 0.0),
           ("N K pc", lambda x: r0(x, x["NK_pc"])), ("N K escena", lambda x: r0(x, x["NK_scene"])),
           ("N C pc", lambda x: r0(x, x["NC_pc"])), ("N F pc", lambda x: r0(x, x["NF_pc"])),
           ("N F pc central", lambda x: r0(x, x["NF_pc_central"])),
           ("N F escena central", lambda x: r0(x, x["NF_escena_central"])), ("N FC pc", lambda x: r0(x, x["NFC_pc"]))]
    for nombre, fn in nat:
        resumen[nombre] = linea(pr, nombre, [(x["z"], fn(x)) for x in pos])
    pr("")
    for b in brazos:
        resumen[b] = linea(pr, b, [(x["z"], r0(x, x[f"{b}_vrp"])) for x in pos])
    pr("\n== RAZÓN CON CEROS, sólo si el brazo PUBLICA (predicado de N)")
    for b in ("S", "C", "S_fan525_rec", "C_fan525_rec", "todoK525", "todoK525_fcodigo", "todoK2025"):
        resumen[f"{b}|pub"] = linea(pr, b + " pub", [(x["z"], r0(x, x[f"{b}_vrp"], f"{b}_pub")) for x in pos])
    pr("\n== CONTROL DE ESCALA: C x2")
    linea(pr, "C x2", [(x["z"], 2 * r0(x, x["C_vrp"])) for x in pos])

    pr("\n== DESCOMPOSICIÓN por cenit (positivos)")
    for nombre, fn in (
            ("npix S", lambda x: fl(x["S_npix"])), ("npix C", lambda x: fl(x["C_npix"])),
            ("npix todoK525", lambda x: fl(x["todoK525_npix"])), ("n_hot K nativo", lambda x: fl(x["NK_nhot"])),
            ("N K pc npix", lambda x: fl(x["NK_npc"])), ("N K n_anom", lambda x: fl(x["NK_nanom"])),
            ("N F pc npix", lambda x: fl(x["NF_npc"])),
            ("N K escena/pc", lambda x: fl(x["NK_scene"]) / fl(x["NK_pc"]) if fl(x["NK_pc"]) else None),
            ("C npix / n_hot K", lambda x: fl(x["C_npix"]) / fl(x["NK_nhot"]) if fl(x["NK_nhot"]) else None),
            ("Lbk/Lhot C", lambda x: fl(x["C_Lbk"]) / fl(x["C_Lhot"]) if fl(x["C_Lhot"]) else None),
            ("Lbk/Lhot C_fan525", lambda x: fl(x["C_fan525_Lbk"]) / fl(x["C_fan525_Lhot"])
             if fl(x["C_fan525_Lhot"]) else None),
            ("anillo525/Lbk_codigo por px", lambda x: fl(x["anillo525_L_med"]) / (fl(x["C_Lbk"]) / fl(x["C_npix"]))
             if fl(x["C_Lbk"]) and fl(x["C_npix"]) else None),
            ("L anillo 5-25 grilla", lambda x: fl(x["anillo525_L_med"])),
            ("L_bg K record", lambda x: fl(x["k_L_bg"])),
            ("t_bg K record", lambda x: fl(x["k_t_bg"])),
            ("dist K al centro km", lambda x: fl(x["k_dcen_km"])),
            ("dist pico C al centro km", lambda x: fl(x["C_pk_dcen_km"])),
            ("dist K - pico C km", lambda x: fl(x["d_k_Cpico_km"])),
            ("dist K - celda C más cerca km", lambda x: fl(x["d_k_Ccerca_km"])),
            ("dist K - pico S km", lambda x: fl(x["d_k_Spico_km"])),
            ("dist MIROVA km", lambda x: fl(x["distM"]))):
        v = [(x["z"], fn(x)) for x in pos if fn(x) is not None]
        linea(pr, nombre, v)

    pr("\n== DETALLE (orden de cenit): razón por pasada (con ceros)")
    pr("hora_utc         z     vM    Kmain  NKpc  NFpc  NFesc  S     C     Cf525r todoK  tKfcod npC nhK dK-Cpk dM")
    for x in sorted(pos, key=lambda y: y["z"]):
        def g(v):
            v = fl(v)
            return f"{v / x['vM']:5.2f}" if v is not None else "  -  "
        km = f"{(fl(x['k_main_disp']) or 0) / x['vM']:5.2f}" if x["k_main_pub"] == 1 else "  np "
        pr(f"{x['hora_utc']} {x['z']:5.1f} {x['vM']:5.2f} {km} {g(x['NK_pc'])} {g(x['NF_pc'])} "
           f"{g(x['NF_escena_central'])} {g(x['S_vrp'])} {g(x['C_vrp'])} {g(x['C_fan525_rec_vrp'])} "
           f"{g(x['todoK525_vrp'])} {g(x['todoK525_fcodigo_vrp'])} {x['C_npix']:>3} {x['NK_nhot']!s:>3} "
           f"{(fl(x['d_k_Cpico_km']) if fl(x['d_k_Cpico_km']) is not None else -1):6.2f} {fl(x['distM']) or -1:5.2f}")
    json.dump(resumen, open(AQUI / "s03_resumen.json", "w", encoding="utf-8"), indent=1, ensure_ascii=False,
              default=str)
    with open(AQUI / "s03_por_pasada.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(P[0].keys()))
        w.writeheader()
        w.writerows(P)
    (AQUI / "s03_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
