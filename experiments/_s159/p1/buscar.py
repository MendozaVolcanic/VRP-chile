# Ubica paginas (indice 0-based del PDF) donde aparecen palabras clave. Solo para UBICAR, no para citar (A95).
import sys, fitz, re
D = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\documentacion"
PDFS = {"c16": "sp426.5.pdf", "cap": "978-3-031-86841-2_9.pdf",
        "sd26": "Coppola_2026_SciData_Global_VRP_Dataset_s41597-026-08100-7.pdf",
        "ug": "MIROVA_Dashboard_UserGuide_V_2_5.pdf", "book": "978-3-031-86841-2.pdf"}
key = sys.argv[1]; pats = sys.argv[2:]
doc = fitz.open(D + "\\" + PDFS[key])
print(key, "paginas:", doc.page_count)
for i, p in enumerate(doc):
    t = p.get_text()
    for pat in pats:
        for m in re.finditer(pat, t, re.I):
            s = t[max(0, m.start()-150): m.end()+150].replace("\n", " ")
            print(f"[idx {i}] {pat!r}: ...{s}...")
