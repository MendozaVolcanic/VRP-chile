# Auditoría S172: déficit de magnitud de Nevados de Chillán en los tres sensores

## 1. Encabezado

- Hora del servidor: inicio Sun, 01 Nov 2026 23:37:07 GMT; cierre de mediciones Sun, 01 Nov 2026 23:52:24 GMT
  (header `Date` de la API de GitHub).
- Commit medido: `origin/main` 14fb62030a186fda02ce2ba172866cf01408eeb9 (2026-11-01T23:34:32Z). Para reproducir el
  auto-audit: 489113c1fe816a4e74658e29a0786b9498bcf980 (el commit que escribió `latest.json`, 2026-10-26T16:09:57Z).
  Copias por `git archive` en `D:/vrp-trabajo/temporales/s172_chillan/repo/` y `D:/vrp-trabajo/temporales/s172_chillan/repo_20261026/`.
  Hashes de cada insumo en `D:/vrp-trabajo/temporales/s172_chillan/INSUMOS_SHA256.txt`.
- Referencia de MIROVA usada (copia de main de hoy): `registro_vrp_consolidado.csv` sha256
  ab1a208c89b32df2fd5622c102ac2a984fa8a0102cfe0fe9f65cb8ff54b7d88f (llega hasta el 2026-10-26 12:40, ver VERIFICADO
  LIMPIO 8) y `registro_vrp_ocr.csv` sha256 d4ad8c44d5112ca44751552d4aee6e920c20ac5dc0d73f4fc5d9f6594785026e, más la
  unión histórica y el respaldo que carga `referencia_mirova_unificada.cargar_referencia_unificada`. D-9 en modo SN.
- Modelo: Claude Opus 5.5 (claude-opus-5-5). Esfuerzo: no lo expone mi sesión; el que fijó quien orquesta.
- CARPETA: `D:/vrp-trabajo/temporales/s172_chillan/`
- Qué NO miré: el código de `pipeline/` (no leí por qué la magnitud cae con el cenit, sólo lo medí); los gránulos;
  ningún paper; los otros diez volcanes; el día (el pipeline no deja pasadas diurnas); no re-corrí los lectores de
  MOD-D, V375-E ni V750-C, sólo leí sus salidas en las ramas; no verifiqué que las fuentes lejanas de 2025 sean
  incendios.

## 2. En una pantalla

1. El déficit de Chillán NO es parejo: en los tres sensores depende del ángulo cenital del satélite (Spearman razón
   contra cenit −0,87 MODIS n 12, −0,50 VIIRS 375 n 53, −0,81 VIIRS 750 n 39; los tres fuera del rango barajado). Cerca
   del nadir (z < 30°) la razón es 0,75 / 0,74 / 0,85; sobre 60° cae a 0,08 / 0,33 / 0,11. Causa común probable: la
   mirada oblicua, y dentro de una noche la caída está en nuestra curva más que en la de MIROVA.
2. Por pasada el déficit es mayor que el del auto-audit (0,36 / 0,57 / 0,42 contra 0,56 / 0,66 / 0,68), y las 3
   alertas protegidas MODIS perdidas están las tres a 57,6 a 58,2° de cenit.
3. Descomposición conteo × VRP por píxel: SIN DATO para el domo (la tabla NRT no trae Npix y el OSF 2025 tiene 1 sola
   fila a menos de 5 km del cráter); nuestro conteo no explica la razón (Spearman −0,05 / 0,12 / −0,17).
4. Las tres vías «código MIROVA» llevan Chillán a ~1 en lo medido retrospectivamente: MOD-D 1,028 (12 pares, z > 30°
   1,100, publica las 4 MODIS perdidas), port V750 0,994 a 0,998 (n 28), V375-E ganancia ×1,546 sobre K (n 27).
5. Falta, para decidir el mecanismo, la lectura de cada vía partida por cenit y con ablación de sus piezas (remuestreo,
   fondo); en V750 el fondo de anillo solo ya baja el port a 0,684 (n 22, SOSPECHA de mecanismo).

Informe: `D:/vrp-trabajo/temporales/s172_chillan/INFORME.md`

## 3. Mediciones (instrumentos, con sus dos preguntas)

Todos los scripts y salidas están en CARPETA. La ventana de los datos de cada número va con él.

### s01, reproducción del auto-audit (`s01_reproducir_autoaudit.py`, salida `s01_salida.txt`, `s01_salida.json`; el script hace `chdir` a la copia y escribió el JSON en `repo_20261026/s01_salida.json`, copiado a CARPETA)
- P1: si la carga de records o de la referencia estuviera rota, `n_noches` y la mediana no coincidirían con
  `latest.json`. P2: control negativo, referencia corrida un día: las noches comunes cambian (8 a 5, 21 a 18, 16 a 12).
- Resultado (ventana 2026-08-27 a 2026-10-26, copia del commit 489113c1, funciones del propio `auto_audit_weekly`):
  MODIS 0,56 (n 8), VIIRS 375 0,662 (n 21), VIIRS 750 0,683 (n 16), idénticos a `latest.json`.

### s02, razón por pasada con el predicado del tablero (`s02_pareo_por_pasada.py`)
- Publica = `banco_paridad.cargar_nuestros` (node sobre `frontend/index.html` de main, sha256 fda0a628…); magnitud
  publicada = `disp` (mirovaEqVrpDisplay). Alerta = fila ALERTA de la unión, D-9 SN, pareo ±120 s (`TOL_S`). VRP de
  MIROVA de la pasada: el de la fila CONS si existe, si no el del OCR.
- P1: control positivo, ×2 a nuestra magnitud dobla la mediana (0,362 a 0,725; 0,571 a 1,142; 0,418 a 0,837).
  Identidad del predicado `[0,1,1,1,0]`, `[1,0]`, la esperada por `banco_paridad.controles`. Lectura directa del JSON
  (`f5_core_vrp_mw` con fallback a `pc.vrp_mw` en V375, `pc.vrp_mw` en los otros) contra `disp` de node: 0 diferencias.
- P2: referencia corrida +1 día: MODIS 0 pares; VIIRS 10 y 6 pares (la órbita repetida cae a veces dentro de ±120 s
  al día siguiente; es un límite de este control, no del banco, que nunca corre la referencia).
- Salidas: `s02_v_autoaudit_resumen.json` (2026-08-27 a 2026-10-26), `s02_v_abr_oct_resumen.json` (2026-04-01 a
  2026-10-26; los pares con magnitud son los mismos, todos entre el 2026-09-28 y el 2026-10-26),
  `s02_v_abr_oct_pasadas.csv` (una fila por pasada nocturna nuestra), `s02_lista_alertas.txt` (las 118 pasadas con
  alerta de MIROVA, con nuestros valores), `s02_v_2025_pasadas.csv` (2025, para s04).

### s03, estratos (`s03_estratos.py`, salida `s03_salida.json`, `s03_salida.txt`)
- P1: si la razón no dependiera de nada, todos los estratos darían lo mismo. P2: el Spearman real se compara con el
  rango de 200 barajados del cenit dentro de cada sensor (semilla 172).
- Normalización dentro de la noche: cada pasada dividida por la pasada más cercana al nadir de la misma noche y sensor,
  por separado para nosotros y para MIROVA. Supone que el domo no cambia mucho en 1 a 2 h (suposición, no dato).

### s04, descomposición contra el OSF v2.5 de 2025 (`s04_osf2025_descomposicion.py`, salidas `s04_osf2025_*`)
- Insumo: filas `IDvolc` 357070 de `VRP_GLOBAL_ARCHIVE_2025.csv` (archivo local del repo, no versionado; extracción
  `osf_v25_chillan_357070.csv` sha256 fdea70f7…), y `s02_v_2025_pasadas.csv` (records K de 2025, reproceso #883).
- P1: identidad conteo × VRP por píxel = razón de escena, error máximo 4,4e-16; |cenit nuestro − cenit MIROVA| máximo
  1,6°. Control positivo: k·A del OSF constante por sensor (error relativo ≤ 1,1e-8). P2: las pasadas pareadas sin
  píxel nuestro van aparte (6 de 46 en V375), no como razón 0.

### s05, controles cruzados (`s05_controles_cruzados.py`, salida `s05_salida.txt`)
- (a) Mis razones K por pasada MODIS contra `razon_k` de la lectura del A/B de MOD-D: 12 de 12 iguales a 1e-3; contra
  `razon_b` (control que no debe coincidir) 0 de 12. (b) El criterio «dash» que el auto-audit reconstruye en Python
  contra el predicado de node: 0 diferencias en 658 pasadas nocturnas de Chillán (2026-08-27 a 2026-10-26).

## 4. Tablas por sensor

Par = pasada nuestra publicada con alerta de MIROVA a ±120 s. Ventana efectiva de los pares: 2026-09-28 a 2026-10-26
(no hay pares antes en 2026-04-01 a 2026-10-26). Razón = mediana de VRP publicado / VRP de MIROVA.

### MODIS (12 pares, 8 noches; 16 pasadas con alerta, 4 sin publicar)

| estrato | n | razón |
|---|---|---|
| todas, por pasada | 12 | 0,362 |
| por noche (par con mayor VRP de MIROVA) | 8 | 0,56 |
| sólo CONS | 12 | 0,362 |
| z < 30 | 6 | 0,749 |
| z 30 a 50 | 3 | 0,205 |
| z 50 a 60 | 2 | 0,206 |
| z ≥ 60 | 1 | 0,076 |
| Aqua / Terra | 7 / 5 | 0,209 / 0,747 (bajo 30°: Aqua 0,635 n 3, Terra 0,751 n 3; la diferencia es de cenit) |
| conteo propio 1 / 2 / 3 a 5 px | 4 / 6 / 2 | 0,419 / 0,616 / 0,207 |
| dentro de la noche, Δz ≥ 35° | 1 | nuestro 0,225, MIROVA 0,84 |
| Spearman razón vs cenit | 12 | −0,867 (barajado [−0,483; 0,503]) |
| MOD-D brazo V (lectura del A/B, los mismos 12) | 12 | 1,028; z ≤ 30 0,926; z > 30 1,100 |

Conclusión MODIS: **causa común probable** (cenit). Para decidir el mecanismo: ablación de MOD-D (sólo remuestreo
contra sólo fondo de MIROVA) sobre estas 16 pasadas, partida en z < 30 / ≥ 30.

### VIIRS 375 (53 pares, 21 noches; 60 pasadas con alerta, 7 sin publicar)

| estrato | n | razón |
|---|---|---|
| todas, por pasada | 53 | 0,571 |
| por noche | 21 | 0,587 |
| sólo CONS | 46 | 0,572 |
| z < 30 | 15 | 0,737 |
| z 30 a 50 | 16 | 0,567 |
| z 50 a 60 | 8 | 0,601 |
| z ≥ 60 | 14 | 0,33 |
| NOAA-20 / NOAA-21 / Suomi NPP | 20 / 19 / 14 | 0,53 / 0,605 / 0,564 |
| conteo propio 1 / 2 / 3 a 5 / 6+ px | 14 / 11 / 21 / 7 | 0,563 / 0,542 / 0,587 / 0,571 |
| dentro de la noche, Δz ≥ 35° | 13 | nuestro 0,737, MIROVA 1,083 |
| Spearman razón vs cenit | 53 | −0,50 (barajado [−0,25; 0,289]) |
| V375-E (lectura retrospectiva, marco 2026-04-01 a 2026-10-21) | 27 | ganancia ĝ ×1,546 sobre K, «MEJORA»; razón propia de Chillán: SIN DATO |

Conclusión VIIRS 375: **causa común probable** (cenit), más débil que en los otros dos. Para decidir: la razón de
V375-E en Chillán por tramo de cenit (el lector la entrega por volcán sólo como ganancia).

### VIIRS 750 (39 pares, 16 noches; 42 pasadas con alerta, 3 sin publicar)

| estrato | n | razón |
|---|---|---|
| todas, por pasada | 39 | 0,418 |
| por noche | 16 | 0,632 |
| sólo CONS | 36 | 0,416 |
| z < 30 | 11 | 0,845 |
| z 30 a 50 | 15 | 0,413 |
| z 50 a 60 | 5 | 0,418 |
| z ≥ 60 | 8 | 0,105 |
| NOAA-20 / NOAA-21 / Suomi NPP | 16 / 15 / 8 | 0,368 / 0,587 / 0,565 (bajo 30°: 0,794 / 0,845 / 0,89) |
| conteo propio 1 / 2 / 3 a 5 px | 19 / 10 / 10 | 0,482 / 0,359 / 0,451 |
| dentro de la noche, Δz ≥ 35° | 9 | nuestro 0,135, MIROVA 0,535 |
| Spearman razón vs cenit | 39 | −0,814 (barajado [−0,332; 0,311]) |
| port V750 «O» (verificador V750-C, 2026-04-02 a 2026-10-17) | 28 | 0,998 (medir); 0,994 [0,920; 1,036] (medir3) |
| port con fondo de anillo «O_fanillo» | 22 | 0,684 [0,360; 0,858] |

Conclusión VIIRS 750: **causa común probable** (cenit). Para decidir: la ablación de V750-C (O, O_fanillo, O_sinhalo)
partida por cenit en Chillán.

### Descomposición conteo × VRP por píxel (pregunta 1)

- NRT 2026: **SIN DATO**. Columnas de la tabla CONS: `timestamp, Fecha_Satelite_UTC, Fecha_Captura_Chile, Volcan,
  Sensor, VRP_MW, Distancia_km, Tipo_Registro, Clasificacion Mirova, Ruta Foto, …`; el OCR agrega `Zenith_Sat_deg,
  Azimut_Sat_deg, Nivel_Anomalia_MIROVA, Distancia_aprox_*` y otras. Ninguna trae número de píxeles (cabeceras leídas en
  esta sesión).
- OSF v2.5 2025 (trae `Npix`): 80 filas nocturnas de Chillán en 2025, sólo 1 con `Max_Dist` ≤ 5 km (2025-11-04 06:00,
  V375, 1 px, 0,08 MW, nosotros sin píxel) y 3 con ≤ 7 km (`s04_osf_cerca_crater.txt`). Para el domo: **SIN DATO**.
- Sobre las fuentes lejanas de 2025 (que nosotros clasificamos `far`: 1 de 78 pasadas pareadas publica), la escena
  sí se descompone (2025-02-15 a 2025-12-31, `s04_osf2025_salida.txt`): MODIS razón 0,873 = conteo 0,613 × VRP por
  píxel 1,706 (n 12); V375 1,076 = 1,0 × 1,175 (n 40); V750 0,992 = 0,742 × 1,341 (n 20). Mismo signo que la razón de
  conteo 0,67 de S158 (contamos menos píxeles, más calientes cada uno), pero es otro objeto (fuentes lejanas extensas) y
  no se traslada al domo.
- En 2026 nuestro conteo no se relaciona con la razón (Spearman −0,046 / 0,124 / −0,174) y bajo 50° de cenit los
  estratos por conteo dan razones parecidas (`s03_salida.json`, clave `por_n_pos_y_cenit<50`).

## 5. Hallazgos (orden por gravedad)

### CH172-01
- TÍTULO: El déficit de Chillán depende del ángulo cenital del satélite en los tres sensores a la vez
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `s03_estratos.py` : `s03_salida.json` (claves `spearman_razon_vs_cenit`, `por_cenit`,
  `dentro_de_la_noche`); pares en `s02_v_abr_oct_pasadas.csv`
- QUÉ PASA: cuando el satélite mira el domo de lado, nuestro VRP publicado cae mucho más que el de MIROVA en la misma
  pasada: cerca del nadir la razón es 0,75 / 0,74 / 0,85 (MODIS / V375 / V750) y sobre 60° es 0,08 / 0,33 / 0,11.
  Dentro de una misma noche, con 35° o más de diferencia de cenit, nuestro VRP baja a 0,23 / 0,74 / 0,14 de la pasada
  más nadir y el de MIROVA a 0,84 / 1,08 / 0,54. Esto es lo que deja a los tres sensores bajo 0,7 a la vez. El
  mecanismo en el código no lo leí.
- CÓMO SE VE EN EL DASHBOARD: la serie de Chillán sube y baja pasada a pasada según qué satélite pasó y con qué ángulo;
  una pasada oblicua aparece como una caída de actividad de hasta 10 veces (VIIRS 750 2026-10-18 06:48, z 67,6°: 2,84 MW
  nuestro contra 22,85 de MIROVA; 48 min antes, z 22,3°: 13,60 MW nuestro contra 18,98).
- CÓMO REPRODUCIRLO: `python -B s02_pareo_por_pasada.py D:/vrp-trabajo/temporales/s172_chillan/repo 2026-04-01
  2026-10-26 s02_v_abr_oct` y `python -B s03_estratos.py s02_v_abr_oct_pasadas.csv s03_salida.json`; ejemplo NdC
  VIIRS_NOAA21_750 2026-10-18 06:48 UTC frente a VIIRS_NOAA20_750 2026-10-18 06:00 UTC.
- CONFIANZA: CONFIRMADO (medido). La lectura «la caída es nuestra y no de MIROVA» descansa en suponer potencia del domo
  casi constante en 1 a 2 h: esa parte es SOSPECHA.
- GRAVEDAD 1-5: 4 (en erupción, el operador puede leer una pasada oblicua como un descenso real de la actividad)

### CH172-02
- TÍTULO: Las 3 alertas protegidas MODIS perdidas de Chillán están todas a ~58° de cenit
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `s02_lista_alertas.txt` (filas MODIS 2026-10-12 07:20, 2026-10-15 01:05,
  2026-10-25 07:20); `modd_resultado_f4.json` clave `chillan.recuperadas`
- QUÉ PASA: a 57,6 a 58,2° el píxel de 1 km que contiene el domo queda tan diluido que no sale alerta: dos pasadas sin
  ningún píxel anómalo y la del 10-25 con 1 píxel a 4,3 km con VRP 0. MIROVA publica 2,18 / 1,72 / 3,79 MW. Una cuarta
  (2026-09-29 07:20, z 58,4°, 0,13 MW) tampoco. El brazo V de MOD-D publica las cuatro (razones 1,05 / 0,84 / 1,69 /
  0,67). El efecto de CH172-01 llega hasta la detección. En VIIRS 750, 2 de las 3 perdidas también son oblicuas
  (z 65,1° y 68,0°, 0,23 y 0,09 MW).
- CÓMO SE VE EN EL DASHBOARD: sin punto MODIS de Chillán en una pasada en que MIROVA alertó sobre 1 MW (la noche se
  publica por otra pasada, según el propio auto-audit).
- CÓMO REPRODUCIRLO: `grep MODIS s02_lista_alertas.txt` (columna `pub 0`); NdC MODIS_AQUA 2026-10-12 07:20,
  MODIS_TERRA 2026-10-15 01:05, MODIS_AQUA 2026-10-25 07:20 UTC.
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 4 (alerta protegida perdida; el criterio de la réplica no admite ninguna)

### CH172-03
- TÍTULO: En VIIRS 750, el fondo de anillo solo ya reproduce el déficit de Chillán dentro del port de MIROVA
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `v750c_medir3_salida.txt` (copia de `origin/claude/s162-viirs750-f63ef4`,
  `experiments/_s162_v750c/verificador/medir3_salida.txt`, commit 5b56c77d) l. 8 y 24; `v750c_medir_salida.txt` l. 96 a 98
- QUÉ PASA: el port con el fondo de MIROVA da 0,994 en Chillán (n 28); el mismo port con nuestro fondo de anillo baja a
  0,684 [0,360; 0,858] (n 22), cerca de la razón de K. De noche la ladera del anillo es más tibia que la cumbre, y
  restar un fondo más tibio baja el VRP. Es candidato a explicar parte del déficit de K en V750; la salida no está
  partida por cenit, así que no sé si explica la caída oblicua o sólo el residuo del nadir (CH172-05).
- CÓMO SE VE EN EL DASHBOARD: VRP de VIIRS 750 de Chillán a dos tercios del de MIROVA.
- CÓMO REPRODUCIRLO: `git -C "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile" show
  origin/claude/s162-viirs750-f63ef4:experiments/_s162_v750c/verificador/medir3_salida.txt` (re-correrlo exige los
  `--insumos` y `--grillas` de esa sesión, que no tengo).
- CONFIANZA: SOSPECHA (leí la salida de otra sesión, no la re-corrí; ventana que declara esa salida: 2026-04-02 a
  2026-10-17)
- GRAVEDAD 1-5: 3

### CH172-04
- TÍTULO: El auto-audit, al dividir máximo de la noche por máximo de la noche, subestima el déficit por pasada y lo
  vuelve sensible a qué pasadas coinciden
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `repo/scripts/auto_audit_weekly.py:683` (`max(o["pub"]) / mvrp`) y l. 584 a 587 (el
  máximo de MIROVA de la noche); `s02_v_autoaudit_resumen.json`; `s01_salida.txt` (control desplazado)
- QUÉ PASA: en una noche con varias pasadas, el auto-audit toma nuestra mejor pasada (casi siempre la más nadir) y la
  divide por la mayor de MIROVA, que puede ser otra pasada, oblicua. Por pasada pareada el déficit es 0,362 / 0,571 /
  0,418 (n 12 / 53 / 39) contra 0,56 / 0,662 / 0,683 por noche, y la dependencia del cenit queda escondida. Con la
  referencia corrida un día la métrica de noche sigue dando números plausibles (0,76 / 1,106 / 1,94), o sea que no
  exige que sea la misma pasada. El propio código lo advierte para los estratos de cenit (`auto_audit_weekly.py:774` a
  779), no para la cifra principal.
- CÓMO SE VE EN EL DASHBOARD: invisible (afecta el número del issue semanal, no el tablero).
- CÓMO REPRODUCIRLO: `python -B s01_reproducir_autoaudit.py D:/vrp-trabajo/temporales/s172_chillan/repo_20261026
  s01_salida.json` y `python -B s02_pareo_por_pasada.py D:/vrp-trabajo/temporales/s172_chillan/repo 2026-08-27
  2026-10-26 s02_v_autoaudit`
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 2 (el aviso salta igual; lo que cambia es cuánto déficit hay y dónde vive)

### CH172-05
- TÍTULO: Queda un déficit de 15 a 25 % aun cerca del nadir
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `s03_salida.json` (`por_cenit`, `z<30`); `modd_resultado_f4.json`
  (`chillan.mediana_z_le30`)
- QUÉ PASA: bajo 30° de cenit la razón es 0,749 (n 6) / 0,737 (n 15) / 0,845 (n 11). No depende del cenit, así que es
  una segunda causa sumada a CH172-01; MOD-D lo deja en 0,926 bajo 30°. Candidato: el fondo (CH172-03); no lo verifiqué
  para MODIS ni V375.
- CÓMO SE VE EN EL DASHBOARD: VRP algo menor que el de MIROVA incluso en las mejores pasadas.
- CÓMO REPRODUCIRLO: igual que CH172-01.
- CONFIANZA: CONFIRMADO el número; la causa es SOSPECHA.
- GRAVEDAD 1-5: 2

### CH172-06
- TÍTULO: Antes de la fase fuerte, las alertas débiles de VIIRS 375 se pierden porque el píxel del cúmulo sale con VRP 0
- ARCHIVO:LÍNEA o SCRIPT:SALIDA: `s02_lista_alertas.txt` (VIIRS375 2026-05-14 05:48, 06-16 05:30, 08-18 05:48,
  08-20 05:12, 08-20 06:06, 09-05 05:48, 09-14 05:42)
- QUÉ PASA: MIROVA alertó con 0,06 a 0,14 MW (sobre el corte D-9 de 0,05 MW); nosotros tenemos un cúmulo de 1 píxel en
  la cumbre (centroide a 0,33 a 0,72 km) pero ese píxel trae VRP 0 en `anomaly_pixels`, así que no publica. En régimen
  débil el déficit es de detección (recorte a cero), no de magnitud, y no entra en ninguna razón.
- CÓMO SE VE EN EL DASHBOARD: noche sin punto VIIRS 375 cuando MIROVA marcó una alerta bajo 1 MW.
- CÓMO REPRODUCIRLO: `grep VIIRS375 s02_lista_alertas.txt | grep "pub 0"`; NdC VIIRS_NOAA21 2026-09-14 05:42 UTC.
- CONFIANZA: CONFIRMADO lo medido; por qué el VRP sale 0 no lo leí en el código (SOSPECHA: fondo más caliente que el
  píxel).
- GRAVEDAD 1-5: 2 (bajo 1 MW, no protegidas)

## 6. SEGUIMIENTOS (fuera de mi eje)

- La clase `class = 1` del OSF v2.5 («volcanic detection» según `MIROVA_Database_Schema_v2.5.docx`; texto extraído en
  `schema_osf_v25_texto.txt` l. 38) marca como volcánicas 51 de las 80 filas nocturnas de Chillán de 2025, todas entre
  el 2025-02-15 y el 2025-03-06 y con `Max_Dist` de 12,7 a 21,5 km (V750 20, V375 19, MODIS 12; `s04_osf_clase1.txt`).
  El esquema dice que es un indicador de cribado (l. 62). Quien use `class` del OSF como etiqueta de actividad del
  cráter se equivoca en Chillán 2025. CONFIRMADO el rótulo y la distancia; que sean incendios es SOSPECHA. Gravedad 1.
- `Distancia_km` de MIROVA crece con el cenit (Spearman 0,79 / 0,67 / 0,64, `s03_salida.json`): todo estrato por
  distancia de MIROVA está confundido con el cenit (A93: es un radio cuantizado a la celda). CONFIRMADO. Gravedad 1.

## 7. VERIFICADO LIMPIO

1. El auto-audit del 2026-10-26 se reproduce exacto con su propio código y los datos de su commit (vara: `latest.json`;
   `s01_salida.txt`).
2. El predicado de node pasa su control de identidad (vara: casos del guard S139, `repo/scripts/banco_paridad.py:158` a
   172).
3. La magnitud publicada leída del JSON (`f5_core_vrp_mw` / `pc.vrp_mw`) coincide con `mirovaEqVrpDisplay` de node en
   todos los pares de los tres sensores (vara: node; `control_json_vs_node_difieren` = 0 en `s02_*_resumen.json`).
4. El criterio «dash» del auto-audit en Python coincide con el predicado de node en 658 de 658 pasadas nocturnas de
   Chillán de 2026-08-27 a 2026-10-26 (vara: node, A97; `s05_salida.txt` (b)). Vale sólo para Chillán y esa ventana.
5. Mis razones K por pasada MODIS = `razon_k` de la lectura de MOD-D en 12 de 12, y distintas de `razon_b` en 12 de 12
   (vara: otra implementación; `s05_salida.txt` (a)).
6. El OCR no mueve la razón: con sólo CONS, 0,362 / 0,572 / 0,416 contra 0,362 / 0,571 / 0,418 (vara: tabla CONS sola).
7. El k·A del OSF es constante por sensor (2.531.250 / 11.081.250 / 18.900.000, error ≤ 1,1e-8; `s04_osf2025_salida.txt`).
8. El consolidado del snapshot de main termina el 2026-10-26 12:40 aunque el remoto de Mirova-v1 llega al 2026-11-01
   20:35 (`remoto_consolidado_20261101.csv`, sha256 2a9e6005…): no es un defecto. Ese archivo lo refresca sólo el commit
   semanal del auto-audit (`git log` del archivo en main: 489113c1, 2e1bc0e3, f3b41421, 0a3b4e3a) y el sync horario
   escribe `latest_consolidado.csv` (`.github/workflows/sync-mirova-csv.yml` l. 108). No afecta esta ventana.

## 8. SIN DATO

- Número de píxeles de MIROVA en 2026 (la tabla NRT no lo trae): descomposición del domo imposible con la referencia NRT.
- Descomposición del domo en el OSF 2025: 1 fila a ≤ 5 km del cráter.
- Estrato «antes del 2026-09-18»: 0 pares con magnitud (el primer par es del 2026-09-28).
- Día contra noche: el pipeline y el banco sólo dejan pasadas nocturnas.
- Razón propia de Chillán en V375-E: el lector la informa como ganancia ĝ (log10 0,189, factor 1,546, n 27) y
  «MEJORA», no como razón contra MIROVA (`v375e_lectura.json`, `M.radiante.detalle.g_hat_por_volcan`). Ventana del marco:
  2026-04-01 a 2026-10-21 sin el 12, 13 y 17 a 20 de octubre (`v375e_PREREGISTRO_E.md` l. 70 a 71, copia de
  `origin/claude/s172-v375e-relector`). El pre-registro deja Chillán fuera como pregunta propia: l. 155 a 156, TEXTO,
  «No mide Chillán sobre 3 MW como pregunta propia (V375-F, después de esto)».
- Lectura retrospectiva oficial de V750-A para Chillán: en `origin/claude/s162-viirs750-2-918174` sólo encontré salidas
  de identidad y bit a bit con Chillán (`experiments/_s162_v750a/bitabit_store_salida.txt` l. 12); el número de
  magnitud viene del verificador de V750-C, otra rama.
- Qué pieza de cada vía corrige la caída con el cenit (remuestreo, fondo, Test 1): no separable con las salidas leídas,
  salvo la ablación de V750-C, que no está partida por cenit.

## 9. FUERA DE ALCANCE

Reprocesos, gránulos, código de `pipeline/`, papers, otros volcanes, propuesta de cambios.

## 10. Conclusión por sensor

| sensor | ¿causa común? | medición que haría falta para decidir |
|---|---|---|
| MODIS | causa común probable (cenit; Spearman −0,87, n 12) | ablación de MOD-D por pieza sobre las 16 pasadas, z < 30 / ≥ 30 |
| VIIRS 375 | causa común probable (cenit; Spearman −0,50, n 53) | razón de V375-E en Chillán por tramo de cenit, y ablación |
| VIIRS 750 | causa común probable (cenit; Spearman −0,81, n 39) | ablación de V750-C (O, O_fanillo, O_sinhalo) por cenit en Chillán |
