# caminos.md: por donde podria estar mal cada afirmacion del auditor de VIIRS 375 (Chillan, cenit)

Escrito ANTES de abrir ningun archivo citado por el auditor. Solo vi: el prompt de la tarea
(sha256 290c01be...), las columnas id, titulo, archivo_linea, confianza, gravedad, eje y
salida_cruda de C:/Users/nmend/vrp-wt/s173_cenit/v375/hallazgos.csv, y COMMIT_MAIN.txt
(5de08ebf62d1ea092c485c0a030f323f2cbdcf2a). No abri INFORME.md del auditor y no lo abrire.

## Afirmacion 1: 27 pasadas pareadas, K 0,75 / 0,56 (Spearman -0,52 fuera del barajado), V375-E 0,92 / 1,00 (+0,28 dentro), V375-E/K 1,21 a 1,76

- A1.1 Pareo que no es por pasada: tolerancia de minutos demasiado ancha (une dos granulos de la
  misma orbita), o pareo por noche disfrazado (misma fecha, distinto minuto).
- A1.2 La hora del scraper (Fecha_Satelite_UTC) no es la del record (acquisition_utc del granulo):
  desfase sistematico de 1 a 6 min que el pareo tolera de un lado y no del otro.
- A1.3 El mismo granulo contado dos veces entre lotes (S159, S162, S162b, FAR): sube n y pesa doble
  una pasada en el Spearman.
- A1.4 Lotes producidos con detectores o codigos distintos (A104): un lote con la via antigua
  (antes de #921 o del re-sellado S172) y otro con la nueva; o K retro vs K de produccion.
- A1.5 El cenit no es el del volcan: el record guarda el cenit del pixel caliente, el del centro de
  escena o el de la grilla; o viene de otro campo (sensor_zenith del hotspot). Si el cenit viene de
  otra fuente (geometria calculada), el auditor pudo calcularlo mal.
- A1.6 Ceros mal tratados: razon = 0 (K no publica) incluida como 0 o excluida; VRP de MIROVA 0
  (division) ; la regla SN (alertas <= 0,05 MW son NONE) no aplicada o aplicada al reves.
- A1.7 El numerador no es el que publica el tablero: pc.vrp_mw contra f5_core_vrp_mw contra vrp_mw
  (A10 y matiz S132); en la via, otro campo.
- A1.8 n chico disfrazado: 27 pasadas partidas en dos tramos; cuantas en cada tramo; cuantas noches
  distintas; un par de pasadas gobierna el Spearman.
- A1.9 Barajado: intervalo [-0,43; 0,33] asimetrico; que percentiles; barajado «dentro del sensor»
  con un solo sensor (VIIRS 375) o por plataforma (SNPP/N20/N21); semilla 173, 200 barajados.
- A1.10 Hitos de A119: la ventana 2026-09-28 a 2026-10-16 es posterior al OCR v30 (2026-08-06), pero
  los TIF/imagenes de MIROVA estan congelados desde el 2026-09-22: el canal OCR puede traer la
  imagen de otra pasada (S150) o nada; la vara seria la tabla sola.
- A1.11 La referencia local (mirova_v1_snapshot) atrasada respecto del remoto: faltan filas o hay
  filas con distinta clase.
- A1.12 Alertas diurnas o pasadas diurnas mezcladas con nocturnas (MIR solo nocturno).
- A1.13 Volcan: variantes del nombre (Nevados de Chillan / NevadosDeChillan / Chillan) perdidas.

## Afirmacion 2: K de produccion completo, 66 pares hasta el 2026-11-02: 0,745 / 0,481, Spearman -0,55

- A2.1 Ventana de inicio no declarada: si empieza antes del 2026-06-13 el OCR no trae distancia;
  si antes de marzo, tabla incompleta (A119).
- A2.2 El corpus de produccion mezcla detectores (A104): todo el historico es K desde #883, pero
  comprobar processed_utc de los records de Chillan.
- A2.3 Duplicados: el mismo minuto en CONS y OCR contado dos veces; dos plataformas en el mismo
  minuto.
- A2.4 Misma lista que A1.5 a A1.9 (cenit, ceros, numerador, n por tramo, barajado).
- A2.5 Copia local de data/mirova_equivalent/ atrasada respecto de origin/main.

## Afirmacion 3: data/sombra_codigo_mirova/ no existe en origin/main (n = 0) aunque el workflow corre con exito desde el 2026-10-31

- A3.1 El workflow escribe en otra rama (sombra/..., loop/activo) y no en main.
- A3.2 El workflow escribe en otra ruta (data/sombra/..., data/mirova_codigo/...).
- A3.3 Solo sube artifacts y no commitea.
- A3.4 «Corre con exito» leido del estado del workflow y no de los jobs (job verde sin datos, S141):
  el paso de commit puede saltarse con «nothing to commit».
- A3.5 La copia local de origin/main esta atrasada (fetch viejo).
- A3.6 La ventana del cron (0 15 UTC) y la primera corrida: si el primer run con datos es del
  2026-11-03, «vacia» es SIN DATO, no FALLA.

## Afirmacion 4: la caja no es la pieza (n 14); el fondo no explica la pendiente; alertados de la via crecen con el cenit (+0,53) y los de K no: firma D17

- A4.1 n = 14 en dos tramos: cuantas por tramo; los seis brazos de V375-C vienen de
  experiments/_s162_v375 producidos con otro codigo que la via de hoy.
- A4.2 «Fondo no explica»: que campo de fondo compara (t_bg del record de K contra el de la via);
  si la via no guarda su fondo, el instrumento mide otra cosa.
- A4.3 Alertados: que campo (n_anomalous_pixels, npix, anomaly_pixels) y si en la via el conteo es
  de celdas de grilla (remuestreo) por construccion: entonces la correlacion con el cenit es
  trivial (pixel oblicuo mas grande cubre mas celdas) y no «firma» de nada mas.
- A4.4 Alternativa a D17: el crecimiento de alertados con el cenit puede ser nube/ruido o el
  bow-tie, no el remuestreo; SOSPECHA del auditor, no se puede confirmar sin ablacion.
- A4.5 Spearman +0,53 sobre n chico y sin barajado.
- A4.6 Los de K «no crecen»: K puede tener Spearman negativo (pixeles mas grandes, menos pixeles),
  que no es «no crecen».

## Afirmacion 5: no existe ablacion por pasada en VIIRS 375

- A5.1 Buscar por el nombre equivocado (A89): la ablacion puede vivir en flags del perfil
  (enable_via_*), en pipeline/mirova_v750_codigo.py con parametros que V375 reutiliza, o en
  experiments/_s16x_v375/.
- A5.2 Los brazos de ROI de V375-C son una ablacion parcial: «no existe ninguna» seria falso si
  existe una (la caja).
- A5.3 El probe C13 puede tener brazos por pieza.

## Afirmacion 6: 13 de 46 pasadas re-corridas difieren del probe C13 en mas de 1e-3 MW

- A6.1 Codigo distinto entre la re-corrida y el probe (A104): commit del probe contra commit de hoy.
- A6.2 Insumos distintos: granulo NRT contra Standard (delta BT < 0,1 K, pero puede mover un
  pixel del umbral), o version de geolocalizacion.
- A6.3 argsort inestable segun CPU (S152): empates que cambian la seleccion del cumulo.
- A6.4 El umbral 1e-3 MW es arbitrario: diferencias de 1e-3 sobre 0,05 MW son 2 %; sobre 5 MW son
  nada. Mirar la diferencia relativa y cuantos pixeles cambian.
- A6.5 El «C13» que leyo el auditor puede ser otra columna o brazo del probe.

## Hallazgos del auditor con camino propio

- CV375-06 (D25 en el catalogo es fondo con recorte, no borde del barrido): la linea 2861 puede ser
  una marca historica y el encabezado vivo decir otra cosa; o el encargo use D25 como etiqueta
  del MISMO fenomeno visto desde otro lado.
- CV375-09 (la via publica dos alertas debiles que K calla, 2026-08-20 05:12 y 2026-09-05 05:48):
  fuera de la ventana 09-28 a 10-16, luego vienen de otro lote; si la alerta es <= 0,05 MW es
  NONE por la regla SN y «publicar» ahi no es acierto; comprobar con el predicado del tablero.
- CV375-02 (ventana de la sombra empieza el 2026-11-03): comprobar con la hora del servidor y el
  cron.
- CV375-04 (fondo cero / factor de area, techos de la tarea 1.33): que son esos techos; si el
  factor de area aplana, la firma seria area y no remuestreo (contradice CV375-03 en parte).

## Controles que me propongo

- Control positivo del pareo: una pasada con razon conocida (a mano) debe salir igual.
- Control del cenit: cenit del record contra cenit calculado desde la geometria del granulo
  (si el campo existe); distribucion del cenit (0 a 70) y conteo por tramo.
- Control del Spearman: con el cenit barajado la mediana del barajado debe ser ~0.
- Control del instrumento muerto: correr el pareo con un volcan sin referencias debe dar n = 0
  declarado, no un numero.

---
sha256 (antes de este pie): 6f76ce54b3b66b1aa604cd7519135d82e05f4798c226f35edf258781c806a76e
hora del servidor: Tue, 03 Nov 2026 00:57:42 GMT
