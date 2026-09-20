# Plan de auditoría S146: los cierres, no el código

> Preparado en S145 para ejecutarse con Claude Fable 5.1. Alcance medido, no estimado:
> `experiments/_s145_censo_cierres/censo_cierres.md` lista las afirmaciones una por una.
> Vinculante antes de lanzar auditores: `../../GUIA_MAESTRA_AUDITORIAS.md` (preámbulo entero,
> cobertura primero, verificador con contexto limpio, las dos preguntas del instrumento, línea
> base roja). Para los prompts: `../../GUIA_PROMPTING_prompting-claude-fable-5-1.md`.

## 1. Por qué esta auditoría, y por qué NO es una auditoría genérica

La regla A51 pide una auditoría integral cada 20 sesiones y la última fue la S138, así que por
calendario todavía no toca. Pero A51 tiene un segundo disparador que **sí se cumplió**: *"si
detecta más de 3 contradicciones cross-source, pausar features nuevas y consolidar primero"*.

En S145, en una sola sesión, cayeron **cuatro veredictos**, y los cuatro por el mismo mecanismo:

| veredicto | qué decía | qué resultó |
|---|---|---|
| **D26** | "efecto nulo bajo la conectiva `min`" | se apoyaba en `experiments/_s136/que_rama_manda.py:41`, que lee **sólo** `diag_mu_dnti` y `diag_sd_dnti`: midió el Test 2 y atribuyó la conclusión a los dos. El sigma gobierna en el 58,7 % de VIIRS 375 y el 75,0 % de VIIRS 750 |
| **D13** | "apaga el 31 % de la **magnitud**" | ese 31 % era una fracción de **records**. En magnitud son **70,7 %** |
| **S137 sobre el caso A2** | "hipótesis no verificada: la batería guarda distancias pero no posiciones" | cada pasada guarda `pc_lat` y `pc_lon`. Era verificable desde el día que se escribió |
| **el orquestador de S145** | "`pc.classification` no existe" | la capacidad existe como `geo_class`, persistida en 40.901 de 62.880 records |

Ninguno era un error de cálculo. Los cuatro son el mismo patrón, que la regla **A95** nombra: *un
cierre hereda las premisas de la lectura con que se derivó*. Y un cierre no es una nota al pie:
**apaga trabajo futuro**, porque nadie vuelve a mirar lo que dice "no reabrir".

Por eso el objeto de esta auditoría no es el código. **Es el conjunto de afirmaciones con las que
el proyecto se dice a sí mismo que algo ya está resuelto.**

## 2. El alcance, medido

`experiments/_s145_censo_cierres/censo.py` barrió los cinco documentos rectores
(`docs/MIROVA_DIVERGENCES.md`, `CLAUDE.md`, `docs/MISSION.md`, `docs/HYPOTHESIS_LOG.md`,
`docs/META_RULES_S80.md`):

- **89 afirmaciones de cierre.**
- **50 sin respaldo citable**: no nombran script, run, PR, paper, documento ni `archivo:línea` en
  su entorno. Un cierre que no se puede verificar no es un cierre, es una creencia.

Por tipo: resuelta 23, refutada 19, cerrada 9, no_reabrir 9, agotado 8, despreciable 7,
irreducible 7, es_fiel 6, no_adoptar 6, menor 2, efecto_nulo 2.

⚠️ **Límite del censo, declarado**: busca por palabras clave, así que un cierre redactado con
otras palabras no aparece. Es un **piso** del problema, no su medida. El primer auditor debe
ampliar el patrón y reportar cuánto creció.

## 3. Los frentes, disjuntos, uno por auditor

Cada auditor recibe su lista del censo y **no comparte archivos de salida con los demás**.

| frente | qué verifica | criterio de salida |
|---|---|---|
| **A. Los 50 sin respaldo** | para cada uno: ¿existe evidencia aunque no esté citada, o no existe? | cada afirmación queda como VERIFICADA (con la evidencia que encontró), SIN EVIDENCIA, o REFUTADA |
| **B. Los cierres con script** | correr el script que cada cierre cita y comprobar que **mide lo que la afirmación dice**. Es el frente donde cayó D26 | por cada uno: qué mide el script contra qué afirma el texto |
| **C. Los cierres con paper** | cotejar la cita verbatim contra el PDF **renderizado a imagen** (`page.get_pixmap(dpi=200)` con PyMuPDF). La capa de texto corrompe operadores y símbolos: p. 21 da `,20.93` donde el papel dice `< -0.93` | cita correcta, cita corrupta, o cita que el paper no sostiene |
| **D. Los cierres con número** | para cada cifra: ¿qué numerador, qué denominador, qué ventana? Es el frente donde cayó D13 | la afirmación nombra el conjunto que su número realmente cuenta, o no |
| **E. Los cierres cruzados** | cierres que dependen de otro cierre. D11 depende de D21 y D22; el corolario de S136 dependía de `min`. Si el de abajo cae, el de arriba cae | grafo de dependencias entre cierres, con los que quedan en falso |

## 4. Las dos preguntas del instrumento, obligatorias

Van en el encabezado de **toda** prueba que cada auditor escriba, respondidas, no citadas:

1. *Si lo que mide estuviera completamente roto, ¿esta prueba fallaría?* Un "no" significa que la
   prueba comprueba que el programa no se cae, no que el fenómeno ocurra.
2. *Si el instrumento mismo estuviera muerto, ¿el resultado se vería distinto?* Un "no" es un dato
   inválido que se parece a un cero.

Y: **SIN DATO no es FALLA y no es OK.** "No pude medirlo" nunca se reporta como "no cambió nada".

## 5. Lo que esta auditoría NO debe hacer

- **No arreglar nada.** Es read-only sobre `pipeline/`, `frontend/` y el perfil. Un cierre que cae
  se anota; el arreglo es otra decisión, del dueño, y va por el ciclo A45.
- **No reabrir frentes por gusto.** Que un cierre no tenga respaldo citable no lo vuelve falso.
  La salida correcta es SIN EVIDENCIA, que es distinto de REFUTADO.
- **No inventar gravedad.** "Los 50 tienen evidencia y acá está" es un resultado legítimo y
  valioso. La guía maestra lo dice: un informe que sólo lista defectos hace que el lector
  desconfíe de lo que sí está bien.
- **No tocar los worktrees ni los stashes viejos** (A96: hay 4 stashes de S72 a S78 que no son de
  ninguna sesión viva).

## 6. Bloque de autonomía para los auditores Fable

Va en el prompt de cada uno, literal (de la guía de prompting, sección "Finish the whole task"):

```text
Operas de forma autónoma. El usuario no está mirando en tiempo real y no puede contestar preguntas
a mitad de la tarea, así que preguntar "¿quieres que...?" bloquea el trabajo. Para acciones
reversibles que se siguen del pedido original, procede sin preguntar. Detente sólo ante acciones
destructivas o cambios de alcance genuinos que el usuario deba decidir.

Antes de terminar tu turno, revisa tu último párrafo. Si es un plan, un análisis, una pregunta, una
lista de próximos pasos o una promesa sobre trabajo que no hiciste, hazlo ahora con llamadas a
herramientas. Eso incluye reintentar después de un error y conseguir tú mismo la información que
falte. No te detengas porque el contexto o la sesión sean largos.
```

Más, en cada prompt: el **porqué** antes de la tarea, objetivo y límites en vez de una lista de
pasos, cada afirmación anclada a la salida de una herramienta que corrió, y **cobertura declarada
antes de los hallazgos**.

## 7. Después de los auditores: el verificador con contexto limpio

No es un trámite. En S144 siete rondas de verificación refutaron siete diseños, y en S145 el
verificador del plan encontró tres fallas graves que el autor no vio, una de las cuales se confirmó
en la práctica el mismo día.

El verificador **no es quien encontró**, recibe sólo **título, ruta y script**, y su trabajo es
enumerar los caminos por los que la afirmación podría estar mal. En S134 encontró algo propio en 4
de 4 frentes.

## 8. Entregable

`docs/AUDIT_S146.md`, con:

1. **Cobertura primero**: cuántas de las 89 se verificaron y cuántas no, por frente.
2. La tabla de veredictos: VERIFICADA / SIN EVIDENCIA / REFUTADA, con la evidencia de cada una.
3. **Los cierres que caen**, ordenados por cuánto trabajo estaban apagando.
4. El grafo del frente E: qué cierres dependen de cuáles.
5. Las correcciones al catálogo y a `CLAUDE.md`, redactadas pero **no aplicadas**: aplicarlas es
   decisión del dueño.

## 9. Escala sugerida

**5 auditores en paralelo (uno por frente) más 1 verificador.** No más: en S120 un fan-out masivo
costó caro y la regla del proyecto es pre-acordar la escala. Si un frente resulta más grande de lo
previsto, se parte en una segunda tanda en vez de agrandar la primera.
