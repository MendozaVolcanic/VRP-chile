# -*- coding: utf-8 -*-
"""F4 S158: localizar páginas de los PDF por la capa de texto (sólo para UBICAR; la lectura se hace renderizando)."""
import sys, io, fitz
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
D = r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile/documentacion/"
buscar = {
 "sp426.5.pdf": ["Table 1", "Table 2", "K1", "0.003", "0.010", "ROI"],
 "campus2022_sensors_22_1713.pdf": ["Table 1", "same used for MODIS", "threshold", "ROI", "5 x 5", "5 × 5", "K1", "0.7", "0.8"],
 "Coppola_2026_SciData_Global_VRP_Dataset_s41597-026-08100-7.pdf": ["Table 1", "hotspot-detection code", "Code Availability", "threshold", "MODIS", "375"],
 "978-3-031-86841-2_9.pdf": ["Table", "K1", "0.003", "NTI"],
 "Aveni_2024_TIRVolcH_RSE.pdf": ["Table 1", "Table 2", "threshold", "ROI", "I5", "200"],
 "1-s2.0-S0377027322002384-main.pdf": ["Table 1", "threshold", "VIIRS"],
}
for f, pats in buscar.items():
    try:
        doc = fitz.open(D + f)
    except Exception as e:
        print("NO ABRE", f, e); continue
    print("=====", f, "paginas:", doc.page_count)
    for pat in pats:
        pags = [i+1 for i in range(doc.page_count) if doc[i].search_for(pat)]
        print(f"  '{pat}': {pags[:40]}")
