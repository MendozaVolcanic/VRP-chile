# Backlog: propuestas descartadas por MISSION.md

Inventario formal de propuestas atractivas (mejorarían algún número) pero
**descartadas por MISSION.md "Las 3 preguntas vinculantes"**. Mantenerlas
documentadas con razón para no reintroducirlas en futuras sesiones.

Regla: una propuesta entra acá si las 3 preguntas dan NO, o si "Q1: ¿está
en papers core?" no se cumple literalmente.

---

## 1. Filtro persistencia VIIRS375 ≥2 noches dentro de 5 días

**Origen**: S48 — subagente Isluga deep dive lo recomendó como PRIO 1 con cita
"Coppola 2016a §4.2".

**Razón descarte (S48)**:
- Verificación literal del paper Coppola 2016a SP426.5:
  - Línea 654: *"MODIS system [...] **does not require historical (temporal)
    analysis**"*
  - Línea 107: *"does not require the analysis of historical data sets"*
  - Línea 364: detección spectral-spatial puro, snapshot-based
- El "§4.2" citado por el subagente **no existe** (alucinación).
- MIROVA explícitamente NO usa filtro de persistencia temporal.

**Q1: ¿en papers core?** NO (paper explícito en sentido opuesto).
**Q2: ¿cierra D1-D5?** NO.
**Q3: ¿alineación interna?** NO (lógica de pipeline).

**Veredicto**: 3/3 NO → DESCARTADO. Re-introducir solo si Nicolás aprueba como
fase (2) "herramienta independiente", no como fase (1) clon MIROVA.

---

## 2. Test 1 integrated VRP — fórmula para magnitud sub-pixel summit

**Origen**: S49 — al investigar 118 records test1+summit+pc.vrp=0 (NdC 89,
Lascar 15, Lastarria 9). Hipótesis original H_S49_TEST1_INTEGRATED_VRP_MISSING
asumía existencia de "Coppola 2015 Eq.1 integrated VRP".

**Razón descarte (S50)**:
- Verificación literal Coppola 2016a SP426.5: Equations 1-5 son sobre
  NTI/NTIbk/ETI/dNTI — **solo detección, no cálculo VRP**.
- Verificación Coppola 2024 chapter Springer:
  - Eq.17 VRP = ΔL_MIR × c × A_pix (Wooster 2003): **inadecuada para
    low-temperature VTFs** (línea 1163-1164).
  - Eq.14 Two-component model: requiere asumir T_hot O f_hot (no observable).
  - Eq.16 Stefan-Boltzmann TIRVolcH: ya implementado como `vrp_tir_mw`.
- Verificación empírica TIRVolcH en NdC: **solo 2/79 records (2.5%) tienen
  vrp_tir_mw>0**. Y uno con 99 MW patológico. NO viable como fallback.
- **No hay fórmula pública en papers core MIROVA** que extraiga magnitud sub-MW
  summit cuando el background ambient (ring 5-25km) está frío similar al
  pixel mezclado. MIROVA reporta 0.02-0.06 MW pero su método interno es
  privado.

**Q1: ¿fórmula en papers core?** NO. Wooster (Eq.17) explícitamente no aplica,
TIRVolcH no funciona empíricamente para estos casos, y no hay tercera fórmula
documentada.

**Veredicto**: DESCARTADO sin fórmula documentada. Re-introducir solo si:
- (a) Surge nuevo paper MIROVA core con fórmula sub-pixel summit explícita
- (b) MIROVA hace público el método interno
- (c) Decisión explícita de Nicolás de implementar Two-component model
  (Eq.14) asumiendo T_hot fija (ej. 600K) — esto sería divergencia
  metodológica documentada en MIROVA_DIVERGENCES.md

**Cobertura operacional actual**: fix audit S48 (H_S48_AUDIT_VRP_ZERO_FALSE_FN)
cuenta TP por `test1+summit+dist≤inner` independientemente de `pc.vrp_mw`.
Recall 97.2% logrado. El issue de magnitud reportada (pc.vrp=0 cuando MIROVA
reporta 0.02-0.30 MW) queda como **limitación conocida del método pixel-level
Wooster**, no como bug del pipeline.

---

## 3. exclude_zone Lago Villarrica / Calafquén (6 far cluster VIIRS-I)

**Origen**: S49 — 6 detecciones VIIRS-I Villarrica far (5.1% del total),
incluyendo incendio agrícola NW 27.5km.

**Razón descarte**:
- MISSION.md "Anti-patrones" tabla: `exclude_zones` removido S27 porque
  "MIROVA no usa máscaras geográficas".
- MIROVA en caso paradigmático 05-04 detectó cluster Lago Calafquén y lo
  clasificó FALSO_POSITIVO manualmente (no por máscara).
- Implementar exclude_zone divergiría del clon literal y enmascararía
  detecciones genuinas hipotéticas.

**Veredicto**: DESCARTADO. Performance Villarrica VIIRS-I (94.9% summit) ya
es excelente; el 5.1% far es noise inherente VIIRS-I 375m esperable.
Documentar en MIROVA_DIVERGENCES.md como "ruido VIIRS-I 375m esperable" en
sesión futura.

---

## 4. Generalización mirova_center_* a otros vols (S49)

**Origen**: S48-49 — fix PCC `mirova_center` motivó pregunta: ¿extender a
Planchón, Villarrica, Tupungatito, NdC?

**Razón descarte (S49)**:
- Verificación TIFs MODIS otros vols:
  - Planchón: peak pixel disperso, no centroide consistente
  - Villarrica: vent vs centroide térmico ≤0.5 km (no warrants fix)
  - Tupungatito: ya tiene mirova_center_lat/lon set
  - NdC: peak pixel disperso, no centroide consistente
- Solo PCC tuvo TIFs con centroide térmico claro (lacolito 2011 dominante).

**Veredicto**: NO procede sin evidencia caso-por-caso. **Replicar el approach
PCC (TIFs MODIS con activity persistente verificada) per-vol**. Es trabajo
para sesión futura específica, NO un fix genérico.

---

## 5. N·σ Di Bella 2024 (12σ noche VIIRS / 8σ día)

**Origen**: S22-S24 mencionado en `docs/PAPERS_AUDIT.md`.

**Razón descarte (S26)**:
- Di Bella es **INGV Catania**, NO MIROVA (Torino + Firenze + Sapienza).
- MISSION.md "Lista de papers NO MIROVA": Di Bella 2024 explícitamente excluido.
- Coppola 2016a Tabla 1 dice 5σ summit / 10σ scene MODIS — esos son los
  thresholds canónicos MIROVA.

**Veredicto**: DESCARTADO. Si nuestro recall MIROVA-paridad pide thresholds
distintos a Coppola 2016a Tabla 1, primero validar contra OSF v2.5 datos
(no contra Di Bella).

---

## 6. Aveni 2025 GRL Eq.9 (k_TIR=60.17 para VIIRS 375m)

**Origen**: S17-S24, evaluado y refutado en `docs/DRIFTS_S17.md`.

**Razón descarte**:
- Aveni 2024 RSE (TIRVolcH, mismo grupo MIROVA) usa Stefan-Boltzmann puro.
  Esa es la versión adoptada operacionalmente.
- Aveni 2025 GRL con k_TIR=60.17 es investigación posterior NO adoptada
  operacionalmente por MIROVA.
- Implementarlo sería divergir del estado operacional MIROVA.

**Veredicto**: DESCARTADO. Adoptar solo si MIROVA OSF v2.6+ refleja este
cambio.

---

## Reglas para agregar entrada acá

1. Verificar las 3 preguntas MISSION.md explícitamente.
2. Documentar la fuente de la propuesta (subagente, paper, intuición).
3. Documentar evidencia empírica si existe (ej. TIRVolcH 2.5% para H_S49).
4. Documentar condición bajo la cual sería re-introducible (paper nuevo,
   decisión explícita de Nicolás, etc).
5. Linkear a HYPOTHESIS_LOG si hay entrada relacionada.
