# caminos.md: por donde podria estar mal cada afirmacion del coordinador

Escrito ANTES de abrir ningun archivo citado (JSON, ablacion.log, leer.py, piezas.py,
ablacion_cenit_modis.py, README.md). Solo con el enunciado del encargo y la lista de archivos del
artefacto (nombres y tamanos, `ls`). No se vuelve a editar: lo aprendido despues va al INFORME.md.

Objeto: corrida 41588951267, commit f4ec1061d (origin/main hoy = f4ec1061d, verificado con
`git rev-parse origin/main` tras `git fetch`), 27 pasadas MODIS de Nevados de Chillan con alerta de
MIROVA, brazos K, V, V0, X2, FA, NAT, G5, NAT_AREA, FSH, SC, RN.

## Caminos transversales (aplican a todas las afirmaciones)

- T1. El instrumento mide otra cosa: la «razon» del coordinador podria ser por noche y no por pasada
  (misma Fecha_Satelite_UTC al minuto). Comprobar como se pareo cada record con la fila del scraper
  (tolerancia de minutos, duplicados del scraper, pasadas con dos filas).
- T2. La magnitud del brazo comparada podria no ser la que publica el tablero (`pc.vrp_mw` o la
  suma de escena, o el nucleo; A10/D32). Si un brazo devuelve la suma y otro el cumulo, la razon
  cambia sin que cambie la pieza.
- T3. La vara: el VRP de MIROVA del scraper podria venir del canal OCR y no de la tabla (A119;
  `latest.php` mas creible, S159). Si las 27 alertas mezclan canales, la razon mezcla varas. Tambien:
  alertas con VRP <= 0,05 MW (regla SN) deberian estar fuera; comprobar que las 27 son de verdad
  alertas con la lectura A.
- T4. El cenit: podria no ser el del record (sensor zenith en el volcan) sino el del centro del
  granulo, o el del pixel pico, o el solar. Y podria estar guardado en otro campo por brazo.
  Comprobar de donde sale y si es el mismo numero en los 11 brazos (si NAT lo recomputa con otra
  geolocalizacion, el estrato cambia).
- T5. Ceros: una razon 0 puede ser «el brazo no detecto» (fisico), «el brazo fallo» (instrumento
  muerto) o «el brazo no publica» (predicado del tablero). Si los ceros entran en la media y en el
  Spearman como 0, un brazo que falla en las oblicuas reproduce una «caida». SIN DATO no es FALLA.
- T6. La media de razones no es la razon de medias; 0,678 y 0,137 podrian ser medias aritmeticas de
  razones con ceros, medianas, o razon de sumas. Recalcular con las tres y ver si el veredicto
  cambia.
- T7. Spearman con n 27 y 4 a 6 ceros empatados: el barajado del cenit dentro del sensor (200,
  semilla 173) podria no ser un nulo valido si los ceros se concentran en un tramo. Jackknife
  (sacar una pasada) y Spearman sin ceros.
- T8. Ventana temporal: 27 pasadas entre 2026-09-29 y 2026-11-02 (por los nombres de los npz).
  Chillan en erupcion: la magnitud real cambia dia a dia, y si las pasadas oblicuas caen en dias
  distintos que las de nadir, la «caida con el cenit» podria ser caida con la fecha (confusor).
  Comprobar la distribucion de fechas por tramo.
- T9. Noche y dia: MODIS Aqua/Terra a 07:xx-08:xx UTC es noche en Chile, 01:xx-02:xx UTC tambien
  (tarde-noche). Verificar que las 27 sean nocturnas; una diurna cambia umbrales (15 sigma) y fondo.
- T10. El commit: el artefacto podria haberse producido con otro commit que f4ec1061d (el workflow
  hace checkout de main al momento de correr). Leer procedencia.txt y el log.
- T11. La copia local: piezas.py de origin/main podria diferir del que corrio en el runner (si hubo
  push despues). Comparar sha del blob con el que cita el log, si lo cita.
- T12. Los recortes nativos/*.npz: podrian ser recortes ya remuestreados, o ya con un fondo
  calculado; si el npz guarda solo el recorte de 1 km no se puede recalcular el brazo «sin
  remuestreo» desde ahi con fidelidad. Ver que arrays trae cada npz.
- T13. Tolerancia de «igual campo a campo»: `registros_iguales` da falso en las 27 segun el propio
  coordinador y lo atribuye a metadatos. Si da falso en TODAS, el comparador podria estar muerto
  (no distingue igual de distinto): hay que ver que campos difieren en cada una, y si alguno es
  numerico (vrp, n_pix, lat/lon).

## Por afirmacion

### (1) Controles: 27/27 ok; K == record guardado; V0 == V; X2 dobla (1,89 / 2,12), su unica
### publicacion perdida (2026-10-01 08:35, 11,44 MW) es la regla de cirrus del tablero
- C1a. «27 de 27 ok» podria ser un contador que cuenta brazos que corrieron sin excepcion, no que
  dieron el valor esperado (control que no puede fallar, A116).
- C1b. «K igual al record guardado» con `registros_iguales` falso en las 27: ver camino T13. Si
  difiere en vrp_mw o n_pixels en alguna, K no reproduce produccion y todos los brazos cuelgan de
  un K distinto.
- C1c. El record guardado podria ser de otro commit (K de produccion al momento del record, no
  el K de f4ec1061d): `regimen.codigo_sha` distinto no es metadato inocuo si el detector cambio
  entre ambos sha. Comprobar que sha trae el record y si entre ese sha y f4ec1061d hay cambios en
  pipeline/process_modis.py.
- C1d. «V0 igual a V en 27»: ver que es V0 (presumo: via codigo MIROVA con las piezas por defecto)
  y si la comparacion es de magnitud, de mascara o de todo. Un «igual» por tolerancia amplia no
  vale.
- C1e. X2 «dobla» 1,89 / 2,12 y no 2,00: si X2 multiplica la radiancia por 2 la razon deberia ser
  exactamente 2 salvo que el detector cambie la mascara (mas pixeles) o que el fondo se mueva.
  Que no sea 2,00 exacto puede ser señal de que el control toca mas que la magnitud.
- C1f. La «publicacion perdida» atribuida a cirrus: comprobar con el predicado real del tablero
  (frontend/index.html, isValidDetection / mirovaEqVrp) y no con una reconstruccion; A97. Y que
  en 2026-10-01 08:35 el record tenga t_bg < 270 K o lo que pida la regla.

### (2) K cae con el cenit: 0,678 (<30, n 10) / 0,137 (>=30, n 17), Spearman -0,90; V plana
### 0,947 / 1,054
- C2a. T5/T6: cuantos ceros hay en K en cada tramo; si los 4 ceros oblicuos se quitan, cuanto
  queda de la caida.
- C2b. T8: fechas por tramo.
- C2c. «V plana» con n 10 / 17: el intervalo de cada media. Dos medias 0,95 y 1,05 con n chico no
  son «planas» con certeza; medir Spearman de V tambien, y su nulo.
- C2d. T4: el cenit por pasada es el mismo en K y V.
- C2e. «fuera del barajado»: el nulo de 200 barajados da un rango; comprobar donde cae -0,90 y si
  el barajado se hizo dentro del sensor (aqui todo es MODIS; «dentro del sensor» podria ser
  Terra/Aqua por separado o no).

### (3) FA (fondo de K sobre la via) baja los dos tramos (0,488 / 0,351), Spearman -0,38 en el
### borde del nulo, 6 ceros: el fondo baja el nivel, no hace la caida
- C3a. 6 ceros en FA contra 4 en K: FA pierde dos publicaciones mas. Si esos ceros son oblicuos,
  la media del tramo >= 30 baja por los ceros y no por el fondo (T5). Medir sin ceros.
- C3b. Si FA «baja el nivel» en ambos tramos por igual, la razon FA/V deberia ser constante con
  el cenit; si FA/V cae, el fondo si participa en la caida.
- C3c. «Fondo de K sobre la via»: que FA cambie SOLO el fondo (anillo, sin halo, interpolacion)
  y no tambien la media 3x3 o la compuerta que van pegadas al fondo en el codigo (A118).
- C3d. Spearman -0,38 con 6 ceros: jackknife.

### (4) NAT (sin remuestreo, area del nadir) reproduce la caida: 0,960 / 0,460, Spearman -0,93;
### luego la pieza es el remuestreo (D17)
- C4a. NAT podria cambiar mas que el remuestreo: sin grilla fija, el detector corre sobre el
  barrido nativo, donde (i) la geolocalizacion es la de 1 km interpolada de la de 5 km (sesgo
  _interp_geo, 1 a 3 km hacia el nadir, segun memoria S151), (ii) la mascara de inner se calcula
  sobre otra geometria, (iii) la ventana 3x3 cubre otra area fisica en el borde (bow tie, D25),
  (iv) el anillo del fondo cubre otra area. Cualquiera de esas puede hacer la caida sin que el
  remuestreo sea la pieza. Leer piezas.py.
- C4b. NAT y G5 podrian compartir causa: si NAT usa la geolocalizacion de 5 km y G5 tambien, los
  dos miden lo mismo. Comparar NAT y G5 pasada a pasada.
- C4c. «area del nadir» en NAT: si suma pixeles nativos (mas pixeles oblicuos que celdas de 1 km
  no, MENOS: un pixel oblicuo de MODIS cubre hasta 4,8 x 2 km, asi que una fuente de tamano fijo
  cae en menos pixeles) con area del nadir, la energia integrada cae con el cenit por construccion.
  Eso es el remuestreo? O es el conteo de pixeles? Separar: NAT con n_pix, V con n_pix.
- C4d. 'publica' None en NAT: si NAT no pasa por el predicado del tablero, los ceros de NAT no son
  comparables con los de K (que si pasa). Y si NAT sin predicado da magnitud donde K da 0, la
  comparacion de medias esta sesgada.
- C4e. Nulo de NAT bajo 30: 0,960 contra V 0,947: si bajo 30 NAT == V, bien; si NAT difiere de V
  por pasada bajo 30 (aunque la media coincida), el brazo cambia algo mas.
- C4f. Spearman -0,93 con 17 oblicuas y ceros: jackknife (T7).
- C4g. La frase «al reves que en VIIRS 750» hereda un resultado de otro frente que no verifico;
  queda SIN EVIDENCIA desde aqui salvo que lo mida.

### (5) G5 (geolocalizacion de 5 km) reproduce la caida (0,985 / 0,415, Spearman -0,75)
- C5a. Que es exactamente G5: usar la geolocalizacion de 5 km sin interpolar? O la de MxD03? Si
  G5 cambia la posicion de los pixeles 1 a 3 km, la mascara de inner (radio 5 km en Chillan) deja
  fuera pixeles en las oblicuas: la caida seria de la mascara, no de la geolocalizacion per se.
- C5b. C4b: comparar con NAT pasada a pasada.
- C5c. Jackknife.

### (6) NAT_AREA sobrecompensa (1,145 / 1,387): el remuestreo no equivale a multiplicar por el
### area del pixel
- C6a. Si NAT_AREA multiplica por el area real del pixel (sec^3 o la de MxD03), y sube MAS en las
  oblicuas que V, el exceso podria venir del mismo defecto de NAT (C4a) multiplicado por el area.
  Comparar NAT_AREA / NAT con el factor de area esperado por cenit.
- C6b. T6: medias con ceros.

### (7) FSH, SC y RN no mueven nada
- C7a. «No mueven nada» podria ser que el flag no se lee (A89, A116): comprobar que cada brazo
  cambia de verdad algo en el camino (un diagnostico distinto de V en al menos una pasada) o que
  la pieza no tiene sustrato en estas 27 (A116: medir que el instrumento PUEDE dar distinto de
  cero). Un brazo identico a V en las 27 es «inerte» o «no cableado»; hay que distinguirlo.
- C7b. Si son identicos a V campo a campo, pedir al log si hubo excepcion silenciosa capturada
  (cortacircuito que salta sin fallar, S157).

## Lo que mediria por otro camino que el del auditor
- Releer el JSON con script propio: razones por pasada, por brazo, medias aritmeticas, medianas,
  razon de sumas, con y sin ceros, por tramo; Spearman con scipy y nulo propio (semilla distinta
  ademas de la 173) y jackknife.
- Pareo propio contra el scraper: tomar las 27 Fecha_Satelite_UTC y buscar la fila en
  data/mirova_reference/mirova_v1_snapshot/ con la lectura A y la regla SN; ver canal (tabla/OCR).
- Cenit propio: leer del record en data/mirova_equivalent/NevadosDeChillan.json (o el nombre que
  tenga) el sensor zenith y compararlo con el del JSON del artefacto.
- Recalcular desde nativos/*.npz con piezas.py de origin/main al menos V y NAT en 3 pasadas (una
  bajo 30, dos sobre 30) y comprobar que reproduce el JSON; y correr NAT con la geolocalizacion de
  V (o V con la de NAT) si el codigo lo permite, para separar remuestreo de geolocalizacion.
- Control positivo del instrumento propio: X2 debe dar razon ~2x de V; si mi script no ve eso,
  el script esta roto.

---
sha256 (antes de esta cola): e23d158fec56587df2fb5f22ba15f4cd2a15d83595bf00004071a575890ada5f
hora del servidor (gh api, header Date): Date: Tue, 03 Nov 2026 06:29:43 GMT
