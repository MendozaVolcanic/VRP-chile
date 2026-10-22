# Caminos por los que cada afirmación podría estar mal (escrito ANTES de abrir 02_analizar.py o sus salidas)

Verificador del censo del oráculo V750 (S159). Sólo leí hasta aquí: CLAUDE.md del proyecto, PREREGISTRO.md del objeto,
el prompt de la tarea, y los listados de carpetas (ls) del objeto y de los artefactos en D:. No abrí 02_analizar.py,
ninguna salida, INFORME.md ni los resultados crudos.

## Afirmación 1: los cuatro controles del pre-registro §5 pasan

Control 1 (K = producción, 5.620 de 5.620):
- C1.1 La vara «producción» puede ser el record de un checkout local atrasado y no `origin/main` 533398f8f (A52, A25).
  Si el artefacto compara contra records que viajaron dentro del job, la vara es la del commit del job, no la de hoy.
- C1.2 El predicado «publica» de K y de producción puede venir del MISMO cálculo (la misma función sobre el mismo record),
  y entonces 5.620 = 5.620 es tautológico: no vería un K roto que se rompe igual en los dos lados. Hay que ver si
  `pub_prod` se evaluó sobre el record publicado en `data/` y `pub_k` sobre el record recién escrito por `store.append_record`.
- C1.3 Tolerancia 0,001 MW en `pc.vrp_mw`: si `pc` es None en los dos lados, la comparación puede dar «igual» por
  `None == None`, sin haber comparado nada. Cuántas de las 5.620 son None-None.
- C1.4 Denominador: 5.746 pasadas en la población, 5.620 ok. La diferencia (126) no es sólo los 20 SIN DATO de la
  afirmación 5: ¿qué son las otras 106? Si son «fuera» (no miran el volcán), el control no las cubre y está bien;
  si son fallas no declaradas, el control está contado sobre un denominador recortado.
- C1.5 El pareo del record de producción a la pasada: a 120 s puede parear otro record del mismo gránulo o del
  gránulo vecino (dos plataformas a 6 min). Un pareo equivocado que da igual en los dos lados tampoco se ve.

Control 2 (oráculo = N, 1.006 de 1.006):
- C2.1 El pre-registro §1 dice que N midió 508 de las 5.746; la afirmación dice 1.006. Puede ser 508 × 2 cajas (O-def y
  O-sens), o un denominador distinto. Si es 508 × 2, decir «1.006 pasadas» confunde cajas con pasadas; si no, hay
  que ver qué conjunto es.
- C2.2 Es el mismo código (`probe_n.py` reusado) corrido sobre los mismos gránulos: la igualdad prueba determinismo
  del port, no corrección. No vería un oráculo roto de la misma forma en N y en el censo. Vale como control de
  regresión, no de verdad.
- C2.3 El run de N que sirve de vara puede ser otro que el citado (`run_39682867040`, `run_39693661527`); las carpetas
  existen en `experiments/_s159/n/`. Comprobar que la comparación lee esos y no el humo.
- C2.4 argsort inestable entre runners (S152, feedback): 1e-6 MW de tolerancia puede esconder o no una diferencia por
  empates; si el run de N y el del censo corrieron en CPUs distintas, la igualdad exacta es informativa.

Control 3 (nulo del instrumento, 1.006 perturbaciones):
- C3.1 El nulo se hace sobre records sintéticos del oráculo: perturbar `pc.vrp_mw = 0` y que deje de publicar prueba
  que el contador lee ese campo; no prueba que el contador NO publique por otra vía (p. ej. `vrp_mw` del record
  distinto de `pc.vrp_mw`). Lo mismo con `distance_class: far`: prueba que lee ese campo.
- C3.2 El (c) del pre-registro (inyectar cúmulo a 50 negativos) exige que el inyectado pase `isThermalArtifact`
  (cirrus: `t_max_k`, `vrp_mir_mw`; difuso: `n_pixels`) y `isValidDetection`. Si los 50 pasan, bien; si alguno no,
  el pre-registro dice que el contador no ve lo que dice ver. Hay que ver si el 1.006 incluye (c) o sólo (a) y (b).
- C3.3 «1.006 perturbaciones» coincide con el número del control 2. Si (a) y (b) se hacen sobre los records del
  oráculo que publican, el número debiera ser 2 × (publicaciones del oráculo), no 1.006. Hay que ver de dónde sale.
- C3.4 El nulo corre con el predicado de node o con una copia en Python: si es una copia, el nulo prueba la copia.

Control 4 (razón mediana 1,000 y 0,999):
- C4.1 Mediana de razones sobre cuántos pares: si el oráculo detecta 145 de 256 la mediana es sobre los detectados y
  calla sobre los 111 no detectados. Una razón de 1,000 con pocos pares no es un control fuerte.
- C4.2 La razón O/MIROVA compara el VRP total de la caja (suma de todos los alertados) con el VRP de MIROVA en el CSV
  del scraper: si el CSV trae el VRP del OCR (dudoso, feedback S159) para parte de los pares, la razón mide también la
  calidad del OCR.
- C4.3 Si la mediana es exactamente 1,000 puede ser señal de que O y MIROVA leen el MISMO número (circular), no de que
  el port reproduzca. Mirar la dispersión (cuartiles), no sólo la mediana.
- C4.4 «Detecta las alertas» con qué predicado: píxeles alertados > 0 o «publica» del tablero. Si es la primera, no es el
  mismo predicado que el resto del censo.

## Afirmación 2: negativos limpios publicados sobre 5.353 ok: K 54, O-def 5, O-sens 15

- N2.1 Denominador: pre-registro dice 5.476 negativos; 5.353 ok. ¿Las 123 que faltan son SIN DATO (20 del 12-oct son
  pasadas de toda clase, 17 negativos) o «fuera»? Si hay «fuera» excluidas del denominador, el pre-registro §4 dice que el
  conteo principal usa las 5.476 y da aparte sin «fuera» ni «sin cráter». Un conteo principal sobre 5.353 invierte eso.
- N2.2 «Negativo limpio» depende de la referencia (consolidado 7ea275df, OCR 4ddd5481). Si el analizador lee un CSV más
  nuevo (el sync horario reemplaza `latest_consolidado.csv`), la clase de algunas pasadas cambia. Verificar qué archivo
  y qué commit lee.
- N2.3 El 54 de K debería coincidir con el conteo de negativos publicados por producción sobre la misma población (frente
  N decía 54 también, pre-registro §6). Recontar desde los crudos sin el analizador (tarea (a)).
- N2.4 El predicado del oráculo lee `distance_class` calculado por `record_oraculo` con el centro del TIF; K lo lee del
  record de producción, que ancla al cráter (`get_detection_anchor`). En PP (1,83 km de desfase, inner 3) y Tupungatito
  (2,85 km, inner 7) el mismo cúmulo puede ser `summit` para uno y `far` para el otro: la comparación 54 vs 5 no es
  del todo entre iguales. El pre-registro lo declara como sensibilidad; ver si se midió.
- N2.5 El record sintético del oráculo no tiene `discarded_reason`, `vrp_vent_mw`, `triggered_test1 = false`:
  `isValidDetection` y `isThermalArtifact` pueden tener ramas que sólo K puede pisar (p. ej. supresión cirrus por
  `t_max_k` bajo, o difuso por `n_pixels`): K puede quedar apagado por una rama que el oráculo nunca pisa (tarea (b)).
  Al revés, el oráculo suma TODOS los alertados de la caja 21 × 21 (hasta 15,75 km del centro) en `pc.vrp_mw` y usa el
  centroide sin pesos: dos píxeles opuestos a 10 km dan centroide en el centro y `summit`; K nunca haría eso.
- N2.6 Pareo a 120 s entre la pasada de la referencia y el record nuestro: si hay dos records (dos plataformas) dentro
  de 120 s, cuál se toma. Si el record de K y la pasada de MIROVA son de gránulos distintos, «sobre el mismo gránulo»
  es falso para esa pasada.
- N2.7 El run tiene 32 chunks; si un chunk se perdió o se duplicó al bajar el artefacto, el total cambia sin error.
  Contar pasadas únicas por (volcán, hora) en los crudos y compararlas con `objetivos.json`.

## Afirmación 3: O-def pierde 6 protegidas (todas Cordón Caulle); O-sens pierde 0 y gana 1; ΔE −90 (−92 a −73)

- P3.1 «Protegida» = lectura A: alerta del scraper de 1 MW o más que decide; antes del 13-jun sólo tabla. Si el
  analizador usa el VRP del OCR antes del 13-jun para decidir que es protegida, el conjunto de 79 cambia.
- P3.2 «Pierde» = K publica y O no. Si K NO publica una protegida (producción ya la pierde), O tampoco la «pierde» por
  definición: las protegidas que producción no publica quedan fuera del conteo de pérdidas del oráculo. Hay que dar
  cuántas protegidas publica K (de 79) y cuántas O, no sólo la diferencia.
- P3.3 Cordón Caulle tiene inner 20 km: el oráculo con caja 21 × 21 (15,75 km de semilado) puede no alcanzar donde
  está el cúmulo publicado por K (lacolito a ~7-10 km, D7). Las 6 pérdidas pueden ser de geometría de la caja, no del
  detector: una caja de 67 × 67 con umbrales de escena las vería. Esto no refuta el conteo pero cambia su lectura.
- P3.4 El rango −92 a −73 sale de 20 SIN DATO (17 negativos todos publicados o ninguno, 3 alertas todas ganadas o
  ninguna). Comprobar la aritmética: −90 − 17 = −107, no −92; o el rango toma los SIN DATO de otro modo. Revisar la
  fórmula del rango contra §4.
- P3.5 ΔE = E_O − E_K con E = bajo 1 MW sin publicar + negativos publicados. Si K publica 54 negativos y O-sens 15, la
  parte de negativos da −39; para llegar a −90, O-sens debe publicar 51 alertas bajo 1 MW más que K. Verificar ese
  desglose: puede estar inflado si O-sens publica bajo 1 MW de alertas donde K publica también (no cuenta) o donde la
  alerta es sólo OCR (no decide).
- P3.6 «Gana 1»: una protegida que K no publica y O-sens sí. Cuál y por qué K no la publica (A46: etiqueta far, tope D9,
  cirrus) para ver si es ganancia real o artefacto del record sintético.

## Afirmación 4: con el rescate del 12-oct no quedan SIN DATO y las etiquetas no cambian (ΔE −62 y −92)

- R4.1 ΔE sin rescate: O-def −62 (afirmación 4) y O-sens −90 (afirmación 3). Con el rescate las cifras dadas son −62 y
  −92: O-def no cambia y O-sens cambia en −2. Ver si ese −2 son dos negativos del 12-oct que K publica y O-sens no.
- R4.2 El rescate procesa OTRO archivo (reprocesado por NASA). K sobre ese archivo puede publicar distinto que
  producción sobre el original: el pre-registro §8 dice que se informa y no cuenta como falla. Pero si K del rescate
  publica distinto que producción, ¿cuál K entra al E_K con rescate? Si entra el K nuevo, E_K cambia y la comparación
  con producción deja de ser «K = producción».
- R4.3 «No quedan SIN DATO»: 20 pasadas en 4 gránulos. Si el run de rescate bajó 4 gránulos y alguno falló, quedarían
  SIN DATO. Comprobar en el log del rescate que los 4 bajaron y que las 20 pasadas están ok.
- R4.4 Las 20 del rescate pueden no ser exactamente las 20 SIN DATO del censo: si los conjuntos difieren, «reemplazando a
  sus SIN DATO» deja huecos o duplica.

## Afirmación 5: los 4 jobs rojos del run 39713438252 son los 20 SIN DATO del 12-oct y no dañan el resto

- J5.1 Un job rojo de GitHub Actions puede haber escrito un `resultados_NN.json` parcial: las pasadas que alcanzó a
  procesar antes de caer quedan ok y las que no, SIN DATO. Hay que ver si los 4 chunks rojos tienen JSON y cuántas
  pasadas traen, y si el analizador distingue «SIN DATO porque el gránulo no bajó» de «SIN DATO porque el job murió».
- J5.2 Un chunk rojo puede haber fallado por otra cosa (timeout, cuota de LAADS, circuit breaker A64) además del 12-oct;
  que las 20 SIN DATO sean todas del 12-oct no excluye que el job haya perdido pasadas de otros días que el analizador
  no cuenta como SIN DATO (p. ej. si las omite del denominador). Contar pasadas esperadas por chunk contra las que
  trae el JSON.
- J5.3 32 chunks en disco; 4 rojos. Cuántos jobs tenía el run (API de GitHub, hasta 20 llamadas): si el run tenía más
  de 32 jobs, falta algún chunk en el artefacto.
- J5.4 Un job rojo puede ser «rojo» por un paso posterior al JSON (subir artefacto, resumen), con los datos
  completos. Entonces la afirmación es cierta en el resultado pero la causa declarada (12-oct) no sería la causa
  del rojo. Mirar el log del job.

## Caminos transversales

- T1 El analizador puede leer `tabla_por_pasada.csv` ya escrita en vez de los crudos, y mi re-corrida reproduciría el
  CSV, no los datos. Ver de qué lee `02_analizar.py` con `--art`.
- T2 Mi re-corrida con `--salida _verif` escribe en la carpeta del objeto: comparar byte a byte las tablas nuevas con
  las del auditor antes de moverlas; una diferencia por orden de filas no es hallazgo, una por conteo sí.
- T3 La población viene de `experiments/_s159/n/poblacion_completa.json` (pre-registro §1): si ese archivo se rehizo
  después del despacho, `objetivos.json` y la población de hoy pueden no coincidir. Comprobar fechas y conteos.
- T4 Las dos preguntas del instrumento para mí mismo: mis recuentos deben tener un control positivo (p. ej. cambiar a
  mano el predicado y ver que el conteo cambia) y declarar denominador y ventana.
- T5 Ventana 2026-04-01 a 2026-10-21 sin el 18 y 19 de octubre: cruza #535 (2026-08-28) y la adopción de K
  (2026-10-18 según CLAUDE.md, A104/A155): «K = producción» requiere que los records de producción de la ventana sean
  todos del detector K (reprocesados) o la comparación mezcla detectores. Revisar la marca de régimen en los datos.
- T6 Los records de `origin/main` 533398f8f: si el job los leyó de un checkout de otra rama, los records de producción
  de la vara no son los de main.

## Qué mediré por camino propio (tarea, al menos una)

- (a) recuento de negativos publicados por K desde los `resultados_*.json` crudos, con mi propio código y el predicado
  de node vía `banco_paridad.correr_node`.
- (b) comparación de ramas del predicado entre record de K y record sintético del oráculo.
- (d) pasadas de la población contra pasadas presentes en los crudos; pareo a 120 s.
- (c) si alcanza: lectura con la tabla sola.

---
sha256 (del contenido anterior a esta línea): 2c1cedfcb60a775b466b3317005781f70f92850ab9e443489883cad2fdec37f6
hora del servidor (GitHub, header Date): Thu, 22 Oct 2026 04:26:28 GMT
