# Diseño — Recuperar la magnitud "Muy Bajo" del Test1 integrado (FN reactivación NdC)

**Fecha**: 2026-06-16 (S111). **Estado**: DISEÑO — NO implementado (gate brainstorming).
**Disparador**: primera anomalía en sitio eruptivo NUEVO del cráter de Nevados de Chillán
(MIROVA VIIRS375 0.06 MW "Muy Bajo", 06-16 05:30 UTC); la detectamos espacialmente pero
con magnitud 0. Diagnóstico: `docs/AUDIT_S111_TEST1_LOWMAG_FN.md`.
**Decisión Nicolás**: alcance = magnitud + FN de detección; enfoque = "intentemos todo"
(A/B multi-brazo, elegir el mejor). **Requiere OK + tag (A45) antes de implementar.**

## 1. Problema (fenómeno → mecanismo → evidencia)

La lava débil sub-píxel de un sitio eruptivo nuevo eleva levemente el NTI del cráter
(MIR sube más que TIR). El Test1 integrado **detecta** bien con NTI (cancela la
topografía, A69/A104) — `triggered_test1=True`, 74 píxeles, summit 0.44 km. Pero la
**magnitud falla por dos mecanismos**:

- **(A) Cascada de `source`** (process_viirs.py:1420-1439): el recompute del VRP Test1
  (1545-1625) está gateado por `final_hotspot_source=='test1'`. Cuando un cluster
  cercano DÉBIL (1 píxel, vrp≈0) coexiste, `eruption_far=False` y `only_test1_source=
  False` → `source=eruption` → el recompute NO corre → magnitud = la del cluster (≈0).
- **(B) Fondo de magnitud contaminado** (1551-1556): el VRP usa radiancia MIR ABSOLUTA
  con `L_bg` del anillo 1-3 km, que en un nevado incluye el valle tibio → `max(L−L_bg,0)
  ≈0`. Es la cara-magnitud de A69 (detectamos con NTI, cuantificamos con MIR absoluto).

**Sensibilidad al fondo (estimación local, 1 píxel pico NdC 06-16)**:
| Fondo | VRP | |
|---|---|---|
| Local 1-3 km (valle tibio) — HOY | ≈0 | FN |
| Global 5-25 km (275.79 K), solo pico | 0.26 MW | 4.4× alto |
| MIROVA | 0.06 MW | objetivo |
→ La magnitud Muy Bajo es finamente sensible al fondo; **calibrar empíricamente, no a ojo**.

**Dimensión**: 0/6 ALERTAS VIIRS375 NdC capturadas en magnitud (3 por (A), 1 por (B), 1
sin pasada, 1 FN detección 22-mar 0.49 MW). Patrón sistémico (Villarrica lava lake,
Lastarria fumarolas). Ground truth: 6 ALERTAS MIROVA, VRP 0.02-0.49, mediana 0.06.

## 2. Solución (3 partes)

### Parte A — Fix de cascada (prerequisito, flag-gated)
Extender la cascada: cuando `test1_summit_hit` Y el eruption/cluster legacy es
trivialmente débil (`primary_cluster is None` o `primary_cluster.vrp_mw < ε`, ε≈0.01 MW),
→ `final_hotspot_source='test1'` → corre el recompute (con su cuantificación y filtros).
Solo afecta records donde el Test1 es la señal real y el cluster no aporta magnitud.
Flag `enable_test1_priority_weak_cluster` (default OFF). NO toca detección (triggered_*).

### Parte B — Calibración de la cuantificación (A/B multi-brazo, "intentemos todo")

**CORRECCIÓN CLAVE (verificación adversarial S111)**: NdC/Lascar/Lastarria YA tienen
`lbg_global_compatible=true` + `enable_test1_lbg_global` ON en el operacional. Por tanto,
con la Parte A ON, el recompute de esos 3 nevados **ya usa el fondo GLOBAL**, no el local.
Consecuencia: la Parte A ON sola **no da ~0; da ~0.26 MW (4.4× alto) y puede inflar RUTINA**.
El problema de la Parte B NO es "destapar la magnitud" (la Parte A + global ya lo hace),
sino **bajar del 0.26 hacia el 0.06 de MIROVA SIN inflar las noches RUTINA**. El brazo Q1
(fondo local) NO aplica a estos 3 (ya usan global); el baseline de Parte A ON = Q2 (global).

Con la Parte A ON, comparar candidatas de cuantificación del VRP Test1 contra las 6
ALERTAS MIROVA. Candidatas (la mayoría ya existen como flags):
| Brazo | Cuantificación | Flag(s) |
|---|---|---|
| Q0 | baseline (cluster) | — (control, da ~0) |
| Q1 | Test1 MIR, fondo local 1-3 km | cascada ON sola |
| Q2 | Test1 MIR, fondo GLOBAL 5-25 km | `enable_test1_lbg_global` + per-vol |
| Q3 | Test1 MIR, fondo anillo INTERMEDIO (probar 2-4 / 3-5 km) | nuevo param |
| Q4 | Eq.16 lava lake (despeja A_hot, Stefan-Boltzmann) | `enable_test1_lava_lake_eq16` + per-vol |
| Q5 | fondo LOCAL sobre NTI (S105) | `enable_test1_local_bg_nti` |
| Q6 | + filtros compacidad (pixel/contextual/spatial-core) sobre el ganador | `enable_test1_*_filter` |
**Criterio pre-registrado (A66)**: elegir el brazo cuyo VRP reproduce mejor las 6 ALERTAS
(error mediano |log(ours/mirova)| mínimo sobre 0.02-0.49) **sin inflar las RUTINA**
(noches MIROVA=0 deben quedar <0.01 en nuestro brazo). Trade-off recall/precisión explícito.

### Parte C — FN de detección 22-mar (0.49 MW, Test1 NO disparó)
Investigar por qué el Test1 no disparó esa noche (k_observed vs k_sigma; cobertura/nube/
calidad del granule). Si es un umbral, evaluar; si es cobertura/nube, documentar (no
fixeable). Frente menor, se cierra con el probe del A/B.

## 3. Plan de validación (A45)
- Tag `pre-s111-test1-lowmag`. Implementar Parte A + exponer brazos B (flags), default OFF.
- A/B: reprocesar NdC (+ validación Villarrica/Lastarria/Lascar para no-regresión) sobre
  la ventana de las 6 ALERTAS. **Targeted a las fechas ALERTA + una muestra de RUTINA**
  (no 2 meses) → rápido (minutos). Audit pre-escrito: VRP por brazo vs ALERTAS MIROVA +
  **conteo de RUTINA inflada ESTRATIFICADO por NdC/Lascar/Lastarria** (los 3
  lbg_global_compatible, donde el riesgo de inflación se concentra — verificación
  adversarial S111). Criterio A66: noches MIROVA=0 → nuestro brazo <0.01 MW. Captura
  k_observed (Parte C). Si la inflación RUTINA aparece en el brazo ganador → mitigar con
  Q5 (fondo NTI) / Q6 (compacidad) o restringir el flag a vols sin lbg_global_compatible.
- R2 pixel-level + R3 + preview antes de adoptar. Si ningún brazo reproduce sin inflar →
  no adoptar, documentar (la señal puede estar bajo el límite de nuestra cuantificación).

## 4. MISSION (3 preguntas) — PASS 3/3
1. ¿Clon-literal MIROVA? SÍ — MIROVA reporta el Test1 integrado para "Muy Bajo"; lo perdemos.
2. ¿Drift real? SÍ — 0/6 ALERTAS reales capturadas (FN de reactivación temprana).
3. ¿Evidencia/papers? SÍ — Coppola 2015 Eq.1 (Test1) + Coppola 2024 Eq.16 + caso real + cruce.

## 5. Riesgos
- Inflar RUTINA → FP (mitigado por el criterio pre-registrado + filtros compacidad Q6).
- La calibración puede no generalizar entre volcanes (validar en Villarrica/Lastarria).
- A47: reproc secuencial por brazo, data_subdir aislado. A45: flags OFF hasta adoptar.

## 6. NO incluye (YAGNI)
- NO toca el path de detección del Test1 (triggered_*) — solo magnitud + source + el FN
  de detección como investigación.
- NO cambia la cuantificación de los regímenes Bajo/Medio/Alto (>0.5 MW) — solo Muy Bajo.
