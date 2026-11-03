# caminos.md: por donde podria estar mal cada afirmacion (escrito ANTES de abrir ningun archivo citado)

Verificador de C:/Users/nmend/vrp-wt/s173_cenit/tupun375/ (VIIRS 375, Tupungatito, caida de la razon con el cenit).
Recibi solo las 5 afirmaciones del encargo, no el razonamiento del auditor. No he abierto INFORME.md ni ningun script suyo todavia.

## Afirmacion 1: K por pasada, 168 pares (2026-02-14 a 2026-11-02), razon 0,43 bajo 30 grados y 0,24 sobre 30, Spearman -0,52 fuera del barajado; se sostiene con la tabla sola, sin referencias sospechosas, desde abril o desde el 13-jun; MIROVA plano (+0,03)

- C1.1 El pareo no es por pasada (A93, A107): si el auditor pareo por noche o por fecha sin el minuto, cada record se cruza con varias filas del scraper y el "par" es un promedio o un maximo. Verificar que la llave sea volcan + sensor/plataforma + minuto UTC.
- C1.2 El mismo granulo contado dos veces: el scraper puede traer la misma pasada en CONS y en OCR (A11), o dos filas por imagen reusada (A106, md5 repetido), o nuestros records pueden traer dos registros por minuto (NRT y Standard, A17). Contar pares unicos por (plataforma, minuto).
- C1.3 La plataforma esta mal pareada: Suomi NPP vs NOAA-20 vs NOAA-21 tienen minutos distintos; un pareo que ignora la plataforma puede cruzar NOAA-20 05:40 con NPP 05:41 por tolerancia de minutos. Verificar como mapea el nombre del satelite del scraper a nuestro campo `sensor`.
- C1.4 El cenit no viene del record: si lo tomo de otra fuente (TLE, estimacion por longitud), la estratificacion en < 30 / >= 30 esta hecha con otra variable. Verificar el campo del record (nombre real: buscar `zenith`, `sensor_zenith`, `sat_zen`, `diag_*`) y que exista en los 168.
- C1.5 La razon usa el campo equivocado de magnitud: para VIIRS 375 el tablero publica `f5_core_vrp_mw` con fallback a `pc.vrp_mw` (A10 matiz S132); `record.vrp_mw` trae el tope D9 y la suma de escena. Y el VRP de MIROVA: con OCR y CONS, cual columna; si CONS trae VRP en MW o en texto con banner.
- C1.6 Ceros mal tratados: razon con VRP de MIROVA 0 (o NONE) da infinito o se descarta; razon con nuestro VRP 0 da 0 y empuja la mediana abajo; si se filtran los ceros de un lado y no del otro, la mediana por tramo queda sesgada. Verificar cuantos ceros hay en cada tramo y que pasa con ellos. Y la regla SN (alertas de VIIRS 375 de 0,05 MW o menos cuentan como "no vio nada") puede quitar pares del tramo bajo.
- C1.7 La ventana contiene dos detectores (A104): 2026-02-14 a 2026-11-02 cruza #535 (2026-08-28, mascara de nube) y K (#850, 2026-10-18; segun S158 R2 todo el corpus fechado es K por reproceso). Si el histórico de Tupungatito no fue reprocesado entero con K, hay records del detector anterior mezclados. Verificar `processed_utc` de los records pareados contra la fecha del merge de K.
- C1.8 La referencia no sirve igual todo el año (A119): OCR mal calibrado hasta 2026-06-11, sin distancia hasta 2026-06-13; Tupungatito no existe antes del 2026-02-14. El "desde abril o desde el 13-jun" dice que lo probo, pero hay que ver si "la tabla sola" quiere decir CONS sin OCR y si el OCR fue excluido tambien del lado del denominador.
- C1.9 El Spearman -0,52 puede ser de n pequeño en un tramo, o estar dominado por una plataforma (NOAA-20 tiene cenit sistematicamente distinto a NPP sobre Chile en una ventana): confusor por plataforma. Control: Spearman dentro de cada plataforma.
- C1.10 El barajado como control: si barajo el cenit entre sensores en vez de dentro del sensor, o con menos de 200 repeticiones, o sin semilla 173; y si el p del barajado se calcula con una cola. Hay que re-correr y ver que el nulo este centrado en 0 (A110, nulo medido).
- C1.11 "MIROVA plano (+0,03)": plano en que? Spearman del VRP de MIROVA contra cenit? Si el VRP de MIROVA en MW no es plano en el log, puede esconder un efecto. Y el denominador: los mismos 168 pares o todas las alertas de MIROVA.
- C1.12 La copia de datos del auditor (`repo/data`) puede estar atrasada respecto a main o loop/activo de hoy: comparar el commit (COMMIT_MAIN.txt dice f20495d374) con origin/main y con los records de data/mirova_equivalent/Tupungatito.json de hoy.
- C1.13 Tramos: < 30 y >= 30 con n por tramo; si un tramo tiene menos de 20 pares la mediana es fragil. Declarar n.
- C1.14 La razon por pasada puede estar calculada como razon de medianas en vez de mediana de razones (A99 rebajada): dan numeros distintos.

## Afirmacion 2: V375-E en 23 pares de los lotes retrospectivos (2026-04-04 a 2026-09-18) da 1,01 / 1,02 sin pendiente; V375-E/K de 2,34 a 3,93

- C2.1 Poblacion distinta: 23 pares contra 168. Los lotes retrospectivos de V375-E cubren fechas elegidas (quiza solo noches con alerta de MIROVA, o solo ciertos granulos); si la seleccion esta correlacionada con el cenit (p. ej. solo pasadas cercanas al nadir) la ausencia de pendiente es un artefacto de rango. Comparar la distribucion de cenit de los 23 contra los 168.
- C2.2 Mismas plataformas? Si los lotes son solo NPP y K tiene NPP + NOAA-20 + NOAA-21, el V375-E/K no compara lo mismo.
- C2.3 Lotes con codigo distinto mezclados (A104): los lotes retrospectivos de V375-E se corrieron en distintas fechas con distintos tags; si uno es anterior al re-sellado del lector (S172, tag s172-v375e-lector-resellado), su VRP sale de otro codigo. Verificar que cada lote tenga el sello/commit y que sean el mismo.
- C2.4 El mismo granulo dos veces entre lotes: si dos lotes se solapan en fechas, el mismo granulo aparece dos veces y pesa doble en la mediana.
- C2.5 1,01 / 1,02 con n de 23 partido en dos tramos: n por tramo puede ser 10 y 13 o 20 y 3. "Sin pendiente" con n chico no es evidencia de ausencia (SIN DATO frente a CONFIRMADA).
- C2.6 "V375-E/K de 2,34 a 3,93": si eso es el cociente de las razones de 2,34 a 3,93 por tramo, deberia coincidir con 1,01/0,43 = 2,35 y 1,02/0,24 = 4,25, no 3,93: hay que ver sobre que pares se calculo (los 23 o los 168). Si es sobre los mismos 23 pares, K en esos 23 puede dar otra razon que en los 168.
- C2.7 El VRP de V375-E viene de que campo: si la via escribe un record distinto (otro directorio de salida) con otro nombre de campo, el instrumento puede estar leyendo el VRP de K en vez del de la via. Control positivo: que los dos VRP difieran en la mayoria de los pares.
- C2.8 Que se compare el mismo minuto: si el lote retrospectivo escribe `observation_utc` con otro redondeo, el pareo por minuto con la referencia falla o cruza otra pasada.
- C2.9 Que la via publique: si V375-E no pasa el predicado del tablero (A97), una razon de 1,01 sobre lo que no se publica no es paridad para el operador.
- C2.10 El pareo de la via contra MIROVA puede ser solo sobre pares donde la via detecta (sesgo de supervivencia): las pasadas donde la via da 0 y MIROVA alerto no entran y la razon sube.

## Afirmacion 3: cambiar solo el fondo de la via por el t_bg de K con recorte a cero reproduce a K (0,415 / 0,246 contra 0,394 / 0,251)

- C3.1 El brazo cambia mas que el fondo: si para usar el t_bg de K hay que tomar tambien su mascara de pixeles alertados, su area o su kernel, el brazo no aisla la pieza (A110, A118). Leer que variables se reemplazan.
- C3.2 "Recorte a cero": si la via sin recorte da negativos (VRP < 0 cuando t_bg de K es mayor que el pixel) y se recortan a cero, el 0,415 puede venir de ceros que K no tiene; comparar el conteo de ceros en cada brazo.
- C3.3 Nulo no medido (A110): el brazo "cambiar el fondo por el de K" tiene que correrse tambien al reves (K con el fondo de la via) o con un fondo placebo (p. ej. t_bg de otra pasada) para ver que el instrumento puede dar distinto de "reproduce a K". Si cualquier fondo reproduce a K, el instrumento no mide el fondo.
- C3.4 Sobre que pares: 0,415 / 0,246 son dos tramos, pero sobre los 23 de la via o sobre los 168 de K? Si es sobre 23, 0,394 / 0,251 de K deberia ser K sobre esos mismos 23, no los 0,43 / 0,24 de los 168. Si no coinciden los conjuntos, la "reproduccion" compara dos poblaciones.
- C3.5 La formula de magnitud de la via y la de K pueden ser distintas en la constante (WOOSTER_COEFF) o el area de pixel (nadir fijo): si solo se cambia t_bg y el area tambien difiere, el resultado no aisla el fondo.
- C3.6 Recomputo offline sobre records persistidos: si el brazo se calcula desde los campos del JSON (t_bg guardado) y no re-corriendo el pipeline sobre L1B, depende de que el record guarde el t_bg exacto que uso (A7, los diagnosticos cambian de nombre) y la radiancia del pixel; si recomputa desde BT con Planck invertido pierde precision.
- C3.7 Tramos de cenit con n chico: 23 pares partidos en dos.

## Afirmacion 4: las 11 alertas que K no publica estan a 48 grados o mas, 9 con cumulo en el crater y 0 MW, ninguna protegida

- C4.1 "No publica" con que predicado: el del tablero (`mirovaEqVrp` / `isValidDetection`, A97) ejecutado, o una reconstruccion. Si el predicado se reconstruyo a mano, puede diferir (p. ej. el gate de inner_radius, el selector noche/rango).
- C4.2 Denominador: 11 de cuantas alertas de MIROVA en la ventana? y bajo que lectura (A con regla SN; alertas de 0,05 MW o menos no cuentan).
- C4.3 "A 48 grados o mas": el cenit del record nuestro de esa pasada; si K no tiene record para esa pasada (no bajo el granulo, A108), el cenit no viene de ningun lado y "48 o mas" es de otra fuente.
- C4.4 "Cumulo en el crater y 0 MW": 0 MW por que: tope D9? piso? cluster sin pixeles alertados? Si `pc.vrp_mw` es 0 pero `f5_core_vrp_mw` no (o al reves), la afirmacion depende del campo.
- C4.5 "Ninguna protegida": protegida = alerta de MIROVA de 1 MW o mas; si el VRP de MIROVA viene del OCR con la imagen de otra pasada (S150), el valor puede ser de otra pasada.
- C4.6 Pareo: las 11 pueden incluir pasadas donde no tenemos record (no son "K no publica" sino "K no proceso").

## Afirmacion 5: las 4 alertas grandes solo de OCR de Suomi NPP antes del 2026-10-09 tienen sus alertados a 9 a 25 km del crater

- C5.1 "Alertados a 9 a 25 km": de que fuente, el record nuestro (pixeles alertados nuestros) o la distancia del OCR de MIROVA? Si es de nuestro record, el "alertado" puede ser `far` de otro objeto (Salar, lago), y no dice donde puso MIROVA su cumulo.
- C5.2 El OCR puede traer la distancia de otra pasada (S150, reference_ocr_imagen_de_otra_pasada) y la geometria del OCR esta mal calibrada hasta el 2026-06-11 (A119).
- C5.3 "Solo de OCR": verificar que no esten en CONS con otro nombre de volcan (A14 variantes de nombre).
- C5.4 "Antes del 2026-10-09": que paso el 09-oct (arreglo de Mirova-v1#20?). Si la fecha es de otro cambio, la frontera es arbitraria.
- C5.5 Diurnas: A76, las alertas grandes de VIIRS 375 solo OCR pueden ser artefactos solares diurnos; verificar hora local.

## Transversales

- T1 Copia local atrasada: el `repo/` del auditor es un snapshot a f20495d374; main hoy puede tener otros records (reprocesos). Comparar contra el checkout de hoy y contra origin.
- T2 Los scripts del auditor pueden no correr fuera de su carpeta (rutas relativas, helpers); si no corren, es resultado.
- T3 Semilla y numero de barajados declarados vs. usados.
- T4 El instrumento muerto: un script que lee un campo ausente y devuelve NaN en todos da "sin pendiente" por construccion. Control positivo obligatorio: la razon de K con el cenit (que si cae) tiene que verse en mi instrumento propio.
- T5 Mi propio pareo: llave (plataforma, minuto) desde data/mirova_reference/mirova_v1_snapshot/ y data/mirova_equivalent/Tupungatito.json, sin sus helpers; comparar n y medianas con las del auditor.

---
sha256 (antes de esta linea): 0da03bdebd76d7a49edd982a18257d1084317b2c622ec0c18c291aefd6e2ce75
hora del servidor (api.github.com): Tue, 03 Nov 2026 02:44:35 GMT
