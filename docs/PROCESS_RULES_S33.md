# Reglas de proceso S33 — prevención de drift por bug en métrica

> Documento vinculante. Surge del bug S33 (`mirovaEqVrp` no validaba
> `pc.centroid_dist_km` contra `inner_radius`) que contaminó los audits
> S27→S31+→S32 y llevó a adopción operacional de Driver B Phase 1 con
> métrica auto-confirmatoria.

## Contexto

S32 P2 Driver A introdujo función `mirovaEqVrp` con bug arquitectural:
chequeaba `distance_class==='summit'` pero NO validaba que el cluster
reportado realmente estuviera dentro del `inner_radius_km` del volcán.

`distance_class` se calcula desde `final_hotspot_dist_km` (Test 1 puede
hacerlo apuntar al centroide ROI 1-3km del vent), pero `primary_cluster`
se elige por VRP máximo — puede ser un cluster geográficamente lejano
(Salar Atacama, lago Conguillío). Resultado: clusters lejanos reportaban
su VRP como del cráter.

Audit Driver B Phase 1 usó la misma función con bug → "validó ratio
2.52→1.66×" pero ambos profiles compartían el bug. Auto-confirmación.

Re-audit con métrica corregida reveló que Phase 1 destruye recall
(74.2% → 55.6%, −18.6pp) en lugar de mejorarlo.

## Reglas R1-R7

### R1 — Test unitario para cada función crítica de audit/frontend

**Aplica**: cualquier función que computa métricas de comparación con MIROVA.

**Implementación**:
- `pipeline/audit_metrics.py` con `mirova_eq_vrp(record, volcano_name)`.
- `tests/test_audit_metrics.py` con casos sintéticos del bug S33:
  - `dist_class=summit + pc.centroid_dist_km=24 + Lascar inner=5 → 0`
  - 17 casos edge cubriendo TODOS los caminos de la función.
- Cualquier modificación futura a la lógica debe pasar los tests existentes.

**Por qué**: el bug S33 era detectable con 1 test unitario. Sin tests,
6+ sesiones de drift.

### R2 — Verificación pixel-level con MIROVA web (gate adopción operacional)

**Aplica**: antes de cambiar `enable_*: true` en `pipeline/profiles/mirova_equivalent.yaml`
(profile operacional). NO aplica a profiles A/B aislados.

**Implementación**:
1. Identificar 5 granules específicos de Tier A donde el cambio se
   espera tener efecto distintivo (caso peor del fix, caso típico, caso
   borde).
2. Procesar esos 5 granules con flag ON y OFF.
3. Comparar pixels detectados pixel-by-pixel contra el plot Latest10NTI
   de MIROVA web (descargable desde mirovaweb.it).
4. Si los pixels nuestros con flag ON coinciden con los puntos rojos
   MIROVA → hipótesis empírica confirmada. Adoptar.
5. Si NO coinciden → hipótesis refutada. NO adoptar.

**Costo**: 2-3h por adopción.

**Por qué**: A/B test con métrica derivada del frontend valida coherencia
interna pero no contra ground truth pixel-level real. La verificación
contra MIROVA es la única que detecta sesgos sistemáticos en la métrica.

### R3 — Audit independiente para validar la métrica

**Aplica**: cuando se reporta resultado A/B importante.

**Implementación**:
- Script `experiments/76_audit_independent.py` re-implementa la lógica
  desde primer principio sin importar `pipeline.audit_metrics`.
- Si los resultados de los dos audits coinciden → métrica robusta.
- Si difieren → bug en uno de los dos. NO confiar en el resultado.

**Por qué**: detecta bugs como S33 que no se ven cuando un solo audit
audita una métrica.

### R4 — Pre-mortem antes de adopción operacional

**Aplica**: antes de cambiar `enable_*: true` en profile operacional.

**Implementación**:
Antes del commit, escribir 1 párrafo respondiendo:

> "Si esta adopción está mal:
>  - ¿Qué resultado vería en producción que confirmaría el problema?
>  - ¿Qué métrica detectaría el problema antes de afectar usuarios?
>  - ¿Cuál es el peor caso si adoptamos sin validar?"

Si las respuestas son "no sé" → bloquear adopción hasta tener respuestas.

**Costo**: 10 min por adopción.

**Por qué**: forzar enumeración de señales de alarma previene "trust the
audit" pasivo. El pre-mortem en Driver B Phase 1 habría preguntado:
"¿qué pasa si Phase 1 destruye recall? ¿cómo lo detectaría?". La
respuesta hubiera sido "verificar pixel-level con MIROVA" → R2 → fix.

### R5 — Brainstorming OBLIGATORIO antes de cambios metodológicos

**Aplica**: cualquier cambio de lógica en `pipeline/process_*.py`,
`pipeline/audit_metrics.py`, o `pipeline/profile.py` que afecte
interpretación de la data (vs solo refactor o fix de typo).

**Implementación**:
- Invocar `superpowers-brainstorming` ANTES de modificar el código.
- Producir doc en `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`.
- Aprobación explícita del usuario antes de implementar.

**Cambio respecto a regla actual**: era "regla fuerte invocar". Ahora
es "OBLIGATORIO con producción de design doc". Sin design doc, NO
hay implementación.

**Por qué**: brainstorming en S32 antes de Driver B Phase 1 habría
identificado la mezcla metodológica (Coppola 2016a Tabla 1 ≠ Coppola
2015 Test 1) y forzado verificación pixel-level antes de adoptar.

### R6 — Cuestionar resultados sorpresivos

**Aplica**: cuando un audit dice "mejora ≥30% del problema" o
"resultado contradice expectativa".

**Implementación**:
Antes de aceptar el resultado, responder:
1. ¿Qué métrica produjo este resultado?
2. ¿Está la métrica documentada con tests?
3. ¿He cuestionado por qué la mejora es tan grande/pequeña?
4. ¿Hay otra forma de medir lo mismo? (R3 audit independiente)

Si alguna respuesta es "no" → BLOQUEAR conclusión hasta validar.

**Por qué**: el "Phase 1 mejora ratio 35%" no fue cuestionado en S32.
Si hubiera sido, R3 + R2 habrían detectado el bug.

### R7 — Audit the audit con casos sintéticos

**Aplica**: cuando se introduce o modifica función de métrica.

**Implementación**:
Construir records sintéticos en `tests/test_audit_metrics.py`:
- Caso bug histórico (ej. S33 dist_class=summit + pc=24km).
- Caso típico positivo.
- Caso típico negativo.
- Casos edge identificados por experiencia.

Los tests deben ejecutar como parte del CI / suite normal.

**Por qué**: cuando el A/B compara dos profiles, los dos comparten el
código que mide. R7 audita el código mismo con datos sintéticos
controlados. Detecta lo que A/B no puede.

## Estado de adopción

| Regla | Estado | Implementación |
|---|---|---|
| R1 | ✅ S33 | `pipeline/audit_metrics.py` + `tests/test_audit_metrics.py` (17 tests) |
| R2 | 📋 documentado, NO aplicado retroactivamente | Para próximas adopciones operacionales |
| R3 | ✅ S33 | `experiments/76_audit_independent.py` |
| R4 | 📋 documentado | Plantilla en este doc |
| R5 | 📋 documentado, regla fuerte | CLAUDE.md actualizado |
| R6 | 📋 documentado | Checklist en este doc |
| R7 | ✅ S33 | Casos sintéticos en test_audit_metrics.py |

## Lecciones meta

1. **Sesgo de confirmación**: tener expectativa "X mejorará Y" + audit
   que confirma → no cuestionamos. Antídoto: R6.

2. **Auto-confirmación A/B**: dos profiles que comparten código de
   medida no validan correctitud absoluta, solo diferencias. Antídoto: R3.

3. **"Trust the audit" es fail mode**: el audit es código, código tiene
   bugs, bugs invisibles cuando solo se valida contra sí mismo. Antídoto:
   R1 + R7.

4. **Tiempo "ahorrado" saltando verificación pixel-level se paga 6×**:
   Driver B Phase 1 adopción "rápida" (1h) costó después 6+h debugging +
   reproc + fix. Antídoto: R2.

## Aplicación retroactiva

S27→S31+→S32 milestones tienen métricas posiblemente contaminadas por
bug S33. Antes de citar como hito, re-validar con métrica corregida:

- "Recall global S31+ 83.5%": verificar con `experiments/76_audit_independent.py`.
- "Ratio S27 1.35×": verificar con métrica corregida.
- "Driver B Phase 1 ratio 1.66×": ya sabemos que era 1.39× (bug + Phase 1).
- "Recall paridad Phase 1": ya sabemos que era −18.6pp (real regresión).
