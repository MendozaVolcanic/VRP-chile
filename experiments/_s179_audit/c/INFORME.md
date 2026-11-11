# Auditoría S179, frente C: instrumento y retrospectiva (el candado y las decisiones post hoc)

## 1. Encabezado

- **Hora del servidor de GitHub** (`gh api -i repos/MendozaVolcanic/VRP-chile`, cabecera `Date`): 2026-11-11 00:46:00 GMT
  con las mediciones en curso y 2026-11-11 01:04:39 GMT al cerrar el informe. Los insumos de GitHub que usé son los bajados por quien orquesta el 2026-11-10 20:37:28 GMT
  (`D:\vrp-trabajo\temporales\s179-audit\insumos\hora_servidor.txt`).
- **Commits sobre los que medí.** Código de la base: main `438a60a1e` (instantánea en
  `D:\vrp-trabajo\temporales\s179-audit\main\`). Documentos del loop: `0472cd95e`. Pre-registro: tag
  `s173-prereg-retro-sellado` (commit `aa2a63079`). Lectura auditada: tag `s178-retro-lectura` (commit `ba5ef81c5`) y rama
  `claude/s178-retro-lectura` (commit `ff8a39972`, el worktree `D:\vrp-trabajo\worktrees\s178-lectura`). Código que corrió la
  retrospectiva: tags `s172-retro-d1` a `d4`, los cuatro sobre `a7a6ae360`. K de disco: `origin/main` `e7cfbaf54`.
- **Modelo y esfuerzo.** claude-fable-5-2. El nivel de esfuerzo real del pedido no lo puedo medir desde dentro de la
  sesión: SIN DATO (la lección de S175 dice que se mide en el transcripto). No lancé subagentes.
- **CARPETA**: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s179_audit\c\` (scripts
  `c01` a `c12`, cada uno con su salida `_salida.txt` al lado, este informe y `hallazgos.csv`). Datos intermedios (155 MB,
  desechables): `D:\vrp-trabajo\temporales\s179-audit\c\`.
- **Llamadas a la API de GitHub**: 2 de 10 (la hora del servidor, dos veces). Ninguna a NASA, ningún
  workflow, ningún commit. El worktree `D:\vrp-trabajo\worktrees\s178-lectura` quedó sin cambios (`git status` vacío antes y
  después; corrí Python con `PYTHONDONTWRITEBYTECODE=1`).
- **Lo que NO miré** (mi silencio sobre esto no quiere decir que esté bien):
  - No corrí la batería ni las mutaciones del lector (`mutar_leer_retro.py`, `mutar_montaje_ab.py`, pruebas de `tests/`).
  - No leí línea a línea `armar_montaje.py` ni `montaje_ab.py`. De C-montaje recalculé con código propio sólo VIIRS 375;
    MODIS y VIIRS 750 los leí del JSON commiteado.
  - No reimplementé el brazo «cercano» de VIIRS 375 ni las piezas selladas de V375-E (`evaluar.py`, `criterios_retro`,
    silencio, P1b). Mi lectura propia mide el brazo «radiante» (el record tal cual). Para el cercano usé las funciones
    del lector.
  - No leí el texto de V750-A (`aa5583646`) ni el pre-registro de V750-B.
  - No miré las imágenes de MIROVA de ninguna pasada (no navegué).
  - No leí los logs de los runs de Actions ni el workflow `reproc-retro-paquete.yml`.
  - Los informes de los verificadores limpios de S178 no están en el repo: leí sólo su resumen en la bitácora.
  - De la bitácora leí enteras las entradas de S178, S177 y S176 (l. 570 a 800) y las de S172 a S175 por búsqueda de
    palabras (comando en la sección 6). Los bloques de arranque S178 y S179 los leí enteros; S172 a S177, por búsqueda.
  - No abrí `docs/PLAN_AUDITORIA_S179.md` ni nada bajo `experiments/_s179_*` fuera de mi carpeta.

Palabras que uso siempre igual. **La vía**: el detector «código MIROVA». **K**: el detector que hoy publica VIIRS.
**Protegida**: alerta de MIROVA de 1 MW o más. **F26**: febrero y marzo de 2026 (MODIS decide sólo con febrero).
**R25**: 2025-02-15 a 2025-12-31, contra el archivo OSF v2.5 de MIROVA. **DM**: 2026-10-01 a 10-16, sólo control de
montaje. **P1**: no perder una protegida que K publica. **P2**: equivocarse menos que K en lo débil, contado por
noche-volcán. **El lector**: `experiments/_s172_retro_paquete/leer_retro.py`. **Radiante** y **cercano**: dos reglas
para decidir a qué distancia del cráter está el calor; el record de la vía publica hoy con radiante.

## 2. En una pantalla

1. **La lectura de la retrospectiva se reproduce y sus números se sostienen.** Re-corrí el lector con insumos aplanados por
   mí y el JSON salió idéntico al commiteado. Con código propio obtuve lo mismo: ninguna protegida perdida, P2 a favor de la
   vía en los tres sensores, magnitud de la vía contra MIROVA entre 0,97 y 1,00 (K: 0,50 a 0,66). El candado (16 de 16),
   C-K (3.138 pasadas, 0 diferencias) y el código de la vía (idéntico entre el despacho, main `438a60a1e`, #974 y #983)
   están sanos.
2. **Dos reservas tocan lo que Nicolás va a decidir.** (501) El «fila 6» de VIIRS 375 depende de una lectura del lector
   (la exención N-3) que deja fuera 3 protegidas sólo del OCR que K publica y que la vía, con la posición que hoy publica
   (radiante), no publica; con la letra del §4.1 sería «DECIDE NICOLÁS», y esas 3 pasadas nunca se listaron. (502) En
   VIIRS 750 el «P2 GANA (B 17)» baja a EMPATE (B 9) sin las pasadas miradas por nombre, y el lector no lo informa.
3. **Controles con poco o ningún poder.** El sorteo del §7 no se corrió como Nicolás aprobó en S174; corrido aquí, lo
   observado se sostiene, pero «GANA» sale por azar en 8,4 % (MODIS) y 10,3 % (VIIRS 375) de los barajados. C-K cubre 12 de
   las 70 pasadas que deciden P2. El control «el nulo puede fallar» no puede fallar. El candado se arma desde la misma ref
   de lectura, creada 31 segundos antes.
4. **Las cuatro decisiones post hoc nombradas.** Caja B4 y OSF por sha256: SOSTENIDAS. Banda de VIIRS 375 en C-montaje:
   SOSTENIDA CON RESERVAS (rotulada, cambia INDECIDIBLE por leído, conserva poder). «SIN SUSTRATO no bloquea»: SOSTENIDA,
   pero deja sin veredicto la pregunta del cenit. El lector tampoco calcula dos cosas que el pre-registro pide y que, al
   calcularlas, salen a favor de la vía: la magnitud por cenit en R25 y las alertas bajo 1 MW del OSF (vía 97,0 % contra K
   94,2 % en VIIRS 375, 8 volcanes).
5. **Nada de esto contradice encender VIIRS.** Cambia lo que hay que decirle a Nicolás antes de «mergea #974» y «mergea
   #983» (sección 7, propuestas 1 a 3).

## 3. Hallazgos (lo peor primero)

Todas las cifras salen de scripts de esta sesión. Ventanas: F26-M 2026-02-01 a 02-28; F26-V 2026-02-01 a 03-31; R25
2025-02-15 a 2025-12-31; DM 2026-10-01 a 10-16 (UTC, pasadas nocturnas). Denominadores: pasadas con record de K y de la vía
(«evaluables»), salvo que se diga otro. Referencia: la congelada de la retrospectiva (CONS `811c4c07`, OCR `01c9478d`), tabla
sola. «Publica» lo da `scripts/banco_paridad.py::correr_node` sobre el frontend del tag de despacho; con el frontend de
main `438a60a1e` da lo mismo en los 130.921 casos (c11).

### 501

- **TÍTULO**: El veredicto «fila 6» de VIIRS 375 depende de la exención N-3 del lector; con la letra del §4.1 del
  pre-registro sería «fila 4, DECIDE NICOLÁS», y las 3 pasadas afectadas nunca se listaron.
- **ARCHIVO:LÍNEA**: `experiments/_s172_retro_paquete/leer_retro.py` l. 42 a 43 (lectura L4), l. 417 a 431 (`es_n3`,
  `solo_ocr_perdidas`) y l. 1309 (sólo se mira el brazo que decide), en main `438a60a1e` (mismo sha256 LF que la ref de
  lectura). Pre-registro `experiments/_s172_prereg_retro/PREREGISTRO_RETRO_PAQUETE.md` l. 232 a 234, l. 312 y l. 487, tag
  `s173-prereg-retro-sellado`. SCRIPT:SALIDA `c05_ocr_solo_cercano.py` y `c05_ocr_solo_cercano_salida.txt`.
- **QUÉ PASA**: En tres noches de marzo de 2026 la imagen de MIROVA leída por OCR dice que hubo una alerta de 1,5 a 2,2 MW
  (Suomi NPP; la tabla de MIROVA no tiene fila para esas pasadas). K publica en la cumbre un punto de 0,04 a 0,38 MW. La
  vía mide casi lo mismo que MIROVA (1,20 a 2,20 MW) pero ubica el calor a 13 a 23 km del cráter, lo clasifica lejano y,
  con la posición radiante, no publica. El pre-registro dice (l. 232 a 234, TEXTO): «una protegida sólo del OCR **no
  veta**; se lista con la cabecera de la imagen revisada (A61) y, si la vía la pierde y K la publica, el sensor va a DECIDE
  NICOLÁS (como MOD-D fase 4 §5 y §7 fila 5). N-3 queda subsumida.» El lector hace otra cosa (l. 42 a 43, TEXTO): «Las
  protegidas sólo del OCR de Suomi NPP anteriores al 2026-10-09 (N-3) se informan y no llevan a la fila 4 en VIIRS 375 ni
  en 750». Como las 21 protegidas sólo del OCR de VIIRS 375 en F26-V son de Suomi NPP, la exención las saca a todas, y la
  comprobación de la fila 4 se hace sólo sobre el brazo cercano (0 pérdidas). Con el brazo radiante son 3 pérdidas. El
  pre-registro pide además leer radiante al lado (l. 312, TEXTO): «el record de la vía publica hoy con radiante (l. 716),
  así que un veredicto de cercano no describe lo que publicaría el paquete tal como está. Si los dos difieren en el
  veredicto, el techo de VIIRS 375 es DECIDE NICOLÁS». Sin la exención, radiante va a la fila 4 y cercano a la 6: difieren.
  Las tres pasadas no aparecen ni en `lectura.json` ni en la consola de la lectura (0 coincidencias), o sea tampoco se
  «informaron». Lectura contraria, que dejo escrita: el primer verificador de #940 leyó que el §5.1 fija N-3 y que el
  lector coincide (`experiments/_s173_aud/ver940/INFORME.md` l. 142, loop/activo `0472cd95e`). No encontré en la bitácora
  una frase de Nicolás sobre L4 (sí sobre L1, VPR940-01, 07 y 10). Lo físico apunta a que no son pérdidas reales (el calor
  está lejos y el OCR de marzo no separaba bien cumbre de lejana), pero eso es justamente lo que el §4.1 manda mirar en la
  imagen.
- **CÓMO SE VE EN EL DASHBOARD**: Hoy, invisible. Con VIIRS 375 encendido (#974, posición radiante), en pasadas como estas
  el operador dejaría de ver el punto débil de cumbre que K muestra (0,04 a 0,38 MW) y no vería nada en la cumbre.
- **CÓMO REPRODUCIRLO**: `python "C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s179_audit\c\c05_ocr_solo_cercano.py"`.
  Pasadas (UTC, VIIRS 375 Suomi NPP): Isluga 2026-03-20 05:06 (OCR 2,21 MW; vía 2,199 MW a 18,94 km; K 0,098 MW); Isluga
  2026-03-24 05:30 (OCR 1,51; vía 1,214 a 23,27 km; K 0,044); Láscar 2026-03-15 05:00 (OCR 1,54; vía 1,198 a 12,99 km; K
  0,377).
- **CONFIANZA**: CONFIRMADO (los números y el código). Que la letra del §4.1 mande la fila 4 es mi lectura; hay otra
  lectura escrita por un verificador.
- **GRAVEDAD 1-5**: 3. Cambia el rótulo del veredicto con que se decide encender VIIRS 375, y deja sin revisar 3 pasadas
  en que la vía calla donde MIROVA (por OCR) y K dicen que hay algo.

### 502

- **TÍTULO**: En VIIRS 750 «P2 GANA (B 17)» se apoya en las pasadas miradas por nombre: sin ellas es EMPATE (B 9, neto -3),
  y el lector no lo informa.
- **ARCHIVO:LÍNEA**: `experiments/_s172_retro_paquete/leer_retro.py` l. 1326 a 1328 (compara sólo el número de fila) y l.
  520 a 541 (`regla_v750`: sin V750-A sellado la fila es 4 siempre), main `438a60a1e`. Pre-registro l. 155 a 157 y l. 171 a
  173. SCRIPT:SALIDA `c03_lectura_propia.py`, `c03_lectura_propia_salida.txt` (bloque VIIRS750).
- **QUÉ PASA**: De los 17 bloques noche-volcán en que la vía y K discrepan en VIIRS 750, ocho son pasadas que S158 ya había
  listado por nombre porque K daba cero donde MIROVA alertaba. Es esperable que la vía «gane» ahí: se eligieron porque K
  fallaba. Al sacarlas quedan 9 bloques y neto -3: EMPATE. El pre-registro pide ese informe (l. 171 a 173, TEXTO): «Por eso
  el lector informa P1, P2 y M de F26-M y de F26-V (750) **con y sin** las pasadas de (b)». El lector sólo guarda el número
  de fila con y sin ellas (`regla_sin_pasadas_b`), y en VIIRS 750 la fila es 4 en los dos casos porque V750-A no está
  sellado, así que `cambia_sin_pasadas_b` da falso. El resumen que recibió Nicolás dice «P2 GANA (B 17)» sin esta salvedad
  (bitácora, `tasks/LOOP_OBJETIVOS.md` l. 635, `0472cd95e`). Detalle menor: el texto sellado da para VIIRS 750 sólo la fecha
  de esas pasadas (l. 155 a 157); las horas las puso el lector (l. 170 a 174). Quitando por fecha (40 pasadas) o por hora (9
  pasadas) el resultado es el mismo. Con V750-A sellado la regla acepta GANA o EMPATE, así que la fila no cambiaría: cambia
  la fuerza de la evidencia, no el rótulo.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `python c03_lectura_propia.py D:\vrp-trabajo\temporales\s179-audit\c\tabla_tag.json D:\vrp-trabajo\temporales\s179-audit\c\lectura\lectura.json`
  (desde la CARPETA). Pasadas: Láscar VIIRS 750 2026-02-04, 02-05, 02-12, 02-21, 02-25, 02-26 y 03-11; Isluga 02-26; Cordón
  Caulle 02-01; Tupungatito 02-26.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD 1-5**: 3. Pesa en la decisión de encender VIIRS 750 (#983), cuya evidencia el bloque S179 ya llama «más
  débil».

### 503

- **TÍTULO**: El sorteo de etiquetas del §7 no se corrió con la lectura que Nicolás aprobó (decisión 2 de S174); corrido
  ahora, los resultados observados se sostienen, pero «GANA» aparece por azar más que el 5 % nominal en MODIS y VIIRS 375.
- **ARCHIVO:LÍNEA**: `experiments/_s172_retro_paquete/leer_retro.py` l. 1156 a 1177, main `438a60a1e`. Bitácora
  `tasks/LOOP_OBJETIVOS.md` l. 1179 (`0472cd95e`). Pre-registro l. 469 a 470. SCRIPT:SALIDA `c07_sorteo_s7.py`,
  `c07_sorteo_s7_salida.txt`.
- **QUÉ PASA**: La pregunta es si la vía acierta donde MIROVA alerta o si sólo publica menos que K (los negativos limpios
  son muchos más que las alertas débiles, así que callar más ya «gana»). El pre-registro pide barajar las etiquetas de
  MIROVA dentro de cada volcán y tramo de cenit (l. 469 a 470, TEXTO): «Antes de leer, el sorteo de etiquetas dentro de cada
  estrato (volcán × tramo de cenit) sobre K contra K dice qué fracción de barajados cumple «GANA o EMPATE» por azar». Con K
  contra K el control no puede variar (B = 0 siempre). Nicolás aprobó el 2026-11-05 leerlo con la vía contra K (l. 1179,
  TEXTO): «Lectura del §7 (VPR940b-01): la vía contra K con las etiquetas barajadas, rotulada post hoc.» La lectura de S178
  no lo hizo: corrió K contra K y escribió «Cómo leer el §7 lo decide Nicolás». Corrido aquí (1.000 barajados, semilla 172):

  | sensor | observado | GANA por azar | GANA o EMPATE por azar | barajados con neto igual o mejor que el observado |
  |---|---|---|---|---|
  | MODIS (593 pasadas) | GANA, B 6, neto -7 | 8,4 % | 100 % | 13 de 1.000 |
  | VIIRS 375 (2.556) | GANA, B 45, neto -28 | 10,3 % | 79,3 % | 1 de 1.000 |
  | VIIRS 750 (2.636) | GANA, B 17, neto -11 | 0,6 % | 37,9 % | 1 de 1.000 |

  O sea: el resultado observado está en la cola en los tres sensores (se sostiene), pero la etiqueta «GANA» de la prueba
  de signos no garantiza el 5 %: en MODIS y VIIRS 375 sale en 8 a 10 % de los barajados. Y el criterio «GANA o EMPATE» que
  la regla de VIIRS 375 pide casi no discrimina (79 % por azar). Dato que lo explica: si en VIIRS 375 se barajan las
  etiquetas en todo el sensor, sin estratos, «GANA» sale en 94,0 % de los barajados, porque la vía publica 550 de 2.556
  pasadas y K 669.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `python c07_sorteo_s7.py D:\vrp-trabajo\temporales\s179-audit\c\tabla_tag.json 1000` (desde la
  CARPETA). Todos los volcanes Tier A, F26.
- **CONFIANZA**: CONFIRMADO. Límite: mide el brazo radiante.
- **GRAVEDAD 1-5**: 2. Una decisión aprobada no se aplicó y un control sellado quedó sin correr; el resultado, al correrlo,
  favorece a la vía.

### 504

- **TÍTULO**: C-K («K de disco es K de hoy») casi no cubre las pasadas que deciden P2: 12 de 70.
- **ARCHIVO:LÍNEA**: pre-registro l. 402 y l. 568; bitácora `tasks/LOOP_OBJETIVOS.md` l. 738 (`0472cd95e`).
  SCRIPT:SALIDA `c03_lectura_propia.py`, `c03_lectura_propia_salida.txt` (líneas «K-gemelo»).
- **QUÉ PASA**: P2 compara la vía contra K de disco. Si K de disco no fuera lo que K haría hoy, la comparación estaría
  torcida. El control re-corre K (el «K-gemelo») sólo en Láscar y Chillán enteros y en tres días de cada otro volcán. Pero
  las pasadas en que la vía y K discrepan están sobre todo en los otros volcanes (Isluga, Lastarria, Cordón Caulle,
  Planchón-Peteroa). Cobertura medida: MODIS 2 de 7 pasadas discordantes (0 de los 5 negativos limpios que K publica);
  VIIRS 375 4 de 46 (6 de los 43 negativos que K publica); VIIRS 750 6 de 17 (0 de 3). Los tres días se eligieron después
  del sello (l. 738, TEXTO): «El pre-registro no fija cuáles son los «tres días de F26 de cada otro volcán»: se eligieron
  antes de mirar datos, repartidos en el tramo [...]: 2026-02-25, 03-10 y 03-25». Sólo uno cae en febrero, el único mes que
  decide MODIS. Los bloques en que K yerra ya se conocían al sellar (§7), así que se pudo elegir días que los cubrieran. Lo
  que mitiga: en las 3.138 pasadas cubiertas hay 0 diferencias también en campos que el sello no pedía (magnitud mostrada,
  clase de distancia, píxeles, distancia, núcleo F5), entre ellas las de las cuatro versiones de código con que se escribió
  K, y K es determinista.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: el mismo comando de 502. Ejemplo no cubierto: Cordón Caulle MODIS 2026-02-01, 02-04, 02-07 y 02-28.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD 1-5**: 2.

### 505

- **TÍTULO**: El candado compara el disco contra un manifiesto armado desde la misma ref de lectura: no puede ver que el
  lector cambió después de existir los datos, y deja fuera archivos de los que depende el veredicto.
- **ARCHIVO:LÍNEA**: `experiments/_s172_retro_paquete/armar_manifiesto.py` l. 68 a 69 y l. 94 (el manifiesto sale de la ref que se le pasa) y
  `leer_retro.py` l. 890 a 893 y l. 910 a 920, tag `s178-retro-lectura`. Pre-registro l. 410 y l. 604 a 610.
  SCRIPT:SALIDA `c11_candado_y_reproduccion.py` y `c12_identidad_git.sh`, con sus salidas.
- **QUÉ PASA**: El candado sirve para que nadie ajuste el instrumento después de ver el resultado. El pre-registro lo
  pide contra un manifiesto previo (l. 410, TEXTO): «contra el manifiesto del sello, **antes** de correr», y su §11 se
  titula (l. 604, TEXTO): «Candado (sin esto no se despacha)». En los hechos D2, D3 y D4 se despacharon el 2026-11-08 y
  11-09 sin manifiesto; el manifiesto se armó el 2026-11-10 08:39:55 UTC desde el tag `s178-retro-lectura`, creado a las
  08:39:24 UTC, que incluye los cambios hechos al lector ese mismo día con los datos ya en disco (caja B4 a las 07:29 UTC,
  comparadores y tags de C-montaje a las 08:11, banda de VIIRS 375 a las 08:35, OSF a las 08:38). Así armado, el candado
  sólo puede fallar si alguien edita un archivo sin commitear entre el tag y la lectura. Además el manifiesto no trae:
  `frontend/cambio_detector.js` (el predicado «publica» lo carga; si falta, node sólo avisa por stderr),
  `scripts/auto_audit_weekly.py` (da la noche), `scripts/calidad_referencia_mirova.py`, `volcanoes.yaml` (radio interno y
  cráter), las dos capas de historia y respaldo que agrega `cargar_referencia_unificada`, ni el texto de V750-A que el §11
  nombra. Efecto medido de esos huecos en esta lectura: ninguno. Con el frontend de main `438a60a1e` (donde
  `cambio_detector.js` cambió 176 líneas) cambian 0 publicaciones de 130.921 casos; sin el módulo, 0; las capas de historia
  y respaldo no aportan ninguna fila en F26; el worktree estaba limpio. Los cambios al lector están commiteados y descritos.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `python c11_candado_y_reproduccion.py` y `bash c12_identidad_git.sh` (desde la CARPETA).
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD 1-5**: 2. No cambió ningún número, pero el control con ese nombre no protege de lo que promete.

### 506

- **TÍTULO**: La pregunta del pre-registro sobre la magnitud cuando el satélite mira de lado quedó sin veredicto en los
  tres sensores, y el lector no calcula la curva de R25 que el §5.3 y la predicción 5 piden.
- **ARCHIVO:LÍNEA**: `leer_retro.py` l. 1310 (la curva se calcula sólo en el tramo que decide) y l. 1239 a 1242, main
  `438a60a1e`. Pre-registro l. 89 a 92, l. 342 a 344 y l. 530. SCRIPT:SALIDA `c04_r25_osf_propio.py`,
  `c04_r25_osf_propio_salida.txt`.
- **QUÉ PASA**: Cuando el satélite mira oblicuo el píxel se estira y la potencia medida cae; K cae más que MIROVA. La
  prueba tenía que decir si la vía cae como MIROVA. En F26 la curva sellada (razón doble dentro de la noche) no tiene
  sustrato: 0, 2 y 0 noches con pares contra un mínimo de 8 (lectura.json). Eso se sabía antes de despachar: el ensayo de
  S174 con K de disco ya había dado «F26 0/2/0, mínimo 8» (bitácora l. 1109). Y el lector no hace la lectura de R25 que el
  texto pide (l. 344, TEXTO): «En R25, sólo cota (§4.3), con el control C-cenit contra `SatZen`», ni comprueba la
  predicción 5 (l. 530, TEXTO): «En R25 la razón de K por cenit cae (Spearman negativo fuera del barajado) y la de la vía
  no cae más que la de MIROVA.» Calculado aquí sobre las protegidas del OSF que los dos brazos publican:

  | sensor (n) | Spearman K/OSF contra cenit | Spearman vía/OSF contra cenit | mediana vía/OSF | mediana K/OSF |
  |---|---|---|---|---|
  | MODIS (160) | -0,581 (p 0,001) | -0,039 (p 0,63) | 0,995 | 0,529 |
  | VIIRS 375 (317) | -0,547 (p 0,001) | +0,082 (p 0,13) | 1,000 | 0,659 |
  | VIIRS 750 (17) | -0,412 (p 0,10) | +0,140 (p 0,61) | 0,998 | 0,586 |

  La predicción 5 se cumple en MODIS y VIIRS 375. Límites: casi todo es Láscar (en VIIRS 375, 44 de 317 son de otros tres
  volcanes y dan 0,999), el OSF está truncado por abajo (por eso el pre-registro lo deja en «cota»), hay pocas pasadas
  sobre 50° (8 en VIIRS 375, 2 en MODIS) y no hay Chillán en erupción.
- **CÓMO SE VE EN EL DASHBOARD**: invisible. Si la vía cayera más que MIROVA en pasadas oblicuas, el operador vería
  noches con potencia baja sólo por la geometría.
- **CÓMO REPRODUCIRLO**: `python c04_r25_osf_propio.py D:\vrp-trabajo\temporales\s179-audit\c\tabla_tag.json D:\vrp-trabajo\temporales\s179-audit\c\lectura\lectura.json`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD 1-5**: 2.

### 507

- **TÍTULO**: El lector no informa las alertas bajo 1 MW del OSF en R25, que es la única evidencia fuera de muestra sobre
  alertas débiles en ocho volcanes.
- **ARCHIVO:LÍNEA**: `leer_retro.py` l. 971 a 1038 (`p1_osf` sólo cuenta protegidas, lejanas y ambiguas), main `438a60a1e`.
  Pre-registro l. 280. SCRIPT:SALIDA `c10_r25_bajo1_y_solo_via.py`, `c10_r25_bajo1_y_solo_via_salida.txt`.
- **QUÉ PASA**: El pre-registro reconoce que fuera de muestra casi no hay protegidas fuera de Láscar, y manda informar
  también lo débil del OSF (l. 280, TEXTO): «**Bajo 1 MW OSF** (sólo 375 y 1 km): informa, con SN por analogía en 375.» El
  lector no lo calcula. Calculado aquí (noche, `class` 1, bajo 1 MW, píxel más caliente dentro del radio interno, pareo a
  ±120 s, sin la regla SN): VIIRS 375, 1.485 alertas en 8 volcanes; K publica 1.399 (94,2 %) y la vía 1.440 (97,0 %). Por
  volcán la vía iguala o supera a K salvo Láscar (180 contra 181). MODIS: 79 alertas; K 67, la vía 77. VIIRS 750: 0 (el
  OSF sólo trae 5 MW o más).
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `python c10_r25_bajo1_y_solo_via.py` (desde la CARPETA).
- **CONFIANZA**: CONFIRMADO. Límite: brazo radiante; el OSF está filtrado y no es el NRT (A105).
- **GRAVEDAD 1-5**: 2. Es una omisión que escondía evidencia a favor.

### 508

- **TÍTULO**: «La noche del operador» (§5.5) está vacía en VIIRS: 0 noches limpias de 627, y el lector imprime «0 de 0»
  sin avisar.
- **ARCHIVO:LÍNEA**: `leer_retro.py` l. 1203 a 1224, main `438a60a1e`. Pre-registro l. 369 a 370. SCRIPT:SALIDA
  `c03_lectura_propia_salida.txt` (líneas «noche del operador») y `lectura.json` (`noche_operador`).
- **QUÉ PASA**: Lo que vive el operador es la noche: ¿calla el tablero cuando MIROVA calla toda la noche? El pre-registro
  la define así (l. 369 a 370, TEXTO): «Noche limpia: noche-volcán en que **todas** nuestras pasadas tienen fila de la
  tabla y todas sus filas son RUTINA (con SN). ¿El tablero calla?» En febrero y marzo de 2026 la tabla no trae NOAA-21, y
  las 627 noches-volcán de VIIRS 375 y las 627 de VIIRS 750 tienen al menos una pasada de NOAA-21 sin fila. Resultado: 0
  noches limpias, y `limpias_calladas` sale `[0, 0]` para la vía y para K. En MODIS sí hay sustrato: 256 noches limpias (la
  vía calla en 256; K en 251).
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: el comando de 502.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD 1-5**: 2. La lectura «por noche» de VIIRS no existe y nadie lo dijo; informa, no decide.

### 509

- **TÍTULO**: El nombre del veredicto de VIIRS 375 lista cuatro volcanes con alertas sin decir que en febrero y marzo de
  2026 las 26 protegidas son todas de Láscar.
- **ARCHIVO:LÍNEA**: `leer_retro.py` l. 1260 a 1265 (`nombre_fila6`), main `438a60a1e`. Pre-registro l. 492.
  SCRIPT:SALIDA `c03_lectura_propia_salida.txt` y `c04_r25_osf_propio_salida.txt`.
- **QUÉ PASA**: El nombre dice «alertas: Isluga, Lascar, PlanchonPeteroa, PuyehueCordonCaulle». Los tres que no son Láscar
  vienen sólo del OSF de 2025 (28 de Cordón Caulle, 14 de Planchón-Peteroa, 2 de Isluga), donde K ya publicaba todas y la
  prueba sólo puede decir que la vía no pierde lo evidente. El pre-registro pedía conteos (l. 492, TEXTO): «El nombre de la
  fila 6 lo arma el lector con los conteos por volcán». El lector une los nombres sin conteos ni tramo. Quien lea el
  veredicto puede creer que se probó contra la tabla de 2026 en cuatro volcanes.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `git show claude/s178-retro-lectura:experiments/_s178_lectura/lectura_salida.txt` (línea
  «VIIRS375: fila 6») contra `c03_lectura_propia_salida.txt` («protegidas por volcan: {'Lascar': 26}»).
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD 1-5**: 2.

### 510

- **TÍTULO**: C-montaje con la banda post hoc de VIIRS 375: bien rotulada en la propuesta y la bitácora, pero el rótulo no
  viaja con la lectura, la causa «triangulación» no se probó, y el rango de diferencias está mal dicho.
- **ARCHIVO:LÍNEA**: `experiments/_s178_montaje/PROPUESTA_C_MONTAJE.md` l. 93 y l. 103 (loop/activo `0472cd95e`);
  `experiments/_s178_lectura/montaje.json` (rama `claude/s178-retro-lectura`). Pre-registro l. 403. SCRIPT:SALIDA
  `c08_montaje_v375_propio.py`, `c08_montaje_v375_propio_salida.txt`.
- **QUÉ PASA**: C-montaje comprueba que la vía que corrió la retrospectiva es la que midieron los A/B. En VIIRS 375, 12 de
  las 51 pasadas con píxeles alertados dieron una potencia distinta de la del port, con los mismos píxeles. El sello sólo
  admitía dos explicaciones (l. 403, TEXTO): «(a) un hunk listado de ese `git diff` la reproduce al re-correr esa pasada con
  el código del tag de origen, o (b) la pasada cambia de gránulo (`otro_granulo`); nada más cuenta como explicación». La
  propia declaración decía (l. 93, TEXTO): «No se ensancha ninguna tolerancia al ver datos.» Después de ver las 12, Nicolás
  aceptó compararlas contra la banda de triangulación del port («Sí, opción 1», bitácora l. 630). Con mi código: 166
  pasadas pareadas, 0 con píxeles distintos, 12 con potencia a más de 0,001 MW del valor puntual, 0 a más de 0,001 MW de la
  banda (2 quedan fuera de la banda por menos del redondeo). Tres reservas. (1) La lectura guarda `montaje.json` con
  «estado: OK» y 0 diferencias, sin marca post hoc: el rótulo vive en loop/activo, no en la ref de lectura. (2) Que la causa
  sea la triangulación del fondo es una explicación razonada; nadie re-corrió una pasada para probarla. (3) La propuesta
  dice (l. 103, TEXTO): «Diferencia entre 0,3 % y 3 %»; medido: de -3,4 % a +7,4 % (Lastarria 2026-10-10 05:54, 0,068
  contra 0,0633 MW). A favor: la banda no es un cheque en blanco. Su ancho mediano es 0,0024 MW y, si la vía diera 5 % de
  más, la banda lo atraparía en 48 de las 51 pasadas con píxeles. La decisión cambia el veredicto: sin ella los tres
  sensores quedaban INDECIDIBLES (l. 403, TEXTO: «una no explicada deja todo INDECIDIBLE»). Poder del control completo:
  píxeles alertados en 12 de 343 pasadas MODIS, 51 de 166 VIIRS 375 (medido aquí) y 32 de 440 VIIRS 750 (cifra del
  verificador de S178, no la recalculé).
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `python c08_montaje_v375_propio.py` (desde la CARPETA).
- **CONFIANZA**: CONFIRMADO en VIIRS 375. La causa física de las 12 diferencias: SOSPECHA.
- **GRAVEDAD 1-5**: 2.

### 511

- **TÍTULO**: El control «el nulo de runner puede fallar» no puede fallar.
- **ARCHIVO:LÍNEA**: `leer_retro.py` l. 716 a 721, main `438a60a1e`. Pre-registro l. 407. SCRIPT:SALIDA `lectura.json`
  (`nulo_runner`) y `c03_lectura_propia_salida.txt` («placebo K x 1,2»).
- **QUÉ PASA**: El pre-registro pide probar que el nulo puede dar rojo (l. 407, TEXTO): «el mismo cálculo sobre K-gemelo
  contra PLACEBO tiene que dar B mayor que 0 o M distinta». La primera pata dio 0 (`B_contra_placebo: 0`) y no puede dar
  otra cosa: multiplicar K por 1,2 no cambia qué se publica en ninguna de las 42.769 pasadas. La segunda pata es la
  mediana de d del placebo contra K, que vale -0,0792 (el logaritmo de 1/1,2) por construcción, haya o no un defecto.
  Además el nulo mismo (B = 0 entre K-gemelo y K) repite lo que C-K ya exige. Es letra del sello, no un desvío del lector.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `python -c "import json;print(json.load(open(r'D:\vrp-trabajo\temporales\s179-audit\c\lectura\lectura.json',encoding='utf-8'))['sensores']['MODIS']['controles']['nulo_runner'])"`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD 1-5**: 2.

### 512

- **TÍTULO**: La decisión 6 de S174 (fijar los tags de origen y los campos de C-montaje antes de despachar D3) no se
  cumplió: se fijaron el 2026-11-10, con D2 a D4 ya en disco.
- **ARCHIVO:LÍNEA**: bitácora `tasks/LOOP_OBJETIVOS.md` l. 1183 y l. 662 a 668 (`0472cd95e`);
  `experiments/_s178_montaje/PROPUESTA_C_MONTAJE.md` l. 3. SCRIPT:SALIDA `c12_identidad_git_salida.txt` (orden de commits).
- **QUÉ PASA**: Nicolás aprobó (l. 1183, TEXTO): «Tags de origen y campos de los tres comparadores de C-montaje: se fijan
  antes del despacho de D3.» D3 salió el 2026-11-09 05:28 UTC. La declaración de C-montaje se commiteó el 2026-11-10 08:04
  UTC (`c592ac2d2`). La propuesta declara qué se había mirado (l. 3, TEXTO): «Escrito ANTES de mirar la vía de D2 en
  ninguna ventana (sólo se contó el campo `roi` de los records de VIIRS 750 de D2». No encontré nada que lo contradiga.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `bash c12_identidad_git.sh` (última sección).
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD 1-5**: 2.

### 513

- **TÍTULO**: El «M MEJORA» que se le informó a Nicolás es el criterio d, que un K multiplicado por 1,2 también cumple en
  los tres sensores; descontando una ganancia pareja, MODIS queda en el borde.
- **ARCHIVO:LÍNEA**: `experiments/_s172_retro_paquete/reglas/evaluar_f4.py` l. 292 a 305; `lectura.json`
  (`c_placebo.m_regla: MEJORA` en los tres). SCRIPT:SALIDA `c03_lectura_propia_salida.txt` (líneas «magnitud via»).
- **QUÉ PASA**: K queda bajo MIROVA, así que cualquier aumento parejo lo acerca. La regla de MOD-D sólo usa M para
  bloquear si EMPEORA, y la de VIIRS 375 sí exige d' (lo hace el código sellado de V375-E, que no audité). Con d' propio
  (lo que la vía gana por sobre una ganancia pareja, intervalo al 95 % por bloques): MODIS -0,034 [-0,171; 0,000] (n 11,
  todo Láscar); VIIRS 375 -0,126 [-0,158; -0,087] (n 174, 9 volcanes); VIIRS 750 -0,146 [-0,200; -0,060] (n 40).
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: el comando de 502.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD 1-5**: 1.

### 514

- **TÍTULO**: La lista «alertas de la tabla sin pasada nuestra» del lector cuenta abril a septiembre, donde la prueba no
  tiene pasadas: da 1.094 y esconde el dato útil (0 protegidas sin pasada en F26).
- **ARCHIVO:LÍNEA**: `leer_retro.py` l. 344 a 355 y l. 1430, main `438a60a1e`. SCRIPT:SALIDA `c06_alertas_sin_pasada.py`,
  `c06_alertas_sin_pasada_salida.txt`.
- **QUÉ PASA**: Una alerta de MIROVA sin pasada nuestra queda fuera de P1 y P2 en los dos brazos. El lector la cuenta
  sobre una sola ventana, del 2026-02-01 al 2026-10-16. Tramo por tramo: F26-M 0 de 14 alertas; F26-V VIIRS 375, 2 de 186
  (bajo 1 MW: Lastarria y Cordón Caulle, 2026-03-10, pasada nuestra más cercana a 30 minutos); F26-V VIIRS 750, 0 de 55.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `python c06_alertas_sin_pasada.py` (desde la CARPETA).
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD 1-5**: 1.

### 515

- **TÍTULO**: Tres decisiones del instrumento salieron de la cola sin respuesta registrada (decisiones 2, 3 y 4 del bloque
  S175).
- **ARCHIVO:LÍNEA**: `tasks/BLOQUE_ARRANQUE_S175.md` l. 50 a 52; `BLOQUE_ARRANQUE_S176.md` l. 46;
  `BLOQUE_ARRANQUE_S177.md` l. 45; ausentes en `BLOQUE_ARRANQUE_S178.md` y `S179.md` (`0472cd95e`). SCRIPT:SALIDA
  `c09_controles_con_insumo_vacio.py` y su salida.
- **QUÉ PASA**: (a) VPR952-04: si todas las etiquetas llegan sin información (una referencia rota), el control de cenit
  dice SIN SUSTRATO y no ROJO; lo comprobé a nivel de función (caso «sólo negativos»). Qué fila daría el lector entero es
  SOSPECHA (no lo corrí). (b) Pre-registro l. 409: el texto dice que con un control de cenit en rojo «la curva no se lee» y
  el lector manda el sensor entero a la fila 1. (c) La fila 4 por la curva no se puede activar en F26. Ninguna afecta la
  lectura de S178 (los controles de cenit dieron SIN SUSTRATO, no rojo). El pendiente de `docs/AUDIT_S175.md` §8 decisión 3
  sí queda cerrado: con insumo vacío, sin cenit o con cenit NaN, los controles de cenit dan ROJO y fila 1.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `python c09_controles_con_insumo_vacio.py` (desde la CARPETA).
- **CONFIANZA**: CONFIRMADO (la cola y las funciones); SOSPECHA (la fila del lector entero con todas las etiquetas vacías).
- **GRAVEDAD 1-5**: 1.

### 516

- **TÍTULO**: El sello no dejó el sha256 LF del pre-registro en el mensaje del commit ni en el tag, como pide el §11.
- **ARCHIVO:LÍNEA**: pre-registro l. 614 a 616; tag `s173-prereg-retro-sellado`. SCRIPT:SALIDA
  `c12_identidad_git_salida.txt`.
- **QUÉ PASA**: El texto dice (l. 614 a 616, TEXTO): «el del sello va en el mensaje del commit y en el tag del sello». El
  mensaje del tag es «Pre-registro retro del paquete sellado por Nicolas 2026-11-02 17:12 UTC», sin hash. La identidad del
  documento descansa en el objeto de git: el blob es el mismo (sha256 `b58a2254...`) en el sello, en loop/activo
  `0472cd95e` y en `origin/loop/activo`. El pre-registro no está en el árbol de la ref de lectura.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `git cat-file -p s173-prereg-retro-sellado`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD 1-5**: 1.

### 517

- **TÍTULO**: Las cifras de poder del §7 no se recalcularon al cambiar el commit de K, como manda el propio §7; medido
  ahora, K no cambió.
- **ARCHIVO:LÍNEA**: pre-registro l. 472 a 474 y l. 622 a 624. SCRIPT:SALIDA `c01_armar_insumos.py`,
  `c01_armar_insumos_salida.txt`.
- **QUÉ PASA**: El texto (l. 472 a 474, TEXTO): «Si antes del despacho se congela otra referencia o cambia el K de disco
  (otro commit de `origin/main`), se vuelve a correr el mismo script y se listan aquí las cifras que cambien.» El §7 se
  contó sobre `47cdc446f`; el despacho fue sobre `a7a6ae360` y la lectura usó `e7cfbaf54`. No encontré en la bitácora ni
  en los bloques S176 a S179 que se re-corriera `recalcular_s7_ref_congelada.py`. Dentro de las ventanas de la prueba K es
  idéntico en los tres commits: 46.468 records iguales, 0 distintos, 0 de más o de menos.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `python c01_armar_insumos.py` (desde la CARPETA; tarda unos minutos).
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD 1-5**: 1.

## 4. Secciones aparte

### SEGUIMIENTOS (visto fuera de mi eje; no lo perseguí)

1. **Reemplazo de la historia (#981), R25, VIIRS 750.** En 2025 la vía publica 158 pasadas que K no publica (91 en
   Isluga, mediana 0,26 MW) y K publica 234 que la vía no (145 en Cordón Caulle). El OSF no puede juzgarlas (piso de 5 MW).
   Al reemplazar la historia serán detecciones nuevas o desaparecidas sin referencia.
   `c10_r25_bajo1_y_solo_via_salida.txt`, sección (2). Confianza: CONFIRMADO el conteo; qué son, SIN DATO.
2. **Reemplazo de la historia, pasadas sin par.** En las ventanas de la prueba hay 816 pasadas de K sin record de la vía
   (K publica en 1 de ellas: VIIRS 375, R25) y 292 de la vía sin K (todas VIIRS 750 salvo 2; la vía no publica en
   ninguna). Salida inline de esta sesión sobre `tabla_tag.json`; los conteos por tramo coinciden con `lectura.json`.
3. **Cotas de la regla de reversión de VIIRS 375 (P10, C-rad 14/17).** Usan los casos de F26-V de esta retrospectiva. No
   las audité (frente B). Si el veredicto de VIIRS 375 pasara a la fila 4 (hallazgo 501), las cotas no cambian, pero
   conviene que el frente B sepa que los «3 Muy Bajo perdidas con radiante» y las 3 sólo OCR de 501 son pasadas distintas
   (no lo comprobé: SOSPECHA).
4. **K de disco no tiene las pasadas NOAA-21 del 2026-10-13** (44, VIIRS 375 y 750) que el K-gemelo sí trae (bitácora l.
   714, S177). Mi c01 ve 3.282 records del K-gemelo contra 3.138 comparados. Hueco de producción sin investigar.
5. **La propuesta de C-montaje dice que los datos de los A/B están sólo en disco local** y que el primer artefacto de
   Actions vence el 2026-11-21 (`PROPUESTA_C_MONTAJE.md` l. 23 a 25). Si se borran, C-montaje no se puede repetir.

### VERIFICADO LIMPIO (qué miré, con qué comando y contra qué vara)

| qué | resultado | comando | vara |
|---|---|---|---|
| Aplanado de D2 y D4 (vía) y D3 (K-gemelo) | 223 y 30 trozos, 42.389 y 3.282 records, 0 claves repetidas; D2 con 19 trozos repetidos una sola vez | `python c01_armar_insumos.py` | artefactos en `C:\Users\nmend\vrp-temporales\s177_d2`, `d3`, `d4` |
| Conteo de pasadas por tramo, sensor y estado | las 21 celdas iguales a `lectura.json` | `python c02_tabla_pasadas.py --frontend tag --salida ...` | código propio contra el lector |
| Protegidas de la tabla en F26 | 9 MODIS, 26 VIIRS 375, 30 VIIRS 750 | idem | §7 del pre-registro (9, 26, 30) |
| P1 en F26 | 0 protegidas que K publica y la vía no, en los tres sensores; en MODIS la vía publica Láscar 2026-02-16 01:20 que K pierde | `python c03_lectura_propia.py ...` | `correr_node` y `etiquetar` de main `438a60a1e` |
| P2 en F26, brazo radiante | MODIS B 6 neto -7; VIIRS 375 B 45 neto -28; VIIRS 750 B 17 neto -11; los tres GANA: igual que el lector | idem | prueba de signos exacta propia (D-45) |
| Controles de mi instrumento | brazo mudo pierde 8 de 8, 26 de 26 y 30 de 30; K contra K da B 0; placebo da d' 0 | idem | control positivo y negativo |
| Lectura reproducible | JSON idéntico al commiteado, con candado, desde el worktree de la ref de lectura | `c11_candado_y_reproduccion.py` (y la corrida del lector, consola en `c11_relectura_consola.txt`) | `lectura.json` de `ff8a39972` |
| Candado | 16 de 16 sha256 LF iguales; OSF en bruto `0863c240...` igual al del pre-registro | idem | manifiesto de la lectura y §4.2 |
| Pre-registro sin cambios | blob idéntico en el sello, `0472cd95e` y `origin/loop/activo` | `bash c12_identidad_git.sh` | tag `s173-prereg-retro-sellado` |
| Código de la vía | entre `a7a6ae360` y main `438a60a1e` sólo cambian `pipeline/fetch.py` y un perfil nuevo; contra #974 y #983, además sólo perfiles | idem | `git diff --stat` (control: lista `fetch.py`) |
| Flags de MODIS del perfil de la retrospectiva | iguales a producción en `438a60a1e` (MxD03 apagado, banda 22, sin Test 1) | idem | `mirova_equivalent.yaml` |
| Caja B4 de VIIRS 750 | records de la vía: «sens» en Cordón Caulle y Tupungatito, «def» en los otros nueve; igual que `grillas_mirova.yaml` en el tag, en main y en #983 | `c03` (bloque CAJA) y `c12` | `pipeline/grillas_mirova.yaml` |
| K de disco estable | idéntico en las ventanas entre `47cdc446f`, `a7a6ae360` y `e7cfbaf54` (46.468 records) | `python c01_armar_insumos.py` | `git show` de cada commit |
| C-K | 3.138 pasadas, 0 diferencias con el criterio sellado y 0 en magnitud mostrada, clase, píxeles, distancia y F5 | `c03` (bloque C-K PROPIO) | código propio |
| Frontend de hoy | con el `index.html` de main `438a60a1e` cambian 0 publicaciones y 0 magnitudes de 130.921 casos | `c11` | `correr_node` |
| Cobertura de la tabla en F26 | 0 protegidas de MIROVA sin pasada nuestra a ±120 s | `python c06_alertas_sin_pasada.py` | `indexar_referencia` (SN), control: sin pasadas salen todas |
| P1-OSF en R25 | 161, 317 y 17 protegidas; 0 candidatas; 1 MODIS sin pasada (Láscar 2025-07-15 02:15); C-cenit máximo 1,05° | `python c04_r25_osf_propio.py ...` | volcán por coordenadas (el lector, por nombre) |
| Lejanas del OSF (49, Chillán) | la vía no publica ninguna como cumbre | idem | idem |
| C-montaje VIIRS 375 | 166 pasadas, 0 con píxeles distintos, 12 de potencia, 0 fuera de la banda con 0,001 MW | `python c08_montaje_v375_propio.py` | port C13 de V375-E en disco |
| Decisión 3 de S174 (caídas a K) | 0 caídas a K y 0 records sin la marca entre los 42.245 records nocturnos de la vía dentro de los tramos: no tuvo efecto en esta lectura | `c03` (primera línea de estados) | marca `via_codigo_mirova` |
| Pendiente `AUDIT_S175` §8 decisión 3 (254) | controles de cenit con insumo vacío, sin cenit o NaN: ROJO, fila 1 | `python c09_controles_con_insumo_vacio.py` | funciones del lector |
| Predicciones del §9 | 1 y 2 se cumplen (razón 1,000 y 0,999; K 0,66 y 0,50); 3 a medias (se predijo SIN PODER y salió GANA con B 6; la vía publica la del 02-16); 5 se cumple en MODIS y VIIRS 375 | `c03` y `c04` | pre-registro l. 524 a 530 |

### SIN DATO (lo que no pude medir, y por qué)

- **Qué muestran las imágenes de MIROVA en las 3 pasadas de 501**: no navegué; hace falta mirarlas (A61).
- **Por qué 12 pasadas de VIIRS 375 difieren del port en DM**: probarlo pide re-correr con el código del tag de origen.
- **C-montaje de MODIS y VIIRS 750 con código propio**: no lo hice (otros formatos); leí el JSON commiteado.
- **Brazo cercano con código propio**: no reimplementado. El sorteo (503), d' (513) y el bajo 1 MW del OSF (507) son del
  brazo radiante.
- **Qué fila da el lector entero con todas las etiquetas vacías** (VPR952-04): no lo corrí.
- **Nivel de esfuerzo real con que corrí**: no medible desde dentro.
- **Si la batería y las mutaciones del lector siguen verdes hoy**: no las corrí.

### FUERA DE ALCANCE

- La regla de reversión de VIIRS y sus cotas, B1 y B2 como PR, la guardia K (frente B).
- La adopción de MODIS y su guardia (frente A). De MODIS sólo miré su lectura retrospectiva.
- El plan de reemplazo de la historia y los 34 volcanes (frente D); dejé dos seguimientos.
- La calidad de la referencia de MIROVA (OCR, tabla) más allá de usar la copia congelada.

## 5. Las cuatro decisiones post hoc que nombra el encargo

| decisión | ¿rotulada post hoc? | ¿podía cambiar un veredicto? | veredicto |
|---|---|---|---|
| Banda de triangulación en VIIRS 375 para C-montaje (2026-11-10, «Sí, opción 1») | Sí, en `PROPUESTA_C_MONTAJE.md`, en la bitácora (l. 630) y en el bloque S179. No en `montaje.json` ni en la ref de lectura | Sí: sin ella, los tres sensores INDECIDIBLES | SOSTENIDA CON RESERVAS (hallazgo 510) |
| Caja B4 por volcán en el lector (2026-11-10, #979) | Rotulada con fecha en el código («S178 (2026-11-10, P1 ...)», `leer_retro.py` l. 818 a 823); no usa la palabra post hoc. Se hizo tras contar el campo `roi` de D2 | Sí: sin ella, VIIRS 750 INDECIDIBLE por un control que no podía pasar | SOSTENIDA: la caja de los records es la de `grillas_mirova.yaml` en el tag, main y #983 |
| OSF fuera de git, verificado por sha256 en bruto (2026-11-10) | Rotulada con fecha en `armar_manifiesto.py` (l. 56 a 59, tag `s178-retro-lectura`) | No cambia números; sin ella no había candado con R25 | SOSTENIDA: en bruto `0863c240...` (pre-registro), LF `d8bd2dec...` (manifiesto) |
| «SIN SUSTRATO no bloquea» en los controles de cenit (S174, #952, 2026-11-07) | Rotulada con fecha («S174») en el código (l. 1239 a 1242) y en la consola de la lectura. Es posterior al sello y anterior a los datos de la vía, pero posterior a saber que F26 no tendría sustrato (ensayo de S174) | Sí bajo otra lectura: el encabezado del §6 dice «si uno cae, no se lee el veredicto de ese sensor»; leído así, los tres INDECIDIBLES | SOSTENIDA: el propio texto la respalda (l. 320, TEXTO: «Si F26-V no tiene 8 noches con pares, (d) es SIN SUSTRATO y se informa»; l. 409: «la curva no se lee»). Reserva: hallazgo 506 |

¿Tenían los controles poder para fallar?

| control | ¿puede fallar? | evidencia |
|---|---|---|
| C-K | Sí, pero donde menos importa: cubre 12 de 70 pasadas que deciden P2 | 504; la sesión de S178 inyectó 6 alteraciones y atrapó 6 (no lo repetí) |
| C-montaje | Sí en VIIRS 375 (un 5 % de más lo atrapa en 48 de 51); poco sustrato en MODIS (12 pasadas con píxeles) | 510 |
| Placebo (K × 1,2) | La pata de publicación no puede dar discordancias (0 de 42.769 por construcción); la pata de M exige d', que es 0 para toda ganancia pareja: comprueba el cableado, no los datos. En VIIRS 750 «separa» no se calculó | `lectura.json`, `c03` |
| Nulo de runner | Repite C-K; su control «puede fallar» no puede fallar | 511 |
| Nulo del lector | Sí: mutación de una protegida da fila 2 y los 50 inyectados suben el contador en 50 (leído de `lectura.json`, no repetido) | `lectura.json` |
| Sorteo del §7 | No, tal como se corrió (K contra K) | 503 |
| Controles de cenit | Sin sustrato en F26; con insumo vacío sí dan rojo | 506, 515 |
| Candado | Sólo ante una edición sin commitear entre el tag y la lectura | 505 |
| C-via, C-cobertura | Sí (con 0 pasadas dan rojo; C-cobertura contó 8, 104 y 0 pasadas sin dato en F26, bajo el 10 %) | `c09`, `c03` |

## 6. Inventario de decisiones del eje y veredicto

Cómo lo armé (para que se pueda revisar la cobertura): lectura completa de `tasks/LOOP_OBJETIVOS.md` l. 570 a 800
(`0472cd95e`) y de `BLOQUE_ARRANQUE_S178.md` y `S179.md`; para S172 a S175,
`awk 'NR>=570 && NR<=1690' tasks/LOOP_OBJETIVOS.md | grep -n -i -E 'retro|leer_retro|pre-registro del paquete|VPR940|VPR946|VPR952|C-montaje|C-K|sorteo|controles de cenit|SIN SUSTRATO|decisi[oó]n 3|#940|#946|#952|#979'`
y lectura de las entradas que salieron (l. 1060 a 1064, 1095 a 1113, 1175 a 1186, 1303 a 1311); para los bloques S174 a
S177, `grep -n -i 'sorteo\|§7\|VPR940b-01\|l\. 409\|VPR952\|N-3'`. Una decisión que no contenga esas palabras se me pudo
escapar.

| # | decisión (sesión, fecha UTC) | veredicto | evidencia de esta sesión |
|---|---|---|---|
| 1 | Sello del pre-registro con R-1 a R-15 (S173, 2026-11-02 17:12) | SOSTENIDA | blob idéntico (`c12`); falta el hash en el tag (516) |
| 2 | Lecturas L1 a L5 del lector y VPR940-01, 07 y 10 (S173, 2026-11-03 y 11-04) | SOSTENIDA en L1, L2, L3, L5 y las tres aprobadas (previas a los datos); **L4 DEBILITADA** | 501 |
| 3 | Decisión 2 de S174: sorteo del §7 con la vía contra K (2026-11-05) | APLICADA DISTINTO (no se aplicó) | 503 |
| 4 | Decisión 3 de S174: caídas a K se tratan como K (implementada en S175) | SOSTENIDA, sin efecto aquí | 0 caídas (`c03`) |
| 5 | Decisión 4 de S174: un Tier A sin F26 en K es rojo | SOSTENIDA (leída en el código l. 629 a 630; no ejercitada; `volcanes_sin_f26_en_k` vacío en `lectura.json`) | lectura de código |
| 6 | Decisión 5 de S174: «separa» de VIIRS 750 se define al sellar V750-A | SOSTENIDA; consecuencia: el placebo de VIIRS 750 quedó a medias, cubierto por el techo de fila 4 | `lectura.json` |
| 7 | Decisión 6 de S174: tags y campos de C-montaje antes de D3 | APLICADA DISTINTO (se fijaron después) | 512 |
| 8 | Decisión 8 de S174 y #952: SIN SUSTRATO de cenit no bloquea; insumo vacío es rojo | SOSTENIDA | sección 5, `c09` |
| 9 | Despacho de D1 a D4 desde tags sobre `a7a6ae360` sin manifiesto previo (S176 y S177) | APLICADA DISTINTO respecto del título del §11; sin daño medido | 505; código idéntico (`c12`) |
| 10 | Elección de los tres días del K-gemelo: 2026-02-25, 03-10 y 03-25 (S177) | SOSTENIDA CON RESERVAS | 504 |
| 11 | Las pasadas de la vía sin K de disco se tratan como «sobran» (S177) | SOSTENIDA: en F26-V son 44, todas VIIRS 750, y la vía no publica en ninguna | `c03` |
| 12 | C-K verde sin excepciones (S178, commit `2bfc9164b`, antes de leer F26) | SOSTENIDA | 0 diferencias (`c03`); orden de commits (`c12`) |
| 13 | Caja B4 por volcán en el lector (S178, #979) | SOSTENIDA | sección 5 |
| 14 | C-montaje, opción A: comparar celda por celda (S178) | SOSTENIDA (más estricta que la propuesta) | `c08` en VIIRS 375 |
| 15 | C-montaje, opción 1: banda en VIIRS 375, post hoc (S178) | SOSTENIDA CON RESERVAS | 510 |
| 16 | Ref de lectura: tag de despacho más el lector de #979 más referencias congeladas; manifiesto desde esa ref (S178) | SOSTENIDA CON RESERVAS | 505; referencias con el sha256 del §7 (`c11`) |
| 17 | OSF por sha256 en bruto (S178) | SOSTENIDA | `c11` |
| 18 | Lectura con `--v750a-sellado no`, `--caja-v750 B4` y posición radiante en VIIRS 750 (R-3, R-12) | SOSTENIDA | reproducción idéntica (`c11`) |
| 19 | Veredicto MODIS: fila 4, DECIDE NICOLÁS (cambia sin las pasadas nombradas) | SOSTENIDA | `c03`: sin las 4 pasadas, SIN SUSTRATO (B 4) |
| 20 | Veredicto VIIRS 375: fila 6, NO SE CONTRADICE | SOSTENIDA CON RESERVAS | 501, 503, 509; a favor: 506, 507 |
| 21 | Veredicto VIIRS 750: fila 4, DECIDE NICOLÁS por V750-A sin sellar | SOSTENIDA, con la salvedad de 502 | `c03` |
| 22 | Verificador limpio de la lectura: «VÁLIDA CON RESERVAS (ninguna cambia un veredicto)» (S178) | SOSTENIDA CON RESERVAS: no vio 501 ni 502 | bitácora l. 625 a 627 |
| 23 | Usar los casos de F26-V para las cotas de la regla de reversión de VIIRS 375 (P10) | fuera de mi eje | seguimiento 3 |
| 24 | «Retro primero»: encender VIIRS si la retrospectiva no pierde protegidas (Nicolás, 2026-11-10 01:17) | fuera de mi eje. Dato para quien la audite: fuera de muestra las protegidas son Láscar (26 en VIIRS 375; 29 más 1 de Isluga en VIIRS 750) y, en el OSF de 2025, Láscar más 44 de otros tres volcanes en VIIRS 375 | `c03`, `c04` |

Pendientes de `docs/AUDIT_S175.md` (rama `claude/relaxed-almeida-d17378`, `37670d910`) que caen en mi eje: §8 decisión 3
(¿#952 cura 254?): cerrado, sí lo cura a nivel de función (`c09`). §8 decisión 4 (decisión 3 de S174): implementada y sin
efecto en esta lectura. §6, hallazgo 127 (el placebo del 1 % nunca entró al evaluador): no lo miré. §6, 308 («ninguna
protegida perdida» es vacuo en varios volcanes): vale igual para la retrospectiva y está dicho en el pre-registro; ver la
fila 24. §11.6: resuelto en S178 (anexo), no es de mi eje. V33B-02 (protegidas sólo del OCR anteriores al 2026-06-11): en
F26 decide la tabla sola, así que no entra a P1; es el mismo terreno del hallazgo 501.

## 7. PROPUESTAS PARA LOS PLANES (no implementadas)

1. **Antes de «mergea #974» (VIIRS 375).** Mostrarle a Nicolás las 3 pasadas del hallazgo 501 con la imagen de MIROVA
   (cabecera revisada, A61) y pedirle una frase sobre la exención N-3 en esta prueba. Si las imágenes muestran calor
   lejano, el veredicto queda como está y por escrito. Si muestran calor en el cráter, son 3 pérdidas de la vía con la
   posición que hoy publica. Atada a 501.
2. **Antes de «mergea #983» (VIIRS 750).** Decirle a Nicolás que el P2 de VIIRS 750 es EMPATE sin las pasadas elegidas
   porque K fallaba, y que P1 fuera de muestra es Láscar más una pasada de Isluga. Atada a 502 y a la fila 24.
3. **Agregar a la lectura un anexo rotulado post hoc** con lo que el pre-registro pide y el lector no calculó, y que sale a
   favor: el sorteo del §7 con la vía contra K (`c07`), la magnitud por cenit en R25 (`c04`) y el bajo 1 MW del OSF
   (`c10`). Con verificador limpio, porque son números de un solo auditor. Atada a 503, 506 y 507.
4. **Para la próxima prueba sellada** (sombra de los 34, Compuerta B, o el control del reemplazo de la historia):
   (a) armar el manifiesto antes del despacho, no al leer, e incluir todo archivo que el lector carga (los módulos de
   `frontend/` que usa el predicado, `auto_audit_weekly.py`, `volcanoes.yaml`, capas de la referencia); (b) elegir los días
   del control de K de modo que cubran los bloques donde K yerra, que se conocen al sellar; (c) exigir que cada control
   «puede fallar» se pruebe con una alteración real (por ejemplo, un K-gemelo con una publicación invertida), no con una
   cantidad que es constante por construcción; (d) correr el lector en modo control sobre datos de ensayo antes de
   despachar, como ya anota el bloque S179. Atada a 504, 505, 511 y 512.
5. **Para el plan de reemplazo de la historia (#981).** Antes de reemplazar 2025 en VIIRS 750, mirar una muestra de las 158
   pasadas que sólo publica la vía (91 en Isluga) y de las 234 que sólo publica K (145 en Cordón Caulle): el OSF no las
   juzga. Y escribir la regla para las 816 pasadas de K sin record de la vía dentro de las ventanas. Atada a los
   seguimientos 1 y 2.
6. **Si el lector se vuelve a usar** (V750-A sellado, o una relectura): que informe P1, P2 y M con y sin las pasadas
   nombradas (no sólo la fila); que liste toda protegida sólo del OCR por brazo; que cuente las alertas sin pasada tramo
   por tramo; que diga «0 noches limpias» cuando el denominador sea 0; que arme el nombre de la fila 6 con conteos por
   volcán y por tramo. Cada cambio con marca fechada y sin tocar el texto sellado. Atada a 501, 502, 508, 509 y 514.
7. **Devolver a la cola de decisiones** las tres del bloque S175 que se cayeron (hallazgo 515) y la lectura del §7.
8. **Guardar en un lugar que no venza** los datos de los A/B que C-montaje necesita (seguimiento 5), si se quiere poder
   repetir el control.
