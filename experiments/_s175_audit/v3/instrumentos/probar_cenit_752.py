# Q1: si controles_cenit (commit 752d348bc) rotulara ROJO el insumo vacio, este script lo mostraria (estado impreso); Q2: instrumento muerto => excepcion/Traceback, no un estado.
# Control positivo: fila 'alertas sin cenit' tambien se imprime; se compara con lo que ctl["controles_cenit"] (l.1227) hace con 'SIN SUSTRATO'.
# Sustrato: filas sinteticas (no datos reales), snapshot s175_audit/main == 752d348bc salvo CRLF (verificado con diff tras tr -d '\r').
import sys, importlib.util
from pathlib import Path
ruta = Path(sys.argv[1]); sys.path.insert(0, str(ruta.parent))
spec = importlib.util.spec_from_file_location("leer_retro", ruta); m = importlib.util.module_from_spec(spec); sys.modules["leer_retro"]=m; spec.loader.exec_module(m)
R = m.Reglas()
casos = {
 "A_vacio": [],
 "B_una_pasada_evaluable_sin_alertas": [{"_evaluable": True, "lab": "neg_limpio", "vol": "Lascar", "dt": "2026-02-03 05:00", "z": 30.0, "vrp_mirova": 0.0, "sensor": "MODIS_AQUA", "_t": {}}],
 "C_alertas_sin_cenit": [{"_evaluable": True, "lab": "protegida", "vol": "Lascar", "dt": "2026-02-03 05:00", "z": None, "vrp_mirova": 3.0, "sensor": "MODIS_AQUA", "_t": {}}],
}
for k, filas in casos.items():
    try:
        print(k, "->", m.controles_cenit(R, filas, "V"))
    except Exception as e:
        print(k, "EXC", type(e).__name__, str(e)[:200])
