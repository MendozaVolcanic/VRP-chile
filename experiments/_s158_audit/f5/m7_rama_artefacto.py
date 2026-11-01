# -*- coding: utf-8 -*-
"""F5 medicion 7. Control positivo de la medicion 1(b)/(c): ¿se ejercita alguna vez la rama isThermalArtifact
(cirrus / campo difuso) del predicado del tablero? Si nunca dispara en la ventana, el acuerdo 0 discordancias entre el
criterio 'dash' del auto-audit y el predicado con node no prueba que el auto-audit vea esa rama.
Ventanas: 2026-03-01 a 2026-10-20 (todo el periodo con referencia sana, A119) y la de K (2026-09-18 a 2026-10-18)."""
import collections, io, os, sys
from pathlib import Path
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "scripts")); os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")
import banco_paridad as bp  # noqa
capt = {}
orig = bp.correr_node
def espia(casos):
    out = orig(casos); capt["out"] = out; return out
bp.correr_node = espia
coords, inner = bp._coords_por_volcan(), bp.inner_desde_html()
for V in (("2026-03-01", "2026-10-20"), ("2026-09-18", "2026-10-18")):
    recs = bp.cargar_nuestros(coords, inner, V)
    c = collections.Counter()
    for r, p in zip(recs, capt["out"]):
        summit, valid, art = p[0], p[1], p[2]
        if summit and valid:
            c[(r["b"], "art" if art else "no_art")] += 1
    print(V, "records nocturnos", len(recs), "| summit y valido, por sensor y rama artefacto:", dict(sorted(c.items())))
