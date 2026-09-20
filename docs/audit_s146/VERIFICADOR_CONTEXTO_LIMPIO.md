# Verificador con contexto limpio, auditoría S146

Fecha: 2026-09-20. Rol: intentar romper cada afirmación de los cinco auditores y de los dos agentes de trabajo nuevo, yendo primero a la fuente primaria y midiendo por un camino propio. Todos los scripts propios están en `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s146_auditoria\verificador\`. Cada número de este informe sale de una salida de herramienta de esta sesión, pegada junto al veredicto. No se modificó ningún archivo existente.

Carga propia: `vlib.py` lee los 11 JSON de `data/mirova_equivalent/` sin pasar por `dlib.py` ni `_s126_lib.py` de los auditores, y lee la referencia cruda (`latest_consolidado.csv` más `mirova_v1_snapshot/registro_vrp_ocr.csv`) con `csv`, sin el loader del proyecto. Control de carga:

```
total 60037 cache MB 97.3
ref filas 39369 Counter({('cons', 'RUTINA'): 36028, ('cons', 'ALERTA_TERMICA'): 1497, ('cons', 'FALSO_POSITIVO'): 878, ('ocr', 'ALERTA_TERMICA_OCR'): 875, ('ocr', 'FALSO_POSITIVO_OCR'): 91})
ref min/max 2026-01-10 19:06:00 2026-09-20 02:45:00
```

## Cobertura y tabla de veredictos

Completada por el segundo tramo. **17 de 17 ítems verificados.** Los ítems 1 a 9, 13, 14 y 15 son del primer verificador (se cortó por un fallo técnico después de V-04); los ítems 10, 11, 12, 16 y 17 son del segundo, otra instancia con contexto limpio. La tabla de veredictos del primer tramo se armó leyendo lo que ese verificador dejó escrito; no se re-verificó su contenido.

Qué NO se cubrió, en ningún tramo: los informes de los frentes A, C y E más allá de los ítems listados; ningún gránulo satelital (no se descarga ni se usan credenciales); la cita textual del boletín del GVP del ítem 16 (el sitio responde 403); el script `01_formula_osf.py` de S139 que sostiene "la fórmula está bien" en el ítem 12; y el predicado completo del dashboard en el ítem 10 (se usó `distance_class == summit`).

| ítem | qué | veredicto | gravedad |
|---|---|---|---|
| 1 | D9: 207 de 214 confirmados, 0 fuga | CONFIRMADO CON MATIZ (denominadores sí, numerador no) | 4 |
| 2 | MODIS encuentra el cráter 90 %, sin tasa base | CONFIRMADO | 4 |
| 3 | AUC 0,859 de A83 | CONFIRMADO CON MATIZ (paradoja de Simpson) | 3 |
| 4 | D16 "la grilla no explica", NO REABRIR | CONFIRMADO CON MATIZ | 4 |
| 5 | NEW-8 figura abierta y corre en producción | CONFIRMADO | 2 |
| 6 | Test 1 integrado y su cita Coppola 2015 | CONFIRMADO, más fuerte que el auditor | 5 |
| 7 | "Caso Gaua, p. 17" | CONFIRMADO CON MATIZ | 2 |
| 8 | N·σ 5 / 10 de BT atribuido a la Tabla 1 | CONFIRMADO | 4 |
| 9 | 76 noches de FN recuperadas (D12) | CONFIRMADO CON MATIZ (76 exacto NO VERIFICABLE) | 3 |
| 10 | 1,5 % corroborado de D13 | CONFIRMADO CON MATIZ | 3 |
| 11 | D20 banda 31 "despreciable" | CONFIRMADO CON MATIZ | 2 |
| 12 | 0,995 a igual conteo (A99) | CONFIRMADO CON MATIZ | 3 |
| 13 | MISSION sin rebajas, D-PCC inner = 7 | CONFIRMADO CON MATIZ | 3 |
| 14 | control vacío del censo S145 | CONFIRMADO CON MATIZ | 2 |
| 15 | hueco del corpus | CONFIRMADO CON MATIZ | 2 |
| 16 | A2 con la vara corregida: 9 de 9 y producción 5 de 9 | CONFIRMADO CON MATIZ (cita GVP NO VERIFICABLE) | 2 |
| 17 | `pc.classification` como post-proceso; OCR no sincronizado | CONFIRMADO CON MATIZ; lateral CONFIRMADA | 2 |

Ningún ítem salió REFUTADO. Eso no es tranquilizador por sí solo: 13 de 17 llevan matiz, y en dos (ítems 1 y 10) el matiz va en contra de la conclusión del auditor, no del cierre auditado. Las secciones "Hallazgos propios" y "Verificado limpio" del segundo tramo están al final.

## Detalle por ítem (en el orden en que se verificó)

### V-05 (ítem 5). NEW-8 figura como gap abierto pero el filtro corre en producción

Caminos por los que podía estar mal: (a) el flag en True pero ningún procesador lo consume; (b) lo consume sólo uno de los tres; (c) la rama que lo consume está detrás de otro flag apagado; (d) el flag se lee de otra sección del YAML (A89).

Qué hice: leí el flag por `pipeline.profile`, tracé el consumo con grep sobre el identificador y sobre el parámetro `apply_unsuitable_filters`, y revisé los flags que encierran las dos ramas.

```
ENABLE_UNSUITABLE_FILTERS_267_273 True
pipeline/process_modis.py:696/704:  apply_unsuitable_filters=ENABLE_UNSUITABLE_FILTERS_267_273   (path D contextual)
pipeline/process_modis.py:866-867:  _unsuit_dnti/_unsuit_deti = -0.1 if ENABLE_UNSUITABLE_FILTERS_267_273 else -np.inf  (first pass Tests 2 y 3)
pipeline/process_viirs.py:1071/1079 y 1272-1273: idem
pipeline/process_viirs_mod.py:705/713 y 854-855: idem
pipeline/profile.py:131  _p = _cfg["paths"]
pipeline/profile.py:676  ENABLE_UNSUITABLE_FILTERS_267_273 = bool(_p.get("enable_unsuitable_filters_267_273", True))
ENABLE_DNTI_CONTEXTUAL_PATH True / ENABLE_FIRST_PASS_TESTS_2_AND_3 True / ENABLE_DNTI_DUAL_ROI True
ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK False
```

La clave no está escrita en `mirova_equivalent.yaml` (grep da 0 ahí), así que vale el default True de `profile.py`, puesto en el commit `d58f7a46f` (S72 F2.3.a). Los tres procesadores lo consumen en las dos ramas (path D contextual y primer paso de los Tests 2 y 3) y las dos ramas están encendidas. El filtro de borde va siempre activo dentro de `build_unsuitable_mask`.

Veredicto: **CONFIRMADO**. `docs/MISSION.md:112` ("NEW-8 gaps 2-4 (pool estadístico m,σ)" como abierta) y `docs/MIROVA_DIVERGENCES.md:435` y `:478` ("siguen vigentes", "sigue siendo un gap de fidelidad literal") describen como pendiente algo que corre en los tres sensores desde S72. Matiz: el cuarto elemento del mismo párrafo del paper (retirar los píxeles del Test 1 del pool) sigue apagado, y ese es el GAP #A, que sí está abierto. Gravedad 2: no apaga trabajo, lo inventa (alguien podría correr el A/B F2.1 que el catálogo todavía propone, contra un control que ya tiene el filtro).

### V-14 (ítem 14). El control del censo S145 es vacío

Fuente: `experiments/_s145_censo_cierres/censo.py:106-114`.

```
if any(re.search(rx, linea) for _, rx in []):
    control.append(rel)
instrumento_ok = len(control) == 0 and len(filas) > 0
>>> python -c "print(any(x for x in []))"
False
```

El `any` itera sobre una lista literal vacía, así que `control` queda siempre vacío y la primera pata de `instrumento_ok` no puede fallar con ningún contenido de los documentos. Veredicto: **CONFIRMADO CON MATIZ**: la segunda pata (`len(filas) > 0`) sí puede fallar, pero sólo detecta "el censo no encontró nada", no "el censo cuenta otra cosa". Los 89 y 50 del censo no quedan refutados por esto, quedan sin control. Gravedad 2.

### V-13 (ítem 13). `docs/MISSION.md` lista resueltas sin las rebajas, y D-PCC dice inner = 7

```
docs/MISSION.md:99-103  Resueltas: D1, D4 (S27), D5, D8/D8', sec3, ancla, **D9 path-D cirrus** (... verificado S113: 0 fuga al dashboard + mediana 0.53x ...)
docs/MISSION.md:105-107 D11 ... **CERRADA S114** (irreducible a 1 km; detección fiel a Coppola verificada file:line; todos los ejes agotados, A82 ...)
docs/MISSION.md:109-110 GAP #A ... **RESUELTO S115 = mislabel, NO es gap** ... NO reabrir
docs/MIROVA_DIVERGENCES.md:1129-1136  ### D-PCC ... RESUELTO S62 ... inner=7 -> 1.86x (-47%). Adoptado en `volcanoes.yaml` S62.
volcanoes.yaml (PuyehueCordonCaulle): inner_radius_km: 20  # MIROVA KML oficial
git log -S"inner_radius_km: 7" -- volcanoes.yaml:
  5d2bea4b9 S62 CIERRE: adoptar Lastarria kernel-bg + revertir PCC inner_radius + refutar Tupungatito (#85)
  fab02ec1c S62: PCC inner_radius 20->7 ... (#79)
```

Veredicto: **CONFIRMADO CON MATIZ**. (1) El "Adoptado inner=7" está en `docs/MIROVA_DIVERGENCES.md:1135`, no en `MISSION.md`; se revirtió en la misma S62 (PR #85) y el catálogo nunca lo anotó. (2) En `MISSION.md` la advertencia S131 cubre sólo la lista de "Abiertas"; la lista de "Resueltas" (D9 incluida) y las frases "irreducible", "todos los ejes agotados" y "GAP #A NO reabrir" siguen sin ninguna de las rebajas que `CLAUDE.md` ya tiene (A82 rebajada S124 y S138, GAP #A reabierto S128). `MISSION.md` es la puerta de tres preguntas que se lee antes de tocar el pipeline, así que es justo el documento donde un cierre viejo apaga más. Gravedad 3.

### V-07 (ítem 7). "Caso Gaua, p. 17" de Coppola 2016a

Caminos por los que podía estar mal: que "Gaua" esté con otra grafía, que esté en una figura (la capa de texto no lo vería), o que la cita sea de otro paper de Coppola.

```
PyMuPDF sobre documentacion/sp426.5.pdf (25 páginas): 'Gaua' 0 páginas, 'Vanuatu' 0 páginas
grep -c -i gaua documentacion/sp426_5.txt -> 0
p. 17 (texto): "these false detections typically radiate less than 5 MW and can be easily identified by a visual inspection of the associated NTI map"
p. 16 (texto): "A limited number of false alerts may be detected by the algorithm. These principally occur on daytime images ..."
grep Gaua en documentacion/: aparece en coppola2019_supp_datasheet.md, coppola2023_frontiers.md y otros 5; docs/audit_s141/lectura/VERIFICADOR_LECTORES.md:134-146 ubica "less than 2% of the total MODIS overpasses" en Coppola et al. 2016, JVGR 322 (Vanuatu), p. 10, §4.6
```

Veredicto: **CONFIRMADO CON MATIZ**. "Gaua" y "<2 %" no están en SP426.5; la sustancia que importa para el tope de 5 MW ("las falsas detecciones irradian típicamente menos de 5 MW") sí está en la p. 17 de SP426.5, pero referida a imágenes **diurnas**, bordes de cuerpos de agua y nubes dispersas, sin volcán nombrado. La atribución "Gaua" viene del paper de Vanuatu (JVGR 322, 2016), que es otro. Hallazgo propio asociado: la cita mala no vive sólo en el catálogo (`docs/MIROVA_DIVERGENCES.md:259, 265, 287`): está en el perfil de producción, `pipeline/profiles/mirova_equivalent.yaml:482` ("Cap=5MW basado en Coppola 2016a Gaua"), y en seis perfiles más. Gravedad 2 (el tope es un parche propio declarado; la cita errada le da un respaldo de paper que para pasadas nocturnas no tiene).

### V-08 (ítem 8). N·σ = 5 / 10 del test de BT atribuido a la Tabla 1

Página 7 de `documentacion/sp426.5.pdf` renderizada a imagen y mirada (PNG borrado después):

```
Test 2:  dNTI_PIX > C1  or  dNTI_PIX > mu_dNTI + C2*sigma_dNTI
Test 3:  dETI_PIX > C1  or  dETI_PIX > mu_dETI + C2*sigma_dETI
Table 1. Parameters used in the MIROVA algorithm
            Night-time ROI1 / ROI2     Daytime ROI1 / ROI2
  K1          -0.8 / -0.8                -0.6 / -0.6
  C1           0.003 / 0.01               0.02 / 0.02
  C2           5 / 10                     15 / 15
Única aparición de 'brightness' en las 25 páginas: p. 5, definición de NTIapp (Tapp = BT_TIR)
pipeline/profiles/mirova_equivalent.yaml:128-134  "N·sigma differential summit/scene (Coppola 2016a Tabla 1)"  n_sigma_mir_summit: 5.0  n_sigma_mir_scene: 10.0
pipeline/profiles/mirova_equivalent.yaml:279-282  "dual-ROI BT ACTIVADO ... (Coppola 2016a Tabla 1)"  enable_dual_roi_bt: true
```

Veredicto: **CONFIRMADO**. En la Tabla 1, C2 multiplica la desviación de dNTI y de dETI. El paper no tiene ningún test sobre temperatura de brillo. El 5 / 10 aplicado a la BT del MIR es un préstamo de los números de C2 a otra variable, y `CLAUDE.md` (sección de reglas científicas) lo presenta dentro de la frase "La detección MODIS es FIEL a Coppola 2016a". Un test de BT absoluta es además justo la clase de path que A69 identifica como vulnerable al gradiente topográfico. Gravedad 4.

### V-06 (ítem 6). Test 1 integrado en el ROI y su cita "Coppola et al. 2015, Bull. Volcanol. 77:55, §2.2 Eq. 1"

Caminos por los que podía estar mal: que el PDF exista con otro nombre; que SP426.5 tenga una suma sobre el ROI en otra página; que el artículo exista y el proyecto simplemente no lo tenga.

```
pipeline/test1_integrated.py:12,17-18  "Coppola et al. 2015, 'MIROVA: a new hotspot detection system based on MODIS Level 1B data', Bulletin of Volcanology 77:55, §2.2"
p. 6 de sp426.5.pdf, renderizada y mirada:  "NTI_PIX > K1   (Test 1)  where NTI_PIX is the NTI pixel value and K1 is the threshold"
   y  "Pixels that satisfy Test 1 are flagged as 'active' and subsequently discarded (unsuitable) for further steps."
grep -i "integrat|sum of" documentacion/sp426_5.txt: la única suma es l. 389 "the sum of the single RP_PIX" (magnitud, no detección)
OpenAlex, Bull. Volcanol. (ISSN 0258-8900), 2015, vol. 77, issue 6:
   https://doi.org/10.1007/s00445-015-0938-7 | Fracture and compaction of andesite in a volcanic edifice | p 55 | Michael J. Heap, Jamie Farquharson
Crossref /works/10.1007/s00445-015-0938-7:
   vol 77 issue 6 art 55 | ['Heap', 'Farquharson', 'Baud', 'Lavallée', 'Reuschlé']
OpenAlex y Crossref, Bull. Volcanol. 2015 con autor Coppola: count 0 / total-results 0
   (control del instrumento: la misma consulta sin autor devuelve 12 artículos del issue 6, así que el cero no es de la consulta)
Crossref query.bibliographic con el título citado: primer resultado 10.1144/sp426.5, "Enhanced volcanic hot-spot detection using MODIS IR data: results from the MIROVA system", publicado en línea 2015-05-14
documentacion/BIBLIOGRAPHY_SYNTHESIS.md:36-47: el propio proyecto ya verificó (S128) que su "coppola2015.pdf" era SP426.5 por hash
```

Veredicto: **CONFIRMADO, y más fuerte de lo que el auditor afirmó**. El artículo 55 del volumen 77 de Bulletin of Volcanology es de Heap et al. sobre mecánica de rocas en andesita (DOI 10.1007/s00445-015-0938-7); Crossref y OpenAlex no registran ningún artículo de Coppola en esa revista en 2015, y el título citado no aparece (lo más parecido que devuelve Crossref es el propio SP426.5). No concluyo más que eso: la referencia, tal como está escrita, no corresponde a ningún artículo localizable. En SP426.5 el Test 1 es por píxel contra K1 y no hay integración sobre el ROI en ninguna parte del algoritmo de detección. El Test 1 integrado (suma del exceso de radiancia MIR sobre el ROI, k_sigma = 3, mir_rel = 0,02, ROI de 3 km, anillo de 1 km) es un detector propio. Está en producción (`TEST1_K_SIGMA 3.0`, `TEST1_ROI_KM 3.0`, `TEST1_MIR_RELATIVE 0.02`), lleva la cita en la cabecera FICHA del sistema de decisiones automatizadas, y `docs/MIROVA_DIVERGENCES.md:707` lo hace pasar la pregunta 1 de `MISSION.md` ("Test 1 ES Coppola 2015 §2.2 Eq.1, paper MIROVA core"). Gravedad 5: es el mecanismo que cerró D4 y pasó la puerta de la misión con un paper que no existe como se cita, y va a una ficha de transparencia publicable.

### V-15 (ítem 15). Hueco del corpus

Script propio `v15_hueco.py` (huecos de más de 7 días entre fechas con records):

```
Lascar huecos>7d: [('2025-11-15', '2026-01-29', 74)] | 2025-11: 136 2025-12: None 2026-01: 26
(idénticos en Lastarria, Isluga, Tupungatito, PlanchonPeteroa, NevadosDeChillan, Llaima, Copahue, Chaiten)
Villarrica huecos>7d: [] | 2025-11: 336 2025-12: 344 2026-01: 353
PuyehueCordonCaulle huecos>7d: [('2025-10-09', '2026-01-29', 111)] | 2025-10: 105 2025-11: None 2025-12: None
```

Veredicto: **CONFIRMADO CON MATIZ**: 10 de 11 tienen el hueco, pero en Puyehue Cordón Caulle es más largo (2025-10-10 al 2026-01-28, 111 días). Sólo Villarrica es continuo. Consecuencia que el enunciado no dice: la referencia del scraper empieza el 2026-01-10 y el corpus retoma el 2026-01-29, así que los primeros 19 días de referencia sólo se pueden parear en Villarrica. Gravedad 2.

### V-09 (ítem 9). Las "76 noches de FN recuperadas" de D12 (S121)

Caminos por los que podía estar mal: que exista otra referencia de MIROVA que sí cubra 2025; que el script de S121 cruzara contra ella.

```
docs/AUDIT_S121_D12_AB.md:3   ventana del reproc 2025-02-15..05-15
docs/AUDIT_S121_D12_AB.md:19  Láscar | 107 | **76** (reales, vol activo) ; columna: noches "curadas" (cluster <= inner)
grep -i "osf|mirova|confirm|real" experiments/_s121_d12_ab/analyze.py -> sólo la ruta BASE: el script no carga ninguna referencia
v09_d12.py:
records MODIS Lascar en ventana: 172 | far con cumulo<=5km: 147 | noches: 88 | noches ya summit: 17 | noches candidatas no cubiertas: 73
ref NRT (CONS+OCR) Lascar en ventana: 0
OSF v2.5 MODIS Lascar en ventana: filas 79 noches 55 Dayflag {0: 79}
candidatas no cubiertas con noche OSF: 39 de 73 | noches OSF ya publicadas summit: 16 | noches OSF sin ninguna de las dos: 0
```

Veredicto: **CONFIRMADO CON MATIZ importante**. Es cierto que la referencia NRT (CSV del scraper) tiene 0 filas en esa ventana y que el script de S121 define "curada" como "cúmulo dentro del inner", sin cruzar con nada: llamarlas "FN recuperadas" es usar una palabra que exige una alerta de MIROVA que nadie miró. Pero "MIROVA tiene 0 alertas" vale sólo para el CSV: el archivo OSF v2.5 (`data/mirova_reference/VRP_GLOBAL_ARCHIVE_2025.csv`, producto filtrado, A105) sí cubre Láscar en esa ventana, con 79 detecciones MODIS nocturnas en 55 noches. Con mi aproximación a la población de S121 (no es el A/B: los artefactos del run vivían en un scratchpad temporal que ya no existe, así que el 76 exacto es **NO VERIFICABLE**), 39 de 73 noches candidatas tienen detección OSF, y las 55 noches OSF quedan todas cubiertas entre lo ya publicado (16) y lo oculto por la etiqueta `far` (39). O sea: D12 como fenómeno queda corroborado por una referencia independiente para cerca de la mitad de las noches; la cifra 76 como "FN" no. Ojo con la trampa A89 que casi me hace errar: buscar el volcán por nombre `ascar` en el OSF da 0 filas (está escrito "Láscar"); por `IDvolc = 355100` da 10.028. Gravedad 3.

### V-01 (ítem 1). D9: "207 de 214 = 96,7 % MIROVA-confirmados" y "199 far, 0 fuga"

Caminos por los que podía estar mal la afirmación del auditor ("no se reproduce con ninguna definición"): que sí se reproduzca con la ventana y el corpus de junio; que el corpus haya sido reprocesado después; que "confirmado" tuviera una tolerancia temporal u otra llave.

Qué hice: (a) barrido de definiciones sobre el corpus de hoy (`v01_d9.py`, `v01b_d9.py`); (b) la misma medición sobre el corpus y la referencia **tal como estaban el 2026-06-19** leídos con `git show` del commit `1d6b5b932` (`v01c_d9_junio.py`, `v01d_d9_tol.py`). Definición: `t_bg_k < 262`, path D dominante (`diag_n_dnti_ctx_path` mayor que la suma de los otros tres), `primary_cluster.vrp_mw > 0`, ventana 2026-05-01 a 2026-06-18.

```
corpus de hoy:   05-01 06-18 | 262 | dominante | far 216, far pc>5: 0 | summit 216
commit de junio: ventana ('2026-05-01', '2026-06-18') records totales 16296 | far 199 far pc>5: 0 | summit 214
   ALERTA                       misma fecha, mismo_sensor=True: 26/214 = 12.1%
   ALERTA+OCR                   misma fecha, mismo_sensor=False: 80/214 = 37.4%
   +FALSO_POSITIVO              misma fecha, mismo_sensor=False: 100/214 = 46.7%
   cualquier fila incl. RUTINA  misma fecha, mismo_sensor=True: 214/214 = 100.0%
tolerancia temporal, commit de junio (cualquier fila | sólo ALERTA* | VRP_MW>0):
tol  30 min mismo_sensor=False: cualquier fila 201/214 | solo ALERTA* 56/214 | VRP_MW>0 61/214
tol  45 min mismo_sensor=False: cualquier fila 204/214 | solo ALERTA* 58/214 | VRP_MW>0 63/214
tol  60 min mismo_sensor=True:  cualquier fila 211/214 | solo ALERTA* 26/214 | VRP_MW>0 27/214
población de junio por volcán: PuyehueCordonCaulle 59, Lastarria 33, Lascar 29, Tupungatito 29
población de hoy por sensor: v750 162, modis 38, v375 16
```

Veredicto: **CONFIRMADO CON MATIZ, y el matiz corrige al auditor en una mitad**. Los denominadores de S113 **sí se reproducen, exactos**: 199 `far` y 214 `summit` salen al primer intento sobre el commit de junio, con 0 `far` sobre 5 MW. Lo que no se reproduce es el numerador: con cualquier definición en que "confirmado" signifique que MIROVA publicó una alerta (misma fecha, con o sin mismo sensor, con o sin OCR, con tolerancia de 5 a 60 min) el máximo es 80 de 214 (37,4 %), y 100 de 214 si además se cuentan los `FALSO_POSITIVO` del scraper. El rango 201 a 211 sólo aparece cuando "confirmado" cuenta **cualquier fila de la referencia, incluidas las RUTINA**, o sea cuando significa "MIROVA miró esa pasada", no "MIROVA vio algo". No encontré la definición exacta que da 207 (NO VERIFICABLE), pero ninguna definición basada en alertas pasa de 47 %. Sobre el "0 fuga": es circular, porque una "fuga" sería un record `far` visible y el predicado del dashboard oculta todo `far` por construcción; la parte no circular de esa frase (0 records sobre 5 MW, tope activo) sí se confirma. Además la composición desmiente la lectura física de S113 ("fondo frío por altitud: Láscar, Lastarria, Tupungatito"): el volcán con más records es Puyehue Cordón Caulle (59 de 214, 2.236 m), y tres de cada cuatro son VIIRS 750. Consecuencia: el argumento con que se descartó para siempre cualquier co-validación del path D en fondo frío ("mataría 207 detecciones reales") no tiene respaldo; lo que los datos dicen es que entre 63 y 88 % de esa población no tiene alerta de MIROVA. Gravedad 4.

### V-02 (ítem 2). "En MODIS el pipeline encuentra el cráter el 90 %" no tiene tasa base

Caminos por los que podía estar mal la afirmación del auditor: que "sin alerta" incluya pasadas que MIROVA no miró (no serían negativos limpios); que la unidad (noche contra pasada) cambie el resultado; que el efecto sea de un solo volcán.

Camino propio (`v02_tasa_base.py`): unidad = pasada MODIS nocturna nuestra; positiva si hay ALERTA MODIS de MIROVA esa fecha, **negativa limpia** si hay filas MODIS de MIROVA esa fecha y todas son RUTINA; "encuentra el cráter" = cúmulo primario con magnitud y centroide dentro del inner.

```
('2026-01-29', '2026-08-28') modis  pos: n=158 crater=148 (93.7%) crater_y_summit=10 (6.3%)
                                    neg: n=4800 crater=4275 (89.1%) crater_y_summit=562 (11.7%)
   Lascar pos [144, 135] 94% | neg [257, 230] 89%      (144 de las 158 pasadas positivas son de Láscar)
('2026-01-29', '2026-08-28') v750   pos 47.5% | neg 22.8%
('2026-01-29', '2026-08-28') v375   pos 84.5% | neg 62.1%
('2026-08-29', '2026-09-19') modis  neg: n=500 crater=430 (86.0%) | pos n=2
re-corrida del script del auditor (d12_tasa_base_crater.py, por noche): modis con_alerta [50, 50, 100.0] sin_alerta [2234, 2276, 98.2]
```

Veredicto: **CONFIRMADO**. Por pasada y con negativos limpios la tasa base es 89,1 % (por noche, con la definición del auditor, 98,2 %; su JSON quedó idéntico tras la re-corrida, comprobado con `cmp`). La diferencia entre "MIROVA alertó" (93,7 %) y "MIROVA miró y no vio nada" (89,1 %) es de menos de cinco puntos: en MODIS casi siempre hay un cúmulo con magnitud dentro del inner, haya o no actividad. El 90 % no mide "encontrar el cráter". Dos cosas que agrego: (1) la muestra positiva es casi un solo volcán (Láscar, 144 de 158); (2) el control de instrumento funciona, porque en VIIRS 375 y 750 sí hay contraste (84,5 contra 62,1 y 47,5 contra 22,8). Esto toca la premisa de A82 y de D11 y D12 ("el problema es sólo de etiqueta, la detección está"): con esta tasa base, destapar la etiqueta destaparía por igual las noches con y sin actividad. Gravedad 4.

### V-03 (ítem 3). El AUC 0,859 de A83

Primero la fuente: el 0,859 **no sale de `discriminant_sweep.py`**. Ese script (`experiments/_s114_audit/discriminant_sweep.py`) es de S114 y compara Láscar contra nevados. El 0,859 de S116 vive sólo en `experiments/_s116_followup/c2_discriminator.json`, **sin script en el repo** (busqué `0.859` y `4560` con grep en `experiments`, `docs` y `scripts`). El JSON declara su propia etiqueta:

```
population.definition: recapture>0 & distance_class==summit & pc.centroid_dist_km<=inner_radius
n_records: 4560   n_tp_mirova_alerta: 1690   n_ntp: 2870   tp_rate_pct: 37.1
tp_label: ALERTA_TERMICA (vol,noche,sensor-bucket) +/-1 dia, A11 RUTINA/FP no cuentan
```

Camino propio (`v03_auc.py`, `v03b_auc_por_volcan.py`): misma población y etiqueta sobre el corpus de hoy, ventana 2026-01-29 a 2026-06-25.

```
n 4547 positivos 2242 (49.3%)
GLOBAL        pos 2242 neg 2305 AUC 0.762 | nulo barajado p2.5-p97.5 [0.484, 0.515]
sensor modis  pos   14 neg  391 AUC 0.749 | nulo [0.347, 0.625]
sensor v750   pos  569 neg 1157 AUC 0.629 | nulo [0.474, 0.528]
sensor v375   pos 1659 neg  757 AUC 0.671 | nulo [0.476, 0.526]
control de confusion: AUC de 'es VIIRS 375' contra la misma etiqueta: 0.706
dentro de volcán y sensor (estratos con al menos 15 por clase):
  v375 Isluga 0.574 | Tupungatito 0.496 | PlanchonPeteroa 0.589 | NevadosDeChillan 0.457 | Villarrica 0.588 | PuyehueCordonCaulle 0.590 | Chaiten 0.501
  v750 Isluga 0.623 | Tupungatito 0.485 | PlanchonPeteroa 0.679 | PuyehueCordonCaulle 0.545
  v375 Lascar pos 298 neg 0 | v375 Lastarria pos 228 neg 7   (sin negativos: no pueden aportar dentro del estrato, pero sí empujan el global)
AUC medio dentro de volcan+sensor, ponderado por pares: 0.554 | estratos: 11
```

Veredicto: **CONFIRMADO CON MATIZ**. Confirmado: la etiqueta es "MIROVA publicó una alerta", y A83 llama "artefacto" a todo lo demás, que por A54 es en su mayoría señal real no publicada; la población se reproduce (4.547 contra 4.560) y el AUC global hoy es 0,762, no 0,859. Matiz 1: contra un nulo de etiquetas barajadas sin estratificar, los AUC por sensor (0,63 y 0,67) sí quedan claramente fuera del nulo (tope 0,53), así que "apenas supera un nulo" vale sólo con el nulo del auditor, que baraja dentro de cada volcán. Matiz 2, que es el hallazgo de fondo y sale por un camino distinto al del auditor: el 0,76 global es una paradoja de Simpson. La sola variable "el record es VIIRS 375" da AUC 0,706 contra esa etiqueta, y dentro de un mismo volcán y sensor el AUC ponderado cae a 0,554, con varios estratos bajo 0,50. La variable separa volcanes (Láscar aporta 298 positivos y cero negativos), no records. Consecuencia doble: el número y el nombre de A83 caen, pero su conclusión práctica ("no hay un escalar por record") sale reforzada bajo esta etiqueta; lo que A83 no puede hacer es apagar la búsqueda de un discriminante real contra artefacto, porque nunca midió esa pregunta. Gravedad 3.

### V-04 (ítem 4). D16: "la grilla UTM NO explica el sub-reporte, CERRADA, NO REABRIR"

Fuente: `docs/MIROVA_DIVERGENCES.md:1857-1899`; script `experiments/_s124_f70/04_tabla_brazos.py` (ubicado; lo re-corrí, sólo imprime, `git status` del directorio quedó limpio).

```
04_tabla_brazos.py l. 18: INI, FIN = "2026-06-25", "2026-08-24"      -> 61 días (calculado con datetime)
04_tabla_brazos.py l. 40: if (r.get("Sensor") or "").strip().upper() != "VIIRS375": continue
volcan                  n   control         A         B         C
Lascar                 32     0.47      0.46      0.58      0.58
Isluga                 40     0.70*     0.69      0.81*     0.81*
Lastarria              27     0.36      0.34      0.34         --
Copahue                 1     1.02*     1.07*     1.07*     1.02*
Tupungatito            17     0.81*     0.82*     0.81*     0.81*
NevadosDeChillan        2     1.31*     1.31*     1.31*     1.31*
Villarrica              9     0.72*     0.72*     0.72*        --
PuyehueCordonCaulle    21     0.75*     0.64      0.64         --
(Llaima no aparece: sin pares)
docs/MIROVA_DIVERGENCES.md:1924-1940 (D17, nota S130): "el mecanismo geométrico SÍ quedó probado, por otro eje: el ÁNGULO ... 0,740 cerca del nadir a 0,253 más allá de 50° en VIIRS375 (n = 2.767) ... El brazo fiel sería bow-tie + regrid en ese orden ... S130 lo deja medido, no implementado"
docs/MIROVA_DIVERGENCES.md:1959 (D17): "Nuestro regrid F70 se centró en volcano["lat"]/["lon"] ..." (el punto equivocado)
```

Veredicto: **CONFIRMADO CON MATIZ**. Todo lo factual se sostiene: sólo VIIRS 375, 61 días, n = 1 en Copahue y n = 2 en Nevados de Chillán, 171 pares en total dominados por tres volcanes del norte, y el remuestreo probado es el F70 que D17 declara mal centrado y sin el paso de bow-tie. Matiz: el propio texto de D16 termina con "lo que queda vivo es otra cosa: ver D17", así que la contradicción no es entre dos cuerpos de texto sino entre el **título y el "NO REABRIR"** de D16 (que dicen "la grilla no explica") y la nota S130 de D17 (que dice que el mecanismo geométrico quedó probado y que el brazo fiel nunca se corrió). Lo que D16 refutó es "el regrid F70 arregla la magnitud", no "la grilla de MIROVA explica el sub-reporte". Quien lea sólo encabezados se lleva lo contrario de lo que el catálogo sabe. Además el experimento no tocó MODIS ni VIIRS 750, y el gradiente cenital de S130 es justo un eje que una mediana de 61 días promedia. Gravedad 4.


---

## Segundo tramo del verificador (ítems 16, 17, 10, 11 y 12)

El primer verificador se cortó por un fallo técnico después de V-04. Este tramo lo hizo otra instancia con contexto limpio, con el mismo método y reutilizando `vlib.py` y `v_cache.json`. No se tocó nada de lo ya escrito arriba.

### V-16 (ítem 16). Caso A2 con la vara corregida: el mejor brazo pasa a 9 de 9 y producción baja a 5 de 9

Caminos por los que podía estar mal, escritos antes de abrir el informe del agente: (a) la coordenada o la distancia y el rumbo mal calculados; (b) el punto GVP no coincide con lo que el autor del paper detecta en su figura; (c) la "regla general" está hecha a la medida y al aplicarla a ciegas mueve o deja de mover otros casos por umbrales elegidos mirando; (d) el acierto depende del radio de 5 km; (e) los controles no podían fallar; (f) el acierto lo dan cúmulos con tope de 5 MW del camino D y no la lava; (g) el veredicto de producción (sin posiciones guardadas) se decidió con una cota mal usada; (h) el pre-registro se editó después.

Qué hice. Hash del pre-registro, recálculo propio de la geometría con dos herramientas, render de la página 19 a imagen y medición con script de la máscara de alerta (`v16_figA2.py`, con la Fig. A3 como control), la misma medición para todas las figuras (`v16_mascaras_todas.py`), y lectura directa de los `resultado_apendice.json` sin importar el evaluador del agente (`v16_a2_propio.py`). El evaluador del agente ya lo había re-corrido el primer verificador sobre una copia: comparé las dos salidas.

```
sha256sum docs/audit_s146/A2_CRITERIO_PRE_REGISTRADO.md
758b3ea1c54e2bc9c7d8384ce2f279f723098b4a3f095fa431d573421cdc6b27      (coincide con el pedido y con HASH_PRE_REGISTRO.txt, sellado Sun Sep 20 06:30:52 UTC 2026)

fisura dec 63.635 -19.44
haversine (9.533342245122443, 88.57684484879292)
pyproj WGS84 km 9.56975058241979 az 88.57861860426766

diff salida_cruda.txt (agente) vs a2_salida.txt (re-corrida del verificador): sólo difiere la línea "escrito: <ruta>"

A2 ALERT mask      n blancos 124  celdas x 33.5 a 37.2  y 25.8 a 28.3  centroide 35.59 27.11 -> dist 9.65 km rumbo 83.4
A3 ALERT mask (control, esperado centro)  n blancos 55  centroide 25.24 26.55 -> dist 0.94 km
Condición 2 en los otros positivos (mi medición): A1 1.42 km | A3 0.94 | A5 1.97 | A6 0.75 | A8 2.5
sep GVP-mascara medida km 0.87

B22sinBTloc max: pasadas 4 con magnitud 4 con posicion 4
   22:05 vrp 33.64 d_cumbre 8.53 sep_GVP 1.57 sep_mascara 1.18
   23:40 vrp 5.0 d_cumbre 7.37 sep_GVP 3.12 sep_mascara 3.78
   03:00 vrp 1.91 d_cumbre 10.86 sep_GVP 2.63 sep_mascara 1.82
   04:40 vrp 58.29 d_cumbre 9.11 sep_GVP 0.97 sep_mascara 0.54
   barrido radio (n pasadas dentro, ancla GVP): {0.01: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 4, 7: 4, 10: 4, 50: 4}
   nulo fino, caja 5 km a 9.53 km, rumbo->n dentro: {0: 0, 30: 0, 60: 3, 90: 4, 120: 1, 150: 0, ... 330: 0}
   sustrato N2 (otros 8, primario a >4.53 km): []
prod B21min: pasadas 4 con magnitud 4 con posicion 0     (evaluador: d_cumbre 1.40, 2.34, 1.77, 3.12 -> cota_A93 8.13, 7.19, 7.76, 6.42)
```

Lectura. La figura A2 muestra un único grupo de celdas brillantes al este del centro y nada en el centro; la costa se ve al sur (franja clara bajo y = 15) y no entra en la máscara. El autor detecta el flanco, no la cumbre, así que evaluar A2 en la cumbre era medir otro objeto.

Veredicto: **CONFIRMADO CON MATIZ**, gravedad 2.

- Confirmado (a): 9,53 km y 88,6° salen igual por haversine; sobre el elipsoide WGS84 son 9,57 km, diferencia sin consecuencia.
- Confirmado (b), y es lo que de verdad sostiene el resultado: en la pasada de la figura (04:40) el mejor brazo pone 58,3 MW a 0,97 km del punto GVP y a 0,54 km de la máscara del autor medida por mí. Dos anclas independientes entre sí (boletín y figura) quedan a 0,87 km una de otra.
- Confirmado (d): el acierto NO depende del radio de 5 km. Se sostiene desde 1 km de radio, y con 4 km ya entran las cuatro pasadas.
- Confirmado (f): el acierto no depende de los cúmulos con tope de 5 MW; basta la pasada de 04:40.
- Confirmado (g): la baja de producción de 6 a 5 es lógica válida aun sin posiciones. Sus cuatro cúmulos están a 3,12 km o menos de la cumbre, así que ninguno puede estar a menos de 6,42 km de la fisura. Lo que producción contaba como acierto eran 0,12 a 0,52 MW junto a una cumbre que ese día estaba bajo hielo.
- Confirmado (c) con matiz: la condición 2 separa A2 de los otros cinco positivos por un margen ancho (9,65 km contra 2,5 km como máximo), así que los umbrales de 5 km y 45° no están ajustados al borde. Matiz: mis distancias (0,75 a 2,5 km) son mayores que las que el criterio toma de S138 (0,21 a 1,29 km), y mi máscara de A2 sale a 9,65 km y no a 10,98 km. Mi medición tiene un sesgo de cerca de una celda (el control A3 da 0,94 km donde debería dar cerca de 0), así que la diferencia cabe en el error de leer una imagen. Ninguna lectura cambia qué caso cumple la condición. La regla es general en su forma, pero sólo se ha ejercitado en un caso: no hay en la batería un segundo caso de flanco que la ponga a prueba.
- Matiz (e), el importante: **los controles no aportan nada al veredicto del mejor brazo**. C1 es una identidad (el evaluador sólo mueve el centro de A2). N1 está vacío por construcción: la batería guarda un cúmulo por pasada y en ese brazo los cuatro están al este, así que las cajas giradas no podían llenarse. N2 no tiene sustrato en ese brazo (0 pasadas de los otros ocho casos con el primario más allá de 4,53 km). El informe del agente lo declara con todas sus letras ("N1 y N2 no detectan regalo" y "son ciegos"), así que no es un hallazgo contra él, pero el pre-registro ponía "el peso de la prueba" en esos nulos y ese peso quedó en cero. Mi nulo fino (cada 30°) sí muestra algo: las cajas a 60° y 120° se llenan con 3 y 1 pasadas porque se solapan con la del este, o sea la vara resuelve la dirección con unos 60° de ancho, no más fino.
- NO VERIFICABLE desde esta sesión: la cita textual del boletín del GVP. `volcano.si.edu` respondió 403 y `web.archive.org` no es alcanzable con mi herramienta. La coordenada queda como SOSPECHA razonable, respaldada de forma indirecta por la figura del paper (0,87 km).
- SIN DATO: mi control de que los casos negativos dan máscara vacía. Mi detector de paneles no encontró los paneles de A4, A7 y A9, así que no dice nada sobre ellos.

Lo que el resultado NO dice, y el agente también lo escribe: no autoriza adoptar nada. Un 9 de 9 en nueve escenas MODIS no mide la sobre-publicación, que es donde está la brecha hoy.

Sobre el camino (h), el orden del pre-registro: los tiempos de modificación son coherentes pero no prueban el orden.

```
03:30:39 -0300 A2_CRITERIO_PRE_REGISTRADO.md | 03:30:52 HASH_PRE_REGISTRO.txt | 03:32:32 evaluar_vara_corregida.py | 03:32:38 out/* | 03:34:16 A2_RESULTADO_VARA_CORREGIDA.md
```

El evaluador (16 KB) figura modificado 100 segundos después del sello, lo que sólo dice que su última edición fue posterior (el propio script declara un diagnóstico "agregado después del pre-registro"). Todo está sin commitear, así que no hay historia de git que lo respalde. El hash prueba que el criterio no cambió desde el sello; que se escribió antes de mirar resultados es declaración del agente, que además admite que no era ciego. Por eso el peso lo pongo en la coincidencia con la figura del paper, que no depende de ese orden.

### V-17 (ítem 17). `pc.classification` como post-proceso, y la afirmación lateral sobre el OCR

Caminos por los que podía estar mal: (a) algún camino escribe en `data/mirova_equivalent/`; (b) algún valor o etiqueta promete un juicio físico; (c) la precedencia no es la del diseño; (d) "sin referencia" y "MIROVA miró y calló" se confunden; (e) la salida no es determinista; (f) los tests pasan aunque la lógica esté rota; (g) el OCR sí se sincroniza por otro workflow.

Qué hice: leí el diseño (§5.2 y §5.3) y el `reparto` de S145 antes que el informe del agente; corrí sólo `tests/test_clasificacion_referencia_s146.py`; corrí el script dos veces a carpetas mías del scratchpad con md5 de los records antes y después; crucé la salida entregada contra la referencia cruda con mi loader (`v17_clasificacion.py`, `v17b_no_reference.py`); y corrí nueve mutantes sobre COPIAS en el scratchpad (`v17c_mutaciones.py`).

```
12 passed in 14.51s
ventana 2026-09-01 a 2026-09-20 | pasadas 2285 | {'mirova_confirmed': 147, 'mirova_same_night': 652, 'mirova_silent': 1100, 'mirova_saw_outside': 18, 'no_reference': 368}   (dos corridas)
RECORDS INTACTOS            (md5 de data/mirova_equivalent/*.json igual antes y después)
DOS CORRIDAS MISMOS BYTES   (sha256 por archivo)
IGUAL A LO ENTREGADO        (sha256 de mis corridas = data/clasificacion_referencia/)

cruce propio contra la referencia cruda:
mirova_confirmed {'con ALERTA a +-2min': 147}
mirova_silent {'solo RUTINA a +-2min': 1100}
mirova_saw_outside {'con FALSO_POSITIVO a +-2min': 18}
mirova_same_night {'solo RUTINA a +-2min': 476, 'con FALSO_POSITIVO a +-2min': 14, 'sin ninguna fila a +-2min': 162}
no_reference {'sin ninguna fila a +-2min': 335, 'solo RUTINA a +-2min': 33}
   las 33: {'FALSO_POSITIVO mismo sensor misma fecha UTC, otra pasada': 33}
silent por sensor y corte OCR {('modis','antes'): 209, ('v375','antes'): 282, ('v750','antes'): 341, ('modis','despues del corte OCR'): 81, ('v375','despues'): 92, ('v750','despues'): 95}
alertas OCR 09-01..09-14: 57 | sin ALERTA equivalente en CONS a +-2 min: 17

mutantes (copias):
M0 sin cambio                                          -> 12 pasan
M1 precedencia: fuera-de-limite antes que misma-noche  -> 12 pasan   (SOBREVIVE)
M2 silencio y sin-dato intercambiados                  -> 5 fallan
M3 sin dato -> silencio                                -> 3 fallan
M4 misma-noche ignorada                                -> 1 falla
M5 guarda de escritura eliminada                       -> 1 falla (test_se_niega_a_escribir_dentro_de_los_records)
M6 hora de generacion en la salida                     -> 1 falla (test_determinista_y_lf)
M7 etiqueta con palabra prohibida                      -> 1 falla
M8 noche de volcan vacia                               -> 1 falla

sync-mirova-csv.yml:50-52  curl ... registro_vrp_consolidado.csv -o latest_consolidado.csv.new     (único curl del workflow)
grep registro_vrp_ocr .github/workflows/*.yml -> sólo audit-weekly.yml:57-58
git log del OCR del snapshot: 3872fedd4 2026-09-14 | a8d96442a 2026-09-07 | 38cb5e31d 2026-08-31 (todos "audit(auto): paridad semanal")
cons 2026-09-20 02:45:00 | ocr 2026-09-14 06:42:01
```

Veredicto: **CONFIRMADO CON MATIZ**, gravedad 2. La afirmación lateral sobre el OCR: **CONFIRMADA** (dos herramientas: lectura del yml y grep sobre todos los workflows; el OCR sólo lo trae el audit semanal, y por eso llega al 2026-09-14).

- (a) Limpio en el uso normal: el único `open(..., "w")` del módulo va a `out_dir`, con una guarda que el mutante M5 demuestra que el test vigila. Matiz 1: `--stats` escribe en la ruta que se le pase **sin ninguna guarda**; `--stats data/mirova_equivalent/Lascar.json` pisaría un archivo de records. No lo probé (sería destructivo); lo leo en `clasificar_referencia.py:100-102`.
- (b) Limpio: los cinco valores y sus textos describen qué hizo la referencia. "Solo nuestro" no insinúa artefacto. El test de palabras prohibidas sí muerde (M7).
- (c) Confirmado: la precedencia es la del `reparto` de S145 (misma pasada, misma noche, fuera de límite, silencio, sin dato). Matiz 2: **ningún test la vigila**. El mutante M1, que invierte "misma noche" y "fuera de límite", pasa 12 de 12, y en la salida real cambiaría 14 pasadas (las `mirova_same_night` con FALSO_POSITIVO a ±2 min).
- (d) Se distinguen bien en lo grueso (M2 y M3 caen con 5 y 3 tests). Matiz 3: 33 de las 368 `no_reference` (9 %) SÍ tienen una fila RUTINA de MIROVA a ±2 min; caen ahí porque ese sensor tuvo un fuera de límite en otra pasada de la misma fecha. El texto del valor dice "MIROVA no listó esta pasada o su registro aún no llega", que para esas 33 es falso. El agente lo declara en su informe (decisión 3), pero el operador lee la etiqueta, no el informe. Matiz 4, el de más peso operativo: 268 de los 1.100 `mirova_silent` son posteriores al corte del OCR (92 de VIIRS 375), y en la quincena previa 17 de 57 alertas del OCR no tenían equivalente en el consolidado. O sea, cerca de un tercio de las alertas del OCR llega sólo por el canal que todavía no está, así que "MIROVA miró y no publicó nada" es provisorio en esas pasadas. El JSON guarda `ultima_fila_ocr_utc`, pero el valor por pasada no lo refleja.
- (e) Confirmado: mismos bytes en dos corridas y además iguales a lo entregado.
- (f) Confirmado con el matiz de M1.

**Incidente propio, ya reparado.** El test `test_se_niega_a_escribir_dentro_de_los_records` apunta `--out` a la carpeta real `data/mirova_equivalent/x`. Con mi mutante M5 (guarda eliminada) el script escribió ahí 11 JSON de clasificación. Borré esa carpeta, que creó mi mutante, y verifiqué con md5 que los 11 records quedaron intactos (`RECORDS INTACTOS`) y que `git status` no muestra nada bajo `data/mirova_equivalent/`. Queda como hallazgo: ese test, el día que la guarda falle de verdad, ensucia el directorio que el cron NRT escribe y no limpia después. Debería apuntar a una copia temporal del árbol.

### V-10 (ítem 10). El "1,5 % corroborado" de D13 (cierre S126)

Fuente: `docs/MIROVA_DIVERGENCES.md:1520-1546` y `experiments/_s126_d13/01_que_apaga_la_cerca.py` (l. 85: `if (f, b) in noches_mir`, o sea fecha Y sensor; `_s126_lib.cargar_mirova` sólo deja alertas con hora UTC 3 a 9 y VRP mayor que cero).

Caminos por los que podía estar mal la crítica: (a) el pareo de S126 no es por sensor; (b) lo apagado no es mayoritariamente MODIS; (c) la tasa base de lo publicado no es baja en MODIS; (d) "por noche" del auditor no es por noche.

Medición propia (`v10_d13.py`, con `vlib`, sin `_s126_lib` ni `dlib`):

```
== alertas MIROVA: hora 3-9 UTC y VRP>0 (S126) n = 1157 por sensor {'v375': 978, 'v750': 161, 'modis': 18}
  apagado            modis  n= 2573  mismo sensor   27 (  1.0 %)  cualquier sensor esa fecha  862 ( 33.5 %)
  apagado            todos  n= 2704  mismo sensor   41 (  1.5 %)  cualquier sensor esa fecha  899 ( 33.2 %)
  publicado(summit)  modis  n=  339  mismo sensor    2 (  0.6 %)  cualquier sensor esa fecha  131 ( 38.6 %)
  publicado(summit)  todos  n= 5340  mismo sensor 1755 ( 32.9 %)  cualquier sensor esa fecha 2290 ( 42.9 %)
noches-volcan con algo apagado 1266 con alerta MIROVA 457 (36.1 %)
noches-volcan con algo publicado 1228 con alerta MIROVA 477 (38.8 %)
noches SOLO apagadas (nada publicado esa noche) 92 con alerta 1
```

Veredicto: **CONFIRMADO CON MATIZ**, gravedad 3. Todo lo que el auditor dice sale igual por mi camino: 41 de 2.704 (1,5 %; S126 tenía 2.694, el corpus creció), 2.573 de 2.704 = 95,2 % MODIS, y el MODIS que SÍ se publica se corrobora 0,6 %, menos que el apagado (1,0 %). La causa es de la referencia, no nuestra: en cuatro meses MIROVA tiene 18 alertas MODIS nocturnas, así que casi ningún record MODIS puede corroborarse por mismo sensor. El 1,5 % mide la rareza de las alertas MODIS de MIROVA, no la calidad de lo que la cerca esconde. Matiz 1: el "33 % contra 43 % por noche" del auditor es por RECORD pareado a una fecha con alerta; en noches de verdad la diferencia casi desaparece (36,1 % contra 38,8 %). Matiz 2, que el auditor no midió y que va en sentido contrario a su conclusión: de las 1.266 noches con algo apagado sólo 92 no tienen ya algo publicado, y de esas 92 sólo 1 coincide con alerta. En la unidad del operador (A94), levantar la cerca agregaría una noche con respaldo de MIROVA. Así que cae el NÚMERO y cae la frase "corroboraría casi nada" como evidencia de artefacto, pero la conclusión práctica de S126 ("D13 no es una palanca") queda en pie por otra razón, que nadie había escrito. Límite de mi medición: "publicado" acá es `distance_class == summit`, no el predicado completo del dashboard (A97).

### V-11 (ítem 11). D20: banda 31 "despreciable", medido contra el margen a K1 y no contra el piso C1

Fuente: `docs/MIROVA_DIVERGENCES.md:2219-2222`: "el corrimiento del NTI entre las dos bandas va de 0,0001 (250 K) a 0,0054 (290 K), contra un margen de ~0,14 entre el NTI típico de escena y el umbral K1 = −0,8; en el dNTI se cancela porque es casi uniforme en la escena". No cita script; el respaldo es prosa de `docs/AUDIT_S128.md`.

Caminos por los que podía estar mal la crítica: (a) la vara de 0,14 sí es la que gobierna; (b) en el dNTI de verdad se cancela; (c) el residuo existe pero no puede cambiar ninguna decisión; (d) el cálculo del auditor tiene un error de Planck.

El fenómeno, antes de los números: el NTI compara el brillo en 4 µm con el brillo en el infrarrojo térmico. Cambiar la banda térmica de 11 a 12 µm corre el NTI de toda la escena, y eso no importa, porque el test que decide en MODIS no mira el NTI sino cuánto sobresale cada píxel respecto de sus ocho vecinos (dNTI) contra un piso de 0,003. Lo que importa es si el corrimiento es igual en el píxel y en los vecinos. No lo es: crece con la temperatura, así que un píxel más tibio que su entorno recibe un empujón extra.

Cálculo propio (`v11_d20.py`, Planck monocromático escrito aparte del de `d09`; agregué el caso con lava, que el auditor no tiene):

```
control S128: s(T)=NTI32-NTI31
  T=250 K  s=-0.00008 | T=270 K  s=+0.00159 | T=290 K  s=+0.00539            (reproduce 0,0001 y 0,0054)
(i) pixel dT mas tibio que sus 8 vecinos, sin lava
  fondo 260 K dT= 2: dNTI31=+0.00289 dNTI32=+0.00306 dif=+0.00017 = +0.06 C1 | cruza C1? b31 False b32 True
  fondo 270 K dT= 5: dNTI31=+0.00945 dNTI32=+0.01016 dif=+0.00072 = +0.24 C1
  fondo 280 K dT=10: dNTI31=+0.02437 dNTI32=+0.02659 dif=+0.00222 = +0.74 C1
(ii) pixel con fraccion f a 1000 K
  fondo 260 K f=1e-05: dNTI31=+0.01297 dNTI32=+0.01314 razon32/31=1.013
  fondo 275 K f=1e-05: dNTI31=+0.00960 dNTI32=+0.00992 razon32/31=1.034
```

Veredicto: **CONFIRMADO CON MATIZ**, gravedad 2.

- Confirmado: la vara de D20 es la equivocada. El margen de 0,14 es el de la ruta del NTI absoluto; el piso que decide en MODIS es 0,003, unas 47 veces más chico. Y "en el dNTI se cancela" es falso como enunciado: queda un residuo, que mi cálculo reproduce igual que el del auditor (hasta 0,74 C1).
- Matiz, contra el auditor: "12 a 74 % de C1" tampoco es la unidad que decide. El residuo es grande sólo cuando el dNTI ya es grande: el caso de 0,74 C1 corresponde a un píxel cuyo dNTI es 0,024, ocho veces el piso, que alerta con cualquiera de las dos bandas. Lo que decide es el cambio RELATIVO del dNTI: 6 a 9 % para contraste de terreno y 1 a 3 % para lava. Sólo cambia de lado un píxel cuyo dNTI esté a menos de ese porcentaje del piso, como el primer caso de la tabla (2 K de contraste a 260 K: 0,00289 contra 0,00306). Cuántos píxeles reales de MODIS viven en esa franja es **SIN DATO**: hay que abrir gránulos y eso no se puede desde acá.
- Hallazgo propio dentro del ítem: la banda 32 amplifica más el contraste de TERRENO (6 a 9 %) que la señal de LAVA (1 a 3 %). O sea, pasarse a la banda del paper empujaría un poco hacia más alertas topográficas en los nevados, no hacia más lava. Es orden de magnitud (cuerpo negro, sin respuesta espectral ni atmósfera), pero el signo importa si algún día se corre ese A/B.
- Consecuencia: "despreciable" debe leerse como "chico y no medido", no como "cero". No cambia ninguna decisión hoy; la gravedad es por el método (un cierre por cálculo contra la vara que no gobierna, A95), no por el efecto.

### V-12 (ítem 12). A99: el 0,995 "a igual conteo" es el producto de dos factores opuestos

Fuente: `experiments/_s139_audit/magnitud/04_fondo_y_test1.py` y su insumo `02_pares.csv` (pareo contra el OSF v2.5, 2025-02-15 a 2025-12-01, o sea régimen previo a #535 y contra una fuente filtrada, A105). No re-corrí el script del autor: leí el CSV con `csv`, sin pandas, y rehice la cuenta (`v12_a99.py`).

Caminos por los que podía estar mal la crítica: (a) los dos factores no son opuestos sino ambos cercanos a 1; (b) el n o la fracción de un píxel no son esos; (c) el producto no es exacto y el 0,995 viene de otro lado; (d) la compensación es un artefacto de la media geométrica.

```
pares 375 con fondo implicito y R>0: 1499
igual conteo: 343 | de ellos con F_hot<=0 (el script 04 los descarta): 1 | conteo distinto: 1156
igual conteo sin filtro F_hot: 343 de un pixel: 233
control identidad R=F_n*F_ex, error max: 0.0
n=342  R gm=0.995  F_hot gm=1.140  F_bg gm=0.873  producto=0.995
dispersion de R: p10=0.52 p25=0.86 mediana=1.07 p75=1.35 p90=1.63 | dentro de 0.8-1.25: 156 de 342 | fuera de 0.5-2: 44
por n de pixeles: {1: (232, 1.013), 2: (68, 0.949), 3: (23, 0.974), 4: (11, 0.913), 5: (3, 0.991), 6: (4, 1.054), 7: (1, 1.332)}
por volcan (n, R gm, F_hot gm, F_bg gm):
   Lastarria                86  0.841  1.176  0.715
   PlanchonPeteroa          63  1.333  1.163  1.146
   Isluga                   60  0.943  1.170  0.806
   PuyehueCordonCaulle      47  1.112  1.043  1.066
   Chaiten                  29  1.233  1.009  1.222
   Lascar                   27  0.803  1.103  0.728
   Copahue                  22  0.661  1.172  0.564
   Villarrica                8  1.386  1.530  0.906
bootstrap R gm IC95: 0.939 1.054
sin Lastarria (n=86): R gm del resto = 1.053 (n=256)
todos los pares 375: R gm = 0.687 | fraccion con igual conteo: 0.231
```

Veredicto: **CONFIRMADO CON MATIZ**, gravedad 3.

- Confirmado, número por número: 343 pares (342 tras descartar uno con nivel caliente no positivo), 233 de un solo píxel, y 0,995 = 1,140 × 0,873. Nuestro píxel caliente queda 14 % por encima del de MIROVA y nuestro fondo resta 13 % de más; se anulan.
- Matiz 1, hallazgo propio: hay una SEGUNDA compensación, entre volcanes. La razón por volcán va de 0,66 (Copahue) a 1,39 (Villarrica), y el factor de fondo de 0,56 a 1,22. El 0,995 es el centro de una nube ancha: sólo 156 de 342 pares están entre 0,8 y 1,25, y 44 están fuera de 0,5 a 2. Es el error de S126 (una mediana agrupada que tapa volcanes opuestos). "A igual conteo la razón es 0,995" no describe ningún volcán en particular.
- Matiz 2: el subconjunto es el 23 % de los pares y está sesgado a lo más simple (dos tercios de un píxel, tres volcanes del norte y Planchón suman 61 %); Villarrica entra con 8 y Llaima, Tupungatito y Nevados de Chillán casi no están.
- Qué parte de A99 sobrevive: que la fórmula (k, A, Planck) no es el problema sigue apoyado por otro script (el 01, que no revisé: SOSPECHA de que está bien, no verificado). Lo que NO sobrevive es usar el 0,995 como prueba de que "a igual selección coincidimos": a igual selección discrepamos 14 % en un sentido y 13 % en el otro, y por volcán hasta 44 % en el fondo. El propio título de A99 nombra el fondo del anillo, así que la regla no es falsa; lo que está mal es la frase que la resume y el uso que se le dio después (`docs/MIROVA_DIVERGENCES.md:2331` y `docs/HYPOTHESIS_LOG.md:1492` la citan como "la fórmula está bien, falta selección").
- De dónde sale el 1,14 (remuestreo de MIROVA que promedia el píxel caliente, banda, o geolocalización) es SIN DATO, igual que para el auditor.

## Hallazgos propios del segundo tramo

Cosas que ni los auditores ni los agentes de trabajo nuevo habían escrito. Cada una remite a la salida pegada en su ítem.

1. **Un test del trabajo nuevo puede ensuciar el directorio que escribe el cron NRT** (V-17). `test_se_niega_a_escribir_dentro_de_los_records` usa la carpeta real `data/mirova_equivalent/x` como destino. Con la guarda rota escribe ahí 11 JSON y no limpia. Me pasó con un mutante sobre una copia; lo limpié y verifiqué md5 de los records. Gravedad 3, porque es justo el escenario para el que el test existe.
2. **La precedencia entre valores de `classification` no tiene test** (V-17): invertir "misma noche" y "fuera de límite" pasa 12 de 12 y cambia 14 pasadas reales. Gravedad 2.
3. **`--stats` escribe sin guarda** en la ruta que reciba, incluida `data/mirova_equivalent/` (V-17, leído en el código, no ejecutado). Gravedad 2.
4. **`mirova_silent` es provisorio después del corte del OCR** (V-17): 268 de 1.100, y 17 de 57 alertas del OCR de la quincena previa no tienen equivalente en el consolidado. El valor por pasada no lo señala. Gravedad 3 para un rótulo que va a leer el geólogo de turno.
5. **33 de 368 `no_reference` sí tienen fila de MIROVA** (V-17): el texto del valor es falso para ellas. Gravedad 2.
6. **Levantar la cerca de D13 agregaría una sola noche con respaldo de MIROVA** (V-10): 92 noches sólo apagadas, 1 con alerta. El 1,5 % cae como número, pero "D13 no es una palanca" se sostiene por esta otra vía, en la unidad del operador. Y el "33 % contra 43 % por noche" del auditor es por record; por noche es 36,1 % contra 38,8 %. Gravedad 2.
7. **La banda 32 amplifica más el terreno que la lava** (V-11): 6 a 9 % contra 1 a 3 % en el dNTI. Y la unidad "fracción de C1" del auditor exagera la relevancia: sólo cambian de lado los píxeles a menos de ese porcentaje del piso. Gravedad 2.
8. **El 0,995 de A99 esconde una segunda compensación, entre volcanes** (V-12): de 0,66 en Copahue a 1,39 en Villarrica; sólo 156 de 342 pares entre 0,8 y 1,25. Gravedad 3.
9. **En A2 lo que sostiene el acierto no son los controles pre-registrados sino la figura del paper** (V-16): 58 MW a 0,54 km de la máscara del autor medida con script, y el acierto se mantiene desde 1 km de radio. Los nulos N1 y N2 están vacíos por construcción en el mejor brazo (el agente lo admite). Mi medición de máscaras da distancias algo mayores que las de S138 (A2 a 9,65 km y no 10,98), sin cambiar qué caso cumple la regla. Gravedad 2.
10. **El orden del pre-registro de A2 no es demostrable**: todo está sin commitear y los tiempos de archivo sólo son coherentes, no probatorios (V-16). Gravedad 1.

## Verificado limpio en el segundo tramo

- El sha256 del pre-registro de A2 coincide con el pedido y con el sello.
- 9,53 km y 88,6° de la cumbre a la fisura: correctos por haversine; 9,57 km sobre WGS84.
- La figura A2 del paper es coherente con calor al este de la cumbre y nada en la cumbre; la costa al sur no entra en la máscara.
- La salida del evaluador de A2 se reproduce idéntica (salvo la ruta de escritura).
- El control C1 de A2 es una identidad, tal como el propio pre-registro declara.
- El acierto de A2 no depende del radio de 5 km ni de los cúmulos con tope de 5 MW.
- La baja de producción de 6 a 5 en la batería es lógica válida por la cota de distancias.
- `clasificar_referencia.py` en uso normal no toca `data/mirova_equivalent/` (md5 antes y después), es determinista (mismos bytes en dos corridas) y reproduce lo entregado byte a byte.
- Ningún valor ni etiqueta de `classification` insinúa artefacto, falso o ruido, y el test que lo vigila muerde.
- 147 de 147 `mirova_confirmed` tienen una ALERTA a ±2 min en la referencia cruda; 1.100 de 1.100 `mirova_silent` tienen sólo RUTINA; 18 de 18 `mirova_saw_outside` tienen un FALSO_POSITIVO.
- 8 de 9 mutantes los atrapa la suite del módulo.
- `sync-mirova-csv.yml` no trae el OCR; sólo `audit-weekly.yml` lo hace, y el OCR del repo termina el 2026-09-14 06:42:01.
- Los números de los auditores en los ítems 10, 11 y 12 se reproducen exactos por un camino independiente (loader propio, Planck propio, lectura propia del CSV).

Scripts del segundo tramo, todos en `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s146_auditoria\verificador\`: `v16_figA2.py`, `v16_mascaras_todas.py`, `v16_a2_propio.py`, `v17_clasificacion.py` (lo dejó a medias el primer tramo; corrió sin cambios), `v17b_no_reference.py`, `v17c_mutaciones.py` (ojo con M5, ver su encabezado), `v10_d13.py`, `v11_d20.py`, `v12_a99.py`. No se modificó ningún archivo existente fuera de este informe.
