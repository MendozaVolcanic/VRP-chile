# S102 — Interacción nadir-fijo VIIRS × ctxpeak (diseño / decisión)

**Fecha**: 2026-06-06 · Brainstorming (regla vinculante). Objetivo: clon literal MIROVA.
Contexto: tras adoptar nadir-fijo MODIS (#354), el A/B de medición VIIRS reveló un
undershoot en VIIRS375 que sospechamos es doble corrección con ctxpeak.

## 1. Evidencia (A/B run 27069747395, abr-may, perfil _viirs_nadir_ab)
Ratio nuestro/MIROVA por sensor, base(sec³+ctxpeak) → nadir(nadir+ctxpeak):
- **VIIRS375 global 1.95× → 0.76×**, FN nuevos 0. Undershoot en focales: Láscar 0.66,
  Isluga 0.62, Lastarria 0.66 (vs MODIS Láscar 0.92). El undershoot vive en records
  **Test1/ctxpeak** (n=49/50/38); los no-Test1 son n=1-5.
- VIIRS750 global 1.63× → 0.80×, 1 FN (Isluga). Residuo glaciar path D persiste
  (Tupun 19→16.6, Isluga 13.6→8.2) = 2ª palanca, frente aparte.

## 2. Mecanismo (verificado en código)
`process_viirs.py:1507-1509`: el VRP de Test1 = `pixel_area × WOOSTER_COEFF × delta_L`.
Escala LINEAL con el área de píxel → nadir-fijo lo reduce. Correcto y esperado.

**Hipótesis central**: ctxpeak (adoptado S100 para curar Tupungatito VIIRS375 18.9×)
fue probablemente un **parche del drift sec³** — la misma raíz que nadir-fijo arregla.
Adoptar nadir (raíz) + mantener ctxpeak (parche) = **doble corrección** → undershoot.
Anti-patrón A55 (parches acumulados). MISSION: la raíz debe reemplazar al parche, no
apilarse.

## 3. Lo que falta medir
¿**Nadir-fijo SOLO** (sin ctxpeak) da ~1.0 y mantiene recall (0 FN)? No es respondible
con los datos actuales (no hay brazo nadir+ctxpeak-OFF).

## 4. Plan (aprobado por Nicolás: opción A)
**3er brazo A/B**: perfil `_viirs_nadir_noctx_ab` = mirova_equivalent + nadir VIIRS ON
+ ctxpeak OFF (`enable_test1_contextual_filter:false` + `_keep_peak:false`). MODIS
nadir igual en los 3 brazos. Comparación 3-way (mismo script extendido):
- base = operacional (sec³ + ctxpeak) [disco]
- arm1 = nadir + ctxpeak [_viirs_ab_art, hecho]
- arm2 = nadir + NO ctxpeak [nuevo]

## 5. Criterio de decisión (pre-registrado, evita confirmation bias)
- **Si arm2 (nadir, sin ctxpeak) ratio ~0.85-1.2 global Y 0 FN nuevos vs base** →
  **adoptar nadir-fijo VIIRS + RETIRAR ctxpeak VIIRS375** (raíz limpia reemplaza parche).
  Es lo MISSION-correcto.
- **Si arm2 sigue sobre-estimando (>1.4) o pierde recall (FN>0)** → ctxpeak NO era solo
  parche del sec³; aporta algo real → mantener ctxpeak, adoptar nadir, aceptar el
  undershoot 0.76 (arm1) como neto-mejor (opción B).
- **Si arm2 undershoot también (<0.7)** → el coeficiente/método tiene otro sesgo;
  NO adoptar, investigar WOOSTER vs Test1 antes (frente nuevo).

## 5bis. VEREDICTO (run 27079762282, parcial 8/11 pero DECISIVO) — 2026-06-07
Resultado 3-way VIIRS375 global: base 2.08 → nadir+ctx **0.78** → **nadir-SIN-ctx 2.43**.
Quitar ctxpeak EMPEORA (Tupun 0.73→13.77, Villarrica 0.94→8.32, Llaima 1.02→21.85).
→ **Cae en el caso 2 (arm2 >1.4)**: ctxpeak NO era parche del sec³ — cura el anillo
nival del Test1 integrado (mecanismo distinto). **Hipótesis central REFUTADA** por datos
(A62). Láscar 0.66(ctx)≈0.70(no-ctx): el undershoot leve es del área nadir misma, NO
doble corrección; dentro de tolerancia 0.7-1.4, mejora enorme desde 1.28.

**DECISIÓN**: adoptar nadir-fijo VIIRS + **MANTENER ctxpeak** (arm1, 0.76-0.78 global,
0 FN VIIRS375). VIIRS750 glaciar residuo (Tupun/PP 16.6, Isluga 8.2) persiste = path D
2ª palanca, frente aparte.

**SECUENCIA recomendada (NO adoptado aún, S102)**: el hang de descarga del NRT (root
cause confirmada esta sesión, fetch.py download_granules sin timeout de pared) hace que
los reprocs históricos sean NO confiables AHORA (colgó 3/11 de este mismo arm-3). Por eso:
1º arreglar el NRT download-timeout (tras confirmar con la instrumentación PR #362),
2º recién entonces VIIRS nadir end-to-end (flip + reproc histórico confiable + promoción +
R2/R3/R8), como MODIS. Adoptar antes = reproc parcial/sucio. A45 (tag+OK+TDD) pendiente.

## 6. Restricciones (A45 / no-revertir)
- ctxpeak está adoptado en operacional (S100, paired A/B d_recall+0). Retirarlo es A45
  (tag + OK + TDD + reproc). Solo si arm2 lo justifica con datos.
- VIIRS750 residuo glaciar = path D, NO se toca acá (2ª palanca).
- Medición aislada (data_subdir propio), NO toca operacional (A47).

## 7. Verificación
analyze_viirs_nadir_ab.py extendido a 3-way + FN por brazo. Decisión por §5.
