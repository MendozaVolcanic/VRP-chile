# -*- coding: utf-8 -*-
"""Mutaciones a mano de la marca «también hay calor en la cumbre»: cada una se aplica, se corre la prueba y se restaura.
Cuenta como atrapada sólo si pytest falla por una aserción (AssertionError / assert), no por una caída de carga."""
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
RAIZ = Path(sys.argv[1])
MUT = [
    ("M1 borde: > pasa a >=", "frontend/cumbre.js", "Number(d) > innerKm) continue;", "Number(d) >= innerKm) continue;"),
    ("M2 sin exigir la vía", "frontend/cumbre.js", 'r.via_codigo_mirova !== true || ', ""),
    ("M3 sin exigir far", "frontend/cumbre.js", ' || r.distance_class !== "far") return null;', ") return null;"),
    ("M4 elige la más vieja", "frontend/cumbre.js", "if (!best || t > best.t)", "if (!best || t < best.t)"),
    ("M5 sin corte de fecha", "frontend/cumbre.js", "if (!(t >= desdeMs)) continue;", ""),
    ("M6 sin filtro de la vista", "frontend/cumbre.js", "if (filtro && !filtro(r)) continue;", ""),
    ("M7 escribe en el record", "frontend/cumbre.js", "if (!m) return \"\";\n    const pc", "if (!m) return \"\";\n    r.marca = 1;\n    const pc"),
    ("M8 singular y plural cruzados", "frontend/cumbre.js", "(m.n === 1\n      ?", "(m.n !== 1\n      ?"),
    ("M9 index marca aunque no haya calor en la cumbre", "frontend/index.html",
     '  if (!m) return null;\n  const host = el("div", clase);\n  host.textContent = "◉ "',
     '  const host = el("div", clase);\n  host.textContent = "◉ "'),
    ("M10 mosaico sin cargar el módulo", "frontend/mosaico.html", ' <script src="cumbre.js"></script>', ""),
    ("M11 tabla con una sola rama", "frontend/index.html",
     '\n          if (i === 2) { const mc = marcaCumbre("marca-cumbre", v, r); if (mc) td.appendChild(mc); }   // S194: también calor en la cumbre', ""),
    ("M12 diario sin el conteo", "frontend/diario.html", "CumbreTablero.calorEnCumbre(r, INNER_RADIUS_KM[volcanoName])", "true"),
]
atrapadas = 0
for nombre, archivo, viejo, nuevo in MUT:
    p = RAIZ / archivo
    orig = p.read_bytes()
    s = orig.decode("utf-8")
    if s.count(viejo) != 1:
        print(nombre, ": NO SE APLICÓ (", s.count(viejo), "apariciones )")
        continue
    p.write_bytes(s.replace(viejo, nuevo).encode("utf-8"))
    try:
        o = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                            "tests/test_tablero_cumbre_s194.py"], cwd=RAIZ, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
    finally:
        p.write_bytes(orig)
    falla = o.returncode != 0
    por_asercion = falla and ("AssertionError" in o.stdout or "assert " in o.stdout)
    atrapadas += por_asercion
    ult = [l for l in o.stdout.splitlines() if l.startswith("FAILED")]
    print(f"{nombre}: {'ATRAPADA' if por_asercion else ('CAE SIN ASERCIÓN' if falla else 'NO ATRAPADA')} {ult[:2]}")
print("atrapadas por aserción:", atrapadas, "de", len(MUT))
