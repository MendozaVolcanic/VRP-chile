import sys, collections
sys.path.insert(0, r"C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile")
from scripts.referencia_mirova_unificada import cargar_referencia_unificada
ref = cargar_referencia_unificada()
w = [f for f in ref if "2026-05-09" <= f["fecha_utc"][:10] <= "2026-05-20"]
print("filas referencia totales:", len(ref), "| ventana 2026-05-09..20:", len(w))
print("buckets:", collections.Counter(f["sensor_bucket"] for f in w))
print("tipos:", collections.Counter(f["tipo"] for f in w))
print("volcanes:", sorted(set(f["volcano"] for f in w)))
print("source:", collections.Counter(f["source"] for f in w))
i = [f for f in w if f["sensor_bucket"]=="VIIRS375"]
print("VIIRS375 en ventana:", len(i), collections.Counter(f["tipo"] for f in i))
for f in i[:6]: print(f)
