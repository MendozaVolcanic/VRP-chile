# -*- coding: utf-8 -*-
"""F2 M9. El tramo debil (MIROVA < 0,10 MW) es lo unico que queda para la decision de recall de `max` (S150 §0).
Agrega abril-agosto V375, con Wilson 95 %, con etiqueta completa y con etiqueta confiable estricta (tabla, u OCR
desde 2026-06-13 que no sea Suomi NPP; A119 + S150_IMAGENES_SNPP §3.2). Perdida = B publica y F no.
Control: los conteos por mes con etiqueta completa deben dar los de recall_por_magnitud (p. ej. junio <0,05: B 15, F 12)."""
import json, sys, io, math, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
def wilson(k, n, z=1.96):
    p = k / n; d = 1 + z * z / n; c = p + z * z / (2 * n); h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return 100 * (c - h) / d, 100 * (c + h) / d
def tramo(v):
    return "<0.05" if v < .05 else "0.05-0.10" if v < .10 else "0.10-0.20" if v < .20 else "0.20-0.50" if v < .5 else ">=0.5"
acc = collections.Counter()
for ruta in sys.argv[1:]:
    mes = ruta.replace("\\", "/").split("/")[-2]
    for k, v in json.load(open(ruta, encoding="utf-8"))["pasadas"].items():
        vol, s, dt = k.split("|")
        if s != "VIIRS375" or len(v) != 2: continue
        c, f = v["control"], v["brazo"]
        if c["lab"] != "pos" or c.get("vrp_ref") is None or not c["pub"]: continue
        t = tramo(c["vrp_ref"]); snpp = "SNPP" in (c.get("plataforma") or "")
        conf = (not c.get("alerta_solo_ocr")) or (dt[:10] >= "2026-06-13" and not snpp)
        for et in ("completa",) + (("confiable",) if conf else ()):
            acc[(et, t, "B")] += 1; acc[(et, t, "F")] += f["pub"]; acc[(et, mes, t, "B")] += 1; acc[(et, mes, t, "F")] += f["pub"]
for et in ("completa", "confiable"):
    print("== etiqueta", et)
    for t in ("<0.05", "0.05-0.10", "0.10-0.20", "0.20-0.50", ">=0.5"):
        b, fk = acc[(et, t, "B")], acc[(et, t, "F")]
        if b: lo, hi = wilson(b - fk, b); print("  %-10s B publica %4d | F pierde %3d = %4.1f %% [%4.1f, %4.1f]" % (t, b, b - fk, 100 * (b - fk) / b, lo, hi))
    b = acc[(et, "<0.05", "B")] + acc[(et, "0.05-0.10", "B")]; fk = acc[(et, "<0.05", "F")] + acc[(et, "0.05-0.10", "F")]
    lo, hi = wilson(b - fk, b); print("  <0.10 total B %d | F pierde %d = %.1f %% [%.1f, %.1f]" % (b, b - fk, 100 * (b - fk) / b, lo, hi))
    print("  por mes, <0.05 (B, F pierde):", {m: (acc[(et, m, "<0.05", "B")], acc[(et, m, "<0.05", "B")] - acc[(et, m, "<0.05", "F")]) for m in ("abril", "mayo", "junio", "julio", "agosto")})
