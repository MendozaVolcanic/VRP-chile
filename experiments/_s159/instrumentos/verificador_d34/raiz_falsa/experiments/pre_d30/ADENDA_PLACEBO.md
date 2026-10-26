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
