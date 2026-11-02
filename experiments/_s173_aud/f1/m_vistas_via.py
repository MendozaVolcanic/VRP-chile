# -*- coding: utf-8 -*-
"""Las cuatro vistas del tablero sobre records MODIS de la via, con node, en la punta de B y en A (= codigo tras el
revert de B, con los records de la via que el revert no borra).

No hay records reales de la via en ningun lado (git grep y rg sobre D:/vrp-trabajo: 0 records con
final_hotspot_source = "codigo_mirova"; ver INFORME). Se producen con el procesador REAL de la punta de B
(process_modis.calculate_vrp con la via encendida) sobre el granulo sintetico de Lascar de
tests/test_mirova_modis_codigo_s164.py, y se pasan por store.append_record real (escribe en una carpeta de esta
auditoria, no en data/).

Preguntas del instrumento:
1. Si una vista tratara mal un record de la via (no lo publica, lo publica lejos, marcador fuera del cumulo), ¿se
   veria? Si: se comparan, por record, publica/magnitud/marcador contra el cumulo que la via escribio.
2. Si el extractor o node estuvieran muertos, ¿se veria distinto? Si: una funcion no encontrada levanta excepcion y el
   script cae; ademas hay control positivo (el mismo record con final_hotspot_source = "ctx_cluster", que todas las
   versiones reconocen) y control negativo (record de la via sin deteccion: no se publica en ninguna vista).
Uso: python m_vistas_via.py <worktree_B> <worktree_A> <salida.json>
"""
import json
import os
import re
import subprocess
import sys
from pathlib import Path

WB, WA, OUT = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve()
# (S173 F1: la primera corrida tenia OUT relativo y, tras el chdir, lo escribio dentro del worktree compartido; se movio
# a esta carpeta al instante. Ahora se resuelve antes del chdir.)
HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(WB), str(WB / "tests")]
os.environ["VRP_PROFILE"] = "mirova_equivalent"
os.environ["PYTHONDONTWRITEBYTECODE"] = "1"
sys.dont_write_bytecode = True
os.chdir(WB)
from unittest.mock import patch  # noqa: E402
import pipeline.process_modis as PM  # noqa: E402
import pipeline.store as ST  # noqa: E402
from pipeline import mirova_v750_codigo as MV  # noqa: E402
import test_mirova_modis_codigo_s164 as T  # noqa: E402

assert PM.ENABLE_MODIS_CODIGO_MIROVA is True, "en B produccion tiene que tener la via encendida"
TMP = HERE / "tmp_store"
TMP.mkdir(exist_ok=True)


def producir(nombre, caliente_crater=True, lejos_km=None, t_lejos=290.0):
    vl, mir, tir, lat, lon, ang = T._granulo_lascar()
    n = mir.shape[0]
    Tm = MV.radiancia_a_temperatura(mir, 3.959)
    if not caliente_crater:
        Tm[n // 2, n // 2] = 265.0
    if lejos_km is not None:
        Tm[n // 2 - lejos_km, n // 2] = t_lejos
    mir2 = MV.temperatura_a_radiancia(Tm, 3.959)
    with patch.object(MV, "leer_radiancia_modis", lambda p: {"MIR": mir2, "TIR": tir}), \
         patch.object(MV, "leer_geo_mxd03", lambda p: (lat, lon, ang)):
        r = PM.calculate_vrp(Path("MYD021KM.A2026306.0735.061.hdf"), Path("MYD03.A2026306.0735.061.hdf"),
                             vl["lat"], vl["lon"], vent_lat=vl["lat"], vent_lon=vl["lon"], inner_radius_km=5.0)
    assert r is not None and r["via_codigo_mirova"] is True, r
    d = TMP / nombre
    d.mkdir(exist_ok=True)
    with patch.object(ST, "DATA_DIR", d):
        ST.append_record("Lascar", dict(r), volcano_lat=vl["lat"], volcano_lon=vl["lon"], overwrite=True,
                         max_hotspot_dist_km=25.0, enable_pixel_level_distance_filter=True,
                         inner_radius_km=5.0)
    js = json.loads((d / "Lascar.json").read_text(encoding="utf-8"))
    return js["records"][-1], vl


casos = {}
casos["V1_crater"], vl = producir("V1")
casos["V2_crater_y_foco_15km_N"], _ = producir("V2", lejos_km=15)
casos["V3_solo_foco_15km_N"], _ = producir("V3", caliente_crater=False, lejos_km=15, t_lejos=300.0)
casos["V4_sin_deteccion"], _ = producir("V4", caliente_crater=False)
casos["CTRL_V2_como_ctx_cluster"] = dict(casos["V2_crater_y_foco_15km_N"], final_hotspot_source="ctx_cluster")


def extraer(src, nombre):
    m = re.search(r"(?<![A-Za-z0-9_.])function\s+" + re.escape(nombre) + r"\s*\(", src)
    if not m:
        raise RuntimeError("no encontre function " + nombre)
    i = src.index("{", m.end())
    prof = 0
    for j in range(i, len(src)):
        if src[j] == "{":
            prof += 1
        elif src[j] == "}":
            prof -= 1
            if prof == 0:
                return src[m.start():j + 1]
    raise RuntimeError("sin cierre " + nombre)


def const(src, nombre):
    m = re.search(r"^const\s+" + re.escape(nombre) + r"\s*=.*?;\s*$", src, re.M | re.S)
    if not m:
        raise RuntimeError("no encontre const " + nombre)
    return m.group(0)


PRE = "let USE_F5_CORE = true; let includeFarDistance = false;\n"
VISTAS = {
    "index_B": (WB / "frontend/index.html",
                ["_havKm", "f5CoreMagnitude", "mirovaEqVrp", "mirovaEqVrpCore", "mirovaEqVrpDisplay",
                 "isCirrusArtifact", "isDiffuseFieldArtifact", "isThermalArtifact", "isValidDetection",
                 "isSummitDetection", "esAnclaHonesta", "pixelesDelMarcador"],
                ["F5_R_CORE_KM", "F5_BT_EXT_K"]),
    "index_A_tras_revert": (WA / "frontend/index.html",
                            ["_havKm", "f5CoreMagnitude", "mirovaEqVrp", "mirovaEqVrpCore", "mirovaEqVrpDisplay",
                             "isCirrusArtifact", "isDiffuseFieldArtifact", "isThermalArtifact", "isValidDetection",
                             "isSummitDetection", "pixelesDelMarcador"],
                            ["F5_R_CORE_KM", "F5_BT_EXT_K"]),
    "diario_B": (WB / "frontend/diario.html",
                 ["_havKm", "f5CoreMagnitude", "mirovaEqVrp", "mirovaEqVrpCore", "isCirrusArtifact",
                  "isDiffuseFieldArtifact", "isThermalArtifact", "isValidDetection", "eqVrpDisplay"],
                 ["INNER_RADIUS_KM"]),
    "mosaico_B": (WB / "frontend/mosaico.html",
                  ["_havKm", "f5CoreMagnitude", "mirovaEqVrp", "mirovaEqVrpCore", "isCirrusArtifact",
                   "isDiffuseFieldArtifact", "isThermalArtifact", "isValidDetection", "isSummitDetection",
                   "eqVrpDisplay"], []),
    "comparacion_B": (WB / "frontend/comparacion.html", ["havKm", "bearingDeg", "sensorBucket",
                                                          "ourSummitDetections"], []),
}
CALLS = {
    "index_B": "({valid: isValidDetection(r), summit: isSummitDetection(r), eq: mirovaEqVrp(r,5,false),"
               " disp: mirovaEqVrpDisplay(r,5,false), artef: isThermalArtifact(r,5),"
               " marcador: (pixelesDelMarcador(r,{vent_lat:VL,vent_lon:VO})[0]||null)})",
    "diario_B": "({valid: isValidDetection(r), eq: mirovaEqVrp(r,'Lascar'), disp: eqVrpDisplay(r,'Lascar'),"
                " artef: isThermalArtifact(r,'Lascar')})",
    "mosaico_B": "({valid: isValidDetection(r), summit: isSummitDetection(r), eq: mirovaEqVrp(r,5,false),"
                 " disp: eqVrpDisplay(r,5), artef: isThermalArtifact(r,5)})",
    "comparacion_B": "({det: ourSummitDetections({records:[r]}, {lat:VL,lon:VO,vent_lat:VL,vent_lon:VO})})",
}
CALLS["index_A_tras_revert"] = CALLS["index_B"]

res = {"casos": {k: {c: v.get(c) for c in ("vrp_mw", "distance_class", "final_hotspot_source",
                                            "final_hotspot_lat", "final_hotspot_lon", "final_hotspot_dist_km",
                                            "hotspot_dist_km", "n_anomalous_pixels", "via_codigo_mirova",
                                            "t_max_k", "f5_core_vrp_mw", "discarded_reason")}
                     | {"pc": v.get("primary_cluster"), "regimen": v.get("regimen"),
                        "anomaly_pixels0": (v.get("anomaly_pixels") or [None])[0]}
                     for k, v in casos.items()}, "vistas": {}}
for vista, (ruta, fns, consts) in VISTAS.items():
    src = ruta.read_text(encoding="utf-8")
    pre = PRE
    if vista == "mosaico_B":
        pre += "const F5_R_CORE_KM = 0.75; const F5_BT_EXT_K = 295.0;\n"
    if vista == "diario_B":
        pre += "const F5_R_CORE_KM = 0.75; const F5_BT_EXT_K = 295.0;\n"
    codigo = pre + "\n".join(const(src, c) for c in consts) + "\n" + "\n".join(extraer(src, f) for f in fns)
    codigo += (f"\nconst VL={vl['lat']}, VO={vl['lon']};\nconst C=JSON.parse(require('fs').readFileSync(0,'utf8'));"
               f"\nconst o={{}}; for (const k in C) {{ const r=C[k]; o[k]={CALLS[vista]}; }}"
               "\nconsole.log(JSON.stringify(o));")
    p = subprocess.run(["node", "-e", codigo], input=json.dumps(casos), capture_output=True, text=True,
                       encoding="utf-8")
    if p.returncode != 0:
        res["vistas"][vista] = {"ERROR": p.stderr[-800:]}
    else:
        res["vistas"][vista] = json.loads(p.stdout)
OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
# resumen legible
for vista, o in res["vistas"].items():
    print("==", vista)
    if "ERROR" in o:
        print("  ERROR", o["ERROR"][:400])
        continue
    for k, v in o.items():
        if "marcador" in v and v["marcador"]:
            m = v["marcador"]
            v = dict(v, marcador={"dist_km": m.get("dist_km"), "lat": m.get("lat")})
        print(" ", k, json.dumps(v, ensure_ascii=False)[:300])
for k, c in res["casos"].items():
    print("caso", k, "vrp", c["vrp_mw"], "dc", c["distance_class"], "src", c["final_hotspot_source"],
          "final_dist", c["final_hotspot_dist_km"], "pc_dist", (c["pc"] or {}).get("centroid_dist_km"),
          "ap0_dist", (c["anomaly_pixels0"] or {}).get("dist_km"), "sha", bool((c["regimen"] or {}).get("codigo_sha")))
