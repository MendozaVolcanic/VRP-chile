# Plan de la auditoría S149: qué falta para cumplir el objetivo, y qué sabíamos y habíamos perdido

> Pedida por Nicolás el 2026-09-21. Vinculante antes de lanzar auditores: `../../GUIA_MAESTRA_AUDITORIAS.md`
> (preámbulo entero, cobertura primero, verificador con contexto limpio, las dos preguntas del
> instrumento) y `docs/_prompts/PREAMBULO-AUDITOR.md`. Escala acordada con Nicolás (regla S120): completa,
> siete auditores más verificadores.

## Por qué ahora

En una sola sesión el plan cambió tres veces por cosas que **ya estaban escritas en algún lado**:

1. la calidad de la base de MIROVA por mes (medida en S139, sin puntero: se eligió una ventana sin mirarla);
2. la regla de Nicolás de que VIIRS captura todo lo que MIROVA publica y sólo MODIS puede perder señal
   sub-píxel (sesión 10): el índice de memoria la resumió como "pérdidas bajo 0,5 MW aceptables" y ese
   corte contaminó cuatro pre-registros;
3. un criterio de posición inventado (C7) que bloqueó el A/B sin Test 1 y después se bajó a informativo.

El eje que esta auditoría estrena (regla A del protocolo): **conocimiento perdido o deformado al
resumirlo**. No busca bugs de código. Busca reglas del dueño, hechos medidos y límites de los datos que
existen en el repo o en la memoria, que no están donde se leen primero, y que cambiarían el plan.

## Definiciones del dueño que la auditoría toma como dadas (2026-09-21)

- **Objetivo**: máxima fidelidad a MIROVA en el perfil réplica; más detecciones, con posibles falsos
  positivos, en el experimental. La réplica se mide contra la base de MIROVA, no se elige.
- **Prioridad en la réplica: paridad en los dos sentidos.** Publicar lo que MIROVA publica y callar donde
  MIROVA calla; se busca el punto que minimiza la suma de los dos errores; lo extra va al experimental.
- **Meta de "cumplido"**: metas por sensor que proponga esta auditoría, midiendo la variabilidad de
  MIROVA contra sí misma, para que Nicolás las apruebe.
- Sin fecha: que quede bien.

## Frentes (disjuntos, uno por auditor)

| frente | pregunta | entregable |
|---|---|---|
| **A. Reglas del dueño** | Censo de TODA directiva de Nicolás (memoria `feedback_*`, archivos de memoria, los tres `CLAUDE.md`, `docs/MISSION.md`, bloques de arranque, `META_RULES`). Para cada una: alcance exacto, dónde está resumida, y si el resumen perdió alcance o la contradice otro texto. Y cuáles violan hoy los pre-registros, criterios y planes vigentes | `FRENTE_A_REGLAS_DEL_DUENO.md` |
| **B. Bases de datos y sus límites** | Todo lo medido sobre la validez de las referencias (CSV del scraper, OCR, OSF, TIF, KML, serie propia con sus huecos): qué sirve desde cuándo y para qué. Y qué instrumentos vigentes lo ignoran | `FRENTE_B_BASES_Y_LIMITES.md` |
| **C. Brechas medidas, por sensor** | Dónde está hoy la réplica contra MIROVA en los tres errores (publicar de más, perder alertas por tramo de magnitud, magnitud pareada), por sensor y por volcán, con el dato de hoy. Incluye la brecha de VIIRS 750 y las 0 de 11 de MODIS en Láscar. Y la variabilidad de MIROVA contra sí misma, para proponer metas | `FRENTE_C_BRECHAS_Y_METAS.md` |
| **D. Veredictos viejos bajo lo que hoy sabemos** | Todo "NO ADOPTAR", "cerrado" o "sin beneficio" de S124 a S148: cuáles se decidieron con un criterio hoy caído (corte de 0,5 MW, C7, C8, saturación por el Test 1, ventana que cruza #535, referencia en tramo defectuoso, flag que no llegaba a sus consumidores) | `FRENTE_D_VEREDICTOS_VIEJOS.md` |
| **E. El paper contra el código, pieza por pieza** | Inventario de todo lo que está encendido en `mirova_equivalent` (leído desde `pipeline.profile`) y no está en los papers del grupo MIROVA, y de lo que está en los papers y no está en el código. La pregunta de Nicolás: ¿nos estamos enredando?, ¿cuál es la configuración más simple y literal? | `FRENTE_E_PAPER_CONTRA_CODIGO.md` |
| **F. El experimental** | Qué existe, qué promete y qué le falta para cumplir su mitad del objetivo; contra qué se valida (actividad de OVDAS, SWIR de alta resolución); cómo se separa de la réplica | `FRENTE_F_EXPERIMENTAL.md` |
| **G. Operación y entrega** | Lo que el operador ve: las vistas del tablero contra lo que el pipeline persiste, la cadencia real del NRT, credenciales y caducidades, ficha de transparencia algorítmica al día, y qué de todo lo anterior bloquea una adopción | `FRENTE_G_OPERACION.md` |

Cada auditor escribe sólo en `docs/audit_s149/plan_final/` y `experiments/_s149_audit/<frente>/`.
Después: verificador con contexto limpio sobre todo hallazgo de gravedad 4 o 5, y síntesis en
`docs/AUDIT_S149.md` con el plan final, las metas propuestas y las decisiones que quedan para Nicolás.
