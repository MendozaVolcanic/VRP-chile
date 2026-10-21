# -*- coding: utf-8 -*-
"""S158: anatomia de las alertas de VIIRS 750 que K no publica, con los campos persistidos del record (sin red).

POR QUE. `listar_perdidas.py` separa dos mecanismos: M1 (el detector no alerta ningun pixel) y M3 (alerta un pixel en
el crater, pero su magnitud queda en 0 y el tablero lo oculta porque isValidDetection pide pc.vrp_mw > 0). Para decir
QUE pasa fisicamente hay que mirar de que etapa sale el pixel (primer pase o recaptura del segundo) y si su BT de M13
queda bajo la temperatura del fondo del anillo (t_bg_k), que es lo que deja la resta L_pixel - L_fondo en cero o
negativa. Y para que el numero signifique algo, el mismo conteo se hace sobre las positivas que SI publicamos y sobre
los negativos limpios (pasadas en que MIROVA miro y no vio nada): si el patron M3 es igual de frecuente donde MIROVA
calla, no distingue nada.

Uso:  python experiments/_s158_v750/anatomia.py   (lee los JSON de produccion y el snapshot, igual que listar_perdidas)
"""
from __future__ import annotations

import collections
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import listar_perdidas as lp  # noqa: E402  (instala sys.path del repo)
import banco_paridad as bp  # noqa: E402
from referencia_mirova_unificada import SNAP_CONS, SNAP_OCR, cargar_referencia_unificada  # noqa: E402

VENTANA = (bp.INICIO_DEFECTO, "2026-10-21")


def patron(r):
    """Clase del record por lo que el detector dejo, independiente de la etiqueta de MIROVA."""
    npx = r.get("n_anomalous_pixels") or 0
    if npx == 0 and not r.get("pc_vrp"):
        return "sin_pixel"
    if r["pub"]:
        return "publica"
    if r["summit"] and r.get("pc_vrp") == 0:
        return "summit_vrp0"
    return "otro_no_publica"


def etapa(r):
    fp, rc = r.get("diag_n_first_pass_pixels") or 0, r.get("diag_n_second_pass_recapture") or 0
    if fp and rc:
        return "primer_pase+recaptura"
    if fp:
        return "solo_primer_pase"
    if rc:
        return "solo_recaptura"
    return "ninguna(otro_camino)"


def bajo_fondo(r):
    if r.get("px_bt_crater") is None or r.get("t_bg_k") is None:
        return "sin_dato"
    return "bt_pixel<=t_bg" if r["px_bt_crater"] <= r["t_bg_k"] else "bt_pixel>t_bg"


def tabla(titulo, sel, f):
    c = collections.Counter(f(r) for r in sel)
    print(f"  {titulo} (n {len(sel)}): " + ", ".join(f"{k} {v}" for k, v in sorted(c.items())))


def mediana(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.median(xs), 2) if xs else None   # verificador S158: antes daba la mediana superior


def main():
    coords = bp._coords_por_volcan()
    inner = bp.inner_desde_html()
    filas = cargar_referencia_unificada(SNAP_CONS, SNAP_OCR)
    por_vb, ns, nv, _ = bp.indexar_referencia(filas, coords, VENTANA, regla_minimas="SN")
    recs = lp.cargar_v750(coords, inner, VENTANA)
    bp.etiquetar(recs, por_vb, ns, nv)

    grupos = {"pos": [r for r in recs if r["lab"] == "pos"],
              "neg_limpio": [r for r in recs if r["lab"] == "neg_limpio"],
              "todos": recs}
    print(f"ventana {VENTANA[0]} a {VENTANA[1]}, VIIRS 750 nocturno, detector K")
    for g, sel in grupos.items():
        print(f"\n[{g}]")
        tabla("patron del record", sel, patron)
    pos = grupos["pos"]
    neg = grupos["neg_limpio"]
    m3 = [r for r in pos if patron(r) == "summit_vrp0"]
    pub = [r for r in pos if r["pub"]]
    m1 = [r for r in pos if patron(r) == "sin_pixel"]
    print("\nEtapa de la que sale el pixel alertado:")
    tabla("M3 perdidas (summit, VRP 0)", m3, etapa)
    tabla("positivas publicadas", pub, etapa)
    tabla("negativos limpios summit VRP 0", [r for r in neg if patron(r) == "summit_vrp0"], etapa)
    print("\nBT del pixel alertado (M13) contra la temperatura del fondo del anillo:")
    tabla("M3 perdidas", m3, bajo_fondo)
    tabla("positivas publicadas", pub, bajo_fondo)
    print("\nMedianas (M3 perdidas | publicadas): "
          f"t_bg {mediana([r['t_bg_k'] for r in m3])} | {mediana([r['t_bg_k'] for r in pub])}; "
          f"BT pixel crater {mediana([r['px_bt_crater'] for r in m3])} | {mediana([r['px_bt_crater'] for r in pub])}; "
          f"cenit {mediana([r['z'] for r in m3])} | {mediana([r['z'] for r in pub])}")
    print("\nM1 (ningun pixel alertado), medianas: "
          f"t_max {mediana([r['t_max_k'] for r in m1])}, t_bg {mediana([r['t_bg_k'] for r in m1])}, "
          f"nti_max {mediana([r['nti_max'] for r in m1])}, cenit {mediana([r['z'] for r in m1])}, "
          f"dist t_max {mediana([r['diag_t_max_dist_km'] for r in m1])} km")
    zs = sorted(round(r["z"], 1) for r in m1 if r["z"] is not None)
    print(f"M1, cenit de cada pasada: {zs}; con 35 grados o mas: {sum(z >= 35 for z in zs)} de {len(zs)}")
    con_px_pos = [r for r in pos if patron(r) != "sin_pixel"]
    con_px_neg = [r for r in neg if patron(r) != "sin_pixel"]
    print("Condicionado a que haya algun pixel alertado, fraccion summit VRP 0: "
          f"positivas {sum(patron(r) == 'summit_vrp0' for r in con_px_pos)} de {len(con_px_pos)}, "
          f"negativos limpios {sum(patron(r) == 'summit_vrp0' for r in con_px_neg)} de {len(con_px_neg)}")
    print("\nPor volcan, positivas: publicadas / M3 / M1:")
    for v in bp.VOLS:
        s = [r for r in pos if r["vol"] == v]
        if s:
            c = collections.Counter(patron(r) for r in s)
            print(f"  {v:20s} n {len(s):3d}  publica {c['publica']:3d}  summit_vrp0 {c['summit_vrp0']:3d}  "
                  f"sin_pixel {c['sin_pixel']:3d}  otro {c['otro_no_publica']:2d}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
