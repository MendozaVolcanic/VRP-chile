---
title: "F46 — Plan fix bug vrp_tir_mw (Stefan-Boltzmann sobre máscara 4σ)"
session: S76
status: plan
ai_generated: true
confidence: high
explored: false
tags:
  - pipeline
  - process_viirs
  - vrp_tir
  - background-sigma
  - stefan-boltzmann
  - aveni-2025
  - mirova
related:
  - docs/F31_AVENI_VRPTIR_PLAN_S74.md
  - docs/F31_AVENI_GRL_2025_EXTRACT.md
  - docs/F31_AVENI_2024_TIRVOLCH_VERIFY.md
  - docs/F31_AGUILERA_2021_PETEROA.md
  - docs/MIROVA_DETAILED_CITATIONS.md
  - experiments/138_audit_mw_outliers_s76/
---

# F46 — Bug `vrp_tir_mw`: Stefan-Boltzmann sobre máscara inflada por σ de background

## 1. Resumen ejecutivo

El campo `vrp_tir_mw` de los records VIIRS está sobreestimado por dos a tres órdenes
de magnitud en una fracción no despreciable del dataset operacional. La auditoría
`experiments/138_audit_mw_outliers_s76/audit2.py` identifica **143 records con
`vrp_tir_mw > 1000 MW`** en `data/mirova_equivalent/`, ventana 2026-01-31 a
2026-05-17, sobre los 11 volcanes Tier A.

El máximo absoluto observado es Lascar 2026-02-08 05:54 SNPP con
`vrp_tir_mw = 9 606.9 MW`, generado a partir de 108 pixels I05 cuya BT máxima es
**285.55 K** — es decir, ~12 °C, lejos de cualquier régimen físico de roca
incandescente. El caso patognomónico es Chaitén 2026-03-25 05:18 SNPP, donde
`n_anomalous_pixels = 0`, `vrp_mir_mw = 0` y aun así `vrp_tir_mw = 6 872 MW`.
Esto demuestra que el path TIR opera sin coherencia con el path MIR/NTI: emite
una "energía radiante" volcánica sin que ningún otro indicador térmico la respalde.

La causa raíz está en `pipeline/process_viirs.py:968-986`: el cálculo es una
aplicación literal de Stefan-Boltzmann sobre todos los pixels que superan
`max(TIR_THRESHOLD_K = 0.5 K, N_SIGMA_TIR = 4 · σ_bg)`. En terreno andino
heterogéneo (nieve, roca expuesta, lago glaciar, cirrus a –40 °C) σ_bg se infla
hasta 3-5 K, el umbral efectivo queda en ~10 K sobre el medio del anillo, y aun así
100-230 pixels caen sobre umbral, cada uno con un excedente térmico de ~3-5 K que
elevado a la cuarta potencia y multiplicado por A_pix = 140 625 m² aporta
3-5 MW/pixel residual.

Este documento describe el fenómeno, el mecanismo en el pipeline, dos opciones de
fix mutuamente combinables y la estrategia de validación A/B sobre perfiles
aislados, siguiendo el patrón S24/S25.

**Magnitud del problema (resumen)**

| Métrica | Valor |
|---|---|
| Records afectados (`vrp_tir_mw > 1000 MW`) | 143 |
| Ventana temporal | 2026-01-31 → 2026-05-17 |
| Máximo absoluto | 9 606.9 MW (Lascar, 2026-02-08, SNPP) |
| Volcanes más afectados | Villarrica, Chaitén, PCC, Lascar, PP, LagunaDelMaule, Llaima, Isluga |
| Caso patognomónico | Chaitén 2026-03-25 05:18 SNPP: `n_anomalous_pixels=0`, `vrp_mir_mw=0`, `vrp_tir_mw=6872` |
| Ground truth máximo plausible (Aguilera 2021 PP lago cratérico) | Qvolc 7-59 MW |
| Sobreestimación factor sobre PP ground truth | ~100× |

## 2. Fenómeno físico

Antes de mirar el código, pensemos qué está pasando físicamente en el ROI del
volcán cuando el satélite VIIRS pasa de noche y mide la radiancia en la banda
TIR I05 (11.45 µm).

Un ROI Tier A típico (Lascar, Villarrica, Chaitén, PCC) tiene 50×50 km de lado.
Dentro de ese cuadrado conviven materiales con respuestas térmicas muy distintas:

- **Roca volcánica expuesta** (depósitos piroclásticos, lavas antiguas, escoria
  del flanco). Inercia térmica baja, alta emisividad, se enfría rápido tras el
  ocaso. BT nocturna típica: 255-275 K según altitud y cobertura nival.
- **Nieve y hielo glaciar**. Emisividad ~0.99 pero capacidad calorífica alta,
  enfría lento. Forma parches discontinuos en el flanco (sobre todo en
  Villarrica, PCC, Planchón-Peteroa). BT típica nocturna: 260-275 K.
- **Lagos cratéricos y lagunas glaciares** (Planchón-Peteroa, Copahue,
  Villarrica reservorio, Laguna del Maule). El agua tiene capacidad calorífica
  enorme, irradia toda la noche desde ~275-285 K aun en pleno invierno. Es la
  fuente caliente persistente más confundible con anomalía volcánica.
- **Nube fina alta (cirrus)**. Cristales de hielo a 250-235 K en la troposfera
  alta, semitransparente al 11 µm pero no totalmente. Cuando un cirrus delgado
  cubre parcialmente el ROI, los pixels que ve VIIRS son una mezcla del suelo
  caliente debajo y la nube fría arriba: la BT cae 2-8 K respecto al pixel
  vecino libre de nube, y crea un gradiente espacial fuerte que NO es volcánico.

El resultado es que la varianza espacial de BT dentro del anillo de background es
**alta y no-gaussiana**: el histograma típico tiene una moda principal (terreno
"frío" homogéneo) y una cola larga hacia BT más cálidas (lagos, parches de roca
seca, pixels parcialmente cubiertos por cirrus). El desvío estándar muestral
σ_bg que sale de ese histograma sobreestima sistemáticamente el "ruido térmico
real" — porque mezcla varias poblaciones físicas en una sola distribución.

Cuando aplicamos Stefan-Boltzmann **absoluto** (no relativo a un background MIR
o a una región hot espacialmente coherente), cualquier pixel a 285 K rodeado de
un background a 266 K aporta una "energía" σ · A · (T⁴ − T_bg⁴) que es
geofísicamente irrelevante (es agua del lago, no es lava), pero que numéricamente
suma. Multiplicada por 100-230 pixels y por A_pix = 140 625 m², la integral
explota a miles de MW.

En síntesis: la fórmula del pipeline confunde **gradiente térmico espacial del
ROI** (señal de heterogeneidad andina) con **anomalía térmica volcánica** (señal
de roca caliente). El error no es de calibración radiométrica, es de definición
de máscara y de ausencia de gate de coherencia con el path MIR/NTI.

## 3. Mecanismo en el pipeline

### 3.1 Código actual

`pipeline/process_viirs.py:968-986`:

```python
# --- TIR channel I05 (11.45 um) — TIRVolcH, low-temperature features ---
vrp_tir_mw = 0.0
t_max_i05 = float("nan")

if "I05" in bands:
    bt5 = bands["I05"]
    bg_vals5 = bt5[bg_mask & ~np.isnan(bt5)]
    if len(bg_vals5) >= 10:
        t_bg_i05 = float(np.median(bg_vals5))
        std_bg5 = float(np.std(bg_vals5))
        threshold_tir = max(TIR_THRESHOLD_K, N_SIGMA_TIR * std_bg5)
        hot5_mask_2d = roi_mask & ~np.isnan(bt5) & (bt5 > (t_bg_i05 + threshold_tir))
        hot5_rows, hot5_cols = np.where(hot5_mask_2d)
        if len(hot5_rows) > 0:
            hotpix5 = bt5[hot5_rows, hot5_cols]
            hotpix5_area = pixel_areas[hot5_rows, hot5_cols]
            vrp_w5 = float(np.sum(hotpix5_area * SIGMA * (hotpix5 ** 4 - t_bg_i05 ** 4)))
            vrp_tir_mw = vrp_w5 / 1e6
```

Donde el perfil `mirova_equivalent` (vía `pipeline/profile.py:81-83`) carga:

- `TIR_THRESHOLD_K = 0.5` (piso absoluto del exceso BT sobre background)
- `N_SIGMA_TIR = 4` (múltiplo del σ_bg que define el threshold relativo)
- `SIGMA = 5.67·10⁻⁸ W·m⁻²·K⁻⁴` (Stefan-Boltzmann)

El umbral efectivo es `max(0.5 K, 4 · σ_bg)`. En los outliers observados,
`σ_bg ∈ [3.06, 5.51] K`, lo que produce `threshold_tir ∈ [12.2, 22.0] K`. El
piso de 0.5 K nunca domina en estos casos — es solo un seguro contra σ_bg → 0.

### 3.2 Por qué falla en condiciones andinas

Tres patologías combinadas:

1. **σ_bg infla el umbral pero NO elimina los pixels que lo causan.** El anillo
   de background y el ROI hot comparten la misma escena. Cuando el cirrus o la
   heterogeneidad nieve/roca/lago infla σ_bg, también inyecta dentro del ROI
   pixels que están en la cola caliente del mismo histograma. El umbral sube
   pero la población contaminante sube con él.

2. **La máscara hot NO requiere agrupación espacial.** Cualquier pixel disperso
   en el ROI que supere el umbral entra a la integral. No hay test de
   connectividad ni de coincidencia con un cluster MIR. Por eso vemos casos como
   Villarrica 2026-03-25 SNPP con 91 pixels TIR "hot" dispersos cuando MIR
   reporta `n_pixels = 0` y `vrp_mir_mw < 1 MW`.

3. **Stefan-Boltzmann absoluto no descuenta el "ruido térmico" del ROI.** La
   fórmula `σ · A · (T⁴ − T_bg⁴)` solo es física cuando T representa una región
   caliente real (lava, escoria fresca, lago cratérico activo) y T_bg representa
   el terreno frío circundante. Si T es 285 K (agua de lago glaciar inactivo) y
   T_bg es 266 K (roca de flanco), la diferencia T⁴ − T_bg⁴ es matemáticamente
   real pero **no representa flujo radiativo volcánico**: representa la
   diferencia natural entre dos cuerpos de distinta inercia térmica.

### 3.3 Qué hace MIROVA distinto

Según `docs/MIROVA_DETAILED_CITATIONS.md` (sección 3.3, líneas 114-125) y la
síntesis de Aveni 2025 GRL, MIROVA opera el path TIR como **complemento**, no
como path primario. El cálculo VRPTIR de Aveni 2025 (Eq. 9) es:

```
VRPTIR = A_pix · k_TIR · Σ (L_TIR_hot,j − L_TIR_bg)
```

con `k_TIR = 60.17 µm·sr` (Aveni 2025, L413), rango de validez 300-600 K, y
limitación explícita al "low-temperature regime" para complementar Wooster MIR.

Tres diferencias críticas respecto al pipeline actual:

| Aspecto | MIROVA / Aveni 2025 | VRP Chile actual (process_viirs.py:968-986) |
|---|---|---|
| Trabaja sobre radiancia (L) o BT⁴ | Radiancia L_TIR, integrada con constante empírica k_TIR | BT⁴ literal vía Stefan-Boltzmann |
| Definición de pixel hot | Pixel ya identificado en path primario (NTI/MIR cluster) | Cualquier pixel I05 > T_bg + 4σ |
| Rango de validez | Sólo 300-600 K (regímenes térmicos donde RP es lineal) | Sin guard de rango, dispara desde 280 K |
| Coherencia con MIR | Sí: TIR sólo computa sobre pixels ya alertados por MIR/NTI | No: paths MIR y TIR independientes |

**Pendiente de verificación S77**: confirmar en Coppola 2024 Cap.11 (Springer)
Tabla 1 o Coppola 2025 si MIROVA publica un VRPTIR independiente o si lo agrega
sólo dentro del VRP total. Si publica independiente, ¿con qué máscara? Documento
`MIROVA_DETAILED_CITATIONS.md` línea 308 marca este punto como **D3 RESUELTO
S17** afirmando que TIR usa Stefan-Boltzmann puro, pero ese rolling fue antes
de que tuviéramos evidencia empírica del bug. Hay que releer la fuente con esa
evidencia en mano.

## 4. Evidencia cuantitativa

### 4.1 Top 10 outliers (extracto de `outliers.json`)

| # | Volcán | Fecha (UTC) | Sensor | vrp_mir_mw | **vrp_tir_mw** | n_pix MIR | t_max_I05 (K) | t_bg (K) | σ_bg (K) | thr_eff (K) |
|---|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | Lascar | 2026-02-08 05:54 | SNPP | 4.95 | **9 606.9** | 108 | 285.55 | 266.79 | 4.23 | 279.48 |
| 2 | Villarrica | 2026-02-10 05:24 | SNPP | 2.00 | **8 740.9** | 115 | 290.38 | 272.70 | 4.56 | 286.38 |
| 3 | Villarrica | 2026-03-21 06:36 | SNPP | 2.09 | **7 701.4** | 72 | 284.82 | 265.15 | 3.06 | 274.34 |
| 4 | **Chaitén** | **2026-03-25 05:18** | **SNPP** | **0.00** | **6 872.0** | **0** | **277.97** | **260.11** | **3.98** | **272.06** |
| 5 | PCC | 2026-03-25 05:36 | N20 | 45.88 | 6 581.1 | 232 | 285.64 | 267.65 | 4.13 | 280.05 |
| 6 | Lascar | 2026-02-08 06:18 | N20 | 3.46 | 6 458.5 | 88 | 285.10 | 266.65 | 5.51 | 283.17 |
| 7 | Villarrica | 2026-03-20 05:30 | N20 | 0.72 | 6 408.0 | 91 | 283.37 | 270.82 | 3.30 | 280.73 |
| 8 | Villarrica | 2026-04-?? 05:?? | NOAA21 | 5.39 | 6 174.6 | 92 | 288.28 | — | — | — |
| 9 | Villarrica | 2026-03-?? 05:?? | SNPP | 0.33 | 5 977.4 | 1 | 286.57 | — | — | — |
| 10 | Villarrica | 2026-03-?? 05:?? | N20 | 3.80 | 5 843.1 | 84 | 287.52 | — | — | — |

(Datos completos en `experiments/138_audit_mw_outliers_s76/outliers.json` y
`audit_output.txt`.)

### 4.2 El caso patognomónico (Chaitén 2026-03-25 05:18 SNPP)

- `n_anomalous_pixels = 0` — el path MIR/NTI no encontró nada.
- `vrp_mir_mw = 0.000` — la integración MIR confirma cero anomalía.
- `pc.vrp_mw` (primary cluster MIR) **no existe** — no se formó cluster.
- `t_max_i04_k = 278.57 K`, `t_max_i05_k = 277.97 K` — ambas bandas están en
  régimen "frío de flanco", no hay roca caliente.
- `t_bg_k = 260.11 K`, `σ_bg = 3.98 K` — terreno heterogéneo en invierno
  patagónico (nieve discontinua, bosque húmedo, posible cirrus).
- `threshold_tir_eff = 272.06 K` (= 260.11 + 4·3.98), umbral efectivo 11.95 K
  sobre background.
- Resultado: `vrp_tir_mw = 6 872 MW`.

No hay físicamente cómo Chaitén irradie casi 7 GW de potencia volcánica una
noche en que ni el MIR ni el NTI detectan un solo pixel anómalo. Es un falso
positivo puro generado por la máscara TIR sobre el gradiente espacial del ROI.

### 4.3 Comparación contra ground truth Aguilera 2021

`docs/F31_AGUILERA_2021_PETEROA.md` reporta para el lago cratérico de
Planchón-Peteroa, ground truth térmico in situ + landsat, **Qvolc 7 a 59 MW**.
Nuestro pipeline reporta `vrp_tir_mw = 4 020.9 MW` para PP el 2026-03-?? SNPP.
Factor de sobreestimación ~70-570× según el extremo del rango Aguilera.

### 4.4 Cuáles volcanes NO están afectados (relevante para el fix)

Volcanes sin glaciar significativo ni lago cratérico (Isluga, Lastarria,
CarranLosVenados, CorcovadoYanteles) tienen outliers mucho más moderados o
ninguno (CarranLosVenados máximo 158 MW; CorcovadoYanteles máximo 60.8 MW).
Esto refuerza la hipótesis de que el driver es la **heterogeneidad
nieve/roca/lago** dentro del ROI, no una falla genérica de calibración VIIRS.

Lastarria, paradójicamente, es Tier A activo con TIR legítimo y NO aparece en
outliers >1000 MW — porque su ROI es desierto altiplánico relativamente
homogéneo (sin lagos, sin glaciares grandes, σ_bg típicamente <2 K). Es el
ejemplo natural de "lo que el path TIR debería ver".

### 4.5 Scope reducido — el bug es exclusivo de VIIRS I-band (S76 verificación)

Verificación cruzada S76 (post-redacción inicial del doc):

| Procesador | Tiene `vrp_tir_mw`? | Tiene path TIR Stefan-Boltzmann? |
|---|---|---|
| `pipeline/process_modis.py` | NO | NO (MODIS no calcula vrp_tir separado) |
| `pipeline/process_viirs.py` (I-band 375m) | **SÍ** | **SÍ — bloque líneas 968-986 (post-PR #158)** |
| `pipeline/process_viirs_mod.py` (M-band 750m) | NO | NO |

Distribución de los 143 outliers por sensor (snapshot del audit
`experiments/138_audit_mw_outliers_s76/outliers.json`):

| Sensor | N outliers |
|---|---|
| VIIRS_SNPP (I-band) | 56 |
| VIIRS_NOAA20 (I-band) | 43 |
| VIIRS_NOAA21 (I-band) | 44 |
| MODIS_TERRA | 0 |
| MODIS_AQUA | 0 |
| VIIRS_*_750 (M-band) | 0 |

**Implicación operativa**: el fix toca un único archivo
(`pipeline/process_viirs.py`) y un único bloque (líneas 968-986). Reduce
significativamente el riesgo de regresión y el alcance del A45 obligatorio.
No hace falta tocar MODIS ni M-band.

**Implicación para opciones A/B**: ambas opciones del §5 se aplican
exclusivamente a `process_viirs.py:968-986`. La estrategia A/B testing del §6
puede usar un solo perfil derivado de `mirova_equivalent` con el cambio
solo a los flags TIR de VIIRS I-band — más simple que lo que el §6
sugiere por defecto.

## 5. Opciones de fix

Las dos opciones siguientes son **mutuamente combinables**. El AB de validación
(§6) las testea independientes y en combinación.

### 5.1 Opción A — Gate de consistencia MIR/NTI

**Idea**: publicar `vrp_tir_mw > 0` sólo si existe coincidencia espacial con la
máscara primaria MIR/NTI. Operacionalmente:

1. Identificar la máscara hot MIR (path primario, `hot_mask` ya existente en
   `process_viirs.py`) y su cluster primario (`primary_cluster` líneas 955-963).
2. Definir una "región hot TIR válida" como `hot5_mask_2d ∩ buffer_kernel(hot_mir_mask, radius=2px)`,
   donde `buffer_kernel` es una dilatación morfológica de 2 pixels (~750 m)
   para capturar el halo TIR adyacente al hot MIR.
3. Si el conteo de pixels TIR dentro de la región válida es `< N_TIR_MIN_PIX = 2`,
   declarar `vrp_tir_mw = 0` y agregar diagnostic `vrp_tir_gated_by_mir = true`.

**Pros**:

- Replica la lógica MIROVA implícita (TIR complemento, no primario).
- Elimina por construcción el caso patognomónico Chaitén (cuando MIR=0, TIR=0).
- Robusto a heterogeneidad andina: no depende de threshold absoluto.
- No requiere recalibrar constantes físicas.

**Contras**:

- Pierde la capacidad de detectar anomalías "TIR-only" (régimen low-T donde MIR
  está por debajo del threshold pero TIR la ve). Aveni 2025 GRL argumenta que
  ese régimen existe para crater lakes 300-330 K. Solución parcial: cuando se
  integre VRPTIR Aveni operacionalmente (F31 Task A2, pending S76), reactivar
  ese path con su propia validación.
- Requiere refactorizar el orden de cálculo en `process_viirs.py` (TIR depende
  de MIR ahora, hoy son independientes).

**Impacto esperado**:

- Recall: caída sobre volcanes con TIR-only legítimo (esperable Lascar low-activity,
  PP lake-only). Estimación grosera: −5 a −15% recall sobre PP, −0 a −5% sobre
  Lascar. Sin impacto sobre Villarrica, Chaitén, Llaima (que tienen señal MIR
  cuando hay actividad real).
- Precision: aumento dramático. Los 143 records outlier desaparecen.
- Ratio ours/MIROVA: convergencia hacia 1.0 para Villarrica, Chaitén, PCC.

### 5.2 Opción B — Threshold realista

**Idea**: subir el piso absoluto `TIR_THRESHOLD_K` y el multiplicador
`N_SIGMA_TIR` a valores físicamente defendibles para señal volcánica real.

Cambios propuestos en `pipeline/profiles/mirova_equivalent_f46_threshold.yaml`:

- `tir_threshold_k: 0.5 → 3.0` (3 K mínimo de exceso BT)
- `n_sigma_tir: 4 → 6` (6σ en vez de 4σ)

Justificación cuantitativa:

- σ_bg típico en ROI andino con heterogeneidad: 3-5 K. Con N=6, threshold
  relativo = 18-30 K. Eso fuerza a pixels TIR > 285-300 K para entrar a la
  máscara, lo cual es plausible para lava o lago cratérico activo, no para agua
  glaciar inactiva.
- Piso absoluto 3 K: Aveni 2025 GRL menciona Δ0.5 K como mínimo detectable
  teórico TIR (`MIROVA_DETAILED_CITATIONS.md:348`), pero a nivel operacional
  con ruido instrumental + atmósfera + heterogeneidad, 3 K es el piso defensable.
- Coppola 2016a Tabla 1 (para NTI no para TIR, pero referencia análoga) usa 5σ
  summit / 10σ scene para MODIS NTI. 6σ TIR es razonable mid-ground.

**Pros**:

- Cambio mínimo, 2 líneas YAML, sin refactor de código.
- Reversible vía toggle de profile.
- Mantiene path TIR independiente — preserva capacidad TIR-only.
- Coherente con la lógica de N·σ ya validada en path MIR (S17 H10 confirmada).

**Contras**:

- No elimina el problema de raíz: la fórmula sigue siendo Stefan-Boltzmann
  literal sobre máscara σ-relativa. En noches de σ_bg excepcionalmente bajo
  (ROI homogéneo + ausencia de cirrus), el threshold puede caer a 3 K y volver
  a admitir falsos positivos de lago.
- Recall TIR-only legítimo se reduce sobre PP/Copahue lake-only.
- No protege contra el patrón "T_hot = 285 K, T_bg = 266 K, ΔT = 19 K real pero
  no volcánico". Ese gradiente sigue pasando 6σ si σ_bg = 3 K.

**Impacto esperado**:

- Recall: caída −10 a −25% sobre PP, Copahue lake-only, Lascar fase quiescente.
- Precision: mejora sustancial. Estimación: 80-90% de los 143 outliers
  desaparecen (los que tienen σ_bg ≥ 3 K). Quedan 15-30 residuales.
- Ratio: convergencia parcial. Probablemente quedan algunos vrp_tir > 500 MW
  residuales.

### 5.3 Opción A+B combinada (recomendada)

Aplicar gate MIR/NTI (A) **y** subir thresholds (B) simultáneamente. Razones:

- A elimina el caso patognomónico (Chaitén n_pix=0) por construcción.
- B protege contra el caso "MIR detecta cluster legítimo pequeño pero TIR
  alrededor está inflado por heterogeneidad", que A no cubre.
- Combinados, recuperan la jerarquía MIROVA: TIR es complemento del MIR, con
  threshold defensable.

Recall esperado combinado: caída −15 a −30% sobre PP/Copahue lake-only, −0 a
−5% sobre Villarrica/Chaitén/Llaima/Lastarria/PCC.

## 6. Estrategia de validación

### 6.1 Patrón AB S24/S25

Clonar `.github/workflows/reproc-ab-test1.yml` como `reproc-ab-f46.yml` con tres
perfiles aislados:

- `pipeline/profiles/mirova_equivalent_f46_gate.yaml` — Opción A activa, B
  defaults.
- `pipeline/profiles/mirova_equivalent_f46_threshold.yaml` — Opción B activa, A
  defaults.
- `pipeline/profiles/mirova_equivalent_f46_both.yaml` — A+B activas.

Cada perfil con `data_subdir: experimental/f46_<variant>` para no contaminar
`data/mirova_equivalent/` operacional.

Ventana de reproceso: misma que la auditoría, **2026-01-31 a 2026-05-17** (3.5
meses), sobre los 11 volcanes Tier A. Coincide con `latest_consolidado.csv`
disponible como ground truth NRT.

`max-parallel: 1` para evitar la race condition documentada S25 sobre archivo
único por volcán (CLAUDE.md sección "Race condition matrix paralelo").

### 6.2 Ground truth anchor

Tres niveles de ground truth, en orden de prioridad:

1. **Aguilera 2021 Planchón-Peteroa** (`docs/F31_AGUILERA_2021_PETEROA.md`):
   Qvolc 7-59 MW lago cratérico. Anchor numérico directo: `vrp_tir_mw_PP` debe
   caer dentro de 7-59 MW en noches sin cirrus.
2. **MIROVA NRT** (`data/latest_consolidado.csv`, scraper Mirova-v1): tabla
   pareada por volcán-fecha-sensor. Métrica: ratio mediano `vrp_tir_mw_ours /
   vrp_mirova_mw` (sabiendo que MIROVA reporta VRP total, no TIR aislado — el
   ratio aceptable es 0.7-1.4 sobre noches con MIR coincidente).
3. **OSF v2.5 archive** (`data/mirova_reference/`): histórico, pero solo
   2000-2025. Para los 143 outliers actuales 2026, OSF no aplica directamente;
   sirve como sanity check sobre volcán-año donde había actividad documentada.

### 6.3 Métricas de aceptación

Por volcán y agregado Tier A, comparar pre-fix vs cada variante:

| Métrica | Threshold de aceptación |
|---|---|
| Conteo outliers `vrp_tir_mw > 1000 MW` | reducir 143 → 0 (variante both); o 143 → ≤15 (variantes individuales) |
| `vmax(vrp_tir_mw)` post-fix sobre PP | ≤ 100 MW (margen 1.7× sobre Aguilera 2021 max 59 MW) |
| `ratio_med(vrp_total_ours/vrp_mirova)` Tier A agregado | 0.7-1.4 |
| Recall por volcán Tier A | caída ≤10% absoluta vs pre-fix (excepción PP/Copahue lake-only, ≤25%) |
| Precision por volcán Tier A | aumento ≥15% absoluto |
| Caso patognomónico Chaitén 2026-03-25 SNPP | `vrp_tir_mw = 0` (Opción A o A+B); `vrp_tir_mw ≤ 50 MW` (Opción B sola) |

### 6.4 Análisis adicional sugerido

- Histograma σ_bg ROI por volcán-mes durante 2026-01 → 2026-05. Identificar
  patrones estacionales (invierno australo = más nieve = más σ_bg).
- Mapa espacial de los pixels `hot5_mask_2d` para Chaitén 2026-03-25 y Lascar
  2026-02-08: ¿están agrupados cerca del vent o dispersos por el ROI? La
  dispersión confirmaría el mecanismo "gradiente espacial vs anomalía".
- Cross-check con cobertura de nube VIIRS VCM (Cloud Mask producto) si está
  disponible — confirmar correlación outliers vs cirrus.

## 7. Riesgo y rollback

### 7.1 Tag defensivo obligatorio (A38+A39)

Antes de tocar `data/mirova_equivalent/` con el fix definitivo (post-AB
validado), pushear tag git:

```
git tag pre-s77-f46-vrp-tir-fix <SHA-actual>
git push origin pre-s77-f46-vrp-tir-fix
```

El tag debe apuntar al commit operacional pre-fix. Permite recuperar 100% del
estado operacional si el reproceso introduce regresión.

### 7.2 Confirmación explícita Nicolás (A45)

`process_viirs.py` es NRT operacional crítico (cron cada 2h, 11 volcanes, 12
corridas/día). Cualquier modificación al cálculo de `vrp_tir_mw` requiere
confirmación explícita del usuario antes del merge a `main`, incluso con tests
baseline OK. Lección S75: A45 fue aplicada correctamente cuando Nicolás
preguntó "no tienes que salvar la configuración actual antes?" — replicar ese
gate aquí.

### 7.3 Criterios de rollback

Disparar rollback (`git reset --hard pre-s77-f46-vrp-tir-fix` + revert YAML
profile) si en el primer reproceso post-merge se observa:

- Recall agregado Tier A cae más de 10% absoluto vs baseline pre-fix.
- Aparece regresión en algún volcán Tier A activo (Lascar, Lastarria, Villarrica)
  con recall <30% donde antes era >60%.
- Conteo `vrp_mir_mw = 0` (path primario MIR) aumenta más de 5% — indicaría que
  el refactor de orden de cálculo (Opción A) afectó accidentalmente al MIR.

### 7.4 Riesgos identificados

| Riesgo | Severidad | Mitigación |
|---|---|---|
| Refactor Opción A introduce bug en path MIR | Alta | Tests unitarios TDD sobre `process_viirs.py` antes de cambio (skill `test-driven-development`). Comparar baseline `vrp_mir_mw` pre/post sobre 100 records sintéticos. |
| Recall PP cae catastróficamente (volcán lake-dominated) | Media | Tener listo el path VRPTIR Aveni (`pipeline/vrptir.py`) como reemplazo cuando F31 A2 esté integrado. Mientras tanto, aceptar caída de recall sobre PP como costo de la consistencia. |
| Bug latente similar en `process_modis.py` o `process_viirs_mod.py` | Media | Auditar paralelamente `vrp_tir_mw` en MODIS y VIIRS_M antes de cerrar F46. Si tienen el mismo patrón Stefan-Boltzmann sobre máscara σ, aplicar fix análogo. |
| Frontend dashboard muestra el `vrp_tir_mw` viejo de records pre-fix | Baja | Guard simétrico ya pendiente (§8 ítem 2): mostrar warning si `vrp_tir_mw > 1000 AND vrp_mir_mw < 10`. |
| Race condition al pushear reproceso (S25) | Baja | `max-parallel: 1` en workflow AB. |

## 8. Pendientes y temas abiertos

1. **VRPTIR Aveni 2025 como reemplazo definitivo**. El módulo
   `pipeline/vrptir.py` ya está disponible (PR #146/153/158, F31 A1+A3+A4+A6
   cerrados S75). La integración operacional (F31 Task A2) está pausada por
   A38+A39 según `MEMORY.md` S75/S76. Cuando A2 se integre, considerar
   reemplazar el bloque Stefan-Boltzmann puro de `process_viirs.py:968-986`
   por VRPTIR con `k_TIR = 60.17`, rango 300-600 K, y la máscara apropiada
   (probablemente la misma de Opción A: pixels coincidentes con cluster MIR).
   F46 puede ser un puente táctico mientras F31 A2 madura.

2. **Guard frontend simétrico (quick win mientras se planea el fix)**.
   `frontend/index.html` ya tiene guard `pc.vrp_mw > 50K` (S73, F2.8). Agregar
   guard análogo: si `vrp_tir_mw > 1000 AND vrp_mir_mw < 10`, no graficar el
   punto TIR y agregar tooltip "valor TIR descartado: gradiente térmico sin
   confirmación MIR (ver F46)". Esto NO arregla el JSON, sólo evita que el
   dashboard muestre los 143 outliers existentes mientras se ejecuta el AB.
   Tarea bite-sized, ~30 min, sin riesgo operacional. Puede ir en paralelo
   al desarrollo del fix.

3. **Verificar fuente MIROVA en `MIROVA_DETAILED_CITATIONS.md:308` (D3
   RESUELTO S17)**. La afirmación "TIR usa Stefan-Boltzmann puro" fue
   confirmada antes de tener evidencia empírica del bug. Releer Coppola 2024
   Cap.11 + Aveni 2024 RSE eq.5 con la pregunta específica: ¿qué máscara usan
   MIROVA y TIRVolcH para definir los pixels TIR hot? ¿Es la misma del path
   primario MIR/NTI o es independiente? Si es independiente, ¿qué threshold
   usan? Si tienen un gate de consistencia que no documentamos, F46 sólo
   tendría que portarlo, no reinventarlo.

4. **Audit paralelo de `vrp_tir_mw` en MODIS y VIIRS_M**. La auditoría
   `experiments/138_audit_mw_outliers_s76/audit2.py` parece centrada en VIIRS
   I-band. Confirmar si MODIS B31 y VIIRS_M M15 tienen el mismo patrón. Si sí,
   el plan F46 se generaliza; si no, F46 es VIIRS-I específico.

5. **Histórico pre-2026 (OSF v2.5 reference)**. ¿Está afectado? La auditoría
   cubre 2026-01-31 → 2026-05-17. Si el bug existe desde S13 (cuando se
   introdujo el campo `vrp_tir_mw`), todo el `data/mirova_equivalent/` previo
   también necesita reprocesamiento. Cuantificar el alcance histórico antes
   de decidir si el fix es solo NRT-forward o requiere reproceso full.

6. **Documentar el caveat A35 sobre VRPTIR Aveni 2025**. El PDF AGU está
   paywalled (MEMORY.md S73). Mientras tanto, la verificación verbatim de
   `k_TIR = 60.17` y la fórmula Eq.9 depende de `aveni2025_crater_lakes.md`
   en el Vault, que es derivada de preprint EarthArXiv. Antes de integrar
   VRPTIR como reemplazo definitivo (§8.1), conseguir PDF GRL final y
   verificar 9/9 constantes como se hizo S75 para Aveni 2024 RSE
   (`F31_AVENI_2024_TIRVOLCH_VERIFY.md`).

---

## Anexo A — Constantes físicas referenciadas

| Símbolo | Valor | Unidad | Fuente |
|---|---:|---|---|
| `SIGMA` | 5.67·10⁻⁸ | W·m⁻²·K⁻⁴ | Stefan-Boltzmann (CODATA) |
| `TIR_THRESHOLD_K` | 0.5 | K | `mirova_equivalent.yaml` (default operacional, propuesto subir a 3.0) |
| `N_SIGMA_TIR` | 4 | adimensional | `mirova_equivalent.yaml` (default operacional, propuesto subir a 6) |
| `A_pix VIIRS I-band` | 140 625 | m² | 375 × 375 m nadir |
| `k_TIR Aveni 2025` | 60.17 | µm·sr | Aveni 2025 GRL L413 (alternativa a Stefan-Boltzmann) |
| `λ TIR I05` | 11.45 | µm | banda I05 VIIRS |
| `Qvolc PP lake (Aguilera 2021)` | 7–59 | MW | `F31_AGUILERA_2021_PETEROA.md` |

## Anexo B — Archivos a tocar (plan, no ejecución)

| Archivo | Cambio |
|---|---|
| `pipeline/process_viirs.py:968-986` | Refactor Opción A: agregar gate `hot5_mask_2d ∩ dilate(hot_mir_mask, 2px)` y conteo mínimo `N_TIR_MIN_PIX`. |
| `pipeline/profile.py:81-83` | Sin cambio de schema, sólo defaults vía YAML. |
| `pipeline/profiles/mirova_equivalent.yaml` | Sin cambio en operacional hasta merge final. |
| `pipeline/profiles/mirova_equivalent_f46_gate.yaml` | NUEVO, extends mirova_equivalent + `enable_tir_mir_gate: true`. |
| `pipeline/profiles/mirova_equivalent_f46_threshold.yaml` | NUEVO, extends + `tir_threshold_k: 3.0`, `n_sigma_tir: 6`. |
| `pipeline/profiles/mirova_equivalent_f46_both.yaml` | NUEVO, ambos. |
| `.github/workflows/reproc-ab-f46.yml` | NUEVO, clonado de `reproc-ab-test1.yml`, `max-parallel: 1`. |
| `frontend/index.html` | (quick win §8.2) Guard simétrico `vrp_tir_mw>1000 AND vrp_mir_mw<10`. |
| `tests/test_process_viirs_f46.py` | NUEVO, TDD sobre gate MIR/TIR antes de modificar código. |
| `tasks/handoff_s77_f46.md` | NUEVO al cerrar plan, con SHA del tag defensivo. |

## Anexo C — Cronograma estimado

| Tarea | Tiempo | Skill requerida | Sesión |
|---|---|---|---|
| Quick win guard frontend §8.2 | 30 min | `verification-before-completion` | S76 (paralelo) |
| Releer fuente MIROVA §8.3 | 1 h | `investigacion` | S76-S77 |
| Auditar MODIS+VIIRS_M §8.4 | 1 h | `dispatching-parallel-agents` | S77 |
| TDD tests F46 | 1 h | `test-driven-development` | S77 |
| Implementar Opción A | 2 h | `superpowers-systematic-debugging` | S77 |
| Implementar Opción B (YAML) | 15 min | — | S77 |
| Workflow AB reproc | 1 h | (template existente) | S77 |
| Reproceso AB 3 variantes × 11 volcanes × 3.5 meses | 4-6 h CI | — | S77 background |
| Análisis comparativo + decisión | 2 h | `result-to-claim` | S78 |
| Tag defensivo + merge + reproceso operacional | 30 min | A38+A39+A45 | S78 |
| **TOTAL ESTIMADO** | **~14-16 h** | | **S76-S78** |

---

*Documento generado en sesión S76 (2026-05-24) como parte del plan F46.
Sin código modificado. Próximo paso: revisión humana del plan + autorización
para crear branches AB.*
