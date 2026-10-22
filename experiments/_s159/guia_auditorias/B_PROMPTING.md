# B. Lo que las guías de prompting dicen sobre la guía de auditorías

2026-10-21. Sólo lectura: no se editó ninguna guía ni se hizo git. Todo lo escrito está en
`C:\vrp-trabajo\s159-pruebas\experiments\_s159\guia_auditorias\`.

## Qué se leyó, entero, en esta sesión

| archivo | líneas |
|---|---|
| `C:\Users\nmend\OneDrive\Escritorio\claude\GUIA_MAESTRA_AUDITORIAS.md` (en adelante GMA) | 214 |
| `C:\Users\nmend\OneDrive\Escritorio\claude\PLANTILLA_CAZA_DE_BRECHAS.md` (PCB) | 531 |
| `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\_prompts\PREAMBULO-AUDITOR.md` (PRE) | 72 |
| `C:\Users\nmend\OneDrive\Escritorio\claude\GUIA_PROMPTING_prompting-claude-fable-5-1.md` (F51), oficial | 898 |
| `C:\Users\nmend\OneDrive\Escritorio\claude\GUIA_PROMPTING_claude-prompting-best-practices.md` (BP), oficial | 1113 |
| `C:\Users\nmend\OneDrive\Escritorio\claude\GUIA_PROMPTING_FABLE5.md` (F5N), notas previas | 98 |

Ejemplos de prompts reales de hoy (sólo encabezados, para ver qué pidió el coordinador):
`C:\vrp-trabajo\s159-pruebas\experiments\_s159\cob\INFORME.md` l. 1-40,
`...\_s159\p1\INFORME.md` l. 1-40, `...\_s159\geo\INFORME.md` l. 1-40, `...\_s159\n\INFORME.md` l. 1-25 y
`...\_s159\chillan_modis\verificador\INFORME.md` l. 1-30. Los informes no traen el prompt textual: lo que digo del
prompt sale de lo que cada informe declara haber cumplido, así que es inferencia (SOSPECHA razonable, no lectura).

No leí las guías propias de Opus 5 ni de Sonnet 5, que BP l. 25-26 nombra («task scope and over-verification,
subagent control, and self-correction» para Opus 5; «literal instruction following» para Sonnet 5). No están en el
workspace. Todo lo que diga de esos dos modelos más allá de lo que BP resume es SOSPECHA. Ninguna de las guías
habla del modelo Opus 5.5, que es el que corre esta sesión: su comportamiento frente a estas recomendaciones es SIN DATO.

Una regla de transcripción: Nicolás prohíbe los guiones largos en todo archivo. Donde una cita textual en inglés
traía un guion largo, lo cambié por coma o paréntesis y lo marco con «[guion del original cambiado]». El resto de
cada cita es literal.

---

## 1. Lo que la guía de auditorías ya hace de acuerdo con las guías de prompting

| práctica de la guía de auditorías | dónde | lo que dice la guía de prompting | dónde |
|---|---|---|---|
| Dar el porqué: quién sufre el bug, que no es código de laboratorio | PRE l. 13-17, GMA l. 131-132 | «Providing context or motivation behind your instructions ... can help Claude better understand your goals» y «Claude is smart enough to generalize from the explanation» | BP «Add context to improve performance», l. 60 y 76; F5N l. 22 y l. 63-64 |
| Anclar cada afirmación a un tool result de la propia sesión; lo no leído es SOSPECHA | PRE l. 24-30, GMA l. 132-133 | «Before reporting progress, audit each claim against a tool result from this session ... if something is not yet verified, say so explicitly» | F5N l. 49 (bloque oficial de Fable 5); BP «Minimizing hallucinations», l. 1001-1008 |
| Objetivo más límites, no checklist; «sobre-prescribir degrada» | GMA l. 157-158 | «Prefer general instructions over prescriptive steps ... Claude's reasoning frequently exceeds what a human would prescribe» | BP l. 776; F5N l. 22 y l. 31 |
| Límites explícitos de lo que NO hace (no arreglar, no tocar otros archivos) | PRE l. 19-22, GMA l. 158 | «Pause for the user only when the work genuinely requires them» y el bloque de alcance de F51 | F5N l. 52; F51 «Finish the whole task», l. 824-828 |
| El que verifica no es el que encontró, con contexto limpio | GMA l. 140-142, PRE l. 63-64 | «Verificación con subagentes frescos > autocrítica»; el encadenamiento de autocorrección en llamadas separadas | F5N l. 30; BP «Chain complex prompts», l. 938 |
| El orquestador sigue trabajando mientras corren los auditores | GMA l. 162 | «don't force the lead agent to stop and wait for each one» | F51 «Let the lead agent keep working while subagents run», l. 888 |
| Estado del agente en el worktree y en git; relanzar reconstruyendo desde `git log` | GMA l. 152-156 | «Use git for state tracking» y «Claude's latest models are extremely effective at discovering state from the local filesystem» | BP l. 846 y l. 825 |
| «La decisión está tomada» se dice por tarea | GMA l. 148-151 | «The user's request (or the plan they approved) sets the scope, and the scope is the deliverable» [guion del original cambiado] | F51 l. 824 |
| Pedir la salida cruda junto al número | GMA l. 145 | «If tests fail, say so with the output; if a step was skipped, say that» | F5N l. 49 |
| Bloque de autonomía si corre desatendido | GMA l. 159 | bloque oficial completo | F51 l. 809-815 |

Además, los informes de hoy muestran que el preámbulo sí llega y se cumple: declaran sólo lectura y carpeta
(`cob` l. 3-5, `p1` l. 3-5, `geo` l. 3-7), las dos preguntas del instrumento con control positivo y denominador
(`cob` l. 31-38, `p1` l. 29-40), el formato SCRIPT:SALIDA y el orden por gravedad (`geo` l. 33-40), y el
verificador enumera sus caminos de ruptura antes de leer el informe (`chillan_modis\verificador` l. 7-11). Y abren
con el resultado («En una pantalla», `p1` l. 7, `geo` l. 9, `n` l. 12), que es lo que pide F5N l. 42-43 («Lead
with the outcome»). Ese último punto **no está en el preámbulo**: lo pone el coordinador cada vez (ver mejora M5).

---

## 2. Mejoras concretas

Ordenadas por valor. Cada una: qué dice hoy, qué recomienda la guía de prompting, texto listo para pegar y por qué ayuda.

### M1 (ALTO). Reemplazar la paráfrasis del bloque de autonomía por el bloque oficial de Fable 5.1, con las paradas propias de una auditoría

**Hoy.** GMA l. 159: «**Bloque de autonomía** si corre desatendido ("nadie contesta a mitad; termina el
entregable")». Es una paráfrasis de una línea y no trae el texto. PRE no tiene bloque de autonomía. F5N l. 61 trae
una versión más corta y anterior.

**La guía.** F51, sección «Finish the whole task», l. 804: sin el empujón el modelo «sometimes describes what it
would do next instead of doing it ("Next, I'll …") or stops to ask permission for a step the original request
already covered». l. 818: «The opening sentence, which tells the model the user isn't watching, carries much of
the effect. Keep it as written. If your product needs the model to stop for specific confirmations, add a sentence
after it listing them.» Y el bloque trae un párrafo de excepción que es justo el caso del auditor (l. 811): «when
the user is describing a problem, asking a question, or thinking out loud rather than requesting a change, the
deliverable is your assessment. Report your findings and stop. Don't apply a fix until they ask for one.»

**Texto para pegar** (al final del preámbulo, sólo cuando el agente corre desatendido; las tres primeras líneas
en inglés, tal cual, porque la guía pide no tocar la primera frase; F5N l. 37 confirma que el modelo los aplica
igual en inglés):

```text
You are operating autonomously. The user is not watching in real time and cannot answer questions mid-task, so asking 'Want me to…?' or 'Shall I…?' will block the work. For reversible actions that follow from the original request, proceed without asking. Stop only for destructive actions or genuine scope changes the user must decide. Offering follow-ups after the task is done is fine; asking permission before doing the work is not.

Exception: when the user is describing a problem, asking a question, or thinking out loud rather than requesting a change, the deliverable is your assessment. Report your findings and stop. Don't apply a fix until they ask for one.

Before ending your turn, check your last paragraph. If it is a plan, an analysis, a question, a list of next steps, or a promise about work you have not done ('I'll…', 'let me know when…'), do that work now with tool calls. That includes retrying after errors and gathering missing information yourself. Do not stop because the context or session is long. End your turn only when the task is complete or you are blocked on input only the user can provide.

Before running a command that changes system state (such as restarts, deletes, or config edits), check that the evidence actually supports that specific action. A signal that pattern-matches to a known failure may have a different cause.
```

Y en español, inmediatamente después (es la frase de paradas que l. 818 dice agregar):

```text
En esta auditoría tu entregable es tu evaluación, nunca un arreglo. Las únicas cosas que exigen detenerte y
dejarlas escritas como pendientes son: tocar algo fuera de «CARPETA»; hacer commit, push o merge; despachar un
workflow que esta tarea no nombre; usar una credencial distinta de las que esta tarea nombra. Todo lo demás
(leer, correr scripts propios, bajar archivos sueltos de la lista de esta tarea, repetir una medición) lo haces
sin preguntar. Si algo te bloquea, termina todas las partes que no dependen de eso y di exactamente qué quedó
fuera y por qué.
```

**Por qué ayuda.** Los auditores de esta casa corren en paralelo y nadie les contesta. Un agente que termina con
«¿quieres que siga con el lote?» entrega media auditoría, y el orquestador lo nota recién al leerla. La
excepción de l. 811 refuerza «auditar no es arreglar» con el texto que el modelo fue ajustado a respetar. La última
frase del bloque (l. 815) importa acá porque los auditores de S159 sí despachan workflows de sólo lectura (`n`
l. 7-9). La frase final en español es el párrafo de l. 826 («If one part turns out to be blocked, complete every
other part in full and say exactly what you left out and why»), adaptado.

### M2 (ALTO). Sacar la ruta de S134 del bloque canónico y nombrar las acciones adyacentes que no se hacen

**Hoy.** PRE l. 19-21: «No modifiques ningún archivo del repositorio; los scripts de medición que escribas van a
`experiments/_s134_audit/` y a ningún otro lado.» El bloque se pega «entero, sin resumir» (PRE l. 5-6), así que
hoy le dice a cada auditor que guarde en la carpeta de una auditoría de hace 25 sesiones. Los auditores de hoy lo
ignoraron porque el coordinador les dio otra carpeta (`cob` l. 4, `geo` l. 5), o sea que el bloque y el prompt se
contradicen en cada lanzamiento. Además el bloque no dice qué hacer con un defecto que el auditor ve fuera de su eje.

**La guía.** F51, sección «Keep changes and tests to what the task asks for», l. 841: con la instrucción «unrequested
additions and committed test code drop substantially with no measurable change in task success». El texto (l. 844):
«If, while working or testing, you find a pre-existing bug, a performance concern, or behavior the task doesn't
mention, don't fix, optimize or extend it in this change unless the requested behavior cannot work without it;
report it as a follow-up in your summary.» Y l. 828: «Something else you notice worth doing ... is a suggestion to
make at the end, not a change to make».

**Texto para pegar** (reemplaza PRE l. 19-22):

```text
Límite: auditar no es arreglar. No modificas ningún archivo fuera de «CARPETA» (ruta absoluta que da quien
orquesta en cada tarea; si no la dio, es la carpeta de tu informe). Ahí van tus scripts, con su salida al lado:
son el instrumento y se quedan (no los borres al terminar ni los conviertas en tests del repositorio). Si al medir
ves un defecto fuera de tu eje, no lo persigas más allá de dejarlo reproducible: anótalo en SEGUIMIENTOS con
archivo:línea y confianza, y vuelve a tu eje. Tampoco "mejoras" el instrumento de otro, ni corriges una cita vieja
que encuentres mal: eso también es un seguimiento. Los arreglos los decide quien orquesta, en tareas aparte, con tag
defensivo y confirmación de Nicolás cuando toquen pipeline/ (regla A45).
```

**Por qué ayuda.** Una regla del bloque canónico que es falsa enseña al auditor que el bloque se puede desobedecer,
que es lo contrario de lo que el bloque necesita. La sección SEGUIMIENTOS separa lo que el auditor vio de pasada
de sus hallazgos, y así el verificador no los mezcla. El paréntesis sobre no borrar scripts resuelve una tensión
real con F51 (ver §3, punto 3).

### M3 (ALTO). Quitar «un informe corto» del preámbulo: choca con «cobertura primero»

**Hoy.** PRE l. 29-30: «Un informe corto y todo sólido vale más que uno largo con relleno.» Y PRE l. 49-50:
«Cobertura primero: reporta todo lo que encuentres con su confianza y gravedad; el filtrado lo hace otro.» GMA
l. 138-139: «un filtro de severidad en el prompt deprime el recall».

**La guía.** Ninguna de las tres guías pide brevedad para informes de hallazgos. F51 l. 836 (resumen de
compactación) dice, para un informe que otro va a usar: «Be complete on these even at the cost of length; keep
everything else concise.» F5N l. 43: «Being readable and being concise are different things, and readability matters
more.» Y BP l. 35: «If you want "above and beyond" behavior, explicitly request it rather than relying on the model
to infer this from vague prompts.»

**Texto para pegar** (reemplaza la última frase de PRE l. 29-30):

```text
Sin relleno no quiere decir corto: cada hallazgo y cada SOSPECHA entran, aunque el informe salga largo. Lo que
sobra es la prosa alrededor, no los hallazgos.
```

**Por qué ayuda.** Un modelo que lee «corto vale más» en la misma página que «reporta todo» tiene que elegir, y
elegir corto es justamente el filtro que GMA l. 139 dice que deprime el recall. Es la clase de instrucción que el
modelo sigue «con alta fidelidad» (F5N l. 23) en la dirección equivocada.

### M4 (ALTO). Tabla de modelo y esfuerzo por tipo de tarea, una sola, y que el informe declare cuál usó

**Hoy.** GMA l. 160-161: «censos exhaustivos → Fable; decidir qué es correcto y verificar lo crítico → Opus;
paridad mecánica y documentación → Sonnet. Effort alto para semántica; bajo/medio para lo mecánico.» PRE l. 69-70
dice otra cosa: «censos exhaustivos y semántica física → Fable, effort alto; decidir qué es correcto y verificar lo
crítico → Opus». O sea que la semántica física es de Opus en una y de Fable en la otra. Ninguna de las dos dice qué
hacer con una búsqueda bibliográfica, y ninguna pide anotar el modelo y el esfuerzo usados.

**La guía.** F51 «Consider all effort levels», l. 34: «Start at the default effort level, `high`, then test the other
levels ... against your own evals. Effort is the primary control for trading off intelligence, latency, and cost».
l. 36: «At `medium`, results roughly match Claude Fable 5 at lower cost ... At `low`, Claude Fable 5.1 is often
competitive with Claude Opus and Claude Sonnet models on cost per task while scoring higher, so include it in the
comparison wherever you'd otherwise run a smaller model at a higher effort level.» F51 «Search triggering at low
effort», l. 849: «At `low` effort, Claude Fable 5.1 is less likely than Claude Fable 5 to call a search or retrieval
tool, and more likely to answer from memory.» F51 l. 875: a `xhigh` y `max` «it may draft much of that deliverable in
its thinking and then write it out again as the reply»; recomienda «run requests like these at `high`». BP l. 779,
sobre Opus 5: «verification instructions carried over from prompts tuned for earlier models can cause
over-verification ... remove these instructions rather than rewriting them».

En Claude Code, según la definición de la herramienta Agent de esta sesión (no es un archivo), el subagente acepta
`model` (sonnet, opus, haiku, fable) y `effort` (low a max), y un `fork` ignora el modelo.

**Texto para pegar** (reemplaza GMA l. 160-161 y PRE l. 69-70, la misma tabla en los dos sitios):

```text
Modelo y esfuerzo por tipo de tarea (punto de partida, no resultado medido; ver la última fila):

| tarea | modelo | esfuerzo | por qué |
|---|---|---|---|
| Censo exhaustivo (barrer muchas fuentes con una regla, clasificar, contar) | Fable | high; medium sólo si una corrida a medium dio la misma tabla | la guía de Fable 5.1 dice que a medium rinde como Fable 5 más barato; el censo vive del recall |
| Semántica física: decidir si un mecanismo es real, atribuir una causa, leer un paper contra el código | Fable | high; xhigh sólo en el frente más difícil y con el informe corto de largo | xhigh redacta el entregable dos veces si es largo |
| Verificador con contexto limpio | Fable high, o Opus si el auditor fue Fable | high | cambiar de modelo evita que el verificador herede el mismo sesgo de lectura (juicio propio, no de la guía); con Opus 5, no agregar "revisa tu respuesta", la regla de anclar a tool results basta |
| Paridad mecánica: remapear archivo:línea, contar guiones, aplicar una marca ya decidida | Sonnet low, o Fable low | low | Fable 5.1 a low compite con Opus y Sonnet en costo por tarea |
| Búsqueda bibliográfica, verificación de citas, "¿qué dice el paper X?" | Fable o Opus | high, nunca low | a low Fable 5.1 busca menos y contesta de memoria |
| Registro obligatorio | | | el informe declara en su encabezado modelo y esfuerzo; sin eso no hay con qué comparar después |
```

**Por qué ayuda.** Hoy el orquestador elige entre dos tablas que no coinciden. La guía de Fable 5.1 insiste en que
la tabla se calibra con evals propias (l. 34), y este workspace no tiene ninguna: anotar modelo y esfuerzo en cada
informe es la forma barata de juntar ese eval sin correr nada extra. La fila de bibliografía cierra el agujero más
caro: CLAUDE.md de VRP Chile ya registra citas corruptas (A76, y la «Coppola 2015» de la regla del NTI, que resultó ser
Heap et al.), y la guía dice que a `low` el modelo busca menos.

### M5 (ALTO). Pedir el informe con forma fija para que otro lo filtre, y con el resultado primero

**Hoy.** PRE l. 40-47 da el formato de cada hallazgo (título, archivo:línea, qué pasa, cómo se ve, cómo
reproducir, confianza, gravedad). GMA l. 146-147: el verificador funde duplicados y asigna IDs, y los auditores
numeran en rangos provisionales. Pero el preámbulo no pide los IDs, no pide abrir con el resultado ni pide un
archivo tabular aparte, y cada informe de hoy armó su propio encabezado (comparar `cob` l. 1-25, `p1` l. 1-27,
`geo` l. 1-31).

**La guía.** BP «State management best practices», l. 844: «When tracking structured information (like test results
or task status), use JSON or other structured formats to help Claude understand schema requirements.» BP l. 41: «Be
specific about the desired output format and constraints.» F5N l. 42-43: «Lead with the outcome. Your first sentence
after finishing should answer "what happened" or "what did you find".» F51 l. 51: «Close with a short recap that
stands on its own [guion del original cambiado] what you found, what you did, and what's next, so a reader who only
sees the last message has the full picture.»

**Texto para pegar** (agregar después de PRE l. 50):

```text
Forma del informe, para que otro lo pueda filtrar sin releerte:
1. Encabezado: fecha y hora del servidor; commit sobre el que mediste; modelo y esfuerzo con que corriste;
   CARPETA; qué NO miraste (para que tu silencio no se lea como "todo bien").
2. "En una pantalla": el resultado primero, en cinco líneas o menos.
3. Hallazgos con ID provisional en el rango «RANGO» (por ejemplo 171 a 189), cada uno con los campos de arriba
   en ese orden y con esos nombres exactos.
4. SEGUIMIENTOS (lo que viste fuera de tu eje), VERIFICADO LIMPIO y SIN DATO, en secciones separadas.
5. Además, `hallazgos.csv` en CARPETA, una fila por hallazgo, con columnas:
   id,titulo,archivo_linea,confianza,gravedad,eje,comando_reproduccion,salida_cruda
   (salida_cruda es la ruta del archivo con la salida del script, no el número).
Tu último mensaje al orquestador repite el punto 2 y la ruta absoluta del informe: es lo único que él lee primero.
```

**Por qué ayuda.** El verificador y el orquestador trabajan sobre diez informes a la vez (S159 tiene `cob`, `geo`,
`m`, `n`, `o1`, `p1`, `p2`, `p3`, `pareo_modis` y `chillan_modis`). Con campos de nombre fijo y un CSV, fundir
duplicados, ordenar por gravedad o sacar todas las SOSPECHA es un script, no una relectura. «Qué NO miraste» viene de
PCB l. 465-467 («una auditoría que sólo leyó fuentes tiene que declarar que no miró ninguna salida»), que hoy vive en
la plantilla y no en el preámbulo. El último párrafo sirve porque F51 l. 42 dice que Fable 5.1 escribe menos texto
para el usuario en cadenas largas y que su mensaje final puede cubrir «only the last step rather than the whole task».

### M6 (ALTO para auditorías bibliográficas, MEDIO en general). Pedir citas marcadas y con localizador

**Hoy.** PRE no dice cómo citar una fuente escrita. El formato exige archivo:línea o script:salida (l. 42), que sirve
para código y no para un PDF. La regla de renderizar la página vive en CLAUDE.md de VRP Chile (A95) y el auditor `p1`
la cumplió porque el coordinador se la pidió (`p1` l. 4-5).

**La guía.** F51 «Quoting retrieved sources», l. 786: «When summarizing documents, Claude Fable 5.1 is more likely than
Claude Fable 5 to reproduce passages of the source text without marking them as quotations. To address this, add one
complete example of a correct response». BP «Long context prompting», l. 272: «For long document tasks, ask Claude to
quote relevant parts of the documents first before carrying out its task.» BP l. 80: «Examples are one of the most
reliable ways to steer Claude's output format».

**Texto para pegar** (agregar al formato de hallazgo, PRE l. 42, y usar el ejemplo tal cual):

```text
Cita de una fuente escrita (paper, manual, ATBD, documento del repo): toda frase copiada va entre comillas, con
autor y año, página impresa (y la del PDF si difieren), párrafo, figura, tabla o ecuación, y cómo la leíste
(RENDER si miraste la página como imagen, TEXTO si leíste la capa de texto). Lo que no está entre comillas es
paráfrasis tuya y se nota en la redacción. Si no encuentras el pasaje, escribe SIN LOCALIZAR; nunca reconstruyas
una cita de memoria.

<example>
Afirmación: el Test 1 es por píxel y no integra el ROI.
Cita: Coppola et al. 2016a, p. impresa 6, §«Test 1», RENDER: «[frase literal del paper]».
Por qué es correcta: la frase copiada está entre comillas y dice dónde está; la conclusión ("por píxel, no
integrada") va fuera de las comillas, con palabras del auditor.
</example>
```

(El ejemplo deja la frase literal como hueco a propósito: no la leí en esta sesión y no la invento.)

**Por qué ayuda.** En este proyecto una cita mal transcrita no es un detalle de estilo: en CLAUDE.md de VRP Chile A76 cayó por una cita
que no decía lo que se le atribuía, y la «Coppola 2015» de la regla del NTI era de otro autor. Con Fable 5.1 el riesgo sube, según l. 786, porque
tiende a copiar sin comillas, y una paráfrasis sin marcar no se distingue de una cita.

### M7 (ALTO). Un bloque propio para el verificador, en vez de dos líneas para el orquestador

**Hoy.** PRE l. 63-64 y GMA l. 140-147 describen al verificador desde fuera: «recibe sólo título + archivo:línea,
relee, enumera los caminos, pone su gravedad», y «re-corre los bancos». No hay texto para pegarle al verificador.
El verificador de Chillán, que lo hizo bien, enumeró sus caminos de ruptura antes de leer (`chillan_modis\verificador`
l. 7-11), así que el patrón funciona cuando el coordinador lo escribe.

**La guía.** BP l. 60 (contexto y motivo), F5N l. 30 (subagentes frescos), BP l. 899: «Provide clear success
criteria». Y F5N l. 28 advierte para Fable 5: «NO le pidas que transcriba o "muestre su razonamiento" en la respuesta
→ dispara el refusal `reasoning_extraction`». F51 no menciona ese refusal; que siga en 5.1 es SOSPECHA, así que
conviene pedir los caminos como entregable, no como razonamiento.

**Texto para pegar** (nuevo, en PRE después de «hasta acá»; va junto con el preámbulo, no en su lugar):

```text
Eres el verificador de un hallazgo que encontró otro. No ves su razonamiento a propósito: si lo vieras,
heredarías sus supuestos. Recibes el título, el archivo:línea o script:salida, y nada más.
1. Antes de releer nada, escribe en tu informe la lista de caminos por los que esa afirmación podría estar mal
   (el instrumento mide otra cosa, la ventana no contiene el fenómeno, el flag se lee de otro lado, el caller
   transforma el argumento, un segundo camino que el arreglo no cubre, la copia local está atrasada).
2. Comprueba cada camino contra el código y los datos de hoy. Re-corre el script del auditor si existe; si no
   corre, eso ya es un resultado.
3. Veredicto por afirmación: CONFIRMADO, CONFIRMADO EN PARTE (di qué parte), REFUTADO o SIN DATO, con tu propia
   gravedad 1-5 y la evidencia de esta sesión.
4. Lo que encuentres de nuevo va como hallazgo propio, en tu rango de ID «RANGO_V». Funde duplicados entre
   auditores y dilo.
Éxito no es confirmar: es que cada veredicto se sostenga ante un tercero que repita tus comandos.
```

**Por qué ayuda.** GMA l. 141-142 dice que en seis verificaciones el verificador encontró además hallazgos propios; eso
pasa cuando se le pide buscar, y este bloque se lo pide en el punto 4. La última frase es el criterio de éxito que BP
l. 899 recomienda dar, y evita que «verificar» se lea como «confirmar».

### M8 (MEDIO). Cuando el auditor corre desatendido: progreso escrito al disco, no en el chat

**Hoy.** GMA l. 152-156: los agentes largos mueren por límite de la API, y su estado tiene que vivir en git y en un
informe incremental. Eso está bien. Falta decirle al auditor que escriba el informe a medida, no al final.

**La guía.** F51 l. 42: Fable 5.1 escribe menos actualizaciones, y más a mayor esfuerzo y en cadenas largas. l. 46:
«audit your prompt for instructions that suppress narration ... Remove lines like that before adding anything.» BP
l. 803-810, para arneses que compactan: «As you approach your token budget limit, save your current progress and state
to memory before the context window refreshes.»

**Texto para pegar** (en el bloque de autonomía de M1, al final):

```text
Escribe el informe en CARPETA a medida que avanzas, no al final: cada hallazgo entra al archivo apenas lo
confirmas o lo dejas como SOSPECHA. Si la sesión se corta, lo que esté en el disco es lo que queda.
```

**Por qué ayuda.** Pone en el prompt del auditor lo que GMA l. 154 ya pide al orquestador. Y no choca con l. 46: no
suprime la narración, la manda a un archivo que sobrevive.

### M9 (MEDIO). Búsqueda bibliográfica: obligar a buscar lo que el modelo «ya sabe»

**Hoy.** GMA no tiene nada para auditorías bibliográficas; PCB l. 268-271 remite a `GUIA_MAESTRA_INVESTIGACION.md`.

**La guía.** F51 l. 854 (texto propuesto por Anthropic): «When a query centers on a name you do not confidently
recognize, or recognize from a fast-moving area ... the name itself is the thing to verify: search before answering,
and include the name as the user wrote it in at least one query alongside any reformulations. This holds even when you
have some background on it [guion del original cambiado] partial background is exactly what makes an out-of-date
answer sound authoritative, so familiarity is not a reason to skip the search.»

**Texto para pegar** (en prompts de auditoría bibliográfica):

```text
Que reconozcas un paper, un autor, un umbral o una sigla no quiere decir que sepas qué dice la página. Antes de
afirmar qué dice una fuente, búscala primero en el disco (documentacion/, BIBLIOGRAPHY_SYNTHESIS.md) y después
afuera, con el nombre tal como aparece en el repo en al menos una búsqueda. Conocerla a medias es justo lo que hace
que una respuesta vieja suene segura.
```

**Por qué ayuda.** Es el fallo de S36 que CLAUDE.md de VRP Chile documenta (buscar online un PDF que estaba en
`documentacion/`) y el de las citas corruptas que registra (A76). La guía dice que el riesgo crece a esfuerzo bajo, que es donde
el orquestador tiende a poner las tareas «fáciles».

### M10 (MEDIO). Una línea contra la prosa recargada, junto a la de los guiones

**Hoy.** El preámbulo no pide nada sobre el estilo. La regla de los guiones vive en CLAUDE.md global. Los informes de
hoy salen densos: el punto 1 de `n` l. 14-21 es un solo párrafo de ocho líneas con tres cifras encadenadas.

**La guía.** F51 «Writing density», l. 764: «its prose is denser than Claude Fable 5's: sentences run longer and there
are fewer paragraph breaks». l. 770-774: «The short version also tends to work: Please remove all mannered prose.»

**Texto para pegar** (al final del preámbulo):

```text
Escribe en frases cortas, una idea por frase, en español de Chile y sin guiones largos ni medios. Please remove all
mannered prose.
```

**Por qué ayuda.** Quien filtra el informe es Nicolás, leyendo diez a la vez. La frase en inglés es la que la guía
dice que funciona sola; la parte en español pone la regla del workspace donde el auditor la ve.

### M11 (MEDIO-BAJO). Estructurar el prompt del coordinador con etiquetas

**Hoy.** El coordinador separa con encabezados («=== Por qué ===», «=== Qué hacer ===», «=== Entregable ===»; es la
forma del prompt de esta misma tarea). Funciona, pero mezcla el preámbulo, el material y la tarea en un solo texto.

**La guía.** BP «Structure prompts with XML tags», l. 94: «XML tags help Claude parse complex prompts unambiguously,
especially when your prompt mixes instructions, context, examples, and variable inputs.» BP l. 243: «Put longform data
at the top ... above your query, instructions, and examples», con hasta 30 % de mejora (l. 246) para material de más
de 20.000 tokens (l. 241).

**Texto para pegar** (esqueleto del prompt de auditor):

```text
<preambulo_auditor> (el bloque, entero) </preambulo_auditor>
<material> (rutas, o el material largo pegado, ARRIBA de la tarea) </material>
<tarea> por qué este frente, qué decide, CARPETA, RANGO, qué está fuera de alcance </tarea>
<autonomia> (M1, sólo si corre desatendido) </autonomia>
```

**Por qué ayuda.** Deja claro qué parte es regla fija y qué parte cambia por tarea, que es lo que permitió que la ruta
de S134 sobreviviera en el bloque sin que nadie la viera (M2).

### M12 (BAJO). A esfuerzo xhigh o max con informe largo, avisar el límite

**Hoy.** Nada. **La guía.** F51 l. 877-883: subir `max_tokens` y agregar una nota («Composing an entire output or
deliverable in full as reasoning and then again as a reply would double the length of the turn without improving the
result, so don't do that.»). En Claude Code el subagente no expone `max_tokens` (definición de la herramienta Agent
de esta sesión), así que lo práctico es la recomendación de l. 875: correr los informes largos a `high`. Ya queda
dicho en la tabla de M4.

---

## 3. Lo que las guías de prompting dicen que la guía de auditorías hace mal o de más

1. **(MEDIO-ALTO) La plantilla prescribe recorrer 27 ejes «uno por uno».** PCB l. 255: «Recorre **las tres lentes**,
   eje por eje.» PCB l. 477: «Ejes propios del código, recorrer uno por uno». BP l. 776: «Prefer general instructions
   over prescriptive steps. A prompt like "think thoroughly" often produces better reasoning than a hand-written
   step-by-step plan.» F5N l. 31: las skills «muy prescriptivas (hechas para modelos previos) pueden **degradarlo**».
   La propia plantilla ya lo sospecha (PCB l. 31-34: la ganancia «viene de unas quince líneas ... y **no** de los 27
   ejes, que son donde nace la inflación»). Propuesta: que los ejes sean un menú de dónde mirar y que el auditor
   declare cuáles cubrió y cuáles no, en vez de una pasada obligatoria por cada uno. Las quince líneas que la
   plantilla nombra (permiso de volver vacío, caso concreto, separar oportunidades, mecanismo de cierre) se quedan.
   Esto no es un resultado medido: el experimento a ciegas de PCB l. 28-30 sigue sin correrse, y es la forma de zanjarlo.

2. **(MEDIO) Mayúsculas y «SIEMPRE» en el bloque.** PRE l. 24 («REGLA OBLIGATORIA»), l. 52 («Cierra SIEMPRE»). BP
   l. 488: «Where you might have said "CRITICAL: You MUST use this tool when...", you can use more normal prompting»,
   porque los modelos nuevos sobre-reaccionan. En un preámbulo de 40 líneas el daño probable es chico, y las dos
   reglas traen su porqué al lado, que es lo que BP l. 60-76 pide. Propuesta: bajar el tono a frase normal y dejar el
   porqué. No lo pongo en ALTO porque no hay evidencia en estos informes de sobre-reacción.

3. **(MEDIO) Tensión entre «el instrumento va al repo» y lo que Fable 5.1 hace por defecto.** GMA l. 62-63: «Un
   instrumento que sirvió para medir un hallazgo va al repo el mismo día.» El bloque oficial de F51 l. 844 dice
   «scratch scripts and quick checks need not be kept», y BP l. 946-949 sugiere borrar los archivos temporales al
   terminar. Si alguien pega esos bloques oficiales sin adaptar, el auditor borra justo lo que la guía de auditorías
   quiere conservar. Lo resuelve el paréntesis de M2 («no los borres al terminar»); conviene que GMA §5 lo diga en
   voz alta para que nadie copie el bloque oficial tal cual.

4. **(MEDIO) Dos tablas de modelos que no coinciden, y una afirmación sin medición.** GMA l. 160 (semántica → Opus) y
   PRE l. 69 (semántica física → Fable). Y GMA l. 129: la disciplina «funciona con Claude Fable 5.1, Opus y Sonnet», que
   ninguna guía de prompting respalda y que el workspace no midió. F51 l. 34 pide calibrar con evals propias. Se
   corrige con M4.

5. **(BAJO) Instrucciones de auto-revisión con Opus 5.** BP l. 779: con Opus 5 las instrucciones genéricas de
   verificación «can cause over-verification». La regla del preámbulo de anclar a tool results no es eso, y debe
   quedarse. Lo que sobra, si el verificador es Opus 5, es agregarle «revisa tu respuesta dos veces». Que aplique igual
   a Opus 5.5 es SOSPECHA.

6. **(BAJO) Las notas previas que la guía usa como respaldo.** F5N trata de Fable 5, no de 5.1 (l. 1-3), trae un
   bloque de autonomía más corto que el oficial de 5.1 (F5N l. 61 frente a F51 l. 809-815) y está escrita con voseo
   (F5N l. 22: «Decile *qué* querés»). Si GMA la sigue citando, que apunte primero a F51 para los bloques textuales.

7. **(BAJO, fuera de la guía de auditorías) «Si dudas, invócala igual».** Está en CLAUDE.md global (Tool selection
   protocol, punto 3) y en el de VRP Chile, no en GMA. BP l. 527: «Instructions like "If in doubt, use [tool]" will
   cause overtriggering.» Lo anoto sólo porque un auditor recibe esas reglas en su contexto; decidir si cambia es de
   Nicolás.

Lo que no encontré: ninguna instrucción antiformato en el preámbulo (F51 l. 778 dice que Fable 5.1 formatea menos y
que esas reglas sobran), ni frases que pidan guardar todo para el mensaje final (F51 l. 46). En eso el preámbulo
está limpio.
