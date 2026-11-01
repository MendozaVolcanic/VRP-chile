# S158: por qué la magnitud de Tupungatito en VIIRS 375 queda bajo la de MIROVA con el detector K

> Escrito el 2026-10-21 (S158, sesión lateral de la sesión dueña del loop) y corregido el mismo día con el
> verificador con contexto limpio (veredicto por afirmación en §7; informe en `verificador/INFORME_VERIFICADOR.md`).
> Sólo lectura: no toca `pipeline/`, los perfiles ni `data/mirova_equivalent/`, y no despacha nada. Cada número
> sale de una salida commiteada junto a su script (regla S91). **No adopta nada**: es insumo para decidir.

## En corto

1. **Las dos alertas protegidas «perdidas» de #864 no son del cráter.** MIROVA misma las dibuja a 22,6 km
   (2026-09-28 05:18, 2,51 MW) y a 9,6 km (2026-09-29 04:54, 1,86 MW) de su centro, fuera de su círculo de 7 km.
   La distancia de ~5 km de la fila del scraper no es de esa pasada (el 28-sep vino de la estrella de la pasada
   siguiente; el 5,68 del 29-sep no tiene origen explicado). Nuestro record de la misma pasada ve el mismo objeto
   lejano y lo clasifica `far`: no publicarlo es lo correcto. Lo mismo pasa con las otras dos protegidas de la
   serie K (2026-08-01, 15,3 km; 2026-09-14, 13,0 km). **En toda la serie K no hay ninguna alerta protegida
   nocturna de cráter en Tupungatito VIIRS 375** (la única de cráter de 1 MW o más es diurna, 2026-04-13 18:24,
   y el pipeline no mira de día).
2. **El 0,266 está inflado por esas alertas, pero el déficit es real.** Sin las dos lejanas la misma métrica da
   0,448 (n = 7). Sobre la serie K con referencia de la tabla da 0,49 por noche (n = 101) y 0,36 por pasada
   (n = 141). El tablero no recorta (F_rec 1,00 de mediana) y medimos el mismo objeto que MIROVA (141 de 141).
3. **El déficit es sobre todo el fondo.** El cráter es un foco débil: el píxel más caliente está ~5 K sobre la
   mediana del anillo de 5 a 25 km, y ese anillo es valle más tibio que la cumbre glaciar. Con un fondo 7 K más
   frío que el anillo cierran las pasadas casi a nadir; con fondo cero nuestros píxeles darían 2,1 veces MIROVA.
   En 6 pasadas con alerta de MIROVA el píxel del cráter queda bajo el anillo y publicamos 0,0 MW.
4. **El detector anterior (C0) restaba un fondo más frío, por su Test 1 integrado** (anillo de 1 a 3 km alrededor
   del cráter, ~13 K más frío que el de 5 a 25 km). En el mismo gránulo, donde C0 restaba ese fondo, K da la
   mitad (K/C0 = 0,51, n = 89); donde C0 restaba el anillo, lo mismo (1,04, n = 38). En las mismas 14 noches de
   la ventana C0 del auto-audit, C0 da 0,825 y K 0,553. La caída de 0,83 a 0,27 que se lee en #864 mezcla eso
   con las dos alertas lejanas y con noches distintas.
5. **El ángulo agrega una pieza compatible con el área (D17), sin probarla.** Sin corregir el área, el fondo que
   cierra crece con el cenit (7, 10 y 14 K). Con el modelo de área B de S131 queda plano (5,0 / 4,2 / 5,5 K);
   con el modelo C se invierte (4,5 / 2,3 / 0,8 K). La selección pesa poco: K alerta más píxeles que C0, y sin
   corregir el área sólo 10 de 141 pasadas (todas desde el este, todas de un píxel) no las cierra ningún fondo.
6. **Lado del barrido:** MIROVA lee más desde el este (factor 1,28, p 0,067) y la razón es más baja desde el
   este (0,835), en la dirección de #879, pero dentro del azar (p 0,13; el nulo trata las pasadas de una noche
   como independientes, así que es optimista).

## 1. El fenómeno

Tupungatito es un volcán de 5.600 m cubierto de glaciar, con un lago cratérico y fumarolas. De noche, a 3,74 µm,
su cráter es un foco débil y chico. En las 141 pasadas con alerta de MIROVA, el píxel de 375 m más caliente marca
266 K de mediana (p10 258, p90 273) y el anillo de fondo, la mediana de 5 a 25 km que baja a valles mucho más
abajo, marca 261 K (p10 252, p90 269) (`d_pasadas_salida.json`). El entorno de 1 a 3 km del cráter, cumbre
glaciar, es bastante más frío: en los 1.130 records C0 en que el Test 1 lo restaba, 251 K (p10 242, p90 257;
`e_fondo_local.py`).

La potencia radiante se calcula con el exceso de radiancia del píxel caliente sobre el fondo. Cuando el foco está
cientos de kelvin sobre su entorno (Chillán), unos kelvin de error en el fondo no importan. Cuando está 5 K sobre
el fondo, importan todo: contra el fondo tibio del valle, el exceso queda en una fracción del que se mediría contra
el hielo que de verdad rodea al cráter, y si el píxel del cráter queda bajo el fondo del valle el exceso se recorta
a cero. Ése es el déficit de Tupungatito.

A eso se suma la geometría: un píxel visto de lado es más grande que a nadir, el mismo foco se diluye en más
superficie y, si la potencia se calcula con el área nominal, se subestima (D17).

## 2. Las alertas protegidas: comprobar que son de su pasada

`a_bajar_imagenes.py` baja de Mirova-v1 las láminas por volcán de esas noches; `b_series_mirova.py` lee píxel a
píxel las series «Last Month» de distancia (`Dist.png`) y potencia (`logVRP.png`), calibradas con las líneas de
grilla de la propia lámina (6 de 6 y 8 de 8 encontradas, desviación máxima 0,30 px). El eje x no se calibra: cada
marcador se asigna a su día por posición relativa y por pareo con la tabla (el verificador midió que leer los
rótulos de semana como 00 UTC correría las pasadas ~0,6 día).

- **El VRP sí es de su pasada.** El panel Latest10NTI trae la celda de las 05:18:00 del 28-sep con 2,51 MW
  (cenit 48°, azimut 105°) y la de las 04:54:00 del 29-sep con 1,86 MW (cenit 62°, azimut 108°), y sólo dos
  pasadas con VRP en cada una de esas noches.
- **La imagen y la distancia no.** La cabecera de los archivos de 05:18 y de 04:54 dice «Last Update» 05:36:01 y
  06:36:00 (memoria S150). El 28-sep el OCR leyó la estrella verde de la pasada de 05:36; el 5,68 km del 29-sep
  no coincide con la otra pasada (5,41) y su origen queda sin explicar. Las cuatro protegidas son filas sólo OCR
  de Suomi NPP, el caso que A119 marca.
- **La serie de MIROVA dice dónde estaban.** Cada noche tiene dos marcadores, uno rojo (< 7 km) y uno gris
  (> 7 km). La tabla `latest.php`, independiente del OCR, ya asigna el rojo a la otra pasada (05:36 con 0,09 MW a
  5,21 km; 05:18 del 29 con 0,04 MW a 5,41 km). El gris es el de la alerta:

| pasada | MIROVA (fila) | serie de MIROVA: distancia, potencia | `Distancia_aprox` del scraper | nuestro record, misma pasada |
|---|---|---|---|---|
| 2026-08-01 05:00 | 1,25 MW, 5,41 km | 15,29 km, 1,41 MW (lámina del 06-ago) | 15,27, «único» | publicado `summit` 0,016 MW; un píxel alertado lejos, 0,89 MW |
| 2026-09-14 06:18 | 2,22 MW, 2,97 km | 12,98 km, 2,28 MW | 13,11, «único» | publicado `summit` 0,008 MW; un píxel alertado lejos, 2,28 MW |
| 2026-09-28 05:18 | 2,51 MW, 5,27 km | 22,62 km, 2,72 MW | ambiguo, 5,27 a 22,57 | no publicado, `far`, cúmulo a 21,57 km del cráter, 0,15 MW |
| 2026-09-29 04:54 | 1,86 MW, 5,68 km | 9,58 km, 1,92 MW | ambiguo, 5,41 a 9,59 | no publicado, `far`, cúmulo a 9,40 km del cráter, 1,11 MW |

Las distancias de MIROVA se miden desde su centro de grilla; el cráter queda a 4,86 km de ese centro, rumbo 330°
(`f_espacial_salida.txt`). La columna `dist_km` de nuestros píxeles se mide desde la coordenada nominal del volcán
(-33,4, -69,8), no desde el cráter (verificador H6); por eso la tabla no la cita.

**Comprobación independiente (verificador, `verificador/v6_miniaturas_direccion.py`):** en la miniatura de cada
pasada hay un punto brillante con el mismo rumbo y la misma distancia que nuestro píxel lejano: 15,6 km a 32°
contra 15,0 km a 32°; 13,8 km a 75° contra 13,1 a 74°; 25,0 km a 26° contra 23,9 a 26°; 9,8 km a 48° contra 9,3 a
46°. La escala de la miniatura (51 km de lado) es un supuesto, respaldado por esas cuatro coincidencias y una de
control.

Control de la lectura de la serie: el marcador del 2026-09-27 05:54 (fila de tabla `FALSO_POSITIVO`, 0,37 MW a
21,8 km) se lee 21,81 km y 0,40 MW; los rojos se leen 0,089 y 0,041 MW contra 0,09 y 0,04 de la tabla. La potencia
leída de un triángulo sale ~8 % alta, lo que no cambia nada. Ojo: dos láminas del 1-ago con la misma cabecera
traen paneles distintos (una con el marcador gris del 1-ago y otra sin él; verificador H9).

Las cuatro noches se publicaron con el cráter en otra pasada. **Ninguna protegida nocturna de cráter se pierde**
(`g_protegidas.py`; la tabla no tiene ninguna `ALERTA_TERMICA` de 1 MW o más en Tupungatito VIIRS 375, verificador
H8). Las lejanas, además, inflan el denominador de la magnitud por noche.

## 3. El 0,266 y la muestra larga (`c_noche_audit.py`)

Con las funciones del auto-audit y la frontera de entonces se reproduce exacto: **0,266, n = 8** (el verificador lo
reprodujo llamando a `evaluar_detector`). La métrica divide, por noche, nuestro máximo publicado por el máximo de
las alertas de MIROVA, sin mirar su distancia.

| ventana | A: auto-audit | B: sin las 2 lejanas | C: sólo tabla | D: tabla y ≤ 7 km |
|---|---|---|---|---|
| auto-audit, noches K (desde 2026-09-18) | 0,266 (8) | 0,448 (7) | 0,448 (7) | 0,448 (7) |
| misma ventana, toda la data ya en K (#883) | 0,489 (22) | 0,531 (21) | 0,537 (20) | 0,537 (20) |
| serie K con referencia, 2026-02-14 a 2026-10-20 | 0,443 (116) | 0,448 (115) | 0,492 (101) | 0,492 (101) |

Cuando la alerta máxima de la noche es sólo OCR, la razón es más baja (0,347, n = 27, contra 0,48 con tabla,
n = 89): el OCR mezcla alertas lejanas.

**La comparación con C0 se hace en las mismas noches** (verificador, `v7_` y `v8_`): en las 14 noches de la
ventana C0 del auto-audit (2026-08-20 a 2026-09-17), C0 da 0,825 y K 0,553 (sólo con alerta máxima de la tabla,
0,844 y 0,571, n = 11). De 0,83 a ~0,55 es el cambio de detector; de 0,27 a 0,45, las dos lejanas; el resto es
que son noches distintas.

## 4. Descomposición pasada por pasada (`d_pasadas.py`, `e_fondo_local.py`)

Pareo: misma pasada (±120 s) con una alerta de la **tabla** a 7 km o menos. 198 pasadas K con alerta del
scraper; 158 con alerta de tabla cerca, 141 publicadas; 40 sólo OCR, fuera. Las 17 no publicadas tienen VRP de
MIROVA bajo 1 MW: 10 sin cúmulo, 1 con el cúmulo lejos y 6 con el cúmulo en el cráter y 0,0 MW, porque en las 6
el píxel del cráter está **bajo** la mediana del anillo (por ejemplo 266,46 contra 268,19 K el 2026-02-23 06:42) y
el exceso negativo se recorta a cero: D25 en su forma extrema. Control: el VRP de los 229 píxeles se reproduce con
la fórmula del procesador y el fondo del anillo. Con la regla D-9 (sin las 12 pasadas de 0,05 MW o menos) la
mediana por pasada es 0,338 (n = 129) en vez de 0,359 (verificador H11).

R = D / M (publicado sobre MIROVA) = F_rec × G. F_rec es el recorte del tablero (núcleo F5 sobre la suma de
nuestros píxeles dentro de 7 km); G es lo que queda para selección, fondo y área.

| cenit | n | R | F_rec | G | G con fondo 10 K más frío | G con fondo cero | fondo que cierra | ídem, área modelo B | f_area (B) | G con área B |
|---|---|---|---|---|---|---|---|---|---|---|
| < 30° | 66 | 0,45 | 1,00 | 0,47 | 1,20 | 2,25 | 7,0 K | 5,0 K | 1,12 | 0,54 |
| 30 a 50° | 47 | 0,28 | 1,00 | 0,28 | 0,97 | 1,78 | 10,2 K | 4,2 K | 1,70 | 0,48 |
| ≥ 50° | 28 | 0,25 | 1,00 | 0,25 | 0,78 | 1,50 | 14,1 K | 5,5 K | 1,80 | 0,39 |
| todas | 141 | 0,36 | 1,00 | 0,37 | 1,08 | 2,08 | 8,0 K | 5,0 K | 1,38 | 0,49 |

«Fondo que cierra»: cuántos K bajo la mediana del anillo tendría que estar el fondo para que nuestros propios
píxeles den el VRP de MIROVA (mediana por pasada; las pasadas sin solución quedan fuera de la mediana: contándolas
como infinito, el verificador obtiene 7,0 / 10,6 / 16,7 K).

### 4.1 Selección del cúmulo: pesa poco

- El tablero no recorta (F_rec 1,00 de mediana en las tres bandas; 3 pasadas bajo 0,99).
- Medimos el mismo objeto: el radio de nuestro cúmulo desde el centro de MIROVA difiere del de la tabla en 0,22 km
  de mediana y 0,67 como máximo, 141 de 141 (`f_espacial.py`; cota sobre radios, A93).
- K alerta **más** píxeles que C0 en el mismo gránulo (mediana 2 contra 1; en 60 pasadas K suma píxeles, en 22
  pierde alguno, y los que pierde estaban 1,7 K **bajo** el anillo).
- Donde C0 y K restan el mismo fondo, K/C0 = 1,04 (n = 38, verificador H3): cambiar la selección de C0 a K no movió
  la magnitud.
- Sin corregir el área, 10 de 141 pasadas no se cierran con ningún fondo: las 10 desde el este, de un solo píxel,
  9 con cenit sobre 34°. Con el área del modelo B cierran, pero 8 de las 10 piden un fondo más frío que el entorno
  de 1 a 3 km. Ahí MIROVA lee más de lo que un píxel nuestro puede dar: suma vecinos que no alertamos, o es el
  efecto del lado de #879. Es la única huella de selección que se ve.

### 4.2 Fondo del anillo: la pieza principal

- Con fondo cero, G sube a 2,08: el fondo puede cerrar la brecha (en Chillán no podía, `_s157_magnitud_chillan`).
- **Qué fondo restaba C0.** Por código (verificador H2): en el recálculo de magnitud del Test 1,
  `select_test1_effective_lbg` (`pipeline/test1_integrated.py:170-176`) sólo usa el anillo intermedio o el global
  si el volcán tiene `lbg_global_compatible`, y Tupungatito no lo tiene; cae al fondo local, la mediana de la
  radiancia MIR entre 1 y 3 km del cráter (`test1_integrated.py:412-447`, `pipeline/profile.py:178-179`). Que todos
  los píxeles de cada record den el mismo fondo (1.130 de 1.130) no prueba nada: 1.126 de esos records tienen un
  solo píxel. El respaldo es el código, comprobado para el código de hoy; para records escritos con código de
  otras fechas es SOSPECHA.
- **Cuánto más frío es.** Despejado del VRP guardado de esos 1.130 records, 13,0 K bajo el anillo de 5 a 25 km (p10
  8,9; p90 22,4); 11,1 K en verano y 14,2 K en invierno. No depende del cenit: 14,7 / 14,0 / 14,6 K en los 434 con
  cenit, y por año y banda 12,0 a 12,9 K en 2025 y 15,4 a 17,5 K desde el 2026-06-07 (verificador H7,
  `verificador/v3b_sonda_salida.txt`). Se enfría con el tiempo, no con el ángulo.
- **Con ese fondo**, nuestros píxeles K pasarían de G 0,37 a 1,30: sobra. El fondo que cierra a nadir (7 K bajo el
  anillo) queda entre el anillo y el entorno de 1 a 3 km, que es lo esperable para la media de los vecinos
  inmediatos de un píxel de 375 m (D25); sin el L1B no se mide.
- **K contra C0 en el mismo gránulo** (127 pasadas), clasificadas por el fondo que C0 restó de verdad (despejado de
  su VRP; el rótulo `final_hotspot_source` no basta, porque 15 records `ctx_cluster` con `triggered_test1` también
  restaban el fondo local; verificador H3, `verificador/v4_k_c0_por_fondo_real.py`):

| fondo que restaba C0 | n | R de C0 | R de K | K / C0 |
|---|---|---|---|---|
| más frío que el anillo (Test 1) | 89 | 0,740 | 0,356 | 0,507 |
| el anillo | 38 | 0,351 | 0,395 | 1,040 |

  La diferencia entre detectores es el fondo, no la selección. Antes de #535 el reproceso K dejó además el anillo
  2,7 K más frío (sin la máscara de nube de 260 K), lo que sube un poco a K. Desde #535 el anillo es el mismo en
  14 de 14 pasadas y la magnitud publicada coincide en 9 de 14.

### 4.3 Área o geometría (D17): la parte que crece con el ángulo, no el nivel

- A nadir el área casi no cuenta (f_area 1,12) y el déficit ya es 0,45: es fondo.
- El fondo que cierra crece con el cenit sin corregir el área (7 → 10 → 14 K), mientras el fondo local medido no
  depende del cenit. Algo que crece con el ángulo se suma al fondo. Con el modelo B de S131 (geométrico, anclado
  al ATBD) un solo desfase de ~5 K describe las tres bandas; con el modelo C la corrección se pasa (4,5 / 2,3 /
  0,8 K; verificador H4, `verificador/v5_fondo_que_cierra_modelos.py`). Es **compatible** con D17, no lo prueba,
  y el área no se separa de otro efecto que crezca con el ángulo (verificador S157, H2 y H3).
- Por zona de agregación a bordo: 3:1 (n 81) 0,41; 2:1 (n 32) 0,29; 1:1 (n 28) 0,25. Aquí 1:1 coincide con
  cenit ≥ 50 y no separa nada.

## 5. Cenit y lado del barrido

Efecto este/oeste dentro de cada banda de cenit, con nulo por sorteo del lado (2.000 permutaciones):

| magnitud | factor este/oeste | IC95 del nulo | p |
|---|---|---|---|
| razón R | 0,835 | 0,79 a 1,26 | 0,13 |
| MIROVA (M) | 1,282 | 0,76 a 1,29 | 0,067 |
| nuestro publicado (D) | 1,146 | 0,75 a 1,36 | 0,39 |
| G con fondo cero | 0,756 | 0,81 a 1,21 | 0,0015 |

El nulo sortea pasada por pasada y las pasadas de una noche no son independientes: los p son optimistas, el de G
con fondo cero es el que más podría estar inflado. La dirección es la de #879 (la razón baja desde el este porque
sube MIROVA), pero en Tupungatito con K y sólo tabla el efecto sobre la razón no se separa del azar. El fondo que
cierra es 10,1 K desde el este y 6,8 K desde el oeste (5,9 y 3,8 con el área B). Por banda de cenit, R desde el
este 0,40 / 0,25 / 0,29 y desde el oeste 0,53 / 0,32 / 0,24. Las 10 pasadas que ningún fondo cierra sin área son
todas del este.

## 6. Lo que no se pudo resolver

- **El fondo real de los vecinos** (D25): sin L1B. Se acota entre el anillo (el actual) y el entorno de 1 a 3 km
  (13 K más frío), y se mide el que haría falta (7 K a nadir).
- **El reparto entre fondo y área en el borde**: depende del modelo de área (B lo deja plano, C lo invierte).
- **Las 10 pasadas del este de un píxel**: selección o efecto del lado; sin el Npix de MIROVA no se separa.
- **Antes y después del 2026-06-13** la razón cambia (0,29 contra 0,44, con cenit parecido y M más alto antes), y
  el fondo local se enfría desde junio; no está atribuido.
- **Por qué 15 records C0 `ctx_cluster` llevan el fondo del Test 1** (SOSPECHA del verificador: píxeles del Test 1
  que entran al cúmulo antes del rótulo final).
- **El origen del 5,68 km del OCR del 29-sep.**
- **Las lejanas vistas por los dos** comparan mal en magnitud (0,15 contra 2,51 el 28-sep; 2,28 contra 2,22 el
  14-sep): con n = 4 no dice nada sobre la calibración. El 28-sep la miniatura de MIROVA muestra además un segundo
  punto a 23 km rumbo 204° que nuestro record no tiene.
- **Distancias**: los filtros «dentro de 7 km» de `d_pasadas.py` y `e_fondo_local.py` usan `dist_km`, que se mide
  desde la coordenada nominal del volcán (a ~2,7 km del cráter), igual que el pipeline; no cambia nada aquí.

## 7. Verificador con contexto limpio

Opus, sólo con rutas y scripts, re-corrió los scripts y escribió los suyos (`verificador/v1_` a `v8_` y tres sondas
`v3b_` a `v3d_`). Veredictos: (1) protegidas lejanas, **CONFIRMADO** también por la dirección en la miniatura;
(2) 0,266 y déficit real, **CONFIRMADO** con la función del auto-audit; (3) fondo como pieza principal,
**PARCIAL**: se sostiene, pero la prueba de coherencia era casi vacía y la planitud con área depende del modelo;
(4) fondo de C0, **PARCIAL**: el mecanismo sale reforzado al reclasificar por fondo efectivo, pero la comparación
0,83 contra 0,27 mezclaba noches; (5) lado, **CONFIRMADO** en los números, con nulo optimista. Este README ya
incorpora sus hallazgos H1 a H11.

## 8. Qué sugiere (no adopta nada)

1. **Tupungatito es el caso donde D25 debería mover más**: foco débil y anillo de valle tibio. Predicción
   falsable, escrita antes del A/B de D25 que corre la sesión dueña del loop: con el fondo por vecinos, la razón
   por pasada de Tupungatito VIIRS 375 con cenit bajo 30° sube de 0,45 hacia 1 si los vecinos quedan ~7 K bajo el
   anillo, y pasa de 1 (hasta ~1,4, G con el fondo de 1 a 3 km) si quedan tan fríos como ese entorno. Las 6 pasadas
   con cúmulo en el cráter y 0,0 MW deberían dejar de ser cero.
2. **El auto-audit y las protegidas deben mirar la distancia de la alerta.** Las cuatro protegidas de la serie son
   sólo OCR de Suomi NPP y lejanas; dos entran como «perdidas» y las cuatro al denominador de la magnitud por
   noche. `Distancia_aprox_*` (Mirova-v1#25) ya da «único» en dos; las otras dos se resuelven pareando con la
   tabla, como en §2.
3. **Al comparar detectores, en las mismas noches**: la magnitud por noche cambia con la ventana más que con
   muchos ajustes.

## 9. Reproducir

```bash
python -I experiments/_s158_tupungatito/a_bajar_imagenes.py <temporal>/img
python -I experiments/_s158_tupungatito/b_series_mirova.py <temporal>/img
python -I experiments/_s158_tupungatito/c_noche_audit.py
git show 8471add46^:data/mirova_equivalent/Tupungatito.json > <temporal>/Tupungatito_pre883.json
python -I experiments/_s158_tupungatito/d_pasadas.py --dest <temporal>/ref --c0 <temporal>/Tupungatito_pre883.json
python -I experiments/_s158_tupungatito/e_fondo_local.py --c0 <temporal>/Tupungatito_pre883.json
python -I experiments/_s158_tupungatito/f_espacial.py
python -I experiments/_s158_tupungatito/g_protegidas.py --dest <temporal>/ref
```

Los scripts del verificador están listados en `verificador/INFORME_VERIFICADOR.md` y esperan el JSON C0 en
`_tmp/Tupungatito_pre883.json` y las láminas en `_tmp/img/` (relativos a la raíz del worktree).

Referencias de la corrida: records en `8471add46` (`sha_json` en `d_pasadas_salida.txt`); C0 del padre de #883;
Mirova-v1 de las láminas en `71ddbffc`; consolidado y OCR remotos con el commit escrito en cada salida (el remoto
avanza cada hora: los conteos de la última semana de la ventana pueden moverse). `c_noche_audit.py` usa el snapshot
del repo, como el auto-audit.
