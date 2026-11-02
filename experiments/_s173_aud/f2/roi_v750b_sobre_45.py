# -*- coding: utf-8 -*-
"""S173 F2 hallazgo 202: ¿el script de V750-B (rama s169-roi-v750) funciona sobre la grilla de 45 de #932?
Corre variante() del script real sobre el pipeline/grillas_mirova.yaml del árbol A+B+#932+s169 (worktree s173-f2-combo).
Pregunta 1: si el script se rompiera con 45 entradas, lanzaría ValueError o dejaría roi distinto de lo esperado en los 11.
Pregunta 2: control: B0 sobre el archivo de hoy debe dar el archivo tal cual (0 notas de brazo)."""
import sys, importlib.util, yaml
sys.stdout.reconfigure(encoding="utf-8")
ruta = sys.argv[1]
spec = importlib.util.spec_from_file_location("R", ruta + "/scripts/roi_v750b_a_grillas.py"); R = importlib.util.module_from_spec(spec); spec.loader.exec_module(R)
t = R.YAML.read_text(encoding="utf-8")
print("grilla:", R.YAML, "entradas:", len(yaml.safe_load(t)["volcanes"]))
for b in ("B0", "B1", "B2", "B3", "B4", "B5"):
    try:
        n = R.variante(t, b); d = yaml.safe_load(n)["volcanes"]
        print(b, "ok; entradas", len(d), "; roi de los 11:", sorted({d[v]["roi_v750"] for v in R.VOLCANES}),
              "; roi de los 34:", sorted({v["roi_v750"] for k, v in d.items() if k not in R.VOLCANES}),
              "; notas de brazo:", n.count("Puesto por la lectura de V750-B"), "; B0 idéntico:", (b == "B0" and n == t) or None)
    except Exception as e:
        print(b, "EXCEPCION", type(e).__name__, e)
