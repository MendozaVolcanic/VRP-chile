"""Corre el instrumento original sin tocarlo: solo redirige AQUI al directorio temporal."""
import sys, importlib.util
from pathlib import Path
repo = Path(sys.argv[1]); datos = Path(sys.argv[2])
spec = importlib.util.spec_from_file_location("lpt", repo / "experiments/_s147_lectura/lectura_por_tramo.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
m.AQUI = datos
sys.argv = ["x"] + sys.argv[3:]
sys.exit(m.main())
