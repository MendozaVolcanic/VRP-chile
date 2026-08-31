# A/B de los cuatro mecanismos del déficit de magnitud — Etapa 1

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Medir, con reproceso real y criterios pre-registrados, cuánto del déficit de magnitud (ratio 0,73 contra MIROVA) aporta cada uno de los dos mecanismos de fondo autorreferente — el pool μ/σ de detección (GAP #A) y el fondo `t_bg` de la magnitud — que hoy están apagados y que el canon MIROVA pide encendidos.

**Architecture:** Tres brazos que difieren en **un solo flag** cada uno, con `data_subdir` aislado, reprocesados en la misma ventana sobre los mismos volcanes. El control es un clon **reprocesado**, no el acumulado de `mirova_equivalent` — esa data se fue armando con versiones distintas del código y mete diferencias espurias (verificado en S125: MODIS se movía +4,03 con piezas que ni lo tocan). Un script de lectura, escrito y testeado **antes** de que corra el reproceso (A16), mide las cuatro firmas pre-registradas.

**Tech Stack:** Python 3.11, `pytest`, perfiles YAML de `pipeline/profiles/`, GitHub Actions `workflow_dispatch`, helpers de `experiments/_s126_lib.py`.

---

## Alcance y por qué esta etapa sola

S128 y S129 identificaron **cuatro** mecanismos con respaldo verbatim del canon. Este plan cubre **dos**, y deliberadamente no los cuatro:

| mecanismo | flag | estado | por qué acá o no |
|---|---|---|---|
| pool μ/σ de detección (GAP #A) | `ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK` | OFF | **En este plan.** Flag existente, sin código nuevo |
| fondo `t_bg` de la magnitud | `ENABLE_TEST1_K1_BG_EXCLUDE` | OFF | **En este plan.** Flag existente, sin código nuevo |
| suma vs clúster | `ENABLE_SUM_VRP_REPORTING` | OFF | **Plan aparte.** S129 ya midió que es marginal y que no hay radio uniforme (`docs/s129/RADIO_DE_SUMA.md`); necesita que Nicolás decida el criterio Lastarria-vs-Chaitén primero |
| remuestreo a malla fija | `ENABLE_UTM_REGRID` | OFF | **Plan aparte.** Es el más invasivo y **exige código nuevo**: Coppola 2012 §3.2 pone la remoción del bow-tie como paso (i) antes del remuestreo, y para MODIS no la tenemos implementada |

Las dos de este plan comparten una propiedad que las hace un experimento limpio: **son el mismo principio del paper aplicado a dos lugares distintos** —«los píxeles ya alertados no entran al fondo»— y sus firmas esperadas son **distinguibles entre sí**, así que un solo reproceso las separa.

---

## El fenómeno, antes del código

Coppola 2016a manda calcular los estadísticos del fondo sobre los píxeles *suitable*, y define como no-suitable a los que ya dispararon el Test 1 — que son, por construcción, los más calientes de la escena:

> *«Pixels that satisfy Test 1 are flagged as 'active' and subsequently discarded (unsuitable) for further steps.»* — `documentacion/sp426_5.txt:297-300`
>
> *«m and s are the arithmetic mean and standard deviation of all the **suitable** pixels within the image.»* — `sp426_5.txt:326-329`
>
> *«L4bk is estimated from the arithmetic mean of all the pixels **surrounding** the active one (or around the active cluster).»* — Eq. 6, `sp426_5.txt:355-358`

Y Aveni et al. 2023, con los cinco autores del canon, lo repite sin ambigüedad:

> *«L_MIRbk is the radiance of the background, namely the average radiance of the surrounding, **non-alerted** pixels»* — Eq. 3, p. 8

**Los dos fondos nuestros incluyen los píxeles alertados.** Las consecuencias físicas son opuestas y por eso separables:

- **En el pool de detección**, meter los píxeles calientes infla μ y sobre todo σ, sube el umbral `μ + C2·σ`, y **se pierden los píxeles marginales del borde del clúster**. En régimen débil —el nuestro, ΔT de 6,8 a 17 K— Steffke & Harris 2011 p. 1134 documentan que perder el 40 % de los píxeles cuesta el 12 % de la potencia en una anomalía intensa pero **el 50 % en una débil**. Firma esperada: **más déficit cuanto más débil la anomalía**, y **más detecciones** al encenderlo.
- **En el fondo de la magnitud**, meter los píxeles calientes sube `t_bg`, sube `L_bg`, baja `ΔL = max(L_hot − L_bg, 0)` y baja el VRP. Firma esperada: **déficit uniforme**, sin dependencia del régimen, y **sin cambio en el número de detecciones**.

Que una toque el conteo y la otra no es lo que permite atribuir sin ambigüedad.

---

## File Structure

| archivo | responsabilidad |
|---|---|
| `docs/s129/PREREGISTRO_AB_FONDOS.md` | Los criterios, congelados **antes** de que corra nada |
| `experiments/_s129_ab_fondos/lectura.py` | La lógica de lectura: carga los brazos, empareja e informa las cuatro firmas |
| `tests/test_lectura_ab_fondos_s129.py` | Tests de `lectura.py` sobre datos sintéticos, escritos primero |
| `pipeline/profiles/_s129_ab_control.yaml` | Brazo control — clon del operacional, `data_subdir` propio |
| `pipeline/profiles/_s129_ab_pool.yaml` | Brazo A — sólo `enable_test1_k1_retire_from_hot_mask: true` |
| `pipeline/profiles/_s129_ab_bgmag.yaml` | Brazo B — sólo `enable_test1_k1_bg_exclude: true` |
| `.github/workflows/reproc-s129-ab-fondos.yml` | El reproceso, 3 perfiles × 5 volcanes |
| `docs/s129/RESULTADO_AB_FONDOS.md` | El veredicto, escrito después de leer |

**Volcanes del A/B (5, no 11):** `Lascar` (único con ground truth MODIS, y foco discreto), `Lastarria` (campo fumarólico extendido — donde el régimen débil pega más), `Villarrica` (nevado de señal débil), `Tupungatito` (nevado con anillo glaciar, el contraejemplo de A19) y `Chaiten` (domo, el único que hoy sobre-reporta). Cubren los cuatro regímenes sin pagar 11 reprocesos.

---

## Task 1: El pre-registro

**Files:**
- Create: `docs/s129/PREREGISTRO_AB_FONDOS.md`

- [ ] **Step 1: Escribir el pre-registro completo**

Crear `docs/s129/PREREGISTRO_AB_FONDOS.md` con exactamente este contenido:

```markdown
# Pre-registro · A/B de los dos fondos autorreferentes (S129)

> Congelado ANTES de lanzar el reproceso. Si algo de acá cambia después de ver
> resultados, se anota el cambio y la razón — no se reescribe.

## Brazos

| brazo | perfil | único flag distinto |
|---|---|---|
| control | `_s129_ab_control` | ninguno (clon reprocesado del operacional) |
| A · pool | `_s129_ab_pool` | `enable_test1_k1_retire_from_hot_mask: true` |
| B · fondo magnitud | `_s129_ab_bgmag` | `enable_test1_k1_bg_exclude: true` |

Ventana: 2026-03-01 a 2026-08-24. Volcanes: Lascar, Lastarria, Villarrica,
Tupungatito, Chaiten. Sensor primario de lectura: VIIRS375.

## Las cuatro firmas, con su predicción

| # | firma | cómo se mide | predicción A (pool) | predicción B (fondo) |
|---|---|---|---|---|
| F1 | ratio mediano vs MIROVA | un par por noche, máximo de ambos lados, sobre la INTERSECCIÓN de pasadas de los 3 brazos | sube | sube |
| F2 | nº de detecciones con `pc.vrp_mw > 0` | conteo sobre la intersección | **sube** | **no cambia** (±2 %) |
| F3 | dependencia del régimen: ratio en el tercil DÉBIL menos ratio en el tercil FUERTE de `t_max − t_bg` | por volcán y agregado | **la brecha se achica** | **la brecha no cambia** |
| F4 | umbral efectivo `diag_eff_threshold_k` mediano | por volcán | **baja** | no cambia |

F2 y F3 son las que atribuyen. Si los dos brazos mueven F1 pero sólo A mueve F2 y
F3, la atribución es limpia.

## Criterios de decisión, en orden

1. **ADOPTAR** un brazo si: F1 sube, el nº de volcanes dentro de la banda de
   paridad [0,7 – 1,4] **no baja**, y no pierde detecciones que MIROVA confirma
   (FN nuevos = 0 sobre noches con contraparte).
2. **NO ADOPTAR** si pierde alguna noche MIROVA-confirmada, aunque mejore F1.
   Recall antes que paridad, que es la prioridad declarada de `mirova_equivalent`.
3. **INCONCLUSO** si los IC95 de F1 se solapan entre control y brazo. Se reporta
   como inconcluso, no se fuerza.
4. Los dos brazos se evalúan **por separado**. Este A/B no prueba la combinación;
   si los dos pasan, la combinación necesita su propia corrida (puede interactuar:
   A sube el nº de píxeles y B cambia el fondo de cada uno).

## Lo que este A/B NO responde

- No prueba el remuestreo ni la suma vs clúster (planes aparte).
- No vale para MODIS fuera de Láscar: los otros diez tienen **cero** alertas MODIS
  nocturnas en el ground truth, así que cualquier veredicto MODIS ahí es INDEFINIDO,
  no débil.
- A18: el reproceso vuelve a correr la selección de clúster desde cero. Ningún
  preview offline predice esto.
```

- [ ] **Step 2: Commit**

```bash
git add docs/s129/PREREGISTRO_AB_FONDOS.md
git commit -m "docs(s129): pre-registro del A/B de los dos fondos autorreferentes"
```

---

## Task 2: El script de lectura — el test primero

**Files:**
- Create: `tests/test_lectura_ab_fondos_s129.py`
- Create: `experiments/_s129_ab_fondos/lectura.py`

Se escribe **antes** de que corra el reproceso (A16: el trabajo pre-escrito hace que el cierre post-workflow tome minutos en vez de horas).

- [ ] **Step 1: Escribir el test que falla**

Crear `tests/test_lectura_ab_fondos_s129.py`:

```python
# -*- coding: utf-8 -*-
"""Tests de la lectura del A/B de fondos (S129), sobre datos sintéticos.

Se escriben antes que el script y antes que el reproceso. Lo que fijan es la
ARITMÉTICA de las cuatro firmas, que es donde aparecen los errores silenciosos:
emparejar sobre la intersección, un par por noche, y la brecha por régimen.
"""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))), "experiments", "_s129_ab_fondos"))
from lectura import brecha_por_regimen, firmas_de_brazo, pares_intersectados


def _rec(fecha, vrp, tmax, tbg, sensor="VIIRS_SNPP", thr=300.0):
    return {"datetime_utc": fecha + "T05:00:00", "sensor": sensor,
            "primary_cluster": {"vrp_mw": vrp}, "t_max_i04_k": tmax,
            "t_bg_k": tbg, "diag_eff_threshold_k": thr,
            "solar_zenith_deg": 150.0}


def test_un_par_por_noche_toma_el_maximo():
    """Dos pasadas la misma noche cuentan UNA vez, con el mayor VRP."""
    recs = [_rec("2026-03-01", 1.0, 290, 280), _rec("2026-03-01", 3.0, 292, 280)]
    pares = pares_intersectados({"x": recs}, {"x": {("2026-03-01", "v375"): 2.0}},
                                pasadas=None)
    assert len(pares) == 1
    assert pares[0]["nuestro"] == 3.0


def test_interseccion_descarta_noches_que_faltan_en_un_brazo():
    """Sin intersección, un brazo con más pasadas 'detecta más' por procesar más."""
    a = [_rec("2026-03-01", 1.0, 290, 280), _rec("2026-03-02", 1.0, 290, 280)]
    b = [_rec("2026-03-01", 2.0, 290, 280)]
    comunes = {p["fecha"] for p in pares_intersectados(
        {"x": a}, {"x": {("2026-03-01", "v375"): 1.0,
                         ("2026-03-02", "v375"): 1.0}},
        pasadas={"2026-03-01"})}
    assert comunes == {"2026-03-01"}


def test_firmas_cuenta_detecciones_y_umbral():
    recs = [_rec("2026-03-01", 1.0, 290, 280, thr=305.0),
            _rec("2026-03-02", 0.0, 285, 280, thr=295.0)]
    f = firmas_de_brazo({"x": recs}, {"x": {("2026-03-01", "v375"): 1.0}},
                        pasadas=None)
    assert f["n_detecciones"] == 1          # sólo el de vrp>0
    assert f["umbral_mediano"] == 300.0     # mediana de 305 y 295


def test_brecha_por_regimen_es_debil_menos_fuerte():
    """F3: ratio del tercil débil menos el del fuerte. Negativa = el débil sufre."""
    pares = [{"ratio": 0.4, "delta_t": 5.0}, {"ratio": 0.5, "delta_t": 6.0},
             {"ratio": 0.6, "delta_t": 10.0}, {"ratio": 0.9, "delta_t": 20.0},
             {"ratio": 1.0, "delta_t": 22.0}, {"ratio": 1.1, "delta_t": 25.0}]
    b = brecha_por_regimen(pares)
    assert b["debil"] < b["fuerte"]
    assert b["brecha"] == round(b["debil"] - b["fuerte"], 3)
    assert b["brecha"] < 0
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `python -m pytest tests/test_lectura_ab_fondos_s129.py -q`
Expected: FAIL — `ModuleNotFoundError: No module named 'lectura'`

- [ ] **Step 3: Escribir la implementación mínima**

Crear `experiments/_s129_ab_fondos/lectura.py`:

```python
# -*- coding: utf-8 -*-
"""Lectura del A/B de los dos fondos autorreferentes (S129).

Escrita ANTES del reproceso (A16). Concentra las decisiones metodológicas que,
re-escritas a mano en cada veredicto, es donde aparecen los errores: emparejar
sobre la INTERSECCIÓN de pasadas, un par por NOCHE con el máximo de ambos lados,
y `pc.vrp_mw` nunca `record.vrp_mw` (A10).
"""
import os
import statistics as st
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))), "experiments"))
from _s126_lib import bucket                                   # noqa: E402

BUCK = "v375"


def _noches(recs):
    """{fecha: (vrp_max, delta_t, umbral)} — un registro por noche, el mayor VRP."""
    out = {}
    for r in recs:
        if bucket(r.get("sensor")) != BUCK:
            continue
        sz = r.get("solar_zenith_deg")
        if sz is not None and sz < 90:
            continue
        f = r.get("datetime_utc", "")[:10]
        v = (r.get("primary_cluster") or {}).get("vrp_mw") or 0.0
        tmax = r.get("t_max_i04_k") or r.get("t_max_k")
        tbg = r.get("t_bg_k")
        dt = (tmax - tbg) if (tmax is not None and tbg is not None) else None
        if f not in out or v > out[f][0]:
            out[f] = (v, dt, r.get("diag_eff_threshold_k"))
    return out


def pares_intersectados(brazo, mirova, pasadas=None):
    """[{vol, fecha, nuestro, mirova, ratio, delta_t}] sobre las noches comunes."""
    pares = []
    for vol, recs in brazo.items():
        for f, (v, dt, _thr) in _noches(recs).items():
            if pasadas is not None and f not in pasadas:
                continue
            m = (mirova.get(vol) or {}).get((f, BUCK))
            if not m or m <= 0 or v <= 0:
                if v <= 0:
                    continue
            pares.append({"vol": vol, "fecha": f, "nuestro": v,
                          "mirova": m, "ratio": (v / m) if m else None,
                          "delta_t": dt})
    return pares


def brecha_por_regimen(pares):
    """F3 — ratio del tercil DÉBIL menos el del tercil FUERTE de delta_t."""
    con = [p for p in pares if p.get("delta_t") is not None
           and p.get("ratio") is not None]
    if len(con) < 6:
        return {"debil": None, "fuerte": None, "brecha": None, "n": len(con)}
    con.sort(key=lambda p: p["delta_t"])
    t = len(con) // 3
    debil = round(st.median([p["ratio"] for p in con[:t]]), 3)
    fuerte = round(st.median([p["ratio"] for p in con[-t:]]), 3)
    return {"debil": debil, "fuerte": fuerte,
            "brecha": round(debil - fuerte, 3), "n": len(con)}


def firmas_de_brazo(brazo, mirova, pasadas=None):
    """Las cuatro firmas del pre-registro para un brazo."""
    pares = pares_intersectados(brazo, mirova, pasadas)
    ratios = [p["ratio"] for p in pares if p["ratio"] is not None]
    umbrales = [thr for recs in brazo.values()
                for (_v, _dt, thr) in _noches(recs).values() if thr is not None]
    return {
        "ratio_mediano": round(st.median(ratios), 3) if ratios else None,
        "n_detecciones": sum(1 for recs in brazo.values()
                             for (v, _dt, _t) in _noches(recs).values() if v > 0),
        "regimen": brecha_por_regimen(pares),
        "umbral_mediano": round(st.median(umbrales), 3) if umbrales else None,
        "n_pares": len(ratios),
    }
```

- [ ] **Step 4: Correr los tests para verificar que pasan**

Run: `python -m pytest tests/test_lectura_ab_fondos_s129.py -q`
Expected: PASS — `4 passed`

- [ ] **Step 5: Correr la suite completa para verificar que no hay regresiones**

Run: `python -m pytest tests/ -q`
Expected: PASS — 1007 passed (1003 previos + 4 nuevos)

- [ ] **Step 6: Commit**

```bash
git add tests/test_lectura_ab_fondos_s129.py experiments/_s129_ab_fondos/lectura.py
git commit -m "test(s129): la lectura del A/B de fondos, escrita antes del reproceso (A16)"
```

---

## Task 3: Los tres perfiles

**Files:**
- Create: `pipeline/profiles/_s129_ab_control.yaml`
- Create: `pipeline/profiles/_s129_ab_pool.yaml`
- Create: `pipeline/profiles/_s129_ab_bgmag.yaml`

Los perfiles del proyecto son **copias completas** del operacional con un flag y el `data_subdir` cambiados — no usan `extends:`. Se sigue ese patrón.

- [ ] **Step 1: Crear los tres perfiles a partir del operacional**

```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
for ARM in control pool bgmag; do
  cp pipeline/profiles/mirova_equivalent.yaml pipeline/profiles/_s129_ab_$ARM.yaml
  python - "$ARM" <<'PY'
import re, sys
arm = sys.argv[1]
p = "pipeline/profiles/_s129_ab_%s.yaml" % arm
s = open(p, encoding="utf-8").read()
s = re.sub(r"data_subdir:\s*\S+", "data_subdir: _s129_ab_%s" % arm, s)
if arm == "pool":
    s = s.replace("\n  cloud_mask_bt_k:",
                  "\n  # S129 A/B — GAP #A: los Test 1 K1 salen del pool mu/sigma\n"
                  "  enable_test1_k1_retire_from_hot_mask: true\n  cloud_mask_bt_k:", 1)
elif arm == "bgmag":
    s = s.replace("\n  cloud_mask_bt_k:",
                  "\n  # S129 A/B — Coppola 2016a Eq.6: el fondo de la magnitud\n"
                  "  # excluye los pixeles alertados\n"
                  "  enable_test1_k1_bg_exclude: true\n  cloud_mask_bt_k:", 1)
open(p, "w", encoding="utf-8").write(s)
print("escrito", p)
PY
done
```

- [ ] **Step 2: Verificar que cada perfil tiene EXACTAMENTE el flag que debe**

Run:
```bash
for ARM in control pool bgmag; do
  echo "== $ARM =="
  VRP_PROFILE=_s129_ab_$ARM python -c "
import pipeline.profile as p
print(' retire:', p.ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK,
      '| bg_exclude:', p.ENABLE_TEST1_K1_BG_EXCLUDE,
      '| subdir:', p.DATA_SUBDIR)" 2>&1 | tail -1
done
```

Expected:
```
== control ==
 retire: False | bg_exclude: False | subdir: _s129_ab_control
== pool ==
 retire: True | bg_exclude: False | subdir: _s129_ab_pool
== bgmag ==
 retire: False | bg_exclude: True | subdir: _s129_ab_bgmag
```

Si algún valor no coincide, el `replace` no encontró su ancla: abrir el YAML y ubicar la clave a mano bajo `thresholds:`. **Leer siempre `pipeline.profile`, nunca el YAML** — resuelve la sección correcta y los duplicados de una vez.

- [ ] **Step 3: Verificar que el control es idéntico al operacional salvo el subdir**

Run: `diff pipeline/profiles/mirova_equivalent.yaml pipeline/profiles/_s129_ab_control.yaml`
Expected: una sola diferencia, la línea `data_subdir`.

- [ ] **Step 4: Commit**

```bash
git add pipeline/profiles/_s129_ab_control.yaml pipeline/profiles/_s129_ab_pool.yaml pipeline/profiles/_s129_ab_bgmag.yaml
git commit -m "exp(s129): los tres perfiles del A/B de fondos, un flag de diferencia cada uno"
```

---

## Task 4: El workflow del reproceso

**Files:**
- Create: `.github/workflows/reproc-s129-ab-fondos.yml`

- [ ] **Step 1: Crear el workflow**

Crear `.github/workflows/reproc-s129-ab-fondos.yml`:

```yaml
name: A/B S129 — los dos fondos autorreferentes

# Tres brazos que difieren en UN flag: control / pool (GAP #A) / bgmag (Eq.6).
# Pre-registro: docs/s129/PREREGISTRO_AB_FONDOS.md
# El control es un clon REPROCESADO, no el acumulado de mirova_equivalent.

"on":
  workflow_dispatch:
    inputs:
      start:
        description: "Start date YYYY-MM-DD"
        required: true
        default: "2026-03-01"
      end:
        description: "End date YYYY-MM-DD (inclusive)"
        required: true
        default: "2026-08-24"

jobs:
  reproc:
    runs-on: ubuntu-latest
    timeout-minutes: 350
    permissions:
      contents: read
    strategy:
      fail-fast: false
      max-parallel: 8
      matrix:
        volcano: [Lascar, Lastarria, Villarrica, Tupungatito, Chaiten]
        profile: [_s129_ab_control, _s129_ab_pool, _s129_ab_bgmag]
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: "pip"

      - name: Install dependencies
        run: |
          pip install --upgrade pip
          sudo apt-get install -y libhdf4-dev
          pip install pyhdf
          pip install earthaccess numpy h5py scipy pyyaml

      - name: Run reprocess
        env:
          EARTHDATA_TOKEN: ${{ secrets.EARTHDATA_TOKEN }}
          EARTHDATA_USERNAME: ${{ secrets.EARTHDATA_USERNAME }}
          EARTHDATA_PASSWORD: ${{ secrets.EARTHDATA_PASSWORD }}
          ARM_START: ${{ github.event.inputs.start }}
          ARM_END: ${{ github.event.inputs.end }}
        timeout-minutes: 320
        run: |
          python scripts/run_pipeline.py \
            --profile ${{ matrix.profile }} \
            --volcano ${{ matrix.volcano }} \
            --start "$ARM_START" \
            --end "$ARM_END" \
            --overwrite

      - name: Upload reprocessed JSON as artifact
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: s129ab-${{ matrix.profile }}-${{ matrix.volcano }}
          path: data/${{ matrix.profile }}/${{ matrix.volcano }}.json
          retention-days: 14
          if-no-files-found: warn
```

Dos detalles que no son cosméticos: `"on":` va **entre comillas** (A43 — el «Norway problem» de YAML 1.1 hizo fallar tres workflows con HTTP 422 durante trece horas en S74), y las fechas pasan por `env:` en vez de interpolarse dentro del `run:` — S128 encontró 31 ocurrencias de esa inyección en 7 workflows, y este no suma una más.

- [ ] **Step 2: Verificar que el YAML parsea y que la clave `on` es string**

Run:
```bash
python -c "
import yaml
d = yaml.safe_load(open('.github/workflows/reproc-s129-ab-fondos.yml', encoding='utf-8'))
ks = list(d.keys())
print('claves:', ks)
assert 'on' in ks, 'la clave on parseo como booleano — falta el quoting (A43)'
print('OK')
"
```
Expected: `claves: ['name', 'on', 'jobs']` seguido de `OK`

- [ ] **Step 3: Commit y merge a main**

`workflow_dispatch` sólo es invocable si el yml está en la branch default.

```bash
git add .github/workflows/reproc-s129-ab-fondos.yml
git commit -m "ci(s129): workflow del A/B de fondos — 3 brazos x 5 volcanes"
git push origin HEAD
```

---

## Task 5: Correr y leer

- [ ] **Step 1: Tag defensivo antes de nada (A45)**

Aunque este A/B **no toca el operacional** —los tres perfiles escriben a `data_subdir` aislados—, la regla A45 pide el tag antes de cualquier ciclo que involucre `pipeline/profiles/`.

```bash
git tag -a pre-s129-ab-fondos -m "snapshot antes del A/B de los dos fondos autorreferentes"
git push origin pre-s129-ab-fondos
```

- [ ] **Step 2: Lanzar el reproceso**

```bash
gh workflow run reproc-s129-ab-fondos.yml --ref main -f start=2026-03-01 -f end=2026-08-24
```

Expected: sin salida y exit 0. Si devuelve HTTP 422, el yml no está en `main` todavía o la clave `on` no quedó quoteada.

- [ ] **Step 3: Esperar y verificar que los 15 jobs terminaron**

Run: `gh run list --workflow=reproc-s129-ab-fondos.yml --limit 1`
Expected: `completed  success`. Duración esperada ~3-5 h (A15: presupuestar `duración × 1,3`).

- [ ] **Step 4: Leer con el script ya testeado**

```bash
python - <<'PY'
import json, os, sys
sys.path.insert(0, "experiments/_s129_ab_fondos")
sys.path.insert(0, "experiments")
from lectura import firmas_de_brazo
from _s126_lib import cargar_mirova, bucket

VOLS = ["Lascar", "Lastarria", "Villarrica", "Tupungatito", "Chaiten"]
VEN = ("2026-03-01", "2026-08-24")
mir, _ = cargar_mirova(VEN)

def cargar(sub):
    out = {}
    for v in VOLS:
        p = os.path.join("data", sub, v + ".json")
        if os.path.exists(p):
            out[v] = [r for r in json.load(open(p, encoding="utf-8"))["records"]
                      if VEN[0] <= r.get("datetime_utc", "")[:10] <= VEN[1]]
    return out

brazos = {a: cargar("_s129_ab_" + a) for a in ("control", "pool", "bgmag")}
# INTERSECCIÓN: sin esto, un brazo con más pasadas "detecta más" por procesar más.
comunes = set.intersection(*[
    {r["datetime_utc"][:10] for recs in b.values() for r in recs
     if bucket(r.get("sensor")) == "v375"} for b in brazos.values()])
print("noches comunes:", len(comunes), "\n")
for a, b in brazos.items():
    print(a, json.dumps(firmas_de_brazo(b, mir, comunes), ensure_ascii=False))
PY
```

- [ ] **Step 5: Escribir el veredicto contra el pre-registro**

Crear `docs/s129/RESULTADO_AB_FONDOS.md` con una sección por criterio del pre-registro, en el mismo orden, marcando **CUMPLE / NO CUMPLE** en cada uno y sin reinterpretarlos. Si un brazo falla el criterio 2 (pierde una noche MIROVA-confirmada), el veredicto es NO ADOPTAR aunque F1 haya subido: recall antes que paridad.

- [ ] **Step 6: Registrar los números nuevos en el libro de cuentas**

Todo número que vaya a citarse después entra a `scripts/libro_de_cuentas.py` con **su definición**, para que no se pudra. Agregar al `REGISTRO` una entrada por cada firma adoptada.

- [ ] **Step 7: Commit**

```bash
git add docs/s129/RESULTADO_AB_FONDOS.md scripts/libro_de_cuentas.py
git commit -m "audit(s129): veredicto del A/B de los dos fondos autorreferentes"
```

---

## Self-review

**Cobertura del alcance.** Los dos mecanismos declarados en el alcance tienen tarea: el pool en el brazo `pool` (Tasks 3-5) y el fondo de magnitud en `bgmag`. Los otros dos mecanismos quedan explícitamente fuera y con su razón. Las cuatro firmas del pre-registro tienen implementación en `lectura.py` y test en Task 2.

**Placeholders.** Ninguna tarea dice «agregar manejo de errores» ni «tests para lo anterior»: los tests están escritos, los perfiles se generan con un comando concreto, y el workflow está completo.

**Consistencia de nombres.** `firmas_de_brazo`, `pares_intersectados` y `brecha_por_regimen` se definen en Task 2 y se usan con esos mismos nombres en Task 5. Los `data_subdir` (`_s129_ab_control` / `_pool` / `_bgmag`) coinciden entre Task 3, el workflow de Task 4 y la lectura de Task 5.

**Riesgo conocido.** Task 3 Step 1 ancla el `replace` en `cloud_mask_bt_k:`. Si esa clave no existe con esa indentación en el operacional, el flag no se inserta — por eso Step 2 **verifica leyendo `pipeline.profile`** en vez de confiar en el `replace`. Es el mismo patrón que atrapó los tres A89 de S128.
