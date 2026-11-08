# -*- coding: utf-8 -*-
"""P4 (F5b): leer con tesseract la cabecera «Last Update» y las etiquetas de fecha de los 10 paneles de una lámina.
Control positivo: las 4 láminas de validación, cuya pasada se conoce por el TIF (nombre = adquisición).
Uso: python -I p4_ocr.py [png ...]; salida JSON por lámina en stdout."""
import json, os, re, sys
import numpy as np
from PIL import Image
import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
sys.stdout.reconfigure(encoding="utf-8")
TMP = r"C:\Users\nmend\vrp-temporales\s175_audit\f5b"
DEF = ["20260612_153203_VIIRS375_Latest10NTI.png", "20260809_082023_VIIRS375_Latest10NTI.png",
       "20260621_092513_VIIRS750_Latest10NTI.png", "20260922_092431_VIIRS375_Latest10NTI.png"]
RE = re.compile(r"(\d{2})-([A-Za-z]{3})-(\d{4})\s*(\d{2}):(\d{2}):(\d{2})")   # la lista blanca de tesseract se come el espacio
CFG = "--psm 7 -c tessedit_char_whitelist=0123456789-:JanFebMrApyulgSOctNovDLstUpdae "


def leer(img, escala=3):
    g = img.convert("L").resize((img.width * escala, img.height * escala), Image.LANCZOS)
    a = np.array(g)
    a = np.where(a < 170, 0, 255).astype(np.uint8)   # texto rojo o negro sobre fondo claro
    t = pytesseract.image_to_string(Image.fromarray(a), config=CFG)
    m = RE.search(t)
    return (t.strip(), "%s-%s-%s %s:%s:%s" % m.groups() if m else None)


def main(pngs):
    for png in pngs:
        im = Image.open(os.path.join(TMP, "png", png)).convert("RGB")
        cab = leer(im.crop((85, 45, 440, 78)))
        paneles = []
        for k in range(10):
            col, row = k % 5, k // 5
            x0, y0 = 8 + 165 * col, 146 + 236 * row
            paneles.append(leer(im.crop((x0, y0, x0 + 162, y0 + 16))))
        print(json.dumps({"png": png, "cabecera": cab, "paneles": paneles}, ensure_ascii=False))


if __name__ == "__main__":
    main(sys.argv[1:] or DEF)
