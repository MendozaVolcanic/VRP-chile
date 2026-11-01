"""Sonda de datos: cobertura de sha/perfil en producción y sombra, formato de fecha_utc de la referencia.
No importa vigilancia_sombra. Uso: python sonda_datos.py <raiz> <ref>"""
import json
import os
import sys
from collections import Counter

raiz, ref = sys.argv[1:3]
sys.path.insert(0, raiz)
sys.path.insert(0, os.path.join(raiz, "scripts"))
os.chdir(raiz)

ADOP = "2026-10-18T09:57:30"
FRONT = "2026-09-18"

for sub in ("mirova_equivalent", "experimental_v2"):
    c = Counter()
    ejemplos = []
    for fn in sorted(os.listdir(os.path.join(raiz, "data", sub))):
        if not fn.endswith(".json"):
            continue
        d = json.load(open(os.path.join(raiz, "data", sub, fn), encoding="utf-8"))
        for r in d.get("records", []):
            dt = (r.get("datetime_utc") or r.get("datetime") or "")[:19]
            if dt < FRONT:
                continue
            reg = r.get("regimen") or {}
            tramo = "post_adop" if dt >= ADOP else "pre_adop"
            c[(tramo, "sha" if reg.get("codigo_sha") else "sin_sha", reg.get("perfil"))] += 1
            if tramo == "post_adop" and not reg.get("codigo_sha") and len(ejemplos) < 3:
                ejemplos.append((fn, dt, r.get("sensor"), list(reg.keys())))
    print(sub)
    for k, v in sorted(c.items(), key=lambda kv: str(kv[0])):
        print("  ", k, v)
    print("   ejemplos post sin sha:", ejemplos)

# Campo de fecha en records
d = json.load(open(os.path.join(raiz, "data", "mirova_equivalent", "Villarrica.json"), encoding="utf-8"))
print("claves record:", sorted(k for k in d["records"][-1].keys() if "date" in k or "time" in k or k == "regimen"))
print("regimen ultimo:", d["records"][-1].get("regimen"))

from referencia_mirova_unificada import cargar_referencia_unificada  # noqa: E402
filas = cargar_referencia_unificada(os.path.join(ref, "registro_vrp_consolidado.csv"),
                                    os.path.join(ref, "registro_vrp_ocr.csv"))
print("fecha_utc ejemplos:", Counter(len(f["fecha_utc"]) for f in filas), filas[0]["fecha_utc"], filas[-1]["fecha_utc"])
print("con T:", sum("T" in f["fecha_utc"] for f in filas))
