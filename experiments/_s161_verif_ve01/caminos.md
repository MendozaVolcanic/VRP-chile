# Caminos de ruptura de VE-01 (escrito antes de abrir ningún archivo citado)

Verificador con contexto limpio, S161. CARPETA =
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\frosty-lamport-3fef52\experiments\_s161_verif_ve01\`.
RANGO de ID propios: VE01-V01 en adelante.

Afirmación: «VE-01: la alerta protegida de MIROVA de Tupungatito del 2026-09-29 04:54 UTC (VIIRS 375,
1,86 MW) está en el cráter según el panel "Latest Images" de MIROVA, y nosotros no la publicamos porque
nuestro píxel cae a 9,42 km ENE, fuera del radio interno: es una protegida perdida por radio.
CONFIRMADO, gravedad 4.»

La afirmación tiene cinco piezas, y cada una puede caer por separado:
(a) existe una alerta protegida (1 MW o más) de MIROVA de Tupungatito a las 04:54 UTC del 29-sep, VIIRS 375;
(b) esa alerta está en el cráter;
(c) nosotros tenemos un record de esa pasada con el píxel a 9,42 km ENE;
(d) ese record no se publica, y no se publica por el radio interno (no por otra condición del predicado);
(e) por lo tanto es una protegida perdida «por radio».

## C1. La miniatura PNG es de otra pasada (A106, memoria reference_ocr_imagen_de_otra_pasada)
- MIROVA sirve a veces la misma imagen bajo una hora nueva, y el panel "Latest Images" muestra la
  última imagen al momento de la captura, no necesariamente la de las 04:54. El nombre del archivo
  (`20260929_122836`) sugiere una captura a las 12:28 UTC, siete horas y media después: en ese lapso
  pudo haber otras pasadas VIIRS 375 (NOAA-20, NOAA-21, Suomi NPP diurna) y la miniatura puede ser de
  una de ellas, quizás diurna.
- Comprobar: qué pasadas hay de Tupungatito en la referencia y en nuestros records entre 04:54 y
  12:28 del 29-sep; si la miniatura tiene cabecera con hora ("Last Update" u hora de adquisición);
  md5 de la miniatura contra otras capturas del mismo volcán (¿se repite?).

## C2. La georreferencia por correlación encaja por textura, no por calor (A110)
- Correlacionar la miniatura con TIF nocturnos despejados alinea la textura del terreno (relieve,
  nieve, borde de escena), no la posición de la anomalía. Si el encaje lo domina la textura, la
  posición del píxel caliente en la miniatura puede estar corrida aunque el encaje sea "bueno".
- La miniatura es un PNG con paleta de colores, quizás con leyenda, ejes o reescalado: la
  correspondencia color a valor y píxel a grilla puede no ser lineal.
- El nulo con "otro volcán" puede ser demasiado fácil: un volcán distinto tiene otra textura, así que
  da correlación baja por construcción. El nulo que importa es el mismo volcán con desplazamientos
  (¿cuán ancho es el pico de correlación? ¿hay picos secundarios a 5 a 10 km?), o el mismo volcán en
  otra fecha sin anomalía.
- Comprobar: re-correr el script; medir la correlación en función del desplazamiento (anchura del
  pico, segundo máximo); medir dónde caería la anomalía con el segundo mejor encaje.

## C3. La protegida es sólo OCR de Suomi NPP antes del 2026-10-09 (A119)
- Si la alerta existe sólo en el canal OCR, su VRP de 1,86 MW y su distancia pueden venir de la imagen
  de otra pasada (memoria reference_ocr_imagen_de_otra_pasada: 5 de 5 en Suomi NPP). Entonces la
  "protegida" puede no corresponder a la pasada de 04:54, o el VRP puede ser de otra.
- Si está en la tabla (CONS) con su `Distancia_km`, esa distancia sola dice si MIROVA la ubicó cerca
  del cráter, sin miniatura. Si CONS da distancia de varios km, la pieza (b) cae por el dato mismo.
- Comprobar: buscar la fila en `latest_consolidado.csv` y en el OCR snapshot, todas las variantes de
  nombre de Tupungatito, ventana de ±2 h; sensor, satélite, VRP, distancia, clase.
- Protegida = alerta de MIROVA de 1 MW o más (lectura A). ¿1,86 MW es VRP de la tabla o del OCR?
  ¿pasa la regla SN (0,05 MW)? Sí, trivial, pero confirmar que la etiqueta de alerta es ALERTA y no
  RUTINA.

## C4. Nuestro record de esa pasada no es el que se cree
- Puede haber varias pasadas VIIRS 375 cerca de las 04:54 (SNPP, NOAA-20, NOAA-21) y el pareo pudo
  tomar otro satélite u otro gránulo. Puede haber otro record de la misma noche o de la misma pasada
  (I-band y M-band) que sí publica dentro del radio.
- "9,42 km" puede ser `final_hotspot_dist_km` (desde el centro) y no la posición del cúmulo primario,
  o el cúmulo primario puede estar en otra parte (A46: hotspot vs primary_cluster). Si el
  `primary_cluster` está dentro del radio, el record sí se publicaría.
- El record puede haberse reprocesado después (K, #883, cese de Suomi NPP): el dato de hoy puede no
  ser el que vio la otra sesión.
- Comprobar: listar todos los records de Tupungatito.json del 2026-09-29 entre 03:00 y 07:00 UTC con
  sensor, hora, final_hotspot, primary_cluster, distance_class, vrp; cuál es el más cercano en hora
  a 04:54.

## C5. El radio que nos deja fuera no es el que se cree
- Tupungatito tiene inner_radius_km 7 en la tabla de CLAUDE.md, pero `volcanoes.yaml` puede decir
  otra cosa hoy, y el ancla de la distancia puede ser el cráter (get_detection_anchor) o el centro de
  la grilla MIROVA. 9,42 km medido desde un punto y no desde el otro cambia el veredicto.
- El predicado del tablero (`isValidDetection` / `mirovaEqVrp`) puede no usar el radio interno sino
  `distance_class`, o puede ocultar el record por otra condición (vrp=0, sensor, hora diurna, nube).
  Si el motivo es otro, la etiqueta "perdida por radio" cae aunque la pérdida sea real.
- La pérdida puede estar compensada: otra pasada de la misma noche (A94, A118) publica, así que en
  la unidad noche no es pérdida.
- Comprobar: ejecutar el predicado con node (banco_paridad.correr_node) sobre el record real; y
  mutarlo (mover el radio a 10 km o cambiar distance_class a summit) para ver si pasa a publicar:
  así se atribuye la causa al radio.

## C6. "Está en el cráter" en la miniatura, pero a qué escala
- Si la miniatura tiene píxeles de 375 m o más gruesos y está reescalada, "en el cráter" puede tener
  una incertidumbre de varios km. Hay que decir cuál es la incertidumbre de la posición (anchura del
  pico de correlación más tamaño del píxel de la miniatura) antes de comparar con 9,42 km.
- Además, si MIROVA y nosotros vemos el mismo píxel caliente, la distancia de MIROVA (CONS u OCR)
  debería ser compatible; si la tabla dice 9 km, la miniatura no la contradice, la mide mal.

## C7. La copia local está atrasada
- Los CSV y los JSON del worktree pueden estar atrasados respecto a origin/main. Comprobar el commit
  y, si hace falta, leer de origin/main.

## C8. El script de la otra sesión no corre o depende de archivos que no están
- Si no corre, eso es un resultado. Si corre, comparar su salida con la commiteada.

---
sha256 del contenido de arriba (antes de agregar este pie): cb91c69238250c8815c61216ca4297d1a1ea8ebe274f10abdd07b0e48298828f
Hora del servidor (GitHub, header Date: Fri, 23 Oct 2026 18:03:24 GMT)
