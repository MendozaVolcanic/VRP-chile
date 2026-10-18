# Cabeceras de las 11 protegidas solo OCR de Suomi NPP en V1 (A/B F/K)

Tarea de solo lectura, 2026-10-17. Ningun repo editado. Todo lo de aqui sale de archivos en
`C:\Users\nmend\AppData\Local\Temp\claude\cabeceras_snpp_v1\`.

## 0. En una linea

**En las 11 la imagen que leyo el OCR es de una pasada POSTERIOR** (cabecera "Last Update" distinta de la hora
de la fila, 11 de 11). La distancia y la clase de las 11 filas son de otra pasada. Recuperando la distancia
PROPIA desde la serie "Last Month" de imagenes posteriores: las 5 de Chillan quedan del lado crater de todos
modos; las dos de Tupungatito que F y K dejan de publicar quedan LEJOS (unos 22,6 y 9,6 km, inner 7 km);
dos de Isluga quedan probablemente lejos; dos casos son ambiguos.

## 1. Como se saco la lista

- `listar_11.py`: importa `experiments/_s151_prereg_fk_11/evaluar_fk.py` del repo, corre su `proteccion()` sobre
  la referencia congelada de V1 (`_congelado_v1`, Mirova-v1@c5944c61, manifiesto OK segun `v1.log` l. 4) y las
  tablas `C:\Users\nmend\AppData\Local\Temp\claude\v1_38639658446\eval\tmp\t_C0_F.json` y `t_C0_K.json`, con el
  mismo predicado `ocr_snpp` del evaluador. Da **11** (9 VIIRS 375 + 2 VIIRS 750), igual que `v1.log` l. 11-12.
  Salida: `las_11.json`.
- Filas crudas del OCR: `_congelado_v1/registro_vrp_ocr.csv` (Ruta Foto, nota) y el CSV vivo de Mirova-v1
  `monitoreo_satelital/registro_vrp_ocr.csv` @ f1467a71 (2026-10-17 12:03 UTC) para `Distancia_aprox_*`
  (copia en `ocr_actual.csv`).
- Imagenes: `bajar.py` baja por la API de GitHub (archivos sueltos, sin clonar) las carpetas del dia de cada
  pasada (`monitoreo_satelital/imagenes_satelitales/<Volcan>/<fecha>/`, rama main al 2026-10-17) a `imagenes\`;
  md5 en `md5_imagenes.json`. Cabeceras leidas mirando `montaje_cabeceras_1.png` y `_2.png` (recortes de las 33
  imagenes VRP, Dist y Latest de las 11 filas), `montaje_latest.png` y `montaje_dist.png`.
- Las otras pasadas de la misma noche: tabla congelada `_congelado_v1/registro_vrp_consolidado.csv`.

## 2. Tabla

Distancias de MIROVA en km desde SU punto de referencia (no desde el crater: en Tupungatito las detecciones
"<7 km" se apilan siempre en ~5,2 km, ver la serie de cualquier Dist.png). C0/F/K: publica (1/0) y distancia del
cumulo al crater nuestro, de `las_11.json`.

| pasada | VRP MIROVA | Dist OCR (fila) | Distancia_aprox (min-max, metodo) | cabecera de la imagen | C0 | F | K | distancia PROPIA recuperada | de quien son dist y clase |
|---|---|---|---|---|---|---|---|---|---|
| Isluga V375 2026-09-09 06:06 | 1,91 | 0,81 | 0,95-24,8 ambiguo | 09-Sep 06:30:01 (NaN, NONE) | 1 / 0,84 | 1 / 0,84 | 1 / 0,84 | ~24 km (columna del 09-sep: 24 y ~0,8; la de ~0,8 es 05:30, 0,84 en tabla) | otra pasada (rojos de 05:30:02) |
| Isluga V375 2026-09-28 05:12 | 1,63 | 0,95 | 0,54-16,67 ambiguo | 28-Sep 05:30:01 | 1 / 1,03 | 1 / 1,03 | 1 / 1,03 | probable ~16,7 km (05:30 y 06:18 estan en tabla a 0,84 y 0,53) | otra pasada (05:30:01) |
| Isluga V375 2026-10-03 05:18 | 1,62 | 0,95 | 0,95-22,9 ambiguo | 03-Oct 05:36:01 | 1 / 0,94 | 1 / 0,94 | 1 / 0,94 | AMBIGUO: en la imagen de 05:36 la columna del 03-oct solo tiene la estrella (<1 km); el 22,9 sale de una imagen del 17-oct y puede ser otra pasada | otra pasada (05:36:01) |
| Chillan V375 2026-09-29 05:00 | 1,41 | 0,95 | 0,95-1,62 ambiguo | 29-Sep 06:00:02 | 1 / 1,53 | 1 / 1,18 | 1 / 1,18 | <5 km sea cual sea (todos los puntos del 29-sep bajo 2,5) | otra pasada (06:00:02); lado crater igual |
| Chillan V375 2026-10-01 06:00 | 5,07 | 0,95 | 0,95-2,43 solapado | 01-Oct 06:18:01 | 1 / 0,57 | 1 / 0,57 | 1 / 0,57 | <5 km | otra pasada (06:18:01); lado crater igual |
| Chillan V375 2026-10-05 06:24 | 8,24 | 0,95 | 0,95 solapado | 05-Oct 06:48:01 | 1 / 0,65 | 1 / 0,55 | 1 / 0,55 | <5 km | otra pasada (06:48:01); lado crater igual |
| Chillan V750 2026-10-01 06:00 | 10,0 | 1,76 | sin_control | 01-Oct 06:18:01 | 1 / 0,68 | 1 / 0,68 | 1 / 0,68 | <5 km (todos los puntos V750 del 29-sep al 05-oct bajo ~2 km) | otra pasada (06:18:01); lado crater igual |
| Chillan V750 2026-10-05 06:24 | 7,0 | 1,76 | sin_control | 05-Oct 06:48:01 | 1 / 0,61 | 1 / 0,61 | 1 / 0,61 | <5 km | otra pasada (06:48:01); lado crater igual |
| Tupungatito V375 2026-09-14 06:18 | 2,22 | 2,97 | 13,11 unico | 14-Sep 06:36:01 (NaN, NONE) | 1 / 2,94 | 1 / 0,17 | 1 / 0,17 | AMBIGUO: esa noche detectaron 05:00 (0,10), 05:42 (0,13, 5,21 en tabla) y 06:18; la columna tiene ~13 y ~5,2 | otra pasada |
| **Tupungatito V375 2026-09-28 05:18** | 2,51 | 5,27 | 5,27-22,57 ambiguo | 28-Sep 05:36:01 | 1 / 2,94 | **0 / 21,57** | **0 / 21,57** | **~22,6 km, LEJOS** | otra pasada (05:36:01, 0,09 MW, 5,21 en tabla) |
| **Tupungatito V375 2026-09-29 04:54** | 1,86 | 5,68 | 5,41-9,59 ambiguo | 29-Sep 06:36:00 (NaN, NONE) | 1 / 0,34 | **0 / 9,40** | **0 / 9,40** | **~9,6 km, LEJOS** | otra pasada (rojos de 05:18:01, 0,04 MW, 5,41 en tabla) |

Notas de la tabla:
- VRP propio confirmado en el panel "Latest Images" (celda de su hora) para Isluga x3 y Tupungatito x3
  (1,91 / 1,63 / 1,62 / 2,22 / 2,51 / 1,86). En Chillan no mire ese panel: VRP propio SIN VERIFICAR aqui.
- Archivos repetidos bajo dos horas (md5 identico, `md5_imagenes.json`): Isluga 2026-09-28 05-12-00 = 06-18-02;
  Chillan 2026-10-01 06-00-00 = 18-42-01. Misma familia que A106.
- Isluga 09-09 y Tupungatito 09-14/09-29: la imagen guardada es de una pasada SIN deteccion (NaN); el OCR no
  leyo estrella sino "grupo de pixeles rojos" de la serie (nota de la fila), o sea un punto de otra pasada.

## 3. Las dos de Tupungatito

Mecanismo: el scraper guardo con la hora de Suomi NPP la imagen de la pasada siguiente. El OCR leyo la estrella
(28-sep, 5,27 = la pasada de 05:36, que la tabla da a 5,21) o un punto rojo (29-sep, 5,68 ~ la de 05:18, tabla
5,41). Esos ~5 km son el lado "crater" de MIROVA en Tupungatito.

La distancia propia se recupera de la serie "Last Month": cada noche tiene exactamente dos pasadas con
deteccion (panel Latest: 28-sep 05:18 y 05:36; 29-sep 04:54 y 05:18; el resto NaN) y la columna tiene
exactamente dos puntos. Uno es el de la tabla (~5,2 a 5,4); el otro, **22,6 km** (28-sep) y **9,6 km**
(29-sep), es el de la pasada de Suomi NPP. `Distancia_aprox_max_km` del CSV vivo da lo mismo (22,57 y 9,59).
Ambos sobre el inner de 7 km: con la clase propia, **estas dos pasadas no serian protegidas A**.

**La evidencia apoya "objeto lejano", no "crater"**, para la deteccion de MIROVA. Que el cumulo de F y K sea el
MISMO objeto queda **SIN VERIFICAR**: solo coinciden radios. Medido desde `mirova_center` (-33,42694, -69,80039,
`volcanoes.yaml` l. 807-808, que supongo el origen de MIROVA, SIN VERIFICAR): F queda a 23,9 km (rumbo 26) y
9,3 km (rumbo 46), contra 22,6 y 9,6 de MIROVA. La serie no trae acimut (A93, A107). Intente leer posicion en
las miniaturas del panel Latest y no hay marca de pixel caliente legible ni extension conocida: sin resultado.
La direccion pediria el GeoTIFF de esa pasada, y los de MIROVA estan congelados desde el 2026-09-22 (memoria
`reference_mirova_tif_congelados_20260922`): para estas fechas probablemente SIN DATO.

## 4. Lo que cambia (para quien decide)

1. Las 11 tienen distancia y clase de otra pasada (11/11). El pre-registro hizo bien en sacarlas de la lectura A.
2. Las 2 que F y K pierden son, por la distancia propia de MIROVA, detecciones lejanas: no son perdidas de
   alerta protegida del crater.
3. Efecto lateral: 2 de Isluga (09-09 seguro, 09-28 probable) tambien son lejanas para MIROVA y C0, F y K
   publican ahi un cumulo a ~1 km del crater. No afectan el veto, pero en la lectura A cuentan como
   coincidencia cuando no lo son.
4. Ambiguas: Isluga 10-03 y Tupungatito 09-14 (las dos publicadas por los tres brazos).

## 5. Limites

- La asignacion de punto a pasada asume que cada pasada con deteccion deja un punto y que las pasadas NaN no
  dejan ninguno; resolucion de la serie ~15 px por dia, asi que pasadas de la misma noche caen en la misma
  columna y se separan solo por valor.
- Lei los valores de la serie a ojo; donde coinciden con `Distancia_aprox_*` lo digo. No corri el algoritmo de
  Mirova-v1 que genera esa columna.
- Imagenes bajadas de la rama main de Mirova-v1 al 2026-10-17, no de un commit fijo.
