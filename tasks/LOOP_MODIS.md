# Loop de MODIS (sesión hija de S162)

Única fuente de verdad de este loop entre vueltas. Rama `claude/s162-modis-774bb0`, worktree
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-modis-774bb0`.
Coordinadora: sesión «Retomar» (`local_4152952c-6afd-433a-82b3-b07575feee3b`), la única que despacha GitHub Actions
y la única que escribe `tasks/LOOP_OBJETIVOS.md`. Programa: `docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md`
§5 (MOD-A a MOD-E). Notas compartidas: `C:\Users\nmend\AppData\Roaming\Claude\side-session-notes\local_4152952c-6afd-433a-82b3-b07575feee3b`.

## Reglas de este loop

- Sólo mi worktree y mi rama. No escribo `tasks/LOOP_OBJETIVOS.md` ni archivos de instrumento, VIIRS 750 o VIIRS 375.
- Nada en `pipeline/` sin tag defensivo y el sí de Nicolás para ese cambio (A45).
- Nunca despacho: pido a la coordinadora, con el pre-registro y los comandos exactos. Sólo `EARTHDATA_TOKEN` (A71).
- Nada de `git stash`; `git add` por archivo; verificador con contexto limpio de otro modelo antes de aceptar un
  resultado; CI con conclusión antes de dar un PR por listo.
- Parada si C: o D: bajan de 3 GB libres.
- Permiso de Nicolás (2026-10-24, reenviado por la coordinadora): puedo abrir sub-sesiones o sub-loops, cada una en su
  worktree y rama, con cola propia enlazada desde aquí, sin despachar por su cuenta; aviso a la coordinadora con nombre e
  id `local_…`. Sub-sesiones abiertas: ninguna.

## Dónde se construye MOD-B

El `pipeline/` de `main` va 708 commits adelante de `loop/activo` (11 archivos, 631 líneas), así que el arnés se
construye y se prueba sobre `main`: worktree `D:\vrp-trabajo\s162-mxd03` (en el disco D:), rama `s162-mxd03-codigo` (cortada de
`origin/main` `80b819828`, sin upstream, checkout parcial: `data/` sólo `mirova_equivalent` y `mirova_reference`).
Carpeta `experiments/_s162_mxd03/`. El tag `s162-mxd03-codigo` irá sobre esa rama (adenda del sello, punto 2). Al
terminar, la carpeta se trae también a esta rama.

## Insumos (dónde están)

Los informes de S159 no están en `loop/activo`: viven en `origin/s159-pruebas` (y `origin/s159-portes`). Copia de
lectura en el scratchpad de la sesión. `experiments/_s159/mxd03_prereg/` se trajo a esta rama desde `origin/s159-pruebas`
(`812624cc6`) para anotar el sello. Grillas del port: `D:\vrp-trabajo\temporales\s159_portes\run_39712862945\` (sólo
grillas 51 × 51 ya remuestreadas: `mir`, `tir`, `mir_b21`, `mir_geo5`, `tir_geo5`; ningún recorte nativo).

## Cola (en el orden del programa)

### MOD-B, MxD03 sobre K (D-19, tarea 1.30)
- [x] B1. (`cd3d12984`) Anotar el sello D-48 en el pre-registro v2 (texto y fecha), con las respuestas del §11 según la
  recomendación, y una adenda declarada con lo que cambia al implementar (D34 del catálogo ya está tomada por el código
  de MIROVA V750: la divergencia nueva sería D35; tag sobre un commit de disparo, no sobre `main`; censo re-medido en el
  sha que se congele).
- [x] B2. (rama `s162-mxd03-codigo`, `7413ac463`, `cfa3330d9`) Re-medir el censo (records, gránulos, ≤ 35°, etiquetas) sobre el `origin/main` que se congele y la referencia
  remota congelada (`MANIFIESTO.json`, sha256 LF).
- [x] B3. (`dcdfeaaf3`, `cfa3330d9`) Arnés `probe_mxd03_ab.py` (brazos K, K2, X, R0 a R19 en ≤ 35°, X_fondo y X_det en las que cambian), partes por
  gránulo, con prueba sintética sin HDF (pyhdf no corre en Windows).
- [x] B4. (`15c517da1`) Workflow de disparo (`"on":` entre comillas, `EARTHDATA_TOKEN` que falla vacío, `ubuntu-24.04`, 24 partes).
- [x] B5a. (`87e91adf0`) Vara VIIRS congelada ANTES del despacho (adaptar `construir_vara_viirs.py` de 1.23 al censo de la ventana).
- [x] B5. (`f10ea9b79`, `91a3055ff`) Evaluador `evaluar_mxd03.py` + `probar_evaluar_mxd03.py` (las 12 pruebas del §8, rojas antes, verdes
  después) y las 5 mutaciones con control de caída.
- [x] B6. Verificador limpio (Fable alto), dos rondas: «listo con cambios chicos» y luego «se puede despachar el humo»; 9 + 3 hallazgos, arreglados o como reglas de operación. Commit final `ffbb36248` (rama `s162-mxd03-codigo`).
- [x] B7. (2026-10-24, mensaje a la coordinadora) Pedido de despacho a la coordinadora (tag, tres tandas de 8 partes, ~47 h de runner).

- [ ] B8. Evaluar el humo cuando llegue el run id (artefactos a `D:\vrp-trabajo\temporales\s162_mxd03\humo\`, evaluador desde checkout del tag, VMX-12) y dar el OK para las tandas.
- [ ] B10. PR del veredicto de MOD-B con D35 en `docs/MIROVA_DIVERGENCES.md` y las marcas A113 en D18 y `docs/SINTOMAS.md` §3 (decisión D-48 aplicada por la coordinadora).
- [ ] B9. (t1 = run 40112510038 COMPLETA: 1.814 de 1.814, sin errores, K = data/ y K2 = K en todas; artefactos en `D:/vrp-trabajo/temporales/s162_mxd03/t1/`. t2 después del lote V375 y de MOD-C) Evaluar las tres tandas (vara con `vara_mxd03.py --evaluar`, luego `evaluar_mxd03.py --art --vara --ref`), informe y verificador limpio del resultado.

### MOD-C, negativos neg_resto del port MODIS (D-36)
- [x] C1. (`21b800259`, redactado por subagente Opus y revisado) Pre-registro del lote (300 a 400 de las 5.093 noches neg_resto), selección con semilla, objetivos, regla de
  decisión (Wilson), para el despacho combinado de la fase 1. Guardar el recorte nativo de cada pasada (lo pide MOD-E).
- [x] C2. Verificador limpio (Fable alto): se sostiene, 3 grietas arregladas (adenda 1, `5f40f604d`); entregado a la coordinadora para la fase 1. Ronda 2 CORRIENDO.

### MOD-E, bow tie (D28), ablación local
- [x] E1. Leer cómo grilla el port MODIS y qué hay en disco; decidir si la ablación se puede hacer sin red.
- [x] E2. Verificador limpio: los números se reproducen, la lectura del bow tie NO (VCD-03/04). Retirada con marca: D28 SIN DATO; la costura de barrido es SOSPECHA; E-2 con matiz (sólo bajo 1 MW, cenit con fecha). Ronda 2 CORRIENDO.
- [ ] C3. Leer el lote de MOD-C cuando la coordinadora pase el run id (disparo `ffc1abc1b`, rama `s162-negmodis-disparo`): artefactos a `C:/vrp-trabajo/temporales/s162_negmodis/run_<id>/` (en C:, no en D:, pedido de la coordinadora por disco), lectura con `07_leer_lote.py`, informe y verificador.
- [ ] E3. Ablación real con los recortes nativos de MOD-C (cuando llegue el lote), con un método de quitar duplicados sin huecos y la clasificación por costura.

### MOD-D, paquete MODIS contra K
- [x] D1. (borrador en `experiments/_s162_modis_paquete/PREREGISTRO.md`) Pre-registro: brazos K, PM (port con D33 corregido), PM sin MxD03; el déficit de Chillán (0,485) se juzga aquí.
- [x] D2. Verificador limpio: v1 tenía reglas que obligaban a decidir después de mirar; v2 las cierra (`ce71a4ab1`). Ronda 2 CORRIENDO.
- [ ] D3. Candado de MOD-D (evaluador, arnés, workflow, verificador) después de MOD-B y MOD-C.

### MOD-A (la hace la sesión del instrumento)
- [ ] A1. Usar la cita de MOD03 de Coppola 2026 p. 4 cuando la entregue (afecta §2 del pre-registro de MxD03).

### Cierre de esta etapa
- [x] Z1. Resumen para la coordinadora (notas compartidas `MODIS_avance.md` y mensaje, 2026-10-24).

## Decisiones para Nicolás (con recomendación)

1. ~~Sellar las reglas de MOD-D v2~~: **resuelta** por la coordinadora con D-48 (2026-10-24), sobre mi recomendación;
   anotada en el pre-registro. El candado sigue pendiente (D3).
2. ~~D35 y marcas A113~~: **resuelta** (D-48): van en el PR del veredicto de MOD-B, no antes (tarea B10).

## Bitácora (la más nueva arriba)

### 2026-10-24 17:30 UTC (vuelta 8): t1 completa
- t1 de MOD-B (40112510038): 9 de 9 jobs en success; 1.814 de 1.814 records en las 8 partes, 0 errores, K igual a
  `data/` en todos (nada retenido para el control 4), K2 = K, commit del tag en todas. 24 a 48 min por job: las 24
  partes van a costar del orden de 15 h de runner, no 47.
- La coordinadora reordenó por cupo: lote V375 (40116289866), luego MOD-C, luego t2.

### 2026-10-24 (vuelta 7): etapa completa
- Ronda 2 del verificador de MOD-C/D/E: MOD-C despachable tal cual; MOD-E arreglado; MOD-D v2 lista para el sello de
  reglas. VCD-15 (textos de MOD-C) y VCD-16/17 (casos borde de Chillán) aplicados (`b6edffb92`).
- Etapa de la sesión cumplida: MOD-B sellado y despachado (t1 corriendo), MOD-C y MOD-D pre-registrados y verificados,
  MOD-E con veredicto verificado (D28 SIN DATO), resumen enviado. Lección a memoria: un brazo de ablación hay que
  medirlo sobre su insumo antes de leerlo.
- Sigue: evaluar t1 a t3 de MOD-B, leer MOD-C, ablación real de D28 y candado de MOD-D.

### 2026-10-24 (vuelta 6): humo de MOD-B en verde; segundo verificador; MOD-C entregado; MOD-D v2
- Humo de MOD-B (run 40111997157, 4 gránulos, 15 records): todos los controles OK (geometría 2,581 km = S151, K = data/
  en 15 de 15, K2 = K, re-etiquetado 0 distintas, predicado, cableado, fetch por sha y main congelado en el runner).
  OK enviado a la coordinadora para t1, t2, t3. Evaluación archivada en `experiments/_s162_mxd03/humo_40111997157/`.
- Verificador de MOD-C/D/E (Fable alto): MOD-C se sostiene (3 grietas arregladas: ángulos en la prueba, controles
  oblicuos, sunglint); MOD-E: mi lectura del bow tie no se seguía de lo medido (el brazo de filas de borde dejaba huecos
  y conservaba copias; la caída de 25 % aparecía en focos vistos una vez): retirada; MOD-D: v1 con BLOQUEA sin fila,
  Chillán inalcanzable, placebo que no puede fallar, alcances sin fijar, 0,485 sin fuente (en la población es 0,635).
- MOD-C enviado a la coordinadora (blob nuevo 2d57443d). MOD-D v2 escrita. Error mío al reescribir MOD-D: puse el
  corte de Chillán en 44° cuando la pasada de K/MIROVA 0,137 tiene 35°; corregido a 30° antes del commit.

### 2026-10-24 (vuelta 5): ronda 2 del verificador y pedido de despacho de MOD-B
- Ronda 2: «se puede despachar el humo». VMX-10 (homónimo en la prueba del arnés) quedó mal en el primer intento: la
  prueba de la 1.17 vuelve a meter su carpeta; arreglado moviendo la reinserción (`ffbb36248`).
- Pedido enviado a la coordinadora: tag `s162-mxd03-tag` sobre `ffbb36248`, humo por push a `s162-mxd03-humo`, y las
  tres tandas sólo con mi OK al humo. MOD-C se manda aparte cuando entregue su verificador.

### 2026-10-24 (vuelta 4): verificador de MOD-B entregó; arreglos
- Veredicto: LISTO CON CAMBIOS CHICOS; ningún hallazgo da un CUMPLE falso. Los de más peso: el humo no tenía el
  gránulo del control 1 de geometría (habría dado INDECIDIBLE siempre y el control 1 recién se estrenaba en la tanda
  3) y el evaluador no deduplicaba pasadas (humo y tanda juntos contaban doble en P2). Además la suite no fijaba el
  camino real (2 de 11 mutaciones del verificador atrapadas) y el control de unión era tautológico.
- Arreglado todo (tabla en `experiments/_s162_mxd03/RESPUESTA_VERIFICADOR.md` de la rama `s162-mxd03-codigo`). Un
  error mío en el camino: un escape `
` dentro de un heredoc se volvió salto de línea real en el código; detectado
  al compilar, corregido.
- Pedido de despacho (borrador, sale tras la segunda ronda): tag `s162-mxd03-tag` (no `s162-mxd03-codigo`, que es el
  nombre de la rama) sobre el commit final; humo por push del tag a `s162-mxd03-humo`; si el humo da controles en verde,
  tandas `-t1`, `-t2`, `-t3`, una a la vez.

### 2026-10-24 16:05 UTC (vuelta 3): MOD-E a 3 MW, informe, segundo verificador
- Ablación sintética a 3 MW: quitar duplicados no cambia la mediana hasta 45° de barrido (S/T 1,000 a 1,005) y la
  BAJA un 25 % a 50° de barrido, 58° de cenit (0,754, n 19), con 24 a 20 detecciones de 40. Conservarlos (el port)
  inflaría respecto de MIROVA sólo en lo muy oblicuo: no explica la subida de Láscar entre 25 y 48°.
- Informe de MOD-E (`experiments/_s162_modis_bowtie/INFORME.md`); MOD-D agrega el brazo PM-sin_dup.
- Segundo verificador limpio (Fable alto) para MOD-C, MOD-D y MOD-E. El de MOD-B sigue corriendo.

### 2026-10-24 (vuelta 2): evaluador, vara, MOD-C, MOD-E paso 1 y 2, borrador de MOD-D
- B5: evaluador con las 12 pruebas del §8: 0 de 12 contra `evaluar_vacio.py`, 12 de 12 con el real, 5 de 5 mutaciones
  atrapadas cada una por su prueba. Dos defectos míos atrapados: la prueba 9 estaba mal armada (con X = 0,97 K las
  protegidas de 1,0 MW cruzaban a P1b, y eso es correcto) y, en la punta a punta, la unión población-arnés dejaba que
  el arnés pisara la etiqueta congelada (ahora manda la población y hay control de unión).
- B5a: vara VIIRS congelada antes del despacho con el instrumento de 1.23: 83 de 92 alertas con vara estricta, 65 con
  cenit ≤ 35°.
- B6 lanzado: verificador Fable alto, contexto limpio, preámbulo canónico entero.
- C1: pre-registro de MOD-C (subagente): 400 pasadas del marco de 5.055, regla Jeffreys, CONFIRMA sólo con 0 de 400,
  INDECIDIBLE con 1 a 7, REFUTA con 8 o más; K re-corrido; recortes nativos para MOD-E (~307 MB); 1,27 h de runner.
  Dato: en S159 se sortearon 38 de `neg_resto` (no 37): 36 evaluables. Falta su verificador.
- E1/E2 (MOD-E): las grillas del port en D: no traen píxeles nativos: la ablación real espera los recortes de MOD-C.
  Sin red: (1) port/MIROVA por cenit en las 89 alertas de S159: 0,964 bajo 25°, 1,052 de 25 a 40°, 1,115 de 40 a 50°;
  tendencia significativa (ρ 0,29, p 0,005) y también dentro de Láscar solo (ρ 0,295, p 0,008). (2) Ablación sintética
  con geometría de barrido MODIS: quitar duplicados no mueve la mediana en ningún ángulo (S/T = 1,00 a 1 MW), sólo la
  dispersión por pasada, y cuando la mueve la SUBE: el bow tie empujaría port/MIROVA hacia abajo, al revés de lo que se
  ve. Lectura provisional: D28 no explica la tendencia (falta 3 MW y verificador).
- Hallazgo para MOD-D: las 2 protegidas de Chillán a 58° que K y K+MxD03 no ven, el port SÍ las ve (0,837 y 1,734).
- D1: borrador de MOD-D (censo del paquete en el arnés: K, K33, PM, PM-geo5, PM-sens, placebo; P2 por signos D-45;
  Chillán con tres salidas). Falta verificador.

### 2026-10-24 (vuelta 1): sello, censo, arnés, workflow; MOD-C delegado
- B1 hecho: sello D-48 con adenda de 5 puntos en el pre-registro (`cd3d12984`).
- B2: el censo re-medido sobre `main` `80b819828` con la referencia de hoy (consolidado `47303dcd`, OCR `534003b3`,
  sha256 en `MANIFIESTO.json`) **reproduce exacto** el del pre-registro: 5.465 records, 1.232 gránulos, 2.046 con cenit
  ≤ 35° en 511, etiquetas 50/42/5.110/253/10 con K publicando 48/32/39/6/0, 222 mitades partidas, 12 `codigo_sha`, las
  4 protegidas expuestas (más 3 bajo 1 MW). Los 5.465 son versión estándar.
- B3: arnés sobre el núcleo ya verificado de 1.17/1.21/1.23 (import, sin copiar). La prueba sintética atrapó un defecto
  real mío (el reemplazo del fondo capturaba la función ya parcheada: recursión) y una aserción ciega (M2 comparaba
  contra la misma función mutada). Final: caso base OK y 4 de 4 mutaciones atrapadas por aserción.
- B4: workflow con push a ramas de disparo (`s162-mxd03-humo`, `-t1`, `-t2`, `-t3`), humo de 3 gránulos; control 4 en
  un paso propio (`recorrer_en_sha.py` + `k_en_sha.py`: worktree del commit viejo, proceso aparte).
- Hallazgo menor: la prueba sintética de 1.17 (`probar_probe_mxd03.py`) falla con K en `deteccion_cambia` (con K el
  cúmulo cambia de magnitud al cruzar el umbral dual); expectativa vieja, no la toco.
- `comparar_con_ganancia` (d′ de D-28) no está en `main`: M se informa con el intervalo de `regla_m` sobre d y d′ como
  estimación puntual (lo prevé el §8).
- MOD-C delegado a un subagente en segundo plano (carpeta `experiments/_s162_modis_negativos/` de esta rama, sin
  commits del subagente).

### 2026-10-24 (vuelta 0): arranque
- Leídos: programa (§1, §2, §5, §7, §9, §11), pre-registro MxD03 v2, informes M, PORTES y su verificador, Chillán MODIS,
  D28 y D33 del catálogo (D33 está en `main`, no en `loop/activo`).
- Hallazgos de arranque: (1) el evaluador `evaluar_mxd03.py` del §8 del pre-registro **no existe** en ninguna rama (sólo
  el de 1.17 en `_s151_mxd03_etiquetas`), ni el arnés ni el workflow: el candado hay que construirlo (B3 a B6).
  (2) La «D34» que el §11 punto 9 propone ya está usada en el catálogo (S158). (3) Las grillas del port en D: no traen
  el recorte nativo, así que la ablación del bow tie no se puede hacer sólo con ellas (E1 lo confirma o lo refuta).
- Sello: decisión D-48 de Nicolás (2026-10-24), registrada por la coordinadora en `tasks/LOOP_OBJETIVOS.md` de
  `loop/activo` (`c8423ce9a`): «sobre las decisiones mías haz lo que tú recomiendes»; la recomendación 9 del programa es
  «sellar el pre-registro v2 y correrlo; adoptarla dentro del paquete MODIS salvo que se atrase más de un mes».
- Disco al arranque: C: 37 GB, D: 8,6 GB.
