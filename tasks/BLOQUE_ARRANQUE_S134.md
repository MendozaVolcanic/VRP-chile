# Bloque de arranque S134

## Prompt para pegar al inicio de la sesión (escrito para Claude Fable 5.1)

```
Continuamos VRP Chile desde S133. Sos el mismo sistema que ayer encontró que MIROVA veía una
anomalía MODIS de 4,75 MW en Villarrica y nosotros no, y que detrás de esa sola pregunta había
cinco defectos silenciosos. Hoy toca lo que ese hilo dejó abierto: el cúmulo que publicamos
está a 2,3-2,8 km del cráter en 9 de los 11 volcanes, y no sabemos si eso explica por qué
nuestra magnitud se aleja de la de MIROVA en régimen débil.

POR QUÉ IMPORTA. Este es un sistema de decisiones automatizadas en producción (CPLT N°372):
lo que publica lo mira un operador del OVDAS para decidir si un volcán cambió. Si integramos
calor del flanco y MIROVA integra el cráter, las dos magnitudes son de dos objetos distintos y
ninguna corrección de área o de banda va a cerrar la brecha. Eso es lo que hay que saber.

OBJETIVO. Ejecutar la auditoría S134 según el plan
  docs/superpowers/plans/2026-09-05-auditoria-s134-anillo-y-paridad.md
y cerrarla con docs/AUDIT_S134.md, una tabla de decisiones para Nicolás y el bloque S135.
El plan tiene cinco frentes con controles y criterios pre-registrados; el eje nuevo declarado
es posición → magnitud → paridad por pasada. Léelo entero antes de lanzar nada.

LÍMITES (no negociables):
- Auditar no es arreglar. Nada en pipeline/ sin tag defensivo Y confirmación de Nicolás (A45).
  Ningún flag se enciende. Los scripts de medición van a experiments/_s134_audit/.
- Todo prompt de auditor empieza pegando ENTERO docs/_prompts/PREAMBULO-AUDITOR.md.
- Regla A: prohibido el barrido general; regla B: cierre por guard; regla C: empezar por los
  pendientes del plan §0, verificados contra el código de hoy. Están en
  docs/PROTOCOLO_AUDITORIA_PROFUNDA.md.
- El que verifica no es el que encontró. Un auditor por frente, worktree propio (A44),
  Fable/Opus/Sonnet según el plan.
- Los TIF de MIROVA no se bajan al PC: sólo los de las pasadas elegidas, y el archivo se
  consulta por su index.csv, nunca listando el directorio (la API corta en 1000 sin avisar).
- La unidad de comparación es la PASADA, no la noche; el ancla es vent_lat/vent_lon, nunca el
  catálogo (Villarrica: 0,85 km de diferencia, A13). Todo número lleva denominador y ventana.

LEER, en este orden, antes de actuar:
  1. tasks/BLOQUE_ARRANQUE_S134.md              (este bloque)
  2. docs/superpowers/plans/2026-09-05-auditoria-s134-anillo-y-paridad.md
  3. docs/s133/ANILLO_TIER_A.md                  (el hallazgo que motiva la sesión)
  4. docs/s133/AUDITORIA_DEL_INCIDENTE.md        (los 5 defectos del 07:50, para no repetirlos)
  5. C:\Users\nmend\OneDrive\Escritorio\claude\GUIA_MAESTRA_AUDITORIAS.md
  6. docs/PROTOCOLO_AUDITORIA_PROFUNDA.md        (reglas A/B/C y registro de ejes)

ESTADO AL ARRANCAR. Suite 1183 passed · 3 skipped · 0 xfail. Los tres flags apagados. Nada
corriendo en CI que haya que esperar. Los artefactos del A/B del área (run 33912398561) y de
B22 (run 33872821788) caducan el 2026-09-18/19: F4 los necesita, bajarlos primero.

AUTONOMÍA. Nicolás no está mirando en tiempo real y no puede contestar a mitad de la tarea.
Para acciones reversibles que siguen del plan, avanza sin preguntar. Detente sólo ante lo
destructivo o ante un cambio de alcance real; las tres decisiones que son suyas (plan §5) se
le presentan al cierre en una tabla con opciones y recomendación, no se toman. Antes de
terminar el turno, mira tu último párrafo: si es un plan, una lista de próximos pasos o una
promesa, hace ese trabajo ahora. Termina sólo cuando la auditoría esté cerrada o estés
bloqueado en algo que sólo Nicolás puede dar.

ENTREGA. El pedido y el plan fijan el alcance, y el alcance es el entregable: no lo
angostes ni lo ensanches. Lo que encuentres de paso (un bug, una limpieza) se reporta como
seguimiento, no se arregla en esta sesión. Antes de empezar di en una línea qué vas a hacer;
mientras trabajas, avisos breves; al cerrar, un resumen que se sostenga solo. Español de
Chile, sin voseo. Primero el fenómeno físico, después el código, al final los números.

Si algo del plan resulta falso al verificarlo (una ruta que no existe, un pendiente ya
cerrado), corrige el plan citando la evidencia y sigue; no te detengas a preguntar.
```

---

## Lo que S133 dejó hecho (para no re-auditar)

| frente | estado | dónde |
|---|---|---|
| A/B del área (chunk 1, 24/24 verdes) | **NO ADOPTAR**: corrige el gradiente pero lo invierte (borde 0,62 → 1,36) | `docs/s133/AB_AREA_VEREDICTO_CHUNK1.md` |
| A/B de B22 | **NO ADOPTAR por ahora**: el fondo cae 1,2 K (no 0,004); magnitud ÷4-10; paridad no medible con n=2 | `docs/s133/AB_B22_VEREDICTO.md` |
| NRT de MODIS | corregido: pedía `MYD021KM_NRT` v61, que no existe; ahora `MYD021KM` v6.1NRT (#587, #588) | `docs/s133/AUDITORIA_NRT_MODIS.md` |
| Cadencia del cron | externa (GitHub entrega 51 % menos); sin pérdida de datos; medida desde el healthcheck | `docs/s133/CADENCIA_DEL_CRON.md` |
| Poller de TIF | vivo (231 snapshots); era el timeout de 10 min contra 12,3 de mediana, no sólo la concurrencia | archive #2 |
| Mapa de foco Villarrica | dos vistas; el anillo | `experiments/_s133_villarrica_focus/` |
| Issues #506 y #567 | cerradas con evidencia | — |
| Docs corregidos | `DATA_SOURCES.md` (nombres NRT), `INDEX.md` (8 docs sin indexar) | #592 |

## Decisiones que esperan a Nicolás (se presentan al cierre de S134, plan §5)

1. **Flip de `ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER`.** El A/B de S132 dio NO ADOPTAR porque
   C2 falló, pero C2 era tautológico (S133). Recomendación: **no encender hasta que F1 y F3
   digan si el cúmulo MODIS está en el cráter**; si se re-corre, con C2' en unidades de
   `inner_radius` (`docs/s133/C2_NORMALIZADO_INNER_RADIUS.md`).
2. Marcador «extensión» para el lacolito de PCC (pregunta volcanológica).
3. Re-correr B22 con ventana ancha y volcanes con más alertas (Isluga 66, Láscar 62).

## Anotado y fuera de alcance (pedido de Nicolás)

- VegStress-v1: caído desde el 13-ago por secrets `SH_CLIENT_ID`/`SH_CLIENT_SECRET`
  ausentes. **No es prioridad; no se trabaja hasta que él lo pida.**
- Rotar el PAT de `~/.claude/settings.json`.
- Reducir a 30 min el disparo de cron-job.org sobre el poller — **NO**: Nicolás lo quiere en
  5 min porque GitHub deja las corridas en cola; ya no se cancelan entre sí.

## Lección de método de S133 para quien arranque

Ninguno de los cinco defectos del 07:50 produjo un error: produjeron un cero (colección
inexistente), una etiqueta plausible (`standard` por `nrt`), una métrica verde (monitores que
miran fallas donde el problema era ausencia) y una palabra ambigua (`cancelled` para timeout
y para concurrencia). Y tres veces el instrumento se equivocó antes que el dato: comparar
poblaciones distintas, truncar un diccionario en el propio `print`, y una API que corta en
1000 sin avisar. Las dos preguntas del instrumento (guía §3) van en cada medición.
