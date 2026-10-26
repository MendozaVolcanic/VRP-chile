"""V3, hallazgo 242 (y 241): ¿el vigilante por plataforma de la rama s159-cese-snpp (f995d7101, PR #892)
ve una plataforma callada? Camino: evaluar() sobre los records reales de SHA_MAIN (snapshot D:), quitando
los records de una plataforma desde un corte. Control: sin quitar nada debe dar ok. Pregunta 2: si el
vigilante estuviera muerto daria lo mismo en control y en escenario; se exige que difieran.
Uso: python -I v3_vigilante_892.py <rama892> <datos_mirova_equivalent>"""
import sys, importlib.util
from datetime import datetime, timezone
rama, datos = sys.argv[1], sys.argv[2]
spec = importlib.util.spec_from_file_location("vp", rama + "/scripts/vigilar_plataformas.py")
vp = importlib.util.module_from_spec(spec); spec.loader.exec_module(vp)
regs = vp.cargar_registros(datos)
ceses = vp.cargar_ceses(rama + "/scripts/ceses_esperados.json")
ultimo = max(t for _, t in regs)
print(f"records Tier A={len(regs)} ultimo={ultimo.isoformat()}")
corte = datetime(2026, 10, 19, 0, 0, tzinfo=timezone.utc)
ahora = datetime(2026, 10, 22, 2, 0, tzinfo=timezone.utc)
def quita(pref):
    return [(s, t) for s, t in regs if not (any(s == p for p in pref) and t >= corte)]
esc = {"control_sin_quitar": regs,
       "snpp_callado_desde_19oct": quita(["VIIRS_SNPP", "VIIRS_SNPP_750"]),
       "noaa21_callado_desde_19oct": quita(["VIIRS_NOAA21", "VIIRS_NOAA21_750"]),
       "modis_entero_callado_desde_19oct": quita(["MODIS_TERRA", "MODIS_AQUA"])}
for n, r in esc.items():
    v = vp.evaluar(r, ahora, ceses)
    print(n, "->", v.get("estado"), {k: v[k] for k in v if k in ("callan", "alarma", "cese_cumplido", "callados", "sin_datos")})
# Mismo escenario SNPP pero evaluado despues del cese anunciado: debe ser informativo, no alarma.
ceses2 = [{**c, "desde": corte} for c in ceses]
v = vp.evaluar(esc["snpp_callado_desde_19oct"], ahora, ceses2)
print("snpp_callado_con_cese_cumplido ->", v.get("estado"), sorted(v.keys()))
