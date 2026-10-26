# -*- coding: utf-8 -*-
"""LIBRO DE CUENTAS — cada número que el proyecto afirma, recalculado hoy.

POR QUÉ EXISTE
==============
Las afirmaciones cuantitativas de este proyecto no se olvidan: **se pudren en
silencio**. Eran ciertas cuando se escribieron, el pipeline y los volcanes
cambiaron, y nadie volvió a medirlas porque no había nada que las recalculara.

La prueba está en el propio `CLAUDE.md`, que tiene **siete reglas marcadas
«⚠️ OBSOLETA»** —A7, A13, A17, A23, A36, A42, A82— todas descubiertas a mano,
sesiones después, por casualidad. Y en S128: A12 decía «Isluga ~20 K» y da 8,3;
D5 decía «1,35×» y el valor real es 0,73, con el signo invertido; D9 citaba un
residuo de «24-83×» que era anterior a nadir-fijo; el `.git` de «3,1 GB» eran 10,6.

Este script recalcula lo que se puede recalcular y —tan importante como eso—
**publica la lista de afirmaciones que NO tienen instrumento**. Esa lista es el
inventario honesto de lo que el proyecto cree sin poder verificar.

CÓMO ESTÁ HECHO
===============
Deliberadamente NO intenta parsear cada número de cada documento: eso es frágil y
produce ruido. En cambio:

  · un REGISTRO explícito ata cada afirmación a la función que la recalcula;
  · un barrido aparte lista los números que aparecen en los documentos vinculantes
    y **no** están en el registro, para que nada se esconda por omisión.

Salir de banda no es un error: es una señal de que la afirmación hay que releer.
Read-only sobre todo el repo.
"""
import io
import json
import os
import re
import statistics as st
import subprocess
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "experiments"))

VINCULANTES = ["CLAUDE.md", "docs/MISSION.md", "docs/MIROVA_DIVERGENCES.md",
               "docs/META_RULES_S80.md"]


def leer(rel):
    p = os.path.join(ROOT, rel)
    return open(p, encoding="utf-8", errors="replace").read() if os.path.exists(p) else ""


def du_mb(rel):
    base = os.path.join(ROOT, rel)
    if not os.path.exists(base):
        return None
    t = 0
    for dp, _dn, fn in os.walk(base):
        for f in fn:
            try:
                t += os.path.getsize(os.path.join(dp, f))
            except OSError:
                pass
    return round(t / 1e6, 1)


# ══ Las funciones de recálculo ═══════════════════════════════════════════
def _ratios(buck=None):
    """Ratio nuestro/MIROVA, un par por noche, máximo de ambos lados (A10 aparte:
    ver el brazo elegido en cada afirmación)."""
    from _s126_lib import VENTS, bucket, cargar_mirova
    mir, _ = cargar_mirova(("2026-01-01", "2026-12-31"))
    out = []
    for vol in VENTS:
        p = os.path.join(ROOT, "data", "mirova_equivalent", vol + ".json")
        if not os.path.exists(p):
            continue
        mejor = {}
        for r in json.load(open(p, encoding="utf-8"))["records"]:
            sz = r.get("solar_zenith_deg")
            if sz is not None and sz < 90:
                continue
            b = bucket(r.get("sensor"))
            v = (r.get("primary_cluster") or {}).get("vrp_mw") or 0
            if b is None or v <= 0 or (buck and b != buck):
                continue
            k = (r.get("datetime_utc", "")[:10], b)
            mejor[k] = max(mejor.get(k, 0), v)
        for (d, b), v in mejor.items():
            m = (mir.get(vol) or {}).get((d, b))
            if m and m > 0:
                out.append(v / m)
    return round(st.median(out), 3) if out else None


def r_ratio_global():
    return _ratios()


def r_ratio_v375():
    return _ratios("v375")


def r_delta_t(vol):
    from _s126_lib import bucket
    p = os.path.join(ROOT, "data", "mirova_equivalent", vol + ".json")
    if not os.path.exists(p):
        return None
    xs = [(r.get("t_max_i04_k") or r.get("t_max_k")) - r["t_bg_k"]
          for r in json.load(open(p, encoding="utf-8"))["records"]
          if bucket(r.get("sensor")) == "v375" and r.get("t_bg_k") is not None
          and (r.get("t_max_i04_k") or r.get("t_max_k")) is not None]
    return round(st.median(xs), 1) if xs else None


def _tier_a_records():
    """Los records de los 11 Tier A, que son los que alimentan el dashboard."""
    from _s126_lib import VENTS
    for vol in VENTS:
        pth = os.path.join(ROOT, "data", "mirova_equivalent", vol + ".json")
        if not os.path.exists(pth):
            continue
        for r in json.load(open(pth, encoding="utf-8"))["records"]:
            yield r


def r_piso_invisibles():
    """Records que el dashboard NO cuenta como detección por tener vrp_mw = 0.

    DEFINICIÓN: replica isValidDetection() de frontend/index.html:1372 — un
    record cuenta si `vrp_mw > 0` O si trae `triggered_test1`. Se miran sólo los
    que alguna vez pasaron por el piso (`diag_vrp_raw_mw` presente), porque son
    los únicos que el piso pudo apagar.

    Debe ser 0 desde S130. Si sube, el piso volvió — por una consolidación de
    perfiles (A63) o porque el backfill se revirtió. Antes de quitarlo eran 582.
    """
    n = 0
    for r in _tier_a_records():
        if r.get("diag_vrp_raw_mw") is None:
            continue
        if not ((r.get("vrp_mw") or 0) > 0) and r.get("triggered_test1") is not True:
            n += 1
    return n


def r_recall_v750_dash():
    """Recall VIIRS750 del DASHBOARD contra noches-ALERTA de MIROVA, en %.

    DEFINICIÓN: de las noches (volcán, fecha) en que MIROVA declaró ALERTA en
    VIIRS750 —loader canónico CONS ∪ OCR, A11— el porcentaje en que nosotros
    tenemos al menos un record que pasa isValidDetection() Y isSummitDetection()
    del frontend. Es el predicado que el dashboard usa DE VERDAD, distinto del
    de auto_audit_weekly, que mide sobre `primary_cluster.vrp_mw` y por eso era
    ciego al piso VRP (hallazgo S130).

    Cota superior: D2 acota la cobertura del CSV en 79,2 %.
    """
    from _s126_lib import VENTS, bucket, cargar_mirova
    mir, _ = cargar_mirova(("2026-01-01", "2026-12-31"))
    nuestras = set()
    for vol in VENTS:
        pth = os.path.join(ROOT, "data", "mirova_equivalent", vol + ".json")
        if not os.path.exists(pth):
            continue
        for r in json.load(open(pth, encoding="utf-8"))["records"]:
            if bucket(r.get("sensor")) != "v750":
                continue
            v = r.get("vrp_mw") or 0
            valida = v > 0 or r.get("triggered_test1") is True
            if not valida:
                continue
            # isSummitDetection(), frontend/index.html:1378
            if v == 0 and r.get("discarded_reason") and not r.get("triggered_test1"):
                continue
            dc = r.get("distance_class")
            if dc == "far":
                continue
            if dc != "summit" and not ((r.get("vrp_vent_mw") or 0) > 0):
                continue
            nuestras.add((vol, r.get("datetime_utc", "")[:10]))
    total = aciertos = 0
    for vol in VENTS:
        for (d, b) in (mir.get(vol) or {}):
            if b != "v750":
                continue
            total += 1
            if (vol, d) in nuestras:
                aciertos += 1
    return round(100 * aciertos / total, 2) if total else None


def r_git_mb():
    return du_mb(".git")


def r_data_mb():
    return du_mb("data")


def r_suite():
    o = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-q", "--co"],
                       cwd=ROOT, capture_output=True, text=True, timeout=900).stdout
    m = re.search(r"(\d+) tests? collected", o)
    return int(m.group(1)) if m else None


def r_flags_true():
    """Cuántos flags ENABLE_* están en True en el perfil operacional."""
    env = dict(os.environ, VRP_PROFILE="mirova_equivalent")
    o = subprocess.run(
        [sys.executable, "-c",
         "import pipeline.profile as p;"
         "print(sum(1 for f in dir(p) if f.startswith('ENABLE_') and getattr(p,f) is True))"],
        cwd=ROOT, capture_output=True, text=True, env=env, timeout=300).stdout
    m = re.search(r"^(\d+)\s*$", o.strip(), re.M)
    return int(m.group(1)) if m else None


def r_inner_radius():
    """La tabla de inner_radius_km de CLAUDE.md contra volcanoes.yaml."""
    import yaml
    cfg = {v["name"]: v.get("inner_radius_km")
           for v in yaml.safe_load(leer("volcanoes.yaml"))["volcanoes"]}
    return {k: cfg[k] for k in ("Lastarria", "Copahue", "Tupungatito",
                                "PuyehueCordonCaulle", "Villarrica") if k in cfg}


def r_wooster():
    env = dict(os.environ, VRP_PROFILE="mirova_equivalent")
    o = subprocess.run(
        [sys.executable, "-c",
         "import pipeline.process_modis as m, pipeline.process_viirs as v;"
         "print(m.WOOSTER_COEFF, v.WOOSTER_COEFF)"],
        cwd=ROOT, capture_output=True, text=True, env=env, timeout=300).stdout
    n = re.findall(r"[\d.]+", o.strip().splitlines()[-1]) if o.strip() else []
    return [float(x) for x in n[:2]] if len(n) >= 2 else None


def r_cobertura_papers():
    j = os.path.join(ROOT, "docs", "s128", "lectura_papers.json")
    if not os.path.exists(j):
        return None
    d = json.load(open(j, encoding="utf-8"))
    tot = d["_meta"]["corpus_papers_distintos"]
    return round(100.0 * d["conteo"].get("LEIDO_A_FONDO", 0) / tot, 1)


# ══ EL REGISTRO ══════════════════════════════════════════════════════════
# id · qué afirma (INCLUYENDO LA DEFINICIÓN) · dónde · valor · función · banda
#
# La definición no es adorno. Al primer intento este libro marcó «17 flags vs 28» y
# los dos números eran correctos contando cosas distintas. Una afirmación numérica
# sin su denominador declarado no es verificable — es una cifra suelta.
REGISTRO = [
    ("D5_ratio_global", "el ratio nuestro/MIROVA global",
     "docs/MIROVA_DIVERGENCES.md D5", 0.73, r_ratio_global, (0.60, 0.90)),
    ("ratio_v375", "ratio en VIIRS375 — DEFINICIÓN: mediana sobre TODOS los pares "
     "noche-volcán juntos (no la mediana de las medianas por volcán, que da 0,60)",
     "docs/AUDIT_S128.md §6", 0.69, r_ratio_v375, (0.55, 0.85)),
    ("A12_dT_lascar", "ΔT mediano de Láscar (A12 declara 21,6 K)",
     "CLAUDE.md A12", 16.9, lambda: r_delta_t("Lascar"), (14.0, 20.0)),
    ("A12_dT_isluga", "ΔT mediano de Isluga (A12 declara ~20 K)",
     "CLAUDE.md A12", 8.3, lambda: r_delta_t("Isluga"), (6.0, 11.0)),
    ("git_mb", "tamaño de .git — DEFINICIÓN: el directorio COMPLETO en disco, no el "
     "`size-pack` de git count-objects (5,99 GiB), que es sólo lo empaquetado. "
     "S121 declaraba 3.100 MB",
     "docs/AUDIT_S128.md §5", 6507.8, r_git_mb, (5500.0, 9000.0)),
    ("data_mb", "tamaño de data/ (S121 decía 2.000 MB)",
     "docs/AUDIT_S128.md §5", 1034.7, r_data_mb, (800.0, 1400.0)),
    ("suite_tests", "tests de la suite",
     "tasks/BLOQUE_ARRANQUE_S129.md", 1003, r_suite, (990, 1200)),
    ("flags_true", "flags ENABLE_* en True — DEFINICIÓN: TODOS los que evalúan True "
     "en `pipeline.profile`, incluidos los que lo son por default del código. "
     "⚠️ S125 declaró 17 con OTRO denominador (probablemente sólo los escritos en el "
     "YAML); los dos pueden ser correctos. Sin la definición, la comparación no "
     "significa nada — ver el encabezado de este registro",
     "docs/AUDIT_S125_PROFUNDA.md §4", 28, r_flags_true, (24, 34)),
    ("wooster", "coeficientes de Wooster MODIS y VIIRS I04",
     "CLAUDE.md Reglas científicas", [18.9, 18.0], r_wooster, None),
    ("inner_radius", "la tabla inner_radius_km de CLAUDE.md",
     "CLAUDE.md Reglas geométricas",
     {"Lastarria": 3, "Copahue": 4, "Tupungatito": 7,
      "PuyehueCordonCaulle": 20, "Villarrica": 5}, r_inner_radius, None),
    ("piso_invisibles", "records que el dashboard NO cuenta por vrp_mw = 0 — "
     "DEFINICIÓN: los que pasaron por el piso VRP (diag_vrp_raw_mw presente) y "
     "fallan isValidDetection() de frontend/index.html:1372. Antes de quitar el "
     "piso en S130 eran 582; si vuelve a subir, el piso se repuso (A63) o el "
     "backfill se revirtió",
     "PR #571 / tests/test_guard_piso_vrp_s130.py", 0, r_piso_invisibles, (0, 0)),
    ("recall_v750_dash", "recall VIIRS750 del DASHBOARD vs noches-ALERTA MIROVA, "
     "en % — DEFINICIÓN: predicado isValidDetection ∧ isSummitDetection del "
     "frontend, NO el de auto_audit_weekly (que mide sobre primary_cluster y por "
     "eso era ciego al piso VRP). Ventana 2026 y volcanes de _s126_lib.VENTS. "
     "⚠️ El PR #571 reporta 82,52 %→84,55 % con OTRO corte: toda la data y los 11 "
     "Tier A explícitos. Los dos son correctos y NO son comparables entre sí — es "
     "el mismo problema de denominador que flags_true. Cota superior por D2",
     "PR #571 (con su propio corte)", 85.06, r_recall_v750_dash, (78.0, 92.0)),
    ("papers_leidos_pct", "% del corpus leído a fondo",
     "docs/s128/lectura_papers.json", 29.0, r_cobertura_papers, (20.0, 100.0)),
]

# ══ Ejecución ════════════════════════════════════════════════════════════
filas = []
for cid, desc, donde, declarado, fn, banda in REGISTRO:
    try:
        hoy = fn()
        err = None
    except Exception as e:                                     # noqa: BLE001
        hoy, err = None, str(e)[:120]
    if err:
        estado = "ERROR"
    elif hoy is None:
        estado = "NO_MEDIBLE"
    elif isinstance(declarado, (dict, list)):
        estado = "OK" if hoy == declarado else "DERIVA"
    elif banda and not (banda[0] <= hoy <= banda[1]):
        estado = "FUERA_DE_BANDA"
    elif abs(hoy - declarado) > max(0.05 * abs(declarado), 1e-9):
        estado = "DERIVA"
    else:
        estado = "OK"
    filas.append({"id": cid, "afirma_y_define": desc, "donde": donde,
                  "declarado": declarado, "hoy": hoy, "estado": estado,
                  "error": err})

# ══ Lo que NO tiene instrumento ══════════════════════════════════════════
# Números que aparecen en los documentos vinculantes y no están registrados.
# No es una lista de errores: es el inventario de lo que creemos sin poder medir.
registrados = " ".join(str(f["declarado"]) for f in filas)
sin_inst = []
for rel in VINCULANTES:
    for n, linea in enumerate(leer(rel).splitlines(), 1):
        if linea.strip().startswith(("|", ">")) or "http" in linea:
            continue
        for m in re.finditer(r"(?<![\w.])(\d{1,3}(?:[.,]\d+)?)\s*"
                             r"(%|×|x\b|MW|K\b|km|MB|GB|σ|sigma)", linea):
            val = m.group(1)
            if val in registrados or len(val) < 2:
                continue
            sin_inst.append({"doc": rel, "linea": n,
                             "valor": m.group(0).strip(),
                             "contexto": linea.strip()[:110]})

R = {"registro": filas, "sin_instrumento": sin_inst,
     "resumen": {"registradas": len(filas),
                 "ok": sum(1 for f in filas if f["estado"] == "OK"),
                 "con_deriva": sum(1 for f in filas
                                   if f["estado"] in ("DERIVA", "FUERA_DE_BANDA")),
                 "sin_instrumento": len(sin_inst)}}
out = os.path.join(ROOT, "docs", "LIBRO_DE_CUENTAS.json")
json.dump(R, open(out, "w", encoding="utf-8"), indent=1, ensure_ascii=False)

print("LIBRO DE CUENTAS — cada número declarado, recalculado hoy\n")
print("%-20s %-14s %-14s %-16s %s" % ("id", "declarado", "hoy", "estado", "dónde"))
for f in filas:
    d = json.dumps(f["declarado"], ensure_ascii=False) if isinstance(
        f["declarado"], (dict, list)) else f["declarado"]
    h = json.dumps(f["hoy"], ensure_ascii=False) if isinstance(
        f["hoy"], (dict, list)) else f["hoy"]
    print("%-20s %-14.13s %-14.13s %-16s %s"
          % (f["id"], str(d), str(h), f["estado"], f["donde"][:42]))
    if f["error"]:
        print("%22s ! %s" % ("", f["error"]))

print("\nresumen: %d registradas · %d OK · %d con deriva · %d números SIN instrumento"
      % (R["resumen"]["registradas"], R["resumen"]["ok"],
         R["resumen"]["con_deriva"], R["resumen"]["sin_instrumento"]))
print("escrito:", out)
