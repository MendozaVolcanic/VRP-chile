# -*- coding: utf-8 -*-
"""S142 Frente A: ¿MOUNTS (Sentinel-2 SWIR, 20 m) ve calor en Nevados de Chillán cuando nosotros o MIROVA lo vemos?

POR QUÉ. El foco del cráter Nicanor es de centésimas de MW: a 375 m ocupa uno o dos píxeles y compite con la
nieve. Un sensor de 20 m en SWIR resuelve un foco sub-píxel para VIIRS (A77) y es de otro grupo (Valade 2019),
así que es un tercer testigo. Pero Sentinel-2 pasa de día (~14:30 UTC) y cada ~5 días: una detección MOUNTS
confirma el DÍA, nunca una pasada nocturna VIIRS concreta.

FUENTES (salida PUBLICADA, regla del workspace, nada del data/ de MOUNTS por disco):
  _dl_mounts/actividad_termica_so2.json  <- https://mendozavolcanic.github.io/MOUNTS-Chile/
  _dl_mounts/mounts_timeseries_357070.html <- http://www.mounts-project.com/timeseries/357070 (origen)
  _dl_mirova/registro_vrp_{consolidado,ocr}.csv <- MendozaVolcanic/Mirova-v1 (remoto)
  records de origin/main (git show)
INSTRUMENTO: la serie del JSON publicado se contrasta punto a punto con la del Plotly de la web de origen.
USO: python experiments/_s142_ndc/mounts_ndc.py
"""
import csv
import io
import json
import math
import re
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INICIO, FIN = "2026-06-01", "2026-09-16"
NIC = (-36.867210, -71.378241)      # cráter Nicanor (S124, ndc_s141.py)
FOCO_KM = 0.5
CELDA_MIROVA_KM = 0.38              # D15
SENS_375 = {"VIIRS_SNPP", "VIIRS_NOAA20", "VIIRS_NOAA21"}


def hav(a, b):
    la1, lo1, la2, lo2 = map(math.radians, (*a, *b))
    h = math.sin((la2 - la1) / 2) ** 2 + math.cos(la1) * math.cos(la2) * math.sin((lo2 - lo1) / 2) ** 2
    return 12742.0 * math.asin(math.sqrt(h))


def main():
    pub = json.loads((HERE / "_dl_mounts" / "actividad_termica_so2.json").read_text(encoding="utf-8"))
    sw = pub["volcanoes"]["nevados-de-chillan"]["series"]["swir"]
    serie = [p for p in sw["data"] if INICIO <= p["date"] < FIN]
    html = (HERE / "_dl_mounts" / "mounts_timeseries_357070.html").read_text(encoding="utf-8", errors="replace")
    g = json.loads(re.search(r"var graph = (\{.*?\});\s*Plotly", html, flags=re.S).group(1))
    tr = next(t for t in g["data"] if t.get("name") == "swir")
    web = {x: y for x, y in zip(tr["x"], tr["y"]) if INICIO <= x < FIN}
    discrep = [p["date"] for p in serie if web.get(p["date"]) != p["value"]] + [x for x in web if x not in {p["date"] for p in serie}]

    mir = []
    for nombre, src in (("registro_vrp_consolidado.csv", "CONS"), ("registro_vrp_ocr.csv", "OCR")):
        for r in csv.DictReader(open(HERE / "_dl_mirova" / nombre, encoding="utf-8")):
            if r["Volcan"] != "Nevados de Chillan" or not (INICIO <= r["Fecha_Satelite_UTC"] < FIN):
                continue
            if r["Tipo_Registro"] not in ("ALERTA_TERMICA", "ALERTA_TERMICA_OCR"):
                continue
            t = datetime.strptime(r["Fecha_Satelite_UTC"], "%Y-%m-%d %H:%M:%S")
            mir.append({"utc": r["Fecha_Satelite_UTC"][:16], "sensor": r["Sensor"], "vrp_mw": float(r["VRP_MW"]),
                        "dist_km": float(r["Distancia_km"]), "src": src, "nocturna": 3 <= t.hour < 10,
                        "crater": float(r["Distancia_km"]) <= CELDA_MIROVA_KM})
    # una alerta por pasada (consolidado y OCR duplican)
    unicas = {}
    for a in sorted(mir, key=lambda a: a["src"]):
        unicas.setdefault((a["utc"], a["sensor"]), a)
    mir = sorted(unicas.values(), key=lambda a: a["utc"])

    raw = subprocess.run(["git", "-C", str(ROOT), "show", "origin/main:data/mirova_equivalent/NevadosDeChillan.json"],
                         capture_output=True, check=True).stdout
    d = json.loads(raw)
    foco = []
    for r in d["records"]:
        if r["sensor"] not in SENS_375 or not (INICIO <= r["datetime_utc"] < FIN):
            continue
        h = int(r["datetime_utc"][11:13])
        if not (3 <= h < 10) or r.get("distance_class") != "summit" or not r.get("f5_core_vrp_mw"):
            continue
        if r.get("final_hotspot_lat") is None:
            continue
        dk = hav(NIC, (r["final_hotspot_lat"], r["final_hotspot_lon"]))
        if dk <= FOCO_KM:
            foco.append({"utc": r["datetime_utc"], "sensor": r["sensor"], "zen": r.get("sensor_zenith_deg"),
                         "f5_mw": r["f5_core_vrp_mw"], "d_nicanor_km": round(dk, 3)})

    por_fecha = []
    for p in serie:
        dia = p["date"][:10]
        prev = (datetime.strptime(dia, "%Y-%m-%d") - timedelta(days=1)).strftime("%Y-%m-%d")
        por_fecha.append({
            "s2_utc": p["date"], "s2pix": p["value"], "deteccion_mounts": p["detection"],
            "imagen": p.get("image_path"),
            "mirova_alertas_crater_noche_mismo_dia": [a for a in mir if a["utc"][:10] == dia and a["nocturna"] and a["crater"]],
            "mirova_alertas_otras_mismo_dia": [a for a in mir if a["utc"][:10] == dia and not (a["nocturna"] and a["crater"])],
            "nuestros_records_foco_noche_mismo_dia": [x for x in foco if x["utc"][:10] == dia],
            "nuestros_records_foco_noche_dia_previo": len([x for x in foco if x["utc"][:10] == prev]),
        })
    fechas_s2 = {p["date"][:10] for p in serie}
    alertas_crater = [a for a in mir if a["nocturna"] and a["crater"]]
    out = {
        "meta": {"generado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                 "mounts_json_generated_at": pub["generated_at"], "ventana": [INICIO, FIN],
                 "definicion_foco_nuestro": "record VIIRS 375 nocturno (03-10 UTC), distance_class summit, f5_core_vrp_mw > 0, final_hotspot a <= 0,5 km de Nicanor. NO es el predicado del dashboard.",
                 "unidad_mounts": sw["unit"], "n_puntos_ventana": len(serie),
                 "n_detecciones_ventana": sum(p["detection"] for p in serie),
                 "control_json_publicado_vs_web_origen": {"n_web": len(web), "discrepancias": discrep}},
        "detecciones_mounts": [p for p in por_fecha if p["deteccion_mounts"]],
        "alertas_crater_mirova_y_s2_mismo_dia": [
            {"alerta": a, "hay_pasada_s2_ese_dia": a["utc"][:10] in fechas_s2,
             "s2_ese_dia": [ {"utc": p["date"], "s2pix": p["value"], "det": p["detection"]} for p in serie if p["date"][:10] == a["utc"][:10]]}
            for a in alertas_crater],
        "por_fecha_s2": por_fecha,
        "caso_14_15_sep": {
            "s2": [p for p in por_fecha if p["s2_utc"][:10] in ("2026-09-14", "2026-09-15")],
            "hay_s2_el_15_sep": "2026-09-15" in fechas_s2,
            "nuestros_foco_14_15": [x for x in foco if x["utc"][:10] in ("2026-09-14", "2026-09-15")],
            "mirova_14_15": [a for a in mir if a["utc"][:10] in ("2026-09-14", "2026-09-15")]},
    }
    (HERE / "mounts_ndc.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(out["meta"], ensure_ascii=False))
    for p in por_fecha:
        print(p["s2_utc"], p["s2pix"], p["deteccion_mounts"], "MIR crater:", [(a["utc"], a["vrp_mw"]) for a in p["mirova_alertas_crater_noche_mismo_dia"]],
              "otras:", [(a["utc"], a["vrp_mw"], a["dist_km"]) for a in p["mirova_alertas_otras_mismo_dia"]],
              "nuestros:", [(x["utc"][11:], x["f5_mw"]) for x in p["nuestros_records_foco_noche_mismo_dia"]])
    print("ALERTAS CRATER vs S2:", json.dumps(out["alertas_crater_mirova_y_s2_mismo_dia"], ensure_ascii=False))
    print("14-15:", json.dumps(out["caso_14_15_sep"], ensure_ascii=False))


if __name__ == "__main__":
    main()
