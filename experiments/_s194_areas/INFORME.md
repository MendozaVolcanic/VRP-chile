# Laboratorio por áreas, opción A: partición posterior de los alertados (S194)

Diseño: `docs/superpowers/specs/2026-11-22-laboratorio-areas-design.md` (rama `loop/activo`), con las respuestas de
Nicolás del 2026-11-22 (AR1: empezar por A; AR2 y AR4: cráter, agua, flanco y resto, sin área de incendio). Sólo
lectura de `data/mirova_equivalent/`: no toca `pipeline/`, perfiles, tablero ni ningún valor publicado.

Archivos (todos en `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\`):

- Áreas: `config\areas_laboratorio.yaml`.
- Partición: `experiments\_s194_areas\particion.py` (salida `particion_salida.txt`, `resumen.json`).
- Recurrencia, densidades y alertas sobre agua: `experiments\_s194_areas\recurrencia.py` (salida
  `recurrencia_salida.txt`, `recurrencia.json`).
- Cruce con el marcador de la cumbre (#1091): `experiments\_s194_areas\cruce_marcador.py` (salida
  `cruce_marcador_salida.txt`).
- Mapas: `experiments\_s194_areas\mapas\<Volcan>.png` (`mapas.py`).
- Pruebas: `tests\test_particion_areas_s194.py` (10 pruebas).
- Tablas por pasada y por píxel (grandes, no versionadas): `D:\vrp-trabajo\temporales\s194_areas\pasadas.csv.gz` y
  `pixeles.csv.gz`; se regeneran con `particion.py`.

Todos los números de este informe salen de esas salidas; ninguno se transcribió de memoria.

## 1. El fenómeno y la pregunta

En una noche, la grilla de 51 × 51 km alrededor de un volcán puede tener calor en varios sitios a la vez: un píxel tibio
en el cráter, roca o salar que guarda el calor del día en el altiplano, un incendio en un valle, la orilla de un lago que
a esa hora está más tibia que la tierra. El tablero resume cada pasada en un solo punto (regla «radiante»: el cúmulo
más radiante), y lo demás no se ve. La pregunta de Nicolás es qué pasa dentro de la escena, por zonas. Esta primera
respuesta usa sólo lo que ya está publicado: los alertados que cada record guarda en `anomaly_pixels` (el censo de #1091
comprobó que la vía los guarda todos), repartidos por su posición.

## 2. Cómo se reparte

**Áreas excluyentes, en este orden de precedencia** (la primera que contiene al centro del píxel se lo queda):

1. **cráter**: `dist_km` del píxel menor o igual a `inner_radius_km` de `volcanoes.yaml` (KML de MIROVA). `dist_km` es la
   distancia que guarda la vía, medida en la grilla desde el cráter, y es la misma que decide `distance_class`: el cráter
   de la partición es la «cumbre» del tablero. El lago cratérico de Copahue cae aquí.
2. **agua**: el centro del píxel dentro de un polígono de `frontend/agua/<Volcan>.geojson` (JRC Global Surface Water,
   ocurrencia ≥ 50 %, la capa del mapa desde #1079).
3. **flanco**: entre `inner_radius_km` y 10 km (radio provisional igual en todos, AR3 sin respuesta).
4. **resto**: lo demás.

**Volcanes:** los 11 Tier A menos Puyehue Cordón Caulle. **Pasadas:** records de la vía «código MIROVA» desde el
2025-02-15, sólo nocturnas (`dayflag` 0 del .m y Sol bajo el horizonte; quedaron fuera 4 diurnas). **Noche:** una pasada
antes de las 12 UTC pertenece a la noche que empezó el día anterior.

**El VRP por área se reconstruye, porque el record no guarda VRP por píxel.** `anomaly_pixels` trae posición, distancia y
temperatura de brillo MIR (`bt_k`), no potencia. El .m calcula la potencia como el coeficiente de Wooster por la
radiancia de todos los alertados menos el fondo interpolado bajo ellos, y el record guarda esos dos totales
(`L_hot`, `L_bk` en `diag_codigo_mirova`). La partición recupera la radiancia de cada píxel invirtiendo Planck desde su
`bt_k` (la misma función del port) y reparte el fondo total por partes iguales entre los alertados. Así la suma de las
áreas devuelve exactamente la potencia del record (D32); lo aproximado es cómo se reparte el fondo entre áreas (crítica
1).

**Controles (`particion_salida.txt`, pruebas):**

- Cierre: en las 8.997 pasadas con alertados, la suma de las áreas da el `vrp_mw` del record dentro de una tolerancia
  derivada del redondeo de `bt_k` a 0,01 K (la peor razón error/tolerancia fuera del caso siguiente es 0,983). La única
  pasada fuera de tolerancia es Nevados de Chillán MODIS_TERRA 2025-11-18 03:00: la suma da -0,032 MW y el record guarda 0,
  porque `store.py` lleva a 0 una potencia negativa (A10, marca S190). Se acepta por esa regla, explícita en el código.
- La radiancia reconstruida desde `bt_k` difiere de `L_hot` guardado en 342 partes por millón como máximo.
- `anomaly_pixels` completo en las 8.997 (0 records con `len` distinto de `n_anomalous_pixels`).
- Pruebas sintéticas: un píxel en cada área cae donde debe; el cráter le gana al agua; la suma cuadra en las tres
  familias; un `vrp_mw` alterado en 10 % hace fallar el cierre; el borde se marca; un píxel sobre una isla de un lago es
  tierra. Ocho mutaciones del script (sin cráter, sin fondo, sin borde, sin flanco, sin agua, islas como agua, cierre
  siempre verdadero, aceptar diurnas): las ocho hacen fallar las pruebas.
- La geometría no usa shapely (no está en `requirements.txt`, y la prueba corre en el CI): punto en polígono con
  matplotlib y distancia al borde a mano. Comparada con una primera corrida hecha con shapely, la tabla por píxel
  (28.526 alertados, área y borde) sale idéntica byte a byte.
- **Cruce con el marcador de la cumbre (#1091):** en su ventana (noches 2026-03-01 a 2026-11-18) y sin Cordón Caulle, la
  partición cuenta 214 pasadas lejanas con alertados en el cráter (MODIS 1, VIIRS 375 211, VIIRS 750 2); el marcador
  cuenta 214 (218 menos 4 de Cordón Caulle), con el mismo reparto por sensor. Son el mismo predicado por dos caminos.

## 3. Resultados

Universo: 66.747 pasadas nocturnas de la vía en los 10 volcanes; 8.997 con detección (MODIS 469, VIIRS 375 6.844,
VIIRS 750 1.684).

### 3.1 Dónde cae el calor

Porcentaje de las pasadas con detección que tienen al menos un alertado en cada área (una pasada puede tener calor en
varias, por eso no suman 100):

| Volcán | Familia | Pasadas | Con detección | Cráter | Agua | Flanco | Resto |
|---|---|---|---|---|---|---|---|
| Láscar | MODIS | 1191 | 362 | 99,7 | 0,0 | 0,0 | 0,6 |
| Láscar | VIIRS 375 | 2270 | 1493 | 93,7 | 0,3 | 2,0 | 17,4 |
| Láscar | VIIRS 750 | 2407 | 982 | 99,3 | 0,1 | 0,2 | 0,8 |
| Isluga | MODIS | 1144 | 3 | 33,3 | 0,0 | 0,0 | 66,7 |
| Isluga | VIIRS 375 | 2261 | 1347 | 92,8 | 0,0 | 1,8 | 18,0 |
| Isluga | VIIRS 750 | 2329 | 279 | 96,8 | 0,0 | 0,4 | 3,2 |
| Lastarria | MODIS | 1193 | 0 | | | | |
| Lastarria | VIIRS 375 | 2275 | 1160 | 82,3 | 0,1 | 4,2 | 25,7 |
| Lastarria | VIIRS 750 | 2487 | 14 | 14,3 | 0,0 | 21,4 | 64,3 |
| Tupungatito | MODIS | 1326 | 0 | | | | |
| Tupungatito | VIIRS 375 | 2573 | 1172 | 91,1 | 0,0 | 0,9 | 14,3 |
| Tupungatito | VIIRS 750 | 2686 | 116 | 88,8 | 0,0 | 6,0 | 8,6 |
| Planchón-Peteroa | MODIS | 1389 | 15 | 86,7 | 0,0 | 0,0 | 13,3 |
| Planchón-Peteroa | VIIRS 375 | 2631 | 671 | 82,7 | 0,1 | 2,2 | 20,7 |
| Planchón-Peteroa | VIIRS 750 | 2709 | 66 | 84,8 | 0,0 | 1,5 | 13,6 |
| Nevados de Chillán | MODIS | 1397 | 76 | 76,3 | 0,0 | 0,0 | 23,7 |
| Nevados de Chillán | VIIRS 375 | 2658 | 332 | 45,8 | 0,0 | 9,3 | 47,3 |
| Nevados de Chillán | VIIRS 750 | 2859 | 166 | 69,3 | 0,0 | 4,2 | 27,1 |
| Copahue | MODIS | 1414 | 7 | 0,0 | 0,0 | 0,0 | 100,0 |
| Copahue | VIIRS 375 | 2742 | 159 | 29,6 | 0,6 | 5,7 | 65,4 |
| Copahue | VIIRS 750 | 2849 | 25 | 0,0 | 0,0 | 0,0 | 100,0 |
| Llaima | MODIS | 1411 | 4 | 25,0 | 0,0 | 0,0 | 75,0 |
| Llaima | VIIRS 375 | 2812 | 106 | 9,4 | 0,0 | 8,5 | 83,0 |
| Llaima | VIIRS 750 | 2921 | 10 | 20,0 | 0,0 | 0,0 | 80,0 |
| Villarrica | MODIS | 1433 | 1 | 100,0 | 0,0 | 0,0 | 0,0 |
| Villarrica | VIIRS 375 | 2857 | 120 | 69,2 | 5,0 | 4,2 | 25,8 |
| Villarrica | VIIRS 750 | 2924 | 11 | 90,9 | 0,0 | 0,0 | 9,1 |
| Chaitén | MODIS | 1562 | 1 | 100,0 | 0,0 | 0,0 | 0,0 |
| Chaitén | VIIRS 375 | 2977 | 284 | 93,0 | 1,4 | 0,4 | 6,3 |
| Chaitén | VIIRS 750 | 3060 | 15 | 100,0 | 0,0 | 0,0 | 0,0 |

Lectura geológica: donde hay actividad persistente en el cráter (Láscar, Isluga, Tupungatito, Planchón-Peteroa,
Lastarria en VIIRS 375), el calor está casi siempre en el cráter, y MODIS y VIIRS 750, con píxeles de 1 km y 750 m, casi
sólo ven el cráter. Fuera del cráter, lo que más pesa es el «resto», y casi siempre en VIIRS 375. En Copahue y Llaima,
en cambio, la mayor parte de las detecciones no tiene nada en el cráter: lo que el detector ve en esas grillas está lejos
del volcán (3.5).

### 3.2 Calor a la vez en el cráter y fuera: lo que la regla «radiante» puede esconder

De las 8.997 pasadas con detección, **624 tienen calor en el cráter y a la vez en otra área** (resto 569, flanco 58, agua
2; una pasada puede tener más de una). **528 de esas 624 se publican lejanas**: el cúmulo de fuera ganó por radiancia y
el operador no ve que también hubo calor en la cumbre. Las otras 96 se publican en la cumbre con calor también fuera, que
tampoco se ve. Es casi todo VIIRS 375: 618 de las 624 (MODIS 1, VIIRS 750 5).

Por volcán, en VIIRS 375 (pasadas con cráter y otra área; de ellas, publicadas lejanas):

| Volcán | Con detección | Cráter y otra área | Publicadas lejanas | Con el flanco | Con el resto |
|---|---|---|---|---|---|
| Láscar | 1493 | 196 | 115 | 17 | 178 |
| Isluga | 1347 | 168 | 162 | 16 | 152 |
| Lastarria | 1160 | 132 | 132 | 17 | 119 |
| Tupungatito | 1172 | 73 | 71 | 1 | 72 |
| Planchón-Peteroa | 671 | 37 | 35 | 3 | 34 |
| Nevados de Chillán | 332 | 6 | 3 | 1 | 5 |
| Villarrica | 120 | 3 | 3 | 0 | 3 |
| Chaitén | 284 | 2 | 2 | 0 | 2 |
| Copahue | 159 | 1 | 1 | 0 | 1 |
| Llaima | 106 | 0 | 0 | 0 | 0 |

En Isluga y Lastarria casi toda pasada con calor en el cráter y fuera termina publicada lejana (162 de 168, 132 de
132): el calor del cráter es débil y cualquier cúmulo de fuera lo supera. En Láscar el cráter gana más a menudo (115 de
196 lejanas). Esto amplía al período completo lo que el marcador de la cumbre (#1091) midió en su ventana; donde las dos ventanas se
solapan, los conteos coinciden exactamente (sección 2).

**Pasadas sin calor en el cráter:** 1.230 de 8.997 (MODIS 33, VIIRS 375 1.061, VIIRS 750 136). Con las 528 anteriores
suman las 1.758 pasadas publicadas lejanas.

### 3.3 Agua: el control negativo

Un lago no es fuente térmica volcánica (salvo aporte geotermal): lo que se alerta ahí es ruido del detector, una orilla
mezclada en el píxel o geotermia (A110). Resultado (`recurrencia_salida.txt`):

- **26 alertados sobre agua en 19 pasadas y 19 noches-volcán**, en 21 meses y 10 volcanes. 25 son VIIRS 375 y uno VIIRS
  750; ninguno MODIS. **Las 19 pasadas se publicaron lejanas**, ninguna como cumbre.
- **10 de los 26 están a menos de media celda de la orilla**: son píxeles mezclados agua y tierra, no agua limpia.
- **Ningún lago alerta de forma recurrente**: ninguna casilla de 1 km sobre agua alertó en 3 noches o más. Los polígonos
  con más alertas son uno de 10,5 km² a unos 21 km de Láscar (5 noches entre 2025-08 y 2026-08), uno de 172,6 km² a unos
  21 km de Villarrica (5 noches; por tamaño y posición sería el lago Villarrica, no verificado sobre carta) y uno de
  933 km² a unos 22 km de Chaitén (4 noches; ese tamaño es el del mar o un fiordo, no el de un lago, SOSPECHA).
- **Densidad por superficie** (alertados VIIRS 375 por km² y por 1000 pasadas): en ningún volcán el agua alerta
  claramente más que la tierra lejana. La razón agua/resto va de 0 (Isluga, Tupungatito, Chillán, Llaima: 0 alertados
  sobre agua) a 1,46 (Lastarria, con 4 alertados, los cuatro de una sola pasada, el 2025-08-18). La razón agrupada de los
  10 volcanes es 0,12, pero está dominada por Villarrica y Chaitén, que tienen casi toda la superficie de agua y poca
  alerta también en tierra; no debe leerse como «el agua alerta 8 veces menos» (crítica 3).

Lectura: el agua no muestra una fuente de falsos positivos sistemática. Lo que alerta sobre agua es esporádico, de una
noche, sólo en VIIRS 375 y en buena parte en la orilla.

### 3.4 Flanco

Pocas pasadas (205 de 8.997) y casi siempre de una noche. Tres sitios repiten en 3 noches o más (casillas de 1 km):

- **Nevados de Chillán, 5 a 6 km al este del cráter:** dos casillas vecinas, 5 y 4 noches entre el 2026-04-14 y el
  2026-05-31, en VIIRS 375 y 750, BT hasta 310,5 K. Es el único foco del flanco con forma de episodio. Si coincide con
  actividad registrada por OVDAS en ese sector es lo primero que conviene contrastar; aquí no se verificó.
- **Láscar, 6 km al oeste:** 3 noches en VIIRS 375, dispersas entre 2025-07 y 2026-03.
- **Tupungatito, 9 km al este:** 4 noches dispersas en un año (2025-10 a 2026-09).

### 3.5 Resto: episodios lejanos y ruido disperso

Dos comportamientos muy distintos:

- **Episodios de días o semanas en un mismo sitio**, que se llevan gran parte del VRP del volcán:
  - Nevados de Chillán, 13 a 21 km al oeste: 27 casillas recurrentes, hasta 11 noches, casi todo entre el 2025-02-14 y el
    2025-03-05, en los tres sensores, BT hasta 358 K.
  - Copahue, 23 a 25 km al sur: 9 casillas recurrentes, hasta 7 noches, entre el 2025-11-15 y el 2025-11-23, en los
    tres sensores; con ellas, el 97,7 a 100 % del VRP de Copahue cae en el resto. Otras dos casillas de Copahue repiten
    en otras fechas: 26 km al norte (4 noches, enero de 2026) y 26 km al noroeste (3 noches, mayo de 2026).
  - Llaima, 25 a 34 km al suroeste: 5 casillas, 3 a 4 noches, en mayo de 2026 y julio de 2025.
  Por forma (un frente que dura una o dos semanas, lejos del edificio, en verano en Chillán), son compatibles con
  incendios; es SOSPECHA, porque aquí no hay vara de fuego (FIRMS no está configurado).
- **Ruido disperso en el altiplano:** en Láscar, Isluga y Lastarria el resto suma 341, 342 y 388 casillas distintas con
  alerta en VIIRS 375, y sólo una de cada volcán repite en 3 noches. El mapa de Láscar lo muestra: puntos aislados
  repartidos por toda la grilla, sin foco. Es calor de una noche en sitios distintos (roca o salar tibio, bordes de nube),
  no una fuente. Es lo que, junto con un cráter débil, produce las 528 lejanas de 3.2.

### 3.6 Qué parte del VRP cae en cada área

Fracción del VRP sumado de todas las pasadas (con el reparto del fondo por partes iguales, crítica 1):

- Láscar: cráter 97,8 % (MODIS), 88,8 % (VIIRS 375), 97,4 % (VIIRS 750).
- Nevados de Chillán: cráter 52,9 %, 47,7 % y 57,7 %; el resto, del episodio de febrero de 2025, 47,1 %, 50,4 % y 41,8 %.
- Copahue y Llaima: el resto se lleva entre el 92,8 y el 100 %.
- Isluga VIIRS 375: cráter 56,8 %, resto 39,1 %. Lastarria VIIRS 375: cráter 29,3 %, resto 63,0 %.
- El agua no pasa del 6,7 % en ningún volcán y familia (Chaitén VIIRS 375, el polígono de 933 km²).

### 3.7 Píxeles en el borde de un área

79 de 28.526 alertados (0,28 %) quedan a menos de media celda de un borde que les cambiaría el área (crítica §9.2 del
diseño); están en 62 pasadas. La regla del centro del píxel no mueve las conclusiones. La excepción es el agua, donde 10
de 26 están junto a la orilla (3.3).

## 4. Crítico despiadado sobre este informe

1. **El VRP por área no está medido, está repartido.** El fondo real bajo cada alertado no se guarda; se reparte el total
   por partes iguales. Un incendio a 20 km tiene un fondo distinto del cráter, así que el VRP del cráter y del resto
   en una pasada mixta puede estar corrido hacia uno u otro. La suma por pasada es exacta (cierre 8.997 de 8.997); el
   reparto, no. No se midió cuánto se equivoca. Los conteos (qué pasadas tienen calor en qué área) no dependen de esto;
   las fracciones de VRP de 3.6 sí. Medirlo bien es la opción B (A45).
2. **Las fracciones por pasada mezclan familias que no se comparan.** VIIRS 375 aporta 6.844 de las 8.997 pasadas con
   detección, con tres satélites y hasta dos pasadas por satélite en una noche, y píxeles de 375 m que ven lo que MODIS
   no. «El 17 % de las pasadas de Láscar tiene calor en el resto» es casi todo VIIRS 375. Por eso la recurrencia (3.4,
   3.5) se contó por noches; las tablas de 3.1 y 3.2 siguen siendo por pasada y por familia, y no deben sumarse entre
   familias como si fueran un mismo instrumento.
3. **El control negativo del agua no es limpio ni tiene poder.** 10 de los 26 alertados sobre agua están en la orilla;
   un polígono de Chaitén de 933 km² parece el mar (SOSPECHA por tamaño, no verificado); la capa JRC no distingue lagunas
   con aporte geotermal (crítica §9.4 del diseño). Con 0 a 6 alertados por volcán, las razones agua/resto no distinguen
   «el agua alerta igual que la tierra» de «alerta menos». La razón agrupada 0,12 es un efecto de composición (A114,
   estratificar por volcán): no se usa como resultado.
4. **Fuera del cráter no hay vara.** Que los episodios del resto en Chillán, Copahue y Llaima sean incendios, y que el
   foco del flanco este de Chillán en abril y mayo de 2026 sea volcánico, es lectura de forma, no comprobación: no hay
   FIRMS configurado ni se cruzó con OVDAS. Esta partición describe; no valida (crítica §9.1 del diseño).
5. **Sólo ve lo que cruzó el umbral.** Una pasada «sin calor en el cráter» (1.230) puede ser un cráter frío o un cráter
   tapado por nube; los records no guardan las celdas válidas por área. Y el radio del flanco (10 km, igual en todos) es
   provisional: con el edificio real de cada volcán, parte del flanco pasaría al resto o al revés. Lo primero lo resuelve
   la opción B; lo segundo espera la respuesta de Nicolás a AR3.

## 5. Qué sigue

- Para Nicolás: los mapas (`experiments\_s194_areas\mapas\`) muestran dónde cae cada alertado. Si el foco del flanco este
  de Chillán (abril y mayo de 2026) le parece volcánico, es el primer caso para contrastar con OVDAS.
- AR3 (radio del flanco por volcán) sigue abierta; cambiarla es editar `config\areas_laboratorio.yaml` y volver a correr
  los tres scripts.
- La opción B (resumen por área dentro del laboratorio, con celdas válidas y fondo por área) resolvería las críticas 1 y 5;
  toca `pipeline/` (A45) y entra con el paso 4 del plan S190 (AR5).
