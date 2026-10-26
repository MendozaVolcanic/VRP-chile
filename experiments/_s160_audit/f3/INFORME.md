# F3: dependencias externas con fecha de vencimiento (auditoría S160)

## 1. Encabezado

- Hora del servidor: GitHub `Date: Thu, 22 Oct 2026 03:11:55 GMT` (insumos del orquestador); CMR respondió mi consulta a las
  2026-10-22 03:27:41 UTC. Toda edad «al cierre» se mide contra 03:11:55 UTC.
- Commit medido: `origin/main` = `d516b9d8c0fad5b0ca458b9fb57cdf5e6f75f956`, instantánea en
  `D:\vrp-trabajo\temporales\s160_audit\main\` (código y datos extraídos con `git archive`). Aparte, PR #889 en
  `origin/s159-instrumentos` = `d0968e389`, extraído con `git archive` a `D:\vrp-trabajo\temporales\s160_audit\f3\arbol_889\`
  (sólo `pipeline`, `scripts`, `volcanoes.yaml`, `frontend/index.html`). Y la rama local `s159-cese-snpp` leída en el
  worktree `C:\vrp-trabajo\s159-instrumentos` tal como estaba el 2026-10-22 03:08 a 03:10 UTC (mtime de sus archivos;
  otra sesión la edita, puede haber cambiado).
- Modelo y esfuerzo: Fable 5.1, `high`.
- CARPETA: `C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\f3\` (informe, scripts y salidas); pesado en
  `D:\vrp-trabajo\temporales\s160_audit\f3\` (árbol de #889, lista de commits, temporales del simulador, 3,4 MB).
- Referencia congelada usada: tabla sola `latest_consolidado.csv` sha256 `bc1522c24c924cb5…` (42.410 filas); OCR
  `data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv` sha256 `94679246acbd0db5…` (1.122 filas). Las dos coinciden
  con las del preámbulo. En este frente no hay cifra de paridad: las dos versiones se usan sólo para medir frescura y huecos.
- Llamadas a la API de GitHub: 3 de 10 (`gh run list` del healthcheck, `gh issue list`, `gh api rate_limit`, que dio 4.844
  restantes). Consultas públicas a CMR: 44 de 150. Ninguna autenticación contra Earthdata. Ningún workflow despachado.
  Nada escrito en `data/`. Disco al cerrar: C: 14 GB libres, D: 11 GB.
- **Qué NO miré**, para que el silencio no se lea como «todo bien»: el código del scraper Mirova-v1 (otra sesión); el
  contenido de la rama `s159-cese-snpp` más allá de qué cubre y qué deja fuera (no corrí sus tests ni propuse cambios); la
  versión de `earthaccess` instalada en el último run del NRT (habría costado leer un log por API; SIN DATO); si LANCE corta
  también el NRT de Suomi NPP el 2-nov (sigue SOSPECHA de S159); el deploy de GitHub Pages (sin llamadas); la configuración
  de avisos de cron-job.org (no tengo acceso); los workflows `probe-*` y `reproc-*` (no son producción); las 34 ramas
  `origin/s146-ab/*`.

## 2. En una pantalla

1. **H3 se confirma en las dos partes.** Además de Suomi NPP, cualquier plataforma o colección que CMR deje de servir
   (NOAA-20 callado, NOAA-21 renumerado, MODIS 6.1 entera, «todo vacío» como el 2026-10-18) deja el NRT en verde con
   «Cobertura: completa» y código 0; medido con el código real de `d516b9d8c` en 14 escenarios (hallazgo 241).
2. **El arreglo de Suomi NPP existe pero no está ni en `origin` ni en `main`** a 11 días del cese; cubre la ausencia por
   plataforma a 72 h (medida por su autor) y el aviso del tablero; deja fuera el mensaje «completa», la versión de colección
   y la referencia (242). PR #889 cambia el mensaje a «NO COMPLETA» pero el código sigue 0 y el encabezado se satura: toda
   corrida del NRT lo dice, porque siempre procesa el día en curso (244).
3. **La referencia se encoge en silencio**: la copia horaria aceptó 7 copias con menos filas en 64 días (hasta 659 líneas),
   porque valida el OCR pero no la tabla; y corre 5,2 veces por día de 24, con huecos de hasta 22,7 h (245, 246).
4. **La única fecha dura con vigilante es el token** (vence 2026-12-07 18:03 UTC; issue desde 2026-11-27, medido con JWT
   sintéticos). Sus huecos: secret ausente da «desconocido» sin issue, y `nrt.yml` no tiene la guarda de token vacío que
   `experimental-diario.yml` sí tiene: con token vacío hace 8 logins con el par vencido y bloquea la cuenta (247).
5. **MODIS 6.1 tiene decomiso anunciado y no ejecutado** (CMR: ACTIVE, 8 a 11 gránulos en 48 h); cuando se ejecute, el
   Standard cae al NRT en silencio y nadie mide la proporción de records NRT (243). El resto (CMR, LANCE, cadencia) degrada
   con aviso en el resumen del run, sin issue (248, 249).

## 3. Hallazgos (IDs 241 a 256; ordenados por gravedad)

### 241. Toda plataforma o colección que calle en CMR se lee como «no hubo pasada»: cobertura «completa», código 0, sin falla

- **ARCHIVO:LÍNEA**: `pipeline/fetch.py:770-800` (`search_granules`: prueba Standard y luego NRT por `_intentos()`, y si
  todas vienen vacías devuelve `[]` sin `_registrar_falla`); `pipeline/fetch.py:1087-1088` (`if not l1b_granules: continue`);
  `pipeline/fetch.py:218-225` (NOAA-21: `"versions": ["2.1"]`, sin alternativa); `scripts/run_pipeline.py:402-418`
  (`informar_cobertura` con lista vacía imprime «Cobertura: completa» y devuelve 0); `scripts/run_pipeline.py:547-550` (el NRT
  no pasa `--estricto-cobertura`).
- **SCRIPT:SALIDA**: `simular_dependencias.py` → `simular_dependencias_salida.txt` (bloque `##### MAIN d516b9d8c`). Sin red:
  reemplaza `earthaccess.search_data`, `.download`, `.login`, el probe TCP y `time.sleep`; llama al `fetch_for_volcano` real
  (Villarrica, 2026-11-05, `nighttime_only=False`) y después a `informar_cobertura` como lo hace `run_pipeline.main`.
  Pregunta 1: si el pipeline viera la caída, aparecería una falla, una incidencia, una excepción o un código distinto de 0.
  Pregunta 2: los cuatro controles del plan se reproducen antes de leer el resto: SNPP vacío = completa y 0; SNPP timeout =
  INCOMPLETA y 0; todo vacío = completa (R2-9); L1B sin geo = descartado sin falla (VB-1). Contraste: «vivo» da las 8
  plataformas.

  | escenario (main) | plataformas con resultado | fallas | mensaje | código NRT | código `--estricto` |
  |---|---|---|---|---|---|
  | vivo (contraste) | 8 | 0 | completa | 0 | 0 |
  | snpp_vacio (2-nov) | 6 | 0 | **completa** | **0** | 0 |
  | snpp_timeout (control) | 2 | 6 | INCOMPLETA | 0 | 3 |
  | noaa21_version_cambia | 6 | 0 | **completa** | **0** | 0 |
  | noaa20_vacio | 6 | 0 | **completa** | **0** | 0 |
  | modis61_decomiso (Standard vacío, NRT sigue) | 6 (sin MODIS: el gránulo NRT simulado no se descarga porque el simulador sólo entrega Standard; ver 243) | 0 | **completa** | **0** | 0 |
  | modis61_y_nrt_vacios | 6 | 0 | **completa** | **0** | 0 |
  | todo_vacio (R2-9, como el 2026-10-18) | 0 | 0 | **completa** | **0** | 0 |

  En `noaa21_version_cambia` el simulador cuenta las consultas: `VJ202IMG 2.1`, `VJ202IMG_NRT 2.1`, `VJ202MOD 2.1`,
  `VJ202MOD_NRT 2.1`, una cada una; ninguna otra versión se prueba.
- **QUÉ PASA**: un satélite que deja de transmitir, una colección renumerada en CMR o un catálogo vacío producen la misma
  respuesta que una noche en que el satélite no pasó sobre el volcán: cero gránulos. El código no tiene modelo de órbita
  para distinguirlas, y por diseño (comentario en `fetch.py:179-181`) una colección inexistente «no da error, da CERO
  granules». El NRT sigue con las plataformas restantes y declara cobertura completa. Lo nuevo respecto de S159 (H1): el
  mecanismo no es de Suomi NPP, es de **todas** las plataformas, y NOAA-21, que NESDIS declara primaria desde el cese, está
  atada a una sola cadena de versión.
- **CÓMO SE VE EN EL DASHBOARD**: la serie de esa plataforma desaparece de la leyenda sin mensaje (S159 lo ubicó en
  `frontend/index.html:3196-3212`, series agregadas sólo `if (snpp375.length)`); el contador «monitoreado · última pasada hace
  X» sigue verde mientras cualquier otra plataforma entregue (`index.html:1863`). Si callara NOAA-21, el operador vería menos
  puntos por noche y lo leería como el volcán, no como el satélite.
- **CÓMO REPRODUCIRLO**: `cd C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\f3 && set F3_TMP=D:\vrp-trabajo\temporales\s160_audit\f3\tmp_sim && PYTHONIOENCODING=utf-8 python -I simular_dependencias.py D:\vrp-trabajo\temporales\s160_audit\main`.
  En producción, el 3-nov el log de `nrt.yml` mostrará `SEARCH_DONE VIIRS_SNPP n_l1b=0` y «Cobertura: completa».
- **CONFIANZA**: CONFIRMADO (leído y simulado con el código de `d516b9d8c`). Que CMR vaya a renumerar NOAA-21 o que LANCE
  corte el NRT de SNPP es SOSPECHA; el comportamiento del pipeline ante el cero es el mismo.
- **GRAVEDAD**: 5. Para Suomi NPP solo, S159 midió 1 noche neta con alerta de MIROVA perdida en 33 días (gravedad 4 allá);
  acá sube a 5 porque el mismo cero deja mudas a NOAA-21 (primaria desde el 2-nov) y a NOAA-20 sin que ningún vigilante de
  `main` lo vea (242), y porque el «todo vacío» ya ocurrió (2026-10-18, R2-13).

### 242. El arreglo del cese de Suomi NPP vive en una rama local sin push a 11 días del cese; cubre la ausencia por plataforma a 72 h y el aviso del tablero; deja fuera el mensaje «completa», la versión de colección y la referencia

- **ARCHIVO:LÍNEA** (worktree `C:\vrp-trabajo\s159-instrumentos`, rama `s159-cese-snpp`, visto 2026-10-22 03:08 a 03:10 UTC,
  `git status --short`: 14 archivos modificados o nuevos, sin commit sobre `d516b9d8c`; `git ls-remote origin
  s159-cese-snpp` vacío según el plan §11.1.3, no lo repetí para no gastar API): `scripts/vigilar_plataformas.py:84`
  (`VENTANA_H = 72`), `:128-180` (`evaluar`: `ok`, `alarma`, `caida_general`), `:206-240` (`planear_issues`: cese esperado
  = un issue informativo una vez; otra plataforma = alarma, comentada y cerrada al volver; todas calladas = nada, lo cubre la
  frescura); `scripts/ceses_esperados.json` (Suomi NPP, `2026-11-02T13:00:00Z`, fuente NASA); `.github/workflows/nrt-healthcheck.yml`
  +280 a +302 (paso «Vigilancia por plataforma», `if: always()`, `python scripts/vigilar_plataformas.py --issues`);
  `frontend/cese_plataformas.js:30-33` (`CESE_UTC`, aviso previo y 90 días después, línea vertical); `frontend/index.html`,
  `diario.html`, `mosaico.html` modificados; `tests/test_cese_plataformas_s159.py` (exige que las dos fechas coincidan) y
  `tests/test_vigilar_plataformas_s159.py`; `experiments/_s159/vigilar_plataformas/medicion.txt` (ventana medida).
- **QUÉ CUBRE** (leído, no ejecutado): la ausencia de records de una plataforma en 72 h sobre los 11 Tier A, con la
  distinción cese anunciado (informativo, una vez) contra cualquier otra plataforma (alarma). Su ventana está medida contra
  los datos: con 48 h habría alarmado 13 días por SNPP y 0 por las otras cuatro; con 72 h, 8 y 0 (`medicion.txt`, 266 días
  desde 2026-01-29). El tablero avisa antes y después del cese.
- **QUÉ DEJA FUERA** (y que esta auditoría mide): (a) el mensaje «Cobertura: completa» y el código 0 del NRT (241; es el
  terreno de #889, ver 244); (b) la causa: ve la ausencia, no distingue satélite caído de colección renumerada (lo declara en
  su ficha, «Limitaciones», y en el caso de NOAA-21 alarmaría igual, que es lo que importa); (c) una plataforma que entregue
  menos pasadas (declarado); (d) la referencia de MIROVA (245, 246); (e) la latencia: corre sólo dentro del healthcheck, que
  arranca 2,5 a 6 h tarde (255), así que el issue informativo del cese llegaría hacia el 5-nov por la tarde UTC; (f) no está
  en `origin`: si la sesión que lo edita se corta, el 2-nov pasa con `main` tal como está.
- **CÓMO SE VE EN EL DASHBOARD**: con la rama, el aviso de `cese_plataformas.js`; sin ella, nada (241).
- **CÓMO REPRODUCIRLO**: `git -C C:\vrp-trabajo\s159-instrumentos status --short` y `git -C C:\vrp-trabajo\s159-instrumentos diff d516b9d8c --stat`.
- **CONFIANZA**: CONFIRMADO en lo que cubre y deja fuera (leído); el estado «sin push» es el del plan §11.1.3 más la ausencia
  de commit local que vi; puede haber cambiado desde las 03:10 UTC.
- **GRAVEDAD**: 4 (apaga una vigilancia si no llega a `main` antes del 2-nov; no propongo el arreglo, ya está en curso).

### 243. MODIS Colección 6.1 con decomiso anunciado y no ejecutado: el Standard cae al NRT en silencio y nadie mide cuánto; si LANCE 6.1 también cierra, MODIS entero calla

- **ARCHIVO:LÍNEA**: `pipeline/fetch.py:187-194` (pide sólo `6.1` y `6.1NRT`; la Colección 7 no se pide);
  `experiments/_s159/biblio_2026/INFORME.md` §0 punto 2, TEXTO: «MODIS Colección 6.1, la que pedimos, tiene decomiso
  anunciado para el 30-sep-2026 (LAADS 199534, 17-mar-2026)»; `cmr_estado_colecciones_salida.txt`.
- **SCRIPT:SALIDA**: `cmr_estado_colecciones.py` → `cmr_estado_colecciones_salida.txt` (44 consultas públicas, 2026-10-22
  03:27 UTC, bbox -76,-46,-66,-17, gránulos con inicio en las últimas 48 h). Pregunta 1: una colección cesada tendría
  `EndingDateTime`, `CollectionProgress` distinto de ACTIVE o 0 gránulos recientes. Pregunta 2: un error de red imprime
  ERROR, no 0. Control positivo: `MYD021KM_NRT` (nombre inexistente de antes de S133) da «0 col» y 0 gránulos, que es
  exactamente lo que el pipeline vería como «no hay dato».

  | colección | versiones en CMR (progress) | gránulos 48 h en la versión pedida |
  |---|---|---|
  | MOD021KM, MOD03 | v7 LAADS ACTIVE; v6.1 LAADS ACTIVE; v6.1NRT LANCEMODIS ACTIVE | 6.1: 8 y 11; 6.1NRT: 15 y 16 |
  | MYD021KM, MYD03 | idem | 6.1: 11 y 11; 6.1NRT: 15 y 15 |
  | VNP02IMG, VNP02MOD (+_NRT) | v2 ACTIVE, sin EndingDateTime, a 11 días del cese | 14 y 15 cada una |
  | VJ102IMG, VJ102MOD (+_NRT) | sólo v2.1 ACTIVE; v2 y v1 no existen | 2.1: 12 y 16; v2: 0; v1: 0 |
  | VJ202IMG, VJ202MOD (+_NRT) | sólo v2.1 ACTIVE | 14 y 19 |

  Y `simular_dependencias.py`, escenario `modis61_decomiso`: las consultas son `MOD021KM 6.1`, `MOD021KM 6.1NRT`,
  `MYD021KM 6.1`, `MYD021KM 6.1NRT`; «Cobertura: completa», código 0. (En ese escenario mi simulador no entrega gránulo NRT,
  así que MODIS sale sin resultado; lo que mide es que la caída al NRT no deja rastro en la cobertura, no que el NRT falle.)
- **QUÉ PASA**: la Colección 6.1 es la que el proyecto calibró contra MIROVA (coeficientes S14 por sensor). NASA anunció su
  decomiso para el 2026-09-30 y tres semanas después sigue produciendo; cuando lo ejecute, cada día el Standard dará cero y
  el pipeline tomará el NRT 6.1 de LANCE, que existe y es correcto, pero (a) `product_version` quedará `nrt` para siempre (el
  auto-upgrade a Standard de `store.py` nunca encontrará Standard) y nadie mide esa proporción; (b) la Colección 7 ya corre en
  Standard sin NRT, así que el día que LANCE pase a 7 o cierre 6.1NRT, MODIS entero da cero gránulos y cae en 241.
- **CÓMO SE VE EN EL DASHBOARD**: invisible en la primera fase (el dato sigue, con el delta NRT contra Standard que CLAUDE.md
  da por «<0.1K, despreciable»); en la segunda, la serie MODIS desaparece sin mensaje y la sombra avisa por bucket a los 3
  días (`vigilancia_sombra.py:362-392`, issue vía `vigilancia-sombra.yml`): es el único vigilante de `main` que lo vería.
- **CÓMO REPRODUCIRLO**: `python -I cmr_estado_colecciones.py` y el simulador (escenarios `modis61_decomiso`,
  `modis61_y_nrt_vacios`).
- **CONFIANZA**: CONFIRMADO el estado en CMR y el comportamiento del código; la fecha de ejecución del decomiso es SIN DATO
  (NASA no la cumplió).
- **GRAVEDAD**: 4 (apaga MODIS, el sensor con el que MIROVA publica Láscar, sin falla; la sombra lo ve a los 3 días, el NRT
  nunca).

### 245. La copia horaria de la tabla de MIROVA acepta copias que se encogen y las propaga al tablero; el OCR sí tiene la defensa

- **ARCHIVO:LÍNEA**: `.github/workflows/sync-mirova-csv.yml:65-84` (consolidado: `curl -fsSL` a un `.new`, `cmp -s`, y si
  difiere `mv` sin mirar líneas ni cabecera) contra `:106-112` (OCR: «Vacío / sin la cabecera esperada / más corto que lo
  que ya tenemos: el registro de MIROVA sólo crece, así que encogerse es truncamiento») y `:199-205` (el OCR malo deja la
  corrida en rojo); `:139-172` (reconstrucción de `data/mirova/<Vol>.json` desde el consolidado encogido, con `|| echo WARN
  ... (continuing)`); `frontend/index.html:992` (lee `data/mirova/`); `frontend/diario.html:209` (lee el CSV directo).
- **SCRIPT:SALIDA**: `medir_encogimientos_consolidado.py` → `medir_encogimientos_consolidado_salida.txt`. Lee con `git show`
  las 400 últimas versiones commiteadas de `latest_consolidado.csv` (2026-08-18 23:33 a 2026-10-21 04:45 UTC) y cuenta
  líneas. Pregunta 1: si el sync aceptara copias encogidas, habría commits con menos líneas que el anterior. Pregunta 2: un
  `git show` fallido imprime SIN DATO, no 0. Control positivo: el encogimiento del 2026-10-18 (`0c8848ff9`, 630 bajas netas
  según S159) tiene que aparecer, y aparece con -630.

  | commit | fecha UTC | líneas antes → después |
  |---|---|---|
  | 0e2dff5b2 | 2026-08-19 19:52 | 34.080 → 33.421 (-659) |
  | 190d2f2fa | 2026-08-25 19:55 | 34.432 → 34.230 (-202) |
  | faf444123 | 2026-08-26 19:18 | 34.392 → 34.206 (-186) |
  | 283d744e2 | 2026-10-06 02:57 | 41.333 → 41.170 (-163) |
  | 595ba6a00 | 2026-10-16 21:25 | 42.909 → 42.394 (-515) |
  | a7a9b2c97 | 2026-10-17 22:17 | 42.448 → 42.357 (-91) |
  | 0c8848ff9 | 2026-10-18 18:04 | 42.509 → 41.879 (-630) |

  7 encogimientos aceptados en 64 días (400 commits). Los conteos por fila (1.948 bajas netas, 14 protegidas, 2 que
  desaparecen del tablero, ninguna repuesta) son de `experiments/_s159/referencia_estable/verificador/INFORME.md` §1 y no
  los repetí; la pérdida es del CSV del scraper (otra sesión lo audita). Lo que es de VRP y de este frente es que **la copia
  no se defiende**, con el ejemplo en el mismo archivo: el canal OCR sí.
- **QUÉ PASA**: la referencia es lo que convierte una detección nuestra en «MIROVA también la vio» o «MIROVA no vio nada».
  Cada fila que se pierde deja una noche sin su hoja de respuestas: el auto-audit y la sombra la recuperan por la unión
  histórica (regenerada en la misma corrida, S159 verificador §2), pero `data/mirova/<Vol>.json`, que es lo que el tablero
  pinta, se reconstruye desde el CSV encogido. Dos alertas protegidas de Láscar MODIS (2026-02-09 07:20 y 2026-04-05 01:35)
  ya no están en el tablero.
- **CÓMO SE VE EN EL DASHBOARD**: triángulos amarillos de MIROVA que estaban y ya no están; una noche con detección nuestra
  pasa de «MIROVA también» a «sólo nosotros». No hay banner: `renderMirovaFreshness` (`index.html:3960-3990`) mira sólo la
  fecha más reciente (> 14 días), no el tamaño.
- **CÓMO REPRODUCIRLO**: `cd C:\vrp-trabajo\s159-pruebas && git log --format='%h %cI' -n 400 -- latest_consolidado.csv > D:\vrp-trabajo\temporales\s160_audit\f3\consolidado_commits.txt && python -I experiments\_s160_audit\f3\medir_encogimientos_consolidado.py . D:\vrp-trabajo\temporales\s160_audit\f3\consolidado_commits.txt`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 4 (no borra alertas nuestras; borra la hoja de respuestas contra la que se decide si somos réplica, y lo
  hace sin rojo ni issue).

### 244. PR #889 cambia «completa» por «NO COMPLETA» pero el código sigue 0 y el encabezado se satura: toda corrida del NRT lo dice

- **ARCHIVO:LÍNEA** (`origin/s159-instrumentos` `d0968e389`, leído con `git diff d516b9d8c...d0968e389`):
  `pipeline/fetch.py` (nuevo bloque S159 I1): `TIPOS_INCIDENCIA = {"sin_granulos": False, "sin_geolocalizacion": True,
  "dia_parcial": True}`; `dia_incompleto(date, ahora)` marca el día en curso más 3 h; en `fetch_for_volcano` se registra
  `dia_parcial` una vez por volcán y día, `sin_granulos` cuando una búsqueda responde vacía sin falla previa, y
  `sin_geolocalizacion` cuando `_match_granules` descarta. `scripts/run_pipeline.py::informar_cobertura`: «Cobertura NO
  COMPLETA: N incidencias» si hay incidencias y no fallas; `return 3 if (estricto and cuenta_estricto) else 0`; el docstring
  dice TEXTO: «Sin modo estricto el código de salida sigue en 0».
- **SCRIPT:SALIDA**: `simular_dependencias.py` sobre `arbol_889` → bloque `##### PR889 d0968e389` de
  `simular_dependencias_salida.txt`. Mismo simulador, mismo volcán y fecha. Pregunta 1: si #889 distinguiera el cese, el
  escenario `snpp_vacio` daría un mensaje o código distinto del de `vivo`. Pregunta 2: el escenario `l1b_sin_geo` (VB-1, que
  #889 dice arreglar) tiene que registrar `sin_geolocalizacion`, y registra 8.

  | escenario (#889) | incidencias | mensaje | código NRT | código `--estricto` |
  |---|---|---|---|---|
  | vivo | 1 (`dia_parcial`) | **Cobertura NO COMPLETA: 1 incidencias** | 0 | 3 |
  | snpp_vacio | 3 (`dia_parcial`, 2 `sin_granulos`) | Cobertura NO COMPLETA: 3 incidencias | 0 | 3 |
  | noaa21_version_cambia, noaa20_vacio, modis61_* | 3 | NO COMPLETA: 3 | 0 | 3 |
  | todo_vacio | 9 | NO COMPLETA: 9 | 0 | 3 |
  | l1b_sin_geo | 9 (8 `sin_geolocalizacion`) | NO COMPLETA: 9 | 0 | 3 |

  El `dia_parcial` del escenario `vivo` sale porque la fecha simulada (2026-11-05) es posterior a la hora real de la corrida;
  en producción pasa lo mismo cada corrida, porque `default_date_window` (`run_pipeline.py:386-399`) incluye siempre el día
  de hoy.
- **QUÉ PASA**: #889 hace lo que promete (ya no dice «completa» con una plataforma vacía, y VB-1 queda registrado), pero la
  palanca satura el encabezado: como el NRT procesa siempre el día en curso, **todas** las corridas dirán «NO COMPLETA», y la
  diferencia entre una noche normal y el cese de Suomi NPP queda en las sublíneas (`sin gránulos, sin juicio ... no cuenta en
  modo estricto`) que nadie lee en 11 jobs por corrida y 17 corridas por día. Es el patrón de A114: un aviso que sale siempre
  no avisa. Y el código de salida del NRT no cambia en ningún escenario (ni en `--estricto`, donde `sin_granulos` «no cuenta»
  por decisión explícita, razonable: el código no sabe si debía haber pasada).
- **CÓMO SE VE EN EL DASHBOARD**: invisible (nada de esto llega al tablero).
- **CÓMO REPRODUCIRLO**: `PYTHONIOENCODING=utf-8 python -I simular_dependencias.py D:\vrp-trabajo\temporales\s160_audit\f3\arbol_889`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 3 (no empeora nada; lo que agrega no sirve de vigilante del cese, y podría leerse como que sí).

### 246. La sincronización horaria de la referencia corre 5,2 veces por día de 24 y pierde corridas desplazadas por el grupo `push-main`; hueco máximo 22,7 h, invisible bajo 7 días

- **ARCHIVO:LÍNEA**: `.github/workflows/sync-mirova-csv.yml:42` (`cron: "12 * * * *"`), `:45-56` (concurrency `push-main`,
  `cancel-in-progress: false`; el comentario de `nrt.yml:57-64` explica que un solo run queda pendiente por grupo);
  insumos `runs_sync-mirova-csv.tsv`.
- **SCRIPT:SALIDA**: `medir_cadencia_insumos.py` → `medir_cadencia_insumos_salida.txt`. Sólo lee los insumos. Pregunta 1:
  si el sync perdiera corridas, habría `cancelled` y huecos mayores de 1 h entre `success`. Pregunta 2: un archivo vacío sale
  con 2 y «SIN DATO». Control positivo (del NRT, mismo script): el hueco entre dos corridas `schedule` consecutivas supera
  2 h al menos una vez, y da 7,19 h.
  - 50 corridas del 2026-10-12 07:19 al 10-21 23:17 UTC: 42 `success`, 8 `cancelled` (canceladas tras 7 a 22 min en cola);
    5,2 corridas por día contra 24 pedidas; hueco máximo entre dos `success`: **22,7 h** (2026-10-16 23:33 a 10-17 22:16);
    los cinco mayores: 8,7, 8,7, 10,5, 10,5 y 22,7 h.
- **QUÉ PASA**: la referencia llega a VRP con horas de atraso que nadie mide. El único vigilante de frescura de la referencia
  es a 7 días (`vigilancia_sombra.avisos_referencia`, `scripts/vigilancia_sombra.py:395-406`, sobre `MAX_GT_STALE_DAYS = 7`
  de `auto_audit_weekly.py:109`) y el banner del tablero a 14 (`index.html:3985`). Medido contra la tabla congelada: el hueco
  máximo entre filas consecutivas desde 2026-01-29 es 11,9 h y entre alertas 71,1 h, así que 7 días nunca alarma en falso y
  tampoco ve un atraso de un día.
- **CÓMO SE VE EN EL DASHBOARD**: la línea de MIROVA termina horas antes que la nuestra; una noche reciente aparece «sólo
  nosotros» hasta que llega la copia. Sin banner.
- **CÓMO REPRODUCIRLO**: `python -I medir_cadencia_insumos.py ..\insumos\runs_nrt.tsv ..\insumos\runs_sync-mirova-csv.tsv`.
- **CONFIANZA**: CONFIRMADO sobre la ventana de los insumos (10 días del sync, 3 del NRT).
- **GRAVEDAD**: 3.

### 247. EARTHDATA_TOKEN: el vigilante funciona, pero un secret ausente da «desconocido» sin issue y `nrt.yml` no tiene la guarda de token vacío: con token vacío hace 8 logins con el par vencido y bloquea la cuenta

- **ARCHIVO:LÍNEA**: `.github/workflows/nrt-healthcheck.yml:320-326` (paso «Vencimiento del EARTHDATA_TOKEN», `if:
  always()`), `:328-400` (issue por transición; TEXTO l. 362-364: `if ESTADO == "desconocido": print("Estado del token
  desconocido (secret ausente o no-JWT): sin issue."); sys.exit(0)`); `scripts/token_edad.py:27` (`DIAS_AVISO = 10`),
  `:43-50`; `nrt.yml:172-174` (pasa los tres secretos, sin comprobar que el token venga) contra `experimental-diario.yml:63-64`
  (TEXTO: «if [ -z "$EARTHDATA_TOKEN" ]; then echo "::error::EARTHDATA_TOKEN vacio. Sin token no se procesa nada, y el login
  por usuario y clave vencido bloquea la cuenta (A71)."»); `pipeline/fetch.py:318-345` (sin token: probe, 8 esperas de hasta
  480 s, `earthaccess.login(strategy="environment")` por intento y `netrc` si existe);
  `C:\Users\nmend\OneDrive\Escritorio\claude\REGISTRO_CREDENCIALES.md` §2 fila 1 (TEXTO: «vence **2026-12-07 18:03 UTC** ...
  **Rotar antes del 2026-11-27**») y fila 2 (el par «NO sirve de respaldo (S146)»); insumos `secretos_nombres_y_fecha.txt`
  (`EARTHDATA_TOKEN 2026-10-08T18:07:05Z`; USERNAME y PASSWORD del 2026-04-04).
- **SCRIPT:SALIDA**: `probar_token_edad.py` → `probar_token_edad_salida.txt` (JWT sintéticos, nunca un token real; el
  vencimiento del vigente lo tomo del REGISTRO y del `updated_at` del secret, no del JWT, que no leí). Pregunta 1: por vencer
  tiene que dar `renovar` o `vencido`. Pregunta 2: ausente o ilegible tiene que dar `desconocido`, que es el estado sin
  issue. Controles: 40 días → `ok`; 10,0 y 5 días → `renovar`; -1 día → `vencido`. Cinco formas de ausencia (vacío, espacios,
  JWT sin `exp`, token opaco, `exp` como texto) → `desconocido` → SIN ISSUE. Para el token vigente: `ok`, 46,6 días al
  2026-10-22 03:00 UTC; el issue se abriría desde el **2026-11-27** (healthcheck de las 12:00 UTC que arranca 14:34 a 17:53).
  Y `simular_dependencias.py`, escenario `token_vacio` (main): 8 `login(environment)` + 8 `login(netrc)` (en esta máquina
  hay `_netrc`; en CI no), 1.300 s de esperas, `RuntimeError ... invalid_credentials`, traceback, exit 1.
- **QUÉ PASA**: la fecha dura del proyecto sí tiene vigilante y está medido. Los dos huecos: (a) si alguien borra o pega mal el
  secret, el vigilante calla por diseño (sólo resumen) y el NRT cae al par vencido, que NASA rechaza; el run sale rojo (no es
  silencio) pero después de 8 intentos, que es la secuencia que bloqueó la cuenta en S146 (A71), y `nrt-monitor` recién abre
  issue con 3 fallas consecutivas (cadencia 6 h); (b) `experimental-diario.yml` ya tiene la guarda y `nrt.yml` no.
- **CÓMO SE VE EN EL DASHBOARD**: con token vencido o ausente, contador «sin pasadas hace X» en rojo a las 72 h en los 11
  volcanes (ya pasó del 2026-10-03 al 10-08, REGISTRO fila 1).
- **CÓMO REPRODUCIRLO**: `python -I probar_token_edad.py D:\vrp-trabajo\temporales\s160_audit\main`; simulador, escenario
  `token_vacio`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 3 (degrada con rojo; el costo es el bloqueo de la cuenta y la latencia del issue).

### 248. La cadencia del NRT depende de un disparador de tercero sin vencimiento declarado; sin él, GitHub entrega 4,7 de 12 corridas por día y nadie abre issue

- **ARCHIVO:LÍNEA**: `scripts/medir_cadencia_cron.py:36-44` (`ESPERADO_POR_DIA` 12 para el NRT; `CRITICO`), `:108-116` (la
  alerta «salta solo con cero corridas del NRT en la ventana») y `:144-149` (TEXTO del comentario de la l. 144: «Un exit code
  distinto pondria el job en rojo por algo que no es una falla»; `return 0`); `nrt-healthcheck.yml:297-305` (la medición va
  con `tee` al resumen del job, sin issue); `REGISTRO_CREDENCIALES.md` §2 fila 31 (PAT `vrp-chile-cron-externo`, «sin
  vencimiento (dicho por Nicolás el 2026-10-17)»); `docs/audit_s142/CRON_EXTERNO_PASO_A_PASO.md:19` (TEXTO: «Expiración: 90
  días (anótala)»: la guía y el registro no dicen lo mismo); memoria `reference_cronjob_org_zona_horaria` (zona del trabajo
  en UTC desde el 2026-10-19).
- **SCRIPT:SALIDA**: `medir_cadencia_insumos.py` → `medir_cadencia_insumos_salida.txt`, sobre `runs_nrt.tsv` (50 corridas,
  2026-10-19 03:23 a 10-22 03:10 UTC): 14 `schedule` (4,7 por día) y 36 `workflow_dispatch` (12,0 por día, las del cron
  externo a los :10); atraso de las `schedule` respecto del cron `0 */2`: mín 1, mediana 68, máx 115 min; hueco máximo entre
  `schedule` solas **7,19 h** (10-19 09:36 a 16:47); duración mediana 38 min, máx 80 (el `timeout-minutes: 80` de
  `nrt.yml:69` se tocó al menos una vez en la ventana).
- **QUÉ PASA**: GitHub no cumple el cron de 2 h (ya lo sabía S142, por eso existe el externo). Si el PAT o la cuenta de
  cron-job.org fallan, el NRT vuelve a ~4,7 corridas por día con huecos de hasta 7 h, sin pérdida de datos (cada corrida
  procesa 8 días) pero con el tablero atrasado hasta 7 h en plena erupción, y ningún vigilante lo convierte en issue: la
  medición de cadencia no distingue eventos, sólo alerta con cero corridas, y nunca sale en rojo.
- **CÓMO SE VE EN EL DASHBOARD**: «datos atrasados · última pasada hace X h» (ámbar entre 30 y 72 h, `index.html:1864`);
  bajo 30 h, nada.
- **CÓMO REPRODUCIRLO**: `python -I medir_cadencia_insumos.py ..\insumos\runs_nrt.tsv ..\insumos\runs_sync-mirova-csv.tsv`.
- **CONFIANZA**: CONFIRMADO sobre 3 días de insumos.
- **GRAVEDAD**: 3.

### 249. CMR caído, HTTP 500 o host de descarga en ConnectTimeout: «INCOMPLETA» con `::warning`, código 0, sin issue; `nrt-retry` sólo reintenta con NASA_DOWN

- **ARCHIVO:LÍNEA**: `pipeline/fetch.py:779-789` (breaker S116: Timeout o ConnectionError de CMR → `_registrar_falla` y `[]`
  para el resto de la corrida), `:790-797` (HTTP 500 cae al `except Exception`, se comprueba credencial y se propaga a
  `fetch_for_volcano:1126-1129`, que lo registra como falla), `:962-983` (breaker de descarga S102/S109);
  `scripts/run_pipeline.py:420-441` (`::warning title=Cobertura incompleta` sólo bajo `GITHUB_ACTIONS`; `return 0`);
  `.github/workflows/nrt-retry.yml:46-64` (busca la anotación `NASA_DOWN`, que sólo pone `nrt.yml:231-243` cuando el log trae
  `NASA_AUTH_UNREACHABLE`, o sea sólo sin token).
- **SCRIPT:SALIDA**: simulador, escenarios `cmr_http500`, `cmr_timeout`, `descarga_timeout` (main y #889): 8 fallas, 0
  plataformas, «Cobertura INCOMPLETA: 8 búsquedas o descargas fallidas», código 0 (3 con `--estricto`).
- **QUÉ PASA**: una caída de NASA de horas se ve en el resumen del run y en una anotación; el dato vuelve en la corrida
  siguiente si NASA vuelve (lookback de 8 días). Si dura más de 48 h, el healthcheck abre issue por volcán. Es «aviso», no
  silencio. Lo que no hay: reintento a los 30 min (sólo para auth sin token) ni issue por corrida incompleta.
- **CÓMO SE VE EN EL DASHBOARD**: nada hasta las 30 h; después ámbar, a las 72 h rojo.
- **CÓMO REPRODUCIRLO**: simulador, esos tres escenarios.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 2 (degrada sin silencio).

### 250. Un L1B sin su geolocalización en el catálogo se descarta en silencio (VB-1); #889 lo registra como incidencia que cuenta sólo en modo estricto

- **ARCHIVO:LÍNEA**: `pipeline/fetch.py:1142-1161` (`_match_granules`: sólo `if t in geo_by_time`), `:1164-1166`
  (`matched` se descarga; el resto no deja rastro).
- **SCRIPT:SALIDA**: simulador, escenario `l1b_sin_geo` (2 L1B y 1 GEO por plataforma): main → 2 archivos por plataforma,
  0 fallas, «completa»; #889 → 8 incidencias `sin_geolocalizacion`, código 0 (3 en estricto).
- **QUÉ PASA**: ya estaba en `docs/AUDIT_S158_R2.md` (VB-1) y S159 lo midió en CMR (72 MOD021KM NRT contra 68 MOD03 el
  20-oct). Acá sólo confirmo que en `main` sigue mudo y que #889 lo deja visible sin cambiar el código de salida del NRT.
- **CÓMO SE VE EN EL DASHBOARD**: una pasada menos esa noche, sin marca.
- **CÓMO REPRODUCIRLO**: simulador, `l1b_sin_geo`, en los dos árboles.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 2.

### 252. Bibliotecas sin fijar: el pipeline codifica supuestos de `earthaccess` 0.17 sin pin ni test de versión; un cambio de envoltorio del 401 devolvería el zombie de S123

- **ARCHIVO:LÍNEA**: `requirements.txt:1` (`earthaccess>=0.9.0`), `:16` (`pyhdf>=0.11.4`); `nrt.yml:143` (`pip install
  earthaccess numpy h5py scipy pyyaml`, sin versión; `:141-142` apt `libhdf4-dev` y `pip install pyhdf`); `pipeline/fetch.py:54`,
  `:268`, `:312`, `:418-452` (`_is_credential_dead` lee `exc.__cause__.response.status_code`, que es cómo 0.17 envuelve el
  rechazo: TEXTO l. 418-420 «earthaccess ≥0.17 envuelve el rechazo HTTP en `RuntimeError(response.text)`, perdiendo el tipo
  pero conservando el status en `__cause__.response`»), `:480` (formato `temporal` de 0.17); `grep` de `__version__` o
  `earthaccess==` en `pipeline/ scripts/ tests/`: 0 resultados. Runner: `nrt.yml:68`, `tests.yml:28`,
  `vigilancia-sombra.yml:36`, `experimental-diario.yml:30` fijados en `ubuntu-24.04` (TEXTO del comentario: «ubuntu-latest
  migra a 26.04 entre 2026-10-19 y 2026-11-19»); healthcheck, monitor, retry, sync, pages y audit-weekly en `ubuntu-latest`
  (sin pyhdf: bajo riesgo).
- **QUÉ PASA**: cada corrida instala la última `earthaccess` publicada. Si rompe la API, el run sale rojo (ERROR, no
  silencio). Si cambia sólo cómo envuelve un 401, `_is_credential_dead` devuelve False, el rechazo vuelve al `except
  Exception` de `fetch_for_volcano:1126` como «WARN: Failed to fetch», y el NRT queda verde sin datos hasta el healthcheck de
  48 h: exactamente el zombie que S123 cerró. No lo simulé (sería inventar la versión futura).
- **CÓMO SE VE EN EL DASHBOARD**: en el caso silencioso, rojo a las 72 h en los 11 volcanes, atribuido a adquisición.
- **CÓMO REPRODUCIRLO**: `grep -n earthaccess requirements.txt .github/workflows/nrt.yml; grep -n __cause__ pipeline/fetch.py`.
- **CONFIANZA**: SOSPECHA (el mecanismo está leído; la versión que lo rompa no existe hoy). Versión instalada en el último
  run: SIN DATO. Local: 0.17.0.
- **GRAVEDAD**: 3 (el silencio es hipotético; la falta de pin es real).

### 251. NOAA-20 se consulta en versiones que no existen; NOAA-21 en una sola

- **ARCHIVO:LÍNEA**: `pipeline/fetch.py:200-203` y `:210-213` (`"versions": ["2.1", "2", "1"]`, NRT `["2.1", "2"]`);
  `:218-225` (NOAA-21 `["2.1"]`); `cmr_estado_colecciones_salida.txt`: VJ102IMG, VJ102MOD y sus NRT tienen **una** colección
  (2.1); v2 y v1 dan 0 gránulos.
- **QUÉ PASA**: en un día sin pasada de NOAA-20, el pipeline hace hasta 5 consultas (2.1, 2, 1 Standard; 2.1, 2 NRT) donde 3
  preguntan por colecciones que CMR no tiene. No cambia resultados; cuesta tiempo cuando CMR está lento (S157 midió 4 a 7 s
  por consulta). La otra cara es NOAA-21: una sola cadena, sin descubrimiento (241).
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `python -I cmr_estado_colecciones.py`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 1.

### 254. La reconstrucción de `data/mirova/<Vol>.json` falla por volcán con «WARN (continuing)»

- **ARCHIVO:LÍNEA**: `.github/workflows/sync-mirova-csv.yml:164-172` (`python scripts/rebuild_mirova_from_consolidado.py ...
  || echo "  WARN: rebuild $stem failed (continuing)"`); `frontend/index.html:3960-3990` (el banner usa el máximo de
  `datetime_utc` de todos los volcanes).
- **QUÉ PASA**: si la reconstrucción de un volcán falla (cambio de nombre en el CSV, fila corrupta), ese JSON queda viejo, el
  commit sale igual, la corrida sale verde, y el banner no lo ve porque otro volcán sigue fresco. No lo simulé: el script
  escribe en `data/`.
- **CÓMO SE VE EN EL DASHBOARD**: ese volcán sin triángulos nuevos de MIROVA; se lee como «MIROVA no publica».
- **CÓMO REPRODUCIRLO**: leer las líneas; para simular haría falta un `--dest` fuera de `data/`, que el script no tiene.
- **CONFIANZA**: SOSPECHA.
- **GRAVEDAD**: 2.

### 256. El consolidado bajado no se valida: una respuesta 200 con HTML o vacía se commitearía

- **ARCHIVO:LÍNEA**: `.github/workflows/sync-mirova-csv.yml:65-84` (sólo `curl -fsSL`, que falla con HTTP ≥ 400 pero acepta
  cualquier 200; `cmp` y `mv`) contra `:106-112` (OCR: líneas ≥ 2, cabecera con `Fecha_Satelite_UTC`, no encogerse);
  `frontend/diario.html:207-211` (lee `latest_consolidado.csv` directo, con fallback al snapshot fechado sólo si el `fetch`
  falla, no si el contenido no es CSV).
- **QUÉ PASA**: un cambio de ruta en Mirova-v1 que devuelva una página, o un commit a medias del scraper, entraría al repo.
  La reconstrucción daría WARN (254) y `diario.html` parsearía basura. Con 400 versiones vistas no encontré ninguna así
  (el conteo de líneas nunca cayó bajo 33.285), de modo que es un hueco de defensa, no un incidente.
- **CÓMO SE VE EN EL DASHBOARD**: `diario.html` sin referencia; `index.html` con los JSON viejos.
- **CÓMO REPRODUCIRLO**: leer las líneas.
- **CONFIANZA**: SOSPECHA.
- **GRAVEDAD**: 2.

### 255. El healthcheck de las 12:00 UTC arranca entre 14:34 y 17:53 UTC

- **ARCHIVO:LÍNEA**: `nrt-healthcheck.yml:6` (`cron: "0 12 * * *"`); `gh_healthcheck_runs.json` (8 corridas `schedule`,
  2026-10-14 a 10-21, todas `success`, creadas a las 16:06, 15:54, 15:42, 14:34, 15:02, 17:53, 15:58 y 16:14 UTC).
- **QUÉ PASA**: toda alerta diaria (staleness, token, y la vigilancia por plataforma de la rama) llega 2,5 a 6 h más tarde
  de lo diseñado. GitHub retrasa los `schedule` (248 lo mide en el NRT: mediana 68 min).
- **CÓMO SE VE EN EL DASHBOARD**: invisible.
- **CÓMO REPRODUCIRLO**: `gh run list --repo MendozaVolcanic/VRP-chile --workflow nrt-healthcheck.yml --limit 8 --json createdAt,conclusion,event`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 1.

## 4. La tabla de dependencias

`dependencias.csv` en CARPETA: 22 filas (plataformas, colecciones, servicios, credenciales, referencia, bibliotecas, OSF,
CI), con fecha de vencimiento y su fuente o SIN FECHA, consumidor `archivo:línea`, qué se apaga, cómo falla medido
(error, aviso o silencio), vigilante y umbral medido. Resumen de la columna «cómo falla»:

| cómo falla | dependencias |
|---|---|
| SILENCIO | Suomi NPP, NOAA-20, NOAA-21 (versión), Terra y Aqua enteras, MODIS 6.1 (caída al NRT), tabla de MIROVA que se encoge, cron-job.org (cadencia), argsort por CPU |
| AVISO sin issue | CMR, LANCE y host de descarga, cadencia de GitHub (resumen), sync desplazado |
| ERROR (rojo) | token vencido (401), token ausente (tras 8 logins y bloqueo), OCR vacío o encogido, bibliotecas que rompen la API, acciones de CI |
| sin efecto en el NRT | código de MIROVA en OSF (nadie lo consume por código), par usuario y clave mientras haya token |

Fechas conocidas y su vigilante: Suomi NPP 2026-11-02 13:00 UTC (vigilante sólo en una rama local, 242); MODIS 6.1
2026-09-30 anunciado y no ejecutado (sin vigilante, 243); EARTHDATA_TOKEN 2026-12-07 18:03 UTC (vigilante medido, issue
desde 2026-11-27, 247); ubuntu-latest a 26.04 entre 2026-10-19 y 2026-11-19 (NRT fijado en 24.04; los demás sin pyhdf);
PAT de cron-job.org: SIN FECHA declarada, la guía pedía 90 días (248). Todo lo demás: SIN FECHA.

## 5. SEGUIMIENTOS (fuera de mi eje; sólo dejo cada uno reproducible)

- **S-1. CLAUDE.md del proyecto (sección Arquitectura) afirma un hueco de datos que ya no existe.** TEXTO: «hay un hueco de
  2025-11-16 a 2026-01-28 en 9 de los 11 Tier A» (marca S146, AUDIT_S146 V-15). En `d516b9d8c`, Láscar tiene 277, 285 y 291
  records en nov-2025, dic-2025 y ene-2026; PCC 348, 366, 360; Villarrica 336, 344, 353 (medido sobre
  `D:\vrp-trabajo\temporales\s160_audit\main\data\mirova_equivalent\`; la salida está en `medir_vigilantes_contra_datos_salida.txt`
  D1 y en mi sesión). S158 reemplazó el histórico con K (#883, #884) y la marca no se propagó (A113). Confianza: CONFIRMADO.
  Me costó un control positivo: lo diseñé sobre esa afirmación y falló; lo reemplacé por un hueco sintético (D2, OK).
- **S-2. `docs/EARTHDATA_TOKEN_SETUP.md:22`** TEXTO: «NO eliminar `EARTHDATA_USERNAME` y `EARTHDATA_PASSWORD`» y, tras un guion del original, «quedan como
  fallback si el token expira», contradice REGISTRO_CREDENCIALES §2 fila 2 y `experimental-diario.yml:64` (el par está
  vencido y bloquea la cuenta). Confianza: CONFIRMADO (texto leído en los dos lados).
- **S-3. El PAT del cron externo**: `docs/audit_s142/CRON_EXTERNO_PASO_A_PASO.md:19` pide 90 días; REGISTRO §2 fila 31 lo
  registra «sin vencimiento». Uno de los dos está desactualizado; cuál, SIN DATO (sólo Nicolás lo ve en GitHub).
- **S-4. Mirova-v1**: los 7 encogimientos de 245 son del CSV del scraper (S159 verificador lo atribuye a la carrera entre
  workflows con `git pull --rebase -X ours`); va a la sesión `audit-mirova-v1`. Y la tabla no cubre nada antes del 2026-01-10
  (A119), pero ese es asunto de F1.
- **S-5. `experiments/_s159/biblio_2026/INFORME.md` §0 punto 1** cita `pipeline/fetch.py:797` y `:803` para `all_platforms`;
  hoy son `:1063` y `:1069` (S159 cese_snpp ya lo anotó; lo repito porque el plan §3 F3 apunta a ese informe).
- **S-6. `nrt-monitor.yml:126`** afirma que «el issue de nrt-healthcheck avisa con 10 días»: VERIFICADO (token_edad
  `DIAS_AVISO = 10`, medido). No es seguimiento, lo dejo porque es una cita entre workflows que podría envejecer.
- **S-7. `nrt-monitor.yml` no cuenta `cancelled`** (`conclusion === 'failure' || 'timed_out'`): una corrida `schedule` del
  NRT quedó `cancelled` el 2026-10-20 03:31 (insumos). Si el grupo `push-main` desplazara 3 seguidas, no habría issue.
  Confianza: CONFIRMADO en el texto, SOSPECHA en que llegue a 3.

## 6. VERIFICADO LIMPIO

| qué | comando o script | contra qué vara | resultado |
|---|---|---|---|
| Credencial rechazada (401) en la descarga aborta ruidoso | simulador, `cred_401`, main y #889 | A123 cierre de S123 (`fetch.py:418-470`, `:984-991`) | `EarthdataCredentialError`, traceback, exit 1 en los dos árboles |
| Token vacío no es silencio | simulador, `token_vacio` | `fetch.py:318-363` | RuntimeError tras 8 + 8 logins; exit 1 (el costo es 247) |
| CMR y descarga caídos quedan en la cobertura | simulador, `cmr_http500`, `cmr_timeout`, `descarga_timeout` | S157 (`fetch.py:720-731`, `run_pipeline.py:402-441`) | 8 fallas, INCOMPLETA, `--estricto` 3 |
| Vigilante del token: estados y umbral | `probar_token_edad.py` | `token_edad.py:27,43-50`; nrt-healthcheck.yml:328-400 | ok/renovar/vencido correctos en el borde de 10,0 días; issue sólo en renovar y vencido |
| Healthcheck 48 h por volcán no alarma en falso | `medir_vigilantes_contra_datos.py` A | 266 días a las 12:00 UTC desde 2026-01-29, 11 Tier A | hueco máximo por volcán 21,5 a 22,8 h; 0 alarmas con 48 h y con 72 h; control sintético (hueco de 6 días en Láscar) da 5 y 4 alarmas, OK |
| Sombra 3 días por volcán y bucket no alarma en falso | idem B | `vigilancia_sombra.py:61,362-392` | hueco máximo MODIS 42,1 h (Láscar), VIIRS 46,6 h; 0 alarmas de 266 en los 33 pares |
| Referencia 7 días no alarma en falso | idem C | `auto_audit_weekly.py:109`; `vigilancia_sombra.py:395-406` | tabla: hueco máximo entre filas 11,9 h, entre alertas 71,1 h; OCR solo 263,5 h (no alarma porque la unificada incluye la tabla) |
| Edad de los datos al cierre | idem A y C | 03:11:55 UTC | último record 2026-10-21 08:05 a 08:10 UTC en los 11 (19 h); tabla 7,1 h; OCR 33,7 h |
| `records[-1]` del healthcheck es el más reciente | idem A (nota «!= max») | `nrt-healthcheck.yml:73`, `nrt.yml:292` | en los 11 archivos `records[-1]` coincide con `max(datetime_utc)` |
| Colecciones pedidas existen y producen | `cmr_estado_colecciones.py` | CMR público, 44 consultas | 16 de 16 ACTIVE, 8 a 19 gránulos en 48 h; control S133 (`MYD021KM_NRT`) da 0 colecciones |
| Cadencia real del NRT y del sync | `medir_cadencia_insumos.py` | insumos (3 y 10 días) | NRT 16,7 corridas/día (12 externas + 4,7 GitHub); sync 5,2/día |
| Issues abiertos hoy | `gh issue list` (1 llamada) | etiquetas `nrt-stale`, `earthdata-token` | ninguno de esas clases; abiertos #864 (auto-audit fuera de banda) y #813 (decisión D-10) |
| Healthcheck corre a diario | `gh run list` (1 llamada) | cron 0 12 | 8 de 8 días `success` (con el atraso de 255) |

## 7. SIN DATO

- La versión de `earthaccess` (y de `numpy`, `pyhdf`) instalada en el último run de `nrt.yml`: habría que leer el log por
  API (una llamada grande); no la gasté. Local: 0.17.0.
- Si LANCE corta el NRT de Suomi NPP a la misma hora que el Standard (S159 §2 lo deja SOSPECHA; se sabe el 3-nov).
- Si NASA ejecutará el decomiso de MODIS 6.1 y cuándo (anunciado 2026-09-30; hoy ACTIVE con producción normal).
- Si cron-job.org avisa por correo cuando el disparo falla (configuración de la cuenta de Nicolás).
- El `exp` real del JWT: no leí el token; uso el REGISTRO (verificado por S150 en un log del healthcheck) y el `updated_at`.
- El estado de GitHub Pages (último deploy, errores): sin llamadas.
- Si el PAT del cron externo tiene vencimiento (S-3).

## 8. FUERA DE ALCANCE

- El código del scraper Mirova-v1 (sesión `audit-mirova-v1`); el arreglo del cese de Suomi NPP (rama de otra sesión; sólo
  auditado); cualquier cambio en `pipeline/`, `scripts/`, `.github/` (A45); los workflows `probe-*` y `reproc-*`; las métricas
  de paridad (F1).

## 9. Instrumentos y salidas (todo en CARPETA)

| script | salida | qué mide |
|---|---|---|
| `simular_dependencias.py` | `simular_dependencias_salida.txt` (+ `_stderr_main.txt`, `_stderr_889.txt`) | 14 escenarios de falla sobre `fetch_for_volcano` real, main y #889 |
| `probar_token_edad.py` | `probar_token_edad_salida.txt` | estados del vigilante del token con JWT sintéticos |
| `medir_vigilantes_contra_datos.py` | `medir_vigilantes_contra_datos_salida.txt` | umbrales 48 h, 72 h, 3 d, 7 d contra la instantánea |
| `medir_encogimientos_consolidado.py` | `medir_encogimientos_consolidado_salida.txt` | copias encogidas aceptadas por el sync (400 commits) |
| `medir_cadencia_insumos.py` | `medir_cadencia_insumos_salida.txt` | cadencia y atrasos del NRT y del sync desde los insumos |
| `cmr_estado_colecciones.py` | `cmr_estado_colecciones_salida.txt` | versiones, progreso y gránulos recientes de cada colección pedida |
| (gh, 2 llamadas) | `gh_healthcheck_runs.json`, `gh_issues_abiertos.tsv` | corridas del healthcheck e issues abiertos |
| `dependencias.csv`, `hallazgos.csv` | | las dos tablas pedidas |

Pesado: `D:\vrp-trabajo\temporales\s160_audit\f3\` (`arbol_889\`, `consolidado_commits.txt`, `tmp_sim\`).
