# -*- coding: utf-8 -*-
"""S155 frente 5, control de identidad del pareo: el OCR de MIROVA lee el cenit del satelite de su propia imagen
(Zenith_Sat_deg, entero). Si nuestra pasada y la de MIROVA son el mismo granulo, |nuestro cenit - OCR| < 1,5 grados.
Pregunta 2: si el pareo emparejara pasadas distintas (otro satelite a la misma hora), la diferencia seria de decenas."""
import json, os
f = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "pareo_pasadas.json"), encoding="utf-8"))
c = [(x["t"], x["b"], x["zen"], float(x["zen_ocr"])) for x in f if x["zen_ocr"] not in ("", None) and x["zen"] is not None]
d = [abs(a - b) for _, _, a, b in c]
print("pares con cenit OCR: %d de %d; |diferencia| max %.2f, n > 1,5 grados: %d" % (len(c), len(f), max(d), sum(1 for x in d if x > 1.5)))
