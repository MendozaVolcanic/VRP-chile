# E1: cuantas pasadas SE-minimas de VIIRS 375 de cada ventana del A/B caen FUERA del conjunto que cuenta el
# denominador de Muy Bajo (V2: antes de 2026-04-01 por decide_sensor; V1: alertas solo OCR, candidatas a
# "solo OCR Suomi NPP"). Usa la referencia CONGELADA de cada ventana, igual que evaluar_fk.archivos_ref.
import sys, collections
from pathlib import Path
from datetime import datetime, timezone
W = Path(sys.argv[1])
sys.path[:0] = [str(W), str(W / "scripts")]
import clase_mirova as cm
import banco_paridad as bp
from referencia_mirova_unificada import cargar_referencia_unificada
coords = bp._coords_por_volcan()
for v, desde, hasta, solo_tabla in (("v1", "2026-08-29", "2026-10-08", False), ("v2", "2026-03-01", "2026-06-12", True)):
    ref = W / "experiments/_s151_prereg_fk_11" / ("_congelado_" + v)
    ocr = ref / "registro_vrp_ocr.csv"
    if solo_tabla:
        vac = Path(sys.argv[2]) / ("ocr_vacio_%s.csv" % v)
        vac.write_text(ocr.read_text(encoding="utf-8").splitlines()[0] + "\n", encoding="utf-8")
        ocr = vac
    filas = cargar_referencia_unificada(ref / "registro_vrp_consolidado.csv", ocr,
                                        historico_path=ref / "consolidado_filas_perdidas.csv",
                                        respaldo_path=ref / "respaldo_20260408.csv")
    rm = cm.aplicar_regla_minimas(filas, "SE")
    por = collections.defaultdict(list)
    for f in filas:
        if f.get("tipo") in cm.TIPOS_ALERTA:
            por[cm.clave_pasada(f)].append(f)
    sel = []
    for k in rm.minimas:
        vol, b, t = k
        if not (desde <= t[:10] <= hasta):
            continue
        dt = datetime.strptime(por[k][0]["fecha_utc"][:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        lat, lon = coords[vol]
        if bp.es_pasada_diurna_descartada(b, lat, lon, dt):
            continue
        sel.append(k)
    antes_abril = [k for k in sel if k[2][:10] < "2026-04-01"]
    solo_ocr = [k for k in sel if all(f["source"] == "OCR" for f in por[k])]
    print(v, "minimas SE nocturnas VIIRS375 en la ventana:", len(sel), "| antes de 2026-04-01:", len(antes_abril),
          "| solo OCR:", len(solo_ocr))
    print("   por mes:", dict(collections.Counter(k[2][:7] for k in sel)))
