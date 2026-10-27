# -*- coding: utf-8 -*-
"""S165: mutaciones sobre los tres flags MxD03 de MODIS, con control de caída (patrón de
experiments/_s164_modis_codigo/mutaciones.py).

POR QUÉ. Una prueba verde no dice que vigile algo: hay que romper el código a propósito y ver que alguna prueba lo
note. Una mutación que hace CAER una prueba con una excepción no cuenta como atrapada (S152, S156):
  atrapada  al menos una prueba falla por una aserción (AssertionError);
  caida     sólo fallan pruebas por excepciones que no son aserciones;
  viva      todo pasa.
Controles del instrumento: (a) sin mutación todo pasa; (b) una mutación que sólo levanta una excepción sale «caida»,
no «atrapada». Para que (b) sea posible, los arneses en subproceso levantan RuntimeError (no assert) cuando el
subproceso muere.

Uso (árbol quieto, nada más corriendo sobre el repo, A112):
    python experiments/_s165_mxd03_flag/mutaciones.py > experiments/_s165_mxd03_flag/mutaciones_salida.txt
"""
from __future__ import annotations

import os
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
PM = "pipeline/process_modis.py"
PR = "pipeline/profile.py"
YA = "pipeline/profiles/mirova_equivalent.yaml"
PRUEBAS = ["tests/test_modis_geo_mxd03_s165.py", "tests/test_guard_mxd03_flags_s165.py",
           "tests/test_mirova_modis_codigo_s164.py"]

# (nombre, archivo, texto original, texto mutado, esperado)
MUTACIONES = [
    ("control_sin_mutacion", None, None, None, "viva"),
    ("control_caida", PM, '    d = haversine_km(vent_lat, vent_lon, lat, lon)\n    if not np.isfinite(d).any():',
     '    raise RuntimeError("control de caida")\n    d = haversine_km(vent_lat, vent_lon, lat, lon)\n'
     '    if not np.isfinite(d).any():', "caida"),
    # Tarea 1: flags
    ("perfil_lee_la_raiz", PR, 'bool(_t.get("enable_modis_geo_mxd03", False))',
     'bool(_cfg.get("enable_modis_geo_mxd03", False))', "atrapada"),
    ("yaml_geo_encendido", YA, "  enable_modis_geo_mxd03: false ", "  enable_modis_geo_mxd03: true  ", "atrapada"),
    ("yaml_dist_encendido", YA, "  enable_modis_dist_desde_crater: false ", "  enable_modis_dist_desde_crater: true  ",
     "atrapada"),
    # Tarea 2: posición
    ("lector_lat_lon_cruzados", PM, "    lat, lon, _ang = _MV.leer_geo_mxd03(geo_path)\n    return lat, lon\n",
     "    lat, lon, _ang = _MV.leer_geo_mxd03(geo_path)\n    return lon, lat\n", "atrapada"),
    ("geo_flag_ignorado", PM, '    if not ENABLE_MODIS_GEO_MXD03:\n        return data["lat"], data["lon"], "interp_5km"',
     '    if True:\n        return data["lat"], data["lon"], "interp_5km"', "atrapada"),
    ("geo_siempre_encendido", PM, '    if not ENABLE_MODIS_GEO_MXD03:\n        return data["lat"], data["lon"], "interp_5km"',
     '    if False:\n        return data["lat"], data["lon"], "interp_5km"', "atrapada"),
    ("geo_sin_control_forma", PM,
     '    if np.shape(lat_m) != np.shape(data["lat"]) or np.shape(lon_m) != np.shape(data["lon"]):',
     "    if False:", "atrapada"),
    ("geo_ilegible_sin_marca", PM, '        return data["lat"], data["lon"], "interp_5km_mxd03_ilegible"',
     '        return data["lat"], data["lon"], "interp_5km"', "atrapada"),
    ("geo_fuente_no_se_escribe", PM, '        **({"geo_fuente": geo_fuente} if ENABLE_MODIS_GEO_MXD03 else {}),',
     "        **({}),", "atrapada"),
    ("geo_fuente_siempre", PM, '        **({"geo_fuente": geo_fuente} if ENABLE_MODIS_GEO_MXD03 else {}),',
     '        **({"geo_fuente": geo_fuente}),', "atrapada"),
    ("geo_no_se_usa", PM, "    lat, lon, geo_fuente = posicion_de_calculo(data, geo_path)\n",
     '    _x, _y, geo_fuente = posicion_de_calculo(data, geo_path)\n    lat, lon = data["lat"], data["lon"]\n',
     "atrapada"),
    # Tarea 3: sin dato
    ("sin_dato_flag_ignorado", PM, '    if not (ENABLE_MODIS_CRATER_SIN_DATO and geo_fuente == "mxd03"):',
     '    if not (geo_fuente == "mxd03"):', "atrapada"),
    ("sin_dato_con_interpolada", PM, '    if not (ENABLE_MODIS_CRATER_SIN_DATO and geo_fuente == "mxd03"):',
     "    if not (ENABLE_MODIS_CRATER_SIN_DATO):", "atrapada"),
    ("sin_dato_no_corta", PM,
     '        print(f"  MODIS {hdf_path.name}: crater sin posicion en el granulo (sin dato, no se escribe record)")\n'
     "        return None\n",
     '        print(f"  MODIS {hdf_path.name}: crater sin posicion en el granulo (sin dato, no se escribe record)")\n',
     "atrapada"),
    ("sin_dato_ancla_en_el_centro", PM,
     "    _ancla_lat, _ancla_lon = (vent_lat, vent_lon) if vent_lat is not None and vent_lon is not None \\\n"
     "        else (volcano_lat, volcano_lon)\n",
     "    _ancla_lat, _ancla_lon = (volcano_lat, volcano_lon)\n", "atrapada"),
    ("borde_ignorado", PM, "    if i in (0, n_l - 1) or j in (0, n_f - 1):\n        return False\n",
     "    if False:\n        return False\n", "atrapada"),
    ("solo_ultima_linea", PM, "    if i in (0, n_l - 1) or j in (0, n_f - 1):", "    if i == n_l - 1:", "atrapada"),
    ("vecinos_ignorados", PM,
     "    return bool(np.isfinite(lat[i - 1:i + 2, j - 1:j + 2]).all() and np.isfinite(lon[i - 1:i + 2, j - 1:j + 2]).all())",
     "    return True", "atrapada"),
    # Tarea 5: distancia
    ("dist_flag_ignorado", PM, "    return vent_dist_per_pixel if ENABLE_MODIS_DIST_DESDE_CRATER else dist",
     "    return dist", "atrapada"),
    ("dist_siempre_desde_crater", PM, "    return vent_dist_per_pixel if ENABLE_MODIS_DIST_DESDE_CRATER else dist",
     "    return vent_dist_per_pixel", "atrapada"),
    ("dist_no_llega_al_pixel", PM, '                "dist_km": round(float(dist_etiqueta[r, c]), 2),',
     '                "dist_km": round(float(dist[r, c]), 2),', "atrapada"),
    ("anillo_desde_el_crater", PM, "    bg_mask = (dist >= BG_INNER_KM) & (dist <= BG_OUTER_KM)",
     "    bg_mask = (dist_etiqueta >= BG_INNER_KM) & (dist_etiqueta <= BG_OUTER_KM)", "atrapada"),
    # Camino del Test 1 integrado: apagado en producción desde K (D30); ninguna prueba lo ejerce. Se declara.
    ("dist_no_llega_al_test1", PM, "build_anomaly_pixels(t1_vrp_2d, lat, lon, dist_etiqueta, bt_mir)",
     "build_anomaly_pixels(t1_vrp_2d, lat, lon, dist, bt_mir)", "no_cubierta"),
]


def correr(nombre):
    xml = REPO / f"experiments/_s165_mxd03_flag/_junit_{nombre}.xml"
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
    originales = {a: (REPO / a).read_bytes() for a in (PM, PR, YA)}
    resumen = []
    try:
        for nombre, arch, a, b, esperado in MUTACIONES:
            if arch is not None:
                # con core.autocrlf=true el checkout trae CRLF; se muta sobre LF y se vuelve al final original (V164-03)
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
            ok = clase == esperado or (esperado == "no_cubierta" and clase == "viva")
            resumen.append((nombre, esperado, clase, ok))
            print(f"{nombre:30s} esperado={esperado:11s} resultado={clase:9s} {'OK' if ok else 'NO'}", flush=True)
            for q in (asc[:2] + exc[:2]):
                print("    ", q, flush=True)
    finally:
        for k, v in originales.items():
            (REPO / k).write_bytes(v)
    reales = [r for r in resumen if r[1] == "atrapada"]
    print(f"\nmutaciones reales atrapadas por aserción: {sum(r[2] == 'atrapada' for r in reales)} de {len(reales)}")
    print(f"controles: sin mutación {resumen[0][2]}, caída {resumen[1][2]}")
    print(f"declaradas no cubiertas: {[r[0] for r in resumen if r[1] == 'no_cubierta']}")
    print("todo como se esperaba" if all(r[3] for r in resumen) else "HAY DIFERENCIAS CON LO ESPERADO")


if __name__ == "__main__":
    main()
