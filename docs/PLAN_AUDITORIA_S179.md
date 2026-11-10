# Plan de auditoría S179: decisiones y planes de S172 a S178, con Fable 5.2

> Pre-registro. Este archivo se commitea en `loop/activo` **antes** de lanzar ningún agente; cada verificador comprueba
> con `git diff <commit del plan> -- docs/PLAN_AUDITORIA_S179.md` que no cambió (guía maestra §3b, «una auditoría
> también se pre-registra»). Lo que se agregue después va rotulado *post hoc*.
>
> Pedido de Nicolás (S178, contestado en S179: «Sí, b3 primero»): auditar con Fable 5.2 las decisiones y planes de S172
> a S178 y mejorar los planes. Diseño según `C:\Users\nmend\OneDrive\Escritorio\claude\GUIA_MAESTRA_AUDITORIAS.md`
> (§3, §3b, §4 y §5), la guía de prompting de Fable 5.2
> (`C:\Users\nmend\OneDrive\Escritorio\claude\GUIA_PROMPTING_prompting-claude-fable-5-2.md`, escrita en S179 desde la
> página oficial) y el plan anterior, `docs/PLAN_AUDITORIA_S175.md` (rama `claude/relaxed-almeida-d17378`, PR #955).

## 0. En una pantalla

- **Qué se audita.** Las decisiones tomadas y los planes escritos entre S172 (2026-11-01) y S178 (2026-11-10): la
  adopción de la vía «código MIROVA» en MODIS, el encendido preparado de VIIRS (B1, B2), la regla de reversión de VIIRS
  sellada, la retrospectiva y su lectura, y los planes pendientes (reemplazo de la historia, red de los 34).
- **Eje nuevo** (regla A del protocolo): «decisión contra su evidencia». Por cada decisión, si la evidencia que la
  sostenía en el momento alcanzaba, si se aplicó como se aprobó y si lo que vino después la confirma o la debilita. Las
  auditorías anteriores midieron el sistema corriendo (S175) o los cierres (S145, S160 F3); ésta mide las decisiones
  recientes y propone mejoras a los planes que siguen abiertos.
- **Cuatro frentes** con un auditor Fable 5.2 a esfuerzo `high` cada uno: A (MODIS), B (VIIRS), C (instrumento y
  retrospectiva), D (planes pendientes). Un verificador Opus 5.5 a `high` por frente, con contexto limpio.
- **Lo que no hace**: ningún arreglo, nada en `pipeline/`, `data/` ni `frontend/`, ningún merge, ningún workflow, ninguna
  llamada a NASA, ningún reproceso.
- **Costo estimado**: 2,7 a 3,6 millones de tokens (sección 7).

## 1. Base (fijada por hash)

| qué | ref | commit |
|---|---|---|
| código y datos | `origin/main` | `438a60a1e516fd04136e2144c797670c1cfdd46a` |
| bitácora, bloques de arranque, experimentos del loop | `origin/loop/activo` | `0472cd95e452b7e09ffddbd9db22dd40d0c21f41` (el commit de este plan va encima y sólo agrega este archivo y los prompts) |
| retrospectiva | tags `s172-retro-d2`, `s173-prereg-retro-sellado`, `s178-retro-lectura`, `s178-retro-historia` | los del tag |
| reglas selladas | tags `s173-regla-modd-sellada`, `s178-regla-reversion-viirs-sellada` | los del tag |
| PR en borrador | #974, #975, #980, #981, #983 (y #955, auditoría S175) | la punta que el auditor anote con su hora del servidor |

Lo que vive fuera de main va rotulado «fuera de main» en cada número.

## 2. Puerta de entrada: pendientes de S175 (regla C)

Cada frente lee `docs/AUDIT_S175.md` §6, §8 y §11.6 (rama `claude/relaxed-almeida-d17378`) y toma primero los
pendientes que caen en su eje. Los que no caen en ninguno se anotan en el informe del frente D como «sin eje», sin
perseguirlos.

## 3. Los frentes (esto es lo que el sello congela)

Para cada decisión del inventario, el veredicto es uno de: SOSTENIDA (la evidencia de entonces alcanzaba y lo
posterior no la contradice), SOSTENIDA CON RESERVAS (di cuáles), DEBILITADA (lo posterior la contradice en parte),
SIN RESPALDO (no hay script, run, commit o archivo:línea que la sostenga) o APLICADA DISTINTO (se implementó otra cosa
que lo aprobado). Además, cada frente entrega una sección PROPUESTAS PARA LOS PLANES: mejoras concretas a los planes
abiertos de su eje, cada una atada a un hallazgo o a una medición de la sesión, sin implementarlas.

### A. MODIS: la adopción de S172 y lo que vino después

- **Pregunta**: ¿la adopción de la vía «código MIROVA» en MODIS (PR B, #934, decisión de Nicolás del 2026-10-31) se
  sostiene hoy? ¿La retrospectiva leída en S178 (MODIS fila 4, DECIDE NICOLÁS, `cambia_sin_pasadas_b`), la regla de
  reversión de MODIS sellada (tag `s173-regla-modd-sellada`), la guardia K de MODIS y el audit semanal vigilan lo que
  dicen vigilar desde el 2026-11-02?
- **Material de partida** (es un piso): bitácora §6 de `tasks/LOOP_OBJETIVOS.md` (entradas S172 a S178), bloques de
  arranque S172 a S179, `experiments/_s171_modd_adopcion/`, `experiments/_s172_miniaud/SINTESIS.md`,
  `pipeline/mirova_v750_codigo.py`, `pipeline/profiles/guardia_k_modis.yaml`, `scripts/vigilancia_guardia_modis.py`,
  `scripts/auto_audit_weekly.py`, `experiments/_s178_lectura/` (rama `claude/s178-retro-lectura`), `docs/MISSION.md`,
  `docs/FICHA_SDA_VRP_CHILE.md`.
- **Hallazgo**: decisión sin evidencia suficiente en su momento; evidencia posterior que la debilita; vigilancia
  prometida que no mira (ciega, sin poder o con un umbral que no puede disparar); diferencia entre lo aprobado y lo que
  corre en main.

### B. VIIRS 375 y 750: el encendido preparado y su regla de reversión

- **Pregunta**: ¿#974 (B1, VIIRS 375) y #983 (B2 sobre B1, VIIRS 750) hacen exactamente lo aprobado y nada más? ¿La
  regla de reversión de VIIRS sellada (D1 a D7, cotas C-rad 14/17 en VIIRS 375 y 12/2 en VIIRS 750) mide lo que dice,
  con el poder que dice? ¿La evidencia de adopción de cada sensor (V375-E, V750-A en borrador #964, la retrospectiva
  fila 6 y fila 4) alcanza para encender?
- **Material de partida**: PR #974, #975, #980 y #983; `experiments/_s176_v375e_adopcion/REGLA_REVERSION_V375E_BORRADOR.md`
  (sellada), `scripts/vigilancia_guardia_viirs.py`, `experiments/_s178_cotas_v375/`, `experiments/_s162_v375/PREREGISTRO_E.md`,
  `experiments/_s162_v750a/`, `docs/superpowers/specs/2026-11-08-encendido-v375e-design.md`, bitácora S176 a S178.
- **Hallazgo**: un PR que enciende más o menos de lo aprobado o en otro orden; una cota que no puede disparar o que
  dispara por azar más de lo declarado; una condición de la regla que el vigilante no implementa; evidencia de adopción
  concentrada en pocos casos sin decirlo.

### C. Instrumento y retrospectiva: el candado y las decisiones *post hoc*

- **Pregunta**: ¿la lectura de la retrospectiva (tag `s178-retro-lectura`) respetó el pre-registro sellado
  (`s173-prereg-retro-sellado`)? Cada decisión tomada después del sello (banda de triangulación en VIIRS 375 para
  C-montaje, caja B4 en el lector, OSF fuera de git verificado por sha256, «SIN SUSTRATO no bloquea» en la curva de
  cenit), ¿está rotulada *post hoc* y podría haber cambiado algún veredicto? ¿Los controles (C-K, C-montaje, placebo,
  sorteo) tenían poder para fallar?
- **Material de partida**: `experiments/_s172_prereg_retro/`, `experiments/_s172_retro_paquete/leer_retro.py` y su
  versión en `claude/s178-retro-lectura`, `experiments/_s178_ck/`, `experiments/_s178_montaje/`, `experiments/_s178_lectura/`,
  bitácora S178. Puedes correr el lector desde el worktree existente `D:\vrp-trabajo\worktrees\s178-lectura` sin
  modificarlo, con la salida en tu carpeta temporal.
- **Hallazgo**: criterio cambiado después del dato sin rótulo; control que no puede fallar; veredicto que cambia con una
  decisión *post hoc* distinta pero igual de razonable; diferencia entre lo que el lector calcula y lo que el
  pre-registro dice.
- **Para este frente, el lector y sus controles son objeto, no vara**: usa una implementación propia donde compares.

### D. Planes pendientes contra la misión

- **Pregunta**: los planes abiertos (reemplazo de la historia con la vía, #981 y `docs/PLAN_REEMPLAZO_HISTORIA_VIA_S178.md`;
  red de los 34, `docs/superpowers/plans/2026-11-02-nrt-34-volcanes.md` y su compuerta de publicación; el orden de
  encendido B1, B2 y el reemplazo), ¿se pueden ejecutar tal como están escritos? ¿Pasan las tres preguntas de
  `docs/MISSION.md`? ¿Qué falta o sobra?
- **Material de partida**: los documentos nombrados, `.github/workflows/pages-deploy.yml`, `scripts/reemplazar_ventana_reproceso.py`,
  bitácora S172 a S178, `docs/MISSION.md`, bloque S179 §b y §g.
- **Hallazgo**: paso que no se puede ejecutar como está escrito; paso que rompe otra cosa (prueba, vigilante,
  despliegue, límite de un servicio); plan que contradice la misión o una regla vigente; decisión pendiente que el plan
  da por tomada.

### Línea base roja (control ciego)

Cada frente tiene defectos ya conocidos de su eje que su barrido tiene que volver a encontrar solo. **No van en los
prompts**: quedan escritos aquí, con este commit, y el orquestador cuenta cuántos reencontró cada auditor. Un frente que
no reencuentra ninguno queda con su cero en SOSPECHA y pasa entero al verificador.

| frente | defecto conocido | dónde quedó escrito |
|---|---|---|
| A | MODIS corre la vía en producción desde el 2026-11-02, y la retrospectiva leída el 2026-11-10 no la respalda sola: fila 4, DECIDE NICOLÁS, sin poder sin las 21 pasadas del §3.1 (b) | bitácora S178, 08:51 UTC |
| A | el audit semanal no juzga MODIS hasta 15 noches con la vía (tenía 7 el 2026-11-09): una semana sin vigilancia de magnitud tras la adopción | bitácora S178, P9 |
| B | #983 contiene B1 y B2: mergearlo antes que #974 enciende los dos sensores | bitácora S178, #983 |
| B | la evidencia de VIIRS 750 se apoya en 14 casos, 12 de Chillán | bloque S179 §b, decisión 2 |
| B | la opción B de las cotas sumaba por día con exposiciones distintas (sin NOAA-21 antes del 2026-04-09) | bitácora S178, P10 verificado |
| C | la banda de triangulación de VIIRS 375 en C-montaje se decidió después de ver las 12 diferencias | `experiments/_s178_montaje/PROPUESTA_C_MONTAJE.md` |
| C | «SIN SUSTRATO no bloquea» en los controles de cenit es de S174, posterior al sello del pre-registro | bitácora S178, verificador de la lectura |
| C | C-montaje con poco poder: celdas alertadas en 12 de 343 MODIS, 51 de 166 VIIRS 375, 32 de 440 VIIRS 750 | idem |
| D | #981 no tiene la regla de no pisar records de la vía ni agregar los de P4 desde el 2026-11-02 | bitácora S178, verificador de #981 |
| D | la unión en `data/_s178_historia_via/` llevaría Pages a ~1.010 MB, sobre el límite de 1 GB | idem |
| D | Tupungatito antes del 2026-02-23 no entra al planificador sellado y el plan no lo resuelve | bloque S179 §b, decisión 7 |

### Corte del verificador (fijado antes de lanzar)

Pasan al verificador: todo hallazgo de gravedad 3 o más; todo hallazgo de cualquier gravedad sobre un instrumento que
sostiene una decisión vigente o inminente (lector de la retrospectiva, `vigilancia_guardia_viirs.py`,
`vigilancia_guardia_modis.py`, revisores de la guardia, `auto_audit_weekly.py`); toda decisión con veredicto DEBILITADA,
SIN RESPALDO o APLICADA DISTINTO; y, si un frente no reencontró ninguna línea base, su informe entero. Lo demás se
publica con su conteo.

## 4. Verificadores y síntesis

- Un verificador por frente (VA, VB, VC, VD), Opus 5.5 a `high`, del otro modelo que el auditor. Recibe título,
  archivo:línea o script:salida y gravedad de cada hallazgo, sin el razonamiento del auditor. Escribe `caminos.md` con su
  sha256 y la hora del servidor antes de abrir nada citado; el orquestador guarda el hash.
- Síntesis del orquestador en `docs/AUDIT_S179.md`, sólo con veredictos de verificador: líneas base reencontradas por
  frente, hallazgos confirmados, propuestas para los planes que sobreviven, decisiones para Nicolás con recomendación, y
  el registro de agentes (modelo, esfuerzo medido en el transcripto, duración, tokens).

## 5. Dónde corre y con qué recursos

- **Instantánea de main sin `data/` ni `experiments/`** (~20 MB): `git archive 438a60a1e pipeline scripts frontend
  .github tests docs CLAUDE.md README.md volcanoes.yaml latest_consolidado.csv` a
  `D:\vrp-trabajo\temporales\s179-audit\main\`, y los documentos del loop (`tasks docs`) de `0472cd95e` a
  `D:\vrp-trabajo\temporales\s179-audit\loop\`. Datos y experimentos, archivo por archivo con
  `git show <ref>:<ruta>` (con `MSYS_NO_PATHCONV=1`).
- **Carpetas**: informe y scripts en `experiments/_s179_audit/<frente>/` del checkout principal
  (`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile`, rama `loop/activo`); temporales en
  `D:\vrp-trabajo\temporales\s179-audit\<frente>\`. Nadie hace commit salvo el orquestador.
- **Insumos de GitHub** (una vez, el orquestador, antes de la ola 1): estado de los PR #934, #955, #964, #974, #975,
  #980, #981, #983 (punta, checks, cuerpo); últimas 20 corridas de `guardia-k-viirs.yml`, `guardia-k-modis.yml`,
  `vigilancia-guardia-viirs.yml`, `vigilancia-guardia-modis.yml`, `audit-weekly.yml`, `sombra-codigo-mirova.yml` y
  `pages-deploy.yml`; issues abiertos; con la hora del servidor, en `D:\vrp-trabajo\temporales\s179-audit\insumos\`.

| recurso | tope | parada |
|---|---|---|
| disco | 500 MB por agente en su temporal; ninguna copia del árbol, ningún worktree nuevo, ningún `git init` | cualquiera se detiene si C: o D: baja de 3 GB |
| agentes | 2 a la vez | el orquestador no lanza un tercero |
| procesos pesados locales | 1 por agente | |
| API de GitHub | 10 llamadas por auditor, 5 por verificador, después de leer los insumos | ninguna si `rate_limit` baja de 200 |
| NASA, workflows, credenciales | ninguno | usar uno es parada |
| subagentes | ninguno, salvo que un barrido no quepa en el contexto; cada uno cuesta lo que un encargo entero | |

**Olas**: 0) instantánea e insumos; 1) A y C; 2) B y D a medida que se libera un cupo; cada verificador entra cuando
termina su auditor; 3) síntesis. El orquestador mira `get_usage` antes de cada lanzamiento y para si el semanal de
todos los modelos pasa de 85 %.

## 6. Prompts

Cada prompt es, en este orden: el bloque `<preambulo_auditor>` de `docs/_prompts/PREAMBULO-AUDITOR.md` **entero**, tal
como está en la base (sha256 del bloque `36a55c66d016afb3a28b2cdca446f19c32065c8c5b9e6affdfa1e31bb2cb6c1b`, igual en
main y en loop), con los huecos llenos; la `<tarea>` del frente; y el bloque `<autonomia>` **para Fable 5.2** de §6.3.
Los arma `experiments/_s179_audit/armar_prompts.py`, que también comprueba que no quede ningún hueco
(`«[A-Z_]+»`). Los prompts armados quedan en `experiments/_s179_audit/prompts/` con este commit.

### 6.1 Huecos comunes

```text
«DEFINICIONES_DE_LA_VARA» =
- «publica»: lo que da el predicado del tablero ejecutado con node por scripts/banco_paridad.py::correr_node (l. 178)
  sobre frontend/index.html del commit 438a60a1e (regla A97). Nunca una reconstrucción a mano.
- «alerta de MIROVA», «protegida» y «negativo limpio»: lo que devuelve scripts/banco_paridad.py::etiquetar (l. 350) en
  438a60a1e, con la regla D-9 de scripts/clase_mirova.py. Protegida es alerta de 1 MW o más (lectura A, D-4).
- pareo de una fila de MIROVA con una pasada nuestra: TOL_S de scripts/banco_paridad.py l. 80 en 438a60a1e.
- la referencia: la copia del repo en 438a60a1e, latest_consolidado.csv (sha256 40b1b928c602b37f...7fdf6) y
  data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv (sha256 7e54155a3e0ddd0a...1e75), no la remota viva.
  La retrospectiva usó sus propias copias congeladas (CONS 811c4c07, OCR 01c9478d): para juzgarla vale la suya.
- «detector efectivo» de un record MODIS: la vía si via_codigo_mirova es true, K en otro caso
  (scripts/auto_audit_weekly.py l. 555 en 438a60a1e).
- decisión de Nicolás: una frase suya registrada en la bitácora o en un PR con su hora; una aprobación reenviada por
  otra sesión no cuenta (regla S157).
- documentos de loop/activo: en 0472cd95e. Lo que vive en una rama o un PR sin mergear: rotulado «fuera de main».
«LIMITES_DE_RECURSOS» = Esta tarea no nombra ningún workflow ni credencial, y no llama a NASA. Hasta 10 llamadas a la
API de GitHub (verificador: 5), después de leer D:\vrp-trabajo\temporales\s179-audit\insumos\. Disco: tu carpeta
temporal, tope 500 MB; ninguna copia del árbol, ningún worktree nuevo, ningún git init. Como mucho un proceso pesado
tuyo a la vez.
```

| agente | «CARPETA» | temporal | «RANGO» |
|---|---|---|---|
| A | `...\experiments\_s179_audit\a\` | `D:\vrp-trabajo\temporales\s179-audit\a\` | 401 a 449 |
| B | `...\experiments\_s179_audit\b\` | `...\s179-audit\b\` | 451 a 499 |
| C | `...\experiments\_s179_audit\c\` | `...\s179-audit\c\` | 501 a 549 |
| D | `...\experiments\_s179_audit\d\` | `...\s179-audit\d\` | 551 a 599 |
| Vn | `...\experiments\_s179_audit\vn\` | `...\s179-audit\vn\` | Vn-01 en adelante |

(`...` es `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile`; en el prompt armado va la ruta entera.)

### 6.2 Líneas comunes de la tarea

```text
Para qué sirve esto: Nicolás va a decidir en los próximos días si enciende la vía «código MIROVA» en VIIRS 375 y 750
y cómo reemplaza la historia publicada. Necesita saber qué decisiones de S172 a S178 se sostienen, cuáles no, y qué
cambiar en los planes antes de ejecutarlos. Tu informe lo lee él y una sesión que no vio nada de esto.

Arma tú el inventario de decisiones de tu eje desde la bitácora (tasks/LOOP_OBJETIVOS.md §6, entradas S172 a S178) y
los bloques de arranque S172 a S179, y declara el comando con que lo armaste, para que la cobertura se pueda revisar.
Una decisión fuera de tu eje va a SEGUIMIENTOS con una línea. Empieza por los pendientes de docs/AUDIT_S175.md §6, §8 y
§11.6 (rama claude/relaxed-almeida-d17378) que caen en tu eje.

Por cada decisión da un veredicto (SOSTENIDA, SOSTENIDA CON RESERVAS, DEBILITADA, SIN RESPALDO o APLICADA DISTINTO) con
la evidencia de tu sesión. Al final, una sección PROPUESTAS PARA LOS PLANES: mejoras concretas a los planes abiertos de
tu eje, cada una atada a un hallazgo o a una medición tuya. No las implementas.

Mide en la base que dice docs/PLAN_AUDITORIA_S179.md §1 y nombra el commit en cada número. Lee el código desde
D:\vrp-trabajo\temporales\s179-audit\main\ y los documentos del loop desde D:\vrp-trabajo\temporales\s179-audit\loop\;
datos y experimentos, con git show <ref>:<ruta> y export MSYS_NO_PATHCONV=1. No toques ramas, worktrees ni carpetas
de otros (D:\vrp-trabajo\worktrees\*, D:\vrp-trabajo\temporales\s17[0-8]*), salvo leer.
```

### 6.3 Bloque `<autonomia>` para Fable 5.2

El de `docs/_prompts/PREAMBULO-AUDITOR.md` trae el bloque oficial de Fable 5.1. Para Fable 5.2 se usa el texto oficial
medido para 5.2 («Finishing work», guía de 5.2 §3.1), en inglés y sin tocar, seguido de las paradas de auditoría y de
la línea con lo que no necesita aprobación (guía de 5.2 §4.3: con 5.2, nombrar los pasos libres rinde y una
instrucción general de «actúa con libertad» no). Llevar este bloque a `PREAMBULO-AUDITOR.md` en main queda como
seguimiento (manda la copia de main).

```text
<autonomia>
# Finishing work
Please avoid stopping while you still owe work the user asked for. Be persistent and do not stop unless needed.

While status notes are welcome, as is clarifying with the user on open decisions, carry on with work that does not depend on the user's answer without unnecessary stops.

If you notice yourself inviting the user to redirect you or offering to wait, instead proceed on the next part of the task. You may meet ordinary obstacles like errors, timeouts, locked files, empty results or failing tools. Diagnose them first, and when they are not real blockers, work through them with the access you have (wait and retry, fix the request, use another tool or source) rather than stopping unnecessarily.

If someone clearly decided something is a hard blocker, such as a file marked not to be touched, access that was intentionally withheld, or a safety guardrail, leave it alone, say plainly what you found, and look for another safe way to finish the task. Stopping before the task is complete is very rarely merited, as in when the task can't move forward without user input, or where the blocker is deliberate and should not be worked past. This does not override the need for confirmation on risky or destructive actions.

Nadie te mira en vivo y nadie puede contestarte a mitad de camino. En esta auditoría tu entregable es tu evaluación,
nunca un arreglo. Son obstáculos deliberados, que no se atraviesan y se dejan escritos como pendientes: escribir fuera
de «CARPETA» y de tu carpeta temporal (porque el checkout lo comparten otras sesiones); hacer commit, push o merge
(porque los merges son sólo de Nicolás); despachar un workflow o llamar a NASA (porque la cuenta Earthdata se bloquea
con reintentos); usar una credencial. No necesitan aprobación y los haces sin preguntar: leer cualquier archivo del
repo, de sus ramas y tags y de los worktrees existentes; correr y re-correr scripts del repo o tuyos con la salida en tu
carpeta; reintentar un comando de lectura que falló; recontar; escribir y reescribir tu informe. Escribe el informe en
«CARPETA» a medida que avanzas: si la sesión se corta, lo que esté en el disco es lo que queda. Si algo te bloquea,
termina todas las partes que no dependen de eso y di exactamente qué quedó fuera y por qué. Si C: o D: baja de 3 GB
libres, te detienes y lo escribes.
«LIMITES_DE_RECURSOS»
</autonomia>
```

Y, antes de `<autonomia>`, el bloque oficial de informes de la guía de 5.2 §3.4 («Communicating clearly»), en inglés,
seguido de: «Escribe en español de Chile, con tú. Sin guiones largos ni medios: delatan texto generado y el informe
puede salir a otras personas. Rutas absolutas completas, porque Nicolás las pega en el explorador.»

### 6.4 Verificadores

Preámbulo entero con los huecos del verificador, el bloque `<verificador>` del mismo archivo, la lista que arma el
orquestador desde `hallazgos.csv` y las decisiones con veredicto DEBILITADA, SIN RESPALDO o APLICADA DISTINTO (título,
archivo:línea o script:salida, gravedad; sin el razonamiento del auditor, tampoco en celdas), y el mismo `<autonomia>`.

## 7. Costo estimado

Base medida: en S175, F1 (Fable 5.1 a `high`) usó 373 mil tokens en 25 minutos y V1 (Opus 5.5 a `high`) 275 mil en
16 minutos (`docs/AUDIT_S175.md` §9); en S160, auditores Fable de 385 a 503 mil y verificadores Opus de 317 a 385 mil
(`experiments/_s160_audit/REGISTRO_AGENTES.md`).

| | agentes | tokens estimados | reloj |
|---|---|---|---|
| auditores (Fable 5.2, `high`) | 4 | 1,5 a 2,0 millones | 25 a 50 min cada uno |
| verificadores (Opus 5.5, `high`) | 4 | 1,1 a 1,5 millones | 15 a 40 min cada uno |
| orquestador (instantánea, insumos, listas, síntesis) | 1 | 0,1 a 0,3 millones | |
| **total** | 9 | **2,7 a 3,8 millones** | 3 a 4 h en dos olas |

En S175 Nicolás calculó que 5 a 6 millones eran un 5 a 6 % de la cuota semanal; con esa regla, esto es un 3 a 4 %.
Fable 5.2 cuesta un 20 % menos por token que 5.1. Riesgo de subestimar: C puede re-correr el lector; D lee el plan de
reemplazo y cuenta archivos de `data/`.

## 8. Lo que decide Nicolás antes de lanzar

| # | decisión | recomendación |
|---|---|---|
| 1 | Los cuatro frentes, o recortar | los cuatro; si hay que recortar, D primero (sus tres huecos más graves ya están anotados en #981) |
| 2 | Verificador de otro modelo por frente | sí, Opus 5.5 a `high`; recortar verificadores es lo último |
| 3 | Lanzar ya o esperar la primera corrida de la guardia (19:35 UTC) | ya: ningún frente necesita esa corrida; B la anota si llega |

## 9. Adenda antes del lanzamiento (2026-11-10 20:36 UTC)

Nicolás dejó la elección en el orquestador («lo que recomiendes»). Se lanzan **los cuatro frentes**, como recomendaba
§8: el semanal de todos los modelos estaba en 33 % y el de Fable en 25 % (`get_usage`, misma hora), y el costo
estimado es de 3 a 4 % de la cuota. La idea de recortar a B y D salió de las mediciones exploratorias de hoy
(`experiments/_s179_perdidas/`, `experiments/_s179_chillan/`), pero esas mediciones no tienen verificador: no
reemplazan a los frentes A y C.

Línea base roja agregada con esta adenda, antes de lanzar y fuera de los prompts (que no cambian; sha256 en
`experiments/_s179_audit/prompts/SHA256.txt`):

| frente | defecto conocido | dónde quedó escrito |
|---|---|---|
| D | ningún plan abierto dice qué pasa con las alertas diurnas de MIROVA (D-10, #813): 162 filas de alerta de abril a noviembre, 138 de 1 MW o más, 63 de Chillán; ni el plan de reemplazo ni el de los 34 las nombran (grep de «diurn», «D-10», «#813» en 0472cd95e: 0) | `experiments/_s179_perdidas/INFORME.md` §2 |

Se descartó como línea base que la retrospectiva no cubra la erupción de Chillán: el propio pre-registro lo declara
(`PREREGISTRO_RETRO_PAQUETE.md` l. 47 en 0472cd95e). Main avanzó a `4cf5fe62e`; la base sigue fijada en §1.
