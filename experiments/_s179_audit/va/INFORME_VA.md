# Verificación del frente A (MODIS), auditoría S179: informe del verificador VA

## 1. Encabezado

- Hora del servidor al escribir: 2026-11-11 01:16:37 UTC (cabecera `Date` de `gh api -i repos/MendozaVolcanic/VRP-chile`).
- Commit medido: código y datos de `main` en `438a60a1e` (extraídos con `git -c core.autocrlf=false archive` a
  `D:\vrp-trabajo\temporales\s179-audit\va\base\`; 347 blobs de código comparados con `git hash-object --no-filters`:
  0 distintos; sha256 de `latest_consolidado.csv` = `40b1b928...7fdf6` y de `registro_vrp_ocr.csv` = `7e54155a...1e75`,
  los declarados). Bitácora del loop en `0472cd95e` (copia en `D:\vrp-trabajo\temporales\s179-audit\loop\`, sha256
  igual al blob). Plan de #981 en `62ccb8830` (rama `origin/claude/s178-plan-reemplazo`, **fuera de main**).
  Control vivo: `origin/main` `16d78e3e0` (2026-11-11 00:52 UTC).
- Modelo y esfuerzo: Claude Opus 5.5 (`claude-opus-5-5`); el esfuerzo no lo declara el encargo y no lo puedo leer
  desde la sesión (SIN DATO).
- CARPETA: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s179_audit\va\`.
  Temporal: `D:\vrp-trabajo\temporales\s179-audit\va\` (194 MB).
- Caminos de error escritos antes de abrir los archivos citados:
  `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s179_audit\va\caminos.md`
  (sha256 del contenido `67d22031...3e30`, cerrado a las 01:06:33 UTC).
- Qué NO miré: el informe y el `hallazgos.csv` del auditor A, ni su `99_escribir_hallazgos_csv.py` (puede contener el
  texto de los hallazgos); `docs/PLAN_AUDITORIA_S179.md`; otras carpetas `experiments/_s179_*`. No re-corrí los scripts
  04, 05, 06, 07, 08, 11 a 16 del auditor (no los necesitaba para estas afirmaciones). No miré VIIRS, el tablero, el
  detector MODIS ni la retrospectiva con candado. No leí PDFs (no hay citas de papers en este frente).
- Llamadas a la API de GitHub: 4 de 5 (tres por la hora, una por el PR #937).

## 2. En una pantalla

1. Las nueve afirmaciones del auditor se sostienen en lo que miden: ocho CONFIRMADAS y una (403) CONFIRMADA con un matiz que baja su gravedad.
2. El plazo de la reversión pre-autorizada de MODIS se gasta en la erupción de Chillán. Van 11 de 29 protegidas en el snapshot y 13 en la vigilancia viva, todas de Chillán y de 6 a 26 MW. A ese ritmo la n.º 29 llega hacia el 20 de noviembre, no hacia el día 109 que estimó la regla.
3. La vigilancia diaria no ve una protegida que la vía calla cuando K tampoco la publica: 3 de las 11 están en ese caso. Ahí no hay issue diario. El audit semanal sí la marca, con hasta 7 días de atraso.
4. Revertir el PR B ya choca en 6 archivos sobre main y en 11 sobre las ramas de VIIRS (dos métodos distintos dan lo mismo). El hunk del flag se revierte limpio. La regla ya preveía choques en los documentos, no en las pruebas.
5. Si se aplica el plan de #981 tal como está, la vigilancia de la guardia queda en VIGILANCIA_CIEGA para siempre, porque el nulo pierde sus 167 pares. Lo demás (410, 412, DEC-10, DEC-15) se confirma con gravedad 1 a 2.

## 3. Veredictos por afirmación

Cada veredicto lleva sus dos preguntas del instrumento en el script citado (encabezado de cada `.py`).

### Afirmación 401: el plazo de la reversión pre-autorizada se agota hacia el 20 de noviembre y sólo con alertas de Chillán (auditor: 3)

**Veredicto: CONFIRMADO. Mi gravedad: 2. Es duplicado en el fondo de DEC-12 (la misma medición; 401 es el número, DEC-12 el juicio).**

- Código: `scripts/vigilancia_guardia_modis.py` l. 228-237 (438a60a1e): `vistas` cuenta protegidas posteriores al
  encendido con record de la guardia y cuyo record de producción no es K; `dentro_de_plazo` exige
  `orden <= PROTEGIDAS_OBJETIVO` (29). l. 520-521 sólo cambia `fase` a `plazo_cumplido`. La regla sellada, §4.6 (l. 305-314),
  TEXTO: «Hasta que la guardia **tenga record** de 29 protegidas nocturnas de MODIS posteriores al encendido, o 120 días
  desde el encendido, lo que ocurra primero». El camino «el plazo es el último de los dos» queda descartado.
- Medición propia, `01_vigilancia_base.py` / `.txt`: veredicto VERDE, `protegidas_vistas_en_guardia` 11, las 11 de
  NevadosDeChillan (2026-11-04 a 2026-11-09), MW de MIROVA de 6,37 a 25,84. Ventana 2026-10-19 a 2026-11-10;
  denominador: 25 pasadas nocturnas MODIS con alerta en la ventana, 11 protegidas posteriores al encendido.
- Otro camino (la vigilancia viva, referencia fresca de Actions): `06_vigilancia_viva_remota.txt`, de `origin/main`
  `16d78e3e0`. La corrida de las 22:53 UTC del 2026-11-10 da 13 vistas, y la serie sube 1, 3, 4, 6, 8, 11, 13 del 5 al
  10 de noviembre. Faltan 16. Al ritmo medido de 13 en 8 noches (1,6 por noche), la n.º 29 llega hacia el 20 o 21 de
  noviembre.
- Otro estrato, la referencia por mes (`01_vigilancia_base.txt`): protegidas MODIS nocturnas de MIROVA de marzo a
  octubre, sin Chillán, 41 en 245 días (todas de Láscar de marzo a junio, más una de Villarrica en septiembre). Eso da
  unas 20 en 120 días, así que sin Chillán el límite de 29 no se habría alcanzado. Chillán aportó 24 en octubre y 13
  hasta el 10 de noviembre.
- Control positivo, `09_plazo_agotado.py` / `.txt`: con 33 protegidas sintéticas (las 11 reales corridas +8 y +16 días),
  si la vía calla la n.º 5, el veredicto es REVERSION_CANDIDATA; si calla la n.º 33, es CANDIDATA_FUERA_DE_PLAZO. Pasada
  la n.º 29, la pérdida se sigue informando por issue, pero ya no está pre-autorizada.
- Matiz: la fecha del 20 de noviembre es una proyección lineal y supone que Chillán sigue igual. «Sólo con alertas de
  Chillán» es un hecho medido hasta hoy, no una garantía hacia adelante. Mi gravedad es 2 y no 3 por una razón. Agotar
  el plazo no apaga la detección: sólo quita la pre-autorización, y la decisión pasa a Nicolás con issue el mismo día
  (l. 336-337 y el workflow, caso `CANDIDATA_FUERA_DE_PLAZO`).

### Afirmación 402: la vigilancia da VERDE cuando la vía pierde una protegida que K tampoco publica o que la guardia no miró (3 de 11) (auditor: 3)

**Veredicto: CONFIRMADO. Mi gravedad: 2.**

- Código: `calla(p)` exige `guardia_pub is True` (l. 239-240). La reversión exige además `prod_via is True` (l. 244-245).
  `sin_record` exige `guardia_pub is True` y `prod_pub is None` (l. 318-319). Ningún disparador mira el caso
  «la guardia no publica, o no tiene record, y la vía calla». Esas pasadas sólo quedan en
  `protegidas_sin_publicar_produccion` (l. 538), un campo del JSON. El workflow
  `.github/workflows/vigilancia-guardia-modis.yml` (438a60a1e) no imprime ese campo en ningún issue, y con VERDE va al
  caso `*) echo "sin issue"`.
- Medición, `02_casos_sinteticos.py` / `.txt`, sobre las 11 protegidas reales:
  - A, la base: VERDE.
  - B, la vía calla la del 11-09 00:55 (K no la publica): VERDE.
  - C, control positivo, la vía calla una que K publica: REVERSION_CANDIDATA.
  - D, la guardia sin record y la vía calla: VERDE.
  - F, la guardia publica y producción no tiene record: INVESTIGAR.
  - G, la vía calla las 3 que K no publica: VERDE.
- «3 de 11»: medido en `01_vigilancia_base.txt`. K (la guardia) no publica 3 de las 11 protegidas posteriores al
  encendido que la vía sí publica: Chillán 2026-11-07 07:25 (9,23 MW), 2026-11-09 00:55 (6,37 MW) y 2026-11-09 02:35
  (7,2 MW). La guardia tuvo record de las 11, así que en esta ventana el caso «no la miró» es 0 de 11.
- Por qué baja a 2: la regla define así el disparador (§4.3, TEXTO: «una protegida que MIROVA publica, la guardia K
  publica y producción (la vía) **tiene record y no publica**»). La pérdida absoluta sí la ve otro control, el audit
  semanal: re-corrí el script 09 del auditor sobre mi base (`03_rerun_audit_semanal_auditor.py` / `.txt`). Con la vía
  callando la pasada del 11-07 07:25 aparece el flag «alerta protegida sin publicar ... (detector VIA_MODIS ...)», que
  degrada el audit a FUERA_DE_BANDA. Sin el cambio no hay flag (control). El audit corre los lunes a las 09:00 UTC
  (`audit-weekly.yml` l. 11), así que el atraso llega a 7 días, sin pre-autorización.

### Afirmación 403: revertir el PR B por git revert ya choca (6 archivos sobre main y 11 tras encender VIIRS); el flag se revierte limpio (auditor: 3)

**Veredicto: CONFIRMADO. Mi gravedad: 2.**

- Identidad: `499935c37` es «Merge pull request #934 from MendozaVolcanic/claude/s173-modd-flip», 2026-11-02 17:18:16
  UTC, con primer padre `438a010ab` (`git log -1`; también `insumos\pr_934.json`, `mergeCommit.oid`). Las ramas
  `origin/claude/s177-b1-v375` = `bbbe2068d` y `origin/claude/s178-b2-sobre-b1` = `e68819484` son las mismas que midió el
  auditor.
- Re-corrida del auditor: su salida `a\10_revert_simulado.txt` (merge-tree) da 0, 6, 11 y 11 conflictos.
- Otro camino, mío: `04_revert_por_parche.sh` / `.txt`. Aplica al revés, archivo por archivo, el parche de B
  (34 archivos) sobre un índice temporal con `git apply -R --cached --check`, sin 3-way. Resultados:
  - Control (destino = el propio merge): 0 archivos que no aplican.
  - Sobre `438a60a1e`: 6 (CLAUDE.md, ficha, MIROVA_DIVERGENCES, MISSION, la regla misma y
    `tests/test_guard_modis_codigo_mirova_encendido_s172.py`).
  - Sobre B1 y B2: 11 cada una (además, 5 pruebas que tocan las ramas de VIIRS).
  - En los cuatro destinos, el hunk del YAML (el flag) se revierte limpio.
- Por qué 2 y no 3: la regla ya preveía esos choques, salvo los de pruebas. §4.3, ronda 4, TEXTO: «puede chocar en las
  marcas A113 que B agrega al inicio de `docs/MISSION.md`, `docs/MIROVA_DIVERGENCES.md` y `CLAUDE.md` [...] en la
  ficha, en esta regla». Y manda resolverlos «a mano, sin esperar a nadie». Lo nuevo son las pruebas en conflicto
  (1 sobre main, 6 sobre B1 y B2), que la regla no nombra. Eso puede atrasar una reversión que debe hacerse el mismo
  día, pero el flag, que es lo que cambia la detección, sale limpio. La regla dice además que «hoy es limpio
  (simulado el 2026-11-02 [...] 0 conflictos)». Esa frase ya no es cierta.

### Afirmación 405: el reemplazo de la historia (#981) dejaría la vigilancia de la guardia en VIGILANCIA_CIEGA todos los días (nulo sin pares) y el plan no lo trata (auditor: 2)

**Veredicto: CONFIRMADO (el plan está fuera de main). Mi gravedad: 2.**

- Código: el nulo empareja records de la guardia en `[encendido - 14 d, encendido)` con records de producción que
  **no** son de la vía (l. 297-307). Con 0 pares, `sin_medir` (l. 312) se convierte en aviso (l. 374-379), y el aviso
  vuelve VIGILANCIA_CIEGA cualquier VERDE (l. 527-528). La ventana del nulo es fija: está atada al encendido, que es el
  menor `processed_utc` de la vía (l. 145).
- El plan (`docs/PLAN_REEMPLAZO_HISTORIA_VIA_S178.md` en `62ccb8830`, l. 142-147, TEXTO) dice: «MODIS: `desde =
  2025-02-15`, `hasta = 2026-11-02`, y sólo se tocan records SIN `via_codigo_mirova` (K)». Es decir, reemplaza justo
  los records K que forman los pares del nulo. Busqué «nulo», «vigilancia_guardia» y «guardia_modis» en los 312
  renglones del plan: aparece sólo «guardia_k_viirs.yaml» (l. 61). El plan no trata el nulo.
- Medición, `05_nulo_tras_reemplazo.py` / `.txt`: sin simulación, 167 pares y 0 distintas (control). Con los 339
  records MODIS de producción anteriores al encendido marcados como de la vía: 0 pares, `sin_medir` y el aviso del
  nulo. Con un record del reproceso (`processed_utc` del 2026-11-09), el encendido sigue en 2026-11-02 20:11:43, porque
  `reemplazar_ventana_reproceso.py` l. 73-76 hereda sólo `first_processed_utc`. Así que la ventana no se mueve y el
  aviso no se va solo.
- Límite: no medí qué publicaría la vía en las pasadas reemplazadas. Por eso el efecto sobre `borde_del_encendido`
  queda SIN DATO.
- Gravedad 2: un aviso permanente no tapa una reversión (l. 527-528), pero cada día comenta el issue de vigilancia
  ciega, y eso entrena a ignorarlo.

### Afirmación 410: el único control de que MODIS sigue vivo volcán por volcán está dentro de la vigilancia de la guardia (auditor: 2)

**Veredicto: CONFIRMADO, con un matiz. Mi gravedad: 2.**

- Simulación, `08_modis_muerto_en_un_volcan.py` / `.txt`: borro en memoria los 12 records MODIS de Láscar desde el
  2026-11-05. Resultado por control:
  - Healthcheck del NRT (`nrt-healthcheck.yml` l. 40-90): sin stale. Mira la edad del último record del volcán con
    cualquier sensor.
  - `vigilar_plataformas.py`: `ok`. Cuenta por plataforma sumando los 11.
  - `auto_audit_weekly.py::cobertura_de_ventana` (l. 346-361): sin aviso. Cuenta días con cualquier record (l. 829).
  - Sólo `vigilancia_guardia_modis.avisos_produccion` (l. 354-355) avisa: «producción de Lascar en MODIS no produce
    hace 6 días».
  - Control: si borro todo, avisan los cuatro.
- Otros caminos revisados:
  - `vigilancia_sombra.py` l. 478-482 quita MODIS de su frescura de producción desde que existe la vía.
  - `vigilancia_guardia_viirs.py` l. 197-198 sólo mira VIIRS.
  - El paso del NRT «Revisar errores de MODIS en el log» sólo ve excepciones, no la ausencia de gránulos (regla §4.4 (a)).
- Matiz: el audit semanal sí avisa «alerta protegida sin record nuestro» cuando MIROVA alerta en ese volcán
  (`03_rerun_audit_semanal_auditor.txt`, caso A10). En un volcán tranquilo no hay nada. La regla lo sabe: §4.7 punto 3
  dice que la guardia «cubre la frescura de MODIS que la vigilancia de K deja de mirar».

### Afirmación 412: la regla sellada no registra los cambios que S175 le hizo a su instrumento (#959) (auditor: 1)

**Veredicto: CONFIRMADO. Mi gravedad: 1.**

- `scripts/vigilancia_guardia_modis.py` l. 47-60 (TEXTO) declara los cambios de S175, «aprobadas por Nicolás el
  2026-11-07». Son cuatro:
  - La reversión exige el record de la vía.
  - «el plazo de 29 protegidas, Muy Bajo y la sobre-publicación cuentan sólo pasadas de la vía (V1-01)».
  - La frescura de la vía se mide por volcán.
  - Las caídas a K son aviso y llevan a VIGILANCIA_CIEGA.
- El instrumento entró con `71ecc61b0` (#959, 2026-11-08 15:23 UTC). La regla sólo recibió después `1b66b7490` (#956),
  cuya única marca (l. 8) es la del hallazgo 154. `grep` de «959», «V1-01», «caída», «sin_grilla», «prod_via» y
  «DIAS_AVISO» en la regla: 0 coincidencias pertinentes.
- Diferencia concreta con el texto sellado: §4.6 dice «"Tener record" es lo que cuenta el instrumento». Hoy el
  instrumento excluye además las pasadas cuyo record de producción es K (l. 228-229). Y la lista de avisos de §4.4
  («Vigilancia ciega») no incluye las caídas a K.
- Efecto hoy: 0 caídas a K (`01_vigilancia_base.txt`, `caidas_a_k` vacío en el JSON del auditor y en el vivo). Por eso
  la gravedad es 1.

### DEC-10: decisión D7 (al día siguiente de una reversión, apartar los records de la vía) DEBILITADA en su premisa (auditor: 2)

**Veredicto: CONFIRMADO. Mi gravedad: 1.**

- La premisa de D7 (regla l. 92, TEXTO): «El revert no toca `data/`: el NRT re-escribe con K sólo 8 fechas hacia
  atrás». El código no la sostiene:
  - `pipeline/store.py` l. 695-706 (438a60a1e) reemplaza un record existente sólo con `overwrite` o con el paso de NRT
    a estándar.
  - `nrt.yml` (l. 185, 201) agrega `--overwrite` sólo si el despacho manual lo pide.
  - El cron no re-escribe.
- La propia regla lo corrige desde el 2026-11-07 en la marca A113 de l. 8 (TEXTO): «el "día después" de una reversión
  no queda re-escrito con K por el NRT».
- Por qué 1: la acción de D7 (apartar y reponer con K en un PR con tag) sigue siendo la correcta y sólo crece su
  alcance. Ahora son todos los records de la vía, no sólo los de más de 8 días. Y quien lea la regla desde arriba ve
  la corrección antes que D7.
- Matiz que agrego: tras un revert, los records recientes de la vía que todavía son NRT se re-escriben con K cuando
  llega su estándar (mediana 13,8 h según la marca). Así, la última noche queda mezclada por otra vía que la que
  supone D7. SOSPECHA: no la medí.

### DEC-12: decisión §4.6 (plazo de 29 protegidas o 120 días), juzgada DEBILITADA (auditor: 3)

**Veredicto: CONFIRMADO. Mi gravedad: 2. Se funde con 401.**

- La justificación de §4.6 (TEXTO): «con 29, una pérdida de una de cada diez se ve con 95 %, 1 - 0,9^29 = 0,953».
  Además, «Ritmo esperado [...] a ese ritmo las 29 llegan cerca del día 109». Las dos premisas fallan en los datos de hoy:
  - El ritmo: ver 401. Las 29 llegarán hacia el día 18.
  - La potencia supone que K publica la protegida, porque sólo entonces una pérdida dispara (402). K publicó 8 de 11.
    Con esa fracción, la potencia baja a 0,888 (`01_vigilancia_base.txt`: 1 - (1 - 0,1 × 0,73)^29). Además, las 29
    vendrán de una sola erupción y de un solo volcán, correlacionadas y de 6 a 26 MW. El riesgo que declara el propio
    instrumento (l. 8-9: «una señal débil o de borde de barrido que K publica podría quedar callada») queda fuera de
    esa muestra.
- Por qué 2 y no 3: vencido el plazo, una pérdida sigue abriendo issue el mismo día, como CANDIDATA_FUERA_DE_PLAZO
  (`09_plazo_agotado.txt`). Lo que se pierde es la pre-autorización, no la detección. Además, (i) Muy Bajo y (ii)
  sobre-publicación siguen contando 120 días (l. 252, 265-266).

### DEC-15: #937 (ablación de MODIS en Actions) está en main sin entrada de bitácora que registre el merge ni la frase de Nicolás (auditor: 1)

**Veredicto: CONFIRMADO. Mi gravedad: 1.**

- `f4ec1061d` es «Merge pull request #937 from MendozaVolcanic/claude/s173-cenit-modis», 2026-11-03 06:15:15 UTC, y es
  ancestro de `438a60a1e`.
- La bitácora en `0472cd95e`, l. 1399-1406 (TEXTO), dice: «Sin despachar; merge pendiente de frase» y «Próximo: CI del
  #937 en verde y frase para mergear y despachar». `grep` de «#937» en todo `LOOP_OBJETIVOS.md`: sólo esas líneas.
  La entrada siguiente que toca el tema (09:39 UTC) dice «Ablación MODIS verificada (run 41588951267)», sin frase.
- El PR (`07_pr937.txt`, `gh pr view 937`): `mergedBy` MendozaVolcanic, 0 comentarios, 0 revisiones. Esa cuenta es la
  misma que usan las sesiones, así que el autor del merge no prueba que fuera Nicolás.
- `git grep "#937"` en `tasks docs experiments` de 438a60a1e: 0. En 0472cd95e: sólo el README e INFORME del cenit,
  que tampoco traen la frase.
- Agrego: el despacho del workflow con NASA (run 41588951267, «Corrida del 2026-11-03 06:17 UTC», README del cenit
  l. 58) tampoco tiene frase registrada, y la propia entrada l. 1406 decía que la necesitaba.
- Riesgo bajo: `.github/workflows/s173-cenit-modis.yml` es sólo `workflow_dispatch`, de lectura, y no escribe en `data/`.

## 4. Hallazgos propios (VA-01 en adelante)

No encontré defectos nuevos fuera de lo que ya cubren las nueve afirmaciones. Lo que medí de más va fundido arriba:

- K no publica 3 de 11 protegidas que la vía publica (en 402 y DEC-12).
- La potencia efectiva es 0,888 (en DEC-12).
- Las pruebas en conflicto del revert no las nombra la regla (en 403).
- El despacho de #937 tampoco tiene frase (en DEC-15).
- Hay una mezcla de K en la última noche tras un revert (en DEC-10, como SOSPECHA).

Los numero para que se puedan filtrar:

- VA-01: la regla dice que el revert de B «hoy es limpio». Ya no lo es, y la regla no nombra las pruebas en conflicto
  (fundido con 403).
- VA-02: tras un revert, el paso de NRT a estándar re-escribe con K la última noche de la vía (fundido con DEC-10).
  SOSPECHA, gravedad 1.

## 5. SEGUIMIENTOS (fuera de mi eje)

- Con el plan de #981, `primera_observacion_via` del JSON de la guardia saltaría al inicio de la historia reemplazada
  (`05_nulo_tras_reemplazo.txt`: 2026-05-01 con un record de mayo). Es un campo informativo. El plan dice que la marca
  del tablero desaparece a propósito. Confianza: CONFIRMADO para el campo, sin efecto medido en disparadores.
- La vigilancia diaria usa la referencia fresca de Mirova-v1 y la de esta auditoría usa el snapshot del repo. La
  diferencia del día 10 fue 11 contra 13 vistas. No cambia ningún veredicto.

## 6. VERIFICADO LIMPIO

- La base de medición es fiel a 438a60a1e: 347 blobs con `git hash-object --no-filters` iguales y los sha256 de la
  referencia iguales. Vara: el blob del commit. (Un primer `git archive` con `core.autocrlf=true` cambió los CSV a
  CRLF y su sha256. Se descartó y se rehízo con `-c core.autocrlf=false`.)
- El script del auditor (02) y el mío (01) dan el mismo veredicto (VERDE), los mismos 167 pares del nulo, 11 vistas y
  551/359/48.689 records y filas. Vara: re-ejecución sobre una base independiente.
- El control positivo de la vigilancia funciona: callar una protegida que K publica da REVERSION_CANDIDATA
  (`02_casos_sinteticos.txt`, caso C). Y la protegida sin record de producción da INVESTIGAR (caso F).
- La protegida n.º 5 sigue pre-autorizada aunque el plazo ya esté cumplido al evaluar (`09_plazo_agotado.txt`).
- El encendido no se mueve con records de reproceso, porque `processed_utc` no se hereda (`05_nulo_tras_reemplazo.txt`).

## 7. SIN DATO

- El efecto del reemplazo de #981 sobre `borde_del_encendido`: no sé qué publicaría la vía en las pasadas reemplazadas
  sin los artefactos D2, D4 y P4, que viven fuera del repo.
- El esfuerzo con que corrí: no lo puedo leer desde la sesión.
- La mezcla de K en la última noche tras un revert (VA-02): no la simulé.

## 8. FUERA DE ALCANCE

VIIRS (guardia, reglas y B1/B2 salvo como destino del revert), el tablero, la retrospectiva con candado y el detector
MODIS mismo.
