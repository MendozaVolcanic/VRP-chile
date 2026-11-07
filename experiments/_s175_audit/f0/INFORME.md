# F0 S175: pendientes de S160 sin eje, y las pasadas que nunca bajamos

## 1. Encabezado

- **Fecha y hora del servidor**: ola 0 `Sat, 07 Nov 2026 04:10:45 GMT` (insumos); última consulta de esta sesión
  `Sat, 07 Nov 2026 16:00:04 GMT` (cabecera `Date` de `gh api -i rate_limit`).
- **Commit medido**: base `752d348bc67190e53b610989877e2405d238a1bc` en todo número salvo donde se nombra otro. El
  clasificador compara además contra `d516b9d8c0fad5b0ca458b9fb57cdf5e6f75f956` (el commit que auditó S160). Bitácora
  de `loop/activo` leída en `395af8034` (fuera de main). Árbol propio extraído con `git -c core.autocrlf=false archive`
  en `C:\Users\nmend\vrp-temporales\s175_audit\f0\arbol\` (192 MB) y records de los 11 Tier A en
  `C:\Users\nmend\vrp-temporales\s175_audit\f0\base_data\` (164 MB).
- **Modelo y esfuerzo**: Claude Opus 5.5 (`claude-opus-5-5`); esfuerzo real declarado por el sistema:
  `reasoning_effort` 15 (se pidió high; corrí en bajo, igual que F3 y F5).
- **CARPETA**: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\f0\`.
  Temporal: `C:\Users\nmend\vrp-temporales\s175_audit\f0\` (unos 360 MB).
- **Llamadas a la API de GitHub**: 3 de 10 (hora del servidor, issues con «Suomi» en el título, pasos fallidos de
  la corrida NRT 42016780200).
- **Instrumentos** (cada uno con su salida al lado, en CARPETA):
  - `f0_clasificador.py` → `f0_clasificador_salida.txt`: un predicado por pendiente, en S160 y en la base.
  - `f0_pasadas_por_satelite.py` → `f0_pasadas_por_satelite_salida.txt`: pasadas por satélite y semana, último
    record contra MIROVA, filas de MIROVA sin record nuestro, control de mutación, historia de `noches_sin_datos`.
  - `f0_203_cumbre_cero.py` → `f0_203_cumbre_cero_salida.txt` (y `_stderr.txt`): cúmulos de cumbre en 0,0 MW con el
    predicado del tablero (banco_paridad con node).
  - `f0_proporcion_nrt_modis.py` → `f0_proporcion_nrt_modis_salida.txt`: fracción MODIS `product_version nrt`.
  - `f0_245_perdidas_vuelven.py` → `f0_245_perdidas_vuelven_salida.txt`: filas perdidas de la referencia.
  - `f0_cadencias.py` → `f0_cadencias_salida.txt`: corridas del NRT y del healthcheck por día.
- **Qué NO miré** (mi silencio no es «todo bien»):
  - Ninguna lámina ni TIF de MIROVA: los casos de la cola de campo (C-02, C-03, C-07, C-08, C-09, C-10) quedan con su
    estado documental y sus datos, no con la mirada que piden.
  - El efecto en lo publicado de V0b-03, F2-212 y V2-09 (pide dETI por píxel o reproceso).
  - Los 12 pendientes de F1b (183 a 187, 190 a 196) sólo los fecho: compruebo que los archivos citados no cambiaron
    desde S160; no rehíce sus números.
  - Los pendientes de S160 que el plan reparte a F2 (201, C-04) y a F3 (281 a 297, 287, 288, U12, V4-01 a V4-03,
    decisión 8): fuera de alcance.
  - La causa de las 7 corridas NRT en rojo del 4 y 5 de noviembre (sólo identifiqué el paso; va a SEGUIMIENTOS).
  - El contenido del secret `EARTHDATA_TOKEN` (no tengo acceso; su fecha sale del registro de credenciales).

## 2. En una pantalla

1. Las tres líneas base rojas se reencuentran: decisión 1 (#891) RESUELTA en `0d73f2a4e`; decisión 6 (C-10) ABIERTA;
   0 records de Suomi NPP después del 2026-11-02 13:00 UTC (el último es del 2026-11-01 06:24, y MIROVA tampoco tiene
   pasada de Suomi NPP esa noche). 203 se reproduce exacto: 30 de 97 cúmulos de cumbre V750 en 0,0 MW, 7 con alerta.
2. De los vencimientos, 241, 242, 245, 247, V3-01 y V3-03 se resolvieron entre el 22 y el 23 de octubre (#891 a #897);
   quedan abiertos 243 (nadie mide la fracción MODIS NRT), V3-02 (la cadencia ignora el disparador externo, que hoy da
   12,8 de 16 corridas diarias) y el código 0 en modo estricto con una plataforma muda. El token hay que rotarlo antes
   del 2026-11-27.
3. Todo lo de VIIRS 750 sigue abierto en el código (203, D32, V2-09 a V2-12) y 203 quedó sin camino: S160 lo dejaba a
   D25, y D25 no se adoptó (`c8423ce9a`). Las decisiones 6 y 9 y C-07, C-09, C-10 siguen abiertas; la cola de campo no
   se tocó desde S160 (10 de 10 «abierto», también C-06, que el mundo ya respondió con el issue #943).
4. Pasadas que nunca bajamos: VIIRS sin hueco (una fila nocturna de MIROVA sin record nuestro en 10 semanas, por borde
   de gránulo); MODIS tiene 49 filas nocturnas de MIROVA sin record desde el 2026-09-14, pasadas enteras de Terra entre
   el 28-sep y el 10-oct, todas RUTINA. Ni `noches_sin_datos` ni el recall pueden verlas: miden por sensor y noche con
   alerta (control de mutación: NOAA-21 quitado 14 días, misma cuenta 464 = 464).
5. Los `hallazgos.csv` de S160 nunca entraron a git (`.gitignore:40 *.csv`) y los de S175 tampoco: V2-13 queda SIN DATO.

## 3. Líneas base rojas (corridas primero)

**Clasificador** (`f0_clasificador.py`). Cada pendiente tiene un predicado sobre `git show <commit>:<ruta>` que dice si
el defecto descrito sigue. P1: si un pendiente estuviera resuelto con otra forma de texto, el predicado daría falso
ABIERTO; por eso cada RESUELTO lleva el commit que cambió el texto (`git log -S`), y los predicados laxos (F2-231,
F2-232, F2-234, F2-235, 249) los revisé a mano contra la línea que encuentran. P2: archivo ausente da «sin archivo»,
nunca «resuelto». Resultado: `dec1 = RESUELTO` (`0d73f2a4e 2026-10-22 ... (#891)`), `dec6 = ABIERTO` (la fila C-10 de
`docs/COLA_CAMPO.md` no existía en `d516b9d8c`, se creó en la rama de S160): **el clasificador distingue**.

**Pasadas** (`f0_pasadas_por_satelite.py`, sección 1): 73.710 records de los 11 Tier A en la base, del 2025-02-15 al
2026-11-07 01:15 UTC. Records Suomi NPP (375 y 750) con hora ≥ 2026-11-02 13:00 UTC: **0**. Control positivo: NOAA-20
111 y NOAA-21 142 después del cese; Suomi NPP 120 en los cuatro días previos. **Rojo reencontrado.**

**203** (`f0_203_cumbre_cero.py`): ventana K de S160 (2026-09-18 a 2026-10-21), VIIRS 750: 97 cúmulos de cumbre, 30 en
0,0 MW, 0 publicados, etiquetas 7 `pos`, 11 `neg_limpio`, 12 `sin_info`: idéntico a S160. Control de identidad del
predicado `([0, 1, 1, 1, 0], [1, 0])`.

## 4. Hallazgos (orden por gravedad)

### 101
- TÍTULO: 203 sigue abierto y quedó sin camino: cúmulos de cumbre de VIIRS 750 en 0,0 MW que el tablero no publica, y D25 (la vía que S160 le asignó) no se adoptó
- ARCHIVO:LÍNEA: SCRIPT:SALIDA `f0_203_cumbre_cero.py` → `f0_203_cumbre_cero_salida.txt`; `docs/MIROVA_DIVERGENCES.md` l. 2863 en la base (TEXTO: «D25 tal como está NO SE ADOPTA»), commit `c8423ce9a`; `docs/AUDIT_S160.md` §5 decisión 4 (TEXTO: «Es la divergencia D25, abierta y con su A/B en #890»)
- QUÉ PASA: cuando el píxel del cráter está a la temperatura del anillo regional o más frío, el exceso sale negativo, se recorta a cero y el cúmulo no se publica. En la base: 30 de 97 (2026-09-18 a 10-21, 7 con alerta de MIROVA), 11 de 58 (2026-10-22 a 11-02, 4 `neg_limpio`, 7 `sin_info`, ninguna alerta) y 6 de 19 (2026-11-03 a 11-07, sin referencia todavía). S160 recomendó no arreglarlo aislado y dejarlo al A/B de D25; D25 se leyó el 2026-10-24 y no se adoptó, así que hoy no hay ningún frente que lo vaya a medir o cerrar.
- CÓMO SE VE EN EL DASHBOARD: invisible; en las 7 pasadas de la ventana K con alerta de MIROVA (Láscar, Isluga y Chillán, 0,09 a 0,36 MW) el operador no ve nada en VIIRS 750.
- CÓMO REPRODUCIRLO: `python C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\f0\f0_203_cumbre_cero.py`; p. ej. Láscar VIIRS_NOAA20_750 2026-10-08 05:42 UTC (MIROVA 0,36 MW).
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 4 (las alertas perdidas son débiles, ninguna protegida; S160 le dio 5 por la fracción, que en la ventana nueva bajó a 19 %)

### 102
- TÍTULO: F1-H6 / D32 abierta: publicamos el cúmulo y MIROVA la suma de todos los píxeles alertados
- ARCHIVO:LÍNEA: `docs/MIROVA_DIVERGENCES.md` l. 3284 en la base (TEXTO: «**ABIERTA (registrada S147, verificada con contexto limpio, gravedad 4; prioridad MEDIA, no es la palanca del 0,7)**»); SCRIPT:SALIDA `f0_clasificador_salida.txt` fila F1-H6
- QUÉ PASA: cuando la anomalía cubre píxeles fuera del cúmulo principal, MIROVA los suma y nosotros no; cambia la magnitud de una parte de lo publicado en VIIRS 750 (S160: 14 de 67 en K). Sin cambio de código ni de estado desde S160. No re-medí la fracción.
- CÓMO SE VE EN EL DASHBOARD: magnitud menor que la de MIROVA en esas pasadas.
- CÓMO REPRODUCIRLO: `grep -n "^## D32" docs/MIROVA_DIVERGENCES.md` en la base.
- CONFIANZA: CONFIRMADO (estado); la fracción de hoy SIN DATO
- GRAVEDAD 1-5: 4 (la de S160; no la re-medí)

### 103
- TÍTULO: Decisión 6 de S160 y C-10 abiertas: el veto de D18 sigue colgando de una alerta MODIS de Láscar de exactamente 1,00 MW
- ARCHIVO:LÍNEA: `docs/COLA_CAMPO.md` fila C-10 (estado «abierto»); `latest_consolidado_base.csv` (copia de la base) l. 37438: `2026-03-27 07:10:00,...,Lascar,MODIS,1.0,1.41,ALERTA_TERMICA`; `loop/activo` `395af8034` `tasks/LOOP_OBJETIVOS.md` l. 522 (TEXTO: «abiertas 6 (mirar C-10, Láscar MODIS 2026-03-27, antes de dar D18 por vetada)»)
- QUÉ PASA: la fila de MIROVA sigue igual (1,0 MW a 1,41 km) y nuestro record de esa pasada (MODIS_AQUA 2026-03-27 07:10) tiene hoy 0,14 MW con el cúmulo a 3,20 km; nadie corrió el veredicto con la alerta en 0,99 y 1,01 MW ni miró la lámina.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `grep "2026-03-27 07:10" latest_consolidado.csv | grep Lascar` en la base; record en `data/mirova_equivalent/Lascar.json`.
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 3

### 104
- TÍTULO: Decisión 9, V0b-01 y C-07 abiertas: K1 sigue en -0,8 y el tope D9 sigue acoplado a K1
- ARCHIVO:LÍNEA: `pipeline/process_viirs_mod.py:1040-1045` en la base (`_path_d_cap_active = (` ... `and n_nti_path == 0`), `pipeline/process_viirs.py:1472-1477`; `pipeline/profiles/mirova_equivalent.yaml:60` (`nti_k1_night: -0.8`)
- QUÉ PASA: un píxel con NTI sobre K1 apaga el tope de 5 MW de los cúmulos contextuales sobre fondo frío; con el K1 del código de MIROVA (-0,7) la protegida de Chillán quedaría topada. Nada adoptó -0,7, así que es latente, pero el acoplamiento sigue y no hay decisión. El record de Chillán VIIRS_SNPP_750 2026-10-01 06:00 sigue en 11,084 MW (`diag_nti_max` -0,7518, `t_bg_k` 268,76) y el de NOAA-20 2026-10-13 05:54 en 5,93 MW.
- CÓMO SE VE EN EL DASHBOARD: hoy nada; si se adopta K1 -0,7, Chillán a 5,0 MW donde MIROVA dio 10,0.
- CÓMO REPRODUCIRLO: `sed -n 1040,1046p pipeline/process_viirs_mod.py` en la base; Nevados de Chillán VIIRS_SNPP_750 2026-10-01 06:00 UTC.
- CONFIANZA: CONFIRMADO (mecanismo y valores del record; el 5,0 bajo -0,7 es simulado por S160)
- GRAVEDAD 1-5: 3

### 105
- TÍTULO: C-09 abierta: la fila OCR de Lastarria del 2026-04-18 (1,29 MW, distancia entre 1,56 y 20,04 km) sigue contando como protegida
- ARCHIVO:LÍNEA: `data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv` (copia de la base, l. 931): `Lastarria,VIIRS375,1.29,0.0,ALERTA_TERMICA_OCR,...,1.56,20.04,ambiguo`; la tabla tiene esa pasada como `RUTINA` (VIIRS 750, 0,0)
- QUÉ PASA: un objeto que puede estar a 20 km del cráter, mal leído desde la imagen, sigue siendo una alerta de 1 MW o más en todo evaluador con el combinado. Nadie miró la imagen.
- CÓMO SE VE EN EL DASHBOARD: en la capa de MIROVA de Lastarria como alerta OCR.
- CÓMO REPRODUCIRLO: `grep -n "2026-04-18 04:4" registro_vrp_ocr.csv | grep Lastarria` en la base.
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 3 (decide «protegida perdida» en cualquier A/B de VIIRS 375 que cruce abril)

### 106
- TÍTULO: V2-09 abierto: los umbrales de cumbre rigen hasta inner_radius (3 a 20 km); MIROVA los usa en una caja de 7 × 7 píxeles
- ARCHIVO:LÍNEA: `pipeline/profile.py:610` en la base (`ENABLE_ROI1_BOX_PAPER: bool = bool(_p.get("enable_roi1_box_paper", False))`); el perfil no lo enciende (valor efectivo `False`, leído con `VRP_PROFILE=mirova_equivalent`)
- QUÉ PASA: entre 2,6 km y el inner de cada volcán aplicamos la vara sensible donde MIROVA aplica la estricta; pesa sobre todo en Cordón Caulle (inner 20 km). Sin cambio desde S160.
- CÓMO SE VE EN EL DASHBOARD: publicaciones de Cordón Caulle con cúmulos lejos del cráter.
- CÓMO REPRODUCIRLO: `python -c "from pipeline import profile as p; print(p.ENABLE_ROI1_BOX_PAPER)"` con `VRP_PROFILE=mirova_equivalent` en el árbol de la base.
- CONFIANZA: CONFIRMADO el código; el efecto SOSPECHA (como en S160: no se sabe qué BOX usa MIROVA en PCC)
- GRAVEDAD 1-5: 3

### 107
- TÍTULO: Rotación de EARTHDATA_TOKEN pendiente con fecha: rotar antes del 2026-11-27 (vence el 2026-12-07 18:03 UTC)
- ARCHIVO:LÍNEA: `C:\Users\nmend\OneDrive\Escritorio\claude\REGISTRO_CREDENCIALES.md:28` (TEXTO: «vence **2026-12-07 18:03 UTC**» y «**Rotar antes del 2026-11-27.**»); `C:\Users\nmend\vrp-temporales\s175_audit\insumos\secretos_nombres_fechas.txt` (`EARTHDATA_TOKEN 2026-10-08T18:07:05Z`); `scripts/token_edad.py:27` (`DIAS_AVISO = 10`)
- QUÉ PASA: a la ola 0 el secret no se había rotado desde el 2026-10-08. El healthcheck abre issue recién a 10 días del vencimiento; la vez anterior el token venció y el NRT estuvo caído del 2026-10-03 al 2026-10-08, en plena actividad de Chillán. La guarda de token vacío ya corta `nrt.yml`, pero un token vencido no es vacío.
- CÓMO SE VE EN EL DASHBOARD: si vence, los datos dejan de llegar en los 11 volcanes.
- CÓMO REPRODUCIRLO: fecha del secret con `gh api repos/MendozaVolcanic/VRP-chile/actions/secrets/EARTHDATA_TOKEN --jq .updated_at`.
- CONFIANZA: CONFIRMADO (fecha del secret a las 04:10 UTC del 2026-11-07; vencimiento según el registro, no leí el JWT)
- GRAVEDAD 1-5: 3 (con fecha; se evita rotando)

### 108
- TÍTULO: La cola de campo no se mantuvo desde S160: los 10 casos siguen «abierto», también C-06, que ya tiene respuesta
- ARCHIVO:LÍNEA: `docs/COLA_CAMPO.md` en la base (último commit `b941c8052`, S160); SCRIPT:SALIDA `f0_clasificador_salida.txt` filas C-02 a C-10; issue #943 «Cese esperado confirmado: Suomi NPP dejó de producir records (informativo)», abierto 2026-11-04T19:01:09Z
- QUÉ PASA: C-06 preguntaba si la vigilancia por plataforma funciona en el mundo real tras el cese de Suomi NPP: funcionó (issue #943, 0 records de Suomi NPP después del cese, aviso del tablero cargado en las tres vistas). La fila sigue diciendo «abierto (fecha fija)». Las demás tampoco tienen fecha ni resultado.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git log --oneline 752d348bc -- docs/COLA_CAMPO.md`; `gh issue view 943 -R MendozaVolcanic/VRP-chile`.
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 2

### 109
- TÍTULO: Pasadas MODIS nocturnas que MIROVA lista y nosotros nunca bajamos: 49 desde el 2026-09-14, incluidas pasadas enteras de los 11 volcanes, invisibles para el recall
- ARCHIVO:LÍNEA: SCRIPT:SALIDA `f0_pasadas_por_satelite.py` → `f0_pasadas_por_satelite_salida.txt`, secciones 2, 4 y 4c
- QUÉ PASA: una pasada que no se baja no deja hueco en el tablero si otra pasada de la noche llega. Filas MODIS nocturnas (00 a 11 UTC) de MIROVA sin ningún record MODIS nuestro a ±120 s: semanas W38 a W45 5, 3, 17, 13, 2, 5, 0 y 4 (de 157, 168, 152, 158, 158, 162, 155 y 123). Hay pasadas enteras sin record en ningún volcán: 2026-09-28 01:25 a 01:30 (11 volcanes), 2026-10-02 00:50 (Láscar, Isluga, Lastarria, Tupungatito) y 2026-10-10 01:05 a 01:10 (11 volcanes); MODIS_TERRA cae a 54 pasadas en W40 contra 79 a 87 las demás semanas. Las 49 son RUTINA (ninguna alerta). Algunas tienen record nuestro a 300 s (borde de gránulo de 5 min, ver SEGUIMIENTOS).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -I C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\relaxed-almeida-d17378\experiments\_s175_audit\f0\f0_pasadas_por_satelite.py`; p. ej. Lascar MODIS 2026-09-28 01:30 UTC.
- CONFIANZA: CONFIRMADO que no hay record; la causa (gránulo no publicado, descarga fallida o pasada descartada) SIN DATO
- GRAVEDAD 1-5: 2 (hoy ninguna con alerta; una pasada con alerta caería igual en silencio)

### 110
- TÍTULO: noches_sin_datos y el recall son ciegos a un satélite callado: miden por sensor y noche con alerta
- ARCHIVO:LÍNEA: `scripts/auto_audit_weekly.py:363-380` en la base (`recall_por_sensor`, `if (vol, b, fecha) not in vistos: sin_datos += 1`); SCRIPT:SALIDA `f0_pasadas_por_satelite_salida.txt` secciones 5 y 6
- QUÉ PASA: si NOAA-21 se calla, NOAA-20 llena la misma noche. Control de mutación: quitando todos los records NOAA-21 de los últimos 14 días (445 records), los volcán-sensor-noche con algún record quedan en 464 = 464. `noches_sin_datos` vale 0 en los cinco `latest.json` que tienen el campo (2026-10-12 a 2026-11-02); antes no existía. Sólo `scripts/vigilar_plataformas.py` (72 h por plataforma) lo ve, y lo vio (#943). La mejora 5 de S174 pedía mirar ahí: el campo no puede verlo.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: el mismo script, sección 5.
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 2 (el vigilante por plataforma cubre el caso a 72 h)

### 111
- TÍTULO: 243 abierto: nadie mide la fracción de records MODIS que llegan como NRT; la fecha de decomiso de la colección 6.1 ya pasó
- ARCHIVO:LÍNEA: SCRIPT:SALIDA `f0_proporcion_nrt_modis.py` → `f0_proporcion_nrt_modis_salida.txt`; `pipeline/fetch.py:212-218` en la base (sólo `6.1` y `6.1NRT`); `product_version` sólo aparece en `scripts/reparar_product_version_modis_s133.py` (grep en `scripts/` y `.github/workflows/`)
- QUÉ PASA: hoy el Standard 6.1 sigue llegando (0 % NRT de abril a octubre; noviembre 14 de 143, 13 de ellos del 6 y 7 de noviembre esperando su upgrade). Un record NRT del 2026-11-02 (Planchón-Peteroa MODIS_TERRA 01:15, `MOD021KM.A2026306.0115.061...NRT.hdf`) sigue sin upgrade a cinco días. Si LAADS ejecuta el decomiso, MODIS pasaría a NRT sin que nadie lo cuente.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -I ...\f0\f0_proporcion_nrt_modis.py`
- CONFIANZA: CONFIRMADO; que el record del 11-02 nunca reciba Standard es SOSPECHA
- GRAVEDAD 1-5: 2

### 112
- TÍTULO: 241 resuelto a medias: una plataforma muda ya no da «completa», pero sigue saliendo con código 0 también en modo estricto
- ARCHIVO:LÍNEA: `scripts/run_pipeline.py:482-505` en la base («Cobertura: faltan plataformas enteras (nota, no es búsqueda fallida)»; `return 3 if (estricto and cuentan) else 0`); `pipeline/fetch.py:789` (`"sin_granulos": False`)
- QUÉ PASA: desde `c3ee70ed6` (#897) la corrida dice qué plataforma faltó y emite `::warning`; el código de salida no cambia ni en estricto, por decisión escrita en el docstring («Que el modo estricto falle por una plataforma muda queda como decisión aparte»). Un reproceso estricto con una plataforma callada sale verde.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `sed -n 451,505p scripts/run_pipeline.py` en la base.
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 2

### 113
- TÍTULO: V3-02 abierto: el medidor de cadencia ignora el disparador externo, que hoy da 12,8 de las 16 corridas diarias del NRT, y su JSON no lo lee nadie
- ARCHIVO:LÍNEA: `scripts/medir_cadencia_cron.py:69` en la base (`if r.get("event") != "schedule":`); `.github/workflows/nrt-healthcheck.yml:327` (única mención de `cadencia.json`); SCRIPT:SALIDA `f0_cadencias.py` → `f0_cadencias_salida.txt`
- QUÉ PASA: en las 50 corridas del NRT de los insumos (2026-11-04 01:10 a 11-07 04:10, 3,12 días): 16,0 por día, 12,8 `workflow_dispatch` (todas a los :10, de 01:10 a 12:10 UTC) y 3,2 `schedule`. La frase «doce veces al día» del preámbulo queda corta: son 16. Si cron-job.org muere, la medición no cambia.
- CÓMO SE VE EN EL DASHBOARD: pasadas que llegan horas más tarde, sin explicación.
- CÓMO REPRODUCIRLO: `python -I ...\f0\f0_cadencias.py`
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 2

### 114
- TÍTULO: Los hallazgos.csv de las auditorías no entran a git: `.gitignore:40 *.csv`; los de S160 ya no existen y V2-13 no se puede clasificar
- ARCHIVO:LÍNEA: `.gitignore:40` (`git check-ignore -v experiments/_s175_audit/f0/hallazgos.csv` → `.gitignore:40:*.csv`); `git ls-tree -r --name-only 752d348bc experiments/_s1*_audit*` da 1 solo `hallazgos.csv`; `git ls-files experiments/_s175_audit` no tiene ningún `hallazgos.csv` (sí `f2/hacer_csv.py` y `f3/escribir_csv.py`)
- QUÉ PASA: el plan arma la lista del verificador desde `hallazgos.csv`, pero ese archivo sólo vive en el disco de quien audita. El de S160 F2 (`C:\vrp-trabajo\s159-pruebas\...\f2\hallazgos.csv`) ya no está en esa ruta, así que la forma defectuosa que V2-13 describía no se puede ni confirmar ni refutar.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git check-ignore -v experiments/_s175_audit/f0/hallazgos.csv`
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 2 (trazabilidad de la auditoría, que la Resolución CPLT N°372 exige)

### 115
- TÍTULO: 166 abierto: las bandas RECALL_MIN del auto-audit siguen calibradas sobre C0 y juzgan a K y a la vía
- ARCHIVO:LÍNEA: `scripts/auto_audit_weekly.py:120` en la base (`RECALL_MIN = {"VIIRS375": 93.4, "VIIRS750": 79.5, "MODIS": 95.0}`)
- QUÉ PASA: sin cambio desde S160. Los dos issues abiertos de auto-audit FUERA_DE_BANDA (#915, #936) se juzgan con estas bandas; que la banda explique parte de esos rojos es SOSPECHA (no lo medí; F1 tiene ese eje para MODIS).
- CÓMO SE VE EN EL DASHBOARD: issues semanales en rojo que pueden ser de la banda y no del detector.
- CÓMO REPRODUCIRLO: `sed -n 118,122p scripts/auto_audit_weekly.py` en la base.
- CONFIANZA: CONFIRMADO el código; la relación con #915 y #936 SOSPECHA
- GRAVEDAD 1-5: 2

### 116
- TÍTULO: V2-10 abierto: anomaly_pixels.dist_km se mide desde el centro del volcán y el popup dice «Distancia al cráter»
- ARCHIVO:LÍNEA: `pipeline/process_viirs_mod.py:1106` (`"dist_km": round(float(dist[r, c]), 2),`); `frontend/index.html:3159` (`Distancia al cráter: ${px.dist_km ...`)
- QUÉ PASA: sin cambio; en Cordón Caulle el centro está a 7,58 km del cráter (S160).
- CÓMO SE VE EN EL DASHBOARD: popups de píxeles secundarios con una distancia que no es al cráter.
- CÓMO REPRODUCIRLO: `sed -n 1106p pipeline/process_viirs_mod.py; sed -n 3159p frontend/index.html` en la base.
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 2

### 117
- TÍTULO: V2-11 abierto: la VRE del tablero suma 6 h por detección, sin base física
- ARCHIVO:LÍNEA: `frontend/index.html:2490` (`const DT_HOURS = 6;`) y `:2500`, `:3319`
- QUÉ PASA: sin cambio; con más de cuatro publicaciones en un día integra más de 24 h.
- CÓMO SE VE EN EL DASHBOARD: en la caja VRE y su curva.
- CÓMO REPRODUCIRLO: `grep -n DT_HOURS frontend/index.html` en la base.
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 2

### 118
- TÍTULO: V2-12 abierto y latente: el tope de 50 GW juzga t_max_k antes de que exista en VIIRS 375
- ARCHIVO:LÍNEA: `pipeline/store.py:165-166`, `:559` (`_apply_sanity_cap(record)`) antes de `:564-565` (copia de `t_max_i04_k`)
- QUÉ PASA: una pasada VIIRS 375 real sobre 50 GW se anularía. Hoy no hay ninguna.
- CÓMO SE VE EN EL DASHBOARD: hoy nada.
- CÓMO REPRODUCIRLO: `sed -n 555,566p pipeline/store.py` en la base.
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 2

### 119
- TÍTULO: V0b-03 abierto: el mínimo de cumbre 0,003 gobierna también el umbral del dETI
- ARCHIVO:LÍNEA: `pipeline/process_viirs.py:1341` (`c1_deti_summit=_c1_sum,`)
- QUÉ PASA: sin cambio; efecto en lo publicado SIN DATO.
- CÓMO SE VE EN EL DASHBOARD: SIN DATO.
- CÓMO REPRODUCIRLO: `sed -n 1336,1345p pipeline/process_viirs.py` en la base.
- CONFIANZA: CONFIRMADO el código
- GRAVEDAD 1-5: 2

### 120
- TÍTULO: V0b-02 abierto: la alerta de Láscar del 2026-03-04 05:06 sigue fuera de la tabla, así que la cota «cero negativos sobre -0,8» depende de la referencia
- ARCHIVO:LÍNEA: `grep "2026-03-04 05:0"` sobre `latest_consolidado_base.csv` y `snapshot_consolidado_base.csv` (insumos) con Láscar: 0 filas
- QUÉ PASA: con la tabla sola, la pasada NOAA-20 de las 05:30 sigue siendo negativo limpio con NTI -0,781.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: el grep de arriba.
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 2

### 121
- TÍTULO: La regla con que se adoptó K sigue igual: V1a-01 (P2 con tolerancia 0), V1a-04 (P3 no puede fallar en VIIRS), V1a-06 (veredicto según la referencia), 164 y 165 abiertos y sin uso pendiente
- ARCHIVO:LÍNEA: `git diff --stat d516b9d8c 752d348bc -- experiments/_s151_prereg_fk_11/` (sólo agrega `v1_cobertura/`); `.github/workflows/vigilancia-sombra.yml:135` (usa el paso 9 de la regla, no P2)
- QUÉ PASA: la debilidad de la regla no se corrigió, pero ningún A/B vigente la usa: la reversión de K la manda el paso 9.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: el `git diff` de arriba.
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 2

### 122
- TÍTULO: Inventario de S160 de VIIRS y unidades sin cambio: F2-210, F2-212, F2-230 a F2-235 y F2-236 abiertos (latentes o de forma)
- ARCHIVO:LÍNEA: `pipeline/store.py:74` (`BT_PHYSICAL_MAX_K = 500.0`, F2-210); `pipeline/process_viirs_mod.py:947` (`eti_for_second_pass = fp_diag.get("eti")`, F2-212); `pipeline/process_viirs.py:77` (unidad de `WOOSTER_COEFF`, F2-230); `frontend/index.html:2927-2928` (`111.0`, F2-231); `frontend/index.html:1162` (`innerKm = 10`) y `frontend/diario.html:265` (`?? 5`, F2-232); `frontend/index.html:798` (5 clases) contra `:2466-2467` y `:3618` (4 en la leyenda, F2-233); `pipeline/store.py:218` (`<= 0`) contra `scripts/run_pipeline.py:136` (`< 0.0`, F2-234); `pipeline/detection_context.py:508-510` (`np.std` sin `ddof`, F2-235)
- QUÉ PASA: ninguno cambió desde S160; ninguno torció una publicación medida (F2-210 y F2-236 inertes hoy).
- CÓMO SE VE EN EL DASHBOARD: F2-233 en la leyenda (sin «Muy Alto»); el resto invisible.
- CÓMO REPRODUCIRLO: `python -I ...\f0\f0_clasificador.py`, filas F2-*
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 1 a 2 (F2-210 y F2-212 2; el resto 1)

### 123
- TÍTULO: Inventario de S160 de dependencias sin cambio: 249, 251, 252, 254, 255 abiertos
- ARCHIVO:LÍNEA: `.github/workflows/nrt-retry.yml:5` y `:65` (sólo NASA_DOWN, 249); `pipeline/fetch.py:226` (`"versions": ["2.1", "2", "1"]`, 251); `requirements.txt:1` (`earthaccess>=0.9.0`, 252); `scripts/sync_mirova_csv.sh:110` (`WARN: rebuild $stem failed (continuing)`, 254); `.github/workflows/nrt-healthcheck.yml` cron `0 12 * * *` y SCRIPT:SALIDA `f0_cadencias_salida.txt` (49 corridas `schedule` creadas entre las 14:34 y las 20:59 UTC, huecos de hasta 27,8 h, 255)
- QUÉ PASA: ninguno cambió; ninguno es silencioso hoy.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -I ...\f0\f0_clasificador.py`, filas 249 a 256
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 1 a 2

### 124
- TÍTULO: 247 resuelto salvo un borde: un token «desconocido» (secret ausente o no-JWT) sigue sin abrir issue
- ARCHIVO:LÍNEA: `.github/workflows/nrt-healthcheck.yml` paso «Vencimiento del EARTHDATA_TOKEN», bloque Python: `if ESTADO == "desconocido":` → `print("Estado del token desconocido (secret ausente o no-JWT): sin issue.")`
- QUÉ PASA: la guarda de token vacío en `nrt.yml` (`79b4e3af6`, #894) hace que el NRT quede en rojo, así que el silencio ya no es posible; el healthcheck sigue sin issue propio.
- CÓMO SE VE EN EL DASHBOARD: el NRT en rojo y datos que dejan de llegar.
- CÓMO REPRODUCIRLO: `git show 752d348bc:.github/workflows/nrt-healthcheck.yml | grep -n desconocido`
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 1

### 125
- TÍTULO: 245 resuelto en parte por decisión de Nicolás: la copia que se encoge avisa en rojo y entra igual; hoy la unión de perdidas tiene 37 filas y ninguna alerta
- ARCHIVO:LÍNEA: `scripts/sync_mirova_csv.sh:32-36` en la base (`avisar_llaves_perdidas_consolidado.py ... || true` y luego `mv`); SCRIPT:SALIDA `f0_245_perdidas_vuelven_salida.txt`
- QUÉ PASA: las 1.948 claves perdidas de S160 volvieron a la copia o quedaron en la unión: `data/mirova_reference/union_historica/consolidado_filas_perdidas.csv` en la base tiene 37 filas (36 RUTINA, 1 FALSO_POSITIVO), 0 alertas fuera de la copia vigente; la alerta de Láscar MODIS 2026-02-09 07:20 (1,64 MW) está otra vez en `data/mirova/Lascar.json`.
- CÓMO SE VE EN EL DASHBOARD: hoy nada.
- CÓMO REPRODUCIRLO: `python -I ...\f0\f0_245_perdidas_vuelven.py`
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 1

### 126
- TÍTULO: Suomi NPP se calló unas 31 h antes del cese anunciado, en nuestros records y en MIROVA; el vigilante lo informó a las 54 h del cese
- ARCHIVO:LÍNEA: SCRIPT:SALIDA `f0_pasadas_por_satelite_salida.txt` secciones 1, 3 y 4b; issue #943 (2026-11-04T19:01:09Z)
- QUÉ PASA: el último record Suomi NPP es del 2026-11-01 06:18 a 06:24 UTC; la noche del 2026-11-02 (antes de las 13:00) no hay pasada Suomi NPP ni nuestra ni en la tabla de MIROVA (las filas VIIRS 375 nocturnas de esa noche parean con NOAA-20 y NOAA-21). Después del cese, 0 filas VIIRS nocturnas de MIROVA quedan sin record nuestro salvo una de VIIRS 750 por borde de gránulo (Láscar 2026-11-04 05:42, record a 361 s). C-06 tiene respuesta: la vigilancia funcionó.
- CÓMO SE VE EN EL DASHBOARD: aviso de cese cargado en las tres vistas (`cese_plataformas.js`); serie sin la tercera plataforma desde el 1-nov.
- CÓMO REPRODUCIRLO: `python -I ...\f0\f0_pasadas_por_satelite.py`
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 1

### 127
- TÍTULO: Decisión 2 resuelta por otra vía: P2 se recalibró (D-42, D-45) y D25 se leyó y no se adoptó; el placebo del 1 % que pedía S160 nunca entró al evaluador
- ARCHIVO:LÍNEA: `docs/MIROVA_DIVERGENCES.md` l. 2863 (`c8423ce9a`); `experiments/_s157_prereg_d25/evaluar_d25.py` en la base (placebos sólo `PLACEBO_GANANCIAS = (1.2, 0.8)`, l. 112; ninguno que apague al azar el 1 %); `d7d36aa3e` sólo toca `tasks/LOOP_OBJETIVOS.md`
- QUÉ PASA: lo que la decisión quería evitar (adoptar D25 con una P2 que aprueba un placebo) no ocurrió; el control concreto no existe.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git show 752d348bc:experiments/_s157_prereg_d25/evaluar_d25.py | grep -n -i placebo`
- CONFIANZA: CONFIRMADO
- GRAVEDAD 1-5: 1

### 128
- TÍTULO: V1a-05 en parte: la cobertura del intento de V1 llegó a main; que estén los datos con que se adoptó K, SIN VERIFICAR
- ARCHIVO:LÍNEA: `experiments/_s151_prereg_fk_11/v1_cobertura/` (agregado en `dab267552`, 2026-10-16, entró a main después de `d516b9d8c`)
- QUÉ PASA: no abrí el contenido ni lo crucé con el veredicto.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git log --format="%h %cs %s" d516b9d8c..752d348bc -- experiments/_s151_prereg_fk_11/v1_cobertura`
- CONFIANZA: SOSPECHA
- GRAVEDAD 1-5: 1

### 129
- TÍTULO: Los 12 pendientes de proceso de F1b (183 a 187, 190 a 196) siguen como se escribieron: son historia de experimentos cerrados y no tienen arreglo en código
- ARCHIVO:LÍNEA: `git diff --stat d516b9d8c 752d348bc -- experiments/_s126_lib.py experiments/_s125_magnitud/02_veredicto_ab.py docs/S125_AB_MAGNITUD_PREREGISTRO.md experiments/_s150_ndc experiments/_s149_prereg_invierno experiments/_s136 docs/CIERRE_FRENTE_KEEP_PEAK_S144.md experiments/_s151_presupuesto_magnitud experiments/_s150_ab_d22 docs/S148_RESULTADO_AB_CONECTIVA.md experiments/_s143_evaluador` → vacío
- QUÉ PASA: ningún archivo citado cambió; los veredictos que sostienen (NO ADOPTAR viejos) siguen con esos defectos de proceso a la vista. No rehíce sus números.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: el `git diff` de arriba.
- CONFIANZA: CONFIRMADO que no cambiaron; su contenido, el de S160 sin verificador
- GRAVEDAD 1-5: 1

## 5. Clasificación completa de la lista §1 fila F0

Salida cruda: `f0_clasificador_salida.txt` (estado en S160 y en la base) más las mediciones de arriba.

| pendiente | estado en la base | evidencia | hallazgo |
|---|---|---|---|
| 241 | resuelto en parte | `c3ee70ed6` (#897), `ccb378425` (#909); código 0 en estricto | 112 |
| 242 | resuelto | `3489e55c3` (#892) | limpio |
| C-06 | respondido en el mundo, abierto en el documento | 0 records SNPP tras el cese; #943 | 108, 126 |
| 243 | abierto | sin vigilante; 0 % NRT hasta octubre | 111 |
| 245 | resuelto en parte (por decisión) | `2ba670463` (#896); unión 37 filas, 0 alertas | 125 |
| 247 | resuelto | `79b4e3af6` (#894); borde «desconocido» | 124 |
| V3-01 | resuelto | `79b4e3af6` (#894) | limpio |
| V3-02 | abierto | `medir_cadencia_cron.py:69` | 113 |
| V3-03 | resuelto | `79b4e3af6` (#894) | limpio |
| V3-04 | nunca fue defecto del sistema | era del simulador de S160 F3 | limpio |
| token | abierto con fecha | rotar antes del 2026-11-27 | 107 |
| 203 | abierto, sin camino | 11 de 58 tras S160; D25 no adoptada | 101 |
| C-08 | abierto | cola de campo sin tocar | 108 |
| F1-H6 (D32) | abierto | catálogo | 102 |
| V2-09 | abierto | `profile.py:610` | 106 |
| V2-10 | abierto | `process_viirs_mod.py:1106`, `index.html:3159` | 116 |
| V2-11 | abierto | `index.html:2490` | 117 |
| V2-12 | abierto (latente) | `store.py:559` antes de `:564` | 118 |
| V2-13 | SIN DATO | el CSV nunca entró a git ni sigue en disco | 114 |
| C-02, C-03 | abiertos | cola de campo sin tocar | 108 |
| decisión 2 | resuelta por otra vía | `c8423ce9a`, D-42, D-45 | 127 |
| decisión 6 | abierta | C-10 «abierto» | 103 |
| decisión 9 | abierta | K1 -0,8, acople vigente | 104 |
| V0b-01 | abierto (latente) | igual que decisión 9 | 104 |
| V0b-02 | abierto | alerta fuera de la tabla | 120 |
| V0b-03 | abierto | `process_viirs.py:1341` | 119 |
| V1a-01, V1a-04, V1a-06 | abiertos, sin uso pendiente | regla sin cambios | 121 |
| V1a-02, V1a-03 | nunca fueron defecto | confirmación y atribución | limpio |
| V1a-05 | en parte (SOSPECHA) | `dab267552` | 128 |
| V1b-01 | abierto | igual que C-10 | 103 |
| V0a-01 | resuelto | D34 en el catálogo de main (autoría `af369ebd7`, S158) | limpio |
| C-07 | abierto | igual que V0b-01 | 104 |
| C-09 | abierto | fila OCR sigue | 105 |
| C-10 | abierto | fila sigue, record 0,14 MW a 3,2 km | 103 |
| F1a 164, 165 | abiertos, sin uso pendiente | regla sin cambios | 121 |
| F1a 166 | abierto | `auto_audit_weekly.py:120` | 115 |
| F2 210, 212, 230 a 236 | abiertos (latentes o de forma) | código sin cambio | 122 |
| F3 249, 251, 252, 254, 255 | abiertos | código sin cambio | 123 |
| F3 250 | resuelto | `ccb378425` (#909) | limpio |
| F3 256 | resuelto | `6547f5315` (#895), `guarda_llaves_consolidado.py` sale 1 sin columnas de llave | limpio |
| F1b 183 a 187, 190 a 196 | historia, sin cambio | `git diff` vacío | 129 |
| F4 292, 294 a 297 | fuera de alcance (F3 de S175) | | |

## 6. Pasadas por satélite (mejora 5 de S174)

Pasadas con record por satélite y semana ISO, 11 Tier A, base `752d348bc` (W45 parcial, hasta el 2026-11-07 01:15):

| satélite | W38 | W39 | W40 | W41 | W42 | W43 | W44 | W45 |
|---|---|---|---|---|---|---|---|---|
| MODIS_AQUA | 78 | 88 | 86 | 82 | 87 | 81 | 85 | 57 |
| MODIS_TERRA | 79 | 85 | **54** | 72 | 84 | 87 | 85 | 64 |
| VIIRS_NOAA20 | 121 | 107 | 103 | 121 | 109 | 102 | 121 | 76 |
| VIIRS_NOAA21 | 102 | 115 | 112 | 103 | 90 | 117 | 100 | 82 |
| VIIRS_SNPP | 111 | 103 | 124 | 110 | 94 | 93 | 117 | **0** |

(Las columnas `_750` siguen a su satélite con diferencias de 0 a 3; tabla completa en la salida.) Último record de cada
satélite por volcán contra la última fila de MIROVA del mismo sensor: en los 11 volcanes MODIS y VIIRS de NOAA-20 y
NOAA-21 quedan entre 4,9 h por delante y 19,8 h detrás de la última fila de MIROVA (que incluye pasadas diurnas que el NRT no procesa);
Suomi NPP 132,9 h. VIIRS 750 de MIROVA se llama «VIIRS» en la tabla (el instrumento lo mapea).

## 7. SEGUIMIENTOS (fuera de mi eje)

- **7 de 50 corridas del NRT en rojo** entre el 2026-11-04 02:10 y el 2026-11-05 11:10 UTC (insumos `runs_nrt.json`); en
  la corrida 42016780200 fallan `process (Villarrica)` y `process (Copahue)` en el paso «Run VRP pipeline:
  mirova_equivalent profile». Causa SIN DATO. Ninguna en rojo después del 2026-11-05 11:10. CONFIRMADO el conteo.
  Gravedad probable 2. Es de F1 si es MODIS.
- **MODIS: 2 cúmulos de cumbre en 0,0 MW con alerta de MIROVA** (etiqueta `pos`) entre el 2026-10-22 y el 2026-11-02,
  y 1 en la ventana K (`f0_203_cumbre_cero_salida.txt`). No los identifiqué. Es el eje de F1 (vía MODIS). SOSPECHA de
  que sea el mismo recorte de 203 en la vía. Reproducir con `f0_203_cumbre_cero.py` agregando el listado para MODIS.
- **Pareo a 120 s contra el borde de gránulo**: filas de MIROVA con record nuestro a 300 s (MODIS, gránulo de 5 min) o
  361 s (VIIRS 750, gránulo de 6 min) cuentan como «sin record». Ejemplos: Copahue MODIS 2026-09-14 07:40, Láscar VIIRS
  750 2026-11-04 05:42. Es el eje de F5 (identidad del pareo). CONFIRMADO.
- **IDs C-NN repetidos entre auditorías**: `docs/audit_s146/FRENTE_C_CIERRES_CON_PAPER.md` usa C-07, C-08, C-09 y C-10
  para otras cosas que la cola de campo de S160 (git grep de los IDs). Un `grep C-10` mezcla las dos. Gravedad 1.
- **La copia de la referencia que lee el banco** (`mirova_v1_snapshot/registro_vrp_consolidado.csv`) termina el
  2026-11-02, así que desde el 2026-11-03 no hay etiquetas en el banco (lo dijo F2; lo reencontré: ventana del 3 al 7 de
  noviembre, todo `sin_info`).

## 8. VERIFICADO LIMPIO

| qué | comando | vara |
|---|---|---|
| Decisión 1: preámbulo en main con la regla del CSV | `f0_clasificador.py` fila dec1 (`0d73f2a4e`) | `docs/_prompts/PREAMBULO-AUDITOR.md:119` en la base |
| 242: vigilante por plataforma en el healthcheck diario | fila 242 (`3489e55c3`); issue #943 | `nrt-healthcheck.yml:301` |
| 247 y V3-03: guarda de token vacío en los dos pasos de `nrt.yml` | fila 247 (`79b4e3af6`) | `nrt.yml:192` y el paso experimental |
| Workflows con cron que usan el token: `experimental-diario`, `guardia-k-modis`, `sombra-34`, `sombra-codigo-mirova` tienen la guarda; `audit-weekly`, `nrt-healthcheck`, `nrt-monitor` no la tienen pero no pasan usuario ni clave | bucle `grep` sobre `.github/workflows/*.yml` de la instantánea | A71: el riesgo es el par usuario y clave |
| V3-01: aviso de protegida sin record | fila V3-01 (`79b4e3af6`) | `auto_audit_weekly.py:1028` y `:1216` |
| 250: L1B sin geolocalización como incidencia | fila 250 (`ccb378425`) | `run_pipeline.py:392-398` |
| 256: un 200 con HTML no se commitea | fila 256 (`6547f5315`) | `guarda_llaves_consolidado.py` sale 1 sin columnas de llave, `sync-mirova-csv.yml:111` |
| V0a-01: D34 en el catálogo de main | fila V0a-01 | `docs/MIROVA_DIVERGENCES.md:3400` |
| Suomi NPP sin records tras el cese y sin pasadas que MIROVA tenga y nosotros no | `f0_pasadas_por_satelite.py` secciones 1 y 4 | records de la base contra la tabla y el OCR de la base |
| VIIRS 375 y 750 nocturno: 0 a 2 filas de MIROVA por semana sin record nuestro en 12 semanas, todas por borde de gránulo | sección 4 y 4c | la misma |
| Upgrade NRT a Standard de MODIS funcionando de abril a octubre (0 % NRT) | `f0_proporcion_nrt_modis.py` | `store.py` auto-upgrade |
| Aviso de cese cargado en index, diario y mosaico | `grep cese_plataformas.js frontend/*.html` | S159 |

## 9. SIN DATO

- V2-13: el `hallazgos.csv` de S160 F2 no está en git ni en `C:\vrp-trabajo\s159-pruebas\`.
- C-02, C-03, C-07, C-08, C-09, C-10: piden mirar láminas o imágenes de MIROVA; no lo hice.
- Causa de las pasadas MODIS sin record del 28-sep, 2-oct y 10-oct (gránulo no publicado, descarga fallida o descarte).
- La fecha de vencimiento real del token (no leí el JWT; uso la del registro).
- El efecto en lo publicado de V0b-03, F2-212 y V2-09.
- `noches_sin_datos` antes del 2026-10-12: el campo no existe en los `latest.json` anteriores.

## 10. FUERA DE ALCANCE

- Arreglos de cualquier cosa de arriba (A45 para `pipeline/`): los decide quien orquesta.
- 201 y C-04 (F2 de S175); 281 a 297 sin aplicar, 287, 288, U12, V4-01 a V4-03 y decisión 8 (F3 de S175); C-05 (cola sin
  frente).
- El código del scraper Mirova-v1.
