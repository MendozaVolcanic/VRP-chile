# -*- coding: utf-8 -*-
"""Mutaciones del evaluador de MOD-D, con control de caída (S156). Cada mutación es un cambio de texto sobre una copia
de evaluar_paquete.py que rompe UNA regla sellada; la batería probar_evaluar_paquete.py tiene que atraparla con al
menos una prueba que FALLE POR ASERCIÓN. Una mutación que hace caer las pruebas (excepción) no cuenta como atrapada: se
informa aparte. Una mutacion puede llevar varias sustituciones (lista de pares). Control de identidad: la copia sin mutar tiene que pasar todas las pruebas (si no, la copia misma está
rota y nada de lo demás vale). Además, cada sustitución tiene que encontrar su texto exactamente una vez.
Uso: python mutar_evaluar_paquete.py   (sale 1 si alguna mutación queda viva o cae, o si la identidad falla)
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

AQUI = Path(__file__).resolve().parent
FUENTE = AQUI / "evaluar_paquete.py"

MUTACIONES = {
    "p1_mira_bajo1": ('if f["lab"] == "protegida" and _pub(f, "K") == 1 and _pub(f, b) == 0]',
                      'if f["lab"] == "bajo1" and _pub(f, "K") == 1 and _pub(f, b) == 0]'),
    "p2_signo_invertido": ('"c": 1 if eb else -1', '"c": -1 if eb else 1'),
    "error_negativo_al_reves": ('        return _pub(f, b) == 1\n    return False', '        return _pub(f, b) == 0\n    return False'),
    "p2_antes_que_p1": ('    if b["p1"]["estado"] == "VETADO":\n        return "NO CANDIDATO"\n    if b["p2"]["estado"] == "PIERDE":',
                        '    if b["p2"]["estado"] == "GANA":\n        return "CANDIDATO"\n    if b["p2"]["estado"] == "PIERDE":'),
    "m_empeora_no_decide": ('or b["m"]["regla"] == "EMPEORA"', 'or b["m"]["regla"] == "EMPEORA_X"'),
    "p1b_umbral_medio": ('if _mag(f, "K") >= 1.0 > _mag(f, b):', 'if _mag(f, "K") >= 0.5 > _mag(f, b):'),
    "escena_invalida_cuenta": ('    if pf.get("motivo_vacio") == "escena_invalida":\n        return False, "escena_invalida"',
                               '    if pf.get("motivo_vacio") == "escena_x":\n        return False, "escena_invalida"'),
    "placebo_sin_ganancia": ('casos.append((escalar(k, PLACEBO), f["inner"]))', 'casos.append((escalar(k, 1.0), f["inner"]))'),
    "contador_sin_inyectar": ('size=min(N_INYECTAR, len(negs))', 'size=min(0, len(negs))'),
    "chillan_sustrato_4": ("    if n < 5:\n        estado = \"SIN SUSTRATO\"", "    if n < 4:\n        estado = \"SIN SUSTRATO\""),
    "chillan_banda_ancha": ('elif med is not None and 0.8 <= med <= 1.25 and 20 * num <= den:',
                            'elif med is not None and 0.5 <= med <= 2.0:'),
    "soporte_sin_viirs": ('and abs(r["dt"] - t) <= w and (r["b"] != "MODIS" or r.get("sensor") != f["sensor"])]',
                          'and abs(r["dt"] - t) <= w and r["b"] == "MODIS" and r.get("sensor") != f["sensor"]]'),
    "s159_tolerancia_floja": ("TOL_PORT_S159 = 1e-6", "TOL_PORT_S159 = 1.0"),
    "k_ignora_predicado": ("    if distinto:\n        c = dict(c, estado=\"INDECIDIBLE\")", "    if False:\n        c = dict(c, estado=\"INDECIDIBLE\")"),
    # sin_info sale de P2 por DOS filtros independientes (la lista de clases de contribuciones_p2 y la definicion de
    # _error). Romper uno solo es una mutacion equivalente (medido: las dos quedaron vivas por separado en la primera
    # corrida, mutar_evaluar_paquete_salida_v1.txt); la que importa es la que rompe los dos a la vez.
    "sin_info_entra_y_cuenta": [
        ('        if f["lab"] not in ("bajo1", "neg_limpio"):\n            continue\n        ek, eb',
         '        if f["lab"] not in ("bajo1", "neg_limpio", "sin_info"):\n            continue\n        ek, eb'),
        ('    if f["lab"] == "neg_limpio":\n        return _pub(f, b) == 1',
         '    if f["lab"] in ("neg_limpio", "sin_info"):\n        return _pub(f, b) == 1')],
    "cobertura_sin_duplicados": ('estado = "OK" if c["estado"] == "OK" and dup["estado"] == "OK" and not fallas else',
                                 'estado = "OK" if c["estado"] == "OK" and not fallas else'),
    # adenda 4: las del verificador del candado que siguen aplicando (verificador_candado/mutaciones_propias.py) ...
    "bloque_por_pasada": ('    return "%s|%s" % (f["vol"], f.get("noche") or f["dt"][:10])',
                          '    return "%s|%s" % (f["vol"], f["dt"])'),
    "chillan_p_flojo": ("elif med is not None and 0.8 <= med <= 1.25 and 20 * num <= den:",
                        "elif med is not None and 0.8 <= med <= 1.25 and 10 * num <= den:"),
    "p1_sin_mirar_k": ('if f["lab"] == "protegida" and _pub(f, "K") == 1 and _pub(f, b) == 0]',
                       'if f["lab"] == "protegida" and _pub(f, b) == 0]'),
    "error_bajo1_al_reves": ('    if f["lab"] == "bajo1":\n        return _pub(f, b) == 0',
                             '    if f["lab"] == "bajo1":\n        return _pub(f, b) == 1'),
    "chillan_regla4_sin_bajo": (
        "    elif med_bajo is not None and med_sobre is not None and med_sobre < 0.8 and 0.8 <= med_bajo <= 1.25:",
        "    elif med_sobre is not None and med_sobre < 0.8:"),
    "soporte_mismo_modis": ('and abs(r["dt"] - t) <= w and (r["b"] != "MODIS" or r.get("sensor") != f["sensor"])]',
                            'and abs(r["dt"] - t) <= w]'),
    # ... y las de los cambios de la adenda 4
    "falla_del_port_no_roja": ("and dup[\"estado\"] == \"OK\" and not fallas else", "and dup[\"estado\"] == \"OK\" else"),
    "grilla_incompleta_sale": ('    if pf.get("motivo_vacio") == "escena_invalida":\n        return False, "escena_invalida"',
                               '    if pf.get("motivo_vacio") == "escena_invalida" or f.get("port_grilla") == '
                               '"grilla_incompleta":\n        return False, "escena_invalida"'),
    "protegida_fuera_no_decide": ('b["m"]["regla"] == "EMPEORA" or prot_k:', 'b["m"]["regla"] == "EMPEORA":'),
    "protegida_fuera_sin_mirar_k": ('if p.get("k_publica")]', ']'),
    "s159_sin_npix": ('igual = a.get("npix") == r.get("npix") and (', 'igual = True and ('),
    "k33_por_el_runner": ('        if "k33_slim" in f:', '        if False:'),
    "atribucion_vacia": ('"tambien_pierden": [x for x in ("PM-geo5", "PM-sens") if x != b and _pub(f, x) == 0]}',
                         '"tambien_pierden": []}'),
    "borde_no_mira": ('if (f.get("crater_mxd03") or {}).get("borde"):', 'if (f.get("crater_mxd03") or {}).get("bordex"):'),
    "sin_sustrato_no_bloquea": ('    if b["p2"]["estado"] == "SIN SUSTRATO":\n        return "INDECIDIBLE"\n',
                                '    if b["p2"]["estado"] == "SIN SUSTRATO":\n        return "CANDIDATO"\n'),
}


def correr(modulo, salida_json):
    env = dict(os.environ, MODD_RAIZ=str(AQUI.parents[1]), PYTHONIOENCODING="utf-8")
    p = subprocess.run([sys.executable, "-I", str(AQUI / "probar_evaluar_paquete.py"), "--modulo", str(modulo),
                        "--json", str(salida_json)], capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    res = json.loads(Path(salida_json).read_text(encoding="utf-8")) if Path(salida_json).exists() else None
    return res, p.stdout[-600:] + p.stderr[-600:]


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    solo = set(sys.argv[1:])
    src = FUENTE.read_text(encoding="utf-8")
    fallas = []
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        ident = td / "evaluar_paquete.py"
        shutil.copy2(FUENTE, ident)
        shutil.copy2(AQUI / "evaluar_d25_ded217af4.py", td / "evaluar_d25_ded217af4.py")
        shutil.copy2(AQUI / "grillas.json", td / "grillas.json")
        res, log = correr(ident, td / "ident.json")
        n_ok = sum(1 for v in (res or {}).values() if v == "pasa")
        print("identidad (copia sin mutar): pasan %d de %d" % (n_ok, len(res or {})))
        if not res or n_ok != len(res):
            fallas.append("la copia sin mutar no pasa todas: " + log)
        tabla = {}
        for nombre, sust in MUTACIONES.items():
            if solo and nombre not in solo:
                continue
            pares = sust if isinstance(sust, list) else [sust]
            invalida = [v for v, _n in pares if src.count(v) != 1]
            if invalida:
                fallas.append("%s: un texto no aparece exactamente una vez" % nombre)
                tabla[nombre] = "SUSTITUCION INVALIDA"
                continue
            mutado = src
            for viejo, nuevo in pares:
                mutado = mutado.replace(viejo, nuevo)
            mut = td / ("mut_%s" % nombre)
            mut.mkdir()
            for a in ("evaluar_d25_ded217af4.py", "grillas.json"):
                shutil.copy2(AQUI / a, mut / a)
            (mut / "evaluar_paquete.py").write_text(mutado, encoding="utf-8")
            r, log = correr(mut / "evaluar_paquete.py", mut / "r.json")
            if r is None:
                tabla[nombre] = "CAE (sin resultado)"
                continue
            fallan = [k for k, v in r.items() if v == "falla"]
            caen = [k for k, v in r.items() if v == "cae"]
            if fallan:
                tabla[nombre] = "ATRAPADA por %s" % ", ".join(fallan[:3]) + (" (ademas caen %s)" % caen if caen else "")
            elif caen:
                tabla[nombre] = "CAE (%s)" % ", ".join(caen[:3])
            else:
                tabla[nombre] = "VIVA"
        for k, v in tabla.items():
            print("  %-28s %s" % (k, v))
    atr = sum(1 for v in tabla.values() if v.startswith("ATRAPADA"))
    print("mutaciones atrapadas por asercion: %d de %d; caen %d; vivas %d" % (
        atr, len(MUTACIONES), sum(1 for v in tabla.values() if v.startswith("CAE")),
        sum(1 for v in tabla.values() if v == "VIVA")))
    for f in fallas:
        print("FALLA:", f)
    sys.exit(0 if atr == len(MUTACIONES) and not fallas else 1)


if __name__ == "__main__":
    main()
