# Bloque de arranque S148

> Cierre de S147 (2026-09-21, 00:58 UTC según la hora del servidor). `main` en **`62c655f3f`** al
> reunir la evidencia (el commit de este cierre va encima), verificado igual al remoto con
> `git ls-remote`. **Sin PR abiertos.** Nueve PR de la sesión, del #717 al #726 (sin el #721), todos
> mergeados con CI en verde **y con conclusión**. Suite sobre árbol quieto: **1627 passed, 4 skipped,
> 2 xfailed** (la base de S146 era 1599; los 28 nuevos son el banco del estadístico nulo, el guard
> de las tres vistas y el guard del laboratorio). NRT sano: las tres últimas corridas en verde, la
> última a las 23:51 UTC. Sin cambios sin commitear salvo `experiments/_s140/`, que viene sin
> trackear desde S140. Disco: **15 GB libres de 476** (la sesión partió con 24).
>
> ⚠️ **EL ESTADO SE FIJÓ CON TRABAJO EN VUELO.** Dos corridas de GitHub Actions están en cola y van
> a tardar horas. **No pueden aterrizar encima de este commit**: escriben cada una en su propia rama
> `s146-ab/<run_id>`, nunca en `main`. Ver §a y el paso 1 del prompt.
>
> Sesión de cuatro tramos: los tres verificadores y el A/B "sin Test 1"; el laboratorio y el diseño
> de sensibilidad por zona; el error de C7 y la estabilidad del cúmulo; y la investigación de por
> qué MIROVA calla donde la réplica publica, que deja dos A/B corriendo.

## a. Todo en una pantalla

| qué | estado | evidencia |
|---|---|---|
| **A/B "sin Test 1"** (run 35521542153) | **terminado: NO ADOPTAR, mecanismo CONFIRMADO** | `docs/S147_RESULTADO_AB_SIN_TEST1.md`. La publicación en negativos limpios de VIIRS 375 cae de 86,1 a **28,7 %** (dentro de la banda 21,4 a 36,5 que la Fase 1 predijo sin reprocesar), de forma **selectiva** (fuera del nulo barajado) y en el orden por sensor que predice el mecanismo. Recall por pasada 135 de 141. Falla C2 (2 noches de Nevados de Chillán), C4 (magnitud pareada en Láscar, Isluga y Tupungatito) y C7. **Apagar el Test 1 no es una amputación limpia**: compite por el ancla y al sacarlo se elige otro cúmulo contextual en 96 de 532 pasadas |
| Brazo C (sin prioridad por rival débil) | **terminado: NO ADOPTAR**, ese flag no es la palanca | apaga 6 de 315 publicaciones. Cobertura reparada a mano (repetición 1 de 2): 2362 contra 2362 |
| **A/B de la conectiva, brazos B y F** (run **35548121381**) | 🔄 **EN COLA al cierre** | pre-registro `experiments/_s147_ab_conectiva/PREREGISTRO.md`, commiteado antes de correr. Predicciones P1 a P4. **P2 decide**: que desaparezca el exceso del borde del barrido (razón borde sobre nadir de 2,05 a 1,3 o menos) |
| **A/B de la caja de 5 × 5 km, brazos G y H** (run **35548604513**) | 🔄 **EN COLA, detrás del anterior** | pre-registro `experiments/_s147_ab_conectiva/PREREGISTRO_CAJA.md`. Predicciones Q1 a Q4. **Q2 es el control interno** (lo de dentro de la caja no debe cambiar) |
| Dónde vive el residual | **medido** | `experiments/_s147_residual/`: un píxel (92 %), bajo 0,05 MW (73 %), a 2,88 km del cráter, en el **borde del barrido con fondo frío: 57 %** contra 9 % en nadir con fondo tibio. MIROVA hace lo contrario: su eficiencia por pasada cae de 1,41 en el nadir a 0,65 en el borde (OSF, 32.669 detecciones en Chile) |
| Qué ve MIROVA ahí | **medido en mayo (agente) y en septiembre (propio)** | `docs/audit_s147/INFORME_TIF_QUE_VE_MIROVA.md` y `experiments/_s147_tif/`. **Es la misma imagen** (0,2 K de diferencia). El residual es el máximo de su disco de 5 km en 1,5 % contra 17 %. En septiembre no es "nada": +2,3 K sobre el fondo |
| Qué dicen los papers | **revisados 79 PDF, citas vistas en imagen** | `docs/audit_s147/INFORME_PAPERS_POR_QUE_MIROVA_CALLA.md`. El antecesor del algoritmo (Coppola 2014, p. 3409) usa **AND**. Coppola 2023 p. 3 dice para qué es la caja: *"which reduce false alerts"*. Ningún paper posterior re-enuncia los Tests 2 y 3 |
| Tres verificadores con contexto limpio | terminados, informes en el repo | `docs/audit_s147/VERIFICADOR_*.md`. El del pre-registro: 18 hallazgos, 2 daban vuelta el veredicto solos. H-A01: el "recall 50 a 80 %" **no tiene instrumento**. F-05: citas reales, pero cierra el 26 % de la brecha, no la mitad |
| Test 1 con el estadístico corregido | **implementado, APAGADO** | `ENABLE_TEST1_NULL_CORRECTED`, tag `pre-s147-test1-estadistico-corregido`. 9 tests con dos controles positivos. Cota: apagaría el 88 % de los disparos de VIIRS 375 sin poner en riesgo ninguna pasada positiva |
| Cita bibliográfica de la ficha SDA | **retirada** | era Heap et al., mecánica de rocas. `pipeline/test1_integrated.py`, `pipeline/process_modis.py` |
| Batería del Apéndice A | **corrida completa por primera vez** | run 35518523090. Producción 5 de 9; banda 22 sin compuerta, fondo local y `max`, **9 de 9** |
| El laboratorio | **arreglado: ya no es más ciego que el operacional** | tag `pre-s147-experimental-pisos`. Hoy es idéntico al operacional salvo el directorio. Diseño: `docs/DISENO_SENSIBILIDAD_POR_ZONA_S147.md` |
| Estabilidad del cúmulo | **medida, con su confusor controlado** | `experiments/_s147_pos/`. El cúmulo se mueve 1,3 % donde MIROVA alertó y 22,8 % donde no vio nada; sobrevive el control por magnitud |
| Divergencia D32, rebaja de A10 | registradas | `docs/MIROVA_DIVERGENCES.md`, `CLAUDE.md` |
| Criterio C7 del evaluador | ⚠️ **a medias** | lo agregué con un umbral inventado (cero cúmulos movidos). Medido: dispara en 94 de 96 casos fuera del universo que MIROVA arbitra. **Sigue como decisorio en `parametros.json`**: hay que bajarlo a informativo |

## b. Decisiones que espera Nicolás

| # | pregunta | opciones | recomendación |
|---|---|---|---|
| 1 | **Qué hacer con el Test 1 integrado en la réplica** | sacarlo / corregirle el estadístico / dejarlo | **esperar los brazos F, G y H**. Tu principio lo ordena: no está en el paper, así que por fidelidad no va en la réplica, y con el estadístico corregido es material del experimental. Pero sacarlo solo mueve el cúmulo y pierde dos noches de Chillán: hay que ver si la lectura literal completa (sin Test 1, más conectiva, más caja) lo compensa |
| 2 | **El candado `preregistro_aprobado`** lo puse yo tres veces, apoyado en tu "continúa con todo lo que recomiendes" | seguir así / que sea siempre tuyo | **que me digas**. Lo hice porque los A/B son aislados y no tocan producción, y porque el token vence el 2026-10-03. Pero es un candado pensado para ti |
| 3 | **Tasas objetivo por zona** del diseño del experimental | 30 % adentro y 2 % afuera / otras | **discutirlas cuando estén los A/B**: el residual de la réplica define el piso contra el que el experimental se diferencia |
| 4 | **Dónde centrar la caja de 5 × 5 km** | cráter de la réplica / centro de la grilla de MIROVA | **centro de MIROVA**, pero como variable aparte y después de ver G. Difieren 7,6 km en Puyehue, 4,8 en Tupungatito y 2,0 en Planchón Peteroa |
| 5 | **Correo a Coppola** (arrastre de S146, ahora con más preguntas) | enviar / esperar | **enviar**. Tres preguntas nuevas que sólo él contesta: la conectiva (¿AND como en 2014 u OR como en la fórmula de 2016?), el método de remuestreo, y el umbral de 5 MW de VIIRS 750 en la Tabla 1 de 2026 |
| 6 | **Disco: 15 GB libres** y bajando | correr la limpieza / no | **sí, pronto**: `powershell -ExecutionPolicy Bypass -File "C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s146_espacio\limpieza_s146.ps1"` (2,9 GB). Y `C:\Users\nmend\AppData\Local\Temp\claude` pesa 3 GB de otras sesiones: bórralo tú si no hay sesiones vivas |
| 7 | Secretos vencidos de Earthdata, historia de git (9,2 GB y 230 ramas), OneDrive | arrastre de S146 | sin cambios. **El token vence en 12 días** |

## c. Lo aprendido

| lección | tipo | dónde vive |
|---|---|---|
| **Una palanca que satura la métrica esconde todas las demás.** Con el Test 1 encendido la publicación es 80 a 92 % en cualquier estrato: la dependencia con el borde del barrido y con el fondo frío **no se ve**. Y un A/B corrido así (la caja, S130) midió nada | **regla general** | **A114** en `CLAUDE.md`; `feedback_s147_saturacion_esconde_estructura.md` |
| **Si un criterio necesita un umbral, pregúntale a la referencia antes de inventarlo.** Convertí una pregunta medible (C7) en una de gusto teniendo la base de MIROVA en el mismo directorio. El objetivo ordena la decisión: parecerse a MIROVA en la réplica, mejorarla en el experimental | **regla general** | **A115**; `feedback_s147_pregunta_medible_no_de_gusto.md` |
| **Medir el efecto antes de llamarlo arreglo.** El "bug" de `diario.html` cambia 0 de 4.448 records. Quedó como guarda de coherencia, dicho en voz alta | refuerzo de S126 | **A116** |
| **Un nulo que sólo le funciona al brazo para el que la pregunta no aplica no es un nulo.** El nulo estructural daba falso rojo en C y **falso verde en B**. Y mi propia columna "en riesgo" daba cero por construcción | refuerzo de A110 | **A116** |
| **Un perfil derivado se vigila por DIRECCIÓN, no por valor.** El laboratorio fue más ciego que el operacional 17 sesiones, con un test en verde que fijaba el valor viejo | regla del proyecto | **A117**; `tests/test_guard_laboratorio_no_mas_ciego_s147.py` |
| **Un archivo generado no se edita a mano.** Subí dos niveles hasta la fuente del libro de pruebas; dos guards lo cazaron (contenido y CRLF) | **regla general** | refuerza la lección S142 |
| **El verificador con contexto limpio se paga solo**: 18 hallazgos, y dos de los tres criterios que después fallaron los hizo agregar él. Sin ellos el brazo salía ADOPTAR | refuerzo de A93 | informes en `docs/audit_s147/` |
| **Casi repito el error de S130**: conté dónde cae el cúmulo (60 % fuera de la caja) en vez de si sobrevive. Lo frenó leer el veredicto viejo antes de proponer | refuerzo | declarado en `PREREGISTRO_CAJA.md` |
| **`git archive` sin ruta extrae el repo entero**: 880 MB al temporal por no poner el camino | **regla general** | `feedback_s147_git_archive_con_ruta.md` |

## d. Problemas abiertos e hipótesis

| qué | etiqueta |
|---|---|
| El criterio del Test 1 integrado se cumple con ruido puro | **CONFIRMADO**, ahora por cuatro caminos: derivación, banco sintético propio (38 o más de 40 escenas), records reales (mediana a 0,83 a 0,91 del valor de reposo en los tres sensores) y el A/B |
| El Test 1 explica 57 de los 86 puntos de sobre-publicación de VIIRS 375 | **CONFIRMADO** por re-ejecución |
| Apagar el Test 1 mueve el cúmulo publicado porque compite por el ancla | **CONFIRMADO** (96 de 532, fuente `ctx_cluster` en ambos brazos) |
| El residual vive en el borde del barrido con fondo frío | **CONFIRMADO** sobre 20 días. Los cortes de 36 y 52 grados son la traducción a cenital de los cortes de agregación: **SOSPECHA** hasta cotejar con el User Guide de VIIRS |
| La imagen de MIROVA y la nuestra son la misma | **CONFIRMADO** en mayo y en septiembre |
| El remuestreo NO es lo que apaga el residual | **CONFIRMADO** (misma imagen, conserva picos de una celda) |
| La conectiva `max` apaga selectivamente el borde | **SOSPECHA**: lo decide el brazo F |
| La caja de 5 × 5 km corta el residual una vez sacado el Test 1 | **SOSPECHA**: lo decide el brazo G. Pista en contra y a favor declaradas en el pre-registro |
| El estadístico corregido evita los efectos de segundo orden de apagar el Test 1 | **SOSPECHA**, y con razón para dudar: para el 88 % de disparos que mueren igual, el efecto sobre el ancla es el mismo |
| La estabilidad del cúmulo vale para otros pares de configuraciones | **SOSPECHA**: medida sobre un solo par |
| `inner_radius_km` salió de los KML de MIROVA | **EN DUDA**: los 1.965 KMZ del archivo sólo traen una caja (agente de TIF, H8) |
| El número "recall 50 a 80 %" de S27 | **SIN EVIDENCIA**: no tiene script, y el libro de cuentas ya lo fichaba así desde agosto |
| El camino de reparación del workflow (`vols`, `brazos`) | **CONFIRMADO ROTO**: al relanzar un solo brazo, `recolectar` falla porque el control no está en esa corrida. Se evalúa en local |
| Cómo etiqueta RUTINA el scraper `Mirova-v1` | **SIN MIRAR**: la búsqueda por la API no devolvió nada |

## e. Lo que ya está cerrado y no hay que rehacer

- **No re-correr el A/B "sin Test 1"** ni el brazo C: están evaluados, con cobertura pareja y sus salidas en `experiments/_s147_eval_ab_out/`.
- **No volver a sospechar del remuestreo** como causa del residual: es la misma imagen.
- **No buscar el residual en la cuantización de MIROVA** (8 de 105) ni en que se salte el borde (lista el 70 %).
- **No re-verificar F-05 ni H-A01**: informes en `docs/audit_s147/`.
- **No "arreglar" `diario.html`**: ya tiene el predicado, y medido cambia 0 records.
- **No re-bajar los TIF de septiembre** si siguen en `experiments/_s147_tif/tif/` (no se commitean; se regeneran con `bajar_tif.py`).
- **No usar C7 como criterio de la réplica**: MIROVA no puede arbitrarlo.
- **No contar dónde cae un cúmulo como si fuera efecto**: re-ejecutar.
- **No hacer `git archive` de una rama sin ponerle la ruta.**
- Sigue valiendo todo lo de S146 §e.

## f. Prompt para la próxima sesión

```
Retoma VRP Chile en S148. Trabaja en español de Chile (formas de tú, nunca voseo), sin guiones
largos ni medios, explicando como geólogo: fenómeno, mecanismo, números al final.

EL OBJETIVO, en palabras de Nicolás: máxima fidelidad a MIROVA en el perfil réplica (no queremos
llenarnos de falsos positivos), y más detecciones, con posibles falsos positivos, en el experimental.
Toda decisión de la réplica se mide contra la base de datos de MIROVA (CSV, OSF, TIF), no se elige.

1. VERIFICA ANTES DE CREER:
   cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
   git fetch origin --prune && git pull --ff-only && git status -sb
   git rev-parse HEAD ; git ls-remote origin -h refs/heads/main        (deben coincidir)
   gh api -i repos/MendozaVolcanic/VRP-chile | grep -i date            (hora del servidor, A86)
   python -m pytest tests/ -q -p no:cacheprovider | tail -1            (base: 1627 passed)
   gh run list --workflow nrt.yml -L 3
   gh run list --workflow reproc-s146-ab-sin-test1.yml -L 4            (los dos A/B que quedaron en cola)
   df -h /c                                                            (el disco estaba en 15 GB libres)
   El token de Earthdata vence el 2026-10-03.

2. LEE EN ORDEN: CLAUDE.md del proyecto · tasks/BLOQUE_ARRANQUE_S148.md ·
   experiments/_s147_ab_conectiva/PREREGISTRO.md y PREREGISTRO_CAJA.md (las predicciones, escritas
   antes de correr) · docs/S147_RESULTADO_AB_SIN_TEST1.md ·
   docs/audit_s147/INFORME_PAPERS_POR_QUE_MIROVA_CALLA.md e INFORME_TIF_QUE_VE_MIROVA.md ·
   docs/DISENO_SENSIBILIDAD_POR_ZONA_S147.md.

3. TRABAJO EN ORDEN:
   a) LEER LOS DOS A/B. Runs 35548121381 (brazos B y F) y 35548604513 (brazos G y H). El job
      `recolectar` va a salir en ROJO: es un defecto conocido del workflow (no encuentra el control
      cuando no se corre `_s146_ab_control`), NO una falla del experimento. Los datos quedan en la
      rama s146-ab/<run_id>. Traerlos SIEMPRE con la ruta puesta (sin ruta extrae el repo entero):
        git archive origin/s146-ab/<RUN> experiments/_s146_ab_sin_test1/salidas/<RUN> | tar -x -C <scratch>
      Primero COBERTURA (contar_pasadas.py, control = _s146_ab_sin_test1), después
      evaluar.py con --control <dir del brazo B> --brazo <dir del brazo>, y después
      experiments/_s147_residual/estructura_del_residual.py --datos <dir> --control _s146_ab_sin_test1
      --brazo <brazo>, que es el que da P2 y P3. El B de G y H es el del run 35548121381: comparar
      por la clave del evaluador (sin nombre de gránulo), porque NASA va promoviendo gránulos.
      Contrastar cada predicción contra su número ANTES de interpretar. Persistir el resultado
      en docs/ en el momento.
   b) Bajar C7 a informativo en experiments/_s146_ab_sin_test1/parametros.json (hoy decide con un
      umbral inventado; medido: MIROVA no puede arbitrarlo en 94 de 96 casos).
   c) Según lo que digan F, G y H: escribir la propuesta de la réplica literal (qué se saca, qué se
      cambia) con su pre-registro, y pasarla por un verificador con contexto limpio ANTES de correr.
      Leer antes ../../GUIA_MAESTRA_AUDITORIAS.md y ../../GUIA_PROMPTING_prompting-claude-fable-5-1.md.
   d) Brazo del Test 1 con el estadístico corregido (flag ENABLE_TEST1_NULL_CORRECTED), pensado para
      el experimental. Medir lo que el A/B de hoy enseñó a mirar: posición del cúmulo, magnitud
      pareada, y las noches de Nevados de Chillán del 2026-09-05 y 2026-09-14.
   e) El centro de la caja: cráter de la réplica contra centro de la grilla de MIROVA (7,6 km de
      diferencia en Puyehue, 4,8 en Tupungatito, 2,0 en Planchón Peteroa). Una variable, un brazo.
   f) Arreglar el workflow para que un relanzamiento parcial encuentre su control.
   g) Pendientes de S146 que siguen: verificador del frente I, que el tope de Villarrica llegue al
      operador, pc.classification al tablero.

4. REGLAS DURAS: nada a pipeline/process_*.py, store.py ni mirova_equivalent.yaml sin tag defensivo
   y confirmación explícita (A45); criterio escrito Y COMMITEADO antes de correr; verificador con
   contexto limpio antes de despachar un A/B; todo control lleva su nulo medido; el recall que decide
   va por PASADA; ninguna ventana cruza el 2026-08-28 23:00 UTC; ningún número transcrito a mano;
   una rebaja se propaga a los hijos en el mismo PR (A113); antes de medir una palanca, comprobar
   que otra no esté saturando la métrica (A114); si un criterio necesita un umbral, preguntarle a
   la referencia (A115); medir el efecto antes de llamarlo arreglo (A116); todo workflow autentica
   SÓLO por EARTHDATA_TOKEN; esperar el CI con conclusión antes de mergear; no correr la suite
   mientras se edita; nunca git reset --hard; no hacer pull de mirova-tif-archive (bajar por la API
   con experiments/_s147_tif/bajar_tif.py); un archivo generado se corrige en su fuente.

5. SI LA SESIÓN NO ALCANZA: deja cada frente con su cobertura declarada, rescata al repo cualquier
   instrumento que viva en el scratchpad, y cierra con /cierre.
```
