# -*- coding: utf-8 -*-
"""Verificador del candado K, segunda vuelta: mutaciones contra el ARNES ENTERO de la ruta K.

A diferencia de v2_mutaciones_candado.py del primer verificador (que corria solo las cinco comprobaciones rapidas),
este corre probar_evaluar_diurno.py de la copia mutada con PROBAR_SOLO (por defecto 1,3,k), o sea: las comprobaciones
rapidas, los casos de punta a punta con --base k (k1 a k5), los casos 1 y 3 con base c0, y los casos 11, 12, 13, 21 y
14 que corren despues del bucle. Con el filtro, cobertura_workflow falla siempre (artefacto conocido: el caso 14 usa
las carpetas de los casos 7, 19 y 8, que el filtro no crea), asi que se descuenta.

Cada mutacion: copia los archivos de primer nivel de _s151_ab_diurno a experiments/_vk2_<nombre>/ (mismo nivel, para
que el evaluador ubique el repo por la profundidad de su carpeta), aplica UN reemplazo de texto (tiene que aparecer
exactamente una vez) en evaluar_diurno.py de la copia y corre su probar_evaluar_diurno.py. Borra la copia al terminar.
Clasificacion:
  ATRAPADA (prueba)  la linea AUTOPRUEBA lista alguna comprobacion fallida distinta de cobertura_workflow
  ATRAPADA (caida)   el arnes no llega a la linea AUTOPRUEBA (traza en la salida)
  NO ATRAPADA        solo falla cobertura_workflow
Uso: python m1_mutaciones_v2.py [nombre ...]     (sin nombres: todas; PROBAR_SOLO por variable SOLO, defecto 1,3,k)
"""
import concurrent.futures as cf
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

L = "    REGLA.update(cola_exacta=(base == \"k\"), w2_decide_nicolas=(base == \"k\"))"
MUT = {
    # --- las 15 del primer verificador (v2_mutaciones_candado.py), mismo texto
    "gt_en_g1": ("    p_cola = float(pmf[x_obs:].sum())", "    p_cola = float(pmf[x_obs + 1:].sum())"),
    "conservadora_en_g1": ("    p_cola = float(pmf[x_obs:].sum())", "    p_cola = float(pmf[max(x_obs - 1, 0):].sum())"),
    "xobs_menos_1": ("    x_obs = int(round(m1 * npos))", "    x_obs = int(round(m1 * npos)) - 1"),
    "xobs_mas_1": ("    x_obs = int(round(m1 * npos))", "    x_obs = int(round(m1 * npos)) + 1"),
    "k_sin_cola": (L, "    REGLA.update(cola_exacta=False, w2_decide_nicolas=(base == \"k\"))"),
    "k_sin_w2": (L, "    REGLA.update(cola_exacta=(base == \"k\"), w2_decide_nicolas=False)"),
    "control_siempre_ok": ("        ok = abs(frac - esperada) <= tol and pasa_b", "        ok = True"),
    "w2_sin_mirar_g1b": ("        if REGLA[\"w2_decide_nicolas\"] and g1b == \"CUMPLE\":", "        if REGLA[\"w2_decide_nicolas\"]:"),
    "h2a_apagado_en_evaluar": ("    if getattr(a, \"base\", \"c0\") == \"k\":", "    if False:"),
    "sha_opcional": ("        if a.base == \"k\" and not getattr(a, \"sha_codigo\", None):", "        if False:"),
    "h2b_silencioso": ("    raise SystemExit(\"--brazos %s sin --base: decir explícitamente el detector de base (c0 o k), adenda K §4 H2b\" % brazos)",
                       "    return \"c0\""),
    "h2a_solo_primera_raiz": ("            for p in sorted((Path(raiz) / BRAZOS[nombre]).glob(\"*.json\")):",
                              "            for p in sorted((Path(raices[0]) / BRAZOS[nombre]).glob(\"*.json\")):"),
    "h2a_solo_control": ("    for nombre in (\"control\", \"diurno\"):\n        for raiz in raices:",
                         "    for nombre in (\"control\",):\n        for raiz in raices:"),
    "h2a_solo_lascar": ("            for p in sorted((Path(raiz) / BRAZOS[nombre]).glob(\"*.json\")):",
                        "            for p in sorted((Path(raiz) / BRAZOS[nombre]).glob(\"Lascar.json\")):"),
    "h2a_sin_test1_roi": ("r.get(\"triggered_test1\") is True or r.get(\"final_hotspot_source\") == \"test1_roi\"",
                          "r.get(\"triggered_test1\") is True"),
    # --- nuevas (segunda vuelta)
    "h2b_c0_con_brazos_k": ("    if base == \"c0\" and not de_c0:", "    if False:"),
    "alfa_g1_010": ("    cumple = (p_cola < ALFA_G2) if REGLA", "    cumple = (p_cola < 0.10) if REGLA"),
    "alfa_g1_le": ("    cumple = (p_cola < ALFA_G2) if REGLA", "    cumple = (p_cola <= ALFA_G2) if REGLA"),
    "alfa_g1_0055": ("    cumple = (p_cola < ALFA_G2) if REGLA", "    cumple = (p_cola < 0.055) if REGLA"),
    "xobs_floor": ("    x_obs = int(round(m1 * npos))", "    x_obs = int(m1 * npos)"),
    "g1_estratos_juntos": ("    pmf = distribucion_x_exacta(est)\n    p_cola",
                           "    pmf = distribucion_x_exacta([tuple(map(sum, zip(*est)))])\n    p_cola"),
    "g1_siempre_cola": ("    cumple = (p_cola < ALFA_G2) if REGLA[\"cola_exacta\"] else (d > p95 + EPS_D)",
                        "    cumple = (p_cola < ALFA_G2)"),
    "g1_regla_inversa": ("    cumple = (p_cola < ALFA_G2) if REGLA[\"cola_exacta\"] else (d > p95 + EPS_D)",
                         "    cumple = (d > p95 + EPS_D) if REGLA[\"cola_exacta\"] else (p_cola < ALFA_G2)"),
    "cola_en_c0": (L, "    REGLA.update(cola_exacta=True, w2_decide_nicolas=(base == \"k\"))"),
    "w2_en_c0": (L, "    REGLA.update(cola_exacta=(base == \"k\"), w2_decide_nicolas=True)"),
    "control_tol_x10": ("        tol = 3 * math.sqrt(max(esperada * (1 - esperada), 1e-12) / N_BRAZOS_AZAR)",
                        "        tol = 30 * math.sqrt(max(esperada * (1 - esperada), 1e-12) / N_BRAZOS_AZAR)"),
    "control_tol_x5": ("        tol = 3 * math.sqrt(max(esperada * (1 - esperada), 1e-12) / N_BRAZOS_AZAR)",
                       "        tol = 15 * math.sqrt(max(esperada * (1 - esperada), 1e-12) / N_BRAZOS_AZAR)"),
    "control_xcrit_ultimo": ("        x_crit = criticos[0] if criticos else len(pmf)",
                             "        x_crit = criticos[-1] if criticos else len(pmf)"),
    "control_colas_gt": ("        colas = pmf[::-1].cumsum()[::-1]", "        colas = np.append(pmf[::-1].cumsum()[::-1][1:], 0.0)"),
    "control_sin_b": ("        ok = abs(frac - esperada) <= tol and pasa_b", "        ok = abs(frac - esperada) <= tol"),
    "control_solo_b": ("        ok = abs(frac - esperada) <= tol and pasa_b", "        ok = pasa_b"),
    "control_exacto_apagado": ("    if REGLA[\"cola_exacta\"]:\n        # Adenda K", "    if False:\n        # Adenda K"),
    "w2_con_sin_sustrato": ("        if REGLA[\"w2_decide_nicolas\"] and g1b == \"CUMPLE\":",
                            "        if REGLA[\"w2_decide_nicolas\"] and g1b != \"FALLA\":"),
    "h2a_solo_diurno": ("    for nombre in (\"control\", \"diurno\"):\n        for raiz in raices:",
                        "    for nombre in (\"diurno\",):\n        for raiz in raices:"),
    "h2a_ignora_ultima_raiz": ("    for nombre in (\"control\", \"diurno\"):\n        for raiz in raices:",
                               "    for nombre in (\"control\", \"diurno\"):\n        for raiz in raices[:-1]:"),
    "h2a_sha_prefijo7": ("        otro = sum(1 for r in recs if ((r.get(\"regimen\") or {}).get(\"codigo_sha\")) != sha)",
                         "        otro = sum(1 for r in recs if str((r.get(\"regimen\") or {}).get(\"codigo_sha\"))[:7] != sha[:7])"),
    "h2a_sin_regimen_ok": ("        otro = sum(1 for r in recs if ((r.get(\"regimen\") or {}).get(\"codigo_sha\")) != sha)",
                           "        otro = sum(1 for r in recs if ((r.get(\"regimen\") or {}).get(\"codigo_sha\", sha)) != sha)"),
    "h2a_no_bloquea": ("            controles.append(\"records de los brazos fuera de K o de otro commit (H2a)\")",
                       "            pass"),
    "h2a_sin_sha_ok": ("        return [\"sin --sha-codigo: no se puede comprobar el commit de los records (H2a)\"]",
                       "        return []"),
    "k_sin_flag_b22": ("                              \"ENABLE_MODIS_B22_PRIMARY\": True}}", "                              }}"),
    "estratos_con_tabla": ("        if c[\"ventana\"] not in ventanas or c[\"estado\"] == \"no_procesada\" or not ({\"pos\", \"neg\"} & c[\"pob\"]):",
                           "        if c[\"ventana\"] not in ventanas or c[\"estado\"] == \"no_procesada\":"),
    "veredicto_w2_antes_de_g3": ("    if res[\"G3\"] != \"CUMPLE\":\n        return \"INDECIDIBLE (G3",
                                 "    if False:\n        return \"INDECIDIBLE (G3"),
}


def copiar(dest):
    dest.mkdir(parents=True)
    for p in ORIG.iterdir():
        if p.is_file() and p.suffix in (".py", ".json"):
            shutil.copy2(p, dest / p.name)


def una(nombre):
    dest = EXP / ("_vk2_" + nombre)
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
        env = dict(os.environ, PYTHONIOENCODING="utf-8", PROBAR_SOLO=SOLO, PYTHONDONTWRITEBYTECODE="1")
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
        det += "".join("\n        " + f[:230] for f in fallas if "devolvi" not in f)
        return nombre, ("ATRAPADA (prueba)" if otras else "NO ATRAPADA"), det, dt
    finally:
        shutil.rmtree(dest, ignore_errors=True)


def main():
    nombres = sys.argv[1:] or (["ninguna"] + list(MUT))
    print("PROBAR_SOLO=%s | %d corridas | arnes y evaluador de %s" % (SOLO, len(nombres), ORIG))
    with cf.ThreadPoolExecutor(max_workers=int(os.environ.get("HILOS", "4"))) as ex:
        res = list(ex.map(una, nombres))
    for nombre, clase, det, dt in res:
        print("MUTACION %-26s %-18s %5.0f s | %s" % (nombre, clase, dt, det))
    print("\nRESUMEN")
    for nombre, clase, _d, _t in res:
        esperado = "OK" if nombre == "ninguna" else ""
        print("   %-26s %s" % (nombre, clase if nombre != "ninguna" else ("CONTROL OK" if clase == "NO ATRAPADA" else "CONTROL ROTO: " + clase)))


if __name__ == "__main__":
    main()
