# Caminos por los que cada afirmación podría estar mal (verificador S160 espacial)

Escrito antes de abrir ningún archivo citado. Sólo vi el listado de la carpeta del auditor.

## Afirmación 1: el calor de MIROVA está en el cráter, no en el centro del TIF

- 1a. Centro del TIF mal calculado: centro de píxel vs esquina (off-by-half), transform leído al revés
  (lat/lon intercambiados), o centro tomado del yaml/mirova_center en vez del TIF real.
- 1b. TIF en EPSG:4326 vs UTM (A106): la conversión de píxel a lat/lon usa una resolución o un origen
  equivocados; un TIF UTM interpretado como grados o al revés.
- 1c. MIROVA reutiliza imágenes viejas bajo hora nueva (md5 repetido, A106): el «foco» de muchas pasadas
  es la misma imagen contada varias veces, n inflado y porcentaje sesgado.
- 1d. TIF congelados desde 2026-09-22 (md5 idéntico): mismo problema.
- 1e. «Foco del TIF» = máximo de un ráster: en un TIF sin señal el máximo cae en ruido o en textura del
  flanco; si se toma sólo en pasadas con alerta, vale; si mezcla RUTINA, mide otra cosa.
- 1f. Selección: el foco se busca sólo cerca del vent (ventana restringida) y entonces «60 % a <1 km» es
  circular por construcción.
- 1g. Distancia_km p50 del CSV: no tiene acimut (A93/A107); «4,8 km al NW» no puede salir de Distancia_km,
  sale de otra cosa (diferencia vent-centro). Si el rumbo se dedujo del yaml y no del TIF, es otra vara.
- 1h. Distancia_km está cuantizada a la celda (D15) y medida desde el centro de la imagen o desde otra
  referencia; si se compara con distancia vent-centro sin saber desde dónde mide, la coincidencia es azar.
- 1i. Coordenada de «vent» usada: yaml vent_lat/lon vs GVP vs cráter físico. Isluga «0,8 a 1,0 km al SW
  del yaml»: puede ser el yaml el corrido, o el TIF mal georreferenciado.
- 1j. «Píxel del código de MIROVA en V750» (oráculo r2): es un port nuestro del MATLAB, corre sobre
  nuestro granulo, no es dato de MIROVA. Su posición depende de nuestra geolocalización (posible offset
  _interp_geo MODIS no aplica a VIIRS pero hay que ver), no prueba nada sobre MIROVA.
- 1k. Incoherencia del mapa PCC: los cuadrados rojos a ~10 km al S. Posibles causas: (i) la figura grafica
  otra columna (centro del TIF, o lat/lon intercambiados, o lon/lat sin signo); (ii) el número 0,48 km es
  la mediana y la mayoría está en el cráter pero hay un grupo lejos; (iii) los marcadores se superponen y
  el grupo visible es minoría; (iv) el vent usado por el script no es el vent de la figura; (v) error de
  números: la distancia calculada contra el punto equivocado (p. ej. contra sí mismo o contra la caja).
- 1l. Ventana temporal: TIF UTM sólo 2026-09-14/15; resto 4326. Mezclar las dos puede introducir offset.
- 1m. Denominadores n = 154/197 (filas CSV) vs n = 62/78 (TIF) vs n = 7/64 (oráculo): poblaciones distintas;
  la afirmación junta números que no describen el mismo conjunto.

## Afirmación 2: nuestro cúmulo a 0,19-0,48 km del foco de MIROVA; 0 de 876 perdidas por geometría; 58 no publicadas de 1 píxel con 0,0 MW

- 2a. Maldición del ganador (A109): comparar con el TIF del mismo gránulo infla la coincidencia; falta
  control con otra pasada de la misma noche.
- 2b. «0 de 876 se pierden por etiqueta/radio/cúmulo»: el instrumento podría no poder dar distinto de cero
  (A116) si clasifica la pérdida con una condición que nunca se cumple; o si la cuenta usa un predicado
  reconstruido y no el de node (A97).
- 2c. Pareo a 120 s: si la tolerancia es otra en el código (por ejemplo 120 min o 1200 s), 876 cambia;
  pareos múltiples (una alerta con dos pasadas) inflan.
- 2d. 876 alertas: ¿incluye OCR? ¿incluye D-9 SN (<=0,05 MW VIIRS 375)? ¿antes de 2026-06-13 OCR decide?
- 2e. «58 no publicadas con energía en el lugar correcto»: la definición de «lugar correcto» puede ser
  circular; 0,0 MW puede ser NaN convertido a 0 o el piso; «1 píxel» puede venir de n_pixels de otro cúmulo.
- 2f. Copias de data del auditor (origin/main db0dfe847) vs datos de hoy: atrasadas.

## Afirmación 3 (E-01): caja por defecto 7x7 marca 0 de 10 / 0 de 48; anillo sensible 7 y 41

- 3a. El port del código de MIROVA (oráculo) puede no ser fiel (A port sin verificar, S159); el «0» puede
  venir de un bug del port y no de MIROVA.
- 3b. La caja 7x7 centrada en el TIF: ¿el oráculo sabe dónde está el centro del TIF de MIROVA o usa nuestro
  mirova_center del yaml? Si es el yaml, mide otra cosa.
- 3c. Denominadores 10/48 y 8 protegidas: ¿por qué tan pocos frente a 154/197? Ventana o sensor (sólo V750).
- 3d. Un 0 que no distingue «no hay» de «no corrió» (filas sin cálculo contadas como 0).
- 3e. Contradicción interna: MIROVA SÍ alertó esas pasadas; si su propia caja por defecto no las marca,
  o el port está mal, o MIROVA no usa esa caja. Conclusión «MIROVA usa el anillo sensible» no se sigue.

## Afirmación 4 (E-02): negativos limpios PCC con cúmulo >2 km, fuera del anillo; contrafactual pierde 3 de 266

- 4a. Definición de negativo limpio mal aplicada (filas RUTINA de otro sensor, o pareo laxo).
- 4b. «Publicamos» reconstruido a mano vs predicado node.
- 4c. «Anillo de MIROVA» medido desde el centro del TIF: ¿qué centro? ¿radio? Si se usa el yaml, otra vara.
- 4d. 3 de 266 perdidas: el denominador 266 ¿son alertas V375 PCC? ¿incluye OCR? ¿D-9 SN?
- 4e. Pareo de MODIS con «MODIS» de la tabla vs «VIIRS» (=V750) mal mapeado.

## Afirmación 5 (E-04, E-08): fuente persistente 10,7 km E de PCC (15 de 161 TIF RUTINA, 10 sigma); focos débiles al N de Isluga y Tupungatito

- 5a. TIF repetidos (md5) cuentan la misma imagen varias veces: 15 de 161 podría ser 2 imágenes únicas.
- 5b. 10 sigma de un máximo sobre una escena: estadístico de máximo, sigma del fondo subestimado.
- 5c. Borde del TIF / artefacto de reproyección / píxel muerto fijo en la misma celda en todas las imágenes.
- 5d. Rasgo real no volcánico (geotermal, fuego, salar). No decide la afirmación pero sí la lectura.

## Afirmación 6 (E-06): dos protegidas de Tupungatito no publicadas son sólo OCR SNPP con geometría de otra pasada

- 6a. «Sólo OCR» verificado contra el consolidado local (copia atrasada) y no contra la tabla.
- 6b. «Geometría de otra pasada»: inferido por cabecera Last Update o por coincidencia de distancia; puede
  ser coincidencia.
- 6c. Las protegidas pueden no estar en nuestros records por falta de gránulo (no por publicación).

## Caminos transversales

- T1. Las copias de JSON en data\ del auditor vs origin/main de hoy (atrasadas).
- T2. comun.py: haversine/rumbo con lat/lon invertidos o signo de rumbo invertido (NW vs NE).
- T3. Volcanes con nombres variantes en el CSV (A14).
- T4. Hora UTC vs hora local en TIF (A106: hora del nombre no es la de la pasada).

---
sha256 (del contenido anterior a esta línea): 2f6ea22f0a049f37f778b105b42101138f2e0dd9643b44929a891ffd904b1a5e
Hora del servidor (GitHub, header Date: Thu, 22 Oct 2026 16:57:37 GMT)
