# Verificador con contexto limpio: pre-registro de invierno (S149)

Documento revisado: `experiments/_s149_prereg_invierno/PREREGISTRO_INVIERNO.md` (rama
`s149-prereg-invierno`). Sólo lectura sobre el repo; mis scripts y salidas están en
`experiments/_s149_verificador_prereg/`. No corrí pytest, no despaché nada, no usé credenciales de NASA.

## Veredicto: APTO CON CAMBIOS (no despachar tal cual)

El cableado de los dos flags está bien y el workflow puede correr las ventanas. Lo que falla es el
sustrato declarado (está inflado por doble conteo), que P6 no puede fallar donde el texto dice que
importa, que la ventana de MODIS no es la mejor disponible, y que el evaluador, con el
`parametros.json` de hoy, no puede dar otro veredicto que INDECIDIBLE o NO ADOPTAR en una ventana que
no sea septiembre.

## 1. Sustrato

**H1 (gravedad 4). Las cuentas de `sustrato_referencia.py` cuentan dos veces la misma pasada.**
La clave de la referencia unificada incluye la fuente (`scripts/referencia_mirova_unificada.py:98`),
y el script deduplica por `(minuto, tipo)` (`sustrato_referencia.py:27`). Una pasada que MIROVA
publicó en la tabla (`ALERTA_TERMICA`) y que además leyó el OCR (`ALERTA_TERMICA_OCR`) son dos tipos
distintos, así que suma dos. Recuento propio leyendo los CSV directo, pasada = volcán, sensor y
minuto, noche por elevación solar propia (`recuento_independiente_salida.txt`, secciones 1 y 2):

| cifra del pre-registro | dice | pasadas únicas |
|---|---|---|
| alertas V375, agosto 01 a 27 | 170 | **126** (45 pasadas con los dos tipos) |
| Villarrica V375, agosto | 9 | **5** |
| Chillán V375, agosto | 7 | **4** |
| Villarrica V750, agosto | 7 | **6** |
| Villarrica V375, junio a agosto | 15 | **11** (3, 3 y 5) |
| Láscar MODIS, junio | 15 | **13** |

El filtro nocturno sí se aplica y es correcto: `indexar_referencia` descarta las diurnas
(`scripts/banco_paridad.py:213`) y el perfil tiene `ENABLE_DAYTIME_MODIS = False` (leído de
`pipeline.profile` con `VRP_PROFILE=_s149_ab_sin_test1_b22_max`). Las 13 de Láscar tienen elevación
solar entre -42 y -51 grados. Lo que está mal es la unidad, no la noche. Ojo: el evaluador no sufre
este defecto (etiqueta records nuestros, no filas), sólo el script de sustrato.
Cambio: corregir el dedup a `(volcán, sensor, minuto)` y reescribir la sección 2 con las cifras
reales.

**H2 (gravedad 4). Agosto no trae el Villarrica débil que motiva la ventana; trae un episodio
fuerte.** Las 5 positivas V375 de Villarrica caen todas entre el 18 y el 24 de agosto y MIROVA les
da 0,87 a 2,21 MW (sección 5 de la salida). El Villarrica "cerca del ruido" del que habla la sección
1 está en mayo: 9 alertas, 8 bajo 0,5 MW (`por_mes_salida.txt`). Entre las 154 ventanas deslizantes
de 27 días, agosto 01 a 27 es la número 15 en Villarrica más Chillán (9 contra 11 de 2026-05-11 a
06-06). Agosto sí es la mejor para Chillán (4 contra 1), así que la elección es defendible, pero el
texto promete algo que la ventana no tiene.
Cambio: decirlo en la sección 1 (agosto mide Villarrica fuerte y Chillán débil), y decidir con
Nicolás si se agrega Villarrica sola en 2026-05-11 a 06-06 (un volcán, dos brazos, unos 75 min por
job) para tener el caso débil.

**H3 (gravedad 3). "El único sustrato de MODIS en todo el año es Láscar en junio" es falso.** El
script sólo miró de junio a septiembre. Láscar MODIS nocturno por mes: febrero 14, **marzo 26 (24
con 0,5 MW o más)**, abril 21, mayo 11, junio 13 (6 con 0,5 o más), julio 2, agosto 1
(`por_mes_salida.txt`). La mejor ventana de 30 días es 2026-03-01 a 03-30: el doble de positivas y
cuatro veces las que activan el umbral duro de la sección 5. La comparación J contra K no necesita
invierno.
Cambio: mover la ventana MODIS a marzo (o correr las dos). El piso "J publica menos de 8" se
recalcula sobre el n real (13 en junio, 26 en marzo).

**Disponibilidad de gránulos (SIN VERIFICAR contra NASA, razonado sobre el código).** Para junio y
agosto `pipeline/fetch.py` pide primero el producto estándar (l. 167 en adelante) y el archivo
estándar no caduca; LANCE y su retención no entran. pyhdf se instala en el job (workflow l. 106).
No veo impedimento. Diferencia a declarar: septiembre se midió con mezcla de NRT y estándar, estas
ventanas serán todo estándar; es igual en los dos brazos.

## 2. Los flags llegan a sus consumidores

- `ENABLE_MODIS_B22_PRIMARY`: un solo punto de decisión, `merge_mir_bands`
  (`pipeline/process_modis.py:322`), aplicado a la radiancia (l. 549), a la BT (l. 553) y a la
  radiancia del NTI (l. 566). Después de la l. 600 no queda ningún uso de `rad21`, `rad22`, `bt21`
  ni `bt22` (grep): magnitud, fondo, NTI, Tests 2 y 3 y segundo pase (l. 774 y 851 reciben
  `rad_mir_for_nti`) heredan la banda elegida. La saturación de la 22 llega como NaN y cae a la 21.
  Llega a todos.
- `ENABLE_TESTS_23_PROSE_BRANCH`: cuatro llamadas por procesador, todas con el flag (MODIS l. 802,
  819, 891, 942; VIIRS l. 1190, 1205, 1294, 1342; VIIRS M l. 787, 802, 876, 921), que cubren las dos
  funciones que tienen conectiva (`detection_context.py:525` y `:943`). Llega a todos.
- Salvedad (gravedad 1): el camino D heredado (`contextual_dnti_hot_mask`) usa C1 solo, sin
  conectiva, y vuelve a decidir si el primer pase no corre (sin `inner_radius_km`, fondo NaN;
  `process_viirs.py:1243`). En los 11 Tier A no aplica.
- `diff_perfiles_s149_salida.txt` confirma que B, J y K difieren en un solo flag cada paso.

## 3. Workflow y evaluador

El workflow no tiene lista cerrada de perfiles ni nada fijo a septiembre salvo los valores por
defecto de `start` y `end` (l. 38 a 45). Duración medida en la corrida 35548121381: 45 a 55 min por
job para 20 días, o sea unos 75 min para 27 y 85 para 30, muy bajo los 300. El costo de la sección
7 (2 a 4 horas por job) está sobreestimado.

**H4 (gravedad 3). Los perfiles J y K no están en `main`.** El checkout del job toma la referencia
del despacho. Cambio: mergear antes, o despachar con `--ref s149-prereg-invierno` y anotarlo. Además
el paso "El brazo LEE lo que declara" (l. 113) no imprime ninguno de los dos flags que este A/B
mueve: agregar `ENABLE_MODIS_B22_PRIMARY` y `ENABLE_TESTS_23_PROSE_BRANCH` al print.

**H5 (gravedad 5). Con el `parametros.json` actual el evaluador no puede evaluar estas ventanas.**
- La ventana sale de `parametros.json` (`evaluar.py:707`), fija en septiembre.
- Por defecto lee la referencia de `_congelado/`, recortada a septiembre (`evaluar.py:696`).
- Sin producción comparable el control positivo falla y `veredicto()` devuelve siempre INDECIDIBLE
  (`evaluar.py:660`). En agosto la producción es de otro régimen (antes de #535), así que no hay
  producción comparable.
- C2 exige que toda noche perdida esté en una lista que es de septiembre (`evaluar.py:577`): cualquier
  pérdida en agosto da NO ADOPTAR automático.
- Los pisos de C1 son conteos absolutos de septiembre (118 y 12), los techos de C3 también, y
  `poder_recall.json` es de septiembre.
- P2, P5 y P6 no los calcula el evaluador. P5 depende de
  `experiments/_s149_costo_oculto/c3_rutina_en_noche_con_alerta.py` y P2 de
  `experiments/_s148_verificador_resultado/r3_nulo_y_costos_ocultos.py`, que lee un `tabla.json` fijo
  a los brazos B y F. `docs/S149_COSTO_OCULTO_MAX.md` y esos scripts **no están en esta rama**
  (commit 4138d43c7, en `s149-caja-segundo-pase`).

Cambio, antes de despachar y commiteado: (a) un `parametros_agosto.json` y uno de MODIS con la
ventana, `criterios_decisorios` sin C2 ni C8, techo V375 en 0,18 y el piso de C1 como fórmula; (b)
congelar la referencia por ventana y pasarla con `--cons` y `--ocr`; (c) una opción del evaluador
que salte el control positivo contra producción sin forzar INDECIDIBLE, conservando el control de
identidad del predicado; (d) un script único y pre-escrito que calcule P2, P5 y P6 desde los dos
directorios de brazos, probado sobre las salidas de septiembre para comprobar que reproduce 0,25 y
49,5 a 18,3 %; (e) traer a la rama los archivos que el pre-registro cita.

## 4. Criterios

**H6 (gravedad 4). P6 no puede fallar en Chillán y es redundante en Villarrica.** Las 4 positivas
de Chillán en agosto tienen 0,02 a 0,09 MW: todas bajo 0,15, así que F puede perder las cuatro y P6
se cumple. Las 5 de Villarrica tienen 0,87 MW o más: ya las cubre la regla de 0,5 MW de P4. P6 no
agrega ningún caso. La mediana de septiembre es de otra población (dominada por Isluga y Láscar).
Cambio: P6 por conteo y por volcán, por ejemplo "F conserva todas las de Villarrica que B publique y
pierde a lo más una de las de Chillán que B publique", con el nulo medido; o declarar P6 informativa.
Con n de 5 y 4 un criterio duro tiene poco poder: decirlo.

**H7 (gravedad 3). P1 la cumple un control que ya esté bajo 18 %.** B en agosto nunca se ha medido
(es código de hoy sobre escena de invierno). Si B publica 18 % o menos, P1 se cumple sin que `max`
haga nada. Un apagado parejo no pasa P1 y P4 juntas si B está cerca de 30 % (haría falta apagar 40 %
y P4 tolera 16 %), pero sólo en ese caso. Cambio: P1 sólo decide si B supera 18 %; si no,
INDECIDIBLE. Informar también la caída relativa.

**H8 (gravedad 2). P4: el 83,7 % no reproduce su origen.** 118 de 141 es 0,83688; con 141
publicadas, 0,837 por 141 da 118,02 y el redondeo hacia arriba exige 119, no 118. Cambio: fijar la
fracción exacta, `ceil(n_B * 118 / 141)` en aritmética entera. No hay circularidad (depende de B, no
de F), pero el piso se conoce después de correr: por eso tiene que ir como fórmula en el archivo de
parámetros, no como número escrito a mano tras ver B.

**H9 (gravedad 2). P2 es inestable con pocos casos.** En septiembre F publicó 6 negativos en nadir.
Si en agosto el nadir da 0, la razón no existe. Cambio: regla previa, por ejemplo menos de 5
publicaciones de F en nadir vuelve P2 INDECIDIBLE, y acompañar con Fisher.

P5: un apagado parejo de la mitad lo cumple; el nulo por barajado ya está previsto en la sección 6.
Sustrato en referencia: 108 pasadas RUTINA con VRP 0 en noche con alerta, V375, agosto (sección 8).
El "60 % de Suomi NPP sin fila" queda SIN VERIFICAR: el CSV no trae plataforma y el informe citado
no está en la rama.

## 5. Cambios de régimen dentro de la ventana

- El scraper no tiene huecos: 123 a 209 filas del consolidado por día en las dos ventanas.
- **H10 (gravedad 2). La versión del OCR cambia dentro de las dos ventanas**: 21.0 a 29.1 el
  2026-06-12, a 29.2 el 06-14, y a 30.0 el **2026-08-06** (`Version_OCR`,
  `experiments/_s149_verificador_prereg/version_ocr_salida.txt`). Qué cambió en la 30.0: SIN VERIFICAR. Afecta sólo a las positivas que
  existen por OCR y no por tabla (en Villarrica, 1 de 5). Cambio: informar P4 y P6 también con la
  tabla sola, y el conteo de positivas antes y después del 08-06.
- La ventana termina el 08-27 y no cruza #535; como los dos brazos se reprocesan con código de hoy,
  eso sólo importa para la producción congelada, que de todos modos no se puede usar (H5).

## Resumen de cambios pedidos

| # | gravedad | cambio |
|---|---|---|
| H5 | 5 | parámetros por ventana, referencia congelada por ventana, salida del control positivo, script de P2, P5 y P6 probado sobre septiembre, archivos citados en la rama |
| H1 | 4 | corregir el doble conteo y reescribir la sección 2 |
| H2 | 4 | decir que agosto es Villarrica fuerte; decidir si se agrega mayo |
| H6 | 4 | rehacer P6 por conteo y por volcán, o bajarla a informativa |
| H3 | 3 | MODIS en marzo (26 positivas) en vez de junio (13) |
| H4 | 3 | perfiles en `main` o `--ref`; imprimir los dos flags en el job |
| H7 | 3 | P1 condicionada a que B supere 18 % |
| H8 | 2 | fracción exacta 118/141 como fórmula |
| H9 | 2 | regla de muestra mínima para P2 |
| H10 | 2 | sensibilidad al cambio de versión del OCR |
