# Bloque de arranque S137

> Cierre de S136 (2026-09-08 al 2026-09-10). Rama `main`, commit `f867161d1`, verificado contra el
> remoto. Suite **1288 passed**, 4 skipped, 2 xfailed.
>
> **El estado se fijó con trabajo en curso**: el cron NRT estaba `in_progress` y `sync-mirova-csv`
> `pending` al momento de escribir esto. Van a commitear sobre `data/`, no sobre nada de lo que esta
> sesión escribió, así que no invalidan el cierre, pero el `HEAD` de arriba habrá avanzado con
> commits automáticos cuando alguien lea esto.

## a. Todo en una pantalla

| qué | estado | evidencia |
|---|---|---|
| **Batería de conformidad del Apéndice A** (los 9 casos del autor) | **construida y corrida** | `experiments/_s136/apendice_a.yaml` + `conformidad_apendice.py` + 17 tests, run 34284386094 |
| Resultado con la fórmula (producción): **6/6 positivos conformes, 3/3 negativos falso positivo** | medido | `experiments/_s136/RESULTADO_APENDICE_A.md`, PR #619 |
| Coordenadas de los 8 volcanes extranjeros, del catálogo Smithsonian, con control por altitud | verificadas | `apendice_a.yaml`; 7 de 8 ya estaban en `VRP_GLOBAL_ARCHIVE_2025.csv` |
| **Flag `ENABLE_TESTS_23_PROSE_BRANCH`** (la conectiva `max`) | implementado, **OFF**, 8 tests | PR #621, tag `pre-s136-tests23-max` |
| Brazo de la prosa contra la batería: **2/6 positivos, 3/3 negativos** | **NO ADOPTAR** | run 34310522104, `VEREDICTO_CONECTIVA.md`, PR #622 |
| El piso C1 gobierna **100 % de MODIS y 99,9 % de VIIRS** | medido | `que_rama_manda.py`, PR #620 |
| Bug de la etiqueta far a summit: impacto neto **4 noches de 946**, 3 de ellas artefacto | medido | `impacto_neto.py`, PR #617 |
| Filtro de intensidad de Laiolo: **no es del pipeline NRT** | descartado, 2 vías | `FILTRO_INTENSIDAD_DESCARTADO.md`, PR #623 |
| Ruido de banda y remuestreo como palanca de detección | **descartados por aritmética** | `POR_QUE_EL_RUIDO_NO_MUEVE_LA_DETECCION.md`, PR #625 |
| Guiones largos en todo lo que escribí | limpiados (99 más 15) | PR #624 |
| Nada a medias, nada en rama sin mergear | verificado | 9 PRs (#617 a #625), todos mergeados |

Hay ramas remotas viejas de sesiones S105 y anteriores (`origin/claude/s105-*` y otras) sin limpiar.
No son de esta sesión y no estorban, pero alguien podría querer purgarlas.

## b. Decisiones que esperan a Nicolás

| # | pregunta | opciones | mi recomendación |
|---|---|---|---|
| 1 | El **"Test 1 integrado"** no está en el paper y sus parámetros salieron de otra parte de la Tabla 1. ¿Qué hace el artículo con eso? | (a) declararlo como divergencia; (b) corregirlo antes de redactar | **(a) declararlo.** Corregirlo es un cambio de detección con A/B propio, y el artículo no debería esperarlo. Declarar una divergencia medida es más fuerte que ocultarla. |
| 2 | El **A/B de B22 de S133** quedó NO ADOPTAR con dos razones, y una era "la detección casi no se movió y eso es sospechoso". Eso ya está explicado (ver §d). ¿Se re-evalúa? | (a) re-evaluar con criterio de **magnitud** contra MIROVA con decenas de pares; (b) dejarlo cerrado | **(a), pero sin apuro.** Su otra razón sigue en pie: con 2 pares no se decide nada. Un A/B nuevo, con ventana larga y criterio de magnitud, es trabajo de una sesión entera. |
| 3 | **D12** (FN MODIS) sigue esperando cierre formal, desde antes de esta sesión | (a) cerrarla; (b) dejarla abierta | **(a) cerrarla**, con la batería del apéndice como evidencia de que la sensibilidad no es el problema. |
| 4 | Las tres opciones que sobreviven sobre por qué el piso de 0,003 no sobre-detecta en manos de MIROVA (ver §d) | (a) perseguirlas; (b) parar el frente del artefacto | **(a)**, empezando por la lectura del paper y no por cómputo. Es donde esta sesión rindió mejor. |
| 5 | Guiones largos en el resto del repo (37 en `detection_context.py`, 71 en `profile.py`, más los de `docs/`) | (a) barrido completo; (b) sólo lo nuevo de aquí en adelante | **(b) por defecto, (a) si vas a proyectar o publicar esos documentos.** Un barrido del pipeline ensucia el diff de archivos críticos por un tema de estilo. |

## c. Lo aprendido

**Regla candidata A94, propia del proyecto.** *Un caso de referencia sólido justifica investigar un
mecanismo, no priorizarlo.* Propuse el bug de la etiqueta como "lo más rentable" apoyado en el caso
A6, que es real y con respaldo del autor del algoritmo, sin medir su tamaño agregado. Medido, rinde
**una noche útil sobre 946**. La prioridad se decide con el agregado, y el agregado había que
contarlo en **noches**, no en records. Es el error de unidades de A90 y A93 aplicado a la elección de
qué hacer, no a un número reportado.

**Regla general del workspace, no sólo de este proyecto.** *Verificar si el experimento ya se corrió,
antes de diseñarlo.* Iba a gastar un run de Actions midiendo el ruido de banda, y S133 lo había
medido con perfiles dedicados y veredicto escrito, con el mismo diagnóstico que yo iba a plantear. Es
A8 y A50, y hoy volvieron a pagar. El síntoma que delata el riesgo: cuando una hipótesis se siente
"obvia y nueva a la vez", conviene buscarla en el repo antes de diseñar nada.

**Trampa de medición, la doceava de la sesión.** El schema guarda la hora como `"2025-02-15 03:15"`,
con espacio, sin segundos y sin la T de ISO. Mi parseo usaba el formato ISO completo y **todo cayó en
"sin hora"**, dando cero pasadas nocturnas en los tres sensores. Lo delató el absurdo del número, no
una revisión del código, igual que los once anteriores.

**Trampa de medición, sobre el propio comando de verificación.** `grep -c` sobre el guion largo da
**falso positivo** en Git Bash sin locale UTF-8: el guion son tres bytes y grep compara byte a byte,
así que reportó 75 coincidencias en archivos que ya estaban limpios. Verificar con un lector que
decodifique UTF-8 (Python), o con `LC_ALL=en_US.UTF-8`.

**Estilo, incumplido toda la sesión.** La instrucción global prohíbe guiones largos y medios en todo
documento, informe o mensaje, incluidos los `.md` del repo. Los usé en los 11 documentos y en cada
mensaje. Corregido en lo escrito hoy (PR #624).

## d. Problemas abiertos e hipótesis

### CONFIRMADO (verificado con herramienta en esta sesión)

- **El piso C1 gobierna el umbral efectivo**: 100 % de los 11.907 records de MODIS, 99,9 % de VIIRS.
  El contraste estadístico nunca decide. Corolario que ahorra experimentos: mientras el piso mande,
  **todo lo que toque μ o σ es irrelevante**. Quedan fuera, sin necesidad de A/B, el pool sobre el que
  se calculan μ y σ, el retiro de los píxeles del Test 1 de ese pool, y ajustar C2.
- **La sensibilidad está bien o de más; el problema es la precisión.** 6 de 6 positivos del apéndice
  conformes y 3 de 3 negativos con falso positivo. Es la primera medida externa de sobre-detección
  que tiene el proyecto: el silencio de MIROVA puede ser alcance operacional (A54), pero que el autor
  publique que su algoritmo no detecta ahí, no.
- **El paper se contradice consigo mismo** entre la fórmula de los Tests 2 y 3 (`or`, verificado en el
  PDF, página 7) y su prosa tres líneas más abajo (C1 como mínimo a superar, y el análisis
  estadístico mandando en escenas variables). Las dos lecturas no pueden ser ciertas a la vez.
- **Ninguna de las dos lecturas reproduce a MIROVA.** Con `min` sobre-detectamos en los 3 negativos;
  con `max` perdemos 4 positivos porque apaga el contextual (327 píxeles a 0). MIROVA consigue 6/6 y
  3/3 a la vez.
- **MIROVA NRT no tiene piso de intensidad**: publica hasta 0,01 MW, con el 18,3 % de sus alertas bajo
  0,1 MW y distribución continua sin salto. Los mínimos por sensor siguen el orden de la resolución,
  así que son sensibilidad del instrumento.
- **MODIS tiene el dNTI 5,10 veces más rugoso que VIIRS 375 m**, con el píxel casi tres veces más
  grande. Controlado: cero pasadas diurnas en los tres sensores (el pipeline es night-only, ahora
  verificado y no supuesto), y los mismos cuatro volcanes dominan ambos sensores con el mismo patrón.
  La causa es el ruido de cuantización de la banda 21 en el extremo frío de su escala, ya
  diagnosticado y medido en S133.
- **Por qué la detección no se movió con B22**, que es el enigma que S133 dejó abierto: porque el
  umbral efectivo es el piso, y el piso no depende de σ. Para que el contraste pasara a gobernar, σ
  tendría que caer 11,7 veces; B22 ofrece 1,3 a 1,8 y remuestrear exigiría promediar unos 137
  píxeles, una ventana de más de 12 km sobre un ROI1 de 5 km. **Los dos quedan descartados como
  palanca de detección**, y B22 queda desacoplado como frente de **magnitud** (allí el efecto es
  grande: la magnitud cae a un décimo en Láscar y a un cuarto en Villarrica).
- **Tolbachik es el negativo más débil** del apéndice: su erupción empezó el 27 de noviembre de 2012,
  siete días después de la fecha del caso, y en fisuras del flanco, no en la cumbre. Prueba que no
  inventamos señal sobre un volcán en reposo, no la sensibilidad. El negativo fuerte es **Stromboli**,
  con actividad estromboliana permanente y nubes dispersas.

### SOSPECHA (no verificado en esta sesión)

- Que MIROVA implemente `max`. **No hay cita que lo diga.** Lo único probado es que las dos lecturas
  del paper son incompatibles, y que `max` puro no sirve.
- **Por qué el mismo piso de 0,003 no sobre-detecta en manos de MIROVA.** Tres opciones sobreviven,
  ninguna verificada: (1) su dNTI no está en nuestra escala **por definición** y no por ruido, o sea
  que lo normaliza de otro modo o lo calcula sobre otro objeto; (2) los filtros de píxeles
  inadecuados podrían quitar el difuso también de los **candidatos** a activo, y no sólo del pool de
  μ y σ como hacemos hoy; (3) el "resampling" del paper podría no ser un promediado, y entonces la
  aritmética de los 137 píxeles no le aplica. Las tres son de lectura de paper antes que de cómputo.
- Que las magnitudes con B22 sean las honestas y las de hoy vengan infladas por el ruido de la propia
  banda. Es la lectura de S133, plausible y no probada: su A/B no pudo medir paridad contra MIROVA
  (2 pares en Láscar, 0 en Villarrica).
- Que el desenlace del filtro contextual de S135 sea "sigue curando". En las 3 pasadas donde el filtro
  actúa, quitarlo lleva la magnitud a 2,23, fuera de la banda de paridad, con un movimiento de 1,91
  que excede el techo de 1,5 del propio criterio. Dirección clara, n insuficiente (3 contra el umbral
  de 4), así que formalmente sigue indeterminado.

## e. Cerrado en esta sesión, no rehacer

Nueve caminos descartados **con medición**, no con opinión. Reabrir cualquiera es trabajo perdido
salvo que aparezca evidencia nueva:

1. **Recalibrar el umbral fijo K1 para VIIRS.** Cerrado por dos vías: empíricamente no existe un valor
   que sirva, y el paper que adapta MIROVA a VIIRS dice que en detección no adapta nada, asignando ese
   umbral sólo a MODIS.
2. **Restaurar la unión de caminos de detección.** Es una divergencia literal real (el código
   construye la unión y la descarta en los tres sensores) pero no resuelve ninguna de las 12 noches
   perdidas: el término que importaría vale cero en todas.
3. **El bug de la etiqueta far a summit.** 4 noches de 946, y 3 son el artefacto de Chillán que S113
   ya dijo no destapar. Beneficio real: una noche.
4. **El discriminante geométrico** entre robo legítimo y artefacto (la distancia del hotspot robado).
   No separa: con corte a 10 km, Láscar tiene el 100 % de sus ocultos del lado "robo claro" y Llaima,
   que no tiene una sola noche confirmada, el 94 %.
5. **Retirar la intersección contextual.** Los datos apuntan a que sigue curando, no a que sobre. ⚠️ **S138: contradice a §d de este mismo archivo** («n insuficiente, 3 contra el umbral de 4, formalmente sigue indeterminado»). Manda §d: NO está cerrado (AUDIT_S138 C5).
6. **La conectiva de los Tests 2 y 3**, en sus **dos** lecturas.
7. **El filtro de intensidad de Laiolo.** No es del pipeline NRT (voz pasiva, sujeto "the VRP time
   series (Fig. 2)", resultado en el material suplementario) y el canal NRT no muestra piso alguno.
8. **El ruido de banda como palanca de detección.** Insuficiente por un factor de 6.
9. **Remuestrear como palanca de detección.** Exigiría promediar 137 píxeles.

Y de antes sigue vigente lo ya cerrado: D9 en sus dos caras, la cara far a summit de D11 por vía
espectral y de magnitud (con la rebaja de A82 para la vía geométrica), y los gates intra-radio de
S84 y S85.

## f. Prompt para la próxima sesión

```
Retomo VRP Chile en S137. Antes de creerle a nada, verifica el estado real:

  cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
  git fetch origin --prune && git pull --ff-only
  python -m pytest tests/ -q --no-header --tb=line | tail -3
  gh api repos/MendozaVolcanic/VRP-chile -i 2>/dev/null | grep -i "^date:"   # A86: la hora del servidor, no la tuya

Lee en este orden, y comprueba contra el codigo de hoy lo que cada uno afirme (una lista de
pendientes envejece hacia el falso positivo):
  1. tasks/BLOQUE_ARRANQUE_S137.md   <- este archivo, con las 5 decisiones que esperan a Nicolas
  2. CLAUDE.md del proyecto (reglas A1 a A93 y la tabla de skill triggers, que es VINCULANTE)
  3. docs/MISSION.md   <- las 3 preguntas, antes de tocar pipeline/
  4. docs/MIROVA_DIVERGENCES.md   <- que esta abierto y que NO reabrir
  5. experiments/_s136/   <- los 12 documentos de la sesion; empieza por RESULTADO_APENDICE_A.md
     y POR_QUE_EL_RUIDO_NO_MUEVE_LA_DETECCION.md, que son los que ordenan el frente

EL FRENTE, en el orden que recomiendo:

  1. Las tres opciones sobre por que el piso de 0,003 no sobre-detecta en manos de MIROVA
     (seccion d de este archivo). Son de LECTURA DE PAPER, no de computo, y ahi rindio mejor S136.
     La mas prometedora es la (2): hoy aplicamos los filtros de pixeles inadecuados al pool de mu y
     sigma; el paper podria estar quitando esos pixeles tambien de los CANDIDATOS a activo. Eso SI
     moveria la deteccion, porque no pasa por sigma.
     Verifica en el PDF, no en documentacion/sp426_5.txt: el texto extraido CORROMPE los operadores
     matematicos (el mayor-que aparece como punto), y por eso la contradiccion de la conectiva casi
     se leyo mal. Usa PyMuPDF linea por linea.

  2. La bateria del Apendice A ya existe y es el patron de medida de cualquier cambio de deteccion:
     gh workflow run probe-s136-conformidad-apendice.yml --ref main            # brazo actual
     gh workflow run probe-s136-conformidad-apendice.yml --ref main -f prosa=1 # brazo max
     Un cambio sirve si y solo si mantiene los 6 positivos Y cura los 3 negativos. Ubinas (-0,91) y
     Villarrica (-0,93) son el freno duro contra pasarse de estricto. Toma unos 40 min, es read-only
     y no toca produccion.
     OJO con una trampa que ya me costo un error: el artefacto trae DOS json, porque el runner hace
     checkout del repo y experiments/_s136/out_apendice/ esta commiteado. El brazo max escribe en
     out_apendice_prosa/. No uses glob para leerlo; nombra el directorio.

  3. Si Nicolas decide la #2 de las decisiones, el A/B de B22 con criterio de MAGNITUD contra MIROVA
     y ventana larga. Es una sesion entera. Lee docs/s133/AB_B22_VEREDICTO.md primero: su criterio
     pre-registrado ya fallo una vez, y el criterio no se mueve despues de ver el dato.

REGLAS DURAS QUE NO SE NEGOCIAN:
  - Tocar pipeline/process_*.py, store.py o mirova_equivalent.yaml exige tag defensivo Y
    confirmacion explicita de Nicolas (A45). El tag va ANTES del primer edit.
  - Antes de editar pipeline/, el test primero (TDD). Antes de declarar listo, verificacion con
    comando y output, no con impresion.
  - Ningun numero transcrito a mano: el script que lo persiste es la fuente (S91). Todo conteo lleva
    denominador y ventana temporal (A90), y sale de la definicion del conjunto que nombra (A93).
  - NADA de guiones largos ni medios en ningun documento, mensaje o commit. Verifica con Python, no
    con grep, que en Git Bash da falso positivo por comparar bytes.
  - Antes de disenar un experimento, busca si ya se corrio (A8/A50). En S136 casi gaste un run
    repitiendo el A/B de B22 de S133.
  - Espanol de Chile, formas de tu, nunca voseo. Fenomeno fisico primero, numeros al final.

SI LA SESION NO ALCANZA: cierra con /cierre. Lo que quede solo en la conversacion se pierde, y en
este workspace ya se perdieron instrumentos y ocho informes completos por esa via. Persiste cada
hallazgo cuando aparece, no al final.
```
