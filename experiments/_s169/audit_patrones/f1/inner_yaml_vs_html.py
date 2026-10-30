# Auditoría S169 f1 (P-G): el B3 del probe usa inner_radius_km de frontend/index.html (banco_paridad.inner_desde_html);
# la vía y la prueba de la rama de la ROI usan el de volcanoes.yaml. ¿Son iguales en los 11? (main 443da8649)
import re, yaml, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
D = Path(__file__).resolve().parent
vy = {v["name"]: v for v in yaml.safe_load((D / "vy_main.yaml").read_text(encoding="utf-8"))["volcanoes"]}
src = (D / "idx_main_443da8649.html").read_text(encoding="utf-8")
out = {}
for m in re.finditer(r'name:\s*"(\w+)".*?inner_radius_km:\s*([\d.]+)', src):   # banco_paridad.inner_desde_html l.94-100
    out.setdefault(m.group(1), float(m.group(2)))
V = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan", "Llaima", "Villarrica",
     "Copahue", "PuyehueCordonCaulle", "Chaiten"]
bad = [v for v in V if out.get(v) != float(vy[v]["inner_radius_km"])]
print("comparados", len(V), "distintos", bad or "ninguno")
# control positivo: si un valor cambiara, se vería
out2 = dict(out); out2["Lascar"] = 6.0
print("control positivo (Lascar html=6.0):", [v for v in V if out2.get(v) != float(vy[v]["inner_radius_km"])])
