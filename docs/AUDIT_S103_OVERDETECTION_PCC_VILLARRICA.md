# AUDIT S103 — ¿Sobre-detección en PCC y Villarrica? (pedido Nicolás, A61/A62)

**Fecha**: 2026-06-07 · Read-only sobre data operacional (no interfiere con el reproc nadir
en perfil aislado). 4 subagentes paralelos + **verificación directa propia** de los hallazgos
críticos (A50/A62: corregí 2 afirmaciones de subagentes que estaban mal).

## Disparador
Nicolás (geólogo) mira el dashboard y siente que en PCC y Villarrica hay muchas más
detecciones de las que debería. A62: su insistencia es señal — asumí error y lo busqué con datos.

## Lo que VERIFIQUÉ yo mismo (fuente de verdad)
1. **Los núcleos detectados son calor REAL, no artefactos de píxel frío.** `t_max − t_bg`:
   Villarrica VIIRS375 **+10.1K** mediana, PCC **+11.2K**, Láscar +18.4K. **0% más fríos que
   el fondo** en los 3. → REFUTA el hallazgo headline del subagente Villarrica ("70% píxel más
   caliente más frío que el fondo"): ese agente miró el campo crudo de footprint, no el record.
2. **PCC: las detecciones SÍ están lejos del cráter** — final_hotspot mediana **10.5 km** del
   cráter (solo 41% <3km). → REFUTA al subagente PCC que dijo "0.96km". El cráter (Puyehue)
   está a 7.57km del centro del grid; las detecciones están ~9-10km de AMBOS (cráter y centro)
   = esparcidas por el campo ancho. Consistente con el lacolito extendido Cordón Caulle (~707
   km², offset del cráter, real) PERO también donde dispararía path-D cirrus. No separable limpio.
3. **Villarrica: razonablemente anclado** — final_hotspot mediana 1.94km del cráter (60% <3km;
   VIIRS375 más ajustado, MODIS arrastra por deuda Salar/difuso). Coincide con el TIF MIROVA al
   cráter (~1.25km).
4. **"contextual-only" NO es marcador de sobre-detección**: Láscar (calibrado 1.4×) es 77%
   contextual-only; PCC 96%, Villarrica 58%. El path dNTI contextual es la vía PRIMARIA de
   VIIRS375 (Test 2/3 MIROVA). Fracción alta = normal.

## Lo que muestran los subagentes (convergente, con caveats)
5. **Sobre-detección vs MIROVA es SISTÉMICA, no localizada en PCC/Villarrica** (Agente 4):
   detección-día ours/MIROVA por volcán (mar-jun): Láscar 1.4× (calibrado), Isluga 3.0,
   Tupun 3.2, Lastarria 3.4, **PCC 5.0**, PP 5.3, Chaitén 17, NdC 25, **Villarrica 37**,
   Copahue 238, Llaima 241. PCC y Villarrica están en el rango medio, NO son el techo.
6. **Loader SANO** (A86): el cruce no falla por matching; MIROVA genuinamente clasifica esas
   noches como RUTINA/NULO (publica pocas ALERTA). OCR congelado (no cubre abr-jun).
7. **Magnitud PCC inflada ~7×** (suma campo difuso MODIS 1km vs foco VIIRS375 MIROVA, A54/A55)
   — eje separado, lo ataca nadir (en curso).

## Síntesis honesta
**El instinto de Nicolás es correcto en que el dashboard MUESTRA mucho — pero la causa es
mayormente (a) recall real > MIROVA + (b) amplificación de display, NO un bug de detección nuevo.**

- Los núcleos son calor real (+10K), no artefactos fríos. El path es normal (igual que Láscar
  calibrado). El loader es sano. → No es un bug de pipeline nuevo.
- El grueso del "exceso vs MIROVA" son **features térmicas reales sub-umbral-MIROVA** (cat-b,
  A54): nosotros las detectamos (recall alto, objetivo de mirova_equivalent), MIROVA las llama
  RUTINA. Es POR DISEÑO (recall > precision). Sistémico (3-241×), no localizado.
- **Lo que amplifica el VISUAL (display, no detección)**:
  - **PCC inner_radius_km=20**: pinta TODO el campo extendido (mediana 10km) de "summit-rojo",
    aunque el cráter Puyehue esté lejos y el calor sea el lacolito offset. Parece un cráter
    denso cuando es campo difuso ancho.
  - **Acumulación 30 días sin deduplicar** (1 punto por pasada satelital × ~8 sensores).
  - Posible footprint crudo (anomaly_pixels) si el mapa lo pinta (no confirmado).

## Lo que NO pude cerrar (honestidad)
- ¿Qué fracción de las detecciones anchas de PCC es lacolito real (cat-b) vs path-D cirrus
  artefacto? No separable: el proxy cirrus `t_bg<270K` está **contaminado por altitud** (Agente 4:
  Láscar 5592m marca 85% "cirrus" solo por fondo nocturno frío de altiplano). El gate t_bg fue
  refutado S86. Cuantificar cirrus real requiere firma path-D + coherencia espacial, no t_bg.
- Esto = el drift **D9/A23 ABIERTO** (path-D contextual sin co-validación). Frente propio.

## Acciones recomendadas (NO implementadas — A45 + brainstorming)
**Ganancia limpia (display, bajo riesgo)**:
1. PCC: renderizar el campo difuso como "extension" (naranja), NO summit-rojo, cuando está
   lejos del cráter físico. O acortar la ventana del mapa (48h/7d) y/o deduplicar por noche/celda.
2. Verificar qué capa pinta el mapa (final_hotspot vs anomaly_pixels footprint).
**Fondo (pipeline, A45, post-reproc, frente propio)**:
3. D9/A23: co-validación BT/NTI para path-D contextual + mejor discriminante de cirrus que t_bg.
   Atacaría la cola de sobre-detección sistémica sin tocar las features reales sub-umbral.

**Conclusión para Nicolás**: no hay un bug nuevo que rompió las detecciones; hay (1) un problema
de DISPLAY que hace ver PCC como cráter-denso siendo campo difuso, y (2) la sobre-detección
sistémica vs MIROVA que es ~recall real (A54) + el drift D9 conocido. Ninguno lo cura el nadir
(magnitud). La magnitud sí mejora con nadir.
