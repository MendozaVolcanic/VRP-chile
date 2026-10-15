# Rama diurna VIIRS apagada por flag: plan de implementación (D-10, issue #813)

> **Para agentes:** sub-skill requerida: superpowers:executing-plans (o subagent-driven-development).
> Pasos con casillas (`- [ ]`).

**Objetivo:** cablear en la réplica la Tabla 1 diurna de Coppola 2016a para VIIRS 375 y VIIRS 750,
detrás de un flag `ENABLE_DAYTIME_VIIRS` apagado, para poder correr después un A/B diurno. Con el
flag apagado producción no cambia ni un bit.

**Por qué.** MIROVA procesa VIIRS de día (Campus et al. 2022, *Sensors* 22:1713, p. 16 §5 y p. 17
Tabla 4) con umbrales más altos (Coppola 2016a, `sp426.5.pdf` p. 7, Tabla 1, página renderizada
S151: de día K1 = -0,6, C1 = 0,02, C2 = 15 en ROI1 y ROI2). Nuestra réplica pierde por construcción
las alertas diurnas: 40 pasadas protegidas usables bajo A119 contra 232 nocturnas
(`experiments/_s151_alertas_diurnas/README.md` §5).

**Arquitectura.** Un módulo nuevo `pipeline/diurno.py` es la ÚNICA lectura del flag (lee
`pipeline.profile.ENABLE_DAYTIME_VIIRS` en el momento de la llamada) y la única fuente del juego de
umbrales diurnos. Cada consumidor lo llama: los dos procesadores VIIRS (rebinding local de los
nombres de umbral al inicio de `calculate_vrp`, el mismo mecanismo que `process_modis.py` usa desde
S90), `store.append_record` (vía `_reject_daytime`), `fetch.fetch_for_volcano` (filtro previo a la
descarga), `scripts/run_pipeline.py` (`_check_night`) y `scripts/auto_audit_weekly.py` (filtra la
referencia con la misma regla del pipeline).

**Stack:** Python 3.12, numpy, pytest. Sin datos nuevos (el disco está al 96 %).

## Restricciones de líneas (contrato G8, `tests/test_guard_declarado_vs_efectivo_s131.py`)

CLAUDE.md cita `process_viirs.py:83` y `:213`, `process_viirs_mod.py:163` y `:466`,
`run_pipeline.py:234` y `:244`. No se agrega ni quita ninguna línea antes de esas citas: en
`process_viirs.py` el código nuevo va después de la l. 213; en `process_viirs_mod.py` después de la
l. 466 (helper al final del archivo, junto a `_parse_datetime`); en `run_pipeline.py` las ediciones
antes de la l. 244 son reemplazos de una línea por una línea.

## Lista de consumidores (A118), sacada con grep antes de escribir código

| sitio | qué decide hoy | qué hace con el flag |
|---|---|---|
| `pipeline/fetch.py` `fetch_for_volcano` | filtro nocturno previo a la descarga, todas las plataformas | no filtra las plataformas VIIRS si el flag está encendido |
| `scripts/run_pipeline.py` `_check_night` | salta el gránulo diurno, todas las plataformas | no salta los gránulos VIIRS si el flag está encendido |
| `pipeline/process_viirs.py` `calculate_vrp` | umbrales nocturnos siempre | Tabla 1 diurna si el flag está encendido y la pasada es diurna |
| `pipeline/process_viirs_mod.py` `calculate_vrp` | ídem | ídem |
| `pipeline/store.py` `_reject_daytime` / `append_record` | rechaza todo VIIRS diurno | acepta VIIRS diurno si el flag está encendido |
| `scripts/auto_audit_weekly.py` `es_pasada_diurna_descartada` (y `banco_paridad`, que la usa) | descarta de la referencia las pasadas VIIRS diurnas | las conserva si el flag está encendido |
| `pipeline/process_modis.py` `_select_thresholds` | MODIS, flag propio | no se toca (fuera de alcance); dos defectos anotados como pregunta |
| `scripts/rebuild_mirova_from_consolidado.py` | clasifica filas de la REFERENCIA de MIROVA | no es un consumidor del flag: describe a MIROVA, no a la réplica |
| `pipeline/vrptir.py`, `detect_tirvolch.py` | VRP TIR y TIRVolcH «sólo noche» | no son camino de publicación de la réplica; anotados |

## Tarea 1: tests que fallan

**Archivo:** `tests/test_rama_diurna_viirs_s151.py`

- [ ] perfil expone `ENABLE_DAYTIME_VIIRS is False`, `C2_DNTI_DAY == C2_DETI_DAY == 15.0`.
- [ ] `diurno.umbrales_viirs(es_dia, habilitado, noche)`: con `habilitado=False` devuelve el MISMO
  objeto `noche`; con `es_dia=False` también; con los dos en True devuelve K1 -0,6, C1 0,02 en las
  dos ROI y en la ROI única, C2 15 en dNTI y dETI de las dos ROI, `viirs_c2_override = None`.
- [ ] `diurno.aplica_filtro_nocturno(nighttime_only, plataforma)`: flag apagado = `nighttime_only`
  para toda plataforma; encendido = False para `VIIRS_*`, `nighttime_only` para `MODIS_*`.
- [ ] `store._reject_daytime`: con `enable_daytime_viirs=True`, VIIRS 375 y 750 de día pasan; MODIS
  de día con su flag apagado sigue rechazado; de noche nada cambia.
- [ ] procesadores: espía sobre `first_pass_tests_2_and_3`, `second_pass_adjacent` y
  `compute_bg_stats` (envuelven la función real). Flag encendido + gránulo diurno: C1 0,02, C2 15,
  K1 -0,6. Flag encendido + gránulo nocturno: los kwargs son los de flag apagado. Flag apagado +
  gránulo diurno: idénticos a flag apagado + nocturno, y el record es idéntico salvo los campos que
  dependen del nombre del gránulo.
- [ ] efecto medido (A116): en la escena `nevado_vecino_tibio` del arnés S142, el primer pase marca
  píxeles de noche y marca menos (o ninguno) con la Tabla 1 diurna; si no cambia nada, el test lo
  dice en vez de pasar.
- [ ] `fetch_for_volcano`: con el flag encendido el filtro nocturno se llama sólo para MODIS.
- [ ] `run_pipeline.process_date`: con el flag encendido un gránulo VIIRS diurno llega al
  procesador; con el flag apagado no.
- [ ] `es_pasada_diurna_descartada` sigue al flag.

Correr: `python -m pytest tests/test_rama_diurna_viirs_s151.py -q` y ver que falla por falta de
`ENABLE_DAYTIME_VIIRS` / `pipeline.diurno`, no por un error de escritura.

## Tarea 2: perfil y módulo `diurno`

- [ ] `pipeline/profile.py`: `ENABLE_DAYTIME_VIIRS` (de `paths:`), `C2_DNTI_DAY` y `C2_DETI_DAY`
  (de `thresholds:`, 15,0 por defecto, Tabla 1).
- [ ] `pipeline/profiles/mirova_equivalent.yaml`: `enable_daytime_viirs: false` en `paths:`, con
  comentario (patrón S142/S145).
- [ ] `pipeline/diurno.py` con cabecera FICHA y POR QUÉ.

## Tarea 3: los dos procesadores VIIRS

- [ ] `_umbrales_de_la_pasada(nombre_granulo, lat, lon)` a nivel de módulo (lee los globales del
  propio módulo para la noche, así un parche de test sobre el módulo sigue funcionando).
- [ ] al inicio de `calculate_vrp`, rebinding local de: `NTI_K1_NIGHT`, `N_SIGMA_MIR_SUMMIT`,
  `N_SIGMA_MIR_SCENE`, `DNTI_CONTEXTUAL_C1`, `DNTI_CONTEXTUAL_C1_SUMMIT`, `DNTI_CONTEXTUAL_C1_SCENE`,
  `C2_DNTI_SUMMIT_NIGHT`, `C2_DNTI_SCENE_NIGHT`, `C2_DETI_SUMMIT_NIGHT`, `C2_DETI_SCENE_NIGHT`,
  `VIIRS_C2_OVERRIDE_NIGHT`.
- [ ] campo `diag_umbrales_diurnos = True` en el record SÓLO cuando se aplicó la Tabla 1 diurna (con
  el flag apagado el campo no aparece y el record es bit a bit el de hoy).

## Tarea 4: store, fetch, run_pipeline, auditoría

- [ ] `store._reject_daytime(..., enable_daytime_viirs=False)`; docstring corregido (Campus 2022).
- [ ] `fetch.fetch_for_volcano`: `if aplica_filtro_nocturno(nighttime_only, platform):`.
- [ ] `run_pipeline._check_night(l1b_path, platform="")`, una línea por una línea.
- [ ] `auto_audit_weekly.es_pasada_diurna_descartada` pasa el flag VIIRS.
- [ ] nota de `tests/test_daytime_modis.py` actualizada.

## Tarea 5: documentación y verificación

- [ ] cabecera FICHA de `process_viirs.py` (sin cambiar el número de líneas), FICHA SDA v1.8,
  marca en D27.
- [ ] suite completa con el árbol quieto (A112) y golden bit a bit.
- [ ] PR sin mergear; pre-registro en `experiments/_s151_ab_diurno/PREREGISTRO.md`.

## Lo que queda como pregunta (no se inventan umbrales)

Caminos que de día quedan igual que de noche porque el paper no da número: Test 1 integrado (MIR
absoluto, detector propio, D30), compuerta `bt > t_bg + 3 K` (D22), camino de BT (apagado, D31; con
el flag encendido usa N·σ = 15 por la misma analogía con C2 que ya usa de noche), máscara de nube
(apagada en producción), tope D9 (fondo bajo 270 K), compuerta de consistencia TIR, magnitud.
