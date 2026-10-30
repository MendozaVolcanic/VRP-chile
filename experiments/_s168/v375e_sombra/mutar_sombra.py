# -*- coding: utf-8 -*-
"""S168 V375-E: nulo de la batería del lector de la sombra por mutaciones de una línea (mismo método que
experiments/_s162_v375/e_adenda2/mutar_adenda2.py: S156, cuenta como ATRAPADA sólo la mutación que la batería rechaza
por aserción; una que hace caer la batería con una excepción es CAÍDA y no cuenta).

Cada mutación cambia UN texto que aparece exactamente una vez en leer_sombra_v375e.py, en una copia propia
(`experiments/_s168/_mut_sombra_<id>/`, a la misma profundidad que la carpeta original para que el lector encuentre la
raíz del repo; borrada al terminar), y corre `probar_sombra.py --dir <copia>`.
  ATRAPADA   la batería sale 1 con su línea RESULTADO (alguna aserción falló)
  SOBREVIVE  la batería sale 0 (la mutación no se ve)
  CAÍDA      la batería se cae (excepción, sin línea RESULTADO): no cuenta como atrapada
Controles: IDENTIDAD (la copia sin mutar tiene que PASAR) y CONTROL (una mutación que rompe la importación tiene que
salir CAÍDA). Hilos: --hilos (1 por defecto; el cupo pesado del equipo es compartido).
Uso: python -I mutar_sombra.py [--hilos N] [--solo ID,ID]  (escribe mutar_sombra_salida.txt, o _repaso con --solo)
"""
from __future__ import annotations

import argparse
import io
import shutil
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
LS = "leer_sombra_v375e.py"

CONTROL = ("CONTROL", "import numpy as np\n", "import numpy_no_existe as np\n")
MUTACIONES = [
    # ---- población y clases
    ("M01", 'return "pos_prot" if any(alerta_protegida(f) for f in ref) else "pos_bajo"',
     'return "pos_bajo" if any(alerta_protegida(f) for f in ref) else "pos_prot"'),
    ("M02", 'return "neg_pub" if r["pub"] else "neg_resto"', 'return "neg_resto" if r["pub"] else "neg_pub"'),
    ("M03", 'and f["source"] == "CONS" for f in ref) else "far_ocr"', 'or f["source"] == "CONS" for f in ref) else "far_ocr"'),
    ("M04", '    return None\n\n\ndef poblacion', '    return "neg_resto"\n\n\ndef poblacion'),
    ("M05", 'if r.get("sensor") == SENSOR_SNPP:', 'if r.get("sensor") == "VIIRS_XX":'),
    ("M06", 'if r["b"] != "VIIRS375":', 'if r["b"] == "MODIS_X":'),
    ("M07", "('z<=40' if z <= 40 else 'z>40')", "('z<=40' if z <= 60 else 'z>40')"),
    ("M08", '"alerta_tabla": any(f["source"] == "CONS" for f in alertas)',
     '"alerta_tabla": any(f["source"] == "OCR" for f in alertas)'),
    ("M09", 'or "750" in r["sensor"]:', 'or "XYZ" in r["sensor"]:'),
    ("M10", 'if solo_via and r.get("via_codigo_mirova") is not True:', 'if False:'),
    ("M11", 'if not (desde <= dt[:10] <= hasta)', 'if not (desde <= dt[:10] <= "2099-12-31")'),
    # ---- brazos y borde
    ("M12", '        dc = d["cercano"]\n', '        dc = d["radiante"]\n'),
    ("M13", 'dc = inn + 0.01 if LP.clase_dc(d["cercano"], inn) == "summit" else inn - 0.01',
     'dc = inn - 0.01 if LP.clase_dc(d["cercano"], inn) == "summit" else inn + 0.01'),
    ("M14", '(("VIA", "radiante"), d["radiante"])):', '(("VIA", "radiante"), d["cercano"])):'),
    ("M15", '("VIA", "sinfiltro"): (npix > 0,', '("VIA", "sinfiltro"): (npix >= 0,'),
    ("M16", 'arms[i][a] = (bool(pub), float(disp or 0.0), npix)', 'arms[i][a] = (bool(pub), float(0.0), npix)'),
    ("M17", 'arms[o["id"]][a] = (False, 0.0, npix)', 'arms[o["id"]][a] = (True, 0.0, npix)'),
    ("M18", '- inner[o["volcan"]]) < BORDE_KM)', '- inner[o["volcan"]]) < 10 * BORDE_KM)'),
    ("M19", 'BORDE_KM = 0.005 ', 'BORDE_KM = 0.002 '),
    # ---- controles
    ("M20", 'desde >= DESDE_P and hasta >= desde', 'hasta >= desde'),
    ("M21", 'and len(claves) == len(set(claves)), \\', 'and True, \\'),
    ("M22", 'if not (desde <= o["noche"] <= hasta)]', 'if not (o["noche"] <= hasta)]'),
    ("M23", 'return r == [True, False, True], r', 'return True, r'),
    ("M24", 'return False, "sin pasada de la vía', 'return True, "sin pasada de la vía'),
    ("M25", 'ok2 = ok2 and identidad_ok', 'ok2 = ok2'),
    ("M26", '> TOL_UNO_KM]', '> 1.0]'),
    ("M27", 'return bool(uno) and not malos', 'return not malos'),
    ("M28", 'return n > 0 and not malos', 'return not malos'),
    ("M29", '!= info[o["id"]]["dc"]]', '== info[o["id"]]["dc"]]'),
    ("M30", 'return bool(casos) and dist == 0', 'return dist == 0'),
    ("M31", 'len(s) / n > UMBRAL_COBERTURA:', 'len(s) / n > 0.2:'),
    ("M32", 'return bool(pob) and not falla', 'return not falla'),
    ("M33", 'if c in CLASES_DECIDEN and n and', 'if c in ("pos_prot",) and n and'),
    ("M34", '    if fallas:\n        return out, fallas\n    filas, base', '    if False:\n        return out, fallas\n    filas, base'),
    ("M35", '    if malos:\n        return None, malos', '    if False:\n        return None, malos'),
    ("M36", 'identidad_ok=ident == IDENTIDAD_ESPERADA)', 'identidad_ok=True)'),
    ("M37", 'regla_minimas="SN")', 'regla_minimas="original")'),
    # ---- curva (VA168-02)
    ("M38", '<= TOL_GANANCIA_LOG10}', '> TOL_GANANCIA_LOG10}'),
    ("M39", '"ok": d2 > d0}', '"ok": d2 < d0}'),
    ("M40", 'return sesgo["sesgado"] or not out["ganancia_pareja"]["ok"]', 'return not out["ganancia_pareja"]["ok"]'),
    ("M41", 'max((p["z"] or 0) - 20, 0)', 'max((p["z"] or 0) - 90, 0)'),
    # ---- mitades, criterios, estado y parada
    ("M42", 'corte = noches[(len(noches) - 1) // 2]', 'corte = noches[len(noches) // 2]'),
    ("M43", 'p2k in ("GANA", "EMPATE", "SIN SUSTRATO")', 'p2k in ("GANA", "EMPATE")'),
    ("M44", 'silencio != "ENCIENDE DE MAS"', 'silencio != "X"'),
    ("M45", 'p2l not in ("PIERDE", "BLOQUEA")', 'p2l not in ("PIERDE",)'),
    ("M46", '"d": NICOLAS if cae_curva else est_d}', '"d": est_d}'),
    ("M47", 'c["estado"] = NO_CUMPLE if NO_CUMPLE in v else NICOLAS if NICOLAS in v else CUMPLE',
     'c["estado"] = NICOLAS if NICOLAS in v else NO_CUMPLE if NO_CUMPLE in v else CUMPLE'),
    ("M48", '"a": CUMPLE if not veta else NO_CUMPLE', '"a": CUMPLE'),
    ("M49", 'x["K"] and not x["X"][a]]', 'x["K"] and x["X"][a]]'),
    ("M50", 'x["c"] == "far_tabla" and E.publica(x, k))', 'x["c"] == "far_ocr" and E.publica(x, k))'),
    ("M51", '["criterios"]["estado"] != e:', '["criterios"]["estado"] == e:'),
    ("M52", 'noches >= PARADA_NOCHES and alertas >= PARADA_ALERTAS', 'noches >= PARADA_NOCHES or alertas >= PARADA_ALERTAS'),
    ("M53", 'if x["c"] in ("pos_prot", "pos_bajo"))', 'if x["c"] in ("pos_prot",))'),
    ("M54", 'PARADA_NOCHES, PARADA_ALERTAS = 30, 40', 'PARADA_NOCHES, PARADA_ALERTAS = 29, 40'),
    ("M55", '            reporte(res, pob, fuera, snpp)\n            cod = 0', '            reporte(res, pob, fuera, snpp)\n            cod = 3'),
]


def preparar(d, mut=None):
    if d.exists():
        shutil.rmtree(d)
    d.mkdir()
    shutil.copy2(AQUI / LS, d / LS)
    if mut:
        _id, viejo, nuevo = mut
        src = (d / LS).read_text(encoding="utf-8")
        assert src.count(viejo) == 1, (_id, src.count(viejo))
        (d / LS).write_text(src.replace(viejo, nuevo), encoding="utf-8")


def correr(d):
    p = subprocess.run([sys.executable, "-I", str(AQUI / "probar_sombra.py"), "--dir", str(d)],
                       capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=1800)
    falla = [x[6:].strip()[:70] for x in p.stdout.splitlines() if x.startswith("FALLA")]
    res = [x for x in p.stdout.splitlines() if x.startswith("RESULTADO")]
    if p.returncode == 0 and res:
        return "SOBREVIVE", falla
    if p.returncode == 1 and res:
        return "ATRAPADA", falla
    return "CAIDA", (p.stderr.strip().splitlines() or ["?"])[-1:]


def una(k, mut):
    d = AQUI.parent / f"_mut_sombra_{k}"
    try:
        preparar(d, mut)
        return correr(d)
    finally:
        if d.exists():
            shutil.rmtree(d)


def comprobar_unicas():
    src = (AQUI / LS).read_text(encoding="utf-8")
    return [(m[0], src.count(m[1])) for m in [CONTROL] + MUTACIONES if src.count(m[1]) != 1]


def main(argv=None):
    from concurrent.futures import ThreadPoolExecutor
    ap = argparse.ArgumentParser()
    ap.add_argument("--hilos", type=int, default=1)
    ap.add_argument("--solo", default="")
    a = ap.parse_args(argv)
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    L = []

    def pr(s):
        print(s, flush=True)
        L.append(s)
    malas = comprobar_unicas()
    if malas:
        print("mutaciones que no aparecen exactamente una vez:", malas)
        return 2
    sel = [m for m in MUTACIONES if not a.solo or m[0] in a.solo.split(",")]
    salida = AQUI / ("mutar_sombra_repaso_salida.txt" if a.solo else "mutar_sombra_salida.txt")
    try:
        e, f = una("identidad", None)
        pr(f"IDENTIDAD (copia sin mutar): {'PASA' if e == 'SOBREVIVE' else 'FALLA ' + e} {f[:3]}")
        e, f = una("control", CONTROL)
        pr(f"CONTROL (rompe la importación): {e} {f}  (tiene que ser CAIDA)")
        cuenta = {"ATRAPADA": 0, "SOBREVIVE": 0, "CAIDA": 0}
        with ThreadPoolExecutor(max_workers=a.hilos) as ex:
            resultados = list(ex.map(lambda m: una(m[0], m), sel))
        for m, (e, f) in zip(sel, resultados):
            cuenta[e] += 1
            pr(f"{m[0]} {e:9s} {f[:2]}")
        pr("")
        pr(f"RESULTADO: {cuenta['ATRAPADA']} de {len(sel)} atrapadas por aserción; sobreviven "
           f"{cuenta['SOBREVIVE']}; caídas {cuenta['CAIDA']}")
    finally:
        salida.write_text("".join(x + chr(10) for x in L), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
