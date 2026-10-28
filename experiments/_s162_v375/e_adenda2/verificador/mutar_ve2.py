# VE2: mutaciones PROPIAS del verificador sobre el lector del autor, corridas contra su bateria (copia en memoria, sin tocar
# archivos del autor). Misma clasificacion que la del autor: ATRAPADA = la bateria sale 1 con RESULTADO; SOBREVIVE = sale 0;
# CAIDA = excepcion. P1: ve si la bateria deja pasar un cambio de comportamiento (control positivo: M00 = mutacion que
# SI debe atraparse; control de identidad M99). P2: si el clasificador estuviera muerto, M00 no seria ATRAPADA y el CONTROL no seria CAIDA.
import io, json, subprocess, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
AQUI = Path(__file__).resolve().parent
E2 = AQUI.parent
LP = "leer_posicion_v375e.py"
M = [
 ("M00_control_atrapa", LP, 'return "summit" if dist <= inner else "far"', 'return "summit" if dist < inner else "far"'),
 ("M99_identidad", LP, "import numpy as np\n", "import numpy as np\n"),
 ("MCTL_rompe_import", LP, "import numpy as np\n", "import numpy_no_existe as np\n"),
 ("V01_pesos_N_sobre_n_ok_a_1", LP, 'pesos = {(c, h): v["N"] / n_ok[(c, h)] for', 'pesos = {(c, h): 1.0 for'),
 ("V03_RP_sin_errores_de_negativos", LP, 'return E.err(x, a) or (x["c"] == "pos_prot" and not pub)', 'return (x["c"] == "pos_bajo" and not pub) or (x["c"] == "pos_prot" and not pub)'),
 ("V04_umbral_cobertura_0.90", LP, 'UMBRAL_COBERTURA = 0.10', 'UMBRAL_COBERTURA = 0.90'),
 ("V05_far_ok_sin_exigir_cobertura", LP, '>= (1 - UMBRAL_COBERTURA) * len(far_tab)', '>= 0'),
 ("V06_C7_sin_exigir_pixeles", LP, 'or dif or not vivos:', 'or dif:'),
 ("V07_C7_sin_umbral_90pct", LP, 'len(ok_c) < 0.9 * len(ctlf)', 'len(ok_c) < 0.0 * len(ctlf)'),
 ("V08_C3_sin_rango_CTLF", LP, 'if any(not (ID_CTLF[0] <= i < ID_CTLF[1]) for i in ctlf):', 'if False:'),
 ("V10_vara3_sin_abs", LP, 'd = [abs(x["dist_ref"][a] - x["dmiro"][g]) for x in filas', 'd = [(x["dist_ref"][a] - x["dmiro"][g]) for x in filas'),
 ("V15_main_pos_y_ref_cambiados", LP, 'dist = distancias(mascara, mir, pos, pos_ref(g),', 'dist = distancias(mascara, mir, pos_ref(g), pos,'),
 ("V17_main_C6_siempre_ok", LP, 'dc_ok[b] = va is not None and va.get("distance_class") == vb.get("distance_class")', 'dc_ok[b] = True'),
 ("V28_tolerancia_C5_5e-2", LP, 'TOL_DIST_KM = 5e-4 + 1e-9', 'TOL_DIST_KM = 5e-2'),
 ("V30_frontera_OCR_06-14", LP, 'FRONTERA_OCR = "2026-06-13"', 'FRONTERA_OCR = "2026-06-14"'),
 ("V50_via_ancla_centroide_en_vez_de_cráter", LP, 'vlat, vlon = v.get("vent_lat", v["lat"]), v.get("vent_lon", v["lon"])\n    box = MV.caja_v375', 'vlat, vlon = v["lat"], v["lon"]\n    box = MV.caja_v375'),
 ("V51_pos_ref_ejes_cambiados", LP, 'return (g["ul_y"] - g["y0"]) / paso - 0.5, (g["x0"] - g["ul_x"]) / paso - 0.5', 'return (g["x0"] - g["ul_x"]) / paso - 0.5, (g["ul_y"] - g["y0"]) / paso - 0.5'),
 ("V52_veto_sin_distinguir_solo_tabla_default", LP, 'def regla_posicion(filas, E, far_ok=True, solo_tabla=False):', 'def regla_posicion(filas, E, far_ok=True, solo_tabla=True):'),
 ("V53_cercano_desde_ref_no_cráter", LP, 'cer = min(celdas, key=lambda p: (d(p[0], p[1], crater), p))', 'cer = min(celdas, key=lambda p: (d(p[0], p[1], ref), p))'),
 ("V54_pico_sobre_toda_la_mascara_no_el_cumulo", LP, 'pico = max(cu, key=lambda p: m13[p])', 'pico = max(celdas, key=lambda p: m13[p])'),
 ("V55_ciclo_no_resuelto_sin_texto", LP, 'if "radiante" in no_vencidos:', 'if "radiante" in no_vencidos or not no_vencidos:'),
 ("V56_C1_exige_igualdad_con_tolerancia_1km", LP, 'len({round(pasadas[i]["dist"][a], 9) for a in BRAZOS_POS}) != 1', 'len({round(pasadas[i]["dist"][a], 0) for a in BRAZOS_POS}) != 1'),
 ("V57_publicar_ignora_inner_html", LP, "casos.append((ra if ra is not None else (p[\"rec\"] or {}), p[\"inner\"]))", "casos.append((ra if ra is not None else (p[\"rec\"] or {}), 1e9))"),
]
def una(m):
    with tempfile.TemporaryDirectory() as t:
        mj = Path(t) / "m.json"
        mj.write_text(json.dumps(m[1:]), encoding="utf-8")
        env = dict(__import__("os").environ, MUT_JSON=str(mj))
        p = subprocess.run([sys.executable, "-I", str(AQUI / "probar_mio.py"), "--dir", str(E2)], capture_output=True,
                           text=True, encoding="utf-8", errors="replace", env=env, timeout=900)
    falla = [x[6:].strip()[:80] for x in p.stdout.splitlines() if x.startswith("FALLA")]
    res = [x for x in p.stdout.splitlines() if x.startswith("RESULTADO")]
    if p.returncode == 0 and res: return "SOBREVIVE", falla
    if p.returncode == 1 and res: return "ATRAPADA", falla
    return "CAIDA", (p.stderr.strip().splitlines() or ["?"])[-1:]
if __name__ == "__main__":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    with ThreadPoolExecutor(max_workers=3) as ex:
        out = list(ex.map(una, M))
    cu = {"ATRAPADA": 0, "SOBREVIVE": 0, "CAIDA": 0}
    for m, (e, f) in zip(M, out):
        cu[e] += 1
        print(f"{m[0]:48s} {e:9s} {f[:2]}", flush=True)
    print("\nRESUMEN", cu)
