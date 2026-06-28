# AUDIT_S116 — Auditoría integral del proyecto VRP Chile (protocolo A51)

**Fecha:** 2026-06-27 · **Sesión:** S116 · **Última auditoría integral previa:** AUDIT_S105
**Método:** 8 ejes en subagentes paralelos (A26/A51) + verificación adversarial (A62) + síntesis.
**Naturaleza:** READ-ONLY / diagnóstico. Ningún eje implementó fixes. Cada fix que toque
`pipeline/` sale como plan priorizado con A45 + MISSION en su propia sesión.
**Tag defensivo:** `pre-s116-audit` (sha `f7b24733`, pusheado).
**Outputs crudos por eje:** `experiments/_s116_audit/eje{1..8}_*.json`.

---

## 1. Veredicto global

**El sistema operacional está SANO. La deuda es de PROCESO y de TRACKING, no de algoritmo.**

El motor de detección/magnitud, el NRT, el frontend y la ground truth pasaron todas las pruebas
adversariales. Lo que la auditoría sí encontró —y es el motivo por el que A51 manda hacer esto cada
~20 sesiones— es un conjunto de **contradicciones cross-source acumuladas**: cosas que la
documentación afirma de una forma y el código muestra de otra, y decisiones marcadas como "pendientes"
hace 30-90 sesiones que nunca se cerraron. Ninguna rompe la alerta volcánica hoy, pero son exactamente
la clase de drift silencioso que A51 busca cazar antes de que muerda.

| Eje | Tema | Veredicto |
|---|---|---|
| 1 | Fidelidad MISSION / clon literal | con_deuda (algoritmo fiel; 1 deuda media conocida) |
| 2 | Integridad del código del pipeline | **sano** |
| 3 | Integridad de datos / ground truth | con_deuda (datos sanos; housekeeping + 1 loader gap) |
| 4 | Divergencias abiertas + recall por sensor | **sano** |
| 5 | Frontend / display coherence | **sano** |
| 6 | Transparencia / SDA CPLT N°372 | con_deuda (cabeceras FICHA + contradicción de inventario) |
| 7 | Git / operacional / NRT | **sano** (1 gap medio de blindaje) |
| 8 | Backlog / deuda técnica | con_deuda (4 items envejecidos a riesgo) |

**Gatillo A51 (>3 contradicciones cross-source):** se identificaron **3 firmes + 1 borderline**
→ estamos **en el umbral**. Recomendación: **antes de abrir features nuevas, hacer un sprint de
consolidación** que cierre las contradicciones documentadas abajo. No es una emergencia; es higiene.

---

## 2. Lo que está sano (refutaciones adversariales que aguantaron)

Lo más valioso de una auditoría no es la lista de problemas sino confirmar, atacándolo, lo que
funciona. Esto resistió el intento de refutarlo:

- **Detección MODIS fiel a Coppola 2016a (Eje 1).** `git log` del pipeline desde S114 está **vacío**:
  cero cambios al motor desde que S114 lo declaró fiel. Verificado file:line que siguen intactos:
  Tests 2∧3 con rama OR `min(C1, μ+C2·σ)` (`detection_context.py:443-460`), dual-ROI 5σ/10σ
  (`:449-468`), `second_pass_adjacent` excluye activos (`process_modis.py:620/735/749`), ETI
  cuadrático + kernel 8-vec aritmético. **0 anti-patrones nuevos** (los 31 `enable_*:true` pasan
  ≥1 de las 3 preguntas MISSION; vent-path, exclude_zones, bt_path_hot siguen OFF).

- **Suite 775 passed, 0 fallos (Eje 2).** 0 regresiones, 0 funciones con `return` faltante (el patrón
  A49 de `compute_bg_stats` sigue corregido). Guard de coherencia A46 **LIVE** (`store.py:359-365`,
  unidireccional summit→far, test 7/7). Dual-anchor S115 **acotado a display**: producción usa solo
  `get_detection_anchor` para los 3 sensores; `mirova_center` (offset PCC) NO entra a ningún gate.

- **Recall por sensor estable vs S114 (Eje 4, CSV fresco 2026-06-27).** VIIRS375 **98.4%** (era 99.1),
  VIIRS750 **85.0%** (era 85.7), MODIS dashboard **12.5%** pero recall-al-cráter **100%** (el pipeline
  encuentra el cráter en las 24 noches ALERTA MODIS). El descenso es ruido de ventana, no regresión.
  **0 sorpresas, 0 caída silenciosa.** D9 y D11 confirmadas cerradas; A82 intacto (los 1084 far→summit
  son el difuso A69 esperado, no un objeto nuevo).

- **Frontend coherente (Eje 5, preview real 4 vistas).** Paridad S92 L5 OK (filtros cirrus + difuso +
  toggle F5' replicados en index/diario/mosaico). **0 `new Date()` crudo sobre UTC** (el fix S115 de
  diario.html está y no quedó otro). Magnitud unificada (fix S96 vigente). **0 errores de consola.**

- **NRT ~92-98% éxito (Eje 7).** Breaker LANCE (A64) presente y activo (`fetch.py:428-546`). Git limpio
  (solo la raíz en main). MEMORY.md 346 líneas (≤500). CLAUDE.md §Estado es puntero correcto (no quedó
  congelado como en el incidente S105). Cadena de punteros coherente extremo a extremo.

---

## 3. Contradicciones cross-source (gatillo A51)

Estas son el corazón del resultado. Cada una es "una fuente dice X, otra dice no-X", verificada.

| # | Contradicción | Fuente A | Fuente B (verificado) | Estado |
|---|---|---|---|---|
| **C1** | ¿`anchor.py` tiene cabecera FICHA SDA? | CLAUDE.md + backlog S115: "solo anchor.py + vrp_regimes.py la tienen" | Eje 6 + verificación directa: `anchor.py` solo tiene docstring S106 + comentario "Nivel 2" interno; el formato canónico Nivel-1 (caja `════ FICHA SDA ════`) **solo está en `vrp_regimes.py`** | **CONFIRMADA.** El gap de cabeceras es de **5-6 archivos núcleo**, no 4. |
| **C2** | Gates intra-radio S84/S85 (`enable_path_d_intra_radio_gate`, `enable_second_pass_intra_radio_gate`) | Justificación de adopción: "infra-alineación" (MISSION puerta 3 gris) | S86 §C6 + S105 contradicción #1 + Eje 1/Eje 8: el frontend `mirovaEqVrp`/`btn-summit-only` **ya hace** esa supresión → los gates son redundantes (anti-patrón A55). **Siguen ON** (yaml l.188 + l.207), sin decisión | **CONFIRMADA, standing.** Flagged por DOS auditorías seguidas sin cerrar. |
| **C3** | ¿La suite de tests está "sana"? | Narrativa de sesión + Eje 2: "775 passed, suite sana" | Verificación: **16 golden records skipped** (`test_golden_records.py`, razón "obsoletos pre-S27 → regenerar post-S31+", nunca regenerados) + 7 R2 pixel-level skipped por path stale | **CONFIRMADA.** "Verde" enmascara pérdida de cobertura metodológica desde S27 (89 sesiones). |
| **C4** | NEW-8 (filtros pool m,σ §267-273) | MIROVA_DIVERGENCES: divergencia abierta, A/B F2.1 pendiente | Eje 4 + Eje 8: la premisa (D9 cirrus) **se curó** S102-S113 (nadir+focal, mediana 0.53×) → el A/B puede haber quedado obsoleto; la divergencia no se actualizó | Borderline. Premisa cambió, doc no. |

**Conteo: 3 firmes (C1, C2, C3) + 1 borderline (C4) = en el umbral A51.** Recomendación de consolidación
en §5.

---

## 4. Hallazgos por eje (severidad)

### Medios (accionar S116-S117)

- **[C1 — Eje 6] Cabeceras FICHA SDA faltan en 5-6 archivos núcleo** (deuda **legal**, CPLT N°372).
  Participan en la decisión y no tienen Nivel-1: `process_modis.py`, `process_viirs.py`,
  `process_viirs_mod.py`, `store.py`, **`anchor.py`** (contra lo documentado), `detection_context.py`.
  NO la requieren (logística/auditoría, excluidos por Res.372 4.8): `fetch.py`, `scan_geometry.py`,
  `clustering.py`, `audit_metrics.py`, loaders/utils. El contenido propuesto de cada cabecera está en
  `eje6_transparencia.json`. **La ficha publicable v1.0 SÍ está al día** — esto no bloquea publicación,
  es trazabilidad de código. Aplicar = solo comentarios, pero toca pipeline → **A45, sesión dedicada**.

- **[C2 — Eje 1/8] Gates intra-radio S84/S85 ON. INVESTIGADO S116** → ver
  [`AUDIT_S116_C2_GATES.md`](AUDIT_S116_C2_GATES.md) (workflow 4 ángulos read-only). El framing
  "redundante → revertir" se **refina**: (1) **parcialmente** redundante con el frontend (mismo umbral
  espacial, pero el gate cambia el DATO persistido y el frontend solo la VISTA); (2) MISSION: ambos
  anti-patrón; (3) **impacto BIMODAL** — de 4560 records summit-intra preservados, solo 26.7%
  MIROVA-confirmados, pero en focales/desérticos es **cat-b REAL** (Láscar 49%, Lastarria 46% → revertir
  destruiría recall) y en nevados ~puro artefacto A55/A69 (Llaima 0.4%, Villarrica 2%). **NO revertir
  global.** Decisión informada: **diferir** (respeta la orden S105 — atados al frente Test1/fondo-local)
  + **A/B reproc estratificado** cuando ese frente reabra (desenlace probable: gate per-volcán o
  discriminante no-geométrico). El read-only mide lo que el gate PRESERVA, no lo que REMUEVE (exige
  reproc). Toca pipeline → **A45**.

- **[C3 — Eje 2] Golden records S27 + R2 pixel-level skipped (cobertura perdida).**
  16 goldens skipped como "obsoletos post-S31", nunca regenerados (89 sesiones). El protocolo de
  adopción de CLAUDE.md (S33) exige R2 pixel-level vs MIROVA, pero esos 7 tests se skipean por un path
  hardcodeado stale: buscan `C:\Users\nmend\OneDrive\mirova-tif-archive\` cuando el archivo real está en
  `...\Escritorio\claude\Volcanologia\mirova-tif-archive\`. **Fix barato y de alto valor:** corregir el
  path del TIF archive (reactiva R2 local) + decidir si regenerar los goldens contra el pipeline actual
  (suite de regresión metodológica). Toca `tests/` → no es pipeline, pero el de goldens debe pasar por
  TDD.

- **[Eje 7] Gap de blindaje CMR-search (espejo de A64).** La única falla NRT real (Copahue, 26-jun)
  fue timeout 50 min porque `cmr.earthdata.nasa.gov` (host de *búsqueda* de metadata) dio ReadTimeout
  60s repetido en los 8 sensores. El breaker A64 protege el host de *descarga* (ConnectTimeout) pero
  trata ReadTimeout como transient → no cubre el hang de search. Aislado (1/50). Candidato a backlog:
  cap/budget de reintentos CMR-search por sensor (mismo patrón que A64). Toca `fetch.py` → **A45**.

- **[Eje 3] `Distancia_km` del CSV MIROVA nunca se parsea** (`diario.html:202-207`). La única geometría
  de referencia MIROVA queda sin usar. No rompe recall (el cruce es por fecha+sensor) pero es una
  oportunidad de validación de posición desperdiciada. Frontend puro.

### Bajos / housekeeping

- **[Eje 3] `data/_*/` ≈ 757 MB + `experiments/_s1*/` ≈ 223 MB** de A/B y drift históricos untracked.
  Recomendación: archivar bajo tag defensivo (A38). NO borrar sin inventario. Conservar `_s104/_s111/_s114`
  (evidencia de frentes vivos). Mayores a archivar: `_s109_modis_mag` (163 MB), `data/_mirova_literal` (78 MB).
  Los scratch dirs no están en `.gitignore` pese a que hermanos análogos sí → agregarlos.
- **[Eje 3] OCR no consumido por el frontend** (sí por los audits). By design (A11/A54), no bug.
- **[Eje 1] `enable_test1_intermediate_bg` (S112)** es extensión geométrica (anillo [1.5,3]km, no el
  ring global 5-25km literal). Justificado y gateado per-vol, pero conviene etiquetarlo como divergencia
  geométrica explícita en MIROVA_DIVERGENCES.
- **[Eje 5] `comparacion.html`** (preview no-live S115) usa `pc.vrp_mw` crudo sin filtros de display.
  Intencional y badgeada "no es el dashboard live", pero si se promueve debe pasar por `mirovaEqVrpDisplay`
  (trampa S96).
- **[Eje 7] ~120 branches locales + ~90 remotas** ya mergeadas sin podar → `git fetch --prune` + cleanup.
- **[Eje 2] `get_effective_vent` alias DEPRECATED** persiste; producción no lo usa (foot-gun latente,
  mitigado por test + docstring).

### VRP fuera del repo (pedido explícito de Nicolás — Eje 3)

| Item (en `Volcanologia/`) | Tamaño | ¿VRP? | Recomendación |
|---|---|---|---|
| `_s76_experiments_pending/` | 115 MB | Sí (experiments S76 cerrados) | **Archivar** (zip), confirmar con Nicolás |
| `backup-s15-dev-untracked-2026-05-20/` | 32 MB | Sí (backup defensivo S70, tiene tag git + README, TIFs/PNGs con valor R2) | **Conservar** |
| `mirova-tif-archive/` | — | Sí | **NO mover** — sibling intencional (A62/A61); pero corregir el path en los tests R2 (ver C3) |
| `IDEAS_CROSS_SENSOR.md`, `IDEAS_MEJORAS_DASHBOARDS.md` | — | Notas VRP | Integrar a `docs/` o `tasks/backlog_*` del repo |

---

## 5. Plan de consolidación priorizado (propuesto, NO ejecutado)

Dado que estamos en el umbral A51, el orden recomendado es **cerrar contradicciones antes que features**.
Cada item con pipeline lleva A45 (tag + OK Nicolás) en su propia sesión.

**Prioridad 1 — Cerrar las contradicciones de tracking (baratas, sin riesgo algorítmico):**
1. **C3 — Reactivar R2 + decidir goldens.** Corregir el path del TIF archive en `tests/test_r2_pixel_level.py`
   (1 línea) + correr R2 local + decidir regenerar goldens S27 contra el pipeline actual. Recupera el
   protocolo de adopción S33. *(tests/, TDD).*
2. **C1 — Cabeceras FICHA SDA en los 6 núcleo.** Solo comentarios; contenido ya propuesto en
   `eje6_transparencia.json`. Cierra deuda legal CPLT N°372. *(pipeline → A45, sesión dedicada).*
   Corregir además CLAUDE.md + backlog: anchor.py NO la tenía.
3. **Corregir la doc** que disparó C1 (CLAUDE.md S115 / backlog) y actualizar MIROVA_DIVERGENCES con el
   estado real de NEW-8 (C4: premisa D9 curada → ¿obsoleto?). *(docs).*

**Prioridad 2 — Decisión pendiente de Nicolás (C2):**
4. **Gates intra-radio S84/S85.** ✅ **INVESTIGADO S116** ([`AUDIT_S116_C2_GATES.md`](AUDIT_S116_C2_GATES.md)):
   NO revertir (impacto bimodal — destruiría cat-b real en focales) + respetar orden S105. La decisión
   pasó de "standing sin decisión" a "diferir con razón + A/B reproc estratificado cuando reabra el
   frente Test1/fondo-local". *(pipeline → A45 + MISSION, en ese frente).*

**Prioridad 3 — Robustez operacional + housekeeping (sin urgencia):**
5. Blindaje CMR-search (espejo A64) en `fetch.py`. *(pipeline → A45).*
6. Archivar `data/_*/` + `_s76_experiments_pending/` bajo tag (A38) + `.gitignore` scratch dirs + podar branches.
7. `Distancia_km` en diario.html (validación de posición). *(frontend).*

**Lo que NO se toca (anti-A8 / decisión Nicolás):**
- far→summit MODIS / D11 (A82, irreducible, cerrado S114).
- inner_radius PCC 20→10 (rechazado S115).
- Parte C Test1-lowmag NdC → es trabajo de Landsat-v1/NHI-v1 (A77, instrumento equivocado), no VRP Chile.

---

## 6. Verificación adversarial de la propia auditoría (A62/A48)

Para no incluir falsos positivos de auditoría (lección A48/A55), verifiqué directamente las dos
contradicciones más consecuentes en vez de confiar en la etiqueta del subagente:
- **C1 (anchor.py):** `head -25 pipeline/anchor.py` → confirmado, solo docstring + comentario Nivel-2;
  la caja Nivel-1 solo existe en `vrp_regimes.py`. El subagente del Eje 6 tenía razón (y corrigió un
  claim erróneo del Eje 1, que había heredado la afirmación de CLAUDE.md sin verificar).
- **C3 (goldens):** `pytest -rs` → confirmado, 16 goldens skipped "obsoletos pre-S27" + 7 R2 por path stale.

Las demás conclusiones "sano" provienen de refutaciones adversariales que los propios ejes intentaron
y no lograron (recall por vol, paridad de vistas en preview, suite cross-source vs origin/main).

---

## 7. Cierre

VRP Chile cumple su misión: clon literal MIROVA, detección fiel, NRT vivo, dashboard coherente, recall
estable. El gap real respecto de MIROVA sigue siendo artefacto metodológico (A54/A82), no bug. Lo que
esta auditoría aporta es la **lista de deuda de tracking** que se acumuló desde S105 y que conviene
saldar antes de abrir frente nuevo: 6 cabeceras de transparencia, la decisión de los gates intra-radio,
y la suite de regresión metodológica (goldens + R2). Ninguna es urgente operacionalmente; todas son la
clase de cosa que A51 existe para no dejar pudrir.
</content>
</invoke>
