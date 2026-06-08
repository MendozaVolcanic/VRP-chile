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
