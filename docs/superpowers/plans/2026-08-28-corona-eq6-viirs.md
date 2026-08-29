# Corona Eq.6 en VIIRS — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Cablear el fondo de corona de la Eq.6 de Coppola 2016a en el path Test 1 de **VIIRS 375 m**, flag-OFF por defecto, para poder decidir por A/B si reemplaza al anillo fijo `[1,5–3] km` que hoy es autorreferente.

**Alcance acotado (S126):** Nicolás limitó el trabajo a **VIIRS 375**. Es donde el problema está probado —87 % de clústeres de 1 píxel, Villarrica midiendo a 2,74 km del cráter, Planchón inflándose ×6,9— y así el A/B mueve una sola variable. VIIRS 750 queda para después, con este resultado a la vista; el port es mecánico (mismo helper, banda M13, coeficiente 19,7).

**Architecture:** Se reusa el helper ya existente y testeado `cluster_corona_background` (`pipeline/vrp_regimes.py:109`) + `cluster_vrp_mw_with_bg` (`:183`), cableados hoy únicamente en `process_modis.py:1049`. Se replica ese patrón exacto en `process_viirs.py`: recomputar **sólo** `primary_cluster.vrp_mw` **después** de la selección del clúster. La detección, la posición y el resto del record quedan intactos. Un flag propio del sensor (precedente: `ENABLE_FOCAL_CLUSTER_MAGNITUDE_VIIRS750`), para dejar la puerta abierta al port sin arrastrar esta decisión.

**Tech Stack:** Python 3.12, numpy, scipy.ndimage, pytest. Perfiles YAML en `pipeline/profiles/`.

---

## Por qué (contexto vinculante para quien ejecute)

**El fenómeno.** En un volcán nevado el cráter emite una señal sub-píxel débil y su entorno inmediato es nieve fría. A 375 m de resolución esa señal no llena el píxel: se mezcla con nieve y el promedio queda en valores intermedios. Para decidir si un píxel es anómalo hace falta un fondo que represente **terreno no afectado**.

**El drift.** Nuestro VIIRS 375 estima ese fondo con un anillo fijo `[1,5–3] km` medido desde el cráter (`TEST1_INTERMEDIATE_BG_RING_KM`), mientras que el ROI del Test 1 es el disco de 3 km (`TEST1_ROI_KM = 3.0`). El anillo es entonces el **75 % del área del propio disco que se está midiendo**. En `process_viirs.py:1729` la energía sale de `maximum(L − effective_L_bg, 0)`: cada píxel se compara contra la media de sus propios tres cuartos exteriores y el recorte a cero se queda con la mitad de arriba. Sumar esa mitad da una VRP que crece con la cantidad de píxeles, no con la energía del volcán.

**Lo que dice el paper.** Coppola 2016a SP426.5, Eq. 6, verbatim: *"L4bk is estimated from the arithmetic mean of all the pixels surrounding the active one (or around the active cluster)."* El fondo de MIROVA es la corona **inmediata al clúster activo**, y por construcción **no** incluye los píxeles medidos.

**Gate de MISSION.** Pasa por la **pregunta 1**: está documentado literalmente en un paper MIROVA core. No es un parche nuevo — es retirar una divergencia. El anillo fijo al cráter es lo que no tiene respaldo documental.

**Por qué debería discriminar.** Una fluctuación de fondo tiene vecinos a su misma temperatura → el fondo local sube hasta el propio píxel → ΔL ≈ 0 → el artefacto se desploma. Un foco sub-píxel real tiene vecinos genuinamente más fríos → ΔL sobrevive. Es el eje **espacial**, el único que A83 encontró capaz de separar cat-b real de artefacto; un anillo fijo al cráter no puede hacerlo porque mide lo mismo tenga o no tenga foco debajo.

**Evidencia previa** (read-only, `experiments/_s125_magnitud/`): `04`–`09` documentan el fondo autorreferente y que Villarrica mide a 2,74 km del cráter aun con actividad confirmada; `10` estima la corona como **cota inferior** y da Láscar 0 % de colapso (el foco real sobrevive) contra Villarrica 0,31× con 34–50 % bajo 0,01 MW. Ver `docs/S126_COSTO_FILTRO_CONTEXTUAL.md`.

## Restricciones no negociables

- **A45**: tag defensivo + confirmación explícita de Nicolás ANTES del primer edit a `pipeline/process_*.py`. La Tarea 0 es eso.
- **Flag-OFF por defecto**: `mirova_equivalent` no cambia de comportamiento. NRT intacto.
- **No tocar detección**: el recompute va DESPUÉS de la selección del clúster. Esto protege el trigger del evento NdC 06-16 que A79 marcó como load-bearing del anillo `[1,5–3]`.
- **A49**: al insertar código entre estructuras, verificar con `git diff` que no se comió la línea anterior ni la siguiente.
- **A47**: el reproceso local nunca en paralelo sobre el mismo `data_subdir`.

## File Structure

| Archivo | Responsabilidad | Acción |
|---|---|---|
| `pipeline/profile.py` | declarar los 2 flags nuevos leyendo de `paths:` | Modificar (~10 líneas) |
| `pipeline/process_viirs.py` | corona en el path Test 1 de VIIRS 375 | Modificar (~20 líneas) |
| `tests/test_corona_eq6_viirs_s126.py` | tests de las dos ramas + fallback degradado | Crear |
| `pipeline/profiles/_s126_corona_off.yaml` | brazo control del A/B | Crear |
| `pipeline/profiles/_s126_corona_on.yaml` | brazo tratamiento del A/B | Crear |
| `docs/S126_CORONA_PREREGISTRO.md` | criterios fijados ANTES de correr | Crear |

---

### Task 0: Tag defensivo y confirmación (A45)

**Files:** ninguno.

- [ ] **Step 1: Confirmar con Nicolás**

Mostrarle este plan y esperar un sí explícito. A45 lo exige aunque los tests estén verdes y el cambio sea flag-OFF. No avanzar sin eso.

- [ ] **Step 2: Tag defensivo sobre el estado actual**

```bash
git tag -a pre-s126-corona-viirs -m "snapshot antes de cablear la corona Eq.6 en VIIRS (S126)"
git push origin pre-s126-corona-viirs
```

- [ ] **Step 3: Verificar que el tag está en el remote**

Run: `git ls-remote --tags origin | grep pre-s126-corona-viirs`
Expected: una línea con el sha y `refs/tags/pre-s126-corona-viirs`

---

### Task 1: Declarar los flags en profile.py

**Files:**
- Modify: `pipeline/profile.py:451-454` (justo después del bloque `LOCAL_CLUSTER_MAG_*`)

- [ ] **Step 1: Escribir el test que falla**

Crear `tests/test_corona_eq6_viirs_s126.py` con:

```python
# -*- coding: utf-8 -*-
"""S126 — corona Eq.6 (Coppola 2016a) cableada en los dos sensores VIIRS.

El fondo del Test 1 en VIIRS sale hoy de un anillo fijo [1,5-3] km al crater que
solapa el 75 % del ROI que mide (fondo autorreferente). La Eq.6 dice que L4bk es
"the arithmetic mean of all the pixels surrounding the active one (or around the
active cluster)". Estos tests fijan esa semantica.
"""
import importlib
import os

import numpy as np
import pytest


def _profile(monkeypatch, name="mirova_equivalent"):
    monkeypatch.setenv("VRP_PROFILE", name)
    import pipeline.profile as prof
    return importlib.reload(prof)


def test_flag_corona_v375_existe_y_esta_off_por_defecto(monkeypatch):
    """El flag existe y NO cambia el comportamiento operacional."""
    prof = _profile(monkeypatch)
    assert prof.ENABLE_LOCAL_CLUSTER_MAGNITUDE_VIIRS375 is False
```

- [ ] **Step 2: Correr el test para verificar que falla**

Run: `python -m pytest tests/test_corona_eq6_viirs_s126.py -v`
Expected: FAIL con `AttributeError: module 'pipeline.profile' has no attribute 'ENABLE_LOCAL_CLUSTER_MAGNITUDE_VIIRS375'`

- [ ] **Step 3: Agregar los flags**

En `pipeline/profile.py`, inmediatamente después de la línea
`LOCAL_CLUSTER_MAG_MIN_CORONA: int = int(_p.get("local_cluster_mag_min_corona", 4))`:

```python
# S126 — corona Eq.6 en VIIRS. El path Test 1 de los dos sensores VIIRS estima el
# fondo con un anillo fijo [1,5-3] km al cráter (TEST1_INTERMEDIATE_BG_RING_KM)
# mientras el ROI del Test 1 es el disco de 3 km (TEST1_ROI_KM): el anillo es el
# 75 % del área que mide → fondo AUTORREFERENTE, y el clip a 0 de
# process_viirs.py:1729 suma la mitad de arriba del ruido de esa misma corona.
# Coppola 2016a Eq.6 dice que L4bk sale de la media de los píxeles que RODEAN al
# clúster activo. Flags SEPARADOS por sensor para A/B independiente (A45),
# OFF default → mirova_equivalent no cambia. Mismos helpers que MODIS
# (cluster_corona_background + cluster_vrp_mw_with_bg) y mismos parámetros
# LOCAL_CLUSTER_MAG_{MODE,RING_PX,MIN_CORONA}.
# Evidencia: docs/S126_COSTO_FILTRO_CONTEXTUAL.md.
ENABLE_LOCAL_CLUSTER_MAGNITUDE_VIIRS375: bool = bool(
    _p.get("enable_local_cluster_magnitude_viirs375", False))
```

- [ ] **Step 4: Correr el test para verificar que pasa**

Run: `python -m pytest tests/test_corona_eq6_viirs_s126.py -v`
Expected: PASS

- [ ] **Step 5: Verificar que no se rompió nada y que el nivel del YAML es el correcto**

Run: `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; print(p.ENABLE_LOCAL_CLUSTER_MAGNITUDE_VIIRS375)"`
Expected: `False`

Run: `python -m pytest -q`
Expected: `911 passed` (+1 nuevo = 912)

- [ ] **Step 6: Commit**

```bash
git add pipeline/profile.py tests/test_corona_eq6_viirs_s126.py
git commit -m "feat(s126): flags de la corona Eq.6 para los dos sensores VIIRS (OFF default)"
```

---

### Task 2: Cablear la corona en VIIRS 375

**Files:**
- Modify: `pipeline/process_viirs.py` (import + bloque Test 1 en `~1776`)
- Test: `tests/test_corona_eq6_viirs_s126.py`

- [ ] **Step 1: Escribir el test que falla**

Agregar a `tests/test_corona_eq6_viirs_s126.py`:

```python
def test_corona_desploma_la_fluctuacion_y_conserva_el_foco():
    """La corona Eq.6 distingue lo que un anillo fijo al cráter no puede.

    Dos escenas idénticas salvo por el ENTORNO del píxel caliente:
      · fluctuación: vecinos a la misma temperatura → dL ~ 0 → VRP se desploma.
      · foco real:   vecinos fríos                 → dL grande → VRP sobrevive.
    Un fondo tomado de un anillo lejano da el MISMO número en los dos casos.
    """
    from pipeline.vrp_regimes import cluster_corona_background, cluster_vrp_mw_with_bg

    areas = np.full((7, 7), 140625.0)
    cluster = [(3, 3)]

    fluctuacion = np.full((7, 7), 272.0)
    fluctuacion[3, 3] = 273.0            # 1 K sobre un entorno a su misma temperatura

    foco = np.full((7, 7), 272.0)
    foco[2:5, 2:5] = 262.0               # entorno inmediato frío (nieve)
    foco[3, 3] = 273.0

    hot = np.zeros((7, 7), dtype=bool)
    hot[3, 3] = True

    t_bk_fluct, deg_f = cluster_corona_background(fluctuacion, cluster, hot)
    t_bk_foco, deg_c = cluster_corona_background(foco, cluster, hot)
    assert not deg_f and not deg_c

    vrp_fluct = cluster_vrp_mw_with_bg(fluctuacion, areas, cluster, t_bk_fluct, 18.0, 3.74)
    vrp_foco = cluster_vrp_mw_with_bg(foco, areas, cluster, t_bk_foco, 18.0, 3.74)

    assert vrp_foco > 5 * vrp_fluct, (
        f"la corona no discrimina: fluctuacion={vrp_fluct:.5f} foco={vrp_foco:.5f}")


def test_corona_viirs375_recomputa_pc_vrp_solo_con_el_flag_on():
    """El helper de VIIRS375 aplica la corona sólo cuando el flag está ON."""
    from pipeline.process_viirs import apply_corona_magnitude_v375

    bt = np.full((7, 7), 272.0)
    bt[2:5, 2:5] = 262.0
    bt[3, 3] = 280.0
    areas = np.full((7, 7), 140625.0)
    hot = np.zeros((7, 7), dtype=bool)
    hot[3, 3] = True

    base = 1.234
    off, deg_off = apply_corona_magnitude_v375(
        base, bt, areas, [(3, 3)], hot, enabled=False)
    assert off == base and deg_off is None

    on, deg_on = apply_corona_magnitude_v375(
        base, bt, areas, [(3, 3)], hot, enabled=True)
    assert deg_on is False
    assert on != base and on > 0


def test_corona_viirs375_degradada_conserva_el_vrp_regional():
    """Con menos de min_corona píxeles válidos NO se pisa el VRP (fallback explícito)."""
    from pipeline.process_viirs import apply_corona_magnitude_v375

    bt = np.full((3, 3), np.nan)
    bt[1, 1] = 280.0                      # corona entera NaN → degradada
    areas = np.full((3, 3), 140625.0)
    hot = np.zeros((3, 3), dtype=bool)
    hot[1, 1] = True

    base = 1.234
    out, deg = apply_corona_magnitude_v375(
        base, bt, areas, [(1, 1)], hot, enabled=True)
    assert deg is True
    assert out == base
```

- [ ] **Step 2: Correr los tests para verificar que fallan**

Run: `python -m pytest tests/test_corona_eq6_viirs_s126.py -v`
Expected: el primero PASA (usa sólo helpers existentes); los dos de `apply_corona_magnitude_v375` FALLAN con `ImportError: cannot import name 'apply_corona_magnitude_v375'`

Si el PRIMERO falla, parar: significa que la corona no discrimina y la hipótesis del plan es falsa. No seguir implementando.

- [ ] **Step 3: Agregar el import en process_viirs.py**

Buscar el bloque de imports desde `.vrp_regimes` en `pipeline/process_viirs.py`. Si no existe, agregarlo junto a los otros imports relativos del paquete:

```python
from .vrp_regimes import cluster_corona_background, cluster_vrp_mw_with_bg
```

Y agregar los flags al bloque que importa de `.profile`:

```python
    ENABLE_LOCAL_CLUSTER_MAGNITUDE_VIIRS375,
    LOCAL_CLUSTER_MAG_MODE,
    LOCAL_CLUSTER_MAG_RING_PX,
    LOCAL_CLUSTER_MAG_MIN_CORONA,
```

- [ ] **Step 4: Escribir el helper**

Agregar a `pipeline/process_viirs.py`, a nivel de módulo, justo antes de la función que procesa el gránulo (buscar `def process_viirs_granule` y ponerlo encima):

```python
def apply_corona_magnitude_v375(
    vrp_mw: float,
    bt_grid: np.ndarray,
    pixel_areas: np.ndarray,
    cluster_indices,
    scene_hot_mask,
    *,
    enabled: bool,
    mode: str = "footprint",
    ring_px: int = 1,
    min_corona: int = 4,
) -> tuple[float, bool | None]:
    """Recomputa el VRP del clúster con la corona Eq.6 (Coppola 2016a).

    POR QUÉ: el fondo del Test 1 en VIIRS375 sale hoy del anillo [1,5-3] km al
    cráter, que es el 75 % del área del propio ROI de 3 km — se compara cada píxel
    contra la media de sus propios tres cuartos exteriores. La Eq.6 usa en cambio
    la corona INMEDIATA al clúster, que no contiene a los píxeles medidos: una
    fluctuación de fondo tiene vecinos a su misma temperatura (ΔL≈0, se desploma)
    y un foco real los tiene fríos (ΔL grande, sobrevive).

    Si la corona degrada (menos de `min_corona` píxeles válidos) NO se pisa el
    valor: se devuelve el VRP regional tal cual, con `degraded=True`, para que el
    fallback quede explícito en el record y no silencioso.

    Returns:
        (vrp_mw, corona_degraded). `corona_degraded` es None cuando el flag está OFF.
    """
    if not enabled:
        return vrp_mw, None
    t_bk, degraded = cluster_corona_background(
        bt_grid, cluster_indices, scene_hot_mask,
        mode=mode, ring_px=ring_px, min_corona=min_corona,
    )
    if degraded:
        return vrp_mw, True
    return cluster_vrp_mw_with_bg(
        bt_grid, pixel_areas, cluster_indices, t_bk, WOOSTER_COEFF, I04_LAMBDA
    ), False
```

- [ ] **Step 5: Correr los tests para verificar que pasan**

Run: `python -m pytest tests/test_corona_eq6_viirs_s126.py -v`
Expected: 4 passed

- [ ] **Step 6: Cablear el helper en el bloque Test 1**

En `pipeline/process_viirs.py`, en el bloque que empieza en `if t1_clusters:` (≈1775), entre la línea `_vrp_t = float(top["vrp_mw"])` y el comentario `# S71 D9 Opción C`, insertar:

```python
                # S126 — fondo de corona Eq.6 (Coppola 2016a) en vez del anillo
                # [1,5-3] km al cráter, que solapa el 75 % del ROI que mide.
                # Sólo magnitud, post-selección: la detección y la posición ya
                # quedaron fijadas arriba, así que el trigger de eventos débiles
                # (A79, NdC 06-16) no se toca. Flag-OFF default (A45).
                _corona_degraded_t = None
                _vrp_t, _corona_degraded_t = apply_corona_magnitude_v375(
                    _vrp_t, bt, pixel_areas, top["pixel_indices"],
                    test1_hot_filtered,
                    enabled=ENABLE_LOCAL_CLUSTER_MAGNITUDE_VIIRS375,
                    mode=LOCAL_CLUSTER_MAG_MODE,
                    ring_px=LOCAL_CLUSTER_MAG_RING_PX,
                    min_corona=LOCAL_CLUSTER_MAG_MIN_CORONA,
                )
```

Y después de la línea `if _d9_capped_t:` / `primary_cluster["d9_capped"] = True`, agregar:

```python
                if _corona_degraded_t is not None:
                    primary_cluster["corona_degraded"] = bool(_corona_degraded_t)
```

- [ ] **Step 7: Verificar la inserción con git diff (A49)**

Run: `git diff pipeline/process_viirs.py`
Expected: el diff muestra SÓLO líneas agregadas (`+`), ninguna borrada. Confirmar a ojo que la línea `_vrp_t = float(top["vrp_mw"])` y el bloque `primary_cluster = {` siguen completos.

Verificación mecánica del mismo punto:

```bash
git diff --numstat pipeline/process_viirs.py
```
Expected: la columna de líneas borradas debe ser `0`.

- [ ] **Step 8: Verificar que el operacional no cambió**

Run: `python -m pytest -q`
Expected: `915 passed` (911 previos + 4 nuevos)

- [ ] **Step 9: Commit**

```bash
git add pipeline/process_viirs.py tests/test_corona_eq6_viirs_s126.py
git commit -m "feat(s126): corona Eq.6 en el path Test 1 de VIIRS375 (flag-OFF)"
```

---

### Task 3: Perfiles del A/B y pre-registro de criterios

**Files:**
- Create: `pipeline/profiles/_s126_corona_off.yaml`
- Create: `pipeline/profiles/_s126_corona_on.yaml`
- Create: `docs/S126_CORONA_PREREGISTRO.md`

- [ ] **Step 1: Crear el brazo control**

`pipeline/profiles/_s126_corona_off.yaml` — clon de `mirova_equivalent` con `data_subdir` aislado. Generarlo así para no derivar del original a mano:

```bash
python - <<'PY'
import pathlib, re
src = pathlib.Path("pipeline/profiles/mirova_equivalent.yaml").read_text(encoding="utf-8")
cab = ("# S126 A/B corona Eq.6 — BRAZO CONTROL.\n"
       "# Identico al operacional; existe para que el control sea un clon REPROCESADO\n"
       "# en la misma ventana y no el acumulado de mirova_equivalent (que mezcla\n"
       "# versiones de codigo distintas y mete diferencias espurias).\n")
out = cab + re.sub(r"^(\s*)data_subdir:.*$", r"data_subdir: _s126_corona_off", src, flags=re.M)
# OJO: la clave va INDENTADA bajo `output:`. Sin el `\s*` el regex no matchea
# y el brazo queda apuntando a data/mirova_equivalent/ — a produccion.
pathlib.Path("pipeline/profiles/_s126_corona_off.yaml").write_text(out, encoding="utf-8")
PY
```

- [ ] **Step 2: Crear el brazo tratamiento**

```bash
python - <<'PY'
import pathlib, re
src = pathlib.Path("pipeline/profiles/_s126_corona_off.yaml").read_text(encoding="utf-8")
src = src.replace("data_subdir: _s126_corona_off", "data_subdir: _s126_corona_on")
src = src.replace("# S126 A/B corona Eq.6 — BRAZO CONTROL.",
                  "# S126 A/B corona Eq.6 — BRAZO TRATAMIENTO (corona ON en los 2 VIIRS).")
# los enable_* de magnitud van bajo `paths:` (profile.py:131 `_p = _cfg["paths"]`)
src = re.sub(r"^(paths:\s*\n)",
             r"\1  enable_local_cluster_magnitude_viirs375: true\n"
             src, count=1, flags=re.M)
pathlib.Path("pipeline/profiles/_s126_corona_on.yaml").write_text(src, encoding="utf-8")
PY
```

- [ ] **Step 3: Verificar los dos perfiles LEYENDO pipeline.profile, no el YAML**

Run:
```bash
for P in _s126_corona_off _s126_corona_on; do
  VRP_PROFILE=$P python -c "
import pipeline.profile as p
print('$P', p.ENABLE_LOCAL_CLUSTER_MAGNITUDE_VIIRS375, p.DATA_SUBDIR)"
done
```
Expected:
```
_s126_corona_off False _s126_corona_off
_s126_corona_on True _s126_corona_on
```

Si el `on` sale `False`, el flag quedó en el nivel equivocado del YAML — tiene que estar bajo `paths:`.

- [ ] **Step 4: Verificar que ningún otro flag difiere entre los brazos**

Run:
```bash
python - <<'PY'
import subprocess, json
def flags(p):
    out = subprocess.run(["python","-c",
        "import pipeline.profile as p;"
        "print({k:str(getattr(p,k)) for k in dir(p) if k.isupper()})"],
        env={**__import__("os").environ,"VRP_PROFILE":p},
        capture_output=True,text=True).stdout.strip().splitlines()[-1]
    return eval(out)
a,b = flags("_s126_corona_off"), flags("_s126_corona_on")
dif = {k:(a.get(k),b.get(k)) for k in set(a)|set(b) if a.get(k)!=b.get(k)}
print(json.dumps(dif, indent=2, ensure_ascii=False))
PY
```
Expected: exactamente 2 diferencias — el flag nuevo y `DATA_SUBDIR` (ignorando
`VALID_PROFILES` y `PROFILE_NAME`, que son metadatos). Cualquier otra cosa invalida el A/B.

- [ ] **Step 5: Escribir el pre-registro ANTES de correr**

Crear `docs/S126_CORONA_PREREGISTRO.md`:

```markdown
# Pre-registro del A/B de la corona Eq.6 (S126)

Fijado ANTES de correr. Cualquier criterio agregado después no cuenta.

## Qué se compara

`_s126_corona_off` (control) contra `_s126_corona_on`, misma ventana
2026-06-25 a 2026-08-24, sobre la INTERSECCIÓN de pasadas (datetime_utc + sensor).
Volcanes: Villarrica, PlanchonPeteroa, Lascar, PuyehueCordonCaulle y
NevadosDeChillan. NdC entra como CANARIO de A79 (el evento 06-16).

## Criterios, estratificados POR VOLCÁN y POR SENSOR

La lección de S126 es que una mediana agrupada invierte el veredicto. Ningún
criterio se evalúa sobre el conjunto.

1. **Más volcanes en banda [0,7–1,4]** en VIIRS375, contando por volcán.
   Hoy el control da 3/4 en el piloto. ADOPTAR exige ≥ ese número y ningún
   volcán que estaba en banda se salga.
2. **Villarrica**: la magnitud debe BAJAR. Es el caso donde está probado que
   medimos una fluctuación a 2,8 km del cráter con contraste negativo.
3. **Láscar es el canario de falso negativo**: 0 detecciones perdidas y su
   magnitud no puede caer más de un 20 % — ahí el foco es real (+7,8 K sobre
   el fondo, a 0,18 km del cráter).
4. **NdC 06-16 sigue disparando** (A79). Si se pierde, NO ADOPTAR sin más.
5. **Cero detecciones nuevas perdidas** en total sobre la intersección.
6. **Control interno**: MODIS no debe moverse ni un dígito. Si se mueve, el
   A/B está mal montado.

## Qué NO decide

- La mediana agrupada de los 5 volcanes. Se reporta, no decide.
- El ratio contra MIROVA en noches DIURNAS: se descartan (A76).
```

- [ ] **Step 6: Commit**

```bash
git add pipeline/profiles/_s126_corona_off.yaml pipeline/profiles/_s126_corona_on.yaml docs/S126_CORONA_PREREGISTRO.md
git commit -m "test(s126): perfiles del A/B de la corona + criterios pre-registrados"
```

---

### Task 4: Correr el A/B

**Files:** ninguno de código.

- [ ] **Step 1: Mergear a main (los workflows sólo se despachan desde la default branch)**

Abrir PR, esperar CI verde, mergear. Ver A39 para el criterio y el workaround por API.

- [ ] **Step 2: Lanzar los dos brazos**

Clonar el template de A/B desde `.github/workflows/_archive/reproc-ab-p3-1.yml`, con
`"on":` **entre comillas** (A43, Norway problem) y el mismo
`concurrency: group: push-main` con `cancel-in-progress: false` (S123), porque el job
`merge` pushea a main. Un brazo por perfil; los dos pueden correr a la vez porque cada
uno escribe en su propio `data_subdir` (A47).

- [ ] **Step 3: Verificar que el reproceso tocó de verdad los datos**

Run, por cada JSON producido:
```bash
python experiments/_s124_ndc_focus/05_verificar_reproceso.py data/_s126_corona_on/Villarrica.json
```
Expected: NO debe decir que hay meses idénticos byte a byte. Ese es el bug de merge de S124: un run puede cerrar en verde sin haber tocado nada.

Ojo también con el job `merge` cancelado en silencio por el grupo de concurrencia
(documentado en S125): si el run figura `cancelled` pero los trozos están verdes, el
cómputo está hecho — recuperarlo con `gh run download <id>` + `merge_chunk_stores.py --ventanas`.

- [ ] **Step 4: Evaluar con un script que persista los números**

Escribir `experiments/_s126_corona/01_veredicto_corona.py` reusando la estructura de
`experiments/_s125_magnitud/09_desagregar_el_veredicto.py` (que ya hace intersección de
pasadas, ground truth CONS ∪ OCR con alias completo, filtro nocturno A76, IC bootstrap y
desagregación por volcán). Cambiar sólo los `BRAZOS` y agregar NevadosDeChillan a `VOLS`
con su alias `{"NevadosDeChillan", "Nevados de Chillan", "Nevados de Chillán"}`.

- [ ] **Step 5: Escribir el veredicto contra el pre-registro, criterio por criterio**

En `docs/S126_CORONA_RESULTADO.md`, una fila por criterio con CUMPLE / NO CUMPLE. Si
falla alguno de los criterios 2, 3 o 4, el veredicto es NO ADOPTAR aunque la mediana
mejore.

- [ ] **Step 6: Commit**

```bash
git add experiments/_s126_corona/ docs/S126_CORONA_RESULTADO.md
git commit -m "exp(s126): veredicto del A/B de la corona Eq.6"
```

---

## Lo que este plan NO hace

- **No apaga el filtro contextual.** Está probado que apagarlo destapa el halo
  (`docs/S126_COSTO_FILTRO_CONTEXTUAL.md`). Si la corona resuelve el fondo
  autorreferente, el filtro se puede reevaluar DESPUÉS, en su propio A/B.
- **No toca `TEST1_INTERMEDIATE_BG_RING_KM` ni `TEST1_ROI_KM`.** El anillo sigue
  gobernando la detección; sólo se le saca el rol de fondo de la magnitud.
- **No cablea la corona en los paths contextuales de VIIRS.** El fondo
  autorreferente está en el path Test 1; ahí se ataca.
- **No toca VIIRS 750.** Alcance acotado por Nicolás; el port queda para después.
- **No promueve nada a `mirova_equivalent`.** El flip es una decisión separada, de
  Nicolás, con el resultado del A/B a la vista.


---

## Registro de ejecución (S126)

- **Task 0** — tag `pre-s126-corona-viirs` en el remote + confirmación explícita. ✅
- **Task 1** — flag `ENABLE_LOCAL_CLUSTER_MAGNITUDE_VIIRS375`, OFF default. ✅
- **Task 2** — helper `apply_corona_magnitude_v375` + cableado en el bloque Test 1.
  A49 verificado: **71 líneas agregadas, 0 borradas**. Suite 919 verdes. ✅
- **Task 3** — perfiles `_s126_corona_{off,on}` + `docs/S126_CORONA_PREREGISTRO.md`. ✅
- **Task 4** — A/B: pendiente del merge de #539.

### Lo que el plan atrapó y hay que recordar

El paso de verificación de perfiles **por `pipeline.profile` en vez del YAML**
evitó un accidente serio: el regex `^data_subdir:` no matcheó porque la clave va
indentada bajo `output:`, así que los dos brazos quedaron apuntando a
`data/mirova_equivalent/` y habrían **escrito sobre la data de producción**. El
paso existía precisamente para eso y funcionó.

El checkpoint de la Task 2 —"si el test de discriminación falla, parar, la
hipótesis es falsa"— **pasó**: 8,8× de separación entre foco y fluctuación con el
mismo píxel.
