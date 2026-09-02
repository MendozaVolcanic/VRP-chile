# S132 · A/B de `distance_class` en MODIS — decisión #4 de AUDIT_S131 §4

**Veredicto según el criterio pre-registrado: NO ADOPTAR.** Falló C2. Los otros tres
criterios pasaron, y uno de ellos con un margen que vale la pena mirar antes de archivar
el frente. La decisión final es de Nicolás; acá está el número, no la recomendación.

Fuente de verdad de todos los valores: `experiments/_s132/ab_distance_class_modis.json`
(regla S91 — nada transcrito a mano). Detalle por record en
`ab_distance_class_modis_flip.csv`. Ventana: 2025-02-15 a 2026-09-02, 11.749 records MODIS
de los 11 Tier A.

## El fenómeno

`distance_class` decide si una detección se pinta como del cráter o como lejana, y el
dashboard la usa **de compuerta**: `mirovaEqVrp` devuelve 0 cuando la etiqueta no es
`summit`. Hoy sale del `final_hotspot`, que en MODIS es el máximo de radiancia MIR
**absoluta** de la escena.

A 1 km de píxel ese máximo no mide el volcán: mide la topografía. El campo de MIR nocturno
está dominado por el gradiente de altitud (A69) — la cumbre nevada está fría y el valle de
baja altitud tibio —, así que el máximo se va al valle. S131 lo probó contra la propia
escena de MIROVA: su máximo cae a 20,8 km del cráter y el nuestro a 21 km, con correlación
0,023 entre ambos. A esta resolución el MIR absoluto no ve el volcán **tampoco para ellos**.

La medición de esta sesión lo confirma sobre el corpus entero: la mediana de
`final_hotspot_dist_km` de los records que cambiarían de etiqueta es **22,15 km**, y la
mediana de la distancia de su cúmulo es **1,918 km**. Son dos puntos distintos de la misma
escena, y el que decide la etiqueta es el que no mide el volcán.

## Criterio pre-registrado y resultado

Escrito antes de mirar ningún resultado (cabecera de `ab_distance_class_modis.py`).

| | criterio | resultado | |
|---|---|---|---|
| **C1** | Las pasadas TP de MODIS no pueden bajar | **436 → 2.332** | ✅ |
| **C2** | ≥ 80 % del flip con el cúmulo a ≤ 2 km del cráter | **52,73 %** | ❌ |
| **C3** | NdC ≤ 50 % del flip que MIROVA no confirma (artefacto A69) | **8,24 %** | ✅ |
| **C4** | No toca VIIRS (MODIS-only por construcción) | **0 records** | ✅ |

**El flip**: 9.218 records pasarían de `far` a `summit`; **0** en el sentido contrario.
De ellos, 4.026 caen en noches que MIROVA sí publicó y 5.192 no.

## Por qué C2 falló, dicho con honestidad

**El umbral que elegí estaba mal calibrado, y eso no habilita a moverlo.** Fijé 2 km
mientras el corte de la etiqueta es el `inner_radius_km` de cada volcán, que va de 3 km
(Lastarria, Planchón-Peteroa) a 20 km (Puyehue-Cordón Caulle). O sea: C2 exigía algo
*más estricto que el cambio mismo*, y por construcción los 9.218 flips están todos dentro
del inner de su volcán. Los cuartiles de la distancia del cúmulo en el flip son
**1,231 / 1,918 / 2,78 km**: tres cuartos del flip están sobre el edificio.

Lo dejo escrito como falla porque se pre-registró y falló. Mover el poste después de ver
el dato es exactamente lo que el pre-registro existe para impedir (A66). Lo que sí
corresponde es señalar que un futuro A/B de este frente debe expresar C2 en unidades de
`inner_radius`, no en kilómetros fijos.

## Un bug de instrumento que el control atrapó

C4 falló en la primera corrida con 18.468 records no-MODIS «tocados», lo cual es imposible
por construcción. No era el dato: comparar dos columnas de pandas con `!=` cuenta como
distintos los pares NaN/NaN, porque `NaN != NaN` es `True`, y hay exactamente 18.468
records no-MODIS sin `distance_class`. El control estaba midiendo la semántica de pandas.
Corregido con relleno explícito; C4 da 0. Es la razón por la que un A/B lleva un brazo de
control que **no puede** fallar: cuando falla, avisa del instrumento antes de que el
instrumento contamine el veredicto.

## Denominadores (A90)

S131 informó «1.073 de 1.233 detecciones MODIS (87 %) con `far`» sobre la banda de ≤ 2 km
**de una ventana propia**; esta medición corre sobre el corpus completo y da 4.861 records
`far` con el cúmulo a ≤ 2 km, sobre 5.664 MODIS con el cúmulo en esa banda (85,8 %). La
proporción coincide; el total no, porque el denominador es otro. No es una contradicción.

Lo mismo con C1: S131 nombró «65 pasadas TP de MODIS» y acá el conteo antes del flip es
436. Son unidades distintas (noche volcán×fecha contra pasada) y ventanas distintas. **No
reconcilié los dos números**, y lo digo en vez de elegir el que me conviene.

## Lo que queda para Nicolás

El frente **no se cierra ni se adopta acá**. Los datos dicen que la etiqueta está anclada
a un punto que mide topografía y que corregirla multiplicaría por 5,3 las pasadas MODIS
que coinciden con MIROVA. En contra: destaparía además 5.192 records que MIROVA no
publica — que por A54 son en su mayoría anomalías físicamente reales, pero que cambian
mucho lo que el operador ve. Y S113 cerró a propósito esta cara del bug A46 (A81), aunque
midiéndola sobre VIIRS, donde el grueso del flip era el artefacto de NdC; acá NdC aporta
el 8,24 %, así que **ese argumento no se traslada a MODIS**.

El flag `ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER` queda implementado y **apagado**.
