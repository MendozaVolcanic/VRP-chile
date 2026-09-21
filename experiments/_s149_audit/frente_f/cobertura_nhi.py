"""Frente F, S149. Que publica NHI-v1 (SWIR 20-30 m) para los 11 Tier A.

Lee SOLO la salida publicada (raw.githubusercontent, docs/nhi_data/<Volcan>/nhi_timeseries.json),
nunca el data/ de otro proyecto por ruta de disco (regla del workspace).

Instrumento:
1. Si NHI-v1 no cubriera un volcan, esto lo ve: HTTP distinto de 200 se reporta como SIN DATO.
2. Control positivo: Villarrica y Lascar deben tener escenas con pixeles calientes si el
   detector SWIR funciona (lago de lava / domo). Un cero ahi hablaria del instrumento.
Denominador: escenas listadas en la serie publicada. Ventana: la que trae la serie (se imprime).
"""
import io
import json
import sys
import urllib.parse
import urllib.request

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
BASE = "https://raw.githubusercontent.com/MendozaVolcanic/NHI-v1/main/docs/nhi_data/"
VOLS = ["Lascar", "Isluga", "Tupungatito", "Planchon-Peteroa", "Nevados de Chillan", "Copahue",
        "Llaima", "Villarrica", "Puyehue - Cordon Caulle", "Chaiten", "Lastarria"]

print(f"{'volcan':26s} {'escenas':>7s} {'desde':>10s} {'hasta':>10s} {'con_px_cal':>10s} {'alerta':>6s} {'max_px':>6s} sensores")
for v in VOLS:
    url = BASE + urllib.parse.quote(v) + "/nhi_timeseries.json"
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            j = json.loads(r.read().decode("utf-8"))
    except Exception as e:  # noqa
        print(f"{v:26s} SIN DATO ({type(e).__name__}: {str(e)[:50]})")
        continue
    fechas = sorted(x["fecha"] for x in j)
    cal = [x for x in j if (x.get("pixeles_calientes") or 0) > 0]
    al = [x for x in j if x.get("alerta")]
    sens = sorted({x.get("sensor", "?") for x in j})
    mx = max((x.get("pixeles_calientes") or 0) for x in j)
    print(f"{v:26s} {len(j):7d} {fechas[0]:>10s} {fechas[-1]:>10s} {len(cal):10d} {len(al):6d} {mx:6d} {','.join(sens)}")
