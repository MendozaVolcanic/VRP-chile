# Pre-registro · A/B de D18 — la geometría del ROI1

**Congelado antes de correr el reproceso.** Los criterios de abajo no se
reinterpretan después de ver resultados. Si algo no estaba previsto, se reporta
como observación, no como veredicto.

## La pregunta

Coppola 2016a SP426.5, verbatim: *«the inner region (ROI1) consists of a box
(5 × 5 km) centred on the volcano's summit»*. Una caja de 25 km², **igual para
todos**. Lo nuestro es un círculo de radio `inner_radius_km`, de 3 a 20 km según el
volcán. El ROI1 decide qué umbrales rigen: N·σ 5 / C1 0,003 adentro contra 10 /
0,010 afuera.

**Los brazos**: `_s130_d18_circulo` (control, lo actual) y `_s130_d18_caja`
(`enable_roi1_box_paper: true`, semilado 2,5 km).

## La tensión, explícita

Esto **no** es un A/B donde una opción domina. La caja es **más fiel al canon** y
recorta el terreno donde el sesgo topográfico A69 genera artefacto. Pero la
dirección del cambio es **menos detecciones**, y `mirova_equivalent` prioriza recall
sobre precisión. **Es decisión de misión.** El A/B mide el costo y el beneficio; no
los pondera.

Por eso el criterio **no** puede ser «cero noches perdidas», como en el A/B de los
fondos: acá se *espera* perder detecciones. La pregunta es **cuáles**.

## Qué separa un buen recorte de uno malo

La distinción que decide todo: **¿la caja recorta artefacto o recorta señal?**

- Si recorta **artefacto topográfico** (A69), el clúster debería **acercarse al
  cráter** en los nevados, porque lo que se va es la cola difusa ladera abajo.
- Si recorta **señal real** (cat-b: el Lazufre de Lastarria, el lacolito de PCC),
  se pierden detecciones **sin** que la posición mejore.

Por eso la firma espacial (F4) es la que arbitra, no el conteo.

## Las firmas

| # | firma | qué mide | predicción si la caja recorta ARTEFACTO |
|---|---|---|---|
| **F1** | recall vs noches-ALERTA MIROVA, por sensor | el costo en recall | baja poco (el artefacto no está MIROVA-confirmado) |
| **F2** | ratio mediano nuestro/MIROVA | paridad de magnitud | se acerca a 1 (hoy 0,675 en el subconjunto de S129) |
| **F3** | n detecciones summit | cuánto se recorta | baja, concentrado en nevados |
| **F4** | **offset mediano del clúster al cráter**, por volcán | posición | **baja en los nevados** (A61/A70: mediana, y desglosada por volcán) |

## Estratificación obligatoria (A83 punto 3, A21)

Seis volcanes, elegidos para cubrir los tres regímenes:

| régimen | volcanes | qué se espera |
|---|---|---|
| **focal** (foco compacto real) | Láscar, Lastarria | poco cambio; **Lastarria es el canario del cat-b** (Lazufre) |
| **nevado** (señal débil, A69) | Llaima, Copahue, Villarrica | el mayor recorte: 66-72 % de sus detecciones summit quedan fuera de la caja |
| **difuso** (feature extensa real) | PCC | el lacolito es real; si desaparece, es cat-b destruido |

Nunca leer la mediana agrupada de los seis: promedia regímenes opuestos
([[feedback_s126_estratificar_por_volcan]]).

## Criterio de decisión, congelado

**NO ADOPTAR** si se cumple cualquiera de estas:

1. El recall (F1) cae **más de 3 puntos porcentuales** en cualquier sensor y el
   offset (F4) **no** mejora en los nevados. Sería recortar señal sin ganar nada.
2. **Lastarria pierde más del 20 %** de sus detecciones summit. Es el canario:
   su offset al norte es el campo fumarólico Lazufre, dato de campo, **no**
   artefacto (A84). Si la caja lo borra, borra cat-b real.
3. **PCC pierde más del 50 %** de sus detecciones summit. Su ROI1 es 50,3× el del
   paper, así que va a perder mucho por construcción — pero el lacolito
   (~7 km de offset, 707 km²) es una feature real documentada.

**ADOPTAR es decisión de Nicolás**, y sólo se le propone si:

- el offset del clúster **baja** en los tres nevados (la caja recortó artefacto), **y**
- el recall no cae más de 3 puntos en ningún sensor, **y**
- ni Lastarria ni PCC cruzan sus límites de arriba.

**INCONCLUSO** si los brazos no difieren: sería el escenario del A/B de los fondos
otra vez. Está descartado de antemano —el control de instrumento del PR #577
comprueba que la caja cambia lo que `dual_roi_bt_threshold` declara anómalo, y el
68,9 % de sustrato está medido— pero se verifica igual antes de leer nada más.

## Ventana y costo

**2026-05-29 a 2026-08-24** (87 días), la misma del chunk 2 del A/B anterior, con
buena cobertura de ground truth reciente. Seis volcanes × dos brazos = **12 jobs**.

A15: 87 días × 2,4 min/día ≈ 209 min por job; `timeout-minutes: 330` cubre
209 × 1,3 = 272. El guard `tests/test_guard_timeout_vs_ventana_s129.py` lo verifica.

## Cómo se lee

`experiments/_s130_d18/veredicto_d18.py`, escrito **antes** de que termine el
reproceso (A16), sobre la intersección de pasadas de los dos brazos — sin eso, un
brazo que procesó más granules parece detectar más cuando sólo miró más veces.
