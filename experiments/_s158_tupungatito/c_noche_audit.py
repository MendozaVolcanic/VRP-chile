# -*- coding: utf-8 -*-
"""S158. Reproduce la magnitud publicada de Tupungatito VIIRS 375 del auto-audit (#864: 0,266x, n = 8, detector
K, ventana 2026-08-20 a 2026-10-19) con las MISMAS funciones del auto-audit, noche por noche, y la vuelve a
medir sobre toda la serie K que dejó #883.

POR QUÉ: la métrica del auto-audit divide, por noche, el máximo publicado nuestro por el máximo de las alertas
de MIROVA de esa noche, sin mirar a qué distancia está la alerta de MIROVA. Si la alerta máxima de una noche
es una anomalía LEJANA (fuera de los 7 km del inner), la noche entra con un denominador que no es el cráter.
b_series_mirova.py mostró que las dos alertas «protegidas» del 28 y 29 de septiembre son justamente eso.

Variantes (todas con el máximo nuestro publicado por noche, `pub` del auto-audit):
  A  auto-audit tal cual (D-9 SN, CONS ∪ OCR ∪ filas perdidas).
  B  A sin las dos alertas que MIROVA dibuja a más de 7 km (b_series_mirova_salida.txt).
  C  sólo alertas de la tabla latest.php (CONS): la distancia de la tabla es la de su pasada (A119; el OCR de
     Suomi NPP puede traer distancia y clase de otra pasada, memoria S150).
  D  C con distancia de la tabla <= inner (7 km): el cráter según MIROVA.
Ventanas: la del auto-audit (sólo noches K, 2026-09-18 en adelante, como el auto-audit) y la serie K
completa con referencia: 2026-02-14 (Tupungatito no existe en la tabla antes, A119) a --hasta.

Uso: python -I c_noche_audit.py [--hasta 2026-10-20]
"""
import argparse
import io
import json
import os
import statistics as st
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import auto_audit_weekly as aw  # noqa: E402

VOL, B = "Tupungatito", "VIIRS375"
# Las dos alertas que la serie «Last Month» de MIROVA dibuja en gris (>7 km): b_series_mirova_salida.txt,
# lámina 2026-09-29_04-54-00 (cabecera 06:36): 22,62 km / 2,72 MW y 9,58 km / 1,92 MW.
LEJANAS_POR_LAMINA = {"2026-09-28 05:18", "2026-09-29 04:54"}


def medir(alertas, recs, win, frontera, etiqueta, coords, salida):
    mir, inst, _ = aw.noches_mirova_con_instante(alertas, coords, win)
    nuestros = aw.nuestros_por_noche(recs, win, frontera)
    ours = nuestros["ours"]
    por_alerta = {}
    for a in alertas:
        if a["volcano"] == VOL and a["sensor_bucket"] == B and a.get("fecha_utc"):
            por_alerta[(a["fecha_utc"][:16])] = a
    filas = []
    for (vol, s, fecha), m in sorted(mir.items()):
        if vol != VOL or s != B or aw.detector_de_noche(fecha, frontera) != "K":
            continue
        o = ours.get((vol, s, fecha))
        if not (o and o["dash"]) or m <= 0:
            continue
        a = por_alerta.get(inst[(vol, s, fecha)][:16], {})
        filas.append({"noche": fecha, "M": m, "instante_M": inst[(vol, s, fecha)][:16], "fuente_M": a.get("source"),
                      "dist_M": a.get("dist_km"), "pub": max(o["pub"]), "n_pub": len(o["pub"]),
                      "R": max(o["pub"]) / m})
    rs = [f["R"] for f in filas]
    res = {"variante": etiqueta, "ventana": list(win), "n_noches": len(rs),
           "ratio_mediano": round(st.median(rs), 3) if rs else None, "noches": filas}
    salida.append(res)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hasta", default="2026-10-20")
    a = ap.parse_args()
    coords = aw._coords_por_volcan()
    recs, _ = aw.cargar_records()
    recs = {VOL: recs[VOL]}
    filas_ref = aw.cargar_filas_referencia()
    alertas = aw.aplicar_d9(aw.alertas_mirova(), aw.REGLA_MINIMAS, filas_ref)
    alertas_v = [x for x in alertas if x["volcano"] == VOL and x["sensor_bucket"] == B]
    inner = aw.INNER[VOL]
    variantes = {
        "A auto-audit": alertas_v,
        "B sin las 2 lejanas por lámina": [x for x in alertas_v if (x["fecha_utc"] or "")[:16] not in LEJANAS_POR_LAMINA],
        "C sólo tabla (CONS)": [x for x in alertas_v if x["source"] == "CONS"],
        "D tabla y dist <= inner": [x for x in alertas_v if x["source"] == "CONS" and x["dist_km"] is not None
                                    and x["dist_km"] <= inner],
    }
    salida = []
    frontera_audit = aw.leer_frontera_k()
    # #864 se escribió con la frontera de entonces (2026-09-18, #860); #883 la movió al 2025-02-15. Para
    # reproducir #864 se usa la de entonces; la segunda ventana es la misma con toda la data ya en K.
    ventanas = [("auto-audit", ("2026-08-20", "2026-10-19"), "2026-09-18"),
                ("auto-audit con toda la data K", ("2026-08-20", "2026-10-19"), "2025-01-01"),
                ("serie K con referencia", ("2026-02-14", a.hasta), "2025-01-01")]
    L = []
    P = L.append
    P(f"{VOL} {B}; inner {inner} km; frontera K del tablero hoy {frontera_audit}; regla D-9 {aw.REGLA_MINIMAS}")
    P(f"snapshot de la referencia: {aw.CONS}")
    for nombre_v, win, frontera in ventanas:
        P(f"\n=== ventana {nombre_v} {win[0]} a {win[1]} (noches K desde {frontera})")
        for et, al in variantes.items():
            r = medir(al, recs, win, frontera, f"{nombre_v} | {et}", coords, salida)
            P(f"  {et:34s} n {r['n_noches']:3d}  mediana {r['ratio_mediano']}")
        if nombre_v == "auto-audit":
            P("  detalle variante A (noche, M, instante de M, fuente, dist de la fila, publicado, pasadas, R):")
            for f in salida[-4]["noches"]:
                P(f"    {f['noche']}  M {f['M']:5.2f}  {f['instante_M']}  {f['fuente_M']}  dist {f['dist_M']}  "
                  f"pub {f['pub']:.3f}  n {f['n_pub']}  R {f['R']:.3f}")
    # serie K: noches de la variante A cuya alerta máxima es OCR, por mes (A119)
    serie_a = next(s for s in salida if s["variante"].startswith("serie K") and "A auto" in s["variante"])
    from collections import Counter
    P("\nserie K, variante A: fuente de la alerta máxima de cada noche, por mes")
    c = Counter((f["noche"][:7], f["fuente_M"]) for f in serie_a["noches"])
    for k in sorted(c):
        P(f"  {k[0]} {k[1]}: {c[k]}")
    P("serie K, variante A: mediana de R por fuente de la alerta máxima")
    for fu in ("CONS", "OCR"):
        rs = [f["R"] for f in serie_a["noches"] if f["fuente_M"] == fu]
        P(f"  {fu}: n {len(rs)}  mediana {round(st.median(rs), 3) if rs else None}")
    txt = "\n".join(L)
    print(txt)
    (AQUI / "c_noche_audit_salida.txt").write_text(txt + "\n", encoding="utf-8")
    (AQUI / "c_noche_audit_salida.json").write_text(json.dumps(salida, indent=1, ensure_ascii=False), encoding="utf-8")


if __name__ == "__main__":
    main()
