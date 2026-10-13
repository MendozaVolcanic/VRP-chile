# -*- coding: utf-8 -*-
"""F2 M2. ¿El "F conserva 946 de 988 (95,7 %)" y el "35,7 a 2,7 %" dependen de etiquetas que A119 y el defecto
del OCR (imagen de otra pasada, S150) declaran no confiables? Estratifica las positivas V375 que B publica por
canal (tabla / solo OCR), por fecha (antes o desde el 2026-06-13, A119) y por satelite.
Pregunta 1: si la etiqueta "solo OCR" estuviera rota, el recall de ese estrato se veria distinto del de la tabla.
Pregunta 2: el conteo total tiene que reproducir 988/946 (control positivo de que leo las mismas tablas).
Ventana: 2026-04-01 a 2026-08-27 (pre #535 en los records de PRODUCCION; los brazos son reproceso con codigo de hoy)."""
import json, sys, io, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
acc = collections.Counter(); ejemplos = collections.defaultdict(list)
for ruta in sys.argv[1:]:
    T = json.load(open(ruta, encoding="utf-8"))["pasadas"]
    for k, v in T.items():
        vol, s, dt = k.split("|")
        if s != "VIIRS375" or len(v) != 2: continue
        c, f = v["control"], v["brazo"]
        if c["lab"] != "pos" or not c["pub"]: continue
        canal = "soloOCR" if c.get("alerta_solo_ocr") else "tabla"
        tramo = "antes0613" if dt[:10] < "2026-06-13" else "desde0613"
        plat = "SNPP" if "SNPP" in (c.get("plataforma") or "") else ("N20" if "NOAA20" in (c.get("plataforma") or "") else ("N21" if "NOAA21" in (c.get("plataforma") or "") else str(c.get("plataforma"))))
        for key in (("TOTAL",), (canal,), (canal, tramo), (canal, plat), (canal, tramo, plat)):
            acc[key + ("n",)] += 1; acc[key + ("f",)] += f["pub"]
print("V375, positivas que B publica, y cuantas conserva F")
keys = sorted({k[:-1] for k in acc})
for k in keys:
    n, fk = acc[k + ("n",)], acc[k + ("f",)]
    print("  %-34s n %4d | F conserva %4d (%.1f %%) | pierde %d" % ("/".join(k), n, fk, 100 * fk / n, n - fk))
# conjunto "confiable" mas estricto: tabla, u OCR desde 0613 que NO sea SNPP (S150_IMAGENES_SNPP §3.2)
n = acc[("tabla", "n")] + sum(acc[("soloOCR", "desde0613", p, "n")] for p in ("N20", "N21"))
fk = acc[("tabla", "f")] + sum(acc[("soloOCR", "desde0613", p, "f")] for p in ("N20", "N21"))
print("\nconfiable estricto (tabla + OCR desde 06-13 sin SNPP): n %d | F conserva %d (%.1f %%) | pierde %d" % (n, fk, 100 * fk / n, n - fk))
