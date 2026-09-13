# Plan de auditoría S138: seis ejes en paralelo y un verificador limpio

> Escrito al cierre de S137 (2026-09-13) por pedido de Nicolás: una auditoría pensada desde los desafíos
> reales del proyecto, no desde una plantilla. Cada eje nace de un error concreto de las últimas
> sesiones (S124 a S137). Marco: `../../GUIA_MAESTRA_AUDITORIAS.md` (preámbulo anti fabricación,
> cobertura primero, verificador con contexto limpio, las dos preguntas del instrumento, línea base
> roja) y `docs/PROTOCOLO_AUDITORIA_PROFUNDA.md` (técnicas T1 a T9). Preámbulo canónico:
> `docs/_prompts/PREAMBULO-AUDITOR.md`, se pega entero en cada prompt.

## Por qué esta auditoría y no otra

Las últimas catorce sesiones dejaron un patrón que se repite con formas distintas:

| sesión | lo que pasó | el patrón |
|---|---|---|
| S124 | A82 decía "agotado, no reabrir"; la auditoría en que se apoyaba nunca miró la geometría | un cierre apoyado en una auditoría incompleta |
| S125 | 12 casos de "declarado ≠ efectivo", 3 propios | el flag no es el fenómeno |
| S127 | 5 falsos negativos de auditoría, los 5 de quien auditaba (A89) | el cero de un grep se lee como ausencia |
| S133 | un guard que pasaba por subcadena (A92) | el instrumento mide otra cosa |
| S134 | 5 enunciados refutados por verificadores limpios, 4 de instrumento (A93) | el verificador limpio encuentra algo propio |
| S136 | "sigma es irrelevante" cerró tres frentes; valía sólo bajo la lectura que la misma sesión refutó | un corolario circular apagó trabajo futuro |
| S137 | `CLAUDE.md` decía "NO quedan gaps de fidelidad literal"; aparecieron D21 y D22 el mismo día; recomendé correr un A/B ya corrido; la v1 de una medición leía el marco de una barra de color | las reglas "cerrado" envejecen hacia el falso positivo |

Y un segundo patrón: **el pipeline lleva 137 sesiones sin una matriz de conformidad construida desde el
PDF del paper**. La de S114 se construyó desde documentos previos y declaró fiel una detección a la que
le faltaban la banda primaria, el remuestreo, el bow tie y una compuerta de temperatura que el paper no
tiene. Lo que S137 encontró leyendo el PDF en dos horas debió encontrarse en S114.

Por eso los ejes apuntan a **lo que hoy gobierna decisiones**: las afirmaciones de cierre, la fidelidad
paso a paso, y los instrumentos con que se midió lo último.

## Los seis ejes (disjuntos, uno por agente, en paralelo)

Cada agente es **read only**: no toca `pipeline/`, perfiles, `data/` ni git. Escribe un solo archivo,
`docs/audit_s138/EJE_<n>_<nombre>.md`, y devuelve al orquestador un resumen de menos de 400 palabras.
Como no escriben en git, no necesitan worktree (y el disco está al 99 %, con 5,9 GB libres: no hay
espacio para seis checkouts). El orquestador commitea al final.

### Eje 1: las afirmaciones de cierre contra el paper y el código de hoy (T6)

**Pregunta.** ¿Cuáles de las afirmaciones "cerrado", "agotado", "no reabrir", "fiel", "resuelto" que
gobiernan el proyecto siguen siendo ciertas hoy?

**Universo.** Todas las de `CLAUDE.md` (reglas A1 a A96, sección Reglas científicas), los encabezados
de `docs/MIROVA_DIVERGENCES.md`, y las secciones "cerrado, no rehacer" de
`tasks/BLOQUE_ARRANQUE_S134.md` a `S138.md`.

**Método.** Para cada afirmación: (a) la premisa en que se apoya, con cita; (b) verificación contra el
PDF (`documentacion/sp426.5.pdf` con PyMuPDF, nunca el `.txt`) y contra `pipeline.profile` +
file:line; (c) veredicto: vigente / condicionada (vale sólo bajo X) / falsa. Empezar por las que apagan
más trabajo futuro.

**Salida.** Tabla afirmación → premisa → evidencia → veredicto. Contar cuántas quedan condicionadas o
falsas: ésa es la medida de cuánto envejeció el conocimiento del proyecto.

### Eje 2: la matriz de conformidad construida DESDE el PDF (T1, T2, T5, T9)

**Pregunta.** Paso por paso del algoritmo tal como lo describe Coppola 2016a, ¿qué hace nuestro código
en cada uno de los tres sensores, y está efectivo en `mirova_equivalent`?

**Método.** Primero leer el PDF y escribir la lista de pasos **sin mirar ningún documento del proyecto**
(banda L21ok, filtro de DN, bow tie, recorte y remuestreo a 1 km centrado en GVP, ROI1 caja de 5 km y
ROI2, NTI, NTIapp, regresión NTIbk, ETI, dNTI y dETI con 8 vecinos, píxeles no aptos, Test 1 y retiro,
Tests 2 y 3 con Tabla 1, retiro de activos, segunda corrida, ecuación 6 del fondo, ecuación 7 del VRP,
y lo que el paper NO tiene: compuerta de temperatura, `keep_peak`, Test 1 integrado, intersección
contextual). Recién después, para cada paso: file:line en `process_modis.py`, `process_viirs.py`,
`process_viirs_mod.py` y `detection_context.py`; si existe, si es flag, y el valor **efectivo** leído de
`pipeline.profile` (A89: nunca del YAML). Marcar lo que el código tiene y el paper no.

**Salida.** La matriz. Es el documento que debió existir en S114 y que `AUDIT_S114_PARITY_BY_SENSOR.md`
no es. Cuenta cuántas divergencias literales quedan sin D#.

### Eje 3: verificador limpio de los instrumentos de S137 (A93, las dos preguntas)

**Pregunta.** ¿Los cinco instrumentos con que S137 midió dicen lo que dicen medir?

**Universo.** `experiments/_s137/sigma_dnti_4brazos.py` (84 pares), `conformidad_apendice.py` con sus
ocho brazos, `probe_etapa_apendice.py`, `medir_figuras_apendice.py`, `comparar_brazos_apendice.py`.

**Método.** Para cada uno, las dos preguntas del instrumento: ¿qué mide exactamente? ¿qué daría si el
fenómeno no existiera? Línea base roja donde se pueda sin CI: `medir_figuras_apendice.py` sobre un panel
sin anomalía (A7 Tolbachik) y con la escala al revés; el comparador con un JSON sintético de 9 casos
todos conformes y todos no conformes. Enumerar los caminos por los que cada número central podría estar
mal (sigma 0,0008 del autor; 5/6 y 3/3; 9,6 km rumbo 83°; caída 3,5 a 4,7×). Comprobar que el recorte
de exceso a cero y el fondo del anillo explican el VRP 0,0 de Villarrica leyendo el código, no el
informe. Recibe sólo títulos, rutas y scripts: no los documentos de resultados.

**Salida.** Por afirmación: confirmada / corregida (con el número nuevo) / no verificable, y los
hallazgos propios. En S134 el verificador encontró algo propio en 4 de 4 frentes.

### Eje 4: D21, D22 y el fondo en VIIRS, medidos sobre los datos (T3, T8)

**Pregunta.** La compuerta `bt > t_bg + 3 K` y el fondo del anillo viven también en VIIRS 375 y 750 m,
donde no hay banda 22. ¿Cuánto cuestan ahí?

**Método.** Sobre `data/mirova_equivalent/*.json`, read only, con denominador y ventana escritos (A90):
(a) records con `primary_cluster.n_pixels > 0` y `vrp_mw == 0` por volcán y sensor, y cuántos de ellos
caen en noches con alerta de MIROVA (CONS ∪ OCR, A11 y A14 para nombres); (b) records summit cuyo
`t_max_k < t_bg_k + 3` por volcán, separando nevados de focales (A83); (c) si el poder estadístico
alcanza (T8) antes de afirmar cualquier diferencia entre volcanes. Si hace falta el probe A75 por etapa
en VIIRS 375 sobre noches confirmadas de Villarrica, escribir el script y el yml, **no dispararlo**: el
disparo lo decide el orquestador.

**Salida.** Tabla por volcán y sensor, y una recomendación explícita: ¿el A/B Tier A de D21/D22 debe
incluir VIIRS desde el inicio o MODIS primero?

### Eje 5: la batería del Apéndice A como instrumento (T7, adversarial)

**Pregunta.** ¿El 5 de 6 y 3 de 3 mide lo que el autor detectó, o mide otra cosa que coincide?

**Método.** (a) Medir en las nueve figuras del apéndice (páginas 18 a 22 del PDF) la posición de la
máscara de alerta, como S137 hizo sólo con A2, y comparar con la posición del cúmulo de cada brazo:
en cuántos de los 6 positivos "conforme" significa "publicamos el objeto del autor". (b) Sensibilidad:
correr `evaluar_caso` sobre los JSON ya commiteados con `INNER_KM` de 3, 5 y 8 km y con la coordenada
GVP contra el centro de la figura; si el veredicto cambia, la batería es frágil. (c) Sobreajuste: tres
correcciones sobre nueve escenas; proponer la referencia de holdout (noches confirmadas de MIROVA en
los 11 Tier A, 2026-06 a 2026-08) y el criterio pre registrado del A/B, en unidades del objeto (A91),
estratificado focal y nevado (A83), con umbral de pérdida cero (decisión de Nicolás en S135).

**Salida.** El instrumento corregido (si hace falta) como propuesta, no como cambio; y el pre registro
del A/B Tier A listo para que Nicolás lo apruebe.

### Eje 6: inventario de decisiones, deuda operativa e higiene (T4, T9)

**Pregunta.** ¿Qué espera decisión, qué ya se ejecutó sin marcarse, y qué está rompiéndose en silencio?

**Método.** (a) Una sola tabla con todas las decisiones abiertas de `AUDIT_S134.md` §D, S135, S136 y
S137, con estado real verificado (ejecutada / superada / abierta) y la evidencia; en S137 se recomendó
correr un A/B que ya estaba corrido porque esa tabla no existía. (b) Operación: cadencia del cron NRT
(S133 midió una caída del 51 %), últimos runs verdes contra último dato commiteado por volcán
(detector de zombies), `sync-mirova-csv`, y el frontend contra los datos (T7: lo que ve el operador).
(c) Higiene: 196 ramas remotas, 4 stashes de S72 a S78 (uno reaplicó solo en S137), 5,9 GB libres,
ramas `s137-*` integradas por squash que `git cherry` marca como pendientes.

**Salida.** La tabla de decisiones, el estado del NRT con números, y una lista de limpieza con el tag
defensivo que requiere (A38) antes de borrar nada.

## El verificador limpio (secuencial, después de los seis)

Un séptimo agente, sin historial, recibe **sólo** los seis archivos de `docs/audit_s138/` y los scripts
que citan. Re corre lo que se pueda re correr, funde duplicados, enumera para cada hallazgo crítico los
caminos por los que podría estar mal, y asigna gravedad final. Regla de la guía maestra: es un segundo
buscador, no un trámite; en S134 aportó 14 hallazgos propios.

## Reglas para el orquestador

1. Leer `../../GUIA_MAESTRA_AUDITORIAS.md` entera antes de lanzar, y
   `../../GUIA_PROMPTING_prompting-claude-fable-5-1.md` si los agentes corren en Fable.
2. Pegar `docs/_prompts/PREAMBULO-AUDITOR.md` entero en cada prompt. Cobertura primero, con CONFIANZA y
   GRAVEDAD por hallazgo; el filtrado es del verificador.
3. Seis agentes en un solo mensaje (paralelo real), read only, cada uno escribe un archivo distinto.
   Máximo dos con red externa a la vez (NASA, Wayback). Ninguno dispara CI.
4. Verificar tú los hallazgos críticos antes de aceptarlos (A48): los agentes son volumen, no fuente
   de verdad. Cruza cualquier "esto está muerto" o "esto no se usa" con A89.
5. Producir `docs/AUDIT_S138.md` con la regla de salida del protocolo: si hay más de tres
   contradicciones entre fuentes, se pausa el frente y se consolida antes de seguir (A51).
6. Nada de guiones largos en ningún archivo; verificar con Python, no con grep.

## Lo que esta auditoría NO hace

No adopta nada. No toca el pipeline. No corre A/B. Su entregable es una lista corta de lo que gobierna
mal y el pre registro del A/B que decidirá D21 y D22.
