# Design — Acercar VRP Chile a MIROVA: tratamiento POR SENSOR

**Sesión S93 (2026-05-30).** Brainstorming + systematic-debugging. Diagnóstico:
`docs/AUDIT_S93_artefactos_sobreestimacion.md`. Datos: `experiments/_s93_audit/`.
**Estado: DISEÑO. NO implementado. Implementación = sesión(es) con tag + OK + TDD + reproc + R2 (A45).**

## 1. Objetivo (criterio de Nicolás, verificable)

Replicar el comportamiento de MIROVA, que **reporta cada satélite por separado**:
1. NO reporta artefactos de campo frío (path D sobre nieve/cirrus/glaciar).
2. SÍ reporta toda anomalía volcánica real, por débil que sea.
3. Si en la misma pasada hay un incendio u otro artefacto más fuerte, reporta el dominante.
4. **Cada sensor (MODIS / VIIRS375 / VIIRS750) es una serie independiente.**

## 2. Diagnóstico raíz (confirmado con datos)

El VRP de Wooster (MIR) ∝ ΔL = L(píxel) − L(fondo); asume fondo=terreno normal, píxel=lava.
Sobre fondo gélido (nieve/cirrus, −10 a −32 °C), el path D contextual (c1=0.003) marca
terreno normal apenas sobre cero y Wooster lee el contraste nieve↔terreno como fondo↔lava →
sobre-estima 20–200×. Suma de cientos de píxeles débiles (`clustering.py:113`).

**Hallazgo decisivo — NO se puede apagar el path D global**: el 93% de las anomalías reales
confirmadas por MIROVA son contextual-puras (igual que los artefactos), porque las señales
volcánicas chilenas actuales son débiles/sub-píxel. Apagarlo mataría el recall. La distinción
artefacto/real NO está en el detector — está **por sensor**:

| Sensor | Precisión nuestra | MIROVA (CSV) | Lectura |
|---|---|---|---|
| MODIS | 2.6% (74 TP / 2796) | 80 alertas (77 Lascar) | ciego a lo débil; lo grande contextual = artefacto |
| VIIRS 375m | 38% (1550 TP) | 787 alertas | **fuente real**, ratio 1.9× |
| VIIRS 750m | 0% (0 TP / 2838) | **0 alertas** | MIROVA no lo usa |

## 3. Diseño POR SENSOR

### 3.1 MODIS — co-validación (solo reporta con foco "duro")
- **Qué**: MODIS reporta un cluster solo si la pasada tiene ≥1 píxel con señal térmica dura
  (BT-path o NTI-path absoluto). Si solo dispara el path D contextual sobre campo frío → no
  reporta (hot_mask MODIS = 0). Replica MIROVA MODIS (solo publica lo grande, 77/80 = Lascar).
- **Mecanismo**: flag `path_d_requires_covalidation` existe (`profile.py:451`, `process_modis.py:771`)
  pero es global. **Hace falta granularidad por sensor**: activarlo SOLO en MODIS
  (`process_modis.py`), NO en VIIRS375. Diseño: `path_d_requires_covalidation_modis: true`
  (nuevo flag por-sensor) o gating del existente al procesador MODIS.
- **Seguridad recall**: los 74 TP MODIS están 100% cubiertos por VIIRS375 el mismo día
  (0 únicos) → recall por evento intacto. Cuando haya erupción real grande / incendio, MODIS
  tendrá foco duro → SÍ reporta (cumple criterio 3).
- **Verificación obligatoria**: reproc local + confirmar 0 pérdida de eventos-noche vs baseline.

### 3.2 VIIRS 750m — no reportar en el perfil operacional
- **Qué**: MIROVA no usa M-band 750m para estos volcanes (0 alertas). El clon no debería
  reportarlo. Opciones: (a) display: ocultar VIIRS750 de las 3 vistas operacionales
  (rápido, reversible, recomendado primero); (b) pipeline: no procesar VIIRS750 en
  `mirova_equivalent` (más profundo). Recomendación: (a) ahora, (b) evaluar después.
- **Riesgo**: nulo en recall (0 TP). Se conserva en datos crudos para provenance/futuro.

### 3.3 VIIRS 375m — NO tocar la detección
- Es la fuente del recall (1550 TP). Su path D contextual capta lo débil real. **Intacto.**
- **Opcional (magnitud)**: reportar el foco (max per-pixel) en vez de la suma para clusters
  de campo difuso, acercando el ratio 1.9× → ~1.5×. Con criterio que no subestime erupciones
  reales extendidas (píxeles genuinamente calientes → suma). Requiere R2. Segunda prioridad.

### 3.4 Display — métricas y series por sensor (como MIROVA)
- **Métricas por sensor** (index.html): hoy `computeMetrics` agrupa por bucket internamente
  pero muestra UN número global (mezcla MODIS 2.6% con VIIRS375 38%). Cambiar a mostrar
  recall/precisión/F1/ratio **por sensor** (MODIS | VIIRS375). Quitar VIIRS750 o marcarlo
  "no-MIROVA".
- **Ocultar VIIRS750** de las 3 vistas (chart, sparkline, tabla, cards) en la vista operacional.
- Chart ya separa por sensor (mantener). diario/mosaico: replicar.

## 4. Orden de implementación (fases, cada una con su verificación)

| Fase | Alcance | Toca | Riesgo | Gate |
|---|---|---|---|---|
| **F1** | Display: ocultar VIIRS750 + métricas por sensor | frontend ×3 | bajo (display) | preview |
| **F2** | Reproc histórico con pipeline ACTUAL (cap D9) | data/ | medio | A47 secuencial, verificar |
| **F3** | MODIS co-validación (flag por-sensor) | process_modis.py | **alto (NRT)** | tag+OK+TDD+reproc+R2 |
| **F4** | VIIRS750 no-procesar (opcional) | process_viirs_mod.py | medio | tag+OK |
| **F5** | VIIRS375 reportar-foco (opcional, magnitud) | process_viirs.py | alto | tag+OK+TDD+reproc+R2 |

Recomendación: **F1 primero** (display-only, impacto visible inmediato, sin riesgo — ya quita
VIIRS750 ruidoso y honestifica las métricas). **F2** (reproc) limpia la deuda. **F3** (el fix
de raíz MODIS) con todo el rigor. F4/F5 según resultados.

## 5. Criterios de aceptación
- Recall por evento-noche (VIIRS375) **no baja** vs baseline (reproc real, no offline).
- Precisión MODIS sube drásticamente (de 2.6% hacia ~MIROVA: casi solo Lascar real).
- VIIRS750 fuera de la vista operacional.
- Métricas mostradas por sensor.
- Ratio mediano por sensor dentro de tolerancia (VIIRS375 ≤2×, MODIS solo en eventos reales).
- R2 pixel-level vs TIF MIROVA en ≥1 caso por sensor afectado.

## 6. Pre-mortem / riesgos
- **R1**: co-validación MODIS a nivel escena podría perder un evento real débil MODIS-only en
  el futuro. Mitigación: hoy 0 casos; la regla es "MODIS solo grande" (consistente con MIROVA);
  VIIRS375 es la red. Reproc real lo confirma antes de adoptar.
- **R2 (A18)**: la estimación offline no predice la selección real de cluster. → reproc local
  obligatorio antes de adoptar F3/F5.
- **R3**: ocultar VIIRS750 podría esconder un futuro caso donde aporte. Mitigación: 0 TP en 5
  meses + MIROVA no lo usa; se conserva en datos crudos; reversible (display).
- **Escudo**: NO gate t_bg ciego (S86). La co-validación distingue por COHERENCIA (foco duro
  presente), no por fondo frío. NO tocar VIIRS375 detección (recall).
