"""S136 - el canal NRT de MIROVA, muestra un piso de INTENSIDAD en la practica?

POR QUE ESTA PREGUNTA Y NO LA DEL PAPER. Laiolo 2026 describe un filtro "in terms of distance
and/or intensity" que deja el 12 % de los datos, PERO en voz pasiva, con sujeto "the VRP time
series (Fig. 2)" y resultado en el material suplementario: es la preparacion del DATASET de ese
estudio, no el pipeline NRT. Aplicarlo al pipeline seria el drift de la Eq.16 (S99). Lo que si
es legitimo es medir el comportamiento OBSERVABLE del canal que comparamos: si MIROVA NRT nunca
publica por debajo de cierto VRP, hay un piso de facto, y eso es una divergencia medible.

READ-ONLY sobre el ground truth ya en disco. Reporta con denominador y ventana (A90).
"""
import os, sys, statistics as st
from collections import Counter
ROOT = r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
sys.path.insert(0, ROOT); sys.path.insert(0, os.path.join(ROOT, "scripts"))
os.environ["VRP_PROFILE"] = "mirova_equivalent"
from pipeline.mirova_csv_loader import load_mirova_alertas

SNAP = os.path.join(ROOT, "data", "mirova_reference", "mirova_v1_snapshot")
al = load_mirova_alertas(cons_path=os.path.join(SNAP, "registro_vrp_consolidado.csv"),
                         ocr_path=os.path.join(SNAP, "registro_vrp_ocr.csv"))
v = [(a.get("vrp_mw"), a.get("sensor_bucket"), a.get("fuente") or a.get("source"))
     for a in al if isinstance(a.get("vrp_mw"), (int, float)) and a["vrp_mw"] > 0]
print(f"alertas de MIROVA con VRP > 0 en el ground truth: {len(v)}\n")

vals = sorted(x[0] for x in v)
def q(p): return vals[min(len(vals)-1, int(p*len(vals)))]
print(f"  minimo   {vals[0]:.4f} MW")
print(f"  p01      {q(.01):.4f}      p05 {q(.05):.4f}      p10 {q(.10):.4f}")
print(f"  mediana  {st.median(vals):.4f}      p90 {q(.90):.3f}      maximo {vals[-1]:.1f}")

print("\n  cuantas alertas por DEBAJO de cada corte candidato:")
for corte in (0.02, 0.05, 0.1, 0.2, 0.5):
    n = sum(1 for x in vals if x < corte)
    print(f"    < {corte:4.2f} MW : {n:6d}  ({100*n/len(vals):5.1f} %)")

print("\n  por sensor (minimo y p05), que es donde se veria un piso por instrumento:")
for b in sorted({x[1] for x in v if x[1]}):
    s = sorted(x[0] for x in v if x[1] == b)
    if len(s) < 20: continue
    print(f"    {b:10s} n={len(s):6d}  min {s[0]:.4f}  p05 {s[int(.05*len(s))]:.4f}  "
          f"mediana {st.median(s):.3f}")

print("\n  los 12 valores mas chicos publicados (si hay piso, se ve como un salto):")
print("   ", [round(x, 4) for x in vals[:12]])
