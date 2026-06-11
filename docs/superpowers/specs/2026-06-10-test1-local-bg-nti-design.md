# Design — Test1 con FONDO LOCAL sobre NTI (realineamiento MIROVA uniforme)

**Fecha**: 2026-06-10 (S105) · Estado: DISEÑO · Gate: A45 + TDD + A/B.
**Principio rector (Nicolás, S105)**: MIROVA usa **UN algoritmo uniforme para todos los
volcanes** (no per-régimen, no per-vol). El fix debe ser uniforme. Cualquier solución
que necesite parámetros distintos por volcán está descartada de entrada.

## 1. Problema (causa raíz confirmada S104 + cerrada S105)

Las detecciones VIIRS375 de los nevados (Villarrica/Tupungatito/Llaima) se sesgan ~1 km
al N del cráter, hacia el terreno tibio de baja altitud (o el lago Conguillío en Llaima).
El `final_hotspot` del Test1 lo posiciona el **centroide ponderado por el exceso de
radiancia integrado sobre el ROI**, con **fondo = mediana del anillo entero** (5–25 km o
1–3 km). Ese fondo mezcla cumbre fría + valle tibio → todo lo que supera la mediana "es
anomalía" → el centroide se arrastra al valle.

**Lo que se descartó en S104–S105 (todo con datos)**:
- **V2 (Test1 integra NTI en vez de MIR)** — A/B run 27223821692: corrige solo ~50 m de
  ~1000–1500 m. El NTI cancela el gradiente de GRAN escala (cumbre-9km-valle) pero el
  sesgo nace DENTRO del ROI de 3 km, donde el fondo del anillo sigue mezclando. No basta
  cambiar MIR→NTI si el fondo sigue siendo el anillo entero.
- **k_sigma** (calibrar el gatillo): refutado offline — la señal fuerte no está mejor
  anclada (el gatillo no mueve el centroide).
- **Anclas de brillo** (BT máx): el pico de BT es el valle topográfico (12–26 km).
- **Discriminante núcleo-anillo** (probe run 27243090277/27244013547): SEPARA limpio en
  Villarrica (lava DISC>0 / topo DISC<0) pero NO es gate de supresión universal — en
  Tupun el "calor en cráter" de las noches sin-ALERTA es **cat-b real** (no topografía;
  Tupun activo casi siempre, confirmado por Nicolás), y en Llaima la lava débil a veces
  no destaca. **Fue la pista correcta hacia el fondo local, no el fix.**

## 2. El mecanismo MIROVA uniforme (Coppola 2024 Eq.13)

MIROVA no se sesga porque integra el exceso de píxeles detectados por NTI/dNTI con
**fondo LOCAL al cluster** — la media de los píxeles que rodean el foco activo — NO la
mediana del anillo entero (Coppola 2024 "Thermal Monitoring", Eq.13; sp426_5.txt l.357-359).

**Física de por qué cancela la topografía UNIFORMEMENTE (sin per-vol)**:
- Un píxel del **valle tibio** se compara con **su propio entorno tibio** → no destaca →
  no contribuye → no arrastra el centroide.
- Un píxel del **cráter con lava** se compara con la **cumbre fría que lo rodea** →
  destaca → contribuye → ancla el centroide al cráter.

El valle deja de ser anomalía **por construcción**, el mismo día, en todos los volcanes,
sin un solo parámetro per-volcán. Cada volcán da lo que su física da: Villarrica suprime
las noches muertas (acerca a MIROVA), Tupun conserva su cat-b real (calor real en cráter),
Llaima conserva lo que haya. Eso es exactamente lo que MIROVA hace.

## 3. Diseño (cambio quirúrgico en compute_test1_nti)

Reemplazar el fondo escalar `nti_bg = mediana(anillo)` por un **fondo LOCAL por píxel**:

```
para cada píxel i en el ROI:
    nti_bg_local[i] = mediana del NTI en el anillo local [r_in, r_out] alrededor de i
                      (ej. 0.5–1.5 km, excluyendo i; mínimo N vecinos válidos)
    excess[i] = max(0, NTI[i] − nti_bg_local[i])
delta_nti = Σ excess[i]
σ_local   = MAD del NTI en el entorno local (propagado)
trigger   = delta_nti > k_sigma · σ_local · √N_contrib
centroide = ponderado por excess[i]  → ancla al cráter (lava destaca sobre su entorno frío)
VRP       = Wooster sobre L_MIR de los píxeles contribuyentes (igual que V2.5, L_bg_mir)
```

- **Uniforme**: mismo kernel (r_in, r_out, k_sigma) para los 11 Tier A. SIN
  `local_kernel_bg_compatible` per-vol (ese flag existente es para la magnitud del path D
  y falló en Tupun sobre MIR; aquí es NTI + Test1, mecanismo distinto).
- **Sobre NTI, no MIR**: la diferencia clave con el `ENABLE_LOCAL_KERNEL_BG` que falló en
  Tupun (A19). El kernel local sobre MIR sube el fondo en el glaciar (vecinos "warm
  relativo") → no cura. Sobre NTI, la lava eleva el índice del píxel del cráter sobre su
  entorno glaciar → sí destaca. (Hipótesis a validar en el A/B — Tupun es el caso test.)
- Flag `enable_test1_local_bg_nti` (default OFF). Reemplaza el modo de fondo cuando ON.
  Mantiene compute_test1_mir (MIR + anillo) como baseline.

### Parámetros (a calibrar en A/B, NO per-vol)
- `r_in, r_out` del anillo local: arranque 0.5–1.5 km (kernel local "rodea el foco" sin
  tocar el píxel mismo). Sensibilidad sub-pixel: el ROI del Test1 sigue siendo 3 km.
- `k_sigma`: arranque 3.0; calibrar por el A/B (criterio 0 FN noches ALERTA).
- `min_local_bg_pixels`: mínimo de vecinos válidos para computar el fondo local (fallback
  al fondo del anillo si insuficiente — borde de granule).

## 4. A/B (criterios, vs baseline MIR-anillo y vs V2-NTI-anillo)
3 brazos: MIR-anillo (actual) / NTI-anillo (V2) / **NTI-local (nuevo)**. 11 Tier A, ≥90 d.
- **(R-recall) 0 FN** en noches ALERTA MIROVA de los 11 — criterio DURO. Atención especial:
  Llaima 05-15 (lava débil, dio DISC<0 en el probe → riesgo FN), Villarrica noches ALERTA.
- **(R-posición) offset N → 0** en los nevados (mediana direccional, A70); %<3km sube.
- **(R-Tupun) cat-b real conservado**: triggered_test1 NO se desploma en Tupun (su calor
  de cráter es real — A54). Si Tupun pierde recall = el kernel local sobre NTI tampoco
  separa ahí → revisar.
- **(R-control) Lascar/Chaitén/NdC** (áridos) y Lastarria (fumarólico Lazufre) SIN cambio.
- **(R3) magnitud** vs MIROVA no empeora.

## 5. Procedimiento A45
1. `git tag pre-s105-test1-local-bg-nti <sha>` + push.
2. OK explícito de Nicolás antes del primer edit a test1_integrated.py / process_viirs.py.
3. TDD (§6) → fix → suite verde.
4. A/B (§4) en GitHub Actions (Earthdata local roto A71; 90 d > timeout local).
5. Si cumple → promover + reproc 11 + R2/R3/R8 + MIROVA_DIVERGENCES + CLAUDE.md.

## 6. TDD (tests sintéticos ANTES del fix) — tests/test_test1_local_bg_nti.py
1. **Gradiente topográfico puro (NTI plano)**: campo con rampa lineal de BT (cumbre fría→
   valle tibio), NTI uniforme. Fondo-anillo → dispara y centroide en el valle. Fondo-local
   → NO dispara / centroide None (cada píxel ≈ su entorno).
2. **Lava sub-pixel en cráter**: un píxel cerca del vent con NTI elevado sobre su entorno.
   Fondo-local → dispara, centroide EN el cráter.
3. **Mixto (gradiente + lava)**: fondo-local → centroide anclado al cráter, no al valle.
4. **Borde de granule** (pocos vecinos): fallback al fondo del anillo, sin crash.
5. **Backward-compat**: flag OFF → idéntico a compute_test1_nti actual (regresión).
6. **Guard shapes**: bt_tir/lat/lon shape ≠ bt_mir → ValueError.

## 7. Pre-mortem / riesgos
- **R1 — FN en lava muy débil** (Llaima 05-15, DISC<0 en probe): el fondo local podría
  exigir que la lava destaque sobre su entorno inmediato; la lava de 0.08 MW casi no lo
  hace. Mitiga: k_sigma calibrado + el criterio integral (suma sobre el ROI, no pico).
  El A/B con criterio 0-FN lo mide; si cae, ablandar k_sigma o r_out.
- **R2 — Tupun glaciar** (donde el kernel local sobre MIR falló, A19): sobre NTI debería
  funcionar (la lava rompe la simetría MIR/TIR), pero NO está garantizado. Tupun es el
  caso-test del A/B. Si Tupun pierde su cat-b real → el kernel local NTI tampoco separa →
  documentar como límite físico, no forzar.
- **R3 — costo computacional**: fondo local por píxel = filtro sobre el ROI. El ROI es
  chico (3 km, ~pocos cientos de píxeles VIIRS375) → barato. MODIS (1 km) aún más chico.
- **R4 — uniformidad vs física**: si el A/B muestra que NINGÚN parámetro uniforme cumple
  0-FN en los 11, eso REFUTA que un fondo local uniforme baste — y sería un hallazgo real
  (MIROVA quizá usa algo más). NO recurrir a per-vol (viola el principio); documentar.

## 8. Qué NO hace este fix (límites honestos)
- No toca el campo difuso MODIS (Fase 3, otro path: path-D scene-wide).
- No toca Lastarria (offset fumarólico Lazufre real).
- No promete resolver el offset — lo PRUEBA el A/B. Si el fondo local uniforme no cancela
  la topografía en los 11 con 0 FN, se documenta el límite y se decide con datos.

---

## 12. Predicciones PRE-REGISTRADAS del A/B (A66, escritas ANTES del resultado)

Hipótesis por volcán, derivadas de la física + los probes S105. Pre-registradas para
evitar confirmation bias (A62) y como material de Validation del paper. El A/B
(run 27275241269 k=3.0 + barrido 27276651420 k=2.0/2.5) las confirma o refuta.

| vol | régimen | predicción fondo-local vs MIR-anillo | criterio de éxito |
|---|---|---|---|
| **Villarrica** | nevado intermitente (11 ALERTA) | offN ↓ fuerte (suprime noches topográficas puras); las noches ALERTA tienen lava que destaca sobre cumbre fría → recall preservado | offN→0, %<3km↑, recall 8/11 igual |
| **Tupungatito** | nevado, cat-b casi continuo (94 ALERTA) | el calor real del cráter destaca sobre su entorno glaciar → trig_t1 CONSERVADO, offN ↓ (el cat-b está EN el cráter, no en el valle) | trig_t1 no se desploma, offN↓, recall 75/75 |
| **Llaima** | nevado, lago Conguillío N | offN ↓ (suprime el sesgo del lago); RIESGO: la lava débil 05-15 dio pico al lago (DISC<0) → posible FN de esa noche | offN↓; vigilar recall 1/1 (riesgo FN) |
| **Lascar** | árido control | sin gradiente topográfico → fondo-local ≈ fondo-anillo → SIN cambio | offN/dist/recall sin cambio (117/127) |
| **Lastarria** | fumarólico Lazufre (offset N REAL) | RIESGO CLAVE: si el campo fumarólico es EXTENDIDO/uniforme, el fondo-local lo trata como "entorno" y NO destaca → podría SUPRIMIR señal real (FN, viola A54). Si es un foco con gradiente, se conserva. | recall 94/105 PRESERVADO. Si cae → el fondo-local borra cat-b extendido = límite del método |

**Lo que CADA resultado significaría (decisión pre-comprometida)**:
- Si Villarrica/Tupun/Llaima offN↓ con 0 FN y Lascar/Lastarria sin cambio → **éxito uniforme**,
  promover (A45). El fondo local uniforme cancela la topografía sin tocar señal real.
- Si Lastarria pierde recall → el fondo-local borra señal fumarólica EXTENDIDA → NO es
  uniformemente seguro. Documentar el límite (el método asume foco con gradiente local; falla
  en señal espacialmente uniforme). NO promover sin resolver.
- Si Llaima pierde la noche ALERTA → calibrar k_sigma (barrido) o aceptar como límite SNR.
- Si Tupun trig_t1 se desploma → el fondo-local sobre NTI tampoco separa en glaciar (como el
  kernel-MIR, A19) → refuta la hipótesis central; documentar.

**k_sigma esperado**: a menor k_sigma (2.0) más sensible → menos FN (mejor para Llaima/lava
débil) pero más FP topográfico residual. El óptimo = el menor k_sigma que aún dé offN↓ en
los nevados (la curva del barrido lo muestra).

## 13. Límite de escala del fondo-local (test sintético offline, S105) — riesgo Lastarria REVISADO

Test sintético (no requiere Earthdata): foco de NTI elevado de radio R, fondo NTI con
ruido realista, modo local (anillo 0.5-1.5km). Resultado:
- **Foco gaussiano (borde suave, como lava/fumarola con gradiente)** R=0.5/1.0/2.0 km:
  el fondo-local DISPARA y ancla al centro del foco (0.02-0.08 km). Detecta bien.
- **Foco escalón** R=1/2/4 km: dispara también (el borde, aunque a 4 km, cae en el anillo
  local de los píxeles del ROI cercanos al borde → excess).

**Conclusión (límite de escala)**: el fondo-local detecta cualquier foco con borde o
gradiente espacial. Solo una señal PERFECTAMENTE UNIFORME sobre un área >> ROI+anillo+r_out
(>~5 km, físicamente irreal) se auto-cancelaría (cada píxel ≈ su entorno). Las señales
volcánicas reales (lava sub-pixel, campos fumarólicos) tienen gradiente → se detectan.

**Riesgo Lastarria REVISADO a la baja**: el campo fumarólico Lazufre, aunque extendido,
tiene borde/gradiente → el fondo-local lo detecta y ancla a SU centro real (al N, el
fumarólico) → CONSERVA el offset N real de Lastarria (no lo borra). Predicción §12
actualizada: Lastarria probablemente "sin cambio" (offset fumarólico preservado), riesgo
FN bajo. El A/B lo confirma empíricamente. (Material de Discussion del paper: el método es
robusto a señal con estructura espacial; el único límite es la señal uniforme infinita.)

## 14. RESULTADOS S106 — brazo k=3.0 (run 27275241269, 10/10 jobs OK; barrido pendiente)

Audit: `audit_local_sweep.py` sobre `local_k30/` (merge de 2 chunks, verificado sin gap
de frontera: el día 2026-03-31 SÍ fue procesado — los otros 4 vols tienen records ese día).

| vol | offN_m (MIR→local) | %<3km | trig_t1 | recall | veredicto vs §12 |
|---|---|---|---|---|---|
| Tupungatito | 1047→**130** ✓ | 96→69 | 465→**95 (−80%)** ✗ | **74/75 (1 FN)** ✗ | **FALLA criterio duro** |
| Villarrica | 748→**261** ✓ | 90→**57** ✗ | 462→88 | 8/11 ✓ | PARCIAL |
| Llaima | 1097→**278** ✓ | 87→48 | 428→79 | 1/1 ✓ (riesgo FN NO se materializó) | PASA offN |
| Lascar (ctrl) | 23→36 ~✓ | 99→91 | 446→**329 (−26%)** | 117/127 ✓ | PARCIAL (no predicho) |
| Lastarria (ctrl) | 886→**931** ✓ conservado | 99→88 | 441→**289 (−34%)** | 94/105 ✓✓ | PASA (§13 acertó) |

**Lectura contra la decisión pre-comprometida (§12, sin racionalizar)**:
- El sesgo topográfico N **SE CURA** en los 3 nevados (offN 1047/748/1097 → 130/261/278 m).
- PERO **Tupun trig_t1 se desploma** (465→95) + 1 FN real (2026-03-31, 5 pasadas baseline
  con 0.04-0.14 MW a 0.03-0.3 km del cráter, Test1-only). Per §12 pre-comprometido:
  **a k=3.0 la hipótesis queda refutada — NO promover k=3.0**.
- Mecanismo (no anticipado en §13): el fondo local no "cancela" la señal débil extendida,
  la ATENÚA — los vecinos del píxel del cráter están templados por la misma fuente
  sub-pixel + σ local más ruidoso (menos píxeles de fondo) → umbral k·σ sube → el exceso
  integrado cae bajo umbral. Es pérdida de SENSIBILIDAD transversal (también Lascar −26%
  y Lastarria −34% en trig_t1, aunque ahí el recall lo cubren los triggers sobrevivientes),
  no confusión lava/topografía.
- El %<3km bajó en Villarrica/Llaima porque al apagarse el Test1 (el ancla precisa), las
  detecciones restantes vienen de paths con anclas más dispersas.

## 15. RESULTADOS S106 — barrido completo (run 27276651420, 20/20 OK) → VEREDICTO: REFUTADO

Curva completa k=2.0/2.5/3.0 (audit_local_sweep.py, 5 brazos):

| vol | métrica | MIR-anillo | k=2.0 | k=2.5 | k=3.0 |
|---|---|---|---|---|---|
| Tupungatito | offN_m / trig_t1 / recall | 1047 / 465 / 75-75 | 182 / 220 / 75-75 | 141 / 129 / 75-75 | 130 / 95 / 74-75 |
| Villarrica | offN_m / trig_t1 / recall | 748 / 462 / 8-11 | 170 / 177 / 8-11 | 182 / 128 / 8-11 | 261 / 88 / 8-11 |
| Llaima | offN_m / trig_t1 / recall | 1097 / 428 / 1-1 | 206 / 209 / 1-1 | 236 / 133 / 1-1 | 278 / 79 / 1-1 |
| Lascar (ctrl) | offN_m / trig_t1 / recall | 23 / 446 / 117-127 | 43 / 409 / 117-127 | 38 / 369 / 117-127 | 36 / 329 / 117-127 |
| Lastarria (ctrl) | offN_m / trig_t1 / recall | 886 / 441 / 94-105 | 742 / 424 / 94-105 | 821 / 372 / 94-105 | 931 / 289 / 94-105 |

**La verificación decisiva (anti-racionalización A66): Test1 disparado EN noches ALERTA
MIROVA** (proxy de cat-b real — si lo perdido fuera solo FP topográfico, esta columna no
debería caer):

| vol | MIR-anillo | k=2.0 | k=2.5 | k=3.0 |
|---|---|---|---|---|
| Tupungatito | 75/75 | **59/75 (−16)** | 31/75 | 17/75 |
| Villarrica | 8/11 | **3/11 (−5 de 8 noches de lava real)** | 2/11 | 1/11 |
| Llaima | 1/1 | 1/1 | 1/1 | 1/1 |
| Lascar | 117/127 | 117/127 | 117/127 | 116/127 |
| Lastarria | 94/105 | 94/105 | 94/105 | 87/105 |

**Veredicto (decisión pre-comprometida §12): REFUTADO en todo el barrido. NO promover.**
- Aun al k más sensible (2.0), el fondo local apaga el Test1 en noches de actividad REAL:
  Tupungatito pierde el trigger en 16/75 noches ALERTA y Villarrica en 5/8 noches de lava
  confirmada. El recall global se sostiene solo porque otros paths rescatan esas noches —
  pero el Test1 ES el detector sensible para cat-b débil (S25-S27); degradarlo en las
  noches reales adelgaza la redundancia y dispersa el ancla (%<3km cae 96→81 / 90→71).
- **Mecanismo de la refutación (= límite del método, refina §13)**: a escala del anillo
  local (0.5-1.5 km), la señal volcánica DÉBIL es espacialmente suave — la fuente sub-pixel
  templa a sus propios vecinos — y resulta INDISTINGUIBLE de la suavidad topográfica. El
  fondo local solo conserva señal con contraste sub-pixel fuerte (Láscar −8% apenas). El
  test sintético §13 falló en anticiparlo porque modeló focos con borde nítido sobre fondo
  de ruido blanco, no señal débil + vecindario auto-templado + σ local ruidoso.
- Cadena completa del frente D11: V1 (co-validación per-pixel) refutado S104 → V2
  (NTI-anillo) cerrado S105 (corrige ~50m de ~1000) → fondo-local-NTI refutado S106 en
  todo el barrido. Los tres compartían el supuesto de que el sesgo es separable de la
  señal débil a alguna escala espacial; la evidencia dice que a escala local NO lo es.
- `enable_test1_local_bg_nti` queda **OFF** (nunca se promovió). Destino del flag/rama:
  decisión de purga en S106+ (AUDIT_S105 P2-8).
- Material para el paper: secuencia completa V1→V2→local con predicciones pre-registradas
  y refutación limpia por criterio duro (Validation/Discussion).
