# Revisión del paper VRP Chile: estado, estructura y riesgos de la IA (S163, 2026-10-26)

Pedido de Nicolás (2026-10-26): «¿cómo va el paper? ¿cómo deberíamos estructurarlo? investiga cómo la IA ha estado
ayudando a su escritura, dónde deberíamos tener cuidado, qué cosas se deberían doble chequear».

**Qué es este documento.** Un diagnóstico y una propuesta para que decidas. No reescribe nada del manuscrito. Se apoya
en la revisión del 2026-10-16 (`experiments/_s152_paper_revision/INFORME_CAMBIOS_PAPER_v2.md`, 69 filas, verificada
con contexto limpio) y **no la repite**: agrega lo que cambió después (detector K, código de MIROVA publicado,
programa por sensor) y lo que esa revisión no cubrió (el esqueleto de S72, la estructura, la IA).

**Rutas.** Las relativas cuelgan de `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\`. Los números
de línea valen para `origin/main` en `e949f06c4` (2026-10-26), salvo que se indique la rama `loop/activo`.

**Marcas.** FALSA, REBAJADA (cierta en parte), DESACTUALIZADA (era cierta o el número cambió), FALTA, ERROR DE CITA.
Lo que no medí yo va como SIN VERIFICAR o con el puntero a quien lo midió.

---

## 0. Resumen en una pantalla

**Estado.** Hay tres secciones en prosa, en inglés, de septiembre (§4 Background, §5 Methods, §6 Validation, en
`docs/paper/`) y un esqueleto anotado de mayo, actualizado en julio (`docs/PAPER_VRP_CHILE_DRAFT_S72.md`), que cubre
título, resumen, introducción, casos, discusión y conclusiones. Faltan en prosa: introducción, casos, discusión,
conclusiones, resumen; faltan todas las figuras, la bibliografía con DOI (`.bib`), los coautores, la declaración de
autoría (CRediT), la de disponibilidad de datos y la de uso de IA. Desde S152 el único commit que tocó `docs/paper/` es
#910 (seguimiento de #906, no una aplicación de ese informe): cubre 2 de sus 69 filas, la geolocalización de MODIS
(5-1) y en parte la banda primaria (5-2), en `sec5_methods.md:7-12`. `numbers.json` es del 2026-09-07
(`83b9df8ff`).

**Lo que cayó y cambia el paper entero** (detalle en §1.2):

1. **La premisa que motiva el paper es falsa desde julio de 2026.** El esqueleto dice que VRP Chile sería «la primera
   implementación open source publicada del algoritmo MIROVA» y §4 cierra con «no reference implementation has been
   released» (`sec4_background.md:142-145`). MIROVA publicó en OSF (zm62w, licencia MIT) su código operacional de
   VIIRS 750 en MATLAB (D34, `docs/MIROVA_DIVERGENCES.md:3373-3378`; la copia del repo trae `LICENSE.txt`
   MIT y un `CITATION.txt` con fecha de liberación 2026-07-23; D34 da el 2026-07-24, fecha de la página de OSF). La prueba de ausencia del esqueleto era una
   búsqueda de Perplexity (`docs/PAPER_VRP_CHILE_DRAFT_S72.md:11` y `:102-103`).
2. **§5 describe un detector que ya no corre.** Dice que el Test 1 integrado es un camino de detección y que los Tests 2
   y 3 se aplican con la conectiva de la fórmula (`sec5_methods.md:81-84` y `:97-99`). Desde #850 (2026-10-18)
   producción corre K: Test 1 integrado apagado (`enable_test1_path: false`, `pipeline/profiles/mirova_equivalent.yaml:268`),
   conectiva `max` (`:271`) y banda 22 primaria (`:578`).
3. **§6 valida otro detector, y su dato ya no existe.** Los números de §6 son del detector anterior y su ventana cruza
   #535 (2026-08-28, A104). Desde #883 (2026-10-21) el histórico de los 11 Tier A está reprocesado con K (marca S160 de
   A100 en `CLAUDE.md`), así que correr hoy `scripts/paper_numbers.py` sobre la misma ventana da números de K que no
   calzan con el texto. A eso se suma lo que S152 ya marcó: la afirmación de que no se puede reportar precisión es falsa
   (hay negativos limpios).

**Propuesta de estructura, en una línea** (detalle en §2): dejar de presentarlo como «la primera implementación» y
presentarlo como **un estudio de reproducibilidad de un producto operacional**: qué pasa cuando se reconstruye MIROVA
desde lo que publica (papers, base OSF, código de VIIRS 750, salida NRT), medido contra su propia salida en las dos
direcciones. Ese marco convierte en resultado lo que hoy está disperso como «divergencias», y el resultado central de
VIIRS 750 (port del código validado contra el intérprete original) ya existe. MODIS y VIIRS 375 dependen del programa
por sensor.

**Lo más urgente: la revista elegida no acepta texto generado por IA.** La política de Volcanica (v1.2, 2026-08-12)
dice «AI usage is not permitted for the generation of text included in manuscripts» (§1.1). §4, §5 y §6 en prosa los
redactó un agente (`docs/paper/README.md`), así que **no se pueden enviar a Volcanica tal como están**. El código hecho
con IA sí se admite, declarado en métodos. O escribes tú el texto (la IA sólo corrige el tuyo) o cambias a una revista
que permita la asistencia declarada (§3).

**Lo que la IA hizo mal en este paper, con ejemplos del propio borrador** (detalle en §1.2 y §4): una atribución de
grupo equivocada (HOTSAT a Massimetti y a Campus, cuando es de INGV Catania), un número de línea de un `.txt` citado
como si fuera sección del paper («§687»), una ausencia «verificada» con un buscador, cierres escritos más fuertes que
la evidencia («physically irreducible», «100% bug elimination») y números de una auditoría que después no se
reprodujeron. Ninguno es exótico: son exactamente los riesgos que documenta la literatura (§3).

**Decisiones que te tocan** (§5): revista y quién escribe el texto (la primera, porque cambia todo lo demás); el
marco del paper; si se espera al paquete de VIIRS 750 (V750-B no se despacha antes
del 2026-11-03); la ventana de validación; qué hacer con el «más allá de MIROVA»; el correo a Coppola antes o después (nunca se envió);
el texto de la declaración de IA; y la licencia, porque hoy el repo es público pero no tiene ninguna (N-18).

---

## 1. Estado del manuscrito

### 1.1 Inventario

| archivo | qué es | última edición | estado real |
|---|---|---|---|
| `docs/PAPER_VRP_CHILE_DRAFT_S72.md` | esqueleto anotado: §0 decisiones, título, resumen, intro, casos, discusión, conclusiones, venue, autoría, plazos | S120 (2026-07-01) | la mayoría de sus números y varias premisas cayeron (§1.2) |
| `docs/paper/README.md` | reglas de la carpeta (números por script, localizadores de cita) | S141 (2026-09-14) | las reglas valen; la tabla de estado está vieja y declara vigente el esqueleto S72 (`README.md:24`), que trae las afirmaciones falsas N-2 y N-9 a N-13 |
| `docs/paper/sec4_background.md` | §4, MIROVA como está publicado | 2026-09-15 | sana salvo el cierre (§1.2 N-1) y lo de S152 (3 REBAJADA, 1 FALTA) |
| `docs/paper/sec5_methods.md` | §5, nuestra implementación | 2026-10-26 (#910) | describe el detector anterior a K; S152: 4 FALSA, 10 REBAJADA |
| `docs/paper/sec6_validation.md` | §6, validación | 2026-09-15 | hay que rehacerla; S152: 5 FALSA |
| `docs/paper/numbers.json`, `TABLAS.md` | salida de `scripts/paper_numbers.py` | 2026-09-07 | el script no usa la unión histórica, ni la regla SN, ni negativos limpios, ni tramos A119 (S152 T-4); el dato de origen cambió con #883 |
| `experiments/_s152_paper_revision/` | revisión de S152 y su verificador | 2026-10-16 | vigente; ninguna de tus tres decisiones (a, b, c) quedó registrada como tomada |

### 1.2 Lo que cayó después de S152, o que S152 no revisó

S152 revisó sólo `docs/paper/`. El esqueleto de S72 todavía manda para título, resumen, introducción, casos,
discusión y conclusiones (`docs/paper/README.md:24`), así que también entra.

| id | dónde | afirmación | evidencia | clase |
|---|---|---|---|---|
| N-1 | `sec4_background.md:142-145` | «no reference implementation has been released» | código operacional de VIIRS 750 en OSF zm62w desde julio de 2026, MIT (D34, `docs/MIROVA_DIVERGENCES.md:3375-3378`, que cita Coppola et al. 2026, *Sci. Data*, p. 21, «Code Availability», página no renderizada por mí; copia en `experiments/_s158_d17_diseno/osf_codigo_mirova/` con `LICENSE.txt` y `CITATION.txt`) | FALSA (ya lo era cuando se escribió, el 2026-09-15) |
| N-2 | `PAPER_VRP_CHILE_DRAFT_S72.md:11-14`, `:59-61`, `:102-104`, `:302`, `:334` | «first published open source implementation»; «no hay implementación open source publicada (verified via Perplexity Deep Research)» | la misma de N-1; además, una búsqueda con un buscador conversacional no prueba una ausencia | FALSA |
| N-3 | `sec5_methods.md:81-84` | Tests 2 y 3 «literally, as a conjunction that keeps the statistical OR branch» | producción usa `max` desde #850 (`mirova_equivalent.yaml:271`); D26 sigue abierta y sin medir bajo `max` (`docs/MIROVA_DIVERGENCES.md:2904`) | DESACTUALIZADA |
| N-4 | `sec5_methods.md:97-99` | el Test 1 integrado en 3 km es un camino de detección | apagado en producción desde #850 (`mirova_equivalent.yaml:268`; D30, `docs/MIROVA_DIVERGENCES.md:3027`) | DESACTUALIZADA |
| N-5 | `sec5_methods.md:85-87` | diferenciales contra la media de los ocho vecinos, «following the paper» | fiel al paper; el código de MIROVA para VIIRS 750 usa 3 × 3 con el central (D34). El texto tiene que decir de qué fuente sale cada pieza (paper o código) | REBAJADA |
| N-6 | `sec6_validation.md` entera; `numbers.json` | recall y magnitud de la ventana 2026-01-01 a 09-07 | detector anterior a K, ventana que cruza #535; el histórico se reprocesó con K en #883 (marca S160 de A100) | DESACTUALIZADA |
| N-7 | `sec5_methods.md:7-12` (corregido en #910) | MOD03 se baja y no se usa; adopción pendiente (D35) | correcto hoy; cambia cuando se adopte MxD03 dentro del paquete MODIS (programa por sensor §5, MOD-B y MOD-D) | vigilar |
| N-8 | todo §6 futuro | ventanas de validación | Suomi NPP deja de operar el 2026-11-02 13:00 UTC (programa por sensor §1, punto 8): toda ventana posterior es otro régimen | FALTA |
| N-9 | `PAPER_VRP_CHILE_DRAFT_S72.md:96`, `:120`, `:122`, `:322`, `:381`, `:383` | «Massimetti 2020 (HOTSAT)», «Campus 2022 (HOTSAT contextual dNTI)», «HOTSAT (INGV-Pisa)» | HOTSAT es de INGV Catania (`documentacion/BIBLIOGRAPHY_SYNTHESIS.md:433`); Campus et al. 2022 es «The transition from MODIS to VIIRS...» (`sec4_background.md:155`) | ERROR DE CITA (grupo y paper equivocados, A9) |
| N-10 | `PAPER_VRP_CHILE_DRAFT_S72.md:154`, `:251` | «False positives "typically <5 MW" (§687)»; el tope de 5 MW «siguiendo Coppola 2016» | «687» es una línea de `documentacion/sp426_5.txt` (el encabezado «Enhanced volcanic hotspot detection»; la frase está en las líneas 689 a 692), y SP426.5 no numera sus secciones. El paper dice que las falsas alertas suelen radiar menos de 5 MW; no propone un tope, y S146 concluyó que no lo sostiene (`docs/AUDIT_S146.md:90-91`, C-02, hallazgo de auditor sin verificador) | ERROR DE CITA |
| N-11 | `PAPER_VRP_CHILE_DRAFT_S72.md:63`, `:158` | umbrales dual-ROI «Coppola (2016, Table 2)» | SP426.5 no tiene Tabla 2: el verificador renderizó las 25 páginas y los umbrales están en la Tabla 1, p. 187 impresa (visor 7), que es la que cita §5 (`sec5_methods.md:79`, comentario `src`) | ERROR DE CITA (tabla inexistente) |
| N-12 | `PAPER_VRP_CHILE_DRAFT_S72.md:70-77`, `:219-223`, `:335-339` | recall 98,4 / 84,5 / 100 % (MODIS cráter); «9/11 en banda»; residual norte «physically irreducible» (l. 77) e «indistinguibles» (l. 337-339) | la «recall cráter» de MODIS no mide detección (S152, grave 3); el «irreducible» de A82 está rebajado (S146 y S157, marcas en `CLAUDE.md`, A82) y D11 quedó sin su condición de cierre (S157) | FALSA |
| N-13 | `PAPER_VRP_CHILE_DRAFT_S72.md:251-253`, `:313-314` | D9 «100% bug elimination»; «D3 resuelto S17. D9 resuelto» | D9 volvió a abrirse en su cara de co-validación (S146 V-01, marca en `CLAUDE.md` A23); el cierre de D3 se apoya en una ecuación mal atribuida (S146 C-06) | FALSA |
| N-14 | `PAPER_VRP_CHILE_DRAFT_S72.md:272-275` (§7bis) | «~95 % de las detecciones extra son reales; el clon las hereda y se clasifican» | A54 sin re-medir (S152, 6-15); el criterio de victoria del 2026-10-13 dice que la réplica calla donde MIROVA calla y el valor agregado va en `experimental` (`docs/MISSION.md:81-131`) | DESACTUALIZADA, choca con la decisión 3 de S120 |
| N-15 | `PAPER_VRP_CHILE_DRAFT_S72.md:194`, `:352` | «796 passed (S119)» | número de julio | DESACTUALIZADA |
| N-16 | repo público citado como disponibilidad de datos (`PAPER_VRP_CHILE_DRAFT_S72.md:348-355`) | el repo es el material suplementario | `origin/main` tiene 78 imágenes de páginas de papers (88 PNG en `experiments/_s146_auditoria/`, `_s149_audit/`, `_s150_audit/`, `_s158_audit/` y `_s158_audit_r2/`, de los que 10 son figuras de gránulos), unas 34 de SP426.5 (derechos de la Geological Society) y otras del capítulo de Springer, Campus 2024 y Aveni 2024, sin licencia abierta; sólo Campus 2022 y Coppola 2023 son CC BY, y Coppola 2026 es CC BY-NC-ND y un PDF con copyright (`documentacion/steffke_harris_2011_review_hotspot_algorithms_10.1007-s00445-011-0487-7.pdf`); la regla de S158 dice que los renders van fuera del repo público | FALTA (limpiar antes de enviar) |
| N-17 | `PAPER_VRP_CHILE_DRAFT_S72.md:357-370` | agradecimiento con declaración de IA | el texto existe pero no está contrastado con la política de la revista (§3) | FALTA |
| N-18 | `PAPER_VRP_CHILE_DRAFT_S72.md:79-80`, `:344` | «published under MIT license»; «Código MIT» | el repo es público pero **no tiene licencia** (sin archivo `LICENSE` en `origin/main`; `gh repo view --json licenseInfo` vacío, 2026-10-26); el propio esqueleto la deja por decidir (`:350`, `:471`). Sin licencia es «código público», no «abierto» (lo detectó la retrospectiva del proceso, `docs/PLAN_PROCESO_VRP_CHILE_S163.md` §0, PR #913) | FALSA |
| N-19 | `PAPER_VRP_CHILE_DRAFT_S72.md:62-66`, `:182` | coeficientes «empirically calibrated against the MIROVA OSF v2.5 database (median error ≤0.17%)» | el 0,17 % es el desajuste entre la **fórmula de Di Bella** para VIIRS 750 y el coeficiente reconstruido desde las 48.360 filas del OSF (`experiments/21_results.json:67-69`, 0,1689 %); MODIS y VIIRS 375 calzan con error del orden de 1e-14 (`:57`, `:81`). No es un error de calibración, y además la fórmula que calza es de un paper de INGV Catania (A9; S152 T-3) | REBAJADA |

Cuento de N-9 a N-13 como **errores de la redacción asistida**: tienen la forma de lo que documenta la literatura
(§3.2) y ninguno lo habría producido alguien leyendo el PDF.

---

## 2. Estructura propuesta

### 2.1 Qué pregunta responde el paper

> ¿Hasta dónde se puede reproducir un producto operacional de monitoreo térmico volcánico (MIROVA NRT) desde lo que
> su grupo publica, y cómo se mide esa réplica contra la salida del original, en las dos direcciones y sensor por
> sensor?

El marco de S72 («la primera implementación», «validada») dependía de una premisa que cayó (N-1) y de una métrica
que no medía lo que decía (N-12). El marco de reproducibilidad no depende de ninguna de las dos, y aprovecha lo que el
proyecto sí encontró:

1. **Una réplica pública (abierta cuando tenga licencia, N-18), operando, con evaluación en las dos direcciones.** Alertas de MIROVA que perdemos y
   publicaciones nuestras donde MIROVA miró y no vio nada (negativos limpios), con alertas protegidas de 1 MW o más,
   regla SN, por sensor y por tramo de calidad de la referencia (`docs/MISSION.md:81-131`). Ese diseño de evaluación
   es reutilizable para cualquier réplica de un producto satelital.
2. **Dónde la descripción publicada no alcanza.** El catálogo de divergencias (D1 a D35) dice, pieza por pieza, qué
   sale del paper, qué del código, qué de la base OSF y qué es decisión nuestra. Con el código de VIIRS 750 hay un
   caso raro y valioso: tres implementaciones del mismo algoritmo (fiel al paper, fiel al código, la salida del
   original) comparadas sobre las mismas pasadas.
3. **La calidad de la referencia como variable.** La tabla de MIROVA y el OCR no sirven igual todo el año (A119); un
   resultado sin esa estratificación es un número plausible y equivocado. Pocas validaciones lo declaran.
4. **Contexto operacional chileno.** 45 volcanes, 11 en serie continua, la erupción de Nevados de Chillán de 2026 y el
   cese de Suomi NPP en medio del período.

Lo que **no** debería ser el aporte: «la primera implementación», «validada» como adjetivo sin métrica, ni el valor
agregado sobre MIROVA (ese va en `experimental` y se valida contra OVDAS y SWIR, no contra MIROVA, A115). Mi
recomendación es dejar el «más allá de MIROVA» para un segundo paper: en este choca con el criterio de victoria y no
tiene validación propia todavía (programa por sensor §6: bloqueado por la cronología de OVDAS, tarea 1.11).

### 2.2 Revista

Volcanica quedó decidida en S120 por costo (`PAPER_VRP_CHILE_DRAFT_S72.md:20-26`) y el marco nuevo le sigue
calzando. Si el paper se vuelve más «software y método» que «volcanología», la alternativa sin costo de publicación
es Geoscientific Model Development (Copernicus), que exige código y datos archivados con DOI; antes de cambiar,
revisar su política vigente de cargos. **Pero las dos prohíben el texto generado por IA** (§3.1), y eso pesa más que el
calce temático: con Volcanica o GMD el texto lo escriben los autores. Las revistas de Elsevier, Springer Nature y AGU
permiten la asistencia declarada, con costo de publicación en acceso abierto o con muro de pago.

### 2.3 Secciones

| § | contenido | de dónde sale | listo | depende de |
|---|---|---|---|---|
| 1 Introducción | monitoreo térmico, MIROVA como referencia operacional, el problema de reproducir un producto operacional, la pregunta | esqueleto S72 §3 sin la premisa N-2 | no | marco (decisión D1) |
| 2 MIROVA como está publicado | papers, base OSF, código de VIIRS 750, salida NRT; qué describe cada fuente | `sec4_background.md` + D34 | casi: corregir N-1 y lo de S152 §2.1 | nada |
| 3 Datos y referencia | L1B, sensores, volcanes; la referencia NRT (tabla y OCR), su calidad por tramo (A119), negativos limpios, alertas protegidas, regla SN; el OSF | `docs/audit_s139/MAPA_BASES_MIROVA_V1.md`, `scripts/calidad_referencia_mirova.py`, `docs/S151_CRITERIO_CLASE_MIROVA.md` | material listo, prosa no | permiso de uso de los datos de mirovaweb.it (§4, D-datos) |
| 4 Implementación | la cadena, K, qué pieza viene de qué fuente; coeficientes k desde el OSF | `sec5_methods.md` reescrita con K | no | si se adopta un paquete por sensor antes de enviar, se describe ese |
| 5 Diseño de la evaluación | criterio de victoria, unidades (pasada y noche), pre-registro, verificador con contexto limpio, placebo | `docs/MISSION.md:81-131`, programa por sensor §2 | material listo | nada |
| 6 Resultados por sensor | VIIRS 375, VIIRS 750, MODIS: recall de protegidas, errores bajo 1 MW, negativos limpios, razón de magnitud por cenit; las tres implementaciones en VIIRS 750 | evaluadores de K y del port | VIIRS 750 en buena parte; MODIS y VIIRS 375 no | V750-B (2026-11-03), V375-B/C, MOD-B/C/D, decisión de ventana |
| 7 Lo que la descripción publicada no determina | tabla paper / código / nuestra por pieza, con efecto medido donde lo hay | `docs/MIROVA_DIVERGENCES.md`, `docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md` | material listo; necesita depurarse (cada D tiene marcas encima) | nada |
| 8 Caso: Nevados de Chillán 2026 | la erupción vista por los dos sistemas | evaluadores de Chillán (programa §1, magnitud) | no | V375-F y paquete V750 |
| 9 Discusión | límites (MODIS subpíxel, cenit, geolocalización, Suomi NPP), lo que una agencia necesita para reproducir un producto, recomendaciones a los productores (publicar la ROI por volcán, el remuestreo) | catálogo + programa §10 | no | resultados de §6 |
| 10 Conclusiones | | | no | |
| Disponibilidad de código y datos | versión etiquetada con DOI (Zenodo), perfiles, scripts de números, referencia congelada por hash | `docs/paper/README.md` | no | limpieza de N-16; licencia del port del código de MIROVA (MIT exige conservar el aviso) |
| Declaración de IA, CRediT, financiamiento, conflictos | | §3 de este informe | no | decisión D6 |

### 2.4 Figuras y tablas

| | qué muestra | dato |
|---|---|---|
| Fig. 1 | mapa: 45 volcanes, 11 en serie continua, ROI de MIROVA y nuestra | `volcanoes.yaml`, KML de MIROVA |
| Fig. 2 | la cadena, con cada pieza coloreada por fuente (paper, código, OSF, decisión propia) | catálogo de divergencias |
| Fig. 3 | línea de tiempo de la referencia y del detector: tramos A119, #535, K, TIF congelados desde el 22-sep, cese de Suomi NPP | `scripts/calidad_referencia_mirova.py`, programa §2 |
| Fig. 4 | por sensor y tramo: protegidas perdidas, errores bajo 1 MW, negativos limpios publicados | evaluador común (programa §8, punto 3) |
| Fig. 5 | razón de magnitud contra cenit: K, port del código y MIROVA (la meta es reproducir la curva de MIROVA, no aplanarla; programa §1, punto 6) | `experiments/_s159/` |
| Fig. 6 | serie de Chillán 2026, los dos sistemas | evaluadores de Chillán |
| Tabla 1 | sensores, bandas, k por sensor calibrados contra el OSF | `numbers.json` (`tabla3`, sin cambio según S152) |
| Tabla 2 | umbrales: paper, código de VIIRS 750, producción | D34 |
| Tabla 3 | divergencias resumidas: estado y efecto medido | catálogo |
| Tabla 4 | resultados por sensor y tramo | evaluador común |

Ninguna figura se genera con IA de imágenes: todas salen de scripts del repo, con los números del pie desde el mismo
script (`docs/paper/README.md`, regla única de números).

### 2.5 Qué está listo y qué depende de trabajo en curso

| bloque | estado | qué falta y cuándo |
|---|---|---|
| §2 MIROVA publicado | casi listo | N-1 y S152 §2.1 |
| Calibración de k contra el OSF | listo (S152 5-10 y `tabla3`) | regenerar en la versión congelada |
| Evaluación (criterio, negativos limpios, regla SN, A119) | diseño listo; el evaluador común no existe todavía (programa §8, punto 3) | arreglos del instrumento, fase 0 del programa |
| VIIRS 750: K contra el port contra MIROVA | el port está validado contra Octave y los números de magnitud existen (programa §1, «Mejor candidato medido»); SIN VERIFICAR por mí | V750-B se despacha el 2026-11-03 (sellado, tag `s162-v750b-sellado`, `tasks/LOOP_OBJETIVOS.md:1119` en `loop/activo`); V750-A (adopción) después de PD1 |
| VIIRS 375 | K medido; el port no | V375-B y V375-C (lote de ~4,9 h de runner, `tasks/LOOP_OBJETIVOS.md:1169`), V375-E |
| MODIS | K medido; MxD03 CUMPLE SIN DAÑO, adopción pendiente (D35) | MOD-B, MOD-C, MOD-D |
| Remuestreo (D17) | pieza obligatoria del paquete según el programa (§1, punto 4) | fases 3 y 4 |
| Chillán 2026 | datos existen | V375-F después del paquete |
| Ventana prospectiva sin Suomi NPP | no existe | desde el 2026-11-03, semanas de datos |

**Recomendación de calendario.** Congelar una «versión de registro» (tag del pipeline + referencia congelada por hash)
y escribir sobre ella. La versión natural es la que cierre la fase 1 del programa (PD1), porque deja medidas las tres
implementaciones en VIIRS 750 y la ROI por volcán, que son el resultado central. No conviene esperar a que los tres
paquetes estén adoptados en producción: el paper es sobre la reproducción y su medición, no sobre el estado del
tablero ese día. Mientras tanto se pueden escribir §2, §3, §5 y §7, que no dependen de resultados nuevos.

---

## 3. La IA en la escritura de artículos científicos

Investigación hecha el 2026-10-26 sobre las páginas oficiales de cada política y sobre estudios con DOI resuelto en
Crossref. El detalle completo, con URL y DOI por fila, está en el anexo `docs/paper/REVISION_S163_ANEXO_IA.md`. La
política de Volcanica la leí yo mismo en su PDF; el resto lo reunió un subagente y lo revisó un verificador con contexto
limpio (§6).

### 3.1 Qué exigen las revistas

**Lo decisivo: Volcanica prohíbe el texto generado por IA.** Su política (*Volcanica Policy on Use of Artificial
Intelligence*, versión 1.2 del 2026-08-12, rotulada «Public draft», https://jvolcanica.org/docs/policies/AI-policy.pdf)
dice en §1.1 «AI usage is not permitted for the generation of text included in manuscripts», y en §3.2 que no acepta
manuscritos en que la IA generativa haya creado contenido o partes del texto. Además:

- §3.3: no se puede usar un LLM para resumir el manuscrito como base del resumen; sólo para traducir con cuidado un
  resumen escrito por los autores a un segundo idioma, declarándolo.
- §3.4: verificar cada referencia, en especial el DOI, porque la IA produce referencias alucinadas.
- §3.5: sí se permite usar IA para mejorar la legibilidad de texto **escrito por los autores** (corrección, estilo,
  revisar traducciones), sin creación autónoma de contenido y con supervisión humana.
- §4.2: todo uso de IA en la investigación, **incluido desarrollar o refinar código**, va detallado en métodos; si se
  usó para raspar datos, citar las fuentes y verificar la validez de lo raspado.
- §5.3: herramientas de IA para visualizaciones sólo si la figura deriva fielmente del dato; se declaran en métodos con
  nombre, versión y desarrollador.
- §6: prohibido todo uso de IA en la revisión por pares.
- La lista de verificación del envío pide marcar que se leyó y aceptó la política (según el subagente; no lo vi yo).

Ojo con la dirección: `volcanica.org` hoy es un dominio estacionado (según el subagente); la revista está en
https://www.jvolcanica.org/ojs/index.php/volcanica. El esqueleto de S72 tiene la dirección vieja
(`PAPER_VRP_CHILE_DRAFT_S72.md:21` y `:415`).

**Las demás**, en una tabla (detalle y URL en el anexo):

| organismo | IA como autora | uso en el texto | dónde se declara |
|---|---|---|---|
| Volcanica | no | **prohibido generar texto**; sólo pulir texto de los autores | métodos (código, datos, figuras) |
| Copernicus / EGU (NHESS, GMD) | no lo trata la página de IA | **prohibido para texto e interpretaciones**; el uso «asistivo» (gramática, legibilidad) no se declara | métodos o agradecimientos |
| Elsevier (JVGR, RSE) | no | permitido, con supervisión humana | sección propia de declaración, que se publica; código en métodos |
| Springer Nature (Bull. Volcanol.) | no | marco verde, ámbar, rojo: escribir resultados o discusión de forma independiente es rojo | declaración de IA en el manuscrito; la guía de Bull. Volcanol. pide métodos |
| AGU (JGR, GRL, ESS) | no | permitido, declarado | materiales y métodos |
| COPE (posición de 2023; versión en línea de 2024) | no | declarar | materiales y métodos |
| ICMJE (enero de 2026, sección II.A.4) | no | declarar | ayuda de redacción en agradecimientos; datos, análisis y figuras en métodos |

En todas, la responsabilidad por lo escrito, los datos y las referencias es de los autores humanos.

### 3.2 Cómo se ha usado la IA en este paper

Lo reconstruyo de los propios archivos:

- **El código** del pipeline y de los scripts de análisis se escribió con asistencia de Claude a lo largo de más de 160
  sesiones (bloques de arranque y memoria del proyecto). Volcanica lo permite, declarado en métodos (§4.2).
- **El esqueleto de S72** lo armó una sesión de Claude, con Perplexity Deep Research como fuente de la afirmación de
  ausencia (`PAPER_VRP_CHILE_DRAFT_S72.md:11`).
- **§4, §5 y §6 en prosa** los redactó un agente («borrador S135 (agente redactor + revisión)», `docs/paper/README.md`,
  tabla de archivos). Es texto generado: **bajo la política de Volcanica no se puede enviar**, aunque cada afirmación
  esté verificada.
- **Lo que se hizo bien y conviene conservar**: números por script (`scripts/paper_numbers.py`, ningún número a mano),
  comentario de fuente por párrafo, localizadores de cita verificados sobre la página renderizada (S141), revisión de
  S152 con verificador con contexto limpio.

### 3.3 Qué hacer, si te quedas con Volcanica

1. **Tú escribes el texto.** Los borradores en prosa de §4 a §6, el esqueleto de S72 y este informe pasan a ser
   material de trabajo: listas de afirmaciones con su fuente, tablas y figuras generadas por script. El texto del
   manuscrito lo redactan tú y tus coautores.
2. **La IA puede, según §3.5 y §4.2**: corregir gramática y estilo de tu texto, revisar una traducción tuya, verificar
   afirmaciones contra el repo y los PDF, regenerar números y figuras desde los scripts, preparar el `.bib` desde
   Crossref. Conviene guardar la traza de cada uso para poder declararlo con precisión.
3. **Zona gris que hay que preguntar al editor antes de escribir**: si se puede escribir en español y que la IA traduzca
   el texto completo al inglés. §3.3 sólo habla de traducir el resumen a un segundo idioma, y §3.5 de «checking
   translations». Correo a editor@jvolcanica.org con la pregunta concreta.
4. **El resumen** lo escribes tú desde cero (§3.3).
5. **La declaración en métodos** (borrador para que lo ajustes; en inglés porque va al manuscrito, y lo escribes tú):
   «The processing pipeline and the analysis scripts were developed with the assistance of Claude (Anthropic; models
   [versiones]) as a coding assistant. All code was reviewed, tested and validated by the authors [cómo]. The
   reference data were collected from the public MIROVA website by a scraper that includes an OCR step [herramienta];
   their quality per period is described in Section 3. [Si aplica: AI tools were used to proof-read text written by
   the authors.] No text, figure or interpretation in this manuscript was generated by AI.» La última frase sólo se
   puede escribir si es verdad.
6. **Si te cambias de revista** a una que permite la asistencia declarada (Elsevier, Springer Nature, AGU), los
   borradores sirven como base, pero igual hay que declarar el uso y responder por cada frase; en Springer, escribir
   resultados o discusión con IA de forma independiente queda fuera. En las revistas de suscripción publicar no cuesta,
   pero el artículo queda tras muro de pago, lo que choca con la decisión de S120.

### 3.4 Riesgos documentados en la literatura

| riesgo | estudio (DOI) | qué encontró |
|---|---|---|
| referencias inventadas | Walters y Wilder 2023, *Sci. Rep.* (10.1038/s41598-023-41032-5) | 55 % (GPT-3.5) y 18 % (GPT-4) de las citas inventadas, sobre 636; además 43 % y 24 % con errores sustantivos entre las reales |
| referencias inventadas | Chelli et al. 2024, *J. Med. Internet Res.* (10.2196/53164) | 34 de 119 referencias (28,6 %) alucinadas con GPT-4 |
| referencias inventadas, modelos de 2026 | Seifi y Seyfi 2026, *Crit. Care Explor.* (10.1097/cce.0000000000001474) | 85 de 300 referencias inventadas por completo |
| cita real que no respalda la afirmación | Wu et al. 2025, *Nat. Commun.* (10.1038/s41467-025-58551-6) | entre 50 y 90 % de las respuestas no están totalmente respaldadas por las fuentes que citan |
| afirmaciones más fuertes que la evidencia | Peters y Chin-Yee 2025, *R. Soc. Open Sci.* (10.1098/rsos.241776) | los resúmenes de LLM generalizan de más, razón de odds 4,85 frente a resúmenes humanos; Claude 3.7 Sonnet entre los modelos probados |
| números plausibles e inventados | Gao et al. 2023, *npj Digit. Med.* (10.1038/s41746-023-00819-6) | resúmenes generados con tamaños de cohorte inventados y verosímiles |
| complacencia | Chen et al. 2025, *npj Digit. Med.* (10.1038/s41746-025-02008-z); Perry et al. 2026, *J. Bone Joint Surg.* (10.2106/jbjs.25.01576) | los modelos siguen pedidos ilógicos y repiten la creencia del usuario |
| plagio involuntario | Lee et al. 2023, *Proc. ACM Web Conf.* (10.1145/3543507.3583199) | plagio literal, de paráfrasis y de ideas, que crece con el tamaño del modelo (medido sólo en GPT-2) |
| marcas léxicas | Kobak et al. 2025, *Sci. Adv.* (10.1126/sciadv.adt3813) | al menos 13,5 % de los resúmenes biomédicos de 2024 pasaron por un LLM |
| detectores poco fiables | Weber-Wulff et al. 2023, *Int. J. Educ. Integr.* (10.1007/s40979-023-00146-z); Liang et al. 2023, *Patterns* (10.1016/j.patter.2023.100779) | ningún detector pasó 80 % de exactitud; 61,3 % de falsos positivos en textos de no nativos |

Casi todos estos estudios son de medicina; no encontré mediciones equivalentes en geociencias. La lectura para este
paper: **el riesgo no es que un detector marque el texto** (los detectores fallan y penalizan a quien escribe en
segunda lengua), **es infringir una política que prohíbe el texto generado, o firmar una afirmación que no resiste la
fuente**. Los errores de §1.2 (N-2, N-9, N-10, N-12, N-13) son de los tipos de esta tabla: ausencia afirmada sin
prueba, cita atribuida al grupo equivocado, localizador inventado, conclusión más fuerte que su evidencia.

---

## 4. Lista de doble chequeo para este paper

Cada punto dice qué se verifica, cómo, y el antecedente del propio proyecto que lo justifica. «Responsable humano»
significa que lo hace una persona mirando la fuente, no un agente; un agente puede preparar el material.

### 4.1 Para todo el manuscrito

| # | qué verificar | cómo | antecedente |
|---|---|---|---|
| G1 | Ningún número escrito a mano | `grep -n -E "[0-9]" sec*.md` contra `[NUM: clave]`; todo número sale de `scripts/paper_numbers.py` en la versión congelada; la clave lleva su definición dentro | A87 («482 píxeles» que ningún campo reproduce), A90 (2.527 que eran 9.196 por backfill), regla S91 |
| G2 | Cada número con unidad, denominador, ventana, sensor, tramo A119 y régimen del detector | revisar cada `[NUM]` contra su definición en `numbers.json` | A93 (pareos contados como «alertas»), A94 (records contra noches), A104 (#535) |
| G3 | Corpus congelado | la referencia de MIROVA congelada por hash y el `git_head` del dato en el JSON; nunca regenerar sobre un corpus vivo sin decirlo | A90, S160 (439 que pasaron a 478) |
| G4 | Palabras de cierre | `grep -n -i -E "first|only|literal|faithful|irreducible|resolved|closed|always|never|all |guarantee|validated|proves"`: cada aparición con su evidencia citable, o se rebaja | A95, A111, A113; N-2, N-12, N-13 de este informe |
| G5 | Cada afirmación del texto tiene su `<!-- src: -->` y la fuente dice eso | lector humano sobre una muestra de al menos 1 de cada 5 párrafos por sección, más todos los de §6 | regla de `docs/paper/README.md`; S152 encontró 10 FALSA en tres secciones |
| G6 | Sin guiones largos ni marcas típicas de texto generado | cero guiones largos (U+2014) y medios (U+2013): `grep -c $'\u2014'` y `grep -c $'\u2013'` en bash; revisar muletillas («delve», «notably», «it is worth noting», «crucial») | regla del usuario; literatura de §3.2 |
| G7 | Coherencia entre secciones | el mismo número o la misma afirmación dice lo mismo en resumen, resultados y conclusiones | `sec5_methods.md:116` contra `:188-189` (S152, 5-23) |
| G8 | Verificador con contexto limpio de otro modelo sobre el manuscrito completo, antes de mandarlo | recibe sólo el texto y el repo, y busca caminos por los que cada afirmación podría estar mal | A93 (el verificador encontró algo propio en 4 de 4 frentes), A110 |
| G9 | Cumplimiento de la política de IA de la revista elegida, en su versión del día del envío | releer la política (la de Volcanica es un «Public draft» y puede cambiar); confirmar que ningún párrafo del manuscrito viene de un borrador generado; guardar la traza de cada uso permitido | §3.1 de este informe |
| G10 | La declaración de IA dice la verdad y está completa | contrastarla con la traza: código, raspado y OCR de la referencia, figuras, corrección de estilo, búsqueda bibliográfica | Volcanica §4.2 y §5.3 |
| G11 | Ninguna conclusión más general que lo medido | por frase de resumen y conclusiones: ¿qué volcán, qué sensor, qué ventana? | Peters y Chin-Yee 2025 (§3.4); S152 grave 3 (Láscar sola enunciada como MODIS) |
| G12 | La sección no reproduce frases de los papers fuente | comparar los párrafos de §2 contra las páginas de Coppola 2016a y Campus 2022 que resumen; el editor correrá un detector de similitud | Lee et al. 2023 (§3.4) |
| G13 | Toda premisa de proceso o de historia del proyecto (qué se envió, qué se midió, qué numeración D) contra su fuente | leer `docs/PLAN_PROCESO_VRP_CHILE_S163.md` §0 (PR #913) antes de escribir; ojo con las dos numeraciones D (`docs/DRIFTS_S17.md` y `docs/MIROVA_DIVERGENCES.md` no coinciden) | N-18, N-19; la cifra «1 a 3 %» de sobre-publicación con K es en realidad 2,5 y 3,7 % en VIIRS 375 (V1 y V2, `experiments/_s153_fk_v2/`) según ese plan |

### 4.2 Citas y bibliografía

| # | qué verificar | cómo | antecedente |
|---|---|---|---|
| C1 | La cita existe y los metadatos son los del paper | DOI resuelto en Crossref u OpenAlex; skill `citation-audit` o MCP `refchecker`; autores, año, revista, volumen, páginas | «Coppola 2015, Bull. Volcanol. 77:55» era Heap et al. (`CLAUDE.md`, Rebajada S146 punto b) |
| C2 | El paper citado dice lo que se le atribuye | **página renderizada a imagen** (PyMuPDF `get_pixmap(dpi=200)`), nunca la capa de texto ni el `.txt` | A95 (la capa de texto da `,20.93` por `< -0.93`), A76 (un «5 %» que no está en el paper citado), A12 (frase condicional citada como regla) |
| C3 | El grupo de autores es el que se dice | lista canónica: MIROVA = Torino, Firenze, Sapienza; INGV Catania y CNR-IMAA Potenza no son MIROVA | A9 (Di Bella), N-9 (HOTSAT) |
| C4 | El localizador es una página, sección, figura o ecuación del paper, no una línea de un archivo nuestro | buscar `§[0-9]{3}` y `L[0-9]{3,}` en el texto | N-10 («§687»), A12 («L1129») |
| C5 | No hay cita de segunda mano | si la idea viene de una nota del Vault o de un resumen, se lee el original | A35 (Wooster 57,6 W era un ejemplo de figura, no un umbral) |
| C6 | La lectura del paper es una sola o se declaran las dos | casos con ambigüedad conocida: conectiva min o max de los Tests 2 y 3; figura 11 contra su pie | S152 4-1 y 4-3, D26 |
| C7 | Paper contra código, explícito | cuando el código de MIROVA y el paper difieren, el texto dice cuál se siguió y por qué | D34 (10 de 13 puntos) |
| C8 | Afirmaciones de ausencia | «nadie ha publicado X» necesita búsqueda reproducible (consulta, base, fecha) y se escribe como «no encontramos» | N-2 (la ausencia «verificada» con Perplexity era falsa) |

### 4.3 Por sección

**§1 Introducción**: C1 a C4 en cada cita; G4 en la frase de aporte; ninguna afirmación de prioridad sin C8.

**§2 MIROVA publicado**
- Cada umbral y fórmula contra la página renderizada (C2), con la Tabla 1 de Coppola 2016a como eje (N-11).
- Separar en el texto: paper, base OSF, código de VIIRS 750, observación del sitio web (con fecha de observación,
  porque el banner cambia; S152 4-3, 4-9).
- La supervisión manual: es de la base v.1, no del OSF v2.5 (A105) ni del NRT.

**§3 Datos y referencia**
- Los tramos de calidad salen de `scripts/calidad_referencia_mirova.py`, no de memoria (A119).
- La definición de alerta es una sola (`scripts/clase_mirova.py`), con la salvedad de que cuenta las protegidas sobre
  la unión aunque se le pida un canal (marca S160 en `docs/MISSION.md:100-101`).
- **Uso de los datos de mirovaweb.it**: el paper publica y redistribuye datos raspados del sitio de MIROVA. SIN
  VERIFICAR qué permiten sus términos; preguntarlo en el correo a Coppola antes de enviar (D-datos en §5).

**§4 Implementación**
- Cada flag que el texto menciona, leído desde `pipeline.profile` en el commit congelado, no desde el YAML (A89).
- Lo que se describe como «corre» corre de verdad en producción ese día (N-3, N-4; S152 5-6, 5-14).
- Cada pieza con su fuente (paper, código, OSF, propia), igual que la Fig. 2.

**§5 Diseño de la evaluación**
- Los umbrales de prueba salen de los datos de MIROVA, no se eligen (A115).
- Cada control con su nulo medido (A110) y cada «cero» con la prueba de que el instrumento puede dar distinto de cero
  (A116).
- Declarar lo que el evaluador no etiqueta (A118: 50 publicaciones apagadas en noches con alerta por otra pasada).

**§6 Resultados**
- Por tramo de régimen: antes y después de #535, antes y después de K, antes y después de Suomi NPP (A104).
- Estratificado por volcán, no sólo por sensor (lección S126: una mediana agrupada invirtió un veredicto).
- Cobertura de cada brazo contra la referencia antes del veredicto (A108; hueco del 12-oct con una protegida de
  8,44 MW, programa §1, punto 7).
- Ninguna métrica saturada por otra palanca (A114).
- Un dato contra un producto derivado del mismo gránulo no es independiente (A109).

**§7 Divergencias**
- Cada D con su estado de hoy: el título de varias D en el catálogo contradice su marca más reciente (D11, D21, D30,
  D17). Leer la última marca, no el encabezado (A113).
- Ningún cierre del catálogo pasa al paper sin su evidencia citable (A111: 50 de 89 cierres no citaban respaldo).

**§8 Caso Chillán**: magnitudes contra MIROVA pareadas por pasada, con cenit; los TIF de MIROVA están congelados
desde el 2026-09-22, así que no sirven como imagen de la erupción.

**§9 y §10 Discusión y conclusiones**: G4 en cada frase; nada que no esté en §6 o §7.

**Disponibilidad de código y datos**
- Limpiar del repo público las imágenes de páginas de papers sin licencia abierta y el PDF con copyright antes de citar el repo (N-16).
- El port del código de MIROVA conserva el aviso de licencia MIT.
- DOI de la versión (Zenodo) y del dato congelado.

**Declaración de IA y autoría**: §3.3.

---

## 5. Decisiones para Nicolás (con recomendación)

| | decisión | recomendación |
|---|---|---|
| D0 | revista y quién escribe el texto | quedarse con Volcanica y escribir tú el texto, con la IA preparando material, verificando y corrigiendo tu inglés (§3.3). Antes, preguntar al editor si se puede traducir con IA un texto escrito en español. Cambiar de revista sólo para poder usar los borradores no compensa: igual hay que reescribirlos (§1.2) y se pierde el acceso abierto sin costo |
| D1 | marco del paper | estudio de reproducibilidad de un producto operacional (§2.1), no «primera implementación» |
| D2 | cuándo congelar | al cierre de la fase 1 del programa (PD1), con V750-B leído; escribir mientras tanto §2, §3, §5 y §7 |
| D3 | ventana de validación (decisión (a) de S152, pendiente) | por tramos A119 y de régimen, con la ventana prospectiva sin Suomi NPP como confirmación; la ventana anterior a #535 sólo como historia |
| D4 | `paper_numbers.py` adopta unión histórica, regla SN, negativos limpios y protegidas (decisión (b) de S152) | sí, y mejor aún: que lea el evaluador común del programa (§8, punto 3) en vez de tener su propia definición |
| D5 | «más allá de MIROVA» | fuera de este paper; segundo paper cuando exista la validación contra OVDAS y SWIR |
| D6 | declaración de IA | según la política de la revista (§3.1). El borrador de S72 la pone en agradecimientos (`PAPER_VRP_CHILE_DRAFT_S72.md:357-370`); Volcanica la pide en métodos (§4.2 y §5.3). Partir del borrador de §3.3, punto 5 |
| D7 | Coppola: contacto | antes de enviar, no después: el correo está redactado desde S139 y **nunca se envió** (`docs/audit_s139/BORRADOR_CORREO_COPPOLA.md`; `docs/PLAN_PROCESO_VRP_CHILE_S163.md` §0), el programa por sensor recomienda mandarlo (§9, punto 6), y además hay que preguntar por el uso de los datos de mirovaweb.it y por la ROI por volcán |
| D8 | coautores SERNAGEOMIN / OVDAS | definirlos antes de escribir la discusión operacional |
| D9 | licencia del código y de los datos | elegirla (y confirmarla con SERNAGEOMIN) antes de enviar: sin licencia el repo no es reutilizable y no se puede llamar «abierto» (N-18). Con licencia, archivar la versión en Zenodo para el DOI |

---

## 6. Verificación de este informe

Dos verificadores con contexto limpio, de otro modelo (Sonnet), recibieron sólo las afirmaciones y una pregunta por
cada una, no el informe (protocolo de verificación en cadena). Sus informes y las listas que recibieron están en
`experiments/_s163_paper_revision/`.

- **Repo** (`VERIFICADOR_REPO.md`, 20 afirmaciones): 16 CONFIRMADO, 3 CONFIRMADO EN PARTE, 1 REFUTADO en el número. Apliqué
  todas las correcciones: el alcance de #910 (cubre 2 de las 69 filas de S152 y no fue una aplicación de ese informe),
  la fecha del código de MIROVA (julio de 2026; `CITATION.txt` dice 2026-07-23), la línea exacta de «§687», que SP426.5
  no tiene Tabla 2 (lo renderizó), y el conteo de páginas de papers en el repo público (78, no las 71 que yo había
  contado con un filtro por nombre). Agregó además que `docs/paper/README.md:24` declara vigente el esqueleto S72.
- **IA** (`VERIFICADOR_IA.md`, 16 afirmaciones): 14 CONFIRMADO, 2 CONFIRMADO EN PARTE, ninguno refutado. Correcciones
  aplicadas: la posición de COPE es de 2023 pero la versión en línea es de 2024; lo de agradecimientos y métodos de
  ICMJE está en su sección II.A.4, no en la página de IA. La página de AGU dio 403 en vivo y se leyó en Wayback
  (2026-09-22).

- **Agregado después de los verificadores** (aviso de la sesión de retrospectiva del proceso, PR #913): N-18, N-19, G13
  y D9, y que el correo a Coppola nunca se envió. N-18 y N-19 los comprobé yo (sin `LICENSE` en `origin/main` y
  `licenseInfo` vacío; `experiments/21_results.json:57`, `:67-69` y `:81`); el «2,5 y 3,7 %» de G13 lo cito de ese plan
  sin medirlo. No pasaron por un verificador con contexto limpio.

## 7. Lo que este informe no verificó

- La página de Coppola et al. 2026 que D34 cita para la fecha y la licencia del código (no la rendericé; el verificador
  vio la licencia MIT y la fecha en la copia del repo).
- Los números del programa por sensor que §2.5 menciona (port contra Octave, magnitud del oráculo): los cito por su
  documento, no los medí.
- La licencia de cada una de las 78 páginas renderizadas: el verificador la clasificó por paper, no página por página.
- Los términos de uso de mirovaweb.it.
