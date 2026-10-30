# -*- coding: utf-8 -*-
"""S168 V375-E (S169: 14 del verificador, 39 de las reglas nuevas de §11.11 y 27 de la ronda 2, §11.12, y 1 de la ronda 3, §11.13): nulo de la batería del lector de la sombra por mutaciones de una línea (mismo método que
experiments/_s162_v375/e_adenda2/mutar_adenda2.py: S156, cuenta como ATRAPADA sólo la mutación que la batería rechaza
por aserción; una que hace caer la batería con una excepción es CAÍDA y no cuenta).

Cada mutación cambia UN texto que aparece exactamente una vez en leer_sombra_v375e.py, en una copia propia
(`experiments/_s168/_mut_sombra_<id>/`, a la misma profundidad que la carpeta original para que el lector encuentre la
raíz del repo; borrada al terminar), y corre `probar_sombra.py --dir <copia>`.
  ATRAPADA   la batería sale 1 con su línea RESULTADO (alguna aserción falló y ninguna sección se cayó)
  SOBREVIVE  la batería sale 0 (la mutación no se ve)
  CAÍDA      la batería sale 2 (alguna sección lanzó una excepción, ronda 2 VL169-02) o se cae sin línea RESULTADO:
             no cuenta como atrapada aunque además falle alguna aserción
Controles: IDENTIDAD (la copia sin mutar tiene que PASAR), CONTROL (una mutación que rompe la importación tiene que
salir CAÍDA) y CONTROL_SECCION (una que lanza dentro de una sección tiene que salir CAÍDA, no ATRAPADA). Las
equivalentes (EQUIVALENTES, declaradas antes de correr) se informan aparte. Hilos: --hilos (1 por defecto; el cupo pesado del equipo es compartido).
Ronda 3 (PREREGISTRO_E.md §11.13, VL2-01 y VL2-02): aborta (sale 2) sin mutar nada si no corre en un checkout de
claude/s169-v375e-lector, si la identidad no pasa o si CONTROL o CONTROL_SECCION no salen CAIDA; una corrida que pasa
de TOPE_S es CAIDA; cada resultado se agrega al archivo de salida apenas termina, y una corrida nueva se salta las
mutaciones ya escritas (retoma). Sale 0 si no sobrevive ninguna no equivalente, 1 si sobrevive alguna o falta alguna.
Uso: python -I mutar_sombra.py [--hilos N] [--solo ID,ID] [--arranque]
     (escribe mutar_sombra_salida.txt; _repaso con --solo; _arranque con --arranque, que sólo corre identidad y controles)
"""
from __future__ import annotations

import argparse
import collections
import io
import os
import shutil
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
LS = "leer_sombra_v375e.py"

CONTROL = ("CONTROL", "import numpy as np\n", "import numpy_no_existe as np\n")
# VL169-02: una excepción dentro de una sección de la batería tiene que salir CAIDA, no ATRAPADA
CONTROL_SECCION = ("CONTROL_SECCION", "    return frozenset(out)\n",
                   "    raise RuntimeError(\"control de caída en una sección\")\n")
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
    ("M20", 'desde == DESDE_P and hasta >= desde', 'hasta >= desde'),
    ("M21", 'and len(claves) == len(set(claves)), \\', 'and True, \\'),
    ("M22", 'if not (desde <= o["noche"] <= hasta)]', 'if not (o["noche"] <= hasta)]'),
    ("M23", 'return r == [True, False, True], r', 'return True, r'),
    ("M24", 'return False, "sin pasada de la vía', 'return True, "sin pasada de la vía'),
    ("M25", 'ok2 = ok2 and identidad_ok', 'ok2 = ok2'),
    ("M26", '> TOL_UNO_KM]', '> 1.0]'),
    ("M27", 'return bool(uno) and not malos', 'return not malos'),
    ("M28", 'return len(usa) > 0 and not malos', 'return not malos'),
    ("M29", '!= info[o["id"]]["dc"]]', '== info[o["id"]]["dc"]]'),
    ("M30", 'return bool(casos) and dist == 0', 'return dist == 0'),
    ("M31", 'len(s) / n > UMBRAL_COBERTURA:', 'len(s) / n > 0.2:'),
    ("M32", 'return bool(pob) and not falla', 'return not falla'),
    ("M33", 'if c in CLASES_DECIDEN and n and', 'if c in ("pos_prot",) and n and'),
    ("M34", '    if fallas:\n        red = {k: out[k]', '    if False:\n        red = {k: out[k]'),
    ("M35", '    if malos:\n        return None, malos', '    if False:\n        return None, malos'),
    ("M36", 'identidad_ok=ident == IDENTIDAD_ESPERADA,', 'identidad_ok=True,'),
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
    ("M53", 'int(o["clase"] in ("pos_prot", "pos_bajo"))', 'int(o["clase"] in ("pos_prot",))'),
    ("M54", 'PARADA_NOCHES, PARADA_ALERTAS = 30, 40', 'PARADA_NOCHES, PARADA_ALERTAS = 29, 40'),
    ("M55", 'cod = {"decide": 0,', 'cod = {"decide": 3,'),
    # ---- S169: las 14 que el verificador de S168 creía que sobreviven (INFORME.md, «Mutaciones que creo...»)
    ("V01", '("S6", ok6, d6)', '("S6", True, d6)'),
    ("V02", 'hay_neg = all(N_neg.get(c, 0) for c in E.CLASES_NEG)', 'hay_neg = True'),
    ("V03", 'est_c = estado_c_sombra(m["veredicto"], LP)', 'est_c = CUMPLE'),
    ("V04", 'c = criterios_sombra(veta, p2k["veredicto"], silencio, p2l["veredicto"], est_c,',
     'c = criterios_sombra(veta, p2l["veredicto"], silencio, p2k["veredicto"], est_c,'),
    ("V05", 'est_d = LP.estado_d_sombra(cur_p["condicionada"], cur_k["condicionada"])',
     'est_d = LP.estado_d_sombra(cur_k["condicionada"], cur_p["condicionada"])'),
    ("V06", 'est_c, cae_curva or cae_k, est_d,', 'est_c, False, est_d,'),
    ("V07a", '[x for x in filas if x["noche"] > corte]', '[x for x in filas if x["noche"] >= corte]'),
    ("V07b", '"P2_K": E.p2(sel, a, "K")["veredicto"]', '"P2_K": E.p2(sel, "K", "K")["veredicto"]'),
    ("V07c", 'EC.decidir_estrato(P, "informa")[0], "P2_K"', 'EC.decidir_estrato(P, "decide")[0], "P2_K"'),
    ("V08a", 'TOL_UNO_KM = 0.0051 ', 'TOL_UNO_KM = 0.0101 '),
    ("V08b", 'TOL_UNO_KM = 0.0051 ', 'TOL_UNO_KM = 0.0011 '),
    ("V09", 'BORDE_KM = 0.005 ', 'BORDE_KM = 0.0045 '),
    ("V10", 'UMBRAL_COBERTURA = 0.10 ', 'UMBRAL_COBERTURA = 0.12 '),
    ("V11", 'INFORMAN = (("VIA", "radiante"), ("VIA", "sinfiltro"))', 'INFORMAN = (("VIA", "radiante"),)'),
    ("V12", '* 1.2) for p in pas]', '* 1.0) for p in pas]'),
    ("V13", 'publicar, LP, n_max=20):', 'publicar, LP, n_max=1):'),
    ("V14", 'return desde == DESDE_P and hasta >= desde', 'return desde >= DESDE_P and hasta >= desde'),
    # ---- S169: una o más por regla nueva del §11 (tabla de §11.11)
    ("N01", '    pob = [o for o in pob if o["noche"] <= corte]\n', '    pob = list(pob)\n'),
    ("N02", 'corte = n_par if alcanzada else hasta', 'corte = hasta'),
    ("N03", '    if not alcanzada:\n        return out, fallas\n', '    if False:\n        return out, fallas\n'),
    ("N04", 'for n in sorted(por_noche):', 'for n in sorted(por_noche, reverse=True):'),
    ("N05", 'if Path(dsal).exists() and any(Path(dsal).glob("lectura_sombra_corte_*")):', 'if False:'),
    ("N06", 'f"lectura_sombra_corte_{corte}"', 'f"lectura_sombra_corte"'),
    ("N07", "pr(f\"  {k} {'OK' if v['ok'] else 'CAE: ' + MOTIVO[k]}\")",
     "pr(f\"  {k} {'OK' if v['ok'] else 'CAE'}: {v['detalle']}\")"),
    ("N08", 'reporte_controles(res, detalle=tipo == "decide")', 'reporte_controles(res, detalle=True)'),
    ("N09", 'sal = {"controles": {k: {"ok": v["ok"], "motivo": "" if v["ok"] else MOTIVO[k]}',
     'sal = {"controles": {k: v'),
    ("N10", 'veta += [(o["volcan"], o["hora_utc"]) for o in sin_dato_prot if o["pub_prod"]]', 'veta += []'),
    ("N11", 'for o in sin_dato_prot if o["pub_prod"]]', 'for o in sin_dato_prot]'),
    ("N12", 'o["clase"] == "pos_prot" and o["id"] not in arms]', 'o["clase"] == "pos_prot" and o["id"] in arms]'),
    ("N13", 'for p, s in list(SHA_DEPS.items()) + list(SHA_SELLO_LECTOR.items())', 'for p, s in list(SHA_DEPS.items())'),
    ("N14", 'paquete(pob, arms, deps, regimen_ok=ok8)\n    ids_borde', 'paquete(pob, arms, deps, regimen_ok=True)\n    ids_borde'),
    ("N15", '            if c[k] == CUMPLE:\n', '            if c[k] == "X":\n'),
    ("N16", 'f = diff_fn(base, s)', 'f = diff_fn(s, s)'),
    ("N17", 'if reg.get("perfil") != perfil:', 'if False:'),
    ("N18", '    shas[commit] += 0\n', '    pass\n'),
    ("N19", '            cambios[str(s)] = "sin sha"\n', '            pass\n'),
    ("N20", '            cambios[s] = "git no lo resuelve"\n', '            pass\n'),
    ("N21", '+ timedelta(days=REZAGO_DIAS)', '+ timedelta(days=0)'),
    ("N22", 'REZAGO_DIAS = 2 ', 'REZAGO_DIAS = 1 '),
    ("N23", '    if alcanzada:\n        ctl.append', '    if False:\n        ctl.append'),
    ("N24", 'return not malos, {"n": len(malos)}', 'return True, {"n": len(malos)}'),
    ("N25", '("S10", ok10, d10)]', '("S10", True, d10)]'),
    ("N26", '<= TOL_S4_KM}', '< 0}'),
    ("N27", 'return ok and sustrato,', 'return ok,'),
    ("N28", 'return NICOLAS if veredicto_m == "SIN SUSTRATO" else LP.estado_c(veredicto_m)', 'return LP.estado_c(veredicto_m)'),
    ("N29", 'cae_k, ctl_k = controles_curva([x for x in filas if x["c"] not in LP.CLASES_FAR], "K", E, CC)',
     'cae_k, ctl_k = False, {}'),
    ("N30", 'if fl and (nom == "conjunta" or fl != conj):', 'if fl and nom == "conjunta":'),
    ("N31", 'if (es_alerta and cl == "summit") or (not es_alerta and cl == "far"):', 'if es_alerta:'),
    ("N32", 'for nom, f in vueltas:', 'for nom, f in vueltas[:1]:'),
    ("N33", 'sin_rec = {k[0]: n for k, n in B.alertas_sin_record(pv, rc).items()}', 'sin_rec = {}'),
    ("N34", '"lejanas_ocr": lej["far_ocr"]', '"lejanas_ocr": lej["far_tabla"]'),
    ("N35", '        if a == DECIDE:\n            pr(f"  criterios:', '        if True:\n            pr(f"  criterios:'),
    ("N36", '({k: v for k, v in r.items() if k != "criterios"} if a != DECIDE else r)', '(r if a != DECIDE else r)'),
    ("N37", 'ap.add_argument("--commit", required=True)', 'ap.add_argument("--commit", default=None)'),
    ("N38", '"b_sin_evidencia": (not hay_neg) and p2k["veredicto"] == "SIN SUSTRATO",', '"b_sin_evidencia": False,'),
    ("N39", '"lista": s}', '"lista": s[:10]}'),
    # ---- S169 ronda 2 (verificador de S169, VL169-01 a 08; §11.12)
    ("R01", '    RAIZ / "pipeline" / "store.py": "baa430d11f2868ab22835ef0486f3145c6279ad48fb155b1ce40bcfb49b5b9d1",\n', ''),
    ("R02", 'if os.environ.get("VRP_PROFILE", PERFIL_K) != PERFIL_K:', 'if False:'),
    ("R03", '    os.environ["VRP_PROFILE"] = PERFIL_K\n', '    pass\n'),
    ("R04", 'RUTAS_REGIMEN = ("pipeline/", "volcanoes.yaml", ', 'RUTAS_REGIMEN = ("pipeline/", '),
    ("R05", 'return ast_sin_docstrings(viejo) != ast_sin_docstrings(nuevo)', 'return viejo != nuevo'),
    ("R06", 'nodo.body = nodo.body[1:] or [ast.Pass()]', 'nodo.body = nodo.body'),
    ("R07", 'return ruta in PERFILES_REGIMEN and viejo != nuevo', 'return viejo != nuevo'),
    ("R08", '                v.pop(k, None)\n', '                pass\n'),
    ("R09", 'return grillas_sin_roi(viejo) != grillas_sin_roi(nuevo)', 'return False'),
    ("R10", 'ilegible: falla cerrada\n            return True', 'ilegible: falla cerrada\n            return False'),
    ("R11", '    if viejo is None or nuevo is None:\n        return True', '    if viejo is None or nuevo is None:\n        return False'),
    ("R12", 'and f.get("sensor_bucket") == "VIIRS375"', 'and True'),
    ("R13", '            red["parada"] = cont', '            pass'),
    ("R14", '        if res.get("parada") and not res.get("parada_alcanzada"):\n            pa = res["parada"]',
     '        if False:\n            pa = res["parada"]'),
    ("R15", '        if out.get("parada") and not out.get("parada_alcanzada"):', '        if False:'),
    ("R16", 'if any(r.get("tipo") == "lectura" for r in registro_local()):', 'if False:'),
    ("R17", 'motivos.append(f"{REF_REGISTRO} no se puede resolver: haz git fetch origin")', 'pass'),
    ("R18", '    elif any(r.get("tipo") == "lectura" for r in rem):', '    elif False:'),
    ("R19", '        anotar_registro({"tipo": "lectura",', '        dict({"tipo": "lectura",'),
    ("R20", '        return 2\n    deps, malos = cargar_deps()', '        pass\n    deps, malos = cargar_deps()'),
    ("R21", 'out.append({"tipo": "lectura", "ilegible": x[:80]})', 'pass'),
    ("R22", 'return leer_registro(mostrar_git(REF_REGISTRO, RUTA_REGISTRO_GIT))', 'return None'),
    ("R24", 'key=lambda x: x[0])\n    return con[0][1]', 'key=lambda x: x[0], reverse=True)\n    return con[0][1]'),
    ("R25", 'else sello}', 'else []}'),
    ("R26", '    if not base:\n        cambios["base"]', '    if False:\n        cambios["base"]'),
    ("R27", '            cambios[s] = f\n    sello', '            pass\n    sello'),
    # ---- S169 ronda 3 (VL2-04): la lectura que decide va sólo a archivo
    ("R28", '        PANTALLA[0] = False\n', '        pass\n'),
    ("R23", '^{{commit}}")[0] != 0:\n        return None\n    return leer_registro', '^{{commit}}")[0] != 0:\n        return []\n    return leer_registro'),
]
# VL169-10: equivalentes declaradas ANTES de correr (sobrevivir no las hace sospechosas)
EQUIVALENTES = {
    "V04": "en el alfabeto de regla_signos (GANA, EMPATE, SIN SUSTRATO, PIERDE, BLOQUEA) lo que (b) acepta para P2 es el "
           "complemento exacto de lo que rechaza para P2-L, así que cruzarlos da el mismo (b) (PREREGISTRO_E §11.10)",
}


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


RAMA = "claude/s169-v375e-lector"
TOPE_S = 5400          # ronda 3 (VL2-01): una corrida de la batería que pase de aquí es CAIDA, no hunde el nulo


def correr(d):
    try:
        p = subprocess.run([sys.executable, "-I", str(AQUI / "probar_sombra.py"), "--dir", str(d)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=TOPE_S)
    except subprocess.TimeoutExpired:
        return "CAIDA", [f"pasó el tope de {TOPE_S} s"]
    falla = [x[6:].strip()[:70] for x in p.stdout.splitlines() if x.startswith("FALLA")]
    res = [x for x in p.stdout.splitlines() if x.startswith("RESULTADO")]
    if p.returncode == 0 and res:
        return "SOBREVIVE", falla
    if p.returncode == 1 and res:
        return "ATRAPADA", falla
    if p.returncode == 2 and res:       # VL169-02: una sección se cayó
        return "CAIDA", [x[7:].strip()[:70] for x in p.stdout.splitlines() if x.startswith("CAE")][:2]
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
    return [(m[0], src.count(m[1])) for m in [CONTROL, CONTROL_SECCION] + MUTACIONES if src.count(m[1]) != 1]


def _git(*args):
    try:
        p = subprocess.run(["git", "-C", str(AQUI.parents[2])] + list(args), capture_output=True, text=True,
                           timeout=60)
    except (OSError, subprocess.SubprocessError):
        return None, ""
    return p.returncode, p.stdout.strip()


def en_la_rama():
    """Ronda 3 (VL2-02): el nulo corre en un checkout de RAMA (la rama, o un commit contenido en origin/RAMA, como el
    tag), nunca en loop/activo ni en main. Devuelve (sí o no, qué hay en HEAD)."""
    rc, rama = _git("rev-parse", "--abbrev-ref", "HEAD")
    if rc == 0 and rama == RAMA:
        return True, rama
    rc2, _ = _git("merge-base", "--is-ancestor", "HEAD", f"origin/{RAMA}")
    return rc2 == 0 and rama not in ("loop/activo", "main"), rama


def leer_hechas(salida):
    """Las mutaciones ya escritas en el archivo de resultados ({id: estado}), para retomar un nulo cortado."""
    out = {}
    if salida.exists():
        for x in salida.read_text(encoding="utf-8").splitlines():
            p = x.split()
            if len(p) >= 3 and p[0] == "MUT":
                out[p[1]] = p[2]
    return out


def main(argv=None):
    from concurrent.futures import ThreadPoolExecutor, as_completed
    from datetime import datetime, timezone
    ap = argparse.ArgumentParser()
    ap.add_argument("--hilos", type=int, default=1)
    ap.add_argument("--solo", default="")
    ap.add_argument("--arranque", action="store_true",
                    help="sólo identidad y controles, sin mutar nada (para comprobar el arranque antes del nulo)")
    a = ap.parse_args(argv)
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    salida = AQUI / ("mutar_sombra_arranque_salida.txt" if a.arranque else
                     "mutar_sombra_repaso_salida.txt" if a.solo else "mutar_sombra_salida.txt")

    def anotar(s):
        """Cada línea va al disco apenas se sabe (VL2-01): un corte no pierde lo hecho."""
        print(s, flush=True)
        with open(salida, "a", encoding="utf-8") as fh:
            fh.write(s + "\n")
            fh.flush()
            os.fsync(fh.fileno())

    malas = comprobar_unicas()
    if malas:
        print("mutaciones que no aparecen exactamente una vez:", malas)
        return 2
    ok_rama, rama = en_la_rama()
    _, head = _git("rev-parse", "HEAD")
    anotar(f"== corrida {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')} | HEAD {head} ({rama}) | "
           f"hilos {a.hilos} | tope {TOPE_S} s")
    if not ok_rama:
        anotar(f"ABORTA: no corre en un checkout de {RAMA} (HEAD en {rama}); no se muta nada")
        return 2
    sel = [m for m in MUTACIONES if not a.solo or m[0] in a.solo.split(",")]
    e, f = una("identidad", None)
    anotar(f"IDENTIDAD (copia sin mutar): {'PASA' if e == 'SOBREVIVE' else 'FALLA ' + e} {f[:3]}")
    if e != "SOBREVIVE":
        anotar("ABORTA: la identidad no pasa (la batería falla sin mutar nada); no se muta nada")
        return 2
    for nom, ctl, que in (("CONTROL", CONTROL, "rompe la importación"),
                          ("CONTROL_SECCION", CONTROL_SECCION, "lanza dentro de una sección")):
        e, f = una(nom.lower(), ctl)
        anotar(f"{nom} ({que}): {e} {f}  (tiene que ser CAIDA)")
        if e != "CAIDA":
            anotar(f"ABORTA: {nom} no sale CAIDA; no se muta nada")
            return 2
    if a.arranque:
        anotar("ARRANQUE OK: la identidad pasa y los dos controles salen CAIDA; no se mutó nada (--arranque)")
        return 0
    hechas = leer_hechas(salida)
    pendientes = [m for m in sel if m[0] not in hechas]
    anotar(f"retoma: {sum(1 for m in sel if m[0] in hechas)} ya escritas en {salida.name}, {len(pendientes)} pendientes")
    with ThreadPoolExecutor(max_workers=a.hilos) as ex:
        futuros = {ex.submit(una, m[0], m): m for m in pendientes}
        for fu in as_completed(futuros):
            m = futuros[fu]
            try:
                e, f = fu.result()
            except Exception as x:      # noqa: BLE001  una mutación que rompe el instrumento no hunde a las demás
                e, f = "CAIDA", [repr(x)[:120]]
            anotar(f"MUT {m[0]} {e} {f[:2]}" + (" (equivalente declarada)" if m[0] in EQUIVALENTES else ""))
    hechas = leer_hechas(salida)
    est = {m[0]: hechas.get(m[0], "FALTA") for m in sel}
    cuenta = collections.Counter(est.values())
    eq = [k for k in est if k in EQUIVALENTES]
    vivas = sorted(k for k, v in est.items() if v == "SOBREVIVE" and k not in EQUIVALENTES)
    anotar("")
    anotar(f"CAIDAS (no cuentan como atrapadas): {sorted(k for k, v in est.items() if v == 'CAIDA')}")
    anotar(f"SOBREVIVEN: {sorted(k for k, v in est.items() if v == 'SOBREVIVE')} (equivalentes declaradas antes de "
           f"correr: {eq})")
    anotar(f"RESULTADO: {cuenta['ATRAPADA']} de {len(sel)} atrapadas por aserción ({len(sel) - len(eq)} no "
           f"equivalentes); sobreviven {cuenta['SOBREVIVE']}; caídas {cuenta['CAIDA']}; faltan {cuenta['FALTA']}")
    return 1 if (vivas or cuenta["FALTA"]) else 0


if __name__ == "__main__":
    sys.exit(main())
