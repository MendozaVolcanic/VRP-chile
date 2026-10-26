# Verificador con contexto limpio: tarea 1.18 (saturación en Nevados de Chillán)

Medición verificada: PR #836, `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s151_saturacion_chillan\`, run 38863912173 (commit 9011b584, 11 jobs verdes más `agregar`).
Insumos que usé: los 12 artefactos del run (los 11 `sat_*.json` por tramo, que traen campos que el resumen no conserva, más el resumen), bajados a `C:\Users\nmend\AppData\Local\Temp\claude\verif_118\tramos\`; `data/mirova_equivalent/NevadosDeChillan.json` de `origin/main` (último commit 2026-10-16 04:19 UTC) en `C:\Users\nmend\AppData\Local\Temp\claude\verif_118\prod_chillan.json`; el snapshot de MIROVA del commit 9011b584 y los CSV remotos actuales de Mirova-v1 (consolidado sha 539f9bdf, OCR sha f9707fc3, 2026-10-16 08:0x UTC). Scripts: `analiza.py`, `q2.py`, `q3.py` en el mismo directorio.

## Veredicto

**CONFIRMADO el cero de saturación.** Ningún píxel saturado se borró en el radio interior ni en la escena de 25 km, en ninguna de las 385 pasadas medidas, y el instrumento sí puede dar distinto de cero sobre estos mismos gránulos.
**PARCIAL la cruza con MIROVA**: el snapshot que se usó termina el 2026-10-14 08:35 en la tabla (CONS), así que al resumen le faltan las once alertas de tabla de los dos últimos días, entre ellas las más grandes de toda la ventana. Esto no cambia el cero, que se mide en el L1B, pero sí cambia cualquier frase sobre «lo que MIROVA publicó».

## 1. ¿El instrumento puede dar distinto de cero?

Sí, con tres pruebas independientes:

- **El bit es el correcto.** `docs/F28_SATURATION_INVESTIGATION.md:83-88` transcribe la Tabla C.1 del User Guide del L1B VIIRS: valor 2 = `Out_of_Range`, **valor 4 = `Saturation`** (cuentas L1A de 4095 o más). El probe usa `SAT_BIT = 0b100` (valor 4) en `saturacion.py` y producción el mismo en `pipeline/process_viirs.py:372` y `process_viirs_mod.py:228`. En MODIS cuenta SI = 65533 y aparte los demás SI > 32767.
- **El bit se enciende en los gránulos reales del run.** El campo `n_bit_granulo_entero` (está en los JSON por tramo, el resumen no lo trae) da I04 con el bit en **59 gránulos** (732 píxeles de día en 47, 17 de noche en 12), I05, M13 y M15 nunca; MODIS SI = 65533 sólo en la banda 22 (59 píxeles en 8 gránulos), nunca en 21 ni 31. El patrón es el físico esperado (I04 y B22 saturan bajo; I05, M13, B21 y B31 tienen techo alto), lo que además respalda que el índice de bandas MODIS está bien. Todos esos píxeles caen fuera de la caja de 25 km.
- **El conteo es anterior al borrado.** `leer_viirs_crudo` lee el DN crudo con h5py y la LUT del propio gránulo; `_leer_si_modis` lee el SI crudo con pyhdf; producción se llama aparte. «Borrado» = el crudo trae valor y producción da NaN. Los 306 gránulos VIIRS traían LUT (`origen_pisos = lut_del_granulo` en todos).
- **El brazo «sin» es producción.** Pareé las 192 pasadas nocturnas del probe con el JSON de producción por plataforma y hora: 183 parean; en las 182 con `t_max_k` la diferencia es **0,00 K en las 182**, y `primary_cluster.vrp_mw` coincide en **157 de 157**. El probe procesó los mismos gránulos y la misma ROI que producción.
- El test sintético (22 tests) corrió en cada job y pasó, pero usa el mismo `S.SAT_BIT` del módulo, así que sólo prueba coherencia interna, no el significado del bit; eso lo cierran los dos puntos de arriba.

**Controles positivos reales disponibles** (no los corrí, son pesados y requieren token):
- MODIS: `MYD021KM.A2026077.0805.061` (Planchón-Peteroa, 2026-03-18 08:05 Aqua), el «fósil» de 695.431 MW de F2.8, con unos 113 píxeles SI = 65533 según `docs/F28_SATURATION_INVESTIGATION.md:184` (ahí figura como hipótesis numérica, verificada aritméticamente, no leída píxel a píxel).
- VIIRS: cualquiera de los gránulos nocturnos con I04 marcado de este mismo run, por ejemplo `VJ202IMG.A2026281.0630.021` (6 píxeles). Lo que falta para cerrar del todo la cadena es una cifra que el probe no guarda: **borrados en el gránulo entero contra `n_bit_granulo_entero`**. Si coinciden, queda probado que un píxel saturado real llega con DN válido (no centinela) y entra a la máscara «borrado». Hoy eso descansa en la Tabla C.1 (clampeo al Reported Range), no en una medición.

## 2. Coherencia de los 348,3 K con producción

- Los **348,31 K** son de una pasada **diurna** (2026-10-08 19:30, Suomi NPP), que producción no procesa; por eso no está en el JSON.
- El máximo **nocturno** del probe en V375 es **347,12 K** (2026-10-15 06:36 Suomi NPP) y es **exactamente** el máximo `t_max_k` V375 de producción en la ventana (mismo record). Igual en V750 (326,89 K, 2026-10-15 06:00 NOAA-21) y en MODIS de noche (295,04 K, 2026-10-16 01:40 Terra). Los 307,08 K de MODIS son diurnos (2026-10-14 13:05).
- Margen: el pico nocturno queda 14,7 K bajo el techo de la LUT de Suomi NPP (361,78 K) y 5,9 K bajo los 353 K de MIROVA. No hay ningún valor apilado contra el techo.
- La coincidencia de `t_max_k` es por construcción (mismo lector), así que confirma que se midió lo mismo, no que no haya saturación; lo segundo lo dice el conteo crudo.

## 3. Pasadas que importan

- **2026-10-15 05:00 V375 (Suomi NPP): entró.** Los **22,13 MW son de MIROVA** (fila OCR `ALERTA_SIN_GEOMETRIA_OCR`), no nuestros. Nosotros: tablero 10,36 MW (`f5_core_vrp_mw` 10,3611; `pc.vrp_mw` 5,109), igual con y sin saturados, 0 borrados, máximo interior 336,2 K. La V750 de la misma hora: MIROVA 14,0, nosotros 1,876. La brecha de magnitud existe pero **no la explica la saturación**.
- **9,0 y 10,0 MW**: son V750 OCR del 2026-10-01 (05:24 NOAA-21 y 06:00 Suomi NPP); nosotros 2,655 y 11,084 MW, 0 borrados, máximos 286,1 y 298,6 K.
- **8,24 MW**: V375 OCR del 2026-10-05 06:24 Suomi NPP; nosotros 4,468 MW, 0 borrados, 333,1 K.
- **No medidas**: V375 del 2026-10-16 05:00 (NOAA-20; en MIROVA es `FALSO_POSITIVO` 10,61 MW a 17 km) y 05:42 (NOAA-21); sus gemelas V750 sí se midieron (282,1 y 319,1 K, 0 borrados). Probablemente no estaban aún en el CMR cuando corrió el tramo V375 5 (06:54 a 07:21 UTC). Tampoco están 3 records MODIS Terra NRT de producción (2026-09-28 01:25 y 01:30, 2026-10-10 01:05): los tres `far`, `t_max_k` 273,7 a 285,1 K, ninguno publica. El probe sólo encontró la versión Standard y esos gránulos NRT no se reemplazaron. Ninguna de estas faltas puede esconder un saturado que importe.
- Los días 2026-10-12 y 10-13 tienen 4 pasadas VIIRS en vez de 8 a 10; producción y MIROVA tienen el mismo hueco (en la noche del 10-13 ninguno de los dos tiene VIIRS). No es pérdida del probe.

## 4. La bajada remota fallida

- **Causa**: `sha_remoto` llama a `gh api` y el job `agregar` del workflow no exporta `GH_TOKEN`; en Actions `gh` sin token falla siempre (`CalledProcessError`). No es de red: **va a fallar en cada corrida** hasta agregar `env: GH_TOKEN: ${{ github.token }}` a ese paso.
- **Qué cambia**: nada del cero (sale del L1B). Pero el snapshot del commit 9011b584 termina en **2026-10-14 08:35 en la tabla** y en 2026-10-15 06:42 en el OCR. Contra el remoto actual, al resumen le faltan once alertas de tabla de Chillán, y entre ellas están **las mayores de toda la ventana**: V750 30,1 MW (2026-10-15 06:00), V375 19,07 (06:36), MODIS 15,27 (07:35), V750 15,15 (06:36), V375 14,67 (06:00), V750 14,02 y V375 13,74 (05:18), MODIS 12,39 (2026-10-16 01:40), V750 8,36 (2026-10-16 05:00), MODIS 6,98 (2026-10-14 13:05) y MODIS 1,72 (2026-10-15 01:05); además el OCR de 2026-10-15 19:00 V375 3,11 (diurno). Todas esas pasadas se midieron con 0 saturados (nosotros 20,42; 11,40; 2,10; 8,51; 9,45; 5,18; 5,85; 8,04; 1,61 MW, máximos interiores entre 289 y 347 K), así que **el cero se extiende a ellas**. Lo que no vale es: (a) `pasadas_con_mirova_alerta` y `suma_mirova_vrp_alertas_mw` del resumen, que están cortos en el tramo final; (b) `mirova_sin_pasada_medida = []`, que es vacuo después del 2026-10-14 08:35; (c) cualquier frase que diga que lo mayor que publicó MIROVA fue 9,0, 10,0, 8,24 o 22,13 MW.
- Nota sobre MODIS: la alerta de 15,27 MW (Aqua 2026-10-15 07:35) contra nuestros 2,10 MW, con B21 interior máximo de 289,2 K y 0 SI inválidos en la caja de 25 km, es la brecha MODIS más grande de la ventana y tampoco es saturación.

## Hallazgos laterales (no cambian el cero, latentes)

1. **Techo I04 de NOAA-21**: la LUT de los 46 gránulos NOAA-21 llega a **361,00 K**, bajo el corte de producción `361,77 − 0,5 = 361,27 K` (`process_viirs.py:400-402`). En NOAA-21 la defensa secundaria nunca dispara: un píxel clampeado sin bit de saturación (por ejemplo con sólo `Out_of_Range`, valor 2, que nadie lee) pasaría como medición válida de 361,0 K. NOAA-20 llega a 361,70 y Suomi NPP a 361,78.
2. **Techo M15 de producción**: `BT_LUT_MAX_MBAND["M15"] = 343,0 K` (`process_viirs_mod.py:182`) mientras la LUT real de M15 llega a 373,7 a 374,6 K. Producción borra como «saturado» todo M15 válido entre 342,5 y 374 K. Aquí no ocurrió (0 borrados en la escena), pero en un flujo de lava expuesto podría. M13: 634 contra 665,9 a 666,5 K, sin consecuencia práctica.
3. El resumen descarta `n_bit_granulo_entero` y `techos_lut_k`, que son justamente el control de instrumento; conviene que la tabla los muestre.

## Resumen (menos de 200 palabras)

CONFIRMADO el cero de saturación; PARCIAL la cruza con MIROVA. El bit leído (valor 4) es `Saturation` según la Tabla C.1, el conteo se hace sobre el DN y el SI crudos antes del borrado, y el instrumento sí se enciende en estos gránulos: I04 marcado en 59 y MODIS B22 = 65533 en 8, siempre fuera de la caja de 25 km. El brazo «sin» reproduce producción exacto (182 de 182 `t_max_k`, 157 de 157 `pc.vrp_mw`). Los 348,3 K son diurnos; el máximo nocturno, 347,12 K, es el mismo de producción y queda 14,7 K bajo el techo. La pasada de 22,13 MW (cifra de MIROVA) entró: nosotros 10,36 MW, sin saturados; también las de 9,0, 10,0 y 8,24. El snapshot de MIROVA termina el 2026-10-14 08:35 en la tabla y omite las once alertas finales, incluidas las mayores (30,1 MW V750; 19,07 V375; 15,27 MODIS), todas medidas con cero saturados. La bajada remota falla siempre por falta de `GH_TOKEN` en el job. Latentes: el techo I04 de NOAA-21 (361,0 K) queda bajo el corte de producción, y el techo M15 de producción (343 K) borra M15 válido hasta 374 K.
