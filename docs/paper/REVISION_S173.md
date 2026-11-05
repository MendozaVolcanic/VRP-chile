# Revisión del manuscrito VRP Chile para Volcanica (S173, 2026-11-05)

Pedido de Nicolás: ¿qué estructura debería seguir el paper, qué tiene, qué le falta, qué mejorar?

**Qué es este documento.** Un informe de revisión, de sólo lectura: no toca el manuscrito. Se apoya en las dos
revisiones previas y **no las repite**: la de S152 (`experiments/_s152_paper_revision/INFORME_CAMBIOS_PAPER_v2.md`, 69
filas) y la de S163 (PR #912, rama `s163-paper-revision`, `docs/paper/REVISION_S163.md`, 458 líneas, con su anexo de IA).
Agrega lo que pasó después del 2026-10-26: la vía «código MIROVA» en producción para MODIS (#934, 2026-11-02), el
hallazgo del cenit (S173), la ROI B4 de VIIRS 750 (#939), el cese de Suomi NPP, la sombra por sensor, y una corrida
nueva de `scripts/paper_numbers.py`. También verifica por mi cuenta la política de IA y las guías de autor de Volcanica.

**Método.** Skill `academic-paper-reviewer`, en modo de evaluación rápida (perspectiva del editor jefe) con foco en el
método (revisor metodológico) y una sección de abogado del diablo. **Aviso**: la skill está pensada para cinco revisores
independientes en paralelo; aquí las perspectivas las escribí yo en una sola sesión, así que no son independientes entre
sí. Para un juicio no anclado en éste, conviene un verificador con contexto limpio (regla G8 de S163).

**Rutas.** Las relativas cuelgan de `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\`. Los números de
línea valen para `origin/main` en `84d3a4581` (2026-11-05 03:43 UTC), leídos en el worktree
`C:\Users\nmend\vrp-wt\paper-rev\`, salvo que diga `loop/activo` (`95dc85854`) o `s163-paper-revision`.

**Marcas.** VERIFICADO (lo leí o lo corrí en esta sesión), SIN VERIFICAR, OPINIÓN DEL REVISOR. FALSA, DESACTUALIZADA,
FALTA, como en S163.

---

## 0. Respuesta corta a las cuatro preguntas

1. **Estructura.** Volcanica no impone secciones para un *research article*; sí exige, en la lista de envío, resumen de
   hasta 150 palabras, **resumen no técnico** (~150 palabras), **declaración de disponibilidad de datos**, **lista de
   contribuciones de autores**, conflictos de interés y DOI en todas las referencias (VERIFICADO, §1). La estructura
   que recomiendo es la de S163 (estudio de reproducibilidad de un producto operacional, por sensor), con tres ajustes:
   el resumen no técnico, una sección de régimen del detector y de la referencia, y el cenit como eje de la magnitud (§2).
2. **Qué tiene.** Tres secciones en prosa de septiembre (§4 Background, §5 Methods, §6 Validation), un esqueleto de
   mayo y julio, un script de números que corre sin red en 9 s, localizadores de cita verificados sobre la página
   renderizada, y un material de evidencia enorme en el repo (catálogo de divergencias, pre-registros, verificadores).
3. **Qué le falta.** Todo lo que no es §4 a §6, y la propia prosa de §4 a §6 **no se puede enviar a Volcanica**: la
   política prohíbe texto generado por IA y esas secciones las redactó un agente (VERIFICADO, §1.2). Además §5 y §6
   describen y validan un detector que ya no corre en ningún sensor (§3).
4. **Qué mejorar y en qué orden.** Primero decisiones (quién escribe, marco, licencia, Coppola), después limpiar el repo
   público y arreglar el instrumento de números, después escribir las secciones que no dependen de resultados, y cerrar
   resultados recién cuando la sombra de VIIRS 375 y la lectura de V750-B estén hechas (~diciembre de 2026) (§6).

---

## 1. Normas de Volcanica (VERIFICADO el 2026-11-05)

### 1.1 Guías de autor

Leídas con WebFetch en https://www.jvolcanica.org/ojs/index.php/volcanica/about/submissions (resumen de la herramienta,
no del texto completo; las frases entre comillas son las que devolvió):

| tema | lo que piden | estado en el manuscrito |
|---|---|---|
| tipo de artículo | *Research article* («can be any length»), *Report* (observatorios y agencias), *Communication of Methods* (formato corto: métodos, análisis, códigos y datos abiertos), *Review* | sin decidir; ver §2.1 |
| resumen | «do not exceed 150 words (each)» | el esqueleto apunta a ~250 palabras (`docs/PAPER_VRP_CHILE_DRAFT_S72.md:49`): FALTA ajustarlo |
| resumen no técnico | uno o dos párrafos, ~150 palabras, está en la lista de envío | FALTA, no aparece en ningún archivo |
| disponibilidad de datos | declaración obligatoria en el manuscrito; repositorio abierto, Zenodo o FigShare; código versionado y archivado (GitHub más Zenodo) | FALTA; el repo no tiene licencia (VERIFICADO: no hay `LICENSE*` en la raíz de `84d3a4581`) |
| contribuciones | «A list of author contributions must be included» (CRediT no se nombra) | FALTA; coautores sin definir |
| conflictos | el autor de correspondencia declara por todos | FALTA |
| referencias | DOI en todas las que lo tengan; nada «in prep» o «submitted» salvo que sea verificable | hay referencias con DOI pendiente (`docs/paper/sec4_background.md:159-161`) y no hay `.bib` |
| figuras | 85 mm (una columna) o 175 mm (dos), alto máximo 200 mm | FALTA, ninguna figura |
| preprints | aceptados y alentados | oportunidad (OPINIÓN: un preprint en EarthArXiv antes del envío protege la prioridad mientras se cierra la sombra) |

### 1.2 Política de IA

El navegador interno no la pudo abrir: el servidor responde con descarga de archivo, **y el intento le mostró a Nicolás
un diálogo de guardar** (no reintenté). La leí con WebFetch, que guardó el PDF, y extraje su texto con PyMuPDF
(5 páginas). Es la *Volcanica Policy on Use of Artificial Intelligence (AI), Version 1.2*, del 2026-08-12, rotulada
«Public draft» en su historial de revisiones (p. 1). Lo que decide:

- ¶ 1.1: «AI usage is not permitted for the generation of text included in manuscripts.»
- ¶ 3.2: no acepta manuscritos en que la IA generativa haya creado contenido o partes del texto.
- ¶ 3.3: el resumen y el resumen no técnico no pueden salir de un resumen hecho por IA; la IA sólo puede traducir, con
  cuidado, un resumen escrito por los autores a un segundo idioma, revisado por un hablante fluido y declarado.
- ¶ 3.4: verificar cada referencia, en especial el DOI.
- ¶ 3.5: se permite usar IA para mejorar legibilidad e idioma de **texto escrito por los autores** (corrección,
  edición, revisar traducciones), sin creación autónoma de contenido.
- ¶ 4.2: todo uso de IA en la investigación, **incluido desarrollar o refinar código**, va detallado en métodos; si se
  usó para raspar datos, citar las fuentes y verificar la validez de lo raspado.
- ¶ 5.3: herramientas de IA para visualizaciones sólo si la figura deriva fielmente del dato; se declaran en métodos con
  nombre, versión y desarrollador.

Coincide con lo que S163 leyó (`REVISION_S163.md` §3.1 en la rama `s163-paper-revision`, l. 225-240). Dos consecuencias
que S163 no subrayó:

1. **¶ 4.2 alcanza a la referencia misma.** La verdad de terreno de §6 sale del scraper Mirova-v1 con un paso de OCR. Si
   ese scraper o su OCR se escribió o ajustó con IA, hay que declararlo y mostrar cómo se verificó lo raspado; el
   proyecto ya tiene esa verificación (`docs/audit_s139/MAPA_BASES_MIROVA_V1.md`, A119), y eso pasa de ser nota interna
   a ser parte obligatoria de métodos (OPINIÓN).
2. **¶ 3.3 favorece a Nicolás.** El resumen en español lo puede escribir él directamente, sin traducción por IA, y el
   inglés lo escribe él con corrección de estilo permitida por ¶ 3.5. Sigue en pie la pregunta de S163 al editor: si se
   puede escribir todo en español y traducir con IA (¶ 3.5 dice «checking translations», no «translating»).

**Este informe y los de S152 y S163 son material de trabajo**, no texto del manuscrito.

---

## 2. Estructura recomendada

### 2.1 Tipo de artículo y marco (OPINIÓN DEL REVISOR)

Coincido con S163 (`REVISION_S163.md` l. 122-148): la premisa «primera implementación abierta» es falsa desde que
MIROVA publicó su código de VIIRS 750 en OSF (`docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md:9-15`, VERIFICADO), y el marco
que resiste es **un estudio de reproducibilidad de un producto operacional, medido contra su propia salida en las dos
direcciones y por sensor**. Lo que cambió desde S163 refuerza ese marco:

- Ya hay **tres implementaciones comparables** en producción o sombra: K (fiel a la prosa del paper) en VIIRS, la vía
  «código MIROVA» en MODIS (`pipeline/profiles/mirova_equivalent.yaml:38`, `enable_modis_codigo_mirova: true`;
  `docs/MISSION.md:7-21`), y la misma vía en sombra para VIIRS (`.github/workflows/sombra-codigo-mirova.yml`, cron
  `0 15 * * *`).
- **El cenit es un resultado físico nuevo y publicable**: la razón de K contra MIROVA cae con el ángulo cenital del
  sensor en los tres sensores, y la vía la lleva cerca de 1 en los dos tramos (`experiments/_s173_cenit/README.md:13-17`
  y `:62-69` en `loop/activo`; MODIS: K 0,678 bajo 30° y 0,137 sobre 30°, vía 0,947 y 1,054, n 10 y 17). Es la clase de
  mecanismo (remuestreo a grilla fija, geolocalización, fondo de anillo) que una agencia necesita saber para reproducir
  cualquier producto MIR, y no está en ningún paper de MIROVA.

**Tipo**: *Research article*. Un *Communication of Methods* (corto) calza con «el port del código y su validación», pero
dejaría fuera la evaluación en dos direcciones, que es lo más reutilizable. Si el material excede (probable), una
salida es dividir: un *Research article* de reproducibilidad y, después, el «más allá de MIROVA» aparte (S163 D5).

### 2.2 Secciones, contra lo que existe

| § | sección | contenido | existe | estado |
|---|---|---|---|---|
| 0 | Título, resúmenes (inglés y español, 150 palabras c/u), resumen no técnico | la pregunta de reproducibilidad, sin «first» | esqueleto (`PAPER_VRP_CHILE_DRAFT_S72.md:37-88`) | **OBSOLETA** (premisa N-2, números S119) y **FALTA** el resumen no técnico |
| 1 | Introducción | monitoreo térmico, MIROVA como referencia operacional, por qué reproducir un producto, la pregunta | esqueleto (`:89-132`) | **OBSOLETA** en su motivación (N-2 de S163); prosa **FALTA** |
| 2 | MIROVA como está publicado | papers, base OSF v2.5, código de VIIRS 750, salida NRT; qué fija cada fuente | `sec4_background.md` | **casi vigente**; corregir l. 142-145 y agregar el código (§3.1) |
| 3 | Datos y referencia | L1B, sensores, 11 Tier A; la referencia NRT (tabla y OCR) y su calidad por tramo (A119); negativos limpios, protegidas, regla SN; cese de Suomi NPP | dispersa en `MISSION.md:100-151`, `docs/S151_CRITERIO_CLASE_MIROVA.md`, `scripts/calidad_referencia_mirova.py` | **FALTA** como sección; `sec6_validation.md:22-34` dice lo contrario (§3.3) |
| 4 | Implementación | la cadena; qué pieza sale de qué fuente (paper, código, OSF, propia); K en VIIRS; vía en MODIS; coeficientes k desde el OSF | `sec5_methods.md` | **OBSOLETA** en su núcleo (§3.2); §5.4 (coeficientes) vigente |
| 5 | Diseño de la evaluación | criterio de victoria, unidades (pasada, noche), pre-registro sellado, verificador limpio, nulos medidos, corte por cenit | `MISSION.md:100-151`, programa por sensor §2 y §12.8 | material listo, prosa **FALTA** |
| 6 | Régimen del detector y de la referencia | línea de tiempo: #535 (2026-08-28), K (#850, con reproceso histórico #883), vía MODIS (#934, 2026-11-02), cese de Suomi NPP (2026-11-02), TIF congelados (2026-09-22) | marcas en `CLAUDE.md`, `MISSION.md`, A104, A119 | **FALTA**; sin ella ningún número de §7 es interpretable (OPINIÓN) |
| 7 | Resultados por sensor | recall de protegidas, errores bajo 1 MW, publicación en negativos limpios, razón de magnitud contra cenit; las tres implementaciones | evaluadores de K, MOD-D, V375-E, V750-B | VIIRS 375 y 750 **en curso** (sombra y V750-B); MODIS adoptado pero con ventana corta |
| 8 | Lo que la descripción publicada no determina | tabla paper / código / nuestra por pieza, con efecto medido | `docs/MIROVA_DIVERGENCES.md` (D1 a D35), `docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md` | material listo, hay que depurarlo (marcas sobre marcas, A113) |
| 9 | Caso Nevados de Chillán 2026 | la erupción vista por los dos sistemas, por pasada y cenit | `experiments/_s172_chillan/`, `_s173_cenit/` | datos existen; **FALTA** |
| 10 | Discusión | límites (subpíxel MODIS, cenit, geolocalización, diurno), recomendaciones a productores, uso operacional en OVDAS | | **FALTA** |
| 11 | Conclusiones | | | **FALTA** |
| A | Disponibilidad de código y datos | versión etiquetada con DOI (Zenodo), referencia congelada por hash, scripts de números | esqueleto (`:348-355`) | **FALTA**; bloqueada por licencia y limpieza (§4) |
| B | Uso de IA (en métodos, ¶ 4.2 y 5.3) | código, scraper y OCR, figuras, corrección de estilo | esqueleto la pone en agradecimientos (`:357-370`) | **en el lugar equivocado**; borrador útil en `REVISION_S163.md` l. 287-293 |
| C | Contribuciones, conflictos, financiamiento, agradecimientos | | | **FALTA** |
| D | Transparencia algorítmica | una frase en métodos: el sistema es un SDA bajo la Resolución CPLT N°372 y tiene ficha publicada | `sec5_methods.md:173-179` | **vigente en la idea**; el nombre exacto de la resolución SIN VERIFICAR (`sec5_methods.md:287-289`), y la ficha va en v1.18 (`docs/FICHA_SDA_VRP_CHILE.md:7`), no v1.5 |

**Figuras**: las seis de S163 (`REVISION_S163.md` l. 176-189) siguen siendo las correctas. Cambio la Fig. 5: debe ser
**razón contra cenit con los tres brazos (K, vía, MIROVA plano)** por sensor, porque es la figura que resume el hallazgo
de S173. Y agrego una Fig. 0: línea de tiempo de regímenes (§6 de la tabla).

---

## 3. Afirmaciones obsoletas por sección

S152 y S163 ya marcaron la mayoría. Aquí van **sólo** las que cambian con lo posterior al 2026-10-26, o que esas
revisiones no tomaron. Cada evidencia nueva la leí en esta sesión.

### 3.1 `docs/paper/sec4_background.md`

| línea | afirmación | evidencia nueva | clase |
|---|---|---|---|
| 142-145 | «What none of these publications provides is executable code ... no reference implementation has been released» | código MATLAB de VIIRS 750 en OSF desde el 2026-07-24, MIT (`docs/S158_CODIGO_MIROVA_VS_VRP_CHILE.md:9-15`) | FALSA (ya en S163 N-1) |
| 49-53 | promedio de «eight neighbours» | el código de VIIRS 750 promedia 3 × 3 con el píxel central (marca S158 R2 en `CLAUDE.md`, kernel 8-vecinos) | correcta para el paper, incompleta frente al código |
| 57-69 | umbrales de la Tabla 1 | el código de VIIRS 750 usa K1 = -0,7 y C1 = 0,02 fuera de la cumbre (`S158_CODIGO...:23-25`) | correcta para el paper; falta decir que el código difiere |

La sección es la más sana: describe papers, y los papers no cambiaron. Lo que le falta es una subsección «4.6 El código
operacional publicado» con la tabla de 13 puntos de S158.

### 3.2 `docs/paper/sec5_methods.md`

| línea | afirmación | evidencia nueva | clase |
|---|---|---|---|
| 7-9 | MODIS baja MOD03/MYD03 «but, as of 2026-10-26», interpola la grilla de 5 km | desde #934 la vía de MODIS usa la geolocalización de 1 km del MxD03 (`MISSION.md:10-11`; `FICHA_SDA_VRP_CHILE.md:29`, nota v1.18) | DESACTUALIZADA |
| 10-11 | banda 22 «in the record reprocessed back to 2026-09-18» | #883 reprocesó con K el histórico de los 11 Tier A desde el 2025-02-15 (marca S160 en `CLAUDE.md`, sección A) | DESACTUALIZADA |
| 58-61 | perfiles de laboratorio «never run by the cron» | `guardia_k_modis`, `sombra_codigo_mirova` y `sombra_34` corren por cron (`.github/workflows/guardia-k-modis.yml`, `sombra-codigo-mirova.yml`, `sombra-34.yml`; crons `40 17`, `0 15`, `7 13`) | FALSA |
| 67-69 | «The detector is the one described in Coppola et al. (2016a)» | MODIS corre el código de MIROVA portado (`mirova_equivalent.yaml:26-38`); VIIRS corre K, que difiere del código en 10 de 13 puntos (`S158_CODIGO...:21-25`) | FALSA para MODIS, REBAJADA para VIIRS |
| 81-84 | Tests 2 y 3 «as a conjunction that keeps the statistical OR branch» | conectiva `max` desde K (`mirova_equivalent.yaml:288-290`) | DESACTUALIZADA (S163 N-3) |
| 89-90 | «does not yet remove the Test 1 pixels» | en VIIRS el Test 1 integrado está apagado (`:287`); en MODIS el código de MIROVA sí los retira (familia 1 de `S158_CODIGO...:21-23`) | DESACTUALIZADA |
| 97-99 | Test 1 integrado en 3 km como camino de detección | `enable_test1_path: false` (`mirova_equivalent.yaml:287`) | DESACTUALIZADA (S163 N-4) |
| 118-124 | «VRP Chile does not resample» | la vía de MODIS remuestrea a la grilla de 1 km (`FICHA_SDA_VRP_CHILE.md:25`, nota v1.18); el remuestreo es justo la pieza que corrige la caída con el cenit en MODIS (`_s173_cenit/README.md:75-79`, `loop/activo`) | FALSA para MODIS |
| 162 | `[NUM: n_tests_collected]` | la clave sólo existe corriendo con `--tests`; no la generé | placeholder |
| 177 | «sixteen pipeline modules carry a machine-readable header» | un grep laxo de «FICHA» en `pipeline/*.py` da 20 archivos; conteo exacto SIN VERIFICAR | DESACTUALIZADA probable |
| 195-197 | D19 «active and unresolved» | con K el `keep_peak` del Test 1 no actúa (marcas S157 y S160 de A100 en `CLAUDE.md`) | DESACTUALIZADA |
| 186-205 | lista de divergencias abiertas | faltan D34 (código publicado), D35 (MxD03), D30 (Test 1 apagado), y la ROI de VIIRS 750 (#939, B4 en `roi_v750`) | FALTA |

**Veredicto**: §5 describe el detector de agosto (banda 21, Test 1 integrado, `min`) parchado en un párrafo (#910). Hoy
no describe ningún sensor de producción. Hay que reescribirla entera, y además decidir **qué versión** describe (§6).

### 3.3 `docs/paper/sec6_validation.md`

| línea | afirmación | evidencia nueva | clase |
|---|---|---|---|
| 26-29 y 134-159 | «the reference carries no negative labels», por eso no se reporta precisión (§6.5 entera) | el criterio de victoria mide **publicación en negativos limpios** (pasadas donde MIROVA miró y no vio nada) como métrica central (`MISSION.md:134-136`, punto 3), y la ficha informa esos números: MODIS de 12,3 a 0,8 % y de 10,8 a 0,9 % con K (`FICHA_SDA_VRP_CHILE.md:25`) | FALSA (ya en S152) |
| 22-25 | cobertura de la referencia 79,2 % | la referencia tiene calidad distinta por tramo (A119, `scripts/calidad_referencia_mirova.py`); un número único no sirve | DESACTUALIZADA |
| 82-86 | 26.028 records; VIIRS 375 0,931 (829 de 890); VIIRS 750 0,805 | ver §4: hoy 35.744 records y otros valores, con mezcla de detectores | DESACTUALIZADA |
| 90-99 | MODIS «labelling failure»: dashboard 0,122 contra cráter 0,976; «no per-record answer at that resolution» | corrida de hoy: dashboard y cráter **iguales**, 0,804 (107 noches); Láscar MODIS 0,866 en los dos; el «irreducible» de A82 está rebajado (marcas S146 y S157 en `CLAUDE.md`) | FALSA: el argumento central de la sección desapareció |
| 107-123 | sesgo de sub-integración por menos píxeles o anillo solapado | la caída de la razón es función del cenit y la causa medida es el fondo de anillo de K (más remuestreo y geolocalización en MODIS) (`_s173_cenit/README.md:13-27`, `loop/activo`; programa §12.8, `loop/activo` l. 529-534) | la mecánica cambió; la nueva es mejor resultado |
| 136-137 | Copahue VIIRS 375 «210 of 214» noches sin alerta | corrida de hoy: 0 de 2 | DESACTUALIZADA |
| 143-149 | categorías de AUDIT_S86 (mayo) | con K la sobre-publicación en negativos limpios de VIIRS 375 es 2,5 y 3,7 % (`FICHA_SDA_VRP_CHILE.md:25`) | DESACTUALIZADA |

### 3.4 ¿Sigue en pie la narrativa central?

**No.** La narrativa de septiembre tenía tres patas, y cayeron las tres:

1. «Primera implementación abierta, porque nadie publicó código»: FALSA (§3.1). Además el repo no tiene licencia, así
   que tampoco es «abierta» todavía (VERIFICADO).
2. «Clon literal de Coppola 2016a»: hoy MODIS corre el código de MIROVA, VIIRS corre K, y K difiere del código en 10 de
   13 puntos (§3.2).
3. «Medimos recall porque precisión no se puede; la brecha de MODIS es de etiquetado»: el proyecto mide desde octubre
   las dos direcciones y la brecha de MODIS se fue con K y la vía (§3.3).

Lo que **sí** queda en pie, y es mejor que lo que cayó: la reconstrucción de los coeficientes k desde el OSF
(`sec5_methods.md:105-116`, tabla 3 sin cambios en la corrida de hoy), la disciplina de números por script, la
evaluación pre-registrada en dos direcciones, y el hallazgo del cenit.

---

## 4. `scripts/paper_numbers.py`, corrida de hoy

**Corre sin red** (VERIFICADO). Desde el worktree, con salida a una carpeta temporal para no tocar `docs/paper/`:
`python scripts/paper_numbers.py --out <scratchpad>/pn`, 9 s, HEAD `84d3a4581`, aviso «pyhdf not found» sin efecto.
Ventana de records 2026-01-01 a 2026-11-05; comparación contra MIROVA recortada a 2026-11-04. Sin `--tests`.

| clave | `numbers.json` commiteado (2026-09-07, `83b9df8ff`) | hoy |
|---|---|---|
| `n_records_tier_a_ventana` | 26.028 (`sec6_validation.md:82`) | 35.744 |
| VIIRS 375: noches alerta, recall | 890; 0,931 / 0,931 | 1.133; 0,958 / 0,958; en banda 9 de 11 |
| VIIRS 750 | 246; 0,805 / 0,805 | 307; 0,759 / 0,759; en banda 5 de 9 |
| MODIS | 82; 0,122 (tablero) / 0,976 (cráter) | 107; 0,804 / 0,804; en banda 2 de 3 |
| Láscar MODIS | 77 noches; 0,117 / 0,974; 9 pares | 82 noches; 0,866 / 0,866; 83 pares, razón 0,50 |
| Tupungatito VIIRS 375, razón | 0,645 | 0,348 |

**Qué claves ya no reflejan el detector vigente.** Ninguna de `tabla4` ni de `agregados` refleja un solo detector, por
cuatro razones (VERIFICADO en el código del script salvo donde digo):

1. **MODIS mezcla K y la vía**: la ventana cruza la primera corrida de la vía (2026-11-02), que además reescribe los 8
   días previos (`MISSION.md:7-11`). El script no separa por `regimen` ni por detector (no aparece ninguna de esas
   palabras en el script).
2. **No implementa el criterio de victoria**: un grep de `RUTINA`, `limpi`, `protegid`, `aplicar_regla` y
   `calidad_referencia` en el script da cero. No hay negativos limpios, ni protegidas, ni regla SN, ni tramos A119.
3. **Su «tablero» no es el tablero**: el predicado es una reconstrucción (cráter más `summit`), sin la regla de cirrus
   del frontend (`t_max` bajo 273,15 K y más de 10 MW oculta el record; programa §12.8 punto 3a, `loop/activo`). El
   grep de `t_max` y `cirrus` en el script da cero. A97 pide el predicado del operador ejecutado.
4. **La ventana cruza #535 y el cese de Suomi NPP** (A104), y el script no corta por cenit (§12.8 punto 2).

`tabla3` (coeficientes k contra el OSF) sigue igual y vigente para K; si la vía de MODIS usa el mismo k es SIN
VERIFICAR. `tabla2` cambió en conteos y fechas de inicio (el histórico está reprocesado; marca S160 V4-02 en
`CLAUDE.md`, Arquitectura).

**Recomendación (S163 D4, reforzada)**: que el paper lea los números del evaluador común del programa por sensor, no
de un predicado propio. Si se mantiene el script, agregarle como mínimo: corte por régimen, criterio de victoria
importando `scripts/clase_mirova.py`, tramos de `scripts/calidad_referencia_mirova.py`, y corte por cenit.

---

## 5. Lo que falta

| ítem | estado | nota |
|---|---|---|
| Introducción, casos, discusión, conclusiones | FALTA | el esqueleto S72 sirve como lista de temas, no como texto (S163 N-2, N-9 a N-19) |
| Resumen (150 palabras), resumen en español, resumen no técnico | FALTA | los tres los escribe Nicolás (¶ 3.3) |
| Figuras | FALTA, 0 de ~7 | todas desde scripts del repo; ninguna con IA de imágenes |
| `.bib` con DOI | FALTA | metadatos pendientes en `sec4_background.md:159-161` (Coppola 2020 y 2023); Coppola 2026 está «in press» con DOI, aceptable |
| Disponibilidad de datos y código | FALTA | requisitos previos: licencia (no hay), limpieza de 88 PNG de páginas de papers en `experiments/_s146_auditoria/` (33), `_s149_audit/` (7), `_s150_audit/` (2), `_s158_audit/` (25), `_s158_audit_r2/` (21), y del PDF `documentacion/steffke_harris_2011_...pdf`, todo todavía en `main` (VERIFICADO); términos de uso de los datos de mirovaweb.it SIN VERIFICAR; el port del código MIT conserva su aviso |
| Declaración de IA | FALTA, en lugar equivocado | va en métodos (¶ 4.2, 5.3), incluye scraper y OCR |
| Coautores y contribuciones | FALTA | decidir antes de la discusión operacional (S163 D8); el contacto con Coppola sigue sin hacerse (el borrador existe: `docs/audit_s139/BORRADOR_CORREO_COPPOLA.md`) |
| Transparencia CPLT | parcial | una frase en métodos más la ficha como material suplementario; verificar el nombre legal de la resolución |
| Sección de régimen | FALTA | ver §2.2, fila 6 |

---

## 6. Recomendación: cómo seguir y en qué orden (OPINIÓN DEL REVISOR)

**¿Esperar la sombra antes de cerrar resultados?** Sí para los resultados, no para la escritura. Por qué: hoy cada
sensor está en un régimen distinto y dos de ellos van a cambiar. MODIS cambió de detector hace tres días (#934); VIIRS
375 tiene la sombra de V375-E llenándose desde el 2026-11-03 con parada estimada el 2026-12-02, rango hasta el 12-09
(programa §12.8, `loop/activo` l. 524-526); VIIRS 750 espera la lectura de V750-B, que es el camino crítico (l. 527-528).
Escribir resultados ahora es escribir §6 una tercera vez. Pero §2, §3, §5 y §8 de la tabla del §2.2 no dependen de
ningún resultado nuevo.

Orden:

1. **Decisiones de Nicolás, esta semana** (bloquean todo lo demás): quién escribe (con Volcanica, él); marco
   (reproducibilidad); licencia del repo y su confirmación con SERNAGEOMIN; coautores; si se contacta a Coppola antes
   de enviar (recomiendo sí, S163 D7). Correo corto al editor con la pregunta de la traducción.
2. **Limpieza del repo público** (en paralelo, A38 con tag defensivo): sacar los 88 PNG de páginas y el PDF con
   copyright; agregar `LICENSE`.
3. **Arreglar el instrumento de números** (§4) antes de que haya un solo `[NUM:]` nuevo.
4. **Escribir, Nicolás**, en este orden: §2 MIROVA publicado (más el código), §3 datos y referencia, §5 diseño de la
   evaluación, §6 régimen, §8 lo que la descripción no determina. Con la IA permitida por ¶ 3.5: corregir su inglés,
   verificar cada afirmación contra el repo y la página renderizada, regenerar números y figuras. Guardar la traza.
5. **Congelar la versión de registro** cuando estén leídas la sombra de V375-E y V750-B (estimado: mediados de diciembre
   de 2026), con tag del pipeline y referencia congelada por hash. Ventana de resultados: por tramo de régimen, con la
   ventana posterior al 2026-11-02 (sin Suomi NPP, con la vía de MODIS) como confirmación prospectiva. MODIS necesita
   al menos el mismo número de noches que la sombra de los otros (OPINIÓN: unas 28).
6. **Escribir §4 implementación, §7 resultados y §9 Chillán** sobre esa versión; después discusión, conclusiones y
   resúmenes (los resúmenes al final, ¶ 3.3).
7. **Verificador con contexto limpio de otro modelo** sobre el manuscrito completo, la lista G1 a G13 y C1 a C8 de S163
   (`REVISION_S163.md` l. 322-409), y preprint.

---

## 7. Lectura del revisor

**Editor jefe (OPINIÓN).** El tema calza con Volcanica: un observatorio que reconstruye un producto operacional y mide
cuánto se le parece es útil para toda la comunidad que depende de MIROVA, y la revista publica métodos y reportes de
observatorios. La novedad ya no está en «existe un clon», sino en (a) la evaluación en dos direcciones con negativos
limpios, (b) las tres implementaciones del mismo algoritmo sobre las mismas pasadas y (c) la dependencia de la magnitud
con el cenit. Riesgo de rechazo de escritorio hoy: alto, por la política de IA y por la premisa falsa.

**Revisor de método (OPINIÓN, con anclas VERIFICADAS arriba).** Las debilidades son de instrumento, no de idea: el
script de números no mide el criterio que el propio proyecto adoptó (§4); los resultados mezclan regímenes; la
referencia se arma con un OCR propio cuya calidad varía por tramo; y varios cierres del catálogo cuelgan de auditorías
rebajadas después (A113). La fortaleza es rara en este tipo de papers: pre-registro sellado, verificador limpio y
nulos medidos. Eso hay que mostrarlo, no esconderlo en el repo.

**Abogado del diablo (OPINIÓN), el argumento más fuerte en contra.** «Los autores validan su réplica contra una
referencia que ellos mismos rasparon con OCR, cuyo tramo útil depende de fechas que ellos eligieron, y cambiaron el
detector varias veces mientras miraban esa misma referencia. Sin datos de terreno, el acuerdo con MIROVA sólo prueba que
se parecen a MIROVA, no que detecten actividad volcánica.» Respuesta posible: (1) el objetivo declarado es reproducir
MIROVA, no superarla, así que la referencia es el objeto y no un proxy; (2) cada cambio pasó por una regla escrita antes
de ver el resultado (`experiments/_s151_prereg_fk_11/REGLA_ADOPCION.md`, citada en `MISSION.md`); (3) la confirmación
prospectiva posterior al 2026-11-02 es fuera de muestra. Si esas tres cosas no están en el texto, el revisor real lo va
a escribir.

---

## 8. Los cinco problemas más importantes

1. **La prosa existente no se puede enviar**: Volcanica prohíbe texto generado (¶ 1.1, 3.2) y §4 a §6 los redactó un
   agente (`docs/paper/README.md:25-27`).
2. **La narrativa central cayó en sus tres patas** (§3.4): no es la primera implementación, no es un clon del paper, y
   la tesis de «sólo recall» se invirtió.
3. **§5 y §6 describen y validan un detector que no corre en ningún sensor** (§3.2, §3.3).
4. **El instrumento de números no mide el criterio de victoria ni separa regímenes**, y su «tablero» no es el tablero
   (§4).
5. **Bloqueos de publicación fuera del texto**: sin licencia, 88 imágenes de páginas de papers y un PDF con copyright en
   el repo público, términos de uso de mirovaweb.it sin consultar, coautores sin definir.

---

## 9. Lo que este informe no verificó

- El texto completo de las guías de autor: leí el resumen que devolvió WebFetch, no la página entera.
- El nombre legal exacto de la resolución del CPLT, y el conteo exacto de cabeceras FICHA.
- Si la vía de MODIS usa el mismo coeficiente k que K.
- Los números de S173 sobre el cenit: los cito de su README, que dice tener verificador limpio; no los re-corrí.
- Los términos de uso de mirovaweb.it.
- Que el correo a Coppola siga sin enviarse: lo dice el plan de S163 (PR #913, §0); no hay evidencia posterior en lo
  que leí.
- No corrí `--tests` (la clave `n_tests_collected`), por costo.
