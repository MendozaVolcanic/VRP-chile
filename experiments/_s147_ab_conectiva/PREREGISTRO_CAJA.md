# Pre-registro de la segunda tanda: la caja de 5 × 5 km del paper (S147)

> **Escrito y commiteado ANTES de correr los brazos G y H.** Complementa a
> [`PREREGISTRO.md`](PREREGISTRO.md), que cubre el brazo F (la conectiva). Misma ventana, mismos
> volcanes, misma referencia congelada, mismo control (el brazo B, sin Test 1).

## 0. Adenda S149: por qué se repite, y qué cambia (escrita ANTES de volver a correr)

**El A/B de S148 no midió la caja.** El flag entregaba la caja sólo al primer pase; el segundo pase
seguía usando el círculo per-volcán y recapturaba con el umbral sensible lo que el primero acababa de
rechazar (`docs/audit_s148/POR_QUE_LA_CAJA_NO_APAGA.md`). Por eso Q1 dio 0 de 61 y Q2 0 de 50 con
tasas idénticas al control: medía el cableado. El arreglo está en `main` desde el PR #738 (las seis
máscaras de summit de los tres procesadores salen de `roi1_summit_mask`), con el flag apagado en
producción y un guard por AST que lo vigila. **Esta es la primera corrida que puede medir D18.**

Lo que cambia respecto del texto de abajo, y nada más:

- **Q1 y Q2 usan los denominadores del control de ESTA corrida**, no los 63 y 42 escritos abajo (que
  eran de otro run; en S148 fueron 61 y 50). La regla es la misma: en Q1 se apaga la mitad o más, con
  redondeo hacia arriba; en Q2 cambia el 12 % o menos (la proporción de 5 sobre 42), con redondeo
  hacia abajo.
- **Q3 se retira como criterio.** No tiene sustrato: centrando la caja en el ancla de detección, que
  es donde la centra el pipeline, hay 0 positivos publicados fuera de la caja sobre 135
  (`experiments/_s148_caja_traza/origen_43_de_135.py`; el "43" de abajo centraba en la coordenada
  nominal). Se informa el conteo y no decide.
- **Se agrega la selectividad a una cola** (C8b, `evaluar.selectividad_supervivencia`, con su nulo
  medido) y el estrato **RUTINA en noche con alerta** (`docs/S149_COSTO_OCULTO_MAX.md`), los dos
  informativos para G y H, porque el recall por pasada solo no ve ese costo.
- **Traza obligatoria si Q1 vuelve a dar cero** (A118): antes de escribir que la caja es inerte,
  contar por etapa (primer pase, recaptura del segundo, cúmulo) qué pasó con los píxeles de fuera de
  la caja, con `experiments/_s148_caja_traza/`.
- Ventana, volcanes, referencia congelada y brazos: los mismos (2026-09-01 a 2026-09-20; B, G y H en
  el MISMO run, para que vean los mismos gránulos). El brazo F de esa ventana ya está evaluado y no
  se repite; la comparación de H contra F usa el F del run 35548121381.

## 1. El fenómeno, primero

Un volcán activo tiene dos zonas con físicas distintas. **Sobre la cumbre** hay una fuente de
calor conocida, y conviene un umbral bajo para no perder una fumarola de alta temperatura o una
grieta caliente recién abierta. **En los flancos y más allá**, lo que aparezca tibio es casi
siempre otra cosa (roca oscura sin nieve, borde de nube, textura del terreno), y conviene un
umbral alto que sólo deje pasar lo que de verdad importa ahí: una colada.

MIROVA implementa exactamente eso, y lo dice con esas palabras. Coppola et al. 2023 (*Front. Earth
Sci.* 11:1240107, p. 3, vista en imagen):

> *"in the summit area (5 × 5 km) slightly lower thresholds are applied to detect the smallest
> thermal anomalies, such as the appearance of high-temperature fumaroles or hot cracks. At
> greater distances, the algorithm uses slightly higher thresholds **which reduce false alerts**,
> while still allowing the prompt detection of effusive activity on the flanks."*

Los números están en la Tabla 1 de Coppola 2016a: de noche, **C1 = 0,003 y C2 = 5 adentro**,
**C1 = 0,01 y C2 = 10 afuera**. El piso sube 3,3 veces y el multiplicador del sigma se duplica.

**La réplica usa los mismos números pero en otra zona**: un círculo de 3 a 20 km según el volcán,
en vez de una caja de 5 × 5 km igual para todos. El círculo de 5 km cubre 3,1 veces la superficie
de la caja; el de 7 km de Tupungatito, 6,2 veces; el de 20 km de Puyehue Cordón Caulle, 50 veces.
En toda esa corona de más aplicamos el umbral permisivo donde MIROVA aplicaría el estricto.

## 2. Lo medido, y la trampa que ya conocemos

Sobre el brazo sin Test 1 (run 35521542153), de los cúmulos que la réplica publica:

| sensor | donde MIROVA alertó | donde MIROVA no vio nada |
|---|---|---|
| VIIRS 375 | 43 de 135 caen **fuera** de la caja (31,9 %) | **63 de 105** (60,0 %) |
| VIIRS 750 | 9 de 13 (69,2 %) | 23 de 36 (63,9 %) |
| MODIS | 0 de 1 | 30 de 39 (76,9 %) |

**Esto NO es una predicción del efecto, y el proyecto ya pagó por confundirlo.** En S130 se midió
que el 42 % de las detecciones tenía su cúmulo fuera de la caja, se presentó como "lo que está en
juego", y el efecto real fue 50 veces menor: casi todas las detecciones **sobrevivían** al umbral
estricto. Contar dónde cae un cúmulo no dice si sobrevive (regla del proyecto: ámbito no es
dependencia). Por eso acá se re-ejecuta en vez de inferir.

**Por qué re-ejecutar algo que S130 ya cerró como NO ADOPTAR.** Porque S130 lo midió con el Test 1
integrado **encendido**, y hoy sabemos dos cosas que entonces no: que ese detector publica por su
cuenta sin mirar los umbrales contextuales, y que satura la tasa de publicación entre 80 y 92 % en
cualquier estrato. Con él encendido la caja sólo podía "redistribuir, no recortar", que es
literalmente lo que S130 encontró. Además su criterio no tenía negativos limpios, que no
existieron como instrumento hasta S139. Es un cierre que hereda las premisas de su medición
(A95, A111).

**Una pista que apunta en contra, y que hay que declarar**: los píxeles del residual casi no
tienen exceso térmico (mediana +0,31 K sobre su fondo, medido contra los TIF de MIROVA de mayo),
así que su dNTI debería estar apenas sobre el piso de 0,003. Si es así, un piso de 0,01 los
apagaría casi todos. Si en cambio sobreviven, es que pasan por la rama del sigma, y entonces la
palanca es la conectiva y no la caja. **Las dos salidas son informativas.**

## 3. Los brazos

| brazo | perfil | qué cambia respecto del control B |
|---|---|---|
| **G** | `_s147_ab_sin_test1_caja` | **una cosa**: `enable_roi1_box_paper: true` |
| **H** | `_s147_ab_sin_test1_caja_max` | **dos**: la caja y la conectiva de prosa. Es la lectura más literal de las dos fuentes juntas |

H no aísla una variable: existe para medir si los dos efectos **se suman o se pisan**. Su lectura
sólo vale junto a F y a G.

**Límite declarado de la caja, que no se toca en este A/B.** El flag centra la caja en el cráter
efectivo de la réplica. MIROVA la centra en el centro de **su** grilla, que según los TIF está a
4,78 km del cráter en Tupungatito, 7,58 km en Puyehue Cordón Caulle y 2,00 km en Planchón
Peteroa. Para esos tres volcanes la caja de este A/B no cae donde cae la de MIROVA. Es una
variable aparte (toca D15 y D17) y se deja fija para no mover dos cosas a la vez; los resultados
se informan **con y sin** esos tres volcanes.

## 4. Las predicciones, con número

Para el brazo G, en VIIRS 375, contra el brazo B:

| # | predicción | umbral | si falla |
|---|---|---|---|
| **Q1** | de los cúmulos residuales que caían **fuera** de la caja, deja de publicarse | **la mitad o más** (32 de 63) | la caja es inerte también sin el Test 1: la baja prioridad de D18 queda confirmada, ahora medida en el régimen correcto |
| **Q2** | los residuales que caían **dentro** de la caja no cambian | cambian **5 o menos** de 42 | el flag toca algo más que el umbral de afuera: revisar el cableado antes de leer nada |
| **Q3** | los positivos de **fuera** de la caja sobreviven, porque MIROVA los alertó bajo sus propios umbrales estrictos | **37 o más** de 43 (85 %) | nuestros umbrales de afuera no equivalen a los de MIROVA, o el centro de la caja importa |
| **Q4** | el recall por pasada aguanta | **118 o más** de 141, sin perder nada de 0,5 MW o más | NO ADOPTAR aunque Q1 se cumpla |

**Q2 es el control interno del instrumento**: la caja no debería tocar lo que está adentro de
ella. Si lo toca, el resultado no se interpreta.

Para el brazo H se informa lo mismo, y además la tasa global de publicación en negativos limpios
contra las de F y G, para ver si los efectos se suman.

## 5. Controles y qué no autoriza

Los mismos del pre-registro del brazo F: cobertura pareja y simétrica contada antes de mirar nada,
identidad del predicado del tablero pineada, referencia y producción congeladas. Y lo mismo que
allá: **nada de esto autoriza un cambio en producción**. Decide qué hipótesis merece el gate
completo del proyecto.
