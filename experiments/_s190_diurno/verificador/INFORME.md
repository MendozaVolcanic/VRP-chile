# Verificación independiente del A/B diurno sobre la vía (adenda V, S190)

- Hora del servidor al empezar: Sat, 21 Nov 2026 14:39:25 GMT (`gh api -i repos/MendozaVolcanic/VRP-chile`).
- Commit revisado: `dda72573f46c21b0f533aea7ab520ad2cb2c4f31` (rama `s190-diurno`, worktree
  `D:\vrp-trabajo\worktrees\s190-diurno`). Sha de código de las corridas: `git rev-parse s190-diurno-via-codigo^{commit}`
  = `51aafdf14c21f5bad267fdaa98028107fccad1d4` (merge de #1035 a main).
- Caminos escritos antes de abrir las salidas: `D:\vrp-trabajo\temporales\s190_diurno\verificador\caminos.md`, con el
  sha256 de `veredicto_salida.txt` (8f205cb2...) y de `informativo_sin_i4b_salida.txt` (12c8e6b0...) en
  `D:\vrp-trabajo\temporales\s190_diurno\verificador\caminos_sha256.txt`.
- Scripts propios en `D:\vrp-trabajo\temporales\s190_diurno\verificador\scripts\` (v1 a v8); cada salida, en un
  `*_salida.txt` al lado. Metadatos de las corridas bajados con `gh` en `verificador\gh\`.
- Qué NO miré: no corrí la batería `tests/test_evaluar_diurno_via_s190.py` ni las mutaciones (me fié del diff y de
  `mutaciones_salida.txt` del repo, sin reejecutarlo); no revisé el código del pipeline que produce los records (la vía,
  `run_pipeline.py`, el descarte 171-01) más allá de lo que dicen los logs; no bajé gránulos (no tengo el token) ni
  abrí el MOD021KM de Isluga; no audité la referencia congelada fila por fila (sólo su sha256 contra el sustrato); no
  revisé el sustrato (`sustrato_via.json`) ni recalculé la vara de I4c desde producción; no verifiqué el predicado del
  tablero contra la página publicada (sólo que el `index.html` del worktree coincide con el del tag en los 11 Tier A).

## En una pantalla

1. Con la regla sellada obtengo **INVÁLIDO POR INSTRUMENTO en los dos flags** (`enable_daytime_modis` y
   `enable_daytime_viirs`). **Coincide** byte a byte con `eval\veredicto_salida.txt` y `eval\veredicto.json`.
2. Lo produce **un solo caso de I4b**: Isluga, MODIS, 2026-07-22. La única pasada diurna que lista MIROVA ese día
   (Terra 12:25, RUTINA, 0 MW) se bajó y se procesó, y la vía no guardó record (descarte de borde 171-01 o volcán fuera
   del gránulo); Aqua no tiene gránulo diurno ese día en CMR (2 gránulos en la caja, ambos nocturnos). I4b mide lo
   escrito, pero no lo que quería medir (pérdida de cobertura): bajo la vía ese descarte también ocurre de noche.
3. Datos sanos: cada raíz trae exactamente lo que dice ORIGEN.txt, los dos brazos de cada volcán salen del mismo job
   y run, la noche es idéntica record a record (12.967 por brazo, suma de las seis ventanas de `v5_records_salida.txt`), ninguna descarga quedó sin terminar, y las noches que
   faltan en los dos brazos están a la tasa de producción (MODIS 89 de 2.362, VIIRS 375 74 de 3.341, VIIRS 750 0).
4. Los 13 días excluidos (2026-11-03 a 11-15) salen bien de la regla (a)+(b'), pero la causa es el **cese definitivo de
   Suomi NPP**, no un hueco: sacan de la cuenta 9 protegidas MODIS, 13 de VIIRS 375 y 12 de VIIRS 750 (la erupción de
   Chillán). Sin excluir, el veredicto sellado y el informativo no cambian.
5. Si Nicolás deja pasar ese caso de I4b (desviación que sólo él decide), el resultado es **DECIDE NICOLÁS CON M4 en
   los dos flags**, con y sin los 13 días excluidos; lo reproduje y coincide con `eval\informativo_sin_i4b_salida.txt`.

## Hallazgos

### H1. El veredicto sellado es INVÁLIDO por un caso de I4b que la compuerta no fue escrita para atrapar
- Dónde: `experiments/_s190_diurno/evaluar_diurno_via.py:183-186` (I4b, heredada de S163 §5 I4 (b) sin adaptar a la
  vía); el dato, `eval\W3\_s190_ab_diurno_via_on\Isluga.json` y `eval\W3\logs\_s190_ab_diurno_via_on_Isluga.log`.
- Qué pasa: I4b exige que ningún volcán, sensor y día con pasadas diurnas de MIROVA quede con cero records diurnos del
  brazo. En S163 (K) eso equivalía a «se perdió una descarga», porque K guardaba record de toda pasada procesada (vara
  VIIRS 375 de producción: 0 de 2.715). Con la vía no es así: producción misma pierde de noche 98 de 2.674 pasadas
  MODIS y 82 de 3.698 de VIIRS 375 (`sustrato_via.json`), y por eso la adenda V cambió la vara de I4c; I4b quedó con
  tolerancia cero. El caso: la única pasada diurna MODIS de MIROVA en Isluga el 22 de julio es Terra 12:25 (RUTINA,
  0 MW, `v7_dias_vacios_salida.txt`). El log del brazo diurno muestra que el gránulo `MOD021KM.A2026203.1225` se buscó,
  se bajó y se procesó, y termina en «sin record (vía encendida: descarte de borde de la vía, 171-01, o volcán fuera del
  gránulo)». Aqua no tiene pasada diurna ese día: CMR da sólo 2 gránulos MYD021KM en la caja el 2026-07-22 (contra 4 y
  6 los días vecinos, `v3_cmr_salida.txt`), y los dos records MODIS de ese día en ambos brazos son nocturnos (01:30 y
  07:45). El mismo descarte aparece de noche en el control (197 líneas «sin record» en los logs del control, 393 en el
  brazo diurno).
- Cómo se ve: `COMPUERTAS: inválido 1` con `I4b Isluga|MODIS|2026-07-22` y nada más; I4c pasa en los tres sensores
  (MODIS 64 de 2.326, VIIRS 375 71 de 3.044, VIIRS 750 0 de 3.012 sin record).
- Lectura: la compuerta falla por un hueco parcial de NASA en Aqua (que la regla de exclusión no cubre: es parcial y es
  MODIS) más un descarte de borde de la vía, que es comportamiento del sistema que se adoptaría, no del brazo roto.
  Es una pasada negativa (RUTINA): su falta no puede inflar ninguna métrica a favor de ADOPTAR. Aun así, el texto
  sellado (adenda 1 punto 4: «si I4 vuelve a fallar después de excluir, INVÁLIDO») manda INVÁLIDO, y saltárselo es una
  desviación que decide Nicolás.
- Reproducir: `python -I experiments/_s190_diurno/evaluar_diurno_via.py --raiz <eval\W2> ... --raiz <eval\W7> --ref
  <ref_db04...> --sha-codigo 51aafdf14c21f5bad267fdaa98028107fccad1d4 --excluidos verificador\excluidos_mios.json`
  (salida en `verificador\veredicto_mio_salida.txt`); trazado del dato con `scripts\v7_dias_vacios.py` y
  `awk '/>>> Isluga \| 2026-07-22/{f=1} />>> Isluga \| 2026-07-23/{f=0} f' eval\W3\logs\_s190_ab_diurno_via_on_Isluga.log`.
- Confianza 5 (en que el veredicto sellado es INVÁLIDO y por esta causa). Gravedad 4: decide el resultado del A/B.
  Confianza 3 en que la causa del descarte sea el borde y no «volcán fuera del gránulo» (el log no separa las dos;
  SIN DATO de la geometría del gránulo).

### H2. Los 13 días excluidos salen de la regla, pero por un cese definitivo de Suomi NPP, y sacan la mitad de W7
- Dónde: `eval\dias_excluidos.json`; regla en `experiments/_s163_diurno_k/PREREGISTRO.md` §11 adenda 1;
  `scripts/ceses_esperados.json` (cese de Suomi NPP desde 2026-11-02 13:00 UTC).
- Qué pasa: desde el 2026-11-03 CMR no tiene ningún gránulo VNP02IMG ni VNP02MOD (el 11-02 tiene 1, el 11-01 tiene 4)
  y el control no tiene records de Suomi NPP: (a) y (b') se cumplen cada día y la regla, mecánica, excluye del 11-03 al
  11-15 **de los dos brazos y de todos los sensores**, incluidos MODIS, NOAA-20 y NOAA-21, que sí tienen datos. La regla
  se escribió para un hueco transitorio (W1, «si alguien pudo tener ese dato»); con un cese definitivo nadie pierde nada
  que MIROVA tenga (MIROVA tampoco puede listar Suomi NPP), así que la exclusión no protege I4 de nada y sólo achica la
  muestra.
- Cómo se ve: sin excluir, las protegidas diurnas observadas suben de 7 a 16 en MODIS, de 42 a 55 en VIIRS 375 y de 18
  a 30 en VIIRS 750 (`sin_exclusion_salida.txt` contra `veredicto_mio_salida.txt`); casi todas son W7 (Chillán en
  erupción). Las compuertas dan lo mismo (sólo el I4b de Isluga) y los veredictos por sensor no cambian: MODIS
  DECIDE NICOLÁS CON M4 (caso e-ii), VIIRS 375 ADOPTAR base y DECIDE NICOLÁS CON M4 por M8, VIIRS 750 ADOPTAR base y
  DECIDE NICOLÁS CON M4 por R-CH y M8.
- Lectura: excluir cumple la regla y no esconde nada que cambie el veredicto; sí deja fuera justamente el tramo que
  motivó W7, y cualquier lectura de M4 que haga Nicolás debería mirar también la corrida sin exclusión.
- Reproducir: `scripts\v3_cmr.py` (consulta CMR propia) y el evaluador con `verificador\excluidos_vacio.json`.
- Confianza 5. Gravedad 2 (no cambia el veredicto; sí cambia lo que Nicolás vería en M4).

### H3. Con I4b de Isluga perdonado, el resultado es DECIDE NICOLÁS CON M4 en los dos flags, y no es frágil
- Dónde: `experiments/_s190_diurno/informativo_sin_i4b.py` (quita exactamente la cadena del caso y nada más; leído).
- Qué da (reproducido, idéntico a `eval\informativo_sin_i4b_salida.txt` y su json):
  - MODIS: 7 de 7 protegidas recuperadas, 1 negativo publicado de 2.223 (Chillán 2026-10-27 20:35, de 1 MW o más),
    0 de 2 alertas bajo 1 MW; neto +1, D cumple, caso e-ii: DECIDE NICOLÁS CON M4. Sin W7 saldría ADOPTAR.
  - VIIRS 375: 23 de 42 protegidas, 8 de 11 alertas bajo 1 MW, 8 negativos de 2.620 (Q_d 0,31 % contra Q_n 1,49 %
    del control de noche); P2 EMPATE con neto 0, caso b: ADOPTAR base; M8 da 11 publicaciones de 1 MW o más en
    pasadas que MIROVA no lista (5 fuera de Chillán), así que DECIDE NICOLÁS CON M4.
  - VIIRS 750: 13 de 18 protegidas, 0 negativos de 2.910; ADOPTAR base (caso b); sin Chillán NO ADOPTAR (R-CH) y
    M8 de 5: DECIDE NICOLÁS CON M4.
  - Las cuatro variantes del §6.4 y las informativas (mínimas, filtro de 12°) dan lo mismo.
- Sin los 13 días excluidos y sin ese I4b, también DECIDE NICOLÁS CON M4 en los dos flags
  (`sin_exclusion_sin_i4b_salida.txt`).
- Confianza 5 en los números (reproducidos). Gravedad 3: es lo que Nicolás leerá si acepta la desviación.

### H4. VIIRS 375 de día no recupera 19 de 42 protegidas de MIROVA, casi todas Láscar y Lastarria al mediodía de junio
- Dónde: `veredicto_mio.json`, `protegidas_no_publicadas`.
- Qué pasa: las 19 no publicadas son 13 de Láscar y Lastarria entre 17:24 y 18:24 UTC (13 a 14 h locales) de W2 y W5,
  más Isluga, Chaitén y Villarrica. W2 da 0 de 11. Es el patrón que el estudio 1.13 marcó como reflejo probable (el
  760 MW de Láscar del 15 de junio es una de ellas). Con el detector de MIROVA (la vía) no las reproducimos: o el NRT
  de MIROVA no corre de día lo mismo que su `.m` publicado, o hay un ajuste diurno que no tenemos. No afecta R1 (el
  control de día no publica nada) pero es la mitad del «beneficio» que el A/B no captura.
- Confianza 4 en el conteo; SOSPECHA en la explicación (no la comprobé). Gravedad 2.

### H5. M8 mezcla pasadas que MIROVA no lista con dobles gránulos de la misma pasada
- Dónde: `evaluar_diurno_via.py:230-250`; dato `scripts\v8_m8_pareo.py` y `v8_m8_pareo_salida.txt`.
- Qué pasa: de 21 publicaciones «sin fila» (VIIRS 375 y 750), 19 están a 18 min o más de la pasada de MIROVA más cercana
  (otro satélite u otra órbita: MIROVA no la lista). Dos (Puyehue-Cordón Caulle 2026-06-13 19:42 y 2026-09-13 18:24)
  están a 6 min: son el gránulo siguiente de la misma pasada de NOAA-20 y NOAA-21; el brazo guardó record de los dos
  gránulos (19:36 y 19:42) y MIROVA uno. Las dos son de menos de 1 MW (0,287 y 0,461), así que no cuentan para el umbral
  de M8 y no cambian nada. El conteo de 1 MW o más (11 en VIIRS 375, 5 en VIIRS 750) es real.
- Confianza 4. Gravedad 1.

### H6. La vara de I4c incluye los días que después se excluyen
- Dónde: `sustrato_via.json`, `vara_cobertura_nocturna_produccion` (pasadas nocturnas de W2 a W7 enteras).
- Qué pasa: la cota p_sup se calculó con las noches de producción del 11-03 al 11-15, que luego salen de la evaluación.
  Con estos números I4c queda lejos de su umbral en los tres sensores, así que no cambia nada. Confianza 3 (no
  recalculé la vara). Gravedad 1.

## VERIFICADO LIMPIO

- **Origen de las raíces** (pregunta 1). Cada JSON y cada log de `eval\W2..W7` coincide por sha256 con un archivo bajado
  de la carpeta que declara `eval\ORIGEN.txt` (`v1_origen_salida.txt`): W2 Láscar y Villarrica de `W2_reparacion`, W4
  Isluga de `W4_reparacion`, W5 Láscar, Planchón-Peteroa y Tupungatito de `W5_reparacion`, Chillán, Lastarria y Villarrica
  de `W5b_reparacion`, todo lo demás de su base. 11 volcanes y 22 logs por ventana.
- **Mismo run para los dos brazos**. Las horas `[diag]` de cada log caen dentro del intervalo del job
  `reproc (<volcán>, <brazo>)` del run declarado, con las fechas exactas de la ventana y `Done.` al final (0 problemas en
  132 logs, `v2_logs_jobs_salida.txt`); control negativo: si se declara la base de W2 para Láscar y Villarrica, el script
  marca 4 problemas. Los 38.890 records tienen `regimen.codigo_sha` = tag, `regimen.perfil` = su brazo y
  `processed_utc` dentro de su job; ninguno fuera de ventana ni duplicado (`v5_records_salida.txt`). Los 10 runs
  tienen `headSha` 51aafdf14 y `headBranch` el tag; los jobs fallidos son los ya declarados (recolectar por cobertura en
  W2, W4 y W5; Lastarria control sin token en W5; Chillán brazo diurno con 401 en la reparación de W5), y ninguno de
  ellos aporta datos a las raíces.
- **Cobertura nocturna pareja** (pregunta 2). Records nocturnos idénticos entre brazos en cada volcán, plataforma y
  ventana (0 grupos distintos; W2 2.132, W3 1.413, W4 2.223, W5 2.344, W6 1.566, W7 3.289 por brazo), cero records
  diurnos en el control. Las pasadas nocturnas de MIROVA sin record en ninguno de los dos brazos están a la tasa de
  producción (MODIS 89 de 2.362, 3,8 %; producción 98 de 2.674, 3,7 %; VIIRS 375 74 de 3.341, 2,2 %; producción 82 de
  3.698, 2,2 %; VIIRS 750 0 y 0) (`v6_noches_mirova_salida.txt`). En los logs, toda descarga que empezó terminó
  (40.353 lotes, 9 reintentos) y los 16 errores de búsqueda en CMR se recuperaron; los 132 logs dicen «ninguna búsqueda
  ni descarga fallida» (`v4_logs_fallas_salida.txt`). Las «incidencias» de W6 y W7 son búsquedas vacías (Aqua y Terra
  un día, y Suomi NPP desde el cese) y salen igual en los dos brazos.
- **Días excluidos** (pregunta 3). Mi consulta propia a CMR (`v3_cmr.py`, misma caja y productos) da la misma lista de 13
  días con la misma evidencia (VNP02IMG y VNP02MOD); NOAA-20, NOAA-21 y MODIS no tienen días vacíos en W2 a W7; (b') se
  cumple esos días. Ver H2 sobre lo que significa.
- **Lectura 2 de R-W7** (pregunta 4). `git diff 51aafdf14 dda72573f` del evaluador cambia sólo la condición
  `if sin_w7 == NO_ADOPTAR` por `if base == ADOPTAR and sin_w7 == NO_ADOPTAR` y su docstring, que es la lectura 2 de
  `PREGUNTA_R_W7.md`; la prueba y la mutación A6L1 cambian en consecuencia. Sin cambios en `experiments/_s163_diurno_k/`,
  `scripts/`, `pipeline/*.py` ni `sustrato_via.json`. `frontend/index.html`, `pipeline/grillas_mirova.yaml` y
  `volcanoes.yaml` difieren sólo en coordenadas de volcanes fuera de los 11 Tier A (vienen de main). En este conjunto
  la lectura 2 no actúa: ningún sensor tiene base NO ADOPTAR con sin W7 NO ADOPTAR.
- **Reproducción del veredicto** (pregunta 5). Salida y json idénticos a los originales (salvo la línea de perfil).
  Referencia congelada con los cuatro sha256 del sustrato.
- **I1, I2, I3, I5, I6, R1, M6, M7** en verde y con sentido: flags en todos los logs; dayflag 1 en 2.329 records MODIS,
  4.650 VIIRS 375 y 4.860 VIIRS 750 de día del brazo; 0 records diurnos sin ángulos; reflejo descartado de día 23 veces
  en MODIS y 4 en cada VIIRS (la defensa contra el Sol actúa); 0 records diurnos caídos a K; noche sin diferencias ni
  en otros campos.

## SIN DATO

- Geometría del gránulo `MOD021KM.A2026203.1225` sobre Isluga (borde o fuera): no tengo token para bajarlo.
- Si producción, encendida de día, daría el mismo descarte (lo supongo por los logs del control nocturno, no lo medí).
- Batería y mutaciones del evaluador en `dda72573f`: no las reejecuté.
- Por qué MIROVA publica de día alertas de Láscar y Lastarria que su propio `.m` (la vía) no reproduce (H4).
- La vara de I4c recalculada sin los días excluidos (H6).

## SEGUIMIENTOS

1. Que Nicolás decida, con H1 a la vista, si acepta perdonar el I4b de Isluga 2026-07-22 (desviación declarada). Si
   no, el A/B queda INVÁLIDO y para repetirlo habría que reescribir I4b para la vía (por ejemplo, contar el volcán-día
   vacío sólo si el log no muestra el gránulo procesado), lo que exige un sello nuevo.
2. Llevar a la regla de exclusión una nota sobre ceses definitivos de plataforma (H2) antes de cualquier A/B que cruce
   el 2026-11-02, y mostrar a Nicolás M4 también sin la exclusión.
3. Si decide con M4: mirar H4 (19 protegidas VIIRS 375 de MIROVA que la vía no reproduce) y la lista de M8 (11 y 5
   publicaciones de 1 MW o más sin fila de MIROVA, 5 de VIIRS 375 fuera de Chillán: Tupungatito, Villarrica dos veces,
   Láscar, Lastarria).
4. M8 debería tratar como una sola pasada dos gránulos consecutivos del mismo satélite (H5); hoy no cambia nada.
