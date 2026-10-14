# -*- coding: utf-8 -*-
"""F3 R5. El snapshot del repo tiene el OCR al dia (sync horario) y el consolidado semanal (auto-audit).
Cuantas alertas OCR del tramo final quedan 'solo OCR' contra el snapshot y dejan de estarlo contra
latest_consolidado.csv (copia horaria del remoto)?
P1: si la asimetria no importara, ambas cuentas coincidirian. P2: control: antes del corte del snapshot
las dos cuentas deben ser iguales (mismo consolidado)."""
import sys, collections
from pathlib import Path
RAIZ = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(RAIZ / "scripts")); sys.path.insert(0, str(RAIZ))
from referencia_mirova_unificada import leer_pasadas, SNAP_CONS, SNAP_OCR
snap = leer_pasadas(SNAP_CONS, "CONS", "snap"); viva = leer_pasadas(RAIZ / "latest_consolidado.csv", "CONS", "viva")
ocr = leer_pasadas(SNAP_OCR, "OCR", "snap")
corte = max(f["fecha_utc"] for f in snap)[:16]
print("ultima pasada del consolidado del snapshot:", corte, "| de latest_consolidado:", max(f["fecha_utc"] for f in viva)[:16])
def k(f): return (f["volcano"], f["sensor_bucket"], f["fecha_utc"][:16])
ks, kv = {k(f) for f in snap}, {k(f) for f in viva}
for tramo, sel in (("antes del corte", lambda f: f["fecha_utc"][:16] <= corte), ("despues del corte", lambda f: f["fecha_utc"][:16] > corte)):
    al = [f for f in ocr if f["tipo"].startswith("ALERTA") and sel(f)]
    print("%-18s alertas OCR %3d | sin fila en snapshot CONS %3d | sin fila en latest_consolidado %3d" % (
        tramo, len(al), sum(1 for f in al if k(f) not in ks), sum(1 for f in al if k(f) not in kv)))
    print("   volcanes:", dict(collections.Counter(f["volcano"] for f in al if k(f) not in ks and k(f) in kv)))
rut_falt = [f for f in viva if f["fecha_utc"][:16] > corte and f["tipo"] == "RUTINA"]
print("filas RUTINA de latest_consolidado posteriores al corte (negativos que el snapshot no ve):", len(rut_falt))
