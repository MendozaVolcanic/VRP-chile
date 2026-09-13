# AUDIT_S138: las afirmaciones de cierre, la fidelidad paso a paso y los instrumentos de S137

> Auditoría integral del proyecto (regla A51). Corrida el 2026-09-13 entre las 11:41 y las 12:40 UTC
> (hora del servidor) sobre `main` en `6b1dd91ef`, con la suite en 1325 passed. Plan:
> `docs/PLAN_AUDITORIA_S138.md`. Seis auditores en paralelo (Fable 5.1, read-only, un archivo cada uno
> en `docs/audit_s138/`) y un verificador con contexto limpio (Opus, `docs/audit_s138/VERIFICADOR.md`).
> Preámbulo canónico `docs/_prompts/PREAMBULO-AUDITOR.md` pegado entero en los siete prompts. Scripts y
> salidas crudas en `experiments/_s138_audit/eje<n>/` y `.../verificador/`. Ningún auditor tocó
> `pipeline/`, perfiles, `data/` ni git; ninguno disparó CI. Quien orquesta verificó por su cuenta los
> hallazgos críticos de cada eje antes de aceptarlos (A48) y el verificador no recibió esos veredictos.

## Resumen ejecutivo (para quien sólo lee esto)

**El veredicto de la regla de salida: seis contradicciones entre fuentes confirmadas, más de tres.
El frente D21/D22 se pausa y se consolida antes de cualquier A/B.** Cinco de las seis son la misma
enfermedad, la de A95: un cierre ("fiel", "agotado", "no reabrir", "clon literal") que hereda una
lectura del paper hoy refutada. Un A/B lanzado hoy heredaría de esos cierres qué brazos no correr.

Lo que la auditoría encontró, en orden de lo que más pesa:

1. **La palanca que borra cúmulos reales del cráter es el fondo del anillo, no la compuerta de
   temperatura (D22).** En una cumbre helada el cráter con lava sub-píxel está más frío que la mediana
   de un anillo de 5 a 25 km lleno de valle tibio; su exceso de radiancia sale negativo y se recorta a
   0,0 MW. El paper mide contra los vecinos del píxel. La compuerta rechaza en el primer pase, pero el
   segundo pase (que corre sin activos y sin compuerta, D19/D2) rescata el píxel: 14 % de los records
   VIIRS375 y 17 % de los VIIRS750 se detectan sólo ahí. Villarrica A6 lo demuestra sin reprocesar: con
   compuerta el cúmulo ya está a 0,8 km del cráter y publica 0,0 MW; quitarla no mueve ese cero;
   cambiar el fondo da 0,539 MW. **Un brazo que quite sólo la compuerta no devuelve ninguna alerta.**
   S137 atribuyó la pérdida al paso equivocado (H-S138-01 y 02).
2. **Pero en la unidad del operador casi no hay pérdida de recall.** Las 33 noches-sensor de alerta
   que VIIRS750 pierde con el cráter en 0,0 MW están cubiertas las 33 por otra pasada del mismo
   volcán esa noche; MODIS pierde 2 de 67 noches reales y VIIRS375 1 de 6. El mecanismo es un problema
   de fidelidad y de magnitud, no de alerta perdida. Priorizarlo por el conteo por sensor sería A94
   otra vez.
3. **La batería del Apéndice A no mide lo que se le hace decir.** No mira la posición del objeto
   (de los 6 "conformes" de producción, 0 verificables y 2 son otro objeto), mezcla pasadas de dos
   noches locales, y usa un predicado que no es el del dashboard: con el del operador, producción da
   2 de 6 y 2 de 3, no 6 de 6 y 0 de 3. Cambia de veredicto con el radio. El 5/6 y 3/3 del mejor brazo
   de S137 sí corresponde al objeto del autor por posición en los cinco, y encuentra A2 fuera de la
   caja de 5 km (H-S138-03).
4. **Las afirmaciones de cierre envejecieron.** De 76 revisadas contra el PDF y el código: 52 vigentes,
   11 condicionadas, 5 falsas, 8 no verificables. `CLAUDE.md` sigue diciendo "GAP #A mislabel, NO
   reabrir" cuando el catálogo lo reabrió en S128 y hay un guard que lo mide; el encabezado de D11
   dice "detección fiel, todos los ejes agotados" en el mismo archivo donde D21 y D22 están abiertas.
5. **La matriz de conformidad construida desde el PDF** (la que debió existir en S114) deja 8
   divergencias literales sin número en el catálogo. Las que pesan: el Test 1 del paper no es camino
   de detección en producción (el primer pase pisa la máscara combinada), el píxel saturado se elimina
   cuando el paper lo conserva, y el día no existe.
6. **Operación:** la cadencia del NRT sigue en 43 % desde el 30 de agosto (73 de 168 corridas en 14
   días, 0 rojas, sin pérdida de records, latencia de ~5 h) y un job puede terminar verde sin
   descargar nada cuando el cortacircuitos de LANCE (A64) declara caído al host al primer timeout:
   Planchón-Peteroa perdió la noche del 13 mientras Villarrica y Láscar bajaban los mismos granules.
7. **Un descubrimiento de instrumento que cambia una regla:** leer el PDF con PyMuPDF **no** cura la
   corrupción de operadores que A95 atribuye sólo al `.txt` (la capa de texto da `,20.93` donde el papel
   dice `< -0.93`). Sólo renderizar la página cura. La fórmula de los Tests 2 y 3 se renderizó y
   coincide con lo que los ejes leyeron.

**Cuentas del verificador**: de los 25 hallazgos de gravedad 3 o más de los seis ejes, 18 confirmados,
6 corregidos, 1 refutado en su consecuencia. Lista fundida sin duplicados: 16 (H-S138-01 a 16).
Ocho hallazgos propios del verificador, dos de ellos de gravedad 4.

## Cómo se corrió (decisiones de infraestructura, 2026-09-13)

- Arranque con `/retomar` verificado contra el remoto y el código: todo lo que el traspaso S137
  afirmaba se sostuvo (suite, NRT, ramas integradas por contenido, archivos citados).
- Nicolás aprobó la decisión 6 del bloque S138 ("la auditoría y luego todo lo que puedas hacer en
  paralelo"). Las decisiones 1 a 5 siguen esperando; el eje 6 las reúne en una sola tabla. El espacio
  en disco quedó fuera de alcance por decisión suya.
- Desvíos del plan detectados antes de lanzar y corregidos en los prompts: `conformidad_apendice.py`
  vive en `experiments/_s136/`, no en `_s137/`; el preámbulo dirige los scripts a
  `experiments/_s134_audit/` y trae 7 guiones largos (se redirigió a `_s138_audit/` y se prohibió el
  guión en las salidas); PyMuPDF en Windows exige `PYTHONIOENCODING=utf-8`.
- Sin worktrees (los agentes no escriben en git). Dos con red, `gh` sólo en lectura.
- Modelos: Fable 5.1 para los seis censos (effort alto), Opus para el verificador. Costo: 17 a 25 min
  y 260 k a 485 k tokens por eje; 22 min y 409 k el verificador.
- El eje 3 recibió sólo títulos de afirmaciones, rutas y scripts (no los documentos de resultados de
  S137); el verificador recibió sólo los seis archivos y sus scripts. Dos de los tres agentes que
  corrieron scripts ajenos tuvieron que restaurar con `git checkout` un archivo trackeado que el script
  ensucia al correr (`experiments/_s133/auditar_guards_por_subcadena.json`); es el hallazgo P7.

## 1. Eje 1: las afirmaciones de cierre contra el paper y el código de hoy

`docs/audit_s138/EJE_1_afirmaciones_de_cierre.md`. Universo: 76 afirmaciones falsables (18 reglas
científicas, 23 reglas A con contenido verificable, 17 encabezados D, 18 ítems "cerrado, no rehacer"
de los bloques S134 a S138). **52 vigentes (68 %), 11 condicionadas (15 %), 5 falsas (7 %), 8 no
verificables (11 %).** Tres de las cinco falsas no llevan marca.

Lo que cambia decisiones (verificado por quien orquesta y por el verificador):
- `CLAUDE.md:119` "GAP #A = mislabel, NO reabrir" es falso: el paper (p. 6) descarta como no aptos los
  píxeles del Test 1 para los pasos siguientes; el código no los retira
  (`ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK = False`, `test1_mask=None` en los tres procesadores); el
  catálogo lo reabrió en S128 con guard. Efecto nulo hoy por falta de sustrato; la frase apaga el
  frente si un volcán entra en fase efusiva.
- El encabezado de D11 ("CERRADA S114, detección fiel, todos los ejes agotados") y A82, A83, A84, el
  camino de D12 y el "no adoptar B22" de S134 heredan la configuración que S137 puso en duda (banda 21,
  compuerta). No se declaran falsos: se declara que no se sabe.
- A66/A67 llaman "clon literal" al área nadir fija; el paper remuestrea (bow tie y grilla de 1 km) y
  S130 midió que el ratio contra MIROVA cae 2,7 veces con el ángulo aun con nadir fijo. Es D17.
- A92 "el barrido de guards por subcadena da 0" envejeció: hoy da 1, el guard de la conectiva de S136
  (`tests/test_conectiva_tests23_s136.py:204`, `assert "min(" in src`, satisfecho por `min_bg_pixels`).

Confirmado sano: Tabla 1 contra flags efectivos, Wooster, Stefan-Boltzmann, kernel aritmético,
conectiva por defecto = fórmula, D21 y D22 vivas en los tres sensores, ancla al cráter con su test,
gates intra-radio y máscara de nube apagados, `"on":` en los 26 workflows, marcas OBSOLETA/FALSA de
A7, A12, A13, A17, A23, A36, A42, A69.

## 2. Eje 2: la matriz de conformidad construida desde el PDF

`docs/audit_s138/EJE_2_matriz_conformidad_pdf.md`. 24 pasos del paper listados desde el PDF antes de
abrir ningún documento del proyecto. MODIS: 8 conformes, 4 conformes con adición, 10 divergentes, 3
ausentes. VIIRS375 y VIIRS750: 8 / 3 / 6 / 2 (más 6 sin equivalente literal: el paper es de MODIS).
**Divergencias literales sin D# en el catálogo: 8 de 18**: saturado eliminado (paper lo conserva),
bow tie ausente como paso, el Test 1 K1 no es camino de detección (`process_modis.py:888`
`hot_mask_2d = fp_hot` pisa el `combine_hot_paths` de la l. 824; igual en los otros dos sensores), el
día no existe, segundo pase sin filtros de no-aptos, refit iterativo 3 sigma en la regresión, fondo =
mediana del anillo 5 a 25 km en vez de media de vecinos (vigente en 6 de 11 MODIS, 11 de 11 M-band y
todo el camino Test 1), `delta_L` recortado a 0.

Su hallazgo principal (H1, gravedad 4) es el que corrige la atribución de D22 (ver resumen, punto 1).
Control sintético M1: primer pase 0, segundo pase 1. También midió que el número que ve el operador
no es la suma de la escena del paper en 87,8 % de los records MODIS, 16,8 % V375 y 18,2 % V750.
VERIFICADO LIMPIO con 17 ítems y comando cada uno.

## 3. Eje 3: verificador limpio de los instrumentos de S137

`docs/audit_s138/EJE_3_verificador_instrumentos_s137.md`. Las seis afirmaciones centrales de S137:
(a) sigma del dNTI del autor ~0,0008: **confirmada** (A6 sobre el PNG nativo del PDF: 0,00079; el
instrumento lee 5 a 12 % bajo; los nuestros en la misma pasada 0,00764 con B21 y 0,00157 con B22);
(b) caída 3,5 a 4,7 veces con B22 y 80 de 84 escenas vacías: **confirmada en número, corregida en
enunciado** (el "primer paso" cuenta Tests 2 y 3 más la compuerta); (c) 6/6 y 0/3 hoy, 5/6 y 3/3 el
mejor brazo: **confirmada bajo el predicado de la batería, corregida bajo el del dashboard** (2/6 y
2/3; 19 de 22 pasadas "publicadas" llevan `far`); (d) A2 a 9,6 km rumbo 83: **confirmada en
sustancia**, el número está escrito a mano en `conformidad_apendice.py:230`; (e) el 0,0 MW de A6 por
anillo y recorte a cero: **confirmada** por código (`process_modis.py:1023`, 1041, 1056); (f) el
remuestreo sube el sigma 13 a 15 %: **confirmada en número, sospecha en atribución** (es nuestro regrid
por vecino más cercano con huecos, `regrid.py:123`, no "el remuestreo").

Controles corridos: comparador con 9/9 y 0/9 sintéticos, `evaluar_caso` con cúmulos a 4 y 6 km,
medidor de figuras con panel uniforme (0), ruido RGB (0,0037), escala espejada (la delata la mediana),
signo (no la delata: H8). Instrumentos 1 a 3 no re-corridos (HDF4 sin pyhdf en Windows).

## 4. Eje 4: D21, D22 y el fondo en VIIRS, medidos sobre los datos

`docs/audit_s138/EJE_4_d21_d22_viirs.md`. Ventana MIROVA 2026-01-11 a 2026-09-07, 11 Tier A, loader
CONS unión OCR con el filtro diurno del pipeline. Por noche-sensor: VIIRS750 pierde 33 de 246 noches
ALERTA con un cúmulo del cráter en 0,0 MW (Tupungatito 8/14, Isluga 11/40, PP 4/9, Láscar 8/136); en
31 de 33 el mecanismo es compuerta, rescate por segundo pase y fondo del anillo. Ejemplo verificado
por quien orquesta en el JSON de producción: Tupungatito 2026-08-21 05:30 UTC `VIIRS_SNPP_750`, cúmulo
de 1 píxel, clase `summit`, 0,0 MW, fondo 256,4 K; las tres pasadas VIIRS375 de esa noche publican
0,06 a 0,16 MW. En VIIRS375 la compuerta ya está neutralizada en detección (9 a 26 % de los records
visibles vienen sólo del segundo pase); costo actual 6 de 896 noches, todas por la pata de magnitud de
`keep_peak` (D19). MODIS: 76 de 77 noches ALERTA son de Láscar y en 59 el cúmulo está en el cráter con
rótulo `far` (A46/A81). No hay diagnóstico persistido de "pasó Tests 2 y 3 y cayó sólo por la
compuerta"; el probe por etapa para VIIRS quedó escrito y **no disparado**
(`experiments/_s138_audit/eje4/probe_compuerta_viirs.py`, `pasadas_eje4.json`, yml).

**Corregido por el verificador (P1 y discrepancias d y e)**: en noches de volcán las 33 están
cubiertas por otro sensor (pérdida real para el operador: 0 en VIIRS750, 2 de 67 en MODIS, 1 de 6 en
VIIRS375); y la partición focal/nevado que usó no existe en el repo (inventa "intermedio", mueve PCC):
con la lista de S131 (`scripts/build_c2ab_windows.py:41-42`) su enunciado numérico cambia de signo,
gobernado por PCC solo. La conclusión de fondo ("lo predice cráter frío contra anillo tibio, no el
régimen") queda reforzada. Su recomendación de incluir VIIRS desde el inicio en el A/B de D22 y del
fondo se mantiene; MODIS sólo aporta a D21.

## 5. Eje 5: la batería del Apéndice A como instrumento

`docs/audit_s138/EJE_5_bateria_apendice_instrumento.md`. Posición de la máscara del autor medida en
las nueve figuras con controles (sintético de posición, escala invertida, negativos reales). En
producción (6/6): 0 conformes verificables como el objeto del autor, 2 con certeza otro objeto (A1: el
autor marca 2 celdas a 0,4 km de la cumbre y nosotros publicamos 42 píxeles con el tope D9 de 5,0 MW a
4,2 km; A2: el autor a ~10 km al E, nosotros a 3,1 km al SE). En el mejor brazo de S137 los 5
conformes son el objeto del autor por posición y A2 también se encuentra, pero fuera de la caja de 5
km. Fragilidad: producción cae a 4/6 con radio 3 km; el mejor brazo pasa a "cumple" con radio 8 km o
con la referencia en el autor. **Holdout**: en jun-ago 2026 MIROVA publicó alertas MODIS sólo en
Láscar (15 noches) y ninguna en nevados; 316 noches confirmadas por cualquier sensor (312 VIIRS375,
64 en nevados). Pre-registro del A/B Tier A escrito en su §4 (5 brazos, unidad noche por volcán,
pérdida cero decisoria, C2 con bootstrap pareado por noche, C3 posición en unidades del inner_radius,
predicciones P1 a P4 y qué refutaría el pre-registro entero). **Queda en espera** por la regla de
salida; se retoma después de la consolidación y con la corrección del verificador: la evaluación de
A2 y la partición de régimen quedan fijadas ahí.

Discrepancia (a) resuelta por el verificador: A2 a **10,1 km rumbo 84** (escala de los rótulos del
eje sobre el raster embebido; horquilla 9,8 a 11,0 entre instrumentos). Nada sustantivo cambia; cae
el post hoc de 3 km.

## 6. Eje 6: decisiones, operación e higiene

`docs/audit_s138/EJE_6_decisiones_operacion_higiene.md`.

### 6.1 Tabla única de decisiones

Denominador: 25 entradas en AUDIT_S134 §D y los bloques S135 a S138. **EJECUTADAS 5** (D1 y D2 en su
parte experimental, D5, S136-2, S138-6), **SUPERADAS 4** (D4, D8, S136-1, S136-5), **ABIERTAS 16, de
las cuales 12 son preguntas distintas** (D1/D2 adopción = S136-1 = S138-4; D4 = S138-5; D8 = S137-2).
Tabla completa con evidencia por fila en el eje 6 §1. Es la única tabla que hereda el bloque S139;
cada reformulación futura marca la anterior como superada. D3 (A/B con C2') y D6 (área por píxel) no
corrieron nunca. Para S138-1 no existe flag de la compuerta y `ENABLE_TEST1_LOCAL_BG_NTI` es de S105,
no el fondo local uniforme de S137.

### 6.2 Operación

- **Cadencia del NRT**: 73 de 168 corridas esperadas en 14 días (43 %), 0 rojas, 49 huecos mayores a
  4 h, hueco típico 4,7 a 5,9 h. Es el régimen que S133 midió en 40 %; no se recuperó. No se pierden
  records (los 11 Tier A con datos los 14 días); se degrada la latencia. Ningún monitor mide cadencia.
  Los otros crons muestran lo mismo (`sync-mirova-csv` 26 %, `nrt-healthcheck` arranca 2 a 4,8 h
  tarde).
- **Job verde sin descargar nada**: en el run de las 08:57 el cortacircuitos de A64 declaró caído a
  LANCE en el job de PlanchonPeteroa al primer ConnectTimeout y saltó las 6 plataformas VIIRS mientras
  Villarrica y Láscar bajaban los mismos granule IDs en el mismo run. PP es el único Tier A sin la
  noche del 13 (último commit remoto del JSON 2026-09-12 20:43 UTC, verificado). `nrt-retry` sólo
  relanza fallos.
- **Sano**: sitio publicado al día, filtros iguales en las 3 vistas, `inner_radius_km` 11/11 idéntico
  entre YAML y vistas, `sync-mirova-csv` 60/60 verdes con CSV al 2026-09-13, indicador D5 lee
  `data/mirova/<V>.json` regenerado. Salvedad del verificador (P5): `isValidDetection` (`vrp_mw > 0`
  o `triggered_test1`) y `mirovaEqVrp` (`primary_cluster.vrp_mw`) discrepan de forma sistemática: un
  record con el cúmulo en 0,0 MW y Test 1 disparado cuenta como detección summit en los contadores y
  se grafica en cero (195 en Tupungatito V750, 121 en Láscar, 68 en PP, 19 en Isluga). Familia A46.

### 6.3 Higiene

196 ramas remotas: 188 borrables (109 con PR mergeado, 28 idénticas a main, 51 sin cambios propios);
no borrar las 4 con trabajo real sin PR (`claude/s79-f66-hybrid-bg-gate` con ~330 líneas de pipeline y
120 de tests, dos `claude/s126-*-tif`) ni `s124-brazoC` (PR #528 cerrado a propósito). 4 stashes de
mayo, dos con JSON operacionales, sobre ramas que ya no existen; uno ya se reaplicó solo en S137.
`.git` 7,8 GB con 1,15 GiB de objetos sueltos. 15 workflows de experimentos en la carpeta viva. Lista
de limpieza propuesta en el eje 6 §3.4; requiere tag defensivo `pre-s138-git-cleanup` más archivo de
shas (A38) y confirmación. No ejecutada.

## 7. Verificación cruzada (contexto limpio; el que verifica no es el que encontró)

`docs/audit_s138/VERIFICADOR.md`. Re-corrió los scripts que operan sobre archivos en disco, reescribió
el predicado del operador desde `frontend/index.html:1043-1064` sin mirar el script del eje 3 (coincide
dígito a dígito, incluido el "19 de 22"), renderizó la fórmula de los Tests 2 y 3 del PDF (coincide con
lo leído), y recalculó la tabla de margen del eje 4 con la partición de S131 (el signo se invierte).

| id | qué es | lo reportan | grav. |
|---|---|---|---|
| H-S138-01 | El fondo del anillo con el recorte a cero borra del dashboard cúmulos reales del cráter | ejes 2, 3, 4 | 4 |
| H-S138-02 | El segundo pase corre sin activos y sin compuerta, y es el que detecta (D19/D2); anula D22 en detección | ejes 1, 2, 4 | 4 |
| H-S138-03 | La batería del Apéndice A no mide lo que se le hace decir | ejes 3, 5 | 4 |
| H-S138-04 | El Test 1 K1 del paper no es camino de detección ni retira del pool | ejes 1, 2 | 3 |
| H-S138-05 | Afirmaciones de cierre apoyadas en una lectura del paper hoy refutada | ejes 1, 6 | 3 |
| H-S138-06 | Sin remuestreo ni bow tie, área fija sobre píxeles que no la miden (D17) | ejes 1, 2 | 3 |
| H-S138-07 | La etiqueta `far` del píxel más caliente esconde el cúmulo del cráter (9.422 records MODIS, 78 %) | ejes 2, 3, 4 | 3 |
| H-S138-08 | El número que ve el operador no es la suma de la escena del paper | eje 2 | 3 |
| H-S138-09 | Los píxeles saturados de MODIS se eliminan; el paper los conserva | eje 2 | 3 |
| H-S138-10 | Cadencia del NRT al 43 % desde el 30 de agosto, sin monitor | eje 6 | 3 |
| H-S138-11 | Un job del NRT termina verde sin descargar nada (cortacircuitos al primer timeout) | eje 6 | 3 |
| H-S138-12 | El holdout MODIS de jun-ago 2026 no tiene estrato nevado | eje 5 | 3 |
| H-S138-13 | El guard de la conectiva pasa por subcadena | eje 1 | 2 |
| H-S138-14 | El día no existe: Tabla 1 diurna escrita y nunca corre | eje 2 | 2 |
| H-S138-15 | ROI1 círculo per-volcán de 3 a 20 km, no la caja de 5 km del paper (D18) | eje 2 | 2 |
| H-S138-16 | CLAUDE.md dice grilla 51x51; el texto del paper dice 50x50 (imprecisión con fuente: las figuras son de 51 celdas) | eje 1 | 1 |

Hallazgos propios del verificador: P1 unidad equivocada (gravedad 4, al revés: baja la prioridad de
H-01 como recall); P2 PyMuPDF no cura los operadores (sólo renderizar); P3 partición del eje 4; P4
atribución de A6; P5 dos predicados de detección en el frontend; P6 los paneles del apéndice no son
isótropos en píxeles; P7 un script de auditoría ensucia un archivo trackeado; P8 el tope D9 es
verificable en el JSON.

## 8. Regla de salida (A51): contradicciones entre fuentes

| # | enunciado que gobierna | la fuente que lo desmiente |
|---|---|---|
| C1 | `CLAUDE.md:119`: GAP #A "RESUELTO S115 = MISLABEL, NO reabrir" | `docs/MIROVA_DIVERGENCES.md:1319-1340` "REABIERTO S128, las dos patas son FALSAS" + guard `tests/test_guard_gap_a_pool_musigma_s128.py` + `ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK = False` |
| C2 | `docs/MIROVA_DIVERGENCES.md:1259`, encabezado D11: "CERRADA S114, detección fiel a Coppola, todos los ejes agotados" | D21 y D22 abiertas en el mismo archivo; PDF p. 7 renderizado: la fórmula de los Tests 2 y 3 no tiene condición de temperatura y `detection_context.py:532` la impone |
| C3 | `CLAUDE.md` A82: far a summit MODIS "irreducible, todos los ejes agotados" | Los ejes se barrieron con `ENABLE_MODIS_B22_PRIMARY=False` y `NTI_BT_SANITY_K=3.0`; rebajada en S124 por geometría, no por la vía espectral |
| C4 | `CLAUDE.md` A92: el barrido de guards "tras endurecerlos da 0" | Corrido hoy: da 1 (`tests/test_conectiva_tests23_s136.py:204`) |
| C5 | `tasks/BLOQUE_ARRANQUE_S137.md:141`, "Cerrado, no rehacer": la intersección contextual "sigue curando" | El mismo archivo `:121-123`: "n insuficiente, formalmente sigue indeterminado" |
| C6 | `CLAUDE.md` A66 y A67: área nadir fija = "clon literal" para los 3 sensores | PDF p. 3 "cropped and resampled (into an equally spaced 1 km grid)" y `ENABLE_UTM_REGRID = False`; D17 abierta |

**Seis, más de tres: se pausa el frente y se consolida.** Lo que la consolidación toca, en orden: el
encabezado de D11 (C2), la frase del GAP #A en `CLAUDE.md` (C1), la rebaja espectral de A82 (C3), el
punto 5 del bloque S137 (C5), la palabra "clon literal" de A66 y A67 (C6) y el guard de la conectiva
(C4, una línea). Además, por P2, A95 pasa a decir "renderizar la página", no "PyMuPDF".

## 9. Cierre por guard (regla B)

| hallazgo | guard que lo mide o razón de que no se pueda |
|---|---|
| C1 GAP #A | ya existe `tests/test_guard_gap_a_pool_musigma_s128.py`; la consolidación sólo corrige la frase |
| C4 guard por subcadena | endurecer el assert con frontera de palabra (A92) y volver a correr `experiments/_s133/auditar_guards_por_subcadena.py` |
| H-S138-05 cierres heredados | no hay guard posible sobre prosa; la defensa es A95 más la tabla única de decisiones |
| H-S138-03 batería | el instrumento corregido del eje 5 §3 (predicado del operador, pasada del autor, posición) es el guard; se implementa cuando se retome el frente |
| H-S138-10 cadencia | monitor de cadencia (`nrt-healthcheck` puede contar corridas de las últimas 24 h) |
| H-S138-11 job verde sin descarga | test sobre `pipeline/fetch.py` que un ConnectTimeout en un host no salte todas las plataformas sin un reintento; toca `pipeline/`, A45 |
| P5 dos predicados de detección | guard G8 del frontend ampliado a `isValidDetection` contra `mirovaEqVrp` |
| P7 script que ensucia un archivo trackeado | el script escribe su JSON al scratchpad o el archivo sale de git |

## M. Pruebas de campo para Nicolás (qué mirar en el dashboard, qué decide)

1. **Tupungatito, noche 2026-08-21 UTC**: en el gráfico VIIRS750 esa noche está en cero y en VIIRS375
   en 0,06 a 0,16 MW summit. Decide si el operador percibe la pérdida por sensor como pérdida.
2. **Villarrica, 2009-06-24 05:55 (figura A6 del paper)**: el brazo B22 sin compuerta publica 0,0 MW y
   con fondo local 0,539 MW. Decide si el fondo de vecinos es la corrección que quieres en el A/B.
3. **Contadores contra gráfico** en Tupungatito y Láscar (últimos 7 días): el contador de detecciones
   summit sube con records que el gráfico muestra en cero (P5). Decide si `isValidDetection` debe
   alinearse con `mirovaEqVrp`.
4. **Planchón-Peteroa**: la tarjeta no tiene datos de la noche del 13 mientras los vecinos sí. Decide
   la prioridad del arreglo del cortacircuitos (A45).

## D. Tabla de decisiones del dueño (opciones y recomendación; no se tomaron)

| # | pregunta | opciones | recomendación |
|---|---|---|---|
| S138-A | Consolidar las seis contradicciones (docs, `CLAUDE.md`, bloque S137, guard C4) antes de cualquier A/B | (a) sí, en un PR de docs más el guard; (b) no | **(a)**: es lo que A51 manda y cinco de las seis son texto |
| S138-B | Con la atribución corregida (el fondo, no la compuerta), ¿la decisión 1 del bloque S138 se reformula? | (a) flags apagados para el fondo de vecinos y el segundo pase condicionado, no para la compuerta sola; (b) mantener la formulación de S137 | **(a)**: un brazo que quite sólo la compuerta no devuelve ninguna alerta |
| S138-C | El A/B de D22 y del fondo, ¿en los 3 sensores o MODIS primero? | (a) los 3 (D21 sólo MODIS); (b) MODIS primero | **(a)**: el mecanismo vive en VIIRS y el holdout MODIS no tiene nevados |
| S138-D | Unidad de recall del A/B | (a) noche de volcán, cualquier sensor; (b) noche-sensor | **(a)** (A94, P1); C4 de magnitud se reporta aparte |
| S138-E | Cortacircuitos de A64: ¿reintento por plataforma antes de declarar caído al host? | (a) sí, con tag A45; (b) dejar | **(a)**, es un job verde que no produce |
| S138-F | Limpieza de git (188 ramas, 4 stashes, gc) | (a) con tag `pre-s138-git-cleanup` e inventario; (b) dejar | **(a)**, en sesión aparte |
| S138-G | Partición focal/nevado oficial | (a) la de S131 en `scripts/build_c2ab_windows.py`; (b) otra | **(a)** y borrar las otras tres o marcarlas históricas |

Las 12 decisiones distintas abiertas de S134 a S138 siguen en la tabla del eje 6 §1.

## Seguimientos (no se arreglan en S138)

- El probe por etapa de VIIRS para medir el costo directo de la compuerta (eje 4) queda escrito y sin
  disparar; sólo tiene sentido después de la consolidación y si la decisión S138-B lo pide.
- D17 (remuestreo) sigue siendo la divergencia geométrica de fondo detrás de H-01, H-06 y H-16.
- Las 8 divergencias literales sin D# del eje 2 se numeran en el catálogo durante la consolidación.
- `regrid.py:123` (vecino más cercano con huecos) explica el +13 a 15 % del sigma; no es "el
  remuestreo" de MIROVA.
