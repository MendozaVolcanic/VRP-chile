# -*- coding: utf-8 -*-
"""F4 S158: renderizar páginas de los PDF a PNG (regla A95: leer la imagen, no la capa de texto)."""
import sys, fitz, pathlib
D = r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/documentacion/"
OUT = pathlib.Path("experiments/_s158_audit/f4/paginas"); OUT.mkdir(exist_ok=True)
pedidos = {
 "sp426.5.pdf": [6, 7],
 "campus2022_sensors_22_1713.pdf": [6, 7],
 "Coppola_2026_SciData_Global_VRP_Dataset_s41597-026-08100-7.pdf": [5, 7, 8],
 "978-3-031-86841-2_9.pdf": [5, 6],
 "Aveni_2024_TIRVolcH_RSE.pdf": [5, 11],
}
for f, pags in pedidos.items():
    doc = fitz.open(D + f)
    for p in pags:
        pix = doc[p-1].get_pixmap(dpi=200)
        nombre = OUT / f"{f.split('.pdf')[0][:20].replace(' ','_')}_p{p}.png"
        pix.save(str(nombre)); print(nombre, pix.width, pix.height)
