import sys, importlib.util, os
from pathlib import Path
sys.dont_write_bytecode=True
A=Path("D:/vrp-trabajo/temporales/s169_ver_lector/arbol").resolve()
sp=importlib.util.spec_from_file_location("S",A/"experiments/_s168/v375e_sombra/leer_sombra_v375e.py")
S=importlib.util.module_from_spec(sp); sp.loader.exec_module(S)
deps,malos=S.cargar_deps()
import banco_paridad as B
import pipeline.profile as p
from pipeline.diurno import flag_viirs_diurno
print("VRP_PROFILE=",os.environ.get("VRP_PROFILE"),"| S0 ok:",bool(deps),malos,"| PROFILE_NAME:",p.PROFILE_NAME,"| ENABLE_DAYTIME_VIIRS:",p.ENABLE_DAYTIME_VIIRS,"| flag_viirs_diurno():",flag_viirs_diurno())
