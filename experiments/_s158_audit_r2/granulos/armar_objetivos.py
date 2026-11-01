"""Arma la lista de pasadas para la prueba con gránulos chilenos (sólo lectura, sin red).

Para cada pasada elegida: la fila de la referencia NRT de MIROVA (latest_consolidado.csv, Sensor == "VIIRS" es
VIIRS 750), nuestro record VIIRS 750 de la misma hora (granule, magnitud del cúmulo, píxeles) y la grilla UTM de
MIROVA medida en los TIF de 375 m (experiments/_s158_d17_diseno/grilla_tif_salida.txt). Elección: los cuatro casos
mínimos del brief, seis alertas más de volcanes distintos y dos pasadas RUTINA como control negativo.
Ventanas de la referencia (A119): todas desde marzo de 2026, VIIRS por pasada desde abril salvo el caso de Tupungatito
del 2026-03-01, que es un caso nuestro (0 MW), no una alerta de MIROVA.
"""
import json, re, sys
from pathlib import Path
import pandas as pd

R = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(R / "scripts"))
import calidad_referencia_mirova as Q  # noqa: E402
Q.avisar("2026-03-01", "2026-10-18")

ARCH = {"Lascar": "Lascar", "Puyehue-Cordon Caulle": "PuyehueCordonCaulle", "Nevados de Chillan": "NevadosDeChillan",
        "Isluga": "Isluga", "Villarrica": "Villarrica", "Tupungatito": "Tupungatito", "Chaiten": "Chaiten",
        "PlanchonPeteroa": "PlanchonPeteroa", "Llaima": "Llaima", "Copahue": "Copahue"}
TIF = {"Lascar": "Lascar", "PuyehueCordonCaulle": "PuyehueCordonCaulle", "NevadosDeChillan": "ChillanNevadosde",
       "Isluga": "Isluga", "Villarrica": "Villarrica", "Tupungatito": "Tupungatito", "Chaiten": "Chaiten",
       "PlanchonPeteroa": "PlanchonPeteroa", "Llaima": "Llaima", "Copahue": "Copahue"}
PASADAS = [  # (volcán en la referencia, hora MIROVA UTC, motivo)
    ("Tupungatito", "2026-03-01 05:36", "caso brief: nuestro V750 en 0 MW"),
    ("Lascar", "2026-10-08 05:42", "caso brief"),
    ("Puyehue-Cordon Caulle", "2026-10-10 05:54", "caso brief"),
    ("Nevados de Chillan", "2026-10-18 06:48", "caso brief"),
    ("Nevados de Chillan", "2026-10-10 05:54", "alerta Moderado"),
    ("Nevados de Chillan", "2026-10-18 05:42", "alerta Moderado"),
    ("Isluga", "2026-10-12 05:48", "alerta débil"),
    ("Villarrica", "2026-09-19 05:48", "alerta débil, lago de lava"),
    ("Lascar", "2026-09-26 05:48", "alerta"),
    ("Puyehue-Cordon Caulle", "2026-10-16 05:42", "alerta lejos del centro"),
    ("Tupungatito", "2026-08-21 05:48", "alerta lejos del centro"),
    ("Chaiten", "2026-10-06 05:30", "alerta débil"),
    ("Villarrica", "2026-10-18 06:48", "CONTROL NEGATIVO: RUTINA"),
    ("Llaima", "2026-10-10 05:54", "CONTROL NEGATIVO: RUTINA"),
]

ref = pd.read_csv(R / "latest_consolidado.csv")
ref = ref[ref.Sensor == "VIIRS"]
grilla = {}
for ln in (R / "experiments/_s158_d17_diseno/grilla_tif_salida.txt").read_text(encoding="utf-8").splitlines():
    m = re.match(r"(\w+)/\S+: EPSG (\d+), 134x134, celda 375.0 m, origen UL \(([-\d.]+), ([-\d.]+)\), centro \(([-\d.]+), ([-\d.]+)\)", ln)
    if m:
        grilla[m.group(1)] = {"epsg": int(m.group(2)), "ul_x": float(m.group(3)), "ul_y": float(m.group(4)),
                              "centro_lat": float(m.group(5)), "centro_lon": float(m.group(6))}
out = []
for vol, hora, motivo in PASADAS:
    a = ARCH[vol]
    fila = ref[(ref.Volcan == vol) & (ref.Fecha_Satelite_UTC.str.startswith(hora))]
    recs = json.loads((R / f"data/mirova_equivalent/{a}.json").read_text(encoding="utf-8"))["records"]
    mios = [r for r in recs if r.get("datetime_utc") == hora and str(r.get("sensor", "")).endswith("_750")]
    out.append({
        "volcan": a, "hora_utc": hora, "motivo": motivo, "grilla": grilla.get(TIF[a]),
        "mirova": fila[["Fecha_Satelite_UTC", "VRP_MW", "Distancia_km", "Tipo_Registro"]].to_dict("records"),
        "nuestros": [{"granule": r["granule"], "sensor": r["sensor"], "vrp_mw": r["vrp_mw"],
                      "pc_vrp_mw": (r.get("primary_cluster") or {}).get("vrp_mw"),
                      "n_px": r["n_anomalous_pixels"], "clase": r["distance_class"],
                      "cenit": r.get("sensor_zenith_deg")} for r in mios],
    })
for o in out:
    print(o["volcan"], o["hora_utc"], "| MIROVA", [(m["VRP_MW"], m["Distancia_km"], m["Tipo_Registro"]) for m in o["mirova"]],
          "| nuestros", [(n["granule"][:23], n["pc_vrp_mw"], n["n_px"], n["clase"]) for n in o["nuestros"]],
          "| grilla", "OK" if o["grilla"] else "FALTA")
(Path(__file__).parent / "objetivos.json").write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
