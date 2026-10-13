# -*- coding: utf-8 -*-
"""F2 M10. La tabla de MIROVA casi no lista Suomi NPP (A119, frente B S149). ¿Cuantos negativos limpios V375
aporta cada satelite, y como publican B y F en las pasadas SIN etiqueta (sin_info) de cada satelite?
Pregunta 1: si `max` no apagara nada en SNPP, la tasa F/B de SNPP en sin_info lo mostraria.
Ventana abril-agosto 2026 (brazos reprocesados con el mismo codigo)."""
import json, sys, io, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
a = collections.Counter()
for ruta in sys.argv[1:]:
    for k, v in json.load(open(ruta, encoding="utf-8"))["pasadas"].items():
        vol, s, dt = k.split("|")
        if s != "VIIRS375" or len(v) != 2: continue
        c, f = v["control"], v["brazo"]; p = c.get("plataforma") or "?"
        p = "SNPP" if "SNPP" in p else "N20" if "NOAA20" in p else "N21" if "NOAA21" in p else p
        a[(p, c["lab"], "n")] += 1; a[(p, c["lab"], "B")] += c["pub"]; a[(p, c["lab"], "F")] += f["pub"]
for p in ("N20", "N21", "SNPP"):
    for lab in ("neg_limpio", "sin_info", "pos", "far_ref"):
        n, b, f = a[(p, lab, "n")], a[(p, lab, "B")], a[(p, lab, "F")]
        if n: print("%-5s %-11s n %5d | B publica %4d (%5.1f %%) | F publica %4d (%5.1f %%) | F/B %.2f" % (p, lab, n, b, 100 * b / n, f, 100 * f / n, f / b if b else float("nan")))
