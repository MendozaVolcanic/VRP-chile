# Plan de auditoría S158: todo lo hecho, medido contra el código de MIROVA

> **Estado: PLAN, sin lanzar.** S158, 2026-10-21. Pedido de Nicolás: «revisa si estos datos nuevos se pueden usar para
> realizar una auditoria profunda de todo lo que hemos hecho [...] piensa en el prompt que cubra todo y revisa los
> prompts que se usaron anteriormente [...] esta nueva informacion puede ser lo que necesitabamos para terminar este
> trabajo». Lanzar los auditores es decisión de Nicolás (escala y costo, §8).
>
> Fuentes del diseño: `GUIA_MAESTRA_AUDITORIAS.md` (workspace), `docs/_prompts/PREAMBULO-AUDITOR.md`,
> `docs/PROTOCOLO_AUDITORIA_PROFUNDA.md` (técnicas T1 a T9, reglas A, B y C), las auditorías S138, S146, S149, S150 y
> S155 (resumidas en el §1), y las guías oficiales de prompting de Claude leídas hoy en platform.claude.com («Prompting
> best practices» y «Prompting Claude Opus 5.5»; las copias del workspace son anteriores a Opus 5.5).

## 0. Por qué ahora sí se puede, y qué no se puede

Hasta S157 toda auditoría comparó contra MIROVA usando su texto (papers), sus resultados (CSV del scraper, OSF v2.5,
TIF) o sus imágenes. Ninguna tuvo el eje **«nuestro código contra el código de MIROVA»**, porque no existía (lo dice el
propio registro de ejes del protocolo). Desde el 2026-07-24 existe para VIIRS 750 (OSF zm62w), y hoy se sumaron tres
varas más: la grilla UTM real de los TIF de MIROVA (§3.1 de `docs/DISENO_D17_REMUESTREO_UTM.md`), el dataset de
VIIRS 375 de Vulcano con Npix y radiancias (OSF jepv6) y la curva angular normalizada en el tiempo de la propia MIROVA
(§3.6 del mismo diseño).

**Lo que la auditoría puede decidir sin reprocesar nada**: qué afirmaciones del proyecto sobre «qué hace MIROVA» son
falsas, cuáles cierres se apoyaban en ellas, qué pruebas congelan premisas falsas, y cuánto sustrato tiene cada
diferencia en los datos ya publicados (los records guardan μ y σ de dNTI y dETI por pasada, la posición, la BT y el VRP
de cada píxel anómalo, pero **no** el dNTI ni el NTI de cada píxel).

**Lo que no puede decidir sin L1B**: el efecto exacto de cada diferencia en la publicación. Eso pide el oráculo (port a
Python del código de MIROVA, Fase 0) corrido sobre gránulos, y después A/B pre-registrados. La auditoría los diseña y
los ordena; no los reemplaza.

**Lo que no puede decidir nunca con estas varas**: MODIS y VIIRS 375 tienen sólo texto y resultados, no código. Para
ellos la auditoría separa lo estructural (trasladable con cita) de lo numérico (a medir contra la referencia, A115).

## 1. Lo que enseñaron las auditorías anteriores (y cómo entra en este plan)

| lección | dónde | cómo entra |
|---|---|---|
| el verificador con contexto limpio encuentra hallazgos propios (8 en S138, 3 en S150) | `docs/AUDIT_S138.md` l. 58 a 60; `docs/audit_s150/VERIFICADOR_AUDITORIA.md` | un verificador por cada dos frentes, que recibe sólo títulos y ubicaciones |
| auditores que inventaron una partición, no refrescaron la referencia o no reprodujeron sus factores | AUDIT_S138 l. 159 a 161; AUDIT_S155 l. 132 a 135 | referencia fijada por hash; todo número con script y salida cruda |
| instrumentos que no podían fallar (un `any` sobre lista vacía, el «0 fuga» de D9, controles que eran identidades) | AUDIT_S146 l. 24, 80, 113 a 115 | las dos preguntas del instrumento y un control positivo en cada medición |
| un mutante escribió en la carpeta real de records | AUDIT_S146 l. 137 y 138 | escritura sólo en la carpeta del frente |
| la rebaja no baja a los documentos hijos (S146, y otra vez en S150) | AUDIT_S146 l. 37 a 42; meta S150 F4 | un frente entero (F2) dedicado a la propagación |
| el censo por palabras clave es sólo un piso | AUDIT_S146 l. 173; AUDIT_S155 l. 167 | F2 declara sus comandos de búsqueda para que la cobertura se pueda auditar |
| S146 dio por «VERIFICADO LIMPIO» la Tabla 1 contra el paper de MODIS; contra el código de VIIRS 750 esa verificación no podía fallar | AUDIT_S146 l. 156 | todo VERIFICADO LIMPIO nombra contra qué vara se verificó |
| el preámbulo canónico manda los scripts a `experiments/_s134_audit/` (defecto parchado sólo en los prompts) | `docs/_prompts/PREAMBULO-AUDITOR.md` l. 20 | corregido en este PR: la carpeta la fija el alcance del frente |
| S155 no revisó `evaluar_fk.py` ni `libro_de_cuentas.py` | AUDIT_S155 l. 166 a 169 | entran en F5 |

## 2. Las perspectivas (una lente por auditor, con su sesgo declarado)

Idea de la skill de perspectivas múltiples: cada auditor parte de un supuesto distinto, para que lo que uno da por
sentado lo cuestione otro.

| frente | lente | supone | desconfía de |
|---|---|---|---|
| F1 | traductor literal | el código publicado es el operacional | cualquier diferencia entre su código y el nuestro, por chica que sea |
| F2 | historiador de decisiones | cada cierre fue razonable con lo que se sabía | los cierres que nadie reabrió cuando cambió la evidencia |
| F3 | volcanólogo térmico | la magnitud es física: foco sub-píxel, huella, cráter, nieve, fondo | un acuerdo numérico que no tiene mecanismo físico |
| F4 | estadístico de inferencia | sólo se sabe lo que se midió | trasladar a MODIS o VIIRS 375 lo que sólo está probado en VIIRS 750 |
| F5 | metrólogo | un número vale lo que vale su instrumento | los evaluadores, bancos y pruebas que dan verde por construcción |
| F6 | escéptico de la fuente | el código publicado puede no ser el operacional | confiar en un archivo «compacto» con comentarios que rotulan al revés |

## 3. Los frentes (disjuntos: un auditor por frente, cada uno con su carpeta)

**F1. El código de MIROVA, de la radiancia al tablero (VIIRS 750).** Extender la comparación de
`docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md` §3 a la cadena entera: entradas (calidad, saturación, píxel frío, escena
incompleta), detección (los dos pases, regiones, umbrales), magnitud y publicación (`store.py`, el predicado del
tablero ejecutado con node, A97). Para cada diferencia, su sustrato en los datos ya publicados (por ejemplo, en cuántas
pasadas de VIIRS 750 el mínimo de 0,02 de MIROVA fuera de la cumbre sería el que decide, porque μ + 10σ queda por
debajo; cuántos píxeles publicados caen fuera de la caja de 7 × 7 celdas; cuánta magnitud quita el recorte a cero).
Carpeta: `experiments/_s158_audit/f1/`.

**F2. El grafo de cierres contra el código.** Toda afirmación del proyecto sobre qué hace MIROVA, en
`docs/MIROVA_DIVERGENCES.md`, `docs/MISSION.md`, las reglas A del `CLAUDE.md` del proyecto, `docs/SINTOMAS.md`,
`docs/META_RULES_S80.md`, los pre-registros vivos y los guards de `tests/`: CONFIRMADA, REFUTADA o NO APLICA (no es
VIIRS 750, o el código no la cubre). Para cada refutada, quién la cita (A113) y qué frente o decisión apagó. Incluye
las pruebas que congelan una premisa que el código contradice. Carpeta: `experiments/_s158_audit/f2/`.

**F3. La física de la magnitud.** Con el código (fondo interpolado bajo un halo dilatado, sin recorte, suma de todos
los alertados), el OSF v2.5 (Npix, L_hot y L_bk por pasada de los volcanes chilenos en 2025), jepv6 y nuestros records:
por tipo de volcán (lago de lava de Villarrica, cráter profundo de Láscar, glaciar de Tupungatito, lacolito de Cordón
Caulle, nevados débiles), qué diferencia explica el déficit de nivel (0,6 a 0,8 cerca del nadir) y cuál la pendiente
con el cenit (S = 0,77). Separar lo que es física del objeto (oclusión, huella) de lo que es procesamiento.
Carpeta: `experiments/_s158_audit/f3/`.

**F4. Qué se traslada a MODIS y VIIRS 375.** Para cada elemento del código: ¿hay evidencia para los otros dos
sensores? Paper (Tabla 1 de MODIS), Coppola 2025 cap. 11 Tabla 2, Campus 2022 y 2024, Aveni 2024, Coppola 2026,
jepv6, OSF v2.5. Y, donde no la hay, cómo sacar el número de la referencia de MIROVA (A115) en vez de suponerlo.
Carpeta: `experiments/_s158_audit/f4/`.

**F5. Los instrumentos y los A/B en curso.** ¿Miden los evaluadores lo que el código dice que MIROVA hace?
`experiments/_s157_prereg_d25/` (el A/B en cola), `scripts/banco_paridad.py`, `scripts/clase_mirova.py`,
`scripts/libro_de_cuentas.py`, `experiments/_s151_prereg_fk_11/evaluar_fk.py` (no revisados en S155), el auto-audit y
la vigilancia de la sombra. Las dos preguntas del instrumento para cada uno. Carpeta: `experiments/_s158_audit/f5/`.

**F6. ¿Es este código el operacional?** Consistencia interna del repositorio publicado (README, comentarios, matriz de
ejemplo, CITATION), contra los papers del grupo y contra los productos publicados (TIF, OSF v2.5, CSV del scraper).
Qué partes del código se pueden contrastar con un resultado publicado de MIROVA y cuáles sólo con su palabra. Lo que
encuentre baja la confianza de F1 a F4 donde corresponda. Carpeta: `experiments/_s158_audit/f6/`.

**Verificadores (contexto limpio).** V1 para F1 y F6, V2 para F2 y F5, V3 para F3 y F4. Reciben sólo título,
archivo:línea o script:salida y gravedad de cada hallazgo de gravedad 3 o más; releen, re-corren los scripts, enumeran
los caminos por los que la afirmación podría estar mal, ponen su propia gravedad, funden duplicados y pueden agregar
hallazgos propios (numerados aparte).

**Fase 0 (antes de los auditores, si no existe todavía):** el port a Python del código de MIROVA como oráculo, con sus
pruebas sobre la matriz de ejemplo. Lo usan F1, F5 y F6. Se puede hacer en esta sesión o en la que falló por disco.

## 4. El bloque común (se pega igual en los seis prompts y en los tres verificadores)

Orden del prompt: **(a)** el bloque canónico de `docs/_prompts/PREAMBULO-AUDITOR.md`, entero, sin resumir; **(b)** el
bloque de abajo; **(c)** el alcance del frente (§5). El orden sigue la guía oficial: contexto y porqué primero,
documentos largos antes de la tarea, la tarea al final.

```text
La vara nueva. Desde el 2026-07-24 MIROVA publica su código operacional de detección y VRP de VIIRS 750 (OSF zm62w,
MIT); copia verificada por hash en experiments/_s158_d17_diseno/osf_codigo_mirova/. Antes de escribir cualquier cosa
sobre qué hace MIROVA, lee esos dos .m: lo que diga un documento del proyecto, un paper o tu memoria sobre MIROVA vale
menos que lo que dice el código, para VIIRS 750 (decisión de Nicolás, 2026-10-21, registrada en docs/MISSION.md).
Para MODIS y VIIRS 375 no hay código: ahí manda el paper, y una afirmación trasladada desde VIIRS 750 se marca
TRASLADADA, no CONFIRMADA. Ojo con dos trampas ya medidas: los comentarios del .m rotulan al revés el ROI de cumbre
(en la matriz de ejemplo BOX==2 es la caja de 7 x 7), y la versión publicada se declara compacta, no completa.
Contexto ya medido, que no tienes que rehacer: docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md (13 puntos comparados) y
docs/DISENO_D17_REMUESTREO_UTM.md §3 (grilla, firma del remuestreo, curva angular). Si encuentras algo que los
contradice, eso es un hallazgo.

Investiga antes de afirmar. No especules sobre código que no abriste ni sobre datos que no leíste. Los records están
en data/mirova_equivalent/<volcán>.json; la referencia de MIROVA, en latest_consolidado.csv y
data/mirova_reference/mirova_v1_snapshot/; antes de usar una ventana de la referencia corre
scripts/calidad_referencia_mirova.py (regla A119). Los PDF están en
C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\documentacion\ (no en el worktree); una cita de
paper se lee renderizando la página a imagen (regla A95), nunca de la capa de texto.

Trabajas solo. Nadie va a contestar preguntas a mitad de camino, así que no preguntes «¿sigo?»: haz el trabajo del
alcance hasta el final. No cierres tu turno con un resumen que anuncia el paso siguiente sin darlo; si te queda algo
del alcance, hazlo. Detente sólo si algo te lo impide de verdad, y dilo. Escribe tu informe en tu carpeta a medida que
avanzas (la sesión puede cortarse): un archivo INFORME.md con los hallazgos en el formato del preámbulo, la sección
VERIFICADO LIMPIO (cada ítem dice contra qué vara se verificó) y, al final, «Lo que no pude medir» con la razón.

Límites: no edites nada fuera de tu carpeta; no toques pipeline/, data/, frontend/ ni docs/; no despaches workflows;
no hagas git push ni commits. Si un script necesita escribir, que escriba en tu carpeta. Si encuentras un defecto
fuera de tu alcance, anótalo en una sección «Fuera de alcance» y sigue.

Escribe en español de Chile, sin guiones largos ni medios, frases directas, sin metáforas. El porqué físico antes que
el código. Todo número lleva script, salida cruda, denominador y ventana.
```

## 5. El alcance de cada frente (se agrega después del bloque común)

Escrito como objetivo y límites, no como checklist (la guía oficial: sobre-prescribir degrada).

**F1.** «Eres el traductor literal. Tu pregunta: ¿en qué difiere, paso por paso, lo que hace nuestro pipeline con un
gránulo de VIIRS 750 de lo que haría el código de MIROVA con el mismo gránulo, desde la radiancia hasta lo que ve el
operador en el tablero? Por qué importa: el proyecto se propuso ser un clon literal y por primera vez hay un original
contra el cual comparar línea por línea. Parte de la tabla de 13 puntos del informe S158 y complétala: lo que esa tabla
no cubre (entradas, calidad, saturación, el paso del record al tablero) es tu trabajo principal. Para cada diferencia,
mide su sustrato en los datos ya publicados con un script, y di si sube o baja la publicación y la magnitud. Si existe
el oráculo (experiments/_s158_oraculo_mirova/), úsalo; si no, dilo.»

**F2.** «Eres el historiador de decisiones. Tu pregunta: ¿qué cierres, reglas, divergencias declaradas y pruebas del
proyecto descansan en una afirmación sobre MIROVA que el código de VIIRS 750 confirma, refuta o no cubre? Por qué
importa: las auditorías S146 y S150 encontraron que una rebaja no baja a los documentos que la citan, y un cierre falso
apaga los frentes que cuelgan de él. Haz el censo con comandos de búsqueda declarados (para que se pueda auditar la
cobertura) y entrega una tabla afirmación · dónde · vara · veredicto · quién la cita · qué apagó. Incluye las pruebas
de tests/ que fijan una premisa contradicha.»

**F3.** «Eres volcanólogo térmico. Tu pregunta: ¿qué explica físicamente el déficit de magnitud contra MIROVA en cada
tipo de volcán, separando lo que es del objeto (huella, oclusión en cráter profundo, nieve, lago de lava) de lo que es
del procesamiento (fondo, recorte, selección, suma)? Por qué importa: el operador lee la magnitud para decidir si un
volcán cambió, y con K el déficit es de nivel (0,6 a 0,8 cerca del nadir) más que de pendiente. Usa el código (fondo
interpolado bajo un halo, sin recorte, suma de todos los alertados), el OSF v2.5 de 2025 (Npix, L_hot y L_bk por
pasada), jepv6 y nuestros records. Para cada mecanismo, una predicción que lo distinga de los otros y la medición.»

**F4.** «Eres estadístico de inferencia. Tu pregunta: de todo lo que el código de VIIRS 750 enseña, ¿qué se puede
trasladar a MODIS y a VIIRS 375 con evidencia, y qué no? Por qué importa: el error de juicio que el código reveló fue
justamente trasladar números de MODIS a VIIRS. Para cada elemento, la evidencia por sensor con su localizador, y donde
falte, el diseño de una medición contra la referencia de MIROVA que dé el número (por ejemplo, un umbral inferido de la
distribución de lo que MIROVA publica), con su poder estadístico (técnica T8).»

**F5.** «Eres metrólogo. Tu pregunta: ¿miden los evaluadores, bancos, pre-registros y vigilantes del proyecto lo que el
código dice que MIROVA hace? Por qué importa: un A/B que compara contra una idea equivocada de MIROVA da un veredicto
confiable sobre la pregunta equivocada, y el A/B de D25 está en cola. Para cada instrumento, las dos preguntas del
instrumento, su control positivo y un caso que debería hacerlo fallar. Empieza por el pre-registro de D25 y su
evaluador.»

**F6.** «Eres el escéptico de la fuente. Tu pregunta: ¿cuánto podemos confiar en que el código publicado es el que
corre en MIROVA? Por qué importa: si el proyecto pasa a tratar ese código como la autoridad para VIIRS 750, un error de
la versión publicada se volvería un error nuestro. Contrasta el código con todo resultado publicado de MIROVA que lo
permita (OSF v2.5: la identidad del VRP y los Npix; los CSV del scraper; los TIF), con los papers del grupo y consigo
mismo (README, comentarios, ejemplo). Clasifica cada parte del código: contrastada con un resultado publicado, sólo con
un paper, o sólo con la palabra del autor.»

**Verificadores.** «Eres verificador con contexto limpio. No viste el trabajo de los auditores: recibes sólo la lista
de hallazgos (título, ubicación, gravedad). Para cada uno: relee la fuente, re-corre el script si lo hay, enumera los
caminos por los que la afirmación podría estar mal, y pon tu veredicto (CONFIRMADO, CON MATIZ, REFUTADO, NO
REPRODUCIBLE) y tu gravedad. Funde duplicados. Si encuentras algo propio, agrégalo numerado aparte (V-1, V-2...): en
este proyecto el verificador ha encontrado hallazgos propios en cada auditoría.»

## 6. Modelos, esfuerzo, escala y orden

- **Seis auditores y tres verificadores**: nueve agentes, dentro de la guía del entorno (menos de diez).
- Modelos (`docs/_prompts/PREAMBULO-AUDITOR.md`, notas): F2 y F4 son censos exhaustivos y van a Fable con esfuerzo
  alto; F1, F3 y F6 deciden qué es correcto y van a Opus con esfuerzo alto; F5 mezcla los dos. Los verificadores en
  Opus.
- Sin worktrees: los auditores sólo leen y escriben en su carpeta de este worktree, así que no necesitan copia propia
  (el disco tiene 15 GB libres y un worktree pide 25).
- Orden: Fase 0 (oráculo), después los seis auditores en paralelo, después los tres verificadores en paralelo, y la
  síntesis (`docs/AUDIT_S158.md`) la escribe quien orquesta, con la tabla de decisiones de Nicolás.
- Señal de tiempo (guía de Opus 5.5): cada prompt dice el presupuesto, unas dos horas por auditor.

## 7. Qué entrega

`docs/AUDIT_S158.md` con: hallazgos confirmados por gravedad; la tabla de F2 (cierres que caen, quién los cita); la
cola de pruebas (qué A/B o probe decide cada hallazgo, con prioridad); la tabla de decisiones de Nicolás con
recomendación; y la lista de lo que la auditoría no pudo medir y por qué. Las marcas A113 de lo que caiga van en el
mismo PR que el informe.

## 8. Lo que decide Nicolás antes de lanzar

1. Si se lanza ahora (nueve agentes, varias horas de cómputo de agentes) o primero la Fase 0.
2. Si la Fase 0 la hago en esta sesión (sin worktree nuevo) o se reintenta la sesión que falló por disco.
3. Si algún frente sobra o falta.
