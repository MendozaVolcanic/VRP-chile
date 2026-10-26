# Loop de MODIS (sesión hija de S162)

Única fuente de verdad de este loop entre vueltas. Rama `claude/s162-modis-774bb0`, worktree
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s162-modis-774bb0`.
Coordinadora: sesión «Retomar» (`local_4152952c-6afd-433a-82b3-b07575feee3b`), la única que despacha GitHub Actions
y la única que escribe `tasks/LOOP_OBJETIVOS.md`. Programa: `docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md`
§5 (MOD-A a MOD-E). Notas compartidas: `C:\Users\nmend\AppData\Roaming\Claude\side-session-notes\local_4152952c-6afd-433a-82b3-b07575feee3b`.

## 0. Cierre de la sesión hija MODIS (2026-10-24, 20:55 UTC, hora del servidor)

Estado fijado sin trabajo de MODIS en vuelo (la única corrida en cola en GitHub es un lote de VIIRS 375 de otra sesión).
Ramas verificadas contra el remoto: `claude/s162-modis-774bb0` y `s162-mxd03-codigo` (`afb3fcdea`). Tags en el remoto:
`s162-mxd03-tag` (sobre `ffbb36248`) y `s162-base-portes` (`0e18e1053`). Sin commitear a propósito: las copias de
trabajo de los verificadores (`experiments/_s162_modis_verif_cde/arbol/` y `copias/` en esta rama;
`experiments/_s162_mxd03/resultado/verificador/copias/` en la de D:), que son copias de código y artefactos.

### a. Todo en una pantalla

| pieza | estado | evidencia |
|---|---|---|
| MOD-B, MxD03 sobre K | **TERMINADO: CUMPLE SIN DAÑO, verificado** (P1 sin pérdida; P2 ≤ 35° empate, ΔX −1 con ruido 4; vara VIIRS MXD03 MAS CERCA; M neutro). 5.465 de 5.465 pasadas | rama `s162-mxd03-codigo` `afb3fcdea`, `experiments/_s162_mxd03/resultado/INFORME.md` y `verificador/INFORME_VERIFICADOR.md`; runs 40111997157 (humo), 40112510038, 40122029477, 40126381034 |
| MOD-B, adopción | **A MEDIAS**: falta el PR del veredicto (D35, A113, BEYOND §12, cita de MOD-A), la auditoría A61 de 48 protegidas y los seguimientos; después tag, TDD del flag y el sí de Nicolás | cola B10, B11, B12 |
| MOD-C, negativos `neg_resto` del port | **TERMINADO: INDECIDIBLE, verificado** (el port publica en 2 de 390; ΔE −18,1 [−43,8; +40,1]). Diagnóstico de las dos: Láscar 05-11 calor real, Llaima 07-24 artefacto de gradiente a 63° | `experiments/_s162_modis_negativos/INFORME.md`, `verificador_resultado/`, `diagnostico/`; run 40120713181 |
| MOD-E, bow tie (D28) | **TERMINADO**: sintético retirado; ablación real verificada (método A sin huecos deja las 11 protegidas intactas; regla de filas de borde mataría una; efecto no confinado al foco; signo de la magnitud SIN DATO) | `experiments/_s162_modis_bowtie/INFORME.md` (marca) y `real/INFORME.md` (marca) |
| MOD-D, paquete MODIS contra K | **A MEDIAS**: pre-registro v2 con reglas SELLADAS (D-48) y adendas 1 y 2 informativas; falta el candado (evaluador, arnés, workflow, verificador) | `experiments/_s162_modis_paquete/PREREGISTRO.md`; cola D3 |
| MOD-A, cita de MOD03 | entregada por la sesión del instrumento en el PR #902 (abierto); falta incorporarla al §2 del pre-registro de MxD03 | PR #902, rama `instrumento/mod-a-cita` |

### b. Decisiones que espera el dueño

| # | pregunta | opciones | recomendación |
|---|---|---|---|
| 1 | ¿Cómo entra MxD03 a producción? | sola, como flag propio ahora; o dentro del paquete MODIS (MOD-D) | **dentro del paquete**, salvo que el paquete se atrase más de un mes (después del 2026-11-24); en los dos casos con tag, TDD que reproduzca X, auditoría A61 y su sí (A45). La coordinadora la aplicó con D-48 |
| 2 | ¿Resolver el «gana contra K» de MODIS con otro lote? | otro lote de negativos; o el censo de MOD-D | **el censo de MOD-D** (ya decidido por la coordinadora con D-48) |
| 3 | ¿Mergear el PR #902 (MOD-A)? | mergear; esperar | **mergear** con CI verde: refuerza el respaldo bibliográfico de MxD03 y de D17 |

### c. Lo aprendido

- **Un brazo de ablación hay que medirlo sobre su insumo antes de leerlo** (regla general del workspace, ya en la memoria:
  `feedback_s162_brazo_que_no_hace_lo_que_dice.md`). El brazo «sin duplicados» del sintético abría huecos y la lectura cayó.
- **Un control que siempre da OK no es un control** (regla general): «vara_cruda» del evaluador de MxD03 era un registro y
  se contó como control; el verificador lo marcó. Contar sólo lo que puede fallar.
- **Una vara que da lo mismo con la referencia de otra noche mide otra cosa** (regla general): la vara VIIRS de MxD03 mide
  cercanía al cráter de Láscar, no al calor de esa noche. Correr el placebo de la referencia antes de leer una vara.
- **Una afirmación de «se ejercitó» exige el registro que lo muestre** (regla general): escribí que el humo ejercitaba el
  control 4 y nunca se ejecutó.
- **Heredoc con escapes** (regla general, ya conocida de S144): barras invertidas dentro de un heredoc pasado a Python se
  volvieron caracteres reales y rompieron código y rutas cuatro veces en esta sesión, y dos heredocs con comillas
  mezcladas no llegaron a correr. Escribir el script con la herramienta de archivos y comprobar con `py_compile` y
  `grep` antes de commitear.
- Propio del proyecto: el umbral de cumbre del oráculo usa la sigma de toda la grilla de 51 km (S-1 del verificador de
  E3): todo A/B de remuestreo (D17, D28) queda acoplado al borde de la escena.

### d. Problemas abiertos e hipótesis

- **CONFIRMADO**: con MxD03 las 48 protegidas con cúmulo quedan más cerca del cráter (mediana 1,46 km); en el borde del
  barrido `_interp_geo` corre el píxel 10 a 16 km (15 records, cenit 63 a 75°); en 36 records de 8 gránulos X pierde
  píxeles sin geolocalización MxD03 que K conserva; el control del módulo de R acepta valores absurdos con relleno (2
  gránulos).
- **CONFIRMADO**: K/MIROVA de Chillán en la población congelada es 0,635 (n 7), de 0,64-0,85 bajo 30° de cenit a
  0,14-0,21 de 35 a 51°; el port de S159 detecta las dos protegidas de Chillán a 58° que K no ve.
- **SOSPECHA**: `_interp_geo` interpola el relleno −999 sin enmascararlo.
- **SOSPECHA**: la publicación del port en Llaima 2026-07-24 01:05 es un desfase entre bandas sobre el gradiente a 63°.
- **SOSPECHA**: quitar duplicados del bow tie cierra las publicaciones en `neg_resto` (2 eventos, al filo, post hoc).
- **SIN DATO**: qué copia del bow tie conserva MIROVA; el efecto de D28 sobre la magnitud.

### e. Lo que ya está cerrado y no hay que rehacer

- El A/B de MxD03 sobre K (veredicto verificado). No re-correr: los artefactos están en
  `D:\vrp-trabajo\temporales\s162_mxd03\tandas\` y el resultado en la rama.
- El lote de negativos de MOD-C y su diagnóstico (no hay lote nuevo: lo cubre el censo de MOD-D).
- La regla de «filas de borde» para quitar duplicados: descartada (mata una protegida y abre huecos).
- La lectura del sintético del bow tie: retirada; no citarla.
- Las reglas de MOD-D v2: selladas; todo cambio va como adenda fechada.

### f. Prompt para la próxima sesión

```text
Sesión de MODIS de VRP Chile (continúa la sesión hija S162 de MODIS). Español de Chile con formas de tú, sin guiones
largos, rutas absolutas, explicar como geólogo.

1. Verifica antes de creer: en C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile haz git fetch origin
   --prune; compara git ls-remote de origin/claude/s162-modis-774bb0 (cola en tasks/LOOP_MODIS.md) y de
   origin/s162-mxd03-codigo (código y resultado de MxD03, worktree D:\vrp-trabajo\s162-mxd03) con lo que dice el bloque
   «0. Cierre» de tasks/LOOP_MODIS.md. Mira el estado del PR #902 (MOD-A) y si la coordinadora S162 sigue viva.
2. Lee en este orden: CLAUDE.md del proyecto (A45, A90, A104, A110, A113, A115, A119); tasks/LOOP_MODIS.md entero;
   experiments/_s162_mxd03/resultado/INFORME.md y verificador/INFORME_VERIFICADOR.md (rama s162-mxd03-codigo);
   experiments/_s162_modis_paquete/PREREGISTRO.md (reglas selladas y adendas 1 y 2).
3. Trabajo, en este orden:
   a. PR del veredicto de MOD-B, sobre origin/main: D35 en docs/MIROVA_DIVERGENCES.md (geolocalización MODIS), marcas
      A113 en D18 y en docs/SINTOMAS.md §3, la candidata Láscar 2026-05-11 07:55 en docs/BEYOND_MIROVA_EXTENSIONS.md §12,
      y la cita de MOD-A (PR #902) en el §2 del pre-registro de MxD03. Avisa a la coordinadora antes de abrirlo (docs
      compartidos). CI con conclusión antes de darlo por listo.
   b. Auditoría espacial A61 de las 48 protegidas cuyo cúmulo se mueve con MxD03 (§6 P4 del pre-registro de MxD03),
      con los artefactos ya bajados; y los seguimientos: relleno −999 en _interp_geo, los 36 records que X pierde, el
      corrimiento de 10 a 16 km en el borde del barrido, el control del módulo de R con relleno. Verificador limpio.
   c. Candado de MOD-D: evaluador con pruebas que fallen contra un vacío y mutaciones con control de caída, arnés que
      envuelva el probe de PORTES (K, K33, PM, PM-geo5, PM-sens, placebo; PM-sin_dup con el método A sólo si se agrega
      por adenda), estrato informativo de la adenda 1 (soporte independiente por publicación en negativos), workflow con
      el molde de MOD-C, verificador limpio. Recién entonces pedir el despacho a la coordinadora.
4. Reglas duras: nada en pipeline/ sin tag defensivo y el sí explícito de Nicolás para ese cambio (A45); nunca despaches
   tú, todo despacho se pide a la coordinadora; sólo EARTHDATA_TOKEN (A71); git add por archivo; nunca git stash para
   probar; verificador con contexto limpio de otro modelo antes de aceptar un resultado; parada si C: o D: bajan de 3 GB
   (D: estaba en 9,6 GB).
5. Si la sesión no alcanza: deja la cola de tasks/LOOP_MODIS.md al día y cierra con /cierre.
```

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
construye y se prueba sobre `main`: worktree `D:\vrp-trabajo\s162-mxd03` (en el disco D:), rama `s162-mxd03-codigo` (cortada de
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

- [x] B8. (humo 40111997157: controles en verde, OK dado) Evaluar el humo cuando llegue el run id (artefactos a `D:\vrp-trabajo\temporales\s162_mxd03\humo\`, evaluador desde checkout del tag, VMX-12) y dar el OK para las tandas.
- [x] B10. (hecho por subagente de la coordinadora: PR #906, borrador, CI verde; incluye X1 y A1) PR del veredicto de MOD-B con D35 en `docs/MIROVA_DIVERGENCES.md` y las marcas A113 en D18 y `docs/SINTOMAS.md` §3 (decisión D-48 aplicada por la coordinadora). Además en ese PR: la candidata Láscar 2026-05-11 en BEYOND §12 (X1).
- [x] B11. (A61 por subagente de la coordinadora, rama `s162-a61-mxd03`; verificador limpio Opus del relevo, `72f85df71`: P4 se sostiene; E4 refutada, H4 −27 a +48 %, E2 46 de 48, VA61-01 ~215 records con el cráter en el borde del gránulo) Auditoría espacial A61 de las 48 protegidas cuyo cúmulo se mueve (§6 P4), antes de cualquier adopción; y los seguimientos de la adopción: relleno −999 en `_interp_geo` (SOSPECHA), 36 records con píxeles sin MxD03 que K conserva, el corrimiento de 10 a 16 km de `_interp_geo` en el borde del barrido (15 records, cenit 63 a 75°), el control del módulo de R que acepta relleno (VRB-01).
- [ ] B12. Adopción (sólo con su sí, A45): dentro del paquete MODIS (MOD-D) salvo atraso de más de un mes; tag defensivo, flag `enable_modis_geo_mxd03` con TDD que reproduzca X record por record, FICHA SDA, marca en las tres vistas, aviso a OVDAS.
- [x] B9. **CUMPLE SIN DAÑO, verificado** (`afb3fcdea`, `experiments/_s162_mxd03/resultado/`, verificador limpio Fable): P1 sin pérdida, P2 ≤ 35° EMPATE, vara MXD03 MAS CERCA (pero mide cercanía al cráter de Láscar, no al calor de la noche: VRB-02), M neutro en la mediana con 17 de 79 alertas cambiando más de 10 %; las 48 protegidas quedan más cerca del cráter con X (1,46 km). Veredicto enviado a la coordinadora.

### MOD-C, negativos neg_resto del port MODIS (D-36)
- [x] C1. (`21b800259`, redactado por subagente Opus y revisado) Pre-registro del lote (300 a 400 de las 5.093 noches neg_resto), selección con semilla, objetivos, regla de
  decisión (Wilson), para el despacho combinado de la fase 1. Guardar el recorte nativo de cada pasada (lo pide MOD-E).
- [x] C2. Verificador limpio (Fable alto): se sostiene, 3 grietas arregladas (adenda 1, `5f40f604d`); entregado a la coordinadora para la fase 1. Ronda 2: «se puede despachar tal como está». Resultado: C3.

### MOD-E, bow tie (D28), ablación local
- [x] E1. Leer cómo grilla el port MODIS y qué hay en disco; decidir si la ablación se puede hacer sin red.
- [x] E2. Verificador limpio: los números se reproducen, la lectura del bow tie NO (VCD-03/04). Retirada con marca: D28 SIN DATO; la costura de barrido es SOSPECHA; E-2 con matiz (sólo bajo 1 MW, cenit con fecha). La ronda 2 lo aprobó.
- [x] C3. Lote de MOD-C leído (run 40120713181, artefactos en `C:/vrp-trabajo/temporales/s162_negmodis/run_40120713181/`): **INDECIDIBLE** (2 de 390, ΔE −18,1 [−43,8; +40,1]); controles en verde; informe `experiments/_s162_modis_negativos/INFORME.md`; verificado con contexto limpio (`da8a68f91`); diagnóstico de las dos publicaciones en `diagnostico/`.
- [x] E3. Ablación real del bow tie, verificada (`f49e57dd7`): método A sin huecos y 11 protegidas intactas se sostienen; la regla B mataría una protegida; el efecto no queda confinado al foco (sigma global del umbral de cumbre) y los cambios de publicación son al filo; signo de la magnitud SIN DATO. MOD-D adenda 2: PM-sin_dup con A, informativo.

### MOD-D, paquete MODIS contra K
- [x] D1. (borrador en `experiments/_s162_modis_paquete/PREREGISTRO.md`) Pre-registro: brazos K, PM (port con D33 corregido), PM sin MxD03; el déficit de Chillán (0,485) se juzga aquí.
- [x] D2. Verificador limpio: v1 tenía reglas que obligaban a decidir después de mirar; v2 las cierra (`ce71a4ab1`); ronda 2: lista para el sello; reglas SELLADAS con D-48 (`de3141b6e`).
- [ ] D3. **EN CURSO (relevo, rama `s162-modd-candado`, worktree `C:\vrp-trabajo\s162-modd`)**: arnés `probe_paquete.py` (6 de 6 mutaciones atrapadas), diagnóstico S-1, evaluador `evaluar_paquete.py` (19 de 19 pruebas; contra el vacío 19 de 19 fallan por aserción), mutaciones del evaluador, ensayo en seco sobre S159, workflow `probe-s162-modd.yml`, adenda 3 (PM-sin_dup NO se agrega). Falta: cerrar mutaciones, verificador limpio del candado, tag y pedido de despacho. Texto previo: Candado de MOD-D (evaluador, arnés, workflow, verificador), ya posible: MOD-B y MOD-C entregaron. Incluye el estrato informativo de la adenda 1 (soporte independiente por publicación en negativos, candidatas a experimental) y, si se agrega por adenda, el brazo PM-sin_dup con el método A (adenda 2). Luego pedir el despacho a la coordinadora.

- [x] F1. (relevo, `74a5f855b`) Plan con TDD del flag de MxD03 para la adopción dentro del paquete: `docs/superpowers/plans/2026-10-25-flag-mxd03-modis.md` (posición por píxel, estado «sin dato» con regla a confirmar en el censo de MOD-D, distancia de la etiqueta desde el cráter). Nada en `pipeline/` sin tag y sí de Nicolás.

### Pedidos de la coordinadora S163 (`local_8a135e90-b711-4bb9-9dec-ff02036f206b`, 2026-10-26)
- [x] O1. Paquete O2 MODIS para MATLAB (`experiments/_s163_o2_modis/`, `89479be35`): 404 escenas de 1 a 4 píxeles,
  identidad 404 de 404, md5 comprobados en el remoto. No corrido: la sesión de MathWorks expiró; queda como prueba de
  oro para cuando Nicolás vuelva a entrar.
- [x] O2. (`21de8dcd5`, verificador Sonnet y marca `38df75a02`: 191 escenas distintas, ruido de 9 % en 1 píxel, 4 píxeles extrapolado) Después del candado: vara PRELIMINAR del fondo de las 404 escenas con la regla de `fillmissing2` que reproduce
  MATLAB en 166 de 166 escenas (`experiments/_s163_o2alt/delaunay_perturbado.py`, rama `s163-o2-alternativa`
  `cd812c746`; su verificador limpio estaba en curso). Marcarla PRELIMINAR.
- [x] O3. (PR #910, CI verde, mergeado por la coordinadora) Después del candado: PR chico a main con el sello D-48 y la adenda (`cd3d12984`) de
  `experiments/_s159/mxd03_prereg/PREREGISTRO_MXD03.md` (main lo presenta como «BORRADOR v2 PARA EL SELLO»), más los
  seguimientos de #906 pendientes en main: `docs/FICHA_SDA_VRP_CHILE.md:29` y `docs/paper/sec5_methods.md:7` dicen que
  usamos MOD03; `docs/MISSION.md` no nombra a Coppola 2026. Si se toca `docs/MIROVA_DIVERGENCES.md`, tomar la
  resolución de D25 de `a907c44f3` (PR #908). Nada en `pipeline/`.

- [ ] O4. Adenda 4 de MOD-D (aprobada por la coordinadora con D-48): M informada también con la regla de
  `fillmissing2` de MATLAB, fuera de línea, con las grillas que guarda el censo; sin cambiar reglas selladas. Escribirla
  cuando entregue el verificador del candado (no cambiarle el pre-registro mientras lo lee) y verificarla.

### Perfil experimental (candidatas)
- [x] X1. (en #906) Anotar en `docs/BEYOND_MIROVA_EXTENSIONS.md` §12 la candidata Láscar 2026-05-11 07:55 (señal real del cráter que MIROVA calla en MODIS; diagnóstico de MOD-C), en el PR del veredicto de MOD-B o de MOD-D (archivo compartido: no tocarlo suelto).

### MOD-A (la hace la sesión del instrumento)
- [x] A1. (en #906) Entregada en el PR #902 (abierto): Coppola 2026 p. 4, MOD03/MYD03 con corrección de terreno como insumo, y el NRT con el mismo procedimiento (p. 3 y 6). Incorporarla al §2 del pre-registro de MxD03 en el PR del veredicto (B10).

### Cierre de esta etapa
- [x] Z1. Resumen para la coordinadora (notas compartidas `MODIS_avance.md` y mensaje, 2026-10-24).

## Decisiones para Nicolás (con recomendación)

1. ~~Sellar las reglas de MOD-D v2~~: **resuelta** por la coordinadora con D-48 (2026-10-24), sobre mi recomendación;
   anotada en el pre-registro. El candado sigue pendiente (D3).
2. ~~D35 y marcas A113~~: **resuelta** (D-48): van en el PR del veredicto de MOD-B, no antes (tarea B10).

## Bitácora (la más nueva arriba)

### 2026-10-25 (relevo MODIS 2, vuelta 1): A61 verificada, candado de MOD-D armado, plan del flag
- Verificador limpio (Opus) de la A61: P4 se sostiene; marca de correcciones al inicio del INFORME (`s162-a61-mxd03` `72f85df71`).
- Candado de MOD-D en `s162-modd-candado` (worktree `C:\vrp-trabajo\s162-modd`); detalle en D3.
- Plan del flag de MxD03 (F1). Sub-sesiones abiertas: ninguna.

### 2026-10-24 (vuelta 15): MOD-B verificado y entregado
- Verificador limpio del resultado: el CUMPLE SIN DAÑO se sostiene con código independiente. Matices anotados en el
  informe (VRB-01 a VRB-07); corrección mía: el control 4 nunca se ejercitó, ni en el humo.
- Veredicto enviado a la coordinadora con la recomendación de adoptar MxD03 dentro del paquete MODIS. Propuse cerrar
  esta sesión (larga) y hacer el PR del veredicto (D35, A113, BEYOND §12) y la auditoría A61 en una nueva.

### 2026-10-24 20:45 UTC (vuelta 14): MOD-B evaluado
- t3 (40126381034) completa: 5.465 de 5.465 en las 24 partes, 0 errores, K = data/ y K2 = K en todas.
- Evaluación conjunta (sin el humo): CUMPLE SIN DAÑO con las reglas selladas; vara VIIRS MXD03 MAS CERCA bajo 35° (0,73
  km, IC 0,49 a 1,10, Terra y Aqua del mismo signo); M neutro con ĝ 1,00. Condiciona la adopción: auditoría espacial A61
  de las 48 protegidas cuyo cúmulo se mueve. Verificador limpio del resultado lanzado (Fable alto).

### 2026-10-24 (vuelta 13): E3 verificada; t3 corriendo
- Verificador de E3: B1 a B3 confirmados (reproducción bit a bit), B4 refutado en parte (VBT-02: el efecto pasa por la
  sigma global del umbral de cumbre, no sólo por el foco duplicado; VBT-01: flips al filo). Marca en el informe; adenda
  2 informativa en MOD-D. Seguimiento S-1 enviado a la coordinadora (toca también los A/B de remuestreo de V750).
- t3 de MOD-B (40126381034) despachada por la coordinadora; watch en segundo plano.

### 2026-10-24 19:40 UTC (vuelta 12): t2 completa
- t2 de MOD-B (40122029477): 1.837 de 1.837 records en las partes 8 a 15, sin errores, K = data/ y K2 = K en todas,
  commit del tag. OK enviado a la coordinadora para t3.

### 2026-10-24 (vuelta 11): ablación real del bow tie
- E3 entregada por el subagente: con datos reales el método sin huecos no cambia las 11 protegidas y apaga las 2
  publicaciones del port en neg_resto (incluida la de Láscar, que el diagnóstico dio como calor real: a revisar en el
  verificador). La magnitud cambia sólo con el foco duplicado y su signo depende de la copia conservada. El criterio de
  costura «detector 0 o 9» no delimita la franja duplicada sobre 50°. Verificador limpio lanzado.
- Adenda 1 informativa de MOD-D escrita (`80ef5fcf2`).

### 2026-10-24 (vuelta 10): MOD-C verificado; diagnóstico de las dos publicaciones; t2 en curso
- Verificador limpio del resultado de MOD-C: INDECIDIBLE confirmado (re-corrida byte a byte; regla propia también
  INDECIDIBLE). Correcciones: VRC-01 (denominadores mezclados en la comparación con K) y VRC-05 (las dos publicaciones
  dependen de B22 y MxD03; son decisivas) (`da8a68f91`).
- La coordinadora decidió con D-48: sin lote nuevo; lo resuelve el censo de MOD-D. Pidió diagnóstico físico de las dos:
  Láscar 05-11 = calor real del cráter (VIIRS de los tres satélites y MIROVA en VIIRS esa noche; píxel aislado de 4,7 K
  a 0,20 km); Llaima 07-24 = artefacto de gradiente a 63° (nada en 10 pasadas ni en 11 noches; campo con 14,1 K de
  rango de TIR y excesos de los dos signos). `experiments/_s162_modis_negativos/diagnostico/` (`10542ae1c`).
- t2 de MOD-B (40122029477) corriendo; E3 (ablación real) corriendo en el subagente.

### 2026-10-24 (vuelta 9): MOD-C leído
- MOD-C (40120713181): 7 trozos en rojo por las 10 pasadas no evaluables previstas (8 volcán fuera del gránulo, 2
  escenas inválidas), sin errores de proceso. Veredicto pre-registrado: INDECIDIBLE (el port publica en 2 de 390
  neg_resto: Láscar 2026-05-11 07:55 y Llaima 2026-07-24 01:05, un píxel cada una). Controles en verde. Verificador
  limpio del resultado lanzado. Aviso a la coordinadora: puede lanzar t2.
- E3 (ablación real del bow tie con los 403 recortes nativos) delegada a un subagente, con la instrucción de medir la
  cobertura de cada método antes de leerlo.

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
