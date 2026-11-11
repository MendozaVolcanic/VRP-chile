# Bloque de arranque S180 (cierre de S179, 2026-11-11 09:12 UTC)

S179 fue la coordinadora y dueña única del loop, en la rama `loop/activo`. Cerró por contexto (ya se había
compactado una vez) a pedido de Nicolás («sí cierra y abre tú misma la siguiente»).

**Estado fijado con trabajo en curso.** A las 09:12 UTC el CI de la punta nueva de #974 (`6ebd35abf`, workflow
«Tests» lanzado 09:08:52 UTC) y el de main después del merge de #985 (09:07:58 UTC) seguían corriendo. También estaba
en cola una corrida del NRT (09:10 UTC). Ningún agente ni proceso local quedó vivo. El servidor de vista previa está
detenido.

Lo anterior: `tasks/BLOQUE_ARRANQUE_S179.md` (cierre de S178) queda como histórico. La bitácora completa de S179 está
en `tasks/LOOP_OBJETIVOS.md` §6 (entradas «(S179)», de la más nueva a la más vieja).

## a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| Auditoría S179 (Fable 5.2, cuatro frentes A a D, verificadores limpios) | TERMINADA | `docs/AUDIT_S179.md`; informes y scripts en `experiments/_s179_audit/`; commit `5e2c0c5cd` |
| Decisión 1 (posición «radiante» en VIIRS 375) | RESUELTA: radiante sirve | Las 5 alertas protegidas «sólo OCR» son la fuente lejana (>5 km) según las imágenes de MIROVA, por el defecto «imagen de otra pasada» del OCR. `experiments/_s179_ocr5/INFORME.md`, commit `b6db4e9d2` |
| Decisión 2 (plazo de reversión: 29 protegidas o 120 días) | DECIDIDA: «Deja el plazo» (Nicolás, 2026-11-11 06:09 UTC) | `experiments/_s179_enmienda_plazo/ENMIENDA_PLAZO.md`; commit `b0c4740e3`. MODIS cerraría el 11-19 o 11-20 con 29 protegidas, todas de Chillán |
| Chillán, octubre y noviembre, tres sensores | Exploratorio cerrado: la vía coincide con MIROVA (razón cerca de 1,00) y la colada va al SO, cerca de 1 km (punto de Nicolás -36,8673, -71,3792) | `experiments/_s179_chillan/`, commits `b89d3ad94`, `12470db9b` |
| Pérdidas por sensor, alertas diurnas, fumarolas de Guallatiri y Callaqui | Exploratorio cerrado | commit `81f71561e` |
| **#985** (el NRT queda rojo ante un error de VIIRS con su vía encendida) | **MERGEADO** con «mergea #985» | merge commit `0965a98ae`, 2026-11-11 09:07:56 UTC |
| **#974** (B1: vía «código MIROVA» en VIIRS 375) | Preparado, **todavía en BORRADOR**; main ya integrado | Punta `6ebd35abf` (rama `claude/s177-b1-v375`, worktree `D:\vrp-trabajo\worktrees\s179-b1`). CI de esa punta CORRIENDO al cierre. 96 pruebas locales pasan; con el perfil de producción `sensores_que_fallan` da MODIS y VIIRS375 |
| Comentarios de `pipeline/process_viirs.py` en B1 | HECHO con A45 («Sí, A45 comentarios») | tag `pre-s179-b1-comentarios` (main `8e2f1cab2`), commit `46facedba`; mismo número de líneas (2337) |
| Condiciones §5 de la regla de VIIRS para B1 | HECHAS | navegador (`experiments/_s179_b1/armar_sitio_b1.py`, 243 records de la vía, capturas), tiempo del NRT (`experiments/_s179_b1/tiempo_nrt.py`: sombra mediana 6,9 y 9,3 min, producción 10,0 y 9,8, techo 50), excepción §12.6 escrita, paso de `nrt.yml` (#985), aviso a consumidores pendiente del merge |
| Guardia K de VIIRS | **1 de 3 noches verdes** | run 42929475700 (2026-11-11 00:12 UTC, success). Las del 11-10 (42734558894, 42742205624) fueron falso rojo del revisor, arreglado en #977 |
| **#983** (B2: VIIRS 750 sobre B1) | Borrador, **DIRTY** (choca con main) | punta `e68819484`; nunca antes de #974 |
| #975, #981, #980, #955, #913 | Abiertos, sin tocar en S179 | `gh pr list --state open` |

## b. Decisiones que espera el dueño

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | Encender VIIRS 375 (#974) | «mergea #974» cuando se cumpla todo lo de abajo, o esperar | Mergear cuando haya: CI verde en la punta, 3 de 3 noches verdes de la guardia (cerca del 13-11), PR pasado de borrador a listo, tag defensivo nuevo sobre main, sí A45 del encendido y la frase. Método: **merge commit**, nunca squash (la regla de reversión revierte con `git revert -m 1`) |
| 2 | Decisión 5 de `docs/AUDIT_S179.md`: mecanismo de reversión | `git revert` del PR o apagar el flag | Declarar el apagado del flag como camino principal: el revert del PR B de MODIS ya choca en 6 archivos sobre main |
| 3 | Decisión 6: reescribir el plan de reemplazo de la historia (#981) antes de ejecutarlo | reescribir o ejecutar tal cual | Reescribir: encendido por fecha explícita, no por el mínimo de `processed_utc`, y conservar el nulo de las guardias |
| 4 | Decisión 7: vigilar «la vía calla y K también» | agregarlo al vigilante diario o dejarlo al audit semanal | Agregar la comparación diaria de cada protegida de MIROVA contra la vía (hoy se ve hasta 7 días tarde) |
| 5 | Decisión 8: confirmar tres decisiones sin frase registrada | #937, #972, fila 4 de VIIRS 750 | Que Nicolás las confirme o las rechace en una línea cada una |
| 6 | Cierre del plazo de MODIS (cerca del 11-19 o 11-20) | dejar la vía o revertir | Decidir con la lista de las 29 en mano y sin leer «29 de 29» como prueba general: son todas de Chillán |

## c. Lo aprendido

Va a la memoria del proyecto en `feedback_s179_lecciones.md`. Lo que es regla general del workspace se marca así.

1. **REGLA GENERAL. Un instrumento de seguridad no viaja dentro del PR que vigila.** El revisor de errores de VIIRS
   estaba dentro de B1; el `git revert -m 1` que manda la regla se lo habría llevado, y B2 no lo traía. Salió a su
   propio PR (#985). Todo lo que debe sobrevivir a la reversión de un cambio va aparte y entra antes.
2. **REGLA GENERAL. `\v`, `\t`, `\n`, `\a` dentro de un string de Python con rutas de Windows.** `"D:\vrp-trabajo"`
   escribió un tabulador vertical en la bitácora, dos veces. Rutas siempre en string crudo (`r"..."`) o con barras
   normales, y escritas desde un archivo de script, no desde un heredoc.
3. **REGLA GENERAL. Una medición de tiempos mezcla regímenes si las corridas no tienen la misma ventana.** La primera
   medición del NRT (mediana 4,0 min) juntaba corridas de la sombra con 1 a 4 días de ventana; con la ventana por
   corrida salió 6,9 y 9,3. Es A90 y A104 aplicado a tiempos. El verificador lo cazó.
4. **Auditoría a ciegas: el control ciego se esconde también del plan.** Los prompts citaban el plan, que contenía
   la línea base roja. Se nombró la base por hash y se prohibió abrir el plan y `experiments/_s179_*`. Va a
   `C:\Users\nmend\OneDrive\Escritorio\claude\GUIA_MAESTRA_AUDITORIAS.md` como propuesta (no editada en S179).
5. **Un borrador de enmienda afirmó dos cosas que no había medido** («el OCR queda fuera», «la opción A no cambia
   nada»); el verificador las refutó. Todo borrador para una decisión del dueño pasa por verificador antes de
   presentarse.
6. **Pruebas que citan números de línea fijan el largo del archivo.** Para editar comentarios de
   `pipeline/process_viirs.py` hay que conservar la cantidad de líneas o correr `scripts/remapear_citas.py`.
7. **`git archive` con `core.autocrlf=true` cambia bytes** (refuerza la lección de S163): `-c core.autocrlf=false`
   y comparar contra los blobs.

## d. Problemas abiertos e hipótesis

| Problema | Etiqueta | Detalle |
|---|---|---|
| CI de `6ebd35abf` (#974) y de main tras #985 | CONFIRMADO en curso al cierre | Leer su resultado con `gh pr view 974 --json statusCheckRollup` antes de creer que está verde |
| #974 está en borrador | CONFIRMADO | `isDraft: true`. Pasarlo a listo (`gh pr ready 974`) antes de la frase |
| #983 choca con main | CONFIRMADO | `mergeStateStatus: DIRTY`. Después de B1, rebasar o mergear main y repetir CI y verificador |
| Issues FUERA DE BANDA del auto-audit (#973, #936, #915) | CONFIRMADO abiertos, SIN REVISAR | Nadie los miró en S178 ni en S179 |
| #968 y #969 (vigilancia ciega de la guardia, 11-09) | SOSPECHA de que están envejecidos | La bitácora de S178 dice que las vigilancias salen verdes desde el 11-10; no se cerraron |
| Disco C: con 5,1 GB libres | CONFIRMADO | Parada bajo 3 GB. Hay unos 37 worktrees colgando (lista con `git worktree list`); limpiar sólo con inventario y confirmación (A38) |
| Archivos del workspace sin commitear (guía de prompting de Fable 5.2, su copia original, nota de la guía de auditorías) | SOSPECHA de que siguen así | Fuera de este repo; revisar en `C:\Users\nmend\OneDrive\Escritorio\claude\` |

## e. Lo que ya está cerrado y no hay que rehacer

- Auditoría S179 completa y verificada. No relanzarla: sus decisiones abiertas son 5 a 8.
- Posición «radiante» en VIIRS 375: las 5 alertas «sólo OCR» no son pérdidas del cráter.
- Plazo de reversión: queda como se selló. No reabrir sin pedido de Nicolás.
- Condiciones §5 de B1 (navegador, tiempo del NRT, excepción §12.6, paso de `nrt.yml`): hechas.
- #985 en main. El revisor ya sigue al flag de cada sensor, sin tocarlo al encender o revertir.
- Comentarios de `process_viirs.py` en B1, con A45.
- Chillán: la colada va al SO, y la vía coincide con MIROVA.

## g. Plan de S180 (en este orden)

1. Verificar: CI de #974 en la punta, guardia K de VIIRS (noches 2 y 3: cron 19:35 UTC, suele llegar 4 a 7 h tarde),
   issues abiertos, disco.
2. Con la guardia en 3 de 3 y CI verde: `gh pr ready 974`, pedir a Nicolás el sí A45 del encendido, tag defensivo
   `pre-s180-b1-encendido` sobre main y la frase «mergea #974»; merge commit con `--match-head-commit`. Después,
   ficha de VRP Chile en `C:\Users\nmend\OneDrive\Escritorio\claude\MAPA_WORKSPACE.md` y comprobar en GitHub Pages
   que el tablero muestra la vía en VIIRS 375 (regla de publicación).
3. #983 (B2) sobre el main nuevo: resolver el choque, CI, verificador limpio. Nunca antes de #974.
4. Revisar los issues #973, #936 y #915 y cerrar #968 y #969 si siguen envejecidos.
5. Decisiones 5 a 8 de `docs/AUDIT_S179.md` con Nicolás.
6. Hacia el 11-19: cierre del plazo de MODIS, con la lista de las 29.

## f. Prompt para la próxima sesión

```
Sesión S180 de VRP Chile (coordinadora del programa de réplica por sensor). Carpeta:
C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile, rama loop/activo. Única dueña del loop.
Objetivo de Nicolás: ver publicada pronto la vía «código MIROVA» de VIIRS en el tablero. #985 ya está en main; #974
(VIIRS 375) está preparado y espera CI, 3 noches verdes de la guardia K de VIIRS y su frase.

1. Verifica antes de creer: date -u; git fetch origin --prune; git status -sb; git rev-parse HEAD contra
   git ls-remote origin -h refs/heads/loop/activo (debe ser el commit del cierre de S179 o posterior);
   gh pr view 974 --json headRefOid,isDraft,mergeStateStatus,statusCheckRollup (punta 6ebd35abf o posterior);
   gh run list --workflow guardia-k-viirs.yml --limit 4 (¿cuántas noches verdes desde el 11-11 00:12 UTC?);
   gh pr view 983 --json mergeStateStatus; gh issue list --state open; gh pr list --state open; df -h /c /d;
   get_usage. Lista las sesiones vinculadas.
2. Lee: CLAUDE.md; tasks/BLOQUE_ARRANQUE_S180.md entero (la sección g es el plan); las entradas S179 de la
   bitácora §6 de tasks/LOOP_OBJETIVOS.md; docs/AUDIT_S179.md (decisiones 5 a 8).
3. Avísale a Nicolás de los issues abiertos y pídele las decisiones de la sección b con su recomendación.
4. Trabajo según la sección g: encendido de #974 cuando toque, B2 sobre el main nuevo, issues, decisiones.

Reglas duras: los merges a main, el encendido y toda A45 nueva son sólo de Nicolás, con la frase «mergea #N» en tu
conversación (el clasificador bloquea frases indirectas); gh pr merge --merge --match-head-commit (merge commit,
nunca squash, para que la reversión sea git revert -m 1). #983 contiene B1 y B2: nunca antes que #974. Nada en
pipeline/, data/ ni frontend/ sin tag y sí de Nicolás (A45). Sólo EARTHDATA_TOKEN (A71); ninguna llamada a NASA
desde verificadores; verificador limpio de otro modelo antes de aceptar un resultado; effort high explícito y
carpeta temporal propia; máximo 5 agentes y 2 procesos pesados locales; tope de 500 MB por agente, sin git init,
git add del árbol ni copias del árbol; parada bajo 3 GB libres en C: o D:; git add por archivo; nunca git stash;
no incluyas archivos de experiments/_s176_codex/; date -u antes de cada encabezado de bitácora; un PR sin checks no
es verde; export MSYS_NO_PATHCONV=1 en git show; rutas de Windows en Python siempre como string crudo; español de
Chile con tú y sin guiones largos ni medios; rutas absolutas completas para Nicolás.

Si la sesión no alcanza: deja la guardia leída y anotada en la bitácora, #974 con su estado al día en el cuerpo del
PR, y cierra con /cierre al 50 % del contexto.
```
