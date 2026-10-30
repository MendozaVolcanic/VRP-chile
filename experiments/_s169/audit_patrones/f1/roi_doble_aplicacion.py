# Auditoría S169 f1: ¿qué pasa si roi_v750b_a_grillas.variante se aplica dos veces (B4 y luego B1)? Pregunta 1: si el
# comentario del YAML quedara mentiroso, ¿esta medición lo vería? Sí: compara el comentario con el brazo real.
# Control positivo: una sola aplicación (B1) deja el comentario "brazo B1".
import importlib.util, re, sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")
R = Path(__file__).resolve().parent / "roi_run"
spec = importlib.util.spec_from_file_location("roi", R / "scripts/roi_v750b_a_grillas.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
t0 = (R / "pipeline/grillas_mirova.yaml").read_text(encoding="utf-8")
def resumen(t):
    br = re.findall(r"brazo (B\d)", t)
    vals = sorted(set(re.findall(r"roi_v750: (\w+)", t)))
    return f"comentario dice brazo {br}; valores reales {vals}"
print("una vez B1      :", resumen(m.variante(t0, "B1")))
print("B4 y luego B1   :", resumen(m.variante(m.variante(t0, "B4"), "B1")))
print("B4 y luego B0   :", resumen(m.variante(m.variante(t0, "B4"), "B0")))
print("B4 luego B0 == original?", m.variante(m.variante(t0, "B4"), "B0") == t0)
