"""V0-105: la fila OCR de Lastarria 2026-04-18 04:42 VIIRS375 (1,29 MW) cuenta como protegida?
P1 (si lo medido estuviera roto, lo veria?): si la regla D-9/lectura A la excluyera, es_protegida daria False; se
imprime el estado real de la pasada.
P2 (instrumento muerto?): el control positivo cuenta cuantas pasadas protegidas hay en total (si diera 0 el
instrumento estaria muerto).
Ventana: referencia de la base (copias de insumos con sha256 igual al de la vara). Denominador: 1 pasada + control."""
import sys
from pathlib import Path
M = Path(r"C:\Users\nmend\vrp-temporales\s175_audit\main")
INS = Path(r"C:\Users\nmend\vrp-temporales\s175_audit\insumos")
sys.path.insert(0, str(M / "scripts"))
sys.path.insert(0, str(M))
import clase_mirova as cm
import banco_paridad as bp

SNAP_CONS = INS / "snapshot_consolidado_base.csv"
SNAP_OCR = INS / "snapshot_ocr_base.csv"
T = Path(r"C:\Users\nmend\vrp-temporales\s175_audit\v0")  # copias de la base: git show 752d348bc:data/mirova_reference/...
filas = bp.cargar_referencia_unificada(SNAP_CONS, SNAP_OCR, respaldo_path=T / "respaldo.csv",
                                       historico_path=T / "consolidado_filas_perdidas.csv")
print("n filas", len(filas))


def es_lastarria_0418(f):
    return f["volcano"].startswith("Lastarria") and f["fecha_utc"].startswith("2026-04-18 04:4")


for f in filas:
    if es_lastarria_0418(f):
        print({k: f.get(k) for k in ("volcano", "sensor_bucket", "fecha_utc", "tipo", "vrp_mw", "dist_km", "source")})
pas = cm.resumir_pasadas(filas, canal="union")
for p in pas:
    if p.volcano.startswith("Lastarria") and str(p.instante).startswith("2026-04-18 04:4"):
        print("PASADA", p.sensor_bucket, p.instante, p.estado, p.vrp_mw, p.dist_km, p.fuente, "solo_ocr", p.solo_ocr,
              "protegida A:", cm.es_protegida(p, "A"))
        print("  de_crater(radio 3):", cm.protegida_de_crater(p, 3.0))
ctl = [p for p in pas if cm.es_protegida(p, "A")]
print("CONTROL positivo: pasadas protegidas (lectura A, union) totales", len(ctl), "de", len(pas))
tabla = cm.resumir_pasadas(filas, canal="tabla")
print("CANAL TABLA Lastarria 04:4x:", [(p.sensor_bucket, p.estado, p.vrp_mw) for p in tabla
                                      if p.volcano.startswith("Lastarria") and str(p.instante).startswith("2026-04-18 04:4")])
# vecindad: otras filas OCR VIIRS375 de Lastarria en abril con dist_km 0.0 y alerta
n = [f for f in filas if f["volcano"].startswith("Lastarria") and f["source"] != "CONS" and f["tipo"] == "ALERTA_TERMICA_OCR"
     and f["fecha_utc"].startswith("2026-04")]
print("OCR alerta Lastarria abril (todas):", [(f["fecha_utc"], f["vrp_mw"], f["dist_km"]) for f in n])
