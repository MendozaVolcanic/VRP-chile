import fitz, sys, os
pdf = sys.argv[1]; pages = sys.argv[2]; tag = sys.argv[3]
out = r"C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\e1f99d6e-4f81-45c2-a1de-37af83cf2b25\scratchpad\png"
os.makedirs(out, exist_ok=True)
d = fitz.open(pdf)
for p in pages.split(","):
    if "-" in p:
        a,b = p.split("-"); rng = range(int(a), int(b)+1)
    else:
        rng = [int(p)]
    for i in rng:
        pg = d[i]
        pix = pg.get_pixmap(dpi=200)
        f = os.path.join(out, "%s_p%03d.png" % (tag, i))
        pix.save(f)
        print(f)
