import fitz, os, sys, re
src = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\documentacion"
out = r"C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\e1f99d6e-4f81-45c2-a1de-37af83cf2b25\scratchpad\txt"
pdfs = []
for root, dirs, files in os.walk(src):
    for f in files:
        if f.lower().endswith(".pdf"):
            pdfs.append(os.path.join(root, f))
for p in pdfs:
    name = os.path.basename(p)[:-4].replace(" ", "_")[:80]
    dst = os.path.join(out, name + ".txt")
    if os.path.exists(dst): continue
    try:
        d = fitz.open(p)
        if d.page_count > 500:
            print("SKIP grande", name, d.page_count); d.close(); continue
        with open(dst, "w", encoding="utf-8") as fh:
            for i, pg in enumerate(d):
                fh.write("\n@@@PAG %d@@@\n" % i)
                fh.write(pg.get_text())
        d.close()
        print("ok", name)
    except Exception as e:
        print("ERR", name, e)
