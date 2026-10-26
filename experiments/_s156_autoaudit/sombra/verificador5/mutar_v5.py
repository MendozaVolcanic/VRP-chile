"""Verificador 5 de S156: corre las mutaciones del autor (y las mias) guardando, por mutacion, el mensaje de
cada <failure> del JUnit, para ver POR QUE el criterio del autor cuenta o no cuenta.
Uso: python mutar_v5.py <copia> <salida.json> [solo_mias] [nobytecode]"""
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

raiz = Path(sys.argv[1])
salida = Path(sys.argv[2])
solo_mias = "solo_mias" in sys.argv[3:]
nobytecode = "nobytecode" in sys.argv[3:]

src = (raiz / "experiments/_s156_autoaudit/sombra/mutar_vigilancia.py").read_text(encoding="utf-8")
cabeza = src.split("\natrapadas = 0", 1)[0]
ns = {"__name__": "mutar_cabeza"}
argv0 = sys.argv
sys.argv = ["x", str(raiz)]
exec(compile(cabeza, "mutar_cabeza", "exec"), ns)
sys.argv = argv0
SCRIPT, WF, originales, por_asercion = ns["SCRIPT"], ns["WF"], ns["originales"], ns["por_asercion"]

MIAS = {
    # --- F1: plazo pasada por pasada
    "V5_vence_inclusivo": ('p["instante_utc"][:10] < vence', 'p["instante_utc"][:10] <= vence'),
    "V5_vence_sin_chequeo": ('<= PROTEGIDAS_OBJETIVO and p["instante_utc"][:10] < vence', '<= PROTEGIDAS_OBJETIVO'),
    "V5_orden_sin_chequeo": ('orden.get(_clave(p), 10 ** 9) <= PROTEGIDAS_OBJETIVO and ', ''),
    "V5_orden_desde_cero": ("orden = {_clave(p): i + 1 for i, p in enumerate(vistas_pros)}",
                            "orden = {_clave(p): i for i, p in enumerate(vistas_pros)}"),
    "V5_orden_al_reves": ('key=lambda p: (p["instante_utc"], p["volcano"], p["sensor"]))',
                          'key=lambda p: (p["instante_utc"], p["volcano"], p["sensor"]), reverse=True)'),
    "V5_orden_sin_ordenar": ('vistas_pros = sorted((p for p in pros if p["protegida"] and p["sombra_pub"] is not None),\n                         key=lambda p: (p["instante_utc"], p["volcano"], p["sensor"]))',
                             'vistas_pros = list(reversed([p for p in pros if p["protegida"] and p["sombra_pub"] is not None]))'),
    "V5_vistas_exige_sombra_publica": ('if p["protegida"] and p["sombra_pub"] is not None)',
                                       'if p["protegida"] and p["sombra_pub"] is True)'),
    "V5_vistas_sin_exigir_sombra": ('if p["protegida"] and p["sombra_pub"] is not None)', 'if p["protegida"])'),
    "V5_vistas_excluye_juzgadas": ('if p["protegida"] and p["sombra_pub"] is not None)',
                                   'if p["protegida"] and p["sombra_pub"] is not None and _clave(p) not in juzgadas)'),
    "V5_dias_119": ("DIAS_MAXIMOS = 120", "DIAS_MAXIMOS = 119"),
    "V5_dias_121": ("DIAS_MAXIMOS = 120", "DIAS_MAXIMOS = 121"),
    "V5_objetivo_30": ("PROTEGIDAS_OBJETIVO = 29 ", "PROTEGIDAS_OBJETIVO = 30 "),
    "V5_objetivo_28": ("PROTEGIDAS_OBJETIVO = 29 ", "PROTEGIDAS_OBJETIVO = 28 "),
    "V5_fuera_se_descarta": ("    elif fuera_de_plazo:\n        veredicto = \"CANDIDATA_FUERA_DE_PLAZO\"\n", ""),
    "V5_fuera_gana_a_reversion": ('    if reversion:\n        veredicto = "REVERSION_CANDIDATA"\n    elif fuera_de_plazo:\n        veredicto = "CANDIDATA_FUERA_DE_PLAZO"\n',
                                  '    if fuera_de_plazo:\n        veredicto = "CANDIDATA_FUERA_DE_PLAZO"\n    elif reversion:\n        veredicto = "REVERSION_CANDIDATA"\n'),
    "V5_fuera_no_en_salida": ('"reversion": reversion, "fuera_de_plazo": fuera_de_plazo,', '"reversion": reversion, "fuera_de_plazo": [],'),
    "V5_fuera_incluye_juzgadas": ('fuera_de_plazo = [p for p in candidatas if not dentro_de_plazo(p)]',
                                  'fuera_de_plazo = [p for p in calla if p["protegida"] and not dentro_de_plazo(p)]'),
    "V5_vence_desde_hoy": ("vence = ((date.fromisoformat(adopcion[:10]) + timedelta(days=DIAS_MAXIMOS)).isoformat()\n             if adopcion else None)",
                           "vence = ((date.fromisoformat(hoy) + timedelta(days=DIAS_MAXIMOS)).isoformat()\n             if adopcion else None)"),
    # --- F2: juzgadas
    "V5_juzgadas_clave_minuto_15": ('    return (p["volcano"], p["sensor"], p["fecha_utc"][:16])',
                                    '    return (p["volcano"], p["sensor"], p["fecha_utc"][:15])'),
    "V5_juzgadas_salen_de_todo": ('    pros = [p for p in pasadas if p["instante_utc"] >= corte]\n',
                                  '    pasadas = [p for p in pasadas if _clave(p) not in juzgadas]\n    pros = [p for p in pasadas if p["instante_utc"] >= corte]\n'),
    "V5_juzgadas_lista_vacia": ('"juzgadas": [dict(p, juicio=juzgadas[_clave(p)]) for p in pasadas if _clave(p) in juzgadas]}',
                                '"juzgadas": []}'),
    "V5_leer_juzgadas_sin_validar_volcan": ('if (p.get("volcano") not in aa.VOLS or p.get("sensor") not in aa.SENSORS',
                                            'if (p.get("sensor") not in aa.SENSORS'),
    "V5_leer_juzgadas_sin_validar_sensor": ('if (p.get("volcano") not in aa.VOLS or p.get("sensor") not in aa.SENSORS',
                                            'if (p.get("volcano") not in aa.VOLS'),
    "V5_leer_juzgadas_regex_con_segundos": (r'r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}"', r'r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}(:\d{2})?"'),
    "V5_leer_juzgadas_ausente_vacio_falla": ("    if not os.path.exists(path):\n        return {}\n", ""),
    "V5_workflow_fuera_sin_detalle": (WF, '          for p in d.get("fuera_de_plazo", []):\n', '          for p in []:\n'),
}
# Controles del criterio (A110): cada uno sólo hace caer el script, con excepciones distintas y en sitios distintos.
CONTROLES = {
    "C1_keyerror_en_disparadores": (SCRIPT, "    adopcion = adopcion or leer_adopcion()\n    juzgadas = juzgadas or {}\n",
                                    "    raise KeyError('control')\n"),
    "C2_valueerror_en_leer_juzgadas": (SCRIPT, "    out = {}\n    for p in d[\"pasadas\"]:", "    raise ValueError('control')\n    out = {}\n    for p in d[\"pasadas\"]:"),
    "C3_typeerror_en_pasadas": (SCRIPT, "    diurna = diurna or _diurna_por_defecto()\n", "    diurna = diurna or _diurna_por_defecto()\n    None + 1\n"),
    "C4_nameerror_en_dentro_de_plazo": (SCRIPT, "    def dentro_de_plazo(p):\n        return bool(vence)", "    def dentro_de_plazo(p):\n        return bool(vence_no_existe)"),
    "C5_valueerror_en_wilson": (SCRIPT, "    if not n:\n        return (None, None)\n", "    if not n:\n        return (None, None)\n    raise ValueError('control')\n"),
    "C6_syntaxerror": (SCRIPT, "def _clave(p):\n", "def _clave(p)\n"),
    "C7_assertionerror_en_disparadores": (SCRIPT, "    adopcion = adopcion or leer_adopcion()\n    juzgadas = juzgadas or {}\n",
                                          "    raise AssertionError('control que DEBE contarse si el criterio es por tipo')\n"),
}

tests = ["tests/test_vigilancia_sombra_s156.py"]
env = dict(os.environ)
if nobytecode:
    env["PYTHONDONTWRITEBYTECODE"] = "1"
res = {}
todas = list(CONTROLES.items()) + list(MIAS.items())
if not solo_mias:
    todas = [("AUTOR_" + k, v) for k, v in ns["CONTROLES"].items()] + todas + [("AUTOR_" + k, v) for k, v in ns["MUT"].items()]
try:
    for nombre, mut in todas:
        archivo, a, b = mut if len(mut) == 3 else (SCRIPT, *mut)
        orig = originales[archivo]
        if orig.count(a) != 1:
            res[nombre] = {"aplica": False, "cuenta": orig.count(a)}
            print(f"{nombre:45s} NO APLICA ({orig.count(a)})", flush=True)
            continue
        if nobytecode:
            for pc in (raiz / "scripts" / "__pycache__").glob("vigilancia_sombra*.pyc"):
                pc.unlink()
        (raiz / archivo).write_text(orig.replace(a, b), encoding="utf-8", newline="\n")
        junit = raiz / ".v5_junit.xml"
        r = subprocess.run([sys.executable, "-m", "pytest", *tests, "-q", "--no-header", "-p", "no:cacheprovider",
                            f"--junitxml={junit}"], cwd=raiz, capture_output=True, text=True, env=env)
        (raiz / archivo).write_text(orig, encoding="utf-8", newline="\n")
        msgs = []
        if junit.exists():
            for tc in ET.parse(junit).getroot().iter("testcase"):
                for f in list(tc.iter("failure")) + list(tc.iter("error")):
                    msgs.append({"test": tc.get("name"), "tag": f.tag, "msg": (f.get("message") or "")[:200]})
            crit = por_asercion(junit)
            junit.unlink()
        else:
            crit = None
        ult = (r.stdout.strip().splitlines() or [""])[-1]
        res[nombre] = {"aplica": True, "rc": r.returncode, "criterio_autor": crit and r.returncode == 1,
                       "resumen": ult, "fallos": msgs}
        print(f"{nombre:45s} rc={r.returncode} criterio={crit} | {ult}", flush=True)
finally:
    for f, t in originales.items():
        (raiz / f).write_text(t, encoding="utf-8", newline="\n")
salida.write_text(json.dumps(res, indent=1, ensure_ascii=False), encoding="utf-8")
