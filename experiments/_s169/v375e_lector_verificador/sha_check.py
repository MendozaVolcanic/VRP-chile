# Pregunta 1: si el sello estuviera roto, ¿se vería? Sí: compara el sha del arbol con el que fija el codigo. Control positivo: un archivo ajeno (probar_sombra.py) NO coincide.
import sys, importlib.util, hashlib
from pathlib import Path
sys.dont_write_bytecode=True
A=Path("D:/vrp-trabajo/temporales/s169_ver_lector/arbol")
sp=importlib.util.spec_from_file_location("S",A/"experiments/_s168/v375e_sombra/leer_sombra_v375e.py")
S=importlib.util.module_from_spec(sp); sp.loader.exec_module(S)
for d in (S.SHA_DEPS,S.SHA_SELLO_LECTOR):
    for p,s in d.items():
        h=S.sha256_lf(p); print("OK " if h==s else "MAL", p.relative_to(S.RAIZ), h[:12])
print("control positivo (debe ser MAL):", S.sha256_lf(A/"experiments/_s168/v375e_sombra/probar_sombra.py")==S.SHA_DEPS[S.V375/"evaluar.py"])
