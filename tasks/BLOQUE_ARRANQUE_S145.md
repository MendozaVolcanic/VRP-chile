# Bloque de arranque S145

> Cierre de S144 (2026-09-19 18:27 a 2026-09-20 02:58 UTC, hora del servidor). `main` en
> **`efe644e30`**, verificado igual al remoto con `git ls-remote`. **Sin PR abiertos**, sin ramas sin
> integrar (las dos de la sesión, `s144-conteo-tif` y `s144-prereg-keep-peak-direccion`, dan diff vacío
> contra `main`: el `git cherry` las marca pendientes por el squash, A96). **Nada en vuelo al fijar
> este estado**: los siete verificadores terminaron y no quedan procesos ni tareas en segundo plano.
> Suite al cerrar: **1551 passed, 4 skipped, 2 xfailed** (base de S143 era 1539; los 12 nuevos son del
> conteo). Sin cambios sin commitear salvo `experiments/_s140/`, que ya venía sin trackear de S140.
>
> Sesión de un solo frente: la **decisión 1 de S144** (medir con dirección si el cúmulo lejano de
> `keep_peak` es el objeto que MIROVA vio). Terminó **cerrada**, sin correr la medida pre-registrada.

## a. Todo en una pantalla

| qué | estado | evidencia |
|---|---|---|
| **Frente `keep_peak` con dirección** | **CERRADO** por decisión de Nicolás, sin correr la medida | `docs/CIERRE_FRENTE_KEEP_PEAK_S144.md`; PR #707 (`efe644e30`) |
| Conteo versionado de pasadas V375 con TIF | en main, con 12 tests | PR #706; `experiments/_s144_conteo_tif/RESULTADO.md` (lo genera el script) |
| **A106 corregida**: la grilla UTM de MIROVA duró 8 adquisiciones (14-sep 06:36 a 15-sep 06:24) | en main | `CLAUDE.md` A106; CRS leído con rasterio archivo por archivo |
| Pre-registro de la medida, v1 a v7, y sus **7 informes de verificación** | en main, versionados | `docs/PREREGISTRO_KEEP_PEAK_DIRECCION_S144*.md` |
| Records del brazo control del A/B S143, que vencían en GitHub el 2026-10-02 | congelados en el repo | `experiments/_s144_keep_peak_direccion/control_s143/` + `MANIFIESTO.json` (18 sha256 verificados) |
| Los 66 scripts de los verificadores, que vivían en carpetas temporales | rescatados | `experiments/_s144_keep_peak_direccion/verificadores/` |
| Reglas nuevas **A109** (maldición del ganador) y **A110** (un control se valida midiendo su nulo) | en main | `CLAUDE.md` |
| Hipótesis `H_S144_DIRECCION` y nota medida en D19 | resueltas y anotadas | `docs/HYPOTHESIS_LOG.md`, `docs/MIROVA_DIVERGENCES.md:2099` |
| Worktrees colgando (`verif-686` y el de `s143-cota-posicion`) | limpiados | `git worktree list` da sólo la raíz |
| NRT | **sano** | 3 runs verdes (17:00, 20:05, 23:54 UTC); los datos entran a las 03, 08 y 14 UTC, así que el silencio de la tarde es el patrón, no un pipeline zombie |
| Poller de TIF | **produciendo** | último commit 2026-09-20 02:52 UTC, "27 new MIROVA snapshot(s)" |
| Disco | **8,2 GB libres de 476** | bajó 0,7 GB: los TIF del conteo pesan 320 MB en `_dl_tif/` (ignorado por git) |

### Lo que quedó medido del fenómeno (todo fuera de la muestra del veredicto)

| qué | valor | ronda |
|---|---|---|
| el sitio donde `keep_peak` publica, contra otro punto de la misma banda, en una imagen de MIROVA que **no** lo eligió | **+0,0514** [+0,0264, +0,0766] | 7 |
| de eso, lo **permanente** (aparece igual en otras noches) | **+0,0441** (86 %) | 7 |
| lo que queda para **esa noche** | **+0,0073** [-0,0241, +0,0385] | 7 |
| medir en la imagen de la **propia** pasada, contra la cruzada | +0,1214 contra +0,0786 | 7 |
| coincidencia de radio con MIROVA: Lastarria contra el resto | **12 de 15** contra **1 de 19** | 2 y 3 |

**En una línea**: `keep_peak` publica un sitio tibio **estable** del terreno (A69), no un evento; y la
coincidencia de radio que sostuvo las pérdidas del A/B S143 es un fenómeno de Lastarria.

## b. Decisiones que espera Nicolás

| # | pregunta | opciones | recomendación |
|---|---|---|---|
| 1 | **D25 (fondo por vecinos) en VIIRS 750**: quedó pendiente de S143 y no se tocó | plan + flag apagado + su propio A/B; o esperar | **plan y flag ahora, A/B después**: las 5 pasadas de V750 que no reproducimos son D25 puro (`docs/audit_s143/PERDIDAS_V750.md`). **Toca `pipeline/`, así que necesita tag defensivo y tu confirmación explícita (A45)** |
| 2 | **Token de Earthdata: vence el 2026-10-03 07:18 UTC** | | renovarlo esta semana. Es credencial, lo haces tú. Quedan 13 días |
| 3 | ¿Abrir el frente de **etiquetado** que dejó el cierre? (cómo mostrar en el dashboard un sitio tibio estable lejos del cráter, marco A72) | abrirlo ahora / dejarlo en backlog | **backlog**: primero conviene ver si el operador lo reporta como molestia real; hoy no hay evidencia de que moleste |
| 4 | ¿Perseguir la separación relieve contra fuente permanente con **SWIR de alta resolución** (A77, Landsat-v1 o NHI-v1)? | proyecto aparte / no | **no por ahora**: es otro instrumento y otro repo; anotarlo como la salida natural si el frente de etiquetado se abre |
| 5 | Cron externo del NRT y correo a Coppola | | siguen como en S142 y S143: `docs/audit_s142/CRON_EXTERNO_PASO_A_PASO.md`, `docs/audit_s139/BORRADOR_CORREO_COPPOLA.md` |

## c. Lo aprendido

| lección | tipo | dónde vive |
|---|---|---|
| **Medir una detección contra un producto derivado del MISMO gránulo la infla por selección** (maldición del ganador): +0,1214 con la imagen propia contra +0,0786 con la de otra pasada de la misma noche | proyecto | `CLAUDE.md` **A109** |
| **Un control se valida midiendo su nulo, no razonándolo**: cuatro controles "obvios" fallaron seguidos (el reflejo mide textura; el temporal es ciego a las fuentes permanentes; el intercambio de roles atenúa el sesgo 5×; el estrato hermano contiene la señal) | **regla general del workspace** | `CLAUDE.md` **A110**; conviene subirla a la guía maestra de auditorías |
| Siete rondas de verificación con contexto limpio refutaron siete diseños, **todas con medición**. El verificador no es un trámite: acá fue el que produjo el resultado | **regla general del workspace** | este traspaso; la guía maestra ya lo dice y esta sesión es su caso más fuerte |
| Un pre-registro puede contestar la pregunta **sin correrse**, si sus controles miden sobre un estrato que comparte el objeto | proyecto | `docs/CIERRE_FRENTE_KEEP_PEAK_S144.md` |
| Los escapes dentro de un heredoc de Python volvieron a romper archivos (dos veces: un salto de línea literal y un `\n` que se expandió). **Para ediciones con secuencias de escape, usar el editor** | **workspace** | ya existía (S140 regla 4); van tres sesiones seguidas |
| Un `grep -c` que da cero **corta una cadena `&&`** y se lleva puesto el commit que venía detrás | **workspace** | este traspaso |
| Escribí la v2 del pre-registro, la mandé a verificar y la sobrescribí **sin commitearla**: las citas de línea de ese informe apuntan a un archivo que no existe | proyecto | declarado en el encabezado del pre-registro |

## d. Problemas abiertos e hipótesis

| qué | etiqueta |
|---|---|
| El sitio donde `keep_peak` publica destaca en el campo de MIROVA, y el 86 % de ese efecto es permanente | **CONFIRMADO** (ronda 7, sobre el estrato hermano) |
| La coincidencia de radio de las noches de S143 es un fenómeno de Lastarria | **CONFIRMADO** (rondas 2 y 3) |
| La radiancia sola no separa relieve tibio de fuente permanente | **CONFIRMADO** como límite de los 7 diseños; coincide con A83 |
| Correr la medida sobre la muestra del veredicto daría INCONCLUSO el 90 % de las veces con los umbrales pre-registrados | **CONFIRMADO** por simulación de la ronda 7 con la estructura real de noches |
| D25 cerraría las 5 pasadas de VIIRS 750 que no reproducimos | **SOSPECHA**: el mecanismo es el mismo (5 de 5), el tamaño no está medido |
| El sitio tibio que publicamos molesta al operador en el dashboard | **SOSPECHA**: nadie lo reportó; es la premisa del frente de etiquetado |

## e. Lo que ya está cerrado y no hay que rehacer

- **El frente `keep_peak` con dirección está cerrado.** `docs/CIERRE_FRENTE_KEEP_PEAK_S144.md` §4 lista
  qué no rehacer, y es la parte más valiosa: **no volver a proponer** el control reflejado (mide
  textura), el control temporal solo (ciego a permanentes), el intercambio de roles (atenúa 5×) ni el
  estrato hermano como nivel (contiene la señal). Los cuatro están refutados con medición.
- **No medir sobre el TIF de la propia pasada** (infla por selección, A109).
- **No reabrir la compatibilidad de radio fuera de Lastarria**: donde el centro de grilla está lejos del
  cráter, se cumple por aritmética.
- **El conteo de pasadas con TIF está versionado y reproducible**; sus 7 números exploratorios quedaron
  explicados (eran otra ventana y otra definición).
- **Los records del control del A/B S143 ya están a salvo**: no hay que volver a bajarlos antes del
  vencimiento.
- **A/B D22/D25 de junio-agosto**: corrido, verificado y cerrado en S143. No relanzar.

## f. Prompt para la próxima sesión

```
Retoma VRP Chile en S145. Trabaja en español de Chile (formas de tú, nunca voseo), sin guiones
largos ni medios, explicando como geólogo: fenómeno, mecanismo, números al final.

1. VERIFICA ANTES DE CREER:
   cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
   git fetch origin --prune && git pull --ff-only && git status -sb
   git rev-parse HEAD ; git ls-remote origin -h refs/heads/main      (deben coincidir; base efe644e30)
   gh pr list --state open
   gh api -i repos/MendozaVolcanic/VRP-chile | grep -i date           (hora del servidor, A86)
   python -m pytest tests/ -q -p no:cacheprovider | tail -1           (base: 1551 passed)
   NRT: gh run list --workflow nrt.yml -L 5   y   gh api "repos/MendozaVolcanic/VRP-chile/commits?per_page=5&path=data/mirova_equivalent"
   (los datos entran ~03, ~08 y ~14 UTC; silencio fuera de esas ventanas es normal, no zombie)

2. LEE EN ORDEN: CLAUDE.md del proyecto (A109 y A110 nuevas, A106 corregida) ·
   tasks/BLOQUE_ARRANQUE_S145.md · docs/CIERRE_FRENTE_KEEP_PEAK_S144.md (sobre todo §4, qué no
   rehacer) · docs/HYPOTHESIS_LOG.md entrada H_S144_DIRECCION.

3. TRABAJO EN ORDEN (lo que Nicolás decida en §b manda):
   a) D25 en VIIRS 750: plan + flag apagado, con tag defensivo y confirmación explícita (A45), y su
      propio A/B pre-registrado con verificador antes y después.
   b) Si Nicolás abre el frente de etiquetado (decisión 3): empezar por medir cuántos records por
      volcán y por noche muestran el sitio tibio lejos del cráter en el dashboard, con el predicado
      real corrido con node (A97), antes de proponer cualquier cambio de display (A72).

4. REGLAS DURAS: nada al pipeline ni a mirova_equivalent.yaml sin tag defensivo y confirmación (A45);
   criterio escrito antes de correr y verificador con contexto limpio antes y después; todo control
   lleva su nulo medido (A110); no medir contra un producto del mismo gránulo (A109); ningún número
   transcrito a mano (S91); esperar el CI con conclusión antes de mergear; correr la suite tras editar
   docs que un test lee; no hacer pull de mirova-tif-archive (17 GB); para ediciones con secuencias de
   escape usar el editor, no heredocs.

5. SI LA SESIÓN NO ALCANZA: deja el plan de D25 escrito y verificado aunque no se corra, y cierra con
   /cierre.
```
