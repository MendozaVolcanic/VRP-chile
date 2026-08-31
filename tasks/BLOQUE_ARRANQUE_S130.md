# Bloque de arranque S130

## Prompt para pegar al inicio de la sesión

```
Continuamos VRP Chile desde S129. Esa sesión hizo tres cosas: leyó el canon que
faltaba, auditó la visualización completa, y dejó un A/B corriendo.

Leé en este orden:
  1. tasks/BLOQUE_ARRANQUE_S130.md    (esto)
  2. docs/s129/DISPLAY_INDICE.md      (los 4 problemas de display, con su medición)
  3. docs/AUDIT_S128.md               (la auditoría del eje exógeno)
  4. docs/MIROVA_DIVERGENCES.md       (catálogo vivo; D18 es nueva)

═══════════════════════════════════════════════════════════════════════════
LO PRIMERO: LEER EL A/B, QUE QUEDÓ CORRIENDO
═══════════════════════════════════════════════════════════════════════════

**Chunk 1 TERMINADO** (15/15 verdes) y **rescatado a `data/_s129_ab_{control,pool,
bgmag}/`** — ventana 2026-03-01 a 05-28, los tres brazos con conteos idénticos por
volcán (Chaitén 1052 · Láscar 821 · Lastarria 826 · Tupungatito 919 · Villarrica 994).

**Chunk 2 quedó corriendo**: run `33412422099`, ventana 2026-05-29 a 08-24,
`overwrite=false`. Al retomar:

    gh run view 33412422099 --json status,conclusion
    gh run download 33412422099 --dir <scratchpad>/ab_chunk2

⚠️ **EL WORKFLOW NO COMMITEA NADA.** Se le omitió el job `consolidate` al escribirlo,
y se dejó así a propósito (un job que pushea a main necesita el grupo `push-main` o su
propio retry, y no vale el peaje para data experimental). Los resultados viven **sólo
como artefactos, 14 días**. La advertencia está en la cabecera del yml. Los chunks son
disjuntos, así que combinar es **concatenar** por volcán y brazo.

**La lectura ya está escrita y testeada** (A16): `experiments/_s129_ab_fondos/lectura.py`
+ 4 tests. Los criterios están **congelados** en `docs/s129/PREREGISTRO_AB_FONDOS.md`
y no se reinterpretan.

**Qué mide y por qué van juntos los dos brazos**: sus firmas son distinguibles.
  · `pool` (`enable_test1_k1_retire_from_hot_mask`) infla el umbral → al encenderlo
    SUBE el conteo de detecciones y BAJA el umbral efectivo.
  · `bgmag` (`enable_test1_k1_bg_exclude`) sube `L_bg` y baja `ΔL` → mueve el ratio
    SIN tocar el conteo.
  Si los dos mueven el ratio y sólo uno mueve el conteo, la atribución es limpia.

**El criterio que no se negocia**: si un brazo pierde aunque sea una noche que MIROVA
confirmó, es NO ADOPTAR aunque mejore la paridad. Recall antes que paridad.

═══════════════════════════════════════════════════════════════════════════
DECISIONES QUE ESPERAN A NICOLÁS
═══════════════════════════════════════════════════════════════════════════

**1 · El piso VRP — explicado y listo para decidir.**

Qué es: si el VRP de una pasada queda bajo un mínimo (MODIS 0,05 · VIIRS375 0,02 ·
VIIRS750 0,15 MW), se pone en **cero**. El registro queda, con el valor original
guardado aparte, pero cuenta como «no hubo nada».

Lo que S129 encontró leyendo el canon:
  · **Coppola 2019** (el paper del sistema MIROVA) **no declara ningún piso**; el
    «1 MW» que aparece es escala nominal.
  · **Coppola 2014** evaluó cortar en 2 MW, midió que bajaba el acierto de ~79 % a
    <59 %, y lo **rechazó**: *«we preferred to keep some false alerts than missing
    several real hot-spots»*. Y del régimen sub-MW dice que el **75 % son focos
    genuinos**.
  · Un campo fumarólico de clase mundial entraría a nuestro pipeline en **~0,07 MW**
    (cálculo propio con Planck sobre las áreas de Mannini 2019 — modelo, no medición).

Y el detalle que confunde: **el piso corre pero pone en cero `record.vrp_mw`, que el
dashboard NO muestra.** Lo visible sale de `primary_cluster.vrp_mw`, y a ése no lo
toca. Así que hoy no cambia lo que ves, deja un campo en cero mientras el otro sigue
distinto, y si alguien lo aplicara al campo visible cortaría el cráter de Láscar e
Isluga.

**Recomendación: quitarlo.** No porque estorbe sino porque **afirma algo falso** —dice
«acá no hubo nada» sobre detecciones que el canon considera reales en 3 de cada 4
casos. Toca `store.py` → **ciclo A45 completo** (tag + confirmación explícita).

**2 · Dos decisiones de display** (las otras dos ya se arreglaron, ver abajo):
  · **Qué vista manda en el nivel de alerta.** `index` muestra la ÚLTIMA pasada
    (cambiado en S90 **a pedido de Nicolás**); `mosaico` el MÁXIMO de 48 h. Difieren
    en el **19 % de las ventanas**; PCC el 50 % del tiempo. Y la tarjeta de `mosaico`
    **enlaza a `index`**, así que se hace clic en «Bajo» y se aterriza en «Muy Bajo».
    Que `mosaico` muestre el máximo puede ser deliberado — es una vista general.
    **Cuál es la correcta es de Nicolás.**
  · **La curva «VRE acumulada».** Usa `record.vrp_mw` mientras la caja de al lado usa
    `eqVrp`; difieren de **8× a 220×**, y el comentario de la caja documenta la razón
    para no usar ese campo. Arreglarlo es alinear la curva — pero el número visible
    cambia de escala de golpe.

**3 · La rama `s129-display-fixes`** está lista y sin PR. Tres bugs sin ambigüedad,
verificados en navegador real. Decidir si se mergea.

**4 · La ficha SDA**: Nicolás pidió dejarla de lado por ahora. Queda anotado que **no
es alcanzable desde el dashboard** (cero archivos del frontend la mencionan; el deploy
no publica `docs/`) y que su encabezado ya se corrigió a v1.4.

═══════════════════════════════════════════════════════════════════════════
LO QUE S129 DEJÓ ARREGLADO
═══════════════════════════════════════════════════════════════════════════

**En `main`**:
  · **`scripts/libro_de_cuentas.py`** — cada afirmación numérica atada a la función
    que la recalcula, con banda de tolerancia, más la lista de los **387 números sin
    instrumento**. Regla de crecimiento: registrar los que alguien va a citar, no los
    387. **La definición va DENTRO de la afirmación** — al primer arranque marcó tres
    derivas y dos eran errores de registro míos.
  · **`tests/test_guard_timeout_vs_ventana_s129.py`** — A15 dejó de ser prosa. Calibrado
    sobre dos corridas reales (2,4 min por día de ventana). Encontró el mismo bug
    latente en `reproc-s124-villarrica-op-ab.yml` y un falso positivo de sí mismo.
  · **`.github/workflows/reproc-watchdog.yml`** — cada hora revisa los `reproc-*` y abre
    un issue si hay una corrida fallida o colgada más de 7 h. Copia el patrón de
    `nrt-monitor.yml`, que existía para el cron NRT y nunca se generalizó.
  · **`tests/test_guard_gap_a_pool_musigma_s128.py`** — 5 tests; impide volver a cerrar
    el GAP #A con prosa.
  · **`git gc`** corrido: 33 packs → 1, basura 1,57 GiB → 0, disco 98 % → 96 %.

**En la rama `s129-display-fixes`** (sin mergear): la barra «Estado actual» que se
congelaba, «Actualizado» que era el reloj del navegador, y «Últ. detección» que
mostraba el timestamp del máximo.

═══════════════════════════════════════════════════════════════════════════
NÚMEROS QUE CAMBIARON — no citar los viejos
═══════════════════════════════════════════════════════════════════════════

  · **D2** (cobertura del CSV): **79,2 %** global — MODIS 85,2 · V750 77,9 · **V375
    75,7**. Medida por primera vez en 127 sesiones; es **cota superior**.
  · **D5**: el ratio es **0,73** IC[0,704–0,767]. Tenía el número y **el signo
    invertido**: sub-reportamos.
  · **A12 REFUTADA**: Isluga da ΔT 8,3 K, no ~20. **Ningún volcán supera 17 K.**
  · **D9 REFUTADO**: el path D puro está MÁS cerca de la paridad que los otros paths
    en 10 de 11 volcanes.
  · `.git` = **6,5 GB** post-gc · `data/` = 1,03 GB · JSON completos **267 MB**, el
    liviano 37 MB.
  · Corpus: **29 % leído a fondo**, 20 % trabajado antes, 18 % sin tocar.

═══════════════════════════════════════════════════════════════════════════
FRENTES DE FIDELIDAD ABIERTOS, medidos y sin A/B
═══════════════════════════════════════════════════════════════════════════

  · **D18 (nueva)** — el ROI1 del paper es una **caja de 5 × 5 km uniforme**; el
    nuestro un **círculo de 3 a 20 km por volcán**. **El 68,9 %** de los píxeles que
    hoy reciben el umbral laxo de *summit* no lo recibirían con la geometría del canon.
    PCC es **50,3×** el área del paper. Es per-volcán, que MISSION excluye, y es el eje
    que A82 nunca auditó. ⚠️ Corregirlo da **menos detecciones**, y `mirova_equivalent`
    prioriza recall — **es decisión de misión**.
  · **El remuestreo** — el fix fiel del gradiente por cenit (medido: VIIRS375 va de
    0,796 cerca del nadir a 0,570 entre 35° y 50°, IC sin solape). Coppola 2014 §2.2 da
    el mecanismo: el remuestreo **parte** el píxel elongado en celdas de área nominal.
    ⚠️ **El brazo tiene que ser bow-tie + regrid**, no regrid solo: Coppola 2012 §3.2
    pone el bow-tie como paso (i), y regridear sin de-solapar duplicaría píxeles
    calientes.
  · **La suma vs el clúster** — MIROVA **suma** todos los píxeles alertados (Coppola
    2019 p.3). Medido: pasar a la suma dentro de 5 km sube el ratio de 0,730 a 0,798,
    **pero no hay radio uniforme que sirva** (el mejor por volcán va de 1 a 25 km) y
    Chaitén sale de banda. Resultado **negativo**; queda como brazo, no como adopción.
  · **A54** sigue sin respaldo reproducible. **D13** necesita que se declare el
    denominador.

═══════════════════════════════════════════════════════════════════════════
LO QUE NO HAY QUE REABRIR (anti-A8)
═══════════════════════════════════════════════════════════════════════════

  · **El archivo público de TIF no adjudica detección ni magnitud**: no trae banda TIR.
    La sonda que lo intentó se refutó sola — el **85 %** de las pasadas donde MIROVA
    declaró ALERTA tampoco pasa su propio corte.
  · **El área nadir fija está respaldada** por Campus 2022 Eq.1.
  · **Publicar por pasada y con la máscara de nube apagada está validado por el canon**:
    Coppola 2019 dice que las series van *«as they are»* y que **no** se corrigen
    automáticamente por nube ni geometría.
  · **Los filtros de artefacto del frontend están DORMIDOS** post nadir-fijo: cero
    disparos. Lo confirmaron tres auditorías independientes.
  · **A81 ya falló sobre el far→summit oculto** (S113): no destapar. ⚠️ Pero los números
    no coinciden — A81 contó 2.527 records y hoy son **9.181**. Resolver esa diferencia
    ANTES de proponer nada ahí.

═══════════════════════════════════════════════════════════════════════════
REGLAS DE ESTA ETAPA
═══════════════════════════════════════════════════════════════════════════

  · **A89 tiene forma nueva: el flag mal nombrado.** Antes de escribir «esto no se usa»
    o «esto está cerrado», trazá **cómo lo lee el código**. En S129 los flags del A/B
    fueron bajo `thresholds:` y `pipeline.profile` los leía `False` — se leen de
    `paths:` (`profile.py:131`).
  · **NUEVA — no heredar afirmaciones de informes previos sin trazarlas.** En S129 pasé
    **tres premisas falsas** en briefs a agentes (que `mosaico` bajaba 267 MB, que
    `_mirova_confirmed` no se mostraba, que los filtros de artefacto suprimían). Las
    tres las corrigieron los agentes. Es el mismo modo de olvido, del lado de quien
    escribe el encargo.
  · **Los cambios de frontend se verifican en NAVEGADOR REAL**, no con `node --check`.
    En S129 un reemplazo dejó colgando un `textContent =` que asignaba `undefined`; la
    sintaxis pasaba limpia y sólo el preview lo mostró. `preview_start` con
    `.claude/launch.json` (puerto 8091), servir desde `/frontend/`.
  · **Toda sonda que juzgue al sistema necesita control de instrumento**: medir primero
    si distingue a MIROVA de sí misma.
  · Verificar flags leyendo `pipeline.profile`, NUNCA el YAML.
  · Estratificar por volcán. Un par por noche, máximo de ambos lados.
  · Todo número sale de un script que lo persiste (S91) — y ahora se registra en
    `scripts/libro_de_cuentas.py` con su **definición**.
```

---

## Estado al cerrar S129

**Suite**: 1024 tests verdes (+3 skipped). **NRT**: sano. **Operacional intacto**: no se
tocó `pipeline/` ni ningún perfil operacional. **Disco**: 96 %.

**Ramas abiertas**: `s129-display-fixes` (3 bugs arreglados, sin PR). Las otras dos
—`s129-ab-fondos` y `s129-ab-fix-timeout`— ya se mergearon y se pueden borrar del remoto.

### Lo que quedó PROBADO

| hallazgo | cómo se probó |
|---|---|
| **El GAP #A no era un mislabel** | cadena de 3 saltos verificada; las dos patas del cierre de S115 son falsas |
| **D17 y el gap de magnitud son el mismo problema** | Coppola 2014 §2.2 verbatim + gradiente medido 0,796→0,570 |
| **MIROVA suma los píxeles alertados** | Coppola 2019 p.3 verbatim; 3 brazos medidos (0,730 / 0,798 / 0,924) |
| **El método MIR no ve lo difuso** | Campus 2024 p.4 verbatim + Mannini 2019: el 93 % del calor es difuso |
| **No hay radio de suma uniforme** | barrido 1-25 km; el mejor por volcán va de 1 a 25 |
| **D18: el ROI1 es 3 a 50× el del paper** | 107.265 píxeles medidos; el 68,9 % perdería el umbral laxo |
| **La barra de alerta se congelaba** | instrumentada en navegador: 0 llamadas antes, 1 por toggle después |
| **La VRE se calcula dos veces** | `index.html:1964` vs `:2786`, 8× a 220× |
| **Dos niveles de alerta distintos** | 2.640 ventanas: 19 % discrepa de nivel, PCC el 50 % |

### El patrón que ordena la sesión

**Una regla escrita no impide el error que describe.** A15 existía, era correcta, la
conocía, y la violé copiando un `timeout` sin recalcular la ventana — ocho jobs muertos
y 6 h de CI. El test que la reemplaza encontró el mismo bug latente en otro workflow al
primer intento.

Eso completa el mapa de los tres modos de olvido, cada uno con su instrumento: el
**libro de cuentas** para los números que se pudren, los **guards** para las
afirmaciones sobre lo que el código hace, y el **watchdog** para los procesos que mueren
sin testigo.
