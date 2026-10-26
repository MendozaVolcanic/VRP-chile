# -*- coding: utf-8 -*-
"""Verificador del candado K, TERCERA vuelta: repite las 42 mutaciones del autor (candado_k_s155/m1_mutaciones_v2.py,
leido antes de usarlo: copia los .py y .json de primer nivel a experiments/<prefijo><nombre>/, aplica UN reemplazo que
tiene que aparecer exactamente una vez y corre el arnes de la copia) y agrega mutaciones NUEVAS contra el codigo que
agrego el commit 1c1c2b1f (conteo de records de H2a, cero records, 40 caracteres, rotulo final) y contra la regla
sellada que ninguna prueba nombraba (simetria de la regla W2, G2 bajo base k, x_obs por techo, alfa compartido).

Las copias van a experiments/_vk3_<nombre>/ y se borran al terminar cada una.

Las dos preguntas del instrumento:
 1. Si la regla estuviera rota de esa forma, ¿esta medicion lo veria? Si: cada mutacion ES la regla rota, y se mira si
    alguna comprobacion con nombre falla.
 2. Si el instrumento estuviera muerto, ¿se veria distinto? Control «ninguna» (arbol sin mutar: solo puede fallar el
    artefacto conocido cobertura_workflow con el filtro) y control positivo: las mutaciones que la segunda vuelta ya
    vio atrapadas tienen que seguir atrapadas. Una mutacion que no se aplica (texto ausente o repetido) se informa como
    NO APLICADA, nunca como atrapada. Una que cae sin llegar a AUTOPRUEBA es ATRAPADA (caida), que NO cuenta.

Uso: SOLO=1,3,k HILOS=5 python m6_mutaciones_v3.py [nombre ...]
"""
import concurrent.futures as cf
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
ORIG = AQUI.parent                       # experiments/_s151_ab_diurno
EXP = ORIG.parent                        # experiments
SOLO = os.environ.get("SOLO", "1,3,k")

spec = importlib.util.spec_from_file_location("m1v2", ORIG / "candado_k_s155" / "m1_mutaciones_v2.py")
m1v2 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m1v2)
MUT = dict(m1v2.MUT)
VIEJAS = list(MUT)

NUEVAS = {
    # --- contra el codigo que agrego 1c1c2b1f
    "h2a_conteo_sin_acumular": ("                leidos += len(recs)", "                leidos = len(recs)"),
    "h2a_conteo_ultima_raiz": ("                conteo[nombre] = conteo.get(nombre, 0) + leidos",
                               "                conteo[nombre] = leidos"),
    "h2a_cero_solo_control": ("            if not leidos:\n", "            if not leidos and nombre == \"control\":\n"),
    "h2a_cero_solo_diurno": ("            if not leidos:\n", "            if not leidos and nombre == \"diurno\":\n"),
    "h2a_cero_apagado": ("            if not leidos:\n", "            if False:\n"),
    "h2a_cero_por_brazo_total": ("            if not leidos:\n", "            if not leidos and raiz == raices[0]:\n"),
    "sha40_desde_7": ("re.fullmatch(r\"[0-9a-f]{40}\", a.sha_codigo or \"\")", "re.fullmatch(r\"[0-9a-f]{7,40}\", a.sha_codigo or \"\")"),
    "sha40_desde_13": ("re.fullmatch(r\"[0-9a-f]{40}\", a.sha_codigo or \"\")", "re.fullmatch(r\"[0-9a-f]{13,40}\", a.sha_codigo or \"\")"),
    "sha40_match_prefijo": ("re.fullmatch(r\"[0-9a-f]{40}\", a.sha_codigo or \"\")", "re.match(r\"[0-9a-f]{12}\", a.sha_codigo or \"\")"),
    "sha40_apagado_c0": ("        if a.base == \"k\" and not re.fullmatch", "        if a.base == \"c0\" and not re.fullmatch"),
    "rotulo_siempre_adenda": ("\"§6 con la adenda K\" if REGLA[\"cola_exacta\"] else \"§6, regla original\"", "\"§6 con la adenda K\""),
    "rotulo_siempre_original": ("\"§6 con la adenda K\" if REGLA[\"cola_exacta\"] else \"§6, regla original\"", "\"§6, regla original\""),
    "linea_h2a_sin_conteo": ("        print(\"   H2a: %d records del control y %d del diurno leídos\" % (leidos.get(\"control\", 0), leidos.get(\"diurno\", 0)))",
                             "        print(\"   H2a: 1 records del control y 1 del diurno leídos\")"),
    # --- contra la regla sellada (veredicto y G1) que el commit no tocaba
    "w2_simetrica_adopta": ("    if g1b != \"CUMPLE\":\n        return \"DEPENDE DEL OCR",
                            "    if g1b != \"CUMPLE\" and not REGLA[\"w2_decide_nicolas\"]:\n        return \"DEPENDE DEL OCR"),
    "w2_k_decide_aunque_falle_sin_w2": ("        if REGLA[\"w2_decide_nicolas\"] and g1b == \"CUMPLE\":",
                                        "        if REGLA[\"w2_decide_nicolas\"] and g1b in (\"CUMPLE\", \"FALLA\"):"),
    "g2_ignorado_en_k": ("    if all(g == \"CUMPLE\" for g in g2):", "    if REGLA[\"cola_exacta\"] or all(g == \"CUMPLE\" for g in g2):"),
    "g2_uno_basta_en_k": ("    if all(g == \"CUMPLE\" for g in g2):", "    if (any if REGLA[\"cola_exacta\"] else all)(g == \"CUMPLE\" for g in g2):"),
    "controles_ignorados_en_k": ("    if controles:\n        return \"INDECIDIBLE (\"",
                                 "    if controles and not REGLA[\"cola_exacta\"]:\n        return \"INDECIDIBLE (\""),
    "repetir_ignorado_en_k": ("    if res[\"repetir\"]:", "    if res[\"repetir\"] and not REGLA[\"cola_exacta\"]:"),
    "g3_ignorado_en_k": ("    if res[\"G3\"] != \"CUMPLE\":\n        return \"INDECIDIBLE (G3",
                         "    if res[\"G3\"] != \"CUMPLE\" and not REGLA[\"cola_exacta\"]:\n        return \"INDECIDIBLE (G3"),
    "xobs_techo": ("    x_obs = int(round(m1 * npos))", "    x_obs = int(math.ceil(m1 * npos - 1e-9)) if REGLA[\"cola_exacta\"] else int(round(m1 * npos))"),
    "xobs_techo_crudo": ("    x_obs = int(round(m1 * npos))", "    x_obs = int(math.ceil(m1 * npos))"),
    "alfa_g1_0045": ("    cumple = (p_cola < ALFA_G2) if REGLA", "    cumple = (p_cola < 0.045) if REGLA"),
    "alfa_global_006": ("ALFA_G2 = 0.05 ", "ALFA_G2 = 0.06 "),
    "cola_exacta_fn_gt": ("    return float(pmf[max(x, 0):].sum()) if x < len(pmf) else 0.0",
                          "    return float(pmf[max(x, 0) + 1:].sum()) if x < len(pmf) else 0.0"),
    "h2a_sin_triggered": ("r.get(\"triggered_test1\") is True or r.get(\"final_hotspot_source\") == \"test1_roi\"",
                          "r.get(\"final_hotspot_source\") == \"test1_roi\""),
    "h2a_salta_C": ("            for p in sorted((Path(raiz) / BRAZOS[nombre]).glob(\"*.json\")):",
                    "            for p in sorted((Path(raiz) / BRAZOS[nombre]).glob(\"[!C]*.json\")):"),
    "h2a_solo_nocturnos": ("                t1 = sum(1 for r in recs if r.get(\"triggered_test1\") is True",
                           "                t1 = sum(1 for r in recs if str(r.get(\"datetime_utc\", \"\"))[11:13] < \"12\" and r.get(\"triggered_test1\") is True"),
    "cableado_log_sin_flags_k": ("            for c, v in DECLARADO[nombre].items():",
                                 "            for c, v in [(c, v) for c, v in DECLARADO[nombre].items() if c.startswith(\"ENABLE_DAYTIME\")]:"),
    "h2b_base_por_defecto_k": ("    if base is not None:\n        return base\n    if de_c0:\n        return \"c0\"",
                               "    if base is not None:\n        return base\n    if de_c0:\n        return \"c0\"\n    return \"k\""),
}
MUT.update(NUEVAS)


def copiar(dest):
    dest.mkdir(parents=True)
    for p in ORIG.iterdir():
        if p.is_file() and p.suffix in (".py", ".json"):
            shutil.copy2(p, dest / p.name)


def una(nombre):
    dest = EXP / ("_vk3_" + nombre)
    if dest.exists():
        shutil.rmtree(dest)
    copiar(dest)
    try:
        ruta = dest / "evaluar_diurno.py"
        src = ruta.read_text(encoding="utf-8")
        if nombre != "ninguna":
            a, b = MUT[nombre]
            n = src.count(a)
            if n != 1:
                return nombre, "NO APLICADA (el texto aparece %d veces)" % n, "", 0.0
            ruta.write_text(src.replace(a, b), encoding="utf-8")
        t0 = time.time()
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PROBAR_SOLO=SOLO, PYTHONDONTWRITEBYTECODE="1",
                   TMP="D:/vrp-trabajo/temporales/v3tmp", TEMP="D:/vrp-trabajo/temporales/v3tmp")
        if not SOLO:
            env.pop("PROBAR_SOLO")
        o = subprocess.run([sys.executable, str(dest / "probar_evaluar_diurno.py")], capture_output=True, text=True,
                           encoding="utf-8", errors="replace", env=env, cwd=str(dest))
        dt = time.time() - t0
        sal = o.stdout + "\n" + o.stderr
        m = re.search(r"AUTOPRUEBA: (\d+) de (\d+) comprobaciones OK(?: \| FALLAN: (\[.*?\]))?", sal)
        fallas = [x.strip() for x in sal.splitlines() if "[FALLA]" in x]
        if not m:
            cola = [x for x in sal.strip().splitlines() if x.strip()][-3:]
            return nombre, "ATRAPADA (caida)", " / ".join(cola), dt
        fallan = eval(m.group(3)) if m.group(3) else []
        otras = [f for f in fallan if f != "cobertura_workflow"]
        det = "%s de %s OK | fallan %s" % (m.group(1), m.group(2), fallan)
        det += "".join("\n        " + f[:260] for f in fallas if "devolvi" not in f)
        return nombre, ("ATRAPADA (prueba)" if otras else "NO ATRAPADA"), det, dt
    finally:
        shutil.rmtree(dest, ignore_errors=True)


def main():
    nombres = sys.argv[1:] or (["ninguna"] + list(MUT))
    print("PROBAR_SOLO=%r | %d corridas | arnes y evaluador de %s | viejas %d, nuevas %d"
          % (SOLO, len(nombres), ORIG, len(VIEJAS), len(NUEVAS)))
    with cf.ThreadPoolExecutor(max_workers=int(os.environ.get("HILOS", "4"))) as ex:
        res = list(ex.map(una, nombres))
    for nombre, clase, det, dt in res:
        print("MUTACION %-34s %-18s %5.0f s | %s" % (nombre, clase, dt, det))
    print("\nRESUMEN")
    for nombre, clase, _d, _t in res:
        grupo = "control" if nombre == "ninguna" else ("vieja" if nombre in VIEJAS else "NUEVA")
        print("   %-7s %-34s %s" % (grupo, nombre, clase))


if __name__ == "__main__":
    main()
