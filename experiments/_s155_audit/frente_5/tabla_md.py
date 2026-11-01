# -*- coding: utf-8 -*-
"""S155 frente 5: escribe tabla_pasadas.md (tabla pasada por pasada del INFORME) desde pareo_pasadas.json y
estratos.json, para que ningun numero del informe se transcriba a mano. Columnas: ver la leyenda que se imprime."""
import json, os
D = os.path.dirname(os.path.abspath(__file__))
todas = json.load(open(os.path.join(D, "pareo_pasadas.json"), encoding="utf-8"))
est = {(f["t"], f["b"]): f for f in json.load(open(os.path.join(D, "estratos.json"), encoding="utf-8"))}
def n(x, d=2):
    return "-" if x is None or x != x else ("%." + str(d) + "f") % x
L = ["| pasada UTC | grupo | satelite | cenit | MIROVA MW (fuente) | reg | publicado MW | R pub | R cumulo sin modo 1 px | R todo alertado <=5 km | R fondo -20 K | R fondo 0 | frac fondo pico | f req | fs | fa | modo 1 px | cumulos |",
     "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
for f in sorted(todas, key=lambda f: (f["t"], f["b"])):
    m = f["mir"]
    R = lambda x: (x / m) if (x is not None and m) else None  # noqa
    e = est.get((f["t"], f["b"]), {})
    fn = f["pc"] is None
    L.append("| %s | %s | %s | %s | %s (%s) | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s | %s |" % (
        f["t"], f["b"], f["sat"].replace("VIIRS_", "").replace("_750", ""), n(f["zen"], 1), n(m), f["fuente"], f["reg"],
        "FN (sin cumulo)" if fn else n(f["pub"]), n(R(f["pub"])), n(R(f["pc_sum"])), n(R(f["inner"])),
        n(e.get("Rbg20")), n(R(f["nobg_inner"])), n(f["frac_bg"]), n(e.get("f_req")), n(f["fs"]), n(f["fa"]),
        "-" if fn else ("si" if f["spm"] else "no"), f["n_clu"]))
open(os.path.join(D, "tabla_pasadas.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
print("filas:", len(L) - 2)
