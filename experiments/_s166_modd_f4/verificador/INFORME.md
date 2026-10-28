# Verificador con contexto limpio: pre-registro S166 MOD-D fase 4 (vía «código MIROVA» de MODIS contra K, tres brazos de posición)

- Hora del servidor (GitHub, header Date) al empezar: Wed, 28 Oct 2026 04:57:01 GMT.
- Commit medido: `e1f6b197b5967c0fde1c8dbfed0f4ab0e023b51f` (rama local `claude/focused-pascal-db1501`). `git diff e1f6b197b -- experiments/_s166_modd_f4/` vacío salvo mi carpeta `verificador/` (no versionada). sha256 de los cuatro archivos del §13 verificados iguales a los del documento (`ec6d062b…`, `3e483dd7…`, `4d883aec…`, `ef346a6a…`).
- `CAMINOS_previos.md` escrito ANTES de abrir el pre-registro. sha256: `678780404c96dbf0de45b605b07033d1994a2095dd0b5a52998bb5b2121bbb1e`.
- Modelo y esfuerzo: Claude Sonnet 5.5 (`claude-sonnet-5-5`), esfuerzo no especificado por el encargo (subagente verificador, una sola sesión).
- Qué NO miré: (1) no existen aún el arnés `probe_f4.py`, `identidad_f4.py`, `poblacion_f4.json`, el workflow ni el humo (el pre-registro §11 los declara pendientes), así que todo lo que dependa de ellos es SIN DATO; (2) no re-corrí las 46 mutaciones del autor (leí su salida y su medidor; corrí 17 mutaciones propias); (3) no descargué ningún gránulo HDF; (4) no leí el `.m` de MIROVA ni el PDF de Coppola; (5) no verifiqué contra LAADS que los gránulos listados por CMR del 17 al 20 de octubre se descarguen; (6) no leí el código de `fetch.py` ni `run_pipeline.py`.

## En una pantalla

1. **Veredicto: se puede sellar CON CAMBIOS CHICOS, no tal cual.** Nada que dé vuelta el veredicto del A/B con datos reales plausibles; sí cuatro huecos de instrumento que dejan pasar un PROPONER ADOPCIÓN o un OK de control por la razón equivocada (VF4-01 a VF4-04, gravedad 3) y una desviación no declarada de A119 (VF4-05).
2. Lo importante: la regla de posición elige por P2' y no mira protegidas (reproducido: elige V-pico que pierde una protegida que V publica, VF4-01); el control de identidad toma su lista de pasadas del propio archivo de identidad (VF4-02); dos controles pasan en silencio si falta una clave (`sin_pasada_nuestra`, `k_difiere_de_guardado`, VF4-03); y mis mutaciones propias dejan VIVAS 12 de 15 reglas del documento que el medidor del autor no muta, incluida «una falla del arnés deja la cobertura en rojo» (VF4-04).
3. Limpio: batería 40 de 40 y 40 de 40 por aserción contra el vacío (corridas mías); reglas P1, P1b, P2, M y Chillán conservadas respecto del sello salvo los cambios que el documento declara; el tablero lee exactamente los tres campos que las variantes cambian; cifras del censo, de S165, de la referencia y de CMR se reproducen (salvo tres sueltas, VF4-11); las 46 mutaciones del autor traen aserción real (46 de 46); las grillas float32 del censo no cambian ninguna máscara (0 de 5.321 con ruido hasta ±1e-5).
4. Sin protocolo escrito: qué pasa si la identidad o la cobertura de E salen rojas (VF4-06) y qué significa «CMR sirve» (VF4-07). Ambas se arreglan escribiendo una línea en el documento antes del sello.
5. Informe: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\focused-pascal-db1501\experiments\_s166_modd_f4\verificador\INFORME.md`

## Hallazgos (ordenados por gravedad)

### VF4-01. La regla de posición ignora las protegidas: puede elegir un brazo que pierde una que V publica, y no da crédito al que recupera una
- ARCHIVO:LÍNEA: `experiments/_s166_modd_f4/evaluar_f4.py` `regla_posicion` (elegibilidad = sólo `p1` contra K; ganar = sólo `p2l_vs_V` GANA), `PREREGISTRO_MODD_F4.md` §6 bis.
- QUÉ PASA: «Elegible» mira P1 contra K, y «gana» mira P2' contra V, que sólo cuenta bajo 1 MW, negativos limpios y `far_ref`. Una protegida que K no publica y V sí no está protegida frente a un brazo de posición (cae en `mirova_sin_ninguno`, que es sólo una lista). Y un brazo que rescata una protegida que V deja lejos no recibe ningún crédito (sólo aparece en `descriptivas_posicion`).
- CÓMO SE VE: el evaluador dice PROPONER ADOPCIÓN con `V-pico` elegido en un mundo donde V-pico pierde una protegida de Chillán (58°) que V publica: P1 de V-pico «SIN PERDIDA», veredicto PROPONER. El criterio de victoria de `docs/MISSION.md` dice que arriba de 1 MW perder una alerta no tiene compensación; la regla de posición la compensa con seis publicaciones de menos bajo 1 MW.
- CÓMO REPRODUCIRLO: `cd experiments/_s166_modd_f4/verificador && python escenarios_mios.py S1,S2` (escenario S1: `{"veredicto": "PROPONER ADOPCIÓN", "posicion": "V-pico", ... "P1": {"V-pico": "SIN PERDIDA"}}`, `mirova_sin_ninguno: [('NevadosDeChillan', ...)]`). S2: el brazo que recupera una protegida queda en `descriptivas_posicion` y V sigue elegido.
- CONFIANZA: CONFIRMADO (corrí el evaluador del commit).
- GRAVEDAD: 3. En MODIS el censo dice que sólo 1 de 5.321 pasadas cambia con «cercano», así que el riesgo real es bajo; pero el documento fija la regla para los tres sensores y la copia de los otros A/B. Arreglo mínimo: que un brazo de posición no sea elegible si pierde una protegida que V publica (P1 contra V además de contra K), o que ese caso lleve el veredicto a DECIDE NICOLÁS.

### VF4-02. El control de identidad (§8.2) es circular en el conjunto de pasadas: `con_grilla` sale del mismo archivo que las identidades
- ARCHIVO:LÍNEA: `evaluar_f4.py` `control_identidad` y `main` (`con_grilla = [tuple(k) for k in idn["con_grilla"]]`, `ident` del mismo `identidad.json`); el documento dice «en cada pasada de C evaluable con grilla guardada por el censo (5.321)».
- QUÉ PASA: `faltan` se calcula contra la lista que declara el propio script de identidad. Si `identidad_f4.py` omite pasadas (npz no leído, filtro, falla silenciosa), `con_grilla` se encoge con ellas y el control da OK. No se coteja con la población ni con el 5.321 del documento.
- CÓMO SE VE: control de identidad OK, y por tanto veredicto sin INDECIDIBLE, habiendo medido la identidad en 1 pasada de 70 (o 40 de 5.321).
- CÓMO REPRODUCIRLO: `python escenarios_mios.py S4` imprime `S4 identidad con 1 de 70 pasadas: OK | veredicto PROPONER ADOPCIÓN`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3. Arreglo: `evaluar` recibe el conjunto esperado (C evaluables con grilla del censo, derivado de la población) y exige igualdad, o al menos `n_con_grilla == 5.321` declarado en el pre-registro.

### VF4-03. Dos controles pasan en silencio si falta una clave de entrada
- ARCHIVO:LÍNEA: `evaluar_f4.py` `main`: `pob.get("sin_pasada_nuestra", ())`; `control_k_produccion`: `f.get("k_difiere_de_guardado")`.
- QUÉ PASA: el control «toda pasada MODIS de la referencia sin pasada nuestra deja rojo» (§8.6) y el «K = producción» (§8.1) dan OK si la población no trae `sin_pasada_nuestra` o el arnés no escribe `k_difiere_de_guardado`. Las dos claves están en el contrato del §11 pero ninguna prueba exige su presencia; hoy no existe ningún script que genere `sin_pasada_nuestra` (`git grep` en el repo sólo lo encuentra en `evaluar_f4.py`).
- CÓMO SE VE: cobertura OK y K = producción OK por ausencia de dato, no por haberlo medido (la misma familia que el 0 del `grep`, A89, y los jobs verdes sin datos de A108).
- CÓMO REPRODUCIRLO: `python escenarios_mios.py S3` corre `evaluar_f4.py` de punta a punta con una población SIN la clave: `control cobertura OK`, `exit 0`. `python escenarios_mios.py S5`: `K_produccion OK` sin el campo.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3. Arreglo: KeyError o INDECIDIBLE si falta la clave, más un escenario de la batería.

### VF4-04. La batería no atrapa 12 de 15 reglas del documento que el medidor del autor no muta
- ARCHIVO:LÍNEA: `experiments/_s166_modd_f4/mutar_evaluar_f4.py` (46 mutaciones), `PREREGISTRO_MODD_F4.md` §13 («una regla del documento por mutación»); mis mutaciones: `verificador/mutar_mio.py`, salida `verificador/mutar_mio_salida.txt`.
- QUÉ PASA: copié `evaluar_f4.py`, mutué una regla que el documento fija y que el medidor no toca, y corrí la batería entera con `F4_RAIZ=<raíz> python probar_evaluar_f4.py --modulo <copia>`. De 15 mutaciones válidas (ver tabla en «Mutaciones propias») sólo 3 son atrapadas por aserción; 12 quedan VIVAS, entre ellas: los 50 negativos inyectados del §8.5 (50 a 40), la banda [0,8; 1,25] y el p ≤ 0,05 de Chillán (§9.1), el «neto 0 o a favor» de la regla de posición (§6 bis), el borde K = 1,0 MW de P1b (§6), que una falla del arnés (`estado` distinto de «ok») o un `motivo` desconocido deje la cobertura en rojo (§8.6: «una falla del arnés deja el control en rojo»), «sin sobrantes» (§8.6), la comprobación de clase y de VRP de §8.9 y que Chillán se evalúe con el brazo elegido y no con V.
- CÓMO SE VE: el documento y el §13 dan a entender que la batería vigila cada regla; vigila 46 y deja sin vigilar las que tocan el camino de falla del arnés (justo el que protege contra «un job verde sin datos»). Un cambio futuro del evaluador en esas líneas pasa en verde.
- CÓMO REPRODUCIRLO: `cd experiments/_s166_modd_f4/verificador && python mutar_mio.py > mutar_mio_salida.txt` (unos 15 min con otras sesiones corriendo); o una sola: copiar `evaluar_f4.py`, cambiar `if f.get("estado") != "ok":` por `if False:`, correr `F4_RAIZ=<raíz del repo> python probar_evaluar_f4.py --modulo <copia>` y ver `40 OK`.
- CONFIANZA: CONFIRMADO (cada mutación corrida; las 12 vivas dieron código de salida 0 con 40 de 40 OK).
- GRAVEDAD: 3. Arreglo: un escenario por cada línea viva (estado de arnés distinto de «ok», `motivo` desconocido, pasada sobrante, 49 vs 50 inyectados, K = 1,0 exacto, banda de Chillán en 0,79 y 1,26, p = 0,0625 con 6 de 7 pares, Chillán con brazo elegido distinto de V).

### VF4-05. Desviación no declarada de A119 (a): el sello decía «tabla sola decide» y aquí decide la unión con OCR salvo en P1
- ARCHIVO:LÍNEA: `PREREGISTRO_MODD_F4.md` §4 («A119: MODIS desde marzo, sin reparos de cobertura de la tabla»), §5 «Canal», tabla «Qué cambia» (no lo lista); sello `s162-modd-tag:.../PREREGISTRO.md` §2 («Ventana T (tabla sola decide, A119)»); `CLAUDE.md` A119 (a): en toda ventana que empiece antes del 2026-06-13 la etiqueta positiva que DECIDE es la de la tabla sola.
- QUÉ PASA: sólo P1 trata distinto las alertas «sólo OCR» (las manda a DECIDE NICOLÁS). P1b, P2 (bajo 1 MW sin publicar), M, Chillán y las curvas cuentan alertas sólo OCR como alertas que deciden; `neto_sin_solo_ocr` es informativo. El sello ya las contaba así en el código (el aviso de A119 se imprime, no se aplica), pero su texto decía lo contrario y la «Qué cambia» de F4 no lo menciona. El 2026-10-14 CLAUDE.md anota que hay 5 alertas MODIS sólo OCR, todas de Láscar (4 nocturnas).
- CÓMO SE VE: una alerta bajo 1 MW de Láscar que sólo existe en el OCR sin publicar sube S_V en P2 y puede mover un bloque.
- CÓMO REPRODUCIRLO: leer `evaluar_f4.py` `contribuciones`, `pares_m`, `chillan`: no filtran `solo_ocr`. `grep -n solo_ocr evaluar_f4.py`.
- CONFIANZA: CONFIRMADO en el código y en los textos; el efecto real es SIN DATO hasta tener `poblacion_f4.json`.
- GRAVEDAD: 2. Arreglo: o declarar el cambio en la tabla (y que decida Nicolás en §12) o hacer que decida la tabla sola con el OCR informado aparte, como A119.

### VF4-06. El camino de fallo del §7 fila 1 y los rojos en el tramo E no tienen protocolo escrito
- ARCHIVO:LÍNEA: `PREREGISTRO_MODD_F4.md` §7 fila 1 («si es la identidad: se arregla la vía y se repite la identidad; no se lee el resto»), §8.6 y §4 (tramo E).
- QUÉ PASA: (a) arreglar «la vía» es editar `pipeline/` (A45: tag, confirmación de Nicolás); además V del runner se calculó con la vía vieja, y el documento no dice si el brazo V se vuelve a correr entero. (b) El tramo E es nuevo (10 días sin censo) y su cobertura entra al mismo control global: un rojo allí (una pasada de MIROVA sin pasada nuestra, una 404, un día sin gránulos) vuelve INDECIDIBLE todo el veredicto de C ∪ E tras ~14 h de runner, sin regla previa de qué hacer (excluir E y leer C es una decisión posterior a ver los datos).
- CÓMO SE VE: se decide después de mirar (camino C1 de mi lista), o se pierde la corrida.
- CONFIANZA: CONFIRMADO en el texto; la probabilidad del rojo en E es SOSPECHA.
- GRAVEDAD: 2. Arreglo: escribir ahora «rojo sólo en E → se excluye E entero en todos los brazos y se informa C solo» (o lo contrario), y «identidad roja → NO se toca pipeline/ sin A45; la parte se repite completa».

### VF4-07. «CMR sirve» se mide por listado, no por descarga, y la regla de armado de E no lo precisa
- ARCHIVO:LÍNEA: `PREREGISTRO_MODD_F4.md` §4 («Entran si al armar la población CMR sirve...»), `cmr_cola.py` (cuenta entradas con `page_size=200`).
- QUÉ PASA: `cmr_cola.py` cuenta gránulos listados. El commit `798400dec` («S159: rescate de gránulos; el 12-oct fue reprocesado y CMR entrega entradas viejas (404)...») y D-29 documentan que CMR puede listar entradas que dan 404 al bajar. Re-corrí el script a las 05:01 UTC: coincide con el del autor salvo `MOD021KM 6.1NRT` del 2026-10-21 (3 a 0 en una hora; esa fila no entra en la afirmación), o sea que el servicio cambia entre consultas.
- CÓMO SE VE: un día «que sirve» en el listado que falla en el runner convierte una pasada en `falla_arnes_*` y deja la cobertura en rojo (VF4-06b).
- CÓMO REPRODUCIRLO: `python experiments/_s166_modd_f4/cmr_cola.py` y `diff` con `cmr_cola_salida.txt` (copia mía: `verificador/cmr_cola_mia.txt`).
- CONFIANZA: CONFIRMADO para la volatilidad; el 404 en estos días es SOSPECHA (no bajé nada).
- GRAVEDAD: 2. Arreglo: definir «sirve» como «el HEAD de la URL de descarga responde 200 para L1B y MxD03 de cada pasada», y hacerlo antes del sello de la lista de días.

### VF4-08. El medidor de mutaciones cuenta como «atrapada» cualquier salida con código 1, incluida una mutación que rompe la sintaxis
- ARCHIVO:LÍNEA: `mutar_evaluar_f4.py` `correr` (`clase = {0: "VIVA", 1: "ATRAPADA", 2: "CAE"}.get(p.returncode, ...)`); `probar_evaluar_f4.py` `main` (`EV = cargar(a.modulo)` fuera del `try`).
- QUÉ PASA: un `SyntaxError` al importar la copia mutada termina el proceso con código 1, que el medidor lee como ATRAPADA aunque ninguna aserción fallara. Es el camino C5 de mi lista (mutación «atrapada» que sólo hizo caer el programa); la propia lección S152/S156 que el docstring cita.
- CÓMO SE VE: hoy no infla nada: leí las 46 filas de `mutar_evaluar_f4_salida.txt` y las 46 traen al menos un escenario con «FALLA ASERCION» (46 de 46). Pero el control de caída del medidor (una excepción dentro de `evaluar`) no cubre este camino, así que una mutación futura mal escrita contaría como atrapada. Me pasó a mí: dos de mis mutaciones salieron ATRAPADA con `aserción: -` hasta que vi el `IndentationError`.
- CÓMO REPRODUCIRLO: `cd experiments/_s166_modd_f4 && python -I -c "import sys,tempfile; sys.path.insert(0,'.'); import mutar_evaluar_f4 as M; t=tempfile.mkdtemp(); print(M.correr('M99','PLACEBO = 1.2','PLACEBO = = 1.2',t))"` devuelve `ATRAPADA` con un `SyntaxError` en el texto.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 2. Arreglo: ATRAPADA sólo si la lista de escenarios con «FALLA ASERCION» no está vacía; si el código es 1 y está vacía, «ROTA».

### VF4-09. `main()` y `cargar()` no tienen ninguna prueba; el `Uso` del docstring está desactualizado
- ARCHIVO:LÍNEA: `evaluar_f4.py` docstring («Uso: ... --art DIR --identidad ... --externos ...», sin `--poblacion`, que `main` exige); `probar_evaluar_f4.py` no importa `main` ni `cargar`.
- QUÉ PASA: la E/S (fusión población-filas, lectura de `f4_parte*.jsonl`, escritura del JSON) está fuera de la batería y de las mutaciones. La corrí de punta a punta con filas sintéticas (`escenarios_mios.py S3`) y funciona (`exit 0`, JSON escrito), pero eso es mi prueba, no la suya.
- CONFIANZA: CONFIRMADO. GRAVEDAD: 2.

### VF4-10. Las adendas informativas del sello (soporte independiente, costura, borde del gránulo, S-1) se descartan, y dos «no cambian con la vía» no valen para E
- ARCHIVO:LÍNEA: §6, tabla «Qué cambia», última fila.
- QUÉ PASA: el sello decía que la adenda 1 «entra al evaluador del candado». Aquí no se calcula, con el argumento de que ya se informó en el censo. Pero en el tramo E hay pasadas nuevas, y una publicación de V en un negativo limpio cuenta como costo en P2 sin que se pueda ver si tiene soporte independiente (la clase de Láscar 2026-05-11, señal real que MIROVA calla).
- CONFIANZA: CONFIRMADO en el texto. GRAVEDAD: 1 a 2 (informativo, pero es el único freno a leer una señal real como error).

### VF4-11. Tres cifras sueltas del documento no calzan con su fuente
- (a) §4: «el consolidado ganó 2.648 filas el 2026-10-27, 18 protegidas recuperadas en 60 días». `tasks/LOOP_OBJETIVOS.md` (rama `loop/activo`, entrada 2026-10-27 12:46 UTC) dice: «Total: 2.648 filas y 23 protegidas». El 18 (y las 1.948 filas) es el conteo anterior a las dos mezclas posteriores. CONFIRMADO.
- (b) §4: CMR sirve «3 a 7 gránulos» por día y plataforma. `cmr_cola_salida.txt` da 2 en `MYD021KM 6.1` del 2026-10-26 (y 3 a 7 el resto). CONFIRMADO.
- (c) §10: «curva de V/MIROVA de 0,93 a 1,10 por tramo, contra 0,63 a 0,21 de K». Censo (`resultado_censo.json`, `curva_cenit_K`): K da 0,63, **0,70**, 0,45, 0,31, 0,22, 0,21; el rango de K es 0,21 a 0,70 y no monótono (V: 0,93; 0,97; 1,04; 1,10; 1,06; 1,09). CONFIRMADO.
- GRAVEDAD: 1 cada una. No cambian ninguna decisión; (a) y (c) son las que se citan después.

### VF4-12. El tie-break «a igual valor, V-pico» se apoya en una frase de S165 que su propio informe no sostiene para el centroide
- ARCHIVO:LÍNEA: §6 bis; `programa-replica-por-sensor.md` §7 («La distancia de MIROVA calza mejor con el píxel pico que con el centroide»); `experiments/_s165_regla_posicion/INFORME.md` §2 (en la configuración (a), «la distancia de MIROVA sigue al cúmulo radiante, no al píxel del borde: 38 de 38»; pico sólo se informa).
- QUÉ PASA: es una preferencia a priori, no un resultado; irrelevante para MODIS (1 de 5.321 cambia) pero queda escrita como regla.
- CONFIANZA: SOSPECHA (leí el informe, no lo re-medí). GRAVEDAD: 1.

## Mutaciones propias

Misma clasificación del autor: sólo cuenta ATRAPADA si algún escenario falla por ASERCIÓN (con la salvedad de VF4-08: verifiqué que cada una traiga la lista de escenarios fallidos). Cada mutación es una copia de `evaluar_f4.py` con UNA línea cambiada; la batería entera (40 escenarios) corre contra la copia con `F4_RAIZ`. Script `verificador/mutar_mio.py`, salida `verificador/mutar_mio_salida.txt` (las filas A06 y A07 de la primera parte de ese archivo son de una primera corrida con la mutación mal escrita, SyntaxError; valen las tres últimas filas, A06, A07 y A10, de la segunda corrida).

| id | regla del documento que se muta | resultado |
|---|---|---|
| IDENTIDAD | ninguna | VIVA, como debe |
| A01 | §8.5: 50 negativos inyectados (50 a 40) | VIVA |
| A02 | §9.1: banda [0,8; 1,25] de Chillán (a [0,5; 2,0]) | VIVA |
| A03 | §9.1: p <= 0,05 de Chillán (a <= 0,5) | VIVA |
| A04 | §6 bis: «SIN SUSTRATO con neto 0 o a favor» (a neto <= 5) | VIVA |
| A05 | §6 P1b: K >= 1 MW inclusivo (a K > 1 MW) | VIVA |
| A06 | §8.6: falla del arnés (`estado` distinto de «ok») deja el control en rojo | VIVA |
| A07 | §8.6: `motivo` desconocido es falla | VIVA |
| A08 | §9.1: Chillán con el brazo elegido (a V siempre) | VIVA |
| A09 | §8.9(a): la clase de V reproduce la distancia radiante | VIVA |
| A10 | §8.9(b): variantes en la misma clase conservan el VRP del cúmulo | VIVA |
| A11 | M: signo de d (invertido) | ATRAPADA (E01, E08, E09, E15, E34) |
| A12 | §6 P1: sólo OCR no veta (a que veta) | ATRAPADA (E04) |
| A13 | §6 «Chillán»: ambas magnitudes mayores que 0 | VIVA |
| A14 | §8.2: con otro gránulo la máscara no se exige | ATRAPADA (E13) |
| A17 | §8.6: sin pasadas sobrantes | VIVA |
| A15 | (equivalente: `_error` ya ignora `far_ref` cuando no es P2') | no cuenta |
| A16 | (regla que no está en el documento: agregué una condición) | no cuenta |

Válidas: 15 (A01 a A14 y A17). Atrapadas por aserción: 3 (A11, A12, A14). Vivas: 12. A15 y A16 salen VIVAS en el archivo y no significan nada.

## VERIFICADO LIMPIO

- Árbol = commit; hashes del §13 iguales; `evaluar_d25.py` blob `1dbabf657407b6db0f91d9e2fc98eb16a8051873` (`git hash-object`) igual al del sello y al que el evaluador exige.
- Batería (mía): `python probar_evaluar_f4.py` 40 de 40 OK en 3 min 48 s (`verificador/bateria_mia.txt`). Contra el vacío (`--modulo evaluar_vacio.py`): 40 de 40 fallan por aserción, 0 caen, código de salida 1 (`verificador/vacio_mio.txt`).
- Mutaciones del autor: las 46 filas de `mutar_evaluar_f4_salida.txt` traen al menos un escenario con «FALLA ASERCION» (leídas con un script, 46 de 46); el control de caída da CAE y la identidad VIVA. Que el medidor las llame «atrapadas» por código de salida es frágil (VF4-08), pero no infla esta cuenta.
- Funciones importadas de `evaluar_d25.py` con las firmas que el evaluador usa; las claves `k`, `d`, `m`, `clave` de los pares coinciden con lo que lee `comparar_con_ganancia`.
- Reglas heredadas del sello (leí `evaluar_paquete.py` del tag `s162-modd-tag` y el `PREREGISTRO.md` sellado, versión v2 con adendas 1 a 4): P1 (veto), P1b (K ≥ 1, brazo < 1; la contraria se lista), P2 (`regla_signos_p2`, bloque noche-volcán), M (sólo EMPEORA decide), Chillán (n < 5 SIN SUSTRATO, banda [0,8; 1,25], p ≤ 0,05 en enteros, corte 30°, empates fuera), regla 1 (b) de la adenda 4 (protegida de K fuera del denominador va a DECIDE NICOLÁS), VCR-06 (predicado de K vs runner). Cambios declarados en la tabla «Qué cambia»: P1 sólo OCR a DECIDE, P2' con `far_ref`, fila 2 del veredicto, denominador por `motivo`, Chillán con magnitud mayor que 0, PROPONER ADOPCIÓN. Único cambio NO declarado: VF4-05.
- §7 contra `veredicto()` fila por fila, y la batería ejerce las seis filas (E01/E34 fila 6; E04, E06, E07, E09, E15 fila 5; E02, E37 fila 4; E05, E26 fila 3; E03, E25 fila 2; E10 a E19 fila 1).
- Brazos de posición contra el tablero: `mirovaEqVrp` (`frontend/index.html:1162`) decide con `distance_class` y `primary_cluster.centroid_dist_km` contra `inner`; `isSummitDetection` con `distance_class`; `isValidDetection` con `primary_cluster.vrp_mw`. Las variantes cambian exactamente `distance_class`, `pc.centroid_dist_km` y `final_hotspot_dist_km` (este último no lo lee el predicado), con la misma frontera inclusiva que `procesar_grilla` (`dcen <= inner_km`). `store.py` (guardia A46, l. ~522) no desharía la variante porque `pc.centroid_dist_km` y `distance_class` salen del mismo número. La regla es la misma de `comun.variante` de S165 (comparé texto). N01 de la batería corre node sobre el tablero real y publica el cambio.
- Contra Nicolás (programa §7): radiante = centroide del cúmulo de la más radiante; cercano = alertado más cercano; pico = el de mayor radiancia. `distancias` lo hace así (comparé con `procesar_grilla` y con `comun.reglas` de S165; el pico del cúmulo y el de todos coinciden porque la semilla es el máximo global).
- Cifras del censo contra `evaluar_censo_salida.txt` y `resultado_censo.json`: P2 GANA neto -41 B 50 (S_K 49, S_b 8), M MEJORA n 78, Chillán 6 de 7 con p = 8/128, SIN RESOLVER; P1b = Láscar 2026-04-25 07:35 (K 1,245; PM 0,9731; MIROVA 1,28), 1,1124 MW con la regla de MATLAB (`tests/test_mirova_modis_codigo_s164.py:209`, verificador del censo); 5.321 + 144 = 5.465.
- Referencia: commits `cb91eb506c37…` (2026-10-27T21:21:07Z) y `cfc57c4d8bc5…` (2026-10-27T13:06:30Z) existen en Mirova-v1 con esas fechas (`gh api`), y son los de `experiments/_s165_regla_posicion/referencia_salida.txt`.
- S165 en MODIS: 1 de 5.321 cambia con «cercano», Láscar 2026-03-30 07:25, 11,685 MW como cumbre, MIROVA `FALSO_POSITIVO` a 26,87 km (`experiments/_s165_regla_posicion/INFORME.md`, sección MODIS).
- #915 y el 25-oct 07:20: «12-oct, 25-oct y 15-oct» a 58,2 / 58,0 / 57,6° (`LOOP_OBJETIVOS.md`, 2026-10-27 11:31 UTC); el censo recupera 12 y 15 y no incluye el 25.
- CMR: re-corrí `cmr_cola.py` (05:01 UTC); idéntico al del autor salvo `6.1NRT` del 21-oct (VF4-07).
- Cuantización float32 (el control de identidad exige máscara idéntica con cero tolerancia; las grillas del censo son float32 y el runner trabaja en float64): `verificador/cuantizacion_float32.py` aplica ruido relativo uniforme de ±6e-8, ±1e-6 y ±1e-5 a las 5.321 grillas guardadas y corre `detectar_mirova` de `pipeline/`: **0 de 5.321 máscaras cambian** en los tres niveles (230 celdas alertadas en base). El rojo por cuantización es improbable (`cuantizacion_float32_salida.txt`).
- Las 5.321 `grilla_NNN.npz` existen en `D:\vrp-trabajo\temporales\s162_modd\censo\` (265 MB).
- Camino «ventana que cruza un régimen»: el A/B recalcula K y V con el mismo código en todas las fechas (A104), #535 y la adopción de K sólo tocan el control K = producción, que compara contra lo que producción escribió en cada fecha y re-corre en su sha. No encontré cruce no declarado.
- Camino «excepciones del tipo se decide al ver»: el único lugar donde hay discrecionalidad es VF4-06.

## SIN DATO

- Arnés, identidad, población, workflow, humo: no existen (§11). Todo lo que dependa del contrato real de `f4_parte*.jsonl` (campos `v_marca`, `motivo`, `dist`, `store_descarto`, `pub_runner`) es la intención del documento, no una medición.
- Si `poblacion_mxd03.py` re-etiqueta con la referencia congelada de S165 sin tocar nada más (el script tiene `VENTANA` fijo y por defecto baja del remoto; el documento dice `--sin-bajar` con las copias de S165).
- Si los gránulos del 17 al 20 de octubre se descargan de LAADS (VF4-07).
- El efecto real de las etiquetas nuevas (post D-39) en P1, P1b, P2 y M: las predicciones del §10 son con la referencia del censo y el propio documento lo dice.
- Si «MIROVA pasó a la Collection 7» (el documento lo declara SIN DATO).
- Si K del arnés = data/ en el tramo E, donde producción pudo escribir con NRT (`product_version`) y el arnés baja primero Standard (delta de BT menor que 0,1 K, pero en el borde del umbral puede cambiar una publicación).

## SEGUIMIENTOS (fuera del eje)

- En MODIS los brazos de posición casi no pueden ganar (1 de 5.321 pasadas cambia en el censo): P2' contra V necesita 5 bloques o más. La maquinaria triplica los records por el almacén para medir algo que el censo ya dice que no se va a mover. Es lo que Nicolás pidió; vale dejar escrito que en MODIS el resultado esperado es «sigue V» y que no es evidencia a favor de radiante.
- La distribución de `neg_limpio` por cenit alto: el pre-registro no estratifica P2 por cenit; el A/B de V750 y el de MODIS podrían compartir esa estratificación (tarea 1.35 del programa).
- La razón brazo/MIROVA en [0,9; 1,1] informa y no decide (§12.4); se ve razonable, pero la mediana sobre «todas las protegidas que el brazo publica» incluye las que K no publica, así que no es comparable con la curva de K.
