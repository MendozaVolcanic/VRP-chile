# Segunda adenda al pre-registro de D25 sobre K: el placebo como comparador de M, no como compuerta

**SELLADA por Nicolás el 2026-10-21 (D-28).** Respuesta textual, registrada por la sesión dueña del loop (S159):
«Placebo como comparador y no como compuerta, por adenda sellada.» Elige la opción (b) de
`experiments/_s159/instrumentos/NOTAS.md` (§ «Decisiones pendientes», punto 1, en la rama de #889). El hash del commit
que deja este texto se anota en la bitácora del loop (`tasks/LOOP_OBJETIVOS.md` §6) al subirlo. Escrita **antes** de
leer el veredicto de V1, V2a y V2b, que siguen sin leer. Todo lo que esta adenda no toca rige como está en
`PREREGISTRO.md` y en `ADENDA_CALIBRACION.md` (D-27).

## 1. El choque que resuelve

La métrica M pregunta si D queda más cerca del VRP de MIROVA que K, con
d = |log10(D/MIROVA)| − |log10(K/MIROVA)|. K queda **bajo** MIROVA en los estratos que deciden (razón mediana 0,52 a
0,66), así que cualquier brazo que sólo suba la magnitud se acerca. Medido con los pares reales de K
(`experiments/_s159/instrumentos/placebo_real_salida.txt`): un brazo K×1,2, que no es ningún mecanismo, da MEJORA con
la calibración sellada en VIIRS 750 con cenit hasta 40° y en VIIRS 375 sin kernel con cenit hasta 40°, en V1 y en V2.
Con el placebo como **compuerta** (la versión de #890 en `1438c8fff`), D25 sale INVALIDO POR INSTRUMENTO en las dos
ventanas haga lo que haga. Con el placebo **fuera**, M no distingue a D25 de una ganancia cualquiera.

Se espera que D25 suba la magnitud (los vecinos del cráter son más fríos que el anillo, probe del L1B de Chillán). Lo
que importa no es si sube en promedio sino si sube **los pares que debe subir**.

## 2. La regla nueva

Para cada estrato que decide o bloquea, con sus pares (K, D, MIROVA):

1. **Ganancia del comparador**: ĝ = mediana de D/K sobre los pares del estrato (en escala logarítmica, la mediana de
   log10(D/K)). Es la ganancia uniforme del mismo tamaño que el efecto típico de D25 en ese estrato.
2. **Diferencia contra el comparador**: d′ = |log10(D/MIROVA)| − |log10(ĝ·K/MIROVA)|. Negativa cuando D queda más
   cerca de MIROVA que una ganancia uniforme del mismo tamaño.
3. **MEJORA** cuenta sólo si se cumplen **las dos**: la regla sellada sobre d da MEJORA (calibración simétrica y opción
   A, como en D-27) **y** la misma regla sobre d′ da MEJORA (intervalo al 95 % por bloques noche-volcán entero bajo 0,
   calibración simétrica de d′ con su propio tope por cola, y mediana de d′ negativa en al menos dos volcanes con 3
   pares o más). Si d da MEJORA y d′ no, el estrato queda **NEUTRO** con la nota «sube en promedio, no en los pares
   correctos».
4. **EMPEORA** se sigue juzgando sobre d (D contra K), como está sellado: un brazo que se pasa de MIROVA o se aleja de
   ella no puede quedar escondido detrás del comparador. El estrato VIIRS 375 sin kernel con cenit sobre 40° sigue
   pudiendo sólo bloquear (sello §8 a).
5. **La compuerta se retira.** Ningún placebo vuelve INVALIDO el veredicto. El evaluador sigue informando, por estrato,
   lo que la regla da sobre K×1,2 y K×0,8 (sin comparador) y ĝ, para que quede a la vista cuánto de la mejora es
   ganancia.

## 3. Detalles de implementación que derivan de (b)

No los eligió Nicolás uno por uno; salen de la definición de (b). Si alguno le parece mal, se cambia **antes** del tag
de lectura, nunca después.

- **ĝ se recalcula en cada réplica del bootstrap** con los mismos pesos por bloque que la mediana de d′, para que la
  incertidumbre de ĝ entre en el intervalo. En la calibración simétrica, ĝ queda fijo en su estimación puntual (la
  calibración prueba la regla bajo el nulo, no a ĝ).
- **ĝ es uno por estrato**, no uno por volcán. Límite declarado: un D25 cuyo efecto sea una ganancia distinta pero
  uniforme dentro de cada volcán (1.14 midió ×1,72 en Isluga y ×2,37 en Tupungatito) puede pasar d′ sin ser «el
  mecanismo correcto» en el sentido fino. Se informa ĝ por volcán junto al veredicto; no decide.
- **Control de la regla, obligatorio antes del tag** (A110 y A116, el nulo se mide, no se razona):
  (i) D = K×1,2 y D = K×0,8 sobre los pares reales de V1 y V2: d′ es idénticamente 0, así que **no puede** dar MEJORA;
  (ii) el caso `sellada` de las pruebas (D a mitad de camino hacia MIROVA en escala log) **tiene** que seguir dando
  MEJORA con al menos dos volcanes; (iii) K×0,8 sigue dando EMPEORA por d; (iv) mutaciones atrapadas por aserción: el
  comparador no se aplica, ĝ fijo en 1, EMPEORA juzgado sobre d′ en vez de d, la compuerta reaparece.
- **Verificador con contexto limpio** del cambio del evaluador antes del tag, como en D-27.

## 4. Lo que esta adenda no decide

- **Los días que CMR no sirve** (17 al 20 de octubre, parciales el 17 y el 20 y vacíos el 18 y el 19 al 2026-10-21, más
  el 13 parcial): la relectura de D25 espera esa decisión aparte (decisión 3 del bloque de arranque S159).
- **El brazo con el fondo del código de MIROVA** va al pre-registro nuevo (R2.3), no a D25.

## 5. Respuestas de Nicolás (D-30) y poder declarado antes del tag

Agregado el 2026-10-21, después de la implementación (`b4258040c`) y del verificador con contexto limpio
(`experiments/_s159/instrumentos/verificador_comparador/INFORME.md`, commit `63e310af5`), **antes** de leer el
veredicto de V1, V2a y V2b, que siguen sin leer. El §1 a §4 no cambian.

### 5.1 Las cinco respuestas

Respuesta textual de Nicolás (D-30, 2026-10-21), registrada por la sesión dueña del loop: «Acepto tus recomendaciones
para las cinco preguntas de la adenda D-28: INDECIDIBLE si falla la calibración de d′, sólo la cola de mejora en esa
calibración, la lectura del caso sellada como el brazo a mitad de camino, el comparador apagado con --calibracion
sellada, y los tres detalles numéricos.»

1. **Si d da MEJORA y la calibración de d′ falla, el estrato queda INDECIDIBLE**, no NEUTRO. Como en D-27, un estrato
   cuya calibración falla no decide, y aquí d′ es condición necesaria del MEJORA: no se sabe si lo hay. Con eso la
   ventana entera queda INDECIDIBLE (`global_ventana`).
2. **La calibración de d′ exige sólo la cola de MEJORA**, porque d′ sólo se usa para MEJORA (lo mismo que D-27 hace en
   el estrato que sólo bloquea). La cola EMPEORA de d′ se informa y no decide.
3. **El «caso `sellada`» del §3 (ii) es el brazo a mitad de camino hacia MIROVA con la calibración simétrica**
   (`mejora750` en `probar_evaluar_d25.py` y la prueba unitaria con dispersión de K de 0,3), no el caso que en ese
   script se llama `sellada`, que corre con la calibración anterior a D-27.
4. **Con `--calibracion sellada` el comparador queda apagado**, y el JSON de salida marca ese veredicto con
   `vale_para_decidir: false`; `--combinar` arrastra la marca.
5. **Los tres detalles numéricos** quedan como están: d′ redondeado a 1e-12 en log10, el ĝ puntual como mediana sin
   pesos sobre los pares, y una semilla propia para la calibración de d′. Cuál semilla y cuántas repeticiones quedó
   abierto en D-30 (el verificador midió que con `SEMILLA + 3` y 200 repeticiones V2 VIIRS 750 z<=40 da 11 falsos
   MEJORA de 200 contra un tope de 10, hallazgo H2, y eso, con la respuesta 1, dejaba INDECIDIBLE la ventana V2 cuando
   d da MEJORA ahí). Lo cerró D-32, en el §5.3.

### 5.3 Semilla y repeticiones de la calibración de d′: sellado antes del tag (D-32)

Respuesta textual de Nicolás (D-32, 2026-10-21): «Sí: sube las repeticiones de la calibración de d′ (por ejemplo a
1.000) y sella esa semilla y ese número antes del tag, para que una sola semilla no decida V2 VIIRS 750.»

**Sellado antes del tag**: la calibración de d′ corre con **1.000 repeticiones** (`N_CALIB_DPRIMA` en `evaluar_d25.py`)
y la **semilla 160** (`SEMILLA_CALIB_DPRIMA`, que es `SEMILLA + 3`, la misma de `b4258040c`). El tope sigue siendo el
5 % de la cola de MEJORA: **50 de 1.000**. La calibración de d (D-27) no cambia: 200 repeticiones.

Medido sobre los mismos pares reales de K y el mismo D sintético que usó el verificador (a mitad de camino hacia
MIROVA, con ruido 0,05 del generador 205, y sin ruido), con la semilla 160
(`experiments/_s159/instrumentos/calib_dprima_1000_salida.txt`, script `calib_dprima_1000.py`). Con 200 repeticiones el
script reproduce lo del verificador (10 y 11 de 200), y eso es su control.

| V2 VIIRS 750 z<=40 (64 pares) | 200 repeticiones (tope 10) | 1.000 repeticiones (tope 50) |
|---|---|---|
| mitad de camino, con ruido 0,05 | 11 falsos MEJORA: falla | 31 falsos MEJORA: calibrada |
| mitad de camino, sin ruido | 10 falsos MEJORA: en el tope | 29 falsos MEJORA: calibrada |

En los otros tres estratos que deciden en la misma salida, con 1.000 repeticiones los falsos MEJORA van de 20 a 28 de
1.000.

La curva de poder del §5.2 se midió con 200 repeticiones, antes de D-32. En V2 VIIRS 750 z<=40 la calibración de d′
fallaba ahí en 0 a 5 de las 12 corridas de cada celda (`poder_salida.txt`, última columna); con 1.000 esa parte puede
cambiar y **no se volvió a medir**.

### 5.2 Poder del comparador, medido antes del tag

Medido por el verificador sobre los pares reales de K (V1 y V2, sin ningún brazo del A/B), con un brazo que lleva cada
par una fracción alfa del camino hacia MIROVA en log10 y le suma un ruido lognormal por pasada de desviación sigma,
12 semillas por celda (`experiments/_s159/instrumentos/verificador_comparador/poder_salida.txt`, script `poder.py`). La
columna cuenta un CUMPLE aproximado: MEJORA final en algún estrato de V1 y en alguno de V2 con la misma semilla, con
P1 y P2 dados por buenos. Con sigma 0 es una sola corrida (no hay ruido que sortear).

| alfa | sigma (log10) | con comparador (D-28) | sólo con d (D-27) |
|---|---|---|---|
| 0,50 | 0,00 | 1 de 1 | 1 de 1 |
| 0,50 | 0,03 | 12 de 12 | 12 de 12 |
| 0,50 | 0,05 | 12 de 12 | 12 de 12 |
| 0,50 | 0,075 | 7 de 12 | 12 de 12 |
| 0,50 | 0,10 | 1 de 12 | 12 de 12 |
| 0,50 | 0,15 | 0 de 12 | 12 de 12 |
| 0,25 | 0,00 | 1 de 1 | 1 de 1 |
| 0,25 | 0,03 | 7 de 12 | 12 de 12 |
| 0,25 | 0,05 | 3 de 12 | 12 de 12 |
| 0,25 | 0,075 | 0 de 12 | 12 de 12 |
| 0,25 | 0,10 | 0 de 12 | 12 de 12 |
| 0,25 | 0,15 | 0 de 12 | 7 de 12 |

O sea: con ruido por pasada de 0,05 en log10, un efecto a mitad de camino da CUMPLE en 12 de 12; con 0,10 baja a 1 de
12; y con alfa 0,25 y ruido de 0,075 o más da 0 de 12. Un ruido de 0,10 en log10 es un factor de más o menos 26 % por
pasada, menos de la mitad de la dispersión que K ya tiene contra MIROVA en esos estratos (0,21 a 0,39).

El poder depende además de cuánto varía K contra MIROVA de un par a otro: si todos los pares quedaran bajo MIROVA en la
misma proporción, ningún mecanismo se distinguiría de una ganancia. Con el brazo a mitad de camino sin ruido sobre pares
sintéticos (`experiments/_s159/instrumentos/verificador_comparador/mitad_dispersion_salida.txt`), la regla final da
NEUTRO con dispersión de K de 0,03 y de 0,10 en log10, y MEJORA con 0,20 y 0,30.

Por eso, un SIN EFECTO no distingue «D25 no acerca» de «D25 acerca con dispersión».
