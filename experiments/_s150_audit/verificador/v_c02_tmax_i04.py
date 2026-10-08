"""Verificador S150, hallazgo C-02.

Mide en el corpus operacional (data/mirova_equivalent/*.json, 11 Tier A + resto, todo el
historial guardado) cuan cerca del techo de la banda I4 (LUT max 361,77 K; el codigo borra
desde 361,27 K) ha llegado el pixel mas caliente de cada record VIIRS 375.

Preguntas del instrumento:
1. Si la saturacion ya estuviera borrando focos, ¿lo veria? Parcialmente: un pixel borrado
   NO aparece en t_max_i04_k (es NaN antes del maximo), asi que un record con el foco
   saturado mostraria el maximo de los vecinos. Esta medicion NO ve el borrado directo;
   solo dice cuanta distancia hay entre lo observado y el techo.
2. Si el instrumento estuviera muerto (campo ausente), ¿se veria distinto? Si: cuento
   records con el campo presente; si es 0, es SIN DATO.
Control positivo: el record de Chillan 2026-10-01 06:18 VIIRS_NOAA20 que el auditor cita
con 336,5 K tiene que aparecer.
"""
import io
import json
import sys
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
REPO = Path(__file__).resolve().parents[3]
D = REPO / "data" / "mirova_equivalent"

n_con = 0
top = []
for f in sorted(D.glob("*.json")):
    try:
        recs = json.loads(f.read_text(encoding="utf-8")).get("records", [])
    except Exception as e:  # noqa
        print("ERR", f.name, e)
        continue
    for r in recs:
        s = r.get("sensor", "")
        if not s.startswith("VIIRS") or s.endswith("_750"):
            continue
        t = r.get("t_max_i04_k")
        if t is None:
            continue
        n_con += 1
        top.append((t, f.stem, r.get("datetime_utc") or r.get("datetime"), s,
                    r.get("vrp_mw"), (r.get("primary_cluster") or {}).get("vrp_mw"),
                    r.get("f5_core_vrp_mw")))
top.sort(reverse=True)
print("records VIIRS375 con t_max_i04_k:", n_con)
print("Top 12 por t_max_i04_k (K, volcan, fecha, sensor, vrp_mw, pc.vrp_mw, f5_core):")
for row in top[:12]:
    print("  ", row)
print("records >= 355 K:", sum(1 for x in top if x[0] >= 355))
print("records >= 361.27 K:", sum(1 for x in top if x[0] >= 361.27))
ch = [x for x in top if x[1] == "NevadosDeChillan" and str(x[2]).startswith("2026-10-01")]
print("Chillan 2026-10-01 (control positivo):")
for x in sorted(ch, key=lambda z: str(z[2])):
    print("  ", x)
