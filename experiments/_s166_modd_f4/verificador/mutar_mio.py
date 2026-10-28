# -*- coding: utf-8 -*-
"""Mutaciones PROPIAS del verificador (VF4): reglas que el pre-registro fija y el medidor del autor no muta.
Misma clasificación que mutar_evaluar_f4.py: ATRAPADA solo si algún escenario falla por ASERCIÓN (código 1).
Uso (desde esta carpeta): python mutar_mio.py > mutar_mio_salida.txt"""
import concurrent.futures as cf, os, subprocess, sys, tempfile
from pathlib import Path
AQUI = Path(__file__).resolve().parent
F4 = AQUI.parent
RAIZ = F4.parents[1]
FUENTE = (F4 / "evaluar_f4.py").read_text(encoding="utf-8")
MUT = [
 ("IDENTIDAD", None, None),
 ("A01_n_inyectar_40", "N_INYECTAR, SEMILLA_INYECTAR = 50, 166", "N_INYECTAR, SEMILLA_INYECTAR = 40, 166"),
 ("A02_chillan_banda_ancha", "0.8 <= med <= 1.25 and 20 * num <= den", "0.5 <= med <= 2.0 and 20 * num <= den"),
 ("A03_chillan_p_0_5", "20 * num <= den", "2 * num <= den"),
 ("A04_no_peor_tolera_mas", 'p["estado"] == "SIN SUSTRATO" and p["neto"] <= 0', 'p["estado"] == "SIN SUSTRATO" and p["neto"] <= 5'),
 ("A05_p1b_k_exacto_1", '_mag(f, "K") >= CORTE_MW > _mag(f, b)', '_mag(f, "K") > CORTE_MW > _mag(f, b)'),
 ("A06_estado_arnes_ignorado", 'if f.get("estado") != "ok":', 'if False:'),
 ("A07_motivo_desconocido_ok", 'if mot:', 'if False:'),
 ("A08_chillan_siempre_V", 'bc = res["posicion_elegida"] or "V"', 'bc = "V"'),
 ("A09_posicion_sin_clase", 'clase_dc(d, f["inner"]) == v.get("distance_class")', "True"),
 ("A10_posicion_sin_vrp_igual", '(w.get("primary_cluster") or {}).get("vrp_mw") == pc.get("vrp_mw")', 'True'),
 ("A11_m_signo", 'abs(math.log10(p["d"] / p["m"])) - abs(math.log10(p["k"] / p["m"]))', 'abs(math.log10(p["k"] / p["m"])) - abs(math.log10(p["d"] / p["m"]))'),
 ("A12_p1_solo_ocr_veta", 'if any(not x["solo_ocr"] for x in perd)', 'if any(True for x in perd)'),
 ("A13_pares_chillan_sin_mag", ' and _mag(f, "K") > 0 and _mag(f, b) > 0:\n            mm = f["vrp_mirova"]', ':\n            mm = f["vrp_mirova"]'),
 ("A14_ident_otro_granulo_fuera_de_malas", 'if k in ident and ident[k]["mismo_granulo"] and not (', 'if k in ident and not ('),
 ("A15_far_ref_cuenta_en_p2_sellada", 'labs = ("bajo1", "neg_limpio", "far_ref") if lejana else ("bajo1", "neg_limpio")\n    out = []', 'labs = ("bajo1", "neg_limpio", "far_ref")\n    out = []'),
 ("A16_ganan_exige_solo_V", 'ganan = [b for b in otros if br[b]["p2l_vs_V"]["estado"] == "GANA"]', 'ganan = [b for b in otros if br[b]["p2l_vs_V"]["estado"] == "GANA" and br[b]["p2"]["estado"] != "PIERDE"]'),
 ("A17_cobertura_sobran_ignorado", "ok = not rep and not faltan and not sobran", "ok = not rep and not faltan"),
]
def correr(n, v, nu, tmp):
    if v is None: src = FUENTE
    else:
        c = FUENTE.count(v)
        if c != 1: return n, "NO APLICA (%d)" % c, ""
        src = FUENTE.replace(v, nu)
    ruta = Path(tmp) / ("ev_%s.py" % n); ruta.write_text(src, encoding="utf-8")
    env = dict(os.environ, F4_RAIZ=str(RAIZ), PYTHONIOENCODING="utf-8")
    p = subprocess.run([sys.executable, str(F4 / "probar_evaluar_f4.py"), "--modulo", str(ruta)], capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    cl = {0: "VIVA", 1: "ATRAPADA", 2: "CAE"}.get(p.returncode, "CODIGO_%s" % p.returncode)
    fa = [ln.split()[2].split("_")[0] for ln in p.stdout.splitlines() if ln.startswith("FALLA ASERCION")]
    ca = [ln.split()[1].split("_")[0] for ln in p.stdout.splitlines() if ln.startswith("CAE ")]
    return n, cl, "aserción: %s | caen: %s" % (",".join(fa) or "-", ",".join(ca) or "-")
if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    solo = sys.argv[1].split(",") if len(sys.argv) > 1 else None
    sel = [m for m in MUT if not solo or m[0].split("_")[0] in solo]
    with tempfile.TemporaryDirectory(prefix="mut_vf4_") as tmp, cf.ThreadPoolExecutor(4) as ex:
        res = list(ex.map(lambda m: correr(*m, tmp), sel))
    for r in res: print("%-42s %-10s %s" % r)
