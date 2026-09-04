# -*- coding: utf-8 -*-
"""
S133 - Sustrato del A/B del area geolocalizada (decision #5 de AUDIT_S131 §4).

FICHA SDA - no participa de la deteccion ni de la clasificacion. Es un script de
medicion read-only sobre records ya persistidos; no escribe en data/ ni en pipeline/.

POR QUE: antes de gastar un reproc de 3 brazos en CI hay que responder la pregunta
previa a "¿mejora algo?", que es "¿llega a ejecutarse?" (leccion S130). Este script
mide las DOS caras del sustrato:

  (1) sustrato de CODIGO: ¿algun consumidor de produccion lee el flag
      ENABLE_GEOLOCATED_PIXEL_AREA o llama a pixel_areas_from_geolocation?
      Si no lo hay, el brazo "area" del A/B es identico al control y el A/B
      no puede medir nada. Se responde por AST, no por grep de texto (A89: el
      nombre en el punto de uso no es el nombre en la definicion).

  (2) sustrato de DATO: distribucion del angulo cenital del sensor en los records
      persistidos, por sensor y por volcan. S131 lo midio sobre 2.773 PARES contra
      MIROVA; aca se mide sobre el corpus entero de RECORDS, que es otro denominador
      (A90) y por eso se declara explicito.

Todo numero sale de aca y se persiste a JSON (S91). Nada transcrito a mano.
"""
import ast
import glob
import io
import json
import os
import sys

import numpy as np

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                    "..", ".."))

FLAG = "ENABLE_GEOLOCATED_PIXEL_AREA"
FUNC = "pixel_areas_from_geolocation"


def sustrato_de_codigo():
    """Hay consumidor de produccion? Se recorre el AST de cada modulo de pipeline/."""
    consumidores_flag = []
    llamadas_func = []
    archivos = sorted(glob.glob(os.path.join(REPO, "pipeline", "**", "*.py"),
                                recursive=True))
    for ruta in archivos:
        rel = os.path.relpath(ruta, REPO).replace("\\", "/")
        with open(ruta, encoding="utf-8") as fh:
            src = fh.read()
        try:
            arbol = ast.parse(src, filename=rel)
        except SyntaxError:
            continue
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Name) and nodo.id == FLAG:
                if isinstance(getattr(nodo, "ctx", None), ast.Store):
                    continue
                consumidores_flag.append("%s:%d" % (rel, nodo.lineno))
            if isinstance(nodo, ast.Attribute) and nodo.attr == FLAG:
                consumidores_flag.append("%s:%d" % (rel, nodo.lineno))
            if isinstance(nodo, ast.Call):
                f = nodo.func
                if isinstance(f, ast.Name):
                    nombre = f.id
                elif isinstance(f, ast.Attribute):
                    nombre = f.attr
                else:
                    nombre = None
                if nombre == FUNC:
                    llamadas_func.append("%s:%d" % (rel, nodo.lineno))

    definicion = []
    ruta_profile = os.path.join(REPO, "pipeline", "profile.py")
    with open(ruta_profile, encoding="utf-8") as fh:
        for i, linea in enumerate(fh, 1):
            if FLAG in linea and "=" in linea and not linea.strip().startswith("#"):
                definicion.append("pipeline/profile.py:%d" % i)

    consumidores = sorted(set(c for c in consumidores_flag if c not in definicion))
    llamadas = sorted(set(llamadas_func))
    return {
        "flag": FLAG,
        "funcion": FUNC,
        "definicion_del_flag": definicion,
        "consumidores_del_flag_en_produccion": consumidores,
        "llamadas_a_la_funcion_en_produccion": llamadas,
        "el_brazo_area_seria_identico_al_control": (
            len(consumidores) == 0 and len(llamadas) == 0),
        "archivos_de_pipeline_recorridos": len(archivos),
    }


def _bucket_sensor(sensor):
    """Convencion del repo (A48): VIIRS_* sin sufijo = I-band 375m; *_750 = M-band."""
    s = str(sensor or "")
    if s.startswith("MODIS"):
        return "MODIS"
    if s.startswith("VIIRS"):
        return "VIIRS750" if s.endswith("750") else "VIIRS375"
    return "otro"


BINS = [(0, 15), (15, 25), (25, 35), (35, 50), (50, 90)]


def _resumen(vals):
    a = np.asarray(vals, dtype=float)
    conteo = {}
    for lo, hi in BINS:
        conteo["%d-%d" % (lo, hi)] = int(((a >= lo) & (a < hi)).sum())
    return {
        "n": int(a.size),
        "cenital_q1": round(float(np.percentile(a, 25)), 2),
        "cenital_mediana": round(float(np.median(a)), 2),
        "cenital_q3": round(float(np.percentile(a, 75)), 2),
        "cenital_max": round(float(a.max()), 2),
        "n_por_bin": conteo,
        "frac_50_mas": round(float((a >= 50).mean()), 4),
    }


def sustrato_de_dato():
    """Distribucion del cenital del sensor en el corpus persistido."""
    por_sensor = {}
    por_volcan = {}
    fechas = []
    _con_mes = {}
    _sin_mes = {}
    n_total = 0
    n_sin_zenith = 0
    for ruta in sorted(glob.glob(os.path.join(REPO, "data", "mirova_equivalent",
                                              "*.json"))):
        volcan = os.path.splitext(os.path.basename(ruta))[0]
        with open(ruta, encoding="utf-8") as fh:
            doc = json.load(fh)
        recs = doc["records"] if isinstance(doc, dict) and "records" in doc else doc
        if not isinstance(recs, list):
            continue
        for r in recs:
            if not isinstance(r, dict):
                continue
            n_total += 1
            b = _bucket_sensor(r.get("sensor"))
            ts = (r.get("datetime_utc") or r.get("timestamp_utc")
                  or r.get("datetime") or r.get("date"))
            mes = str(ts)[:7] if ts else ""
            if ts:
                fechas.append(str(ts)[:10])
            z = r.get("sensor_zenith_deg")
            if z is None:
                _sin_mes[mes] = _sin_mes.get(mes, 0) + 1
            else:
                _con_mes[mes] = _con_mes.get(mes, 0) + 1
            try:
                z = abs(float(z))
            except (TypeError, ValueError):
                n_sin_zenith += 1
                continue
            if not np.isfinite(z):
                n_sin_zenith += 1
                continue
            por_sensor.setdefault(b, []).append(z)
            por_volcan.setdefault((volcan, b), []).append(z)

    # Cobertura del campo por mes. POR QUE: el cenital no esta en todo el corpus, y
    # los porcentajes de arriba corren sobre el subconjunto que SI lo tiene. Declarar
    # cual es ese subconjunto es la diferencia entre un dato y un dato enganoso (A90).
    cobertura = {}
    for mes in sorted(set(list(_con_mes.keys()) + list(_sin_mes.keys()))):
        if not mes:
            continue
        c, s = _con_mes.get(mes, 0), _sin_mes.get(mes, 0)
        cobertura[mes] = {"con_cenital": c, "sin_cenital": s,
                          "cobertura": round(c / (c + s), 4) if (c + s) else None}

    salida_sensor = {k: _resumen(v) for k, v in sorted(por_sensor.items())}
    salida_volcan = {}
    for (vol, b), v in sorted(por_volcan.items()):
        if b in ("VIIRS375", "VIIRS750") and len(v) >= 30:
            salida_volcan.setdefault(b, {})[vol] = _resumen(v)

    return {
        "ventana_temporal": {
            "primera_fecha": min(fechas) if fechas else None,
            "ultima_fecha": max(fechas) if fechas else None,
        },
        "denominador_records_totales": n_total,
        "records_sin_cenital_persistido": n_sin_zenith,
        "por_sensor": salida_sensor,
        "por_volcan": salida_volcan,
        "cobertura_del_campo_por_mes": cobertura,
        "nota_denominador": (
            "S131 midio 2.773 PARES contra MIROVA (1.147 en el bin 50+). Aca el "
            "denominador son RECORDS persistidos de todos los volcanes con JSON, "
            "no pares. A90."),
    }


def main():
    res = {
        "sesion": "S133",
        "proposito": ("sustrato del A/B del area geolocalizada, decision #5 de "
                      "AUDIT_S131 §4"),
        "sustrato_de_codigo": sustrato_de_codigo(),
        "sustrato_de_dato": sustrato_de_dato(),
    }
    destino = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           "sustrato_area_geolocalizada.json")
    with open(destino, "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2, ensure_ascii=False)

    sc = res["sustrato_de_codigo"]
    print("=== SUSTRATO DE CODIGO ===")
    print("definicion del flag:", sc["definicion_del_flag"])
    print("consumidores en produccion:", sc["consumidores_del_flag_en_produccion"])
    print("llamadas a la funcion:", sc["llamadas_a_la_funcion_en_produccion"])
    print("brazo 'area' identico al control:",
          sc["el_brazo_area_seria_identico_al_control"])
    print()
    sd = res["sustrato_de_dato"]
    print("=== SUSTRATO DE DATO ===")
    print("ventana:", sd["ventana_temporal"], "| records:",
          sd["denominador_records_totales"], "| sin cenital:",
          sd["records_sin_cenital_persistido"])
    for k, v in sd["por_sensor"].items():
        print("  %-9s n=%6d  mediana=%5.1f  frac>=50=%.3f  bins=%s"
              % (k, v["n"], v["cenital_mediana"], v["frac_50_mas"], v["n_por_bin"]))
    print()
    print("JSON:", destino)


if __name__ == "__main__":
    main()
