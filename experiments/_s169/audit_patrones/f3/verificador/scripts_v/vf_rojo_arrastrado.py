"""Hallazgo propio: un record de K caído (via != True) commiteado el día D deja rojo el job de revisar_sombra en cada
corrida de los 7 días siguientes, aunque esas corridas estén sanas, porque `otros` se cuenta sobre la ventana de 8
días y no sobre lo escrito en la corrida (scripts/revisar_sombra.py l. 27-39).
P1: control: el mismo JSON sin el record de K -> verde todos los días. P2: si revisar no mirara la ventana, el rojo
no se arrastraría.
"""
import sys, json
from datetime import date, timedelta
sys.path.insert(0, sys.argv[1] + "/scripts")
import revisar_sombra as rs, ventana_sombra as vs
def r(dt, via=True): return {"datetime_utc": dt, "via_codigo_mirova": via}
base = [r("2026-11-%02d 06:12" % d) for d in range(3, 16)]   # una pasada sana por día
k = r("2026-11-05 06:40", "geo_distinta")
out = {}
for d in range(5, 16):
    hoy = date(2026, 11, d)
    ini, fin = vs.ventana(hoy)
    ok_con, _ = rs.revisar(base + [k], "", ini.isoformat(), fin.isoformat())
    ok_sin, _ = rs.revisar(base, "", ini.isoformat(), fin.isoformat())
    out[hoy.isoformat()] = {"ventana": [ini.isoformat(), fin.isoformat()], "verde_con_un_K_del_05": ok_con, "verde_control": ok_sin}
print(json.dumps(out, indent=1))
