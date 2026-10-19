"""C3: Muy Bajo VIIRS 375 en el tramo retrospectivo (datos K reprocesados), con instrumento propio.
Mide: (a) qué fracción de las Muy Bajo con record en ambos la sombra publica (si la sombra no publica todas,
el denominador de la vigilancia no es el del A/B, donde C0 publicó 194 de 194); (b) la tasa por volcán y su
cota inferior de Wilson contra la cota del A/B. No importa vigilancia_sombra.
Uso: python muy_bajo_retro.py <raiz> <ref>"""
import csv
import math
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone

raiz, ref = sys.argv[1:3]
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.argv = [sys.argv[0], raiz, ref]
import instrumento_propio as ip  # noqa: E402  (reusa sus lecturas; corre su impresión una vez)


def wilson(k, n, z=1.96):
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return c - m, c + m


COTA = max(wilson(16, 194)[1], wilson(26, 388)[1])
print("cota V1", round(wilson(16, 194)[1], 4), "cota V2", round(wilson(26, 388)[1], 4), "usada", round(COTA, 4))
for s in ("VIIRS375", "VIIRS750", "MODIS"):
    por_vol = defaultdict(lambda: [0, 0, 0, 0])   # k diferencial, n con ambos, sombra publica, k K-calla-total
    for (vol, ss, minuto), fs in ip.pasadas.items():
        if ss != s:
            continue
        vmax = max(v for _, v, _ in fs)
        if vmax >= 1.0 or (s == "VIIRS375" and vmax <= 0.05 + 1e-9):
            continue
        dt = fs[0][0]
        if dt >= ip.ADOP:
            continue
        pp, sp = ip.mira(ip.prod, vol, s, dt), ip.mira(ip.sombra, vol, s, dt)
        if pp is None or sp is None:
            continue
        c = por_vol[vol]
        c[1] += 1
        c[0] += sp and not pp
        c[2] += bool(sp)
        c[3] += not pp
    tk = sum(c[0] for c in por_vol.values()); tn = sum(c[1] for c in por_vol.values())
    ts = sum(c[2] for c in por_vol.values())
    print(f"{s}: total diferencial {tk} de {tn} (sombra publica {ts} de {tn})")
    for vol, (k, n, sp, kc) in sorted(por_vol.items()):
        lo, hi = wilson(k, n)
        print(f"   {vol:22s} k={k:3d} n={n:3d} sombra_pub={sp:3d} K_calla={kc:3d} wilson_lo={lo:.4f} "
              f"{'DISPARARIA' if s == 'VIIRS375' and lo > COTA else ''}"
              f" | tasa sobre sombra_pub: {k}/{sp}")
