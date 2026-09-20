# Frente H (S146): lo que creemos haber probado y no probamos

> Auditoría de sólo lectura, 2026-09-20 (hora del servidor al empezar: 11:34 UTC). No se modificó
> ningún archivo existente, no se corrió pytest, no se re-ejecutó ningún A/B ni se bajó nada. Se
> crearon sólo este informe y los archivos de `experiments/_s146_auditoria/frente_H/`
> (`tabla.py` es la fuente única de la tabla y de `hipotesis.json`; `extraer_workflows.py` produce
> `workflows_ab.json`). Cada afirmación lleva la línea que abrí en esta sesión. Lo no verificado se
> marca SOSPECHA o SIN DATO. La columna "prof." dice hasta dónde llegué en cada fila: **A** abrí el
> instrumento (script, workflow o perfil), **B** leí el documento que declara el veredicto, **C**
> sólo la entrada de `docs/HYPOTHESIS_LOG.md` o la regla de `CLAUDE.md`.

## 0. Lo que cambia la lectura de todo lo demás: cuatro hechos de fecha

Antes de la tabla, cuatro hechos que fijé con `git` y que deciden el veredicto de casi todas las filas.

1. **La máscara de nube de 260 K no era del perfil, estaba escrita a mano en el código, y sólo en
   VIIRS 375.** `git log -S"260.0" -- pipeline/process_viirs.py` da dos commits: `a6e9a6ee4`
   (2026-04-05, "cloud mask for VIIRS 375m") y `1888c1e3e` (2026-08-28 19:00 -0400, #535). El diff de
   #535 quita `CLOUD_BT_THRESHOLD = 260.0` y pone `CLOUD_MASK_BT_K`, con el comentario "este sensor
   ignoraba `cloud_mask_bt_k` mientras MODIS sí la leía". `process_viirs_mod.py` no tiene ninguna
   máscara (grep de `CLOUD` da cero). Consecuencia: **todo A/B de VIIRS 375 corrido entre el 5 de
   abril y el 28 de agosto de 2026 corrió con la máscara puesta, dijera lo que dijera su perfil**
   (los perfiles que abrí, `_s126_corona_on`, `_s129_ab_control` y `_s130_d18_caja`, dicen `cloud_mask_bt_k: 0.0`; el comentario de `_s125_cloudmask_on.yaml:8-9` dice que el operacional ya lo fijaba en 0). Los A/B de MODIS y de VIIRS 750 no
   están afectados por este cambio.
2. **El régimen lo fija el código que procesa, no la fecha del gránulo.** El propio proyecto lo dejó
   escrito en `experiments/_s136/RESULTADO_PROBE.md:14-19` y lo midió (producción contra reproceso
   del mismo gránulo con código distinto: difieren 11 de 16). Por eso la columna que importa en la
   tabla es "código respecto de #535", no la ventana de los datos. Con eso **corrijo al hallazgo A-13
   del frente A en un punto**: el A/B de D18 (ventana 2026-05-29 a 08-24) NO corrió en el régimen
   viejo. Su flag se mergeó el 2026-08-31 (`d6d9b8e05`), tres días después de #535, así que reprocesó
   datos de invierno con la máscara ya apagada. Lo mismo vale para la corona (S127), los fondos
   (S129), el área y la banda 22 (S133), S135 y S143. F70 (datos commiteados el 2026-08-27) y el
   piloto de magnitud de S125 (2026-08-28 15:06 UTC, ocho horas antes de #535) sí corrieron con la
   máscara.
3. **La detección contextual contra la que se adoptó el Test 1 integrado ya no existe.** El Test 1
   entró al operacional el 2026-05-01 (`d6e64dc0b`, S29). El primer pase de los Tests 2 y 3 más el
   segundo pase entraron el 2026-05-16 (`3d25ea16e`, S46), y desde entonces los caminos viejos "se
   calcularon arriba (diag) pero no contribuyen" (`pipeline/process_viirs.py:1235-1237`, blame
   `958a7a189`, 2026-05-15). El "+30 puntos de recall" de S27 se midió contra una detección que dos
   semanas después fue reemplazada.
4. **El área con sec³ duró hasta el 2026-06-05 en MODIS (#354) y hasta el 2026-06-07/08 en VIIRS
   (#368, #373).** Todo lo de magnitud anterior a esas fechas (el kernel de fondo por volcán, el
   Tupungatito de A19, el barrido de S46) se midió con un área que multiplicaba por 1 a 5 fuera del
   nadir.

## 1. Cobertura, primero

| fuente | cómo | lo que NO cubrí |
|---|---|---|
| `docs/HYPOTHESIS_LOG.md` (1.567 líneas, 67 encabezados `## H`, de los cuales 1 es la plantilla: **66 entradas**) | **entero**, en tres tramos | nada. Las 66 están mapeadas a una fila o a "confirmada, fuera del censo" en el apéndice A |
| `docs/AUDIT_S146.md`, `docs/PLAN_PARIDAD_POST_AUDITORIA_S146.md`, `docs/audit_s146/FASE1_SUSTRATO_SOBREPUBLICACION.md` | enteros | |
| `docs/MIROVA_DIVERGENCES.md` (2.834 líneas) | **por tramos**: todos los encabezados, y las secciones D9 (222-300, 579-648), S33 (733-770), H_S27_1 y S28/S29 (784-935), D10/S103 (1365-1400), D11 (1420-1460), D14 (1829-1900), más un barrido de "NO ADOPTAR, REFUTAD, descartad, empeora" sobre todo el archivo | el cuerpo de D12, D13, D15 a D31 más allá de los encabezados y de lo que otros frentes ya citan |
| `docs/MISSION.md` (262 líneas) | líneas 60 a 262 (la puerta, los anti-patrones, las hipótesis abiertas de S27) | 1 a 59 |
| `CLAUDE.md`, reglas A | las tenía cargadas enteras como instrucciones de la sesión | |
| Workflows de A/B y probe | **los 93** (72 de `_archive/` más 21 vivos con `reproc` o `probe` en el nombre), por script: fechas, volcanes, sensores y fecha de alta en `workflows_ab.json` | sólo abrí a mano el de S105; el resto es extracción automática de texto, y las fechas pueden incluir la del comentario de cabecera |
| Perfiles de `pipeline/profiles/` (73) y `_archive/` (89) | listados; abrí los de la máscara de nube; leí el perfil efectivo con `VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile"` (28 flags en True) | no abrí el resto uno por uno |
| Informes de A/B | leí el veredicto y la ventana de: S99, S100, S102, S103, S108, S109, S112, S118, S121, S124 (F70, Villarrica, selección de cúmulo), S125, S126 (máscara, piso), S127, S129 (suma, radio), S130 (fondos, D18, gradiente), S131, S132 (los dos), S133 (área, B22), S135, S136 (puerta, probe, filtro de intensidad, sustrato) | `AUDIT_S105/S106/S110/S111/S114/S116/S119/S122/S123/S125_PROFUNDA/S127/S128/S131/S134/S138` no los abrí: uso lo que `CLAUDE.md`, el catálogo y `AUDIT_S146.md` citan de ellos |
| Scripts de medición | **abrí** `experiments/_s104_roi_probe/audit_local_sweep.py` y `experiments/87_audit_s46_round1.py`; comprobé que existen otros 32 citados (lista en la sección 3) | no corrí ninguno |
| `tasks/backlog_*.md` (5) | `backlog_s27`, `backlog_s115`, `backlog_s93` por encabezados y líneas clave | `backlog_data_integrity_session`, `backlog_s32` (son de esquema y de datos, no de detección) |
| `docs/audit_s146/FRENTE_F_FIDELIDAD_VIIRS.md` | lo encontré al final: leí la lista de hallazgos y F-01, F-02, F-07 | el resto. Lo cruzo en la sección 5 para no duplicar |
| Bloques de arranque y notas de cierre de `tasks/` | **no cubiertos**, salvo por un `grep` de "nunca se corrió / probó / midió" sobre `docs/`, `CLAUDE.md` y `tasks/` | es el hueco más grande de este frente para "ideas anotadas y abandonadas" |

**La tabla tiene 53 filas**: 43 de cosas descartadas, refutadas o nunca medidas y 10 de adopciones.
No es el universo: los A/B de mayo (S38 a S44, S72 a S73) están agrupados en dos filas (H-29 y H-A10)
con sólo existencia y ventana verificadas, y lo digo en la fila.

## 2. La tabla

Códigos de la columna de configuración: **M260** máscara de 260 K cableada (sólo VIIRS 375, 5 de
abril a 28 de agosto); **PRE46** máscara de píxeles armada con los caminos viejos (antes del 16 de
mayo); **G3K** compuerta `bt > t_bg + 3 K` (D22); **B21** banda 21 primaria en MODIS (D21); **SEC3**
área con sec³; **T1** Test 1 integrado activo (D30); **ANILLO** fondo por mediana de anillo (D25);
**PISO** pisos VRP; **C2G** cercas intra-radio activas; **ANCLA_TUP** ancla de Tupungatito en el
centro de caja del KMZ y no en el cráter. Veredicto H: **SIGUE** sigue valiendo; **CONFIG** vale
sólo bajo su configuración o su criterio; **PERDIDO** instrumento perdido; **NUNCA** nunca se midió;
**OBSOLETA** el mecanismo medido ya no existe en el código.

