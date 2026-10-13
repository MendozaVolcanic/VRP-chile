# Meta-auditoría S150, frente F3: defectos de la vara descubiertos tarde, aplicados hacia atrás

> Auditor F3, 2026-10-09. Sólo lectura del repositorio: no se tocó `pipeline/`, `frontend/`, `data/` ni
> ningún documento salvo este. Repo en `main` `13f5bb0dd` (2026-10-09 16:10 UTC). Scripts y salidas en
> `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s150_meta_audit\F3\`
> (`r1` a `r10`, cada uno con su `*_salida.txt`). Las ramas de A/B se leyeron con `git archive` hacia el
> scratchpad de la sesión, fuera del árbol. Ningún número de este informe está transcrito de otro documento
> sin decirlo: lo que no medí yo, lo cito como cita.

## 0. En una pantalla

La pregunta del frente: qué conclusiones **vigentes** se midieron con una referencia de MIROVA que hoy
sabemos defectuosa (A119, el OCR con la imagen de otra pasada de S150, #535 de A104, el OSF de A105, los
GeoTIFF de A106, la copia atrasada), y si al corregir la vara cambia el veredicto.

**Lo principal, en lenguaje de volcán.** La referencia de MIROVA tiene dos canales: la tabla `latest.php`,
que MIROVA arma pasada por pasada, y el OCR, que lee la imagen que MIROVA publica por volcán. Cuando sólo el
OCR trae una alerta, muchas veces es una pasada de Suomi NPP que la tabla nunca listó, al borde del barrido,
y puede llevar la clase y la distancia de otra pasada. Tratar esas filas como "MIROVA vio calor en el
cráter" fabrica pérdidas que no existen. Medido sobre la decisión que hoy espera a Nicolás (el recall de la
conectiva `max` en VIIRS 375, abril a agosto):

- **Todas las pérdidas de 0,20 MW o más que se le atribuían a `max` salen de filas sólo OCR** (8 de 8: seis
  de Suomi NPP, dos de NOAA-21). Con la vara corregida, `max` conserva **119 de 119** alertas de 0,5 MW o
  más, y el control también. La tabla publicada decía 94,4 % y 96,9 %.
- **El costo bajo 0,10 MW no cambia**: bajo 0,05 MW `max` publica 30 de 46 (65,2 %) y entre 0,05 y 0,10 MW
  131 de 157 (83,4 %). La pregunta 1b de `AUDIT_S150` queda confirmada y más limpia: es sólo ese tramo.

Además: **el consolidado remoto de Mirova-v1 volvió a perder filas en silencio** (tercera vez, entre el
2026-10-05 22:37 y el 2026-10-06 02:57 UTC): 207 filas, 8 de ellas alertas, entre ellas la alerta MODIS de
Láscar del 2026-04-18 (2,06 MW), en un sensor que tiene 77 alertas de sustrato desde marzo. Y **el
instrumento que avisa de la calidad de la referencia** (`scripts/calidad_referencia_mirova.py` y la regla
A119) sobrestima un defecto (el "86 % en enero" es Tupungatito ausente: sin él, 97 a 100 %) y omite cuatro.

**Conteo** (detalle en §3): conclusiones vigentes tocadas por cada defecto: A119 9, OCR de otra pasada 6,
#535 1, OSF 2, GeoTIFF 3, copia atrasada o remoto que pierde filas 4. Re-medí 7; en ninguna cambia la
dirección del veredicto, en una cambian los números que se le muestran a Nicolás (la tabla por tramo) y en
una cambia la regla (enero).

## 1. Cómo busqué (para que la cobertura se pueda auditar)

1. **Quién consume la referencia.** `grep -rlE "cargar_referencia_unificada|load_mirova_alertas|registro_vrp_ocr|banco_paridad"`
   sobre `experiments/`, `scripts/` y `pipeline/`: 56 carpetas de sesión de S126 a S150 más 8 scripts de
   `scripts/`. Leí el etiquetador común (`scripts/banco_paridad.py:275-299`), el cargador
   (`scripts/referencia_mirova_unificada.py`) y el loader (`pipeline/mirova_csv_loader.py:125-203`): ninguno
   filtra el OCR por fecha ni por satélite.
2. **Qué conclusiones están vigentes.** Reglas A97 a A119 de `CLAUDE.md` del proyecto y las rebajas con
   número de A10, A23, A54, A82, A83, A99; encabezados D1 a D32 de `docs/MIROVA_DIVERGENCES.md` (cuerpo de
   D2 y D17); `docs/AUDIT_S149.md` §0 a §4; `docs/AUDIT_S150.md` entero; `docs/S150_RESULTADO_MESES.md`;
   `docs/S150_IMAGENES_SNPP.md`; `docs/S150_ALERTAS_DEBILES_MAX.md`; `experiments/_s150_ab_d22/PREREGISTRO.md`;
   `tasks/BLOQUE_ARRANQUE_S150.md`; la memoria `project_tiering_osf_v2_5.md`.
3. **Para cada una, la vara leída en su script, no en su texto**: ventana y canal de referencia en
   `recall_por_magnitud.py`, `armar_tabla.py`, `banco_noches.py` (salida guardada), `linea_base_post535.py`
   (su `RESULTADOS.md`), `medir_f05.py`, `estructura_del_residual.py`, `conteo_tif.py`, `g2.py` de S144,
   `auto_audit_weekly.py`, `clases_rechazo.py`.
4. **Qué NO cubrí**: las conclusiones de `AUDIT_S121` a `AUDIT_S138` que no subieron a `CLAUDE.md` ni al
   catálogo; las divergencias medidas con la batería del Apéndice A del paper (D19, D21, D22, D25, D26, D30),
   que no usan la referencia de MIROVA y quedan fuera de este eje; la historia de la auditoría semanal
   (`data/audit_continuous/history.jsonl`).

## 2. Hallazgos, lo peor primero

### F3-1. La tabla de recall por tramo que decide la pregunta 1b mezcla filas sólo OCR; con la vara corregida, todas las pérdidas fuertes de `max` desaparecen

- **ARCHIVO:LÍNEA**: `experiments/_s149_prereg_invierno/recall_por_magnitud.py:12` (`v["control"]["lab"] == "pos"`,
  la etiqueta de `scripts/banco_paridad.py:290-291`, que marca positiva cualquier pasada con ALERTA de la
  tabla o del OCR); la tabla que se le muestra a Nicolás está en `docs/S150_RESULTADO_MESES.md` §2.
  SCRIPT:SALIDA: `experiments/_s150_meta_audit/F3/r1_recall_tramo_vara_corregida.py` → `r1_salida.txt`,
  `r1b_f_sobre_b.py` → `r1b_salida.txt`.
- **QUÉ PASA**: una fracción grande de las "alertas de MIROVA" de cada mes son filas que sólo trae el OCR
  (abril 51 de 206, mayo 98 de 296, junio 74 de 238, julio 37 de 155, agosto 34 de 125, en VIIRS 375). Antes
  del 2026-06-13 A119 dice que no deciden; después, las de Suomi NPP pueden traer clase y distancia de otra
  pasada. El script las cuenta igual que las de la tabla, sin mirar fecha ni satélite.
- **Medición** (las dos preguntas): (1) si la vara metiera positivos falsos, ¿lo vería? Sí: tres varas sobre
  la misma tabla por pasada, L0 completa, L1 tabla sola, L2 = tabla sola antes del 2026-06-13 y tabla más OCR
  después salvo las sólo OCR de Suomi NPP. (2) Si el instrumento estuviera muerto, ¿se vería? Sí: L0
  reproduce al número los cinco `recall_por_magnitud_*.txt` publicados (abril 206, B 196, F 189; mayo 296,
  288, 276; junio 238, 231, 221; julio 155, 153, 150; agosto 125, 120, 110) y el agregado del §0 de
  S150 (F conserva 946 de 988 con L0, 684 de 708 con L1). Control positivo: L1 quita 34 positivos en
  agosto. Denominador: pasadas nocturnas de VIIRS 375 de los 11 Tier A con alerta y magnitud de MIROVA,
  referencias congeladas por mes (`_congelado/<mes>`), 2026-04-01 a 2026-08-27, runs 35639417826 más
  37823348991, 35599902448, 35675490175, 35728617326, 35759688167.

  | tramo de MIROVA (abril a agosto, VIIRS 375) | L0 completa: n, B, F | L2 corregida: n, B, F |
  |---|---|---|
  | bajo 0,05 MW | 57, 87,7 %, 66,7 % | 46, 89,1 %, **65,2 %** |
  | 0,05 a 0,10 | 200, 94,0 %, 85,0 % | 157, 93,0 %, **83,4 %** |
  | 0,10 a 0,20 | 232, 98,3 %, 96,6 % | 184, 98,9 %, 97,8 % |
  | 0,20 a 0,50 | 336, 99,1 %, 98,2 % | 250, 100 %, 99,2 % |
  | 0,50 o más | 195, 96,9 %, 94,4 % | 119, **100 %**, **100 %** |

  Sobre lo que B publica, las pérdidas de F con MIROVA de 0,20 MW o más son 8 con L0 y **las 8 son sólo OCR**:
  las cinco de Suomi NPP ya explicadas en `docs/S150_IMAGENES_SNPP.md`, Puyehue Cordón Caulle 2026-05-05
  05:54 (Suomi NPP, 0,23 MW) y dos de NOAA-21 en Lastarria (2026-06-17 05:06, 0,46 MW; 2026-08-04 05:06,
  0,20 MW). Con L1 son 0; con L2 quedan sólo esas dos de NOAA-21.
- **CÓMO SE VE EN EL DASHBOARD**: invisible. Lo que tuerce es la decisión de adoptar `max` en la réplica: la
  fila "0,50 o más" de la tabla publicada sugiere que `max` cuesta alertas fuertes, y no las cuesta.
- **CÓMO REPRODUCIRLO**: `python experiments/_s150_meta_audit/F3/r1_recall_tramo_vara_corregida.py --tmp <dir fuera del repo>`
  y después `python experiments/_s150_meta_audit/F3/r1b_f_sobre_b.py <mismo dir>`.
- **CONFIANZA**: CONFIRMADO (medido, con el control L0 al número). Que las dos de NOAA-21 tengan el mismo
  mecanismo que las de Suomi NPP es **SOSPECHA**: no miré la cabecera de sus imágenes.
- **GRAVEDAD 4**: es la tabla con que Nicolás decide el recall de la réplica. El veredicto de `AUDIT_S150`
  (1b: "la pregunta es sólo el tramo bajo 0,10 MW") **se mantiene y sale reforzado**; lo que está mal son los
  números de las filas altas de la tabla publicada.

### F3-2. El consolidado remoto de Mirova-v1 perdió 207 filas en silencio por tercera vez; "la referencia es el remoto del dueño" no protege de esto

- **SCRIPT:SALIDA**: `experiments/_s150_meta_audit/F3/r5b_filas_perdidas.py` → `r5b_salida.txt`, más la
  traza por commit de `latest_consolidado.csv` (comando abajo).
- **QUÉ PASA**: entre la copia que escribió la auditoría semanal (commit `80b358f6d`, 2026-10-05) y la copia
  horaria de hoy faltan 207 filas del consolidado (196 RUTINA, 8 ALERTA_TERMICA, 3 FALSO_POSITIVO),
  repartidas de enero a octubre y en los 11 volcanes; 0 filas cambiaron de tipo. Por los commits de
  `latest_consolidado.csv`, la caída ocurrió entre `2fbc42a87` (2026-10-05 22:37, 41.333 líneas, la alerta
  MODIS de Láscar del 2026-02-14 presente) y `283d744e2` (2026-10-06 02:57, 41.170, ausente). Es el mismo
  patrón que H201 de `docs/audit_s139/MAPA_BASES_MIROVA_V1.md` §0.2 (dos pérdidas previas). De las 8 alertas,
  4 las recupera el respaldo del 2026-04-08 (comprobado con `grep` en el respaldo), 1 es diurna, y **3
  nocturnas quedan sin respaldo de tabla**: Láscar MODIS 2026-04-18 01:50 (2,06 MW; sobrevive sólo en el OCR
  con 2,0 MW truncado y es anterior al 2026-06-13, así que bajo A119 estricta desaparece), Isluga VIIRS 375
  2026-08-05 05:42 (0,34 MW) y Puyehue Cordón Caulle VIIRS 750 2026-08-18 05:48 (0,64 MW), estas dos sin
  fila OCR.
- **Medición**: (1) si el remoto perdiera filas, ¿lo vería? Sí, comparo llave por llave dos copias del mismo
  remoto en dos fechas. (2) Si la clave estuviera mal, ¿se vería? Sí: 41.121 de 41.328 llaves coinciden; y
  la fila de Láscar se comprobó a mano con `grep` en los dos CSV crudos.
- **CÓMO SE VE EN EL DASHBOARD**: no lo vi en la línea de MIROVA de Láscar: `data/mirova/Lascar.json` todavía
  trae 2026-04-18 01:50 (probablemente por el OCR que S150 sumó a esa línea; no lo comprobé para las otras
  dos). Lo que sí tuerce: toda referencia que se congele del remoto desde el 2026-10-06 (el A/B
  `vent_anchored` contra `vrp_max` pendiente, un despacho MODIS en los 11 volcanes) pierde esas alertas.
  Las referencias congeladas de S149 sí las tienen (comprobado en `_congelado/abril` y `_congelado/agosto`);
  la de Chillán (`experiments/_s150_ndc/_congelado_ndc`, bajada el 2026-10-08) es posterior a la pérdida,
  pero las 7 filas perdidas de su ventana son RUTINA de otros volcanes.
- **CÓMO REPRODUCIRLO**: `python experiments/_s150_meta_audit/F3/r5b_filas_perdidas.py`; y
  `for h in $(git log --format=%h --since=2026-10-04 -- latest_consolidado.csv); do git show $h:latest_consolidado.csv | grep -c "2026-02-14 01:40:00.*Lascar,MODIS"; done`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD 3**: MODIS sólo tiene sustrato de recall en Láscar (77 alertas desde marzo, `AUDIT_S149` §0);
  perder una alerta en silencio en la vara de la próxima prueba es justo el error que A119 quería evitar.

### F3-3. El instrumento que avisa de la calidad de la referencia sobrestima un defecto y omite cuatro

- **ARCHIVO:LÍNEA**: `scripts/calidad_referencia_mirova.py:18-28` (HITOS); `CLAUDE.md` del proyecto,
  l. 1492-1494 (A119: "cobertura nocturna 86 % en enero, 95 % en febrero"; "0 alertas MODIS dependen del
  OCR"); `scripts/banco_paridad.py:72` (`INICIO_DEFECTO = "2026-03-01"  # ... OCR confiable desde marzo`) y
  `:285-291` (etiqueta positiva cualquier ALERTA, sin fecha ni satélite).
  SCRIPT:SALIDA: `r6_cobertura_enero.py` → `r6_salida.txt`.
- **QUÉ PASA**:
  1. El "86 % en enero" es Tupungatito, que no existe en la tabla antes del 2026-02-14, contado en el
     denominador. Medido: enero (desde el 11) 90,5 / 90,9 / 88,3 % con 11 volcanes y **99,5 / 100 / 97,1 %**
     sin Tupungatito (MODIS / VIIRS 375 / VIIRS 750); febrero 95,1 a 95,8 % contra **99,3 a 100 %**. Control:
     marzo da 100 % con los dos denominadores. Lo había dicho S149 (frente B, B-03, citado en `AUDIT_S149.md`
     §1) y no se propagó ni a la regla ni a los hitos (A113). La consecuencia práctica: "enero no se usa" saca
     de la vara noches que la tabla sí cubre; lo que sí sigue valiendo es que **antes de abril la tabla expone
     menos gránulos VIIRS por noche**, así que las tasas por pasada no se comparan.
  2. Faltan en los hitos: NOAA-21 ausente de la tabla antes del 2026-04-09 (`AUDIT_S149.md` §2, no
     re-medido por mí); la fila sólo OCR de Suomi NPP con imagen de otra pasada (S150); la pérdida de filas
     del remoto (F3-2).
  3. "0 alertas MODIS dependen del OCR" ya era falso en S149 (`AUDIT_S149.md` §1) y hoy, por F3-2, la
     alerta nocturna de Láscar del 2026-04-18 depende sólo del OCR (medido: 2 alertas MODIS sin fila de
     tabla, ésa y una diurna de 15 MW del 2026-05-05 19:30).
  4. `banco_paridad` avisa pero sigue etiquetando con el OCR anterior al 2026-06-13, y su ventana por defecto
     parte el 2026-03-01 con un comentario ("OCR confiable desde marzo") que contradice A119.
     `AUDIT_S149.md` §2 ya pedía que la separación quedara dentro del etiquetador.
- **Medición** (r6): (1) si la tabla de enero estuviera de verdad incompleta, la cobertura sin Tupungatito
  también bajaría; no baja. (2) Control positivo: marzo 100 % con ambos denominadores. Noche: hora UTC antes
  de 10:42 o desde 22:42 (definición de `MAPA_BASES_MIROVA_V1.md` §2). Error propio corregido en la misma
  corrida: la primera versión contaba enero desde el día 21; está arreglado y la salida guardada es la buena.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `python experiments/_s150_meta_audit/F3/r6_cobertura_enero.py`.
- **CONFIANZA**: CONFIRMADO para 1, 3 y 4; para 2, CONFIRMADO que faltan en el código (leído), y la ausencia
  de NOAA-21 es cita de S149.
- **GRAVEDAD 3**: es la pieza que debía impedir esta clase entera de error, y hoy le da al que la consulta
  una regla más estricta donde no hace falta y ningún aviso donde sí.

### F3-4. La "etiqueta confiable" de las alertas débiles incluye 8 filas sólo OCR sin comprobar, dos de Suomi NPP

- **ARCHIVO:LÍNEA**: `docs/S150_ALERTAS_DEBILES_MAX.md:22-23` y `:279-281`; regla en
  `experiments/_s150_debiles/clases_rechazo.py:44-45` y `:70` ("tabla, u OCR desde 06-13"). Contra
  `docs/S150_IMAGENES_SNPP.md` §3.2: una alerta de Suomi NPP sólo OCR "no es confiable como etiqueta
  positiva mientras no se compruebe que la cabecera de su imagen coincide con su hora".
- **QUÉ PASA**: de las 46 pérdidas de `experiments/_s150_debiles/filas.json`, 11 son sólo OCR posteriores al
  2026-06-13; S150 excluyó las 3 que miró y dejó como confiables las otras 8: Suomi NPP Lastarria
  2026-08-21 05:24 (0,15 MW) y Planchón Peteroa 2026-08-24 06:12 (0,04 MW); NOAA-21 Lastarria 2026-06-17
  05:06 y 2026-08-04 05:06, Planchón Peteroa y Chaitén 2026-06-17 05:12, Puyehue Cordón Caulle 2026-06-19
  04:36; NOAA-20 Planchón Peteroa 2026-08-14 04:36. Tres volcanes con alerta sólo OCR de NOAA-21 en la
  misma pasada del 2026-06-17 es un patrón que vale mirar (SOSPECHA).
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: leer `experiments/_s150_debiles/filas.json` filtrando `perdida` y `solo_ocr` con
  `dt >= "2026-06-13"`; la plataforma está en `B.sensor` (comando en la sesión de esta auditoría, mismo
  filtro que `r1`).
- **CONFIANZA**: CONFIRMADO el conteo; que sean otra pasada es SOSPECHA.
- **GRAVEDAD 2**: el propio documento mide (H4) que la tasa de pérdida en el tramo débil es igual con tabla y
  con OCR, así que el patrón no lo fabrica la etiqueta. Toca los conteos ("36 con etiqueta confiable", "14
  del camino D22") que heredan el pre-registro D22 (suspendido) y la sonda de tres campos.

### F3-5. D2 dice que la unión CONS ∪ OCR mitiga "de facto" la cobertura incompleta; la mitiga justo donde el OCR no es confiable

- **ARCHIVO:LÍNEA**: `docs/MIROVA_DIVERGENCES.md:44-48`; `CLAUDE.md` del proyecto, sección Estado ("D2 quedó
  mitigada de facto por el loader CONS∪OCR de S86"). SCRIPT:SALIDA: `r9_ocr_alerta_vs_tabla_rutina.py` →
  `r9_salida.txt`.
- **QUÉ PASA**: las alertas VIIRS 375 sólo OCR (pasadas que la tabla nunca lista) son, de marzo a septiembre,
  318 antes del 2026-06-13 (179 de Suomi NPP) y 176 desde entonces (**118 de Suomi NPP, 67 %**). Antes del
  2026-06-13 A119 dice que no deciden; después, dos tercios son del satélite cuyo OCR trae a veces la imagen
  de otra pasada. La mitigación es real sólo para NOAA-20 y NOAA-21 desde el 2026-06-13. Dato a favor de la
  vara: en las mismas fechas, **ninguna** alerta del OCR coincide con una pasada que la tabla lista como
  RUTINA (0 contradicciones): lo sólo OCR son pasadas que faltan, no pasadas en que los canales discrepan.
- **Medición**: (1) si el OCR contradijera a la tabla, aparecería como "tabla RUTINA"; da 0. (2) Satélite
  tomado de nuestro record a más o menos 2 min; 70 y 23 alertas quedan "sin record" y se informan aparte.
  Ventana 2026-03-01 a 2026-09-30, referencia `latest_consolidado.csv` (2026-10-09) más respaldo y snapshot OCR.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `python experiments/_s150_meta_audit/F3/r9_ocr_alerta_vs_tabla_rutina.py`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD 2**: una métrica de recall de VIIRS que confíe en "D2 mitigada" cuenta como fallas nuestras
  pasadas de Suomi NPP que quizá no eran del cráter.

### F3-6. La auditoría semanal cuenta como noche con alerta 12 noches VIIRS 375 que sólo sostiene el OCR, 9 de ellas sólo Suomi NPP

- **ARCHIVO:LÍNEA**: `scripts/auto_audit_weekly.py:318-319` (`load_mirova_alertas`, CONS ∪ OCR, por noche).
  SCRIPT:SALIDA: `r10_auditoria_semanal_noches_solo_ocr.py` → `r10_salida.txt`.
- **QUÉ PASA**: en la ventana vigente de `data/audit_continuous/latest.json` (2026-08-06 a 2026-10-05), de 194
  noches VIIRS 375 con alerta, **12 se sostienen sólo en filas del OCR y 9 sólo en filas OCR de pasadas
  Suomi NPP**. Si esas noches no tienen record nuestro publicable, salen como falla de recall. Desde S150 el
  veredicto DEGRADADO abre un issue: una falla fabricada por la vara puede abrir uno.
- **Medición**: (1) si el OCR no pesara, daría 0. (2) Control: el total da 194, el mismo `n_noches` que
  `latest.json` (`recall.VIIRS375.n_noches`). Aproximación declarada: noche = hora UTC de 00 a 12, no la
  elevación solar del pipeline. **No crucé** esas 9 noches con las 14 fallas de la semana.
- **CÓMO SE VE EN EL DASHBOARD**: invisible; se vería como un issue de recall bajo la banda.
- **CÓMO REPRODUCIRLO**: `python experiments/_s150_meta_audit/F3/r10_auditoria_semanal_noches_solo_ocr.py`.
- **CONFIANZA**: CONFIRMADO el conteo; que alguna sea una de las fallas reportadas es SOSPECHA.
- **GRAVEDAD 2**. La ventana de recall de esa semanal cruza además #535 (2026-08-28); la de falsas
  publicaciones ya parte el 2026-09-01, bien.

### F3-7. El snapshot del repo tiene el OCR al día y el consolidado semanal: en la cola, cualquier alerta parece sólo OCR

- **ARCHIVO:LÍNEA**: `.github/workflows/sync-mirova-csv.yml:99-100` (OCR al snapshot cada hora) contra
  `.github/workflows/audit-weekly.yml:53-57` (consolidado al snapshot una vez por semana); consumidores del
  par: `scripts/banco_paridad.py:456` (modo `--snapshot`), `scripts/clasificacion_referencia.py:65`,
  `experiments/_s147_agentes/medir_f05.py:30` (default del cargador). SCRIPT:SALIDA:
  `r5_snapshot_asimetrico.py` → `r5_salida.txt`.
- **QUÉ PASA**: hoy el consolidado del snapshot termina el 2026-10-05 13:45 y el OCR el 2026-10-09. De las 14
  alertas OCR posteriores al corte, las 14 quedan "sin fila de tabla" contra el snapshot y sólo 5 contra
  `latest_consolidado.csv`; faltan además 644 filas RUTINA. Dos de las 9 mal clasificadas son de Chillán, en
  plena erupción.
- **Medición**: (1) si la asimetría no importara, las dos cuentas coincidirían; antes del corte coinciden
  (593 contra 595, diferencia explicada por F3-2). (2) Mismo cargador para las dos.
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `python experiments/_s150_meta_audit/F3/r5_snapshot_asimetrico.py`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD 2**: afecta sólo a los últimos 0 a 7 días y sólo a scripts que lean el par del snapshot; la
  auditoría semanal refresca los dos antes de medir.

### F3-8. A54 sigue vigente sin marca y se midió con un OCR que A119 hoy no deja decidir

- **ARCHIVO:LÍNEA**: `CLAUDE.md` del proyecto, regla A54 (sin ⚠️); fuente `docs/AUDIT_S86.md:16-19` y
  `:54-56` (2026-05-28, "CONS ∪ OCR como universo MIROVA", l. 142).
- **QUÉ PASA**: la composición que sostiene "el 95,4 % de los falsos positivos son anomalías físicamente
  reales" (49,1 % "MIROVA sí publicó pero el cruce falló", 46,3 % reales no publicadas, 4,6 % artefactos)
  se armó entera con OCR anterior al 2026-06-13: versiones inestables hasta el 2026-02-24, geometría mal
  calibrada hasta el 2026-06-11 y sin distancia medida (`MAPA_BASES_MIROVA_V1.md` §2.2), con el que el OCR
  decide ALERTA contra FALSO_POSITIVO. Una alerta OCR mal calibrada que en verdad era un foco lejano pasa de
  la categoría (a) a otra. El sentido del sesgo no se puede saber sin re-medir.
- **CÓMO SE VE EN EL DASHBOARD**: invisible; A54 sostiene la postura de no agregar compuertas (A55, A68, A72).
- **CÓMO REPRODUCIRLO**: no se puede con el corpus de S86 (reprocesado muchas veces desde entonces); exige
  re-clasificar el corpus de hoy con la vara de A119.
- **CONFIANZA**: CONFIRMADO que la vara es la afectada (leído); el efecto sobre los porcentajes es SOSPECHA.
- **GRAVEDAD 2**.

### F3-9. La distancia del OCR no es la misma magnitud que la de la tabla, aun para la misma pasada

- **SCRIPT:SALIDA**: `r7_ocr_distancia_vs_tabla.py` → `r7_salida.txt`.
- **QUÉ PASA**: desde el 2026-06-13, en 185 pasadas VIIRS 375 que traen fila en los dos canales, la clase
  coincide en 185 de 185 y el VRP en 185 de 185 (diferencia de 0,05 MW o menos), pero la distancia difiere en
  más de 0,5 km en **30 (16 %)**, de forma sistemática por volcán: Puyehue Cordón Caulle 3,5 a 3,8 km en el
  OCR contra 7,7 a 8,2 en la tabla, Tupungatito 2,3 contra 5,21, Láscar 0,41 contra 1,5. No es la imagen de
  otra pasada (el VRP coincide): es otra definición de distancia. Cualquier uso que mezcle las dos distancias
  como una sola (por ejemplo `dist_ref` de `far_ref` en `banco_paridad.py:292-294`, que toma la primera fila
  con distancia de cualquier canal) mezcla dos magnitudes. S144 ya lo había visto para su caso (N3 de
  `docs/PREREGISTRO_KEEP_PEAK_DIRECCION_S144_VERIFICADOR_V2.md:105-116`) y lo resolvió usando la de la tabla.
- **Medición**: (1) si el OCR describiera su pasada con la misma vara, la distancia coincidiría salvo
  redondeo. (2) Control: el VRP de VIIRS 375 coincide en 185 de 185, así que el pareo es el correcto.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD 1**: no encontré una conclusión vigente que dependa de la distancia OCR fuera de S144.

### F3-10. Un rango de S150 omite abril

- **ARCHIVO:LÍNEA**: `docs/S150_RESULTADO_MESES.md:94` ("en el control la tasa falsa del borde del barrido es
  1,9 a 3,6 veces la del nadir", en un párrafo que habla de abril a agosto). Abril da 1,54
  (`experiments/_s149_prereg_invierno/resultados/abril_VIIRS375.txt`, P2; reproducido por `r8`).
- **GRAVEDAD 1**: no cambia ningún veredicto (el brazo `max` da 0,22 en abril).

## 3. Conclusiones vigentes tocadas, por defecto

| conclusión vigente | vara leída en su script | defecto que la toca | qué hice | ¿cambia? |
|---|---|---|---|---|
| Tabla de recall por tramo de `max` (S150 §2, decisión 1b) | `recall_por_magnitud.py:12`, CONS+OCR, abril a agosto | A119 y OCR de otra pasada | re-medida (r1, r1b) | **números sí** (filas de 0,20 MW o más); veredicto no, se refuerza |
| A98 "874 de 877 noches" (S139) | `banco_noches_out.json`, `cons_ocr`, 2026-01-10 a 09-07 | A119 (enero, OCR antes del 06-13) | re-leída la configuración `cons` de la misma salida: **789 de 792 (99,6 %)** | no |
| Rebaja de A10 / D32 (1.512 pares, 0,706 contra 0,783) | `medir_f05.py:30`, CONS+OCR del snapshot, 03-01 a 09-20 | A119, OCR de otra pasada, snapshot | re-medida (r4): L0 hoy 0,707 y 0,784 (n 1.311); L2 **0,726 y 0,794** (n 972) | no |
| A118 / S148 "137 a 135 de 143" | tabla de S148, septiembre | OCR de otra pasada | re-medida (r1c) con la referencia de hoy: L0 da 148 positivas, no 143 (la referencia cambió); las pérdidas de F son las mismas 3 de tabla, NOAA-20, 0,14 MW o menos, bajo las tres varas | no |
| A114 y P2 de S150 (borde sobre nadir) | `estructura_del_residual.py:59`, septiembre; P2 por mes | composición por satélite (S149 §2) | re-medida (r8) dentro de NOAA-20 y NOAA-21 por separado: 1,3 a 3,9 | no |
| A119 "86 % en enero" | `calidad_referencia_mirova.py:22` | denominador con Tupungatito | re-medida (r6) | **sí: 97 a 100 % sin Tupungatito** |
| D2 "mitigada de facto" | loader CONS ∪ OCR | A119 y OCR de otra pasada | medida la composición (r9) | se acota: sólo NOAA-20 y 21 desde el 06-13 |
| Recall de la auditoría semanal | `auto_audit_weekly.py:319`, 08-06 a 10-05 | OCR de otra pasada; cruza #535 | medida la exposición (r10): 12 de 194 noches sólo OCR | SIN DATO del efecto (no crucé las fallas) |
| A54 (S86) | CONS ∪ OCR, todo antes del 06-13 | A119 | leída | por re-medir |
| Rebaja de A82, cara VIIRS (84,5 contra 62,1; 47,5 contra 22,8) | ventana 01-29 a 08-28 con OCR (texto de `FASE0_VERIFICADOR.md:89`) | A119 | sólo dirección: quitar positivos OCR dudosos sube la tasa en positivos, agranda el contraste | no, por dirección (no re-medida) |
| Rebaja de A23 ("como mucho 80 de 214") | `VERIFICADOR_CONTEXTO_LIMPIO.md:188-199`, "con o sin OCR" | A119 | sólo dirección: quitar OCR sólo baja el numerador | no |
| Rebaja de A83 (AUC 0,762 y 0,554) | etiqueta "MIROVA publicó" con OCR | A119 | no | por re-medir; dirección no evidente |
| A94 "1 noche de 946" | loader CONS ∪ OCR | A119 | no | por re-medir, prioridad baja (S149 ya la rebajó por unidad) |
| "36 con etiqueta confiable" (alertas débiles) | `clases_rechazo.py:70` | OCR de otra pasada | contada (F3-4) | conteo sí; patrón no |
| A99 (pares contra el OSF de 2025) | OSF v2.5 | A105: el OSF está filtrado por umbrales de VRP de MIROVA, o sea seleccionado por el denominador | no | ya rebajada; el sesgo de selección se suma, sin medir |
| Tiering por conteos del OSF (memoria `project_tiering_osf_v2_5.md`) | OSF v2.5 | A105 | dirección: el filtro sólo quita filas; los 10 volcanes tienen 741 a 10.028 refs contra un umbral de 30 | no |
| D17 (centro de grilla desde los GeoTIFF, 10 a 408 m) | TIF EPSG:4326 | A106 | leída: el caveat ya está escrito (`MIROVA_DIVERGENCES.md:2246-2248`) | no |
| A109 y el cierre de `keep_peak` (S144) | TIF por pasada | A106 (imagen repetida) | leído: `conteo_tif.py:74-82` marca "propia" por md5 y `g2.py` usa sólo propias | no |
| A107 (cota de radio, S143) | `Distancia_km` | distancia OCR distinta (F3-9) | leído: S144 fijó la de la tabla | no |
| Futuras referencias congeladas desde el remoto | `congelar_desde_remoto.py` y similares | remoto que pierde filas (F3-2) | medido | **sí, para lo que se congele desde el 2026-10-06** |

Totales por defecto (una conclusión puede estar en dos): A119, 9 (tabla por tramo, A98, D32, D2, A54, A82,
A23, A83, A94); OCR de otra pasada, 6 (tabla por tramo, D32, A118, D2, semanal, alertas débiles); #535, 1
(semanal); A105, 2 (A99, tiering); A106, 3 (D17, A109, A107 vía distancias); copia atrasada o remoto que
pierde filas, 4 (D32 por el snapshot, `banco_paridad --snapshot`, `clasificacion_referencia`, referencias
futuras). **Re-medidas: 7** (tabla por tramo, A98, D32, A118, A114, A119 enero, exposición de la semanal).

## 4. Lo que queda por re-medir, en orden

1. **Las dos pérdidas de NOAA-21 en Lastarria** (2026-06-17 05:06, 0,46 MW; 2026-08-04 05:06, 0,20 MW),
   únicas pérdidas de 0,20 MW o más que sobreviven a la vara corregida: mirar la cabecera "Last Update" de sus
   imágenes como hizo `docs/S150_IMAGENES_SNPP.md`. Decide si `max` tiene algún costo sobre 0,20 MW.
2. **Las 8 sólo OCR de la "etiqueta confiable"** (F3-4), mismo método.
3. **A54** con el corpus de hoy y la vara de A119, si la postura de "no compuertas" vuelve a discutirse.
4. **A83** con etiqueta de tabla sola.
5. **Cruce de las 9 noches sólo Suomi NPP con las fallas de la semanal** (F3-6).

## 5. VERIFICADO LIMPIO

Lo que miré y está sano frente a estos defectos de la vara; no hace falta volver a mirarlo por este eje.

| qué | por qué está sano | cómo se confirma |
|---|---|---|
| A104 (62,6 % y 86,5 % de 358 y 325 en `RESULTADOS.md`) | sus tramos son 2026-08-12 a 08-28 y 09-01 a 09-17: después del 06-13, después de abril, con NOAA-21 en la tabla | leer `experiments/_s142_linea_base/RESULTADOS.md` §1 |
| Negativos limpios de todos los A/B de S146 a S150 | `banco_paridad.py:295-297` exige una fila RUTINA de la tabla con VRP 0: el OCR no fabrica negativos | lectura del código |
| El OCR nunca contradice una RUTINA de la tabla | 0 casos de marzo a septiembre | `r9_ocr_alerta_vs_tabla_rutina.py` |
| La clase del OCR, cuando la tabla también trae la pasada | 185 de 185 iguales en VIIRS 375 desde el 06-13 | `r7_ocr_distancia_vs_tabla.py` |
| Las 28 alertas VIIRS 750 en cero (`AUDIT_S149` §3) | son filas de la tabla según su verificador (`VERIFICADOR_MAGNITUD_CERO.md:18`); consistente con `r1`: VIIRS 750 tiene 0 a 3 filas sólo OCR por mes desde junio | `r1_salida.txt` (no re-medí caso a caso) |
| MODIS en los A/B de S149 y S150 | la tabla trae MODIS completo; sólo OCR hay 2 alertas MODIS de marzo a septiembre, una diurna | `r9_salida.txt` y el listado de F3-3 |
| Referencias congeladas de S149 (`_congelado/<mes>`) | contienen las alertas que el remoto perdió después (comprobado: abril 04-18, agosto 08-05 y 08-18) | `grep` en esos CSV |
| Referencia congelada de Chillán | las filas perdidas de su ventana son RUTINA de otros volcanes | `r5b` filtrado desde 2026-09-20 |
| Imágenes repetidas en el análisis TIF de S144 | marca "propia" por md5 | `experiments/_s144_conteo_tif/conteo_tif.py:74-82` |
| Coeficientes de Wooster calibrados contra el OSF (S14) | A105 habla de conteos; el coeficiente es por fila y no depende de qué filas filtra el OSF | lectura de A105 y de la regla científica |
| Estructura borde mayor que nadir | existe dentro de NOAA-20 y de NOAA-21 por separado, mes a mes | `r8_borde_por_satelite.py` |
