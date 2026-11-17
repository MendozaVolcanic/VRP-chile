# Adenda V al pre-registro diurno: el día con la vía «código MIROVA» (S190, issue #813)

Estado: **BORRADOR, sin sellar.** Lo sella Nicolás. Hasta el sello no se despacha nada.

Base: `experiments/_s163_diurno_k/PREREGISTRO.md` (sellado el 2026-10-26, tag `s163-diurno-k-sellado`), que a su vez
reemplazó la regla G1 y G2 de `experiments/_s151_ab_diurno/PREREGISTRO.md` y `ADENDA_K.md`. Todo lo que esta adenda no
cambia rige tal cual: unidad (la pasada de MIROVA), «publica» = `isValidDetection` del tablero corrido con node (A97),
día = elevación solar mayor que 0 (`pipeline.store._solar_elevation`), clases por periodo (§4), compuertas I1 a I6
(§5), prueba D y casos a a e (§6.2), opción e-ii, días excluidos por huecos de NASA con la regla (a) más (b') y
referencia congelada antes de despachar.

## 0. Por qué una adenda nueva

El fenómeno: de día el canal de 4 µm suma a la emisión térmica la luz del Sol reflejada. Una nube, un salar o un
glaciar al mediodía levantan píxeles sin nada caliente debajo. MIROVA igual mira de día, con umbrales más altos, y
publica: desde marzo, 21 alertas diurnas MODIS (18 de 1 MW o más), 75 de VIIRS 375 (60) y 31 de VIIRS 750 (30), casi
todas de Chillán en octubre y noviembre (`inventario_salida.txt`). Nosotros no tenemos ni una pasada diurna en
`data/mirova_equivalent/` (mismo archivo, 0 de 76.543 records). Esas alertas las perdemos por construcción.

El A/B sobre K (S163) terminó en DECIDE NICOLÁS por una razón que ya no existe: la rama diurna de K usaba los
umbrales de la Tabla 1 (K1 -0,6), y el código de MIROVA usa -0,5 y descarta el reflejo bajo 12°. Desde S186 producción
corre la vía en los tres sensores, y el detector de la vía **es** el `.m` de MIROVA, con su rama diurna
(`pipeline/mirova_v750_codigo.py::detectar_mirova`: con `dayflag` 1, NTI absoluto -0,5, 15σ en los dos pases,
pisos 0,02, y escena descartada si el ángulo de reflejo es menor que 12°). Lo que impide que esa rama actúe son tres
compuertas previas, todas fuera del detector:

| compuerta | dónde | VIIRS (375 y 750) | MODIS |
|---|---|---|---|
| filtro antes de bajar el gránulo | `pipeline/fetch.py:1311`, vía `diurno.aplica_filtro_nocturno` | abre con `enable_daytime_viirs` | **no abre con ningún flag** |
| salto del gránulo ya bajado | `scripts/run_pipeline.py:205`, misma función | abre con `enable_daytime_viirs` | **no abre con ningún flag** |
| rechazo del record diurno | `pipeline/store.py::_reject_daytime` | abre con `enable_daytime_viirs` | abre con `enable_daytime_modis` |

MODIS es justo el caso de S92: un flag que abre una sola compuerta y mide cero sin saberlo. Esta adenda agrega MODIS
al A/B y, para eso, un cambio de una línea en `pipeline/diurno.py::aplica_filtro_nocturno` que lo hace seguir a
`ENABLE_DAYTIME_MODIS` (apagado en producción, así que producción no cambia; prueba en
`tests/test_rama_diurna_viirs_s151.py`). `diurno.py` no está en la lista de A45; `store.py` y los procesadores no se
tocan.

## 1. Brazos

Dos perfiles nuevos, aislados (`data_subdir` propio, A47), que heredan de `mirova_equivalent` (la vía en los tres
sensores, `enable_*_codigo_mirova: true`):

- **control** `_s190_ab_diurno_via_control`: producción tal cual, con su directorio.
- **diurno** `_s190_ab_diurno_via_on`: el control más `enable_daytime_viirs: true` y `enable_daytime_modis: true`, y
  nada más (prueba sobre todas las constantes de `pipeline.profile`, como `tests/test_perfiles_diurno_k_s154.py`).

Sin `--no-night-filter`: lo que se prueba es que los flags abren solos las tres compuertas (trampa de S92).

`enable_daytime_modis` también cambia los umbrales diurnos del camino K de MODIS. En la vía eso no actúa (la vía
devuelve el record antes). Sí actuaría en los records que caen a K (`via_codigo_mirova` en `sin_grilla`, `sin_mxd03`
o `geo_distinta`): esos records diurnos se cuentan y se listan aparte (M6) y **no entran** a la regla, porque no son lo
que se adopta.

## 2. Ventanas

Las de S163 más una nueva. Los 11 Tier A. Canal unión (tabla más OCR desde el 2026-06-13, A119).

| ventana | fechas | MODIS: protegidas / alertas / pasadas diurnas | VIIRS 375 | VIIRS 750 |
|---|---|---|---|---|
| W2 | 06-13 a 06-30 | 0 / 1 / 388 | 11 / 12 / 585 | 1 / 1 / 617 |
| W3 | 07-20 a 07-31 | 0 / 0 / 263 | 1 / 3 / 425 | 0 / 0 / 410 |
| W4 | 08-13 a 08-31 | 0 / 1 / 435 | 5 / 9 / 546 | 2 / 2 / 525 |
| W5 | 09-01 a 09-20 | 0 / 0 / 473 | 4 / 6 / 579 | 1 / 1 / 550 |
| W6 | 10-01 a 10-14 | 1 / 1 / 316 | 5 / 6 / 412 | 2 / 2 / 397 |
| **W7 (nueva)** | **10-15 a 11-15** | **15 / 15 / 759** | **29 / 30 / 788** | **24 / 24 / 812** |
| W2 a W7 | | 16 / 18 / 2.634 | 55 / 66 / 3.335 | 30 / 30 / 3.311 |

Conteo grueso de `ventanas.py` (`ventanas_salida.txt`); el que decide lo cuenta el evaluador sobre la referencia
congelada. Control de instrumento: W2 a W6 da 26 protegidas en VIIRS 375 y 6 en VIIRS 750, lo mismo que la tabla del
§3 del pre-registro de S163. W1 (Láscar en marzo) no se corre: es anterior a abril (A119) y su tasa no se suma.

**Por qué W7.** En S163 no había W7 porque la tabla del árbol se cortaba el 2026-10-19; hoy cubre hasta el 2026-11-16
y ningún día de W7 queda sin filas de la tabla en los 11 Tier A. W7 trae la erupción de Chillán, que es donde está casi
todo lo que MIROVA publica de día, y casi todas las protegidas de MODIS. El verificador de S167 advirtió (VD167-03)
que el beneficio salía casi entero de Chillán en W6; por eso **el veredicto se lee también sin Chillán** (§4, R-CH).

## 3. Lo que cambia en el instrumento

`evaluar_diurno_via.py` reusa `experiments/_s163_diurno_k/evaluar_diurno_k.py` (importa, no copia) y cambia sólo esto:

1. **Sensores**: MODIS, VIIRS 375 y VIIRS 750. Para MODIS, la vara de I4 (c) es la tasa nocturna de pasadas sin
   record de MODIS en la noche de producción del sustrato, con Clopper-Pearson al 95 %, igual que en VIIRS.
2. **I1, cableado de la vía**: por log, `ENABLE_MODIS_CODIGO_MIROVA`, `ENABLE_V375_CODIGO_MIROVA` y
   `ENABLE_V750_CODIGO_MIROVA` verdaderos en los dos brazos; `ENABLE_DAYTIME_VIIRS` y `ENABLE_DAYTIME_MODIS` falsos en
   el control y verdaderos en el diurno. Por record: `regimen.codigo_sha` igual al commit del tag, los 40 caracteres.
3. **I2, la palanca actuó**: el marcador ya no es `diag_umbrales_diurnos` (la vía no pasa por ahí) sino
   `diag_codigo_mirova.dayflag`. El brazo diurno trae records con dayflag 1 en cada ventana y sensor con pasadas
   diurnas de MIROVA; el control trae cero records diurnos (por elevación solar) en los tres sensores.
4. **Dayflag contra elevación**: la vía decide el día con el cenit solar del píxel más cercano al volcán
   (`solar_zenith` menor o igual que 90°) y el evaluador con la elevación de `store`. No coinciden en el crepúsculo:
   hoy hay 5 records MODIS de producción con dayflag 1 que `store` llama noche (`inventario_salida.txt`). El
   evaluador clasifica por elevación (la regla de §4 de S163) y **informa** la tabla cruzada dayflag contra elevación.
   Un record sin ángulos cae a noche en silencio (`geom.get("solar_zenith", 180.0)`): se cuentan los records diurnos
   por elevación sin `solar_zenith_deg`, y si hay alguno, I2 falla.
5. **Reflejo**: las escenas que el `.m` descarta (`diag_codigo_mirova.motivo == "sunglint"`) se cuentan por sensor
   (M7). Es la defensa principal de MIROVA contra el Sol y tiene que verse actuar: si en W2 a W7 no descarta ninguna
   escena VIIRS diurna, se informa como sospecha de cableado antes de leer el veredicto.
6. **Pasadas que la tabla no lista** (VD167-01): una publicación diurna del brazo en una pasada sin fila de MIROVA no
   entra al criterio de S163. Aquí se cuentan por sensor (M8) con su magnitud. Si en un sensor hay 5 o más de 1 MW o
   más, ese sensor no puede salir ADOPTAR: pasa a DECIDE NICOLÁS CON M4.
7. **Magnitud** (M5, nueva): mediana del cociente nuestro/MIROVA en las alertas diurnas recuperadas, por sensor. Con
   5 o más pares, un cociente fuera de 0,5 a 2 impide ADOPTAR (DECIDE NICOLÁS); con menos de 5, se informa.
8. **Noches intactas (I5)** sin cambios: misma publicación y misma magnitud en los records nocturnos de los dos
   brazos, ahora también en MODIS (el desempate del top-100 que depende de la CPU es de K; en la vía se espera
   identidad, y si no la hay se lista).

## 4. Regla de decisión

Por sensor, W2 a W7, los casos a a e del §6.2 de S163 con la opción e-ii (sellada en S163), más:

- **R-CH**: el mismo veredicto calculado sin Nevados de Chillán. Si con Chillán sale ADOPTAR y sin Chillán sale NO
  ADOPTAR, el sensor pasa a DECIDE NICOLÁS CON M4 (el beneficio sería de un solo volcán en erupción).
- **R-W7**: el veredicto también sin W7. Se informa; no cambia el veredicto salvo que sin W7 salga NO ADOPTAR, caso en
  que pasa a DECIDE NICOLÁS CON M4.
- M5 y M8 como en el §3.

Veredicto global:
- cualquier I1 a I4 falla: INVÁLIDO POR INSTRUMENTO; I5 o I6: INDECIDIBLE (repetir desde el mismo tag);
- por lo demás, **un veredicto por flag**: `enable_daytime_modis` sigue al de MODIS; `enable_daytime_viirs` abre VIIRS
  375 y 750 juntos, así que ADOPTAR exige los dos en ADOPTAR o uno en ADOPTAR y el otro en SIN CAMBIO. Un sensor VIIRS
  en ADOPTAR y el otro en NO ADOPTAR da DECIDE NICOLÁS (separar el flag es un parche en `pipeline/`, A45).
- Se elimina la cláusula de S163 «VIIRS 750 en ADOPTAR pasa a DECIDE NICOLÁS»: existía porque la rama diurna de K no
  seguía el código de MIROVA, y la vía sí lo sigue.

Encender el día en producción es un PR aparte que espera el «mergea #N» de Nicolás, con A45 (perfil
`mirova_equivalent.yaml`), y antes de él el frontend tiene que dejar de suponer que toda pasada es nocturna
(`frontend/index.html`, texto de ayuda y frescura por noche; `pipeline/diurno.py`, nota FRONTEND).

## 5. Controles que pueden fallar (A110, A116)

Antes de despachar, sobre el commit del instrumento:
- **mutaciones** del evaluador (al menos: I2 mirando el marcador viejo, MODIS fuera de la lista de sensores, R-CH
  apagado, M8 sin umbral, dayflag ignorado): cada una tiene que cambiar un veredicto en un caso sintético; se cuentan
  sólo las atrapadas por aserción, con control de caída (S156);
- **prueba de humo** con un despacho corto real (un volcán, tres días de W7, los dos brazos): tiene que dar records
  diurnos con dayflag 1 en los tres sensores y cero en el control. Si da cero diurnos en MODIS, el cambio de
  `diurno.py` no llegó y no se despacha lo demás;
- **brazo perfecto y brazo ruidoso** sintéticos sobre la referencia congelada: el perfecto (publica justo las alertas
  de MIROVA) no puede salir NO ADOPTAR; uno que publica todas las pasadas diurnas no puede salir ADOPTAR.

## 6. Despacho y costo

Workflow nuevo `reproc-s190-ab-diurno-via.yml` copiado de `reproc-s151-ab-diurno.yml`: grupo propio, `max-parallel: 3`,
un volcán y un brazo por job, sólo `EARTHDATA_TOKEN` (A71), sin push a main, salidas como artefactos. Se despacha
desde un tag del commit del instrumento (sha de 40 caracteres), una ventana por despacho, `brazos` y `control`
explícitos. Costo esperado por el de S163 (unas 117 h de runner y 39 h de reloj para W2 a W6 en dos sensores), más
MODIS de día y W7 (que es casi tan grande como W2 a W6 juntas): del orden de **250 h de runner y 3 a 4 días de reloj**
con `max-parallel: 3`. Antes de cada despacho se avisa a la sesión dueña del loop (runners y cuenta de NASA
compartidos con las tandas y el NRT).

## 7. Después

Verificador de contexto limpio (effort high) sobre el resultado, informe con veredicto por sensor, PR a main con esta
adenda, el instrumento y el resultado, y comentario en #813.
