# -*- coding: utf-8 -*-
"""S164 MOD-D fase 3: mutaciones sobre lo nuevo de la vía «código MIROVA» para MODIS, con control de caída.

POR QUÉ. Una prueba verde no dice que vigile algo: hay que romper el código a propósito y ver que alguna prueba lo
note. Y una mutación que hace CAER una prueba con una excepción (TypeError, KeyError) no cuenta como atrapada: la prueba
se cayó, no comprobó nada (S152, S156). Por eso cada mutación se clasifica por el tipo de falla que produce:
  atrapada  al menos una prueba falla por una aserción (AssertionError);
  caida     sólo fallan pruebas por excepciones que no son aserciones;
  viva      todo pasa.
Controles del instrumento: (a) sin mutación todo pasa; (b) una mutación que sólo levanta una excepción tiene que salir
«caida», no «atrapada» (si saliera atrapada, el clasificador cuenta caídas como aciertos).

Uso (árbol quieto, nada más corriendo sobre el repo, A112):
    python experiments/_s164_modis_codigo/mutaciones.py > experiments/_s164_modis_codigo/mutaciones_salida.txt
"""
from __future__ import annotations

import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MOD = "pipeline/mirova_v750_codigo.py"
PM = "pipeline/process_modis.py"
PRUEBAS = ["tests/test_mirova_modis_codigo_s164.py", "tests/test_mirova_v750_codigo_s162.py",
           "tests/test_mirova_v750_cableado_s162.py"]

# (nombre, archivo, texto original, texto mutado, esperado)
MUTACIONES = [
    ("control_sin_mutacion", None, None, None, "viva"),
    ("control_caida", MOD, '    """Distancia en km (R = 6371)',
     '    raise RuntimeError("control de caida")\n    """Distancia en km (R = 6371)', "caida"),
    ("lam_mir_modis_m13", MOD, '"lam_mir": LAMBDA_MODIS_B22,', '"lam_mir": LAMBDA_M13,', "atrapada"),
    ("lam_tir_modis_m15", MOD, '"lam_tir": LAMBDA_MODIS_B31,', '"lam_tir": LAMBDA_M15,', "atrapada"),
    ("coef_modis_area_v750", MOD, "COEF_VRP_MODIS = 1.89e7 * 1.0 / 1e6", "COEF_VRP_MODIS = 1.89e7 * 0.5625 / 1e6",
     "atrapada"),
    ("lado_sensible_7", MOD, '"lado_sensible": 5, "lado_anillo": 15,', '"lado_sensible": 7, "lado_anillo": 15,',
     "atrapada"),
    ("lado_anillo_21", MOD, '"lado_sensible": 5, "lado_anillo": 15,', '"lado_sensible": 5, "lado_anillo": 21,',
     "atrapada"),
    ("paso_750", MOD, "PASO_MODIS_M = 1000.0", "PASO_MODIS_M = 750.0", "atrapada"),
    ("sin_corte_5_km", MOD, '              "dist_max_centro_km": 5.0},', '              "dist_max_centro_km": None},',
     "atrapada"),
    ("corte_5_km_ignorado", MOD, 'if cfg["dist_max_centro_km"] is not None and dist[i0] > cfg["dist_max_centro_km"]:',
     'if False:', "atrapada"),
    ("b21_primaria", MOD, 'return {"MIR": merge_mir_bands(b21, b22, True), "TIR": b31}',
     'return {"MIR": merge_mir_bands(b21, b22, False), "TIR": b31}', "atrapada"),
    ("tir_es_b21", MOD, 'return {"MIR": merge_mir_bands(b21, b22, True), "TIR": b31}',
     'return {"MIR": merge_mir_bands(b21, b22, True), "TIR": b21}', "atrapada"),
    ("geo_sin_enmascarar_lat", MOD, "    lat[(lat < -90) | (lat > 90)] = np.nan\n", "", "atrapada"),
    ("geo_sin_escala_angulos", MOD, '        ang[k] = s.get().astype(np.float64) * float(s.attributes().get("scale_factor", 1.0))',
     '        ang[k] = s.get().astype(np.float64)', "atrapada"),
    ("lam_fija_m13_en_record", MOD, '    lam = cfg["lam_mir"]\n', '    lam = LAMBDA_M13\n', "atrapada"),
    ("lam_tir_fija_en_detector", MOD, "    bt15 = radiancia_a_temperatura(m15, lam_tir)", "    bt15 = radiancia_a_temperatura(m15, LAMBDA_M15)",
     "atrapada"),
    ("lam_mir_fija_en_pasada", MOD, "    m13_esp = temperatura_a_radiancia(bt15, lam_mir)",
     "    m13_esp = temperatura_a_radiancia(bt15, LAMBDA_M13)", "atrapada"),
    ("caja_con_lados_v750", MOD, '                   lado_sensible=cfg["lado_sensible"], lado_anillo=cfg["lado_anillo"], paso_m=g["paso"])',
     '                   paso_m=g["paso"])', "atrapada"),
    ("bandas_m13_m15", MOD, '"bandas": ("MIR", "TIR"),', '"bandas": ("M13", "M15"),', "atrapada"),
    ("roi_de_v750", MOD, '"clave_roi": "roi_modis",', '"clave_roi": "roi_v750",', "equivalente"),
    ("pm_familia_v750", PM, 'inner_radius_km, _sensor_modis(hdf_path.name), familia="MODIS")',
     'inner_radius_km, _sensor_modis(hdf_path.name), familia="VIIRS750")', "atrapada"),
    ("pm_sin_marca_sin_grilla", PM, '            _via_marca = "sin_grilla"', '            _via_marca = None', "atrapada"),
    ("pm_sin_control_mxd03", PM, "        elif geo_path is None:", "        elif False:", "atrapada"),
    ("pm_sin_control_forma", PM, '            if np.shape(_lat) != np.shape(_rad["MIR"]):', "            if False:", "atrapada"),
    ("pm_marca_no_se_escribe", PM, '        **({"via_codigo_mirova": _via_marca} if _via_marca is not None else {}),',
     "        **({}),", "atrapada"),
    ("pm_sin_fecha", PM, '                             "datetime_utc": _parse_datetime(hdf_path.name)})',
     "                             })", "atrapada"),
    ("pm_flag_ignorado", PM, "    if ENABLE_MODIS_CODIGO_MIROVA:\n", "    if True:\n", "atrapada"),
    ("pm_vent_ignorado", PM, "                    vent_lat if vent_lat is not None else volcano_lat,\n",
     "                    volcano_lat,\n", "atrapada"),
    # las cinco que el verificador S164 encontró vivas (V164-06), agregadas tras reforzar las pruebas
    ("remuestreo_nearest", MOD, 'v[ok], (X, Y), method="linear"))', 'v[ok], (X, Y), method="nearest"))', "atrapada"),
    ("radio_recorte_30_km", MOD, "RADIO_RECORTE_KM = 45.0 ", "RADIO_RECORTE_KM = 30.0 ", "atrapada"),
    ("sunglint_sin_azimut", MOD, '                      geom.get("sensor_azimuth", 0.0), geom.get("solar_azimuth", 0.0))',
     "                      0.0, 0.0)", "atrapada"),
    ("distance_class_siempre_summit", MOD, '("summit" if dcen <= inner_km else "far")', '"summit"', "atrapada"),
    # la vía devuelve None (volcán fuera del gránulo) y en vez de terminar ahí el procesador sigue a K
    ("pm_via_none_cae_a_k_en_silencio", PM,
     '                if _rec is None:\n                    return None\n                _rec.update({"granule": hdf_path.name,\n'
     '                             "product_version": product_version_from_granule(hdf_path.name),\n'
     '                             "datetime_utc": _parse_datetime(hdf_path.name)})\n                return _rec\n',
     '                if _rec is not None:\n                    _rec.update({"granule": hdf_path.name})\n'
     '                    return _rec\n', "atrapada"),
]


def correr(nombre):
    xml = REPO / f"experiments/_s164_modis_codigo/_junit_{nombre}.xml"
    env = dict(os.environ, PYTHONIOENCODING="utf-8", VRP_PROFILE="mirova_equivalent")
    subprocess.run([sys.executable, "-m", "pytest", *PRUEBAS, "-q", "-p", "no:cacheprovider", f"--junitxml={xml}"],
                   cwd=REPO, env=env, capture_output=True, text=True, encoding="utf-8")
    raiz = ET.parse(xml).getroot()
    xml.unlink()
    aserciones, excepciones = [], []
    for caso in raiz.iter("testcase"):
        for f in list(caso.findall("failure")) + list(caso.findall("error")):
            msg = (f.get("message") or "")
            quien = f"{caso.get('name')}: {msg[:110]!r}"
            (aserciones if msg.startswith(("AssertionError", "assert")) else excepciones).append(quien)
    if aserciones:
        return "atrapada", aserciones, excepciones
    return ("caida" if excepciones else "viva"), aserciones, excepciones


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    originales = {a: (REPO / a).read_bytes() for a in (MOD, PM)}
    resumen = []
    try:
        for nombre, arch, a, b, esperado in MUTACIONES:
            if arch is not None:
                # V164-03: con core.autocrlf=true el checkout trae CRLF; se muta sobre LF y se vuelve al final original
                s = originales[arch].decode("utf-8")
                crlf = "\r\n" in s
                s = s.replace("\r\n", "\n")
                assert s.count(a) == 1, f"{nombre}: el texto original aparece {s.count(a)} veces"
                s = s.replace(a, b)
                (REPO / arch).write_bytes((s.replace("\n", "\r\n") if crlf else s).encode("utf-8"))
            try:
                clase, asc, exc = correr(nombre)
            finally:
                for k, v in originales.items():
                    (REPO / k).write_bytes(v)
            ok = clase == esperado or (esperado == "equivalente" and clase == "viva")
            resumen.append((nombre, esperado, clase, ok))
            print(f"{nombre:28s} esperado={esperado:11s} resultado={clase:9s} {'OK' if ok else 'NO'}", flush=True)
            for q in (asc[:2] + exc[:2]):
                print("    ", q, flush=True)
    finally:
        for k, v in originales.items():
            (REPO / k).write_bytes(v)
    reales = [r for r in resumen if r[1] == "atrapada"]
    print(f"\nmutaciones reales atrapadas por aserción: {sum(r[2] == 'atrapada' for r in reales)} de {len(reales)}")
    print(f"controles: sin mutación {resumen[0][2]}, caída {resumen[1][2]}")
    print("todo como se esperaba" if all(r[3] for r in resumen) else "HAY DIFERENCIAS CON LO ESPERADO")


if __name__ == "__main__":
    main()
