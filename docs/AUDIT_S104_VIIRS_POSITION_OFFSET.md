# AUDIT S104 — Offset de POSICIÓN de las detecciones VIIRS375 (Villarrica y otros)

**Fecha**: 2026-06-08 · Disparador: Nicolás reporta en el dashboard de Villarrica
"muchos puntos en forma concéntrica y lejos del cráter". A62 (insistencia del
experto = señal) → auditoría con `superpowers-systematic-debugging`. A61 (eje
espacial obligatorio): el problema era invisible a las distancias-número, solo
aparece mirando ubicaciones.

## Veredicto: el patrón que ve Nicolás = 3 capas distintas apiladas

### Capa 1 — anillo gris lejano = ruido difuso de MODIS (DF-6, conocido)
- MODIS (1 km/píxel) NO resuelve el lava lake (sub-pixel). Cuando dispara, su
  "píxel más caliente" cae en terreno tibio cualquiera del recuadro de 25 km.
- 219 records MODIS a ≥15 km del cráter, **todos `distance_class=far`**,
  `triggered_test1=False`, t_max ~287-300 K (≈14-27 °C = NO lava). Pico de
  densidad en **18-27 km** (más área en anillos exteriores → patrón anular).
- **Ocultos por default** (toggle "🎯 Solo cráter", `vrp_include_far=false`,
  filtro en `index.html:2412`). Si Nicolás los ve = tiene "📍 Incluir lejanas" ON
  (flag persistido en su navegador).
- = frente DF-6 / D9 / A23 (ya scopeado, no resuelto). No es bug nuevo.

### Capa 2 — puntos VIIRS375 corridos ~1 km del cráter = CAUSA RAÍZ NUEVA
- VIIRS375 detecta el lava lake, PERO el `final_hotspot` cae sistemáticamente
  **lejos del cráter físico**, mismo offset en los 3 satélites independientes
  (NOAA-20/21/SNPP coinciden → NO es ruido ni view-angle ni un producto):
  - Villarrica 1.07 km NW, Tupungatito 1.21 km NW, Lastarria 1.11 km NW,
    Llaima 1.12 km N. **Corridos = volcanes con glaciar/nieve de cumbre/relieve.**
  - Láscar 0.13, Chaitén 0.09, NdC 0.06, PP 0.23 = **centrados** (sin nieve/áridos).
- Ground truth: Nicolás (geólogo, campo) confirma actividad **puntual en el
  cráter cumbre**. MIROVA CSV consolidado reporta las 11 ALERTA de Villarrica a
  **dist 0.84 km del Smithsonian** (= en el cráter; Smithsonian está 0.85 km al E
  del cráter). → las detecciones corridas son **error nuestro, no física**.
- **NOTA TIF (A24 reconfirmado 2x)**: el TIF de MIROVA es el campo de radiancia
  de FONDO (topografía), NO un mapa de anomalías. Su pico global cae a 18 km
  (esquina), su pico local <4km apenas supera el fondo. **No usable** para
  localizar el calor. Ground truth válido = Nicolás + Distancia_km del consolidado.

#### Causa raíz (código) — CORREGIDA tras prototipo offline (A62)
- **Hipótesis inicial REFUTADA por datos**: pensé que era el centroide laxo del
  Test1 (`test1_integrated.py:141-168`, pondera todos los píxeles con
  `excess > median(L_bg)`). Pero el prototipo mostró que el **píxel detectado
  crudo está MÁS lejos** (2.86 km NW, npx=1, 378 records) que el centroide
  (1.52 km). El centroide *acerca*, no aleja. No es la causa.
- **Causa raíz real**: en Villarrica VIIRS375, **0 records vienen de umbral
  ABSOLUTO** (BT/NTI). Los 473 son **dNTI contextual (281) o Test1 integrado
  (192)** — métodos que dependen del CONTRASTE local/integral, no del valor
  absoluto. El lava lake es tan sub-pixel que ningún píxel supera el umbral
  absoluto. Ambos métodos contextuales están corridos ~1.5 km por igual.
- **Mecanismo físico**: el fondo nocturno de Villarrica tiene un **gradiente
  térmico** (glaciar/nieve de cumbre + relieve hacia el NW). Los métodos
  contextuales (dNTI 8-vecinos, Test1 ROI integrado) se disparan sobre el borde
  de ese gradiente → seleccionan píxeles del flanco NW, no del lava lake del
  cráter. **VIIRS750 (banda M, 750 m) promedia el gradiente → queda en el cráter
  (0.23 km); VIIRS375 (banda I, 375 m) lo resuelve → se va al flanco (1-2.8 km).**
- = **manifestación ESPACIAL del drift D9/A23** (path dNTI contextual sin
  co-validación absoluta). Conocido como inflado de magnitud; acá aparece como
  corrimiento de posición. Mismo origen.
- Pendiente confirmar exacto: requiere ROI completo (reproc instrumentado de 1
  granule) — el campo de radiancia no está en los JSON.

#### Alcance
- NO afecta detección ni magnitud VRP (el VRP usa el cluster, no el centroide
  Test1). **Solo afecta la POSICIÓN mostrada** → `distance_class`, ubicación en
  el mapa. Cosmético-operacional, pero engaña la lectura geológica del mapa.

### Capa 3 — el nadir-fijo S103 (ayer) AGREGÓ corrimiento al Oeste en Villarrica
- Comparación pre/post `pre-s103-nadir-fixed-viirs`:
  - Villarrica: (+740 N, **+39 E**) 0.74 km → (+739 N, **−774 E**) 1.07 km.
    **shift_E = −813 m** (el componente Norte crónico intacto; el Oeste lo agregó
    el nadir).
  - Tupun −7 m, Lastarria +19 m, Llaima +141 m, Láscar +10 m → **shift casi
    exclusivo de Villarrica**.
- Mecanismo: el nadir cambió el área → cambió qué records disparan Test1 (A67,
  Villarrica 636→602 det) → cambió la composición/mediana de posiciones. Efecto
  de **composición**, no del centroide individual.
- **NO es regresión sistemática** (auditado los 11): el nadir movió la posición
  >0.2 km en 4 volcanes, MIXTO — **mejoró NdC (0.83→0.06 km)**, Copahue
  (0.76→0.58), Isluga (0.96→0.74); **empeoró Villarrica (0.74→1.07 km)**. El resto
  estable (<0.15 km). El offset crónico de Capa 2 es el problema dominante; el
  nadir solo redistribuye. Ambos comparten la misma causa raíz (centroide laxo).
- **El efecto-POSICIÓN del nadir NO se auditó al promover S103** (solo magnitud
  y FN). Regla A67 ampliada: al adoptar un cambio de área/escala, auditar también
  la POSICIÓN del hotspot, no solo magnitud/FN/cantidad.

Tabla efecto-posición nadir (offset VIIRS375 al cráter, mediana, pre→post):
Chaiten 0.06→0.09 · Copahue 0.76→0.58 · Isluga 0.96→0.74 · Lascar 0.15→0.13 ·
Lastarria 1.06→1.11 · Llaima 1.11→1.12 · **NdC 0.83→0.06** · PP 0.23→0.23 ·
PCC 0.33→0.36 · Tupun 1.18→1.21 · **Villarrica 0.74→1.07**.

## ⭐ GROUND TRUTH — campo crudo de BT I04 (reproc instrumentado, Actions run 27173150500)
Probe `experiments/_s104_roi_probe/` sobre 2 granules VIIRS I-band de Villarrica
2026-05-17 (SNPP 05:24, NOAA21 04:54). Carga el campo CRUDO de BT I04 con las
funciones del pipeline (`read_viirs_l1b/geo`) — sin paths de detección (no-A48).

**Resultado contundente (ambos satélites coinciden):**
- BT_max de todo el ROI = **281.5 K @ ~9 km al NORTE** del cráter.
- BT_max dentro de 2 km del cráter = **272 K** → el cráter está **9 K MÁS FRÍO**
  que el terreno de afuera.
- Imágenes `out/roi_*.png`: el cráter (vent_lat) cae en el centro de la zona
  **más fría** de la escena (el **cono nevado/glaciar**, ~266-270 K); el terreno
  tibio (~278-281 K) está en las **laderas bajas y valles** alrededor.

**Reformulación de la causa raíz (la definitiva):**
- En estas pasadas **el lava lake sub-pixel NO produce señal térmica detectable**
  — el píxel de 375 m sobre la cumbre está dominado por el **glaciar frío**. El
  campo crudo nocturno está gobernado por el **gradiente topográfico de altitud**
  (cumbre nevada fría ↔ valle tibio), NO por actividad volcánica.
- Los métodos de detección **relativos/integrales** (dNTI 8-vec, Test1 con fondo =
  mediana del ROI) miden "exceso sobre el fondo". El terreno tibio del valle (281 K)
  tiene exceso sobre la mediana del ROI (274 K) → **se detecta como anomalía** y
  arrastra el centroide hacia el terreno bajo (N). El lava lake real (cráter frío)
  no destaca.
- → Una fracción de las detecciones VIIRS375 de Villarrica (y probablemente
  Tupun/Lastarria/Llaima, los nevados) son **falsos positivos topográficos**, NO
  el lava lake. Esto MATIZA el marco A54 ("95% de FP = realidad física"): acá hay
  realidad física TÉRMICA (valle tibio) pero NO realidad VOLCÁNICA. El instinto de
  Nicolás ("hay demasiadas detecciones") era correcto en lo esencial.
- Por qué Láscar (árido) NO se afecta: sin gradiente topográfico nieve/valle, el
  fondo del ROI es homogéneo → el foco (cuando lo hay) destaca limpio.

**Implicación para el fix (D9/A23, eje físico real):** el `background` del ROI
(mediana global) NO modela el gradiente topográfico → mezcla cumbre fría + valle
tibio en una sola mediana, y todo lo que supera esa mediana "es anomalía". El fix
correcto ataca el FONDO: un background que capture la estructura topográfica
(kernel local / bandas de altitud / co-validación con BT absoluto), de modo que un
píxel solo sea anómalo respecto a su entorno topográfico inmediato, no respecto a
la mezcla cumbre+valle. Conecta con `ENABLE_LOCAL_KERNEL_BG` (process_viirs.py:1106,
ya intentado per-vol; Tupun lo refutó por ring glaciar, A19) — hay que rediseñarlo
con este ground truth.

**Caveat honesto:** 2 pasadas de 1 noche (05-17); la ALERTA MIROVA de esa fecha
fue otra pasada (05:48 NOAA20, que dio 0 px válidos en el ROI = NaN/cobertura). El
MECANISMO está demostrado; cuantificar qué fracción de detecciones es topográfica
vs lava-lake-real requiere más pasadas (incluyendo noches con señal fuerte real).

## ⭐⭐ CAUSA RAÍZ CONFIRMADA — triple auditoría (papers + código + tests previos)

**La pregunta de Nicolás: ¿por qué MIROVA NO se sesga y nosotros sí?**
Respuesta (Coppola 2016a SP426.5 + Coppola 2024, leídos en `documentacion/`):

**MIROVA detecta sobre NTI = índice normalizado (L_MIR − L_TIR)/(L_MIR + L_TIR).**
El NTI **cancela el gradiente topográfico por construcción**: el terreno tibio del
valle sube MIR *y* TIR juntos → el cociente normalizado queda estable. El paper lo
dice literal: el NTI "saca la variabilidad natural cualquiera sea el tipo de
superficie" (sp426_5.txt l.367-373) y dETI "independiza de topografía y clima
local". El "Test 1" REAL de Coppola 2016a es **NTI_pix > K1** (umbral de índice,
l.300), NO una integral de radiancia MIR. La suma integrada (Coppola 2024 Eq.13)
suma el exceso ΔL de píxeles **ya detectados por NTI/dNTI**, con fondo **local al
cluster** (media de los píxeles que rodean el cluster activo, l.357-359). Verificado
con datos: (I04−I05) en el ROI es **plano (mediana 0.01–0.14 K)** mientras I04 solo
tiene gradiente de 15 K → la diferencia MIR−TIR mata la topografía.

**Nuestro "Test1 integrado" (`pipeline/test1_integrated.py`) NO es el de MIROVA — es
un drift:**
- Integra **exceso de radiancia MIR ABSOLUTA (I04)**, no NTI (`test1_integrated.py:140-142`).
- Background = **mediana del anillo 5–25 km** (mezcla cumbre fría + valle tibio),
  no fondo local al cluster (líneas 98, 133).
- **Centroide ponderado por el exceso de radiancia MIR** (líneas 162-167) → el valle
  tibio (281 K) supera la mediana del anillo (274 K), aporta "exceso" y **arrastra el
  centroide hacia el terreno bajo**.
- En Villarrica/Tupun/Llaima (señal sub-pixel, `triggered_test1` domina,
  `final_hotspot_source="test1"`) este es el path que posiciona la detección → sesgo
  topográfico directo.

**Los paths NTI son inmunes** (auditoría código): Path B `n_nti_path` (NTI>K1), Path C
`n_nti_rel_path` (NTI>bg+3σ), Path D `n_dnti_ctx_path` (dNTI 8-vec) usan NTI → cancelan
topografía. Path A `n_bt_path` usa MIR absoluto pero está **OFF** por default. **El
culpable es el Test1 integrado MIR.**

**Por qué Lastarria NO entra acá** (dato de campo de Nicolás): su offset Norte es el
**campo fumarólico real** (Lazufre), NO artefacto topográfico. Tupun/Villarrica/Llaima
SÍ son artefacto. El fix no debe tocar Lastarria.

**Conexión con trabajo previo:**
- ctxpeak (S100, `S100_TEST1_FULL_AB.md`) curó la MAGNITUD del Test1 (Tupun 18.9→2.46×)
  pero **no la posición/detección** — el centroide sigue ponderado por MIR absoluto.
- kernel-bg local (A12/A19, `F66_BG_KERNEL_LOCAL_DEEP_S78.md`): ON Villarrica, OFF
  Tupun/Llaima (glaciar lo empeora). Solo afecta magnitud, no posición.
- D9/A23 (`MIROVA_DIVERGENCES.md`): path D cirrus, eje relacionado pero distinto.
- **MISSION.md 3-preguntas**: ¿MIROVA integra MIR crudo del ROID? NO → el Test1 MIR es
  un drift a realinear (NTI-based o co-validación), NO a parchar más.

**Por qué el Test1 integrado existe igual**: se introdujo (S13/S25) para curar
Villarrica recall 0% (MIROVA ve el lava lake integrando el ROI, nosotros no lo
veíamos pixel-level). El problema que resuelve es REAL (sensibilidad sub-pixel). El
defecto es la IMPLEMENTACIÓN (MIR absoluto + fondo anillo + centroide MIR). El fix
raíz: realinear con Coppola 2016a/2024 — integrar el exceso de píxeles **NTI-detectados**
con **fondo local**, y/o **co-validar la posición del Test1 con NTI** (un píxel solo
cuenta si su NTI también destaca). Eso mataría el sesgo topográfico sin perder el
recall sub-pixel.

## Acciones (NO implementadas — requieren A45 + brainstorming + TDD)
1. **Fix Capa 2 (raíz) = atacar D9/A23 en su eje espacial.** El prototipo offline
   descartó los fixes de "anclar al foco" (el píxel detectado mismo está corrido,
   no solo el centroide). El fix real es **co-validar las detecciones contextuales
   (dNTI/Test1) contra una referencia absoluta** para que no se vayan al gradiente
   del fondo. Candidatos a brainstorming: (a) cuando solo disparan métodos
   contextuales y hay un gradiente de fondo, anclar el `final_hotspot` al píxel de
   mayor BT absoluto dentro del inner-radius (el foco real, no el borde del
   gradiente); (b) co-validación BT/NTI obligatoria para el path dNTI ctx (el fix
   D9 "de fondo" que ya estaba en backlog); (c) penalizar/excluir píxeles en el
   borde de un gradiente de fondo fuerte. **Requiere ROI completo (reproc
   instrumentado de 1 granule de Villarrica) para confirmar el mecanismo exacto y
   evaluar candidatos.** A45 + reproc + R2.
2. **Capa 3**: decidir si el shift O del nadir en Villarrica se corrige con (1) o
   se acepta. Auditar efecto-posición del nadir en los 11 (pendiente: solo medido
   en 5).
3. **Capa 1**: display — confirmar si el toggle "Incluir lejanas" de Nicolás está
   ON; el anillo MODIS es DF-6 (frente aparte).

## Reglas de método nuevas (candidatas a CLAUDE.md)
- **A6x AUDIT-DIRECCIÓN**: auditar posición incluye el VECTOR (Δlat,Δlon)/rumbo,
  no solo la distancia escalar. Una mediana de distancia "1.9 km" ocultó que TODOS
  los puntos van al mismo lado (sesgo direccional = bug; disperso = ruido). Tres
  satélites independientes coincidiendo en rumbo = prueba de que es físico/sistémico.
- **A6x NADIR-POSICIÓN**: ampliar A67 — un cambio de área/escala puede mover la
  POSICIÓN del hotspot vía composición de detecciones; auditar posición además de
  magnitud/FN.
