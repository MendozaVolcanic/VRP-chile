"""S146 - pruebas locales de la bateria, sin MODIS real, sin credenciales y sin red.

QUE PRUEBA, y con que:
  P1 captura.py de punta a punta: calculate_vrp REAL de pipeline.process_modis sobre una escena
     sintetica (el lector de granulos reemplazado, igual que tests/arnes_sintetico_s142.py, del que
     se reusa la escena) con DOS focos: uno en la cumbre y otro plantado 10 km al este. Comprueba
     que la captura devuelve los dos cumulos donde se plantaron, que los pixeles traen camino, que
     cuadra con el record y que NO cambia el resultado (misma corrida sin captura).
  P2 captura muerta: `instalar` sobre un modulo al que le falta una funcion debe levantar error.
  P3 evaluar_bateria.py contra salidas sinteticas armadas desde los JSON commiteados de S137, con
     pixeles conocidos: control negativo (limpio), control positivo (pixel plantado en una caja
     rotada -> INDECIDIBLE por R1), pixel de magnitud cero (no ocupa), pixel a 5,2 km (fuera),
     pixel en la cumbre de un negativo (reserva R3) y captura muerta (salida 1).
  P4 verificar_cobertura.py: cobertura pareja -> 0 ; un brazo con una pasada menos -> 1.
  P5 los 10 brazos armados con el MISMO codigo del probe (correr_bateria.armar_brazo), uno por
     proceso, sobre la escena sintetica donde la compuerta decide: flags efectivos, y que quitar la
     compuerta y encender el fondo local cambian de verdad el resultado.

Todo se escribe en un directorio temporal; no toca out/ ni evaluacion/ de esta carpeta.

LAS DOS PREGUNTAS DEL INSTRUMENTO
(1) Si lo probado estuviera roto, fallaria? Cada prueba trae su contraparte: el mismo insumo con y
    sin el pixel plantado tiene que dar resultados distintos, y se comprueban los dos.
(2) Si esta prueba estuviera muerta (no ejecuta nada), se veria distinto? Si: imprime los valores
    medidos (posiciones, conteos, codigos de salida), no solo "ok", y termina con salida 1 y la
    lista de fallas si alguna comprobacion no se cumple.
"""
import copy
import io
import json
import os
import subprocess
import sys
import tempfile
import types
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
RAIZ = HERE.parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "tests"))
sys.path.insert(0, str(HERE))
os.environ.setdefault("VRP_PROFILE", "mirova_equivalent")

import numpy as np  # noqa: E402
import brazos as B  # noqa: E402
import captura as C  # noqa: E402

FALLAS = []


def comprobar(cond, texto):
    print(("   ok   " if cond else "  FALLA ") + texto)
    if not cond:
        FALLAS.append(texto)


# ------------------------------------------------------------------------------------------- P1
def escena_dos_focos():
    import arnes_sintetico_s142 as arnes
    import pipeline.process_modis as pm
    data = arnes.escena_modis("nevado")          # foco de 290 K en el centro (la cumbre)
    n = data["lat"].shape[0]
    c = n // 2
    lam = pm.BAND21_LAMBDA

    def rad(bt, lm):
        return float(pm.C1 / (lm ** 5 * (np.exp(pm.C2 / (lm * bt)) - 1)))
    for clave in ("band21", "band22"):
        data[clave] = data[clave].copy()
        data[clave][c, c + 10] = rad(300.0, lam)  # segundo foco: 10 pixeles (10 km) al este
        data[clave][c, c + 11] = rad(285.0, lam)  # y su vecino, para que el cumulo tenga 2 pixeles
    return arnes, data, c


def correr(data, arnes, con_captura):
    import pipeline.process_modis as pm
    originales = {n: getattr(pm, n) for n in C.FUNCIONES}
    cap = C.instalar(pm) if con_captura else None
    try:
        with patch.object(pm, "read_modis_l1b", return_value=data):
            rec = pm.calculate_vrp(
                hdf_path=Path("MOD021KM.A2026200.0300.061.hdf"), geo_path=Path("MOD03.sintetico.hdf"),
                volcano_lat=arnes.LAT0, volcano_lon=arnes.LON0, radius_km=25.0,
                vent_lat=arnes.LAT0, vent_lon=arnes.LON0, inner_radius_km=5.0)
    finally:
        for n, f in originales.items():
            setattr(pm, n, f)
    return rec, cap


def p1():
    print("\nP1  captura de punta a punta con calculate_vrp real (escena sintetica, dos focos)")
    arnes, data, c = escena_dos_focos()
    rec0, _ = correr(data, arnes, con_captura=False)
    rec1, cap = correr(data, arnes, con_captura=True)
    comprobar(rec0 is not None and rec1 is not None, "calculate_vrp devuelve record en las dos corridas")
    comprobar(json.dumps(rec0.get("primary_cluster"), sort_keys=True) == json.dumps(rec1.get("primary_cluster"), sort_keys=True)
              and rec0.get("vrp_mw") == rec1.get("vrp_mw") and rec0.get("n_anomalous_pixels") == rec1.get("n_anomalous_pixels"),
              f"la captura NO cambia el resultado: pc={rec1.get('primary_cluster')} vrp={rec1.get('vrp_mw')} n={rec1.get('n_anomalous_pixels')}")
    cum, pix, publicada, disc = C.extraer(cap, rec1, arnes.LAT0, arnes.LON0)
    for x in cum:
        print(f"        cumulo {x['origen']} orden={x['orden']} primario={x['es_primario_publicado']} n_px={x['n_pixels']} "
              f"d_cumbre={x['dist_cumbre_km']} km crudo={x['vrp_mw_crudo']} MW publicado={x['vrp_mw_publicado']}")
    for x in pix:
        print(f"        pixel ({x['fila']},{x['col']}) d_cumbre={x['dist_cumbre_km']} km vrp={x['vrp_mw']} caminos={x['caminos']}")
    comprobar(disc == [], f"captura cuadra con el record (discrepancias={disc})")
    comprobar(len(cum) >= 2, f"devuelve mas de un cumulo ({len(cum)}); la bateria vieja guardaba 1")
    lejos = [x for x in cum if 9.0 <= x["dist_cumbre_km"] <= 11.5]
    comprobar(len(lejos) == 1 and lejos[0]["n_pixels"] == 2 and not lejos[0]["es_primario_publicado"],
              "el foco plantado 10 km al este aparece como cumulo NO primario de 2 pixeles")
    cerca = [x for x in cum if x["es_primario_publicado"]]
    comprobar(len(cerca) == 1 and cerca[0]["dist_cumbre_km"] < 1.0, "el primario publicado es el de la cumbre")
    px_lejos = [x for x in pix if (x["fila"], x["col"]) in {(c, c + 10), (c, c + 11)}]
    comprobar(len(px_lejos) == 2 and all((x["vrp_mw"] or 0) > 0 for x in px_lejos),
              "los dos pixeles plantados estan en la lista, con magnitud")
    comprobar(all(x["caminos"] for x in pix), "todo pixel alertado trae al menos un camino")
    n_ctx = sum(1 for x in pix if x["origen"] == "contextual")
    comprobar(n_ctx == rec1.get("n_anomalous_pixels"),
              f"pixeles de la llamada contextual ({n_ctx}) == n_anomalous_pixels del record "
              f"({rec1.get('n_anomalous_pixels')}); los otros {len(pix) - n_ctx} son del bloque del Test 1")
    # contraparte: la misma escena SIN el segundo foco no debe traer el cumulo lejano
    data2 = arnes.escena_modis("nevado")
    rec2, cap2 = correr(data2, arnes, con_captura=True)
    cum2, _, _, _ = C.extraer(cap2, rec2, arnes.LAT0, arnes.LON0)
    comprobar(not [x for x in cum2 if 9.0 <= x["dist_cumbre_km"] <= 11.5],
              f"contraparte: sin plantar el foco, no hay cumulo a 10 km ({len(cum2)} cumulos en total)")


def p2():
    print("\nP2  captura muerta: modulo al que le falta una funcion")
    falso = types.SimpleNamespace(__name__="falso", combine_hot_paths=len, second_pass_adjacent=len,
                                  cluster_hotspots=len)     # falta first_pass_tests_2_and_3
    try:
        C.instalar(falso)
        comprobar(False, "instalar debia levantar AttributeError y no lo hizo")
    except AttributeError as e:
        comprobar(True, f"instalar se niega: {e}")


# ------------------------------------------------------------------------------------------- P3
def cargar_ev():
    import importlib.util
    spec = importlib.util.spec_from_file_location("ev_sellado", RAIZ / "experiments/_s146_a2/evaluar_vara_corregida.py")
    # el modulo reenvuelve sys.stdout al importarse; se le presta un stdout descartable
    real = sys.stdout
    sys.stdout = io.TextIOWrapper(io.BytesIO(), encoding="utf-8")
    try:
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
    finally:
        sys.stdout = real
    return mod


def salida_sintetica(commiteado):
    """Salida del formato nuevo fabricada desde un JSON commiteado: cada cumulo primario con
    magnitud se vuelve un cumulo de un pixel en su propia posicion."""
    d = json.loads((RAIZ / commiteado / "resultado_apendice.json").read_text(encoding="utf-8"))
    for c in d:
        for k, p in enumerate(c["pasadas"]):
            p["cumulos"], p["pixeles_alertados"], p["captura_discrepancias"] = [], [], []
            if p.get("pc_lat") is not None and (p.get("vrp_pc_mw") or 0) > 0:
                p["cumulos"].append({"origen": "contextual", "orden": 0, "es_primario_publicado": True,
                                     "n_pixels": 1, "lat": p["pc_lat"], "lon": p["pc_lon"],
                                     "dist_cumbre_km": p["dist_crater_km"], "vrp_mw_crudo": p["vrp_pc_mw"],
                                     "vrp_mw_publicado": p["vrp_pc_mw"]})
                p["pixeles_alertados"].append({"origen": "contextual", "cumulo_orden": 0, "fila": 100 + k,
                                               "col": 100, "lat": p["pc_lat"], "lon": p["pc_lon"],
                                               "dist_cumbre_km": p["dist_crater_km"], "vrp_mw": p["vrp_pc_mw"],
                                               "caminos": ["primer_pase_t23"]})
            elif p.get("pc_lat") is not None:
                p["pc_lat"] = p["pc_lon"] = None    # primario sin magnitud: no lo modelamos
        c["intentos"] = [{"granule": p["granule"], "estado": "procesada"} for p in c["pasadas"]]
    return d


def plantar(d, caso, lat, lon, vrp, dist_cumbre):
    p = [c for c in d if c["caso"] == caso][0]["pasadas"][0]
    orden = len(p["cumulos"])
    p["cumulos"].append({"origen": "contextual", "orden": orden, "es_primario_publicado": False,
                         "n_pixels": 1, "lat": lat, "lon": lon, "dist_cumbre_km": dist_cumbre,
                         "vrp_mw_crudo": vrp, "vrp_mw_publicado": None})
    p["pixeles_alertados"].append({"origen": "contextual", "cumulo_orden": orden, "fila": 7, "col": 7 + orden,
                                   "lat": lat, "lon": lon, "dist_cumbre_km": dist_cumbre, "vrp_mw": vrp,
                                   "caminos": ["segundo_pase_recaptura"]})


def escribir(tmp, nombre, arm, d):
    o = tmp / nombre / arm
    o.mkdir(parents=True, exist_ok=True)
    (o / "resultado_apendice.json").write_text(json.dumps(d), encoding="utf-8")
    (o / "meta.json").write_text(json.dumps({"intentos_malos": [], "captura_discrepancias": []}), encoding="utf-8")
    return tmp / nombre


def evaluar(out_dir, tmp):
    r = subprocess.run([sys.executable, str(HERE / "evaluar_bateria.py"), "--out", str(out_dir),
                        "--informe", str(tmp / ("inf_" + out_dir.name))],
                       capture_output=True, text=True, encoding="utf-8")
    inf = tmp / ("inf_" + out_dir.name) / "resultado_bateria_s146.json"
    j = json.loads(inf.read_text(encoding="utf-8")) if inf.exists() else None
    return r, j


def p3(tmp):
    print("\nP3  evaluador contra salidas sinteticas con pixeles conocidos (mejor brazo de S137 como base)")
    ev = cargar_ev()
    MEJOR = "out_apendice_b22_sincompuerta_fondolocal_prosa"
    et = B.por_nombre(MEJOR)["etiqueta"]
    base = salida_sintetica(B.por_nombre(MEJOR)["commiteado"])
    cumbre = (63.633, -19.633)
    D = ev.hav(*cumbre, *ev.FISURA["A2"])
    Rf = ev.rumbo(*cumbre, *ev.FISURA["A2"])
    centro_oeste = ev.punto_desde(*cumbre, D, (Rf + 180) % 360)

    r, j = evaluar(escribir(tmp, "limpio", MEJOR, base), tmp)
    b = j["brazos"][et]
    print("        limpio:", r.returncode, b["A2_final"], "|", b["regalo"], "|", b["lectura"])
    comprobar(r.returncode == 0 and b["A2_final"] == "ACIERTO" and b["nulas_ocupadas"] == 0 and b["nulas_evaluadas"] == 34,
              "control negativo: sin pixeles plantados, ACIERTO y 0 de 34 cajas nulas ocupadas")
    comprobar(j["Cpx_d"]["iguales"] == j["Cpx_d"]["total"] == 9, f"Cpx-d reproduce lo commiteado: {j['Cpx_d']}")

    d = copy.deepcopy(base)
    plantar(d, "A2", *centro_oeste, 0.5, D)
    r, j = evaluar(escribir(tmp, "plantado", MEJOR, d), tmp)
    b = j["brazos"][et]
    print("        plantado +180:", r.returncode, b["A2_final"], "|", b["regalo"], "|", b["lectura"])
    comprobar(b["A2_sellado"] == "ACIERTO" and b["A2_final"].startswith("INDECIDIBLE (R1") and b["nulas_ocupadas"] == 1
              and b["regalo"] == "regalo marginal" and b["total_final"] == 8,
              "control positivo: un pixel de 0,5 MW en la caja rotada +180 -> A2 INDECIDIBLE por R1, 8/9, regalo marginal")

    d = copy.deepcopy(base)
    plantar(d, "A2", *centro_oeste, 0.0, D)
    r, j = evaluar(escribir(tmp, "plantado_cero", MEJOR, d), tmp)
    b = j["brazos"][et]
    caja = [c for c in b["cajas"] if c["caso"] == "A2" and c["giro"] == 180.0][0]
    print("        plantado con magnitud cero:", caja)
    comprobar(b["A2_final"] == "ACIERTO" and caja["n_con_magnitud"] == 0 and caja["n_alertados"] == 1,
              "pixel de magnitud cero: no ocupa la caja decisoria y si aparece en el conteo informativo")

    d = copy.deepcopy(base)
    fuera = ev.punto_desde(*centro_oeste, 5.2, 0.0)
    plantar(d, "A2", *fuera, 0.5, ev.hav(*cumbre, *fuera))
    r, j = evaluar(escribir(tmp, "plantado_fuera", MEJOR, d), tmp)
    b = j["brazos"][et]
    comprobar(b["A2_final"] == "ACIERTO" and b["nulas_ocupadas"] == 0,
              "pixel a 5,2 km del centro de la caja: queda fuera (el borde de 5,0 km se respeta)")

    d = copy.deepcopy(base)
    for k in range(4):   # R2: cuatro cajas N2px ocupadas en cuatro volcanes distintos
        caso = ["A3", "A5", "A6", "A8"][k]
        cy = [c for c in d if c["caso"] == caso][0]
        import yaml
        cc = {c["caso"]: c for c in yaml.safe_load((RAIZ / "experiments/_s136/apendice_a.yaml").read_text(encoding="utf-8"))["casos"]}[caso]
        pt = ev.punto_desde(cc["lat"], cc["lon"], D, (Rf + 90) % 360)
        plantar(d, caso, *pt, 0.2, D)
    r, j = evaluar(escribir(tmp, "plantado_x4", MEJOR, d), tmp)
    b = j["brazos"][et]
    print("        cuatro cajas N2px:", b["regalo"], "|", b["lectura"])
    comprobar(b["nulas_ocupadas"] == 4 and b["regalo"] == "REGALA ACIERTOS" and "SIN VALOR DISCRIMINANTE" in b["lectura"],
              "R2: cuatro cajas nulas ocupadas -> REGALA ACIERTOS y el 9/9 se informa sin valor discriminante")

    d = copy.deepcopy(base)
    plantar(d, "A9", 38.789 + 0.01, 15.213, 0.3, 1.1)
    r, j = evaluar(escribir(tmp, "negativo", MEJOR, d), tmp)
    b = j["brazos"][et]
    print("        pixel en la cumbre de Stromboli:", b["reservas_negativos"], "|", b["lectura"])
    comprobar(b["reservas_negativos"] == ["A9"] and "reserva" in b["lectura"],
              "R3: pixel con magnitud a 1 km de la cumbre de un negativo CONFORME -> reserva")

    d = copy.deepcopy(base)
    for p in [c for c in d if c["caso"] == "A2"][0]["pasadas"]:
        p["pixeles_alertados"], p["cumulos"] = [], []
    r, j = evaluar(escribir(tmp, "captura_muerta", MEJOR, d), tmp)
    print("        captura muerta: salida", r.returncode, "|", [x for x in r.stdout.splitlines() if "Cpx" in x and "muerta" in x][:1])
    comprobar(r.returncode == 1, "captura muerta (A2 acierta por cumulo y no hay pixeles): el evaluador sale con 1")

    # excluida: un pixel en A1 rumbo 358,6 (Klyuchevskoy) no entra a la tasa
    d = copy.deepcopy(base)
    bez = (55.972, 160.595)
    plantar(d, "A1", *ev.punto_desde(*bez, D, (Rf + 270) % 360), 0.1, D)
    r, j = evaluar(escribir(tmp, "excluida", MEJOR, d), tmp)
    b = j["brazos"][et]
    comprobar(b["nulas_ocupadas"] == 0 and b["excluidas"][0]["n_con_magnitud"] == 1,
              "caja excluida (A1 al norte, Klyuchevskoy): se reporta aparte y no entra a la tasa")
    return base


def p4(tmp, base):
    print("\nP4  verificador de cobertura")
    ctrl = salida_sintetica("experiments/_s136/out_apendice")
    raiz = escribir(tmp, "cob_ok", "out_apendice", ctrl)
    escribir(tmp, "cob_ok", "out_apendice_b22_sincompuerta_fondolocal_prosa", base)
    lista = json.dumps(["out_apendice", "out_apendice_b22_sincompuerta_fondolocal_prosa"])
    r = subprocess.run([sys.executable, str(HERE / "verificar_cobertura.py"), "--brazos", lista, "--out", str(raiz)],
                       capture_output=True, text=True, encoding="utf-8")
    print("        " + "\n        ".join(r.stdout.strip().splitlines()))
    comprobar(r.returncode == 0, "cobertura pareja -> salida 0")
    corto = copy.deepcopy(base)
    [c for c in corto if c["caso"] == "A7"][0]["pasadas"].pop()
    raiz2 = escribir(tmp, "cob_mala", "out_apendice", ctrl)
    escribir(tmp, "cob_mala", "out_apendice_b22_sincompuerta_fondolocal_prosa", corto)
    r = subprocess.run([sys.executable, str(HERE / "verificar_cobertura.py"), "--brazos", lista, "--out", str(raiz2)],
                       capture_output=True, text=True, encoding="utf-8")
    print("        " + "\n        ".join(x for x in r.stdout.strip().splitlines() if x.startswith("  -") or "NO PAREJA" in x))
    comprobar(r.returncode == 1, "un brazo con una pasada menos en A7 -> salida 1")
    r = subprocess.run([sys.executable, str(HERE / "verificar_cobertura.py"), "--brazos",
                        json.dumps(["out_apendice", "out_apendice_b22"]), "--out", str(raiz)],
                       capture_output=True, text=True, encoding="utf-8")
    comprobar(r.returncode == 1, "un brazo pedido sin salida -> salida 1 (ausencia no es 'nada que reportar')")


# ------------------------------------------------------------------------------------------- P5
def un_brazo(nombre):
    """Proceso hijo: arma UN brazo con el mismo codigo del probe (correr_bateria.armar_brazo) y corre
    la escena `nevado_vecino_tibio`, la que S142 construyo para que la compuerta y el fondo decidan."""
    import arnes_sintetico_s142 as arnes
    import correr_bateria as CB
    import pipeline.process_modis as pm
    s136 = CB.cargar_s136()
    brazo = B.por_nombre(nombre)
    efectivo = CB.armar_brazo(pm, s136, brazo)
    cap = C.instalar(pm)
    data = arnes.escena_modis("nevado_vecino_tibio")
    with patch.object(pm, "read_modis_l1b", return_value=data):
        rec = pm.calculate_vrp(
            Path("MOD021KM.A2026200.0300.061.hdf"), Path("MOD03.sintetico.hdf"),
            arnes.LAT0, arnes.LON0, 25.0, vent_lat=arnes.LAT0, vent_lon=arnes.LON0,
            vent_radius_km=4.0, inner_radius_km=5.0, exclude_zones=None, active_water_bodies=None,
            lbg_global_compatible=False, local_kernel_bg_compatible=brazo["fondo_local"])
    cum, pix, publicada, disc = C.extraer(cap, rec, arnes.LAT0, arnes.LON0)
    pc = rec.get("primary_cluster") or {}
    print("JSON:" + json.dumps({"efectivo": efectivo, "n_primer_pase": rec.get("diag_n_first_pass_pixels"),
                                "n_pixeles": len(pix), "n_cumulos": len(cum), "vrp_pc": pc.get("vrp_mw"),
                                "publicada": publicada, "disc": disc,
                                "crudo_contextual": round(sum(x["vrp_mw_crudo"] or 0 for x in cum
                                                              if x["origen"] == "contextual"), 4)}))


def p5():
    print("\nP5  los 10 brazos armados con el codigo del probe, escena sintetica donde la compuerta decide")
    res = {}
    for b in B.como_dicts():
        r = subprocess.run([sys.executable, str(Path(__file__)), "--brazo", b["nombre"]],
                           capture_output=True, text=True, encoding="utf-8")
        linea = [x for x in r.stdout.splitlines() if x.startswith("JSON:")]
        if r.returncode != 0 or not linea:
            comprobar(False, f"{b['nombre']}: el proceso hijo fallo: {r.stderr[-400:]}")
            continue
        j = res[b["nombre"]] = json.loads(linea[0][5:])
        print(f"        {b['etiqueta']:24s} primer_pase={j['n_primer_pase']} pixeles={j['n_pixeles']} cumulos={j['n_cumulos']} "
              f"vrp_pc={j['vrp_pc']} crudo_ctx={j['crudo_contextual']} publicada={j['publicada']} disc={j['disc']}")
        e = j["efectivo"]
        comprobar(e["ENABLE_MODIS_B22_PRIMARY"] == b["b22"] and e["ENABLE_TESTS_23_PROSE_BRANCH"] == b["prosa"]
                  and e["compuerta_t23_quitada"] == b["sin_compuerta"] and e["local_kernel_bg_compatible"] == b["fondo_local"]
                  and j["disc"] == [], f"{b['nombre']}: flags efectivos = los del brazo y la captura cuadra")
    if len(res) == len(B.como_dicts()):
        con, sin = res["out_apendice_b22"], res["out_apendice_b22_sincompuerta"]
        comprobar((sin["n_primer_pase"] or 0) > (con["n_primer_pase"] or 0),
                  f"quitar la compuerta CAMBIA el primer pase en esta escena ({con['n_primer_pase']} -> {sin['n_primer_pase']}): el parche engancha")
        a, l = res["out_apendice_b22_sincompuerta"], res["out_apendice_b22_sincompuerta_fondolocal"]
        # En esta escena publica el bloque del Test 1, que no usa el fondo por vecinos; el efecto del
        # fondo local se ve en la magnitud cruda de los cumulos de la llamada contextual.
        comprobar(a["crudo_contextual"] != l["crudo_contextual"],
                  f"el fondo local CAMBIA la magnitud cruda de los cumulos contextuales "
                  f"({a['crudo_contextual']} -> {l['crudo_contextual']} MW): el argumento llega")


def main():
    if hasattr(sys.stdout, "buffer"):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", line_buffering=True)
    if len(sys.argv) == 3 and sys.argv[1] == "--brazo":
        un_brazo(sys.argv[2])
        return 0
    p1()
    p2()
    p5()
    with tempfile.TemporaryDirectory() as t:
        tmp = Path(t)
        base = p3(tmp)
        p4(tmp, base)
    print(f"\n{'TODO OK' if not FALLAS else 'FALLAS: ' + str(len(FALLAS))}")
    for f in FALLAS:
        print("  -", f)
    return 1 if FALLAS else 0


if __name__ == "__main__":
    sys.exit(main())
