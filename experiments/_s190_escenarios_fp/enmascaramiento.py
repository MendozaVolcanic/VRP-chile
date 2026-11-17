# -*- coding: utf-8 -*-
"""S190, escenario 10: enmascaramiento. Una pasada con calor en la cumbre y calor lejos a la vez.

POR QUÉ. MIROVA publica un solo número por pasada: la suma del VRP de todos los píxeles alertados (D32), y la réplica
hace lo mismo a propósito. Si en la misma pasada hay un foco lejano (un incendio a 15 km) y una señal débil en la
cumbre, el número mezcla las dos, y la posición (en la vía, el cúmulo más radiante, regla «radiante») puede quedar
lejos: el tablero no publica la pasada y la señal de cumbre queda escondida. Este script mide cuántas pasadas tienen
píxeles alertados a la vez dentro y fuera del radio interior y estima cuánto VRP pone cada lado.

Qué guardan los records (vía «código MIROVA», `pipeline/mirova_v750_codigo.py`): cada píxel alertado con su
distancia al cráter y su temperatura de brillo MIR (`anomaly_pixels`, `bt_k`), y el total de la pasada: `vrp_mw` =
coef × (L_hot − L_bk), con L_hot y L_bk sumas de radiancia sobre los alertados (`diag_codigo_mirova`). NO guardan el VRP
por píxel ni por cúmulo, ni el fondo de cada píxel. Estimación: radiancia de cada píxel por Planck desde `bt_k` a la λ
MIR del sensor (la misma de la vía), fondo de cada píxel = L_bk / npix (fondo medio), y coef = vrp_mw / (L_hot − L_bk)
leído del propio record. El reparto suma el total salvo el error de la reconstrucción (control abajo); su sesgo es que un píxel lejano en el llano tiene un
fondo más tibio que uno en la cumbre, y el fondo medio le asigna de más al llano y de menos a la cumbre (sentido esperado; magnitud sin medir).
Se comprueba que Σ Planck(bt_k) reproduzca L_hot.

Uso (raíz del repo, checkout de origin/main):
    python experiments/_s190_escenarios_fp/enmascaramiento.py > experiments/_s190_escenarios_fp/salida_enmascaramiento.txt
"""
from __future__ import annotations

import io
import math
import statistics
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import escenarios_fp as ef  # noqa: E402
from pipeline import mirova_v750_codigo as via  # noqa: E402

LAM_MIR = {"MODIS": 3.959, "VIIRS750": 4.05, "VIIRS375": 3.74}   # pipeline/mirova_v750_codigo.py, LAMBDA_*
C1, C2 = 1.191042e8, 1.4387752e4   # W µm⁴ m⁻² sr⁻¹, µm K (Planck en W m⁻² sr⁻¹ µm⁻¹, unidades de L_hot)
UMBRAL = 1.0


def planck(t_k, lam_um):
    """Inversa exacta de la que usó la vía para escribir `bt_k` (mismas constantes h, c, k del `.m`)."""
    return float(via.temperatura_a_radiancia(t_k, lam_um))


def main():
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    recs = ef.cargar()
    mir = ef.pasadas_mirova()
    filas, errores_lhot = [], []
    pub_noche = Counter()
    for (conj, n), d in recs.items():
        for (r, origen) in d.values():
            g = ef.fila(conj, n, r, origen)
            if g["vrp_pub"] > 0:
                pub_noche[g["noche"]] += 1
    for (conj, n), d in recs.items():
        inner = ef.INNER_34 if conj == "34" else float(ef.VOLC[n]["inner_radius_km"])
        for (r, origen) in d.values():
            if not r.get("via_codigo_mirova") or not (r.get("vrp_mw") or 0) > 0 or ef.es_noche(r) is False:
                continue
            dg = r.get("diag_codigo_mirova") or {}
            pix = r.get("anomaly_pixels") or []
            L_hot, L_bk = dg.get("L_hot"), dg.get("L_bk")
            if not pix or L_hot is None or L_bk is None or L_hot - L_bk <= 0:
                continue
            lam = LAM_MIR[ef.bucket(r["sensor"])]
            Lp = [planck(p["bt_k"], lam) for p in pix]
            errores_lhot.append(abs(sum(Lp) - L_hot) / L_hot)
            coef = r["vrp_mw"] / (L_hot - L_bk)
            bk = L_bk / len(pix)
            cumbre = sum(coef * (L - bk) for L, p in zip(Lp, pix) if p["dist_km"] <= inner)
            fuera = sum(coef * (L - bk) for L, p in zip(Lp, pix) if p["dist_km"] > inner)
            n_in = sum(1 for p in pix if p["dist_km"] <= inner)
            n_out = len(pix) - n_in
            if n_in == 0 or n_out == 0:
                continue
            f = ef.fila(conj, n, r, origen)
            for canal in ("union", "tabla"):
                p = ef.par_mirova(mir[canal], f) if conj == "11" and f["t"] >= ef.DESDE[canal] else None
                f[f"mir_{canal}"] = p.estado if p else ("sin_fila" if conj == "11" and f["t"] >= ef.DESDE[canal] else None)
                f[f"mir_{canal}_prot"] = bool(p and ef.cm.es_protegida(p))
                f[f"mir_{canal}_solo_ocr"] = bool(p and p.solo_ocr)
                f[f"mir_{canal}_dist"] = p.dist_km if p else None
            f.update({"n_in": n_in, "n_out": n_out, "vrp_cumbre": cumbre, "vrp_fuera": fuera,
                      "dmax": max(p["dist_km"] for p in pix)})
            filas.append(f)

    print(f"raíz: {ef.ROOT}")
    print(f"control de la reconstrucción: |Σ Planck(bt_k) − L_hot| / L_hot, mediana {statistics.median(errores_lhot):.2e}, "
          f"p99 {sorted(errores_lhot)[int(0.99 * len(errores_lhot))]:.2e}, máx {max(errores_lhot):.2e} "
          f"en {len(errores_lhot)} pasadas nocturnas de la vía con VRP > 0")
    for conj in ("11", "34"):
        F = [f for f in filas if f["conj"] == conj]
        pub = [f for f in F if f["vrp_pub"] > 0]
        esc = [f for f in F if f["vrp_pub"] == 0]
        print(f"\nconjunto {conj}: pasadas con píxeles alertados dentro Y fuera del radio interior: {len(F)} "
              f"(publicadas {len(pub)}, no publicadas {len(esc)}); volcanes {dict(Counter(f['volcan'] for f in F).most_common(6))}")
        # (b1) publicadas mezcladas: la cumbre sola ¿cruzaría 1 MW?
        cruza = [f for f in pub if f["vrp_pub"] >= UMBRAL > f["vrp_cumbre"]]
        print(f"  publicadas: VRP publicado ≥ 1 MW pero cumbre estimada < 1 MW (cambio de clase por la parte lejana): {len(cruza)}; "
              f"fracción mediana del VRP que pone lo lejano {statistics.median(f['vrp_fuera']/f['vrp_mw'] for f in pub) if pub else float('nan'):.2f}")
        # (b2) escondidas: la pasada no se publica (cúmulo más radiante lejos) aunque haya alertados en la cumbre
        alta = [f for f in esc if f["vrp_cumbre"] >= UMBRAL]
        print(f"  no publicadas con alertados en la cumbre: {len(esc)}; cumbre estimada ≥ 1 MW: {len(alta)}; "
              f"cumbre estimada > 0: {sum(1 for f in esc if f['vrp_cumbre'] > 0)}; noches {len({f['noche'] for f in esc})}")
        if conj == "11":
            for nombre, S in (("publicadas", pub), ("no publicadas", esc)):
                print(f"  MIROVA union en {nombre}: {dict(Counter(f['mir_union'] for f in S if f['mir_union']))}; "
                      f"protegidas A pareadas {sum(f['mir_union_prot'] for f in S)}")
            print("  no publicadas que MIROVA dio como alerta o fp (union):")
            for f in sorted((f for f in esc if f["mir_union"] in ("alerta", "fp")), key=lambda x: x["t"]):
                print(f"    {f['volcan']} {f['t']:%Y-%m-%d %H:%M} {f['sensor']} total {f['vrp_mw']:.2f} MW, cumbre est. "
                      f"{f['vrp_cumbre']:.2f}, lejos est. {f['vrp_fuera']:.2f}, píxeles {f['n_in']}+{f['n_out']}, "
                      f"más lejano {f['dmax']:.1f} km; MIROVA {f['mir_union']} prot {f['mir_union_prot']} sólo_ocr {f['mir_union_solo_ocr']} "
                      f"dist_MIROVA {f['mir_union_dist']} tabla {f['mir_tabla']}; "
                      f"otras publicadas nuestras esa noche {pub_noche[f['noche']]}")
        print(f"  detalle de las no publicadas con cumbre estimada ≥ 1 MW:")
        for f in sorted(alta, key=lambda x: x["t"]):
            print(f"    {f['volcan']} {f['t']:%Y-%m-%d %H:%M} {f['sensor']} total {f['vrp_mw']:.2f}, cumbre {f['vrp_cumbre']:.2f}, "
                  f"lejos {f['vrp_fuera']:.2f}, {f['n_in']}+{f['n_out']} px, MIROVA union {f['mir_union']} tabla {f['mir_tabla']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
