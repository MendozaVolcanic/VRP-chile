# C. Integración de A y B en la guía maestra de auditorías

2026-10-21. Archivos editados (sin git; el coordinador commitea):
- `C:\Users\nmend\OneDrive\Escritorio\claude\GUIA_MAESTRA_AUDITORIAS.md`: de 214 a 442 líneas.
- `C:\Users\nmend\OneDrive\Escritorio\claude\PLANTILLA_CAZA_DE_BRECHAS.md`: de 531 a 536 líneas (tres cambios chicos).

Insumos: `C:\vrp-trabajo\s159-pruebas\experiments\_s159\guia_auditorias\A_LECCIONES_PROYECTO.md` (A) y
`C:\vrp-trabajo\s159-pruebas\experiments\_s159\guia_auditorias\B_PROMPTING.md` (B).

Decisión de estructura: la sección nueva de experimentos va como **§3b** y no como §4, porque otros proyectos citan
la guía por número de sección (ARSAND `PROXIMA-SESION.md` cita §2 y §6; riesgomapas cita §5 y §8.1; OVDAS_datos_sinteticos
cita §0 y §8; VRP Chile cita §5, §7 y §8). Por la misma razón el título de §1 sigue diciendo «siete patrones»
(lo citan ARSAND y riesgomapas) y el patrón nuevo entra como párrafo debajo de la tabla, igual que el de
las constantes calibradas. Ningún número de sección ni de paso existente cambió de significado.

Guiones: la guía queda con 0 largos y 0 medios (traía 6 largos, en el título, en §3 y en §4; los reescribí al tocar esas
líneas). La plantilla traía 66 largos y 6 medios; quedan 65 y 6, todos en líneas que no toqué; lo agregado tiene 0.
Contado con Python (U+2014 y U+2013).

## 1. Qué entró y dónde

### De A (lecciones del proyecto)

| lección | sección de la guía |
|---|---|
| L1 gemelo idéntico es identidad, no nulo | §3 viñeta 2; §3b fila 5 |
| L2 el nulo de un control se mide; control verde sobre instrumento refutado está roto | §3 viñeta 1 |
| L3 nulo por signo de la diferencia, por bloque | §3b fila 5 |
| L4 mutaciones con control, atrapada sólo por aserción | §3 viñeta 3 |
| L5 placebo | §3b fila 6 |
| L6 curva de poder, barajado por estrato | §3b fila 7 |
| L7 población condicionada; A109 mismo insumo | §3b fila 4 |
| L8 censo antes de ponderar; techo físico | §3b fila 3 |
| L9 mismo número de oportunidades | §3b fila 12 |
| L10 conteo absoluto en corpus vivo, denominador y ventana | §7 |
| L11 unidad en que el usuario vive el efecto; caso de referencia no prioriza | §6 paso 1 |
| L12 régimen; frontera en la fecha de los datos | §3b fila 10 |
| L13 cobertura pareja antes del veredicto | §3b fila 2 |
| L14 la referencia externa cambia con el tiempo | §3b fila 14 |
| L15 distribución, no mediana; Simpson | §3b fila 13 |
| L16 saturación | §3b fila 9 |
| L17 contrafactual a todos los consumidores | §1 patrón 6 (ampliado) y §3b fila 8 |
| L18 pre-registro | §3b fila 1 y «pre-registro mínimo» |
| L19 nombre del veredicto | §3, regla de la etiqueta |
| L20 tolerancia menor que el efecto | §3b fila 11 |
| L21 medir el efecto antes de llamarlo arreglo | §6 paso 2 |
| L22 el umbral se pregunta a la referencia; criterios distintos por vara | §3b fila 15 |
| L23 una regla sospechada rota se verifica como un arreglo | §2 regla 14 |
| L24 independencia: veredictos antes de la ronda anterior, otro modelo, port contra el original | §2 regla 1; §5 verificador |
| L25 caminos de ruptura antes de leer | §5 verificador y su bloque |
| L26 VERIFICADO LIMPIO dice contra qué vara | §5 forma del informe |
| L27 predicado literal del producto, mismo intérprete | §0 |
| L28 definiciones de la vara en el bloque común | §5 preámbulo |
| L29 dos escalares no identifican el objeto | §7 |
| L30 cierres: apagan trabajo, heredan premisas, sin respaldo no es refutado | §2 regla 13; §4 frente «por cierres» |
| L31 propagar la rebaja en el mismo cambio | §6 paso 6 |
| L32 rendimiento del eje nuevo | §4 «regla de rendimiento» |
| L33 guarda por hallazgo; empezar por los pendientes | §6 paso 3; §4 |
| L34 «no se usa» falla del lado del auditor | §2 regla 2 |
| L35 guarda por subcadena | §7 |
| L36 capacidad construida y no conectada | §1, párrafo bajo la tabla |
| L37 N = 1 necesaria no es causa; hipótesis sobre un tercero | §2 regla 15 |
| L38 vigilante ciego da verde | §3 viñeta 4 |
| L39 configuración relativa se vigila por la relación | §1 patrón 3 |
| L40 suite en segundo plano mientras se edita | §7, junto a «dos builds» |
| L41 «0 checks» es SIN DATO | §3 |
| L42 flag apagado no prueba que se fue | §2 regla 16 |
| L43 el bloque canónico propaga sus errores | §5 preámbulo; §8 paso 1 |
| L44 «lo que no pude medir» y «fuera de alcance» | §5 forma del informe |
| L45 cita sobre página renderizada; no agrega números | §2 regla 17; §5 citas |
| L46 esperas y verificadores en primer plano | §5 agentes largos |
| L47 aprobación reenviada no vale | §6 paso 6 |
| L48 evidencia con derechos no va al repo público | §2 regla 7 |
| L49 «hoy» a la hora del servidor | §7 |

Matices de A §4 aplicados en su lugar (reescritos, no en sección paralela):
- C1 semilla: §2 regla 12 («fijar la semilla da reproducibilidad, no validez»).
- C2 «≈ 0»: §3 («ese ≈ 0 se mide») y viñetas 1 y 2.
- C3 independencia: §2 regla 1, con puntero a la 8c de la plantilla.
- C4 sistema corriendo y salida renderizada: §0 («precisiones de VRP Chile») y una frase en la plantilla, Parte D.
- C5 repetir dos veces: §2 regla 6 («la repetición prueba estabilidad, no medición»).
- C6 cobertura sin verificación de lo menor: §5 «cobertura primero» (lo no verificado se publica con su conteo).
- C7 instrumento al repo: §2 regla 7.
- C8 falta de experimentos comparativos: §3b entera, más §8 paso 6.

### De B (prompting)

| mejora | sección de la guía |
|---|---|
| M1 bloque de autonomía oficial de Fable 5.1, en inglés tal cual, más las paradas de auditoría en español | §5 «bloque de autonomía» (verificado contra `GUIA_PROMPTING_prompting-claude-fable-5-1.md`, sección «Finish the whole task»: coincide letra por letra con la cita de B) |
| M2 límites: SEGUIMIENTOS, no mejorar el instrumento de otro, scripts se conservan | §5 forma del informe y «objetivo + límites» |
| M3 contradicción cobertura contra brevedad | §5 «cobertura primero»: «sin relleno no quiere decir corto» |
| M4 tabla única de modelo y esfuerzo, con registro | §5 «modelo y esfuerzo» (reemplaza la línea vieja; resuelve la discrepancia con el preámbulo de VRP dando Fable a la semántica y Opus a decidir lo crítico) |
| M5 informe filtrable, resultado primero, CSV | §5 «forma del informe» |
| M6 citas marcadas con localizador y un ejemplo completo | §5 «citas marcadas» (sin el ejemplo literal: B dejó la frase del paper como hueco y no la invento) |
| M7 bloque del verificador | §5, bloque de texto |
| M8 informe escrito a medida | §5 agentes largos y paradas de autonomía |
| M9 búsqueda bibliográfica: buscar lo que el modelo «ya sabe» | §5 citas marcadas (una frase) |
| M10 prosa: `Please remove all mannered prose.` | §5 «tono y estructura del prompt» |
| M11 etiquetas para separar lo fijo de lo variable | §5 «tono y estructura del prompt» |
| B §3.1 ejes como menú | plantilla, Parte B paso 2 y encabezado de los ejes de código (marcado como no medido) |
| B §3.2 mayúsculas | §5 «tono y estructura del prompt» |
| B §3.3 conservar scripts contra el bloque oficial que dice no conservarlos | §5 «objetivo + límites» y §2 regla 7 |
| B §3.4 «funciona con Fable 5.1, Opus y Sonnet» sin medición | título de §5 rebajado a «usada con ...; no medida con evals propias» |
| B §3.5 auto-revisión con Opus 5 | tabla de §5, fila del verificador |
| B §3.6 notas previas de Fable 5 | §5, primer párrafo (apunta a la guía oficial de 5.1) |

Las SOSPECHA de B quedaron como SOSPECHA: guías propias de Opus 5 y Sonnet 5 (no están en el workspace), Opus 5.5 (SIN
DATO), y que el rechazo por «muestra tu razonamiento» siga en Fable 5.1.

## 2. Qué descarté y por qué

- **A §2.1, cola de campo persistente en VRP**: la guía ya la tiene (§0, §6 paso 5, §8 paso 4). Lo que falta es aplicarla
  en VRP, no cambiar la guía; sólo agregué en §0 que, si el sistema no se mira en vivo, la revisión del dueño sobre la
  salida publicada va a esa misma cola.
- **A §2.5, barrer las reglas de VRP que se apoyan en un número sin script**: es una acción del proyecto, no una regla
  general; la regla general ya está (§2 reglas 7 y 13).
- **A §2.3 «la regla B del protocolo diga guarda vista en rojo»**: el cambio al protocolo de VRP es de otro repo; en la
  guía quedó como «guarda vista en rojo» (§6 paso 3) y «toda guarda nace con su rojo» (§3).
- **B M12, avisar el límite a xhigh**: en Claude Code el subagente no expone `max_tokens`; lo práctico (correr los
  informes largos a `high`) ya está en la tabla.
- **B §3.7, «si dudas, invócala igual»**: está en los `CLAUDE.md`, no en la guía. Queda para que Nicolás lo decida; lo
  dejo anotado: la guía de buenas prácticas dice que «If in doubt, use [tool]» provoca sobre-invocación.
- **El ejemplo literal de cita de M6**: no lo copié porque B no leyó la frase del paper y dejó el hueco a propósito; la
  guía pide «un ejemplo completo» sin inventar uno.
- **Las cifras finas de A que no hacían falta para la regla** (por ejemplo 18,6 / 25,0 / 38,1 % por zona del barrido):
  la guía usa una cifra por ejemplo, y el detalle queda en A.

## 3. Cambios propuestos al preámbulo de VRP Chile

Archivo: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\_prompts\PREAMBULO-AUDITOR.md` (otro
repo; lo cambia el coordinador en su PR). Líneas citadas según la lectura de hoy (72 líneas).

**P1. Límite (reemplaza l. 19 a 22; quita la ruta vieja `experiments/_s134_audit/`):**

```text
Límite: auditar no es arreglar. No modificas ningún archivo fuera de «CARPETA» (ruta absoluta que da quien
orquesta en cada tarea; si no la dio, es la carpeta de tu informe). Ahí van tus scripts, con su salida al lado:
son el instrumento y se quedan (no los borres al terminar ni los conviertas en tests del repositorio). Si al medir
ves un defecto fuera de tu eje, no lo persigas más allá de dejarlo reproducible: anótalo en SEGUIMIENTOS con
archivo:línea y confianza, y vuelve a tu eje. Tampoco mejoras el instrumento de otro ni corriges una cita vieja que
encuentres mal: eso también es un seguimiento. Los arreglos los decide quien orquesta, en tareas aparte, con tag
defensivo y confirmación de Nicolás cuando toquen pipeline/ (regla A45).
```

**P2. Brevedad (reemplaza la última frase de l. 29 a 30, «Un informe corto y todo sólido vale más que uno largo con relleno»):**

```text
Sin relleno no quiere decir corto: cada hallazgo y cada SOSPECHA entran, aunque el informe salga largo. Lo que
sobra es la prosa alrededor, no los hallazgos.
```

**P3. Tono (l. 24 y l. 52):** «REGLA OBLIGATORIA, antes de reportar, audita» pasa a «Antes de reportar, audita»; «Cierra
SIEMPRE con» pasa a «Cierra con». El porqué de cada regla ya está al lado. (La l. 24 trae además un guion largo; esta
redacción lo elimina.)

**P4. Formato (agregar al formato de hallazgo, l. 40 a 47, y después de l. 50):** la forma del informe de la guía §5
(encabezado con hora del servidor, commit, modelo y esfuerzo, CARPETA y qué NO miraste; «En una pantalla»; IDs en
«RANGO»; secciones SEGUIMIENTOS, VERIFICADO LIMPIO con la vara contra la que se verificó, SIN DATO, fuera de alcance;
`hallazgos.csv`), y el párrafo de citas marcadas con RENDER o TEXTO y SIN LOCALIZAR. Texto listo en B, M5 y M6.

**P5. Vara común (agregar al bloque, después del contexto):** un hueco «DEFINICIONES DE LA VARA» que quien orquesta
llena por plan (qué es «alerta de MIROVA», qué es «negativo limpio», tolerancia de pareo en minutos), para que los
frentes no midan con cuatro definiciones distintas (AUDIT_S158_R2 §7).

**P6. Notas para quien orquesta (reemplaza l. 69 a 70, la línea de modelos):** «Modelo y esfuerzo: la tabla de
`GUIA_MAESTRA_AUDITORIAS.md` §5, una sola; el informe declara cuál usó.» Así deja de haber dos tablas que no coinciden.

**P7. Bloques opcionales (agregar a las notas):** «Si el auditor corre desatendido, pegar al final el bloque de
autonomía de la guía §5, el inglés tal cual y las paradas en español. Al verificador, pegarle el bloque del verificador
de la guía §5 junto con este preámbulo.»

**P8. Revisión del bloque:** agregar arriba, en la nota de procedencia (l. 3 a 7): «Revisar este bloque al inicio de cada
plan: lo que se copia sin leer también propaga sus errores (la carpeta de S134 viajó aquí 25 sesiones).»

La cabecera del preámbulo (l. 1) y los campos del formato (l. 43 a 47) también traen guiones largos; si el coordinador toca
esas líneas, conviene cambiarlos por dos puntos.
