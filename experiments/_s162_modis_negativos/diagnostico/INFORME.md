# Diagnóstico físico de las dos publicaciones del port en neg_resto (MOD-C)

2026-10-24, sólo lectura. Pedido de la coordinadora: si las dos publicaciones que dejan INDECIDIBLE el lote de MOD-C son
calor real o artefacto. Script y salida: `diagnostico_dos_publicaciones.py` → `diagnostico_dos_publicaciones_salida.txt`.
**Sin verificador propio**: es un diagnóstico que informa a MOD-D, no un veredicto; las clasificaciones van como
SOSPECHA fuerte hasta que el censo de MOD-D las vea con su verificador.

## Láscar 2026-05-11 07:55 (Aqua, cenit 38°): calor real del cráter (SOSPECHA fuerte)

- **Otros sensores, la misma noche** (independientes del gránulo, A109): nuestro K publica el cráter en VIIRS 375 y
  750 de los tres satélites entre 05:00 y 05:54 UTC, a 0,03 a 0,31 km del cráter, con 0,13 a 1,14 MW.
- **MIROVA esa noche**: alertó en VIIRS 375 y 750 (05:54 UTC, tabla, 1,24 y 1,73 MW); su MODIS de las 07:55 dice RUTINA.
  En las noches vecinas MIROVA alertó casi todas, también en MODIS (05-10 01:25 1,07 MW; 05-13 01:45 0,84 MW y 07:35
  0,76 MW; 05-15 01:25 0,86 MW).
- **El píxel**: aislado, a 0,20 km del cráter, con 4,7 K de MIR sobre TIR, contra 1,8 K del percentil 99 del anillo de
  5 a 25 km y 1,2 K como máximo en sus 8 vecinos; sin nube (ninguna TIR bajo 240 K en el anillo); detector 8, no está en
  la costura.
- **Lectura**: foco puntual en el cráter de un volcán que esa noche estaba activo según tres sensores y según MIROVA en
  VIIRS. Para la réplica cuenta como costo (MIROVA calló en MODIS esa pasada); físicamente es señal.

## Llaima 2026-07-24 01:05 (Terra, cenit 63°): artefacto del gradiente en una pasada muy oblicua (SOSPECHA fuerte)

- **Otros sensores, la misma noche**: ninguna de las otras 10 pasadas (VIIRS 375 y 750 de los tres satélites, una a
  3,7° de cenit, y el otro MODIS) tiene cúmulo; MIROVA dice RUTINA en todas.
- **Noches vecinas**: del 19 al 29 de julio, ni nuestro K ni MIROVA ven nada en ningún sensor.
- **El píxel**: a 2,08 km del cráter, 2,95 K de MIR sobre TIR, con vecinos de hasta 2,5 K y, en el mismo 5 × 5, excesos
  negativos de hasta −3 K; la TIR cambia 14,1 K en ese 5 × 5. Es un campo con gradiente fuerte, no un foco. Mecanismo
  compatible: el gradiente de temperatura del terreno visto a 63°, donde un desfase leve entre las bandas MIR y TIR
  fabrica excesos de los dos signos (SOSPECHA, no medido). Detector 7, no está en la costura.
- **Lectura**: costo real del port; el tipo de falso positivo que la marca de pasada oblicua (MEJ-9 del frente M) o el
  propio código de MIROVA con su eliminación de duplicados y su grilla podrían callar.

## Para MOD-D

De las 2 publicaciones que deciden, 1 es probablemente señal (Láscar) y 1 probablemente artefacto oblicuo (Llaima). El
censo cuenta las dos como costo para la réplica (así está sellado); conviene informar al lado cuántas de las
publicaciones en negativos tienen soporte en otro sensor la misma noche, con la vara VIIRS de MOD-B.
