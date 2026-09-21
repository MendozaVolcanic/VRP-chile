# Bloque de arranque S150

> Estado de S149 (2026-09-21, hora del servidor al retomar 10:36 UTC). `main` en **`86121536c`** al
> reunir la evidencia (el commit de este bloque va encima). Tres PR mergeados (#737, #739, #740), todos
> con CI en verde **y con conclusión**; suite completa sobre `main` después del último merge, en árbol
> quieto: **1638 passed, 4 skipped, 2 xfailed**. Un PR abierto a propósito: **#738**.
> Ningún A/B ni agente quedó corriendo. No se despachó ningún workflow.

> ⚠️ **ACTUALIZACION de las 13:20 UTC, manda sobre lo de abajo donde choquen.** Nicolás confirmó las
> dos decisiones: (1) **#738 MERGEADO** (`0227dd7ac`; la caja llega al segundo pase, flag apagado;
> suite sobre `main` 1645 passed; worktree borrado); (2) pre-registro v2 **APROBADO**, con orden
> "mayo y marzo". **TRABAJO EN VUELO**: run **35599902448** (mayo, 11 volcanes, brazos B y F,
> despachado 12:30 UTC desde `0227dd7ac`) y run **35599941522** (mayo, gemelo de Láscar, en espera
> detrás del primero). **Marzo (Láscar; brazos B, J, K y gemelo) NO está despachado todavía**: GitHub
> guarda un solo run pendiente por grupo, así que se despacha cuando termine el primero, con
> `start=2026-03-01 end=2026-03-31 vols=["Lascar"]
> brazos=["_s146_ab_sin_test1","_s149_ab_sin_test1_b22","_s149_ab_sin_test1_b22_max","_s149_ab_sin_test1_gemelo"]
> control=_s149_ab_sin_test1_b22`. Las salidas quedan en ramas `s146-ab/<run>`. Además: **#742
> mergeado** (22 tests dejaban el perfil cambiado para el siguiente; arreglo en `tests/conftest.py`,
> y con eso el test con fuga de la sección d queda RESUELTO). Falta verificar que el primer NRT
> posterior a #738 salga verde.

## a. Todo en una pantalla

| qué | estado | evidencia |
|---|---|---|
| **El costo oculto de `max`** (las 50 publicaciones apagadas en noches con alerta) | **medido y verificado: no es un costo de fidelidad** | `docs/S149_COSTO_OCULTO_MAX.md` (#737). En 34 de las 50 la tabla `latest.php` de MIROVA lista esa misma pasada con VRP 0; 16 no tienen fila, 14 de ellas Suomi NPP. Donde MIROVA arbitra, control 49,5 % y F 18,3 % (n 109) |
| Por qué el evaluador no lo veía | explicado y arreglado | `banco_paridad.etiquetar` exige para el negativo limpio una noche sin alerta; la RUTINA en noche con alerta caía en `sin_info`. Estrato informativo nuevo en el evaluador (#739) |
| La premisa "fila RUTINA = MIROVA miró" | **verificada en la fuente** | código del scraper (repo Mirova-v1, `scraper.py`): RUTINA se asigna sólo a filas de `latest.php` con VRP 0; no fabrica filas. Se lee con `gh api repos/MendozaVolcanic/Mirova-v1/contents/scraper.py` |
| ¿Son calor real? | **en parte, medido por posición** | un tercio cae a un píxel del cúmulo de la pasada positiva de esa noche, otro tercio a más de 2 km. Supervivencia bajo `max` de lo que publica el control: negativos limpios 9 %, RUTINA en noche con alerta 37 %, positivas 99 %. Argumento para que el **experimental** conserve `min` |
| Los cúmulos que se mueven más de 500 m | medidos con dirección | 12 de 201 pares, 10 en Lastarria, que salta entre dos puntos fijos (5 hacia la posición típica de alerta, 5 alejándose): sin sesgo |
| **Cableado de la caja al segundo pase** | **PR #738, CI verde, SIN MERGEAR: espera tu "sí"** (A45) | las seis máscaras `is_summit` de `second_pass_adjacent` salen de `roi1_summit_mask(..., _roi1_mask)`. Flag apagado: inerte, probado bit a bit. Tag `pre-s149-caja-segundo-pase`. Trae G8 y `CLAUDE.md` remapeados |
| Evaluador del A/B | **arreglado** (#739) | C8b: selectividad a una cola con nulo medido (apagador al azar 3 de 200; C8 lo cumplía 200 de 200). Banda del control apagable por parámetro. No altera criterios ya congelados |
| **Pre-registro de la conectiva fuera de septiembre** | **v2 escrita y verificada, NO aprobada, NO despachada** (#740) | `experiments/_s149_prereg_invierno/PREREGISTRO_INVIERNO.md`. Mayo (11 volcanes, B y F), agosto 01 a 27 (ídem), marzo sólo Láscar (B, J con banda 22, K con banda 22 y `max`), más un gemelo de B por ventana como control de determinismo |
| Instrumentos para evaluar otra ventana | validados sobre septiembre | `armar_tabla.py`: 0 diferencias en 2.386 pasadas contra la tabla verificada en S148. `medir_predicciones.py`: reproduce lo publicado |
| Receta de la unión de septiembre | **escrita por primera vez** | B y F del run 35548121381, con Chaitén, Tupungatito y Villarrica del brazo B tomados del run 35558196104. `git archive <rama> <ruta>`: 17 MB |
| Cron del NRT | la sospecha de S148 queda **refutada** | hueco mediano de 4,8 h desde el 14 de septiembre, antes de cualquier A/B. Es la entrega a medias de GitHub conocida desde S133, no los A/B |

## b. Decisiones que espera Nicolás

| # | pregunta | recomendación |
|---|---|---|
| 1 | **Mergear #738** (la caja llega al segundo pase; flag apagado) | **sí**. Es inerte hoy y sin él D18 no se puede medir nunca. Después: repetir los brazos G y H de la caja con pre-registro actualizado (Q3 no tiene sustrato) |
| 2 | **Aprobar el pre-registro v2 y el orden mayo, agosto, marzo** | **sí, de a una ventana, mayo primero**. El candado `preregistro_aprobado` es tuyo: yo no lo pongo |
| 3 | El experimental se queda con `min` aunque la réplica pase a `max` | **sí**: el estrato intermedio (37 % de supervivencia) es justo la señal bajo el umbral de MIROVA que ese perfil quiere ver |
| 4 | Arrastre | token de Earthdata **vence el 2026-10-03**: rotarlo esta semana. Correo a Coppola: la conectiva sigue siendo LA pregunta (no toqué el borrador, lo excluiste en S141). Disco: 18 GB libres (97 %) |

## c. Lo aprendido

| lección | tipo | dónde vive |
|---|---|---|
| **Una etiqueta de "negativo limpio" definida por noche esconde los negativos de pasada de las noches activas**, que es donde un cambio de umbral más puede costar. El estrato se abre por dentro antes de llamarlo costo | del proyecto | `docs/S149_COSTO_OCULTO_MAX.md` §2; estrato nuevo en el evaluador |
| **Una premisa sobre un dato externo se verifica en el código que lo produce**, aunque ese código viva en otro repo: se lee por la API. El verificador la había dejado SIN VERIFICAR por no tenerlo en disco | general | ídem §6 |
| **Medir el sustrato por pasada única y en TODO el rango disponible**: conté doble (fila de tabla más fila de OCR) y miré sólo el invierno, y por eso afirmé que junio era el único sustrato MODIS cuando marzo tiene el doble. Lo cazó el verificador | refuerzo de S130 y A90 | pre-registro v2 §2 y §9 |
| **Un umbral fijo para una razón entre brazos lo puede cumplir el azar**: "la mitad o menos" se cumplía con un apagado parejo (0,47). El umbral se ata a su nulo | refuerzo de A110 y A116 | pre-registro v2 §5 |
| **`import evaluar` no es único en este repo**: un test pasaba solo y fallaba dentro de la suite porque otro test había cargado otro `evaluar.py`. Se carga por ruta con nombre propio | general | `tests/test_evaluador_selectividad_s149.py` |
| Un test que se salta no prueba nada: quité la red de `pytest.skip` que había puesto y completé el sintético | general | ídem |
| El verificador con contexto limpio volvió a pagarse: 6 hallazgos en el costo oculto y 10 en el pre-registro, uno de gravedad 5 | refuerzo de A93 | `docs/audit_s149/` |

## d. Problemas abiertos e hipótesis

| qué | etiqueta |
|---|---|
| Donde MIROVA arbitra, lo que `max` apaga en noches con alerta es sobre-publicación | **CONFIRMADO** (34 de 34, septiembre, NOAA-20 y NOAA-21) |
| Lo mismo vale para Suomi NPP | **SIN VERIFICAR**: MIROVA casi no lista SNPP (sin fila el 60 % de sus pasadas); por qué, tampoco se sabe |
| Un tercio de las apagadas es calor real | **SOSPECHA** apoyada en posición; el control de posición mide sobre todo distancia al cráter (correlación 0,996) |
| Cuál de los dos puntos de Lastarria es el campo fumarólico | **SIN VERIFICAR**: pide una coordenada de terreno |
| `max` generaliza fuera de septiembre | **SIN MEDIR**: es el pre-registro v2 |
| Villarrica y Chillán bajo `max` | **SIN PODER en ninguna ventana**: MIROVA casi no alerta ahí en tiempo casi real (1 a 9 y 0 a 4 pasadas por mes) |
| Test con fuga de estado: `tests/test_probe_3brazos_s136.py::test_el_brazo_actual_refleja_el_perfil_operacional` falla con `-k "profile or perfil or libro or guard"` y pasa solo y en la suite completa | **SIN INVESTIGAR** |

## e. Lo que ya está cerrado y no hay que rehacer

- No volver a mirar las 50 a nivel de píxel para la réplica: MIROVA ya las arbitró.
- No usar el evaluador de S146 para otra ventana: usar `armar_tabla.py` y `medir_predicciones.py`.
- No citar C8; la selectividad es C8b.
- No despachar el brazo MODIS en junio ni en agosto: el sustrato es marzo.
- No buscar poder estadístico para Villarrica o Chillán en la tabla de tiempo casi real de MIROVA.
- No atribuir los huecos del cron a los A/B.
- Sigue valiendo todo lo de S148 §e (`tasks/BLOQUE_ARRANQUE_S149.md`).

## f. Prompt para la próxima sesión

```
Retoma VRP Chile en S150. Trabaja en español de Chile (formas de tú, nunca voseo), sin guiones
largos ni medios, explicando como geólogo: fenómeno, mecanismo, números al final.

EL OBJETIVO, en palabras de Nicolás: máxima fidelidad a MIROVA en el perfil réplica, y más
detecciones, con posibles falsos positivos, en el experimental. Toda decisión de la réplica se
mide contra la base de datos de MIROVA (CSV, OSF, TIF), no se elige.

1. VERIFICA ANTES DE CREER:
   cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
   git fetch origin --prune && git pull --ff-only && git status -sb
   git rev-parse HEAD ; git ls-remote origin -h refs/heads/main        (deben coincidir)
   gh api -i repos/MendozaVolcanic/VRP-chile | grep -i date            (hora del servidor, A86)
   gh pr view 738 --json state,mergeStateStatus                        (¿sigue abierto?)
   python -m pytest tests/ -q -p no:cacheprovider | tail -1            (base S149: 1638 passed; árbol quieto)
   git worktree list                                                    (../VRP-Chile-s149-caja se borra tras mergear #738)
   El token de Earthdata vence el 2026-10-03.

2. LEE EN ORDEN: CLAUDE.md del proyecto · tasks/BLOQUE_ARRANQUE_S150.md ·
   docs/S149_COSTO_OCULTO_MAX.md · experiments/_s149_prereg_invierno/PREREGISTRO_INVIERNO.md ·
   docs/audit_s149/VERIFICADOR_PREREGISTRO_INVIERNO.md.

3. TRABAJO EN ORDEN (pregúntale a Nicolás por las decisiones 1 a 3 de la sección b antes de
   despachar nada o de mergear #738):
   a) Si aprueba #738: mergear (si main avanzó, rebasar y remapear G8 por contenido, A101), borrar el
      worktree, y reescribir el pre-registro de la caja (Q3 sin sustrato) antes de repetir G y H.
   b) Si aprueba el pre-registro v2: despachar SOLO la ventana de mayo (start 2026-05-01, end
      2026-05-31, brazos B y F con los 11 volcanes; y en un segundo despacho el gemelo sólo con
      Láscar), control _s146_ab_sin_test1. Contar cobertura antes de mirar nada (A108). Evaluar con
      armar_tabla.py y medir_predicciones.py contra _congelado/mayo. Verificador con contexto limpio
      sobre el resultado si la mejora supera 30 %.
   c) Diseñar cómo el experimental conserva `min` cuando la réplica pase a `max` (hoy los dos perfiles
      son idénticos salvo el directorio; ver docs/DISENO_SENSIBILIDAD_POR_ZONA_S147.md).
   d) Investigar el test con fuga de estado de la sección d.
   e) Arrastre de S147 y S146: brazo del Test 1 con el estadístico corregido para el experimental;
      centro de la caja; verificador del frente I, tope de Villarrica al operador,
      pc.classification al tablero.

4. REGLAS DURAS: nada a pipeline/process_*.py, store.py ni mirova_equivalent.yaml sin tag
   defensivo y confirmación explícita (A45); criterio escrito Y COMMITEADO antes de correr;
   verificador con contexto limpio antes de despachar un A/B y sobre toda mejora mayor que 30 %;
   todo control lleva su nulo medido, y un umbral sobre una razón entre brazos se ata a ese nulo;
   el sustrato se cuenta por pasada única y en todo el rango disponible; el recall que decide va por
   PASADA, y además se mira el estrato RUTINA en noche con alerta; ninguna ventana cruza el
   2026-08-28 23:00 UTC; ningún número transcrito a mano; una rebaja se propaga a los hijos en el
   mismo PR (A113); un flag tiene que llegar a todos sus consumidores (A118); todo workflow
   autentica SOLO por EARTHDATA_TOKEN; esperar el CI con conclusión antes de mergear; no correr la
   suite mientras se edita; nunca git reset --hard; git archive SIEMPRE con ruta; módulos de
   experiments/ se cargan por ruta en los tests; documentos largos con la herramienta de escritura.

5. SI LA SESION NO ALCANZA: deja cada frente con su cobertura declarada, rescata al repo
   cualquier instrumento que viva en el scratchpad, y cierra con /cierre.
```
