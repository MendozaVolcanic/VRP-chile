# caminos.md: caminos por los que cada afirmación podría estar mal

Escrito antes de abrir ningún archivo citado. Solo conozco títulos, archivo:línea y gravedad del auditor.

## MA172-101 y MA172-302 (vigilancia_sombra cuenta records MODIS de la vía como K) [probable duplicado]
1. Los records de la vía quizá no se distinguen de K en el JSON (campo via_codigo_mirova), pero el script de vigilancia podría filtrar por ese campo en otra línea que el auditor no vio (el caller transforma).
2. La vigilancia quizá solo compara datos de la ventana de sombra (perfil sombra / 34 volcanes), no los records de producción de los 11 Tier A: la vía solo cambia producción, así que el efecto podría no llegar a lo que mide.
3. La línea citada (432) puede haber corrido por versión: el auditor midió en B (b42823194) pero la lógica puede estar en PR A, o en base. El defecto podría no existir en ninguna de las dos puntas.
4. "Puede pedir revertir K": quizá el umbral de disparo exige condiciones (n mínimo, ventana, sensor) que MODIS con la vía no alcanza; o el issue solo se abre, no revierte nada automáticamente. La gravedad 3 puede ser excesiva.
5. store.py:549 y store.py:89-94 pueden ser dos sitios distintos del mismo defecto; confirmar si ambos son parte de él o uno es solo comentario.
6. El workflow (vigilancia-sombra.yml:134-135) quizá lee otro archivo de datos (sombra) donde la vía está apagada por flag fijado en false en experimental, así que la vía nunca entra.
7. El flag se lee de otro lado: el workflow puede correr con un perfil distinto al de producción.
8. Fusión: confirmar que son realmente el mismo defecto y no dos (uno de campo, otro de workflow).

## MA172-102 (tablero no reconoce codigo_mirova como ancla honesta)
1. "Ancla honesta" puede estar definida por una lista de valores de final_hotspot_source / anchor; codigo_mirova podría estar cubierto por otro nombre o por otra rama del código, o el valor real que emite process_modis para la vía es otro string.
2. Los números 14,89 km y 0,318 km son de un caso sintético o de un arnés, no de un record real de MODIS; el arnés podría no reproducir lo que hace producción (pyhdf roto en Windows).
3. Las líneas citadas (1631, 1697, 2735...) pueden ser lugares donde el helper se usa pero con fallback correcto (cluster del record) antes de llegar al marcador.
4. Puede que el efecto exista también con K (final_hotspot ya no es el ancla), es decir que no es nuevo de la vía sino preexistente: entonces no bloquea el PR B.
5. La vía quizá no emite final_hotspot_source distinto; la clasificación puede ser vigente con cualquier valor de fuente.
6. El tablero en main y en B pueden diferir (frontend/index.html tocado por PR A/B); medir en la punta correcta.
7. Gravedad: un marcador mal ubicado en el mapa vs. clasificación errónea de alerta; el predicado "publica" (isValidDetection) podría no depender del marcador.

## MA172-103 (prueba roja en B: tests/test_guard_adopcion_k_s153.py:45-48)
1. La prueba puede fallar en el worktree por causa ajena al flip (entorno Windows, pyhdf, ruta, autocrlf, caché), no por el PR B. Hay que compararla con da67fa417 y con la base.
2. Puede que ya fallara en da67 y en main antes del PR B ("pre-existente", regla A50).
3. Puede que PR B corrija la prueba en otra parte del diff y el worktree de B no la tenga, o que la prueba cubra justo el cambio y esté bien que quede roja hasta actualizar (entonces es un hallazgo del PR B no actualizó el guard).
4. La falla puede depender de un test en paralelo (A112) o de orden.
5. Que el flag se lea de pipeline.profile y no del YAML: la prueba podría leerlo por YAML.

## MA172-104 (perfil _s154_reproc_k_historico.yaml hereda la vía; prueba de identidad verde)
1. "Hereda" por extends: quizá el perfil se arma por extends de mirova_equivalent pero fija explícitamente enable_modis_codigo_mirova: false, o el cargador de perfiles no hereda ese flag.
2. Verificar con pipeline.profile (A89), no con el YAML.
3. El perfil quizá es un artefacto histórico no usado por ningún workflow vivo; el reproceso con K no se volverá a correr (sin consumidor), así que no bloquea.
4. "Prueba de identidad sigue verde": podría ser verde por subcadena (A92) o por comparar contra algo que también cambió; el control positivo.
5. El reproceso histórico con K de verdad exigiría que la vía esté apagada: pero MODIS sólo corre en Linux Actions; el perfil se usaría ahí.

## MA172-105 (textos que dicen que MODIS de producción es K sin marca A113)
1. Las tres citas pueden estar ya marcadas en otra línea cercana, o la marca A113 vive en un documento padre (CLAUDE.md, MISSION.md) y no hace falta en cada hijo.
2. README.md:52-56 / SINTOMAS.md:25-28 / index.html:544 pueden hablar de K como histórico (el detector K del 18-sep) y no afirmar que es el de hoy.
3. Cuánto texto sin marca bloquea: es documentación; PR B puede traer parte ya en su diff (ficha SDA v1.18, marcas A113). Mirar si el diff de B ya cubre alguna.
4. Líneas movidas entre bases: README en B vs base.
5. frontend/index.html:544 es texto visible al operador? Si lo es, sube de gravedad; si es un comentario, baja.

## MA172-106 (cabeceras FICHA y POR QUÉ dicen APAGADA en archivos que corren en producción)
1. "APAGADA" puede referirse a otra cosa (la vía en VIIRS 750, un flag de VIIRS, o la caja de ROI), no a la vía de MODIS.
2. pipeline/mirova_v750_codigo.py es el módulo de V750 (y la vía MODIS lo reusa); la cabecera dice apagada para V750 y eso sigue cierto.
3. store.py:351-356 puede ser comentario sobre otro flag.
4. La guía de transparencia (GUIA_MAESTRA_TRANSPARENCIA_ALGORITMICA) exige cabecera al día: gravedad de documentación, pero SDA en producción (Resolución CPLT 372) lo hace más serio.
5. Podría estar ya arreglado en PR A o B (cabeceras tocadas) y el auditor haya mirado la base.

## MA172-110 (experimental_lowT hereda la vía; ni guard ni declaración lo cubren)
1. experimental_lowT podría no heredar de mirova_equivalent, o heredar de otro perfil que fija el flag false.
2. Podría ser un perfil muerto (sin workflow, sin uso): sin consumidor, sin efecto.
3. Verificar con pipeline.profile con VRP_PROFILE=experimental_lowT, no con el YAML.
4. El guard de "flag fijado en false en experimental, experimental_ndc_focus y _s146_ab_control" quizá se ejerce por una lista fija; lowT no está en ella; pero si lowT no hereda, no es defecto.
5. Un perfil derivado se vigila por dirección (A117): lowT hereda otras cosas?

## Caminos generales a todos
- El worktree b (D:/vrp-trabajo/worktrees/s172-miniaud-b) podría no estar en b42823194 (HEAD movido): verificar con git rev-parse.
- Los scripts de los auditores pueden leer una copia (copia_b, copia_da67) distinta del worktree; reproducir con mi propio camino.
- El campo via_codigo_mirova puede aparecer sólo en records de la vía y no en otros; un grep puede contar cero sin que signifique ausencia (A89).
- La vara de "producción": leer pipeline.profile con VRP_PROFILE=mirova_equivalent, no el YAML.
- Windows: pyhdf roto; arneses sintéticos pueden no ser representativos.
- Gravedad: bloquea PR A, PR B o ninguno. Los PR están separados: algo que solo dice la vía y existe solo después del flip bloquea B, no A. Algo que A declara inerte y no lo es bloquea A.
- Disco D: 6,6 GB libres (OK sobre 3 GB); un proceso pesado a la vez.

---
NOTA FINAL: hora del servidor 2026-11-02 01:36:11 UTC. sha256 del contenido anterior a esta línea: 2cb9a5f59ee0c5263066d5d40cf36482ce82b9fb540e2454e9a44e2c9dce94f9
