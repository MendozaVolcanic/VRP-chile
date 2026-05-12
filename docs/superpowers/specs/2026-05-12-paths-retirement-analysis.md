# Análisis paths viejos — qué retirar si H_D8_5 valida (S37/S38)

**Status**: análisis preparatorio para Bloque F del handoff S38. NO implementar
hasta que A/B H_D8_5 muestre que el algoritmo del paper produce recall y
ratio aceptables.

**Driver**: clon literal MIROVA implica que solo deberíamos correr los paths
documentados en Coppola 2015 + 2016a. Los paths "nuestros" (Path C dNTI
relativo, etc.) sobreviven por inercia pre-S37 y pueden estar contribuyendo
ruido o redundancia.

---

## Mapa actual de paths (post-S37)

En cada procesador (`process_modis.py`, `process_viirs.py`, `process_viirs_mod.py`)
los paths se OR'an antes de aplicar filtros finales:

```python
hot_mask_2d = (bt_path_hot
               | nti_path_hot
               | dnti_ctx_hot
               | test1_hot
               | eti_path_hot)        # ← S37 H_D8_5 nuevo
```

(Y `nti_rel_hot` en VIIRS si `ENABLE_NTI_RELATIVE_PATH=true`, OFF por
default).

---

## Tabla de decisión

| Path | Coppola 2015/2016a? | Quien lo activa hoy | H_D8_5 lo cubre? | Acción S38 |
|---|---|---|---|---|
| `bt_path_hot` | NO en 2016a (single-pixel BT > floor + N·σ) | `enable_eruption_path` (ON default) | **Sí** — el path ETI cuadrático opera sobre dNTI/dETI scene-wide. Cualquier pixel con BT alto suficiente desviará la regresión y disparará Tests 2 ∧ 3. | **Retirar** si H_D8_5 valida. Path BT es heredado pre-papers MIROVA. |
| `nti_path_hot` | **SÍ** — Coppola 2015 Test 1 single-pixel K1=-0.8 noche / -0.6 día | `enable_eruption_path` | **NO redundante** — Tests 2/3 son contextuales (dNTI vs μ+C2σ); el test K1 es absoluto y captura señales que pasan el threshold absoluto pero no destacan localmente (raro pero documentado en paper Tabla 1). | **Mantener**. Es uno de los Tests 1 del paper. |
| `nti_rel_hot` | NO — Path C nuestro (S11), nti > nti_bg + 3σ_nti | `enable_nti_relative_path` (default OFF) | Sí — equivalente débil a Test 2 sin Test 3 conjunción. | **Retirar** del código entero (ya OFF default, sin papers, sin uso reportado). |
| `dnti_ctx_hot` | Sí pero solo parcialmente — paper menciona dNTI 8-vecinos pero requiere conjunción con dETI (Test 3). Nuestra implementación NO incluye dETI. | `enable_dnti_contextual_path` (ON default) | **Sí — H_D8_5 first-pass es exactamente este path pero CON dETI conjunción**. La conjunción Tests 2 ∧ 3 es lo que el paper exige. | **Retirar**. Cubierto por `eti_path_hot` first-pass. |
| `test1_hot` | **SÍ** — Coppola 2015 §2.2 Eq.1 integrated-ROI (suma de exceso sobre ROI summit). Diferente concepto de Tests 2/3 per-pixel. | `enable_test1_path` (ON default) | NO — Test 1 integrated-ROI opera sobre ROI agregado (suma de pixels), no per-pixel. Es ortogonal. | **Mantener**. Captura señales sub-pixel espacialmente difusas (Villarrica lava lake). |
| `eti_path_hot` | **SÍ** — Coppola 2016a SP 426.5 algoritmo completo Tests 2 ∧ 3 + second-pass + ETI cuadrático scene-wide | `enable_eti_quadratic_scene` (S37) | — (es la palanca H_D8_5) | **Mantener** (core H_D8_5). |

---

## Resultado esperado post-cleanup

Si H_D8_5 valida en A/B, el operacional debería ser:

```python
hot_mask_2d = (nti_path_hot       # Test 1 K1 single-pixel (Coppola 2015 Tabla 1)
               | test1_hot         # Test 1 integrated-ROI (Coppola 2015 §2.2 Eq.1)
               | eti_path_hot)     # Tests 2 ∧ 3 contextuales + second-pass (Coppola 2016a)
```

Tres paths, todos en papers MIROVA core. Ninguno parche ad-hoc.

**Eliminados** (todos pre-papers MIROVA o redundantes):
- `bt_path_hot` (heredado pre-S15, BT puro)
- `nti_rel_hot` (Path C S11, nuestro)
- `dnti_ctx_hot` (S15 P3.2, redundante con H_D8_5 first-pass)

---

## Por qué NO implementar en S37

Riesgos sin A/B validation:

1. **Pérdida de recall sin saber por qué**: si removemos `bt_path_hot` y H_D8_5
   no captura señal X que sí capturaba bt_path_hot, baja recall sin
   diagnóstico claro.
2. **Paths viejos pueden ser load-bearing**: en casos no del paper (Villarrica
   sub-pixel, Tupungatito glaciar), los paths viejos pueden estar rescatando
   signals que H_D8_5 paper-puro no captura.
3. **R5 brainstorming requerido**: cambio metodológico operacional grande,
   regla CLAUDE.md.

---

## Plan S38 (gated por A/B success)

1. **Si A/B H_D8_5 valida** (recall ≥ disabled, ratio mejorado, D8 cases bajan):
   - Activar 3 flags H_D8_5 en `mirova_equivalent.yaml` (Bloque D handoff).
   - Reproc 7 días Tier A con flags ON + paths viejos AÚN ON.
   - Verificar producción de dashboards (R8).
2. **S39+ — cleanup paths viejos** (Bloque F):
   - Brainstorming formal con Nicolás antes de remover.
   - A/B incremental: comparar `H_D8_5_only` (sin paths viejos) vs `H_D8_5_with_paths`.
     Si recall no baja >2pp → safe para retirar paths viejos.
   - Si A/B muestra paths viejos load-bearing → mantener y documentar por qué.

---

## Cómo medir contribución de cada path al recall

Idea para A/B incremental S39+:

Agregar flag `enable_only_h_d8_5_paths` que cuando ON, salta `bt_path_hot |
dnti_ctx_hot | nti_rel_hot` en el OR final. Solo deja
`nti_path_hot | test1_hot | eti_path_hot`. Comparar contra baseline que sí
los suma.

Pseudocódigo:
```python
if ENABLE_ONLY_H_D8_5_PATHS:
    hot_mask_2d = nti_path_hot | test1_hot | eti_path_hot
else:
    hot_mask_2d = (bt_path_hot | nti_path_hot | nti_rel_hot
                   | dnti_ctx_hot | test1_hot | eti_path_hot)
```

Por cada record con sum_active > 0:
- ¿Sin paths viejos sigue detectando? → safe retirar
- ¿Pierde detección? → identificar qué path viejo lo levantaba y por qué
  no lo levanta H_D8_5

---

## Tracking referencias

Implementación: pendiente S38+ post-A/B + brainstorming.
Test plan: A/B incremental, R2 pixel-level vs mirova-tif-archive como antes.
Documentación clon literal final: actualizar `docs/MIROVA_DIVERGENCES.md`
si retirar paths viejos cierra D1-D8.
