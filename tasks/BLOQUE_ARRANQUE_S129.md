# Bloque de arranque S129

## Prompt para pegar al inicio de la sesión

```
Continuamos VRP Chile desde S128. Esa sesión estrenó el eje exógeno —el archivo de
GeoTIFF de MIROVA y los papers leídos verbatim— y reabrió una divergencia que cuatro
documentos daban por cerrada.

Leé en este orden:
  1. docs/AUDIT_S128.md              (el informe: 3 hallazgos nuevos, 21 de 28 pendientes cerrados)
  2. docs/s128/                      (los informes de lectura de papers, uno por racimo)
  3. docs/MIROVA_DIVERGENCES.md      (catálogo vivo; el GAP #A volvió a estar abierto)
  4. tasks/BLOQUE_ARRANQUE_S129.md   (esto)

═══════════════════════════════════════════════════════════════════════════
LO QUE S128 DEJÓ LISTO PARA DECIDIR
═══════════════════════════════════════════════════════════════════════════

**1 · El GAP #A no era un mislabel. Está abierto, y es el candidato más directo
para D12** (los ~70 de 79 falsos negativos de MODIS en Láscar).

Coppola 2016a manda calcular μ y σ del fondo sobre los píxeles *suitable*, y define
como no-suitable a los que ya dispararon el Test 1 —que son, por construcción, los más
calientes de la escena—. Hoy esos píxeles **sí entran** al fondo: inflan μ y σ, suben el
umbral `μ + C2·σ`, y la detección queda menos sensible. El error va hacia el falso
negativo.

El cierre de S115 se apoyaba en dos afirmaciones y **las dos son falsas**, verificadas
contra el código y contra el paper:
  · «ya cubierto por el second-run» — el second-run recibe `hot_mask_2d = fp_hot`,
    sólo Tests 2∧3; los K1 nunca entran;
  · «el flag controla el reporte, no el pool» — al revés: decide si `nti_path_hot` se
    pasa como `test1_mask`, y adentro `unsuitable = unsuitable | test1_mask`, que ES
    el pool. Es A89: se lo juzgó por el nombre.

**El A/B está pedido y no corrido**: encender `ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK`
con reproceso real, criterio pre-registrado, midiendo **recall** (la dirección esperada
es ganar detecciones) y magnitud. Ciclo A45 completo — tag defensivo y confirmación de
Nicolás antes de tocar `pipeline/`.

Guard: `tests/test_guard_gap_a_pool_musigma_s128.py` (5 tests). **Falla si alguien
vuelve a cerrarlo con prosa.** No lo borres: actualizalo con la medición.

**2 · El ángulo de vista explica parte del gap de magnitud.** Medido, n=1.046:
VIIRS375 pasa de 0,796 cerca del nadir a 0,570 entre 35° y 50°, con IC que no se
solapan. MIROVA **descarta** esas pasadas (Massimetti, tesis: «Zenith scanning angle
< 50°» en cap. 4, «Zenith > 40°» en cap. 3) y nosotros no descartamos ninguna, aunque
sí tomamos el área nadir fija que su remuestreo justifica.

**Y Coppola 2014 —conseguido en S128— da el mecanismo, que cambia el fix.** Su §2.2:
*«high scan angles contribute to the growth of the projected ground spatial element (up
to approximately 10 km² for scan angles of 55°). This leads the radiance of a potential
sub-pixel hot-spot to be integrated over a variable area»*, y la solución: *«one hot-spot
pixel, whose area is 2 km² in the original image, becomes **two pixels** with equal areas
of 1 km² in the resampled image»*.

El remuestreo **parte** el píxel elongado en varias celdas de área nominal: la energía se
conserva porque crece el NÚMERO de celdas. Por eso Campus 2022 usa `A_pix` constante.
**Nosotros tomamos el área constante y no remuestreamos** (`ENABLE_UTM_REGRID = False`),
así que perdemos la multiplicidad — y la pérdida es el factor de elongación.

⚠️ **D17 y el gap de magnitud son el mismo problema.** El regrid a malla fija es lo que
`ENABLE_UTM_REGRID` y `geo_utils.get_grid_center()` (escrita en S98, sin llamador) existen
para hacer.

**El orden correcto**: (1) A/B del regrid con la paridad **estratificada por cenit** — la
predicción falsable es que el gradiente 0,796 → 0,570 se aplane; (2) sólo si queda
residuo, evaluar el filtro de cenit. Y el caveat del filtro sigue en pie: está en los
análisis de investigación de Massimetti, no en una descripción del producto NRT.

**3 · El ROI1 del paper es una CAJA de 5 km, no un círculo de 3-20 km.** *«the inner
region (ROI1) consists of a box (5 × 5 km) centred on the volcano's summit»*, igual para
todos. En PCC (r=20 km) nuestro ROI1 es ~50× el del paper, así que media escena hereda
los umbrales laxos de *summit*. **Es el eje geométrico que A82 nunca auditó**, y por el
que S124 la rebajó.

═══════════════════════════════════════════════════════════════════════════
LO QUE CAMBIÓ DE VALOR (no volver a citar los números viejos)
═══════════════════════════════════════════════════════════════════════════

  · **D2 medida por primera vez en 127 sesiones**: la cobertura del CSV es **79,2 %**
    global (MODIS 85,2 · VIIRS750 77,9 · **VIIRS375 75,7**), no «~70 % en VIIRS». Y es
    **cota superior**: el archivo de TIF también es un poller.
  · **D5 tenía el número y el signo invertido**: el ratio de hoy es **0,73**
    IC[0,704–0,767] sobre n=1.055. 1/0,73 = 1,37. **Sub-reportamos**, no sobre-reportamos.
  · **A12 REFUTADA**: Isluga da ΔT = 8,3 K, no ~20. **Ningún volcán supera 17 K** en
    ningún sensor, así que con sus propios umbrales la regla clasificaría 9 de 11 como
    «necesita kernel-bg» y ninguno como «ya calibrado». Inutilizable como está escrita.
  · **D9 REFUTADO, y la lectura se invierte**: el residuo «24-83×» era pre-nadir-fijo.
    Hoy el path D puro da 0,28–1,02, y en **10 de 11 volcanes está MÁS CERCA de la
    paridad que los demás paths**.
  · **`.git` son 10,6 GB**, no 3,1 — con 1,57 GiB de basura suelta y 33 packs. El disco
    al 98 % lo llena `.git`, no `data/` (que es 1,03 GB).
  · **Cobertura bibliográfica 65,7 %** (46/70), no el 54 % de S13.
  · **La lista canónica de MISSION.md tiene 11 papers, no 12**: «Coppola 2015» y
    «Coppola 2016a SP426.5» son el mismo.
  · **El argumento que reencuadraba el piso VRP se cayó.** Coppola 2014 —conseguido en
    S128— **no menciona 0,1 MW**; sus puntos de inflexión están en 1, 10, 100 y 1000 MW.
    Evaluó un corte en **2 MW**, midió que costaba bajar el acierto de ~79 % a <59 %, y lo
    **rechazó**: *«we preferred to keep some false alerts than missing several real
    hot-spots»* (p. 3413). Y del régimen sub-MW dice que *«in 75% of cases … represents a
    genuine hot-spot»* (pp. 3417-18) — **corrobora A54 desde la fuente primaria**.
    La recomendación de S126 sobre el piso (quitarlo, no aplicarlo a `pc.vrp_mw`) queda
    respaldada por el canon, no sólo por nuestros datos.
    ⚠️ **Y una precisión sobre el piso, que S128 tuvo que corregirse a sí misma**: decir
    que «hoy es un no-op» es engañoso. El piso **corre y está activo** — MODIS 0,05 ·
    VIIRS375 0,02 · VIIRS750 0,15 MW, leídos de `pipeline.profile` — pero pone en cero
    `record["vrp_mw"]`, que es la suma scene-wide, y **no toca `primary_cluster.vrp_mw`**,
    que es lo que el dashboard reporta (A10). O sea: es no-op **para lo que publicamos**,
    y a la vez deja un campo en cero mientras el reportado sigue distinto de cero. Ésa es
    la parte de «además miente». Nuestro artefacto topográfico (0,04-0,06 MW) cae justo
    en el borde del piso de MODIS.
  · **Coppola 2012 §3.2 da un tercer requisito que no teníamos anotado**: el remuestreo es
    el paso **(ii)**, y va **después** del paso (i), la remoción del *bow-tie*. Sobre 25°
    de barrido los barridos de MODIS se solapan, así que **regridear sin de-solapar
    primero duplicaría píxeles calientes**. Los dos pasos van juntos. Para VIIRS el punto
    es discutible —el sensor borra el bow-tie a bordo y nosotros leemos su valor de
    relleno (`FLAG_DNS` incluye 65533 `Bowtie_Deleted`, `process_viirs.py:80`)— pero
    **para MODIS no hacemos ninguno de los dos**. Esto entra al diseño del A/B del regrid:
    el brazo tiene que ser bow-tie + regrid, no regrid solo.

═══════════════════════════════════════════════════════════════════════════
LO QUE NO HAY QUE REABRIR (anti-A8)
═══════════════════════════════════════════════════════════════════════════

  · **El archivo público de TIF no adjudica detección ni magnitud.** Trae una sola
    banda (MIR) y no TIR, así que el NTI no se reconstruye. La sonda que lo intentó se
    refutó sola: en el **85 %** de las pasadas donde MIROVA declaró ALERTA, su propio
    GeoTIFF no muestra realce al cráter con un índice sobre MIR absoluto. Sirve para
    geometría de grilla, para cobertura, y para ilustrar A69. Extiende A24.
  · **El área nadir fija está respaldada por la fuente primaria**: el `A_pix = 0,5625`
    de la Eq. 1 de Campus 2022 es exactamente nuestro `k` de VIIRS M-band. S102/S103
    acertó.
  · **La grilla de MIROVA está centrada en la cumbre**, no anclada a una esquina. El
    patrón de esquina compartida que se ve en los TIF es artefacto de la reproyección a
    EPSG:4326.
  · **Publicar por pasada y con la máscara de nube apagada está validado por el canon**:
    Coppola dice que las series se entregan *«as they are»*, y Campus 2022 prueba
    explícitamente el modo NRT *«without applying image inspections or filters that
    discard cloudy scenes»*. El máximo diario de Laiolo 2026 es para integrar volumen
    sobre TADR, **no es el producto publicado**. Si se usa, va en la auditoría de
    paridad, no en el pipeline.

═══════════════════════════════════════════════════════════════════════════
PENDIENTES QUE SON LA PUERTA DE ENTRADA (regla C)
═══════════════════════════════════════════════════════════════════════════

  1. **A/B del GAP #A** — el de mayor valor. Ciclo A45.
  2. **A/B del regrid** (`ENABLE_UTM_REGRID` ON) con la paridad estratificada por cenit.
     Es el fix fiel del gap de magnitud y cierra D17 al mismo tiempo. El filtro de cenit
     va DESPUÉS, y sólo si queda residuo.
  3. **El ROI1 caja-vs-círculo** — eje geométrico sin auditar.
  4. **A54 sigue sin respaldo reproducible** (el 95,4 % de FP físicamente reales). Para
     cerrarla hay que re-etiquetar una muestra estratificada con criterio explícito y
     **persistir la etiqueta en el record**. Hoy no hay etiqueta en el schema.
  5. **D13** — necesita que se declare el denominador antes de medir nada.
  6. **Inyección de comandos en 7 workflows, 31 ocurrencias** (`nrt.yml` entre ellos).
     Fix mecánico: pasar por `env:` y citar la variable.
  7. **`nrt-retry.yml` sin `timeout-minutes`.**
  8. **`mirova_center_lat/lon` es por volcán y debería ser por volcán×sensor** — el
     residuo es de 180-310 m, casi un píxel de VIIRS375. Y los offsets de kilómetros de
     **Tupungatito (2,8 km al S)** y **Planchón-Peteroa (1,9 km al N)** contra nuestro
     `volcano_lat/lon`.
  9. **La saturación de M15**: usamos 423 K «por analogía con I05»; Campus 2022 Tabla 1
     da 343 K. Resolver contra el VIIRS L1B UserGuide, que manda sobre el paper (A35).
 10. **Schema**: el JSON no persiste qué píxeles del `anomaly_pixels` pertenecen al
     `primary_cluster`. Eso hace que el invariante de la corona (S127) no sea auditable
     desde el dato publicado. Familia A46.

═══════════════════════════════════════════════════════════════════════════
DECISIONES QUE ESPERAN A NICOLÁS
═══════════════════════════════════════════════════════════════════════════

  ✅ **El `git gc` ya se corrió en S128** (autorizado): 33 packs → 1, 7,38 → 5,99 GiB,
     basura 1,57 GiB → 0. Recuperó **8 GB**; el disco pasó de 98 % a **96 %** (21 GB
     libres). `git fsck` limpio, 91 tags y todas las ramas intactos. No re-correrlo por
     rutina.

  1. **Los duplicados de `documentacion/`**: 101,9 MB en 8 grupos byte-idénticos. Ojo:
     ese directorio está **gitignoreado**, así que pesan sólo en disco local. El candidato
     serio si hace falta espacio es `978-3-031-86841-2.pdf` (93 MB, del que sólo usamos
     un capítulo ya extraído). Borrar exige A38 (inventario + tag + confirmación).
  2. **Los 6 papers conseguidos en S128 NO están en git**, por el mismo gitignore:
     Coppola 2014 y 2012, **Wright 2002** (el origen del NTI), Schroeder 2014, Li 2018 y
     el ATBD VIIRS 375 m. Viven sólo en el disco de Nicolás. Si se quiere respaldo, es
     una decisión aparte.
  3. **Los ~466 MB de `experiments/_s104_roi_probe/`** siguen sin trackear. `experiments/`
     completo son 1.428 MB, no los 458 que decía S121.
  4. **Quedó un racimo de la Fase 3 sin cubrir**: el agente de Aveni et al. 2023 (FY-3D
     MERSI-II) murió dos veces por límite de sesión y no dejó informe. Es el precedente
     de cómo el propio grupo MIROVA calibra un sensor nuevo — el molde de lo que
     hacemos. `documentacion/The_Capabilities_of_FY-3DMERSI-II_Sensor_to_Detect.pdf`.

═══════════════════════════════════════════════════════════════════════════
REGLAS DE ESTA ETAPA
═══════════════════════════════════════════════════════════════════════════

  · **A89 sigue siendo el patrón dominante, y ahora tiene una forma nueva: el flag mal
    nombrado.** En S128 apareció cuatro veces — tres del auditor, y la cuarta es la que
    produjo el cierre falso del GAP #A. Antes de escribir «esto no se usa» o «esto está
    cerrado», trazá **cómo lo lee el código**, no cómo se llama.
  · **Toda sonda que produzca un veredicto sobre nosotros necesita un control de
    instrumento**: medir primero si el instrumento distingue a MIROVA de sí misma. En
    S128 eso salvó de publicar «257 falsos positivos» que no existían. Costó veinte
    minutos.
  · Verificar flags leyendo `pipeline.profile`, NUNCA el YAML.
  · Estratificar por volcán, no sólo por sensor. Un par por noche, máximo de ambos lados.
  · Helpers comunes en `experiments/_s126_lib.py`. Reusarlo.
  · Todo número sale de un script que lo persiste (S91).
```

---

## Estado al cerrar S128

**Suite**: 1003 tests verdes (998 + 5 guards nuevos). **NRT**: sano. **Operacional
intacto**: no se tocó `pipeline/` ni ningún perfil. La auditoría fue read-only sobre el
código; lo único que se editó son documentos, tests y `experiments/`.

### Lo que quedó PROBADO

| hallazgo | cómo se probó |
|---|---|
| **El GAP #A está abierto** | cadena de 3 saltos verificada: `process_modis.py:791-793` → `first_pass_tests_2_and_3(test1_mask=)` → `unsuitable \| test1_mask`; flag `False` leído de `pipeline.profile` |
| Las dos patas del cierre de S115 son falsas | el second-run recibe `hot_mask_2d = fp_hot` (sólo Tests 2∧3); el flag gobierna el pool, no el reporte |
| **El sub-reporte crece con el cenit** | n=1.046 pares; VIIRS375 0,796 → 0,570, IC sin solape |
| **D2 = 79,2 %** | 1.960 pasadas del archivo de TIF como denominador, primera vez que existe |
| **D5 tiene el signo invertido** | ratio 0,73 IC[0,704–0,767], n=1.055 |
| **A12 refutada** | ΔT medido en los 11 × 3 sensores; ninguno supera 17 K |
| **D9 refutado** | path D puro 0,28–1,02, y más cerca de la paridad que los otros paths en 10 de 11 |
| **El TIF no adjudica detección** | control de instrumento: 85 % de las ALERTAS de MIROVA no pasan su propio corte |
| La grilla es fija y centrada en la cumbre | dispersión 0,0 m en 4 bordes × 33 pares; Campus 2022 p. 7 verbatim |
| `.git` = 10,6 GB con 1,57 GiB de basura | `git count-objects -v` |
| 7 workflows con inyección de inputs | 31 ocurrencias, parseo de bloques `run:` |

### Guards nuevos

`tests/test_guard_gap_a_pool_musigma_s128.py` — cinco tests: el cableado del flag, que
el second-run no cubre el retiro, que `nti_path_hot` es el Test 1, que **la
documentación no puede volver a cerrarlo con prosa** (acepta el texto tachado, prohíbe
la afirmación vigente), y el mecanismo aritmético que fija la dirección del error.

### Divergencias que cambiaron de estado

- **GAP #A · REABIERTO** con guard. Tres frases corregidas en `MIROVA_DIVERGENCES.md` y
  `AUDIT_S114_PARITY_BY_SENSOR.md` (tachadas, no borradas).
- **D2 · MEDIDA** por primera vez.
- **D5 · el número era correcto y el signo estaba invertido.**
- **D9 · residuo REFUTADO** post nadir-fijo.
- **D14 · CONFIRMADA**, ahora con A/B pareado e IC en vez de una correlación sin script.
  Matiz nuevo: la máscara no es el driver, pero aporta 9-18 % en VIIRS375 (cerca de un
  tercio del gap en Láscar), no cero.
- **D17 · el contenido real es otro**: no es que no repliquemos la grilla —está centrada
  en la cumbre, como hacemos— sino que `mirova_center` es por volcán cuando debería ser
  por volcán×sensor, y que Tupungatito y PP tienen offsets de kilómetros.

### El patrón que ordena la sesión

**El eje exógeno rindió, pero no donde se esperaba.** La sonda diseñada para ser la más
filosa se cayó en su propio control; las dos «de infraestructura» cerraron una
divergencia y midieron una creencia de 127 sesiones; y los dos hallazgos que más rinden
—el ángulo de vista y el GAP #A— salieron del **cruce** entre un paper leído verbatim y
código o datos que ya estaban ahí. El Lote C del diseño de S128 («leer no sirve si no se
cruza») era la parte correcta, y el Lote B (descargar lo que falta) fue el que menos
rindió.
