# Handoff S14→S15 arranque — VRP Chile

Fecha: 2026-04-21. **Leer ESTE archivo PRIMERO** al arrancar S15. Supersede
`tasks/status_s14_handoff.md` (que queda como referencia histórica).

---

## TL;DR — lo que pasó esta sesión y dónde estamos

Sesión de trabajo de cierre S14 que resolvió:

1. **Factor 42 diagnosticado**: Láscar 2025-11-15 05:48 UTC VIIRS_SNPP tiene 77 px
   nuestros vs 4 MIROVA. Causa identificada: falta dual-ROI + dNTI contextual +
   ETI cuadrático + second-pass. **No es fórmula ni coeficiente, es detección**.
2. **Audit S1-S14 completo** → 5 hallazgos estructurales en
   `tasks/audit_s1_to_s14.md`.
3. **~74 papers procesados** en 6 batches paralelos (Vault Obsidian) → síntesis
   consolidada en `Vault/20_Conceptos/sintesis_papers_s15.md`.
4. **Backfill Nov 2025 local** quedó a 46/120 combos, posiblemente detenido (ver
   sección "Estado operacional").
5. **Plan S15 escrito**: 7 fixes priorizados (P3.1→P4.2) con fuente canónica y
   esfuerzo estimado.

---

## Los 3 documentos a leer al arrancar S15 (en este orden)

```
1. C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\tasks\status_s15_arranque.md
   (este archivo — cóntaxto completo, decisiones abiertas, próximos pasos)

2. C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\tasks\audit_s1_to_s14.md
   (auditoría sesiones previas — 5 hallazgos críticos, regresión Lascar S11 sin cerrar,
    Test 1 Villarrica pendiente 6 sesiones, cero tests pipeline/)

3. C:\Users\nmend\OneDrive\Escritorio\claude\Vault\20_Conceptos\sintesis_papers_s15.md
   (síntesis consolidada ~74 papers — factor 42 diagnóstico completo, regímenes
    térmicos chilenos, aprendizajes A6-A10, plan S15 ordenado)
```

Con estos tres cualquier sesión de Claude entra con todo el contexto cargado sin
re-leer los 74 papers ni re-diagnosticar el bug.

---

## Plan S15 ordenado por impacto × factibilidad

| # | Fix | Impacto | Fuente canónica | Esfuerzo |
|---|---|---|---|---|
| **P3.1** | Dual-ROI thresholds (C1/C2 summit vs scene) | Muy alto | `coppola2016enhanced.md` | 1 día |
| **P3.2** | dNTI contextual 8-vecinos | Alto | `coppola2016enhanced.md` | 1-2 días |
| **P3.3** | ETI cuadrático (background adaptativo) | Medio-alto | `coppola2016enhanced.md` | 1 día |
| **P3.4** | Second-pass adyacente | Medio | `coppola2016enhanced.md` | 1 día |
| **P3.5** | Filtros negativos dNTI<−0.1 | Bajo | `coppola2016enhanced.md` | 30 min |
| **P4.1** | Filtro ≤5 km summit (modo publicación mirovaweb) | Alto para matchear mirovaweb | `massimettithermal.md` p.130 | 1 h |
| **P4.2** | Filtro satzen ≤50° (modo publicación) | Medio | `massimettithermal.md` | 1 h |

**P3.* son la paridad algorítmica contra OSF v2.5 raw (objetivo declarado).**
**P4.* son para matchear mirovaweb supervisado (opcional, modo alternativo).**

Primer fix a atacar: **P3.1 dual-ROI**. Los umbrales exactos están en
`Vault/10_Bibliografia/99_por_clasificar/coppola2016enhanced.md` sección "Notas clave".
Valores MODIS:
- ROI1 summit 5×5 km: C1=0.003 noche, C2=5σ noche sobre dNTI
- ROI2 scene 50×50 km: C1=0.01 noche, C2=10σ noche
- Filtros negativos: dNTI/dETI < −0.1 descartados

Para VIIRS 375m/750m, Campus 2022 (`campus2022transition.md`) confirma que es el
mismo algoritmo que MODIS — usar los mismos C1/C2 escalados por resolución si hace
falta.

---

## Estado operacional al cerrar

### Backfill Nov 2025 (local, profile `mirova_equivalent_backfill_nov2025`)

- **Estado**: 46/120 combos procesados, última actualización en Lascar 2025-11-16.
- **Fails**: 8 (Villarrica 2025-11-07 a 11-14, errores de red transitorios).
- **Proceso background bash ID**: `bc7qj3fdv` (puede haber muerto — verificar al
  reanudar con `tail logs/backfill_nov2025.log`).
- **Datos parciales disponibles en**: `data/mirova_equivalent_backfill_nov2025/`
  (Villarrica.json completo, Lascar.json parcial, Copahue y Chaiten faltantes).

Si el proceso murió, relanzar con:
```
python -u scripts/backfill_nov_2025.py > logs/backfill_nov2025.log 2>&1 &
```
o retomar solo los combos faltantes con `--volcano X --start Y --end Z`. Store.py
es idempotente con `overwrite=True`.

### NRT operacional (GitHub Actions)

- Corriendo normal cron cada 2h. Último fail transitorio 20:38 UTC (Errno 101
  network unreachable del runner, no bug).
- S14 pusheado al remoto como commit `5478bce`.

### Git status al cerrar (sin commitear, working tree)

```
 M pipeline/profile.py                                          ← VALID_PROFILES +backfill
?? data/mirova_equivalent_backfill_nov2025/                     ← output backfill (NO commitear si es grande)
?? experiments/25_crossmatch_nov2025.json                       ← crossmatch parcial
?? experiments/25_crossmatch_nov2025.png                        ← scatter parcial
?? experiments/25_crossmatch_nov2025_vs_osf.py                  ← script crossmatch
?? frontend/llaima_anomalies.png                                ← screenshot pendiente decisión
?? frontend/planchonpeteroa_anomalies.png                       ← screenshot pendiente decisión
?? logs/                                                        ← NO commitear
?? pipeline/profiles/mirova_equivalent_backfill_nov2025.yaml    ← nuevo profile
?? scripts/backfill_nov_2025.py                                 ← nuevo script
?? tasks/audit_s1_to_s14.md                                     ← auditoría
```

**Commit sugerido al inicio de S15** (después de leer los 3 docs y decidir):
```
S15 infraestructura: backfill profile + crossmatch + audit

- pipeline/profiles/mirova_equivalent_backfill_nov2025.yaml: perfil clonado de
  mirova_equivalent con data_subdir separado y MODIS off (pyhdf Windows).
- scripts/backfill_nov_2025.py: wrapper reproceso granule-por-granule 4 volcanes ×
  30 días (Lascar, Villarrica, Copahue, Chaitén).
- experiments/25_crossmatch_nov2025_vs_osf.py: cross-match OSF v2.5 por
  (volcán, sensor, Δt≤15min) con ratio/Spearman/recall/precision.
- tasks/audit_s1_to_s14.md: auditoría sesiones previas S1→S14.
- pipeline/profile.py: VALID_PROFILES incluye mirova_equivalent_backfill_nov2025.
```

No commitear: `data/mirova_equivalent_backfill_nov2025/`, `logs/`, los 2 PNG
sueltos de `frontend/`. `.gitignore` ya está actualizado para excluir
`data/mirova_reference/` y `*.S13backup`.

---

## Decisiones abiertas para S15

1. **¿P3 o P4 primero?** Mi recomendación: P3.1 dual-ROI. Es el fix más alto
   impacto y todos los umbrales están disponibles. P4 son capa de publicación,
   no cierran el bug contra OSF.

2. **¿Esperar al backfill completo antes de aplicar P3?** No. El backfill actual
   tiene el bug. Una vez que P3 esté implementado hay que **reprocesar** el Nov 2025
   entero con el pipeline corregido — los granules ya están bajados en los JSONs
   parciales pero las detecciones cambian. El backfill fresco sirve solo para
   medir pre-fix vs post-fix.

3. **¿Seguir procesando las 6 referencias bibliográficas faltantes?** Lista en
   síntesis sección 8. Opcionales, no bloquean S15. Priorizar solo si aparece
   una duda específica.

4. **¿Implementar `anthropic-skills:writing-plans` antes de P3.1?** Sí,
   recomendado por regla `CLAUDE.md` — "Antes de escribir fix que toque
   `pipeline/` con >20 líneas → `writing-plans`". P3.1 es edición mayor de 3
   archivos (`process_modis.py`, `process_viirs.py`, `process_viirs_mod.py`).

5. **Hallazgos audit S1-S14 pendientes**: ver `tasks/audit_s1_to_s14.md`. Los 2
   más urgentes:
   - **#2 regresión Lascar S11** (recall 0.79→0.56 sin investigar): ¿investigar
     antes de P3 o asumirlo capturado por el fix de dual-ROI?
   - **#3 Test 1 integrado-ROI Villarrica**: 6 sesiones postergado, plan existe en
     `tasks/plan_s13_test1_integrated_roi.md`. Considerar si entra al sprint S15.

---

## Bloque de arranque literal para pegar a Claude al inicio de S15

```
Arranco sesión S15 del proyecto VRP Chile.

Por favor leé en orden estos 3 documentos antes de hacer nada:

1. C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\tasks\status_s15_arranque.md
2. C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\tasks\audit_s1_to_s14.md
3. C:\Users\nmend\OneDrive\Escritorio\claude\Vault\20_Conceptos\sintesis_papers_s15.md

Cuando termines confirmame que los leíste, resumime en ≤10 líneas dónde quedamos,
y esperame el próximo paso. No toques código ni lances agents ni pushes git
hasta que yo apruebe explícitamente.

Contexto mínimo por si no lo tenés: soy Nicolás, geólogo SERNAGEOMIN, trabajando
en VRP Chile — sistema independiente de MIROVA para 11 volcanes chilenos con
VIIRS 375m/750m + MODIS. Hablame en español, fenómeno físico antes que fórmula,
"por qué" antes que "cómo".
```

---

*Fin handoff S15 arranque. 2026-04-21 cierre sesión S14 procesamiento masivo
papers + diagnóstico factor 42 + plan S15.*
