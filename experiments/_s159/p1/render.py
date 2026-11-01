import sys, fitz
D = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\documentacion"
PDFS = {"c16": "sp426.5.pdf", "cap": "978-3-031-86841-2_9.pdf",
        "sd26": "Coppola_2026_SciData_Global_VRP_Dataset_s41597-026-08100-7.pdf",
        "ug": "MIROVA_Dashboard_UserGuide_V_2_5.pdf", "book": "978-3-031-86841-2.pdf"}
key = sys.argv[1]
doc = fitz.open(D + "\\" + PDFS[key])
for a in sys.argv[2:]:
    i = int(a)
    clip = None
    pix = doc[i].get_pixmap(dpi=200)
    out = f"png/{key}_idx{i}.png"; pix.save(out); print(out, pix.width, pix.height)
