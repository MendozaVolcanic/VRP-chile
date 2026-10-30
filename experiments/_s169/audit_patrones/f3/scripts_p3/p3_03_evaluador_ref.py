# -*- coding: utf-8 -*-
"""Sondas sobre scripts/evaluador_comun.py (main) y scripts/referencia_mirova_unificada.py / clase_mirova.py.

Se ejecutan en carpetas temporales (TMP del sistema); el arbol auditado solo se lee. Se corre node (liviano) para el
predicado del tablero SOLO en el caso control (un record).

Cada caso declara: P1 = si la referencia estuviera rota, esta medicion lo veria?; P2 = si el instrumento estuviera muerto
(siempre OK), el resultado cambiaria? Para P2 hay un control positivo en cada bloque (caso donde SI debe dar INVALIDO).
Datos: sinteticos. Ventana: 2026-11-03 a 2026-11-10.
"""
import json, os, subprocess, sys, tempfile, csv
from pathlib import Path

ARBOL = Path(r"D:/vrp-trabajo/temporales/s169_audit_patrones/f3_comun/arbol")
PY = sys.executable
VOLS = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa", "NevadosDeChillan",
        "Llaima", "Villarrica", "Copahue", "PuyehueCordonCaulle", "Chaiten"]
COLS = ["Volcan", "Sensor", "Fecha_Satelite_UTC", "Tipo_Registro", "VRP_MW", "Distancia_km", "Clasificacion Mirova",
        "Ultima_Actualizacion", "Nota_Validacion", "Metodo_Validacion"]

def escribir_ref(d, filas, bom=False, cons_nombre="registro_vrp_consolidado.csv"):
    d.mkdir(parents=True, exist_ok=True)
    with open(d / cons_nombre, "w", encoding="utf-8-sig" if bom else "utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS); w.writeheader()
        for f in filas: w.writerow({c: f.get(c, "") for c in COLS})
    with open(d / "registro_vrp_ocr.csv", "w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=COLS); w.writeheader()

def lado(d, records_por_vol=None):
    d.mkdir(parents=True, exist_ok=True)
    for v in VOLS:
        (d / f"{v}.json").write_text(json.dumps({"records": (records_por_vol or {}).get(v, [])}), encoding="utf-8")

def correr(args):
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    env.pop("VRP_PROFILE", None)
    r = subprocess.run([PY, "-I", str(ARBOL / "scripts" / "evaluador_comun.py")] + args, capture_output=True, text=True,
                       encoding="utf-8", env=env, cwd=str(ARBOL))
    ln = [l for l in r.stdout.splitlines() if l.startswith("COBERTURA CONTRA MIROVA")]
    return r.returncode, (ln[0] if ln else "(sin linea de cobertura)"), r.stderr[-300:]

T = Path(tempfile.mkdtemp(prefix="p3_eval_"))
# ---------- BLOQUE 1: referencia que no llega a la ventana (stale) o vacia
alerta = {"Volcan": "Lascar", "Sensor": "VIIRS375", "Fecha_Satelite_UTC": "2026-11-05 05:10:00", "Tipo_Registro": "ALERTA_TERMICA",
          "VRP_MW": "3.2", "Distancia_km": "1.1", "Clasificacion Mirova": "Bajo", "Ultima_Actualizacion": "2026-11-05 08:00:00"}
vieja = dict(alerta, Fecha_Satelite_UTC="2026-10-01 05:10:00", Ultima_Actualizacion="2026-10-01 08:00:00")
rec_ctrl = {"datetime_utc": "2026-11-05 05:10", "sensor": "VIIRS_NOAA20", "vrp_mw": 3.0, "distance_class": "summit",
            "t_max_k": 310.0, "primary_cluster": {"vrp_mw": 3.0, "centroid_dist_km": 1.0, "n_pixels": 3},
            "sensor_zenith_deg": 20.0, "triggered_test1": False}
base = ["--control", "prod", "--desde", "2026-11-03", "--hasta", "2026-11-10", "--sensores", "VIIRS375"]

print("== B1a: referencia VIEJA (ninguna fila en la ventana), control y brazo con un record de 11-05")
escribir_ref(T / "ref_vieja", [vieja]); lado(T / "prod", {"Lascar": [rec_ctrl]}); lado(T / "brazo", {"Lascar": [rec_ctrl]})
print("  ", correr(["--lado", f"prod={T/'prod'}", "--lado", f"brazo={T/'brazo'}", "--ref", str(T / "ref_vieja")] + base))
print("== B1b: CONTROL POSITIVO: referencia al dia (alerta 3,2 MW de 11-05), control tiene el record y el brazo NO")
escribir_ref(T / "ref_al_dia", [alerta]); lado(T / "brazo_vacio")
print("  ", correr(["--lado", f"prod={T/'prod'}", "--lado", f"brazo={T/'brazo_vacio'}", "--ref", str(T / "ref_al_dia")] + base))
print("== B1c: referencia al dia, brazo y control con record: debe ser OK")
print("  ", correr(["--lado", f"prod={T/'prod'}", "--lado", f"brazo={T/'brazo'}", "--ref", str(T / "ref_al_dia")] + base))

# ---------- BLOQUE 2: nombres de archivo de la referencia versionada vs lo que --ref espera
print("== B2: carpeta del snapshot versionado (nombres reales del repo) pasada a --ref")
snap_nombres = ["registro_vrp_consolidado_respaldo_20260408.csv"]            # referencia_mirova_unificada.RESPALDO_20260408
esperado = ["respaldo_20260408.csv", "consolidado_filas_perdidas.csv"]        # evaluador_comun.main (opc)
print("   nombre del respaldo en el snapshot:", snap_nombres[0], "| nombre que busca evaluador_comun:", esperado[0])
print("   el nombre del snapshot coincide con el que busca evaluador_comun:", snap_nombres[0] == esperado[0])
fila_perdida = dict(alerta, Fecha_Satelite_UTC="2026-11-06 05:12:00")
(T / "ref_snap").mkdir()
escribir_ref(T / "ref_snap", [alerta])
with open(T / "ref_snap" / "registro_vrp_consolidado_respaldo_20260408.csv", "w", encoding="utf-8", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=COLS); w.writeheader(); w.writerow({c: fila_perdida.get(c, "") for c in COLS})
sys.path.insert(0, str(ARBOL)); sys.path.insert(0, str(ARBOL / "scripts"))
os.environ.pop("VRP_PROFILE", None)
import referencia_mirova_unificada as RM
import clase_mirova as CM
# lo que hace evaluador_comun.main con la carpeta del snapshot:
ref_dir = T / "ref_snap"
opc = lambda n: (ref_dir / n) if (ref_dir / n).exists() else None
f_eval = RM.cargar_referencia_unificada(ref_dir / "registro_vrp_consolidado.csv", ref_dir / "registro_vrp_ocr.csv",
                                        respaldo_path=opc("respaldo_20260408.csv"), historico_path=opc("consolidado_filas_perdidas.csv"))
f_ok = RM.cargar_referencia_unificada(ref_dir / "registro_vrp_consolidado.csv", ref_dir / "registro_vrp_ocr.csv",
                                      respaldo_path=ref_dir / "registro_vrp_consolidado_respaldo_20260408.csv", historico_path=None)
print("   filas con la rutina de evaluador_comun.main:", len(f_eval), "| filas si se pasa el respaldo por su nombre real:", len(f_ok))

# ---------- BLOQUE 3: BOM en el CSV (renombre de columna) y NaN en VRP
print("== B3a: consolidado con BOM utf-8 (primer encabezado '\\ufeffVolcan')")
escribir_ref(T / "ref_bom", [alerta], bom=True)
f_bom = RM.leer_pasadas(T / "ref_bom" / "registro_vrp_consolidado.csv", "CONS", "principal")
print("   filas leidas con BOM:", len(f_bom), "| sin BOM (control):", len(RM.leer_pasadas(T / "ref_al_dia" / "registro_vrp_consolidado.csv", "CONS", "principal")))
print("== B3b: VRP_MW = 'nan' en una fila de alerta (lectura A, umbral 1 MW)")
for v in ("nan", "", "0.4", "1.2"):
    fila = {"tipo": "ALERTA_TERMICA", "vrp_mw": RM._float(v)}
    print(f"   VRP_MW={v!r:6} -> _float={fila['vrp_mw']!r:6} alerta_protegida(A)={CM.alerta_protegida(fila)}")
