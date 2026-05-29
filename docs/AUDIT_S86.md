# Auditoría integral S86 — síntesis cross-source

**Fecha**: 2026-05-28
**Disparador**: Nicolás S86 — "¿el gap precisión 0.024 es realmente bug, o las anomalías MIROVA son simplemente las más fuertes y nosotros detectamos un superset volcánico real?"
**Metodología**: 5 subagentes paralelos (E clasificación física FPs · F integridad scraper · G tests+drifts pipeline · H estado GitHub · I coherencia docs).
**Outputs subagentes**: `experiments/_s86_audit_profundo/{E,F,G,H,I}_*.{md,json}` + scripts reproducibles.

---

## TL;DR — El gap precisión 0.024 es mayormente artefacto metodológico, no bug del pipeline

**Composición real del "gap"** (Subagente E sobre 3687 "FPs" del cruce estricto):

| Componente | n | % | Tratamiento correcto |
|---|---:|---:|---|
| **(a) MIROVA SÍ publicó pero el cruce falló** (mismatch ±1d / cross-sensor) | 1812 | **49.1%** | Reajustar metodología del cruce (Subagente F amplifica esto: bugs del loader local) |
| **(b) Anomalía volcánica REAL no publicada por MIROVA** | 1707 | **46.3%** | **Reportar como valor agregado VRP Chile** (sub-complejos chilenos no priorizados por MIROVA) |
| **(c) Geotermal/lacustre no-volcánico real** | 0 | **0%** | Frontend `mirovaEqVrp` desde S33 ya las filtra fuera de `inner_radius` |
| **(d) Artefacto espurio** (cirrus, glaciar, singleton) | 168 | **4.6%** | Únicos FPs reales — concentrados en Tupungatito ring glaciar (29) y PCC cirrus (19) |

**Lectura geológica**: 95.4% de los "FPs" son anomalías térmicas físicamente reales. El proyecto NO es sub-óptimo — está haciendo trabajo distinto + ampliado respecto de MIROVA NRT.

---

## Cambio de marco fundacional

### Lo que veníamos asumiendo
**Opción A (clon literal MIROVA estricto)**: TP = exactamente lo que MIROVA publica. Cualquier detección extra = FP a cerrar. Gap precisión 0.024 es bug.

### Lo que los datos muestran (E + F)
**Opción B (clon + extensión volcánica documentada)** se ajusta mejor a la realidad:
- MIROVA publica un subset operacional NRT (típicamente las anomalías más fuertes por volcán).
- VRP Chile detecta el superset de anomalías térmicas volcánicas reales, incluyendo features que MIROVA no prioriza (cráter secundario El Agrio en Copahue, Cerro Blanco en NdC, Pichi-Llaima en Llaima, Lazufre en Lastarria, cráter Planchón N en complejo multi-cráter PP, lacolito difuso extendido PCC, lava lake Villarrica).
- Solo 4.6% son artefactos reales.

**Implicación operacional**: este NO es un proyecto a "limpiar de FPs", es un proyecto a **etiquetar honestamente** — separar dashboard:
- "ALERTA MIROVA confirmada por VRP Chile" (la mayoría)
- "Detección adicional VRP Chile (feature volcánica no publicada por MIROVA)" con cita Smithsonian GVP
- "Detección descartada por gate cirrus/glaciar" (los pocos artefactos)

### Implicación para `docs/MISSION.md`
MISSION.md declara "clon literal MIROVA NRT" como objetivo (1) y "herramienta independiente" como (2) futuro. La realidad empírica S86 muestra que **estamos haciendo (1)+(2) simultáneamente sin haberlo declarado**. El cambio de marco no requiere abandonar (1) — requiere distinguir explícitamente qué detecciones corresponden a cada bucket.

---

## Hallazgos paralelos relevantes

### Subagente F — bugs locales del loader VRP Chile (no del scraper)

El scraper Mirova-v1 es ground truth confiable (NRT ~2.5h, encoding limpio, timezone consistente, 0 gaps >48h en 134 días). Pero **nuestro loader local subcontamos MIROVA ~45%** por 4 bugs locales:

| Bug | Impacto | Fix |
|---|---|---|
| **F-B1** OCR (344 ALERTAs únicas) no consumido por loader | Subconteo MIROVA 45% | Cargar CONS ∪ OCR dedup por (ts, vol_norm, sensor_norm) |
| **F-B2** OCR `Distancia_km=0` en 100% filas (real vive en `Nota_Validacion` regex) | Filtros distancia rechazan 100% OCR | Parsear regex `dist[≈~=]\s*(\d+\.?\d*)\s*km` |
| **F-B3** Tupungatito CONS arranca 2026-02-14 (35d después) | Audits ventana >94d sobre-estiman FP-rate Tupungatito | Documentar coverage, recortar ventanas |
| **F-B4** Variante huérfana `Peteroa` pre-2026-01-16 | Audits perdían 6 días PP | Alias `Peteroa → PlanchonPeteroa` |
| **F-I2** 363 filas `FALSO_POSITIVO` CONS (filtradas por `limite_km` scraper) | Detecciones lacolito PCC 7-12 km perdidas como TPs | Política: tratar como `far` en vols con anomalía extendida |

**Una sola PR ~30 líneas resuelve los 4** y ajusta hacia abajo el "gap precisión" residual.

### Subagente G — pipeline en mejor estado del esperado

- 70 tests, 22 módulos, core algorítmico cobertura 75-95%.
- D1/D2/D3/D6 cerrados con evidencia + test.
- D2 default ahora alineado Coppola 2016a Tabla 1 (`N_SIGMA_SUMMIT=5.0`, `SCENE=10.0`).
- Wooster k=18.9/19.7/18.0 verificados. Stefan-Boltzmann puro confirmed. Kernel `np.mean` confirmed.
- **Bug A49 `apply_f66_consistency_gate` NO está en main** — quedó en branch huérfana F66, falsa alarma S79.
- Path D cross-sensor consistente (centralizado en `detection_context.py`).

**Riesgos no-documentados** (gaps de infraestructura, no de algoritmo):
- **R1** `process_viirs_mod.py` 1170 LOC con coverage 25% (clon parcial — patrón histórico de delay aplicando fixes vs `process_viirs.py`).
- **R2** `profile.py` 530 LOC + 80 flags sin tests invariantes.
- **R3** Regla científica "MIR solo nocturno" implementada pero sin test directo.

### Subagente H — repo saludable, NRT operacional confiable

- NRT últimos 30 runs: 79.3% éxito. Único burst de fails (2026-05-24/25) por LANCE DNS timeout upstream, ya recuperado.
- Workflows operacionales OK. 3 reproc obsoletos sin archivar.
- Pages live, dashboard up-to-date, `latest_consolidado.csv` actualizado 2026-05-28.
- 49/50 PRs últimos MERGED.
- Issue #1 OPEN ya resuelto (auto-generado durante burst).
- **A43 Norway YAML** (`"on":` sin quote): `nrt.yml` + `nrt-monitor.yml` con riesgo HTTP 422 latente — fix 5 min defensivo.
- ⚠️ **GitHub PAT en `~/.claude/settings.json` pendiente rotar** desde sesión anterior (regla CLAUDE.md global).
- ~70 min total cleanup opcional (cosmético).

### Subagente I — 7 contradicciones cross-source, regla M8 dispara

| # | Sev | Tema | Resolución |
|---|---|---|---|
| **C1** | ALTA | Worktree canónico ambiguo (3 docs / 3 paths) | Actualizar CLAUDE.md proyecto + MEMORY.md |
| **C2** | ALTA | Reglas A54-A60 huérfanas (A54/A55 nunca existieron, A56-A60 viven solo en META_RULES_S80) | Migrar/renumerar a CLAUDE.md proyecto |
| **C4** | ALTA | Drift D8 (cluster selection factor 27× Puyehue S35) huérfano: ausente de MIROVA_DIVERGENCES y SESSION_INDEX_S80 | Cerrar formalmente |
| **C6** | ALTA | **Anti-patrón emergente** (CRÍTICO ver §"Reideación") | **§ aparte** |
| C3 | MEDIA | Offset Tupungatito 3km S vs 2.99 km SE | **RESUELTO S87**: ya confirmado en `AUDIT_INTEGRAL_S81.md:154` — offset real vent→mirova_center = **4.86 km** (KMZ exacto; "3 km SE" era subestimación humana). Frente D S87 verificó: nuestro primary ancla en el cráter (bearing 322°≈vent 330°); el gap de distancia vs MIROVA es por el punto de referencia (centro de grilla/GVP, A13), no error de ubicación. |
| C5 | MEDIA | Lista papers MIROVA con/sin Cigolini | Estandarizar |
| C7 | MEDIA | MEMORY.md sin entrada S86 (viola M2) | Persistir en cierre |

**MEMORY.md health**: 282 líneas (OK bajo cap M9=500), pero S86 sin entrada. Reformulación M8 propuesta: "cada 10 sesiones O 25 PRs" en lugar de "cada 20 sesiones" — el ritmo S70-S86 (~3 PRs/sesión) acumula deriva más rápido.

---

## Anti-patrón emergente (CRÍTICO, hallazgo I-C6 + E)

PRs adoptados S83-S85:
- **PR #224 (S83)** — `enable_path_d_intra_radio_gate` activado en operacional
- **PR #229 (S85)** — `enable_second_pass_intra_radio_gate` activado en operacional

Ambos pasan MISSION.md 3-preguntas solo por puerta 3 "GRIS alineación infraestructural". Pero:

1. **Hallazgo S85 reveló que el gate intra-radio YA EXISTE desde S33** en `frontend/index.html:868-889` (función `mirovaEqVrp`). Los PRs #224 y #229 son **redundantes operacionalmente**.
2. **Hallazgo S86-E reveló que la mayoría de "FPs" suprimidos por estos gates son anomalías volcánicas reales no publicadas por MIROVA** (categoría (b) 46.3%) — features volcánicas legítimas del complejo. Suprimirlos pre-emptivamente reduce el valor científico del proyecto.
3. **Patrón histórico análogo**: S22-S26 acumuló parches ad-hoc (MAX_SIGMA_COMPONENT_K=7K, vent-path, exclude_zones de inner-radius, Reglas D, cloud mask, pisos VRP) que MISSION.md documenta hoy como anti-patrones. Cada uno parecía justificado individualmente; acumulados anulaban la diferenciación summit/scene MIROVA y forzaron una rebajada de fase grande.

**Si entra un PR #N más de tipo "gate intra-radio por path" sin pasar las 3 preguntas explícitas + verificar (E) antes**, se reabre el ciclo cerrado S27.

**Recomendación**: agregar fila explícita "gate intra-radio sin paper" a MISSION.md anti-patrones; pausar cualquier feature de tipo gate adicional hasta consolidar.

---

## Reideación del plan post-auditoría

### Lo que NO debemos hacer
- **NO implementar Frente 1.A G1** (`sensor != VIIRS_M_750`) como estaba diseñado. El gate suprime un sensor entero — pero VIIRS M-band puede capturar features volcánicas reales (cráteres pequeños, fumarolas) que MIROVA no publica. Antes de filtrar por sensor, hay que clasificar pixel-level las detecciones VIIRS_M_750 nuestras (categoría b vs d).
- **NO extender exclude_zones** (Frente 4 catálogo S85): la cartografía mostró que las features no-volcánicas caen fuera del inner_radius y el gate frontend ya las filtra. Categoría (c) = 0%.
- **NO seguir adoptando "gates intra-radio por path"** (anti-patrón C6).

### Lo que sí mueve el proyecto adelante

**Bloque 1 — Sincronización del marco (1-2h)**

1. **Reescribir cabecera `docs/MISSION.md`** declarando explícitamente Objetivo (1) clon literal MIROVA + Objetivo (2) extensión volcánica documentada como **simultáneos**, no secuenciales. Las 3 preguntas siguen aplicando a (1).
2. **Resolver C1/C2 (contradicciones críticas)**:
   - Worktree canónico = `VRP Chile/` raíz tras S82-prep reapuntó a main.
   - Migrar A56-A60 a CLAUDE.md proyecto y renumerar limpio (sin gap A54/A55).
3. **Persistir entrada S86 en MEMORY.md** (regla M2 violada).
4. **Cerrar D8 formalmente** (probablemente resuelto S38 con `enable_vent_anchored_clustering`).

**Bloque 2 — Fix loader local CSV (1 PR ~30 líneas, ~1-2h)**

Resuelve F-B1/B2/B3/B4/I2. Después de aplicarlos, **rehacer el cruce TP/FP** con metodología correcta:
- CONS ∪ OCR como universo MIROVA.
- Distancia OCR parseada de `Nota_Validacion`.
- Variantes de nombre normalizadas.
- Tolerancia ±1d / cross-sensor cuando hay ambigüedad de timezone.

Reportar el nuevo gap precisión. Hipótesis: cae a ≤0.5 (gran parte del 49% mismatch desaparece).

**Bloque 3 — Etiquetar honestamente las detecciones (~3-4h, 1-2 sesiones)**

Implementar en `pipeline/store.py` campo derivado `pc.classification`:
- `"mirova_confirmed"` — match exacto con MIROVA CONS+OCR (post-Bloque 2 metodología correcta).
- `"vrp_chile_volcanic_extension"` — cluster dentro de inner_radius o ≤2 km de feature volcánica catalogada Smithsonian GVP, NO en MIROVA.
- `"vrp_chile_summit_unconfirmed"` — cluster summit nuestro sin MIROVA esa noche (puede ser ALERTA OCR que se nos escapa o detección sub-pixel que MIROVA no resolvió).
- `"artifact_candidate"` — cirrus alto (`t_bg<260K` + path D solo + n_pixels=1) o ring glaciar warm-relativo Tupungatito.

Frontend separa visualmente las 4 categorías. Dashboard se vuelve "monitoreo VRP Chile con desglose MIROVA" en lugar de "clon MIROVA".

**Bloque 4 — Mejorar coverage tests pipeline (~2h, opcional)**

Cerrar riesgos G-R1/R2/R3:
- Tests sintéticos `process_viirs_mod.py` paridad con `process_viirs.py`.
- Tests invariantes `profile.py` (defaults Coppola 2016a, flags consistentes).
- Test directo "MIR solo nocturno" rechazo records day-time.

### Lo que queda para S88+
- Refinamiento path D condicional para Tupungatito ring glaciar (29 FPs categoría d).
- Refinamiento path D condicional para PCC cirrus alto (19 FPs categoría d).
- Investigación scientific de las 1707 detecciones categoría (b) — cuáles son features volcánicas conocidas vs candidatos nuevos por documentar.

---

## Estado de salud del proyecto (post-auditoría)

| Aspecto | Veredicto |
|---|---|
| Algoritmo Coppola 2016a (paths A/B/C/D + Test1) | ✅ Bien implementado |
| Coeficientes Wooster + Stefan-Boltzmann | ✅ Verificados S14, mantenidos |
| Coverage tests core | ✅ 75-95% sobre módulos críticos |
| Drifts D1/D2/D3/D6 | ✅ Cerrados con evidencia |
| NRT operacional GitHub Actions | ✅ 79% éxito (red de seguridad funcionando) |
| Scraper Mirova-v1 ground truth | ✅ Confiable |
| Drifts D7/D8/D9 | ⚠️ Abiertos pero no críticos |
| `process_viirs_mod.py` coverage | ⚠️ 25%, gap real |
| `profile.py` tests invariantes | ⚠️ Ausentes |
| Coherencia docs cross-source | 🔴 7 contradicciones (M8 dispara) |
| Loader local CSV (subconsumo OCR + bugs) | 🔴 4 bugs, subcontamos MIROVA 45% |
| Marco conceptual (clon estricto vs ampliado) | 🔴 Implícitamente cambiado sin documentar |
| Anti-patrón emergente "gates intra-radio" | 🔴 PRs #224 + #229 + riesgo PR #N |

**Conclusión**: el problema central NO es el código del pipeline (que está mejor del esperado), es **la metodología de evaluación + el marco conceptual del proyecto + los bugs del loader CSV**. La auditoría reorienta el trabajo a estas tres cosas y para de perseguir un "gap precisión" que en su mayoría no existía como bug.

---

## Outputs de S86 (todos durables)

- `experiments/_s86_f_precision_gap/{A,B,C,D}_*.{md,json,py}` — investigación gap precisión (3 mecanismos investigados, 1 confirmado, 2 refutados con datos)
- `experiments/_s86_audit_profundo/{E,F,G,H,I}_*.{md,json,py}` — auditoría integral
- `docs/F_PRECISION_GAP_INVESTIGATION_S86.md` — síntesis Frente 2.A (con conclusión actualizada por auditoría)
- `docs/AUDIT_S86.md` — este doc
- `tasks/BLOQUE_ARRANQUE_S87.md` — pendiente generar al cierre

## Reglas activas usadas

- **calidad-paso-a-paso (S85)** — investigar antes de implementar. Refutó Mecs 2 y 3 con datos antes de tocar pipeline. Auditoría profunda S86 confirmó que NO debíamos implementar G1 ciego.
- **superpowers-brainstorming** — step-back metodológico cuando Nicolás cuestionó el marco TP/FP.
- **dispatching-parallel-agents** — 5 subagentes E/F/G/H/I cubrieron auditoría en ~30 min reloj wall vs 5h secuencial.
- **A45** — pendiente para el momento de tocar pipeline.
- **M2 persistencia in-vivo** — violada parcialmente (MEMORY.md sin S86). Corregir al cierre.
- **M8 audit cada 20 sesiones** — disparada por >3 contradicciones. Reformulación propuesta: "cada 10 sesiones O 25 PRs".

## Tags defensivos

Ninguno creado en S86 — auditoría 100% offline sin tocar pipeline. Tags se crearán en S87 cuando se implemente Bloque 2 (loader fix) o Bloque 3 (campo `pc.classification`).
