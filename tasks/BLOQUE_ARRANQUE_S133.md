# Bloque de arranque S133

## Prompt para pegar al inicio de la sesión

```
Continuamos VRP Chile desde S132. Esa sesión ejecutó las 8 decisiones que S131 había dejado
esperando en AUDIT_S131 §4, más las mejoras de dashboard de DASHBOARD.md (PR #582, mergeado,
deploy d3b55ac4 verificado en el sitio publicado).

Leé en este orden:
  1. tasks/BLOQUE_ARRANQUE_S133.md         (este bloque)
  2. docs/s132/AB_DISTANCE_CLASS_MODIS.md  (A/B corrido: NO ADOPTAR, y por qué)
  3. docs/s132/AB_AREA_GEOLOCALIZADA.md    (el A/B que falta correr, con su criterio)
  4. docs/AUDIT_S131.md §4                 (las 8 decisiones, para ver qué quedó)

═══════════════════════════════════════════════════════════════════
NADA CORRIENDO. Suite 1104 passed · 3 skipped · 0 xfail.
═══════════════════════════════════════════════════════════════════

LO QUE S132 APLICÓ
· Higiene del dato: 1.635 sellos de piso incoherentes + 28 vrp_tir_mw. Los guards G3 y G7
  dejaron de ser xfail y ahora vigilan los invariantes de verdad.
· M15 saturación 423,0 → 343,0 K (Campus 2022 Sensors 22:1713 Tabla 1, verificado contra el
  PDF, no contra la nota). Las BT de M15 entre 342,5 y 423 K ya no entran como medición.
· F5' BAJÓ DEL NAVEGADOR AL PIPELINE. La magnitud que el operador ve para VIIRS375 vivía
  sólo en JavaScript y no existía en ningún JSON. Ahora es `pipeline/f5_core.py` y se
  persiste en `f5_core_vrp_mw` (17.459 de 24.368 I-band).
  ⚠️ UN AUDIT DE VIIRS375 QUE QUIERA MEDIR LO QUE EL OPERADOR VE USA `f5_core_vrp_mw`,
  con fallback a pc.vrp_mw cuando falta. MODIS y V750 siguen en pc.vrp_mw. A10 lo anota.
· Dashboard: ΔT en la tarjeta · anomalía relativa a la base del propio volcán · columna
  MIROVA (23,7 % a 90 d, verificado en vivo) · el 5,00 MW marcado como tope · «qué NO ve
  este sistema» + FICHA/CPLT en el modal · arranca en un volcán con data · `region` al yaml
  con guard · `processed_utc` en el record.
· Higiene de disco: 213 MB (duplicados verificados byte a byte + huérfanos del probe S104).

LOS 3 FLAGS APAGADOS — NO SON BUGS, SON DECISIONES ESPERANDO
  a) ENABLE_MODIS_B22_PRIMARY. Coppola 2016a l.141-144 dice textual que L21ok usa L22 y cae
     a L21 sólo cuando B22 satura; el repo hacía lo inverso. NO es «una línea» como decía el
     §4: B22 tiene NEΔT 0,017 K contra 0,183 K de B21, así que la banda primaria decide el
     ruido del fondo y por lo tanto dónde caen los umbrales N·σ — mueve DETECCIÓN (A67).
     Validación que S131 propuso: MODIS Láscar por pasada (n=50) antes/después y
     `diag_sigma_bg_k` mensual (esperable que baje).
  b) ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER. A/B YA CORRIDO: C1 TP 436→2.332 OK ·
     C2 52,73 % FALLA · C3 NdC 8,24 % OK · C4 OK → NO ADOPTAR por lo pre-registrado.
     PERO C2 estaba mal calibrado (fijé 2 km donde el corte es el inner_radius, 3-20 km):
     es la regla A91. Un A/B nuevo debe expresar C2 en unidades de inner_radius. La decisión
     de fondo es de Nicolás y el número está en el doc.
  c) ENABLE_GEOLOCATED_PIXEL_AREA. La función está construida y probada contra el ATBD
     (0,144 → 0,631 km², 4,38×). Falta el A/B de 3 brazos con reproc real; criterio
     pre-registrado en docs/s132/AB_AREA_GEOLOCALIZADA.md. NO extender a MODIS.

TAMBIÉN ESPERA A NICOLÁS
  · El marcador «extensión» de PCC (R15/R16). Es una pregunta volcanológica, no de código:
    ¿el lacolito del Cordón Caulle, a 7 km del vent y sobre 707 km², se lee «cráter» o
    «extensión»? Cambiarlo revierte una decisión de diseño de S88 (el inner siempre gana).
    R16 sin esa decisión es un no-op, y un no-op necesita un test antes que un commit.
  · Rotar el PAT de ~/.claude/settings.json.
  · Persistir `diag_d9_capped` en el pipeline: hoy el tope de 5,00 MW se reconoce por el
    valor en el frontend, que funciona pero es frágil. A72 pide el flag en el algoritmo.

REGLAS QUE ESTA SESIÓN CONFIRMÓ
  · A91 (nueva): el criterio pre-registrado va en las unidades del objeto que juzga. Si no,
    falla por mal calibrado y se lee como si hubiera fallado el dato. Y una vez que falló,
    NO se mueve: se reporta y la decisión pasa al humano.
  · El brazo de control que no puede fallar, cuando falla, avisa del instrumento: C4 «falló»
    con 18.468 records imposibles y era `NaN != NaN` de pandas.
  · Un port se prueba contra el original, no contra sí mismo (F5': node sobre 4.000 records
    reales del repo, extrayendo las funciones del propio index.html).
  · El guard G8 atrapó TRES veces que una cita file:line de CLAUDE.md se había corrido por
    inserciones mías. Funciona, pero es fricción conocida al editar mucho un archivo citado.
```

---

## Estado al cerrar S132

**PR**: #582 (squash a main, `d3b55ac4`). **Deploy**: pages-deploy verde y verificado en
https://mendozavolcanic.github.io/VRP-chile/ (columna MIROVA, tarjeta con ΔT/anomalía/MIROVA/
próxima pasada, modal con «qué NO ve» y CPLT, arranque en Isluga).
**Suite**: 1104 passed · 3 skipped · **0 xfail**.
**Tags defensivos**: `pre-s131-data-hygiene`, `pre-s132-pipeline-fixes`.

**Docs nuevos**: `docs/s132/AB_DISTANCE_CLASS_MODIS.md`, `docs/s132/AB_AREA_GEOLOCALIZADA.md`.
**Código nuevo**: `pipeline/f5_core.py`, `scripts/backfill_f5_core.py`,
`pipeline/scan_geometry.py::pixel_areas_from_geolocation`,
`derivar_distance_class` y `merge_mir_bands` en `process_modis.py`,
`aplicar_techo_saturacion_mband` en `process_viirs_mod.py`.
**Tests nuevos**: 5 archivos (`test_f5_core_python_s132`, `test_saturacion_mband_s132`,
`test_b22_primaria_modis_s132`, `test_distance_class_modis_s132`,
`test_area_geolocalizada_s132`, `test_guard_region_s132`, `test_sello_proceso_s132`).

### El patrón que ordenó la sesión

**Tres veces el instrumento falló antes que el dato, y las tres se notó porque había un
control.** El brazo C4 del A/B, que no podía fallar por construcción, falló y era pandas. El
guard de regiones «pasó» en una verificación que en realidad no había inyectado nada. Y mi
propio chequeo de R7 dio falso positivo enganchándose con el texto de la leyenda. La
diferencia entre las tres y un hallazgo falso fue, en los tres casos, haber preguntado antes
«¿esto podría estar midiendo otra cosa?».
