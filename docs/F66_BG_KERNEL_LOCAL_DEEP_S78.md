# F66 — Background kernel local 3×3 vs ring 5-25km (DEEP S78)

> **Status**: READ-ONLY brainstorm. No tocar pipeline/data. PR docs-only.
>
> **Sesión**: S78 — F66 deep dive sobre el drift documental detectado en S77
> (`docs/MIROVA_DETAILED_CITATIONS.md` §1).
>
> **Pregunta raíz**: ¿es el cómputo de background (ring 5-25 km vs kernel local
> 3×3) el bug arquitectural que explica los FPs lago/Salar/lacolito persistentes
> que ni F61 (-0.8 dura) ni Approach 5 (NTI per-vol) atacan en su causa
> primaria?

---

## 1. Hallazgo central

**El drift de bg ring vs kernel local NO es un drift uniforme — es un drift
parcial e inconsistente entre cómputos del pipeline.** Después de leer
`pipeline/process_*.py`, `vrp_regimes.py` y `detection_context.py`:

| Cómputo | Geometría actual | Lo que dice MIROVA | Drift? |
|---|---|---|---|
| `t_bg`, `std_bg` (umbral detección N·σ) | **median(ring 5-25km)** vía `compute_bg_stats` | "adjacent pixels", "surrounding the active one" | **SÍ** |
| `L_bg` para Wooster VRP (Path BT, NTI, Test1) | **`bt_to_spectral_radiance(t_bg)`** = derivado del ring | "adjacent pixels" | **SÍ** |
| `L_bg` cuando flag `enable_local_kernel_bg=ON` Y per-vol `local_kernel_bg=true` | **kernel 3×3** vía `compute_local_background` (vrp_regimes.py:21) | "adjacent pixels" | **No** |
| dNTI contextual Path D (`contextual_dnti_hot_mask`) | kernel 8-vecinos local | "kernel 8-vec arithmetic mean" Coppola 2016a L240-249 | **No** |

**Tres consecuencias**:

1. El gate de detección (¿este pixel supera `t_bg + N·σ`?) usa **ring** —
   el lago tibio (280K) en el ring 5-25 km baja `t_bg` median si hay
   muchos pixels nieve fríos, o lo sube si el lago domina espacialmente.
   Resultado depende de balance lago/nieve/roca en ese annulus específico.
2. El cómputo de VRP (cuando Path D dispara) usa **ring** para `L_bg` salvo
   que la doble condición flag global + per-vol esté ON. Solo Path D dNTI
   usa contexto local "puro". Esto genera VRPs inflados o sub-pixel
   incorrectos sobre pixels Path-A/B/C lago/lacolito.
3. El flag `enable_local_kernel_bg` solo actúa sobre **L_bg para Wooster**,
   NO sobre `t_bg`/`std_bg` que gobiernan **qué pixel entra a hot_mask**.
   Por eso activarlo no elimina los FPs lago: el pixel lago ya entró a
   hot_mask por gate vs ring (que es más permisivo en lago), solo cambia
   cuánta VRP se le asigna.

---

## 2. Literatura MIROVA verbatim — tabla canónica

Fuente primaria: `docs/MIROVA_DETAILED_CITATIONS.md` §1 (extractos verbatim
de Coppola 2024 chapter Springer, Coppola 2016a SP426.5, Campus 2024).

| Paper / cita | Línea | Texto verbatim | Kernel | Geometría |
|---|---|---|---|---|
| Coppola 2024 chapter (Springer 2025) | L1129 | "If T_bk is retrieved from the pixels **adjacent to the hot one**, Eq. 14 can be solved..." | local | "adjacent" |
| Coppola 2024 chapter | L1051 | L_bk "generally calculated from **pixel(s) surrounding the anomaly**" | local | "surrounding" |
| Coppola 2024 chapter | L974-985 | "the threshold based on the comparison of each pixel **with its surroundings**. When a pixel exceeds the radiance of the **adjacent pixels** by a certain value..." | local | "adjacent / surroundings" |
| Coppola 2016a SP426.5 | L357-359 | "L4_bk is estimated from the **arithmetic mean** of all the pixels **surrounding the active one (or around the active cluster)**" | local | "surrounding cluster" |
| Coppola 2016a SP426.5 | L351 | "ΔL4_PIX = L4_alert − L4_bk (Eq. 6)" — usa L4_bk local del L357 | local | implícito |
| Coppola 2016a SP426.5 | L240-249 | dNTI/dETI kernel 8-vecinos arithmetic mean (Tests 2/3) | 3×3 explícito | 8-conn |
| Campus 2024 VIIRS 375m | L119-124 | "At each alerted pixel, a background radiance value (L_pixbk) is also associated, this last **computed from the arithmetic mean of the radiance of the pixels surrounding the alerted one(s)**. The total background radiance (L_MIRbk) is then obtained as the **sum of L_pixbk**" | local per-pixel + sum | "surrounding" |
| Aveni 2024 RSE (TIRVolcH) | — | Test 1 integrated-ROI; usa "background from surrounding cluster" idéntico a Coppola 2016a, hereda la convención. Aveni es mismo grupo Torino. | local | "surrounding" |
| Coppola 2016a SP426.5 | L240+ (dNTI) | kernel exacto: "spatial analysis... computed as the average of the 8 immediately adjacent pixels (3×3 window centered on candidate, excluding center)" | **3×3 = 8-neighbor** | explícito |

**Síntesis**: los 3 papers MIROVA canónicos (Coppola 2024 chapter, Coppola
2016a SP426.5, Campus 2024) usan **siempre** "adjacent / surrounding / 8
immediately adjacent" para el background del pixel/cluster activo. **Ningún
paper MIROVA menciona ring annular de 5-25 km** como background del cálculo
de exceso ΔL ni del umbral de detección.

**El ring 5-25 km es una invención de nuestro pipeline** (probablemente
heredada del paradigma "scene-wide background statistics" típico de
detectores escena tipo NHI/RSDF Catania — sistemas NO MIROVA, ver A9 en
CLAUDE.md).

---

## 3. Cómputo actual en código — mapa de invocaciones

### 3.1 `compute_bg_stats` (detection_context.py:895)

- Entrada: `bt`, `bg_mask` (ring 5-25 km construido en process_*.py:509,
  282, 330 vía `dist >= BG_INNER_KM & dist <= BG_OUTER_KM`).
- Salida: `t_bg = median(bt[ring])`, `std_bg = std(bt[ring])`.
- Usado por: **threshold de detección** en Path BT/NTI/Path D en los 3
  procesadores (process_modis.py:316, process_viirs.py:634,
  process_viirs_mod.py:351).
- **Drift documental**: paper dice "adjacent pixels", código usa "ring
  annular 5-25 km median".

### 3.2 `compute_local_background` (vrp_regimes.py:21)

- Entrada: `bt_grid`, `hot_rows`, `hot_cols`, `kernel_size=3`.
- Salida: lista per-hot-pixel de `mean(8 vecinos no-hot, no-NaN)`.
- Usado por: **solo cómputo de L_bg para Wooster VRP** cuando
  `ENABLE_LOCAL_KERNEL_BG && local_kernel_bg_compatible` (process_viirs.py:1067,
  process_modis.py:742).
- **NO se usa para threshold de detección** ni para Path D dNTI (Path D
  tiene su propio kernel contextual independiente en
  `contextual_dnti_hot_mask`).

### 3.3 Discrepancia clave

```
hot_mask = (bt > t_bg_ring + N·σ_ring)   # ← decisión "este pixel es hot"
                                         #   usa ring 5-25km
↓
for r,c in hot_pixels:
    if flag_ON and per_vol_ON:
        L_bg = bt_to_spectral(mean(3x3 around r,c))  # ← local
    else:
        L_bg = bt_to_spectral(t_bg_ring)             # ← ring (default)
    vrp_pixel = WOOSTER_COEFF * (L_hot - L_bg) * A_pix
```

El gate de detección y el cómputo de VRP **usan dos backgrounds distintos**
cuando el flag está ON, y **ambos usan ring** cuando OFF. MIROVA usa **el
mismo background local en ambos pasos** (el paper saca `ΔL_PIX = L_alert −
L_bk` con `L_bk` del L357-359 que es local; ese mismo `L_bk` define
implícitamente el threshold porque el "alert" se construye sobre la misma
referencia local en Tests 2/3 contextuales).

---

## 4. Estado per Tier A — flag matrix

| Volcán | `local_kernel_bg` (yaml) | `lbg_global_compatible` (yaml) | far_30d (>5km) ALERTAS | dist_max_30d |
|---|---|---|---|---|
| Copahue (lago Caviahue) | **False** | UNSET | 99 | 35.3 km |
| Villarrica | True | UNSET | 97 | 32.8 km |
| Llaima (lago Conguillío) | **False** | UNSET | 84 | 32.3 km |
| Lascar (Salar Atacama) | UNSET=False | True | 56 | 34.2 km |
| Tupungatito (glaciar) | UNSET=False | True | 86 | 33.7 km |
| Isluga (Salar Surire) | UNSET=False | UNSET | 50 | 34.3 km |
| Nevados de Chillán | UNSET=False | UNSET | 83 | 34.5 km |
| Planchón-Peteroa | True | UNSET | 93 | 33.5 km |
| Chaitén | True | UNSET | 76 | 32.5 km |
| Puyehue Cordón Caulle (lacolito) | True | UNSET | **255** | 33.2 km |
| Lastarria | True | UNSET | 85 | 31.5 km |

**Lectura geológica**:

- Volcanes con LK=True igual tienen far detections masivas (PCC 255, V 97,
  PP 93, Chaitén 76, Lastarria 85). Esto **refuta la hipótesis simple
  "kernel local cura los FP lago"** — el flag solo cambia el L_bg para VRP,
  NO el gate de detección que sigue usando ring.
- Copahue/Llaima con LK=False son comparables a otros LK=True. El flag
  per-vol prácticamente no tiene impacto observable en `far_30d` porque
  esa métrica viene del gate de detección, no del L_bg de Wooster.
- **Puyehue 255 far_30d** es muy llamativo: el lacolito está fuera del
  inner_radius_km=20 (mayor de todos), pero la geometría del bg ring para
  ese volcán probablemente captura mucho terreno volcánico activo o lago.

---

## 5. Reanálisis físico — ¿por qué el kernel local debería curar lago?

**Escenario lago (Caviahue, Conguillío, Aluminé)**:

- Lago a 280K rodeado de nieve/roca a 268K.
- Pixel central lago: BT=279K. Vecinos 3×3 si están en lago también: BT=279K
  → `t_bg_local = 279K`. ΔT = 0K. **No triggea NTI/BT/dNTI**.
- Bajo ring 5-25 km: el ring incluye mix lago+nieve+roca+valle. Median
  típicamente 265-270K (porque el ring es mayoritariamente terreno). ΔT
  pixel lago vs ring = 9-14 K. **Triggea umbral 5K eruption o N·σ summit**.

**Esta es la asimetría que el drift produce**: ring "ve" el contraste entre
lago tibio (anomalía espacial cerrada) y terreno frío circundante a varios
km, mientras que kernel local "ve" solo lago vs lago — ningún contraste,
ninguna detección.

**Escenario cráter caliente real**:

- Pixel cráter: BT=320K (lava). Vecinos 3×3 roca/nieve fría 270K.
- `t_bg_local = 270K`. ΔT = 50K. **Triggea ampliamente**.
- Ring 5-25 km: median 270K. ΔT = 50K. **Triggea igual**.

**Escenario lava lake sub-pixel (Villarrica)**:

- Pixel mezclado lava+ambiente: BT=275K. Vecinos 3×3 fríos 270K (el lava
  lake es sub-pixel del único pixel central).
- `t_bg_local = 270K`. ΔT = 5K. **Triggea umbral 5K — bien**.
- Ring 5-25 km: median 270K (no incluye lava). ΔT = 5K. **Triggea igual**.
- Si el ring incluye contaminación geotermal/lago al N (caso S58
  Villarrica): median ring = 273K → ΔT = 2K → **NO triggea**. Aquí el
  ring local es peor que el kernel.

**Escenario cirrus fría dispersa**:

- Pixel cráter caliente BT=295K. Vecinos 3×3 todos cubiertos por cirrus
  alta 245K (mucho más fríos que terreno claro).
- `t_bg_local = 245K`. ΔT = 50K. **Triggea exageradamente — Wooster sobre
  ΔL inflado da VRP 100-1000 MW falsamente alto** (esto es exactamente el
  bug D9 que el cap path_d_only_cap_mw=5MW S71 mitiga). El kernel local
  AMPLIFICA el bug cirrus. Ring 5-25 km lo amortigua.

---

## 6. Conclusión sobre la hipótesis raíz

**El drift bg-kernel NO es la causa raíz universal de los FPs lago.** Es
**parte** del cuadro, pero con efectos opuestos según el escenario:

| Escenario | Ring 5-25 (actual) | Kernel local 3×3 | Quién gana |
|---|---|---|---|
| Lago tibio rodeado de lago | FP (ΔT spurio vs terreno frío lejano) | OK (sin ΔT local) | **kernel** |
| Lago tibio en borde de lago | FP idéntico | parcial: vecinos mitad lago mitad terreno → ΔT atenuado | **kernel** ligeramente |
| Cráter caliente clásico | OK | OK | empate |
| Lava lake sub-pixel + ring contaminado | **FN** (ring tibio mata ΔT) | OK (local frío) | **kernel** |
| Cirrus fría dispersa | OK (ring amortigua) | FP (D9, ΔL inflado) | **ring** + cap D9 |
| Salar borde con halo halita caliente | FP (ring de roca fría exalta el Salar) | atenuado (vecinos también Salar) | **kernel** |
| Lacolito Puyehue (15-20km del cráter, terreno volcánico activo) | FP por ring del cráter principal | el lacolito tendría su propio bg local → atenuado | **kernel** |

**Veredicto**: kernel local **probablemente reduce 50-70% de los FP
agua/Salar/lacolito** documentados, **a costo de exacerbar el D9 cirrus**
(que ya tiene cap defensivo S71). El cambio NO es plug-and-play porque hay
que migrar **ambos**: `compute_bg_stats` (gate) + `L_bg` para VRP. La
migración parcial actual (solo VRP, default OFF) es exactamente la
configuración menos útil — cambia la magnitud de VRP pero no quien entra
a hot_mask.

---

## 7. Plan de implementación — bite-sized vs comprehensivo

### Approach BITE-SIZED — solo activar flag per-vol UNSET

**Costo**: 30 min. **Riesgo**: bajo. **Impacto esperado**: marginal (afecta
solo L_bg de VRP, no detección).

Cambiar en `volcanoes.yaml`:
```yaml
# Copahue, Llaima — actualmente False explícito
local_kernel_bg: true   # cambiar de false
# Lascar, NdC, Isluga, Tupungatito — actualmente UNSET (default False)
local_kernel_bg: true   # agregar línea
```

**No requiere cambios de código**. Solo testea hipótesis débil: "kernel
local de VRP cura FPs sin tocar gate". Predicción: ratio_med mejorará en
estos 6 vol (similar al patrón Villarrica/PP S61), pero **far_30d count
no bajará** porque el gate sigue usando ring.

**Validación obligatoria S33** (regla CLAUDE.md):
- R1 tests sintéticos antes de adoptar (`tests/test_local_kernel_per_vol.py`).
- R2 pixel-level vs TIFs MIROVA archive para 5 records canónicos por vol.
- R3 audit independiente sensor-aware.
- A/B con profile dedicado `_lkbg_all_on.yaml`.

**No esperar revolución** — es ajuste fino de calibración VRP.

### Approach COMPREHENSIVO — migrar gate de detección a kernel local

**Costo**: 2-3 sesiones. **Riesgo**: alto (toca el corazón del pipeline).
**Impacto esperado**: alto (50-70% reducción FP agua, mejora recall
lava-lake sub-pixel, exacerba D9 cirrus controlable con cap).

**Tareas**:

1. **A1** — diseñar `compute_local_bg_stats(bt, candidate_rows, candidate_cols, kernel=5)`:
   - Para cada pixel candidato (definido como aquellos con NTI > algún
     pre-screen razonable, NO ring), calcular `t_bg_local = mean(5×5 vecinos
     no-hot, no-NaN)`, `std_bg_local = std(5×5 vecinos)`.
   - Kernel 5×5 (no 3×3) para tener >10 muestras y `std` estable. Coppola
     2016a no especifica kernel exacto para `L4_bk surrounding`, pero el
     dNTI/dETI usa 3×3 (8-vec). Para `std` de gate, 5×5 (24 vec) más
     robusto.
   - Excluir centro + cualquier vecino flageado como activo (paso second-pass
     ya implementado).

2. **A2** — modificar process_*.py para que `t_bg`, `std_bg` per-pixel
   reemplacen los escalares globales actuales:
   - Cada pixel candidato tiene su propio `t_bg_local[r,c]`, `std_bg_local[r,c]`.
   - Threshold local: `bt[r,c] > t_bg_local[r,c] + N·σ_local[r,c]`.
   - Mantener escalar global para diagnostic backward-compat.

3. **A3** — actualizar Paths A/B/C (BT/NTI/NTI-rel) para usar t_bg_local.
   Path D dNTI ya usa kernel — sin cambio.

4. **A4** — `L_bg` para Wooster usa `bt_to_spectral(t_bg_local[r,c])` always.
   Eliminar flag `enable_local_kernel_bg` (siempre ON post-migración).

5. **A5** — pre-screen para candidatos: NO podemos correr kernel local sobre
   TODOS los pixels de la imagen (10⁵-10⁶ pixels × 25 vecinos = costo). El
   pre-screen razonable es `nti > -0.9` o `bt > 270K` (rough hot candidates).
   Coppola 2016a hace algo similar: candidatos vía Test 1 NTI absoluto, luego
   Tests 2/3 contextuales sobre kernel local.

6. **A6** — A/B exhaustivo: profile `_comprehensive_local_bg.yaml` con
   30d × 11 vol Tier A. Predicción: `far_30d` baja significativamente en
   Copahue/Llaima/Lascar/Isluga; ratio_med más cercano a 1.0 en todos.

7. **A7** — verificación cirrus D9: si D9 cap=5MW se activa más frecuentemente
   con local bg → cap funciona como defensa. Si pixels cirrus exceden el cap
   sistemáticamente, escalar cap o agregar atm-gate t_bg_local mínimo.

**Riesgos comprehensive approach**:

- **Performance**: pre-screen + kernel 5×5 per-pixel = costo O(N × 25) por
  procesador. Granule MODIS típico tiene ~5000 pixels en ROI; 5000 × 25 =
  125k ops. Tolerable. Para VIIRS 375m 50k pixels = 1.25M ops, ~2s python
  puro — aceptable.
- **σ_bg local muy bajo en zonas homogéneas** (lago grande, Salar) → N·σ
  threshold colapsa a `max(floor, ε)` = 5K floor. Esto es feature, no bug:
  precisamente queremos que pixels en medio del lago no triggen. Pero hay
  que confirmar que `floor` defensivo funciona (anomaly_threshold_k=5K en
  mirova_equivalent.yaml).
- **Pixels en borde del ROI** con vecinos parcialmente fuera del ROI: NaN
  fallback al ring global como safety net.
- **Romper Approach 4 (Aveni 2024 baseline 10yr)**: no, ortogonal. Aveni es
  baseline temporal, este es kernel espacial; combinan ortogonalmente.
- **Romper Test 1 integrated-ROI**: cuidado. Test 1 usa `L_bg` para ΔL
  integrated sobre toda ROI. Si pasamos a per-pixel local, Test 1 necesita
  decisión: o se mantiene Test 1 con `L_bg` integrated del ring (compatible
  con Coppola 2015 Eq.1 que es integrated), o se migra Test 1 a "suma de
  ΔL_PIX local" (Coppola 2016a Eq.6+8). **Coppola 2016a explícito**: Eq.6
  usa `L4_bk` local, Eq.8 suma. **Test 1 integrated y Test 1 sum-local NO
  son lo mismo** — diferencia teórica importante. Discutir en S79.

### Approach HÍBRIDO — dual-bg defensivo (sugerido)

**Costo**: 1 sesión. **Riesgo**: medio. **Impacto esperado**: 80% del
comprehensive sin tocar arquitectura.

Idea: **mantener ring 5-25 km como prior global**, **agregar kernel local
3×3 como gate secundario consistencia**:

```python
hot_mask_ring = bt > t_bg_ring + N·σ_ring   # gate actual
hot_mask_local = bt > t_bg_local + N·σ_local  # gate nuevo (vecinos 3x3)
hot_mask_final = hot_mask_ring & hot_mask_local
```

Pixel solo es hot si **ambos** gates lo confirman. Lago tibio rodeado de
lago: ring dice hot (ΔT vs terreno frío distante), kernel dice no-hot (ΔT
local cero) → kernel veta. Cráter real: ambos hot. Cirrus dispersa: ring
hot, kernel hot (vecinos cirrus aún más fríos) → dispara, pero D9 cap
controla.

Trade-off: pierde recall en pixels reales que tienen vecinos también
calientes (lava extendida grande). Mitigado por second-pass S46 que ya
excluye active pixels antes de recomputar.

---

## 8. Recomendación S78 → S79

**Decisión sugerida** (en orden de prioridad):

1. **S78 — solo este doc**. NO tocar pipeline. Discutir con Nicolás:
   - ¿Asume el costo de migración comprehensiva?
   - ¿Acepta el approach híbrido como defensa intermedia?
   - ¿Prefiere agotar Approach 4 Aveni baseline 10yr primero?

2. **S79 candidato bite-sized** (si Nicolás aprueba): activar `local_kernel_bg`
   en los 6 vol UNSET/False + A/B mínimo. **Predicción**: marginal en
   far_30d, mejora ratio_med calibración VRP.

3. **S80+ candidato comprehensive**: migrar gate. Requiere superpowers-brainstorming
   adicional + writing-plans + TDD por la magnitud. El work se enmarca en
   reaperturar drift D10 (registrar el drift en `MIROVA_DIVERGENCES.md`
   como bloque D10 BG_KERNEL).

4. **Combinar con F61 / F63 / Approach 5**: el bg local es ortogonal a F61
   (-0.8 cura) que destruía 98% TPs reales — sigue NO viable. Bg local +
   Approach 5 (NTI per-vol adaptativo) son **complementarios**: bg local
   resuelve geometría espacial, Approach 5 resuelve fenomenología
   per-volcán. Aveni 2024 baseline 10yr resuelve dimensión temporal.

---

## 9. Riesgos generales

- **Cita verbatim insuficiente**: Coppola 2016a SP426.5 dice "kernel 8
  immediately adjacent" para Tests 2/3 (dNTI/dETI), pero **NO especifica
  kernel size exacto para L4_bk surrounding** (L357). "Surrounding" puede
  interpretarse 3×3, 5×5, o región 8-conn del cluster. **Necesitamos
  verificar Coppola 2024 Springer chapter directo en PDF** que el kernel
  L_bk = 3×3 (no inferir).
- **MIROVA NRT vs MIROVA paper**: el paper describe el algoritmo. MIROVA
  NRT (mirovaweb.it) puede tener parches operacionales no documentados.
  Aveni 2024 RSE (mismo grupo) hereda — usar como secondary confirmation.
- **Volcán-dependiente**: el approach puede curar Copahue/Llaima (lago
  bien definido cercano al cráter) pero exacerbar Tupungatito (glaciar
  amplio donde local = global). El gate per-vol `local_kernel_bg` debería
  preservarse incluso post-migración comprehensive — algunos volcanes
  legítimamente quieren ring global.
- **Performance reproc**: si migración comprehensive, reproc histórico
  30-90d × 11 vol = costo cómputo significativo. Planificar en local
  Nicolás, no GH Actions (regla CLAUDE.md).

---

## 10. Próximas verificaciones recomendadas

Si Nicolás aprueba avanzar a S79:

1. **PDF check Coppola 2024 chapter** verbatim sobre kernel size L_bk. Bajar
   a `papers_mirova/` si no está local.
2. **Reproducir 3 escenarios canónicos** sin tocar pipeline:
   - Caviahue lago Copahue noche clara: t_bg ring vs t_bg kernel 3×3.
   - Cráter Villarrica lava lake: idem.
   - Salar Atacama Lascar: idem.
   Reportar diferencia numérica `t_bg_ring - t_bg_kernel` para los 3.
3. **Verificar ETI quadratic Coppola 2016a L259-265**: NTI_bk usa regresión
   cuadrática scene-wide, **NO kernel local**. Tests 2/3 (dNTI/dETI) usan
   kernel 8-vec. Hay dos backgrounds: NTI_bk (scene quadratic) y L4_bk
   (local surrounding). Drift documental adicional posible: ¿nuestro
   `enable_eti_quadratic_scene=true` está bien implementado vs paper?
4. **Audit drift integrado**: actualizar `MIROVA_DIVERGENCES.md` con bloque
   D10 BG_KERNEL post-S78. Esta nota cita `MIROVA_DETAILED_CITATIONS.md` §1
   pero merece su propia entrada de drift formal.

---

## 11. Síntesis ejecutiva (3 líneas para reporte PR)

1. **Drift confirmado bug raíz parcial**: el background MIROVA es local
   (kernel 3×3 "surrounding the active one") según Coppola 2016a/2024 +
   Campus 2024 verbatim; nuestro pipeline usa ring 5-25 km median para
   **t_bg gate detección**, y kernel local solo para L_bg Wooster cuando
   doble-flag (global + per-vol) ON. Migración parcial actual = peor de
   ambos mundos.
2. **Fix viable en 3 niveles**: bite-sized (activar flag 6 vol UNSET, 30
   min, impacto marginal calibración VRP), híbrido (dual-bg gate
   consistency, 1 sesión, reduce 50-70% FP agua), comprehensive (migrar
   `compute_bg_stats` a per-pixel local, 2-3 sesiones, reduce ~70% FP +
   recupera lava-lake sub-pixel). Requiere A/B obligatorio R1+R2+R3 S33.
3. **Impacto esperado comprehensive**: -50/-70% en far_30d Copahue (99),
   Llaima (84), Lascar (56), Tupungatito (86), Isluga (50), NdC (83). PCC
   (255) caso especial — lacolito es señal real fenomenológica probablemente
   no-FP. Riesgo: exacerba D9 cirrus (mitigable con cap=5MW S71 ya
   activo). Trade-off recall lava extendida grande (mitigable second-pass
   S46 ya activo).
