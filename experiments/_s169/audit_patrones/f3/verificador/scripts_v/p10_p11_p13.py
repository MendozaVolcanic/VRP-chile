"""P3-10, P3-11, P3-13.
P3-10. P1: un directorio con un record de la vía (via_codigo_mirova True) y uno de K caído (via "sin_mxd03") en la
misma noche; si cargar_lado filtrara, devolvería 1. Control: sensor None (bucket None) se descarta -> se ve que el
instrumento sí filtra algunas cosas. Fecha ilegible ("2026-11-05 06:12:30") se cuenta aparte.
P3-11. ¿Con --ref apuntando a una carpeta con los NOMBRES DEL REPO (snapshot) entran el respaldo y el histórico?
Mido filas cargadas con y sin cada capa y si main() imprime algo sobre ellas.
P3-13. cargar_filas_referencia con CONS inexistente: ¿avisa o devuelve None en silencio?
"""
import sys, os, json, io, contextlib, shutil
arbol, base = sys.argv[1], sys.argv[2]
sys.path.insert(0, arbol); sys.path.insert(0, arbol + "/scripts")
os.environ["VRP_PROFILE"] = "mirova_equivalent"
import evaluador_comun as ev, banco_paridad as bp, referencia_mirova_unificada as rmu
from pathlib import Path
out = {}
work = os.path.join(base, "p10_work"); shutil.rmtree(work, ignore_errors=True); os.makedirs(work)
def rec(t, sensor, via):
    return {"sensor": sensor, "datetime_utc": t, "vrp_mw": 0.0, "primary_cluster": None, "distance_class": None,
            "triggered_test1": False, "anomaly_pixels": [], "via_codigo_mirova": via}
recs = [rec("2026-11-05 06:12", "MODIS_AQUA", True), rec("2026-11-05 06:40", "MODIS_AQUA", "sin_mxd03"),
        rec("2026-11-05 06:50", None, True), rec("2026-11-05 06:55:30", "MODIS_AQUA", True)]
for v in bp.VOLS:
    json.dump({"records": recs if v == "Lascar" else []}, open(os.path.join(work, v + ".json"), "w", encoding="utf-8"))
buf = io.StringIO()
with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
    cargados, faltan = ev.cargar_lado(work, ("2026-11-05", "2026-11-05"), ("MODIS",), bp._coords_por_volcan(), bp.inner_desde_html())
out["P3-10_records_en_json"] = len(recs)
out["P3-10_cargados"] = [(r["dt"].isoformat(), r["sensor"]) for r in cargados]
out["P3-10_salida_de_cargar_lado"] = buf.getvalue()[-300:]
# P3-11
snap = os.path.join(base, "ref_snap")
opc = lambda n: (Path(snap) / n) if (Path(snap) / n).exists() else None
out["P3-11_opc('respaldo_20260408.csv')_en_carpeta_con_nombres_del_repo"] = str(opc("respaldo_20260408.csv"))
out["P3-11_opc('consolidado_filas_perdidas.csv')"] = str(opc("consolidado_filas_perdidas.csv"))
out["P3-11_nombre_respaldo_en_repo"] = rmu.RESPALDO_20260408.name
out["P3-11_nombre_historico_en_repo"] = rmu.HISTORICO_RECUPERADAS.name
c, o = Path(snap) / "registro_vrp_consolidado.csv", Path(snap) / "registro_vrp_ocr.csv"
n_base = len(rmu.cargar_referencia_unificada(c, o, None, None))
n_resp = len(rmu.cargar_referencia_unificada(c, o, Path(snap) / rmu.RESPALDO_20260408.name, None))
n_hist = len(rmu.cargar_referencia_unificada(c, o, None, Path(snap) / "consolidado_filas_perdidas.csv"))
n_todo = len(rmu.cargar_referencia_unificada(c, o, Path(snap) / rmu.RESPALDO_20260408.name, Path(snap) / "consolidado_filas_perdidas.csv"))
out["P3-11_filas_sin_capas"] = n_base; out["P3-11_filas_mas_respaldo"] = n_resp
out["P3-11_filas_mas_historico"] = n_hist; out["P3-11_filas_con_ambas"] = n_todo
# filas del historico con fecha >= 2026-10-01 (las que una caida futura en la ventana de la sombra se llevaria igual)
hist = rmu.leer_pasadas(Path(snap) / "consolidado_filas_perdidas.csv", "CONS", "historico")
import collections
out["P3-11_historico_por_mes"] = dict(sorted(collections.Counter(f["fecha_utc"][:7] for f in hist).items()))
# P3-13
import auto_audit_weekly as aa
aa_cons = aa.CONS
aa.CONS = Path(work) / "no_existe.csv"
buf = io.StringIO()
with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
    r = aa.cargar_filas_referencia()
out["P3-13_retorno_con_CONS_inexistente"] = repr(r)
out["P3-13_lo_que_imprimio"] = buf.getvalue()
aa.CONS = aa_cons
print(json.dumps(out, ensure_ascii=True, indent=1))
