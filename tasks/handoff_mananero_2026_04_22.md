# Handoff mañanero 2026-04-22 — P3.2 validation overnight

Este documento te orienta al despertar. Leelo en orden.

## TL;DR rapido

- **Overnight lanzado a 00:29:43**. Timeouts 2h/1.5h/1h para Lastarria/Lascar/
  Chaiten. Al terminar corre crossmatch + delta report.
- **Observacion temprana** (cuando escribi este doc, ~10 min post-lanzamiento):
  download VIIRS lento. Puede pasar que solo Lastarria termine en 5h.
  **Lastarria es el caso critico** (ratio 20x a arreglar), asi que parcial OK.
- **Si ves delta report con solo Lastarria**: el veredicto sigue siendo valido
  para el objetivo principal del fix. Lascar y Chaiten son canary/verificacion,
  se pueden repetir despues.
- **Primer record Lastarria reprocesado mostraba senal rara**: 48 px Path D a
  10.15 km del vent (Lazufre). **Probable P3.2 NO APROBADO** sin P3.1 dual-ROI
  acoplado. Ver Escenario B.

## Paso 1 — Revisar el log del overnight

```bash
tail -40 logs/overnight_p32.log
```

Deberías ver las 4 etapas con `=== END ... rc=0 ===` o bien un fallo/timeout.

Etapas esperadas:
1. Lastarria Feb-Apr 2026 (timeout 2h)
2. Lascar Feb-Apr 2026 (timeout 1.5h)
3. Chaitén Feb-Apr 2026 (timeout 1h)
4. Crossmatch post-P3.2 (5 min)
5. Delta report pre/post P3.2 (2 min)

Si una etapa timeout-eó (rc=124) las siguientes igual corrieron. Si el
orquestador entero crasheó (raro), ver `logs/overnight_p32_wrapper.log`.

## Paso 2 — Leer el veredicto

```bash
cat experiments/30_p32_delta_report.md
```

El reporte dice **APROBADO** o **NO APROBADO** según 3 criterios:

1. Lastarria ratio mediano < 3.0 (desde 19.87).
2. Lascar ratio mediano en [1.10, 1.30] (canary).
3. Recall global >= 0.23 (baseline 0.28).

## Paso 3 — Actuar según veredicto

### Escenario A — P3.2 APROBADO

Seguís con **P3.1 dual-ROI** (plan: `tasks/plan_s15_p3_1_dual_roi.md`).
El código P3.2 puede pushear a main para que NRT lo tome:

```bash
git push origin main
```

Verificar que el próximo NRT (cron 2h) produzca records con `n_dnti_ctx_path`.

### Escenario B — P3.2 NO APROBADO (caso más probable dada la observación temprana)

**Observación al cierre de sesión anoche**: primer record Lastarria reprocesado
(2026-02-01 04:48 VIIRS_SNPP) tenía **48 pixels Path D a 10.15 km del vent**
con VRP 8.42 MW. Lastarria tiene `inner_radius=3`, esos pixels son del sistema
Lazufre (fumarólico crónico al sur de Lastarria). Path D los captura como
anomalías reales (lo son térmicamente) pero MIROVA los descarta o los clasifica
distinto.

**Si el ratio Lastarria SUBE en vez de bajar**: P3.2 por sí solo amplifica
FPs de zonas contextuales heterogéneas fuera del summit. La cura física
completa es P3.1 dual-ROI (C1=0.010 estricto en scene descarta esos 48 pixels).

**Opciones** en orden de preferencia:

1. **No revertir código, implementar P3.1 ya** (`tasks/plan_s15_p3_1_dual_roi.md`).
   Mantener `enable_dnti_contextual_path=true` pero agregar `enable_dnti_dual_roi=true`.
   Reprocesar Lastarria+Lascar+Chaitén con P3.2+P3.1 juntos. Nuevo delta report.
   Es el camino correcto — P3.2+P3.1 fueron diseñados como complementarios.

2. **Revertir solo el flag en mirova_equivalent** (cirugía mínima, si urge
   detener el impacto de P3.2 en NRT antes de tener P3.1):
   ```yaml
   # pipeline/profiles/mirova_equivalent.yaml
   paths:
     enable_dnti_contextual_path: false
   ```
   Commit + push. NRT vuelve a comportamiento pre-P3.2 pero el código queda.

3. **No pushear P3.2 a main** hasta tener P3.1 listo. Trabajar localmente,
   NRT sigue corriendo con código S14 + Fase 0.7. Esta es la opción default
   si el overnight no terminó bien.

### Escenario C — overnight no terminó / log incompleto

Posibles razones:
- Fetch earthaccess muy lento (LAADS DAAC rate limit, red residencial).
- Un granule corruptó y el subprocess colgó.
- Ventana 5h insuficiente para los 3 volcanes × 80 días × 4 sensores.

Recovery:
- `experiments/27_crossmatch_post_p32.json` puede existir parcialmente.
- Re-correr solo el crossmatch + delta report sobre lo que se procesó:
  ```bash
  python experiments/27_crossmatch_vs_consolidado.py --out experiments/27_crossmatch_post_p32.json
  python experiments/30_p32_delta_report.py
  ```
- Si solo Lastarria terminó, el delta report sobre Lastarria igual es
  accionable (es el volcán crítico).
- Si nada terminó, lanzar manualmente solo Lastarria con ventana más chica:
  ```bash
  python scripts/run_pipeline.py --volcano Lastarria --start 2026-03-15 --end 2026-04-22 --overwrite
  ```

## Paso 4 — Estado del working tree

Commits de esta sesión (rama main local, **sin pushear**):

```
<último> S15 foreground noche: OSF crossmatch + Path D diagnostic + P3.1 skeleton
<prev>   S15 P3.2: orquestador overnight + delta report automatizado
b0ba72b  S15 P3.2 step 6: Path D en process_modis.py (1km)
f24f683  S15 P3.2 step 5: Path D en process_viirs_mod.py (750m)
885ac02  S15 P3.2 step 3: Path D en process_viirs.py (375m)
366e618  S15 P3.2 step 2: profile keys
<prev>   S15 P3.2 step 1: contextual dNTI helper + tests TDD
6df01c0  correccion metodologica Tabla 3 OSF vs NRT
<prev>   analisis historico OSF v2.5 25 anos
d6beaff  Fase 1: perfil distancias + crossmatch baseline
13d18c2  Fase 0.7: mirova_center Tupungatito + PP
23752b8  Fase 0: smoke test coeficientes Wooster
9e90972  Fase 0: cerrar S14 infra
```

Tests: 26/26 pytest passing. No pushes al remoto hasta validar P3.2.

## Paso 5 — Próximos hitos S15

1. Decidir P3.1 vs P3.2-rollback según delta.
2. Ejecutar P3.1 si aplica (1-2 días).
3. Task 7 del plan P3.2: reproceso 11 volcanes (VIIRS-only desde local).
4. Memory update final + commit consolidado para push.

## Contacto

Cualquier duda del overnight — abrir sesión Claude diciendo "sigo sesión S15,
leí handoff mananero". Claude puede:
- Interpretar logs y delta report.
- Lanzar P3.1 si decidiste ese camino.
- Ajustar C1 o parámetros Path D si iteramos.
