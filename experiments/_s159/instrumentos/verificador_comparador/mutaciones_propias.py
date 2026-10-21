# -*- coding: utf-8 -*-
"""Verificador S159: mutaciones del comparador D-28 que el corredor del implementador NO prueba. Para cada una: copia
evaluar_d25.py mutado a una subcarpeta de ESTA carpeta, corre tests/test_evaluar_d25_placebo_s159.py contra la copia
(D25_EVALUADOR_DIR) y además mide directo, sobre los pares reales de K (pares_k.json), el efecto de la mutación en un
caso donde debería importar. Se clasifica la falla por el JUnit XML (aserción o caída), como el corredor original.

Control (A110): la copia sin mutar tiene que dar 0 fallas. Uso: python mutaciones_propias.py
"""
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[3]
ORIG = RAIZ / "experiments" / "_s157_prereg_d25"
PRUEBA = RAIZ / "tests" / "test_evaluar_d25_placebo_s159.py"

MUT = [
    ("control sin mutar", []),
    ("opción A sobre d′ retirada (d′ basta con un volcán)",
     [('"dprima_da_mejora": bool(r_p == "MEJORA" and calibrada and vols_neg >= MIN_VOLCANES_MEJORA)}',
       '"dprima_da_mejora": bool(r_p == "MEJORA" and calibrada)}')]),
    ("calibración de d′ ignorada (calibrada siempre True)",
     [('    calibrada = f_mej <= MAX_FALSOS_CALIB and f_emp <= MAX_FALSOS_CALIB\n    vols_neg, vols_n, g_vol = 0, 0, {}',
       '    calibrada = True\n    vols_neg, vols_n, g_vol = 0, 0, {}')]),
    ("sin redondeo de d′ (DEC_DPRIMA = 30)",
     [('DEC_DPRIMA = 12', 'DEC_DPRIMA = 30')]),
    ("ĝ con el signo invertido (K / ĝ)",
     [('    dp = np.round(np.abs(lD) - np.abs(lK + g_hat), DEC_DPRIMA)',
       '    dp = np.round(np.abs(lD) - np.abs(lK - g_hat), DEC_DPRIMA)'),
      ('np.abs(lK[None, :] + g_b[:, None])', 'np.abs(lK[None, :] - g_b[:, None])')]),
    ("ĝ = media en vez de mediana (punto)",
     [('    g_hat = float(np.median(g))                        # §2.1, estimación puntual',
       '    g_hat = float(np.mean(g))')]),
    ("calibración de d′ sólo con la cola MEJORA",
     [('    calibrada = f_mej <= MAX_FALSOS_CALIB and f_emp <= MAX_FALSOS_CALIB\n    vols_neg, vols_n, g_vol = 0, 0, {}',
       '    calibrada = f_mej <= MAX_FALSOS_CALIB\n    vols_neg, vols_n, g_vol = 0, 0, {}')]),
    ("opción A de d′ contada con d en vez de d′",
     [('            vols_n += 1; vols_neg += float(np.median(dp[sel])) < 0',
       '            vols_n += 1; vols_neg += float(np.median((np.abs(lD) - np.abs(lK))[sel])) < 0')]),
]


def cargar(dst):
    spec = importlib.util.spec_from_file_location("ev_mut_%s" % dst.name, dst / "evaluar_d25.py")
    m = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(ORIG))
    spec.loader.exec_module(m)
    return m


def main():
    pares = json.loads((AQUI / "pares_k.json").read_text(encoding="utf-8"))
    for i, (nombre, cambios) in enumerate(MUT):
        dst = AQUI / ("_mut_%02d" % i)
        if dst.exists():
            shutil.rmtree(dst)
        dst.mkdir()
        try:
            for f in ("evaluar_d25.py", "ADENDA_CALIBRACION.md", "ADENDA_PLACEBO.md"):
                shutil.copy2(ORIG / f, dst / f)
            src = (dst / "evaluar_d25.py").read_text(encoding="utf-8")
            # la copia vive más hondo que el original: se fija RAIZ (aplica igual al control sin mutar)
            src = src.replace("RAIZ = AQUI.parents[1]", "RAIZ = Path(%r)" % str(RAIZ), 1)
            for a, b in cambios:
                n = src.count(a)
                if n != 1:
                    print("%-55s TEXTO NO ENCONTRADO (%d): %r" % (nombre, n, a[:70]))
                    break
                src = src.replace(a, b)
            else:
                (dst / "evaluar_d25.py").write_text(src, encoding="utf-8")
                xml = dst / "r.xml"
                env = dict(os.environ, D25_EVALUADOR_DIR=str(dst), PYTHONIOENCODING="utf-8")
                subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--junitxml", str(xml),
                                str(PRUEBA)], cwd=str(RAIZ), capture_output=True, text=True, env=env)
                fall, cae = [], []
                for c in ET.parse(xml).getroot().iter("testcase"):
                    for f in c.findall("failure"):
                        msg = (f.get("message") or "").strip()
                        (fall if msg.startswith(("assert ", "AssertionError")) else cae).append(c.get("name"))
                    for e in c.findall("error"):
                        cae.append(c.get("name"))
                estado = "ATRAPADA (aserción)" if fall and not cae else "CAE" if cae else "NO ATRAPADA"
                # efecto directo sobre los pares reales: brazo "un volcán a MIROVA, resto x1.2" y "placebo x1.2"
                X = cargar(dst)
                efectos = []
                for w in ("V1", "V2"):
                    for nom in ("VIIRS750|z<=40", "VIIRS375|sin_kernel|z<=40"):
                        P = pares[w][nom]
                        r12 = X.decidir_estrato([dict(p, d=p["k"] * 1.2) for p in P], "decide", "simetrica", True)
                        efectos.append("%s %s x1.2 -> %s" % (w, nom.split("|")[0] + nom.split("|")[-1], r12[0]))
                print("%-55s %-20s fallas por aserción %d, caídas %d | %s" % (nombre, estado, len(fall), len(cae),
                                                                             "; ".join(efectos)), flush=True)
                for t in fall:
                    print("      aserción: %s" % t)
                for t in cae:
                    print("      cae: %s" % t)
        finally:
            shutil.rmtree(dst, ignore_errors=True)


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    main()
