# Medicion en seco: ¿el OCR de Mirova-v1 perdio filas como el consolidado? No escribe nada en el repo.
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, sys.argv[1])
from scripts import referencia_mirova_unificada as R  # noqa: E402

NOMBRE = "registro_vrp_ocr.csv"
versiones = R.versiones_diarias(NOMBRE, "2025-12-01", "2026-10-14")
print("versiones diarias:", len(versiones), "desde", versiones[0]["dia"] if versiones else None)


def clave(r):
    vol = R.normalize_volcano_name(r.get("Volcan"))
    f = (r.get("Fecha_Satelite_UTC") or "").strip()
    if vol is None or len(f) < 16:
        return None
    return (vol, R.normalize_sensor(r.get("Sensor")), f[:16])


ultima, nueva, aporte = {}, set(), Counter()
with ThreadPoolExecutor(6) as ex:
    for v, (cab, filas) in zip(versiones, ex.map(lambda v: R._bajar_version(NOMBRE, v["sha"]), versiones)):
        ks = set()
        for r in filas:
            k = clave(r)
            if k:
                ks.add(k)
                ultima[k] = (r, v["dia"])
        nueva = ks
perdidas = {k: ultima[k] for k in ultima if k not in nueva}
print("claves en la union:", len(ultima), "en la version mas nueva:", len(nueva), "perdidas:", len(perdidas))
print("perdidas por tipo:", dict(Counter((r.get("Tipo_Registro") or "").strip() for r, _ in perdidas.values())))
print("ultimo dia con las filas perdidas:", dict(Counter(d for _, d in perdidas.values()).most_common(10)))
