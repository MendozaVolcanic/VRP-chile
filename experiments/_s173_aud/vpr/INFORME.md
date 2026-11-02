# INFORME del segundo verificador: pre-registro de la prueba retrospectiva del paquete (ronda 2, sin sello)

## 1. Encabezado

- Hora del servidor de GitHub al empezar: **2026-11-02 12:21:10 GMT**; al cerrar las mediciones: **12:43:40 GMT**
  (`gh api -i repos/MendozaVolcanic/VRP-chile`, cabecera `Date`). 4 llamadas de lectura a la API en total (3 de hora,
  1 `gh run view 39125546355`).
- Objeto: `origin/loop/activo:experiments/_s172_prereg_retro/PREREGISTRO_RETRO_PAQUETE.md`, 630 lineas, sha256
  `aad33de7348e92bdb2fb8e2b2d3878954ef170b935fb5615cd1b667d93c87f9e` (coincide con el `aad33de7` de la tarea).
  Copia de trabajo: `D:/vrp-trabajo/temporales/s173_aud/vpr/PREREGISTRO_copia.md`. Ultimo commit del archivo en
  `origin/loop/activo`: `18ab00217` (2026-11-01 23:13:25 -0300). La ronda 1 (`01be21ff5`) da sha256 `45f48a930a…`,
  como dice el encabezado del pre-registro.
- Commits de hoy (tras `git fetch origin --prune`): `origin/loop/activo` = `c28a0889191181a75cb5dbb5dfba9b2e58149476`,
  `origin/main` = `c3540b731f2b8331a7abcacb74f811375c38aa2a` al empezar y `47cdc446f29f712e55961886799b76578eb8deee`
  al exportar (NRT entre medio). El pre-registro cita `origin/main` = `14fb62030` y `loop/activo` = `fa22f4b87`;
  `git diff --stat 14fb62030 origin/main -- . ':!data' ':!latest_consolidado.csv'` esta VACIO: ninguna linea citada
  de codigo o docs se movio entre el commit citado y hoy.
- Modelo y esfuerzo reales: **Claude Fable 5.1 (claude-fable-5-1)**. El esfuerzo de razonamiento es el que fijo la
  coordinadora al lanzarme; no lo puedo leer desde adentro ni lo cambie.
- CARPETA: `D:/vrp-trabajo/temporales/s173_aud/vpr/` (scripts con su salida al lado, `caminos.md`,
  `hallazgos.csv`, `main_export/` con el `git archive` de `origin/main` usado para medir, este informe).
- `caminos.md` escrito antes de abrir ningun archivo citado; sha256 del contenido antes del sello `8dcd11d1b97e2dbd…`
  y con el sello (hora 12:23:57 GMT y sha) `a57819593fc2db88…`. No se volvio a editar.
- Disco: C: 34 GB libres todo el rato; D: 7,4 GB al empezar, oscilo entre 3,6 y 4,8 GB por otros agentes (mi carpeta
  pesa ~190 MB). Nunca bajo de 3 GB; lo mire antes de cada corrida.
- Vara que use: la del preambulo. «Produccion» leida con `pipeline.profile` en el worktree de PR B
  (`flags_prb_pipeline_profile.txt`); «publica» con el predicado del tablero ejecutado con node por
  `scripts/banco_paridad.py` de `origin/main` exportado; «alerta protegida» con `clase_mirova.alerta_protegida`
  lectura A y la regla SN de D-9; referencia = la copia del worktree (sha256 `ab1a208c…` y `d4ad8c44…`, comprobados).
- Que NO mire (para que el silencio no se lea como «todo bien»): §6.

## 2. En una pantalla

**Veredicto: SELLABLE CON CAMBIOS** (lista exacta en §3 bis). Ninguna ventana de seleccion de parametros de las tres
vias toca febrero de 2026 ni 2025 (verificado linea a linea en los seis pre-registros citados y en los de D25 y MxD03), y
las cifras de poder se reproducen con scripts mios sobre la referencia del worktree y el OSF (26 / 30 / 9 protegidas en
F26, 317 / 17 en el OSF, 48 / 18 / 6 bloques, K pierde solo Lascar MODIS 2026-02-16 01:20). Lo que no se sostiene es
(a) el inventario de pasadas «miradas por nombre» del §3.1 (b): falta Lastarria MODIS 2026-02-24 07:05, que es uno de
los cinco negativos publicados por K en F26-M, y faltan siete pasadas de 2025 nombradas en los informes de la sonda M y
de CM162; (b) la cifra MODIS del OSF (162 con «1 Villarrica») contradice la regla «noche del proyecto» (son 161; la de
Villarrica es diurna); (c) cuatro reglas que dos lectores leerian distinto: SIN SUSTRATO en VIIRS 375 cumple por el
codigo sellado (§9.7) pero cae en la fila 5; «veta» significa fila 2 en F26 y fila 4 en R25 sin decirlo en C-cobertura;
el placebo «M no da MEJORA» da MEJORA por d con K bajo 0,83 de MIROVA si no se exige d′ (D-28); y las excepciones
«nombradas» de C-K y del nulo no tienen tope. El brazo de control y el del paquete corren el mismo codigo salvo las
vias, y el merge del PR B no los contamina (flags escritos en `thresholds:`, deep-merge hijo-gana, predicado del
tablero sin cambio).

## 3. Hallazgos (de mayor a menor gravedad)

### VPR2-01
- TÍTULO: El inventario (b) del §3.1 esta incompleto: una pasada negativa de F26-M y siete de 2025 fueron miradas por nombre y no estan
- ARCHIVO:LÍNEA: `PREREGISTRO_copia.md` l. 129 a 137 (y l. 397: «Sin las tres pasadas de §3.1 (b), F26-M queda con 5 bloques donde K publica un negativo limpio»). Evidencia: `origin/main:experiments/_s159/m/INFORME.md` l. 49 (TEXTO: «se apaga | RUTINA (miró y no vio nada) | 5: … Lastarria 2026-02-24 07:05 …»), l. 50, 51 y 78; `origin/main:experiments/_s159/m/analizar_m_salida.txt` l. 51; `origin/main:experiments/_s162_vuelta2/CUMULOS_POR_MATRIZ.md` l. 15, 64, 66; `origin/loop/activo:experiments/_s172_chillan/auditor/INFORME.md` l. 153. Salidas mias: `febrero_pasadas_nombradas.txt`, `pasadas_2025_nombradas.txt`, `contar_f26_F26M_bloques_modis.txt`.
- QUÉ PASA: la sonda M de MxD03 (S159) miro por nombre la pasada MODIS Aqua de Lastarria del 2026-02-24 07:05 (K publica 0,529 MW donde la tabla dice RUTINA; con MxD03 «se apaga»). Esa pasada es uno de los cinco bloques «negativo publicado por K» de F26-M que mi conteo lista (Puyehue 02-01, 02-04, 02-07, 02-28 y Lastarria 02-24). El pre-registro dice que las tres de Lascar son «exactamente» las de (b) y que sin ellas quedan 5 bloques de negativos: quedan 4 si se saca tambien Lastarria, y con B de 4 o menos la regla de signos da SIN SUSTRATO por construccion. En 2025 la sonda M nombro Llaima 2025-02-15 03:15 (1,243 MW), Lascar 2025-03-17 06:25, 2025-05-23 07:25 y 2025-06-02 07:20 y Cordon Caulle 2025-08-03 06:35 (MODIS, contra el OSF); CM162 nombro Lascar VIIRS 750 2025-07-07 05:24; el auditor de Chillan, 2025-11-04 06:00. Ninguna eligio parametros (tipo b, no a), pero la lectura «con y sin (b)» que el propio pre-registro ordena necesita la lista completa.
- CÓMO SE VE EN EL DASHBOARD: invisible (es un defecto del protocolo, no del dato).
- CÓMO REPRODUCIRLO: `git grep -n 'Lastarria.\{0,40\}2026-02-24 07:05' origin/main -- experiments`; `python contar_f26.py <export> 2026-02-01 2026-02-28 F26M` y mirar `contar_f26_F26M_bloques_modis.txt` (Lastarria 2026-02-24T07:05 MODIS_AQUA neg_limpio pub=1 pc_vrp=0.529).
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 3 (en F26-M el contraste descansa en 6 bloques; una pasada mal inventariada cambia el denominador de la lectura «sin (b)» y puede mover el veredicto de MODIS entre SIN PODER y otro).

### VPR2-02
- TÍTULO: SIN SUSTRATO de P2 cumple en la regla sellada de VIIRS 375 pero cae en la fila 5 del §8.1: dos lectores, dos veredictos
- ARCHIVO:LÍNEA: `PREREGISTRO_copia.md` l. 418 (fila 5: «la regla da SIN SUSTRATO en F26 … SIN PODER FUERA DE MUESTRA») y l. 275 (la regla de 375 es «§5.4 (a) a (d) … y el código del §9.7»). `s170-v375e-lector:experiments/_s162_v375/PREREGISTRO_E.md` §9.7, tabla, fila (b), TEXTO: «P2 contra K GANA, EMPATE o SIN SUSTRATO … el silencio no da ENCIENDE DE MAS» en la columna CUMPLE (mi extracto en la salida del comando de abajo, l. 9 y 14). Para VIIRS 750, `aa5583646:experiments/_s162_v750a/PREREGISTRO_V750A.md` l. 232 a 233 pide «P2 … GANA o EMPATE (no PIERDE ni BLOQUEA)» y no nombra SIN SUSTRATO.
- QUÉ PASA: la regla sellada de V375-E mapea SIN SUSTRATO de P2 a CUMPLE («con 4 bloques discordantes o menos, el brazo y K casi no difieren en errores»), asi que aplicada en codigo nunca «da SIN SUSTRATO» y el veredicto cae en la fila 6 (NO SE CONTRADICE); leida literalmente, cae en la fila 5 (SIN PODER). En MODIS la regla F4 (fila 4 de su §7) si da INDECIDIBLE, que el §5.6 renombra SIN PODER. El §5.6 solo declara el caso de MOD-D. En 750, la regla de V750-A no dice que pasa con SIN SUSTRATO ni con BLOQUEA de signo cero, asi que el lector tiene que inventarlo.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git show s170-v375e-lector:experiments/_s162_v375/PREREGISTRO_E.md | sed -n '/^### 9\.7/,+40p' | grep -n 'SIN SUSTRATO'`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2 (con 48 bloques donde K yerra en 375 es improbable que B quede en 4 o menos, pero la regla tiene que ser computable igual; en 750 con 18 bloques es menos improbable).

### VPR2-03
- TÍTULO: «Veta» significa NO SE SOSTIENE en F26 y DECIDE NICOLÁS en R25, y C-cobertura lo usa sin decir el tramo
- ARCHIVO:LÍNEA: `PREREGISTRO_copia.md` l. 356 (C-cobertura: «Una protegida SIN DATO que K publica veta (como leer_sombra_v375e.py l. 573)»), l. 355 (C-via R25: «veta (lleva a DECIDE NICOLÁS, como toda candidata OSF)»), l. 415 (fila 2: «incluida una SIN DATO que K publica») y l. 417 (fila 4: «candidata a veto en P1-OSF»).
- QUÉ PASA: la misma palabra lleva a la fila 2 (NO SE SOSTIENE) cuando la protegida es de la tabla en F26 y a la fila 4 (DECIDE NICOLÁS) cuando es del OSF en R25. C-cobertura cubre los dos tramos y dice «veta» a secas: una protegida OSF que la via descarta sin record (regla de cobertura de `mirova_v750_codigo.py` l. 798 a 808) y que K publica se puede leer como fila 2 o como fila 4. La cita a `leer_sombra_v375e.py` l. 573 (tag `s170-v375e-lector`; en el tag `s172-v375e-lector-resellado` es la l. 612) es de un lector que solo tiene tabla: no resuelve el caso del OSF.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: leer las cuatro lineas citadas.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### VPR2-04
- TÍTULO: El placebo «M no da MEJORA» da MEJORA por d cuando K esta bajo 0,83 de MIROVA, salvo que se exija d′ (D-28); en 750 «MEJORA» no existe
- ARCHIVO:LÍNEA: `PREREGISTRO_copia.md` l. 361 (PLACEBO: «M no da MEJORA | instrumento roto»); `evaluar_d25_blob_1dbabf65.py` l. 245 a 253 (`regla_m` y `d_par`: d = |log10(D/M)| − |log10(K/M)|; MEJORA si el IC queda entero bajo 0); `origin/main:experiments/_s157_prereg_d25/ADENDA_PLACEBO.md` l. 15, TEXTO: «un brazo K×1,2, que no es ningún mecanismo, da MEJORA con» y l. 55: «D = K×1,2 … d′ es idénticamente 0, así que **no puede** dar MEJORA»; `aa5583646:…/PREREGISTRO_V750A.md` l. 234 a 236 (M de 750 es una banda [0,9; 1,1] y «el comparador separa a P de K×1,2»).
- QUÉ PASA: con K/MIROVA en 0,65 (el propio §9 predice 0,6 a 0,7 en 375 y bajo 0,8 en 750), K×1,2 queda en 0,78, mas cerca de MIROVA: d = |log10 0,78| − |log10 0,65| = 0,108 − 0,187 < 0, o sea MEJORA legitima por d. D-28 lo resolvio exigiendo ademas d′ (ganancia pareja) para contar MEJORA; el F4 importa `comparar_con_ganancia`, pero el §6 del pre-registro no dice que el «M» del placebo es el de D-28. Un lector que aplique `regla_m` sobre d declara «instrumento roto» sobre un instrumento sano y deja los tres sensores INDECIDIBLES (fila 1). En 750 la M es una banda: «no da MEJORA» no esta definido; la prueba de V750-A es otra (el comparador separa P de K×1,2).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -c "import math; print(abs(math.log10(0.78))-abs(math.log10(0.65)))"` (da −0,079).
- CONFIANZA: CONFIRMADO (la aritmetica y las citas); que el lector futuro lo lea mal es SOSPECHA.
- GRAVEDAD: 2.

### VPR2-05
- TÍTULO: Las protegidas MODIS del OSF son 161, no 162: la de Villarrica es diurna con la noche del proyecto que el §4.2 dice usar
- ARCHIVO:LÍNEA: `PREREGISTRO_copia.md` l. 226 («Se usa la noche del proyecto (elevación solar), no `Dayflag`»), l. 238 a 240 («162 en 1 km (155 Láscar, 6 Planchón-Peteroa, 1 Villarrica)»; «160 de 160 con record (dos MODIS sin record de K)»), l. 384 («R25, 1 km | 162 | … | 1,9 % (sin Láscar: 7, 43 %)»), l. 225 («las cuatro diurnas con 0 son MODIS, una de 1 MW o más»). SCRIPT:SALIDA `contar_osf.py` → `contar_osf_vent_salida.txt` y `contar_osf_centro_salida.txt`.
- QUÉ PASA: con noche por elevacion solar, class 1, VRP ≥ 1e6 W y pixel mas caliente a ≤ `inner_radius_km` del crater (con `vent_lat/lon` y tambien con el centro: mismo resultado), el OSF da **161** protegidas en 1 km (Lascar 155, Planchon-Peteroa 6), K publica 160 y 1 queda sin record a ±120 s. La fila de Villarrica (2025-03-26 13:55, 14,39 MW, `Dayflag` 0) es **de dia** para el proyecto: es una de las «cuatro diurnas con 0». Y de esas cuatro, tres tienen 1 MW o mas (1,27; 1,53; 14,39), no una. Consecuencias: «sin Láscar: 7, 43 %» pasa a 6 y 50 %; «dos sin record» es uno sin record mas una diurna. 375 (317: 273 / 28 / 14 / 2), 750 (17 Lascar), pisos (0,011 / 0,176 / 5,053), 2.577 filas, 49 lejanas de Chillan a 12,1 a 19,6 km, 13 ambiguas (9 Lascar, 4 Puyehue) y Δt = 0 s en los 494 pares se reproducen exactos.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python contar_osf.py D:/vrp-trabajo/temporales/s173_aud/vpr/main_export "<raiz>/data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv" vent`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2 (cifra de poder y de denominador en la tabla del §7; no cambia el diseño).

### VPR2-06
- TÍTULO: C-K y el nulo del runner admiten excepciones «nombradas con su causa» sin tope: un control que no puede fallar
- ARCHIVO:LÍNEA: `PREREGISTRO_copia.md` l. 357 («salvo pasadas nombradas con su causa escrita antes de leer F26») y l. 362 («B = 0 en P2 salvo las pasadas nombradas de C-K»).
- QUÉ PASA: las excepciones se escriben despues de ver que K-gemelo y K de disco difieren y antes de leer F26: no hay numero maximo ni criterio de que cuenta como causa (el ejemplo, un empate de `argsort`, S152, es legitimo, pero nada impide nombrar 40). A110 y A116: un control sin forma de fallar no es control. El pre-registro mismo rechaza el 1 % por ser del tamano del efecto y luego deja la puerta sin medida.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: leer las dos lineas.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### VPR2-07
- TÍTULO: El texto de V750-A que se aplicaria «como anexo no verificado» no esta fijado por commit ni por lineas
- ARCHIVO:LÍNEA: `PREREGISTRO_copia.md` l. 276 («se aplica el mismo texto como anexo **no verificado**») y l. 124 (cita `aa5583646` solo para la ventana). Verificado: en `aa5583646` el §6 esta en l. 217 a 243, el §6 bis en l. 174 a 196 y el §6 ter en l. 197 a 216 de `experiments/_s162_v750a/PREREGISTRO_V750A.md`; el worktree `.claude/worktrees/s162-viirs750-2-918174` sigue en esa punta.
- QUÉ PASA: V750-A es borrador; si se edita antes del despacho D2, «el mismo texto» cambia sin que este pre-registro lo note (A95). Hay que fijar commit y lineas.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git show aa5583646:experiments/_s162_v750a/PREREGISTRO_V750A.md | grep -n '^## 6'`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### VPR2-08
- TÍTULO: Seis de las catorce decisiones no se contestan con «sí» sin ambigüedad (R-2, R-3, R-6, R-8, R-11, R-12)
- ARCHIVO:LÍNEA: `PREREGISTRO_copia.md` l. 552 (R-2 «¿de disco … o re-corrido entero?»), 553 (R-3 no es pregunta), 556 (R-6 «¿Con qué lectura B…?»), 558 (R-8 «Febrero y marzo de MODIS», sin pregunta), 561 (R-11 doble: «¿… te basta …?» mas «no como prueba de los volcanes débiles»), 562 (R-12 «¿esperar su sello o correr con techo…?»).
- QUÉ PASA: Nicolas suele contestar «sí a todo» (asi aprobo la sombra, `sombra_codigo_mirova.yaml` l. 2). Un «sí» a una disyuntiva (R-2, R-12) o a una fila sin pregunta (R-3, R-8) no es computable; en R-11 un «sí» podria leerse como aceptar el sensor «como prueba de los volcanes débiles», que es lo contrario de la recomendacion. Las otras ocho (R-1, R-4, R-5, R-7, R-9, R-10, R-13, R-14) si se leen de una sola manera.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: leer la tabla del §12.
- CONFIANZA: CONFIRMADO (la forma); que Nicolas conteste asi es SOSPECHA apoyada en el precedente.
- GRAVEDAD: 2.

### VPR2-09
- TÍTULO: C-montaje decide con «cada diferencia se explica», sin criterio de que cuenta como explicacion
- ARCHIVO:LÍNEA: `PREREGISTRO_copia.md` l. 358.
- QUÉ PASA: «se escriben las diferencias esperadas» y «una no explicada deja todo INDECIDIBLE» dependen de un juicio del lector. Un criterio computable seria: una diferencia esta explicada solo si un hunk listado del `git diff` entre el tag de origen y el del despacho la reproduce al re-correr esa pasada con el codigo del tag de origen (o si la pasada cambia de granulo, `otro_granulo`); lo demas, INDECIDIBLE.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: leer la linea.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 2.

### VPR2-10
- TÍTULO: «Marzo de 2026 lo toca sólo en MODIS (MOD-D)» omite la ventana V2 de K, y el inventario no nombra a D25
- ARCHIVO:LÍNEA: `PREREGISTRO_copia.md` l. 127; `origin/main:experiments/_s151_prereg_fk_11/PREREGISTRO.md` l. 99 a 102 (V2 2026-03-01 a 06-12, «MODIS, toda la ventana»; VIIRS desde el 04-01); `origin/main:experiments/_s153_fk_v2/v2.log` l. 15 («en V2, VIIRS desde abril»: marzo de VIIRS no entro al sustrato, verificado). D25: `docs/PREREGISTRO_AB_D22_D25_S143.md` l. 89 y 91 (2026-06-01 a 08-31; 09-01 a 09-15) y `experiments/_s157_prereg_d25/PREREGISTRO.md` (04-01 a 06-12; 08-29 a 10-08). Salida: `cita_k_prereg_l85_105.txt`, `cita_fk_v2_marzo.txt`.
- QUÉ PASA: la frase resume mal la tabla de arriba, que si lista a K con marzo. K es el control y su seleccion no contamina a la via, pero marzo de MODIS lo tocaron dos selecciones, no una. D25 no toca F26 ni 2025 (verificado), pero la tarea lo pedia y el inventario no lo dice.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: los `git show` citados.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

### VPR2-11
- TÍTULO: Las cifras de composicion por satelite del §3.3 no se reproducen con SN y Tupungatito desde el 02-23 (800 / 132 / 163 contra 790 / 111 / 162)
- ARCHIVO:LÍNEA: `PREREGISTRO_copia.md` l. 178 a 180. SCRIPT:SALIDA `contar_f26.py` → `contar_f26_F26_salida.txt` (linea «por satelite»).
- QUÉ PASA: con tabla sola, SN, noche del proyecto y Tupungatito desde el 02-23 obtengo en 375: NOAA-20 790 etiquetadas y 111 sin fila; Suomi NPP 162 etiquetadas y 702 sin fila; NOAA-21 895 sin fila (igual); en 750: NOAA-20 844 y Suomi NPP 198 etiquetadas (el pre-registro dice 855 y 200). El total de 1.708 sin fila en 375 y los 895 / 889 de NOAA-21 si coinciden. El pre-registro no dice con que reglas conto el verificador; la conclusion («la evidencia de F26-V es NOAA-20 y las pasadas oblicuas de Suomi NPP») no cambia.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python contar_f26.py D:/vrp-trabajo/temporales/s173_aud/vpr/main_export 2026-02-01 2026-03-31 F26`.
- CONFIANZA: CONFIRMADO EN PARTE (los totales si; el desglose por satelite difiere en 10 a 21 pasadas).
- GRAVEDAD: 1.

### VPR2-12
- TÍTULO: Dos citas que no se localizan como estan escritas («27 pasadas contra 48 bloques; V375-E l. 66 a 68» y «port de V750 0,994 a 0,998»)
- ARCHIVO:LÍNEA: `PREREGISTRO_copia.md` l. 357 y l. 64 a 65. `s170-v375e-lector:experiments/_s162_v375/PREREGISTRO_E.md` l. 66 a 68 habla de la equivalencia («tolerar 1 % de pasadas distintas, ~8 de 859»); «27 pasadas» y «48 bloques» no aparecen en ese archivo (grep vacio, `cita_v375e_ventana.txt`). `origin/loop/activo:experiments/_s172_chillan/verificador/INFORME.md` l. 28 dice 0,996 sobre 22 y 0,998 sobre 28; 0,994 no esta en esa linea.
- QUÉ PASA: el «48 bloques» es el propio conteo del §7 (yo lo reproduzco); la cita de V375-E para el «1 % es del tamaño del efecto» corresponde a la equivalencia, no a P2. Cita vieja, SIN LOCALIZAR como esta.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git show s170-v375e-lector:experiments/_s162_v375/PREREGISTRO_E.md | grep -n -E '27 pasadas|48 bloques'`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

### VPR2-13
- TÍTULO: La curva de cenit del §5.3 omite NULO SESGADO y el nulo de 8 noches, y la fila 4 hace decidir a la curva donde V375-E §9.7 dice que en retrospectiva solo informa
- ARCHIVO:LÍNEA: `PREREGISTRO_copia.md` l. 308 a 310 y l. 417 («la curva de la vía CAE MÁS QUE MIROVA» → DECIDE NICOLÁS); `s170-v375e-lector:…/PREREGISTRO_E.md` §5.3 (TEXTO: «SIN SUSTRATO con menos de 8 noches en la lectura o en el nulo; NULO SESGADO si el nulo no contiene 1») y §9.7 fila «(d), retrospectiva | informa, no decide | nunca | nunca» (`cita_v375e_s53.txt`).
- QUÉ PASA: el §5.3 del pre-registro copia cuatro de los seis veredictos y el §8.1 convierte uno de ellos en DECIDE NICOLÁS. Es conservador, pero es una desviacion de la regla sellada que el §5.6 no declara («ninguna cambia un umbral» es cierto; esta cambia quien decide).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `git show s170-v375e-lector:experiments/_s162_v375/PREREGISTRO_E.md | sed -n '/^### 5\.3/,+12p'`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

### VPR2-14
- TÍTULO: La «regla del tres» del §7 trata 26 noches casi consecutivas de un mismo crater como ensayos independientes, y las cifras siguen siendo «las del verificador»
- ARCHIVO:LÍNEA: `PREREGISTRO_copia.md` l. 376 a 386 y l. 403 a 404 («Antes del sello se recalculan … y se escriben aquí con su sha»).
- QUÉ PASA: la cota 3/n vale para n ensayos independientes; las protegidas de Lascar en F26 son noches de un mismo regimen (dependencia que el propio D-45 reconoce al sortear por bloque). Decirlo. Y hoy las cifras del §7 no estan recalculadas por el autor: las reproduje yo con la referencia del worktree (coinciden salvo VPR2-05 y VPR2-11); el sello deberia traer el sha de la referencia y el commit de K con que se contaron (mi export: `origin/main` `47cdc446f`, consolidado `ab1a208c…`, OCR `d4ad8c44…`).
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `contar_f26_F26_salida.txt`, `contar_f26_F26M_salida.txt`, `contar_osf_vent_salida.txt`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: 1.

## 3 bis. Cambios de texto exactos para que sea SELLABLE

1. §3.1 (b): agregar «MODIS, Lastarria 2026-02-24 07:05 Aqua (negativo que K publica, mirado por la sonda M, `experiments/_s159/m/INFORME.md` l. 49)» y una viñeta «2025 (contra el OSF): Llaima 2025-02-15 03:15, Láscar 2025-03-17 06:25, 2025-05-23 07:25 y 2025-06-02 07:20, Cordón Caulle 2025-08-03 06:35 (MODIS, sonda M, l. 50, 51 y 78); Láscar VIIRS 750 2025-07-07 05:24 (CM162, `_s162_vuelta2/CUMULOS_POR_MATRIZ.md` l. 15); Chillán 2025-11-04 06:00 (auditor S172 l. 153)». Cambiar «Son exactamente las tres de febrero en que K no publica una alerta» por «Son las tres de febrero en que K no publica una alerta; la cuarta es un negativo que K publica». En §7 corregir «queda con 5 bloques … negativo limpio» por «4 bloques (Puyehue 02-01, 02-04, 02-07 y 02-28)» y decir que con 4 la regla da SIN SUSTRATO por construccion. (VPR2-01)
2. §8.1 fila 5: «la regla da SIN SUSTRATO en F26 **o, en VIIRS 375 y 750, P2 contra K da SIN SUSTRATO aunque el código del §9.7 de V375-E lo mapee a CUMPLE** (y ninguna condición de la fila 4)». Y en §5.6 una fila «SIN SUSTRATO en V375-E §9.7 (b) | CUMPLE | SIN PODER | el mismo nombre para los tres sensores». En 750, decir que BLOQUEA y SIN SUSTRATO se leen como en D-45 (`regla_signos_p2`). (VPR2-02)
3. §6 C-cobertura: «Una protegida SIN DATO que K publica: en F26, fila 2 del §8.1; en R25, candidata a veto (fila 4)». Y en C-via R25 reemplazar «veta» por «es candidata a veto (fila 4)». (VPR2-03)
4. §6 PLACEBO: «M (la de D-28: d **y** d′ con `comparar_con_ganancia`) no da MEJORA en MODIS ni en VIIRS 375; en VIIRS 750, el comparador de V750-A §6.2 separa la vía de K×1,2». (VPR2-04)
5. §4.2 y §7: «161 en 1 km (155 Láscar, 6 Planchón-Peteroa)»; «K ya las publica todas: 317 de 317, 17 de 17 y 160 de 161 con record (una MODIS sin record de K a ±120 s)»; fila R25 1 km: «161 … 1,9 % (sin Láscar: 6, 50 %)»; «las cuatro diurnas con 0 son MODIS, tres de 1 MW o más (entre ellas Villarrica 2025-03-26 13:55, 14,39 MW)». (VPR2-05)
6. §6 C-K y nulo del runner: fijar un tope a las excepciones, por ejemplo «a lo más 3 pasadas por sensor, cada una con el empate de `argsort` mostrado en el record; si hacen falta más, C-K cae». (VPR2-06)
7. §5.1 fila VIIRS 750: «el texto de `aa5583646:experiments/_s162_v750a/PREREGISTRO_V750A.md` §6 (l. 217 a 243), §6 bis (l. 174 a 196) y §6 ter (l. 197 a 216); si V750-A se sella en otro commit, se lista el diff». (VPR2-07)
8. §12: reescribir R-2, R-3, R-6, R-8, R-11 y R-12 como «¿Aceptas: <recomendación>?» de modo que «sí» tenga una sola lectura; en R-11 separar la segunda frase a la columna «por qué». (VPR2-08)
9. §6 C-montaje: definir «explicada» como en VPR2-09 (hunk del diff que reproduce la diferencia, u `otro_granulo`). (VPR2-09)
10. §3.1 l. 127: «Marzo de 2026 lo tocan MOD-D y la V2 de K (control), sólo en MODIS». Agregar fila «D25 (S143, S157) | 2026-04-01 a 06-12; 06-01 a 09-15; 08-29 a 10-08 | no se adopta (S162)». (VPR2-10)
11. §3.3: o reemplazar 800 / 132 / 163 / 855 / 200 por las cifras con SN y Tupungatito desde el 02-23 (790 / 111 / 162 / 844 / 198) o escribir con qué reglas se contaron las del verificador. (VPR2-11)
12. §6 C-K: quitar «V375-E l. 66 a 68» (SIN LOCALIZAR) y citar el §7 de este mismo documento; §1: «0,996 a 0,998». (VPR2-12)
13. §5.3: agregar NULO SESGADO y «8 noches en la lectura o en el nulo»; §5.6: fila «curva CAE MÁS en retrospectiva | informa (V375-E §9.7) | DECIDE NICOLÁS | conservador». (VPR2-13)
14. §7: «cota bajo independencia entre pasadas, que en Láscar no se cumple (noches consecutivas): es un piso». Y dejar escritas las cifras con el sha de la referencia y el commit de K. (VPR2-14)

Ninguno de los 14 cambia el diseño (brazos, ventanas, unidad, controles); todos son de texto o de definicion. Por eso SELLABLE CON CAMBIOS y no NO SELLABLE.

## 4. SEGUIMIENTOS (fuera de mi eje; no los persegui)

- S-A. En DM (2026-10-01 a 10-16) K de disco **no publica** tres protegidas de la tabla: Chillán MODIS 2026-10-12 07:20 (2,18 MW) y 2026-10-15 01:05 (1,72 MW) y Puyehue-Cordón Caulle VIIRS 750 NOAA-21 2026-10-10 05:54 (1,19 MW), las tres con `pc_vrp=None` (`contar_f26_DM_salida.txt`). Las de Chillán ya las nombra el F4 (#915); la de Puyehue no la vi citada. CONFIRMADO sobre `origin/main` `47cdc446f`. Gravedad 2 si DM se usa como control de montaje y el lector espera «K publica todas».
- S-B. `scripts/banco_paridad.sha_git` usa `git hash-object` con `cwd=ROOT`: sobre un `git archive` (sin `.git`) igual funciona (el hash no necesita repo) y da el blob del contenido tal como esta en disco. Con `core.autocrlf`, la copia del worktree da sha256 `ab1a208c…` y el `git show` de `origin/main` da `c0f18b6a…`, pero `hash-object` da el mismo blob `00feeebc…` para las dos: son el mismo contenido con otro fin de linea. Para el candado del §11 conviene fijar el sha256 **con LF** (como ya hace el lector de V375-E, `2126b743…`), no el del disco. CONFIRMADO. Gravedad 1 (feedback S163 md5 y autocrlf; S169 CRLF en sha256).
- S-C. El prompt de esta tarea tiene CRLF en disco (sha256 `e28cf896…`); con `tr -d '\r'` da el `6eff26a0…` anunciado. Mismo patron. Gravedad 1.
- S-D. `run 39125546355` tiene **178** jobs (el pre-registro dice 176; probablemente 176 `reproc` mas 2 de armado), 6 fallidos todos de Chillán, 5 cortados entre 171,4 y 171,7 min y uno (trozo 9, 2025-12-08 a 2026-01-13) que fallo a los 50 min por otra causa; el trozo 11 (2026-02-20 a 03-28) y el 12 (03-29 a 05-04) de Chillán fallaron: el K de disco de Chillán en F26 viene de otra corrida (`57d18ad78` y `c408a909e`), como dice el §2. Gravedad 1 (`run_39125546355.json`).
- S-E. El disco D: bajo a 3,6 GB libres durante la sesion por otros agentes (mi carpeta pesa ~190 MB). Gravedad 1.

## 5. VERIFICADO LIMPIO (que mire, con que comando y contra que vara)

Eje 1, fuera de muestra:
- Ventanas de seleccion, leidas en el commit o tag citado: K `origin/main:experiments/_s151_prereg_fk_11/PREREGISTRO.md` l. 88 a 102 (V1 08-29 a 10-08; V2 03-01 a 06-12, VIIRS desde 04-01); MOD-D censo `_s162_modis_paquete/PREREGISTRO.md` l. 54 a 58 (03-01 a 10-16); F4 `s168-modd-f4-sellado:…/PREREGISTRO_MODD_F4.md` l. 90 a 121 (C 03-01 a 10-16, E 10-17 a 10-26, «Enero y febrero no entran»); V375-E `s170-v375e-lector:…/PREREGISTRO_E.md` l. 69 a 70 (04-01 a 10-21 sin 12, 13, 17 a 20 de octubre) y §9.2 l. 550 a 556; V750-B `s167-v750b-adenda3-sellada:…/PREREGISTRO_V750B.md` l. 97 a 106 (T 04-01 a 06-12; O 06-13 a 11-02 12:59); V750-A `aa5583646` l. 130 a 137; S165 `origin/loop/activo:experiments/_s165_regla_posicion/INFORME.md` l. 47, 60, 75; MxD03 `_s159/mxd03_prereg/PREREGISTRO_MXD03.md` l. 231 a 237 (03-01 a 10-16; «Febrero sólo para controles»); D25 (ver VPR2-10). **Ninguna toca febrero de 2026 ni 2025.** Salidas `cita_*_ventana.txt`.
- K no uso 2025: `git show origin/main:experiments/_s151_prereg_fk_11/PREREGISTRO.md | grep -c 2025` = 0.
- Febrero de 2026 no esta nombrado en ninguna carpeta de las vias de VIIRS 375 (`git grep -c '2026-02-'` sobre `_s159/portes`, `_s159/n`, `_s162*`, `_s164*`, `_s165*`, `_s166*`, `_s168*`, `_s170*`, `_s157_prereg_d25`: solo `_s159/m` y `_s158_audit_r2`; `febrero_en_vias_archivos.txt`). Las tres de Lascar de (b) existen donde se citan (`_s159/mxd03_prereg/sustrato_mirova_modis_feb_salida.txt`, lineas «K no publica»; `_s158_audit_r2/verificador/va/INFORME.md` l. 37; `_s159/m/INFORME.md` l. 52 y 58). Los ceros de V750 de febrero de S158 RA1 existen en `contar_ceros_v750.txt` l. 71 a 150 (`cita_ra1_ceros_feb.txt`).
- La via de 750 usa el coeficiente del `.m` y las de MODIS y 375 los de S14: `origin/main:pipeline/mirova_v750_codigo.py` l. 70 a 85 (COEF_VRP_V750 = 1,97e7 × 0,5625; MODIS 1,89e7; V375 1,80e7 × 0,140625). Regla de cobertura l. 798 a 808 (`< 100` celdas a `RADIO_RECORTE_KM`, `dist_max_centro_km`).

Eje 2, poder (scripts mios; vara: tabla sola, noche por elevacion solar, SN, lectura A, ±120 s, Tupungatito desde 02-23; K = `origin/main` `47cdc446f`; referencia del worktree `ab1a208c…` / `d4ad8c44…`; predicado node de `frontend/index.html` de `origin/main`; control de identidad del predicado `([0,1,1,1,0],[1,0])`):
- F26 (`contar_f26_F26_salida.txt`): VIIRS 375 26 protegidas (Lascar 26), K publica 26, bajo 1 MW 158, negativos limpios 730, `sin_info` 1.708 (64 %), 48 bloques donde K yerra, NOAA-21 895 `sin_info`; VIIRS 750 30 (Lascar 29, Isluga 1), K publica 30, bajo 1 MW 25, 18 bloques, NOAA-21 889; MODIS feb+mar 32 protegidas, K pierde solo Lascar 2026-02-16 01:20 (1,04 MW); 627 volcan-dia. F26-M (`contar_f26_F26M_salida.txt`): 9 protegidas (K publica 8), 5 bajo 1 MW, 6 bloques P2 (E) mas el bloque de la protegida, 286 volcan-dia. F26-M3: 341. DM: 176. **Control positivo**: las tres pasadas de S159 salen con su etiqueta (bajo1, bajo1, protegida) y «K no publica».
- Versiones de codigo de K en F26: `3695f6758` (mayoria), `57d18ad78` 429, `c408a909e` 6, `255e97e77` 10 (suma de las tres lineas `codigo_sha`): coincide con el §2.
- Regla de signos: `evaluar_d25` blob `1dbabf65` l. 149 (`MAX_B_SIN_SUSTRATO_P2 = 4`), l. 150 (`TOPE_P2_DEN = 20`), l. 509 a 539 (bloques de suma 0 entran a B y duplican sin mover; p = k / 2^B) y l. 552 a 566: con B = 6, GANA exige 6 de 6 (1/64) o 5 y uno en cero (2/64); 5 contra 1 da 7/64 y no llega. **CONFIRMADO** el §7.
- OSF (`contar_osf_vent_salida.txt`): 615.470 filas leidas; 2.577 chilenas del 2025-02-15 al 12-31 de 10 volcanes (Tupungatito 0); codigos `Satellite` 1 y 2 = MODIS, 3 y 4 = VIIRS; pisos 0,011 / 0,176 / 5,053 MW; `Dayflag` 0 = noche del proyecto en 2.524 de 2.528 y 1 = dia en 49 de 49; K 2025 cargado: 37.811 records nocturnos; Δt = 0 s en los 494 pares; 375: 317 (273 / 28 / 14 / 2), K publica 317; 750: 17 Lascar, K publica 17; lejanas class 1 ≥ 1 MW fuera del radio: 12 + 17 + 20 = 49, todas de Chillán, 12,1 a 19,6 km, 2025-02-15 a 03-05; ambiguas class 0 ≥ 1 MW dentro: 13 (9 Lascar, 4 Puyehue) con el crater `vent` (12 con el centro). Salvo VPR2-05, el §4.2 se reproduce.
- A119: `origin/main:scripts/calidad_referencia_mirova.py` l. 18 a 47 (hitos 02-14 y 02-23 de Tupungatito; 03-01 cobertura 98,2 a 99,6 % en febrero; 04-01 A119 b en l. 27; 06-11 y 06-13 OCR; 04-09 NOAA-21 «no reconstruida»); `etiqueta_que_decide` l. 60 a 62 (tabla sola antes del 06-13). El cargador imprimio los avisos en `contar_f26_*_err.txt`.

Eje 3, reglas:
- F4 §7 en l. 209 a 241 del tag (`cita_f4_regla_l205_245.txt`), §6 l. 142 a 204 (P1, P1b, P2, P2′, M, Razón, curvas); V375-E §5.4 l. 134 a 151, §8.13 l. 503, §10 l. 703 a 716 («Cercano decide»; radiante «posterior a la lectura»); V750-A §6, §6 bis, §6 ter en `aa5583646`; `regla_m` (MEJORA / EMPEORA / NEUTRO). El tag `s172-v375e-lector-resellado` solo agrega el §11.14 (141 lineas) a `PREREGISTRO_E.md`: la regla citada en `s170` es la vigente.
- `docs/MISSION.md` (`origin/main`) l. 92 a 109 lectura A, l. 115 «por sensor y por tramo de calidad de la referencia», l. 119 a 131 regla SN (`cita_mission_l88_135.txt`).
- `leer_sombra_v375e.py` l. 85 `UMBRAL_COBERTURA = 0.10` y l. 573 (VS168-03) en el tag `s170-v375e-lector` (en `s172-…-resellado` son l. 85 y 612).

Eje 4, mismo codigo salvo las vias y PR B:
- `pipeline/profile.py` (`origin/main`, sin diff con PR B) l. 46 a 67: `extends` resuelve un nivel con `_deep_merge` donde el hijo gana clave a clave; l. 902, 909, 933 y 923 a 925: los seis flags se leen de `_t = thresholds`. Un perfil hijo con `enable_modis_codigo_mirova: false` en `thresholds:` gana al padre encendido.
- Flags leidos con `pipeline.profile` en el worktree de PR B (`flags_prb_pipeline_profile.txt`): `mirova_equivalent` MODIS via True, V375 y V750 False, MxD03 False/False/False, Test 1 False, prose True, B22 True; `sombra_codigo_mirova` las tres vias True; `guardia_k_modis` las tres False; `experimental` Test 1 True / prose False / B22 False (A117, laboratorio congelado en C0).
- PR A (`d3cd0b2ae..0a0dae344`, 48 archivos sin contar data) no toca `pipeline/`; `frontend/index.html`, `diario.html` y `mosaico.html` solo agregan `CambioDetector.notarRecords` (marca de fecha). PR B (`0a0dae344..c9525f994`, 32 archivos) toca en `pipeline/` solo comentarios de `process_modis.py` (l. 20 y 631 a 632) y los YAML (`mirova_equivalent` enciende; `_s146_ab_control`, `experimental`, `experimental_ndc_focus` declaran false); en `frontend/index.html` agrega `esAnclaHonesta` con `codigo_mirova` (posicion del marcador). **Las diez funciones que `banco_paridad` extrae para «publica» (`_havKm`, `mirovaEqVrp`, `f5CoreMagnitude`, `mirovaEqVrpCore`, `mirovaEqVrpDisplay`, `isCirrusArtifact`, `isDiffuseFieldArtifact`, `isThermalArtifact`, `isValidDetection`, `isSummitDetection`) no leen `final_hotspot_source` ni `via_codigo_mirova` ni en main ni en PR B; control positivo: `esAnclaHonesta` si** (`predicado_lee_via_*_salida.txt`).
- Consumidores del flag y la marca en PR B (`consumidores_prb_detalle.txt`): `ENABLE_MODIS_CODIGO_MIROVA` se lee solo en `pipeline/process_modis.py` l. 106 y 637 (y en `profile.py` l. 909); la marca `via_codigo_mirova` la escribe `mirova_v750_codigo.py` l. 704 (y `sin_grilla` en `process_viirs.py` l. 2285, `process_viirs_mod.py` l. 1545, `process_modis.py` l. 1767) y la leen `store.py` l. 357 y 609 (la via salta el filtro de distancia y el nucleo F5: parte del paquete, por record, igual en los dos brazos), `auto_audit_weekly.py`, `vigilancia_guardia_modis.py`, `revisar_guardia_modis.py`, `revisar_sombra.py`, `vigilancia_sombra.py` y `frontend/cambio_detector.js` (ninguno entra al retro). Los workflows `guardia-k-modis.yml` y `sombra-codigo-mirova.yml` afirman sus flags con `pipeline.profile` (A89).
- La rama `origin/s169-roi-v750` (`cd5aa300c`) agrega solo `scripts/roi_v750b_a_grillas.py` y pruebas: no toca K (`roi_v750_diffstat.txt`).
- `pipeline/profiles/sombra_codigo_mirova.yaml` (`origin/main`): tres vias en `thresholds:`, K declarado, MxD03 heredado (apagado hoy); el perfil del retro del §10.1 escribe los seis: equivalente mientras produccion no encienda MxD03.

Citas sueltas que comprobe: `leer_f4_salida.txt` @`e0bb1b150` l. 2 y 17 («posición: V (ninguno gana contra V)», razón 0,9827, P2 GANA neto −44 B 53); `v375e_lectura_salida.txt` l. 39 (0,9996); Spearman −0,867 / −0,50 / −0,814 (`_s172_chillan/auditor/INFORME.md` l. 100, 120, 140); `_s172_capacidad_nrt/INFORME.md` l. 27 y 145 (1,25); token 2026-12-07 18:03 y aviso ~11-27 (`docs/AUDIT_S160.md` l. 68); `tasks/LOOP_OBJETIVOS.md` @`4be4b2e32` l. 589 a 597 (sombra de los 34 aprobada 01:24 UTC); plan `2026-11-02-nrt-34-volcanes.md` l. 168 (Tarea 0.1), 216 a 264 (Tarea 0.2), 397 a 400 («los 34 … con los tres sensores o con ninguno»); `sustrato_mirova_modis_feb_salida.txt` (las tres de Lascar); `test_guard_perfiles_congelados_s153.py` existe; aritmetica de jobs (47 / 30 / 176) y volcan-dia (627 / 286 / 341 / 3.200 / 176 / 803 / 321); regla del tres (33 / 11,5 / 10 / 1,9 / 0,9 / 18 / 6,8 %).

§15: los 21 tratamientos declarados estan en el texto donde dicen (§0, §3.1, §3.2, §3.3, §4.2, §4.3, §5.1, §5.6, §6, §7, §8.1, §8.2, §10.2, §10.4, §12 R-8, R-11 a R-14; S-1 en §2, §4.1 y §7; S-6 declarado sin corregir). Lo que no alcanza es lo de VPR2-01 (VPR172-02 quedo a medias) y VPR2-05 (VPR172-14 metio una cifra inconsistente).

## 6. SIN DATO y FUERA DE ALCANCE

SIN DATO:
- Si V750-A se sella antes de D2; plan de la cuenta de GitHub (tope de jobs); disponibilidad de MxD03 en 2025: los tres los declara el pre-registro y no tengo forma de medirlos sin despachar nada.
- Esfuerzo de razonamiento con que corri (no legible desde adentro).
- La definicion de `Dayflag` y `Satellite` en Coppola et al. 2026: no renderice el PDF (A95); el pre-registro ya lo deja SIN VERIFICAR y yo tampoco lo verifique. Mi verificacion empirica coincide con la suya (2.524 de 2.528 y 49 de 49).
- Si el lector `leer_retro.py` existira con las piezas que el §11 pide: no existe aun en `loop/activo` (`git ls-tree` de `experiments/_s172_prereg_retro/` lista solo el pre-registro y la carpeta del primer verificador, que no abri).

FUERA DE ALCANCE (no mire, a proposito o por limite):
- El informe y la carpeta del primer verificador (`experiments/_s172_prereg_retro/verificador/`, `D:/vrp-trabajo/temporales/ver_s172_prereg_retro/`): no los abri; sus salidas (`k_en_tramos_salida.txt`, `osf_protegidas_salida.txt`, etc.) las reemplace con scripts propios.
- No corri pytest ni la bateria de ningun lector; no toque el worktree compartido (solo `git status`, limpio, y lecturas con `pipeline.profile` sin escribir bytecode).
- No medi la via (ningun brazo corrio); no lei la sombra de los 34 ni `grillas_mirova.yaml`.
- No verifique las cifras de costo por volcan-dia (2,39 min; 4,76 de Chillán) mas alla de los tiempos de los jobs fallidos del run.
- GUIA §3b (filas 7 y 12) y `docs/PROTOCOLO_AUDITORIA_PROFUNDA.md`: no abiertos.
