"""Bateria del verificador 4. Corre las 62 mutaciones del autor y las nuevas sobre una COPIA.
Atrapada = al menos una prueba falla por ASERCION (AssertionError o pytest.fail/DID NOT RAISE). Si todas las
fallas son otra excepcion (el script cae), NO cuenta. Uso: python mutar_v4.py <copia> <junit_tmp>"""
import re, subprocess, sys
import xml.etree.ElementTree as ET
from pathlib import Path

raiz = Path(sys.argv[1]); tmpd = Path(sys.argv[2])
src_aut = (raiz / "experiments/_s156_autoaudit/sombra/mutar_vigilancia.py").read_text(encoding="utf-8")
bloque = src_aut[src_aut.index("MUT = {"):src_aut.index("\ntests =")]
ns = {}; exec(bloque, ns)
S = "scripts/vigilancia_sombra.py"; WF = ".github/workflows/vigilancia-sombra.yml"
MUT = [(n, S, a, b, "autor") for n, (a, b) in ns["MUT"].items()]
NUEVAS = [
    ("V4_juzgadas_reportadas_pero_disparan", S,
     'vivas = [p for p in pasadas if (p["volcano"], p["sensor"], p["fecha_utc"][:16]) not in juzgadas]', "vivas = list(pasadas)"),
    ("V4_retro_incluye_juzgadas", S, 'retro = [p for p in vivas if p["instante_utc"] < corte]',
     'retro = [p for p in pasadas if p["instante_utc"] < corte]'),
    ("V4_plazo_29_estricto", S, '"cumplida": vistas >= PROTEGIDAS_OBJETIVO or', '"cumplida": vistas > PROTEGIDAS_OBJETIVO or'),
    ("V4_plazo_dia_estricto", S, "bool(vence and hoy >= vence)}", "bool(vence and hoy > vence)}"),
    ("V4_fuera_de_plazo_sin_reversion", S, 'if reversion and duracion["cumplida"]:', 'if duracion["cumplida"]:'),
    ("V4_vistas_solo_si_sombra_publica", S,
     'p["instante_utc"] >= corte and p["protegida"] and p["sombra_pub"] is not None)',
     'p["instante_utc"] >= corte and p["protegida"] and p["sombra_pub"])'),
    ("V4_vistas_cuenta_no_protegidas", S,
     'p["instante_utc"] >= corte and p["protegida"] and p["sombra_pub"] is not None)',
     'p["instante_utc"] >= corte and p["sombra_pub"] is not None)'),
    ("V4_salida_juzgadas_vacia", S, '"juzgadas": [dict(p, juicio=', '"juzgadas": [] and [dict(p, juicio='),
    ("V4_leer_juzgadas_siempre_vacio", S, "    if not os.path.exists(path):\n        return {}", "    if True:\n        return {}"),
    ("V4_juzgadas_clave_sin_sensor", S,
     'return {(p["volcano"], p["sensor"], p["fecha_utc"][:16]): p for p in d["pasadas"]}',
     'return {(p["volcano"], "VIIRS750", p["fecha_utc"][:16]): p for p in d["pasadas"]}'),
    ("V4_cota_V1_denominador_194", S, '"V1_SE": (7, 161)', '"V1_SE": (7, 194)'),
    ("V4_cota_min_de_V1_V2", S, "return max(wilson(k, n)[1] for k, n in cotas.values()) if cotas else None",
     "return min(wilson(k, n)[1] for k, n in cotas.values()) if cotas else None"),
    ("V4_wf_fuera_de_plazo_sin_issue", WF, 'abrir "Sombra de K: candidata fuera de plazo"', 'echo "Sombra de K: candidata fuera de plazo"'),
    ("V4_wf_fuera_de_plazo_mismo_prefijo", WF, 'abrir "Sombra de K: candidata fuera de plazo"', 'abrir "Sombra de K: candidata a reversion"'),
    ("V4_wf_fuera_de_plazo_dice_preautoriza", WF, "Fuera de plazo NO hay reversion pre-autorizada",
     "Fuera de plazo hay reversion pre-autorizada"),
]
MUT += [(n, f, a, b, "v4") for n, f, a, b in NUEVAS]
orig = {f: (raiz / f).read_text(encoding="utf-8") for f in (S, WF)}
res = {"autor": [0, 0], "v4": [0, 0]}
try:
    for i, (n, f, a, b, quien) in enumerate(MUT):
        o = orig[f]
        if o.count(a) != 1:
            print(f"{quien:5} {n:44s} NO APLICA (cuenta {o.count(a)})"); continue
        (raiz / f).write_text(o.replace(a, b), encoding="utf-8", newline="\n")
        xml = tmpd / f"j{i}.xml"
        r = subprocess.run([sys.executable, "-m", "pytest", "tests/test_vigilancia_sombra_s156.py", "-q", "--no-header",
                            "-p", "no:cacheprovider", f"--junitxml={xml}"], cwd=raiz, capture_output=True, text=True)
        (raiz / f).write_text(o, encoding="utf-8", newline="\n")
        tipos = []
        if xml.exists():
            for tc in ET.parse(xml).getroot().iter("testcase"):
                for fl in list(tc.findall("failure")) + list(tc.findall("error")):
                    msg = (fl.get("message") or "") + " " + (fl.text or "")[-400:]
                    m = re.search(r"\nE\s+(\w+(?:\.\w+)*(?:Error|Exception|Failed|Exit|Interrupt))", "\n" + (fl.text or ""))
                    t = fl.tag + ":" + (m.group(1) if m else (fl.get("type") or "?"))
                    tipos.append((tc.get("name"), t))
        aserc = [x for x in tipos if "AssertionError" in x[1] or "Failed" in x[1] or "assert" in x[1].lower()]
        ok = bool(aserc)
        res[quien][0] += ok; res[quien][1] += 1
        otras = sorted({t for _, t in tipos if (_, t) not in aserc})
        print(f"{quien:5} {n:44s} {'ATRAPADA' if ok else 'NO ATRAPADA'} | {len(aserc)} por asercion"
              f"{' | otras: ' + ', '.join(otras) if otras else ''}"
              f"{' | ej: ' + aserc[0][0] if aserc else ''}")
finally:
    for f, o in orig.items():
        (raiz / f).write_text(o, encoding="utf-8", newline="\n")
for q, (k, n) in res.items():
    print(f"{q}: {k} de {n} atrapadas por asercion")
