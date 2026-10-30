"""P3-01: ¿el evaluador común da COBERTURA OK con referencia de MIROVA vieja, vacía o con BOM?
P1 (si lo medido estuviera roto, lo vería): corro main() de evaluador_comun de punta a punta sobre lados sintéticos
con un hueco real (el brazo no tiene una pasada que el control sí); con referencia que lista esa pasada como alerta
protegida el veredicto DEBE ser INVALIDO (control positivo). Luego la misma corrida con referencia vieja (snapshot
cc3887290, que termina antes de la ventana), vacía (sólo encabezado) y con BOM.
P2 (instrumento muerto): si main() no corriera o node fallara, no habría exit 0/2 ni líneas COBERTURA; registro ambos.
Sensor VIIRS750 (en el consolidado "VIIRS" es 750, A48). Ventana sintética 2026-11-05..2026-11-07 (posterior a la referencia congelada).
"""
import sys, os, json, csv, io, shutil, contextlib, collections
arbol, base = sys.argv[1], sys.argv[2]
sys.path.insert(0, arbol); sys.path.insert(0, arbol + "/scripts")
os.environ["VRP_PROFILE"] = "mirova_equivalent"
import evaluador_comun as ev
import banco_paridad as bp
import referencia_mirova_unificada as rmu
snap = os.path.join(base, "ref_snap")
work = os.path.join(base, "p01_work"); shutil.rmtree(work, ignore_errors=True); os.makedirs(work)
out = {}
# 0) fecha máxima de la referencia congelada
mx = {}
for n in ("registro_vrp_consolidado.csv", "registro_vrp_ocr.csv"):
    with open(os.path.join(snap, n), encoding="utf-8") as fh:
        mx[n] = max((r.get("Fecha_Satelite_UTC") or "")[:19] for r in csv.DictReader(fh))
out["max_fecha_ref_cc3887290"] = mx
# 1) BOM: leer_pasadas con y sin BOM (cabecera empieza por 'timestamp')
src = os.path.join(snap, "registro_vrp_consolidado.csv")
bom = os.path.join(work, "cons_bom.csv")
with open(src, "rb") as a, open(bom, "wb") as b:
    b.write(b"\xef\xbb\xbf" + a.read())
n_sin = len(rmu.leer_pasadas(rmu.Path(src), "CONS", "x")); n_con = len(rmu.leer_pasadas(rmu.Path(bom), "CONS", "x"))
out["bom_filas_sin_bom"] = n_sin; out["bom_filas_con_bom"] = n_con
# BOM con 'Volcan' como primera columna (orden distinto): ¿se pierden filas?
hdr_reord = os.path.join(work, "cons_bom_volcan_primero.csv")
with open(src, encoding="utf-8") as fh:
    rows = list(csv.DictReader(fh)); campos = list(rows[0].keys())
campos2 = ["Volcan"] + [c for c in campos if c != "Volcan"]
with open(hdr_reord, "w", encoding="utf-8-sig", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=campos2); w.writeheader(); w.writerows(rows[:2000])
out["bom_volcan_primero_filas_(de_2000)"] = len(rmu.leer_pasadas(rmu.Path(hdr_reord), "CONS", "x"))
# 2) lados sintéticos
coords = bp._coords_por_volcan()
def rec(t, sensor="VIIRS_NOAA20_750"):
    return {"sensor": sensor, "datetime_utc": t, "vrp_mw": 0.0, "distance_class": None, "primary_cluster": None,
            "triggered_test1": False, "anomaly_pixels": [], "sensor_zenith_deg": 10.0}
for lado, recs in (("control", [rec("2026-11-05 06:00"), rec("2026-11-05 06:10")]),
                   ("brazo", [rec("2026-11-05 06:00")])):
    d = os.path.join(work, lado); os.makedirs(d)
    for v in bp.VOLS:
        with open(os.path.join(d, v + ".json"), "w", encoding="utf-8") as fh:
            json.dump({"records": recs if v == "Lascar" else []}, fh)
def ref_dir(nombre, filas_cons, filas_ocr=None, con_bom=False):
    d = os.path.join(work, "ref_" + nombre); os.makedirs(d)
    for n, filas in (("registro_vrp_consolidado.csv", filas_cons), ("registro_vrp_ocr.csv", filas_ocr or [])):
        with open(os.path.join(d, n), "w", encoding="utf-8-sig" if con_bom else "utf-8", newline="") as fh:
            w = csv.DictWriter(fh, fieldnames=campos); w.writeheader()
            for f in filas: w.writerow({**{c: "" for c in campos}, **f})
    return d
alerta = {"Fecha_Satelite_UTC": "2026-11-05 06:10:00", "Volcan": "Lascar", "Sensor": "VIIRS", "VRP_MW": "5.0",
          "Distancia_km": "1.0", "Tipo_Registro": "ALERTA_TERMICA", "Ultima_Actualizacion": "2026-11-05 07:00:00"}
rutina = {**alerta, "Fecha_Satelite_UTC": "2026-11-05 06:00:00", "VRP_MW": "0.0", "Tipo_Registro": "RUTINA"}
casos = {"positivo_alerta_en_hueco": ref_dir("pos", [alerta, rutina]),
         "vacia_solo_encabezado": ref_dir("vacia", []),
         "bom_con_alerta_en_hueco": ref_dir("bom", [alerta, rutina], con_bom=True)}
# vieja: copia de la referencia congelada (termina antes de la ventana)
dv = os.path.join(work, "ref_vieja"); os.makedirs(dv)
for n in ("registro_vrp_consolidado.csv", "registro_vrp_ocr.csv"):
    shutil.copy(os.path.join(snap, n), dv)
casos["vieja_snapshot_cc3887290"] = dv
for nom, d in casos.items():
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            code = ev.main(["--lado", "control=" + os.path.join(work, "control"), "--lado", "brazo=" + os.path.join(work, "brazo"),
                            "--control", "control", "--desde", "2026-11-05", "--hasta", "2026-11-07",
                            "--sensores", "VIIRS750", "--ref", d, "--salida", os.path.join(work, nom + ".json")])
        except SystemExit as e:
            code = "SystemExit %s" % e.code
    txt = buf.getvalue()
    res = json.load(open(os.path.join(work, nom + ".json"), encoding="utf-8")) if os.path.exists(os.path.join(work, nom + ".json")) else {}
    out[nom] = {"exit": code, "primera_linea": txt.splitlines()[0] if txt else "", "pasadas_mirova": res.get("pasadas_mirova"),
                "protegidas_sin_record": len(res.get("cobertura", {}).get("protegidas_sin_record_en_brazos", [])),
                "lineas_con_aviso_referencia": [l for l in txt.splitlines() if "referencia" in l.lower() or "vac" in l.lower()][:5]}
print(json.dumps(out, ensure_ascii=False, indent=1))
