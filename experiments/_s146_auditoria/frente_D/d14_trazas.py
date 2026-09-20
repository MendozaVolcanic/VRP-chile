# -*- coding: utf-8 -*-
"""d14: trazas a fuente de tres cierres de A/B (no re-medibles: sus brazos no estan en disco).
(a) A85 / catalogo: '0 robos en 214 noches focales': suma la tabla de docs/AUDIT_S118_C2_GATES_AB.md.
(b) divergencia D12: 'cura 76 noches de Lascar': busca la fila en docs/AUDIT_S121_D12_AB.md.
(c) divergencia D18: n_detecciones circulo vs caja en experiments/_s130_d18/veredicto_d18.json.
Instrumento: (1) si la tabla no existiera el regex da 0 filas y se imprime. (2) idem."""
import io, sys, re, json, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
t = open(os.path.join(ROOT, "docs/AUDIT_S118_C2_GATES_AB.md"), encoding="utf-8").read().split("## _c2ab_2pass_off")[0]
rows = re.findall(r"\| (\w+) \| (focal|nevado) \| (\d+) \| (\d+) \|", t)
print("filas", len(rows), "focal noches", sum(int(n) for _, g, n, _ in rows if g == "focal"), "robos", sum(int(x) for _, g, _, x in rows if g == "focal"),
      "| nevado noches", sum(int(n) for _, g, n, _ in rows if g == "nevado"), "robos", sum(int(x) for _, g, _, x in rows if g == "nevado"))
for l in open(os.path.join(ROOT, "docs/AUDIT_S121_D12_AB.md"), encoding="utf-8"):
    if "76" in l: print("S121:", l.strip()[:200])
d = json.load(open(os.path.join(ROOT, "experiments/_s130_d18/veredicto_d18.json"), encoding="utf-8"))
for v, x in d.items(): print(v, x["circulo"]["n_detecciones"], x["caja"]["n_detecciones"], "noches perdidas", x["noches_mirova_perdidas"])
