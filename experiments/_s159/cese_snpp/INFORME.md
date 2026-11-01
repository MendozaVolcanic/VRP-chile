# S159, frente «cese de Suomi NPP y colecciones de NASA»: qué pasa el 2 de noviembre

Fecha: 2026-10-21 (hora del servidor CMR al medir: 2026-10-22 02:44 UTC). Código leído de `origin/main` en
`d516b9d8c` (2026-10-22 01:49 UTC). Nada de esto toca el repositorio: sólo scripts y salidas en
`C:\vrp-trabajo\s159-pruebas\experiments\_s159\cese_snpp\`. El árbol de `origin/main` usado para simular se extrajo
con `git archive` (con rutas) a
`C:\Users\nmend\AppData\Local\Temp\claude\C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile\b66eab35-0745-4a69-a582-8578a1f20f47\scratchpad\arbol\`.

## 0. En una línea

El 2 de noviembre el pipeline **no se rompe ni se cuelga**: deja de recibir Suomi NPP, lo trata como «no hay
pasada» y sigue verde, con la cobertura declarada «completa». Lo que se pierde es un tercio de las pasadas
nocturnas VIIRS, y **ninguna vigilancia del proyecto mira por plataforma**, así que nada avisa. El costo medido en
la última ventana del detector K es chico pero no nulo: una noche con alerta de MIROVA por sensor VIIRS en 33 días
habría quedado sin publicar, y una de ellas es una alerta protegida (PCC, VIIRS 750, 2026-10-10, 1,19 MW).

## 1. El fenómeno, antes del código

Suomi NPP es el más viejo de los tres satélites que llevan VIIRS. NOAA deja de distribuir sus datos y apaga su
transmisión directa el 2 de noviembre a las 13:00 UTC, y en diciembre empieza a bajarle la órbita para que reingrese.
Sobre Chile, las tres plataformas pasan de noche en un racimo de una a dos horas (en los records: NOAA-21 hacia las
04:30 a 05:12, Suomi NPP 04:54 a 07:06, NOAA-20 05:12 a 06:54 UTC). O sea que ninguna noche queda sin VIIRS: se
pierde una de tres miradas al volcán dentro de la misma noche. Para un foco débil que a veces se ve y a veces no
(nube fina, cenit alto, píxel que parte el foco), una mirada menos es una probabilidad menos de publicarlo. La última
pasada nocturna de Suomi NPP que se va a entregar es la de la madrugada del 2 de noviembre (antes de las 13:00 UTC).

## 2. Las fuentes (tarea 1)

| Afirmación | Fuente leída hoy | Estado |
|---|---|---|
| La entrega de Suomi NPP cesa el 2026-11-02 13:00 UTC, sujeto a cambio | NASA Earthdata, aviso emitido 2026-10-21; LAADS 199516; LDOPE 1479 (abierto 2026-08-03, actualizado 2026-10-07); NESDIS «Update #2», emitido 2026-10-19 | CONFIRMADO en las cuatro |
| El archivo histórico de SNPP sigue disponible | LAADS 199516 («historical SNPP VIIRS product collections will remain available») | CONFIRMADO |
| Tabla de reemplazo VNP02/03 IMG y MOD → VJ102/103 y VJ202/203 | LAADS 199516 (tabla completa, también DNB, VNP09, VNP46) | CONFIRMADO |
| NESDIS: «All users should transition to using NOAA-21 (Primary) and NOAA-20 (Secondary)»; Direct Broadcast deshabilitado a la misma hora; S-NPP se baja desde el 1-dic hasta ~12-dic para reingreso | NESDIS Update #2 | CONFIRMADO |
| MODIS C6.1 L1 se decomisa el 2026-09-30 | LAADS 199534 (17-mar-2026: «remain available for the next six months before being decommissioned on September 30, 2026») | CONFIRMADO el texto; NO ejecutado (ver §3) |
| ¿Incluye el NRT (LANCE)? | Ninguna de las cinco fuentes lo dice. La página de LANCE redirige a Earthdata, cuyo banner dice «Delivery of new Suomi NPP data ceases on Nov. 2, 2026» sin nombrar productos | SIN DATO en las fuentes. SOSPECHA fuerte de que sí: NESDIS dice «all S-NPP data products» con «Length of Outage: Permanent» y apaga la transmisión directa, y LANCE se alimenta del mismo flujo de nivel 0. Se confirma el 3-nov con la consulta de §7 |
| Fecha discordante | Un aviso viejo de Earthdata (emitido 2026-08-07) dice «cease November 1, 2026»; LDOPE 1479 da «2026/305» y LAADS «2026/306». El 2 de noviembre de 2026 es el día 306 (calculado) | SOSPECHA de errata en LDOPE (lo leí a través del resumen de la herramienta de lectura, no el HTML crudo) |

Script: `C:\vrp-trabajo\s159-pruebas\experiments\_s159\cese_snpp\cmr_colecciones_y_granulos.py`, salida
`...\cese_snpp\cmr_colecciones_y_granulos_salida.txt`.
Pregunta 1: si una colección hubiera dejado de producir, su último gránulo sobre Chile sería viejo y el conteo de 3 días
daría 0. Pregunta 2: un error de red imprime ERROR, no 0. Control positivo: VJ102IMG_NRT y VJ202IMG_NRT dan 25 y 30.
Control del instrumento: `MYD021KM_NRT` (el nombre equivocado de antes de S133) da «0 colecciones», que es exactamente
lo que el pipeline vería como «no hay dato». Ventana: gránulos con inicio 2026-10-19 00:00 a 2026-10-22 02:44 UTC,
bbox -76,-46,-66,-17.

| Colección | Proveedor | CollectionProgress | Gránulos Chile 3 d | Último |
|---|---|---|---|---|
| VNP02IMG v2 | LAADS | ACTIVE | 14 | 2026-10-21 18:54 |
| VNP02IMG_NRT, VNP03IMG_NRT, VNP02MOD_NRT, VNP03MOD_NRT v2 | LANCEMODIS | ACTIVE, sin fecha de fin | 23 cada una | 2026-10-21 20:24 |
| MOD021KM v6.1 / v7 / v6.1NRT | LAADS / LAADS / LANCEMODIS | ACTIVE las tres | 8 / 11 / 25 | 10-21 03:15 / 10-21 12:45 / 10-22 00:45 |
| MYD021KM v6.1 / v7 / v6.1NRT | idem | ACTIVE | 11 / 11 / 24 | 10-21 08:10 / 10-21 08:10 / 10-21 21:45 |
| MOD03, MYD03 v6.1 / v7 / v6.1NRT | idem | ACTIVE | 11 / 11 / 25 y 24 | al día |

Lo que esto dice: (a) a doce días del cese, ninguna colección de SNPP en CMR tiene fecha de fin ni está marcada como
terminada; (b) **no existe un NRT de la Colección 7 de MODIS** (las únicas versiones de MOD021KM y MYD021KM son 7, 6.1 y
6.1NRT); (c) la 6.1 Standard sigue produciendo tres semanas después de su fecha de decomiso.

### Contraste de los hallazgos H1 a H3 del frente de bibliografía

- **H1**: CONFIRMADO en el fondo. Las líneas citadas derivaron: `all_platforms` con `VIIRS_SNPP` y `VIIRS_SNPP_750`
  está hoy en `pipeline/fetch.py:1063` y `:1069` (no `:797` y `:803`); la tabla `PRODUCTS` sí sigue en `:196-209`.
- **H2**: CONFIRMADO el texto del aviso y que el pipeline pide sólo 6.1 (`pipeline/fetch.py:187-194`). Agrego: no hay
  C7 NRT en CMR, así que «caer al NRT» sólo funciona mientras LANCE siga en 6.1.
- **H3**: CONFIRMADO por día y con un matiz. Script `...\cese_snpp\cmr_hueco_17_20_oct.py`, salida
  `..._salida.txt`. Control positivo: el 14-oct Standard da 9, 9 y 8. El 18 y el 19 Standard da 0 en VNP02IMG,
  VJ102IMG y MOD021KM 6.1, y NRT da 8 a 10. **El matiz**: nuestros records de esos días SÍ son Standard, por ejemplo
  Villarrica `VNP02IMG.A2026291.0542.002.2026291121847.nc` y `MOD021KM.A2026291.0120.061.2026291131348.hdf` (ver
  hallazgo 5). Los gránulos existían cuando el NRT corrió y hoy CMR no los lista.

## 3. Hallazgos, de lo peor a lo menos grave

### H1. El cese de Suomi NPP es invisible para el pipeline: cero gránulos se lee como «no hubo pasada», cobertura «completa», salida 0

- **ARCHIVO:LÍNEA**: `pipeline/fetch.py:770-800` (`search_granules`: prueba Standard y luego NRT, y si los dos vienen
  vacíos devuelve `[]` sin registrar nada); `pipeline/fetch.py:1085-1088` (`if not l1b_granules: continue`, sin
  `_registrar_falla`); `pipeline/fetch.py:179-181` (el propio código documenta que «una colección inexistente no da
  error, da CERO granules»); `scripts/run_pipeline.py:402-417` (`informar_cobertura` sólo cuenta fallas, con lista
  vacía imprime «Cobertura: completa»).
- **SCRIPT:SALIDA**: `...\cese_snpp\simular_snpp_vacio.py` → `simular_snpp_vacio_salida.txt`. Sin red: reemplaza
  `earthaccess.search_data`, `auth` y `download_granules`, y llama al `fetch_for_volcano` real de `origin/main`
  (Villarrica, 2026-11-05). Pregunta 1: si el pipeline avisara de una plataforma vacía, el escenario «vacío» dejaría
  fallas o excepción. Pregunta 2: control positivo, el mismo escenario con SNPP lanzando `ConnectTimeout` debe dejar
  falla, y la deja.

  | Escenario | Plataformas con resultado | Consultas a CMR | Fallas de cobertura | Mensaje |
  |---|---|---|---|---|
  | SNPP vivo | 8 | 16 | 0 | Cobertura: completa |
  | SNPP vacío (el 3-nov) | 6, sin `VIIRS_SNPP` ni `VIIRS_SNPP_750` | 16 | **0** | **Cobertura: completa**, código 0 |
  | SNPP con ConnectTimeout (control) | 2, sólo MODIS | 5 | 6 | Cobertura INCOMPLETA |

- **QUÉ PASA**: el satélite deja de entregar y el pipeline hace lo mismo que en una noche en que el satélite no pasó
  sobre el volcán. No cuesta tiempo (las mismas 16 consultas, rápidas, sin descarga; no hay riesgo tipo A64 porque sin
  gránulos no se toca ningún host de descarga) ni produce error. El control de timeout muestra de paso que una falla de
  red en SNPP enciende el cortacircuito de CMR para toda la corrida y apaga también NOAA-20 y NOAA-21 (es el diseño de
  S116, no algo nuevo del cese).
- **CÓMO SE VE EN EL DASHBOARD**: las series «VIIRS SNPP 375m» y «VIIRS SNPP 750m» desaparecen de la leyenda sin
  mensaje (`frontend/index.html:3196-3212`, cada serie se agrega sólo `if (snpp375.length)`). Hay un tercio menos de
  puntos VIIRS por noche. Medido sobre los 11 Tier A, pasadas nocturnas del 2026-09-18 al 2026-10-20 (detector K):
  SNPP es 501 de 1.514 records VIIRS 375 y 497 de 1.501 VIIRS 750 (script `medir_peso_snpp.py`, abajo).
- **CÓMO REPRODUCIRLO**: `cd <arbol> && PYTHONIOENCODING=utf-8 python C:\vrp-trabajo\s159-pruebas\experiments\_s159\cese_snpp\simular_snpp_vacio.py <arbol>`.
  En producción: el log de `nrt.yml` del 3-nov mostrará `SEARCH_DONE VIIRS_SNPP n_l1b=0` y ningún aviso.
- **CONFIANZA**: CONFIRMADO (leído y simulado con el código de `origin/main`). Que LANCE también corte el NRT es SOSPECHA
  (§2), pero el comportamiento del pipeline es el mismo en los dos casos.
- **GRAVEDAD**: 4. No por el silencio en sí, sino porque tuerce publicaciones (ver H3).

### H2. Ninguna vigilancia del proyecto mira por plataforma; todas miran por volcán o por sensor agregado

- **ARCHIVO:LÍNEA**: `.github/workflows/nrt-healthcheck.yml:53` y `:73-87` (edad del último record del volcán, 48 h,
  cualquier sensor); `.github/workflows/nrt.yml:271-315` (A57, edad del último record del volcán, 72 h, sólo avisa);
  `scripts/vigilancia_sombra.py:362-392` (frescura por volcán y bucket MODIS / VIIRS375 / VIIRS750, más de 3 días,
  `MAX_DIAS_SOMBRA_SIN_DATOS = 3` en `:61`); `scripts/auto_audit_weekly.py:309-316` (`our_bucket` funde las tres
  plataformas) y `:362-380` (`noches_sin_datos` por bucket); `.github/workflows/nrt-monitor.yml` (sólo corridas
  fallidas, y el cese no hace fallar ninguna).
- **SCRIPT:SALIDA**: `...\cese_snpp\simular_vigilancia_sin_snpp.py` → `..._salida.txt`, llama a
  `vigilancia_sombra.avisos_produccion` real con records sintéticos de 20 días. Pregunta 1: si avisara por plataforma,
  «sin SNPP» daría avisos. Pregunta 2 y control positivo: «sin MODIS» debe avisar.

  | Escenario | Avisos |
  |---|---|
  | todo vivo | 0 |
  | sin SNPP desde el 2-nov | **0** |
  | sin MODIS desde el 2-nov (control) | 11, «producción (K) de Lascar en MODIS no produce hace 10 días» |

- **QUÉ PASA**: mientras NOAA-20 o NOAA-21 entreguen una pasada, el bucket VIIRS sigue «vivo» y todo da verde.
- **CÓMO SE VE EN EL DASHBOARD**: invisible. Tampoco se abre ningún issue.
- **CÓMO REPRODUCIRLO**: `python C:\vrp-trabajo\s159-pruebas\experiments\_s159\cese_snpp\simular_vigilancia_sin_snpp.py <arbol>`.
- **CONFIANZA**: CONFIRMADO.
- **GRAVEDAD**: 3. Hoy el único caso esperado es SNPP, pero el mismo hueco dejaría pasar la muerte silenciosa de
  NOAA-20 o NOAA-21 (o un cambio de versión de NOAA-21, que sólo se busca en `"2.1"`, `pipeline/fetch.py:218-225`).

### H3. Lo que se pierde en alertas: noches que hoy sólo publica la pasada de Suomi NPP

- **SCRIPT:SALIDA**: `...\cese_snpp\medir_peso_snpp.py` → `medir_peso_snpp_salida.txt`. Usa el predicado del tablero
  ejecutado con node (`banco_paridad.cargar_nuestros`, A97) y las etiquetas del banco (`banco_paridad.etiquetar`) sobre
  la referencia snapshot de `origin/main` (última fila 2026-10-20 17:30). Ventana: 2026-09-18 a 2026-10-20, pasadas
  nocturnas, 11 Tier A, 3.769 records. Noche = (volcán, sensor, fecha UTC). Regla de mínimas: la **original** del banco
  (no SN de D-9), por eso los denominadores no coinciden con el auto-audit (107 contra 93 en VIIRS 375). Pregunta 1: si
  SNPP no pesara, los conteos «sólo por SNPP» darían 0. Pregunta 2: control positivo, NOAA-20 y NOAA-21 salen con
  conteos de su tamaño (517 y 496 records), y la suma por plataforma cuadra con el total.

  | | VIIRS 375 | VIIRS 750 |
  |---|---|---|
  | Records SNPP / total | 501 / 1.514 | 497 / 1.501 |
  | Noches con algún record / sólo con SNPP | 362 / **0** | 362 / **0** |
  | Noches publicadas / publicadas sólo por SNPP | 138 / 11 | 40 / 11 |
  | Noches con alerta de MIROVA / publicadas / publicadas sólo por SNPP | 107 / 99 / **3** | 30 / 22 / **2** |
  | De esas, con la alerta de MIROVA pareada sólo a la pasada SNPP (MIROVA también la pierde) | 2 | 1 |
  | Pérdida neta (MIROVA alerta en una pasada NOAA, nosotros sólo publicamos la SNPP) | **1**: Lastarria 2026-09-26 | **1**: PuyehueCordonCaulle 2026-10-10 |

- **QUÉ PASA**: ninguna noche se queda sin VIIRS, pero en 22 noches publicadas (11 + 11) la única pasada publicada era
  la de Suomi NPP. Donde MIROVA alertó en esa misma pasada, la pérdida es simétrica (MIROVA tampoco la tendrá). Donde
  MIROVA alertó en una pasada de NOAA y nosotros no la publicamos pero sí la de SNPP, el tablero hoy «salva la noche» por
  otra pasada y después del 2-nov no. El caso de PCC es exactamente el que el auto-audit de hoy lista como «alerta
  protegida sin publicar: PuyehueCordonCaulle VIIRS750 2026-10-10 05:54 UTC, MIROVA 1.19 MW (detector K; la noche sí se
  publicó en otra pasada)» (`data/audit_continuous/latest.json` de `origin/main`); la otra pasada es la SNPP de las 04:54,
  06:30 o 06:36. Con un satélite menos esa misma situación pasa a ser una noche protegida sin publicar.
- **CÓMO SE VE EN EL DASHBOARD**: del orden de una noche con alerta menos por mes por sensor VIIRS (1 en 33 días en cada
  uno, n chico). El recall por noche de VIIRS 750 del auto-audit ya está bajo su banda (73,3 % contra 79,5 %, n = 30,
  `latest.json`), así que esto lo empuja más abajo; en VIIRS 375 (96,8 %, banda 93,4 %) la pérdida de 1 a 3 de unas
  100 noches lo deja todavía dentro. Además la ventana rodante de 60 días del auto-audit mezclará noches con tres y con
  dos plataformas durante dos meses: una caída de recall o de falsas publicaciones por noche en noviembre puede leerse
  como efecto del detector K cuando es efecto del muestreo (A104 por otra puerta).
- **CÓMO REPRODUCIRLO**: `cd <arbol> && PYTHONIOENCODING=utf-8 python C:\vrp-trabajo\s159-pruebas\experiments\_s159\cese_snpp\medir_peso_snpp.py <arbol> 2026-09-18 2026-10-20`.
- **CONFIANZA**: CONFIRMADO lo medido; que MIROVA siga igual con NOAA-20 y NOAA-21 es SOSPECHA.
- **GRAVEDAD**: 3 (una protegida en 33 días, en un sensor que ya está fuera de banda).

### H4. MODIS 6.1: si se retira la Standard caemos al NRT 6.1, que no tiene reemplazo C7, y los reprocesos quedan vacíos en silencio

- **ARCHIVO:LÍNEA**: `pipeline/fetch.py:187-194` (sólo `"version": "6.1"` y NRT `"6.1NRT"`, sin `"7"`);
  `pipeline/fetch.py:554-564` (`_intentos`: Standard y luego NRT, nada más); `pipeline/store.py:675-691` (el
  reemplazo NRT → Standard exige un record nuevo `standard`); `pipeline/product_version.py` (marca `nrt` por el token
  `.NRT.`); `scripts/run_pipeline.py:386-399` (el NRT reprocesa 8 días, el día de hoy y 7 atrás).
- **SCRIPT:SALIDA**: `cmr_colecciones_y_granulos_salida.txt` (§2): la 6.1 Standard sigue ACTIVE con gránulos al
  2026-10-21; existe C7 Standard; **no existe C7 NRT**.
- **QUÉ PASA**: hoy nada. El día que LAADS retire la 6.1 de verdad: (a) el NRT sigue andando por `6.1NRT`, pero todos los
  records MODIS quedan `product_version: "nrt"` para siempre, porque nunca llega una Standard 6.1 que los reemplace;
  (b) todo reproceso, backfill o A/B de MODIS sobre días más viejos que la retención de LANCE (unos siete días) encuentra
  cero gránulos en las dos colecciones y sale con «Cobertura: completa» (mismo mecanismo que H1); (c) si después LANCE
  pasa su NRT a la C7, MODIS queda en cero también en el NRT. Ese último caso sí lo ve la vigilancia de la sombra a los
  cuatro días (control positivo de H2), con un issue titulado «vigilancia ciega» que manda a revisar
  `experimental-diario.yml`, o sea al lugar equivocado.
- **CÓMO SE VE EN EL DASHBOARD**: (a) invisible; (b) invisible en el tablero, pero un A/B de MODIS mediría un brazo sin
  datos; (c) desaparecen los puntos MODIS de todos los volcanes.
- **CÓMO REPRODUCIRLO**: `python -I C:\vrp-trabajo\s159-pruebas\experiments\_s159\cese_snpp\cmr_colecciones_y_granulos.py`; repetir
  semanalmente y mirar la línea `MOD021KM v6.1`.
- **CONFIANZA**: CONFIRMADO el código y el estado de CMR; las consecuencias (a) a (c) son CONFIRMADO por lectura, no
  simuladas con la colección retirada. Si la C7 cambia algo del L1B que lea `process_modis.py` es SOSPECHA sin mirar.
- **GRAVEDAD**: 3, latente (no tiene fecha cierta; la anunciada ya pasó sin ejecutarse).

### H5. Gránulos Standard que ya usamos y que hoy CMR no lista (18 y 19 de octubre)

- **SCRIPT:SALIDA**: `cmr_hueco_17_20_oct_salida.txt`. CMR hoy: Standard 0 el 18 y el 19 en VNP02IMG, VJ102IMG y
  MOD021KM 6.1 sobre todo Chile. Nuestros records de `origin/main` de esos días: todos `standard`, con nombres de
  producción del día (Villarrica: `VNP02IMG.A2026291.0542.002.2026291121847.nc`,
  `VJ202IMG.A2026292.0448.021.2026292102240.nc`, `MYD021KM.A2026292.0830.061.2026292193305.hdf`).
- **QUÉ PASA**: NASA publicó esos Standard, el NRT los procesó, y después dejaron de aparecer en el catálogo (lo más
  probable, ligado al aviso «VIIRS Data Product Processing Delay» y a los huecos de nivel 0 del 12 y 13 de octubre que
  cita el frente de bibliografía: SOSPECHA). Un reproceso de esos días hoy caería al NRT (gránulos distintos de los que
  produjeron el record) y, cuando LANCE los descarte, a cero, otra vez con «Cobertura: completa».
- **CÓMO SE VE EN EL DASHBOARD**: invisible. Afecta la reproducibilidad de los A/B que crucen esas fechas.
- **CÓMO REPRODUCIRLO**: `python -I C:\vrp-trabajo\s159-pruebas\experiments\_s159\cese_snpp\cmr_hueco_17_20_oct.py <arbol>`.
- **CONFIANZA**: CONFIRMADO (los nombres y los conteos); la causa, SOSPECHA.
- **GRAVEDAD**: 2.

### H6. La ficha pública del SDA declara Suomi NPP como entrada

- **ARCHIVO:LÍNEA**: `docs/FICHA_SDA_VRP_CHILE.md:29` («VIIRS `VNP02IMG`/`VJ102IMG`/`VJ202IMG` (375 m) y
  `VNP02MOD`/`VJ102MOD`/`VJ202MOD` (750 m)») y `:40-42` (la propia ficha dice revisarla «cuando cambie ... los sensores
  de entrada»).
- **QUÉ PASA**: desde el 2-nov la ficha que exige la Resolución CPLT N°372 declarará una entrada que ya no existe, y no
  dirá que el muestreo VIIRS bajó un tercio.
- **CÓMO SE VE EN EL DASHBOARD**: invisible en el tablero; visible para quien lea la ficha.
- **CONFIANZA**: CONFIRMADO. **GRAVEDAD**: 2 (transparencia, no decisión).

### H7. La vigilancia de la sombra juntará protegidas más lento

- **ARCHIVO:LÍNEA**: `scripts/vigilancia_sombra.py:30` («hasta ver 29 protegidas A nocturnas ... o 120 días»).
- **QUÉ PASA**: 47 de las 188 pasadas VIIRS 375 pareadas a una alerta de MIROVA en la ventana son de SNPP (y 13 de 52 en
  VIIRS 750, `medir_peso_snpp_salida.txt`). Sin ellas el contador de protegidas vistas sube más lento, y la regla puede
  llegar a los 120 días sin haber visto 29.
- **CONFIANZA**: SOSPECHA sobre la magnitud (no conté protegidas, sino pasadas pareadas). **GRAVEDAD**: 1.

### H8. Etiquetas que nombran SNPP pero no dependen de que exista (sin efecto)

`scripts/auto_audit_weekly.py:285-287` usa `"VIIRS_SNPP"` y `"VIIRS_SNPP_750"` como nombre representativo del bucket
para el filtro diurno; `pipeline/store.py:126` lista `VIIRS_SNPP` para el piso de magnitud (hoy 0,0 en todos los
perfiles); `pipeline/process_viirs.py:237-241` y `process_viirs_mod.py:206-210` asignan el sensor por prefijo del
archivo (`VNP` → SNPP, `VJ2` → NOAA-21, el resto → NOAA-20). Ninguno se rompe sin SNPP. CONFIRMADO. GRAVEDAD 1.

## 4. Cambios mínimos recomendados, por urgencia (no implementados)

**Antes del 2 de noviembre (no tocan `pipeline/`):**

1. **Vigilancia por plataforma** en `.github/workflows/nrt-healthcheck.yml` (o como cuarto aviso en
   `scripts/vigilancia_sombra.py::_avisos_frescura`): último record por (volcán, plataforma), aviso si una plataforma con
   records en los últimos 14 días no tiene ninguno en 48 h. Con una lista de «ceses esperados» (`VIIRS_SNPP` y
   `VIIRS_SNPP_750` desde 2026-11-02 13:00 UTC) que convierta ese caso en **un** issue informativo («cese esperado
   confirmado el AAAA-MM-DD») en vez de una alarma diaria, y que siga gritando si muere NOAA-20, NOAA-21 o MODIS. Mismo
   patrón de un issue por incidente que ya usa `audit-weekly.yml`. Agregar el control positivo de §3 H2 como prueba.
2. **Aviso al operador en el tablero**, replicado en `frontend/index.html`, `diario.html` y `mosaico.html` (regla S92 L5).
   Texto propuesto: «Desde el 2 de noviembre de 2026 a las 13:00 UTC, NASA y NOAA dejaron de entregar los datos del
   satélite Suomi NPP. VIIRS (375 m y 750 m) sigue con NOAA-20 y NOAA-21: cada noche hay una mirada menos al volcán (antes
   tres, ahora dos). Una anomalía débil que sólo aparece en una de las pasadas tiene menos probabilidad de verse. Las
   series anteriores al 2 de noviembre no cambian.» Puede ir como una marca vertical en el gráfico, igual que
   `frontend/cambio_detector.js` marca el detector K.
3. **Ficha SDA v1.10** (`docs/FICHA_SDA_VRP_CHILE.md`): sacar `VNP02IMG`/`VNP02MOD` de las entradas vigentes («hasta el
   2026-11-02»), declarar la caída del muestreo y agregar la fila al historial. Sin cambio de lógica.
4. **Consulta programada el 3-nov** (manual, cinco minutos): `cmr_colecciones_y_granulos.py` para confirmar que
   `VNP02IMG_NRT` y `VNP02MOD_NRT` dejaron de recibir gránulos después de las 13:00 UTC del 2-nov (resuelve la SOSPECHA
   de §2) y que NOAA-20 y NOAA-21 siguen.

**En la semana siguiente (scripts de medición, no `pipeline/`):**

5. **Marca de régimen de plataformas en `scripts/auto_audit_weekly.py`**: estratificar recall y falsas publicaciones
   por noche antes y después del 2026-11-02 (como ya se hace con la frontera del detector K), e informar pasadas por noche.
   Sin eso, la ventana de 60 días mezcla dos muestreos hasta enero.

**Con tag defensivo y sí de Nicolás (A45), sin urgencia:**

6. `pipeline/fetch.py:1061-1070`: dejar de pedir SNPP para fechas posteriores al 2026-11-02 y conservarlo para
   reprocesos históricos, con una línea de log «plataforma retirada». Beneficio pequeño (ahorra 4 a 12 consultas vacías
   por volcán y corrida, sin riesgo de cuelgue); su valor real es que el log diga por qué falta.
7. `scripts/run_pipeline.py` (`informar_cobertura`): sumar a la cobertura las plataformas que dieron cero gránulos en
   **todos** los días de la corrida, como nota y no como falla. Habría hecho visible H1 y H4(b) sin vigilancia aparte.
8. **MODIS C7**: no cambiar la versión en silencio. Antes del día en que LAADS ejecute el decomiso, pre-registrar un A/B
   6.1 contra 7 (la C7 trae otra calibración; qué colección usa MIROVA hoy no lo verifiqué) y decidir si `"7"` entra
   como versión Standard alternativa. Mientras tanto, la recomendación 1 debería incluir el último gránulo de
   `MOD021KM 6.1` y `6.1NRT` en CMR, para enterarse el mismo día.

Fuera de este repo: el scraper Mirova-v1 también verá a MIROVA perder SNPP (filas de la tabla y del OCR de imágenes por
plataforma). No lo revisé: SOSPECHA de que hay que mirar cómo trata el fin de una plataforma.

## 5. VERIFICADO LIMPIO (no hace falta volver a mirarlo)

- **No hay cuelgue ni gasto de tiempo por el cese**: con SNPP vacío, `fetch_for_volcano` hace las mismas 16 consultas que
  con SNPP vivo y ninguna descarga (`simular_snpp_vacio_salida.txt`). Sin gránulos no se toca `nrt3.modaps`, así que el
  cortacircuito de descarga (A64) no entra en juego. La búsqueda por ventana de S157 (`pipeline/fetch.py:625-647`)
  también reparte `[]` por día y sigue.
- **Una colección vacía o inexistente no da error en CMR**: `MYD021KM_NRT` da 0 colecciones y el pipeline lo vive como
  `[]` (`cmr_colecciones_y_granulos_salida.txt`; `pipeline/fetch.py:179-181`).
- **El etiquetado de sensor no depende de que SNPP exista** (`process_viirs.py:237-241`, `process_viirs_mod.py:206-210`),
  ni el piso de magnitud (`store.py:126`, pisos en 0,0), ni el filtro diurno del auto-audit (`auto_audit_weekly.py:285-299`).
- **Ninguna noche queda sin VIIRS al sacar SNPP** en la ventana 2026-09-18 a 2026-10-20: 0 de 362 noches por sensor
  dependían sólo de SNPP (`medir_peso_snpp_salida.txt`).
- **El archivo histórico de SNPP sigue disponible** (LAADS 199516), así que los reprocesos anteriores al 2-nov no cambian.
- **La sombra y la producción pierden SNPP a la vez** (las dos usan el mismo `fetch.py`), así que la comparación de la
  vigilancia de la sombra no se sesga por el cese; sólo se vuelve más lenta (H7).
- **NOAA-20 y NOAA-21 NRT y Standard están vivas** sobre Chile al 2026-10-21 (25 y 30 gránulos NRT en 3 días).

Comandos: los cinco scripts de `C:\vrp-trabajo\s159-pruebas\experiments\_s159\cese_snpp\` con su `_salida.txt` al lado;
los que llevan `<arbol>` necesitan el `git archive origin/main pipeline scripts frontend data/mirova_reference` más los
11 JSON Tier A de `data/mirova_equivalent/`.

Fuentes: [NASA Earthdata, aviso 2026-10-21](https://www.earthdata.nasa.gov/data/alerts-outages/reminder-suomi-npp-observations-cease-november-2-2026) ·
[LAADS 199516](https://ladsweb.modaps.eosdis.nasa.gov/alerts-and-issues/199516) ·
[LAADS 199534](https://ladsweb.modaps.eosdis.nasa.gov/alerts-and-issues/199534) ·
[LDOPE 1479](https://landweb.modaps.eosdis.nasa.gov/displayissue?id=1479) ·
[NESDIS Update #2, 2026-10-19](https://www.nesdis.noaa.gov/news/administrative-update-2-cessation-of-suomi-national-polar-orbiting-partnership-s-npp-data-users-november-02-2026-1300-utc-and-decommissioning-issued-october-19-2026-1400-utc) ·
[Earthdata, aviso viejo del 2026-08-07 con fecha 1-nov](https://www.earthdata.nasa.gov/data/alerts-outages/suomi-npp-data-product-delivery-cease-november-1-2026).
