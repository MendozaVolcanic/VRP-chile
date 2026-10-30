import sys, importlib.util
from pathlib import Path
sys.dont_write_bytecode=True
A=Path("D:/vrp-trabajo/temporales/s169_ver_lector/arbol").resolve()
sp=importlib.util.spec_from_file_location("S",A/"experiments/_s168/v375e_sombra/leer_sombra_v375e.py")
S=importlib.util.module_from_spec(sp); sp.loader.exec_module(S)
B=S.BASE_REGIMEN
print("base contra si misma (esperado []):", S.diff_git(B,B))
print("sha inexistente (esperado None):", S.diff_git(B,"0"*40))
print("base contra el sha de origin/main cc388729 (pipeline/):", S.diff_git(B,"cc38872901fff1600ac92c6069dfe65f611be355"))
print("base contra 983f6f28d (tag del lector):", S.diff_git(B,"983f6f28d24dbc298d0300977790c9d04d6c06b9"))
