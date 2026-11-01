import sys, fitz, re
D = r"C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\documentacion\978-3-031-86841-2.pdf"
doc = fitz.open(D); a, b = int(sys.argv[1]), int(sys.argv[2])
for i in range(a, b):
    t = doc[i].get_text()
    for pat in sys.argv[3:]:
        for m in re.finditer(pat, t, re.I):
            s = t[max(0, m.start()-130): m.end()+130].replace("\n", " ")
            print(f"[idx {i} lib {i-3}] {pat!r}: ...{s}...")
