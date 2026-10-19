"""Verificador 3: mutaciones con clasificacion por TIPO de falla (asercion vs excepcion).
Uso: python mutar3.py <copia> [autor]   Restaura el archivo al terminar."""
import subprocess, sys, re, importlib.util, xml.etree.ElementTree as ET
from pathlib import Path
raiz = Path(sys.argv[1]); p = raiz / "scripts" / "vigilancia_sombra.py"; orig = p.read_text(encoding="utf-8")
NUEVAS = {
 "N1_minimas_umbral_004": ('minimas = cm.aplicar_regla_minimas(filas, "SN").minimas',
                           'minimas = cm.aplicar_regla_minimas(filas, "SN", umbral_mw=0.04).minimas'),
 "N2_pasadas_con_filas_SN": ("    for f in filas:\n        if f.get(\"tipo\") in cm.TIPOS_ALERTA and win[0]",
                             "    for f in cm.aplicar_regla_minimas(filas, \"SN\").filas:\n        if f.get(\"tipo\") in cm.TIPOS_ALERTA and win[0]"),
 "N3_instante_sin_segundos": ('"instante_utc": dt.strftime("%Y-%m-%d %H:%M:%S")', '"instante_utc": dt.strftime("%Y-%m-%d %H:%M:00")'),
 "N5_negativos_desde_medianoche": ("corte_dt = _instante(adopcion) if adopcion else None",
                                   'corte_dt = _instante(adopcion[:10] + " 00:00:00") if adopcion else None'),
 "N6_frescura_borde_mayor_igual": ("if dias > MAX_DIAS_SOMBRA_SIN_DATOS:", "if dias >= MAX_DIAS_SOMBRA_SIN_DATOS:"),
 "N7_frescura_solo_volcanes_vistos": ("    av = []\n    for v in vols:", "    av = []\n    for v in sorted(ultima):"),
 "N9_muy_bajo_sin_exigir_record_sombra": ('if p["protegida"] or p["prod_pub"] is None or p["sombra_pub"] is None:',
                                          'if p["protegida"] or p["prod_pub"] is None:'),
 "N12_retro_persistencia_con_minimas": ('"persistencia": _persistencia([p for p in calla_retro if not p["minima"]])',
                                        '"persistencia": _persistencia(calla_retro)'),
 "N18_ciega_tapa_reversion": ('if veredicto == "VERDE" and avisos:', "if avisos:"),
 "N19_hoy_ayer": ("hoy = datetime.now(timezone.utc).date().isoformat()",
                  "hoy = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()"),
 "N22_tolerancia_61": ("TOL_S = cm.VENTANA_S", "TOL_S = 61"),
 "N23_sospecha_si_alguna_es_ocr": ('{f.get("source") for f in protegidas} == {"OCR"}', '"OCR" in {f.get("source") for f in protegidas}'),
 "N24_investigar_ignora_persistencia": ("elif persistencia or negativos", "elif negativos"),
 "N25_retro_incluye_corte": ('retro = [p for p in pasadas if p["instante_utc"] < corte]', 'retro = [p for p in pasadas if p["instante_utc"] <= corte]'),
 "N26_avisos_sombra_sin_continue": ("ese volcán está ciego\")\n            continue\n", "ese volcán está ciego\")\n"),
 "N27_corte_sin_adopcion_es_cero": ('corte = adopcion or "9999-99-99 99:99:99"', 'corte = adopcion or "0000"'),
 "N28_wilson_z_164": ("def wilson(k, n, z=1.96):", "def wilson(k, n, z=1.64):"),
 "N29_lab_original_tras_sn": ('    for r in prod:\n        r["lab_original"] = r["lab"]\n    bp.etiquetar(prod, *bp.indexar_referencia(filas, coords, win, regla_minimas="SN")[:3])\n',
                              '    bp.etiquetar(prod, *bp.indexar_referencia(filas, coords, win, regla_minimas="SN")[:3])\n    for r in prod:\n        r["lab_original"] = r["lab"]\n'),
}
MUT = dict(NUEVAS)
if len(sys.argv) > 2:
    spec = importlib.util.spec_from_file_location("ma", raiz / "experiments/_s156_autoaudit/sombra/mutar_vigilancia.py")
    src = (raiz / "experiments/_s156_autoaudit/sombra/mutar_vigilancia.py").read_text(encoding="utf-8")
    ns = {}
    exec(src.split("tests = [")[0].replace("raiz = Path(sys.argv[1])", "raiz = Path(%r)" % str(raiz)), ns)
    MUT = ns["MUT"]
xml = raiz.parent / "junit_tmp.xml"
res = {}
try:
    for nombre, (a, b) in MUT.items():
        if orig.count(a) != 1:
            print(f"{nombre:42s} NO APLICA (cuenta {orig.count(a)})"); res[nombre] = "NO_APLICA"; continue
        p.write_text(orig.replace(a, b), encoding="utf-8", newline="\n")
        r = subprocess.run([sys.executable, "-m", "pytest", "tests/test_vigilancia_sombra_s156.py", "-q", "-p", "no:cacheprovider",
                            f"--junitxml={xml}"], cwd=raiz, capture_output=True, text=True, encoding="utf-8", errors="replace")
        tipos = []
        try:
            for tc in ET.parse(xml).getroot().iter("testcase"):
                for f in list(tc.findall("failure")) + list(tc.findall("error")):
                    msg = (f.get("message") or "").strip()
                    t = "ASERCION" if (msg.startswith("AssertionError") or msg.startswith("assert ")) else "EXC:" + msg.split(":")[0][:40]
                    tipos.append((tc.get("name"), t))
        except Exception as e:
            tipos.append(("xml", "EXC:" + repr(e)))
        n_as = sum(t == "ASERCION" for _, t in tipos)
        veredicto = "ATRAPADA" if n_as else ("SOLO_EXCEPCION" if tipos else "SOBREVIVE")
        res[nombre] = veredicto
        exc = sorted({t for _, t in tipos if t != "ASERCION"})
        print(f"{nombre:42s} {veredicto:15s} asercion={n_as} otras={len(tipos)-n_as} {exc if exc else ''} | {[n for n,_ in tipos][:4]}")
finally:
    p.write_text(orig, encoding="utf-8", newline="\n")
print("\nresumen:", {v: sum(1 for x in res.values() if x == v) for v in set(res.values())})
