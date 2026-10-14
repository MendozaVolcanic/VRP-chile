# ¿El canal OCR de Mirova-v1 también perdió filas? (pendiente iv de la tarea 0.1 del loop)

**Por qué.** El consolidado remoto de Mirova-v1 perdió 794 filas en cinco caídas silenciosas (#778). El canal OCR
(`registro_vrp_ocr.csv`) nunca se había revisado con el mismo método.

**Cómo.** `medir.py` recorre la última versión de cada día del OCR en la historia de Mirova-v1 (por la API, sin
clonar), con las mismas funciones de `scripts/referencia_mirova_unificada.py`, y cuenta las claves (volcán,
sensor, minuto) que alguna versión tuvo y la más nueva ya no. No escribe nada en el repo. Uso:
`python medir.py <raíz del repo>`. Salida: `salida.txt` (2026-10-14).

**Resultado.** 232 versiones diarias desde el 2026-01-20. La unión tiene 1.065 claves; la versión más nueva,
1.060. Se perdieron **5 filas, todas ALERTA_TERMICA_OCR**, cuyo último día con las filas fue el 2026-01-20 (3),
el 2026-02-05 (1) y el 2026-02-22 (1).

**Decisión: no se agregan a la referencia.** Las cinco caen en el tramo en que el OCR estaba inestable (siete
versiones y doce métodos de validación hasta el 2026-02-24, hito de `scripts/calidad_referencia_mirova.py`),
cuando el scraper reprocesaba y revalidaba filas: que desaparezcan ahí es lo esperable de una revalidación, no la
firma de una caída silenciosa como las del consolidado (que se llevó filas viejas de todos los meses). Además,
antes del 2026-06-13 el OCR no decide la etiqueta positiva (A119). Si más adelante el OCR pierde filas después
del 2026-06-13, este mismo script lo muestra y entonces sí corresponde una capa histórica para el OCR.
