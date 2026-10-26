# Anexo de REVISION_S163: políticas de IA y riesgos documentados (2026-10-26)

Material de apoyo de `docs/paper/REVISION_S163.md` §3. Lo reunió un subagente (Opus) el 2026-10-26 leyendo las páginas
oficiales y resolviendo cada DOI en Crossref; la política de Volcanica la releyó la sesión autora en su PDF, y un
verificador con contexto limpio de otro modelo (Sonnet) contrastó las afirmaciones que el informe usa
(`experiments/_s163_paper_revision/VERIFICADOR_IA.md`). Las páginas de política cambian: releerlas antes de enviar.

**Correcciones del verificador** (`VERIFICADOR_IA.md`): COPE, la posición es de 2023 pero la página en línea dice
«Version 1 published 20 August 2024», y la fecha de 2023 salió de una búsqueda web; ICMJE, lo de agradecimientos y
métodos está en la sección II.A.4 (defining-the-role-of-authors-and-contributors.html), no en la página de IA; AGU,
la página da 403 en vivo y se verificó en Wayback (2026-09-22); Liang et al. 2023, citar la versión publicada (61,3 %),
no el preprint (61,22 %).

---

Consulta: 2026-10-26. Todas las páginas de política se leyeron en su versión oficial ese día (texto bajado
con curl o con el navegador interno; nada se tomó de resúmenes de terceros). Los DOI de la parte 2 se
resolvieron uno por uno contra `api.crossref.org/works/<DOI>` (título, autores, revista y año coinciden) y
las cifras salen del resumen en OpenAlex o Europe PMC, o del texto completo de acceso abierto donde se indica.
Los PDF y HTML descargados quedaron sólo en el directorio temporal de la sesión, no en el repo.

## Aviso previo sobre Volcanica: el dominio volcanica.org NO es la revista

`https://www.volcanica.org/` responde hoy con una página de estacionamiento de dominio (redirige a
`/lander`, servida por la plataforma de parking de GoDaddy, `img1.wsimg.com/parking-lander`). La revista
está en **https://www.jvolcanica.org/ojs/index.php/volcanica**. Conviene corregir la URL en cualquier
documento interno, y no enviar nada a volcanica.org.

## Parte 1: políticas de editoriales y organismos de ética

### 1.1 Lo que más importa para este manuscrito

**Volcanica prohíbe que la IA generativa produzca texto del manuscrito.** Sólo admite corrección de
estilo, gramática y traducción de texto escrito por humanos. El uso de IA para desarrollar o refinar
código sí está permitido, pero debe detallarse en Métodos. Si buena parte de la redacción salió de Claude,
el manuscrito tal como está **no cumple** la política de Volcanica: habría que reescribir el texto por los
autores (usando la IA, a lo más, para pulir) o elegir otra revista. Las revistas Copernicus/EGU (NHESS,
GMD) tienen la misma prohibición para texto e interpretaciones. Elsevier, Springer Nature y AGU lo
permiten con declaración y responsabilidad humana, con matices (ver tabla).

Además, al enviar a Volcanica el autor marca en la lista de verificación que leyó y acepta la política
de IA (página de envíos, «Submission Preparation Checklist»).

### 1.2 Tabla de políticas

| Organismo | ¿IA autora? | Qué declarar y dónde | ¿Distingue estilo de generación? | Imágenes y figuras | Revisores | Código | Verificado contra |
|---|---|---|---|---|---|---|---|
| **Volcanica** (Policy on Use of AI, v1.2, 12-ago-2026, rotulada «Public draft») | No: un LLM no puede rendir cuentas, no cumple criterios de autoría (§3.2). | Uso de IA en la investigación, incluido código: en Métodos (§4.2). Herramientas de visualización: en Métodos con nombre, versión y desarrollador (§5.3). Traducción del resumen a otro idioma: declarar en el manuscrito (§3.3). | Sí, explícito (§3.1). Prohíbe generar contenido o partes del texto (§3.2); permite mejorar legibilidad, corrección y traducción de texto humano, sin creación autónoma (§3.5). Cita: «AI usage is not permitted for the generation of text included in manuscripts» (§1.1). Prohíbe usar un LLM para resumir el manuscrito como base del abstract (§3.3). | Visualizaciones con IA sólo si derivan fielmente de los datos, declaradas en Métodos (§5.3). Imágenes primarias generadas con IA no, salvo que sean parte de la investigación y rotuladas (§5.4). Arte: autores o ilustrador (§5.4). | Prohibido todo uso de IA en la revisión; subir el manuscrito a un LLM se considera mala práctica (§6.1, §6.2). | Sí: «using AI to help develop or refine code» se detalla en Métodos (§4.2). | https://jvolcanica.org/docs/policies/AI-policy.pdf (enlazado desde https://www.jvolcanica.org/ojs/index.php/volcanica/about/submissions) |
| **Elsevier** (JVGR, RSE; «Policy updated June 2026») | No; tampoco citar la IA como autor. | Sección propia al enviar, que se publica. Título recomendado: «Declaration of generative AI and AI-assisted technologies in the manuscript preparation process». Nombre de la herramienta, propósito y grado de supervisión. Uso como parte del método: en Métodos. | Sí: gramática, ortografía y puntuación básicas no se declaran; cambios sustantivos de estructura u organización sí. | Explicativas (diagramas de flujo, esquemas): permitidas, declarando en la leyenda de cada figura y en la declaración general. Visualizaciones de datos: sólo si derivan de los datos, declarando modelo, versión y desarrollador en Métodos. Imágenes primarias: no. Resumen gráfico: no con herramientas generales de imágenes. | No subir el manuscrito a una herramienta de IA; uso sólo de apoyo (lenguaje del informe, búsqueda bibliográfica) con herramientas «privadas» y declarando el uso. | Sí (FAQ): código escrito o editado con IA se declara en detalle en Métodos; mismos estándares de validez y reproducibilidad. | https://www.elsevier.com/about/policies-and-standards/generative-ai-policies-for-journals |
| **Springer Nature, nivel grupo** (marco de riesgo verde/ámbar/rojo; sin fecha visible) | No (rojo: «Assigning authorship or accountability to AI systems»). | «AI Declaration» en el manuscrito, describiendo el uso y confirmando responsabilidad del autor, incluso en uso verde. Figuras: además en la leyenda. | Sí, por niveles. Verde: corrección, legibilidad, traducción. Ámbar: borradores de secciones a partir de material del autor, con verificación. Rojo (no permitido): «Writing results or discussion independently», generar afirmaciones o interpretaciones científicas. | Permitidas si derivan de datos o material verificable, con modelo y propósito declarados; las que no tienen insumo verificable, no. | No subir contenido a herramientas públicas o inseguras; la IA no puede sustituir la evaluación; declarar el uso. | Ámbito «research practice»: «code scaffolding» es verde; el código generado con IA debe tener revisión y validación humana (sección de figuras). | https://www.nature.com/nature-portfolio/editorial-policies/ai ; https://www.springernature.com/gp/policies/editorial-policies/ai-manuscript-preparation ; .../using-ai-in-research ; .../using-ai-in-peer-review |
| **Bull. Volcanol.** (guía de envío de la revista, Springer) | No: los LLM no cumplen criterios de autoría. | «Use of an LLM should be properly documented in the Methods section». | Sí: la corrección de estilo asistida por IA de texto humano **no necesita declararse**; no incluye creación autónoma de contenido. | Remite a la política de Springer sobre imágenes generadas con IA. | No lo trata en esa página (aplica la política del grupo). | No lo trata en esa página. | https://link.springer.com/journal/445/submission-guidelines |
| **AGU** (JGR, GRL, ESS; sin fecha visible) | No (adopta la posición de COPE). | En Materiales y Métodos (o sección similar): qué herramienta y cómo se usó, para escritura, imágenes o datos. | No distingue explícitamente estilo de generación en la página. | Incluidas en la obligación de declarar («production of images or graphical elements»). | Prohibido usar LLM para revisar en nombre del revisor y subir manuscritos; puede pulir su propio texto, declarándolo al editor. | No lo menciona en la sección de IA. | https://www.agu.org/publications/authors/policies (secciones «Authorship and AI Tools» y «Reviewing and AI Tools») |
| **Copernicus/EGU** (NHESS y GMD, texto idéntico en ambas) | La página de IA no lo trata (no encontré mención de autoría de IA en la política de publicación de NHESS). | Uso «generativo»: en Métodos o Agradecimientos, con nombre de la herramienta, propósito y alcance; el autor lo certifica al registrar el manuscrito. | Sí: uso «asistivo» (estructura de oraciones, legibilidad, gramática) no se declara. Cita: «Generative AI must not be used for text or interpretations». | Permite generar ilustraciones y esquemas con IA si se cita la herramienta. | Prohibido subir manuscritos o informes y prohibido generar informes con IA; sólo uso asistivo. | No lo menciona. | https://www.natural-hazards-and-earth-system-sciences.net/policies/ai_policy.html ; https://www.geoscientific-model-development.net/policies/ai_policy.html |
| **COPE** (posición «Authorship and AI tools», última revisión 13-feb-2023) | No: «AI tools cannot be listed as an author of a paper». | En Materiales y Métodos (o sección similar): qué herramienta y cómo se usó, en escritura, imágenes o datos. | No. | Incluidas en la obligación de declarar. | No lo trata en esta posición. | No lo trata. | https://publicationethics.org/guidance/cope-position/authorship-and-ai-tools (doi:10.24318/cCVRZBms, no resuelto en Crossref, se leyó la página) |
| **ICMJE** (Recommendations, «Updated January 2026»; orientadas a medicina, pero son referencia general) | No: no pueden responder por exactitud, integridad ni originalidad. | Al enviar, en la carta y en el trabajo: «Use of AI for writing assistance should be reported in the acknowledgment section»; uso en datos, análisis o figuras, en Métodos con herramienta, versión y prompts si aplica. | Implícita (escritura en agradecimientos, método en Métodos). | Figuras generadas con IA: en Métodos; el autor debe poder afirmar que no hay plagio en texto ni imágenes de IA. | Seguir la política de la revista o pedir permiso; mantener confidencialidad; declarar el uso. | No menciona código específicamente. | https://www.icmje.org/recommendations/browse/artificial-intelligence/ai-use-by-authors.html ; .../ai-use-by-reviewers.html ; .../roles-and-responsibilities/defining-the-role-of-authors-and-contributors.html ; .../manuscript-preparation/preparing-for-submission.html |

### 1.3 Observaciones sobre los textos

- **Volcanica**: el documento se rotula «Public draft» (v1.2) y el correo de contacto del final trae una
  errata (`editor@jvolcania.org`; el correcto, en la cabecera, es `editor@jvolcanica.org`). Pide además
  comprobar cada referencia, en especial el DOI, porque la IA puede producir referencias alucinadas (§3.4).
- **Springer Nature contra Bull. Volcanol.**: la guía de la revista conserva el texto anterior (Métodos;
  la corrección de estilo no se declara), mientras el marco del grupo pide describir incluso el uso verde
  en una «AI Declaration». Ante la duda, declarar de más no tiene costo según el propio grupo
  («Declaration does not disadvantage your manuscript»).
- **Elsevier** aplica la misma política a todas sus revistas; no revisé las guías particulares de JVGR ni
  de RSE.
- **AGU** remite para buenas prácticas a las guías de Wiley; no las revisé.
- Ninguna de las siete exige un formato específico para declarar el uso de un asistente en el código
  más allá de «describirlo en Métodos» (Volcanica, Elsevier) o validarlo humanamente (Springer Nature).

## Parte 2: riesgos documentados en literatura revisada por pares

Todas las filas: DOI resuelto en Crossref el 2026-10-26 con metadatos coincidentes. «Fuente de la cifra»
indica de dónde salió el número.

| Riesgo | Referencia | Qué midió | Cifra principal (con denominador) | Verificado contra |
|---|---|---|---|---|
| Referencias inventadas | Walters, W.H. y Wilder, E.I. (2023). Fabrication and errors in the bibliographic citations generated by ChatGPT. *Scientific Reports* 13, 14045. | 84 revisiones breves (42 temas, GPT-3.5 y GPT-4), 636 citas. | Inventadas: 55 % (GPT-3.5) y 18 % (GPT-4). Con errores sustantivos entre las reales: 43 % y 24 %. Resumen. | doi:10.1038/s41598-023-41032-5 |
| Referencias inventadas | Bhattacharyya, M., Miller, V.M., Bhattacharyya, D. y Miller, L.E. (2023). High rates of fabricated and inaccurate references in ChatGPT-generated medical content. *Cureus* 15(5), e39238. | 30 artículos médicos breves de GPT-3.5, 115 referencias. | 47 % inventadas, 46 % reales pero inexactas, 7 % reales y exactas (de 115). Resumen. | doi:10.7759/cureus.39238 |
| Referencias inventadas | Chelli, M. et al. (2024). Hallucination rates and reference accuracy of ChatGPT and Bard for systematic reviews. *J. Med. Internet Res.* 26, e53164. | Replicar 11 revisiones sistemáticas; 471 referencias. | Alucinadas: 55/139 (39,6 %) GPT-3.5, 34/119 (28,6 %) GPT-4, 95/104 (91,4 %) Bard. Resumen. | doi:10.2196/53164 |
| Referencias inventadas (modelos 2026) | Seifi, A. y Seyfi, A. (2026). Hallucination rate of peer-reviewed citations generated by large language models in neurocritical care. *Critical Care Explorations* 8(9), e1474. | GPT-5.3, DeepSeek-V3 y Grok-4, sin búsqueda web, 300 referencias. | 165/300 (55,0 %) con alguna inexactitud; 85/300 (28,3 %) completamente inventadas. Resumen. Nota: Crossref lista dos autores casi homónimos («Seifi» y «Seyfi»); no lo comprobé en el artículo. | doi:10.1097/cce.0000000000001474 |
| DOI inventados (incluye Claude) | Kim, E., Kipchumba, F. y Min, S. (2025). Geographic variation in LLM DOI fabrication. *Publications* 13(4), 49. | GPT-4o-mini, Claude-3-haiku, Gemini-2.0-flash-lite y DeepSeek V3; 3.451 citas validadas contra Crossref. | Tasa de alucinación de DOI sobre 80 % para países de ingreso bajo; sube para publicaciones de la década de 2020. El resumen no da la tasa global. | doi:10.3390/publications13040049 |
| Cita real que no respalda la afirmación | Wu, K. et al. (2025). An automated framework for assessing how well LLMs cite relevant medical references. *Nature Communications* 16, 3615. | 7 LLM, 800 preguntas, 58.000 pares afirmación y fuente. | Entre 50 y 90 % de las respuestas no están totalmente respaldadas por las fuentes que citan; GPT-4o con búsqueda web: cerca de 30 % de las afirmaciones sin respaldo. Resumen. | doi:10.1038/s41467-025-58551-6 |
| Atribuciones erróneas propagadas y complacencia | Perry, A.J. et al. (2026). Current artificial intelligence large language models exhibit sycophantic behavior in orthopaedic contexts. *J. Bone Joint Surg.* | 2 LLM generales; pistas correctas e incorrectas, creencias del usuario, información falsa insertada. | Exactitud de 78 % baja a 48 % con pistas incorrectas (error por complacencia 52 %); repiten la creencia del usuario en 56 %; perpetúan atribuciones incorrectas en 99 % de los casos. El resumen no da los denominadores. | doi:10.2106/jbjs.25.01576 |
| Complacencia (sycophancy) | Chen, S. et al. (2025). When helpfulness backfires: LLMs and the risk of false medical information due to sycophantic behavior. *npj Digital Medicine* 8, 605. | 5 LLM de frontera ante pedidos ilógicos (equivalencias de fármacos falsas). | Cumplimiento inicial de hasta 100 % con el pedido ilógico; mejora con prompts y ajuste fino. Resumen (sin denominador). | doi:10.1038/s41746-025-02008-z |
| Exageración de la evidencia | Peters, U. y Chin-Yee, B. (2025). Generalization bias in large language model summarization of scientific research. *Royal Society Open Science* 12(4), 241776. | 10 LLM (entre ellos Claude 3.7 Sonnet), 4.900 resúmenes comparados con el texto original. | DeepSeek, ChatGPT-4o y LLaMA 3.3 70B generalizan de más en 26 a 73 % de los casos, aun pidiendo exactitud; frente a resúmenes humanos, razón de odds 4,85 (IC 95 % 3,06 a 7,70). Modelos nuevos peores que los antiguos. Resumen. Verificado: existe y dice lo que se le atribuye. | doi:10.1098/rsos.241776 |
| Inconsistencias factuales al resumir | Tang, L. et al. (2023). Evaluating large language models on medical evidence summarization. *npj Digital Medicine* 6, 158. | GPT-3.5 y ChatGPT resumiendo evidencia médica en 6 dominios, evaluación humana. | Resúmenes factualmente inconsistentes y afirmaciones excesivamente convincentes o inciertas; peor con contextos largos. El resumen no da porcentajes. | doi:10.1038/s41746-023-00896-7 |
| Números inventados y detección | Gao, C.A. et al. (2023). Comparing scientific abstracts generated by ChatGPT to real abstracts with detectors and blinded human reviewers. *npj Digital Medicine* 6, 75. | 50 resúmenes reales y 50 generados; detector de IA, detector de plagio, revisores ciegos. | Los tamaños de cohorte generados eran plausibles pero inventados; 100 % de originalidad en el detector de plagio; revisores identificaron 68 % de los generados y marcaron como generados 14 % de los reales; AUROC del detector 0,94. Resumen. | doi:10.1038/s41746-023-00819-6 |
| Detección poco fiable | Weber-Wulff, D. et al. (2023). Testing of detection tools for AI-generated text. *Int. J. Educ. Integrity* 19, 26. | 14 detectores (12 públicos, Turnitin y PlagiarismCheck), 54 casos de prueba. | Ninguna herramienta superó 80 % de exactitud; con texto de IA parafraseado por máquina, exactitud de 26 %. Texto completo de acceso abierto. | doi:10.1007/s40979-023-00146-z |
| Sesgo de detectores contra no nativos | Liang, W., Yuksekgonul, M., Mao, Y., Wu, E. y Zou, J. (2023). GPT detectors are biased against non-native English writers. *Patterns* 4(7), 100779. | 7 detectores sobre 91 ensayos TOEFL y 88 ensayos escolares de EE. UU. | Tasa media de falsos positivos en ensayos TOEFL: 61,3 %. Texto completo (PMC10382961). Relevante para un autor que escribe en inglés como segunda lengua. | doi:10.1016/j.patter.2023.100779 |
| Marcadores léxicos de LLM | Kobak, D., González-Márquez, R., Horvát, E.-Á. y Lause, J. (2025). Delving into LLM-assisted writing in biomedical publications through excess vocabulary. *Science Advances* 11(27), eadt3813. | Más de 15 millones de resúmenes de PubMed, 2010 a 2024, palabras de estilo en exceso. | Al menos 13,5 % de los resúmenes de 2024 procesados con LLM (cota inferior); hasta 40 % en algunos subcorpus. Resumen. | doi:10.1126/sciadv.adt3813 |
| Prevalencia de texto modificado por LLM | Liang, W. et al. (2025). Quantifying large language model usage in scientific papers. *Nature Human Behaviour* 9(12), 2599 a 2609. | 1.121.912 preprints y artículos (arXiv, bioRxiv, Nature portfolio), 2020 a sep-2024. | Hasta 22 % de contenido modificado por LLM en informática; hasta 9 % en matemáticas y Nature portfolio. Resumen en Europe PMC. | doi:10.1038/s41562-025-02273-8 |
| Restos de chatbot no declarados en revistas | Strzelecki, A. (2024). «As of my last knowledge update»: How is content generated by ChatGPT infiltrating scientific papers published in premier journals? *Learned Publishing* 38(1), e1650. | Artículos en revistas indexadas (WoS, Scopus) con frases típicas de ChatGPT. | Hay artículos con esas marcas sin uso declarado, ya citados por otros, incluso en ciencias ambientales e ingeniería. El resumen no da el número de artículos; no revisé el texto completo. | doi:10.1002/leap.1650 |
| «Tortured phrases» | Teixeira da Silva, J.A. (2023). «Tortured phrases» in preprints. *Current Medical Research and Opinion* 39(5), 785 a 787. | Comentario sobre el detector del Problematic Paper Screener. | 213 preprints con frases torturadas (13 sobre COVID-19), al 10-ene-2023. Advierte no equipararlas automáticamente con mala conducta. Ojo: este fenómeno nace de parafraseadores automáticos, no específicamente de LLM. | doi:10.1080/03007995.2023.2201098 |
| Regurgitación y plagio | Lee, J., Le, T., Chen, J. y Lee, D. (2023). Do language models plagiarize? *Proc. ACM Web Conference 2023*, 3637 a 3647. | Plagio literal, de paráfrasis y de ideas de GPT-2 contra sus datos de entrenamiento. | Los tres tipos de plagio están extendidos y crecen con el tamaño del modelo. Sin cifra única en el resumen. Modelo antiguo (GPT-2); no hay medición equivalente con los modelos actuales en esta lista. | doi:10.1145/3543507.3583199 |

### 2.1 Qué significa para este manuscrito (lectura del autor de este informe, no de los estudios)

1. **Referencias**: el riesgo mejor medido. Toda referencia que haya pasado por Claude (incluida la
   corrección de estilo, que puede alterar el texto de la cita, como advierte Springer) se comprueba
   contra Crossref y contra el PDF: existencia, metadatos y que la página citada diga lo que se le atribuye
   (Wu 2025 y Perry 2026 muestran que una cita real puede no respaldar la frase).
2. **Números**: Gao 2023 muestra cifras plausibles pero inventadas. Cada número del texto debe salir de un
   script, no de una redacción.
3. **Alcance de las conclusiones**: Peters y Chin-Yee 2025 midieron la tendencia a generalizar de más, con
   Claude 3.7 Sonnet entre los modelos. Revisar resumen y conclusiones frase por frase contra los
   resultados (por ejemplo, que lo medido en un volcán o un sensor no se enuncie para todos).
4. **Complacencia**: con un asistente que tiende a darle la razón al usuario, las conclusiones que el autor
   ya esperaba son las que más necesitan un verificador independiente.
5. **Detección**: los detectores no son fiables (Weber-Wulff 2023) y penalizan a quien no escribe en su
   lengua materna (Liang 2023); el riesgo real no es «ser detectado» sino infringir una política que
   prohíbe el texto generado (Volcanica, Copernicus) o no declararlo.

## Lo que no pude verificar

- No encontré **fecha de actualización** en las páginas de Springer Nature ni de AGU.
- No revisé las guías particulares de **JVGR**, **RSE**, **JGR**, **GRL** ni **Earth and Space Science**;
  asumí que aplica la política general del editor, porque así se presenta cada una.
- El DOI de la posición de **COPE** (10.24318/cCVRZBms) no lo resolví en Crossref; se leyó la página.
- **Copernicus**: no encontré una política de IA a nivel editorial central (la URL de política general de
  publications.copernicus.org dio 404); las páginas por revista (NHESS, GMD) son idénticas.
- **Estudio sobre «números alterados»** específicamente (LLM que cambia cifras de un texto dado al
  corregirlo): no localicé uno con DOI; sólo Gao 2023 (cifras inventadas) y Tang 2023 (inconsistencias
  factuales, sin porcentaje en el resumen).
- **Sharma et al. 2024** (complacencia, ICLR) y **Carlini et al. 2021** (extracción de datos de
  entrenamiento, USENIX Security) no tienen DOI en Crossref; no los incluí.
- **Tortured phrases**: el trabajo fundacional (Cabanac, Labbé y Magazinov 2021) es un preprint de arXiv;
  no encontré versión revisada por pares.
- Cifras sin denominador en el resumen (Chen 2025, Perry 2026, Strzelecki 2024, Tang 2023, Kim 2025 tasa
  global): no revisé el texto completo.
- Un candidato (Jain et al. 2025, *J. Cranio-Maxillofac. Surg.* 53(10), 1871 a 1872,
  doi:10.1016/j.jcms.2025.08.004) resuelve en Crossref, pero no tiene resumen accesible y parece una carta
  de dos páginas; no lo incluí en la tabla.
