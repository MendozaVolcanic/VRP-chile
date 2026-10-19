"""F3: ¿avisos_de_ventana avisa por hitos POSTERIORES al fin de la ventana? P1: una ventana marzo-abril
no debería traer el hito del 2026-10-10; si lo trae, el filtro mira sólo el inicio. P2: imprime la lista entera."""
import sys, os
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "scripts"))
import calidad_referencia_mirova as c
for w in (("2026-03-01", "2026-04-30"), ("2026-08-20", "2026-10-19")):
    av = c.avisos_de_ventana(*w)
    print(w, len(av), [a[:10] for a in av], "posteriores_al_fin:", [a[:10] for a in av if a[:10] > w[1]])
