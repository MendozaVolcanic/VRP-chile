# -*- coding: utf-8 -*-
"""S150. Clasifica cada alerta que B publica por el CAMINO por el que B la publico y, para las que F pierde,
por la condicion que la rechaza en F, hasta donde los records permiten deducirlo.

Deducciones (codigo: detection_context.py:525-552 primer pase, 943-967 segundo pase; process_viirs.py
1182-1364):
 - Primer pase de B: umbral min(C1, mu+C2 sd) = C1 en la cumbre (mu+5sd > C1 en 983 de 983, estratos.py),
   mas la compuerta bt > t_bg + 3 K (D22). Primer pase de F: max(C1, mu+5sd), misma compuerta.
 - Si B tiene pixeles del primer pase (diag_n_first_pass_pixels > 0) y F no publica, esos pixeles pasaron
   dNTI > C1, dETI > C1 y la compuerta, y en F fallaron dNTI > mu+5sd o dETI > mu_e+5sd_e (mu, sd identicos
   en los dos brazos: perdidas_max.py). Cual de los dos tests falla no se puede saber: los records no
   guardan el dNTI ni el dETI por pixel.
 - Si B NO tiene pixeles del primer pase, lo publicado salio del segundo pase SIN condicionar (se corre
   aunque el primero este vacio, D2/D19) y SIN compuerta de BT. Si el pixel publicado tiene bt - t_bg < 3 K,
   la compuerta lo bloqueaba en el primer pase de los DOS brazos: la conectiva no decide ahi; decide que el
   segundo pase de F exige mu2 + 5 sd2, con mu2 y sd2 calculados sin los filtros de no-aptos (D26) y NO
   persistidos.
 - Etiqueta: alerta solo del OCR antes del 2026-06-13 (A119: sin distancia medida, geometria mal calibrada
   hasta el 2026-06-11) se marca aparte; las 5 filas OCR de Suomi NPP con la imagen de otra pasada
   (docs/S150_IMAGENES_SNPP.md) se excluyen.

  python clases_rechazo.py filas.json
"""
import collections, io, json, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
F = json.load(open(sys.argv[1], encoding="utf-8"))
MALAS = {"Lastarria|VIIRS375|2026-05-02 05:06", "Isluga|VIIRS375|2026-05-29 04:54", "Lascar|VIIRS375|2026-06-25 04:54",
         "Lascar|VIIRS375|2026-08-17 05:00", "Lascar|VIIRS375|2026-08-22 05:06"}


def camino(r):
    b = r["B"]
    if b["diag_n_first_pass_pixels"]:
        return "B por 1.er pase"
    exc = (b["ap_bt_max"] - b["t_bg_k"]) if b.get("ap_bt_max") is not None and b.get("t_bg_k") else None
    if exc is not None and exc < 3.0:
        return "B solo 2.o pase, BT < t_bg+3K (compuerta D22 lo bloquea en ambos)"
    return "B solo 2.o pase, BT >= t_bg+3K"


def etiqueta(r):
    if r["clave"] in MALAS:
        return "OCR imagen de otra pasada"
    if r["solo_ocr"]:
        return "solo OCR, antes 06-13" if r["dt"] < "2026-06-13" else "solo OCR, desde 06-13"
    return "tabla"


def f_estado(r):
    f = r["F"] or {}
    if not f.get("n_anomalous_pixels"):
        return "F sin pixeles"
    return "F con pixeles, cumulo a %s km" % ("<5" if (f.get("pc_dist") or 99) < 5 else ">=5")


for b in ("VIIRS375", "VIIRS750"):
    sel = [r for r in F if r["b"] == b]
    print("\n==", b, "| alertas que B publica:", len(sel), "| F pierde:", sum(r["perdida"] for r in sel))
    c = collections.defaultdict(lambda: [0, 0])
    for r in sel:
        c[camino(r)][0 if r["perdida"] else 1] += 1
    for k, (p, k2) in sorted(c.items()):
        print("   %-70s pierde %3d de %4d (%.0f %%)" % (k, p, p + k2, 100 * p / (p + k2)))
    L = [r for r in sel if r["perdida"]]
    print("   perdidas por etiqueta:", dict(collections.Counter(etiqueta(r) for r in L)))
    print("   perdidas por estado de F:", dict(collections.Counter(f_estado(r) for r in L)))
    print("   cruce camino x etiqueta (perdidas):")
    for (k1, k2), n in sorted(collections.Counter((camino(r), etiqueta(r)) for r in L).items()):
        print("      %-70s %-28s %d" % (k1, k2, n))
    limpias = [r for r in L if etiqueta(r) in ("tabla", "solo OCR, desde 06-13")]
    print("   perdidas con etiqueta confiable (tabla, o OCR desde 06-13):", len(limpias),
          "| por camino:", dict(collections.Counter(camino(r) for r in limpias)))
