# S149: verificador con contexto limpio del costo oculto de `max`

> Sólo lectura sobre el repo. Scripts y salidas propias en
> `experiments/_s149_verificador_costo_oculto/` (`v1` a `v5`, `salida_v1.txt` a `salida_v5.txt`).
> Documento auditado: `docs/S149_COSTO_OCULTO_MAX.md`. Ventana 2026-09-01 a 2026-09-20, VIIRS 375.

## Veredicto

**Se sostiene con salvedades.** El conteo 50 = 34 + 16 y las tasas 49,5 % y 18,3 % sobre 109 se
reproducen exactas leyendo los CSV congelados con `csv.DictReader`, sin `bp.parear`, sin
`bp.etiquetar` y sin `cargar_referencia_unificada` (`salida_v1.txt`, bloque A). Lo que no queda
probado es la lectura «RUTINA con VRP 0 = MIROVA miró esa pasada y no alertó» (hallazgo H1), y dos
frases del documento no se sostienen como están escritas (H2 y H5).

## 1. Caminos por los que podía estar mal (enumerados antes de mirar)

| camino | resultado |
|---|---|
| tolerancia de 120 s parea una fila de otra pasada | descartado: las filas CONS V375 de un mismo volcán nunca están a menos de 1.081 s entre sí y ninguna pasada de la clase parea más de una fila (`salida_v1.txt`, bloque F). Con pareo al minuto exacto da lo mismo, 34 y 16 (`salida_v2.txt`) |
| segundos del CSV | los CSV traen segundos 00, 01 y 02; un pareo con tolerancia 0 sobre la fecha completa falla por eso (bloque B de `salida_v1.txt`, que NO debe leerse como resultado; lo reemplaza `salida_v2.txt`) |
| claves duplicadas | 0 claves repetidas en CONS V375 (bloque F) |
| nombres de volcán o sensor perdidos | 0 filas descartadas (primera línea de `salida_v1.txt`) |
| el predicado de publicar | igual con `pub` (node) y con `pub2` (port independiente), bloque C |
| definición de noche con alerta | cualquier sensor: 50, 34, 16. Sólo V375: 49, 34, 15 (bloque D). El documento lo declara |
| misma pasada partida en dos gránulos | ocurre, ver H3 |
| la fila RUTINA es del mismo satélite | el CSV no trae satélite; SIN VERIFICAR de forma directa. Indirecto: la hora coincide al minuto con nuestro gránulo y no hay otra fila a menos de 18 min |
| «RUTINA VRP 0» significa que MIROVA procesó | SIN VERIFICAR, ver H1 |
| zona horaria | todas las pasadas de la clase caen entre 04 y 07 UTC, una sola fecha UTC por noche; sin efecto |

## 2. Hallazgos

**H1 (gravedad 3). La fila RUTINA no trae nada que pruebe que MIROVA miró.** Las 514 filas RUTINA
V375 nocturnas de la ventana son idénticas en todas las columnas informativas: `Clasificacion
Mirova = NULO`, `Ruta Foto = No descargada`, `Distancia_km = 0.0`, `VRP_MW = 0.0`
(`salida_v3.txt`). Desde el CSV no se puede distinguir «MIROVA listó la pasada con VRP 0» de «el
scraper rellenó». El código del scraper no está en este computador: SIN VERIFICAR. A favor de la
lectura: en 0 de 514 casos el canal OCR contradice a una RUTINA del consolidado, y las filas no
aparecen en bloque para los 11 volcanes sino por gránulo (3 volcanes del norte, 8 del sur). En
contra: el consolidado pierde pasadas reales, **30 de las 74 alertas OCR nocturnas (41 %) no tienen
fila en el consolidado** (`salida_v3.txt`), así que el canal no es exhaustivo. Es la misma lectura
que ya usa el negativo limpio del evaluador, y el documento lo declara en su sección 6; no es un
error nuevo, es una premisa heredada que sostiene el «34 de 34 correctas» de la sección 5.

**H2 (gravedad 3). Las «sin fila» no son un hueco del scraper del 13 y 14 de septiembre: son
Suomi NPP.** Sobre las 962 pasadas V375 de la tabla, no tiene fila el **60,0 % de las de SNPP**
contra 15,5 % de NOAA-20 y 8,7 % de NOAA-21. De las 16 apagadas sin fila, **14 son SNPP**
(`salida_v1.txt`, bloque G). Y por fecha no hay hueco: el 13 y el 14 faltan 15 y 16 filas, igual que
el 3 (19), el 4 (22), el 8 (20) o el 19 (19). La sospecha de la sección 6 del documento queda
refutada como explicación; la concentración de 9 casos en esas dos noches viene de que fueron
noches con muchas alertas, no de un corte. Consecuencia: las 109 arbitrables están sesgadas a
NOAA-20 y NOAA-21 (85 de 109), y sobre SNPP la afirmación casi no dice nada (24 con fila, 49 sin).

**H3 (gravedad 2). Las 50 publicaciones son 49 sobrevuelos.** Isluga 2026-09-02 06:36 y 06:42 son
dos gránulos contiguos del mismo paso de SNPP; uno cuenta en las 34 (tiene RUTINA) y el otro en
las 16 (`salida_v2.txt`). Hay 27 pares así en la tabla V375. No cambia el veredicto.

**H4 (gravedad 3). El control de posición de la sección 4 mide la distancia al cráter, no la
coincidencia con el calor de esa noche.** La separación al «cúmulo confirmado» correlaciona 0,996
con `pc_dist` y difiere de ella 0,16 km de mediana (`salida_v4.txt`). Además c1 compara
estadísticos distintos: mínimo sobre los cúmulos de la misma noche contra mediana sobre todas las
otras noches (`c1_las_50.py`, funciones `sep` y bloque del nulo). Con el mismo estadístico, el nulo
de otras noches da **0,71 km**, más cerca que la misma noche (0,91), y 0,80 sorteando una noche
(p5 0,68, p95 0,92). La conclusión que el documento saca («la posición no distingue el calor de
esta noche») sale reforzada; lo que sobra es el nombre «cúmulo confirmado»: es nuestro cúmulo en la
pasada positiva, no la posición de MIROVA (A107). El contraste con los negativos limpios se
mantiene con estadístico simétrico (2,91 km; en Chaitén 0,72 contra 2,70 y en Cordón Caulle 0,71
contra 6,51), pero en Isluga, Planchón Peteroa y Tupungatito apagadas y negativos caen igual.

**H5 (gravedad 2). Frase falsa a nivel de pasada.** «Isluga, Tupungatito, Villarrica, todas a más
de 2 km» describe medianas por volcán. El propio listado de `salida_c4_cruce.txt` trae tres
pasadas de Tupungatito a 0,46, 0,15 y 0,21 km.

**H6 (gravedad 1).** La referencia congelada termina el 2026-09-20 02:45 UTC: la noche del 20 no
tiene ninguna fila V375 (44 de 44 sin fila, bloque G). No entra en la clase porque sin fila no hay
positiva, pero la ventana efectiva es del 1 al 19.

## 3. Números del documento contra las salidas

Todos los números de las secciones 0, 2, 3, 4 y 6 aparecen en `salida_c1` a `salida_c4`. La
explicación de 141 contra 109 (noches con etiqueta de falso positivo) no salía de ningún script;
la verifiqué: las 32 de diferencia son todas noches sin positiva y con `far_ref` V375
(`salida_v5.txt`). No salen de un script: «cerca de un tercio sobre el foco (Láscar, Chaitén,
Cordón Caulle)» (el tercio sí, 16 de 49; la atribución por volcán es de medianas de 0,72 y 0,71,
que no son 0,4 o menos) y la frase de H5.

## 4. Números que difieren

Ninguno de la afirmación. Difieren por definición y quedan dichos: 49, 34, 15 con alerta sólo
V375; nulo de posición 0,71 (o 0,80) en vez de 0,81; negativos limpios 2,91 en vez de 2,99.
