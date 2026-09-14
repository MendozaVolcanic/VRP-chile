# Fase 0 del plan de paridad S139: el instrumento. Plan de ejecución

> **Para quien ejecute:** usar `executing-plans` o `subagent-driven-development`, una tarea por vez,
> con checkpoint entre tareas. Cada paso lleva casilla. Spec aprobada por Nicolás el 2026-09-14:
> `docs/superpowers/specs/2026-09-13-plan-definitivo-paridad-design.md` (§2, §3, §7.5).

**Objetivo:** dejar un banco de prueba congelado con positivos y negativos por pasada, la
descomposición de magnitud contra el OSF, una línea base con sha, y el auto-audit midiendo falsas
publicaciones; más las cuatro correcciones chicas que la spec agrega a la Fase 0. **Nada de esto
cambia una decisión del pipeline.**

**Arquitectura:** dos scripts nuevos en `scripts/` promovidos desde `experiments/_s139_audit/`
(banco y descomposición), con tests que fijan los controles de instrumento medidos en S139; el
auto-audit semanal consume el banco. Las correcciones de loader, store y NRT son cambios de pocas
líneas, cada uno con su test. Todo lo que toque `pipeline/`, `store.py` o `nrt.yml` va con tag
defensivo y confirmación explícita de Nicolás antes de mergear (A45).

**Reglas fijas:** predicado del dashboard ejecutado desde `frontend/index.html` con node y sha
fijado; unidad pasada y noche de volcán, siempre por volcán (S126); ventana desde 2026-03-01;
negativo limpio por gránule; FALSO_POSITIVO = sin información para el cráter; sin guiones largos;
`PYTHONIOENCODING=utf-8`; un commit por tarea; español de Chile.

---

## Orden y dependencias

| # | tarea | toca pipeline | depende de |
|---|---|---|---|
| 1 | Loader OCR: distancia con mojibake | no (`pipeline/mirova_csv_loader.py` es lector, no detección; igual tag) | nada |
| 2 | Referencia unificada (snapshot + respaldo abril + OCR) | no | 1 |
| 3 | `scripts/banco_paridad.py` + tests | no | 2 |
| 4 | `scripts/descomponer_magnitud_osf.py` + tests | no | nada |
| 5 | Línea base congelada | no | 3, 4 |
| 6 | Auto-audit semanal: falsas publicaciones y factor de conteo | no | 3, 4 |
| 7 | Radiancia de fondo persistida | **sí** (`store.py`, `process_*.py`) | nada |
| 8 | NRT: perfil experimental, detector de producto, aviso de token, A64 visible | **sí** (`nrt.yml`, `fetch.py`) | nada |
| 9 | Docs: A95, cita fabricada, catálogo D20, README de artefactos | no | nada |

Las tareas 4, 7, 8 y 9 son independientes entre sí y de 1 a 3; pueden ir en paralelo en worktrees
distintos (A44). Cada PR chico, cap 12 por sesión (A53).

---

### Tarea 1: el loader recupera la distancia del OCR con notas en mojibake

**Archivos:** modificar `pipeline/mirova_csv_loader.py:91` (`_OCR_DIST_RE`); test nuevo
`tests/test_mirova_csv_loader_mojibake_s139.py`.

- [ ] **Paso 1: test que falla**

```python
# -*- coding: utf-8 -*-
"""S139: 578 de 846 ALERTA_TERMICA_OCR quedaban sin distancia porque el commit ffc7a97d8b de
Mirova-v1 (2026-06-12) reescribio las notas con codificacion doble: 'dist≈3.33 km' quedo como
'distâ‰ˆ3.33 km'. El regex del loader no lo reconocia y la alerta perdia su posicion."""
import csv, os
from pipeline.mirova_csv_loader import parse_ocr_distance

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OCR = os.path.join(ROOT, "data", "mirova_reference", "mirova_v1_snapshot", "registro_vrp_ocr.csv")


def test_mojibake_verbatim():
    assert parse_ocr_distance("Estrella en Y=283 (dentro lÃ\xadmite Y=257, distâ‰ˆ3.33 km)") == 3.33


def test_formatos_previos_siguen():
    assert parse_ocr_distance("Grupo píxeles rojos (área=50 px², dist≈12.94 km)") == 12.94
    assert parse_ocr_distance("validado -> 2.5 km") == 2.5
    assert parse_ocr_distance("sin distancia") is None


def test_alertas_ocr_reales_con_distancia():
    """Control de instrumento: sobre el CSV real, la fraccion sin distancia baja de 68 % a menos de 5 %."""
    rows = [r for r in csv.DictReader(open(OCR, encoding="utf-8")) if r["Tipo_Registro"] == "ALERTA_TERMICA_OCR"]
    assert len(rows) > 500
    sin = [r for r in rows if parse_ocr_distance(r.get("Nota_Validacion", "")) is None]
    assert len(sin) / len(rows) < 0.05, f"{len(sin)} de {len(rows)} sin distancia"
```

- [ ] **Paso 2: correr y ver el rojo**

`python -m pytest tests/test_mirova_csv_loader_mojibake_s139.py -q` → esperado: 2 fallan
(`test_mojibake_verbatim`, `test_alertas_ocr_reales_con_distancia`).

- [ ] **Paso 3: cambio mínimo** en `pipeline/mirova_csv_loader.py:91`:

```python
# S139: las notas del OCR anteriores al 2026-06-13 estan en codificacion doble desde el commit
# ffc7a97d8b de Mirova-v1 ('≈' aparece como 'â‰ˆ'). Se acepta esa forma ademas de las reales.
_OCR_DIST_RE = re.compile(r"(?:dist(?:[≈~=]|â‰ˆ)|->|→)\s*(\d+\.?\d*)\s*km")
```

- [ ] **Paso 4: verde** `python -m pytest tests/test_mirova_csv_loader_mojibake_s139.py -q` → 3 passed.
- [ ] **Paso 5: suite completa** `python -m pytest tests/ -q -p no:cacheprovider | tail -1` → ningún rojo nuevo.
- [ ] **Paso 6: commit** `fix(loader): distancia OCR con notas en mojibake (578 alertas recuperan posicion)`.

---

### Tarea 2: referencia unificada

**Archivos:** crear `scripts/referencia_mirova_unificada.py`; crear
`data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado_respaldo_20260408.csv` (copia de
`C:\Users\nmend\OneDrive\Escritorio\claude\Automatizacion web\Automatizacion web\Mirova-v1\monitoreo_satelital\registro_vrp_consolidado al 08042026.csv`,
11.319 filas; `git add -f` porque `*.csv` está ignorado, con línea en `.gitignore` diciendo por qué);
test `tests/test_referencia_unificada_s139.py`.

- [ ] **Paso 1: test que falla**

```python
import os
from scripts.referencia_mirova_unificada import cargar_referencia_unificada

def test_recupera_las_alertas_perdidas():
    ref = cargar_referencia_unificada()
    claves = {(a["volcano"], a["sensor_bucket"], a["fecha_utc"][:16]) for a in ref}
    # Alerta que el remoto perdio el 23-abr (verificado S139 contra el respaldo del 8-abr)
    assert ("Lascar", "MODIS", "2026-03-04 07:15") in claves
    # Sin duplicados por (volcan, sensor, fecha, fuente)
    assert len(claves) == len({(a["volcano"], a["sensor_bucket"], a["fecha_utc"][:16], a["source"]) for a in ref})
```

- [ ] **Paso 2: rojo** (el módulo no existe).
- [ ] **Paso 3: implementar** `cargar_referencia_unificada()`: llama a
`pipeline.mirova_csv_loader.load_mirova_alertas` dos veces (snapshot actual + respaldo de abril,
mismo `ocr_path`) y une por clave `(volcano, sensor_bucket, fecha_utc, source)`; conserva la fila del
snapshot actual cuando las dos existen. Devuelve la lista con el mismo esquema que el loader.
- [ ] **Paso 4: verde**, suite, commit `feat(referencia): union snapshot + respaldo 8-abr + OCR`.

---

### Tarea 3: `scripts/banco_paridad.py`

**Archivos:** crear `scripts/banco_paridad.py` promoviendo de
`experiments/_s139_audit/eje2/banco_noches.py` (funciones `bucket`, `inner_desde_html`,
`correr_node`, `control_identidad_predicado`, `cargar_referencia`, `cargar_nuestros`, `armar`,
`etiqueta`, `evaluar`, `agregar`) y de `experiments/_s139_audit/verificador/v1_negativo_por_pasada.py`
(`publica`, `parear` con tolerancia ±2 min, `zbin`); test `tests/test_banco_paridad_s139.py`. **No
modificar los scripts de `experiments/`**: son el registro histórico.

Cambios respecto de los scripts de origen (todos de la spec §7.5):
1. referencia = `cargar_referencia_unificada()` (tarea 2), no el snapshot solo;
2. ventana por defecto `2026-03-01` a hoy; enero y febrero quedan como `sin_info`;
3. etiquetas por pasada: `pos` (ALERTA cons u OCR nocturna), `neg_limpio` (gránulo MIROVA con VRP 0,
   nocturno, sin ALERTA ni FALSO_POSITIVO en esa noche y sensor, record nuestro a ±2 min),
   `far_ref` (FALSO_POSITIVO: sin información para el cráter, control para nuestras `far`),
   `sin_info` (resto);
4. el predicado del dashboard se extrae de `frontend/index.html` con node y el script escribe en su
   salida el sha de ese archivo (`git hash-object frontend/index.html`);
5. salida JSON con, por sensor y por volcán, en pasada y en noche de volcán: recall en `pos`, tasa de
   publicación en `neg_limpio`, n, ventana, sha; más los dos controles (etiquetas barajadas y oráculo);
6. **métrica `far_ref`** (pedido de Nicolás, 2026-09-14): de las pasadas FALSO_POSITIVO nocturnas
   (VRP > 0 publicado por MIROVA a más de `limite_km` del volcán), fracción en que tenemos un record a
   ±2 min con `distance_class == "far"` y cúmulo con `vrp_mw > 0`, y fracción en que
   `|centroid_dist_km - Distancia_km| <= 2` (diferencia de radios, no posición: A93). Reportar n por
   sensor (MODIS tiene sólo ~10 nocturnas; el grueso es VIIRS 375). Si no vemos el foco lejano que
   MIROVA vio, es una pérdida real (incendio o foco excéntrico), no un acierto. Aparte, contar las
   noches en que el cráter tiene alerta en otra pasada y esta pasada quedó FALSO_POSITIVO: es el
   volumen de "cráter tapado por un foco lejano" en el propio MIROVA.

- [ ] **Paso 1: test que falla**

```python
import json, subprocess, sys, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def _correr(tmp_path):
    out = tmp_path / "banco.json"
    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "banco_paridad.py"), "--out", str(out)],
                       capture_output=True, text=True, timeout=600, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    assert r.returncode == 0, r.stderr[-800:]
    return json.load(open(out, encoding="utf-8"))

def test_controles_de_instrumento(tmp_path):
    b = _correr(tmp_path)
    assert b["meta"]["ventana"][0] == "2026-03-01"
    assert len(b["meta"]["sha_index_html"]) == 40
    # el predicado extraido reproduce los casos del guard S139
    assert b["controles"]["identidad_predicado"] is True
    # barajar etiquetas destruye la separacion: AUC por volcan en [0.4, 0.6]
    for v, a in b["controles"]["auc_barajado_por_volcan"].items():
        assert 0.4 <= a <= 0.6, (v, a)

def test_linea_base_reproduce_s139(tmp_path):
    """Numeros medidos en S139 (VERIFICADOR.md): con la referencia solo-snapshot el V375 publicaba en
    63,5 % de los negativos limpios por pasada. Con la referencia unificada y ventana desde marzo el
    valor puede moverse unos puntos, no de orden: se fija una banda."""
    b = _correr(tmp_path)
    v375 = b["por_sensor"]["VIIRS375"]["pasada"]
    assert v375["n_neg_limpio"] > 1000
    assert 0.50 <= v375["tasa_pub_neg"] <= 0.75
    assert b["por_sensor"]["VIIRS375"]["noche_volcan"]["recall_pos"] > 0.95
```

- [ ] **Paso 2: rojo.** **Paso 3: implementar** copiando las funciones nombradas (mismo cuerpo, sin
reescribir la lógica) y aplicando los 5 cambios. **Paso 4: verde**, en menos de 5 min.
**Paso 5: commit** `feat(banco): banco de paridad por pasada con negativos (S139 F0)`.

---

### Tarea 4: `scripts/descomponer_magnitud_osf.py`

**Archivos:** crear el script promoviendo de `experiments/_s139_audit/magnitud/02_descomposicion_pares.py`
(`planck`, `res`, `crater`, `nearest`, `core_pixels`, `build`, `gm`, `table`) y `04_fondo_y_test1.py`;
test `tests/test_descomponer_magnitud_s139.py`. Entrada: OSF (`data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv`,
si no está el test se salta con `pytest.skip`). Salida JSON por sensor, volcán y bin de cenit:
`n`, `R`, `Fn`, `Fhot`, `Fbg`, `Npix_med`, `pub_n_med`.

- [ ] **Paso 1: test que falla**

```python
import json, os, subprocess, sys, pytest
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OSF = os.path.join(ROOT, "data", "mirova_reference", "VRP_GLOBAL_ARCHIVE_2025.csv")

@pytest.mark.skipif(not os.path.exists(OSF), reason="OSF no descargado")
def test_reproduce_descomposicion_s139(tmp_path):
    out = tmp_path / "mag.json"
    r = subprocess.run([sys.executable, os.path.join(ROOT, "scripts", "descomponer_magnitud_osf.py"), "--out", str(out)],
                       capture_output=True, text=True, timeout=900, env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    assert r.returncode == 0, r.stderr[-800:]
    m = json.load(open(out, encoding="utf-8"))
    t = m["VIIRS375"]["total"]
    # medido S139 (MAGNITUD_DESCOMPOSICION_OSF.md), corpus 2025 fijo: no debe moverse
    assert t["n"] == 1499
    assert abs(t["R_gm"] - 0.659) < 0.01 and abs(t["Fn_gm"] - 0.553) < 0.01
    assert abs(m["VIIRS375"]["igual_conteo"]["R"] - 0.995) < 0.01
    # control negativo: pareo desplazado 6 h da 0 pares
    assert m["controles"]["pares_desplazados_6h"] == 0
```

- [ ] **Pasos 2 a 5** como en la tarea 3. Commit `feat(magnitud): descomposicion contra OSF (S139 F0)`.

---

### Tarea 5: línea base congelada

**Archivos:** crear `data/audit_continuous/linea_base_s139/banco.json` y `magnitud.json` (salidas
de las tareas 3 y 4 sobre `main`), más `README.md` con sha de `main`, sha de `index.html`, fecha
del servidor (`gh api repos/MendozaVolcanic/VRP-chile -i | grep -i ^date`) y el comando exacto.

- [ ] Correr los dos scripts, guardar, escribir el README, commit `data(linea-base): banco y magnitud S139 congelados`.

---

### Tarea 6: auto-audit semanal mide falsas publicaciones

**Archivos:** modificar `scripts/auto_audit_weekly.py` (después de la l. 283, donde arma `recall`);
modificar `tests/test_audit_metrics.py` o crear `tests/test_auto_audit_falsas_s139.py`.

- [ ] **Paso 1: test** que, con un JSON sintético de 4 records (2 en pasadas `neg_limpio`, 1 publicada),
el resumen trae `falsas_pub_pct` = 50,0 para ese sensor y el flag
`"falsas VIIRS375 50.0% > banda 10%"` cuando supera la banda.
- [ ] **Paso 2: rojo.** **Paso 3:** importar `evaluar` de `scripts.banco_paridad` y agregar al dict
de salida `falsas_pub` por sensor (pasada, ventana rodante de 60 días) y `factor_conteo` (de la tarea
4 cuando el OSF está; si no, `null`); bandas de la spec §2 revisada: `FALSAS_MAX = {"VIIRS375": 10.0,
"VIIRS750": 10.0, "MODIS": 10.0}` en focales, 15 en nevados, con la partición de S131
(`scripts/build_c2ab_windows.py:41-42`). **Paso 4: verde.** **Paso 5: commit**.

---

### Tarea 7: radiancia de fondo persistida (toca pipeline: tag + confirmación)

**Archivos:** modificar `pipeline/process_viirs.py:2095`, `pipeline/process_modis.py:1508`,
`pipeline/process_viirs_mod.py:1356` (el dict del record, junto a `"t_bg_k"`); `pipeline/store.py`
no cambia si no valida esquema; test `tests/test_store_l_bg_persistido_s139.py`.

- [ ] **Paso 0:** `git tag pre-s139-f0-lbg-persistido && git push origin pre-s139-f0-lbg-persistido`;
pedir confirmación a Nicolás antes del primer edit.
- [ ] **Paso 1: test** que procesa un granule sintético (patrón de `tests/test_f5_core_python_s132.py`
para armar records) y verifica que el record trae `diag_L_bg_w_m2_sr_um` (float > 0, igual a Planck
de `t_bg_k` en la banda del sensor con tolerancia 1e-6) y `diag_n_suitable` (int ≥ 0); y que **ningún
otro campo cambia** contra el record de referencia (comparar dict sin esas dos claves).
- [ ] **Paso 3:** en los tres procesadores, junto a `"t_bg_k"`: `"diag_L_bg_w_m2_sr_um": round(float(L_bg_global), 6)`
(la variable ya existe: `L_bg_global` en `process_modis.py:1023`; el equivalente en VIIRS es el que
alimenta `delta_L`; trazar el nombre en cada archivo, A89) y `"diag_n_suitable": int(n_bg)` (el `n_bg`
de `compute_bg_stats`). Cuando el kernel local actúa, además `"diag_L_bg_local_w_m2_sr_um"` con la
mediana de `L_bg` por píxel del cúmulo.
- [ ] **Paso 4: verde**, suite completa, guards de citas `file:line` (`tests/test_guard_declarado_vs_efectivo_s131.py`)
actualizados si se corrieron líneas. **Paso 5: commit**; PR con confirmación de Nicolás.

---

### Tarea 8: NRT (toca `nrt.yml` y `fetch.py`: tag + confirmación)

Cuatro PR chicos, cada uno con su verificación:

- [ ] **8a. Perfil experimental.** Decidir con Nicolás: (i) quitar el paso de `nrt.yml:192-215` del cron, o
(ii) commitear `data/experimental_v2/` en `nrt.yml:330`. Recomendación: (i), porque nadie consume
ese perfil y ahorra ~la mitad del reloj del job. Verificación: el siguiente run del cron dura menos
y `gh run view --json jobs` no muestra el paso.
- [ ] **8b. Detector de producto.** Reemplazar en `process_modis.py:1546`, `process_viirs.py:2100`,
`process_viirs_mod.py:1391` la expresión `"nrt" if "_NRT" in ... else "standard"` por
`product_version_from_granule(<nombre>)` (importado de `pipeline.fetch`). Test: nombre MODIS con
`.NRT.` → `"nrt"`; VIIRS con `_NRT` → `"nrt"`; estándar → `"standard"`.
- [ ] **8c. Aviso de token.** En `nrt-healthcheck.yml` agregar un paso que lea
`gh api repos/MendozaVolcanic/VRP-chile/actions/secrets/EARTHDATA_TOKEN --jq .updated_at` y abra
issue si pasaron más de 50 días. Test: script `scripts/token_edad.py` con test unitario sobre fechas.
- [ ] **8d. A64 visible.** En `fetch.py:824` (donde el host caído pasa a WARN), escribir además una
línea `::warning::` de GitHub Actions y un contador en el resumen del job (`$GITHUB_STEP_SUMMARY`).
- [ ] Tag `pre-s139-f0-nrt` antes de 8a y 8b; confirmación de Nicolás; commits separados.

---

### Tarea 9: documentación

- [ ] **A95** en `CLAUDE.md:1152`: cambiar "los operadores" por "los operadores y símbolos (`>` sale
como punto, `=` como `¼`, μ/σ como m/s)"; cita `docs/audit_s139/LECTURA_PDF_TABLAS_FIGURAS.md`.
- [ ] **Cita fabricada** `docs/MIROVA_DETAILED_CITATIONS.md:214-216`: reemplazar por "El paper no
escribe la ecuación del ETI. La Fig. 3 (p. 7) lo rotula `ETI = NTI - NTIbk` y la Fig. 4 (p. 8)
`ETI = NTI - NTIapp`; la ecuación (5) impresa es `NTIbk = aNTIapp² + bNTIapp + c`. Verificado S139
renderizando las páginas." Correr `tests/test_guard_declarado_vs_efectivo_s131.py`.
- [ ] **Catálogo**: nota en D20 (MODIS TIR banda 31 en Fernandina 2025, SOSPECHA del agente hasta
verificar la página) y en D17/D25 la cita de Fernandina p. 9 (verificada).
- [ ] **`experiments/_artefactos_ab/README.md`** (fuera de git por `.gitignore`; el README sí, con
`git add -f`): qué hay, de qué runs, y que se regeneran sólo reprocesando.
- [ ] Commit `docs: A95 ampliada, cita del ETI corregida, catalogo D17/D20/D25`.

---

## Autoevaluación del plan contra la spec

- §3.1 banco → tareas 2, 3. §3.2 magnitud → 4. §3.3 línea base → 5. §3.4 auto-audit → 6.
- §7.4 radiancia → 7. §7.3 NRT → 8. §7.5 loader OCR, A95, cita → 1 y 9. §7.5 correo a Coppola: lo
envía Nicolás, fuera del plan. Renovar token Earthdata: Nicolás, fuera del plan.
- Nombres consistentes: `cargar_referencia_unificada` (2 y 3), `scripts/banco_paridad.py` (3, 6),
`diag_L_bg_w_m2_sr_um` y `diag_n_suitable` (7), `product_version_from_granule` (8b, ya existe en `fetch.py:367`).
- Sin placeholders: las bandas numéricas de la tarea 6 salen de la spec §7.5; los números de los
tests de 3 y 4 salen de las mediciones de S139 y son el control de que el instrumento no cambió.
