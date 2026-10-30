"""P3-02 y P3-03: revisar_sombra.revisar sobre escenarios sintéticos con el MISMO estado del JSON que vería el job.
El job corre revisar DESPUÉS del commit (paso 'Revisar...' del workflow, l. 147-151), sobre el JSON del checkout, que
trae los records commiteados por corridas anteriores. Ventana del día D>=2: [max(2026-11-03, D-7), D].
P1: control positivo: día 1 (JSON vacío) y log vacío -> debe FALLAR. Si no fallara, el instrumento no ve nada.
P2: escenario 'corrida vacía el día 2': el JSON trae sólo los records del día 1 (nada nuevo) y el log no tiene
ERROR processing. Si revisar da OK, la corrida vacía no se ve.
P3-03: el día trae sólo VIIRS 375 de la vía y ningún MODIS ni V750: ¿revisar falla?
"""
import sys, json
sys.path.insert(0, sys.argv[1] + "/scripts")
import revisar_sombra as rs
def r(dt, sensor, via=True):
    return {"datetime_utc": dt, "sensor": sensor, "via_codigo_mirova": via}
dia1 = [r("2026-11-03 06:12", "VIIRS_NOAA20"), r("2026-11-03 06:12", "VIIRS_NOAA20_750"), r("2026-11-03 06:40", "MODIS_AQUA")]
out = {}
out["control_dia1_json_vacio"] = rs.revisar([], "", "2026-11-03", "2026-11-03")
out["dia1_normal"] = rs.revisar(dia1, "", "2026-11-03", "2026-11-03")
out["dia2_corrida_vacia_sin_errores"] = rs.revisar(dia1, "", "2026-11-03", "2026-11-04")
out["dia9_corrida_vacia_ventana_8d"] = rs.revisar(dia1, "Cobertura NO COMPLETA: 30 búsquedas fallidas", "2026-11-03", "2026-11-11")
out["dia12_corrida_vacia_fuera_de_ventana"] = rs.revisar(dia1, "", "2026-11-04", "2026-11-12")
solo375 = [r("2026-11-05 06:12", "VIIRS_NOAA20"), r("2026-11-05 06:14", "VIIRS_NOAA21")]
out["P3-03_solo_viirs375_sin_modis_ni_v750"] = rs.revisar(solo375, "", "2026-11-05", "2026-11-05")
out["control_errores_en_log"] = rs.revisar(dia1, "  ERROR processing X.hdf: boom", "2026-11-03", "2026-11-04")
out["control_record_K_en_ventana"] = rs.revisar(dia1 + [r("2026-11-04 06:00", "MODIS_TERRA", "sin_mxd03")], "", "2026-11-03", "2026-11-04")
print(json.dumps(out, ensure_ascii=False, indent=1))
