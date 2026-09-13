# Bloque de arranque S139

> Cierre de S138 (2026-09-13, 11:41 a 17:10 UTC hora del servidor). Rama `main` en `1013d9e17`,
> verificado igual al remoto. Suite **1325 passed**, 4 skipped, 2 xfailed en los tres PRs. Ningún agente
> vivo; sólo el CI de `main` post-merge en curso (no escribe archivos). Los commits del cron NRT seguirán
> aterrizando sobre `data/`; no invalidan nada de esto. Los 4 stashes de S72 a S78 siguen intactos.

## a. Todo en una pantalla

| qué | estado | evidencia |
|---|---|---|
| **Auditoría integral S138**: 6 ejes en paralelo (Fable, read-only) + verificador limpio (Opus) | **terminada y mergeada** | `docs/AUDIT_S138.md`, `docs/audit_s138/EJE_1..6_*.md`, `VERIFICADOR.md`, scripts en `experiments/_s138_audit/`; PR #638 |
| Regla de salida A51: **6 contradicciones entre fuentes** (> 3) | **el frente D21/D22 queda PAUSADO** hasta consolidar | AUDIT_S138 §8 (C1 a C6) |
| Consolidación de las 6 contradicciones en su fuente + guard de la conectiva endurecido | **mergeada** | PR #639: `CLAUDE.md` (GAP #A, A82, A66/A67, A92, A95), D11 en el catálogo, bloque S137 §e.5, `tests/test_conectiva_tests23_s136.py`; barrido A92 vuelve a 0 |
| Catálogo: **D23 a D29** nuevas y **D22 corregida** en su atribución | **mergeada** | PR #640, `docs/MIROVA_DIVERGENCES.md` |
| **El fondo del anillo (D25), no la compuerta (D22), es lo que deja el cráter en 0,0 MW**; el segundo pase (sin activos, sin compuerta) rescata el píxel | verificado con las salidas commiteadas de la batería y con el código, sin reprocesar | AUDIT_S138 resumen 1; verificador §3.b; `detection_context.py:803` (firma sin BT) |
| En **noches de volcán** las 33 noches-sensor perdidas de VIIRS750 están cubiertas las 33; MODIS pierde 2 de 67; VIIRS375 1 de 6 | medido | `experiments/_s138_audit/verificador/cobertura_cruzada.py` |
| La batería del Apéndice A: con el predicado del dashboard producción da **2/6 y 2/3**, no 6/6 y 0/3; no mira posición ni pasada del autor | medido por dos vías independientes | eje 3 H1, eje 5 H1-H3, verificador §3.c (`predicado_operador.py`) |
| 76 afirmaciones de cierre: 52 vigentes, 11 condicionadas, 5 falsas, 8 no verificables | medido | eje 1 |
| PyMuPDF tampoco cura los operadores del PDF (capa de texto: `,20.93` por `< -0.93`, p. 21); sólo renderizar | verificado por mí y por el verificador | A95 corregida en `CLAUDE.md` |
| NRT al 43 % de cadencia desde el 30 de agosto (73 de 168 en 14 días, 0 rojas); job de PP verde sin descargar por el cortacircuitos A64 | medido | eje 6 §2; `experiments/_s138_audit/eje6/cadencia_nrt.py` |
| Pre-registro del A/B Tier A de D21/D22 (5 brazos, noche por volcán, pérdida cero) | **escrito, en espera** | eje 5 §4; con dos correcciones pendientes del verificador (A2 a 10,1 km rumbo 84; partición focal/nevado = S131) |
| Probe por etapa de VIIRS para el costo directo de la compuerta | **escrito, NO disparado** | `experiments/_s138_audit/eje4/probe_compuerta_viirs.py` + yml; sólo tiene sentido si la decisión S138-B lo pide |
| Memoria del agente | actualizada | `project_s138_estado.md`, `feedback_s138_atribucion_paso_siguiente.md`, `MEMORY.md` (138 líneas) |
| `MAPA_WORKSPACE.md` | sin cambios: no hubo proyecto nuevo, credencial ni pipeline que dejara de producir | recordatorio del hook atendido |
| Nada a medias, nada en rama sin mergear | verificado | `git status` limpio; ramas `s138-*` borradas tras squash |

## b. Decisiones que espera Nicolás

Las 7 nuevas de `docs/AUDIT_S138.md` §D, más las 12 distintas heredadas (tabla única en
`docs/audit_s138/EJE_6_decisiones_operacion_higiene.md` §1, que es la que manda desde ahora).

| # | pregunta | opciones | mi recomendación |
|---|---|---|---|
| S138-B | Con la atribución corregida, ¿la decisión 1 de S138 (flags apagados en `pipeline/`) se reformula? | (a) flags para el **fondo de vecinos** (D25) y el **segundo pase condicionado** (D19/D2), no para la compuerta sola; (b) mantener la formulación de S137 | **(a)**. Un brazo que quite sólo la compuerta no devuelve ninguna alerta. Toca `process_*.py` y `detection_context.py`: A45, tag y tu confirmación |
| S138-C | El A/B de D22 y del fondo, ¿en los 3 sensores o MODIS primero? | (a) los 3 (D21 sólo MODIS); (b) MODIS primero | **(a)**: el mecanismo vive en VIIRS y el holdout MODIS jun-ago 2026 no tiene nevados (15 noches, todas Láscar) |
| S138-D | Unidad de recall del A/B | (a) noche de volcán, cualquier sensor; (b) noche-sensor | **(a)** (A94, verificador P1); la magnitud se reporta aparte |
| S138-E | Cortacircuitos de A64 en `pipeline/fetch.py`: ¿reintento por plataforma antes de declarar caído al host? | (a) sí, con tag A45; (b) dejar | **(a)**: hoy un job verde puede no producir nada (PP perdió la noche del 13) |
| S138-F | Limpieza de git: 188 ramas borrables, 4 stashes, gc | (a) con tag `pre-s138-git-cleanup` + inventario de shas (A38); (b) dejar | **(a)** en sesión aparte; no borrar las 4 ramas con trabajo real ni `s124-brazoC` |
| S138-G | Partición focal/nevado oficial | (a) la de S131 (`scripts/build_c2ab_windows.py:41-42`); (b) otra | **(a)** y marcar históricas las otras tres (S114, `_s136`, `_s135`) |
| S138-H | Frontend P5: `isValidDetection` (vrp > 0 **o** Test 1) contra `mirovaEqVrp` (pc.vrp): un record con cúmulo en 0,0 y Test 1 cuenta como detección summit y se grafica en cero | (a) alinear `isValidDetection` con `mirovaEqVrp` en las 3 vistas + guard G8; (b) dejar | **(a)**: es la familia A46 en el display; 195 records en Tupungatito V750 |

S138-A (consolidar) ya se ejecutó en esta sesión. Las decisiones 2 a 5 del bloque S138 siguen abiertas
tal como estaban (S138-2 conectiva, S138-3 evaluación de A2, S138-4 keep_peak, S138-5 Isluga).

## c. Lo aprendido

**Regla del proyecto, propuesta como A97** (va a `CLAUDE.md` cuando Nicolás la apruebe; hoy vive en
memoria `feedback_s138_atribucion_paso_siguiente.md`): *una atribución de mecanismo se decide
simulando el paso siguiente del pipeline, y "publicamos" se mide con el predicado literal del
operador.* S137 culpó a la compuerta con un probe que envolvía sólo el primer pase; el segundo pase
rescataba el píxel y las salidas commiteadas de la batería ya lo decían. Y la batería declaraba 6/6
con "cúmulo a menos de 5 km con VRP > 0" mientras el dashboard exige `summit`: 2/6.

**Regla general del workspace (corrige A95 y el protocolo de auditoría):** la capa de texto de un
PDF, sea por `.txt` o por PyMuPDF, corrompe los operadores matemáticos. Lo que decide una fórmula se
lee **renderizando la página** (`page.get_pixmap(dpi=200)`) y mirándola. Verificado en la p. 21 de
Coppola 2016a. Va a `GUIA_MAESTRA_AUDITORIAS.md` §7 (trampas de medición) en la próxima revisión.

**Regla general del workspace (unidades, refuerza A90/A93/A94):** un conteo de pérdidas por
noche-sensor no es una pérdida para el operador si otra pasada de la misma noche publica. Tres ejes
midieron en la unidad equivocada y el verificador limpio lo corrigió: VIIRS750 33 a 0.

**Método que rindió, para la guía maestra §5:** el verificador con contexto limpio aportó 8 hallazgos
propios y corrigió 6 de 25, dos de ellos decisivos (unidad y atribución). Y darle al eje 3 sólo
títulos y scripts, sin los documentos de resultados, hizo que encontrara el predicado equivocado de la
batería que S136 y S137 no vieron.

**Trampas de esta sesión:** (1) el plan citaba un script en `_s137/` que vive en `_s136/`; (2) el
preámbulo canónico trae 7 guiones largos y una ruta vieja (`_s134_audit/`): conviene parametrizar la
ruta y limpiar los guiones (fuera del bloque copiable no importa, dentro sí); (3) un script de
auditoría de S133 modifica un archivo trackeado al correr (P7): dos agentes tuvieron que restaurarlo;
(4) OneDrive bloquea escrituras transitoriamente: un script Python que escribe varios archivos del
repo seguidos puede caer con `OSError 22`; el `Edit` tool o un reintento lo resuelven; (5) el eje 4
inventó una partición focal/nevado ("intermedio") que no existe en el repo y su conclusión numérica
cambió de signo con la de S131 (A48 otra vez: los subagentes son volumen, no fuente de verdad).

**Sobre el modelo.** Los seis censos corrieron en Fable 5.1 (17 a 25 min, 260 k a 485 k tokens cada
uno) y el verificador en Opus (22 min). La combinación funcionó; repetirla.

## d. Problemas abiertos e hipótesis

### CONFIRMADO (verificado con herramienta en esta sesión)

- El segundo pase no recibe temperatura de brillo (`second_pass_adjacent`, `detection_context.py:803`)
  y corre sin activos (`ENABLE_SECOND_PASS_CONDITIONED = False`); en la batería, B22 sin compuerta deja
  a A6 NO CONFORME y B22 sin compuerta con fondo local lo hace CONFORME.
- Con el predicado `distance_class == summit` (el del dashboard), el run de producción de la batería
  da 2/6 positivos y 2/3 negativos; 19 de las 22 pasadas "publicadas" llevan `far`.
- Tupungatito 2026-08-21 05:30 UTC `VIIRS_SNPP_750`: cúmulo de 1 píxel summit en 0,0 MW, fondo
  256,4 K; las tres pasadas VIIRS375 de esa noche publican 0,06 a 0,16 MW.
- MIROVA publicó alertas MODIS en jun-ago 2026 sólo en Láscar (15 noches); 316 noches por cualquier
  sensor, 64 en nevados.
- `ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK = False`; `hot_mask_2d = fp_hot` pisa el combine
  (`process_modis.py:888`); PDF p. 6 descarta los píxeles del Test 1 como no aptos.
- PyMuPDF capa de texto p. 21: `,20.93` donde el papel dice `< -0.93`.
- NRT: 73 corridas de 168 esperadas en 14 días; PP sin la noche del 13 (último commit remoto de su
  JSON 2026-09-12 20:43 UTC) con el job `success`.
- El guard viejo de la conectiva (`assert "min(" in src`) pasaba por `min_bg_pixels`; el nuevo vigila
  `combinar = max if use_prose_branch else min` y exige 2 apariciones. Barrido A92: 0.

### SOSPECHA (no verificado)

- Que la magnitud del efecto de D23 (Test 1 K1 fuera del hot mask) y D24 (saturado eliminado) sobre
  eventos reales sea grande: son controles sintéticos y conteos; no se reprocesó ningún granule.
- Que el costo directo de la compuerta en VIIRS sea medible sólo con el probe por etapa: no hay
  diagnóstico persistido de "pasó Tests 2 y 3 y cayó sólo por la compuerta".
- Que las tres correcciones juntas no sobreajusten: nueve escenas no lo descartan. Lo decide el A/B
  Tier A con holdout, después de la consolidación y con las decisiones S138-B/C/D tomadas.
- Que el sigma del dNTI del autor sea 0,0008 a 0,0009: medición sobre raster de imprenta, con
  estimadores distintos a los nuestros (std ordinaria contra MAD). El orden de magnitud es firme.
- Que el +13 a 15 % del sigma con remuestreo sea propiedad de nuestro regrid con huecos
  (`regrid.py:123`) y no del remuestreo de MIROVA.

## e. Cerrado en esta sesión, no rehacer

1. **La auditoría S138 entera.** No relanzar los seis ejes; sus archivos y scripts están en el repo.
2. **Las seis contradicciones C1 a C6**: corregidas en su fuente (PR #639). No volver a "descubrirlas".
3. **La atribución de A6 a la compuerta** (S137): CORREGIDA, es el fondo (D25). No correr un brazo
   "sólo sin compuerta" esperando recuperar alertas.
4. **El conteo 33 de 246 noches VIIRS750 como pérdida de recall**: en noches de volcán es 0 de 33.
   No priorizar D25 como recall; sí como fidelidad y magnitud.
5. **"La batería da 6/6 en producción" como evidencia de fidelidad**: refutado (2/6 con el predicado
   del operador). No usar la batería tal como está para decidir nada más; el instrumento corregido
   está propuesto en eje 5 §3.
6. **Numerar las divergencias sin D#**: hecho, D23 a D29 (PR #640).
7. **El A/B de `keep_peak`** (S135) y todo lo cerrado en S137 §e siguen cerrados, con la salvedad de
   S137 §e.5 (intersección contextual), que NO está cerrado (C5).
8. **Medir el disco**: fuera de alcance por decisión de Nicolás.

## f. Prompt para la próxima sesión

```
Retomo VRP Chile en S139. Antes de creerle a nada, verifica el estado real:

  cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
  git fetch origin --prune && git pull --ff-only
  python -m pytest tests/ -q --no-header --tb=line -p no:cacheprovider | tail -1   # esperado: 1325 passed
  gh api repos/MendozaVolcanic/VRP-chile -i 2>/dev/null | grep -i "^date:"          # A86: la hora del servidor
  gh run list --workflow=nrt.yml --limit 3                                          # el NRT sigue vivo?

Lee en este orden, comprobando contra el codigo de hoy lo que cada uno afirme:
  1. tasks/BLOQUE_ARRANQUE_S139.md              <- este archivo: 7 decisiones nuevas (S138-B a S138-H)
  2. docs/AUDIT_S138.md                         <- resumen ejecutivo + §8 (las 6 contradicciones) + §D
  3. docs/audit_s138/EJE_6_decisiones_operacion_higiene.md §1   <- la tabla UNICA de 25 decisiones; manda esta
  4. docs/audit_s138/VERIFICADOR.md §2 y §3     <- la lista fundida H-S138-01..16 y las discrepancias resueltas
  5. docs/MIROVA_DIVERGENCES.md, D22 a D29      <- lo nuevo del catalogo (D25 es la palanca real)
  6. docs/audit_s138/EJE_5_bateria_apendice_instrumento.md §3 y §4   <- instrumento corregido + pre-registro

EL FRENTE D21/D22 ESTA PAUSADO (regla A51, 6 contradicciones). Lo que sigue depende de Nicolas:

  1. Pedirle las decisiones S138-B a S138-H (tabla b de este bloque). Sin S138-B, C y D no hay A/B.
  2. Si aprueba S138-B (a): tag defensivo `pre-s139-d25-d19-flags` ANTES del primer edit, TDD
     (test que capture el crater en 0,0 MW con anillo y > 0 con vecinos: Villarrica A6, Tupungatito
     2026-08-21 05:30 V750), flags APAGADOS para (i) fondo de vecinos uniforme (D25) y (ii) segundo
     pase condicionado (D19/D2, ya existe ENABLE_SECOND_PASS_CONDITIONED), en los 3 sensores.
     Confirmacion explicita de Nicolas antes de mergear (A45). Nada de "solo sin compuerta".
  3. Si aprueba S138-C/D/G: corregir el pre-registro del eje 5 §4 con (a) A2 evaluada a 10,1 km rumbo 84
     respecto del centro de la figura, (b) particion focal/nevado de S131, (c) unidad noche de volcan
     por cualquier sensor, (d) brazos en los 3 sensores para D25/D19, MODIS para D21. Recien entonces
     el A/B Tier A (patron A47: un data_subdir por brazo, nunca paralelo sobre el mismo; A15 timeout).
  4. Si aprueba S138-H: alinear isValidDetection con mirovaEqVrp en index/diario/mosaico (las 3, S92)
     + guard G8; verificar en el navegador, no con node --check.
  5. Si aprueba S138-E: reintento por plataforma en pipeline/fetch.py antes de declarar caido al host
     (A45: tag + confirmacion). Si aprueba S138-F: limpieza git con tag pre-s138-git-cleanup e
     inventario (A38), en sesion aparte.
  6. Si no hay decisiones todavia: lo unico util sin ellas es el instrumento corregido de la bateria
     (eje 5 §3) como script nuevo en experiments/_s139/, sin tocar el de _s136, y correrlo sobre los
     JSON ya commiteados de los 8 brazos para tener la tabla con el predicado del operador.

REGLAS DURAS QUE NO SE NEGOCIAN:
  - Tocar pipeline/process_*.py, detection_context.py, fetch.py, store.py o mirova_equivalent.yaml
    exige tag defensivo Y confirmacion explicita de Nicolas (A45). El tag va ANTES del primer edit.
  - Toda atribucion "X lo elimina" lleva contestada la pregunta "y el paso siguiente, lo recupera?"
    con datos (probe A75 envolviendo TODAS las etapas, o las salidas ya commiteadas). S137 se
    equivoco por saltarla.
  - "Publicamos" se mide con el predicado literal del frontend (mirovaEqVrp, distance_class), y se
    dice con que predicado se midio. Perdidas en noches de volcan, cualquier sensor (A94).
  - Formulas del paper: renderizar la pagina (page.get_pixmap) y mirarla. Ni el .txt ni la capa de
    texto de PyMuPDF sirven para operadores (A95 corregida S138).
  - Flags: leer pipeline.profile, nunca el YAML (A89). Particion focal/nevado: la de S131, unica.
  - Antes de recomendar correr un experimento, buscar si ya corrio: ls experiments/ docs/ (A8/A50).
  - Ningun numero transcrito a mano: el script que lo persiste es la fuente (S91). Todo conteo con
    denominador y ventana (A90), en la unidad del operador (A94).
  - git: nunca stash pop sin git stash list (A96); git cherry miente con squash: verificar por
    contenido. Los 4 stashes S72-S78 no son tuyos.
  - NADA de guiones largos ni medios en ningun archivo, mensaje o commit. Verificar con Python.
  - Espanol de Chile, formas de tu, nunca voseo. Fenomeno fisico primero, numeros al final.
  - Subagentes son volumen, no fuente de verdad (A48): el eje 4 invento una particion que no existe.
  - OneDrive bloquea escrituras a ratos: para editar varios archivos del repo usar el Edit tool o
    reintento; no un script que escriba en cadena.

SI LA SESION NO ALCANZA: cierra con /cierre. Lo que quede en experiments/_s139/ se commitea aunque
este a medias, con su README diciendo que falta. Nada queda solo en la conversacion.
```

---

## Histórico: bloque S138 (cierre de S137)

Se conserva íntegro en `tasks/BLOQUE_ARRANQUE_S138.md`. Lo que ese bloque daba por hecho y S138
corrigió: (1) "la compuerta elimina el cráter de Villarrica en A6" (§a fila 3, §d CONFIRMADO 2): la
compuerta lo rechaza en el primer pase, el segundo pase lo rescata, y lo que lo borra es el fondo del
anillo (D25); (2) "A2 a 9,5-9,7 km rumbo 83": medido con controles, 10,1 km rumbo 84 respecto del
centro de la figura, 11,6 km respecto de la coordenada GVP; (3) su §e.6 daba por cerrado con salvedad
lo que su propio §d dejaba indeterminado (C5). Todo lo demás de ese bloque se sostuvo.
