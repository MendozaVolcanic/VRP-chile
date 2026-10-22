# Plan de auditoría S160: los instrumentos, las unidades, lo que vence y los cierres con número

> **Estado: APROBADO y revisado antes del sello (2026-10-22, §11).** Lo que cambió respecto del borrador está en el
> §11 y manda sobre el texto de arriba donde choquen. Borrador original: escrito el 2026-10-21 (S159) para que Nicolás lo apruebe. Es la primera auditoría
> diseñada con la guía nueva `C:\Users\nmend\OneDrive\Escritorio\claude\GUIA_MAESTRA_AUDITORIAS.md` (442 líneas; el
> commit `31b70f1` del repo `workspace-guias` lo da el coordinador, no lo comprobé) y su plantilla
> `C:\Users\nmend\OneDrive\Escritorio\claude\PLANTILLA_CAZA_DE_BRECHAS.md`. El §10 lista lo que la guía no me dio y
> tuve que decidir yo: es parte del entregable, porque esta auditoría también pone a prueba la guía.
>
> Leído entero en esta sesión: la guía, la plantilla, `CLAUDE.md` del proyecto, `docs/PROTOCOLO_AUDITORIA_PROFUNDA.md`,
> las dos copias de `docs/_prompts/PREAMBULO-AUDITOR.md`, `experiments/_s159/guia_auditorias/C_INTEGRACION.md`,
> `docs/PLAN_AUDITORIA_S158.md`, `docs/AUDIT_S158.md`, `docs/AUDIT_S158_R2.md`. De los informes de hoy
> (`C:\vrp-trabajo\s159-pruebas\experiments\_s159\`) leí sólo el encabezado y el resumen de cada uno, y dos tramos de
> `B_PROMPTING.md` (M5 y M6). Todo lo que este plan dice de un archivo que no está en esa lista va marcado SOSPECHA o
> «según» con su fuente.

## 0. En una pantalla

1. **Cuatro frentes de auditoría, tres con eje nuevo** (regla A del protocolo): F1 los instrumentos de decisión (todos
   los pre-registros y evaluadores sellados, contra las 15 filas del §3b de la guía), F2 unidades y magnitudes (frente
   L de la guía, nunca corrido en el proyecto), F3 dependencias externas con fecha de vencimiento, y F4 los cierres y
   reglas con número escritos **desde S146** (no es eje nuevo: se justifica por la regla C y se limita al delta).
2. **Dos verificaciones de pendientes antes que nada** (regla C): F0a y F0b verifican los 16 hallazgos de gravedad 1
   y 2 de S158 que nadie verificó; los demás pendientes van al frente cuyo eje les toca.
3. **Diez subagentes** (6 auditores o verificadores de pendientes, 4 verificadores con contexto limpio) y la síntesis
   del orquestador, en tres olas de no más de cuatro agentes a la vez. Unas 16 horas-agente y 6 a 7 horas de reloj
   (estimación sin base medida, §8). **Cero workflows despachados, cero descargas de L1B, cero worktrees nuevos.**
4. **Cada frente trae su propia línea base roja**: los defectos de instrumento que ya se encontraron hoy (el placebo de
   D25, el gemelo identidad, el +104 ponderado, el contrafactual a una etapa, «Cobertura: completa» con Suomi NPP
   vacío) son el control positivo que el barrido de cada frente tiene que volver a encontrar con su propio
   instrumento. Si no los ve, su cero no vale.
5. **Lo urgente no espera a esta auditoría**: Suomi NPP deja de entregar el 2026-11-02 13:00 UTC (según
   `experiments/_s159/biblio_2026/INFORME.md` §0), en doce días. F3 mide cómo falla todo lo que vence; la decisión de
   qué hacer con Suomi NPP es de Nicolás y conviene tomarla antes de lanzar (§9, decisión 1).

## 1. Puerta de entrada: los pendientes de S158 (regla C)

`docs/PROTOCOLO_AUDITORIA_PROFUNDA.md` l. 274 a 276: la auditoría siguiente «**empieza** por los pendientes antes de
abrir eje nuevo». Los de S158, según lo que leí:

| pendiente | dónde está | a qué frente va | por qué ahí |
|---|---|---|---|
| F5-03 a F5-07 de la primera ronda (SN, negativo limpio con tres caminos a 0,0, `libro_de_cuentas.py` fuera de banda, halo, filtros de artefacto sin sustrato) | `experiments/_s158_audit/f5/INFORME.md` l. 106 a 195 | F1 | son defectos de instrumento: el mismo eje |
| F2-H3 a F2-H9 (grafo de cierres) y las marcas U1 a U4 y U8 a U13 del meta-auditor | `docs/AUDIT_S158.md` l. 76; `docs/AUDIT_S158_R2.md` l. 276 a 277 | F4 | cierres y propagación |
| F1-H4, H6, H8, H9 y F6-3 a F6-8 (encontrados por agentes Opus, según `docs/PLAN_AUDITORIA_S158.md` l. 201 a 203) | `docs/AUDIT_S158.md` l. 76 | F0a (Fable) | el verificador es el otro modelo del que encontró (guía §5, tabla) |
| F4-H2, H3, H5, H7, H8 (encontrados por Fable) y R2-17 (las tres vistas del tablero; quién lo encontró: SOSPECHA) | `docs/AUDIT_S158.md` l. 76; `docs/AUDIT_S158_R2.md` l. 169 | F0b (Opus) | ídem |
| R2-16 (411 pasadas del OSF sin record) | `docs/AUDIT_S158_R2.md` l. 168 | ninguno | ya medido hoy: `experiments/_s159/cob/INFORME.md` §0 lo explica (357 anteriores a la serie, 53 diurnas, 1 que NASA no sirve) |
| el «1 SIN EVIDENCIA» de los 50 cierres del censo S145 | `CLAUDE.md`, A113 | F4 | cierres |

Antes de verificar nada, F0a y F0b buscan cada ID en los informes de hoy (`grep -rn "<ID>"
C:\vrp-trabajo\s159-pruebas\experiments\_s159\`): lo que S159 ya resolvió se cita como resuelto y no se rehace.

## 2. Los ejes, con su porqué

| eje | frente | ¿lo usó alguna auditoría? | por qué ahora |
|---|---|---|---|
| instrumentos de decisión contra el §3b de la guía | F1 | no como barrido: cada defecto de instrumento se encontró de a uno, casi siempre por un verificador | en un día, dos verificadores encontraron cinco formas distintas de instrumento que no podía fallar (placebo que aprueba, gemelo que es identidad, población condicionada, estimador ponderado donde se podía censar, contrafactual que llega a un consumidor de dos). Las decisiones en producción (K, S153) y los «NO ADOPTAR» que cerraron frentes salieron de instrumentos de la misma familia y nadie los barrió |
| unidades y espacio de definición de cada constante | F2 | no (0 archivos, según el coordinador; el registro de ejes del protocolo, l. 282 a 299, no lo lista) | el ejemplo ya medido: un mínimo de 0,02 en las unidades del código de MIROVA vale 0,0225 en las nuestras, que promedian 8 vecinos (guía §4, frente L). Se encontró por accidente en S158. Si hay uno, el censo dice cuántos más |
| dependencias externas con fecha de vencimiento | F3 | no (no está en el registro de ejes) | Suomi NPP cesa en doce días y la simulación de hoy dice «Cobertura: completa» y código de salida 0 con Suomi NPP vacío (`experiments/_s159/cese_snpp/simular_snpp_vacio_salida.txt`). Es un vigilante ciego de manual (guía §3, «un vigilante ciego no da error, da verde») |
| cierres y reglas con número sin script | F4 | sí: censo S145 y auditoría S146 (89 cierres) | **no estrena eje**; entra porque es el objeto de mayor rendimiento (guía §2 regla 13) y porque desde S146 se escribieron al menos las reglas A114 a A119, la divergencia D34 y varias decisiones D (D-4, D-9, D-27,
según `CLAUDE.md` y `docs/AUDIT_S158_R2.md`) sin que nadie las barriera. Se limita al delta desde el commit de `docs/AUDIT_S146.md` (`61cc94e3a`, 2026-09-20) |

Tres de cuatro frentes con eje nuevo: sobre el 50 % que la regla de rendimiento (guía §4; protocolo l. 228 a 244)
asocia a las auditorías que movieron el pipeline.

**Ejes que la guía sugiere y este plan no corre** (§9, decisión 3): el frente **por uso** (promesa, supuesto y
control de cada etiqueta del tablero; la guía §8 paso 2 dice que «casi siempre» aplica, y V3-1 de S158 ya mostró una
etiqueta que miente: «Distancia al cráter» mide desde el centro) y el frente **M de prueba de campo** (VRP no tiene una
cola de validación en campo persistente: C_INTEGRACION §2). Propongo que la síntesis abra esa cola (§7) en vez de
gastar un frente en ella. El de uso queda como F5 opcional si Nicolás lo pide.

## 3. Los frentes

Formato de cada uno: hipótesis, qué la refutaría, insumos, salida, criterio, pendientes de entrada, modelo y esfuerzo,
carpeta. Los seis corren **desatendidos** (subagentes; Nicolás no contesta a mitad de camino), así que todos llevan el
bloque de autonomía de la guía §5 con las paradas de auditoría.

Carpetas: `C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\<frente>\` (scripts, salidas, informe) y, para lo
pesado, `D:\vrp-trabajo\temporales\s160_audit\<frente>\` (fuera del repo).

### F1. Los instrumentos de decisión (el frente más difícil)

- **Hipótesis H1.** Al menos un instrumento cuyo veredicto está hoy en producción, o que cerró un frente que sigue
  cerrado, falla una de las filas del criterio de abajo; es decir, habría dado el mismo veredicto con un efecto nulo o
  con un placebo. **H1b.** Una parte de esos fallos son el mismo fallo, heredado de `scripts/banco_paridad.py`, que
  usan 7 de los 16 evaluadores (`find experiments scripts -iname "evaluar*.py" | xargs grep -l banco_paridad`, corrido
  hoy): son una sola medición repetida (plantilla, regla 8c).
- **Lo que la refutaría.** Que cada instrumento de la prioridad A y B rechace los tres placebos, que su nulo dé
  distinto de cero por construcción y del tamaño del ruido real, y que su población, ventana y tolerancia pasen las
  filas del criterio. Y que `banco_paridad` reimplementado de forma independiente dé las mismas etiquetas.
- **Insumos** (inventario hecho hoy con `find`; el auditor lo completa y declara su comando):
  - prioridad A, veredicto en producción: `experiments/_s151_prereg_fk_11/` (`PREREGISTRO.md`, `REGLA_ADOPCION.md`,
    `evaluar_fk.py`), la regla con que se adoptó K en S153 (`CLAUDE.md`, marca S153).
  - prioridad B, cierres y adopciones: `docs/PREREGISTRO_AB_D1_D2_S135.md`, `docs/PREREGISTRO_AB_D22_D25_S143.md`,
    `docs/PREREGISTRO_KEEP_PEAK_DIRECCION_S144.md` (y sus 7 verificadores), `docs/PREREGISTRO_CONFORMIDAD_A6_S136.md`,
    `docs/PREREGISTRO_PROBE_S136_TEST1_CONTEXTUAL.md`, `docs/S125_AB_MAGNITUD_PREREGISTRO.md`,
    `docs/S126_CORONA_PREREGISTRO.md`, `docs/s129/PREREGISTRO_AB_FONDOS.md`, `docs/s130/PREREGISTRO_AB_D18.md`, y en
    `experiments/`: `_s135_ab_d1d2`, `_s136`, `_s143_preregistro`, `_s143_evaluador`, `_s146_ab_sin_test1`,
    `_s146_bateria`, `_s146_a2`, `_s147_ab_conectiva`, `_s149_prereg_invierno`, `_s150_ab_d22`, `_s150_ndc`,
    `_s151_ab_diurno`, `_s151_ab_vrp_max`, `_s151_prereg_caja`, `_s151_presupuesto_magnitud`, `_s151_mxd03_*`,
    `_s151_saturacion_chillan`. Qué decidió cada uno: lo establece el auditor (no lo leí).
  - prioridad C, ya revisados hoy, sólo como control: `experiments/_s157_prereg_d25/`, `experiments/_s159/n/`,
    `experiments/_s159/m/`, `experiments/_s159/chillan_modis/`, `experiments/_s159/mxd03_prereg/`,
    `experiments/_s159/gemelo_d25/`.
  - compartidos: `scripts/banco_paridad.py` (`TOL_S = 120` en l. 76, `correr_node` l. 141, `etiquetar` l. 300),
    `scripts/clase_mirova.py`, `scripts/calidad_referencia_mirova.py`, `scripts/libro_de_cuentas.py`, el auto-audit
    (ubicación: la encuentra el auditor).
  - datos de los brazos: en las ramas `origin/s146-ab/<run>` (según `experiments/_s159/gemelo_d25/INFORME.md`), que
    se extraen **por ruta** con `git show` a `D:\vrp-trabajo\temporales\s160_audit\f1\`, nunca con `checkout` ni
    `pull`.
- **Criterio (pre-registrado: queda fijo al commitear este plan).** Una matriz instrumento por fila, con OK, FALLA,
  NO APLICA o SIN DATO en cada celda. Las filas son las 15 del §3b de la guía más dos:

  | fila | FALLA cuando |
  |---|---|
  | R1 pre-registro | el commit del pre-registro no precede al primer dato, o el criterio cambió después sin rótulo *post hoc* (`git log` del archivo contra la fecha del run) |
  | R2 cobertura | borrar un día de un brazo (copia en CARPETA) no cambia el veredicto a SIN DATO o a falla |
  | R3 censo antes de ponderar | el subconjunto donde el cambio puede actuar es contable y el instrumento muestrea o pondera; o el estimador supera su techo físico |
  | R4 población | se eligió por lo que el sistema publica y se leyó sin vara externa; o se midió contra un producto del mismo gránulo |
  | R5 nulo | el nulo corre el mismo código en el mismo proceso (identidad), o da cero exacto sin mostrar que podía dar distinto de cero |
  | R6 placebo | con la salida del propio control multiplicada por 1,10, por 1,2 y desplazada sin información, el instrumento da el veredicto que aprueba en alguno de los tres |
  | R7 poder | barajando las etiquetas dentro de cada estrato (200 barajados o más, semilla sellada en el informe antes de correr), el criterio «cumple» en más del 5 % de los barajados (umbral mío, §10 punto 9) |
  | R8 contrafactual | el valor que cambia tiene un consumidor (por `grep`) al que el brazo no llega y nadie lo declaró |
  | R9 saturación | el A/B se midió con un camino saturante encendido (por ejemplo el Test 1 integrado, A114) o la métrica casi no varía entre dos estratos físicos |
  | R10 régimen | la ventana cruza un cambio de régimen fechado en los datos (#535 el 2026-08-28 23:00 UTC, A104; el reproceso con K, R2-12) sin medir por tramo |
  | R11 tolerancia | la tolerancia, en unidades del veredicto, es mayor que el efecto que decidió |
  | R12 oportunidades | una unidad con dos registros cuenta si cuenta cualquiera, en un brazo y no en el otro |
  | R13 distribución | el veredicto sale de un agregado y dentro de algún estrato el signo se invierte |
  | R14 referencia | la ventana pisa un hito de `scripts/calidad_referencia_mirova.py` sin separarlo, o el instrumento lee la referencia viva y no una copia con hash (la tabla pierde filas y el OCR reescribe alertas: `experiments/_s159/referencia_estable/`) |
  | R15 umbral | un umbral del criterio se eligió sin preguntarle a la referencia (informativo, no FALLA, salvo que decida) |
  | R16 nombre del veredicto | el nombre promete más de lo que la regla prueba (guía §3, «CUMPLE» que pasó a «CUMPLE SIN DAÑO») |
  | R17 insumo compartido | el instrumento hereda un defecto medido en `banco_paridad`, `clase_mirova` o el predicado del tablero |

  Medición profunda (placebo, barajado, borrado de un día) obligatoria para la prioridad A y para todo instrumento de
  la B que tenga evaluador en código; los pre-registros que son sólo documento se clasifican leyendo, con SIN DATO
  donde no se pudo medir. Cobertura primero: la matriz lleva **todos** los instrumentos del inventario, aunque sea con
  SIN DATO.
- **Control positivo del barrido** (su línea base roja): con su propio instrumento, el auditor tiene que volver a
  encontrar (a) el placebo de D25 que aprueba (R6; `docs/AUDIT_S158_R2.md` §1 fila 9), (b) el gemelo de D25 que es
  identidad (R5; `experiments/_s159/gemelo_d25/`), (c) el +104 ponderado contra +12 del censo (R3;
  `experiments/_s159/n/INFORME.md` §1, primera viñeta), (d) la caja que llegó al primer pase y no al segundo (R8; A118).
  Si una de las cuatro no sale, su fila no vale para el resto de la matriz y se dice.
- **Gravedad** (guía §6 paso 1: en la unidad en que el usuario vive el efecto, que para un instrumento es la decisión
  que torció): 5 si el instrumento sostiene una decisión en producción; 4 si cerró un frente que sigue cerrado; 3 si
  sostiene un A/B pendiente; 2 si es exploratorio; 1 de forma.
- **Salida.** `INFORME.md`, `matriz_instrumentos.csv` (instrumento, ruta, decisión que sostiene, R1 a R17, script de
  cada celda medida), `hallazgos.csv`, y la reimplementación independiente de `etiquetar` con su comparación.
- **Modelo y esfuerzo.** Fable a `high`. Es semántica (decidir si un instrumento puede fallar) más censo; la guía
  reserva `xhigh` para «el frente más difícil», y lo es, pero el entregable es largo y a `xhigh` se redacta dos veces
  (guía §5, tabla): elijo `high` y lo dejo registrado para comparar. Presupuesto: unas 3 horas.
- **Carpeta.** `C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\f1\`; datos en `D:\vrp-trabajo\temporales\s160_audit\f1\`
  (tope 2 GB). IDs provisionales 161 a 199.

### F2. Unidades y magnitudes (frente L)

- **Hipótesis H2.** Fuera de los casos ya conocidos, hay al menos una constante que se aplica en un espacio distinto
  del que la define: otra unidad (W contra MW, m² contra km², K contra °C), otro nivel de agregación (píxel, media de 8
  vecinos, 3 × 3 con el central, cúmulo, ROI, escena, pasada, noche), otro punto de referencia (centro del volcán
  contra cráter, A3) u otro sensor (un número de MODIS usado en VIIRS sin marca). Y al menos un recorte (`np.maximum`,
  `np.clip`, `min`) que se come el rango real en Chile.
- **Lo que la refutaría.** Un censo completo, con su control positivo encontrado entero, en que cada constante tiene
  unidad, espacio de definición, espacio de aplicación y fuente, y ninguna discrepa fuera de la lista conocida.
- **Instrumento.** Uno propio. El de la guía (`C:\Users\nmend\OneDrive\Escritorio\claude\ARSAND\tools\auditoria\censo-magnitudes.py`)
  **no sirve aquí**, leído hoy: sólo reconoce decimales con punto (`NUM = r'-?\d+\.\d+f?'`), así que no ve `5`, `25`
  ni `1e6`; no lee `.yaml`, donde viven los umbrales del perfil; su vocabulario de unidades es el de la AR Sandbox (cm,
  fauna, batimetría); y su control positivo busca `CreatureSystem.cpp` y `ModeManager.cpp`, así que en este repo sale
  siempre con código 2. El censo de F2 recorre el AST de `pipeline/*.py` y `scripts/*.py` (constantes en
  comparaciones, asignaciones, argumentos por defecto y respaldos), los **valores efectivos** del perfil leídos desde
  `pipeline.profile` con `VRP_PROFILE=mirova_equivalent` (técnica T2: nunca el YAML a mano), y los umbrales de
  `frontend/index.html`, `diario.html` y `mosaico.html`.
- **Control positivo del censo** (sale con código distinto de 0 si falta uno): `WOOSTER_COEFF` 18.9
  (`pipeline/process_modis.py:87`), 18.0 (`pipeline/process_viirs.py:77`) y 19.7 (`pipeline/process_viirs_mod.py:66`);
  los C1 de 0,003 y 0,010 y los N·σ de 5, 10 y 15 del perfil (según `CLAUDE.md`); el tope de 5 MW de D9; el corte de
  1 MW de protegida y el de 0,05 MW de la regla D-9 (`scripts/clase_mirova.py`, según `CLAUDE.md`); `TOL_S = 120`
  (`scripts/banco_paridad.py:76`); el `inner_radius_km` de cada volcán. Los valores del perfil los tomé de `CLAUDE.md`,
  que describe parte de ellos como estado previo a S153: si el valor efectivo de hoy es otro, el auditor lo documenta y
  usa el efectivo, y eso no es falla del censo. Control negativo: un archivo sin constantes da
  0 filas, y el conteo se compara con un `grep` independiente sobre los mismos archivos.
- **Control positivo del barrido** (los casos ya conocidos, que tiene que volver a clasificar como discrepancia): el
  0,02 contra 0,0225 (S158 F4-H1 y V3); el recorte a cero del fondo (`docs/AUDIT_S158_R2.md` §1 fila 1, que lo ubica en
  `pipeline/process_viirs_mod.py:1056`); el rótulo «Distancia al cráter» que mide desde el centro (V3-1); el tope de
  cordura aplicado antes de normalizar `t_max` (R2-7).
- **Criterio.** Cada constante entra en `censo_magnitudes.csv` con: valor, archivo:línea, unidad declarada, unidad
  inferida, espacio de definición, espacio de aplicación, sensor, fuente (código de MIROVA con línea, paper con
  localizador RENDER, medición con script, o SIN FUENTE) y qué pasa en el rango chileno chico, medio y grande (BT de
  cumbre de unos 250 a 290 K, VRP de 0,01 a 100 MW, cenit de 0 a 70°; el auditor mide los rangos en `data/`, no los
  copia de aquí). Es discrepancia si la unidad o el espacio de aplicación no coinciden con los de definición, o si un
  recorte cambia el resultado en algún rango real. SIN FUENTE no es discrepancia: se cuenta y se publica.
- **Pendientes de entrada.** Ninguno propio; R2-7 y V3-1 entran como control.
- **Salida.** `INFORME.md`, `censo_magnitudes.py` con su `--control`, `censo_magnitudes.csv`, `hallazgos.csv`.
- **Modelo y esfuerzo.** Fable a `high` (censo exhaustivo; guía §5, primera fila). Unas 2 horas. IDs 201 a 239.

### F3. Dependencias externas con fecha de vencimiento

- **Hipótesis H3.** Además de Suomi NPP, al menos una dependencia, si cae, deja al NRT en verde sin producir (pipeline
  zombie), y ninguna de las que tienen fecha conocida de vencimiento avisa antes de vencer.
- **Lo que la refutaría.** Que para cada dependencia una falla simulada sin red (como
  `experiments/_s159/cese_snpp/simular_snpp_vacio.py`) dé código de salida distinto de 0 o un aviso que alguien recibe,
  y que cada fecha de vencimiento tenga un vigilante con umbral medido contra los datos.
- **Inventario mínimo** (el auditor lo completa; la plantilla, ejes P8, P9, B10 y B11, sirve de menú):
  plataformas (Suomi NPP, NOAA-20, NOAA-21, Aqua, Terra); colecciones (MODIS 6.1 con decomiso anunciado y la 7 en
  paralelo, según `experiments/_s159/biblio_2026/INFORME.md` §0; VIIRS v2 y v2.1; Standard contra NRT); servicios (CMR,
  LAADS, LANCE, el host `nrt3.modaps` de A64, GitHub Actions, GitHub Pages, el cron externo de cron-job.org según la
  memoria del proyecto); credenciales (`EARTHDATA_TOKEN` y su rotación de 50 días, según `CLAUDE.md`; sólo metadatos,
  **nunca valores**: `C:\Users\nmend\OneDrive\Escritorio\claude\REGISTRO_CREDENCIALES.md` §2 y la lista de secretos con
  su fecha de actualización); la referencia (mirovaweb.it, el scraper Mirova-v1, la copia horaria
  `.github/workflows/sync-mirova-csv.yml`, una tabla que pierde filas y un OCR que reescribe alertas según
  `experiments/_s159/referencia_estable/`); bibliotecas con comportamiento que cambió (pyhdf, earthaccess, el orden de
  `argsort` según la CPU de S152); el código de MIROVA en OSF (zm62w).
- **Control positivo** (que su simulador tiene que reproducir antes de medir lo demás): Suomi NPP vacío da
  «Cobertura: completa» con código 0, y un timeout da «Cobertura INCOMPLETA» también con código 0
  (`experiments/_s159/cese_snpp/simular_snpp_vacio_salida.txt`); cero gránulos da «completa» (R2-9); un L1B sin su
  geolocalización se descarta en silencio (VB-1).
- **Criterio.** Una tabla dependencia · tipo · fecha de vencimiento (con fuente y fecha de consulta, o SIN FECHA) · qué
  la consume (archivo:línea) · qué se apaga si cae · cómo falla, **medido** con simulación (error, aviso o silencio) ·
  vigilante que existe · umbral del vigilante medido contra datos. Es hallazgo toda dependencia que falle en silencio y
  toda fecha sin vigilante. Se mide sobre `origin/main` y, aparte, sobre la rama de PR #889
  (`origin/s159-instrumentos`, cabeza `d0968e389` al sellar; se lee con `git show`, no tiene worktree propio: el
  worktree `C:\vrp-trabajo\s159-instrumentos` está hoy en la rama `s159-cese-snpp`), porque esa rama dice traer
  arreglos de instrumento que no están mergeados (SOSPECHA hasta leerla). **Revisión del sello, §11**: el arreglo de
  Suomi NPP ya está en curso en la rama `s159-cese-snpp` (otra sesión); F3 lo audita y no propone el mismo arreglo, y
  el código del scraper Mirova-v1 lo audita otra sesión (`audit-mirova-v1`): F3 mide sólo cómo lo consume VRP.
- **Límites propios.** Sin autenticación contra Earthdata desde esta máquina (A71: la cuenta se bloquea). CMR sólo con
  búsquedas públicas, hasta 150 consultas. GitHub, desde el archivo de insumos del orquestador (§5), y hasta 10
  llamadas propias. Ninguna simulación toca `data/`: corre con `data_subdir` en CARPETA o sin escritura.
- **Salida.** `INFORME.md`, `dependencias.csv`, los simuladores con su salida, `hallazgos.csv`.
- **Modelo y esfuerzo.** Fable a `high`; lee avisos web, así que nunca `low` (guía §5). Unas 2 horas. IDs 241 a 279.

### F4. Cierres y reglas con número escritos desde S146

- **Hipótesis H4.** Al menos un cierre o regla vinculante escrito o modificado desde `61cc94e3a` cita un número que
  ningún script de hoy reproduce, y al menos una rebaja de ese período no bajó a los documentos que la citan (A113).
- **Lo que la refutaría.** Que cada número del delta se reproduzca corriendo el script citado (técnica T1) y que cada
  rebaja tenga su marca en todos los hijos encontrados por `grep` del número, la frase y el ID.
- **Insumos.** `git log -p 61cc94e3a..«SHA_MAIN» -- CLAUDE.md docs/MIROVA_DIVERGENCES.md docs/MISSION.md
  docs/META_RULES_S80.md docs/SINTOMAS.md` y la memoria del proyecto (`MEMORY.md` y sus archivos; sólo lectura). Las
  reglas que el coordinador nombra (A83, A84) entran como control: A83 ya está rebajada en S146 por un AUC sin script
  y el barrido tiene que clasificarla así. El censo S145 (`experiments/_s145_censo_cierres/censo.py`) **escribe sobre
  sus propios archivos** (`SALIDA = HERE / "censo_cierres.json"`, l. 48, y el `.md`, l. 219): se copia a CARPETA y se
  corre la copia, para medir cuánto creció el universo desde S145.
- **Criterio.** Cada afirmación sale verificada, en parte, refutada, SIN EVIDENCIA o «no era un cierre» (guía §2 regla
  13), con el comando que lo decide; para cada rebaja, la lista de hijos y si tienen marca. Sin respaldo no es lo mismo
  que refutado.
- **Pendientes de entrada.** F2-H3 a F2-H9 de S158, U1 a U4 y U8 a U13 del meta-auditor, el «1 SIN EVIDENCIA» de S146.
- **Salida.** `INFORME.md`, `cierres_delta.csv`, `propagacion.csv`, `hallazgos.csv`. **No pone marcas**: propone cada
  una con su texto; las pone el orquestador en el PR de la síntesis.
- **Modelo y esfuerzo.** Fable a `high` (censo). Unas 2 horas. IDs 281 a 319.

### F0a y F0b. Verificación de los pendientes sin verificar de S158

Son verificadores, no auditores: reciben la lista de IDs del §1 con su título y ubicación, y nada más. F0a (Fable a
`high`) verifica los que encontró Opus; F0b (Opus a `high`) los que encontró Fable. Prompt: el del verificador del §6
con su lista. Una hora cada uno. IDs propios V0a-01 en adelante y V0b-01 en adelante. Sus veredictos entran a la
síntesis como veredictos de verificador; lo nuevo que encuentren va a la puerta de la auditoría siguiente, con su conteo.

## 4. Verificadores y síntesis

- **Un verificador por frente**: V1 para F1, V2 para F2, V3 para F3, V4 para F4. Todos Opus a `high`, porque los
  cuatro auditores son Fable (guía §5: «el otro modelo del que encontró»). Con Opus no se agrega «revisa tu
  respuesta» (misma tabla).
- **Qué reciben**: título, archivo:línea o script:salida y gravedad de cada hallazgo de gravedad 3 o más, y, en F1,
  **toda celda FALLA** de un instrumento de prioridad A o B sin importar su gravedad (un instrumento roto de gravedad 2
  puede ser el que sostiene una regla). No leen el `INFORME.md` del auditor.
- **Independencia demostrable sin git**: el verificador escribe primero `caminos.md` (los caminos por los que cada
  afirmación podría estar mal) y anota en él su `sha256` y la hora del servidor antes de abrir ningún archivo citado.
  El orquestador guarda ese hash al recibir el informe.
- **Lo que no pasa por el verificador** (gravedad 1 y 2, fuera de F1) se publica con su conteo en la síntesis y es la
  puerta de entrada de S161+.
- **Síntesis**: la escribe el orquestador (Opus), sólo con veredictos de verificador, en `docs/AUDIT_S160.md`:
  confirmados, refutados y pendientes (los tres números de la regla C); por cada confirmado, la guarda que lo cerraría
  y cómo se vería en rojo (regla B del protocolo, guía §6 paso 3); la lista de marcas A113 propuestas por F4; las
  decisiones de Nicolás con recomendación; la cola de campo (§7); y una sección «lo que la guía no dio», que actualiza
  el §10 de este plan con lo que los agentes encontraron. Antes de cerrar, `grep` de cada ID declarado contra la cola y
  contra la tabla final (guía §6 paso 5).

## 5. Dónde corre, y con qué recursos

**El código que se audita es `origin/main`, fijado por hash.** Hoy hay al menos cuatro versiones vivas: `main`, la
rama `loop/activo` en `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile`, la rama `s159-pruebas` en
`C:\vrp-trabajo\s159-pruebas` y la de PR #889. No se crea worktree nuevo (pide unos 25 GB, `docs/PLAN_AUDITORIA_S158.md`
l. 205; hoy había 19 GB libres en C: al empezar este plan y 15 al terminarlo, y 13 en D:: algo más está escribiendo
en C:, y el orquestador lo mira antes de lanzar).

Ola 0, el orquestador, antes de lanzar (unos 30 minutos):
1. Nicolás aprueba; el orquestador commitea este plan y anota su hash como «SHA_PLAN». Los criterios del §3 son el
   pre-registro de la auditoría; cada verificador comprueba con `git diff «SHA_PLAN» -- docs/PLAN_AUDITORIA_S160.md`
   que no cambiaron.
2. `git -C C:\vrp-trabajo\s159-pruebas fetch origin --prune`; anota `git rev-parse origin/main` como «SHA_MAIN».
3. Instantánea del código de hoy, **con rutas** (un `git archive` sin ruta extrae el repo entero, memoria S147):
   `git -C C:\vrp-trabajo\s159-pruebas archive «SHA_MAIN» pipeline scripts frontend .github tests CLAUDE.md docs |
   tar -x -C D:\vrp-trabajo\temporales\s160_audit\main\`. Los datos se leen del worktree sólo si
   `git -C C:\vrp-trabajo\s159-pruebas diff --quiet «SHA_MAIN» -- data/mirova_equivalent latest_consolidado.csv
   data/mirova_reference` sale con 0; si no, con `git show «SHA_MAIN»:<ruta>`.
4. Archivo de insumos de GitHub, una sola vez: `gh api rate_limit` primero; después los últimos commits de
   `MendozaVolcanic/Mirova-v1` y de `VRP-chile` (regla 5 del `CLAUDE.md` global: frescura contra el remoto), las
   últimas 50 corridas de `nrt.yml` y `sync-mirova-csv.yml`, y `gh secret list` (nombres y fecha, sin valores). Todo a
   `C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\insumos\`. Nada de `gh run watch`.
5. Crea las carpetas de los diez agentes, cada una con `.gitignore` de `*/png/`, `*/paginas/`, `*/render/` y
   `*/descargas/` (regla del bloque de arranque S159: los renders de papers no van al repo público).
6. Reemplaza el preámbulo canónico por el del §6 en las dos copias (§10 punto 2), o deja escrito por qué no.
7. `df -h` de C: y D:; no lanza si C: tiene menos de 15 GB o D: menos de 10 GB.

| recurso | tope por agente | regla de parada |
|---|---|---|
| disco D: | F1 2 GB; los demás 0,5 GB | cualquier agente se detiene y lo escribe si C: o D: baja de 3 GB |
| API de GitHub | 10 llamadas por auditor, 5 por verificador, leyendo primero el archivo de insumos | si `rate_limit` baja de 200, ninguna llamada más |
| CMR | 150 búsquedas públicas, sólo F3 | sin autenticación (A71) |
| workflows | ninguno | despachar uno es parada |

**Olas** (la guía §5: siete agentes en paralelo agotan el límite en una hora):

| ola | agentes | concurrencia |
|---|---|---|
| 1 | F1, F2, F3 | 3 |
| 2 | F4, F0a, F0b; y V1, V2, V3 a medida que terminan F1, F2 y F3 | hasta 4 |
| 3 | V4; síntesis del orquestador | 1 a 2 |

Las esperas y los verificadores van en primer plano (guía §5): el orquestador no entrega con un verificador corriendo.

## 6. Los dos prompts de ejemplo, enteros

### 6.1 El preámbulo corregido (se pega igual en los diez)

Cambios aplicados respecto de `C:\vrp-trabajo\s159-pruebas\docs\_prompts\PREAMBULO-AUDITOR.md` (76 líneas, con el arreglo
de carpeta de S158): P1 (límite con CARPETA, SEGUIMIENTOS, los scripts se quedan), P2 (sin relleno no es corto), P3
(sin «REGLA OBLIGATORIA» ni «SIEMPRE»), P4 (forma del informe y citas marcadas), P5 (hueco de la vara) de
`C_INTEGRACION.md` §3, y los guiones largos de los campos cambiados por dos puntos. P6 a P8 son notas para quien
orquesta y no van en el bloque. El ejemplo de cita, que B dejó como hueco, lo completo con un pasaje que sí leí.

```text
<preambulo_auditor>
Contexto: esto es un Sistema de Decisiones Automatizadas en producción (Resolución CPLT N°372) que apoya la
decisión de alerta volcánica de SERNAGEOMIN. Corre solo, doce veces al día, sobre once volcanes, y lo que publica lo
mira un operador del OVDAS para decidir si un volcán cambió. Un bug silencioso acá no es un test rojo: es una anomalía
térmica que un geólogo no ve, o una que ve y no existe. No estás revisando código de laboratorio.

Definiciones de la vara (son las mismas en todos los frentes; si tu frente audita una de ellas, lo dice tu tarea):
«DEFINICIONES_DE_LA_VARA»

Límite: auditar no es arreglar. No modificas ningún archivo fuera de «CARPETA» (ruta absoluta que da quien
orquesta en cada tarea; si no la dio, es la carpeta de tu informe). Ahí van tus scripts, con su salida al lado:
son el instrumento y se quedan (no los borres al terminar ni los conviertas en tests del repositorio). Si al medir
ves un defecto fuera de tu eje, no lo persigas más allá de dejarlo reproducible: anótalo en SEGUIMIENTOS con
archivo:línea y confianza, y vuelve a tu eje. Tampoco mejoras el instrumento de otro ni corriges una cita vieja que
encuentres mal: eso también es un seguimiento. Los arreglos los decide quien orquesta, en tareas aparte, con tag
defensivo y confirmación de Nicolás cuando toquen pipeline/ (regla A45).

Antes de reportar, audita cada afirmación contra un tool result de tu propia sesión. Sólo reporta lo que puedas
respaldar con evidencia archivo:línea que leíste o con un número que produjo un script tuyo en esta sesión. Nada de
citar de memoria ni de heredar afirmaciones de docs anteriores sin verificarlas contra el código de hoy (una lista de
pendientes envejece hacia el falso positivo). Si una afirmación te resulta obvia pero no la leíste, márcala SOSPECHA
sin ninguna vergüenza. Sin relleno no quiere decir corto: cada hallazgo y cada SOSPECHA entran, aunque el informe
salga largo. Lo que sobra es la prosa alrededor, no los hallazgos.

Las dos preguntas del instrumento, en el encabezado de cada medición que hagas:
1. Si lo que mido estuviera completamente roto, ¿esta medición lo vería? Si no, dilo y no la cuentes como
   verificación.
2. Si el instrumento mismo estuviera muerto, ¿el resultado se vería distinto? Un cero que no distingue «no hay» de
   «no medí» es un dato inválido: SIN DATO no es FALLA y FALLA no es OK.
Incluye un control positivo (algo que seguro cambia y la medición lo ve) y declara el denominador y la ventana
temporal de los datos de cada número (regla A90 del proyecto).

Formato de cada hallazgo, con estos nombres exactos:
- TÍTULO: en una línea
- ARCHIVO:LÍNEA (ruta exacta) o SCRIPT:SALIDA
- QUÉ PASA: el defecto, en una o dos frases, primero el fenómeno físico y después el código
- CÓMO SE VE EN EL DASHBOARD: qué vería el operador del OVDAS, o «invisible» si no se ve
- CÓMO REPRODUCIRLO: comando exacto, volcán, pasada UTC
- CONFIANZA: CONFIRMADO (lo leíste o lo mediste) o SOSPECHA (hay que probarlo)
- GRAVEDAD 1-5: medida en qué decisión de alerta puede torcer

Cita de una fuente escrita (paper, manual, ATBD, documento del repo): toda frase copiada va entre comillas, con
autor y año o ruta, página impresa (y la del PDF si difieren) o línea, párrafo, figura, tabla o ecuación, y cómo la
leíste (RENDER si miraste la página como imagen, TEXTO si leíste la capa de texto; un PDF se cita sólo en RENDER, regla
A95). Lo que no está entre comillas es paráfrasis tuya y se nota en la redacción. Si no encuentras el pasaje, escribe
SIN LOCALIZAR; nunca reconstruyas una cita de memoria.
<example>
Afirmación: el protocolo del proyecto prohíbe que una auditoría repita el barrido general de ejes.
Cita: docs/PROTOCOLO_AUDITORIA_PROFUNDA.md l. 246, TEXTO: «está prohibido repetir el barrido general».
Por qué es correcta: la frase copiada está entre comillas y dice dónde está; un archivo Markdown se puede citar en
TEXTO; la conclusión va fuera de las comillas, con palabras del auditor.
</example>

Cobertura primero: reporta todo lo que encuentres con su confianza y gravedad; el filtrado lo hace otro. Ordena por
gravedad, lo peor primero.

Forma del informe, para que otro lo pueda filtrar sin releerte:
1. Encabezado: fecha y hora del servidor; commit sobre el que mediste; modelo y esfuerzo con que corriste; CARPETA;
   qué NO miraste (para que tu silencio no se lea como «todo bien»).
2. «En una pantalla»: el resultado primero, en cinco líneas o menos.
3. Hallazgos con ID provisional en el rango «RANGO», cada uno con los campos de arriba en ese orden.
4. Secciones aparte: SEGUIMIENTOS (lo visto fuera de tu eje); VERIFICADO LIMPIO (qué miraste y está sano, con el
   comando que lo confirma y contra qué vara lo verificaste: una verificación contra la vara equivocada no podía
   fallar); SIN DATO (lo que no pudiste medir, y por qué); fuera de alcance.
5. Además, hallazgos.csv en CARPETA, una fila por hallazgo, con columnas
   id,titulo,archivo_linea,confianza,gravedad,eje,comando_reproduccion,salida_cruda
   (salida_cruda es la ruta del archivo con la salida del script, no el número).
Tu último mensaje a quien orquesta repite el punto 2 y la ruta absoluta del informe.
</preambulo_auditor>
```

### 6.2 El prompt completo de F1

```text
<preambulo_auditor>
[el bloque del §6.1 entero, con los huecos llenos así:]
«DEFINICIONES_DE_LA_VARA» =
- «publica»: lo que da el predicado del tablero ejecutado con node por scripts/banco_paridad.py::correr_node (l. 141)
  sobre frontend/index.html del commit «SHA_MAIN» (regla A97). Nunca una reconstrucción a mano.
- «alerta de MIROVA», «protegida» y «negativo limpio»: lo que devuelve scripts/banco_paridad.py::etiquetar (l. 300)
  en «SHA_MAIN», con la regla D-9 de scripts/clase_mirova.py. Protegida es alerta de 1 MW o más (lectura A, D-4).
- pareo de una fila de MIROVA con una pasada nuestra: TOL_S = 120 segundos (scripts/banco_paridad.py l. 76).
- la referencia: la copia del repo en «SHA_MAIN» (latest_consolidado.csv y
  data/mirova_reference/mirova_v1_snapshot/registro_vrp_ocr.csv), identificada por su sha256, no la remota viva.
- Excepción de este frente: banco_paridad.py, clase_mirova.py y el predicado son objeto de tu auditoría. Para
  auditarlos no puedes usarlos como vara: escribe una implementación propia de lo que necesites y compara.
«CARPETA» = C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\f1\ (y, para datos extraídos,
D:\vrp-trabajo\temporales\s160_audit\f1\, con tope de 2 GB)
«RANGO» = 161 a 199
</preambulo_auditor>

<material>
- El código de hoy está en D:\vrp-trabajo\temporales\s160_audit\main\ (instantánea de «SHA_MAIN»). Los datos, según
  diga C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\insumos\LEEME.md.
- El criterio que aplicas es el de la tabla de F1 en C:\vrp-trabajo\s159-pruebas\docs\PLAN_AUDITORIA_S160.md §3
  (filas R1 a R17), fijado en el commit «SHA_PLAN». No lo cambies; si una fila te parece mal planteada, dilo en
  SEGUIMIENTOS y aplícala igual.
- La guía de la que salen esas filas: C:\Users\nmend\OneDrive\Escritorio\claude\GUIA_MAESTRA_AUDITORIAS.md §3 y §3b.
- El inventario de instrumentos (prioridad A, B y C) y los compartidos: plan §3, F1, «Insumos». Complétalo y declara
  el comando con que lo hiciste.
- Pendientes de entrada: F5-03 a F5-07 de C:\vrp-trabajo\s159-pruebas\experiments\_s158_audit\f5\INFORME.md
  (l. 106 a 195). Empieza por ellos; antes, búscalos en C:\vrp-trabajo\s159-pruebas\experiments\_s159\ por si S159 ya
  los resolvió.
- Lo ya medido hoy que no rehaces, y que usas como control positivo de tu barrido: el placebo de D25
  (C:\vrp-trabajo\s159-pruebas\docs\AUDIT_S158_R2.md §1, fila 9), el gemelo de D25
  (C:\vrp-trabajo\s159-pruebas\experiments\_s159\gemelo_d25\), el +104 contra +12
  (C:\vrp-trabajo\s159-pruebas\experiments\_s159\n\INFORME.md), y la caja que no llegó al segundo pase (A118 en el
  CLAUDE.md del proyecto).
</material>

<tarea>
Eres metrólogo de experimentos. Tu pregunta: ¿qué instrumentos de decisión del proyecto (pre-registros, evaluadores,
reglas de adopción y los bancos que comparten) podían dar el veredicto que dieron sin importar cuál era el efecto real?

Por qué importa: el detector que corre hoy en producción se adoptó con uno de estos instrumentos, y varios frentes
están cerrados por un «NO ADOPTAR» que salió de otros. Un instrumento que no puede fallar no da error: da un veredicto
plausible, y el frente queda cerrado sobre la pregunta equivocada. En un solo día, dos verificadores encontraron cinco
formas distintas de este defecto en instrumentos que nadie había mirado como familia.

Lo que entregas: la matriz instrumento por fila (OK, FALLA, NO APLICA, SIN DATO), con la medición profunda
(placebo, barajado dentro de estratos, borrado de un día) en todos los de prioridad A y en todos los de prioridad B
que tengan evaluador en código; los demás, clasificados leyendo. Corre los evaluadores sobre copias en tu CARPETA,
con brazos placebo construidos desde la salida del control. Si una de las cuatro formas ya conocidas no sale con tu
instrumento, esa fila no vale para el resto y lo dices. Para H1b, reimplementa etiquetar por tu cuenta y compara
sus etiquetas con las de banco_paridad sobre la misma ventana.

Gravedad de un defecto de instrumento: 5 si sostiene una decisión en producción, 4 si cerró un frente que sigue
cerrado, 3 si sostiene un A/B pendiente, 2 si es exploratorio, 1 de forma.

No reprocesas L1B, no despachas workflows, no lees el veredicto del A/B de D25 (decisión de Nicolás, sigue en pie), y
los datos de los brazos los extraes de las ramas origin/s146-ab/<run> por ruta con git show, nunca con checkout ni
pull. Presupuesto: unas tres horas. Escribe en español de Chile, formas de tú, sin guiones largos ni medios.
Please remove all mannered prose.
</tarea>

<autonomia>
You are operating autonomously. The user is not watching in real time and cannot answer questions mid-task, so asking 'Want me to…?' or 'Shall I…?' will block the work. For reversible actions that follow from the original request, proceed without asking. Stop only for destructive actions or genuine scope changes the user must decide. Offering follow-ups after the task is done is fine; asking permission before doing the work is not.

Exception: when the user is describing a problem, asking a question, or thinking out loud rather than requesting a change, the deliverable is your assessment. Report your findings and stop. Don't apply a fix until they ask for one.

Before ending your turn, check your last paragraph. If it is a plan, an analysis, a question, a list of next steps, or a promise about work you have not done ('I'll…', 'let me know when…'), do that work now with tool calls. That includes retrying after errors and gathering missing information yourself. Do not stop because the context or session is long. End your turn only when the task is complete or you are blocked on input only the user can provide.

Before running a command that changes system state (such as restarts, deletes, or config edits), check that the evidence actually supports that specific action. A signal that pattern-matches to a known failure may have a different cause.

En esta auditoría tu entregable es tu evaluación, nunca un arreglo. Las únicas cosas que exigen detenerte y
dejarlas escritas como pendientes son: tocar algo fuera de «CARPETA»; hacer commit, push o merge; despachar un
workflow que esta tarea no nombre; usar una credencial distinta de las que esta tarea nombra. Todo lo demás
(leer, correr scripts propios, bajar archivos sueltos de la lista de esta tarea, repetir una medición) lo haces
sin preguntar. Escribe el informe en «CARPETA» a medida que avanzas: si la sesión se corta, lo que esté en el
disco es lo que queda. Si algo te bloquea, termina todas las partes que no dependen de eso y di exactamente qué
quedó fuera y por qué.
Esta tarea no nombra ningún workflow ni ninguna credencial. Antes de cada extracción, mira el espacio libre: si C: o
D: baja de 3 GB, te detienes y lo escribes. Hasta 10 llamadas a la API de GitHub, después de leer el archivo de
insumos.
</autonomia>
```

### 6.3 El prompt completo de V1 (verificador de F1)

```text
<preambulo_auditor>
[el bloque del §6.1 entero, con «DEFINICIONES_DE_LA_VARA» igual que en F1, incluida la excepción;
«CARPETA» = C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\v1\ (datos en D:\vrp-trabajo\temporales\s160_audit\v1\,
tope 1 GB); «RANGO» = V1-01 en adelante]
</preambulo_auditor>

<verificador>
Eres el verificador de un hallazgo que encontró otro. No ves su razonamiento a propósito: si lo vieras,
heredarías sus supuestos. Recibes el título, el archivo:línea o script:salida, y nada más.
1. Antes de releer nada, escribe en tu informe la lista de caminos por los que esa afirmación podría estar mal
   (el instrumento mide otra cosa, la ventana no contiene el fenómeno, el flag se lee de otro lado, el caller
   transforma el argumento, un segundo camino que el arreglo no cubre, la copia local está atrasada).
2. Comprueba cada camino contra el código y los datos de hoy. Re-corre el script del auditor si existe; si no
   corre, eso ya es un resultado.
3. Veredicto por afirmación: CONFIRMADO, CONFIRMADO EN PARTE (di qué parte), REFUTADO o SIN DATO, con tu propia
   gravedad 1-5 y la evidencia de esta sesión.
4. Lo que encuentres de nuevo va como hallazgo propio, en tu rango de ID «RANGO_V». Funde duplicados entre
   auditores y dilo.
Éxito no es confirmar: es que cada veredicto se sostenga ante un tercero que repita tus comandos.
</verificador>

<material>
- «RANGO_V» = V1-01 en adelante.
- La lista que verificas: C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\v1\LISTA.md (la arma quien orquesta:
  cada hallazgo de F1 de gravedad 3 o más y toda celda FALLA de un instrumento de prioridad A o B, con título,
  ubicación, gravedad y la fila del criterio que el auditor dice que falla). No abras
  C:\vrp-trabajo\s159-pruebas\experiments\_s160_audit\f1\INFORME.md ni otros informes de F1; sí puedes correr los
  scripts que la lista nombra.
- El criterio contra el que se juzga cada celda: C:\vrp-trabajo\s159-pruebas\docs\PLAN_AUDITORIA_S160.md §3, tabla de
  F1. Antes de usarlo, comprueba que no cambió desde el sello: git -C C:\vrp-trabajo\s159-pruebas diff «SHA_PLAN» --
  docs/PLAN_AUDITORIA_S160.md tiene que salir vacío; si no, eso es tu primer hallazgo.
- El código de hoy: D:\vrp-trabajo\temporales\s160_audit\main\ (instantánea de «SHA_MAIN»).
</material>

<tarea>
Tu primer archivo es caminos.md en tu CARPETA: los caminos de ruptura de cada afirmación de la lista, escritos antes
de abrir cualquier archivo que la lista cite. Al terminarlo, anota al final su sha256 y la hora del servidor (por
ejemplo con curl -sI https://cmr.earthdata.nasa.gov/search/ y la línea Date), y no lo vuelvas a editar; lo que
aprendas después va al informe.

Para cada celda FALLA, el veredicto se apoya en una medición tuya por otro camino que el del auditor: si él construyó
el placebo multiplicando la magnitud, tú desplaza la posición o cambia la ganancia; si él barajó por volcán, tú
baraja por noche. Si el instrumento del auditor no corre, eso es un resultado. Pon tu propia gravedad con la misma
regla (5 producción, 4 frente cerrado, 3 A/B pendiente, 2 exploratorio, 1 forma).

Presupuesto: hora y media. Español de Chile, formas de tú, sin guiones largos ni medios. Please remove all mannered
prose.
</tarea>

<autonomia>
[el mismo bloque del §6.2, con «CARPETA» la de V1, tope de 1 GB en D: y hasta 5 llamadas a la API de GitHub]
</autonomia>
```

Los prompts de F2, F3 y F4 siguen la misma forma: preámbulo con sus huecos, `<material>` con su sección del §3,
`<tarea>` con la pregunta, el porqué y el entregable, y `<autonomia>`. Los de V2 a V4 y F0a y F0b, la forma de V1.

## 7. Qué entrega la auditoría

`docs/AUDIT_S160.md` (§4), los informes y scripts de las diez carpetas, y dos cosas que el proyecto no tiene:
- **La cola de validación en campo** (guía §0 y §8 paso 4): un archivo con ID, qué mirar, qué decide, qué desbloquea y
  de dónde sale, sembrado con los cinco casos de `docs/AUDIT_S158_R2.md` §9 y con los ítems de campo que declare cada
  frente (F3, por ejemplo: «el 2026-11-02 después de las 13:00 UTC, ¿el tablero muestra que Suomi NPP dejó de
  llegar?»). Dónde vive y quién la mantiene lo decide Nicolás (§9, decisión 4).
- **Un registro de modelo y esfuerzo por agente** (guía §5, última fila de la tabla): modelo, esfuerzo, duración,
  hallazgos, cuántos confirmó el verificador. Es la primera medición propia que la guía pide para calibrar su tabla.

## 8. Costo estimado

Sin base medida: no leí el consumo de ninguna auditoría anterior. La única referencia es «unas dos horas por auditor»
de `docs/PLAN_AUDITORIA_S158.md` l. 208.

| agente | modelo y esfuerzo | horas estimadas |
|---|---|---|
| F1 | Fable `high` | 3 |
| F2, F3, F4 | Fable `high` | 2 cada uno |
| F0a | Fable `high` | 1 |
| F0b | Opus `high` | 1 |
| V1 | Opus `high` | 1,5 |
| V2, V3, V4 | Opus `high` | 1 cada uno |
| síntesis | orquestador (Opus) | 1 |

Total unas 16,5 horas-agente; de reloj, 6 a 7 horas en las tres olas. Disco: hasta 4,5 GB en D: (de 13 libres). API
de GitHub: unas 100 llamadas en todo el plan. Workflows: cero. Si el límite de sesión de la API corta a un agente, se
relanza con «reconstruye el estado desde lo que está en tu CARPETA», que es donde escribe a medida que avanza.

## 9. Lo que el plan no hace, y lo que decide Nicolás antes de lanzar

No hace: ningún arreglo; ningún A/B nuevo ni reproceso; ninguna descarga de L1B; no lee el veredicto del A/B de D25;
no mergea #889 ni #890; no audita el código del scraper Mirova-v1 (otro repo: sólo sus salidas); no corre el frente
por uso ni el de prueba de campo; no mide el costo en tokens con precisión; no prueba la guía con el experimento a
ciegas que propone la plantilla (prompt ingenuo contra plantilla contra plantilla sin semillas), aunque el registro
del §7 junta datos para eso.

| # | decisión | recomendación |
|---|---|---|
| 1 | Suomi NPP cesa el 2026-11-02 13:00 UTC | decidir antes de lanzar si se trata como arreglo propio (con tag y A45) y no esperar a F3, que sólo mide cómo falla |
| 2 | lanzar los cuatro frentes o menos | los cuatro; si hay que recortar, F4 primero (no estrena eje) |
| 3 | agregar F5 por uso (etiquetas del tablero) | no en S160; sí la cola de campo |
| 4 | dónde vive la cola de campo | `docs/COLA_CAMPO.md`, mantenida por la síntesis de cada auditoría |
| 5 | reemplazar el preámbulo canónico por el del §6.1 en las dos copias | sí, en el mismo PR que commitea este plan |
| 6 | el umbral del 5 % de la fila R7 | aceptarlo o cambiarlo **antes** del sello |

## 10. Lo que la guía no me dio y tuve que decidir yo

Cada punto dice qué faltaba o estaba mal, qué decidí y dónde está en el plan.

1. **Qué commit es «el sistema de hoy» cuando hay cuatro versiones vivas.** La guía §0 dice que la fuente de verdad es
   el sistema corriendo, pero no dice cómo fijar la base de una auditoría estática con ramas divergentes y un PR de
   instrumentos sin mergear. Decidí `origin/main` por hash, con instantánea por `git archive` con rutas, y F3 mide
   aparte la rama de #889 (§5).
2. **El bloque canónico tiene dos copias que no coinciden, y la integración cita la vieja.** La copia de
   `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\_prompts\PREAMBULO-AUDITOR.md` (72 líneas)
   todavía manda los scripts a `experiments/_s134_audit/` en su l. 20; la de `C:\vrp-trabajo\s159-pruebas` (76 líneas)
   ya trae el arreglo de S158. Los números de línea de `C_INTEGRACION.md` §3 son los de la copia vieja. La guía §5 dice
   «revisarlo al inicio de cada plan» pero no qué copia manda. Decidí escribir el bloque entero en el plan (§6.1) y
   reemplazar las dos copias en el mismo PR (§9, decisión 5).
3. **El instrumento del frente L no es portable.** La guía §4 dice de `censo-magnitudes.py` «portable a cualquier
   `src/`; trae control positivo». Leído hoy: sólo ve decimales con punto, no lee YAML, su vocabulario de unidades es
   el de la AR Sandbox y su control positivo está atado a dos archivos de ARSAND, así que en otro repo sale con código
   2. Decidí que F2 escriba su censo con un control positivo de este proyecto (§3, F2). La guía debería decir que lo
   portable es el método, no el script.
4. **No hay frente de dependencias externas.** La guía tiene el vigilante ciego (§3) y la referencia que cambia con
   el tiempo (§3b fila 14), y la plantilla tiene P8, P9, B10 y B11, pero el §4 no lista un frente «lo que vence». Lo
   armé desde la plantilla (F3).
5. **Una auditoría también necesita pre-registro.** El §3b pide pre-registro para los A/B; para los criterios de una
   auditoría no dice nada, y sin eso un auditor puede ajustar la vara a lo que encontró. Decidí que los criterios del
   §3 sean el pre-registro, sellados con el commit del plan y comprobados por cada verificador con `git diff`.
6. **La auditoría como instrumento necesita su línea base roja.** La guía pide control positivo por medición, no
   por barrido. Decidí que cada frente tenga que volver a encontrar los defectos ya conocidos de su eje antes de que
   su cero valga (§0 punto 4 y cada frente).
7. **Independencia del verificador sin git.** La guía §5 pide que escriba sus caminos antes de leer, y en segunda
   ronda que los commitee; un subagente con la parada «sin commit» no puede. Decidí `caminos.md` con su sha256 y la
   hora del servidor, que el orquestador guarda (§4).
8. **La vara común cuando un frente audita la vara.** La guía §5 pide definir la vara en el bloque común; no dice qué
   hacer cuando un frente audita justo esa definición (`banco_paridad`). Decidí que F1 la trate como objeto y use una
   implementación propia, y que los demás la usen como vara (§6.2, excepción).
9. **Umbrales del propio criterio.** El §3b fila 7 pide la curva de poder y el barajado, pero no cuándo un criterio
   «cumple de más» bajo el azar; y fila 15 dice que el umbral se le pregunta a la referencia, cosa que aquí no aplica
   porque la pregunta es estadística. Puse 5 %, convención, y lo dejo para que Nicolás lo cambie antes del sello (§9,
   decisión 6).
10. **Gravedad de un defecto de instrumento.** La guía §6 manda priorizar en la unidad del usuario (la noche, la
    alerta). Un instrumento roto no pierde noches: tuerce decisiones. Decidí la escala por decisión sostenida
    (producción, frente cerrado, A/B pendiente, exploratorio).
11. **Qué pasa por el verificador.** La guía da «por ejemplo, gravedad 1 y 2» como lo que no se verifica, sin regla.
    Decidí gravedad 3 o más, salvo en F1, donde toda celda FALLA de prioridad A o B se verifica (§4).
12. **Verificar pendientes encontrados por modelos distintos.** La tabla dice «el otro modelo del que encontró»; con
    una lista mezclada hay que partirla, y para R2-17 no sé qué modelo lo encontró. Decidí dos verificadores chicos
    (F0a y F0b) y asigné R2-17 a Opus sin saberlo (§1).
13. **Los pendientes cruzan los ejes.** La regla C dice empezar por los pendientes, y la guía dice frentes disjuntos.
    Decidí repartir cada pendiente al frente de su eje y dejar sólo los huérfanos a F0 (§1).
14. **Un eje viejo dentro de una auditoría nueva.** La regla A prohíbe repetir el barrido general; no dice si se puede
    incluir un eje ya usado (cierres, S145 y S146) limitado al delta. Lo incluí limitado y es lo primero que se
    recorta (§9, decisión 2).
15. **Recursos externos compartidos por agentes en paralelo.** La guía §5 habla del límite de sesión (429) y §6 del
    instrumento único para los arreglos; no de una cuota externa compartida (API de GitHub, CMR, el bloqueo de
    Earthdata por reintentos, A71), ni del disco. Decidí archivo de insumos único, topes por agente y reglas de parada
    (§5).
16. **El ejemplo de cita.** La guía §5 pide «un ejemplo completo» y no trae ninguno; B lo dejó como hueco a propósito.
    Lo completé con un pasaje que leí hoy (protocolo l. 246), en un archivo Markdown donde TEXTO vale (§6.1).
17. **El presupuesto de tiempo en el prompt.** El plan S158 lo ponía por la guía de Opus 5.5; la guía nueva no lo
    menciona. Lo mantuve (unas 3 horas en F1); su efecto es SOSPECHA.
18. **La cola de campo.** La guía §0 dice que toda auditoría entrega una lista de pruebas de campo y §8 paso 4 que se
    abre una cola; VRP no la tiene (C_INTEGRACION §2). Decidí que la abra la síntesis en vez de un frente (§7).
19. **Costo.** La guía no da cómo estimar el costo de una auditoría ni registra consumos. Lo di en horas-agente sin
    base medida y agregué el registro del §7 para que la próxima tenga datos.

## 11. Revisión antes del sello (2026-10-22, orquestador de S160)

Nicolás aprobó lanzar con la instrucción de mejorar el método antes. Revisé el borrador con la regla A111 (un cierre o
un plan hereda las premisas con que se escribió) y con lo aprendido el 2026-10-21 en otras ramas. Lo que sigue manda
sobre el texto de arriba donde choquen.

### 11.1 Hechos nuevos que el borrador no tenía

1. **La referencia no es una sola.** La tabla `latest.php` (canal CONS, el consolidado del scraper) pierde filas por una
   carrera de workflows en el scraper Mirova-v1 (1.948 bajas netas en 6 tandas, 14 protegidas, según
   `experiments/_s159/referencia_estable/verificador/INFORME.md` §1), y el OCR tiene 39 reescrituras que son
   correcciones manuales documentadas de Nicolás (mismo informe). Nicolás considera la tabla lo más creíble y pide
   **informar siempre la tabla sola además del combinado** (memoria del proyecto, `feedback_s159_latest_php_mas_creible`).
2. **`scripts/clase_mirova.py::alerta_protegida` (l. 65 a 78 en `d516b9d8c`) mira sólo la fila que recibe**: con
   lectura A, una fila OCR de tipo alerta y 1 MW o más es protegida aunque la tabla tenga para esa pasada una fila
   FALSO_POSITIVO (según el coordinador; la función no cruza canales, leído por mí: si el que la llama tampoco lo hace,
   el efecto es ese; SOSPECHA hasta trazar a los que la llaman). Es un insumo compartido del criterio de K (fila R17).
3. **Suomi NPP cesa el 2026-11-02 13:00 UTC y el arreglo ya está en curso** en la rama local `s159-cese-snpp`
   (worktree `C:\vrp-trabajo\s159-instrumentos`, otra sesión, sin push al sellar: `git ls-remote origin s159-cese-snpp`
   vacío). La decisión 1 del §9 queda tomada. F3 lee ese worktree sin tocarlo, fecha lo que vio y no propone el mismo
   arreglo.
4. **El scraper Mirova-v1 lo audita otra sesión** (`audit-mirova-v1`). F1 y F3 no auditan su código; miden cómo lo
   consume VRP. Lo que vean del scraper va a SEGUIMIENTOS.
5. **El preámbulo corregido es la copia de `main` de un PR propio** (rama `s160-preambulo`), no la del §6.1: se le
   agregaron la tabla de huecos con la regla `grep -nE "«[A-Z_]+»"` antes de lanzar, el bloque de autonomía oficial de
   Fable 5.1 textual con sus paradas y un hueco `«LIMITES_DE_RECURSOS»`, y el bloque del verificador con `caminos.md`
   y su sha256. Los auditores de S160 llevan esa versión entera. La decisión 5 del §9 queda tomada así.
6. **Los datos del worktree no son los de `main`** (`git diff --quiet d516b9d8c -- data/mirova_equivalent
   latest_consolidado.csv data/mirova_reference` sale con 1). Se extrajeron con `git archive` a
   `D:\vrp-trabajo\temporales\s160_audit\main\data\` (179 MB); es la única copia de datos que leen los agentes.
7. **PR #889** está en `origin/s159-instrumentos` (`d0968e389`), sin worktree propio; se lee con `git show`.

### 11.2 Cambios al método

1. **La vara lleva dos referencias.** Toda cifra de paridad (alerta, protegida, negativo limpio, recall) se informa con
   la tabla sola y con el combinado tabla más OCR, las dos desde la copia congelada de `d516b9d8c` con su sha256. Un
   veredicto que cambia de signo entre las dos es hallazgo por sí mismo (fila R14).
2. **F1 se parte en dos**, porque el borrador le pedía a un solo agente medición profunda de unos 25 instrumentos en
   tres horas, y el que sostiene producción (K) merece un agente propio:
   - **F1a, prioridad A y los compartidos** (IDs 161 a 179): la regla con que se adoptó K
     (`experiments/_s151_prereg_fk_11/`) con medición profunda (placebo, barajado, borrado de un día) y **el veredicto
     de K recalculado con la tabla sola** sobre la misma referencia congelada; `banco_paridad.py`, `clase_mirova.py`
     (incluido el punto 11.1.2), `calidad_referencia_mirova.py`, `libro_de_cuentas.py` y el auto-audit, con la
     reimplementación independiente de `etiquetar` (H1b). Controles positivos del barrido: (a) y (b) del F1 original.
   - **F1b, prioridad B y C** (IDs 180 a 199): la matriz completa, con medición profunda en los de evaluador en código
     que cerraron un frente que sigue cerrado. Controles positivos: (c) y (d) del F1 original. Pendientes de entrada:
     F5-03 a F5-07.
   F1a y F1b no comparten carpeta; lo que uno encuentre del otro va a SEGUIMIENTOS.
3. **La fila R7 la fija Nicolás antes de lanzar F1a y F1b**, en un commit aparte de este plan («SHA_PLAN_F1»). F2, F3
   y F4 no usan R7 y se lanzan con «SHA_PLAN». Recomendación que se le lleva: mantener el 5 % convencional, pero con
   1.000 barajados en vez de 200 (con 200, el error de una fracción cercana al 5 % es de 1,5 puntos y el corte no se
   distingue del azar), y llamar FALLA sólo si el intervalo de 95 % de la fracción queda entero sobre el 5 %; si lo
   cruza, SIN PODER CONCLUYENTE, que no es OK.
4. **Olas, rehechas**: ola 1 con F2, F3 y F4 (no dependen de R7); ola 2 con F1a y F1b en cuanto Nicolás fije R7, y
   F0a y F0b; los verificadores en cuanto termina su auditor, con tope de cuatro agentes a la vez. V1 se parte en V1a y
   V1b. Total: once agentes de auditoría o verificación de pendientes y verificadores, más la síntesis.
5. **Modelos.** Auditores Fable a `high` como en el borrador, con `Please remove all mannered prose.`; verificadores
   Opus a `high`. F0a (verifica lo que encontró Opus) Fable; F0b (verifica lo de Fable) Opus.
6. **Archivo de insumos**: `experiments/_s160_audit/insumos/` (hora del servidor, rate limit, commits de Mirova-v1 y
   VRP-chile, 50 corridas de `nrt.yml` y de `sync-mirova-csv.yml`, nombres y fecha de los secretos, PR abiertos),
   bajado una vez por el orquestador el 2026-10-22 03:11 UTC. `LEEME.md` ahí dice dónde está cada cosa.

### 11.3 Lo que no cambié y por qué

- Las filas R1 a R6 y R8 a R17, los criterios de F2, F3 y F4 y la escala de gravedad: están bien planteados y
  cambiarlos ahora sería ajustar la vara antes de ver datos sin motivo.
- No agregué el frente por uso (decisión 3): sigue siendo de Nicolás.
