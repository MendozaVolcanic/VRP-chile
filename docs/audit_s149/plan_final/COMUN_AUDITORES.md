# Instrucciones comunes a los siete auditores de S149 (léelas ENTERAS antes de empezar)

1. Lee y aplica ENTERO, sin resumir, `docs/_prompts/PREAMBULO-AUDITOR.md` (el bloque entre "EL BLOQUE" y
   "hasta acá"). Donde dice `experiments/_s134_audit/`, tu carpeta es `experiments/_s149_audit/<tu frente>/`.
2. Lee `docs/PLAN_AUDITORIA_S149.md`: por qué existe esta auditoría, las definiciones del dueño que se dan
   por dadas, y cuál es TU frente. No invadas los otros frentes; si ves algo de otro frente, anótalo en
   una sección final "Para otros frentes" con archivo:línea, sin desarrollarlo.
3. Contexto de la sesión: `tasks/BLOQUE_ARRANQUE_S150.md`, `docs/S149_COSTO_OCULTO_MAX.md`,
   `docs/S149_RESULTADO_CONECTIVA_MAYO.md`, regla A119 en `CLAUDE.md`. La memoria del agente está en
   `C:/Users/nmend/.claude/projects/C--Users-nmend-OneDrive-Escritorio-claude-Volcanologia-VRP-Chile/memory/`
   (índice `MEMORY.md`, archivos `feedback_*`, `reference_*`, `project_*`, `MEMORY_ARCHIVE_*`).
4. El eje nuevo: CONOCIMIENTO PERDIDO O DEFORMADO AL RESUMIRLO. El ejemplo que motivó todo: la regla del
   dueño "VIIRS captura todo lo que MIROVA publica, sólo MODIS puede perder sub-píxel" quedó en el índice
   como "pérdidas bajo 0,5 MW aceptables" y contaminó cuatro pre-registros. Busca ESA clase de cosa en tu
   frente: algo que está escrito y medido en algún lado, no está donde se lee primero, y cambiaría el plan.
5. Límites duros: sólo lectura sobre el repo salvo tu carpeta de experimentos y tu informe en
   `docs/audit_s149/plan_final/`. No hagas git commit, push, checkout, stash ni pull. NO corras pytest
   (hay procesos en segundo plano sobre este árbol). No despaches workflows. No uses credenciales de NASA.
   El disco está al 97 %: nunca `git archive` sin ruta, nunca copies datos grandes al repo. Python que
   imprima tildes: `sys.stdout` en utf-8. Documentos con la herramienta de escritura de archivos, nunca
   con heredoc. Escribe en español de Chile (formas de tú, sin voseo) y SIN guiones largos ni medios.
6. Para leer cómo está configurado el pipeline, resuelve el perfil como lo resuelve el código
   (`VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; ..."`), nunca leyendo el YAML
   (regla A89). Una búsqueda que da cero no prueba ausencia: repítela con otro nombre o por otro camino.
7. Autonomía: nadie va a contestarte a mitad de camino. Si algo es ambiguo, elige la lectura más útil
   para el objetivo, dilo en el informe y termina el entregable. Guarda tu informe de forma incremental.
8. Al terminar, devuelve un resumen de menos de 450 palabras: los hallazgos de gravedad 4 y 5 con su
   evidencia, lo que cambiaría el plan, y lo que dejaste SIN VERIFICAR.
