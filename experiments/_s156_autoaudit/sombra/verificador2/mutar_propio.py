"""C5: mutaciones nuevas del verificador 2 sobre una COPIA de scripts/vigilancia_sombra.py.
Clasifica cada falla: ATRAPADA_ASSERT (alguna prueba falla por aserción), SOLO_EXCEPCION (todas las fallas son
excepciones que no son AssertionError: no cuenta como atrapada), NO_ATRAPADA (pasan las 25).
Uso: python mutar_propio.py <copia> [autor]   (con 'autor' re-clasifica las 21 del autor)"""
import importlib.util
import re
import subprocess
import sys
from pathlib import Path

copia = Path(sys.argv[1])
p = copia / "scripts" / "vigilancia_sombra.py"
orig = p.read_text(encoding="utf-8")

MUT = {
    "M1_pareo_sin_sensor": [('idx[nombre][(r["vol"], r["b"])].append(r)', 'idx[nombre][r["vol"]].append(r)'),
                            ('for r in idx[n].get((vol, b), [])', 'for r in idx[n].get(vol, [])')],
    "M2_ultima_de_produccion": [('ultima = max((r["noche"] for r in sombra), default=None)',
                                'ultima = max((r["noche"] for r in prod), default=None)')],
    "M3_muy_bajo_sin_condicion_sombra": [('c[0] += p["sombra_pub"] and not p["prod_pub"]',
                                         'c[0] += not p["prod_pub"]')],
    "M4_persistencia_incluye_retro": [("persistencia = _persistencia(calla)\n",
                                      "persistencia = _persistencia(_sombra_si_produccion_no(pasadas))\n")],
    "M5_umbral_protegida_05": [("protegidas = [f for f in fs if cm.alerta_protegida(f)]",
                               "protegidas = [f for f in fs if cm.alerta_protegida(f, umbral=0.5)]")],
    "M6_sombra_carga_produccion": [("sombra = bp.cargar_nuestros(coords, inner, win, data=SOMBRA)",
                                   "sombra = bp.cargar_nuestros(coords, inner, win)")],
    "M7_negativos_sin_d9": [('idx = bp.indexar_referencia(filas, coords, win, regla_minimas="SN")',
                            'idx = bp.indexar_referencia(filas, coords, win, regla_minimas="original")')],
    "M8_sospecha_sin_hito": [("and minuto[:10] < aa.HITO_OCR_SUOMI_NPP\n", "\n")],
    "M9_diurna_lat_lon_cambiados": [("aa.es_pasada_diurna_descartada(b, ll[0], ll[1], dt)",
                                    "aa.es_pasada_diurna_descartada(b, ll[1], ll[0], dt)")],
    "M10_lectura_con_sin_geometria": [('if f.get("tipo") in cm.TIPOS_ALERTA and win[0]',
                                      'if f.get("tipo") in cm.TIPOS_ALERTA + ("ALERTA_SIN_GEOMETRIA_OCR",) and win[0]')],
    "M11_historial_se_sobrescribe": [('"sombra_history.jsonl"), "a"', '"sombra_history.jsonl"), "w"')],
    "M12_prod_incluye_no_K": [('prod = [r for r in bp.cargar_nuestros(coords, inner, win) if r.get("sha")]',
                              'prod = bp.cargar_nuestros(coords, inner, win)')],
    "M13_reversion_tambien_sin_record_prod": [  # producción sin record cuenta como calla en la reversión
        ('reversion = [p for p in calla if p["protegida"]]',
         'reversion = [p for p in pros if p["protegida"] and p["sombra_pub"] is True and not p["prod_pub"]]')],
}

if len(sys.argv) > 2 and sys.argv[2] == "autor":
    spec = importlib.util.spec_from_file_location("ma", sys.argv[3])
    src = Path(sys.argv[3]).read_text(encoding="utf-8")
    ns = {}
    exec(re.search(r"MUT = \{.*?\n\}\n", src, re.S).group(0), ns)
    MUT = {k: [v] for k, v in ns["MUT"].items()}

try:
    for nombre, pares in MUT.items():
        txt = orig
        ok = True
        for a, b in pares:
            if txt.count(a) != 1:
                print(f"{nombre:40s} NO APLICA (cuenta {txt.count(a)}): {a[:60]!r}")
                ok = False
                break
            txt = txt.replace(a, b)
        if not ok:
            continue
        p.write_text(txt, encoding="utf-8", newline="\n")
        r = subprocess.run([sys.executable, "-m", "pytest", "tests/test_vigilancia_sombra_s156.py", "-q",
                            "--no-header", "-p", "no:cacheprovider", "--tb=short", "-rf"],
                           cwd=copia, capture_output=True, text=True, encoding="utf-8")
        ult = (r.stdout.strip().splitlines() or [""])[-1]
        secciones = re.split(r"\n_{3,} (test_\w+) _{3,}\n", r.stdout)
        fallas, assert_f = [], []
        for i in range(1, len(secciones) - 1, 2):
            nom, cuerpo = secciones[i], secciones[i + 1]
            elin = [ln for ln in cuerpo.splitlines() if ln.startswith("E ")]
            tipo = "assert" if any(re.match(r"E\s+(assert |AssertionError)", ln) for ln in elin) else (
                elin[-1][:120] if elin else "?")
            fallas.append(f"{nom}: {tipo if tipo == 'assert' else 'EXCEPCION ' + tipo}")
            if tipo == "assert":
                assert_f.append(nom)
        if r.returncode == 0:
            estado = "NO_ATRAPADA"
        elif assert_f:
            estado = f"ATRAPADA_ASSERT ({len(assert_f)} de {len(fallas)} fallas por asercion)"
        else:
            estado = f"SOLO_EXCEPCION ({len(fallas)} fallas)"
        print(f"{nombre:40s} {estado} | {ult}")
        for ln in fallas[:4]:
            print("      ", ln[:200])
finally:
    p.write_text(orig, encoding="utf-8", newline="\n")
