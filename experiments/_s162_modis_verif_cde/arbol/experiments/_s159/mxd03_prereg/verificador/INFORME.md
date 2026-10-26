# Verificador con contexto limpio: borrador del pre-registro de MxD03 (S159)

Fecha 2026-10-21. Objeto: `experiments/_s159/mxd03_prereg/PREREGISTRO_MXD03.md` (commit `a0484dc8b`). No escribí el
borrador. No toqué nada fuera de esta carpeta ni hice commits ni despachos. Datos: JSON de `origin/main` (`5b922c363`
y `7689c487a`, extraídos con `git show` a `D:\vrp-trabajo\temporales\s159_mxd03_verif\`, borrados al terminar) y la
referencia fijada a los shas que declara el borrador (consolidado `c110787a`, OCR `4ddd5481`). Páginas de los papers
renderizadas a imagen con PyMuPDF en `D:\vrp-trabajo\temporales\s159_mxd03_verif\img\` (fuera del repo).

Scripts y salidas de esta carpeta (`C:\vrp-trabajo\s159-pruebas\experiments\_s159\mxd03_prereg\verificador\`):

| script | salida | qué mide |
|---|---|---|
| `correr_sustrato_fijo.py` (corre `sustrato_copia.py`, copia sin tocar de `sustrato_mirova_modis.py`) | `sustrato_c7689_salida.txt`, `sustrato_hoy_salida.txt` | reproducción de la población del borrador |
| `extra_verif.py` (`main`) | `extra_verif_salida.txt` | alertas sin record, dependencia del OCR, gránulos distintos, pasadas partidas, publicación fuera de P1 y P2 |
| `extra_verif.py` (`detalle_neg_pub`) | `extra_negpub_salida.txt` | quiénes son los 39 negativos limpios que K publica |
| `m_sensibilidad.py` | `m_sensibilidad_salida.txt` | si la prueba M puede bloquear por un cambio de magnitud despreciable |

## Veredicto global: LISTO CON CAMBIOS

La población está bien armada y sus números se reproducen exactos. Pero la regla que va a decidir (P2) no tiene
nulo medido, la prueba M puede bloquear por un 3 % de magnitud, el candado promete algo que el evaluador de D25 no
permite, y una cita le hace decir al paper un ángulo que no dice. Los cambios 1 a 4 son obligatorios antes del sello;
5 a 9 son de redacción o de informe.

## Hallazgos, lo peor primero

### H1. P2 decide con un nulo muerto: el gemelo K2 da 0 por construcción y una sola pasada inclina el veredicto

- SCRIPT:SALIDA `extra_negpub_salida.txt`; borrador §3 (K2 «en el mismo proceso») y §6 (P2, «se espera 0»).
- QUÉ PASA. El fenómeno que mueve P2 no es ruido del runner sino la sensibilidad de los casos de borde a cualquier
  corrimiento de 1 a 5 km. K2 corre el mismo código en el mismo proceso: no puede discrepar de K (M: 85 de 85), así que
  «ruido = 0» no es una medición, es la definición (pregunta 2 del instrumento: el resultado sería el mismo con el
  instrumento muerto). Con ruido 0, P2 da GANA o PIERDE con una pasada neta sobre una base de 49. Y esa base no está en
  Láscar: **31 de los 39 negativos limpios que K publica son de Puyehue-Cordón Caulle** (Láscar 5, Isluga, Chillán y
  Chaitén 1), muchos con el cúmulo entre 18 y 19,8 km del cráter con `inner_radius_km` = 20 (03-29 19,848; 06-19
  19,228; 04-26 18,913; 10-05 18,574; 03-08 18,563; 10-11 18,011). Es el campo difuso del lacolito al borde del radio
  (A20): un corrimiento de 1 km en cualquier dirección lo mete o lo saca. La predicción 2 («casi todas en Láscar») no
  mira donde está la masa de P2.
- CÓMO SE VE EN EL DASHBOARD: invisible hasta la adopción; después, un CUMPLE o NO CUMPLE decidido por el azar del
  borde de Cordón Caulle.
- CÓMO REPRODUCIRLO: `PYTHONPATH=C:\vrp-trabajo\s159-pruebas\scripts python -c "import sys; sys.argv=['x',DIR_JSON,DIR_DL]; import extra_verif as e; e.detalle_neg_pub()"`.
- CONFIANZA: CONFIRMADO que K2 no puede discrepar y dónde está la masa de P2; SOSPECHA el tamaño del vaivén de borde.
- GRAVEDAD 4: decide la adopción.
- CAMBIO: el ruido de P2 tiene que salir de un nulo que pueda dar distinto de 0 (A110): varias semillas de R (no una)
  sobre las pasadas donde la publicación puede cambiar, con P2 decidiendo sólo si el saldo de X cae fuera del rango de
  los saldos de R. Mientras R sólo valga bajo 35°, el saldo sobre 35° (Cordón Caulle tiene 6 de sus 31 publicaciones
  ahí) se informa y no decide. K2 se puede quitar (ahorra un tercio del proceso) o dejar como control de identidad,
  pero no como ruido. Informar P2 también sin Cordón Caulle.

### H2. La prueba M bloquea por un 3 % de magnitud, porque K queda bajo MIROVA en 77 de 80 pares

- SCRIPT:SALIDA `m_sensibilidad_salida.txt`: 80 pares (Láscar 72, Chillán 7, Villarrica 1), K sobre MIROVA en 3 de 80,
  K/MIROVA mediana 0,532. Con X = K·0,97 la mediana de d es +0,0132 con IC95 [+0,0132, +0,0132] (EMPEORA); con
  X = K·1,03, −0,0128 (MEJORA, que no cuenta); con X = K, 0 exacto (control de identidad).
- QUÉ PASA. Con K casi siempre bajo MIROVA, cualquier baja sistemática pone a d del mismo lado en todos los pares y el
  intervalo queda entero sobre 0. El evaluador de D25 juzga el EMPEORA sobre d, no sobre el d′ del comparador D-28
  (`evaluar_d25.py`, docstring de `decidir_estrato`: «EMPEORA se sigue juzgando sobre d»). El borrador mismo dice (§10)
  que este A/B no decide la magnitud MODIS, y M midió X/K de 1,00 a 1,03.
- CÓMO SE VE EN EL DASHBOARD: invisible; bloquearía una adopción por una diferencia de magnitud que el operador no
  distingue (MODIS ya está a la mitad de MIROVA).
- CÓMO REPRODUCIRLO: `python m_sensibilidad.py DIR_JSON DIR_DL`.
- CONFIANZA: CONFIRMADO el lado de K y la mecánica con un factor uniforme; SOSPECHA que X real baje la magnitud (M dio
  subida).
- GRAVEDAD 3.
- CAMBIO: en este A/B, que EMPEORA se juzgue también con el comparador D-28 (d′ contra una ganancia uniforme del mismo
  tamaño), o que M sólo informe. Decidirlo antes de correr.

### H3. El candado no se puede armar como está escrito: `evaluar_d25.py` descarta MODIS

- ARCHIVO:LÍNEA `origin/s159-evaluador-d25:experiments/_s157_prereg_d25/evaluar_d25.py`: `SENS = ("VIIRS375",
  "VIIRS750")` (l. 65); `crudos()` salta todo record MODIS y lo cuenta aparte; `evaluar()` marca ROTO un brazo con
  records MODIS («el brazo declara MODIS apagado»); `ESTRATOS` (l. 128) y `DECLARADO` son sólo VIIRS; la entrada son
  directorios por perfil de un reproceso con líneas `FLAGS_BRAZO`, no la salida por gránulo del arnés.
- QUÉ PASA. El borrador (§8) dice que `evaluar_mxd03.py` «reutiliza sin tocar» ese evaluador «con el sensor fijado a
  MODIS». No se puede: hay que parametrizarlo o escribir otro, y entonces sus pruebas y mutaciones no se heredan.
  Además M no tiene estratos MODIS definidos (¿uno solo? ¿por cenit?).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD 3: un candado que se reescribe después del sello es un criterio no pre-registrado.
- CAMBIO: declarar que se escribe un evaluador nuevo que importa las funciones de regla (`regla_m`,
  `calibrar_simetrico`, `comparar_con_ganancia`, `decidir_estrato`) sin copiarlas, fijar los estratos MODIS de M y el
  formato de entrada del arnés, y pedir pruebas y mutaciones propias.

### H4. Coppola 2016a no dice «sobre ~50°» ni «sobre ~55°»: el umbral es del borrador

- ARCHIVO:LÍNEA `documentacion/sp426.5.pdf`, página de índice 16 (impresa 197 si el capítulo parte en 181, no
  verificado contra el número impreso), «Satellite viewing geometry», mirada como imagen.
- QUÉ PASA. El paper da un solo número: «c. 69% of the data have a satellite zenith >30°», y lo usa para la detección en
  cráteres hondos. La frase sobre la geolocalización («high scan angles ... decrease in the accuracy of the pixel(s)
  geolocation ... up to several kilometres») no trae ángulo. El borrador (§2, §7 y §10) le atribuye «sobre ~50°» y
  «sobre ~55°» y con eso decide que ahí «no se exige nada». Si se toma el número del paper, el aviso empieza en 30°, y
  cubre el tramo 25 a 40° donde están las 4 protegidas expuestas.
- CONFIANZA: CONFIRMADO (página renderizada).
- GRAVEDAD 3: cita que fija qué tramo puede decidir la vara.
- CAMBIO: citar textual («high scan angles», sin ángulo; «>30°» sólo para la detección) y declarar los 35° y 50° como
  cortes propios (35° de 1.23 por el bow tie), elegidos.

### H5. El pareo ya no es una dependencia abierta, y la rama de 300 s entrega a Nicolás un instrumento peor

- SCRIPT:SALIDA `experiments/_s159/pareo_modis/INFORME.md` (hallazgos 1 a 4); `extra_verif_salida.txt` (d).
- QUÉ PASA. El frente terminó: ±120 s acierta y ensanchar empeora (cuenta dos veces la misma pasada y agrega negativos
  donde MIROVA miró el gránulo sin cráter). El borrador (§6) todavía dice «hoy en curso» y deja que, si P1 o P2 cambian
  entre 120 y 300 s, decida Nicolás. En el censo: **222 records son mitad de una pasada partida; 112 son negativos
  limpios y 104 de ésos tienen a su hermano en `sin_info`**, fuera de P1 y P2. Cuando MIROVA lista el gránulo sin
  cráter, el cambio de X en la mitad que sí lo tiene es invisible; con 300 s esa mitad pasa a negativo contra una RUTINA
  de «no miré».
- CONFIANZA: CONFIRMADO los conteos; la fracción de cráter por mitad no la medí aquí (la midió el frente).
- GRAVEDAD 2.
- CAMBIO: fijar 120 s sin rama de decisión; informar aparte los cambios de publicación de X en las 222 mitades (o con
  la variante «órbita» del frente) y en `sin_info` (253, K publica 6) y `far_ref` (10) (A118 c).

### H6. CUMPLE no significa «mejora»: con X idéntico a K el A/B da CUMPLE, y la pregunta del §1 sobre «donde lo ve MIROVA» no tiene prueba que decida

- ARCHIVO:LÍNEA borrador §10, tabla de veredictos; §1, «poniendo el calor donde lo ve MIROVA»; §7.
- QUÉ PASA. CUMPLE pide P1 sin pérdida, P2 sin PIERDE, P3 sin bloqueo y M sin EMPEORA: nada positivo (D25 exigía M
  MEJORA). P3 bajo 35° ya se sabe que da MXD03 MAS CERCA (1.23, n 76), así que no aporta información nueva; la vara de
  paridad (V-TIF) sólo informa y probablemente queda SIN PODER. Lo que el diseño decide es «no daña la réplica»; el §1
  promete además paridad de posición con MIROVA, que nada decide.
- CONFIANZA: CONFIRMADO (lectura de las reglas).
- GRAVEDAD 2: es defendible para un cambio de fidelidad literal, pero el operador y Nicolás tienen que leer CUMPLE
  como «sin daño».
- CAMBIO: renombrar el veredicto (CUMPLE SIN DAÑO) o sacar del §1 la parte de MIROVA; y decir que el poder del veto son
  4 protegidas (las expuestas, todas de 25 a 40° del frame 0), no 48.

### H7. El costo usa 5.465 descargas, pero son 1.232 gránulos

- SCRIPT:SALIDA `extra_verif_salida.txt` (c): 1.232 gránulos MODIS distintos para 5.465 records (todos con `granule`).
- QUÉ PASA. Los 38 s por record de M incluyen bajar L1B y MxD03; en el censo cada gránulo sirve a 4,4 records en
  promedio. Las 58 h son una cota alta si las partes se arman por gránulo; si se arman por record, las descargas se
  repiten entre partes y el «se bajan una vez» del §9 no se cumple. R00 a R19 no están costeados.
- CONFIANZA: CONFIRMADO el conteo; SOSPECHA el costo real (la parte de proceso no está separada).
- GRAVEDAD 1.
- CAMBIO: partir por gránulo, no por record.

### H8. Afirmaciones heredadas que no se reproducen o se estiran

- «5 alertas MODIS de Láscar dependen del OCR» (§10): en esta ventana y con esta referencia son **0**; las 92 alertas
  tienen fila de la tabla y las 50 protegidas lo son por la tabla (`extra_verif_salida.txt` (b)). Viene de la marca
  S151 de A119, no re-medida. Quitar o re-medir.
- «Los GeoTIFF MODIS de MIROVA son todos EPSG:4326»: medido en 10 de 5.540 (8 de una muestra y 2 del 14-sep). Decir
  «en una muestra de 10».
- Coppola 2026, p. 4: la cita de MOD03 es exacta (página renderizada). Pero «accessed via the NASA LANCE/LAADS
  distribution systems» pertenece gramaticalmente a la oración de VIIRS, no a la de MODIS: el argumento «nombra LANCE,
  luego es la cadena NRT» vale para VIIRS y es indirecto para MODIS. Además dice «For the MODIS period (2000 to 2025)».
- «Bajo 40° M no tenía dato» (§1 punto 3 y §5) choca con el propio §1 (n = 4 por lado cerca del nadir). Decir «casi
  sin dato».
- GRAVEDAD 1 cada una.

### H9. El control 3 (arnés igual a producción, 98 %) tolera más diferencias que toda la base de P2

- QUÉ PASA. El 2 % de 5.465 son hasta 109 pasadas, más que las 49 de P2. Además los records de `data/` de la ventana
  están escritos por al menos 16 `codigo_sha` distintos (perfiles `_s154_reproc_k_historico` y `mirova_equivalent`,
  `sustrato_modis_salida.txt`), así que una discrepancia puede ser de versión, no del arnés. No tuerce P1 ni P2 (comparan
  K y X del arnés), pero sí lo que el borrador dice de K («la suma de K es 49»).
- CONFIANZA: CONFIRMADO los shas; SOSPECHA el efecto.
- GRAVEDAD 1.
- CAMBIO: control 3 sin tolerancia en las 92 alertas, los 39 negativos publicados y las expuestas; el resto con el 98 %
  y estratificado por `codigo_sha`.

## VERIFICADO LIMPIO

- **Los números de la población salen de sus scripts, exactos.** `python correr_sustrato_fijo.py <JSON de 7689c487a>
  <dl>` reproduce `sustrato_mirova_modis_salida.txt` línea por línea (sólo cambian los avisos de stderr), y con los JSON
  de `origin/main` de hoy da lo mismo (`diff` vacío). 5.465 pasadas; 50 protegidas (K publica 48), 42 bajo 1 MW (32),
  5.110 negativos limpios (39), 253 `sin_info`, 10 `far_ref`; con 300 s, +1 bajo 1 MW y +119 negativos. Por volcán:
  Láscar 40 + 40, Chillán 9 + 1, Villarrica 1 + 1, los otros ocho 0 alertas. 44 de 50 protegidas con cenit ≤ 40°;
  43 de 44 y 38 de 39 noches cubiertas por VIIRS; las 4 protegidas expuestas y la base de P2 (10 + 39 = 49).
- **La población no está condicionada a lo que publica K.** Es el censo de records de K, publiquen o no; 0 alertas
  MODIS nocturnas de MIROVA en la ventana quedan sin record a ±120 s (`extra_verif_salida.txt` (a), contrastado con
  `banco_paridad.alertas_sin_record`). Único condicionamiento: X sólo corre donde K dio record; con 0 alertas fuera, no
  pesa.
- **Etiquetas positivas sólo de la tabla**: ninguna alerta MODIS de la ventana depende del OCR, así que los hitos del OCR
  de A119 no tocan este A/B.
- **Líneas del §4 y del §1** en `pipeline/process_modis.py` de `7689c487a` (265-266, 292-295, 385-396 `_interp_geo` con
  `zoom` de orden 1, 513, 560, 564, 581-582, 657, 791, 838, 959, 977, 1046, 1141-1142, 1168, 1287, 268-271,
  1624-1625): dicen lo que el borrador afirma, y `pipeline/` no cambió entre `7689c487a` y `origin/main`.
- **Flags** leídos de `pipeline.profile` con `VRP_PROFILE=mirova_equivalent`: `ENABLE_UTM_REGRID`,
  `ENABLE_VENT_PATH_MODIS`, `ENABLE_TEST1_PATH` y `ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER` en False.
  `clase_mirova.SENSORES_MINIMA = ("VIIRS375",)` (l. 108): D-9 no toca MODIS. `banco_paridad.TOL_S = 120` (l. 76).
- **Coppola 2026 p. 4** (MOD03 y MYD03 «Terrain-Corrected Geolocation products») y **Coppola 2016a** (extracción de
  «pixel(s) geolocation (latitude and longitude)» y recorte y remuestreo a 1 km, página de índice 2): textuales, mirados
  como imagen.
- **TIF**: según `tif_modis_14sep_crs_salida.txt`, la celda de máximo de Láscar 14-sep 07:35 está en (fila 23, col 0),
  lon −67,9715, lat −23,352: a unos 24,7 km al oeste del cráter, en el borde de la caja. La lectura del borrador es
  correcta; uso de máximo local, hora del índice y md5 nuevo bien planteados.
- **Costo de la alternativa** (2,57 min por día-volcán, 1,86 de búsqueda y descarga; 2.530 días-volcán por brazo):
  sale de `tiempo_por_dia_reproc_salida.txt`. **38 s por record**: 51,5 min en 81 intervalos, `tiempo_modis_probe_m_salida.txt`.

No verifiqué: el control positivo de geometría de S151 (2,581 km), el número impreso de las páginas 183 y 197, ni la
georreferencia de los TIF MODIS (no bajé ninguno).
