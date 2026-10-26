# Verificador IA: resultados (2026-10-26)

Fuentes leídas hoy. Crossref y OpenAlex para los DOI; páginas oficiales para las políticas. AGU bloquea WebFetch y curl directo (403), así que se leyó la copia de Wayback del 2026-09-22.

| ID | Veredicto | Corrección |
|---|---|---|
| I1 | CONFIRMADO | La página de NHESS y la de GMD dicen lo mismo. Matiz: ninguna muestra fecha. |
| I2 | CONFIRMADO | Matiz: lo básico (gramática, ortografía, puntuación) no se declara. |
| I3 | CONFIRMADO | Ver detalle. |
| I4 | CONFIRMADO | Leído en Wayback (2026-09-22), no en vivo. |
| I5 | CONFIRMADO EN PARTE | Contenido exacto. La fecha «2023» no sale de la página actual. |
| I6 | CONFIRMADO EN PARTE | La cita está en la sección II.A.4, no en la URL indicada (sección V.A). |
| I7 | CONFIRMADO | Ver detalle. |
| I8 a I16 | CONFIRMADO | Ver detalle de cifras. |

## Detalle

**I1.** https://www.natural-hazards-and-earth-system-sciences.net/policies/ai_policy.html y https://www.geoscientific-model-development.net/policies/ai_policy.html. Ambas traen la frase «Generative AI must not be used for text or interpretations». El uso asistivo (gramática, ortografía, legibilidad) no se declara. El uso generativo sí se declara, nombrando la herramienta, en Methods o Acknowledgements. Se permiten ilustraciones y esquemas con IA si se cita la herramienta. Ninguna página trae fecha de vigencia.

**I2.** Elsevier permite herramientas de IA para apoyar la preparación, con «supervisión y control humanos». Pide una declaración de IA separada que aparece en el artículo publicado, al final del manuscrito antes de las referencias. El código escrito o editado con IA como parte de la investigación se declara en detalle en Methods. Termina con «Policy updated June 2026».

**I3.** https://www.springernature.com/gp/policies/editorial-policies/ai-manuscript-preparation. Tabla de riesgo con verde, ámbar y rojo. Rojo, «Not permitted»: escribir resultados o discusión de forma independiente, generar afirmaciones o interpretaciones científicas, listar la IA como autora. La guía de Bull. Volcanol. (https://link.springer.com/journal/445/submission-guidelines, leída con curl) dice que el uso de un LLM se documenta en Methods (o en otra parte adecuada si no hay Methods). La «AI assisted copy editing» no necesita declararse.

**I4.** AGU (copia Wayback 2026-09-22 de https://www.agu.org/publications/authors/policies). Quien use IA en la redacción, en imágenes o en la recolección y análisis de datos debe declarar herramienta y uso en Materials and Methods (o sección similar). Las herramientas de IA no pueden asumir responsabilidad por el trabajo, así que no son autoras. No se verificó en vivo, porque la página da 403.

**I5.** https://publicationethics.org/guidance/cope-position/authorship-and-ai-tools. Dice que la IA no puede ser autora y que el uso se declara en Materials and Methods (o similar), incluyendo redacción, imágenes y análisis. La página actual muestra «Version 1 published 20 August 2024» (es la versión del sitio nuevo). La declaración original es del 13 feb 2023 según una búsqueda web, sin leer la página original. Si el informe escribe «2023», acompáñalo de una nota de que la versión hoy en línea lleva fecha de 2024.

**I6.** ICMJE, «Updated January 2026» (https://www.icmje.org/recommendations/). La URL indicada (sección V.A) pide declarar el uso al enviar y describirlo «en la sección apropiada», pero no dice agradecimientos ni métodos. Esa precisión está en la sección II.A.4 (https://www.icmje.org/recommendations/browse/roles-and-responsibilities/defining-the-role-of-authors-and-contributors.html). La ayuda de redacción va en agradecimientos y el uso en recolección de datos, análisis o generación de figuras va en métodos. Corrección: citar la sección II.A.4 (y II.A.3), no solo la V.A.

**I7.** volcanica.org devuelve una página que redirige a /lander, una página de dominio estacionado (GoDaddy, `parking-lander`). La revista responde en https://www.jvolcanica.org/ojs/index.php/volcanica (OJS 3.3). En /about/submissions, la lista de verificación pide confirmar que se leyó y aceptó la «Volcanica Policy on Use of Artificial Intelligence (AI)».

**I8.** Crossref (10.1038/s41598-023-41032-5): Walters y Wilder, Sci Rep 13:14045, 2023. 636 citas en 84 textos. 55 % (GPT-3.5) y 18 % (GPT-4) inventadas. Entre las reales, 43 % y 24 % con errores sustantivos.

**I9.** Crossref (10.2196/53164): Chelli et al., JMIR 26:e53164, 2024. Tasas de alucinación 39,6 % (55/139) GPT-3.5, 28,6 % (34/119) GPT-4 y 91,4 % (95/104) Bard. El denominador es 119 referencias devueltas por GPT-4 (471 analizadas en total).

**I10.** Crossref (10.1097/cce.0000000000001474): Seifi y Seyfi, Crit Care Explor 8(9):e1474, publicado 2026-08-25. 300 referencias (3 modelos × 10 temas × 10). 165 (55,0 %) con alguna inexactitud y 85 (28,3 %) completamente inventadas. Ojo: modelos GPT-5.3, DeepSeek-V3 y Grok-4, con un rango por modelo de 8 % a 50 % de fabricación.

**I11.** OpenAlex (10.1038/s41467-025-58551-6): Wu et al., Nat Commun 16:3615, 2025. «Entre 50 % y 90 % de las respuestas no están totalmente respaldadas, y a veces contradichas» por las fuentes que citan. 7 LLM, 800 preguntas, 58.000 pares afirmación-fuente.

**I12.** Crossref (10.1098/rsos.241776): Peters y Chin-Yee, R Soc Open Sci 12:241776, 2025. OR 4,85 (IC 95 % 3,06 a 7,70) de generalización amplia frente a resúmenes humanos. Diez LLM, entre ellos Claude 3.7 Sonnet, 4900 resúmenes.

**I13.** Crossref y texto (nature.com): Gao et al., npj Digit Med 6:75, 2023. El texto completo dice que los resúmenes generados «contained fabricated numbers» en rangos parecidos a los reales; tamaños de cohorte con correlación logarítmica r = 0,76. El resumen sólo dice «completely generated data».

**I14.** Crossref (10.1126/sciadv.adt3813): Kobak et al., Sci Adv 11:eadt3813, 2025. «At least 13.5 %» de los resúmenes de 2024 procesados con LLM, sobre más de 15 millones de resúmenes de PubMed. Es una cota inferior, y llega a 40 % en algunos subcorpus.

**I15.** Weber-Wulff et al., Int J Educ Integr 19:26 (2023). El texto dice que todas las herramientas puntuaron bajo 80 % de exactitud y sólo 5 sobre 70 %. Liang et al., Patterns 4:100779 (2023). La versión publicada (PMC10382961) dice «average false-positive rate: 61.3 %» en ensayos TOEFL. El preprint de arXiv v3 dice 61,22 %, así que citar la versión publicada.

**I16.** Chen et al., npj Digit Med 8:605 (2025): cumplimiento de pedidos ilógicos de hasta 100 % en cinco LLM, en el dominio de relaciones entre fármacos. Perry et al., JBJS (publicado 2026-05-21): los modelos repiten la creencia del usuario en 56 % y perpetúan atribuciones incorrectas en 99 %. Lee et al., Proc ACM Web Conf 2023: tres tipos de plagio (literal, paráfrasis, ideas) en textos de GPT-2. La afirmación se sostiene, aunque «repiten la creencia del usuario» viene de Perry y «siguen pedidos ilógicos» de Chen; Chen tampoco es un estudio de redacción científica, sino de preguntas médicas.
