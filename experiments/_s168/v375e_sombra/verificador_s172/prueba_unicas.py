# Verificador S172: cada mutacion de MUTACIONES aparece exactamente una vez en el lector (si no, el nulo ABORTA con rc=2).
# Q1: si una cuenta fuera 0 o 2 el script lo diria. Q2: un script muerto no imprime "N de N".
import importlib.util, sys
from pathlib import Path
sys.dont_write_bytecode = True
W = Path("D:/vrp-trabajo/worktrees/s172-relector/experiments/_s168/v375e_sombra"); sys.path.insert(0, str(W))
spec = importlib.util.spec_from_file_location("MS", W / "mutar_sombra.py"); MS = importlib.util.module_from_spec(spec); spec.loader.exec_module(MS)
src = (W / "leer_sombra_v375e.py").read_text(encoding="utf-8")
malas = [(m[0], src.count(m[1])) for m in [MS.CONTROL, MS.CONTROL_SECCION] + MS.MUTACIONES if src.count(m[1]) != 1]
print("mutaciones totales:", len(MS.MUTACIONES), "| con conteo != 1:", malas)
print("R07 en MUTACIONES:", any(m[0] == "R07" for m in MS.MUTACIONES), "| linea de R07 en el lector:", src.count("return ruta in PERFILES_REGIMEN and viejo != nuevo"))
print("S01..S08 presentes:", [m[0] for m in MS.MUTACIONES if m[0].startswith("S")])
print("EQUIVALENTES:", sorted(MS.EQUIVALENTES))
print("RAMA:", MS.RAMA)
