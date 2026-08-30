# Reauditoría S52 — contexto olvidado por Claude

> Documento creado S52 (2026-05-17) tras Nicolás señalar "siento que olvidas
> cosas". Resultado de reauditoría exhaustiva subagente sobre memoria +
> CLAUDE.md + MISSION.md + HYPOTHESIS_LOG + feedback files.
>
> **Propósito**: documentar EXPLÍCITAMENTE el contexto crítico que debo
> tener siempre presente para no repetir errores. Leer al inicio de cada
> sesión.

## Errores cometidos esta sesión (S52)

1. **CSV consolidado tratado como "MIROVA reportó X"**: el CSV es scraper
   hecho por NICOLÁS (Mirova-v1) contra mirovaweb.it. `Tipo_Registro` son
   categorías que NICOLÁS asignó, no MIROVA:
   - `ALERTA_TERMICA` = MIROVA detectó y reportó (= TP real)
   - `FALSO_POSITIVO` = MIROVA reportó pero fuera de radios oficiales
     (categoría Nicolás del scraper)
   - `RUTINA` = scraper diario corrió pero MIROVA no reportó nada
     (= vacío, NO es "MIROVA dijo RUTINA")
   - **Universo MIROVA real** = ALERTA + FP = 15/561 records (no 561) en
     Villarrica VIIRS-I 5 meses.

2. **Window auditable confundido**: el CSV consolidado más reciente
   commiteado termina **2026-05-01**. Hoy 2026-05-17. Cualquier audit con
   window 30d real solo abarca 16 días. S47 ya documentó esto pero lo
   olvidé al reporter "F1 98.3% window 30d".

3. **MISSION.md 3 preguntas no aplicadas explícitamente** en propuestas
   recientes. Aunque el resultado fue MISSION-compliant, no validé.

## Contexto crítico que SIEMPRE tener presente

### CSV ground truth (regla S22+)

**Origen**: scraper `Mirova-v1` de Nicolás contra
`mirovaweb.it/latest.php`. NO es export oficial.

**Categorías `Tipo_Registro`** (asignadas por scraper Nicolás):
- ALERTA_TERMICA: MIROVA reportó alerta = TP
- FALSO_POSITIVO: MIROVA reportó pero `Distancia_km > radio_oficial` =
  el cluster está fuera del bbox MIROVA esperado
- RUTINA: scraper corrió esa hora, MIROVA no publicó nada = vacío
- NULO: campo `VRP_MW=0.0` típico de RUTINA

**Para audit recall**: denominador = ALERTA_TERMICA + FALSO_POSITIVO,
**NO contar RUTINA**.

**Window auditable**: latest_date(CSV) - 30 días. Si CSV termina 2026-05-01
y hoy es 2026-05-17, window real audit = 16 días.

### MIROVA NRT no tiene supervisión humana (regla S22+)

CSV NRT = scraper de Nicolás contra latest.php publicado por MIROVA NRT.
**MIROVA NRT NO tiene curaduría manual** (Coppola 2023 §2.5 supervisión
aplica solo a OSF v2.5 histórico curado).

Diferencias recall NRT son **algorítmicas**, no curatoriales.
RUTINA puede ser alerta perdida por MIROVA, NO necesariamente FP nuestro.

### TIF MIROVA ≠ lo que MIROVA reporta (S33+)

TIF en `mirova-tif-archive/data/tif/<Volcan>/YYYYMMDD_*.tif` es **producto
de visualización pre-clustering** con sum de pixels brutos (scene-wide).
NO es la VRP que MIROVA publica.

Caso paradigmático: Puyehue lacolito TIF=2313 MW vs MIROVA reporta 0.18 MW
(468× diff).

**R2 pixel-level válido solo para GEOMETRÍA** (centroid match), NO para
magnitud. Magnitud cubierta por CSV consolidado.

### MIROVA = clon literal, NO "mejor que" (MISSION.md)

Si MIROVA falla en algo, nosotros también fallamos en lo mismo. Esa es la
definición de clon.

Lista vinculante autores MIROVA core:
- **MIROVA**: Coppola, Laiolo, Massimetti, Campus, Aveni, Cigolini
  (Torino + Firenze + Sapienza Roma + INGV + LMV)
- **NO MIROVA aunque sea italiano**: INGV Catania (Del Negro, Corradino,
  Di Bella, Torrisi, Cariello, Amato, Malaguti) → sistemas RSDF/V-STAR/
  FastVRP/CNN. CNR-IMAA Potenza (Marchese, Pergola, Genzano, Filizzola)
  → sistema NHI.

### Las 3 preguntas vinculantes (MISSION.md)

Antes de implementar cualquier fix/threshold/exclusion/path:

1. ¿Está documentado en papers MIROVA core?
2. Si NO, ¿cierra divergencia D1-D5 documentada?
3. Si NO, ¿es alineación interna no-metodológica?

**Si las 3 son NO → NO IMPLEMENTAR**. Anotar en
`tasks/backlog_no_mirova.md`.

### Reglas R1-R8 PROCESS_RULES_S33 (frecuencia uso)

- R1: tests sintéticos antes de cambio audit_metrics.py
- R2: validación pixel-level vs mirova-tif-archive
- R3: audit independiente (no auto-validación)
- R4: pre-mortem en design doc
- R5: brainstorming antes de adopción >50%
- R6: cuestionar mejora >30% antes de aceptar
- R7: tests detectables del bug
- R8: verificación post-deploy próximos ciclos NRT

### Comunicación con Nicolás (CLAUDE.md)

1. **Fenómeno físico primero**, después código
2. Explicar como geólogo, NO como programador
3. No adivinar valores físicos/instrumentales/legales
4. Trade-offs científicos: nombrar explícitamente costo de cada lado
5. Lenguaje llano, no jerga técnica (traducir términos primera vez)

## Conclusiones recientes a re-validar

- "F1 98.3%" S48: válido pero window es ~16d real (no 30d). El número
  sigue siendo correcto, solo el caveat de window.
- "44/45 NRT success" S47: válido (manual trigger validó fix H7b).
- "Villarrica 489 records summit" S51: válido para `mirova_equivalent`
  current.
- "FP_a = 2 con audit espacial" S48: válido bajo nueva convención S48 fix.
- "Pre-S20 Villarrica nunca detectó" S51: válido — verificado con git
  history exhaustivo.

## Top 5 antes de cualquier task nueva

1. Verificar window auditable real (`latest_date(CSV) - 30d`)
2. Leer `pipeline/profiles/mirova_equivalent.yaml` para conocer flags
3. Schema: `pc.vrp_mw` ≠ `record.vrp_mw`, `final_hotspot_dist_km` para
   distancia, `datetime_utc` no `timestamp_utc`
4. Filtrar CSV a `Tipo_Registro in ('ALERTA_TERMICA', 'FALSO_POSITIVO')`
   para audit recall
5. Aplicar 3 preguntas MISSION.md explícitamente antes de proponer cambio
   pipeline

## Persistencia in-vivo (regla meta-meta S21)

Cuando descubras hallazgo durante sesión: persistir INMEDIATAMENTE en
memoria/docs, NO esperar al cierre. La sesión puede cortarse
abruptamente.

## Archivos referencia obligatoria

- `docs/MISSION.md` — 3 preguntas vinculantes
- `docs/MIROVA_DIVERGENCES.md` — D1-D5 documentadas
- `docs/HYPOTHESIS_LOG.md` — H1-H_S52 todas las hipótesis
- `docs/PROCESS_RULES_S33.md` — R1-R8
- `documentacion/BIBLIOGRAPHY_SYNTHESIS.md` — síntesis **46/70 documentos distintos (65.7 %)**, re-medido S128 por `scripts/audit_corpus_documentacion.py` (antes decía 30/60, cifra de S13 nunca re-medida)
- `tasks/backlog_no_mirova.md` — propuestas descartadas
- `~memory/feedback_*.md` — reglas Nicolás
- `~memory/reference_mirova_csv_ground_truth.md` — convención CSV
- `~memory/feedback_audit_verify_data_first.md` — verificar data antes
