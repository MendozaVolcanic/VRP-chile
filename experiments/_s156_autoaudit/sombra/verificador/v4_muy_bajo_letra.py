# Verificador S156: disparador (i) de Muy Bajo leido segun la LETRA de la regla (por volcan, todos los sensores,
# cota V1 16 de 194) contra la version del codigo (por volcan y sensor, cota por sensor = max V1/V2 de las Muy Bajo
# PERDIDAS por K en terminos absolutos). Lee v3_instrumento_propio.json (instrumento propio, D-9 SN aplicada a mano:
# V375 <= 0,05 MW fuera). Tambien la cota diferencial acotada que el A/B permite deducir de la seccion 6.
import json, math, collections, sys
from pathlib import Path


def wilson(k, n, z=1.96):
    if not n:
        return (None, None)
    p = k / n
    den = 1 + z * z / n
    c = (p + z * z / (2 * n)) / den
    m = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, c - m), min(1.0, c + m))


filas = json.load(open(Path(__file__).with_name("v3_instrumento_propio.json")))
porvol = collections.defaultdict(lambda: [0, 0])
porvs = collections.defaultdict(lambda: [0, 0])
for r in filas:
    if r["sol"] >= 0 or r["A"]:
        continue
    if not any(t in ("ALERTA_TERMICA", "ALERTA_TERMICA_OCR") for t in r["tipos"]):
        continue
    if r["b"] == "VIIRS375" and r["vrp"] <= 0.05 + 1e-9:
        continue
    if r["p120"] is None or r["s120"] is None:
        continue
    hit = bool(r["s120"] and not r["p120"])
    for d, k in ((porvol, r["vol"]), (porvs, (r["vol"], r["b"]))):
        d[k][1] += 1
        d[k][0] += hit
cota_letra = wilson(16, 194)[1]
print("cota de la letra (V1 16 de 194, Wilson superior): %.4f" % cota_letra)
print("\nLETRA: por volcan, todos los sensores")
for v, (k, n) in sorted(porvol.items()):
    lo, hi = wilson(k, n)
    print("  %-20s %2d de %3d  Wilson [%.4f, %.4f]  dispara=%s" % (v, k, n, lo, hi, lo > cota_letra))
print("\nCOTAS que usa el codigo vs cota diferencial deducible del A/B (seccion 6, K lectura A):")
ab = {"MODIS": {"V1": (3, 4, 4), "V2": (5, 26, 25)}, "VIIRS375": {"V1": (16, 194, 0), "V2": (26, 388, 0)},
      "VIIRS750": {"V1": (14, 30, 10), "V2": (26, 75, 22)}}
for s, d in ab.items():
    cod = max(wilson(k, n)[1] for k, n, _ in d.values())
    # diferencial = #(C0 publica y K no) entre las Muy Bajo; C0 publica n - perdidasC0
    lim = []
    for nom, (kK, n, kC0) in d.items():
        c0pub = n - kC0
        lo_d, hi_d = max(0, kK - kC0), min(kK, c0pub)
        lim.append((nom, lo_d, hi_d, n, wilson(hi_d, n)[1]))
    print("  %-8s cota codigo %.4f | diferencial acotado: %s | cota diferencial maxima posible %.4f" % (
        s, cod, ["%s %d..%d de %d" % (a, b, c, e) for a, b, c, e, _ in lim], max(x[4] for x in lim)))
