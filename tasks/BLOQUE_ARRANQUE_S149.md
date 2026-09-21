# Bloque de arranque S149

> Cierre de S148 (2026-09-21, 09:30 UTC según la hora del servidor). Sesión nocturna desatendida:
> Nicolás pidió "continúa con todo lo que recomiendes" y revisar cada hora. `main` en
> **`82c334268`** al reunir la evidencia (el commit de este cierre va encima), igual al remoto.
> Siete PR mergeados, del #729 al #735, todos con CI en verde **y con conclusión**. La suite
> completa NO se corrió en local esta sesión (la base declarada de S147 es 1627 passed; el CI de
> cada PR la corrió entera y pasó).
>
> ⚠️ **Trabajo en vuelo al fijar el estado**: un solo run, el NRT despachado a mano
> (**35583101154**, 09:24 UTC), porque el cron de GitHub llevaba 6 horas sin disparar (última
> corrida por cron: 03:27 UTC, en verde). Escribe a `main` como cualquier NRT. Ningún A/B ni
> agente quedó corriendo.

## a. Todo en una pantalla

| qué | estado | evidencia |
|---|---|---|
| **A/B de la conectiva, brazo F** (`min` a `max`), ventana completa | **terminado: hipótesis CONFIRMADA en VIIRS 375; merece el gate completo; NO autoriza nada en producción** | `docs/S148_RESULTADO_AB_CONECTIVA.md` (#735). Cobertura 2386 contra 2386 tras la reparación (run 35558196104). Falsos 29,8 a **2,7 %** (10 de 372); borde sobre nadir 2,15 a 0,25; borde con fondo frío 58,4 a 2,6 %; recall por pasada 137 a **135 de 143**, ninguna pérdida de 0,5 MW o más |
| Dos verificadores con contexto limpio sobre F | terminados, **ninguno logró romperla**, sin hallazgos de gravedad 4 o 5 | `docs/audit_s148/VERIFICADOR_LECTURA_CONECTIVA.md` y `docs/audit_s148/VERIFICADOR_RESULTADO_CONECTIVA.md` |
| **El costo que el evaluador no mira** | **medido por el verificador, SIN verificar a nivel de píxel** | con `max` se apagan **50 publicaciones de VIIRS 375 en noches en que MIROVA sí alertó** en ese volcán por otra pasada (84 a 34 de 171). Es lo primero que hay que mirar |
| Otros costos de `max` | medidos | magnitud pareada contra MIROVA 0,79 a 0,71 (se pierde el vecino tibio; baja en Cordón Caulle, Tupungatito y Chaitén); el cúmulo se mueve más de 500 m en 13 de 228 pares, 10 en Lastarria; **en MODIS apaga el detector** (va junto con banda 22, D21) |
| H2 y H3 de la conectiva | **medidos** | `docs/audit_s148/MEDICION_H2_H3_CONECTIVA.md`. La compuerta `bt > t_bg + 3 K` (D22) y el segundo pase sin condicionar **se compensan**: 34 de 135 positivas de V375 publican sin ningún píxel del primer pase. Se tocan juntas o no se tocan |
| **A/B de la caja de 5 × 5 km, brazos G y H** | **NO MEDIBLE con este cableado** | `docs/audit_s148/POR_QUE_LA_CAJA_NO_APAGA.md` (#734). `enable_roi1_box_paper` llega sólo al primer pase; el segundo recibe el círculo (`pipeline/process_viirs.py:1313`, verificado por mí; mismo patrón en `process_modis.py:923` y `process_viirs_mod.py:892` según el agente) y recaptura lo rechazado. G con cobertura exacta: Q1 0 de 61, Q2 0 de 50, tasas idénticas al control. **D18 marcada: nunca se midió** |
| El "43 de 135" del pre-registro de la caja | **resuelto: Q3 no tiene sustrato** | centraba la caja en la coordenada nominal y no en el ancla de detección; con el ancla da 0 de 135. No había script en el repo |
| C7 del evaluador | **bajado a informativo** | #729 |
| Workflow del A/B | **arreglado**: un relanzamiento parcial ya no sale en rojo falso; entrada nueva `control` | #730. Comprobado en vivo: run 35572961810 salió 7 de 7 en verde |
| Evaluador: banda del control positivo | ⚠️ **defecto abierto** | `banda_control_tasa_pub_neg` está calibrada para el control de producción; con el brazo B de control imprime INDECIDIBLE aunque identidad y cobertura den 1,0. No lo toqué |
| Evaluador: criterio C8 | ⚠️ **no prueba selectividad** | un apagador al azar lo cumple en 200 de 200 semillas (verificador, H2) |
| Brazo H | incompleto, **no reparar** | le faltan 23 pasadas de Tupungatito; tampoco puede responder la pregunta de la caja |
| Copia de trabajo de los datos | **en disco, fuera de git** | la carpeta `prelim_s148` bajo `experiments/_s147_lectura/` (unión de los runs 35548121381, 35548604513, 35558196104 y 35572961810, todos en ramas remotas `s146-ab/<run>`). Se puede borrar: se reconstruye con `git archive` CON RUTA |

## b. Decisiones que espera Nicolás

| # | pregunta | opciones | recomendación |
|---|---|---|---|
| 1 | **Arreglar el cableado de la caja** (pasarle la máscara de la caja también al segundo pase, en los tres procesadores; el flag sigue apagado) | hacerlo / dejarlo | **hacerlo**, con A45 (tag y tu confirmación) y TDD. Es inerte en producción porque el flag está apagado, y sin él D18 no se puede medir nunca. Después repetir G y H |
| 2 | **La conectiva `max`: pasarla al gate completo** | sí / esperar | **sí, pero empezando por el costo oculto**: mirar a nivel de píxel, contra los TIF de MIROVA, las 50 publicaciones que se apagan en noches con alerta. Si son calor real, `max` tal cual cuesta más de lo que muestra el recall por pasada |
| 3 | **Ventana de invierno para la conectiva** (junio a agosto, los dos brazos reprocesados con el código de hoy) | despachar / no | **despachar después de la 2**, con pre-registro y verificador antes. Septiembre casi no tiene Villarrica (5 positivas) ni Chillán (4) |
| 4 | **Brazo MODIS: banda 22 con `max`** | despachar / no | **sí, junto con la 3**. En MODIS `max` sola apaga el detector |
| 5 | **El candado `preregistro_aprobado`** | arrastre de S147 | esta sesión lo puse **una vez**, sólo para repetir brazos ya pre-registrados con el mismo código (run 35572961810). No despaché ningún A/B nuevo. **Dime si eso también debe ser tuyo** |
| 6 | Arrastre: correo a Coppola (la conectiva es ahora LA pregunta), limpieza de disco (18 GB libres, 97 %), token de Earthdata (**vence el 2026-10-03**), tasas por zona del experimental, centro de la caja | sin cambios | enviar el correo; correr la limpieza; rotar el token esta semana |

## c. Lo aprendido

| lección | tipo | dónde vive |
|---|---|---|
| **Un flag que cambia un umbral o una geometría tiene que llegar a TODOS sus consumidores, y un "no cambia nada" se traza antes de creerlo.** La caja llegaba al primer pase y no al segundo, que deshacía su efecto. El cero estaba bien medido (el flag se leía, los diagnósticos cambiaban, el instrumento tenía control positivo) y aun así no medía la caja. Probablemente S130 cerró D18 sobre este mismo defecto | **regla general** | **A118** en `CLAUDE.md` |
| **Mi primera explicación del cero no sobrevivió a medirla.** Escribí que el adaptativo quedaba bajo el piso; medido, pasa en 556 de 1618. La retiré y la dejé como SIN VERIFICAR antes de que llegara la traza | refuerzo de A116 | `docs/S148_LECTURA_PRELIMINAR_CAJA.md` §3 |
| **Un evaluador sólo ve los estratos que etiqueta.** El recall por pasada daba 137 a 135 y el costo real estaba en pasadas que no son ni positivas ni negativos limpios: noches con alerta por otra pasada | regla del proyecto | A118 (segunda parte); verificador H1 |
| **Un control positivo calibrado para un control no vale para otro.** La banda de 80 a 92 % hizo imprimir INDECIDIBLE a un resultado con identidad 1,0 | defecto del instrumento, abierto | fila de la tabla a |
| **El verificador con contexto limpio volvió a pagarse**: los tres encontraron algo propio (las salvedades de la lectura, el mecanismo de H3, el costo subcontado y C8) | refuerzo de A93 | `docs/audit_s148/` |
| Una cita a una ruta que sólo existe en una rama de datos rompe el guard del libro de pruebas; y un heredoc largo con comillas invertidas volvió a fallar: los documentos largos se escriben con la herramienta de escritura, no por la terminal | del proyecto y general | se les avisa a los agentes en el prompt; refuerza la lección de S144 |

## d. Problemas abiertos e hipótesis

| qué | etiqueta |
|---|---|
| `max` apaga selectivamente el borde del barrido con fondo frío en VIIRS 375 | **CONFIRMADO** sobre 20 días de septiembre, por dos verificadores |
| Las 50 publicaciones apagadas en noches con alerta son calor real | **SOSPECHA**, sin mirar a nivel de píxel |
| D22 y el segundo pase sin condicionar se compensan | **CONFIRMADO** (650 de 650 píxeles a 3 K o menos sobre el fondo) |
| Un primer pase sin compuerta vería esos mismos píxeles bajo `max` | **SIN VERIFICAR** (deducción del agente) |
| La caja no llega al segundo pase | **CONFIRMADO** en `process_viirs.py:1313` por mí; en MODIS y VIIRS 750 por el agente, no re-verificado |
| S130 cerró D18 sobre este mismo cableado | **SOSPECHA** |
| Con la caja en los dos pases se apagarían al menos 11 de 51 | **SOSPECHA** (cota del agente, sin reprocesar) |
| Los 10 cúmulos que se mueven en Lastarria tocan el campo fumarólico real | **SOSPECHA**, sin mirar con dirección |
| P2 "se invierte" | **NO SE PUEDE AFIRMAR**: 2 contra 6 publicaciones; que quede en 1,3 o menos sí es robusto |
| El cron del NRT se salta corridas cuando los A/B ocupan corredores | **SOSPECHA**: huecos de 3 a 6 h los dos últimos días, coincide con los A/B; no medido |

## e. Lo que ya está cerrado y no hay que rehacer

- **No re-correr el brazo F ni su reparación**: evaluado, con cobertura exacta y dos verificadores.
- **No gastar más reparaciones en G y H**: no pueden responder la pregunta de la caja.
- **No escribir que la caja es inerte**, en ningún documento.
- **No buscar el script del "43 de 135"**: no existe; está reconstruido en `experiments/_s148_caja_traza/origen_43_de_135.py`.
- **No condicionar el segundo pase sin sacar la compuerta de 3 K**, ni al revés.
- **No citar C8 como prueba de selectividad.**
- **No leer el INDECIDIBLE del evaluador como falla del experimento** cuando el control es el brazo B.
- Sigue valiendo todo lo de S147 §e (`tasks/BLOQUE_ARRANQUE_S148.md`).

## f. Prompt para la próxima sesión

```
Retoma VRP Chile en S149. Trabaja en español de Chile (formas de tú, nunca voseo), sin guiones
largos ni medios, explicando como geólogo: fenómeno, mecanismo, números al final.

EL OBJETIVO, en palabras de Nicolás: máxima fidelidad a MIROVA en el perfil réplica, y más
detecciones, con posibles falsos positivos, en el experimental. Toda decisión de la réplica se
mide contra la base de datos de MIROVA (CSV, OSF, TIF), no se elige.

1. VERIFICA ANTES DE CREER:
   cd "C:/Users/nmend/OneDrive/Escritorio/claude/Volcanologia/VRP Chile"
   git fetch origin --prune && git pull --ff-only && git status -sb
   git rev-parse HEAD ; git ls-remote origin -h refs/heads/main        (deben coincidir)
   gh api -i repos/MendozaVolcanic/VRP-chile | grep -i date            (hora del servidor, A86)
   python -m pytest tests/ -q -p no:cacheprovider | tail -1            (base S147: 1627 passed; árbol quieto)
   gh run list --workflow nrt.yml -L 5                                 (¿el cron se sigue saltando corridas?)
   df -h /c                                                            (estaba en 18 GB libres)
   El token de Earthdata vence el 2026-10-03.

2. LEE EN ORDEN: CLAUDE.md del proyecto · tasks/BLOQUE_ARRANQUE_S149.md ·
   docs/S148_RESULTADO_AB_CONECTIVA.md (empieza por su sección 0) ·
   docs/audit_s148/POR_QUE_LA_CAJA_NO_APAGA.md · docs/audit_s148/MEDICION_H2_H3_CONECTIVA.md ·
   docs/audit_s148/VERIFICADOR_RESULTADO_CONECTIVA.md.

3. TRABAJO EN ORDEN (pregúntale a Nicolás por las decisiones 1 a 5 de la sección b antes de
   despachar nada o de tocar pipeline/):
   a) EL COSTO OCULTO DE max: las 50 publicaciones de VIIRS 375 que el brazo F apaga en noches
      en que MIROVA alertó por otra pasada (script del verificador:
      experiments/_s148_verificador_resultado/r3_nulo_y_costos_ocultos.py). Mirarlas a nivel de
      píxel contra los TIF de MIROVA (experiments/_s147_tif/bajar_tif.py; ojo con A106 y A109:
      usar otra pasada de la misma noche, no el mismo gránulo). Pregunta: ¿son calor real?
   b) Los 13 cúmulos que se mueven más de 500 m, con DIRECCION (10 en Lastarria: ¿hacia o desde
      el campo fumarólico?).
   c) Si Nicolás aprueba: arreglar el cableado de la caja con A45 (tag
      pre-s149-caja-segundo-pase, confirmación explícita, TDD: primero el test que muestra que
      second_pass_adjacent ignora la caja). El flag sigue apagado. Después repetir G y H con el
      pre-registro actualizado (Q3 no tiene sustrato: reescribirla o sacarla).
   d) Arreglar el evaluador: la banda del control positivo debe depender del control, y C8 se
      reemplaza por una prueba que un apagador al azar NO cumpla (medir su nulo, A110).
   e) Pre-registro de la ventana de invierno para la conectiva y del brazo MODIS banda 22 con
      max; verificador con contexto limpio ANTES de despachar.
   f) Arrastre de S147: brazo del Test 1 con el estadístico corregido para el experimental;
      centro de la caja; pendientes de S146 (verificador del frente I, tope de Villarrica al
      operador, pc.classification al tablero).

4. REGLAS DURAS: nada a pipeline/process_*.py, store.py ni mirova_equivalent.yaml sin tag
   defensivo y confirmación explícita (A45); criterio escrito Y COMMITEADO antes de correr;
   verificador con contexto limpio antes de despachar un A/B y sobre toda mejora mayor que 30 %;
   todo control lleva su nulo medido; el recall que decide va por PASADA, y además mirar las
   noches con alerta por otra pasada; ninguna ventana cruza el 2026-08-28 23:00 UTC; ningún
   número transcrito a mano; una rebaja se propaga a los hijos en el mismo PR (A113); un flag
   tiene que llegar a todos sus consumidores (A118); todo workflow autentica SOLO por
   EARTHDATA_TOKEN; esperar el CI con conclusión antes de mergear; no correr la suite mientras se
   edita; nunca git reset --hard; git archive SIEMPRE con ruta; no citar en docs rutas que sólo
   existen en ramas de datos (rompe el guard del libro de pruebas); documentos largos con la
   herramienta de escritura, no con heredoc.

5. SI LA SESION NO ALCANZA: deja cada frente con su cobertura declarada, rescata al repo
   cualquier instrumento que viva en el scratchpad, y cierra con /cierre.
```
