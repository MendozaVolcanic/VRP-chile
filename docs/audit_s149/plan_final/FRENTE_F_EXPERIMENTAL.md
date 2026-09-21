# Frente F de la auditoría S149: el perfil experimental

> Auditor del frente F. Hora del servidor al cerrar: 2026-09-21 18:08 UTC (`gh api -i repos/MendozaVolcanic/VRP-chile`, cabecera `Date`).
> Sólo lectura sobre el repo. Scripts y salidas en
> `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s149_audit\frente_f\`.
> Leí enteros `COMUN_AUDITORES.md`, `PREAMBULO-AUDITOR.md` y `PLAN_AUDITORIA_S149.md` antes de empezar.
> Cada afirmación lleva archivo:línea leído hoy o la salida de un script mío; lo demás va rotulado SOSPECHA o SIN VERIFICAR.

## 0. En una pantalla

El fenómeno primero. Un volcán con un foco chico (lago de lava, campo fumarólico, domo tibio) entrega una señal que a 375 m está al borde de lo resoluble. MIROVA publica sólo la parte de esa señal que cruza su umbral; el resto es calor real que queda bajo la línea. La mitad del objetivo del dueño que le toca al experimental es mostrar esa franja, aceptando falsos positivos.

Hoy esa mitad **no existe como producto**:

1. El perfil `experimental` resuelve **idéntico** al operacional: de 144 constantes sólo cambian el nombre y el directorio de salida.
2. **No corre**: salió del cron en S141 y, si se despacha a mano, su salida se pierde porque el paso de commit agrega otro directorio.
3. **No tiene datos**: `data/experimental_v2/` no existe ni en disco ni en el remoto. La serie vieja `data/experimental/` está congelada en el 2026-08-25 y es de una configuración que el propio perfil declara ruido.
4. **El tablero del laboratorio muestra un aviso de archivo faltante** para los volcanes, siempre.
5. **Hereda del operacional por `extends`**: el día que la réplica adopte `max` (o apague el Test 1), el experimental lo adopta en silencio, y el guard que lo vigila sigue verde porque sólo mira los pisos de magnitud. Es el mismo defecto de A117 por otra puerta, y es el hallazgo más urgente de este frente.
6. **Las varas de validación que el diseño nombra no existen como datos**, salvo una (NHI-v1), y esa ya se probó en S131 con resultado débil que el diseño de S147 no recoge.

## 1. Qué existe hoy

### 1.1 Los perfiles, resueltos como los lee el código

Script: `experiments/_s149_audit/frente_f/diff_perfiles.py`, salida `salida_diff_perfiles.txt`. Resuelve cada perfil en un subproceso con `VRP_PROFILE` y compara todas las constantes públicas en mayúsculas de `pipeline.profile`. Instrumento: (1) si los perfiles difirieran lo vería, porque compara las 144 constantes; (2) control positivo: el brazo `_s147_ab_sin_test1_max` muestra sus dos flags conocidos (`ENABLE_TEST1_PATH` y `ENABLE_TESTS_23_PROSE_BRANCH`), así que el instrumento no está muerto.

| perfil | constantes | difieren del operacional | cuáles |
|---|---|---|---|
| `experimental` | 144 | 2 | `DATA_SUBDIR` (`experimental_v2`), `PROFILE_NAME` |
| `experimental_ndc_focus` | 144 | 4 | lo anterior más `SENSOR_MODIS=False`, `SENSOR_VIIRS_750=False` |
| `experimental_lowT` | 144 | 3 | lo anterior más `ENABLE_VRPTIR_AVENI=True` |
| control: `_s147_ab_sin_test1_max` | 144 | 4 | `ENABLE_TEST1_PATH=False`, `ENABLE_TESTS_23_PROSE_BRANCH=True` |

Una diferencia de comportamiento que las constantes no muestran: sin `--volcano`, el perfil operacional se filtra a los 11 Tier A y cualquier otro perfil procesa los 45 (`scripts/run_pipeline.py:459`). El NRT siempre pasa `--volcano` (`.github/workflows/nrt.yml:222-223`), así que en la práctica no actúa. Es la única rama del código que depende de `PROFILE_NAME` (`grep -rn PROFILE_NAME pipeline/*.py scripts/run_pipeline.py`: 2 usos fuera de `profile.py`, el otro es un `print`).

`experimental_lowT` enciende un flag que, según su propia cabecera, el pipeline no consume todavía (`pipeline/profiles/experimental_lowT.yaml:19-23`). Si eso sigue siendo cierto hoy queda SIN VERIFICAR (no tracé `ENABLE_VRPTIR_AVENI` en `process_viirs.py`; CLAUDE.md A89 cita un import de `vrp_tir_mw` que corre en cada gránulo, así que la cabecera puede estar vieja).

### 1.2 Si corre

- El cron no lo corre: el paso "experimental profile" sólo se ejecuta con despacho manual `profile == 'experimental'` (`.github/workflows/nrt.yml:192-200`, decisión de Nicolás del 2026-09-14).
- Si se despacha, escribe en `data/experimental_v2/` y **el paso de commit agrega `data/experimental/`** (`.github/workflows/nrt.yml:337`). La salida se pierde. El propio workflow lo dice en su comentario (líneas 194 a 196).
- La opción de despacho `experimental_ndc_focus` existe en el menú (`nrt.yml:27`) y **ningún paso la atiende** (única aparición del nombre en el archivo). Elegirla corre un job que no procesa nada. Su serie se genera por `reproc-s124-ndc-focus.yml`.

### 1.3 Qué datos hay

Script: `experiments/_s149_audit/frente_f/frescura_datos.py`, salida `salida_frescura.txt`. Control positivo: `data/mirova_equivalent` da último record 2026-09-21 en los 11 Tier A. Denominador: todos los json del directorio; ventana: la serie completa.

| directorio | estado | último record |
|---|---|---|
| `data/mirova_equivalent/` | vivo | 2026-09-21 06:06 a 08:50 UTC |
| `data/experimental/` | 45 archivos, **congelado**; configuración vieja de S15 que `experimental.yaml:3-21` declara ruido | 2026-08-25 06:12 (remoto: último commit al directorio 2026-08-25T15:59Z) |
| `data/experimental_v2/` | **NO EXISTE** en disco ni en el remoto (`gh api repos/MendozaVolcanic/VRP-chile/contents/data` lista sólo `experimental` y `experimental_ndc_focus`) | sin dato |
| `data/experimental_ndc_focus/` | 1 archivo (Nevados de Chillán), 518 records | 2026-08-27 06:54 |
| `data/experimental_lowT/` | NO EXISTE | sin dato |

### 1.4 Qué ve el operador

- `frontend/index.html:411` enlaza "Laboratorio" hacia `frontend/experimental/`.
- `frontend/experimental/index.html:400` pide `data/experimental_v2/<volcán>.json`, que no existe, y muestra el aviso "No se pudo cargar la serie experimental... falta el archivo, no porque no haya actividad" (`frontend/experimental/index.html:431-437`). El aviso es honesto; la vista está vacía.
- `frontend/experimental/beyond-mirova.html` no consume el perfil experimental: lee `data/mirova_equivalent/` (línea 231) y un A/B viejo (`data/_s99_test1_eq16/`, línea 391). Su insignia dice "la detección NO cambia" (línea 53).
- `diario.html`, `mosaico.html` y `comparacion.html` leen sólo `mirova_equivalent` (líneas 180, 471, 195). No hay selector de perfil en ninguna vista.

## 2. Qué está diseñado y no hecho

| pieza | dónde | estado verificado hoy |
|---|---|---|
| Sensibilidad por zona (umbral permisivo dentro del `inner_radius_km`, estricto afuera; tasas objetivo 30 % y 2 % como punto de partida) | `docs/DISENO_SENSIBILIDAD_POR_ZONA_S147.md` | Pasos 0 y 1 de su tabla (§10) hechos; pasos 2 a 6 sin empezar. Las tasas esperan decisión del dueño (§6, §11). No hay flag en `pipeline/profile.py` para esto |
| Test 1 con el estadístico corregido | `docs/S147_TEST1_ESTADISTICO_CORREGIDO.md` §5; `pipeline/profile.py:301` | Implementado, apagado por omisión. "Pensado para el experimental" (memoria `project_s147_estado.md:50`). Ningún perfil experimental lo enciende; ningún A/B lo ha corrido (arrastre en `BLOQUE_ARRANQUE_S150.md:139`) |
| El experimental conserva `min` cuando la réplica pase a `max` | `tasks/BLOQUE_ARRANQUE_S150.md:66` (decisión 3, recomendación "sí") y `:136-137` | Sin diseñar. Hoy no hay nada que lo garantice (hallazgo F-1) |
| Display de tres estados (equivalente MIROVA, laboratorio zona del cráter, laboratorio fuera) | diseño §8 | Sin empezar |
| Ficha de transparencia del laboratorio si se publica | diseño §8 | `docs/FICHA_SDA_VRP_CHILE.md` no menciona "experimental" ni "laboratorio" (dos búsquedas, por esas palabras y por "perfil/profile": las únicas coincidencias hablan de perfilar personas). Frente G |
| Mecanismo de override por volcán para un perfil | `scripts/run_pipeline.py:134-145` (`VOLCANO_OVERRIDES`) | Existe y sirve: permite al laboratorio cambiar geometría sin tocar `volcanoes.yaml` |

**Conocimiento deformado al resumirlo (eje de esta auditoría).** La definición del dueño de qué va al experimental es ancha: "SWIR de alta resolución para focos sub-píxel, índices nuevos, TIR alternativo, MOUNTS, InSAR" (memoria `feedback_s143_primero_igualar_a_mirova.md`, sección "How to apply"). El diseño de S147 y los bloques S148 a S150 la redujeron a **un solo eje**: el umbral por zona. Y el hecho nuevo de S149 (la franja que `max` apaga) agrega un segundo eje que todavía no tiene diseño. El experimental que pide el dueño es "todo lo que mejora la detección y MIROVA no tiene"; el que está escrito es "un umbral más bajo cerca del cráter".

## 3. Con qué se valida: inventario de varas independientes

MIROVA no puede ser la vara (A115; diseño §7). El diseño nombra tres fuentes. Estado real de cada una y de las demás que el ecosistema menciona:

| fuente | ¿existe como dato legible por máquina? | qué cubre, desde cuándo | límite medido |
|---|---|---|---|
| **Actividad conocida de OVDAS (RAV, cambios de alerta técnica)** | **NO.** Dos búsquedas (`RAV/REAV` y `rnvv/nivel_alerta/alerta técnica/episodios conocidos`, fuera de `data/`) dan sólo menciones en prosa: `docs/BASELINE_LITERATURA_TIER_A_S77.md:18,174` (URL `rnvv.sernageomin.cl`), el diseño, la ficha. `find -iname "*rav*"` y `"*ovdas*"` a 3 niveles: nada útil. La carpeta hermana `Volcanologia/OVDAS/` contiene turnos, iconos y postulaciones, no reportes | nada | Es la vara "que importa operacionalmente" (diseño §7.1) y **no hay ni una tabla de episodios** |
| **NHI-v1** (SWIR 20 a 30 m, Sentinel-2 y Landsat, repo hermano público) | **SÍ.** `docs/nhi_data/<Volcán>/nhi_timeseries.json` por volcán, cron diario, último push 2026-09-21T17:38Z. Script `cobertura_nhi.py`, salida `salida_cobertura_nhi.txt` | 10 de 11 Tier A, desde el 2026-02-04/13 hasta el 2026-09-16/19; 53 a 109 escenas por volcán; escenas con píxeles calientes: Láscar 30, Villarrica 27, Llaima 26, Planchón 21, Copahue 20, Isluga 13, Chillán 12, Tupungatito 9, Chaitén 6, Cordón Caulle 4 | **Lastarria no está** (HTTP 404 y ausente del listado del directorio): el campo fumarólico Lazufre no tiene vara SWIR. Sólo Láscar está validado contra el NHI Tool original; el repo declara falsos positivos grandes y planea deprecar `docs/nhi_data/` en favor de la variante TOA (`SESSION_STATUS.md` del repo, líneas 60 a 78 y 138). Diurno, cadencia de días |
| **Piloto NHI contra nuestras detecciones (S131)** | **SÍ, ya hecho y sin puntero.** `docs/s131/agentes/OTRO_SENSOR.md`; script y salidas en `experiments/_s131_audit/otro_sensor/` (verifiqué que existen los 4 elementos) | 5 volcanes, 2026-02-06 a 2026-09-02, 714 noches "detección sin MIROVA" | Resultado del piloto: en **4 de 5 volcanes la tasa de alerta NHI en esas noches es igual a la tasa basal de NHI del volcán** (20 a 49 %); sólo Nevados de Chillán sube (25 % contra 12 %). Veredicto de S131: no sirve como juez automático, sí como panel de contexto. **Ni el diseño de S147 ni los bloques S147 a S150 ni `CLAUDE.md` lo citan** (`grep OTRO_SENSOR`: cero en esos archivos). No re-corrí el piloto: los números son de S131, leídos hoy |
| **Landsat-v1** (repo hermano público, vivo, push 2026-09-21T14:43Z) | **No como detección.** Publica imágenes (PNG, GIF RGB/SWIR/THERMAL) e índices de fechas; su README no describe ninguna salida de píxeles calientes. S131 anotó un `niveles_landsat.json` categórico "no verificado a fondo"; yo tampoco lo verifiqué | 43 volcanes | Sirve para mirar a ojo un caso, no para medir una tasa |
| **Columnas NPixHot de MIROVA OLI/MSI** | **NO.** Ningún repo las persiste. `docs/AUDIT_S134.md:87`: "P7 scraper OLI/MSI NPixHot, ABIERTO, 0 código". El CSV del scraper no trae esa columna (cabecera de `data/mirova_reference/mirova_v1_snapshot/registro_vrp_consolidado.csv` leída hoy) | sólo visita manual por navegador (A77) | Sería el juez de más autoridad (mismo grupo MIROVA, alta resolución). Pendiente desde S131 |
| **AVTOD, Reath et al. 2019** (ASTER 90 m) | SÍ, `data/mirova_reference/avtod_reath2019_chile.csv` (1.146 bytes) | un valor máximo por volcán, 2000 a 2017 | Estático e histórico: ordena volcanes por clase térmica, no valida una noche de 2026 |
| **Categoría b de A54** (lago de lava de Villarrica, Lazufre en Lastarria, lacolito del Cordón Caulle, cráter El Agrio) | **Sólo como prosa.** `volcanoes.yaml` las menciona en comentarios y `notes` (líneas 17, 35, 66, 173, 181, 645); no hay coordenadas ni polígonos de esos rasgos como dato. `docs/S149_COSTO_OCULTO_MAX.md:116-117` lo confirma para Lastarria: "pide una coordenada de terreno que no tengo" | 4 rasgos nombrados | Sin coordenadas de terreno no se puede decir si un cúmulo cae "sobre el rasgo" |
| `data/clasificacion_referencia/` | existe (11 archivos) pero **no es independiente**: sus valores son `mirova_confirmed` y `mirova_same_night` | septiembre de 2026 | Es MIROVA otra vez |
| **Persistencia espacial propia** (diseño §7.3) | derivable de nuestra serie; sin instrumento escrito | toda la serie | S149 ya midió el límite: la posición "no distingue calor de esta noche de lugar donde siempre cae algo" (`S149_COSTO_OCULTO_MAX.md:67-71`, correlación 0,996 con la distancia al cráter) |

Lectura: de las tres varas del diseño, la primera no existe, la segunda existe pero ya mostró poco poder como juez binario y no cubre Lastarria, y la tercera tiene un límite de instrumento ya medido. **El experimental no tiene hoy contra qué declararse bueno o malo.** Eso no impide publicarlo (el dueño acepta falsos positivos); sí impide afirmar que "la sensibilidad ganada es real".

## 4. Hallazgos, por gravedad

### F-1. El experimental hereda la conectiva y el Test 1 de la réplica: al adoptar `max`, la señal débil desaparece de los dos perfiles y ningún guard lo nota
- ARCHIVO:LÍNEA: `pipeline/profiles/experimental.yaml:23` (`extends: mirova_equivalent`) y `:59-61` (lo único que sobrescribe son los pisos); `pipeline/profile.py:51-62` (herencia por mezcla profunda); `tests/test_guard_laboratorio_no_mas_ciego_s147.py` cabecera ("NO cubre otros parámetros") y `PISOS` en la línea 44. SCRIPT: `salida_diff_perfiles.txt` (2 diferencias de 144).
- QUÉ PASA: la franja de calor real bajo el umbral de MIROVA (medido en S149: bajo `max` sobrevive el 9 % de los negativos limpios, el 37 % de las RUTINA en noche con alerta y el 99 % de las positivas; un tercio de las apagadas cae sobre el foco de esa noche) tiene que quedar visible en el experimental. Pero el experimental no fija ni `enable_tests_23_prose_branch` ni `enable_test1_path`: los hereda. El cambio de una línea en `mirova_equivalent.yaml` los cambia en los dos perfiles a la vez.
- CÓMO SE VE EN EL DASHBOARD: invisible. Hoy el laboratorio ya está vacío (F-2), así que nadie vería la diferencia; el día que se pueble, mostraría lo mismo que la réplica.
- CÓMO REPRODUCIRLO: `python experiments/_s149_audit/frente_f/diff_perfiles.py`; el brazo de control muestra que el flag de la conectiva es una constante resuelta que `experimental` no sobrescribe.
- CONFIANZA: CONFIRMADO (mecanismo leído y perfiles resueltos). Que la adopción de `max` ocurra es una decisión pendiente, no un hecho.
- GRAVEDAD: **4**. No tuerce una alerta hoy; garantiza que la segunda mitad del objetivo del dueño se rompa en silencio en el momento exacto en que más importa. Es A117 repetida. Hay que resolverlo **antes** del gate de la conectiva, no después.

### F-2. El experimental no produce ni conserva datos: fuera del cron, y el despacho manual bota su salida
- ARCHIVO:LÍNEA: `.github/workflows/nrt.yml:192-200` (sólo despacho manual), `:337` (`git add data/experimental/...`, no `experimental_v2`), contra `pipeline/profiles/experimental.yaml:71` (`data_subdir: experimental_v2`). SCRIPT: `salida_frescura.txt` (`data/experimental_v2: NO EXISTE`), y el listado del remoto.
- QUÉ PASA: no hay ninguna serie del perfil experimental vigente, de ninguna fecha. La única serie con ese nombre es la de la configuración de S15, congelada el 2026-08-25.
- CÓMO SE VE EN EL DASHBOARD: `frontend/experimental/index.html` muestra el aviso de archivo faltante para todos los volcanes.
- CÓMO REPRODUCIRLO: `python experiments/_s149_audit/frente_f/frescura_datos.py`.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: **4** respecto del objetivo (la mitad experimental tiene cero entrega); 2 respecto de una decisión de alerta, porque el aviso del tablero es honesto.

### F-3. La vara principal del experimental (actividad conocida de OVDAS) no existe como dato
- ARCHIVO:LÍNEA: `docs/DISENO_SENSIBILIDAD_POR_ZONA_S147.md:136-137` la nombra primera; búsquedas de la sección 3 sin ningún archivo de episodios.
- QUÉ PASA: para decir que una detección extra es real hace falta saber qué hacía el volcán. El proyecto no tiene una tabla de episodios (fechas de cambio de alerta técnica, reportes especiales, incandescencia observada por cámaras) para sus 11 volcanes.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: los `grep` y `find` de la sección 3.
- CONFIANZA: CONFIRMADO para este repo y para `Volcanologia/OVDAS/`; una búsqueda con cero no prueba ausencia en el resto del workspace (SIN VERIFICAR fuera de esas dos rutas; `Volcanologia/Camaras` y `Volcanologia/RRSS` no se miraron).
- GRAVEDAD: **3**. Sin ella, el paso 5 del diseño no se puede ejecutar. La puede aportar sólo el dueño (es geólogo del OVDAS).

### F-4. El resultado del piloto NHI de S131 no llegó al diseño de validación de S147
- ARCHIVO:LÍNEA: `docs/s131/agentes/OTRO_SENSOR.md` §3 y §4; ausencia de puntero en `docs/DISENO_SENSIBILIDAD_POR_ZONA_S147.md:138-141`, en los bloques S147 a S150 y en `CLAUDE.md`.
- QUÉ PASA: el diseño dice "si la zona A empieza a marcar noches en que el SWIR muestra píxeles calientes, la sensibilidad ganada es real". S131 ya midió que en 4 de 5 volcanes esa coincidencia ocurre a la tasa basal: los focos crónicos hacen que NHI alerte entre el 20 y el 49 % de sus escenas haya o no detección nuestra. Una validación armada así daría "confirmado" por azar. Es A110 (un control se valida midiendo su nulo) con el nulo ya medido y olvidado.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: leer `experiments/_s131_audit/otro_sensor/pilot_output_feb_sep.txt`; cobertura actual con `cobertura_nhi.py`.
- CONFIANZA: CONFIRMADO que el documento existe y que no está citado; los números del piloto son de S131, no re-medidos hoy.
- GRAVEDAD: **3**. Es el caso de manual del eje de esta auditoría en mi frente.

### F-5. Lastarria no tiene vara SWIR, y ningún rasgo de la categoría b tiene coordenadas
- SCRIPT:SALIDA: `salida_cobertura_nhi.txt` (Lastarria: HTTP 404). ARCHIVO:LÍNEA: `docs/S149_COSTO_OCULTO_MAX.md:112-117`.
- QUÉ PASA: Lastarria es donde el cúmulo salta entre dos puntos bajo `max` (10 de los 12 cúmulos que se mueven) y donde el rasgo real (Lazufre) está desplazado del cráter. Es el volcán donde más falta un juez externo y es el único Tier A que NHI-v1 no cubre.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: **2**.

### F-6. La opción `experimental_ndc_focus` del despacho del NRT no hace nada
- ARCHIVO:LÍNEA: `.github/workflows/nrt.yml:27` (única aparición).
- QUÉ PASA: quien la elija obtiene un run verde que no procesó nada (A108 en chico).
- CONFIANZA: CONFIRMADO por búsqueda del nombre en el archivo; no despaché nada.
- GRAVEDAD: **1**.

### F-7. La descripción del alcance del experimental se angostó al resumirse
- ARCHIVO:LÍNEA: memoria `feedback_s143_primero_igualar_a_mirova.md` (lista ancha) contra `pipeline/profiles/experimental.yaml:25-30` y `BLOQUE_ARRANQUE_S150.md:136-137` (sólo umbral por zona y `min`).
- QUÉ PASA: ver el final de la sección 2. No es un defecto de código; es una decisión del dueño que nadie le ha vuelto a preguntar.
- CONFIANZA: CONFIRMADO (los dos textos leídos hoy).
- GRAVEDAD: **2**.

### F-8. `data/experimental/` sigue en el repo y en el paso de commit, con nombre de producto vivo
- ARCHIVO:LÍNEA: `nrt.yml:337`; `pipeline/store.py:57` (comentario "data/mirova_equivalent/ or data/experimental/").
- QUÉ PASA: 45 archivos de una configuración declarada ruido, con el nombre que cualquiera asociaría al laboratorio actual. Riesgo de que una sesión futura la lea como "la serie del experimental".
- CONFIANZA: CONFIRMADO.
- GRAVEDAD: **1**. Cualquier limpieza pide tag defensivo (A38).

## 5. Propuesta: lo que le falta al experimental, en pasos chicos y en orden

Ningún paso toca `mirova_equivalent`. Los que tocan `pipeline/` o el NRT pasan por A45.

| # | paso | por qué en este lugar | toca |
|---|---|---|---|
| 1 | **Clavar en `experimental.yaml` los flags que definen "ver más"**, con su valor de hoy escrito explícito: como mínimo `enable_tests_23_prose_branch: false` y `enable_test1_path: true`. Y extender el guard de S147 para que compare **esos flags por dirección** (el laboratorio nunca más estricto que la réplica en la conectiva ni sin un camino de detección que la réplica tenga) | Cierra F-1. Es inerte hoy (los valores son los mismos) y tiene que estar mergeado **antes** del gate de la conectiva | un YAML de laboratorio y un test; no toca el operacional |
| 2 | Decidir con el dueño **qué es el experimental el día 1** (ver decisiones abajo). La opción más barata y más fiel a su frase: "el operacional de hoy, congelado" (`min` y Test 1 encendido), que ya sabemos que publica de más | Da contenido sin escribir código nuevo | decisión |
| 3 | **Arreglar la entrega**: que el paso de commit agregue `data/experimental_v2/`, o mejor, un workflow propio del laboratorio (cadencia baja, una o dos veces al día, fuera del candado de `nrt.yml`) para no devolverle al NRT los 19 minutos por job que S141 le quitó | Cierra F-2. Sin esto no hay serie | workflow (A45 por ser NRT) |
| 4 | **Poblar la historia sin reprocesar**: las ramas `origin/s146-ab/<run>` ya guardan brazos con `min` para septiembre y mayo (7 ramas en el remoto hoy). Evaluar si el brazo de control sirve como serie inicial del laboratorio. SOSPECHA: esos brazos son "sin Test 1", así que no equivalen al paso 2 si el dueño elige conservar el Test 1 | Evita un reproceso largo en la máquina local con el disco al 97 % | sólo lectura |
| 5 | **Armar la tabla de episodios de OVDAS**: una fila por volcán y episodio (fecha de inicio y fin, qué se observó, fuente). Aunque sean 20 filas | Cierra F-3. Es la única vara que el dueño considera operacional, y sólo él la puede llenar | dato nuevo en `data/` de referencia |
| 6 | **Coordenadas de los rasgos de la categoría b** (Lazufre, El Agrio, centro del lacolito, lago de lava) como dato en un archivo de referencia | Cierra F-5 y el SIN VERIFICAR de S149 sobre Lastarria | dato nuevo |
| 7 | **Validación con nulo medido**: rehacer el cruce con NHI de S131 sobre la franja que `max` apaga, comparando siempre contra la tasa basal de NHI del volcán, y declarar de antemano que sólo es informativo donde la tasa basal es baja | Recoge F-4 en vez de repetir el error | script de experimento |
| 8 | Scraper de NPixHot de MIROVA OLI/MSI (en el repo Mirova-v1, no acá) | El juez de más autoridad; pendiente desde S131 | otro repo |
| 9 | Recién entonces: sensibilidad por zona (pasos 3 a 5 del diseño de S147) y el brazo del Test 1 con estadístico corregido | Necesitan línea base, serie y vara | `pipeline/` (A45) |
| 10 | Display de tres estados y ficha del laboratorio | Último, cuando haya algo que mostrar | frontend, ficha (frente G) |

### Decisiones que hacen falta del dueño

1. **¿Qué es el experimental mientras no exista la sensibilidad por zona?** Opciones: (a) el operacional de hoy congelado, con `min` y Test 1; (b) `min` sin Test 1 (el brazo B de los A/B); (c) `min` con el Test 1 corregido. La (a) es la única que no requiere medir nada y conserva todo lo que hoy se ve; su costo conocido es el 86 % de publicación en negativos limpios de VIIRS 375 (cifra de S147 citada en `MEMORY.md`, no re-medida hoy).
2. **¿Se publica el laboratorio al operador del OVDAS o es sólo interno?** Si se publica, necesita ficha (CPLT N°372) y el display de tres estados; si es interno, basta la serie.
3. **¿Cadencia?** Cron propio diario, o sólo bajo demanda.
4. **¿Alcance?** Sólo umbrales térmicos, o también lo que la memoria de S143 lista (SWIR, TIR alternativo, MOUNTS, InSAR), que hoy vive en repos hermanos y no en este perfil.
5. **Tasas objetivo por zona** (30 % y 2 % son un punto de partida del diseño, no una derivación): pendiente desde S147.
6. **¿Puede aportar la tabla de episodios y las coordenadas de los rasgos?** (pasos 5 y 6).

## 6. Para otros frentes

- **Frente G**: `docs/FICHA_SDA_VRP_CHILE.md` no declara el laboratorio, que está enlazado desde el tablero público (`frontend/index.html:411`). `nrt.yml:1` sigue llamándose "both profiles" y `:18` tiene por omisión `both`, que ya no corre dos perfiles (lo explica el comentario de `:197-198`).
- **Frente G**: `nrt.yml:27`, opción de despacho sin paso que la atienda (F-6).
- **Frente B**: NHI-v1 planea borrar `docs/nhi_data/` al deprecar L2A (`SESSION_STATUS.md` del repo NHI-v1, línea 138); cualquier instrumento que lo lea debe apuntar a la variante que sobreviva. La variante TOA guarda sólo una ventana rodante de 14 días según S131 (`OTRO_SENSOR.md` tabla §1), no re-verificado hoy.
- **Frente D**: `experimental_lowT.yaml:19-23` afirma que el pipeline no llama a VRPTIR; `CLAUDE.md` A89 cita `from pipeline.vrptir import vrp_tir_mw as _aveni_vrp_tir_mw` como función que corre en cada gránulo. Una de las dos está vieja.
- **Frente A**: la regla de S143 sobre el alcance del experimental (F-7) no está en `CLAUDE.md` ni en `docs/MISSION.md` (`grep -i experimental docs/MISSION.md`: cero; segunda búsqueda por "perfil/profile/lab": sin mención del laboratorio).

## 7. VERIFICADO LIMPIO

| qué miré | resultado | comando |
|---|---|---|
| El perfil `experimental` no es más ciego que el operacional hoy | 142 de 144 constantes idénticas; pisos en 0.0 en ambos | `python experiments/_s149_audit/frente_f/diff_perfiles.py` |
| `experimental_ndc_focus` no cambia la detección, sólo apaga MODIS y VIIRS 750 | 4 diferencias, ninguna de umbral | ídem |
| Ninguna rama del pipeline se comporta distinto por el nombre del perfil, salvo el filtro de volcanes sin `--volcano` | 2 usos de `PROFILE_NAME` fuera de `profile.py` | `grep -rn PROFILE_NAME pipeline/*.py scripts/run_pipeline.py` |
| El aviso del tablero del laboratorio dice la verdad (archivo faltante, no calma) | texto leído | `sed -n 415,445p frontend/experimental/index.html` |
| Las tres vistas operacionales no mezclan datos del laboratorio | leen sólo `data/mirova_equivalent/` y `data/mirova/` | `grep -n "data/" frontend/diario.html frontend/mosaico.html frontend/comparacion.html` |
| NHI-v1 y Landsat-v1 están vivos y son públicos | push del 2026-09-21 en ambos | `gh api repos/MendozaVolcanic/NHI-v1`, ídem Landsat-v1 |
| Los archivos del piloto NHI de S131 existen | 4 elementos en la carpeta | `ls experiments/_s131_audit/otro_sensor/` |
| `ENABLE_TEST1_NULL_CORRECTED` existe y está apagado por omisión | `pipeline/profile.py:301` | `grep -n TEST1_NULL_CORRECTED pipeline/profile.py` |

## 8. SIN VERIFICAR (dicho en voz alta)

- Si `ENABLE_VRPTIR_AVENI` tiene hoy consumidor en `process_viirs.py` (no lo tracé).
- Los números del piloto NHI de S131 (leídos, no re-medidos).
- El 86 % de publicación en negativos limpios del operacional actual (cifra heredada de S147).
- Si `niveles_landsat.json` de Landsat-v1 es térmico o genérico.
- Si en otras carpetas del workspace (`Volcanologia/Camaras`, `RRSS`, `Papers`) hay un registro de episodios de OVDAS.
- Si los brazos de control de las ramas `s146-ab/*` sirven como serie inicial del laboratorio (sólo conté que las ramas existen: 7).
- No corrí pytest (límite de la auditoría), así que el guard del laboratorio está leído, no ejecutado.
