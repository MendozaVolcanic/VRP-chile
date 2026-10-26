# -*- coding: utf-8 -*-
"""Verificador del candado K (PR #858), parte 2: ¿las pruebas NUEVAS del arnés ven un candado roto?

Para cada mutación: copia evaluar_diurno.py (sin tocar el original) a un temporal, aplica UNA mutación, la registra
como `evaluar_diurno` y corre, en un proceso aparte, las cinco comprobaciones rápidas del arnés que no dependen de la
batería larga (chequear_orden_del_nulo, chequear_base_k, chequear_cola_exacta, chequear_regla_w2, chequear_h2a_h2b).
La batería larga (main) corre siempre con la base por defecto (c0) y nunca pasa --brazos ni --base, así que no puede
ver ninguna mutación que sólo actúe con base k (eso se comprueba aparte con grep, ver INFORME).
ATRAPADA = alguna comprobación da FALLA o el arnés se cae con un error que no es de importación de la mutación.
Uso: python -I v2_mutaciones_candado.py            (todas, en serie)
     python -I v2_mutaciones_candado.py <nombre>   (una)
"""
import contextlib
import importlib.util
import io
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

AQUI = Path(__file__).resolve().parent
EXP = AQUI.parent
RAIZ = EXP.parents[1]
MUT = {
    "gt_en_g1": ('    p_cola = float(pmf[x_obs:].sum())', '    p_cola = float(pmf[x_obs + 1:].sum())'),
    "conservadora_en_g1": ('    p_cola = float(pmf[x_obs:].sum())', '    p_cola = float(pmf[max(x_obs - 1, 0):].sum())'),
    "xobs_menos_1": ('    x_obs = int(round(m1 * npos))', '    x_obs = int(round(m1 * npos)) - 1'),
    "xobs_mas_1": ('    x_obs = int(round(m1 * npos))', '    x_obs = int(round(m1 * npos)) + 1'),
    "k_sin_cola": ('    REGLA.update(cola_exacta=(base == "k"), w2_decide_nicolas=(base == "k"))',
                   '    REGLA.update(cola_exacta=False, w2_decide_nicolas=(base == "k"))'),
    "k_sin_w2": ('    REGLA.update(cola_exacta=(base == "k"), w2_decide_nicolas=(base == "k"))',
                 '    REGLA.update(cola_exacta=(base == "k"), w2_decide_nicolas=False)'),
    "control_siempre_ok": ('        ok = abs(frac - esperada) <= tol and pasa_b', '        ok = True'),
    "w2_sin_mirar_g1b": ('        if REGLA["w2_decide_nicolas"] and g1b == "CUMPLE":', '        if REGLA["w2_decide_nicolas"]:'),
    "h2a_apagado_en_evaluar": ('    if getattr(a, "base", "c0") == "k":', '    if False:'),
    "sha_opcional": ('        if a.base == "k" and not getattr(a, "sha_codigo", None):', '        if False:'),
    "h2b_silencioso": ('    raise SystemExit("--brazos %s sin --base: decir explícitamente el detector de base (c0 o k), adenda K §4 H2b" % brazos)',
                       '    return "c0"'),
    "h2a_solo_primera_raiz": ('            for p in sorted((Path(raiz) / BRAZOS[nombre]).glob("*.json")):',
                              '            for p in sorted((Path(raices[0]) / BRAZOS[nombre]).glob("*.json")):'),
    "h2a_solo_control": ('    for nombre in ("control", "diurno"):\n        for raiz in raices:',
                         '    for nombre in ("control",):\n        for raiz in raices:'),
    "h2a_solo_lascar": ('            for p in sorted((Path(raiz) / BRAZOS[nombre]).glob("*.json")):',
                        '            for p in sorted((Path(raiz) / BRAZOS[nombre]).glob("Lascar.json")):'),
    "h2a_sin_test1_roi": ('r.get("triggered_test1") is True or r.get("final_hotspot_source") == "test1_roi"',
                          'r.get("triggered_test1") is True'),
}
FUNCIONES = ("chequear_orden_del_nulo", "chequear_base_k", "chequear_cola_exacta", "chequear_regla_w2", "chequear_h2a_h2b")


def una(nombre):
    src = (EXP / "evaluar_diurno.py").read_text(encoding="utf-8")
    src = src.replace("AQUI = Path(__file__).resolve().parent", "AQUI = Path(r\"%s\")" % EXP)
    if nombre != "ninguna":
        a, b = MUT[nombre]
        if src.count(a) != 1:
            print("MUTACION %s: el texto aparece %d veces, no se aplica" % (nombre, src.count(a)))
            return 9
        src = src.replace(a, b)
    tmp = Path(tempfile.mkdtemp(prefix="verif_candado_"))
    ruta = tmp / "evaluar_diurno.py"
    ruta.write_text(src, encoding="utf-8")
    for p in (str(RAIZ / "scripts"), str(RAIZ), str(EXP)):
        sys.path.insert(0, p)
    spec = importlib.util.spec_from_file_location("evaluar_diurno", ruta)
    m = importlib.util.module_from_spec(spec)
    sys.modules["evaluar_diurno"] = m
    spec.loader.exec_module(m)
    spec2 = importlib.util.spec_from_file_location("probar_evaluar_diurno", EXP / "probar_evaluar_diurno.py")
    PE = importlib.util.module_from_spec(spec2)
    spec2.loader.exec_module(PE)
    buf = io.StringIO()
    caida = None
    with contextlib.redirect_stdout(buf):
        for f in FUNCIONES:
            try:
                getattr(PE, f)()
            except BaseException as e:  # noqa: BLE001
                caida = "%s en %s: %s" % (type(e).__name__, f, e)
                break
    malos = [c for c, ok in PE.RESULTADOS if not ok]
    fallas = [x for x in buf.getvalue().splitlines() if "[FALLA]" in x]
    print("MUTACION %s | %d de %d comprobaciones OK | fallan %s | caida %s" % (
        nombre, len(PE.RESULTADOS) - len(malos), len(PE.RESULTADOS), sorted(set(malos)), caida))
    for x in fallas:
        print("      " + x.strip()[:200])
    return 1 if (malos or caida) else 0


def main():
    if len(sys.argv) > 1:
        return una(sys.argv[1])
    resumen = []
    for nombre in ["ninguna"] + list(MUT):
        o = subprocess.run([sys.executable, "-I", str(Path(__file__)), nombre], capture_output=True, text=True,
                           encoding="utf-8", env=dict(__import__("os").environ, PYTHONIOENCODING="utf-8"))
        lineas = [x for x in o.stdout.splitlines() if x.startswith("MUTACION") or x.startswith("      ")]
        print("\n".join(lineas) if lineas else "MUTACION %s SE CAYO: %s" % (nombre, o.stderr.strip().splitlines()[-3:]))
        rc = o.returncode
        bien = (rc == 0) if nombre == "ninguna" else (rc == 1)
        resumen.append((nombre, rc, bien))
    print("\nRESUMEN (ninguna tiene que dar rc 0; cada mutación, rc 1 = ATRAPADA)")
    for nombre, rc, bien in resumen:
        print("   %-26s rc=%s %s" % (nombre, rc, "ATRAPADA" if (bien and nombre != "ninguna") else ("OK" if bien else "NO ATRAPADA" if nombre != "ninguna" else "FALLA EL CONTROL")))


if __name__ == "__main__":
    sys.exit(main())
