# -*- coding: utf-8 -*-
"""S165 V375-E: mutaciones sobre lo nuevo de la vía «código MIROVA» para VIIRS 375, con control de caída.

POR QUÉ. Una prueba verde no dice que vigile algo: hay que romper el código a propósito y ver que alguna prueba lo
note. Y una mutación que hace CAER una prueba con una excepción (TypeError, KeyError) no cuenta como atrapada: la prueba
se cayó, no comprobó nada (S152, S156). Cada mutación se clasifica por el tipo de falla que produce:
  atrapada  al menos una prueba falla por una aserción (AssertionError);
  caida     sólo fallan pruebas por excepciones que no son aserciones;
  viva      todo pasa.
Controles del instrumento: (a) sin mutación todo pasa; (b) una mutación que sólo levanta una excepción tiene que salir
«caida», no «atrapada». Es la batería de experiments/_s164_modis_codigo/mutaciones.py (#919) con una diferencia: muta
una COPIA del árbol en una carpeta aparte, no el worktree, para no tocar archivos que otro proceso esté leyendo (A112).

Uso: python experiments/_s165_v375_via/mutaciones_v375.py <carpeta_vacia_para_la_copia>
     > experiments/_s165_v375_via/mutaciones_v375_salida.txt
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
MOD = "pipeline/mirova_v750_codigo.py"
PV = "pipeline/process_viirs.py"
ST = "pipeline/store.py"
RP = "scripts/run_pipeline.py"
PF = "pipeline/profile.py"
PRUEBAS = ["tests/test_mirova_v375_codigo_s165.py", "tests/test_mirova_v750_codigo_s162.py",
           "tests/test_mirova_v750_cableado_s162.py", "tests/test_mirova_modis_codigo_s164.py",
           "tests/test_f5_core_python_s132.py"]
COPIAR = ["pipeline", "tests", "scripts", "frontend", "volcanoes.yaml", "pytest.ini", "experiments/_s162_v375",
          "experiments/_s159/portes", "experiments/_s158_audit_r2/oraculo",
          # datos que leen dos pruebas vecinas (paridad F5 con el JavaScript, Etna del OSF); sin ellos el control sin
          # mutación sale «atrapada» y la batería no vale (primera corrida, 2026-10-27)
          "data/mirova_equivalent", "experiments/_s158_d17_diseno/osf_codigo_mirova"]

# (nombre, archivo, texto original, texto mutado, esperado)
MUTACIONES = [
    ("control_sin_mutacion", None, None, None, "viva"),
    ("control_caida", MOD, '    """Distancia en km (R = 6371)',
     '    raise RuntimeError("control de caida")\n    """Distancia en km (R = 6371)', "caida"),
    # números de 375
    ("lam_mir_375_es_m13", MOD, '"lam_mir": LAMBDA_I4,', '"lam_mir": LAMBDA_M13,', "atrapada"),
    ("lam_tir_375_es_m15", MOD, '"lam_tir": LAMBDA_I5,', '"lam_tir": LAMBDA_M15,', "atrapada"),
    ("coef_375_area_750", MOD, "COEF_VRP_V375 = 1.80e7 * 0.140625 / 1e6", "COEF_VRP_V375 = 1.80e7 * 0.5625 / 1e6",
     "atrapada"),
    ("coef_375_wooster_750", MOD, "COEF_VRP_V375 = 1.80e7 * 0.140625 / 1e6", "COEF_VRP_V375 = 1.97e7 * 0.140625 / 1e6",
     "atrapada"),
    ("paso_750", MOD, "PASO_V375_M = 375.0", "PASO_V375_M = 750.0", "atrapada"),
    ("bandas_m13_m15", MOD, '"bandas": ("I04", "I05"),', '"bandas": ("M13", "M15"),', "atrapada"),
    ("sin_corte_5_km", MOD, '"dist_max_centro_km": 5.0, "roi1_half_m"', '"dist_max_centro_km": None, "roi1_half_m"',
     "atrapada"),
    # la caja C13
    ("lado_sensible_15", MOD, '"lado_sensible": 13, "lado_anillo": None,', '"lado_sensible": 15, "lado_anillo": None,',
     "atrapada"),
    ("roi1_14_celdas", MOD, "HALF_ROI1_V375_M = 10.5 * 750.0", "HALF_ROI1_V375_M = 3.5 * 750.0", "atrapada"),
    ("sin_roi1", MOD, "    b[np.ix_(en_y, en_x)] = 1\n", "", "atrapada"),
    ("c13_en_el_centro_de_la_grilla", MOD, "    i0, j0 = int(np.argmin(np.abs(ys - yc))), int(np.argmin(np.abs(xs - xc)))",
     '    i0, j0 = int(np.argmin(np.abs(ys - grilla["y0"]))), int(np.argmin(np.abs(xs - grilla["x0"])))', "atrapada"),
    ("c13_por_piso_de_celda", MOD, "    i0, j0 = int(np.argmin(np.abs(ys - yc))), int(np.argmin(np.abs(xs - xc)))",
     '    i0, j0 = int((grilla["ul_y"] - yc) // paso), int((xc - grilla["ul_x"]) // paso)', "equivalente"),
    ("c13_sin_recorte_al_borde", MOD, "    b[max(i0 - h, 0):i0 + h + 1, max(j0 - h, 0):j0 + h + 1] = 2",
     "    b[i0 - h:i0 + h + 1, j0 - h:j0 + h + 1] = 2", "equivalente"),
    ("375_usa_caja_roi", MOD, '    if cfg.get("roi1_half_m") is not None:', "    if False:", "caida"),
    # lectura
    ("leer_default_i", MOD, 'def leer_radiancia_l1b(ruta, bandas=("M13", "M15")):',
     'def leer_radiancia_l1b(ruta, bandas=("I04", "I05")):', "atrapada"),
    ("leer_ignora_bandas", MOD, "        for b in bandas:\n", '        for b in ("M13", "M15"):\n', "atrapada"),
    # procesador de 375
    ("pv_flag_ignorado", PV, "    if ENABLE_V375_CODIGO_MIROVA:\n", "    if True:\n", "atrapada"),
    ("pv_familia_750", PV, 'inner_radius_km, _sensor_label_from_filename(l1b_path.name), familia="VIIRS375")',
     'inner_radius_km, _sensor_label_from_filename(l1b_path.name), familia="VIIRS750")', "atrapada"),
    ("pv_bandas_por_defecto", PV, "_MV.leer_radiancia_l1b(l1b_path, bandas=_fam[\"bandas\"])",
     "_MV.leer_radiancia_l1b(l1b_path)", "atrapada"),
    ("pv_sin_marca_sin_grilla", PV, "        _via_sin_grilla = True\n", "", "atrapada"),
    ("pv_marca_no_se_escribe", PV, '        record["via_codigo_mirova"] = "sin_grilla"', "        pass", "atrapada"),
    ("pv_sin_fecha", PV, '                         "datetime_utc": _parse_datetime(l1b_path.name)})',
     "                         })", "atrapada"),
    ("pv_vent_ignorado", PV, "                vent_lat if vent_lat is not None else volcano_lat,\n",
     "                volcano_lat,\n", "atrapada"),
    ("pv_via_none_no_devuelve_none", PV, "            if _rec is None:\n                return None\n            _rec.update(",
     "            if _rec is None:\n                _rec = {}\n            _rec.update(", "atrapada"),
    # almacén, log y perfil
    ("st_nucleo_f5_para_la_via", ST, 'es_viirs_iband(record.get("sensor")) and not _via_mirova:',
     'es_viirs_iband(record.get("sensor")):', "atrapada"),
    ("st_nucleo_f5_para_nadie", ST,
     'if inner_radius_km is not None and es_viirs_iband(record.get("sensor")) and not _via_mirova:', "if False:",
     "atrapada"),
    ("rp_log_con_corchetes", RP, "VRP_MIR={result.get('vrp_mir_mw')}", "VRP_MIR={result['vrp_mir_mw']}", "atrapada"),
    ("pf_flag_encendido_por_defecto", PF, '_t.get("enable_v375_codigo_mirova", False))',
     '_t.get("enable_v375_codigo_mirova", True))', "atrapada"),
]


def correr(raiz, nombre):
    xml = raiz / f"_junit_{nombre}.xml"
    env = dict(os.environ, PYTHONIOENCODING="utf-8", VRP_PROFILE="mirova_equivalent")
    env.pop("PYTHONPATH", None)
    subprocess.run([sys.executable, "-m", "pytest", *PRUEBAS, "-q", "-p", "no:cacheprovider", f"--junitxml={xml}"],
                   cwd=raiz, env=env, capture_output=True, text=True, encoding="utf-8")
    arbol = ET.parse(xml).getroot()
    xml.unlink()
    aserciones, excepciones = [], []
    for caso in arbol.iter("testcase"):
        for f in list(caso.findall("failure")) + list(caso.findall("error")):
            msg = (f.get("message") or "")
            quien = f"{caso.get('name')}: {msg[:110]!r}"
            (aserciones if msg.startswith(("AssertionError", "assert")) else excepciones).append(quien)
    if aserciones:
        return "atrapada", aserciones, excepciones
    return ("caida" if excepciones else "viva"), aserciones, excepciones


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    raiz = Path(sys.argv[1]).resolve()
    assert not raiz.exists() or not any(raiz.iterdir()), f"{raiz} no está vacía"
    for p in COPIAR:
        o, d = REPO / p, raiz / p
        d.parent.mkdir(parents=True, exist_ok=True)
        if o.is_dir():
            shutil.copytree(o, d, ignore=shutil.ignore_patterns("__pycache__", "cache_brazos.json"))
        else:
            shutil.copyfile(o, d)
    print("copia en", raiz, "(el worktree no se toca)")
    archivos = {m[1] for m in MUTACIONES if m[1]}
    originales = {a: (raiz / a).read_bytes() for a in archivos}
    resumen = []
    try:
        for nombre, arch, a, b, esperado in MUTACIONES:
            if arch is not None:
                s = originales[arch].decode("utf-8")
                crlf = "\r\n" in s
                s = s.replace("\r\n", "\n")
                assert s.count(a) == 1, f"{nombre}: el texto original aparece {s.count(a)} veces"
                s = s.replace(a, b)
                (raiz / arch).write_bytes((s.replace("\n", "\r\n") if crlf else s).encode("utf-8"))
            try:
                clase, asc, exc = correr(raiz, nombre)
            finally:
                for k, v in originales.items():
                    (raiz / k).write_bytes(v)
            ok = clase == esperado or (esperado == "equivalente" and clase == "viva")
            resumen.append((nombre, esperado, clase, ok))
            print(f"{nombre:32s} esperado={esperado:11s} resultado={clase:9s} {'OK' if ok else 'NO'}", flush=True)
            for q in (asc[:2] + exc[:2]):
                print("    ", q, flush=True)
    finally:
        for k, v in originales.items():
            (raiz / k).write_bytes(v)
    reales = [r for r in resumen if r[1] == "atrapada"]
    print(f"\nmutaciones reales atrapadas por aserción: {sum(r[2] == 'atrapada' for r in reales)} de {len(reales)}")
    print(f"controles: sin mutación {resumen[0][2]}, caída {resumen[1][2]}")
    print("todo como se esperaba" if all(r[3] for r in resumen) else "HAY DIFERENCIAS CON LO ESPERADO")


if __name__ == "__main__":
    main()
