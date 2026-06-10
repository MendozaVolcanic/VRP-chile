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
