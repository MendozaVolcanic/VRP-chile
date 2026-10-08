# -*- coding: utf-8 -*-
"""S150. Prueba de medir_ndc.py ANTES de despachar (verificador del pre-registro, H4): nulo y dos controles
positivos, sobre los records de produccion de Nevados de Chillan y la referencia congelada.

  NULO: todos los brazos = produccion, salvo E = produccion reetiquetada (etiqueta MODIS desde el cumulo).
        Esperado: controles OK, cableado OK, cero perdidas, P5 sin cambios.
  POSITIVO 1: en F se oculta (distance_class far) la alerta VIIRS 375 del 2026-09-29 05:18 (MIROVA 5,73 MW).
        Esperado: P1 VETADO con exactamente esa pasada.
  POSITIVO 2: E = produccion SIN reetiquetar. Esperado: CABLEADO ROTO.

Uso: python probar_medir_ndc.py <TMP>   (escribe sólo en <TMP>)
"""
import copy, io, json, shutil, subprocess, sys
from pathlib import Path
AQUI = Path(__file__).resolve().parent; RAIZ = AQUI.parents[1]
# medir_ndc ya envuelve sys.stdout en utf-8 al importarse; envolverlo dos veces cierra el flujo.
sys.path.insert(0, str(AQUI)); import medir_ndc as m  # noqa: E402
TMP = Path(sys.argv[1]); PROD = json.load(open(RAIZ / "data" / "mirova_equivalent" / "NevadosDeChillan.json", encoding="utf-8"))
INNER = 5.0


def reetiquetar(d):
    d = copy.deepcopy(d)
    for r in d["records"]:
        pc = r.get("primary_cluster") or {}
        if r.get("sensor", "").startswith("MODIS") and r.get("distance_class") is not None and pc.get("centroid_dist_km") is not None:
            r["distance_class"] = "summit" if pc["centroid_dist_km"] <= INNER else "far"
    return d


def ocultar(d, sensor_prefijo, t):
    d = copy.deepcopy(d); n = 0
    for r in d["records"]:
        if r.get("datetime_utc") == t and r.get("sensor", "").startswith(sensor_prefijo) and not r["sensor"].endswith("_750"):
            r["distance_class"] = "far"; n += 1
    assert n == 1, n
    return d


def armar(nombre, cambios):
    raiz = TMP / nombre; shutil.rmtree(raiz, ignore_errors=True)
    for n, perfil in m.BRAZOS.items():
        (raiz / perfil).mkdir(parents=True)
        json.dump(cambios.get(n, PROD), open(raiz / perfil / (m.VOL + ".json"), "w", encoding="utf-8"))
    out = TMP / (nombre + ".json")
    r = subprocess.run([sys.executable, str(AQUI / "medir_ndc.py"), "--raiz", str(raiz), "--ref", str(AQUI / "_congelado_ndc"),
                        "--out", str(out), "--tmp", str(TMP / ("tmp_" + nombre))], capture_output=True, text=True, encoding="utf-8")
    print("#" * 20, nombre, "rc", r.returncode); print(r.stdout[-6000:]); print(r.stderr[-1500:])
    return json.loads(out.read_text(encoding="utf-8")) if out.exists() else None


E = reetiquetar(PROD)
nulo = armar("nulo", {"E": E})
p1 = armar("positivo_p1", {"E": E, "F": ocultar(PROD, "VIIRS", "2026-09-29 05:18")})
p2 = armar("positivo_cableado", {})
chk = {
    "nulo: controles OK": nulo and nulo["controles_ok"],
    "nulo: cableado OK": nulo and nulo["cableado_etiqueta_ok"],
    "nulo: P1 y P2 cumplen": nulo and nulo["veredicto"].get("P1") == "CUMPLE" and nulo["veredicto"].get("P2") == "CUMPLE",
    "nulo: P5 sin cambios": nulo and nulo["veredicto"].get("P5_T0") == "CUMPLE",
    "positivo 1: P1 VETADO": p1 and p1["veredicto"].get("P1") == "VETADO",
    "positivo 2: cableado ROTO": p2 and p2["cableado_etiqueta_ok"] is False,
}
print("\n== RESUMEN"); [print("  ", "OK  " if v else "FALLA", k) for k, v in chk.items()]
sys.exit(0 if all(chk.values()) else 1)
