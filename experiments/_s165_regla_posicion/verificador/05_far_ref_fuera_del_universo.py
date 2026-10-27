# -*- coding: utf-8 -*-
"""Verificador S165 (regla de posición), 5: las pasadas con FALSO_POSITIVO de la tabla que los universos de VIIRS no
contienen, y cuántas de ellas MIROVA mismo resuelve «cerca del cráter» en su imagen (OCR). Sólo lectura.

POR QUÉ. La configuración que decide (un alertado débil en el cráter y otro más radiante lejos) es justo la que la
tabla de MIROVA etiqueta FALSO_POSITIVO cuando publica el lejano (así quedó el único cambio de MODIS, lab far_ref).
Las poblaciones de S159 para VIIRS (neg_limpio y pos) no las contienen, así que el «resto 0» de las tablas de VIIRS
750 y VIIRS 375 del informe no mide esa configuración: la excluye. Aquí se cuenta cuántas pasadas nocturnas son, y en
cuántas el OCR de la misma pasada trae una alerta a menos del inner (MIROVA vio el cráter en la imagen y publicó el
lejano en la tabla), que es la cota inferior de pasadas de esa configuración que «cercano» cambiaría de publicación
si nuestro detector tuviera también el píxel del cráter (SIN DATO: no hay grillas para correr la vía ahí).
Uso: python 05_far_ref_fuera_del_universo.py  (escribe 05_far_ref_fuera_del_universo_salida.txt)
"""
import collections
import io
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent))
import comun as C  # noqa: E402

L = []


def pr(*x):
    s = " ".join(str(v) for v in x)
    L.append(s)
    print(s, flush=True)


TIER_A = ["Chaiten", "Copahue", "Isluga", "Lascar", "Lastarria", "Llaima", "NevadosDeChillan", "PlanchonPeteroa",
          "PuyehueCordonCaulle", "Tupungatito", "Villarrica"]
VENTANA = {"MODIS": ("2026-03-01", "2026-10-16 23:59"), "VIIRS750": ("2026-04-01", "2026-10-21 23:59"),
           "VIIRS375": ("2026-04-01", "2026-10-21 23:59")}


def main():
    idx, proc = C.cargar_referencia()
    V = C.volcanes()
    filas = [f for lst in idx.values() for _, f in lst]
    for b, (d0, d1) in VENTANA.items():
        fp = [f for f in filas if f["sensor_bucket"] == b and f["source"] == "CONS" and f["volcano"] in TIER_A
              and f["tipo"] == "FALSO_POSITIVO" and d0 <= f["fecha_utc"][:16] <= d1
              and 0 <= int(f["fecha_utc"][11:13]) < 12]
        pasadas = {(f["volcano"], f["fecha_utc"][:16]) for f in fp}
        con_ocr_cerca, con_ocr_lejos, sin_ocr = [], [], 0
        for f in fp:
            inner = V[f["volcano"]]["inner_radius_km"]
            ocr = [o for o in C.parear(idx, f["volcano"], b, f["fecha_utc"][:16]) if o["source"] == "OCR"
                   and o["dist_km"] is not None and (o["vrp_mw"] or 0) > 0]
            if not ocr:
                sin_ocr += 1
            elif any(o["dist_km"] <= inner for o in ocr):
                con_ocr_cerca.append((f, ocr))
            else:
                con_ocr_lejos.append((f, ocr))
        pr(f"\n== {b} ({d0} a {d1[:10]}): FALSO_POSITIVO nocturnos de la tabla, Tier A: {len(fp)} filas en "
           f"{len(pasadas)} pasadas (fuera de los universos de VIIRS; en MODIS son el lab far_ref)")
        pr(f"   por volcán:", dict(collections.Counter(f['volcano'] for f in fp)))
        pr(f"   dist de la tabla (km): mín {min(f['dist_km'] for f in fp):.2f}, mediana "
           f"{sorted(f['dist_km'] for f in fp)[len(fp) // 2]:.2f}, máx {max(f['dist_km'] for f in fp):.2f}")
        pr(f"   con OCR de la misma pasada a menos del inner (MIROVA vio el cráter en la imagen): {len(con_ocr_cerca)}; "
           f"con OCR sólo lejos: {len(con_ocr_lejos)}; sin OCR: {sin_ocr}")
        for f, ocr in con_ocr_cerca[:40]:
            pr(f"      {f['volcano']} {f['fecha_utc'][:16]} tabla FP {f['vrp_mw']} MW a {f['dist_km']} km | OCR "
               + "; ".join(f"{o['tipo']} {o['vrp_mw']} MW a {o['dist_km']} km" for o in ocr))
        pr("   (A119: el OCR tiene distancia desde el 2026-06-13; antes de esa fecha una fila OCR sin distancia no cuenta)")
    (AQUI / "05_far_ref_fuera_del_universo_salida.txt").write_text("\n".join(L) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
