import sys, os
arbol, d = sys.argv[1], sys.argv[2]
sys.path.insert(0, arbol); sys.path.insert(0, arbol + "/scripts")
os.environ["VRP_PROFILE"] = "mirova_equivalent"
import referencia_mirova_unificada as rmu, clase_mirova as cm
from pathlib import Path
ref = rmu.cargar_referencia_unificada(Path(d)/"registro_vrp_consolidado.csv", Path(d)/"registro_vrp_ocr.csv", None, None)
print(ref)
ps = cm.resumir_pasadas(ref, canal="union", regla_minimas=cm.MODO_MINIMAS)
print(ps)
