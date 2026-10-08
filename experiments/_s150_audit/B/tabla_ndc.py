# -*- coding: utf-8 -*-
"""S150 frente B. Tabla por pasada de Nevados de Chillan: que muestra cada vista del tablero
(index, diario, mosaico, evaluadas con su JS literal via vistas.js) y que publico MIROVA
(CONS y OCR, crudos del remoto de Mirova-v1, todas las filas, no solo alertas).

Dos preguntas del instrumento:
1. Si el tablero ocultara todas las pasadas de erupcion, esta tabla lo veria: columna ix_chart
   en 0 frente a alerta MIROVA en la misma pasada. Control positivo: el caso conocido
   2026-10-01 08:35 MODIS (far, cumulo a 0,9 km) debe salir oculto.
2. Si el instrumento estuviera muerto (node no evalua, o el JSON no tiene la ventana), el
   resultado se veria distinto: se imprime el conteo de records y de alertas por sensor y la
   ultima fecha del JSON; cero records = SIN DATO, no "nada oculto".

  python tabla_ndc.py  (lee datos/ de esta carpeta, descargados del remoto en esta sesion)
"""
import csv, json, subprocess, sys
from datetime import datetime, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
DATOS = AQUI / "datos"
DESDE = "2026-09-20"


def bucket_nuestro(s):
    s = s or ""
    if s.startswith("MODIS"):
        return "MODIS"
    if s.endswith("_750"):
        return "VIIRS750"
    if s.startswith("VIIRS"):
        return "VIIRS375"
    return None


def bucket_mirova(s):
    return {"MODIS": "MODIS", "VIIRS375": "VIIRS375", "VIIRS": "VIIRS750"}.get(s)


def leer_mirova():
    filas = []
    for f, fuente in (("consolidado.csv", "CONS"), ("ocr.csv", "OCR")):
        for r in csv.DictReader(open(DATOS / f, encoding="utf-8")):
            if "Chill" not in r["Volcan"] or r["Fecha_Satelite_UTC"] < DESDE:
                continue
            filas.append({"dt": datetime.strptime(r["Fecha_Satelite_UTC"][:19], "%Y-%m-%d %H:%M:%S"),
                          "b": bucket_mirova(r["Sensor"]), "vrp": float(r["VRP_MW"] or 0),
                          "dist": r["Distancia_km"], "tipo": r["Tipo_Registro"],
                          "clase": r["Clasificacion Mirova"], "fuente": fuente})
    return filas


TOL_MIN = 10  # misma pasada: MIROVA rotula con hh:mm:ss de la misma adquisicion (verificado en la salida)


def main():
    flag = "--flag-cumulo" in sys.argv
    d = json.load(open(DATOS / "NevadosDeChillan.json", encoding="utf-8"))
    recs = [r for r in d["records"] if r["datetime_utc"] >= DESDE]
    if flag:
        # Contrafactual del flag ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER: replica
        # pipeline/process_modis.py:300-320 (derivar_distance_class) sobre MODIS. Ignora el
        # guard A46 de store.py:480, que no puede volver a 'far' un pc <= inner.
        n = 0
        for r in recs:
            if not r["sensor"].startswith("MODIS") or r.get("final_hotspot_dist_km") is None:
                continue
            pcd = (r.get("primary_cluster") or {}).get("centroid_dist_km")
            if pcd is not None:
                nuevo = "summit" if pcd <= 5.0 else "far"
                n += nuevo != r.get("distance_class")
                r["distance_class"] = nuevo
        print("CONTRAFACTUAL flag cumulo: MODIS reetiquetados:", n)
    recs.sort(key=lambda r: r["datetime_utc"])
    print(f"records NdC desde {DESDE}: {len(recs)}; ultimo record del JSON: "
          f"{max(r['datetime_utc'] for r in d['records'])}; updated={d.get('updated')}")
    casos = AQUI / "_casos.json"
    casos.write_text(json.dumps(recs), encoding="utf-8")
    o = subprocess.run(["node", str(AQUI / "vistas.js"), str(RAIZ / "frontend"), str(casos),
                        str(DATOS / "mirova_NdC.json")], capture_output=True, text=True, timeout=600)
    if o.returncode != 0:
        raise SystemExit("node fallo: " + o.stderr[-2000:])
    vis = json.loads(o.stdout)
    assert len(vis) == len(recs)
    mir = leer_mirova()
    usados = set()
    filas = []
    for r, v in zip(recs, vis):
        b = bucket_nuestro(r["sensor"])
        dt = datetime.strptime(r["datetime_utc"], "%Y-%m-%d %H:%M")
        cand = [(abs((m["dt"] - dt).total_seconds()), i, m) for i, m in enumerate(mir)
                if m["b"] == b and abs((m["dt"] - dt).total_seconds()) <= TOL_MIN * 60]
        cand.sort(key=lambda x: (x[0], x[2]["fuente"] != "CONS"))
        mm = [c[2] for c in cand]
        for c in cand:
            usados.add(c[1])
        pc = r.get("primary_cluster") or {}
        filas.append({
            "dt": r["datetime_utc"], "sensor": r["sensor"], "b": b,
            "dc": r.get("distance_class"), "fh_src": r.get("final_hotspot_source"),
            "fh_dist": r.get("final_hotspot_dist_km"), "hs_dist": r.get("hotspot_dist_km"),
            "tmax_dist": r.get("diag_t_max_dist_km"),
            "pc_vrp": pc.get("vrp_mw"), "pc_dist": pc.get("centroid_dist_km"), "pc_n": pc.get("n_pixels"),
            "f5": r.get("f5_core_vrp_mw"), "vrp_mw": r.get("vrp_mw"), "t_max": r.get("t_max_k"),
            "t_bg": r.get("t_bg_k"), "disc": r.get("discarded_reason"), "sza": r.get("solar_zenith_deg"),
            "n_nti": r.get("diag_n_nti_path"), "n_bt": r.get("diag_n_bt_path"),
            **v,
            "mirova": [{"dt": m["dt"].strftime("%m-%d %H:%M"), "vrp": m["vrp"], "tipo": m["tipo"],
                        "clase": m["clase"], "fuente": m["fuente"], "dist": m["dist"]} for m in mm],
        })
    sin_par = [m for i, m in enumerate(mir) if i not in usados]
    (AQUI / ("tabla_ndc_flag.json" if flag else "tabla_ndc.json")).write_text(json.dumps({"filas": filas, "mirova_sin_record_nuestro": [
        {**m, "dt": m["dt"].strftime("%Y-%m-%d %H:%M")} for m in sin_par]}, ensure_ascii=False, indent=1),
        encoding="utf-8")

    def f(x, n=2):
        return "-" if x is None else (f"{x:.{n}f}" if isinstance(x, float) else str(x))
    print("\nPASADAS CON ALGO (pc_vrp>0, o MIROVA con alerta/FP en la pasada):")
    print("fecha UTC        sensor            dc     pc_vrp pc_d  f5    | idx_graf tarj  lvl      cens far   conf | diario mosa_sp mosa_t | MIROVA")
    for x in filas:
        alertas = [m for m in x["mirova"] if m["tipo"] != "RUTINA"]
        if not ((x["pc_vrp"] or 0) > 0 or alertas):
            continue
        ms = "; ".join(f"{m['fuente']} {m['dt']} {m['vrp']} {m['tipo'][:12]} {m['clase']} d={m['dist']}" for m in alertas) or \
             ("RUTINA" if x["mirova"] else "sin fila")
        print(f"{x['dt']} {x['sensor']:<17} {str(x['dc']):<6} {f(x['pc_vrp']):>6} {f(x['pc_dist'],1):>5} {f(x['f5']):>5} | "
              f"{f(x['ix_chart']):>7} {str(x['ix_card'])[0]:>4} {x['ix_level']:<8} {str(x['ix_cens'])[0]:>4} {f(x['ix_far']):>5} {str(x['ix_conf'])[0]:>4} | "
              f"{f(x['di_chart']):>6} {f(x['mo_spark']):>7} {str(x['mo_card'])[0]:>6} | {ms}")
    print("\nALERTAS / FP DE MIROVA SIN RECORD NUESTRO A +-TOL_MIN MIN (mismo sensor):")
    for m in sorted(sin_par, key=lambda m: m["dt"]):
        if m["tipo"] == "RUTINA":
            continue
        print(f"  {m['dt']:%Y-%m-%d %H:%M} {m['b']:<9} {m['fuente']} {m['vrp']} {m['tipo']} {m['clase']} d={m['dist']}")


if __name__ == "__main__":
    main()
