# S150 verificador. Perdidas de F (max) entre las positivas VIIRS 375 que B publica, por satelite, canal
# (tabla u OCR-solo) y zona del barrido. Pregunta: las dos perdidas de agosto son un caso aislado o un patron?
# Uso: python perdidas_por_satelite.py tabla_mayo.json tabla_junio.json ...  (tablas de armar_tabla.py)
import json, sys, io, collections
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
def zona(z): return "?" if z is None else ("nadir" if z < 36 else ("medio" if z < 52 else "borde"))
tot = collections.defaultdict(lambda: [0, 0])
for ruta in sys.argv[1:]:
    D = json.load(open(ruta, encoding="utf-8")); g = collections.defaultdict(lambda: [0, 0]); fuertes = []
    for k, v in D["pasadas"].items():
        vol, b, dt = k.split("|")
        if b != "VIIRS375" or len(v) != 2: continue
        c, f = v["control"], v["brazo"]
        if c["lab"] != "pos" or not c["pub"]: continue
        canal = "ocr" if c["alerta_solo_ocr"] else "tabla"
        for key in ((c["plataforma"], canal), (c["plataforma"], canal, zona(c["z"]))):
            g[key][0] += 1; g[key][1] += (not f["pub"]); tot[key][0] += 1; tot[key][1] += (not f["pub"])
        if (c["vrp_ref"] or 0) >= 0.5 and not f["pub"]:
            fuertes.append((vol, dt, c["plataforma"], canal, c["vrp_ref"], c["z"], c["disp"], c["pc_dist"], f["pc_dist"]))
    print("==", D["ventana"])
    for key in sorted(k for k in g if len(k) == 2): print("   %-14s %-5s publica B %3d | F pierde %2d" % (key + tuple(g[key])))
    for x in fuertes: print("   perdida >=0,5 MW: %s %s %s %s MIROVA %.2f MW | cenit %.1f | B disp %.3f MW, pc_dist %.1f km | F pc_dist %s" % x)
print("== TOTAL")
for key in sorted(tot): print("   %-40s publica B %3d | F pierde %2d (%.0f %%)" % (" ".join(key), tot[key][0], tot[key][1], 100 * tot[key][1] / tot[key][0]))
