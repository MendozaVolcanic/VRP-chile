# Verificacion con contexto limpio del PR #944 (S173 S1, filtro cirrus y la via «codigo MIROVA»)

Verificador: Claude Fable 5.1, worktree propio `C:/Users/nmend/vrp-wt/ver944` en `01318eb95` (punta de
`claude/s173-cirrus-s1`, borrador, base `main`, `mergeStateStatus: CLEAN`). Hora del servidor al empezar:
`Thu, 05 Nov 2026 04:01:14 GMT` (`gh api -i repos/MendozaVolcanic/VRP-chile`). Solo lectura del repo; todo lo
escrito esta en `C:/Users/nmend/vrp-wt/ver944/experiments/_s173_aud/ver944/`. Hallazgos en `hallazgos.csv`
(separador `;`).

## Veredicto: MERGEABLE CON CAMBIOS

La parte que importa al operador (las tres vistas) hace lo que dice, con prueba que falla con la regla de antes y
medicion reproducida exacta. Lo que no cuadra es `scripts/banco_paridad.py`: el PR dice que carga el modulo
«para que el predicado ejecutado sea el del navegador» y medido no es asi (VPR944-01, gravedad 3). No mueve
ningun numero hoy, pero deja escrito algo que no ocurre, y el banco es el predicado de la vigilancia que decide
la reversion. Hay que elegir: hacerlo efectivo (y medir) o quitarlo y documentar que el banco conserva la regla
de antes a proposito. Decide Nicolas.

Conteo por gravedad: 5: 0 · 4: 0 · 3: 1 · 2: 1 · 1: 5.

## Cobertura: archivos del diff (`gh pr diff 944 --name-only`, 16 archivos, leidos enteros)

| archivo | que cambia | leido |
|---|---|---|
| frontend/cambio_detector.js | `esViaCodigoMirova(r)` (`r.via_codigo_mirova === true`), exportado; `primeraViaModis` lo usa | si |
| frontend/index.html, mosaico.html, diario.html | `isCirrusArtifact` e `isDiffuseFieldArtifact` devuelven false si `CambioDetector.esViaCodigoMirova(r)`; misma linea, hunks sin corrimiento | si |
| scripts/banco_paridad.py | el runner node hace `require` de cambio_detector.js | si |
| tests/test_filtro_cirrus_no_oculta_via_s173.py | guard: 5 casos x 3 vistas | si |
| experiments/_s173_cirrus_s1/ (10 archivos) | instrumento, salidas antes/despues, suite, navegador, via_tmax, aviso A119 | si |

## Consumidores del predicado y de la marca (grep sobre frontend/, scripts/, tests/, experiments/, pipeline/)

- Vistas vivas: `index.html` (isThermalArtifact en l. 1425, 1681, 1842, 2432, 3669; artifactKind l. 3875),
  `mosaico.html` (l. 399), `diario.html` (l. 439). Las tres pasan por `isCirrusArtifact` /
  `isDiffuseFieldArtifact`, y las tres cargan `cambio_detector.js` antes (l. 12, 24, 10). CUBIERTAS.
  `comparacion.html` y `experimental/*.html` no usan el predicado (grep: 0). No hay copia en linea del criterio
  fuera de las dos funciones (grep `273.15|278.15` en las tres vistas: solo l. 1338/1358, 364/376, 379/391 y
  dos conversiones a grados Celsius).
- `scripts/banco_paridad.py` (runner node): tocado, pero INERTE (VPR944-01). Sus consumidores
  (`auto_audit_weekly.py:225`, `clasificar_referencia.py:51`, `vigilancia_guardia_modis.py:372,376`,
  `vigilancia_sombra.py:444,446`) pasan por `cargar_nuestros`, que recorta con `CAMPOS_JS` sin la marca.
- Runners node de experimentos sellados (`_s155_audit/frente_2/*.js`, `_s158_audit_r2/m2`, `_s160_audit/f0b`,
  `_s139_audit/eje2`, `_s153_fk_v2/r3`, `_s156_autoaudit`): no cargan el modulo, siguen con la regla de antes
  (VPR944-03, por diseno).

## Las preguntas del encargo

1. **¿La marca que lee `esViaCodigoMirova` es la que escribe el pipeline?** Si. `pipeline/mirova_v750_codigo.py:704`
   escribe `"via_codigo_mirova": True` en el record de la via (familias V750, V375 y MODIS); `process_modis.py:1767`
   escribe la clave solo con texto (`sin_grilla` l. 643, `sin_mxd03` l. 645, `geo_distinta` l. 650) cuando la via no
   corre, y en el camino de la via devuelve directo el record de `calcular_vrp_granulo` (l. 652-662).
   `process_viirs.py:2285` y `process_viirs_mod.py:1545` escriben solo `"sin_grilla"`. `store.py:357` lee
   `is True`, igual que el modulo.
2. **¿Puede un record de K llevar `True`?** Por codigo no: el unico sitio que escribe `True` es el constructor del
   record de la via, y `store.append_record` reemplaza el record entero en el upgrade NRT a estandar (l. 695-704),
   no mezcla campos. En los datos (`data/mirova_equivalent/`, 76.398 records): 85 con `True`, los 85 MODIS, los
   85 con `diag_codigo_mirova` (81 sin deteccion, 4 con `final_hotspot_source == "codigo_mirova"`); 0 records
   con la clave en texto; 0 records de K con rastro de la via. Flags del perfil: solo `enable_modis_codigo_mirova:
   true` (`pipeline/profiles/mirova_equivalent.yaml:38`).
3. **¿Se reproduce la medicion?** Si, identica. Copia del instrumento que solo cambia `ROOT` (`medir_ocultos_copia.py`,
   `diff --strip-trailing-cr` = IDENTICA salvo esa linea), frontend de antes extraido del tag
   `pre-s173-cirrus-s1` (anotado, apunta a `58edb9788`, ancestro del PR). `medir_ocultos_reproduccion.out`:
   antes y despues coinciden linea a linea con `medir_ocultos_antes.out` y `_despues.out` del PR: 85 records de
   la via (2026-11-02 01:15 a 2026-11-05 01:40), 0 con `t_max < 273,15`, 3 sobre 10 MW, 0 ocultos; 6 de K
   ocultos en las 3 vistas antes y despues (Guallatiri, Lonquimay, MochoChoshuenco, Osorno, Putana, SanJose,
   abril de 2026, sin cenit, sin fila de MIROVA); control X2 `via_cirrus` 1 antes y 0 despues. Conteo
   independiente por volcan: 11 Tier A, 7 a 9 por volcan, Chillan 8 (coincide con `verificacion_navegador.txt`).
4. **¿La prueba nueva falla con la regla de antes y puede fallar?** Si a las dos. Sobre el PR: 3 passed. Copia
   de la prueba con `ROOT` por variable de entorno contra el frontend del tag: 3 failed, en la asercion de la via
   (`[1, 0]`), con los controles de K en verde. Contra un mutante del frontend nuevo con la exencion quitada:
   3 failed igual. El `require` del modulo no esta en try: si falta, node cae y la prueba no pasa en verde.
5. **¿El cambio del banco altera algun numero sellado?** No puede: la marca no llega a node (VPR944-01,
   `banco_inerte.py`: record completo `[1, 1, 0, 11.442, 1]`, record recortado por `CAMPOS_JS`
   `[1, 1, 1, 11.442, 0]`). Por eso mismo tampoco hace lo que el PR dice que hace.

## Suite completa

`python -m pytest tests/ -q -p no:cacheprovider` en el worktree `ver944` (arbol quieto: nadie edita ese
checkout; `git status --porcelain` solo muestra `experiments/_s173_aud/`): **3202 passed, 32 skipped, 2 xfailed,
84 warnings en 807 s**, exit 0 (`suite_ver944.out`). Mismos conteos que el PR (`suite_completa.out`) y que el
check `pytest` de GitHub (pass, 9m14s). Nota honesta: el bucle que esperaba al `pytest` ajeno (PID 28500, de
otra sesion y otro worktree) salio antes de tiempo (el `tasklist /FI` no filtro) y la suite corrio en paralelo
con ese proceso; es contencion de CPU, no un arbol editado, asi que A112 no se viola.

## Esfuerzo

Alto: 16 archivos del diff leidos enteros, trazado de la marca en 5 archivos de `pipeline/`, grep de
consumidores en 5 arboles, reproduccion completa del instrumento (2 corridas sobre 76.398 records x 3 vistas,
referencia remota de MIROVA descargada), prueba corrida en 3 configuraciones (PR, tag, mutante), medicion
propia de la inercia del banco, suite completa.
