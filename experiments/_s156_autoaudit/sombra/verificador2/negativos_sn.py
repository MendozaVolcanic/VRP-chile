"""(iii) con la etiqueta original contra SN, sobre producción K (records con sha), VIIRS 375, en el tramo
retrospectivo. Mide cuánto mueve SN la tasa que se compara contra una cota del A/B calculada con la original.
Uso: python negativos_sn.py <copia> <ref>"""
import math
import os
import sys

copia, ref = sys.argv[1:3]
sys.path.insert(0, copia)
sys.path.insert(0, os.path.join(copia, "scripts"))
os.chdir(copia)
import banco_paridad as bp  # noqa: E402
import auto_audit_weekly as aa  # noqa: E402
from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402


def wilson(k, n, z=1.96):
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return round(c - m, 4), round(c + m, 4)


coords = aa._coords_por_volcan()
filas = cargar_referencia_unificada(os.path.join(ref, "registro_vrp_consolidado.csv"),
                                    os.path.join(ref, "registro_vrp_ocr.csv"))
for win in [("2026-09-18", "2026-10-08"), ("2026-09-18", "2026-10-17")]:
    recs = [r for r in bp.cargar_nuestros(coords, bp.inner_desde_html(), win) if r.get("sha")]
    for modo in ("original", "SN"):
        bp.etiquetar(recs, *bp.indexar_referencia(filas, coords, win, regla_minimas=modo)[:3])
        negs = [r for r in recs if r["b"] == "VIIRS375" and r["lab"] == "neg_limpio"]
        k = sum(bool(r["pub"]) for r in negs)
        print(win, modo, f"K V375 negativos limpios publicados {k} de {len(negs)}", wilson(k, len(negs)),
              "cota 0.0501")
