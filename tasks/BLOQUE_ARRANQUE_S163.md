# Bloque de arranque S163 (cierre de S162, sesión coordinadora «Retomar», 2026-10-24 ~12:00 UTC a 2026-10-25 ~02:20 UTC)

Escrito el 2026-10-25 ~02:20 UTC (servidor 02:10) sobre `loop/activo`. **El estado se fijó con trabajo en curso**: cinco
subagentes lanzados a las ~02:15 UTC siguen corriendo y todavía no habían empujado sus ramas (ver §a, fila «en vuelo»).
El bloque anterior (`tasks/BLOQUE_ARRANQUE_S162.md`) queda como historia. El detalle de cada paso está en
`tasks/LOOP_OBJETIVOS.md` §6 (entradas del 2026-10-24 ~12:30 UTC al 2026-10-25 ~02:15 UTC).

## a. Todo en una pantalla

| qué | estado | evidencia |
|---|---|---|
| D25 (fondo por vecinos) | **LEÍDO: DECIDE NICOLÁS; decidido NO ADOPTAR** (D-48). Veredicto confirmado bit a bit por verificador limpio | `experiments/_s157_prereg_d25/lectura_s162/` en `s159-evaluador-d25` (`ded217af4`); marca al inicio de D25 en `docs/MIROVA_DIVERGENCES.md` |
| Programa de la réplica por sensor | **ESCRITO**: de palancas sueltas al paquete del código de MIROVA por sensor; D17 pasa a pieza obligatoria | `docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md` (`b05d60527`) |
| D-48 | Nicolás: «sobre las decisiones mías haz lo que tú recomiendes». La coordinadora aplicó las recomendaciones (sellos de pre-registros incluidos), revocable | `tasks/LOOP_OBJETIVOS.md` §6, entrada ~16:30 UTC |
| Instrumento (fase 0) | **TERMINADO**: cobertura contra la referencia, alerta y protegida única, placebo y d′ comunes, MOD-A | PRs #902 a #905, CI verde, sin merge; rama `claude/s162-instrumento-021324` |
| MOD-B: MxD03 sobre K | **CUMPLE SIN DAÑO, verificado** (5.465 pasadas; 0 de 48 protegidas perdidas; MxD03 más cerca por 0,73 km) | `s162-mxd03-codigo` `afb3fcdea`, `experiments/_s162_mxd03/resultado/`; tag `s162-mxd03-tag` |
| MOD-C: negativos del port MODIS | **INDECIDIBLE, verificado** (2 de 390; Láscar 05-11 calor real, Llaima 07-24 artefacto); se resuelve en el censo de MOD-D | `claude/s162-modis-774bb0` `experiments/_s162_modis_negativos/` |
| MOD-E: bow tie D28 | **medido y verificado**: método A sin huecos; efecto sobre la magnitud SIN DATO; S-1: la sigma de escena acopla todo A/B de remuestreo | `claude/s162-modis-774bb0` `experiments/_s162_modis_bowtie/real/` |
| MOD-D: paquete MODIS | reglas **SELLADAS** (D-48) más adendas 1 y 2 informativas; **falta el candado** | `claude/s162-modis-774bb0` `experiments/_s162_modis_paquete/` |
| V750-C: ablación del oráculo | **verificado**: la interpolación lineal y la ROI callan las cumbres tibias; el fondo del código da la magnitud (0,458 contra 0,999) | `claude/s162-viirs750-f63ef4` `experiments/_s162_v750c/` |
| V750-B: ROI por volcán | **SELLADO** (tres vueltas de verificador, 13 de 13 mutaciones); **despacho no antes del 2026-11-03** | tag `s162-v750b-sellado` (`1af6c3cd8`) |
| V750-A: paquete V750 | borrador con prueba de equivalencia (roja sin módulo) y diagnóstico S-1; falta analizador y vía de proceso | `claude/s162-viirs750-f63ef4` `27973d13a` |
| V375-C: caja | **verificado**: caja C13 en el cráter; recall bajo 1 MW 0,69 → 0,95, a la par de K | `claude/s162-viirs375-c1b864` `experiments/_s162_v375/resultado_run40116289866/` |
| V375-B (+B2): silencio | **RESUELTO, verificado: SILENCIO ACOTADO BAJO K** (6 de 1.165 nuevas, 0,52 %; cota 2,48 % contra 3,85 %) | `claude/s162-viirs375-c1b864` `c0215a97d` (rama subida por la coordinadora: no estaba en el remoto) |
| Hallazgos de K en producción | cúmulos armados por la matriz del barrido (= D17, verificado; 7 a 13 de 290 publicaciones V750); hueco silencioso del 12-oct en el A/B (defecto del instrumento) | `experiments/_s162_vuelta2/` |
| **En vuelo al cerrar** | 5 subagentes (lanzados ~02:15 UTC): A61 de MxD03 → `s162-a61-mxd03`; PR del veredicto de MxD03 (borrador) → `s162-pr-veredicto-mxd03`; analizador V750-A → `s162-v750a-evaluador`; 6 protegidas SNPP de V375 → `s162-v375-protegidas-snpp`; auto-audit del lunes → scratchpad S162 `vuelta3\autoaudit_lunes` | ninguna rama en el remoto a las 02:10 UTC; comprobar con `git ls-remote` |
| Relevos sin abrir | MODIS 2 y VIIRS 750 2: briefs listos (la app no abre sesiones desde el control remoto) | `tasks/BRIEFS_SESIONES_S162.md` |
| Runs | ninguno del loop; NRT corriendo al cerrar (11 jobs, normal) | `gh run list` |
| Disco | C: 39 GB, D: 9,6 GB | `df -h` |

Sesiones hijas (todas linkeadas a la coordinadora `local_4152952c-6afd-433a-82b3-b07575feee3b`): `loop-instrumento`
(terminada), `loop-viirs375` (en pausa), `loop-modis` (cerrada, traspaso en el bloque 0 de `tasks/LOOP_MODIS.md`),
`loop-viirs750` (loop detenido; cola en `tasks/LOOP_VIIRS750.md`).

## b. Decisiones que espera el dueño

| # | pregunta | opciones | recomendación |
|---|---|---|---|
| 1 | Merges (el clasificador de permisos bloquea los merges a main de Claude) | mergear tú; o agregar una regla de permiso | **mergear #900 antes del 2026-11-02** (aviso de VIIRS sin juzgar tras el cese); después #902 a #905 (instrumento) y #901, #898 (registro). Todos con CI verde |
| 2 | Abrir los relevos MODIS 2 y VIIRS 750 2 | desde el computador, pedirlo a la coordinadora; o abrir sesión con el prompt de `tasks/BRIEFS_SESIONES_S162.md` | **abrir los dos** después de leer los resultados de los cinco subagentes |
| 3 | Adopción de MxD03 | sola ahora; o dentro del paquete MODIS | **dentro del paquete** (D-48), salvo que el paquete se atrase más de un mes; requiere A61, tag, TDD y tu sí (A45) |
| 4 | Vía de proceso «código MIROVA» en `pipeline/` | construirla detrás de flag; esperar | **construirla** (VIIRS 750 primero, V375 y MODIS la reutilizan); encenderla sólo con tu sí |
| 5 | Limpieza (Claude no borra archivos de forma permanente) | borrar; conservar | **borrar**: `C:\vrp-trabajo\temporales\s162_v375\verif_v3\` (1,8 GB), `D:\vrp-trabajo\mirova-v1` (885 MB), temporales de pytest en `D:\vrp-trabajo\temporales\`, `experiments/_s140`, `experiments/_s160_espacial/data` |
| 6 | O2 en MATLAB Online (15 min) | correrlo; no | **correrlo**: cierra la banda de 1,82× del fondo en alertas de 1 píxel; paso a paso en `experiments/_s162_v750f/PASO_A_PASO_O2.md` de `claude/s162-viirs750-f63ef4` |
| 7 | Correo a Coppola sobre la ROI por volcán | enviarlo; no | **enviarlo** (borrador en `docs/audit_s139/BORRADOR_CORREO_COPPOLA.md`, agregar los números de V750-C y V375-C) |
| 8 | #889 (cobertura del NRT con cero gránulos; toca `pipeline/fetch.py`, en conflicto) | rebase y A45; cerrar | **rebase en una sesión aparte**, con tag y tu sí |

## c. Lo aprendido

Reglas generales del workspace (memoria `feedback_s162_lecciones.md`):
- **La app no abre sesiones desde el control remoto, y un turno disparado por un agente o un despertador no puede
  abrirlas** (sólo proponer tarjetas, que desde el control remoto tampoco se muestran). Las sesiones hijas con loop
  propio no pueden abrir sesiones nuevas solas en sus vueltas. Dejar los briefs escritos en un archivo del repo.
- **Una rama de sesión hija tiene que estar en el remoto**: la de VIIRS 375 vivía sólo en el disco después de doce
  horas de trabajo. Todo brief exige push tras cada commit, y la coordinadora lo comprueba con `git ls-remote`.
- **Una regla de decisión corregida se re-verifica aunque tenga batería**: en V750-B cada una de las tres vueltas de
  verificador encontró un G3 en la regla que decide, y la propia batería del autor encontró otro.
- **Un disparo armado sobre un árbol viejo arrastra sus workflows**: cada push a una rama de disparo armada sobre
  `ca034d66e` dejó una corrida vacía del `vigilar-osf-mirova.yml` inválido de S158.

Del proyecto (rutear al `CLAUDE.md` del proyecto y al catálogo cuando se mergeen los PRs):
- **Las palancas sueltas sobre K no llevan a la paridad; el código de MIROVA actúa acoplado** (fondo y suma sobre K
  encienden de más, la compuerta sola no cambia nada, D25 es ganancia pareja); el camino es el paquete por sensor.
- **La cobertura de un A/B tiene que compararse contra la referencia de MIROVA, no sólo entre brazos** (12-oct: 44
  pasadas ausentes en todos los brazos, una protegida de 8,44 MW, invisible a cuatro controles). Arreglado en #904.
- **Los cúmulos se arman por la matriz del barrido, no por el terreno** (D17): en pasadas oblicuas K publica fragmentos
  y en cenit bajo cuenta huellas dos veces.

## d. Problemas abiertos e hipótesis

- **CONFIRMADO**: K en VIIRS 750 publica a veces un fragmento del foco sin el píxel más caliente (Chillán 2026-10-14
  06:18, Láscar 2026-05-05 06:06 cruza 1 MW); es D17 y lo subsume el paquete.
- **CONFIRMADO**: el umbral de cumbre del código de MIROVA usa la sigma de toda la grilla de 51 km (S-1); acopla todo A/B
  de remuestreo al borde de la escena. Diagnóstico obligatorio en V750-A §5 y MOD-D.
- **CONFIRMADO**: 6 protegidas de Suomi NPP sólo OCR que todos los brazos de VIIRS 375 pierden; si son del cráter lo
  decide el subagente 4 con la regla de #903.
- **SOSPECHA**: `_interp_geo` interpola el relleno −999 sin enmascararlo (subagente 1).
- **SOSPECHA**: el corte de Suomi NPP alcanza también a LANCE NRT; confirmar el 2026-11-03 (caso C-06).
- **CONFIRMADO por simulación** (subagente 5, `experiments/_s162_vuelta3/AUTOAUDIT_LUNES_26.md`, origin/main `f9e22f8d6`,
  validado reproduciendo los 10 flags de #864 con el reloj del 19-oct): el lunes 26 el auto-audit da FUERA_DE_BANDA con
  11 flags (los 10 de #864 más Puyehue VIIRS 750 0,517x, n 10) y **abre un issue NUEVO sin cerrar #864** (quedarían dos
  abiertos con los mismos flags). Con o sin #900 sale igual (#900 recién recorta en el informe del 9-nov). Casi todo lo
  que cambia es del instrumento (frontera de K en 2025-02-15 y ventana de 60 días). Bordes: MODIS recall 69,2 % con n 13
  (el flag exige 15); Chillán V750 a 0,006 de la banda; si el NRT se atrasa 2 días, sale DEGRADADO. Recomendación:
  cuando aparezca el issue del 26, cerrar #864 con un comentario que apunte al nuevo.
- **SIN DATO**: qué copia del bow tie conserva MIROVA; el efecto de D28 sobre la magnitud.

## e. Lo que ya está cerrado y no hay que rehacer

- D25 tal como está no se adopta; la lectura está verificada bit a bit. No re-leer con otro evaluador.
- V750-C, V375-B, V375-C, MOD-B, MOD-C y MOD-E tienen veredicto verificado; no re-correr sus lotes (artefactos en
  `D:\vrp-trabajo\temporales\s162_mxd03\`, `C:\vrp-trabajo\temporales\s162_negmodis\`, `C:\vrp-trabajo\temporales\s162_v375\`).
- V750-B está sellado: el 03-11 se generan objetivos y se despacha, sin tocar reglas.
- Las 11 y 35 pasadas «volcán fuera del gránulo» de los lotes de V375 son «no observadas», no fallas de cobertura.
- El hueco del NRT por la tarde es la cadencia normal (cron-job.org 04:10-12:10 UTC más el schedule de GitHub cada ~5 h).
- La regla de «filas de borde» para el bow tie está descartada (mata una protegida de Chillán).

## f. Prompt para la próxima sesión

```text
Retoma VRP Chile como sesión coordinadora (cierre de S162, 2026-10-25 ~02:20 UTC). Antes de creerle a nada:

1. cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"; git fetch origin --prune; git status -sb
   (loop/activo, en el commit de este cierre o más nuevo); hora del servidor con
   gh api -i repos/MendozaVolcanic/VRP-chile | grep -i date (A86).
2. Lee CLAUDE.md del proyecto, tasks/BLOQUE_ARRANQUE_S163.md, tasks/LOOP_OBJETIVOS.md §6 (desde la entrada del
   2026-10-24 ~12:30 UTC), docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md y
   tasks/BRIEFS_SESIONES_S162.md.
3. Comprueba los cinco subagentes que quedaron en vuelo: git ls-remote origin de s162-a61-mxd03,
   s162-pr-veredicto-mxd03, s162-v750a-evaluador y s162-v375-protegidas-snpp, y lee su INFORME.md o su PR; el quinto
   (auto-audit del lunes) quedó en el scratchpad de S162 (vuelta3\autoaudit_lunes), puede no estar accesible: si falta,
   re-simúlalo. Mira el estado de #900 a #905 y si el auto-audit del lunes 26 abrió issue.

Trabajo, en orden:
- Anota en tasks/LOOP_OBJETIVOS.md §6 lo que entregaron los subagentes (con su verificación) y corrige los briefs.
- Desde el computador, abre los relevos MODIS 2 y VIIRS 750 2 con los briefs de tasks/BRIEFS_SESIONES_S162.md, cada
  uno con su loop; esta sesión coordina y es la única que despacha GitHub Actions.
- 2026-11-03: despachar V750-B cuando loop-viirs750 entregue objetivos y sha256; consulta C-06 del cese contra CMR.
- Recordarle a Nicolás las decisiones de §b del bloque S163 (merges, limpieza, O2, correo a Coppola).

Reglas duras: nada en pipeline/, data/ ni frontend/ sin tag y el sí explícito de Nicolás (A45); sólo EARTHDATA_TOKEN
(A71); despachos uno a la vez dentro del cupo de 20 jobs (NRT usa 11); verificador limpio de otro modelo antes de
aceptar un resultado; git add por archivo; nunca git stash para probar; las ramas de las hijas tienen que estar en el
remoto; disco justo (parada bajo 3 GB); español de Chile sin voseo ni guiones largos; rutas absolutas. Si la sesión no
alcanza: commitea, anota en la bitácora qué quedó corriendo y cierra con /cierre.
```
