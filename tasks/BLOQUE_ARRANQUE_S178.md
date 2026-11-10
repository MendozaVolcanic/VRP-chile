# Bloque de arranque S178 (cierre de S177, 2026-11-10 01:25 UTC)

> **Estado fijado con trabajo en curso.** En GitHub Actions corre la guardia K de VIIRS (run 42734558894, lanzada a mano
> a las 01:16 UTC, en cola y con 4 trabajos en curso al cierre); escribe en `data/` de main con su propio bucle de
> reintentos. Hay dos sesiones de Claude abiertas en esta misma carpeta: «Prueba ciega y auditoría de VRP Chile con
> Codex» (`local_2562eac1-e657-4c7b-9250-c3f61cd27eb5`, espera a Nicolás) y «Liberar espacio borrando D:\Windows
> antiguo» (`local_30c67c69-acec-4157-b7f6-e3c5c397a95a`, trabajando al cierre). Sus archivos sin commitear en
> `experiments/_s176_codex/` son de ellas: no se incluyen en commits ajenos. Leer el estado real antes de creerle a esta tabla.
>
> El bloque anterior sigue entero en `tasks/BLOQUE_ARRANQUE_S177.md`. Se cierra porque el contexto pasó el límite.
>
> **Pedido de Nicolás para S178: empezar pronto a publicar VIIRS con la vía «código MIROVA».** Eligió «Retro primero»
> (2026-11-10 01:10 UTC): leer la retrospectiva y encender VIIRS si no pierde protegidas. La sección g es la lista de
> lo que puede avanzar en paralelo.

## a. Todo en una pantalla

| Qué | Estado | Evidencia |
|---|---|---|
| D2 (F26 y DM, vía) | VERDE, sin leer (§11) | run 42507820590 intento 2; 47 de 47; `C:/Users/nmend/vrp-temporales/s177_d2/`; vence en GitHub 2026-12-09 |
| D3 (control K) | VERDE, sin leer | run 42567518008; 30 de 30; `C:/Users/nmend/vrp-temporales/s177_d3/`; C-via 0 % en 90 de 90 líneas (nulo) |
| D4 (R25, vía, 10 volcanes) | VERDE, sin leer | run 42601379627; 177 de 177; `C:/Users/nmend/vrp-temporales/s177_d4/` (93 MB); C-via 100 % (MODIS 6.736, V375 13.361, V750 13.940); 320 de 320 días por volcán; `experiments/_s177_cmr/control_via_d4.py` |
| Lector de la retrospectiva | EXISTE en main, no se ha corrido con candado | `experiments/_s172_retro_paquete/leer_retro.py`, `armar_manifiesto.py`, `armar_montaje.py`, `tests/test_leer_retro_s172.py` |
| Guardia K de VIIRS | CORRIENDO su primera corrida | cron 19:35 UTC del 11-09 **no se disparó** (0 corridas); run 42734558894 a mano; las 3 noches cuentan desde el 11-10 |
| #970, #971, #972 | MERGEADOS | `b4b8a61a0`, `e79314dac`, `bfab7c8c0`; VPR967-02 a 06 y VPR964-01 a 03 resueltos |
| Vista preliminar de los 34 | PUBLICADA | https://mendozavolcanic.github.io/VRP-chile/preliminar_34.html; Chrome: 34 de 34, 0 en cumbre, 22 focos lejanos SIN VERIFICAR |
| Audit semanal 2026-11-09 | FUERA DE BANDA (#973) | V750 recall 73,3 % (n 15, K); V375 Chillán 0,579 y Tupungatito 0,373 (K); MODIS sin juzgar (7 noches de la vía, mínimo 15) |
| #955 síntesis S175 | BORRADOR | falta el anexo con el audit del 11-09 |
| Producción contra sombra, misma pasada, 11-03 a 11-09 | EXPLORATORIO, sin verificador | V375 K 0,485 / vía 0,993 (n 47); V750 K 0,428 / vía 1,000 (n 20); MODIS 0,998; 0 protegidas perdidas en los dos; negativos limpios V375 K 10 de 117 y vía 0, V750 K 4 de 168 y vía 0. `C:/Users/nmend/vrp-temporales/s177_cmr/magn_1109/m.py` |
| Prueba ciega de Codex | PUNTUADA: 4 de 8, bajo el umbral 5 | `experiments/_s176_codex/PUNTUACION_PRUEBA_CIEGA.md` (sin commit, de la otra sesión); Codex local armado en `D:\codex-vrp`, sin lanzar |
| **B1 (VIIRS 375) y B2 (VIIRS 750)** | **BORRADOR, CI verde, sin verificador** (escritos con el sí A45 de Nicolás del 2026-11-10, «Sí, escríbelos»; tag `pre-s178-b1-b2`) | #974 `claude/s177-b1-v375` punta `bbbe2068d`, 22 archivos; #975 `claude/s177-b2-v750` punta `9d3e63015`, 21 archivos; `pytest` y `bateria-v750a` en verde, CLEAN; suite local 2 fallas, las mismas de main (`test_guard_libro_de_pruebas_s146`). El segundo en entrar se rebasa (ficha y 8 pruebas compartidas chocan; los perfiles no). Pendiente fuera de alcance: paso de `nrt.yml` de la regla §5, comentarios «APAGADA» en `process_viirs.py` l. 18 y 761 y `process_viirs_mod.py` l. 498 (A45 propio), prueba en navegador, tiempo del NRT, vara MATLAB. Worktrees `D:/vrp-trabajo/worktrees/s177-b1` y `s177-b2` |
| `loop/activo` | `01ec1e33e`, igual al remoto | main va 178 commits adelante (casi todo datos del NRT; código: #970, #971, #972) |
| Disco | C: 11 GB, D: 7,5 GB (01:18 UTC) | 6 worktrees retirados, tag `pre-s177-worktrees-cleanup`; `D:\Windows` viejo (22,6 GB) espera el sí de Nicolás en la otra sesión |

## b. Decisiones que espera el dueño

| # | Pregunta | Opciones | Recomendación |
|---|---|---|---|
| 1 | ~~A45 para escribir B1 y B2~~ **CONTESTADA** 2026-11-10 («Sí, escríbelos»): escritos en #974 y #975 | | |
| 2 | Despachar los tramos de historia que faltan con la vía (unos 2.900 volcán-día: enero, abril a septiembre y desde el 17-oct de 2026, y Tupungatito antes del 23-feb-2026) | ahora / después del encendido | **Ahora**: el reemplazo de la historia es lo que quita el aviso de MODIS y lo que necesita VIIRS para publicar sin escalón; los artefactos de D2 vencen el 2026-12-09 |
| 3 | Quitar el primer aviso del tablero (K desde el 15 feb 2025, antes C0) | quitar / dejar | **Quitar**: hay 0 records anteriores al 2025-02-15 en los 45 archivos; describe algo que no está. Tag y sí (A45, `frontend/`) |
| 4 | Merge de #955 tras el anexo | frase | Sí |
| 5 | Sello de la regla de reversión D1 a D7 | ahora / tras recalcular cotas V375 | Tras recalcular con los casos del reproceso |
| 6 | Encender B1 (V375) y B2 (V750) | por sensor | Sí por separado cuando la lectura no pierda protegidas y la guardia tenga 3 noches; B2 con la vara MATLAB re-corrida en verde |
| 7 | Borrar `D:\Windows` viejo (22,6 GB) | sí / no | Sí: la otra sesión comprobó que Windows arranca desde C:; contestar en esa sesión |
| 8 | Codex local en `D:\codex-vrp` | lanzar / no | Sólo tras rotar el PAT; la otra sesión lo espera |
| 9 | Heredadas: fases del visualizador, protección de main, radio de cráter de los 34 (5 km), caída a K y VIGILANCIA_CIEGA, dos líneas para `CLAUDE.md` | ver bloque S177 §b | Las recomendadas ahí |

Sólo Nicolás, sin decisión: rotar `EARTHDATA_TOKEN` antes del 2026-11-27; rotar el PAT en `C:\Users\nmend\.claude\settings.json` y moverlo a variable de entorno.

## c. Lo aprendido

- **REGLA GENERAL. Un workflow nuevo con `schedule` puede no dispararse nunca: vigilar «0 corridas», no sólo los rojos.** La guardia K de VIIRS se mergeó el 11-08 y su cron del 11-09 no corrió; la vigilancia lo leyó como «ciega», esperada. Al día siguiente de un merge con cron, `gh workflow view <archivo>` debe dar «Total runs» mayor que 0. Destino: `feedback_s177_lecciones.md`.
- **REGLA GENERAL. Un aviso de interfaz que describe una frontera de datos envejece cuando la historia se reemplaza.** El aviso «antes, del detector C0» siguió en pantalla tres semanas después de que #883 dejara 0 records anteriores al 2025-02-15. Su prueba vigila la fecha de la frontera, no que exista algo al otro lado. Destino: misma memoria.
- **Proyecto.** C-via tiene su nulo en D3 (0 % en el brazo K): el control distingue y su 100 % en D4 vale como montaje.
- **Proyecto.** La vara MATLAB de VIIRS 750 ya está en main (`experiments/_s162_v750a/vara_matlab_v750a.py`, salida del 2026-11-08 «TODO COMO SE ESPERA»); el «roja con Octave» del diseño es anterior.

## d. Problemas abiertos e hipótesis

| Ítem | Etiqueta |
|---|---|
| La guardia K de VIIRS no tuvo corrida por cron el 11-09 (`gh workflow view guardia-k-viirs.yml`: Total runs 0 a las 00:58 UTC) | CONFIRMADO |
| Por qué no se disparó el cron | SIN VERIFICAR (cron de Actions atrasado u omitido; mirar el 11-10 a las 19:35 UTC) |
| Sombra de los 11 roja el 11-09 23:42 UTC: Chillán, Copahue y Llaima con «2026-11-10: sin pasada a la vez», día recién empezado | SOSPECHA: la corrida atrasada cruzó la medianoche y `scripts/revisar_sombra.py` juzgó un día sin noche todavía (3 líneas de log) |
| Primer aviso del tablero sin datos detrás | CONFIRMADO (0 records antes del 2025-02-15 en los 45 archivos de main `0ac5b898c`) |
| La vía publica 2 alertas V375 de MIROVA menos que K (49 contra 51 de 53), las dos bajo 1 MW | CONFIRMADO en el medidor exploratorio, sin verificador |
| V750 de la vía en Cordón Caulle 0,566 (n 3) | CONFIRMADO en el medidor, sin causa |
| Auto-audit verde con sólo Láscar MODIS vivo 60 días (hallazgo de Codex, sobre copia modificada) | SOSPECHA en main (no comprobado; `nrt-healthcheck.yml` podría avisar) |

## e. Lo que ya está cerrado y no hay que rehacer

- D2, D3 y D4: corridos, verdes, bajados y con C-via; no se relanzan. Las 29 pasadas sobrantes las trata el lector (`sobra_en_via`).
- VPR967-02 a 06 y VPR964-01 a 03: resueltos en #970 y #971.
- Vista preliminar de los 34 publicada; por qué los 34 no van al tablero principal: sin referencia de MIROVA.
- Prueba ciega de Codex: hecha y puntuada (4 de 8); no se repite.
- Seis worktrees de PR mergeados retirados; no volver a inventariar C: y D: completos (ver `C:/Users/nmend/vrp-temporales/s177_cmr/clasificacion.txt`).
- La pregunta «¿por qué seguimos con K?» ya está contestada con números (sección a); no rehacer el medidor salvo para extender la ventana.

## g. Lo que puede avanzar EN PARALELO para publicar VIIRS con la vía

Ruta crítica: **P1 → encendido**. Todo lo demás corre al lado. Máximo 5 agentes, cada uno con su worktree en D: (A44),
carpeta temporal propia, tope de 500 MB y sin `git init`, `git add` del árbol ni copias del árbol.

| # | Frente | Depende de | Quién | Sale con |
|---|---|---|---|---|
| **P1** | **Candado y lectura de la retrospectiva.** (1) C-montaje en DM con `armar_montaje.py`; (2) manifiesto con `armar_manifiesto.py --ref s172-retro-d2` (comprueba que el pre-registro no cambió desde `s173-prereg-retro-sellado`); (3) excepciones de C-K escritas y commiteadas **antes** de leer F26 (R-15); (4) `--caja-v750` = la ROI que eligió V750-B y `--v750a-sellado no` si V750-A no se selló antes de D2 (§10.3; comprobar); (5) `leer_retro.py --manifiesto` sobre D2, D3 y D4; (6) verificador limpio de otro modelo | nada | coordinadora (no delegar el candado) | veredicto por sensor del §8.1 |
| P2 | **B1 y B2: ESCRITOS (#974, #975), falta** verificador limpio de otro modelo sobre los dos; decidir el orden de entrada (el segundo se rebasa); los pendientes fuera de alcance de la fila de la sección a (el paso de `nrt.yml` y los comentarios de `process_viirs*.py` piden su propio A45) | nada | agente verificador (Sonnet o Fable, effort high) | informe MERGEABLE o hallazgos |
| P3 | **Guardia K de VIIRS**: 3 noches (11-10 a 11-12); confirmar que el cron del 11-10 a las 19:35 UTC dispara; si no, lanzar a mano cada día y averiguar por qué | nada | coordinadora, una mirada por día | 3 corridas verdes y cierre de #968 y #969 |
| P4 | **Tramos de historia que faltan con la vía** (unos 2.900 volcán-día) en carpeta aislada, mismo workflow `reproc-retro-paquete.yml` | decisión b2 | Actions, `max-parallel` 6 o menos, fuera de 01 a 12 UTC si se puede | artefactos listos para el reemplazo |
| P5 | **Vara MATLAB de V750**: re-correr `experiments/_s162_v750a/vara_matlab_v750a.py` sobre la punta de main | nada | agente liviano | salida verde fechada (condición de B2) |
| P6 | **Plan del reemplazo de la historia** (después del encendido): cómo aplicar D2, D4 y P4 a `data/mirova_equivalent/` como hizo #883, con tag, y comprobar que el aviso de MODIS desaparece solo | nada para escribirlo; P1 y P4 para aplicarlo | agente con worktree | plan escrito y prueba de que el aviso se apaga sin records K antes de la vía |
| P7 | **Quitar el primer aviso** (`DATOS_K_DESDE_UTC` y sus pruebas `tests/test_cambio_detector_s153.py`, `tests/test_cambio_detector_frontera_s155.py`; ficha SDA) | decisión b3 | agente con worktree | PR chico |
| P8 | **Falso rojo de la sombra** (`scripts/revisar_sombra.py` no debe juzgar el día UTC en curso sin noche cerrada); primero confirmar la causa (es SOSPECHA) | nada | agente con worktree, TDD | PR con prueba roja antes de verde |
| P9 | **Anexo de #955** con el audit del 11-09 | nada | coordinadora o agente | anexo y frase de Nicolás |
| P10 | **Recalcular las cotas de VIIRS 375** con los casos del reproceso (antes del sello D1 a D7) | P1 (los casos salen de la lectura) | después de P1 | cotas nuevas para el sello |

Orden sugerido del primer día: P1 y P3 en la coordinadora; P5, P7 (si dice sí) y P8 a agentes; P2 y P4 apenas
Nicolás conteste b1 y b2. Antes de lanzar agentes: `get_usage`, `df -h /c /d` (parada bajo 3 GB, mira `C:\pagefile.sys`).

## f. Prompt para la próxima sesión

```
Sesión S178 de VRP Chile (coordinadora del programa de réplica por sensor). Carpeta:
C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile, rama loop/activo. Única dueña del loop.
Objetivo de Nicolás: empezar pronto a publicar VIIRS con la vía «código MIROVA», leyendo antes la retrospectiva.

1. Verifica antes de creer: date -u; git fetch origin --prune; git status -sb; git rev-parse HEAD contra
   git ls-remote origin -h refs/heads/loop/activo (debe ser 01ec1e33e o posterior); gh run view 42734558894 (guardia
   K de VIIRS lanzada a mano); gh workflow view guardia-k-viirs.yml (¿corrió el cron del 11-10 19:35 UTC?);
   gh issue list --state open; df -h /c /d; get_usage. Lista las sesiones vinculadas: dos pueden seguir en esta carpeta.
2. Lee: CLAUDE.md; tasks/BLOQUE_ARRANQUE_S178.md entero (la sección g es el plan en paralelo); las entradas S177 de
   la bitácora §6 de tasks/LOOP_OBJETIVOS.md; experiments/_s172_prereg_retro/PREREGISTRO_RETRO_PAQUETE.md §5, §8.1,
   §10 y §11; docs/superpowers/specs/2026-11-08-encendido-v375e-design.md (decisiones 7 y 8).
3. Integra main en loop/activo (merge, sin rebase) para tener #970 a #972.
4. Trabajo según la sección g: P1 (candado y lectura) y P3 (guardia) tú; P5, P8 y, si Nicolás dice sí, P7 a agentes;
   P2 y P4 cuando conteste b1 y b2. Pide al empezar las decisiones b1, b2 y b3 con recomendación.
5. Al terminar P1: veredicto por sensor, verificador limpio, y si no pierde protegidas, P10 y luego pedir sello y
   encendido (decisión b6).

Reglas duras: los merges a main, el sello de la regla de reversión, la A45 de B1 y B2 (también para escribirlos) y el
encendido son sólo de Nicolás, con su frase en tu conversación; gh pr merge --match-head-commit. Nada en pipeline/,
data/ ni frontend/ sin tag y sí de Nicolás (A45). No leas D2, D3 ni D4 como evidencia antes del candado §11. Sólo
EARTHDATA_TOKEN (A71), nunca a Codex; ninguna llamada a NASA desde verificadores; verificador limpio de otro modelo
antes de aceptar un resultado y el autor comprueba al verificador; effort high explícito y carpeta temporal propia;
máximo 5 agentes y 2 procesos pesados locales; tope de 500 MB por agente, sin git init, git add del árbol ni copias
del árbol; parada bajo 3 GB libres en C: o D:; git add por archivo; nunca git stash; no incluyas archivos de
experiments/_s176_codex/ (son de otra sesión); date -u antes de cada encabezado de bitácora; un PR sin checks no es
verde; heredocs sin \v ni \t; export MSYS_NO_PATHCONV=1 en git show y rutas C:/ en git worktree add; español de
Chile con tú y sin guiones largos ni medios; rutas absolutas completas para Nicolás.

Si la sesión no alcanza (contexto sobre 50 %, dos hitos o cambio de día): commitea, anota en la bitácora y cierra con
/cierre dejando tasks/BLOQUE_ARRANQUE_S179.md.
```
