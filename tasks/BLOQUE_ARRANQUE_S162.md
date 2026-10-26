# Bloque de arranque S162 (cierre de S161, sesión dueña del loop: 2026-10-22 18:55 UTC a 2026-10-23 ~20:45 UTC)

Escrito el 2026-10-23 ~20:45 UTC (hora del servidor 20:39 al empezar) sobre `loop/activo`. **Sin trabajo en curso**:
ningún agente ni proceso propio vivo (el único python del equipo es `run_ciclo.py`, ajeno al proyecto); la rama
`s159-evaluador-d25` limpia e igual al remoto en `a7418e01d`; las cinco sesiones laterales terminaron. El bloque
anterior (`tasks/BLOQUE_ARRANQUE_S161.md`) queda como historia. El detalle de cada vuelta está en
`tasks/LOOP_OBJETIVOS.md` §6 (entradas del 2026-10-22 19:04 al 2026-10-23 20:17) y las decisiones D-45 a D-47 en su
§5 y en las notas selladas.

## a. Todo en una pantalla

| qué | estado | evidencia |
|---|---|---|
| D-45: P2 por prueba de signos por bloque | **TERMINADO Y VERIFICADO.** Quinta adenda sellada; código; rojas 31 de 31 por aserción; mutaciones **58 de 58** con las pruebas finales (control 0 fallas en 106); verdes: probar 31 de 31, suite 2.447 pasan y 1 falla del entorno (frescura del CSV de la rama); placebos (a) GANA y (b) PIERDE en todas las celdas con sustrato, (c) por noche 8/320 y 4/320 | `experiments/_s157_prereg_d25/ADENDA_SIGNOS_P2.md` (`c13cf5808`); `experiments/_s159/instrumentos/signos_p2/README.md`; rama `s159-evaluador-d25` |
| Verificador limpio de D-45 | **Fable 5.1, high: código CONFIRMADO** (enumeración y generador propios, 5 mutaciones propias atrapadas); V45-01 y V45-02 sobre el texto de la regla, ratificadas en D-47 | `experiments/_s159/instrumentos/verificador_d45/INFORME.md` (`fb053347a`) |
| D-46 y D-47 | **SELLADAS** (Nicolás, 2026-10-23) | `experiments/_s157_prereg_d25/NOTA_D46.md` (sha256 `bf226b50...4684`), `NOTA_D47.md` (`e77eda6d...c6e4`) |
| **Tag de lectura de D25** | **`s161-d25-lectura` sobre `a7418e01d`**, subido (objeto `724e43452`); `evaluar_d25.py` sha256 `93c26d62...fec2` | `git ls-remote origin refs/tags/s161-d25-lectura` |
| Veredicto de D25 | **SIN LEER** (a propósito): es lo primero de S162 | |
| #897 cese de Suomi NPP en el NRT | **MERGEADO** (squash `c3ee70ed6`) con tag `pre-s161-cese-snpp` sobre `180b61317`; CI de `main` verde | el NRT no busca Suomi NPP desde el 2026-11-03 |
| #899 vigilante de OSF de MIROVA | **MERGEADO** (`e31bf0a1d`): era un workflow inválido desde S158 (comillas dobles en `if:`), nunca corrió en `main` y mandaba un correo por cada push; guarda nueva sobre los 47 workflows | primer calendario: miércoles 2026-10-28 10:15 UTC |
| #900 auto-audit con régimen del cese | **BORRADOR, CI verde**: juzga VIIRS sólo desde el 2026-11-03 y deja lo anterior aparte | espera revisión de Nicolás antes del 2-nov |
| #901 verificador de VE-01 | **BORRADOR, CI verde**: VE-01 CONFIRMADO EN PARTE: MIROVA alertó sobre nuestro mismo píxel, a 9,4 km al E del cráter; la etiqueta de protegida viene de una distancia OCR de otra pasada. **No sostiene un cambio de radio** | rama `claude/frosty-lamport-3fef52` |
| #898 mapa interactivo y persistencia | **BORRADOR, CI verde**: el cráter es el único foco persistente en los tres volcanes; su «VE-01 CONFIRMADO» quedó sobredimensionado (ver #901) | rama `claude/gracious-merkle-6447d8` |
| Estado de #864 | informe en `experiments/_s161_estado_864/INFORME.md` (commiteado en este cierre): el auto-audit corrido hoy ya no da los números de #864 | ver §d |

## b. Decisiones que espera Nicolás

| # | pregunta | recomendación |
|---|---|---|
| 1 | #900 (auto-audit con el régimen del cese) | revisar y mergear **antes del 2026-11-02**; no toca `pipeline/`, así que no exige tag A45 |
| 2 | #901 y #898 como registro | mergear los dos como registro de experimentos (sólo `experiments/`), con la nota de que #901 corrige el «CONFIRMADO» de #898 |
| 3 | Modo estricto de cobertura ante una plataforma muda (abierto en #897) | dejarlo como nota y decidir después de medir cuántos volcán-día de MODIS dan cero gránulos hoy |
| 4 | Limpieza: 7 PRs en borrador viejos (#776, #880, #886 a #890; #888 ya superado en lo del vigilante por #899) y 15 worktrees | inventario sin borrar en una tarea aparte, después de leer D25 |
| heredadas | D-36 (ampliar el port con negativos), D-38 (alarma de plataforma callada), D-39 a D-41 y Mirova-v1#26, lo que queda de D-43, D-10 (#813), PAT en `settings.json` | las del bloque S161 §b |

## c. Lo aprendido

Reglas generales del workspace (candidatas al `CLAUDE.md` global o a la guía de auditorías):
- **Una corrida larga en el computador de Nicolás puede morir sin aviso**: se suspendió 17 h al cambiar la fuente de
  energía (pedir que no se duerma no cubre eso) y se reinició al día siguiente. Los agentes largos commitean y suben
  por tramo y sus scripts reanudan leyendo lo ya escrito; así la reinicialización costó minutos.
- **Un workflow de GitHub inválido no falla donde se mira**: deja una corrida en `failure` con 0 jobs por cada push a
  cualquier rama que lo contenga (rotulada con la ruta del archivo, no con su nombre) y su calendario nunca dispara.
  Las expresiones `if:` usan comillas simples.
- **Una prueba que fija la forma de un archivo fija también su error**: la de S158 exigía `"1"` y `"2"` con comillas
  dobles, justo lo que dejaba ciego al vigilante. Al arreglar algo, buscar las pruebas que lo congelaron.
- **Una regla sellada con umbral sobre muchas celdas tiene que decir a qué nivel se mira**: con 16 celdas de 40
  semillas, «más del 5 % en una celda» rechaza una regla correcta con probabilidad 0,67. Se fija antes de correr
  (aquí costó D-46 después de mirar el placebo).
- **A96 otra vez, ahora en un worktree disperso**: `git stash` con árbol limpio no guardó nada y `stash pop` reaplicó
  un stash de S78. Para probar «sin mi cambio», usar `git show <commit>:<archivo>` a un temporal, nunca stash.

Del proyecto:
- Una confirmación desde la miniatura PNG de MIROVA (sin TIF después del 2026-09-22) necesita verificador de otro
  modelo: el «VE-01 CONFIRMADO» del mapa resultó ser una alerta a 9,4 km del cráter con distancia OCR de otra pasada.
- El auto-audit cambió su frontera de K con el histórico reprocesado: los números de #864 (del 19-oct) ya no son los
  de hoy.

## d. Problemas abiertos e hipótesis

| problema | estado |
|---|---|
| Recall de VIIRS 750 fuera de banda (72,9 %, n = 48, ventana 2026-08-24 a 2026-10-23) | **CONFIRMADO** por el auto-audit corrido hoy en la sesión lateral (`experiments/_s161_estado_864/INFORME.md`); no medido por mí |
| Tupungatito VIIRS 375 sube de 0,27x a 0,45x con la frontera nueva; flag nuevo PCC VIIRS 750 0,52x | según la misma sesión lateral, sin verificar por mí |
| Las dos protegidas de Tupungatito de #864 no son del cráter | **CONFIRMADO** por dos caminos independientes (#901 y el verificador de #886) |
| El próximo auto-audit (lunes) abrirá un issue con la lista nueva, no con la de #864 | **SOSPECHA** |
| El corte de Suomi NPP alcanza también a LANCE NRT | **SOSPECHA**; confirmar el 3-nov (caso C-06) |
| La primera corrida por calendario del vigilante de OSF funciona | **SOSPECHA** hasta el 2026-10-28 10:15 UTC |
| `test_mirova_csv_freshness_f49` falla en ramas viejas | **CONFIRMADO**, del entorno (CSV de la rama de más de 48 h), no de D-45 |

## e. Lo que ya está cerrado y no hay que rehacer

- El evaluador de D25 en `a7418e01d` decide P2 como la quinta adenda: no se re-verifica antes de leer.
- Las 58 mutaciones, los placebos (a), (b) y (c) y las mediciones sintéticas de D-45 están corridos y verificados.
- El 5 % del placebo (c) se lee sobre todo (c) (D-46); las tres lecturas de D-47 están ratificadas.
- #897 y #899 están en `main`. VE-01 no justifica un cambio de radio (#901).

## f. Prompt para la próxima sesión

```
Retoma VRP Chile (cierre de S161, 2026-10-23 ~20:45 UTC). Antes de creerle a nada:

1. cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"; git fetch origin --prune; git status -sb
   (loop/activo, en el commit de este cierre o más nuevo); hora del servidor con
   gh api -i repos/MendozaVolcanic/VRP-chile | grep -i date (A86).
2. Lee CLAUDE.md del proyecto, después tasks/BLOQUE_ARRANQUE_S162.md, después tasks/LOOP_OBJETIVOS.md §6 (entradas
   del 2026-10-22 19:04 al 2026-10-23 20:17).
3. Comprueba: git ls-remote origin refs/tags/s161-d25-lectura (debe apuntar a a7418e01d); la rama
   s159-evaluador-d25 en a7418e01d; worktree C:\vrp-trabajo\s159-evaluador limpio; #900, #898, #901 y #864.

Trabajo, en orden:
- LEER D25. El evaluador es el del tag s161-d25-lectura (no lo cambies). Lee primero
  experiments/_s157_prereg_d25/ (PREREGISTRO.md, las cinco adendas, NOTA_D44, NOTA_D46, NOTA_D47, NOTA_ESTRATO_203)
  para saber qué decide cada prueba y cómo se combinan las ventanas. Corre el evaluador sobre V1, V2a y V2b con la
  referencia congelada por hash (congelar.py), informando al lado la tabla de latest.php sola (sin el OCR, memoria
  feedback_s159_latest_php_mas_creible) y el estrato 203. Anota la versión de numpy (D-47). Después, aparte y sin que
  entre al veredicto, el brazo del 17 al 19 de octubre (run 39756261926, rama s146-ab/39756261926). Los artefactos de
  los runs están en los runs y ramas que nombra la bitácora; búscalos en tasks/LOOP_OBJETIVOS.md antes de bajar nada.
  Reporta el veredicto a Nicolás explicándolo como geólogo, con la decisión de adopción que le corresponde (A45: nada
  en producción sin tag y su sí).
- Con el veredicto, revisar los puntos de Chillán de #864.
- #900 antes del 2026-11-02 (decisión 1). El 2026-11-03, consulta C-06 del cese contra CMR.

Reglas duras: nada en pipeline/, data/ ni frontend/ sin tag y sí de Nicolás (A45); sólo EARTHDATA_TOKEN (A71); nada
de gh run watch ni bucles de gh; disco justo (C: 35 GB, D: 8,6 GB al cierre; parada bajo 3 GB); git add por archivo;
nunca git stash para probar «sin mi cambio» (A96); esperar el CI con conclusión antes de dar un PR por listo; español de
Chile sin voseo ni guiones largos; rutas absolutas. Si la sesión no alcanza: commitea, anota en la bitácora qué quedó
corriendo y cierra con /cierre.
```
