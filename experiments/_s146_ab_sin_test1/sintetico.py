# -*- coding: utf-8 -*-
"""Prueba del evaluador del A/B S146 contra una salida SINTETICA con casos conocidos.

POR QUE. El evaluador decide un cambio en el sistema de alerta. Antes de creerle una sola cifra
hay que saber que se equivoca cuando tiene que equivocarse. Aca se le dan cuatro brazos cuyo
veredicto correcto se conoce de antemano, construidos a mano sobre volcanes y fechas reales
(las coordenadas y el radio interno los lee del repo, como en la corrida de verdad):

  bueno   : baja mucho la publicacion en negativos limpios y no pierde ninguna noche -> ADOPTAR
  malo    : baja igual, pero pierde una noche que MIROVA publico con 3,0 MW        -> NO ADOPTAR
  muerto  : copia byte a byte del control, no cambia nada                          -> NO ADOPTAR
  inventa : publica en una pasada donde el control no tiene ningun pixel anomalo   -> INDECIDIBLE

LAS DOS PREGUNTAS DEL INSTRUMENTO.
 (1) Si lo que mide estuviera roto, fallaria? Si: el caso "muerto" es un brazo identico al
     control. Un evaluador que diga ADOPTAR ahi esta roto, y ese es justo el modo de falla que
     mas caro sale (A110: un control que pasa en verde sobre un instrumento ya refutado es la
     prueba de que el control esta roto).
 (2) Si el instrumento estuviera muerto (por ejemplo, si el veredicto no dependiera de los
     datos), se veria distinto? Si: los cuatro brazos tienen que dar veredictos DISTINTOS y por
     criterios distintos. Si los cuatro dieran lo mismo, el evaluador no esta leyendo nada.

No toca nada del repo: todo se escribe en un directorio temporal y se borra al salir (salvo
--conservar). No usa la red: la referencia son dos CSV que genera este mismo archivo.
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ROOT = AQUI.parents[1]

VOLCANES = {"Villarrica": "Villarrica", "Lascar": "Lascar", "Isluga": "Isluga"}
TODOS_LOS_VOLCANES = ["Lascar", "Lastarria", "Isluga", "Tupungatito", "PlanchonPeteroa",
                      "NevadosDeChillan", "Llaima", "Villarrica", "Copahue",
                      "PuyehueCordonCaulle", "Chaiten"]
# Nombre del volcan tal como lo escribe el CSV de MIROVA (normalize_volcano_name lo mapea).
NOMBRE_CSV = {"Villarrica": "Villarrica", "Lascar": "Lascar", "Isluga": "Isluga"}
SENSOR_NUESTRO = {"VIIRS375": "VIIRS_SNPP", "VIIRS750": "VIIRS_NOAA20_750", "MODIS": "MODIS_AQUA"}
SENSOR_CSV = {"VIIRS375": "VIIRS375", "VIIRS750": "VIIRS750", "MODIS": "MODIS"}
# Hora UTC de cada pasada: de madrugada en Chile, para que ninguna se descarte por diurna.
HORA = {"VIIRS375": 6, "VIIRS750": 7, "MODIS": 5}

VENTANA_INICIO = datetime(2026, 9, 1, tzinfo=timezone.utc)
# Cuantas pasadas de cada clase por volcan y sensor. Los dias NO se comparten entre clases: si
# una noche tiene una ALERTA, todas sus pasadas dejan de ser negativo limpio (asi etiqueta el
# banco), y el sintetico se quedaria sin denominador. Dias 0 a 15 negativos, 16 a 19 positivos.
N_NEG = 16
N_SIN_PIXELES = 2
DIAS_POS = [16, 17, 18, 19]
MINUTOS_POS = [0, 40]


def record(dt, sensor_b, publica, *, n_px=3, vrp=0.4, t1=True, lat=-39.42, lon=-71.93):
    """Un record nuestro. `publica` decide si el predicado del dashboard lo va a publicar:
    con vrp > 0 y distance_class summit publica; con vrp 0 no (isValidDetection)."""
    v = float(vrp) if publica else 0.0
    pc = {"vrp_mw": v, "centroid_dist_km": 1.0, "n_pixels": max(1, n_px),
          "centroid_lat": lat, "centroid_lon": lon, "single_pixel_mode": False}
    r = {
        "datetime_utc": dt.strftime("%Y-%m-%d %H:%M"),
        "sensor": SENSOR_NUESTRO[sensor_b],
        "distance_class": "summit",
        "vrp_mw": v, "vrp_mir_mw": v, "t_max_k": 290.0,
        "triggered_test1": bool(t1), "discarded_reason": None,
        "n_anomalous_pixels": n_px,
        "final_hotspot_source": "test1_roi" if t1 else "ctx_cluster",
        "primary_cluster": pc if n_px else None,
        "granule": "SINTETICO",
    }
    if sensor_b == "VIIRS375":
        r["f5_core_vrp_mw"] = v
    else:
        r["anomaly_pixels"] = [{"lat": lat, "lon": lon, "vrp_mw": v, "bt_k": 290.0}]
    return r


def construir():
    """Devuelve (records_por_brazo, filas_referencia). Un solo lugar define la verdad."""
    brazos = {n: {v: [] for v in VOLCANES} for n in
              ("control", "bueno", "malo", "muerto", "inventa")}
    ref = []
    # La noche que el brazo "malo" pierde, con una magnitud que NO es sub-pixel.
    noche_cara = ("Villarrica", "VIIRS375", 2)  # indice dentro de DIAS_POS
    for vol in VOLCANES:
        for sb in ("VIIRS375", "VIIRS750", "MODIS"):
            # --- negativos limpios: MIROVA miro y publico RUTINA con VRP 0 ---
            # El control publica en el 90 % de VIIRS 375, 20 % de VIIRS 750 y 10 % de MODIS.
            cuota = {"VIIRS375": 15, "VIIRS750": 4, "MODIS": 2}[sb]
            # El brazo bueno publica en muchas menos, y la caida es mayor en VIIRS 375 que en
            # VIIRS 750 que en MODIS: es el orden que predice el mecanismo de F-01 (criterio C6).
            cuota_buena = {"VIIRS375": 4, "VIIRS750": 1, "MODIS": 1}[sb]
            for i in range(N_NEG):
                dt = VENTANA_INICIO + timedelta(days=i, hours=HORA[sb])
                pub_c, pub_b = i < cuota, i < cuota_buena
                brazos["control"][vol].append(record(dt, sb, pub_c))
                brazos["muerto"][vol].append(record(dt, sb, pub_c))
                for n in ("bueno", "malo", "inventa"):
                    brazos[n][vol].append(record(dt, sb, pub_b))
                ref.append((vol, sb, dt, "RUTINA", 0.0))
            # --- positivos: MIROVA publico ALERTA_TERMICA. Dos pasadas por noche, para que el
            # brazo "malo" pueda perder una noche entera y para que el criterio de magnitud
            # tenga al menos 5 pares por volcan y sensor.
            for j, dia in enumerate(DIAS_POS):
                for minuto in MINUTOS_POS:
                    dt = VENTANA_INICIO + timedelta(days=dia, hours=HORA[sb], minutes=minuto)
                    pierde = (vol, sb, j) == noche_cara
                    vrp_ref = 3.0 if pierde else 0.12
                    for n in brazos:
                        brazos[n][vol].append(record(dt, sb, not (pierde and n == "malo")))
                    ref.append((vol, sb, dt, "ALERTA_TERMICA", vrp_ref))
            # --- pasadas sin ningun pixel anomalo: el nulo estructural ---
            for k in range(N_SIN_PIXELES):
                dt = VENTANA_INICIO + timedelta(days=k, hours=HORA[sb], minutes=20)
                for n in brazos:
                    inventa = (n == "inventa" and k == 0 and sb == "VIIRS375")
                    brazos[n][vol].append(
                        record(dt, sb, inventa, n_px=(3 if inventa else 0)))
                ref.append((vol, sb, dt, "RUTINA", 0.0))
    return brazos, ref


def escribir(base, brazos, ref):
    for nombre, porvol in brazos.items():
        d = base / ("data_" + nombre)
        d.mkdir(parents=True, exist_ok=True)
        for vol, recs in porvol.items():
            (d / f"{vol}.json").write_text(
                json.dumps({"volcano": vol, "records": recs}, indent=1), encoding="utf-8")
        # Los ocho volcanes restantes existen y estan vacios: banco_paridad recorre los once y
        # exige el archivo. Asi el sintetico ejercita el mismo recorrido que la corrida real.
        for vol in TODOS_LOS_VOLCANES:
            p = d / f"{vol}.json"
            if not p.exists():
                p.write_text(json.dumps({"volcano": vol, "records": []}, indent=1), encoding="utf-8")
    # produccion = copia del control, para el control positivo del evaluador
    shutil.copytree(base / "data_control", base / "data_produccion")

    cabecera = ["timestamp", "Fecha_Satelite_UTC", "Fecha_Captura_Chile", "Volcan", "Sensor",
                "VRP_MW", "Distancia_km", "Tipo_Registro", "Clasificacion Mirova", "Ruta Foto",
                "Fecha_Proceso_GitHub", "Ultima_Actualizacion", "Editado"]
    cons = base / "registro_vrp_consolidado.csv"
    with open(cons, "w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(cabecera)
        for vol, sb, dt, tipo, vrp in ref:
            w.writerow([int(dt.timestamp()), dt.strftime("%Y-%m-%d %H:%M:%S"),
                        dt.strftime("%Y-%m-%d %H:%M:%S"), NOMBRE_CSV[vol], SENSOR_CSV[sb],
                        vrp, 0.0, tipo, "NULO" if tipo == "RUTINA" else "MODERADO",
                        "No descargada", "2026-09-21 00:00:00", "2026-09-21 00:00:00", "NO"])
    ocr = base / "registro_vrp_ocr.csv"
    with open(ocr, "w", encoding="utf-8", newline="") as fh:
        csv.writer(fh).writerow(cabecera)
    return cons, ocr


def parametros_sinteticos(base):
    """Los MISMOS umbrales de la corrida de verdad, salvo la lista de noches perdidas esperadas,
    que aca se vacia: en el sintetico toda perdida tiene que contar."""
    par = json.loads((AQUI / "parametros.json").read_text(encoding="utf-8"))
    par["perdidas_esperadas_noche_volcan"] = []
    par["perdidas_esperadas_noche_sensor"] = []
    par["max_noches_perdidas_volcan"] = 0
    par["max_noches_perdidas_sensor"] = 0
    par["_sintetico"] = "umbrales reales; listas de perdidas esperadas vaciadas a proposito"
    p = base / "parametros_sintetico.json"
    p.write_text(json.dumps(par, indent=1, ensure_ascii=False), encoding="utf-8")
    return p


ESPERADO = {"bueno": "ADOPTAR", "malo": "NO ADOPTAR", "muerto": "NO ADOPTAR",
            "inventa": "INDECIDIBLE"}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--conservar", action="store_true", help="no borrar el directorio temporal")
    a = ap.parse_args(argv)

    base = Path(tempfile.mkdtemp(prefix="s146_sintetico_"))
    try:
        brazos, ref = construir()
        cons, ocr = escribir(base, brazos, ref)
        par = parametros_sinteticos(base)
        salida = base / "resultado_sintetico.json"
        cmd = [sys.executable, str(AQUI / "evaluar.py"),
               "--control", str(base / "data_control"),
               "--produccion", str(base / "data_produccion"),
               "--cons", str(cons), "--ocr", str(ocr),
               "--parametros", str(par), "--out", str(salida), "--control-cargador"]
        for n in ("bueno", "malo", "muerto", "inventa"):
            cmd += ["--brazo", str(base / ("data_" + n))]
        entorno = dict(__import__("os").environ)
        entorno["PYTHONIOENCODING"] = "utf-8"
        o = subprocess.run(cmd, cwd=str(ROOT), capture_output=True, text=True, env=entorno)
        print(o.stdout)
        if o.returncode != 0:
            print(o.stderr[-4000:], file=sys.stderr)
            return 1

        res = json.loads(salida.read_text(encoding="utf-8"))
        print("=" * 78)
        print("COMPROBACION: veredicto esperado contra veredicto obtenido")
        ok = True
        vistos = {}
        for b in res["brazos"]:
            nombre = b["brazo"].replace("data_", "")
            esp = ESPERADO[nombre]
            bien = b["veredicto"] == esp
            ok = ok and bien
            vistos[nombre] = b["veredicto"]
            fallan = [k for k, v in b["criterios"].items() if not v]
            print("  %-8s esperado %-12s obtenido %-12s  %s   criterios que fallan: %s"
                  % (nombre, esp, b["veredicto"], "OK" if bien else "MAL", fallan or "-"))
        # El evaluador tiene que distinguir POR QUE falla cada uno, no solo fallar.
        malo = next(b for b in res["brazos"] if b["brazo"].endswith("malo"))
        muerto = next(b for b in res["brazos"] if b["brazo"].endswith("muerto"))
        por_motivo_distinto = (not malo["criterios"]["C1_recall_pasada"]
                               and malo["criterios"]["C3_publicacion_negativos"]
                               and muerto["criterios"]["C1_recall_pasada"]
                               and not muerto["criterios"]["C3_publicacion_negativos"]
                               and len(malo["pasadas_perdidas_grandes"]) == len(MINUTOS_POS)
                               and len(muerto["pasadas_perdidas"]) == 0)
        print("  'malo' falla por recall (1 pasada perdida de 0,5 MW o mas) y 'muerto' por"
              " publicacion (0 pasadas perdidas): motivos distintos ->", por_motivo_distinto)
        cargador = res["meta"].get("control_cargador", {})
        print("  control del cargador contra banco_paridad identico:", cargador.get("identico"))
        print("  control positivo del control cumple:", res["control_positivo"]["cumple"])
        ok = ok and por_motivo_distinto and cargador.get("identico") and \
            res["control_positivo"]["cumple"] and len(set(vistos.values())) >= 3
        print("VEREDICTO DE LA PRUEBA:", "PASA" if ok else "FALLA")
        if a.conservar:
            print("temporal conservado en", base)
        return 0 if ok else 1
    finally:
        if not a.conservar:
            shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
