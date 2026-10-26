"""S163: costo EQUIVALENTE a precio de API de los tokens medidos en los transcripts locales.

POR QUE: el plan de proceso pide un rango de costo, no un numero unico. Esto NO es lo que
Nicolas pago (si usa suscripcion, pago la cuota); es lo que costaria el mismo trafico por API.
Precios: tabla de la skill claude-api (cacheada 2026-10-06), USD por millon de tokens.
Supuestos declarados, que dan el rango:
  - escritura de cache: 1,25x el input (TTL 5 min) en el piso, 2x (TTL 1 h) en el techo;
  - lectura de cache: el precio publicado cuando la tabla lo da (Opus 5.5 0,20; Sonnet 5.5 0,20;
    Fable 5.1 0,25); si no lo da, 0,1x el input en el techo y 0,05x en el piso.
Entrada: los totales por modelo que imprime medir_transcripts.py (copiados abajo desde
medir_transcripts.out por el propio script, no a mano).
"""
import re, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
P = {  # input, output, cache_read publicado (o None)
 "claude-opus-5-5": (4, 20, 0.20), "claude-opus-5": (5, 25, None), "claude-fable-5-1": (10, 50, 0.25),
 "claude-fable-5": (10, 50, None), "claude-opus-4-8": (5, 25, None), "claude-opus-4-7": (5, 25, None),
 "claude-sonnet-5-5": (2, 10, 0.20), "claude-sonnet-5": (2, 10, None), "claude-haiku-4-5-20251001": (1, 5, None)}
txt = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "medir_transcripts.out"), encoding="utf-8").read()
lo = hi = 0.0
for mod, inp, cw, cr, out in re.findall(r"^\s+(claude[\w.-]+): input=([\d.]+)M cache_creation=([\d.]+)M cache_read=([\d.]+)M output=([\d.]+)M", txt, re.M):
    pi, po, pcr = P[mod]; inp, cw, cr, out = map(float, (inp, cw, cr, out))
    crl = pcr if pcr else 0.05 * pi; crh = pcr if pcr else 0.10 * pi
    l = inp*pi + cw*1.25*pi + cr*crl + out*po; h = inp*pi + cw*2*pi + cr*crh + out*po
    lo += l; hi += h; print(f"{mod:28s} USD {l:9,.0f} a {h:9,.0f}")
print(f"TOTAL ventana de los transcripts: USD {lo:,.0f} a {hi:,.0f}")
