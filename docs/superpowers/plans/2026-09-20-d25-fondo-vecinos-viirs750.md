# D25 (fondo por vecinos) en VIIRS 750: plan de implementación con el flag apagado

> **Para quien lo ejecute:** las tareas están en pasos con casilla (`- [ ]`). Cada paso es una
> acción de 2 a 5 minutos. El orden importa: los tests van antes que el código.

**Objetivo.** Llevar a VIIRS 750 (M-band) el mismo fondo por vecinos que VIIRS 375 ya tiene desde
S142, dejándolo **apagado en producción**, con sus tests y con el A/B pre-registrado escrito, para
que la decisión de adoptarlo se tome con una medición y no con un argumento.

**Arquitectura.** No hay algoritmo nuevo: `pipeline/vrp_regimes.py:neighbor_mean_radiance_background`
ya es agnóstica de sensor (recibe `wavelength_um`). El trabajo es un envoltorio de respaldo para
M13, un flag propio, tres sitios de cableado en `pipeline/process_viirs_mod.py`, el bloque de
diagnostico, y el ajuste de los guards que hoy afirman que VIIRS 750 no conoce este fondo.

**Herramientas.** Python 3.12, numpy, pytest, el arnés sintético de S142
(`tests/arnes_sintetico_s142.py`) y el banco de paridad (`scripts/banco_paridad.py`, predicado del
dashboard con node).

---

## 0. Por qué, antes del código

En una cumbre nevada, de noche, la temperatura en el infrarrojo medio sigue la altitud: el cráter
está alto y frío, y el anillo de 5 a 25 km con que hoy calculamos el fondo está lleno de valle
tibio de baja cota. Cuando ese cráter tiene lava sub-píxel, su exceso sobre semejante fondo sale
**negativo**, el código lo recorta a cero y el volcán desaparece de la magnitud aunque la detección
lo haya aceptado. Es el mecanismo que explica las cinco pasadas de VIIRS 750 que MIROVA publica y
nosotros no (`docs/audit_s143/PERDIDAS_V750.md`): en las cinco encontramos el foco en el cráter, a
0,2 a 0,7 km, y le asignamos 0,0 MW.

El paper no pide ese anillo. Coppola 2016a (p. 8, ecuación 6) resta como fondo *"the arithmetic
mean of all the pixels surrounding the active one"*; Fernandina 2025 (p. 9) precisa que son los
vecinos **no alertados**, y Campus 2024 (p. 3) que cada píxel alertado tiene **su propio** fondo.
Siete textos del grupo coinciden (`docs/MIROVA_DIVERGENCES.md` D25). Nuestro anillo con mediana es
la divergencia, y hoy la tenemos corregida sólo en un sensor de tres.

**Pero este plan no promete recall, y conviene decirlo antes de empezar.** El sustrato medido en
§1.2 dice que en VIIRS 750 este cambio no destapa ni una sola noche de alerta que hoy no esté
cubierta, y que su efecto dominante cae del lado de la sobre-publicación, que es la brecha real del
proyecto (A98). Por eso el entregable es el flag **apagado** más el A/B, no la adopción.

---

## 1. Evidencia verificada en esta sesión

### 1.1 Gate de misión (docs/MISSION.md, las 3 preguntas)

| pregunta | respuesta | apoyo |
|---|---|---|
| 1. ¿Está en papers MIROVA core? | **SÍ** | Coppola 2016a p. 8 ec. 6; Fernandina 2025 p. 9; Campus 2024 p. 3. Los tres están en la lista de 11 papers core. Cita verbatim en `docs/MIROVA_DIVERGENCES.md` D25 |
| 2. ¿Cierra divergencia documentada? | **SÍ** | D25, abierta desde S138 |
| 3. alineación interna | no aplica | — |

Además, el hecho canónico de MISSION dice que MIROVA es **un algoritmo por sensor, uniforme**.
Tener el fondo por vecinos en I-band y la mediana del anillo en M-band es justamente la conmutación
que ese principio prohíbe. Cerrar la asimetría va a favor del gate, no en contra.

### 1.2 Sustrato medido antes de cualquier A/B (regla S130)

Medido por `experiments/_s145_d25_v750/sustrato.py`, salida en `sustrato.json`. Ventana
**2026-03-01 a 2026-09-20**. "Publica" es el predicado del dashboard ejecutado con node (A97), con
su control de identidad en verde (`([0,1,1,1,0],[1,0])`, el mismo valor que exige
`tests/test_evaluador_ab_s143.py:603`).

**VIIRS 750, 9338 pasadas nocturnas** (los **11 volcanes Tier A**, que es lo que carga
`banco_paridad`; los otros 34 del `volcanoes.yaml` no tienen serie continua ni entran al cron):

| clase | n | qué le hace D25 |
|---|---|---|
| sin cúmulo | 5831 | nada: D25 es magnitud, no detección |
| cúmulo fuera del radio interno | 171 | nada que el dashboard publique |
| **rescate**: cúmulo en el cráter con 0,0 MW | **1035** | podría despegarlo de cero |
| **exposición**: cúmulo en el cráter con magnitud | **2301** (2299 publican hoy) | le sube la magnitud |

**Lo que el rescate compra y lo que cuesta, en noches (A94):**

| medida | valor |
|---|---|
| pasadas de rescate donde MIROVA alertó | 48 de 1035 |
| pasadas de rescate donde MIROVA miró y no vio nada | 489 de 1035 |
| **noches con alerta de MIROVA hoy sin cubrir que se destaparían** | **0** |
| noches nuevas que se estrenarían sin que MIROVA las confirme | 20 |

**Lo que la exposición arriesga:** de las 2299 que ya publican, MIROVA no vio nada en **1130** y
alertó en **223**.

La lectura honesta: en VIIRS 750 el fondo por vecinos **no agrega ni una noche de recall** (las 48
pasadas con alerta están todas en noches que otra pasada ya cubre) y pone en juego 1035 candidatos
a publicar más, con diez negativos limpios por cada alerta confirmada.

⚠️ **Los 1035 son un techo de exposición, no una predicción.** Este script no corre el pipeline:
clasifica lo que hay. Cuántas despegan realmente de cero, y cuánto sube la magnitud de las 2299, lo
contesta el A/B de §4 y nada más.

### 1.3 Evidencia previa que apunta en contra, y que hay que mirar de frente

Dos mediciones ya hechas tensionan la utilidad de este cambio:

- **A99 (S139)**: a igual número de píxeles la razón de magnitud contra MIROVA es **0,995**. Si el
  fondo bajara, el exceso subiría y esa paridad casi perfecta se pasaría de largo. El déficit de
  magnitud está en el **conteo de píxeles**, no en el fondo.
- **H_S141_VECINO_FOCO_V2 (S142)**, criterio pre-registrado, en VIIRS 375: *"el fondo del cúmulo
  (D25) no cierra la brecha en ninguno"* (`docs/HYPOTHESIS_LOG.md`, entrada resuelta como **no
  confirmada**). El mecanismo en M-band es el mismo; que el resultado también lo sea es **sospecha**,
  no medición.

Esto no invalida el gate de misión: la fidelidad literal al paper se justifica sola. Lo que dice es
que el A/B debe llevar la sobre-publicación como criterio primario y no como nota al pie.

### 1.4 Dónde se resta un fondo a la radiancia en VIIRS 750

Tres sitios, todos **posteriores** a que `hot_mask_2d` quede fijado, así que el cambio es de
magnitud y no toca detección:

| sitio | línea | qué hace |
|---|---|---|
| A, bloque contextual | `pipeline/process_viirs_mod.py:983-987` | `L_bg_rad` desde `t_bg` y `delta_L = np.maximum(L_hot - L_bg_rad, 0.0)` |
| B, primer recompute del Test 1 | `pipeline/process_viirs_mod.py:1198-1205` | `t1_delta_L = np.maximum(t1_L - effective_L_bg, 0.0)` |
| C, segundo recompute del Test 1 (cúmulo) | `pipeline/process_viirs_mod.py:1214-1221` | igual que B, sobre `t1_vrp_2d` |

La máscara de alertados es `hot_mask_2d`, fijada en `:785-853`, y el recompute del Test 1 usa
`test1_hot_filtered`. En VIIRS 375 el orden equivalente es `process_viirs.py:1459`, `:1921` y
`:1952`, con `hot_mask_2d` cerrado en `:1386`.

### 1.5 Guards que este cambio rompe, y que hay que mover a propósito

Tres contratos se tocan. No son daño colateral: son lo que el cambio modifica, y moverlos sin
pensar es exactamente lo que A92 previene. Los tres los encontro el verificador del plan; el
primero estaba declarado desde el principio, los otros dos no.

| test | qué exige hoy | qué debe exigir después |
|---|---|---|
| `tests/test_d25_fondo_vecinos_s142.py:223` `test_modis_y_viirs750_no_conocen_el_fondo_por_vecinos` | que `process_modis.py` **y** `process_viirs_mod.py` no nombren `neighbor_mean_radiance_background`, `vrp_bg_neighbor_mean_v375`, `VRP_BG_NEIGHBOR_MAX_HALF_PX` ni `ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375` | que **MODIS** siga sin nombrarlos, y que **VIIRS 750** use su propio flag y nunca el de I-band |
| `tests/test_apagado_no_cambia_nada_s142.py:133` `test_modis_y_viirs750_no_cambian_con_los_dos_flags_on` | que con el perfil de verificación de S142 (que enciende los flags de I-band) MODIS y V750 no se muevan | **lo mismo, sin cambios**: el flag nuevo es propio de V750 y ese perfil no lo enciende. Si este test se pusiera rojo, el flag nuevo se está leyendo donde no debe |
| `tests/test_guard_declarado_vs_efectivo_s131.py:153` y `:156` (contrato G8) | que `pipeline/process_viirs_mod.py` **línea 440** diga `Villarrica/PP/Lastarria/Chaiten/PCC` y su **línea 159** diga `compute_test1_mir` | las mismas dos anclas, **en su línea nueva**: toda inserción por encima de la 159 las corre hacia abajo. Lo encontró el verificador del plan; el import de la Tarea 1 Paso 3, de **una sola línea**, ya basta para romperlo |

⚠️ **El tercero es el que muerde callado.** No falla en `process_viirs_mod.py` sino en dos citas de
`CLAUDE.md`, un archivo que el ejecutor no tocó, así que el rojo aparece lejos de la causa. El
arreglo NO es recalcular las líneas a mano: es correr `scripts/remapear_citas.py`, que compara la
versión vieja (`origin/main`) con la del árbol usando `difflib` y **sólo** mueve citas que caen en
bloques idénticos (A101). Va en la Tarea 5.

El guard de `:223` usa frontera de palabra (`(?<![A-Za-z0-9_])token(?![A-Za-z0-9_])`), así que
`..._VIIRS375` y `..._VIIRS750` no se confunden entre sí. `VRP_BG_NEIGHBOR_MAX_HALF_PX` sí es
compartido y por eso el guard nuevo debe dejarlo pasar en V750 explícitamente.

---

## 2. Mapa de archivos

### 2.1 Crear

| archivo | responsabilidad |
|---|---|
| `tests/test_d25_fondo_vecinos_v750_s145.py` | el envoltorio de M13, el cableado de los 3 sitios y la simetría entre sensores |
| `docs/superpowers/plans/2026-09-20-d25-fondo-vecinos-viirs750.md` | este plan |
| `experiments/_s145_d25_v750/sustrato.py` + `sustrato.json` | ya creados: el sustrato de §1.2 |

### 2.2 Modificar

| archivo | cambio |
|---|---|
| `pipeline/profile.py` | agregar `ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750` (default `False`), junto al de I-band |
| `pipeline/profiles/mirova_equivalent.yaml` | `enable_vrp_bg_neighbor_mean_viirs750: false`, explícito |
| `pipeline/process_viirs_mod.py` | import del helper, envoltorio `vrp_bg_neighbor_mean_v750`, cableado en los sitios A, B y C, y los dos diagnósticos del record |
| `tests/test_d25_fondo_vecinos_s142.py:223` | el guard pasa a distinguir MODIS de V750 |
| `docs/MIROVA_DIVERGENCES.md` D25 | anotar que existe el flag de V750, apagado, con el sustrato medido |

---

## 3. Tareas

### Tarea 0: rama, tag defensivo y línea base

Esta tarea es obligatoria y no se salta: `process_viirs_mod.py` corre en el cron NRT 12 veces al día
sobre 11 volcanes (A45).

- [ ] **Paso 1: rama desde main al día**

```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune && git pull --ff-only
git checkout -b s145-d25-v750 origin/main
```

- [ ] **Paso 2: tag defensivo y subirlo**

```bash
git tag -a pre-s145-d25-v750 -m "snapshot defensivo antes de tocar process_viirs_mod.py (D25 M-band)"
git push origin pre-s145-d25-v750
```

- [ ] **Paso 3: línea base de la suite, para comparar al final**

Ejecutar: `python -m pytest tests/ -q -p no:cacheprovider | tail -1`

**Anotar el numero que devuelva, no compararlo contra uno escrito aca.** La suite crece entre
sesiones y una cifra fija en un plan envejece hacia el falso positivo (A90): al 2026-09-20, con el
sustrato de esta sesion ya en el arbol, son **1556 passed, 4 skipped, 2 xfailed**, pero lo que vale
es lo que mida el ejecutor en su rama. Esa cifra es la base contra la que se comparan las Tareas 6.

- [ ] **Paso 4: confirmación explícita del dueño**

No avanzar sin el sí de Nicolás por A45, aunque la suite esté verde.

---

### Tarea 1: el envoltorio de M13 y su test

El envoltorio decide el respaldo cuando un píxel no tiene vecinos no alertados: el fondo que el
bloque usaría hoy. Es el espejo exacto de `process_viirs.py:682`, con `M13_LAMBDA` en vez de
`I04_LAMBDA`.

**Archivos:**
- Crear: `tests/test_d25_fondo_vecinos_v750_s145.py`
- Modificar: `pipeline/process_viirs_mod.py` (import + envoltorio)

- [ ] **Paso 1: escribir el test que falla**

```python
# -*- coding: utf-8 -*-
"""S145: el fondo por vecinos (D25) en VIIRS 750 (M-band).

POR QUE. El helper de vrp_regimes ya es agnostico de sensor; lo que este archivo fija es que en
M-band se use M13_LAMBDA (4,05 um) y no I04, que el respaldo del pixel sin vecinos sea el fondo de
hoy, y que el flag propio de V750 no se confunda con el de I-band (A92).
"""
import re
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# M13_LAMBDA NO vive en pipeline.constants: esta definido en el propio process_viirs_mod (l. 165),
# igual que I04_LAMBDA vive en process_viirs. Importarlo de constants da ImportError.
from pipeline.process_viirs_mod import M13_LAMBDA, vrp_bg_neighbor_mean_v750  # noqa: E402
from pipeline.vrp_regimes import neighbor_mean_radiance_background  # noqa: E402


def test_el_envoltorio_de_m_band_usa_la_longitud_de_onda_de_m13():
    """Si usara I04 (3,74 um) el fondo saldria distinto: Planck no es plano entre 3,74 y 4,05 um."""
    bt = np.full((5, 5), 270.0)
    bt[2, 2] = 400.0
    alerta = np.zeros((5, 5), dtype=bool)
    alerta[2, 2] = True
    l_bg, n_sin = vrp_bg_neighbor_mean_v750(bt, alerta, [2], [2], 9.99, max_half_px=1)
    esperado, _ = neighbor_mean_radiance_background(
        bt, alerta, [2], [2], M13_LAMBDA, max_half_px=1)
    assert n_sin == 0
    np.testing.assert_allclose(l_bg, esperado)


def test_sin_vecinos_no_alertados_cae_al_fondo_de_hoy_y_lo_cuenta():
    """Un unico pixel de una escena 1x1: no hay a quien promediar, manda el respaldo."""
    bt = np.full((1, 1), 300.0)
    alerta = np.ones((1, 1), dtype=bool)
    l_bg, n_sin = vrp_bg_neighbor_mean_v750(bt, alerta, [0], [0], 0.1234, max_half_px=3)
    assert n_sin == 1
    np.testing.assert_allclose(l_bg, [0.1234])
```

- [ ] **Paso 2: correr el test y ver que falla**

Ejecutar: `python -m pytest tests/test_d25_fondo_vecinos_v750_s145.py -q`
Esperado: FALLA con `ImportError: cannot import name 'vrp_bg_neighbor_mean_v750'`.

- [ ] **Paso 3: agregar el import del helper**

En `pipeline/process_viirs_mod.py`, junto al import de `cluster_focal_vrp_mw` (hoy la línea 147):

```python
from .vrp_regimes import cluster_focal_vrp_mw  # S112 magnitud núcleo-focal (A69/D11)
from .vrp_regimes import neighbor_mean_radiance_background  # S145 D25 en M-band
```

- [ ] **Paso 4: escribir el envoltorio**

En `pipeline/process_viirs_mod.py`, inmediatamente antes de `def calculate_vrp(`:

```python
def vrp_bg_neighbor_mean_v750(bt_grid, alert_mask, hot_rows, hot_cols, legacy_l_bg, *, max_half_px):
    """Fondo MIR por píxel para el VRP de VIIRS 750 con el flag D25 de M-band encendido (S145).

    POR QUÉ UN ENVOLTORIO. `neighbor_mean_radiance_background` devuelve NaN para el píxel sin
    vecinos no alertados dentro de `max_half_px`. Acá se decide el respaldo: el fondo que el bloque
    usaría HOY (`legacy_l_bg`, que en M-band es la mediana del anillo o el L_bg efectivo del Test 1).
    Así el flag nunca deja a un píxel sin fondo, y el respaldo queda contado en el record.

    POR QUÉ NO SE REUSA EL DE I-BAND. El de `process_viirs.py` fija `I04_LAMBDA` (3,74 µm). Acá la
    banda MIR es M13 (4,05 µm) y Planck no es plano entre las dos: usar la longitud equivocada
    sesgaría el fondo de todo el sensor.

    Returns:
        (l_bg, n_sin_vecinos): radiancia de fondo por píxel (float64) y cuántos usaron el respaldo.
    """
    l_bk, _half = neighbor_mean_radiance_background(
        bt_grid, alert_mask, hot_rows, hot_cols, M13_LAMBDA, max_half_px=max_half_px)
    respaldo = np.broadcast_to(np.asarray(legacy_l_bg, dtype=np.float64), l_bk.shape)
    sin_vecinos = ~np.isfinite(l_bk)
    return np.where(sin_vecinos, respaldo, l_bk), int(np.count_nonzero(sin_vecinos))
```

- [ ] **Paso 5: correr el test y ver que pasa**

Ejecutar: `python -m pytest tests/test_d25_fondo_vecinos_v750_s145.py -q`
Esperado: `2 passed`.

- [ ] **Paso 6: commit**

```bash
git add tests/test_d25_fondo_vecinos_v750_s145.py pipeline/process_viirs_mod.py
git commit -m "S145 D25: envoltorio del fondo por vecinos para M-band (sin cablear)"
```

---

### Tarea 2: el flag propio de VIIRS 750, apagado

**Archivos:**
- Modificar: `pipeline/profile.py` (bloque D25, hoy las líneas 490-498)
- Modificar: `pipeline/profiles/mirova_equivalent.yaml`
- Modificar: `tests/test_d25_fondo_vecinos_v750_s145.py`

- [ ] **Paso 1: escribir el test que falla**

Agregar al final de `tests/test_d25_fondo_vecinos_v750_s145.py`:

```python
def test_el_flag_de_v750_existe_y_esta_apagado_en_el_perfil_operacional():
    """A45: el default operacional es OFF; encenderlo es una decision aparte, con A/B."""
    import pipeline.profile as p
    assert hasattr(p, "ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750")
    assert p.ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750 is False


def test_los_dos_flags_son_independientes_y_no_se_confunden_por_subcadena():
    """A92: ningun nombre es subcadena del otro, y el YAML declara los dos por separado."""
    import pipeline.profile as p
    i, m = "ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375", "ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750"
    assert i not in m and m not in i
    yaml_txt = (ROOT / "pipeline" / "profiles" / "mirova_equivalent.yaml").read_text(encoding="utf-8")
    for clave in ("enable_vrp_bg_neighbor_mean_viirs375", "enable_vrp_bg_neighbor_mean_viirs750"):
        assert re.search(r"^\s*" + clave + r"\s*:", yaml_txt, re.M), clave
    assert getattr(p, i) is False and getattr(p, m) is False
```

- [ ] **Paso 2: correr y ver que falla**

Ejecutar: `python -m pytest tests/test_d25_fondo_vecinos_v750_s145.py -q`
Esperado: FALLA con `AssertionError` en `hasattr(p, "ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750")`.

- [ ] **Paso 3: agregar el flag en `pipeline/profile.py`**

Justo debajo de `ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375` (hoy la línea 498):

```python
# S145 D25 en M-band: el mismo fondo por vecinos, para VIIRS 750. Flag PROPIO y no el de I-band,
# porque la banda MIR es otra (M13 4,05 µm contra I04 3,74 µm) y porque la decisión de adoptar se
# toma por sensor, con su propio A/B. Comparte VRP_BG_NEIGHBOR_MAX_HALF_PX. OFF por A45: el sustrato
# medido en S145 (experiments/_s145_d25_v750/sustrato.json) dice que en V750 no destapa ninguna
# noche de alerta hoy sin cubrir y expone 1035 pasadas a publicar de más.
ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750: bool = bool(
    _p.get("enable_vrp_bg_neighbor_mean_viirs750", False))
```

- [ ] **Paso 4: declararlo apagado en el perfil operacional**

En `pipeline/profiles/mirova_equivalent.yaml`, junto a `enable_vrp_bg_neighbor_mean_viirs375`:

```yaml
  # S145 D25 en VIIRS 750 (M-band). OFF: ver docs/superpowers/plans/2026-09-20-d25-fondo-vecinos-viirs750.md
  enable_vrp_bg_neighbor_mean_viirs750: false
```

Verificar en qué sección vive la clave de I-band antes de escribir (el bug de S124: una clave
escrita en la raíz y leída de `thresholds:` arranca siempre apagada y su A/B corre cuatro brazos
idénticos). `pipeline/profile.py` la lee de `_p`, así que va en la misma sección que la de 375.

- [ ] **Paso 5: correr y ver que pasa**

Ejecutar: `python -m pytest tests/test_d25_fondo_vecinos_v750_s145.py -q`
Esperado: `4 passed`.

- [ ] **Paso 6: commit**

```bash
git add pipeline/profile.py pipeline/profiles/mirova_equivalent.yaml tests/test_d25_fondo_vecinos_v750_s145.py
git commit -m "S145 D25: flag propio de VIIRS 750, apagado en el perfil operacional"
```

---

### Tarea 3: cablear los tres sitios

**Archivos:**
- Modificar: `pipeline/process_viirs_mod.py` sitios A (`:983-987`), B (`:1198-1205`), C (`:1214-1221`)

⚠️ **A49**: cada edición inserta código **entre** estructuras existentes. Antes de commitear, correr
`git diff` y comprobar que ni la línea anterior ni la siguiente al bloque nuevo desaparecieron.

- [ ] **Paso 1: escribir el test de cableado que falla**

Agregar a `tests/test_d25_fondo_vecinos_v750_s145.py`:

```python
def _fuente_v750():
    return (ROOT / "pipeline" / "process_viirs_mod.py").read_text(encoding="utf-8")


def test_los_tres_sitios_de_fondo_consultan_el_flag():
    """Los 3 bloques que restan fondo en M-band deben pasar por el envoltorio cuando el flag esta ON.

    Se cuenta la GUARDA, no el nombre suelto: un import sin cablear dejaria el flag inerte y este
    test en verde (A89, el cero de un grep se lee como ausencia).
    """
    s = _fuente_v750()
    guardas = re.findall(r"if ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750:", s)
    assert len(guardas) == 3, f"esperaba 3 guardas (sitios A, B y C), hay {len(guardas)}"
    assert s.count("vrp_bg_neighbor_mean_v750(") == 4, "3 llamadas + la definicion"


def test_el_recorte_a_cero_sigue_despues_del_fondo_nuevo():
    """D25 cambia el FONDO; el recorte del exceso negativo es otra pregunta, abierta con el autor."""
    s = _fuente_v750()
    assert s.count("np.maximum(") >= 3
    assert "ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750" in s


def test_v750_no_nombra_el_flag_de_i_band():
    """A92: el sensor equivocado leyendo el flag del otro es el modo de falla de esta familia."""
    s = _fuente_v750()
    assert not re.search(r"(?<![A-Za-z0-9_])ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375(?![A-Za-z0-9_])", s)
    assert not re.search(r"(?<![A-Za-z0-9_])vrp_bg_neighbor_mean_v375(?![A-Za-z0-9_])", s)


def test_el_contador_se_reinicia_solo_en_el_bloque_que_publica():
    """Espejo exacto de la forma de I-band (tests/test_d25_fondo_vecinos_s142.py:216-219).

    El bloque contextual ACUMULA (+=), el segundo recompute del Test 1 REINICIA (=), y el primero
    no cuenta: si contara, el diagnostico describiria una poblacion distinta de la publicada.
    """
    s = _fuente_v750()
    assert len(re.findall(r"_bg_vecinos_n_sin_vecinos \+= _n_sin", s)) == 1
    assert len(re.findall(r"_bg_vecinos_n_sin_vecinos = _n_sin", s)) == 1
    assert len(re.findall(r"diag_L_bg_vecinos = redondear_diag\(", s)) == 2


def test_el_fondo_del_test1_promedia_sobre_la_union_de_alertados():
    """Un vecino alertado por la ruta contextual no puede entrar al promedio del fondo del Test 1."""
    s = _fuente_v750()
    union = re.findall(
        r"np\.asarray\(hot_mask_2d, dtype=bool\) \| np\.asarray\(test1_hot_filtered, dtype=bool\)", s)
    assert len(union) == 2, f"los 2 bloques del Test 1 deben usar la union; hay {len(union)}"
```

- [ ] **Paso 2: correr y ver que falla**

Ejecutar: `python -m pytest tests/test_d25_fondo_vecinos_v750_s145.py -q -k sitios`
Esperado: FALLA con `esperaba 3 guardas (sitios A, B y C), hay 0`.

- [ ] **Paso 3: importar el flag y las constantes en `process_viirs_mod.py`**

Agregar `ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750` y `VRP_BG_NEIGHBOR_MAX_HALF_PX` a la lista del
`from pipeline.profile import (` que empieza en la línea 73.

- [ ] **Paso 4: cablear el sitio A (bloque contextual)**

En `pipeline/process_viirs_mod.py`, después de `L_bg_rad = bt_to_spectral_radiance(...)` y **antes**
de `delta_L = np.maximum(...)`:

```python
        L_bg_rad = bt_to_spectral_radiance(np.float64(t_bg), M13_LAMBDA)
        # D25 (S145): fondo = media de la radiancia de los vecinos NO alertados de cada píxel
        # alertado (Coppola 2016a ec. 6). POR QUÉ: en la cumbre nevada la mediana del anillo
        # 5-25 km es valle tibio y deja al cráter con exceso negativo, recortado a 0,0 MW.
        # Va DESPUÉS del bloque de arriba a propósito: su resultado es el respaldo del píxel sin
        # vecinos no alertados. Los alertados son hot_mask_2d entero.
        if ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750:
            L_bg_rad, _n_sin = vrp_bg_neighbor_mean_v750(
                bt, hot_mask_2d, hot_rows, hot_cols, L_bg_rad,
                max_half_px=VRP_BG_NEIGHBOR_MAX_HALF_PX)
            _bg_vecinos_n_sin_vecinos += _n_sin
            diag_L_bg_vecinos = redondear_diag(float(np.nanmedian(L_bg_rad)))
        # Per-pixel area accounts for scan-angle elongation
        hotpix_area = pixel_areas[hot_rows, hot_cols]
        # S26: clip ΔL ≥ 0 (paridad MODIS/VIIRS 375m). Wooster physics.
        delta_L = np.maximum(L_hot - L_bg_rad, 0.0)
```

- [ ] **Paso 5: cablear el sitio B (primer recompute del Test 1)**

Después de `t1_L = bt_to_spectral_radiance(t1_bt, M13_LAMBDA)` y antes de `t1_delta_L`. Dos
detalles que el espejo de I-band (`process_viirs.py:1918-1927`) fija y que **no** son libres:

- los alertados son la **unión** `hot_mask_2d | test1_hot_filtered`, no el disco del Test 1 solo:
  un vecino alertado por la ruta contextual no puede entrar al promedio del fondo;
- este bloque **no** toca el contador ni la mediana de diagnóstico. No es olvido: este recompute no
  reconstruye `anomaly_pixels`, así que si contara acá, el diagnóstico describiría una población
  distinta de la que se publica (hallazgo H8 del verificador del plan de S142).

```python
            t1_L = bt_to_spectral_radiance(t1_bt, M13_LAMBDA)
            _t1_Lbg = effective_L_bg
            if ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750:
                # D25 (S145): mismo fondo por vecinos que el bloque contextual. Respaldo =
                # effective_L_bg. Sin contador: este bloque no reconstruye anomaly_pixels.
                _t1_Lbg, _n_sin = vrp_bg_neighbor_mean_v750(
                    bt, np.asarray(hot_mask_2d, dtype=bool) | np.asarray(test1_hot_filtered, dtype=bool),
                    t1_rows, t1_cols, effective_L_bg, max_half_px=VRP_BG_NEIGHBOR_MAX_HALF_PX)
            t1_delta_L = np.maximum(t1_L - _t1_Lbg, 0.0)
```

- [ ] **Paso 6: cablear el sitio C (el recompute que reconstruye `anomaly_pixels`)**

Igual que el anterior, y **acá sí** se reinician el contador y la mediana, con `=` y no con `+=`,
porque tienen que describir la población publicada y no la suma de dos bloques con píxeles
distintos:

```python
            t1_L = bt_to_spectral_radiance(t1_bt, M13_LAMBDA)
            _t1_Lbg = effective_L_bg
            if ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750:
                # D25 (S145): ídem bloque anterior. Este es el que reconstruye anomaly_pixels (lo
                # que suma F5 en store.py), así que el contador y la mediana se REINICIAN acá.
                _t1_Lbg, _n_sin = vrp_bg_neighbor_mean_v750(
                    bt, np.asarray(hot_mask_2d, dtype=bool) | np.asarray(test1_hot_filtered, dtype=bool),
                    t1_rows, t1_cols, effective_L_bg, max_half_px=VRP_BG_NEIGHBOR_MAX_HALF_PX)
                _bg_vecinos_n_sin_vecinos = _n_sin
                diag_L_bg_vecinos = redondear_diag(float(np.nanmedian(_t1_Lbg)))
            t1_delta_L = np.maximum(t1_L - _t1_Lbg, 0.0)
```

- [ ] **Paso 7: inicializar los dos acumuladores**

Junto a las demás inicializaciones de diagnóstico del comienzo de `calculate_vrp` (cerca de la
línea 927 en el archivo de I-band; en M-band, junto a `hotspot_dist_km = None`):

```python
    _bg_vecinos_n_sin_vecinos = 0
    diag_L_bg_vecinos = None
```

- [ ] **Paso 8: correr el test y ver que pasa**

Ejecutar: `python -m pytest tests/test_d25_fondo_vecinos_v750_s145.py -q`
Esperado: `9 passed` (2 de la Tarea 1, 2 de la Tarea 2, 5 de esta).

- [ ] **Paso 9: comprobar que no se comió ninguna línea vecina (A49)**

Ejecutar: `git diff pipeline/process_viirs_mod.py`
Esperado: sólo líneas agregadas; ningún `return`, ningún `delta_L =` ni `hotpix_area =` borrado.

- [ ] **Paso 10: commit**

```bash
git add pipeline/process_viirs_mod.py tests/test_d25_fondo_vecinos_v750_s145.py
git commit -m "S145 D25: cablear el fondo por vecinos en los 3 sitios de magnitud de M-band (flag OFF)"
```

---

### Tarea 4: los diagnósticos en el registro de salida

Sin estos campos, el A/B no puede distinguir un fondo por vecinos real de un respaldo silencioso.

⚠️ **M-band NO tiene variable `record`.** Esto lo encontró el verificador del plan y es la
diferencia con I-band que hay que respetar: `process_viirs.py` arma un `record = {...}`, lo completa
y lo devuelve; `process_viirs_mod.py:1328` hace `return {` con un **dict literal** que cierra en la
línea 1405, y las únicas dos apariciones del string "record" en el archivo son comentarios. No se
puede escribir `record["..."]`. La salida mínima es nombrar el dict y devolverlo, que es **una línea
cambiada** más el bloque nuevo: el cuerpo del dict no se toca.

- [ ] **Paso 1: escribir el test que falla**

```python
def test_los_diagnosticos_solo_aparecen_con_el_flag_encendido():
    """Con el flag OFF la salida queda IDENTICA a la de hoy: ni una clave nueva.

    M-band no tiene variable `record` como I-band: arma un dict literal y lo devuelve. Por eso el
    bloque se escribe sobre `salida`, el nombre que la Tarea 4 le pone a ese dict.
    """
    s = _fuente_v750()
    assert 'salida["diag_L_bg_vecinos_w_m2_sr_um"]' in s
    assert 'salida["diag_bg_vecinos_n_sin_vecinos"]' in s
    bloque = s.split("if ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750:")[-1]
    assert "diag_L_bg_vecinos_w_m2_sr_um" in bloque, "los diag deben colgar de la guarda del flag"


def test_el_dict_de_salida_se_devuelve_una_sola_vez():
    """Control de A49: nombrar el dict no puede dejar un `return` huerfano ni duplicado."""
    s = _fuente_v750()
    assert s.count("    salida = {") == 1
    assert s.count("    return salida") == 1
```

- [ ] **Paso 2: correr y ver que falla**

Ejecutar: `python -m pytest tests/test_d25_fondo_vecinos_v750_s145.py -q -k "diagnosticos or salida"`
Esperado: FALLA en el primer `assert`.

- [ ] **Paso 3: nombrar el dict de salida**

En `pipeline/process_viirs_mod.py`, cambiar **sólo** la línea de apertura (hoy la 1328):

```python
    return {
```

por:

```python
    salida = {
```

El cuerpo del dict (hasta el `}` de la línea 1405) **no se toca**.

- [ ] **Paso 4: agregar el bloque y el return, justo después del `}` que cierra el dict**

```python
    }

    # S145 D25: diagnóstico del fondo por vecinos en M-band. Con el flag OFF los campos NO aparecen
    # y la salida queda idéntica a la de hoy. `n_sin_vecinos` cuenta los píxeles que cayeron al
    # respaldo en el bloque que publica.
    if ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750:
        salida["diag_L_bg_vecinos_w_m2_sr_um"] = diag_L_bg_vecinos
        salida["diag_bg_vecinos_n_sin_vecinos"] = int(_bg_vecinos_n_sin_vecinos)

    return salida
```

- [ ] **Paso 5: actualizar el conteo de guardas de la Tarea 3, de 3 a 4**

Este bloque abre la **cuarta** guarda `if ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750:`, así que el test
`test_los_tres_sitios_de_fondo_consultan_el_flag` de la Tarea 3 se pone en rojo. No es un error: es
el mismo número que tiene I-band (`grep -c "if ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375:"
pipeline/process_viirs.py` devuelve **4**: los 3 sitios de magnitud más el de diagnóstico).
Cambiar en ese test:

```python
    guardas = re.findall(r"if ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750:", s)
    assert len(guardas) == 4, (
        f"esperaba 4 guardas (sitios A, B, C y el bloque de diagnostico), hay {len(guardas)}")
    assert s.count("vrp_bg_neighbor_mean_v750(") == 4, "3 llamadas + la definicion"
```

y renombrar la función a `test_los_cuatro_usos_del_flag_estan_donde_corresponde`, para que el
nombre no mienta.

- [ ] **Paso 6: correr y ver que pasa**

Ejecutar: `python -m pytest tests/test_d25_fondo_vecinos_v750_s145.py -q`
Esperado: `11 passed` (2 de la Tarea 1, 2 de la Tarea 2, 5 de la Tarea 3, 2 de esta).

- [ ] **Paso 7: commit**

```bash
git add pipeline/process_viirs_mod.py tests/test_d25_fondo_vecinos_v750_s145.py
git commit -m "S145 D25: diagnosticos del fondo por vecinos en la salida de M-band"
```

---

### Tarea 4b: un test que ejerza el flag ENCENDIDO de punta a punta

Seis de los tests anteriores son greps sobre el fuente: comprueban que el cableado **está escrito**,
no que **funcione**. Falta el que corre el pipeline con el flag ON sobre una escena sintética. El
arnés de S142 ya trae la escena de M-band: `tests/arnes_sintetico_s142.py:188 correr_v750(tipo)`.

- [ ] **Paso 1: escribir el test que falla**

```python
def test_con_el_flag_on_el_crater_en_cero_deja_de_estar_en_cero(monkeypatch):
    """El punto entero del cambio: en la escena nevada el crater sale mas frio que la mediana del
    anillo, su exceso se recorta a 0,0 MW, y el fondo por vecinos lo despega."""
    import pipeline.process_viirs_mod as pvm
    sys.path.insert(0, str(ROOT / "tests"))
    import arnes_sintetico_s142 as arnes

    apagado = arnes.correr_v750("nevado_vecino_tibio")
    monkeypatch.setattr(pvm, "ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750", True)
    encendido = arnes.correr_v750("nevado_vecino_tibio")

    assert encendido["vrp_mw"] > apagado["vrp_mw"], (
        "el fondo por vecinos es mas frio que la mediana del anillo: el exceso tiene que subir")
    assert "diag_L_bg_vecinos_w_m2_sr_um" in encendido
    assert "diag_L_bg_vecinos_w_m2_sr_um" not in apagado
```

- [ ] **Paso 2: correr y ver que falla**

Ejecutar: `python -m pytest tests/test_d25_fondo_vecinos_v750_s145.py -q -k punta`
Esperado: FALLA. Si falla porque la escena `nevado_vecino_tibio` **no** ejerce el camino (los dos
VRP salen iguales con el flag ON), eso es un **hallazgo de instrumento**, no un test malo: anotarlo
y elegir la escena del arnés que sí lo ejerza antes de seguir. Un test que pasa porque la escena no
toca el camino es peor que no tenerlo (A110).

- [ ] **Paso 3: no hay implementación nueva**

Las Tareas 3 y 4 ya pusieron el código. Este test sólo comprueba que hace lo que dice.

- [ ] **Paso 4: commit**

```bash
git add tests/test_d25_fondo_vecinos_v750_s145.py
git commit -m "S145 D25: test de punta a punta con el flag encendido en M-band"
```

---

### Tarea 5: mover el guard de S142 a propósito

**Archivos:**
- Modificar: `tests/test_d25_fondo_vecinos_s142.py:223`

- [ ] **Paso 1: correr la suite de S142 y ver el rojo esperado**

Ejecutar: `python -m pytest tests/test_d25_fondo_vecinos_s142.py -q`
Esperado: FALLA `test_modis_y_viirs750_no_conocen_el_fondo_por_vecinos` con
`('pipeline/process_viirs_mod.py', 'neighbor_mean_radiance_background')`.

Este rojo es **la prueba de que el guard servía**. Si no apareciera, el cableado de la Tarea 3 no
estaría en el archivo que el guard vigila.

- [ ] **Paso 2: reemplazar el test por su versión de dos sensores**

⚠️ **Conservar el decorador**: `rel` no es una fixture, es un
`@pytest.mark.parametrize("rel", ["pipeline/process_modis.py", "pipeline/process_viirs_mod.py"])`
que está justo encima (hoy la línea 221). Sin él, el test falla con `fixture 'rel' not found`.

```python
@pytest.mark.parametrize("rel", ["pipeline/process_modis.py", "pipeline/process_viirs_mod.py"])
def test_modis_no_conoce_el_fondo_por_vecinos_y_v750_usa_solo_el_suyo(rel):
    """MODIS sigue con la mediana del anillo (D25 abierta ahi, S145 no lo toca).

    VIIRS 750 desde S145 tiene su propio fondo por vecinos: puede nombrar el helper compartido y su
    propio flag, nunca el de I-band (A92: el modo de falla de esta familia es el sensor equivocado
    leyendo el flag del otro).
    """
    s = _src(rel)
    prohibidos = ["ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375", "vrp_bg_neighbor_mean_v375"]
    if "process_modis" in rel:
        prohibidos += ["neighbor_mean_radiance_background", "VRP_BG_NEIGHBOR_MAX_HALF_PX",
                       "ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750"]
    else:
        # control de instrumento: si V750 dejara de cablearlo, este test pasaria por omision
        assert re.search(r"(?<![A-Za-z0-9_])ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750(?![A-Za-z0-9_])", s)
    for token in prohibidos:
        assert not re.search(r"(?<![A-Za-z0-9_])" + token + r"(?![A-Za-z0-9_])", s), (rel, token)
```

- [ ] **Paso 3: correr y ver que pasa**

Ejecutar: `python -m pytest tests/test_d25_fondo_vecinos_s142.py -q`
Esperado: todos en verde, incluido `test_modis_y_viirs750_no_cambian_con_los_dos_flags_on`, que
**no se toca** (el perfil de verificación de S142 no enciende el flag nuevo).

- [ ] **Paso 4: barrer la familia de guards por subcadena (A92)**

Ejecutar: `python experiments/_s133/auditar_guards_por_subcadena.py`
Esperado: 0 candidatos. Si aparece alguno nuevo, endurecerlo a frontera de palabra antes de seguir.

- [ ] **Paso 5: remapear las citas `archivo:línea` que la inserción corrió (A101)**

Las inserciones de las Tareas 1, 3 y 4 empujaron hacia abajo todo lo que está debajo en
`process_viirs_mod.py`, y el contrato G8 pinea dos anclas de ese archivo desde `CLAUDE.md`. **No
recalcular las líneas a mano ni con aritmética**: el script las mueve por contenido y sólo cuando el
bloque es idéntico.

Ejecutar: `python scripts/remapear_citas.py`
Esperado: reporta las citas movidas de `pipeline/process_viirs_mod.py`. Revisar el diff de
`CLAUDE.md` antes de aceptarlo: las citas históricas deliberadas (A6, A49) **no** se remapean.

- [ ] **Paso 6: comprobar que el contrato G8 quedó verde**

Ejecutar: `python -m pytest tests/test_guard_declarado_vs_efectivo_s131.py -q`
Esperado: todos en verde. Si sigue rojo, leer qué línea espera y cuál encontró antes de tocar nada:
que una cita no se haya remapeado significa que su bloque **cambió**, y entonces el ancla hay que
revisarla a mano y no moverla.

- [ ] **Paso 7: commit**

```bash
git add tests/test_d25_fondo_vecinos_s142.py CLAUDE.md
git commit -m "S145 D25: guard de S142 por sensor, y citas remapeadas por contenido tras la insercion"
```

---

### Tarea 6: la suite entera y el PR

- [ ] **Paso 1: suite completa**

Ejecutar: `python -m pytest tests/ -q -p no:cacheprovider | tail -1`
Esperado: **la base de la Tarea 0 mas 12**, que son todas las de
`test_d25_fondo_vecinos_v750_s145.py` contando la de punta a punta de la Tarea 4b. El guard de S142
sigue aportando sus 2 instancias parametrizadas, no una mas. Cualquier otro numero exige explicarlo
antes de seguir: un test que cambio de resultado sin que lo tocaramos es una regresion hasta que se
demuestre lo contrario (A50). Cualquier otro
número exige explicarlo antes de seguir: un test que cambió de resultado sin que lo tocáramos es
una regresión hasta que se demuestre lo contrario (A50).

- [ ] **Paso 2: comprobar que el perfil operacional no se movió**

Ejecutar:
```bash
VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; print(p.ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750, p.ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375)"
```
Esperado: `False False`.

- [ ] **Paso 3: anotar D25 en el catálogo**

En `docs/MIROVA_DIVERGENCES.md`, dentro de D25, agregar que existe el flag de M-band, apagado, y el
sustrato medido de §1.2, con la ruta del JSON.

- [ ] **Paso 4: abrir el PR y esperar el CI con conclusión**

```bash
git push -u origin s145-d25-v750
gh pr create --title "S145 D25: fondo por vecinos en VIIRS 750, apagado" --body "Ver docs/superpowers/plans/2026-09-20-d25-fondo-vecinos-viirs750.md"
gh pr checks --watch
```

⚠️ "0 checks" recién abierto el PR es **sin dato**, no verde (A39 enmendada en S142). Esperar el run
con conclusión antes de mergear.

---

## 4. El A/B pre-registrado, que es una decisión aparte

El flag queda apagado. Encenderlo exige este A/B, con su criterio escrito **antes** de correrlo y un
verificador con contexto limpio antes y después (A110, A93).

**Brazos** (perfiles con `data_subdir` aislado, patrón de S143):

| brazo | flag | `max_half_px` |
|---|---|---|
| control | OFF | — |
| A | ON | 1 (sólo los 8 vecinos) |
| B | ON | 3 (hasta 7x7) |

**Ventana**: la misma con que se midió el sustrato, y declarada en el resultado (A90). Contar las
pasadas de cada brazo contra el control **antes** de mirar el veredicto: un run 100 % verde no
prueba cobertura pareja (A108).

**Criterio primario, y es de sobre-publicación, no de recall.** El sustrato ya dice que el recall en
noches no puede subir (0 noches de alerta hoy sin cubrir). Entonces:

1. **Cero pérdidas**: ninguna noche-volcán que hoy publica con alerta de MIROVA puede dejar de
   publicar. Una sola pérdida es NO ADOPTAR.
2. **Sobre-publicación**: la tasa de publicación en **negativos limpios** (pasadas donde MIROVA miró
   y no vio nada) no puede subir más de 2 puntos porcentuales. La línea base sale del mismo script.
3. **Magnitud**: la razón contra MIROVA a igual conteo de píxeles debe quedar en [0,9, 1,1]. Hoy es
   0,995 (A99), así que este criterio es el que más riesgo corre: si el fondo baja, la razón sube.
4. Si 1 y 2 pasan y 3 falla, el veredicto es **NO ADOPTAR con hallazgo**: el paper y la paridad
   empírica se contradicen en este punto, y eso es material para el correo a Coppola
   (`docs/audit_s139/BORRADOR_CORREO_COPPOLA.md`, que ya tiene abierta la pregunta del recorte a
   cero).

**Lo que el A/B no contesta**: si el recorte del exceso negativo a cero es correcto. Ningún texto
del grupo lo menciona; es la mitad abierta de la pregunta 4 del correo y sigue fuera de alcance.

---

## 5. Lo que este plan NO hace, a propósito

- **No enciende nada en producción.** El default es OFF y el perfil operacional lo declara.
- **No toca MODIS.** D25 sigue abierta ahí (mediana del anillo en 6 de 11 Tier A). Es otro sensor,
  otro sustrato y otra decisión: el sustrato de MODIS son 11 pasadas de rescate con 0 alertas de
  MIROVA, así que ni siquiera hay qué medir.
- **No toca el recorte a cero.**
- **No toca la detección.** Los tres sitios son posteriores a que `hot_mask_2d` quede fijado, y eso
  lo fija el test de la Tarea 3.
- **No replica el kernel 3x3 opt-in** de los 5 volcanes del YAML: cuando el flag esté ON, lo pisa,
  igual que en I-band.
