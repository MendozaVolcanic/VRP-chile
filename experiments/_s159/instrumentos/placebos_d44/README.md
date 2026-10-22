# Placebos de P2 que sí pueden fallar (D-44)

Vara: `experiments/_s157_prereg_d25/NOTA_D44.md` punto 3 (commit `172313c2d`), que nace del hallazgo V42-10 del
verificador de D-42, vuelta 2 (`experiments/_s159/instrumentos/verificador_d42/vuelta2/INFORME.md`). El placebo
anterior, que apagaba al azar publicaciones de K, no podía fallar: 86 % de lo apagado eran alertas, así que GANA era
imposible. Aquí van los tres que sí pueden fallar. Brazos armados desde producción (`sustrato_k.unir_k`), nunca desde
artefactos del A/B. Regla de P2 tal como está hoy (D-34 más la calibración de D-42), sin tocar el evaluador ni las
adendas. El veredicto de D25 no se leyó.

## Cómo

- `placebo_d44.py`: arma K, K' y D, corre el nulo (D = K) y clasifica cada pasada de su tabla. Las clases son las de
  `errores_por_pasada`: alerta bajo 1 MW (etiqueta «pos» no protegida) o negativo limpio. Se toma una pasada sólo si su
  clase es la misma con las reglas original y SN, y quedan fuera los días excluidos de D-29 y, en V1, las alertas que
  sólo están en el OCR de Suomi NPP. Después aplica el placebo y corre el evaluador. Apagar es poner el cúmulo en
  0,0 MW; encender, poner un cúmulo de cumbre de 0,3 MW dentro del radio interno. Cada semilla cuenta cuántas pasadas
  tocadas llegaron cambiadas a la tabla: en las 444 corridas, todas, y ninguna otra cambió.
- Ventana tipo V1: 2026-09-18 a 10-18, 7 volcanes, K, K' y D, con los días de D-29 excluidos. Tipo V2: 2026-04-01 a
  06-12, 6 volcanes, K y D, tabla sola. 20 semillas por punto; con 100 % todas las semillas apagan lo mismo y basta una
  corrida. En el simétrico al 50 % agregué semillas: 100 en V1 y 60 en V2.
- `evaluar_sin_m.py`: el evaluador tal cual, sin calcular M (M queda SIN SUSTRATO). P2 se decide antes que M y no lee
  nada de M, y M con sus calibraciones era casi todo el tiempo de cada corrida. Control (`comparar_sin_m.py`, salidas
  `comparar_sin_m_V1.txt` y `_V2.txt`): con la misma semilla, el evaluador entero y el atajo dan **P2 idéntico** en las
  dos reglas y los dos sensores, y las mismas pasadas cambiadas en la tabla.
- `resumir_d44.py`, salida `resumen_d44.txt`. Celda = semilla × regla × sensor. Un punto vale como control si la
  calibración corrió en más de la mitad de sus celdas. Como las clases se eligieron iguales en las dos reglas, original
  y SN dieron lo mismo en todas las semillas, y la cuenta honesta es semilla × sensor (celdas independientes). Así se
  informa.

## Composición de lo que K publica (lo pidió el verificador)

Tabla del nulo, sin días excluidos:

| ventana | sensor | publica K | alertas bajo 1 MW | negativos limpios | % de negativos entre las publicadas | % entre alertas y negativos | sin publicar: alertas / negativos |
|---|---|---|---|---|---|---|---|
| V1 | VIIRS 375 | 230 | 80 | 11 | 4,8 % | 12,1 % | 3 / 280 |
| V1 | VIIRS 750 | 55 | 8 | 10 | 18,2 % | 55,6 % | 11 / 487 |
| V2 | VIIRS 375 | 776 | 284 | 22 | 2,8 % | 7,2 % | 8 / 330 |
| V2 | VIIRS 750 | 195 | 49 | 17 | 8,7 % | 25,8 % | 22 / 840 |

El resto de lo publicado son protegidas, pasadas sin etiqueta útil o con clase distinta entre reglas, y no cuentan
en P2.

## (a) Poder: apagar publicaciones en negativos limpios (tiene que dar GANA)

| punto | apagadas | celdas calibradas | resultado (semilla × sensor) |
|---|---|---|---|
| V1 10 % | 2 | 0 de 80 | SIN SUSTRATO; no vale |
| V1 25 % | 5 | 0 de 80 | SIN SUSTRATO; no vale |
| V1 50 % | 11 | 80 de 80 | **GANA 40 de 40** |
| V1 100 % | 21 | 4 de 4 | GANA en VIIRS 750; **INDECIDIBLE en VIIRS 375** |
| V2 10 % | 4 | 0 de 80 | no vale |
| V2 25 % | 10 | 40 de 80 (VIIRS 375 completo) | VIIRS 375 GANA 20 de 20; VIIRS 750 sin sustrato; no vale |
| V2 50 % | 19 | 80 de 80 | **GANA 26 de 40, INDECIDIBLE 14** |
| V2 100 % | 39 | 4 de 4 | GANA 2 de 2 |

Nunca sale PIERDE ni BLOQUEA. **Pero donde hay sustrato no siempre da GANA.** Los INDECIDIBLE son todos del mismo
tipo: todas las discordantes van a favor de D y, sin calibrar, dan GANA, pero hay una noche con dos pasadas y las
demás con una (11 discordantes en 10 noches, u 8 en 7). En esos casos la calibración da 4,9 a 6,7 % de falsos por
cola, y basta una cola sobre el tope para que el sensor quede INDECIDIBLE. En cambio, con 5 o 6 noches de una pasada cada una
(V1 al 50 %), la cola mayor de cada celda queda entre 2,1 y 3,8 % y todas deciden GANA. O sea, la regla calibrada no es monótona en el sustrato: una noche con dos pasadas
discordantes puede bajarle el poder más que tener menos noches.

## (b) Dirección: apagar publicaciones en alertas bajo 1 MW (tiene que dar PIERDE)

| punto | apagadas | celdas calibradas | resultado (semilla × sensor) |
|---|---|---|---|
| V1 10 % | 9 | 40 de 80 (VIIRS 375 completo) | VIIRS 375 PIERDE 16 de 20, INDECIDIBLE 4; no vale |
| V1 25 % | 22 | 40 de 80 | VIIRS 375 PIERDE 19 de 20, INDECIDIBLE 1; no vale |
| V1 50 % | 44 | 40 de 80 | VIIRS 375 PIERDE 20 de 20; no vale |
| V1 100 % | 88 | 4 de 4 | PIERDE en VIIRS 375; **INDECIDIBLE en VIIRS 750** (8 en 7 noches) |
| V2 10 %, 25 %, 50 % | 33, 83, 166 | 80 de 80 cada uno | **PIERDE 40 de 40 en cada punto** |
| V2 100 % | 333 | 4 de 4 | PIERDE 2 de 2 |

En V1 los puntos de 10 a 50 % no valen como control sólo porque VIIRS 750 tiene 8 alertas publicadas y queda sin
sustrato; en VIIRS 375 sí hay. Nunca sale GANA. Los INDECIDIBLE son el mismo caso de la noche con dos pasadas.

## (c) Simétrico: efecto esperado 0 (GANA y PIERDE en 5 % o menos por cola)

**Cómo se garantiza el 0.** La receta literal del pedido («apagar el p % de las publicaciones de K y encender el p %
de las no publicadas, en la proporción de la población») no puede dar esperado 0 con K: casi no hay alertas bajo 1 MW
sin publicar. Hay 3 en VIIRS 375 de V1; en la primera prueba se pidieron 18 encendidas en VIIRS 375 y sólo hubo pozo
para 7. Lo implementé así: cada pasada tocada aporta +1 o -1 con probabilidad exacta 1/2. Del lado +1 están las alertas
publicadas, que se apagan, y los negativos sin publicar, que se encienden; del lado -1, los negativos publicados (se
apagan) y las alertas sin publicar (se encienden). Por sensor se tiran n = round(2 · p · M) monedas justas, con M el
tamaño del lado -1. Cada moneda toma, sin reposición, una pasada al azar del lado que salió. En la misma semilla hay
apagadas y encendidas. La moneda nunca pidió más de lo que había en el pozo («faltaron» 0 en todos los puntos).

**Medido.** La media del neto de P2 sobre las semillas queda en 0 dentro de su intervalo en los 8 casos (punto ×
sensor): de -0,30 a +0,80, con todos los intervalos cruzando 0.

| punto | semillas | celdas calibradas | GANA (semilla × sensor) | PIERDE | BLOQUEA |
|---|---|---|---|---|---|
| V1 25 % | 20 | 80 de 80 | 0 de 40 (Wilson 0 a 9 %) | 0 de 40 | 13 de 40 |
| V1 50 % | 100 | 400 de 400 | 6 de 200 (3 %, 1 a 6 %) | 5 de 200 (2 %, 1 a 6 %) | 95 de 200 |
| V2 25 % | 20 | 80 de 80 | 0 de 40 | 0 de 40 | 21 de 40 |
| V2 50 % | 60 | 240 de 240 | 1 de 120 (1 %, 0 a 5 %) | 2 de 120 (2 %, 0 a 6 %) | 58 de 120 |
| **todos** | | | **7 de 400 (2 %, 1 a 4 %)** | **7 de 400 (2 %, 1 a 4 %)** | |

Por sensor, en V1 al 50 % con 100 semillas: GANA 3 % y PIERDE 2 % en VIIRS 375; 3 % y 3 % en VIIRS 750. **El criterio
se cumple: 5 % o menos por cola en cada punto y en el total.** Con las primeras 20 semillas, V1 al 50 % daba PIERDE 2
de 20 en VIIRS 750 (10 %, Wilson 3 a 30 %); por eso agregué 80 semillas, y el número bajó a 3 %. BLOQUEA aparece en
33 a 53 % de las celdas del nulo: es lo que ya midió V34-02 y Nicolás eligió en D-34. Lo informo para que nadie lea un
BLOQUEA como señal.

## Preguntas para Nicolás (no inventé regla)

1. **(a) y (b) con sustrato no siempre deciden.** Con todas las discordantes a favor (o en contra) de D, un sensor
   queda INDECIDIBLE cuando hay una noche con dos pasadas y las demás con una (11 en 10 noches, 8 en 7). La calibración
   cae justo sobre el 5 % en una cola (4,9 a 6,7 %). Pasó en 14 de 40 celdas de V2 (a) al 50 %, en VIIRS 375 de V1 (a)
   al 100 % y en VIIRS 750 de V1 (b) al 100 %. Nunca dio la dirección equivocada. Es una propiedad de la regla sellada
   (el tope del 5 % por cola sobre un nulo de bloques desiguales), no del código. ¿Se acepta esa pérdida de poder, como
   se aceptó la de 4 noches o menos en D-44?
2. Lectura que apliqué en (c): el esperado 0 se garantiza con la moneda justa por pasada (arriba), no con la receta
   literal, que con K no puede dar 0.

## Lo que no hice y salvedades

- No toqué el evaluador, las pruebas ni las adendas. Por eso no volví a correr la suite: `git status` sólo muestra
  esta carpeta.
- El atajo sin M está validado con una semilla por ventana (P2 idéntico); no con todas.
- V1 tiene 7 volcanes y un mes; los brazos son producción con K, no el A/B. Lo encendido es un cúmulo artificial de
  0,3 MW: mide la regla, no la física de un detector.
- Sobre V42-11 (verificador, vuelta 2): mi corrida de suite y probar del cierre anterior empezó después de que el
  corredor de mutaciones terminó. Su resumen había llegado antes, y antes de `status_antes_v42.txt` conté 0 procesos de
  Python vivos. La suma de duraciones del corredor no se solapa con esa ventana.
- Sin verificador limpio todavía; NOTA_D44 lo pide.
