# S99 — Auditoría retrospectiva de hallazgos dormidos (registro durable)

**Pedido por Nicolás (S99, 2026-06-03):** tras redescubrir por casualidad que el flag
`enable_test1_pixel_filter` tenía un comentario que diagnosticaba el 19× de Tupungatito
y quedó apagado y olvidado, auditar TODAS las sesiones (~99) buscando hallazgos
valiosos dormidos: fixes a medias, flags OFF con diagnóstico real, A/B sin concluir,
diseños no ejecutados, drifts abiertos. **Todo debe quedar registrado.** Es la
auditoría A51 (cada 20 sesiones) aplicada con foco en deuda latente.

**Método:** 6 agentes en paralelo (A26/A51). Detalle por veta en
`experiments/_s99_audit/dormant/{flags_off, ab_abandonados, specs_no_ejecutados,
drifts_abiertos, code_todos, github_estado}.md`.

## Hallazgo estructural (lo más importante)
La contabilidad de veredictos del proyecto es **buena** (la mayoría de A/B y drifts
están bien cerrados con doc). Pero los hallazgos dormidos que SÍ quedan **no son
aleatorios: se agrupan en UN tema** — la **inflación de magnitud / manejo sub-píxel en
Tier A "Muy Bajo"** (fondo frío, glaciar, cirrus, lava lake sub-píxel). Es exactamente
el frente de S99 §2. Varios de los dormidos son **enfoques rivales o complementarios
del fix que estamos probando ahora mismo** (recorte espacial Test 1). No verlos sería
repetir el error de abandono sobre el mismo problema.

## Registro rankeado (verificado donde se indica)

### Tier 1 — alto valor, construido/diseñado, MISMO tema que S99
| ID | Hallazgo | Estado | Verificado | Impacto | Recomendación |
|---|---|---|---|---|---|
| **DF-1** | `compute_vrp_lava_lake_eq16` (Coppola 2024 Eq.15+16, lava lake sub-píxel) en `pipeline/vrp_regimes.py:105` | Construido + 10 tests, conectado flag-OFF S99 (PR #326) | ✅ por mí | ⚠️ **NO fiel a MIROVA NRT — ver "Verificación fuente primaria" abajo** | **NO adoptar operacional (drift per-volcán). Solo experimental.** Medido en A/B por completitud |
| **DF-2** | VRP integrated Eq.1 textual (`docs/superpowers/specs/2026-05-06-*`) | Diseño completo, **0 código** | doc | Ataca la suma Test1 en su raíz conceptual; **hipótesis rival** del recorte espacial S99 | Comparar en el mismo A/B antes de descartar |
| **DF-3** | `enable_test1_k1_retire_from_hot_mask` (NEW-7) `profile.py:335` | Flag codificado, **ausente del yaml operacional**, cita SP426.5 §298-300; A/B "S72 F2.3" nunca corrido | ✅ por mí (ausente) | Señalado S72 como causa más probable del drift Muy Bajo remanente | A/B barato; retomar junto a S99 |

### Tier 2 — sistémicos abiertos, tema adyacente
| ID | Hallazgo | Estado | Impacto | Recomendación |
|---|---|---|---|---|
| **DF-4** | D9 causa raíz (path D dNTI ctx en fondo frío) | Cap 5 MW tapó síntoma; ratios post-cap 6-83× (Villarrica/Chaiten/PP/Tupun/NdC) ABIERTO | Magnitud sistémica | Probable que el fix S99 (espacial) + DF-1/DF-3 lo cierren — re-medir tras S99 |
| **DF-5** | `enable_final_pixel_filter` (Driver B Phase 2) `mirova_equivalent_phase2` | **Nunca re-evaluado** con métrica corregida post-bug S33; ausente del yaml | Mismo problema (pixels marginales) | Cerrar formalmente o re-correr como control del A/B S99 |
| **DF-6** | MODIS deuda Salar (recall-al-cráter ~9-12%) + gate intra-radio MODIS ("ABIERTO P0") | FN (cluster se va al Salar) + FP (~70-100 det/vol RUTINA) | **FN = lo más grave** + FP masivo | Frente MODIS propio (distinto sensor); priorizar el FN |
| **DF-7** | Drift #7 A_pix nadir-fijo MODIS (`_drift7_*`) | Perfiles existen, **A/B nunca corrido**; ratio MODIS 1.21× sin cerrar | Magnitud MODIS | Cerrar A/B (reconciliar con A36) |

### Tier 3 — higiene / bajo
| ID | Hallazgo | Recomendación |
|---|---|---|
| DF-8 | GitHub issue #1 (NRT alert) nunca cerrado; causa (outage abril) muerta desde H7/S35; cron hoy intermitente | Cerrar #1; abrir uno nuevo si molestan los fails esporádicos |
| DF-9 | ~70 ramas remotas stale (`claude/sNN-*`, worktrees huérfanos) | Poda (`clean_gone`); 0 valor perdido (todo llegó a main) |
| DF-10 | D2 nsigma_mir_5/12 veredicto caducado (premisa cap=7K ya no aplica, cap=999 hoy) · F_S81_C r3_zone · HotLINK CNN benchmark nunca iniciado | Re-evaluar D2 si se toca N·σ; HotLINK rompería circularidad de medirnos solo vs MIROVA (futuro) |

### Lección de schema (no accionable, pero registrar)
El gap `anomaly_pixels`↔`primary_cluster` estuvo ~62 sesiones abierto (`backlog_s32`) y
rompía el mapa del dashboard hasta el fix S94 #294. Mide cuánto pueden latir los gaps
de schema. (A46 ya lo recoge.)

## Mecanismo anti-recurrencia (cómo evitar que vuelva a pasar)
1. **Este doc es el registro vivo.** Cada flag OFF y cada perfil A/B debe tener estado
   de veredicto acá (adoptado / refutado-con-doc / **dormido**). Actualizar en cada
   auditoría A51 y cuando se abra/cierre un A/B.
2. **Regla de cierre de sesión (propuesta):** ningún flag nuevo `enable_*` default OFF
   ni perfil A/B nuevo se considera "terminado" sin una línea de estado en este registro.
   Un A/B "colgado sin veredicto" es deuda, no neutral.
3. **Al diseñar un fix, revisar primero este registro** por enfoques rivales/dormidos
   del mismo problema (lo que DF-1/DF-2 son para S99). Evita reimplementar o abandonar
   por segunda vez.

## Verificación fuente primaria (S99, post-auditoría — A62)
Nicolás cuestionó la premisa de DF-1/DF-2: ¿MIROVA NRT conmuta de método por
volcán/régimen, o es UN algoritmo por SENSOR uniforme? Auditoría verbatim de los
papers (`experiments/_s99_audit/dormant/papers_per_sensor.md`):
- **Coppola 2016a (paper del sistema NRT)**: el objetivo declarado fue NO calibrar
  por volcán — *"does not require... case by case determination of adapted
  thresholds"*, *"self-adapting thresholds... independent of local conditions"*,
  *"completely autonomous... easily exportable to several target volcanoes"*. La
  única variación por-objetivo es ROI/summit (centro GVP) + **SENSOR** (bandas + α +
  umbrales). Wooster Eq.17 *"can be applied to any sensor... by adapting Apix and α"*.
- **Coppola 2024 chapter**: lava lake (Eq.15-16/Burgi) y crater lake (Eq.25) están en
  la sección *"Applications"* como **productos de segundo nivel, manuales, calibrados
  caso por caso** (*"requires specific calibrations"*, *"valid only within the limits
  of the assumptions"*), NO el pipeline NRT automático. *"VRP is inadequate for
  low-T VTFs"* es un caveat de validez de Wooster (600-1500 K), no un cambio de
  algoritmo.
- **Conclusión**: DF-1 (Eq.16 por-volcán) y DF-2 (integrated Eq.1 por-régimen) son
  **drifts del clon MIROVA**, no fidelidad. El fix de magnitud correcto es **uniforme
  por sensor, sobre el conjunto de píxeles alertados** (Candidatos A/B del A/B S99).
  MIROVA llega a ~0.2 MW en Villarrica Y Tupungatito con el MISMO Wooster-Σ uniforme
  porque alerta POCOS píxeles; nosotros inflamos por sobre-marcado del Test 1.
- **Mecanismo anti-recurrencia aplicado**: DF-1/DF-2 quedan marcados "investigado
  S99: NO fiel a MIROVA, no adoptar operacional". Que una sesión futura no los
  resucite creyéndolos buena idea dormida.

## Veredicto
Sí hay valor dormido, pero **acotado y coherente**: gira alrededor de la magnitud
Muy-Bajo/sub-píxel. El ejemplar mayor (19× Test1) ya está en tratamiento (S99). Los
dos hallazgos que cambian el plan inmediato son **DF-1 (Eq.16 lava-lake, construido+
testeado, sin conectar)** y **DF-2 (integrated Eq.1, diseñado)** — ambos enfoques del
mismo problema de magnitud que conviene **comparar en el A/B de S99** en vez de seguir
solo con el recorte espacial. No hay un segundo "gigante dormido" con fix limpio fuera
de este tema.
