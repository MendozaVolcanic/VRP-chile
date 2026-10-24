# T4 y T6 (fase 0 del programa por sensor): alerta y protegida por pasada, y protegida de cráter

Sesión hija «Instrumento» de S162, 2026-10-24. Programa: `docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md`
§8.4 y V375-A (§4).

## Qué fenómeno arregla

MIROVA informa cada pasada por dos canales: la tabla de `latest.php` (el más creíble) y el OCR de la imagen de cada
volcán. Hasta hoy la referencia se juzgaba **fila por fila**: si la tabla decía que en una pasada MIROVA vio calor
lejos del cráter (FALSO_POSITIVO) o nada (RUTINA) y el OCR de la imagen decía ALERTA de 1 MW o más en esa misma
pasada, la pasada salía **protegida**. Y la fila de la tabla (05:18:02) y la del OCR (05:17:58) de una misma pasada
caían en minutos distintos y podían contar como dos pasadas.

## Qué cambia en el código (`scripts/clase_mirova.py`, sólo agregado)

- `resumir_pasadas(filas, canal, regla_minimas)`: junta las filas del mismo volcán y sensor a 120 s o menos de la
  primera (sin encadenar) y decide el estado de la pasada (`alerta`, `minima`, `sin_geometria`, `fp`, `rutina`).
  **Si la tabla tiene la pasada, la tabla decide**; el OCR sólo se anota (`ocr_contradice_tabla`). Si no la tiene,
  decide el OCR (`solo_ocr`). Canal `tabla`: el OCR no entra. Regla D-9 en SN por defecto.
- `es_protegida(pasada, lectura)`: lectura A (decide) y B (informa), sobre la pasada.
- `protegida_de_crater(pasada, radio_km, plataforma)`: V375-A, **informada al lado de la lectura A, nunca en su lugar**.
  Motivos para no serlo: `ocr_sin_distancia_medida` (sólo OCR antes del 2026-06-13, A119), `ocr_snpp_antes_del_hito`
  (sólo OCR de Suomi NPP antes del 2026-10-09; la distancia puede ser de otra pasada), `plataforma_desconocida_antes_del_hito`
  (la referencia no trae plataforma; la da el record nuestro), `sin_distancia`, `lejos_del_crater` (sobre
  `inner_radius_km`).
- Las funciones viejas (`alerta_protegida`, `pasadas_protegidas`) **no cambian**: las usan evaluadores con
  pre-registro sellado, que tienen que reproducirse tal cual.

## Cuántos casos mueve hoy (`t4_t6_medir_referencia.py` → `t4_t6_medir_referencia_salida.txt`)

Referencia unificada del snapshot del repo (`origin/main` 80b819828): 45.344 filas (44.215 tabla, 1.129 OCR).

- **T4: 0.** Protegidas A con la regla original: 479 con la función vieja y 479 con la nueva, 0 claves de diferencia,
  0 pasadas con filas de alerta en dos minutos, **0 pasadas donde el OCR contradice a la tabla**. El riesgo sigue
  latente, como midió la auditoría de Mirova-v1; el arreglo lo cierra por construcción para cuando la tabla pierda
  una fila y el OCR no.
- Con SN: unión 479 (VIIRS 375 248, VIIRS 750 162, MODIS 69; 175 sólo OCR); **tabla sola 304** (119, 117, 68).
- **T6, protegida de cráter** (unión, SN): MODIS 68 de 69; **VIIRS 375 123 de 248**; VIIRS 750 118 de 162. Motivos en
  VIIRS 375: 94 sólo OCR sin distancia medida, 48 Suomi NPP antes del hito, 71 plataforma desconocida, 1 sin
  distancia; **0 lejos del cráter** en los tres sensores (el scraper ya marca FALSO_POSITIVO fuera de su radio).
- Las 76 protegidas VIIRS con plataforma desconocida **no tienen ningún record de producción a ±10 min**: producción
  no tiene esas pasadas. Es un dato para T1 (cobertura contra la referencia), no un defecto de esta regla.

## Pruebas

- `tests/test_clase_mirova_pasadas_s162.py`: 26 pruebas (canal, ventana y borde de 120 s, no encadenar, tabla
  manda, estados, umbral de 1 MW, SN, no mutar la entrada, los motivos de cráter y sus bordes).
- Roja por aserción: la mutación M1 (la semántica vieja, la tabla deja de mandar) hace fallar 3 pruebas por aserción.
- Mutaciones (`mutar.py`, `mutaciones_t4_t6.json` → `mutaciones_t4_t6_salida.txt`): **20 de 20 atrapadas por
  aserción**, con control de caída (una mutación que hace caer las pruebas con otra excepción no cuenta; la primera
  versión de M10 cayó y se reescribió). Dos mutaciones vivas en la primera corrida (lectura B con RUTINA de VRP, y el
  hito de Suomi NPP alcanzando a MODIS) pidieron dos pruebas nuevas.

## Límites

- Si la tabla tiene una alerta mínima (0,04 MW, VIIRS 375) y el OCR una de 1,5 MW en la misma pasada, la regla D-9
  no la vuelve RUTINA (protege la del OCR) y la tabla decide 0,04: queda alerta no protegida. Caso de borde con 0
  ocurrencias hoy (0 contradicciones).
- `radio_km` es el `inner_radius_km` del tablero, no el `limite_km` del scraper (que no está en este repo).
