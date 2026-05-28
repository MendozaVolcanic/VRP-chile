# BLOQUE ARRANQUE S86

**Sesión previa**: S85 (2026-05-28). Sesión muy larga con 5 PRs mergeados,
3 hipótesis investigadas + 2 descartadas, 5 docs durables persistidos,
2 feedback memory rules nuevas.

## §0 — Worktree canónico

**Path**: `C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile`

**Primer comando**:
```bash
cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
git fetch origin --prune
git log --oneline HEAD..origin/main  # ¿algo nuevo?
git pull --ff-only
cat tasks/BLOQUE_ARRANQUE_S86.md
```

## §1 — Lo que cerró S85

### PRs mergeados a main

| PR | Tema | Impacto |
|---|---|---|
| [#227](https://github.com/MendozaVolcanic/VRP-chile/pull/227) | Preventivos NRT + Fase B' implementación | A57+A58+A60 documentación + healthcheck staleness diario + helper second_pass_intra_radio |
| [#228](https://github.com/MendozaVolcanic/VRP-chile/pull/228) | Audit script Fase B' pre-escrito | Reusable cross-sesión |
| [#229](https://github.com/MendozaVolcanic/VRP-chile/pull/229) | **Adopción Fase B' operacional** | Default ON: `enable_second_pass_intra_radio_gate=true` en mirova_equivalent.yaml. -59% pixels MODIS recapturados ruidosos. Cero pérdida TPs. |
| (este cierre) | Docs Fase C + bloque arranque | Persiste hallazgos + plan S86 |

### Hallazgo crítico S85 (el insight central)

**El gate de supresión "R3 cluster fuera de inner_radius" YA EXISTE
operacionalmente desde S33** — vive en `frontend/index.html:868-889`
(función `mirovaEqVrp`). El dashboard NUNCA mostró los 155 R3 violators
detectados por audits Python. Esos audits están **mal calibrados**: no
replicaban la lógica del frontend.

Validación empírica adicional: **367/367 ALERTAs MIROVA Tier A reales
caen 100% dentro del inner_radius del KMZ**. Cero excepciones. Esto
confirma uniformidad MIROVA (intuición Nicolás) + valida que la
geometría inner_radius_km del KMZ es correcta tal cual.

### Hipótesis investigadas y descartadas con datos (valor durable)

1. **Fase B (gates A/B/C MODIS)** — refutada por audit B0 (87.7% R3 no
   tienen path 1er pase activo). Doc: `docs/F_S81_B_BACKLOG_PATH_ABC_GATES.md`.
2. **Fase B' (second_pass causa dominante de R3)** — implementada,
   adoptada por mejora interna (-59% MODIS), pero R3 cae solo -7.5%.
   Hipótesis principal refutada. Doc: `docs/F_S81_B_PRIME_ADOPTION_S85.md`.
3. **Fase C zonas no-volcánicas per-vol** — cartografía 18 clusters
   reveló que mayoría son features volcánicas reales del complejo que
   MIROVA tampoco publica como TPs (porque caen fuera del inner_radius).
   Doc: `docs/F_S81_C_1_ZONES_CATALOG.md`.
4. **Fase C geometría extendida per-vol** — refutada por audit empírico
   367/367 MIROVA intra-radio. MIROVA NO extiende geometría per-vol.
   Doc: `docs/F_S81_C_R3_NATURE_AUDIT.md` cabecera.

### Feedback memory rules nuevas (durables cross-sesión)

- `feedback_calidad_paso_a_paso.md` — "tenemos tiempo y tokens
  ilimitados, paso a paso, registrar y descartar con datos".
- `feedback_when_to_close_session.md` — heurística zona verde/amarilla/roja
  para decidir continuar vs cerrar.

### Tags defensivos creados S85 (snapshots origin/main pre-cambio)

- `pre-s85-f-s81-b-prime` → snapshot pre-implementación Fase B'.
- `pre-s85-f-s81-b-prime-adoption` → snapshot pre-adopción operacional.
- `pre-s85-f-s81-c` → snapshot pre-investigación Fase C (no implementada).

## §2 — Plan S86

Dado que el "problema R3" se reveló como artefacto de audit (no
operacional), S86 tiene **opciones diversas SIN un único próximo paso
obvio**. Lo que sigue son frentes posibles, ordenados por valor /
esfuerzo:

### Frente 1 — Schema consistency (opcional, baja-media prioridad)

**Problema**: los JSONs persistidos retienen records con `pc.vrp_mw > 0`
aunque el frontend los descarte. Audits Python externos deben replicar
`mirovaEqVrp` para no contar FPs fantasma.

**Opciones**:
- **1.A** — Enriquecer schema con campo derivado `pc.mirova_publishable`
  (bool). Pipeline calcula en store.py. Frontend sigue igual (toggle
  funciona). Audits Python usan campo nuevo. **Tag defensivo + tu OK
  recomendado**. ETA 1-2h.
- **1.B** — Mover lógica filtro al backend (zero-out store.py). Rompe
  toggle "incluir lejanas" del frontend. No recomendado salvo que decidas
  retirar ese toggle. ETA 2h.
- **1.C** — Statu quo. NO hacer nada. El sistema funciona correcto para
  el dashboard. Audits Python ya saben replicar `mirovaEqVrp` desde S33.

**Recomendación** si tomás este frente: **1.A** (bajo riesgo, valor real
para futuras integraciones).

### Frente 2 — Atacar gap precisión vol-sensor-level (alta prioridad histórica)

El balance honesto del proyecto (sesión S85) reveló que la **gran
diferencia con MIROVA NO es R3, es precisión global**: emitimos ~1031 FPs
MODIS / 25 TPs Lascar (precision 0.024). MIROVA suprime ~99% de lo que
nosotros publicamos.

Pero **MIROVA usa la misma lógica algorítmica para todos** (uniformidad
confirmada S85). ¿Cuál es el mecanismo real de supresión que NO está en
papers? Posibles direcciones:

- **2.A** — Audit OSF v2.5 MIROVA: ¿qué fracción de los pixels detectados
  por nuestro algoritmo (idéntico a Coppola 2016a) sobreviven en el CSV
  publicado MIROVA NRT? Si hay un threshold de magnitud + extensión
  mínima que no aplicamos → encontrar ese threshold.
- **2.B** — Investigar `enable_test1_pixel_filter` (refutado S33 por bug
  `mirovaEqVrp` con métrica auto-confirmatoria). Re-evaluar ahora que
  `mirovaEqVrp` está limpio post-S33.
- **2.C** — Replicar la lógica de "publicación condicional" mostrada por
  el behavior empírico: Test 1 + coherencia temporal + magnitud >= 0.1 MW.

**Recomendación**: 2.A primero (offline puro, sin tocar pipeline).
Investigación ~3-4h, output `docs/F_PRECISION_GAP_INVESTIGATION_S86.md`.

### Frente 3 — Magnitud VRP gaps (media prioridad)

Volcanes con ratio fuera de banda 0.5-2.0 (S85 audit baseline):

- Tupungatito VIIRS 5.27× (sobreestimación)
- PP VIIRS 4.39× (sobreestimación)
- PCC VIIRS 0.19× (subestimación)

Estos son drifts de magnitud per-cluster individuales. Cada uno requiere
investigación física separada. **Recomendación**: investigar PCC primero
(subestimación grave, lacolito extenso). ETA 4-5h por vol.

### Frente 4 — Implementar exclude_zones extendido (baja prioridad)

Categoría (b) del catálogo C.1 son 4 features no-volcánicas claras:
- Copahue cluster 2 — campo geotermal Las Máquinas.
- NdC cluster 11 — cuenca Río Diguillín fuera complejo.
- PP cluster 15-16 — ladera argentina (Malargüe).

Activar flag `enable_exclude_zones` para esos vols + agregar 4 zonas
nuevas. ~1-2h + A/B. Acerca ligeramente al clon literal por el lado
"supresión MIROVA".

**Recomendación**: NO urgente. Dashboard ya está limpio. Hacer solo si
en algún audit externo (publicación, integración SERNAGEOMIN) los R3
del JSON crudo causan ruido.

### Frente 5 — Beyond MIROVA roadmap

`docs/BEYOND_MIROVA_EXTENSIONS.md` lista 11 extensions documentadas para
post-validación clon literal. EXT-1 (Fan 2015 BTD cirrus filter)
históricamente primera candidata. Solo activar cuando frentes 1-3 estén
resueltos.

## §3 — Reglas vinculantes activas (cross-sesión)

- **A45** tag defensivo + confirmación Nicolás antes de
  `pipeline/process_*.py`, `store.py`, `mirova_equivalent.yaml`.
- **A47** NO paralelo local sobre `data/mirova_equivalent/`.
- **A49** verificar `git diff` post-insert/edit.
- **A50** cross-source verify `origin/main` antes de etiquetar "pre-existing".
- **A52** `git fetch + pull` en worktrees, no asumir estado.
- **A56-A60** preventivos NRT (ver `docs/META_RULES_S80.md`).
- **M1** cap PRs/sesión soft 12 hard 20 (S85 acumuló 4 → OK).
- **M2** persistencia in-vivo, no esperar al cierre.
- **calidad-paso-a-paso (S85)** — investigar antes de implementar,
  descartar con datos, persistir descartes.
- **when-to-close-session (S85)** — zona verde/amarilla/roja para decidir.

## §4 — Comunicación con Nicolás

Hablarle como geólogo: fenómeno físico → mecanismo pipeline → fórmula al
final. Cuando propongas adopción operacional, explicar primero qué hace
el cambio sobre el campo térmico, después por qué el audit valida.

## §5 — Prompt copy-paste para S86

```
Sesión S86 — VRP Chile. S85 cerró con 4 PRs + 5 docs durables + 2 feedback
memory rules nuevas.

Hallazgo S85 clave: el gate "R3 cluster fuera de inner_radius" YA EXISTE
operacionalmente desde S33 (frontend mirovaEqVrp:868). Audit empírico
367/367 ALERTAs MIROVA Tier A confirma uniformidad MIROVA + geometría
inner_radius del KMZ tal cual. Hipótesis Fase B/C (gates A/B/C,
second_pass causa dominante, geometría extendida per-vol) REFUTADAS por
datos. Fase B' adoptada por mejora interna (-59% pixels MODIS recapturados
ruidosos), no por resolver R3.

Adopción operacional Fase B': PR #229. Flag default ON.

Worktree: C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile

Primer comando:
  cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
  git fetch origin --prune && git pull --ff-only
  cat tasks/BLOQUE_ARRANQUE_S86.md

Lectura obligatoria:
1. tasks/BLOQUE_ARRANQUE_S86.md (este doc)
2. docs/F_S81_C_R3_NATURE_AUDIT.md (insight central S85, cabecera)
3. docs/F_S81_C_1_ZONES_CATALOG.md (referencia futura categoría b)
4. memory/feedback_calidad_paso_a_paso.md + feedback_when_to_close_session.md
5. docs/F_S81_B_PRIME_ADOPTION_S85.md (decisión adopción Fase B')

Frentes posibles S86 (no hay uno obvio):
- Frente 1 (1.A): schema consistency campo mirova_publishable. 1-2h.
- Frente 2 (2.A): audit OSF MIROVA — encontrar mecanismo supresión real
  que explica gap precisión 0.024. 3-4h, recomendado para entender el
  problema mayor del proyecto.
- Frente 3: drifts magnitud PCC/Tupungatito/PP VIIRS. 4-5h por vol.
- Frente 4: exclude_zones extendido para 4 features no-volcánicas. No
  urgente.
- Frente 5: beyond MIROVA (post-validación).

Reglas activas: A45, A47, A49, A50, A52, A56-A60, M1, M2,
calidad-paso-a-paso, when-to-close-session.

Comunicame como geólogo: fenómeno → mecanismo pipeline → fórmula al final.
```
