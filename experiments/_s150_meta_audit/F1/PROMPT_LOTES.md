# Prompt común a los lotes de extracción F1 (S150 meta-auditoría)

Contexto: VRP Chile es un Sistema de Decisiones Automatizadas en producción que replica MIROVA
(detección térmica de volcanes chilenos con MODIS/VIIRS) para SERNAGEOMIN. Repo:
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile` (rama main; NO hagas checkout,
pull, stash, commit, push ni edites archivos del repo). El objetivo del dueño: la réplica
(`mirova_equivalent`) debe publicar lo que MIROVA publica y callar donde calla, medida contra la
base de MIROVA; el perfil `experimental` busca más detección real aunque traiga falsos positivos.

Estamos haciendo el CENSO DE RECOMENDACIONES de las auditorías pasadas: qué recomendaron y qué
pasó con cada cosa. Tu tarea: extraer TODAS las recomendaciones de los archivos de tu lote y
determinar su estado HOY con evidencia. Cobertura primero: es preferible una fila de más que una
recomendación perdida. Lee los archivos completos (no sólo las líneas con palabras clave): las
recomendaciones viven en tablas de decisiones, "Seguimientos", "Correcciones redactadas y no
aplicadas", "Acciones derivadas", "Plan", "Pendientes", "Próximos pasos", "Decisiones para
Nicolás", "Lo que no cubrió", y también en frases sueltas ("habría que medir", "conviene", "queda
abierto", "propuesta").

Qué cuenta como recomendación: toda acción propuesta (cambiar código, correr un A/B o una
medición, corregir un documento, agregar un test/guard, decidir algo, cambiar operación). No
cuentan las observaciones sin acción. Una fila por acción distinta; si el mismo archivo la repite,
una sola fila con la primera línea.

Estados (elige uno, con evidencia OBLIGATORIA en la columna evidencia):
- HECHO: commit o PR (usa `experiments/_s150_meta_audit/F1/prs.json` = todos los PR con título y
  `experiments/_s150_meta_audit/F1/gitlog_main.txt` = git log de main), o archivo:línea del código
  o test de hoy, o valor de flag leído de `experiments/_s150_meta_audit/F1/flags_mirova_equivalent.txt`
  (volcado de `pipeline.profile`; NUNCA leas el YAML para decidir un flag, regla A89: el nombre en
  el YAML no es el nombre en el código).
- DESCARTADO: documento:línea donde se descartó, con la razón.
- REEMPLAZADO: qué lo reemplazó y dónde.
- VIGENTE: sigue abierto Y figura como pendiente en algún documento de S147 a S150
  (`tasks/BLOQUE_ARRANQUE_S150.md`, `docs/AUDIT_S149.md` §4 y §6, `docs/AUDIT_S150.md` §8,
  `docs/PLAN_AUDITORIA_S149.md`, o una D abierta de `docs/MIROVA_DIVERGENCES.md`). Cita la línea.
- ABANDONADO: no hay evidencia de que se hizo ni de que se descartó, y ningún documento de S147 a
  S150 lo rastrea. Escribe en evidencia qué buscaste (patrones de grep y dónde).
- SIN_EVIDENCIA: no pudiste decidir. Di por qué.

Cómo buscar: `grep -rn` en `docs/`, `tasks/`, `pipeline/`, `tests/`, `scripts/`, `frontend/`,
`.github/workflows/`; `grep -i` en los títulos de prs.json y en gitlog_main.txt. Busca por el ID
(D17, A69, H-S138-04, F70...), por el nombre del flag o función, y por una frase clave. Recuerda A89:
un grep que da cero no prueba ausencia; prueba con dos o tres variantes antes de llamar ABANDONADO.

Premisa caída: varias afirmaciones viejas fueron rebajadas (marcadas con ⚠️ en
`CLAUDE.md` del proyecto y en `docs/MIROVA_DIVERGENCES.md`): el «irreducible/agotado» de A82/A83/A84/A85
y D11; D9 «cerrada»; el «0,995» de A99; el NO ADOPTAR de la caja D18 de S130 (medido con el Test 1
encendido y con el flag que sólo llegaba al primer pase); la fidelidad «fiel a Coppola» de S114;
A10 (`pc.vrp_mw` como lo que MIROVA reporta); D26 «efecto nulo»; D13 «31 %»; A69 cierre; A23.
Si una recomendación (o su descarte) se apoya en una de esas premisas, anótalo en premisa_caida.

Salida: escribe con el módulo csv de Python (utf-8, coma, comillas) el archivo
`experiments/_s150_meta_audit/F1/lote_<ID>.csv` con columnas exactas:
`lote,fuente,auditoria,tema,recomendacion,tipo,objetivo,estado,evidencia,premisa_caida,nota`
- fuente: ruta relativa al repo + `:línea`
- auditoria: S## de la auditoría
- tema: etiqueta corta para deduplicar entre lotes (ID si existe: `D17`, `D18-caja`, `A69-test1-nti`,
  `D9-covalidacion`, `OCR-snpp`, `token-earthdata`...)
- tipo: pipeline | medicion | doc | test | frontend | operacion | decision | referencia | otro
- objetivo: replica | experimental | operacion | higiene | ambos
- recomendacion y nota: español de Chile, una o dos frases, sin guiones largos ni medios.

Antes de entregar, audita tu propio CSV: cada HECHO/DESCARTADO/REEMPLAZADO/VIGENTE debe tener una
evidencia concreta que leíste en esta sesión. Si no, bájala a SIN_EVIDENCIA.

Entrega con SubagentHandback un resumen de menos de 300 palabras: ruta del CSV, número de filas
por estado, y las 3 a 5 recomendaciones ABANDONADAS o VIGENTES que más servirían a la fidelidad de
la réplica medida contra MIROVA o a más detección real en el experimental, con su fuente.
