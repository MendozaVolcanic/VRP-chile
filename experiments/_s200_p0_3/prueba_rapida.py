"""Prueba de humo del arnés en una escena (no es la medición)."""
import time, json
import comun as C
import medir as M
C.utf8()
esc = [e for e in C.escenas() if e["clave"].startswith("NevadosDeChillan")][0]
t0 = time.time()
E = C.Escena(esc)
mask, d = E.detectar(E.m13g, E.m15g)
org = M.celda_pico(E, mask)
s13, s15, zona = M.quitar_anomalia(E, E.m13g, E.m15g, mask)
m2, d2 = E.detectar(s13, s15)
print("origen", org, "zona quitada", int(zona.sum()), "alertas R-sin", int(m2.sum()), "u2 p1", d2["pasada1"]["u_nti2"], "p2", d2["pasada2"]["u_nti2"])
pts = M.puntos(E, org)
print("puntos", len(pts), "sin pixel", sum("i" not in p for p in pts), f"{time.time()-t0:.1f}s")
p = [q for q in pts if "i" in q and q["d"] == 5.0][0]
for nb, (a, b) in {"con": (E.m13g, E.m15g), "sin": (s13, s15)}.items():
    t1 = time.time()
    print(nb, M.vrp_minimo(E, a, b, p, 1000.0), f"{time.time()-t1:.1f}s")
