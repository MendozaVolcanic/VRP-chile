# Tarea 1.18: saturación en la erupción de Nevados de Chillán, leída en el L1B

Medición **descriptiva**: entrega conteos y magnitudes, no tiene umbral de veredicto y no decide nada.
Fila 2 de `experiments/_s151_repaso_crudo/INVENTARIO.md` (rama `loop/activo`).

## Por qué

Cuando un píxel está muy caliente, el detector del satélite llega al tope de su escala y deja de medir:
el píxel queda saturado. Nuestro pipeline borra esos píxeles (los deja en NaN) antes de detectar, para que
un valor recortado no se lea como temperatura. El problema es que un píxel borrado tampoco aparece en
`t_max_k` de nuestros JSON, así que el JSON no distingue «no saturó» de «saturó y se borró»
(`docs/audit_s150/VERIFICADOR_AUDITORIA.md:205-206`). Si en la erupción se borran píxeles, la magnitud que
publicamos queda corta justo cuando más importa, y eso sólo se puede contar en el L1B.

Techos: I04 361,77 K en nuestro lector (`pipeline/process_viirs.py:373`) contra 353 K de MIROVA
(`docs/audit_s146/FRENTE_F_FIDELIDAD_VIIRS.md:524`); el corpus ya llegó a 354,24 K. En MODIS se borra el
SI = 65533 (D24). MIROVA publicó en estas semanas 9,0, 10,0 y 8,24 MW, entre otros.

## Qué mide

Por cada gránulo de Chillán del 2026-09-28 a hoy, VIIRS 375, VIIRS 750 y MODIS, **de noche y de día por
separado**:

1. **Píxeles borrados por saturación**, por banda (MIR y TIR) y por región: radio interior (`inner_radius_km`
   = 5 km alrededor del ancla de detección) y la caja de escena (`radius_km` = 25 km). «Borrado» se define
   comparando la lectura cruda del L1B con la lectura de **producción** (`read_viirs_l1b`,
   `read_viirs_mod_l1b`, `read_modis_l1b`, llamadas, no copiadas): el L1B trae un valor y producción devuelve
   NaN. Se separa por motivo:
   - VIIRS: con el bit de saturación de `*_quality_flags` (bit 2, valor 4; la cita es la del pipeline,
     `pipeline/process_viirs.py:366-372`, Tabla C.1 del User Guide del L1B VIIRS; A37: VIIRS no usa
     centinela), o sin el bit pero en el techo del pipeline (BT de la LUT a 0,5 K o menos del techo);
   - MODIS: SI = 65533 («Detector is saturated»); los demás SI mayores que 32767 se cuentan aparte. En MODIS
     la banda MIR se da por perdida cuando faltan la 21 y la 22 a la vez, porque `merge_mir_bands` rellena
     una con la otra.
   Los centinelas de DN de VIIRS (bowtie, relleno, 65532 a 65535) no cuentan como saturación.
2. **El VRP con y sin esos píxeles**: el mismo `calculate_vrp` + `store.append_record` de producción, dos
   veces sobre el mismo L1B. Brazo «sin»: tal cual (hoy). Brazo «con»: la lectura devuelve los saturados en
   su piso (abajo). De cada brazo se guarda `primary_cluster.vrp_mw`, `f5_core_vrp_mw`, `vrp_mw` y la
   magnitud y publicación del tablero (`mirovaEqVrpDisplay` y el predicado completo, ejecutados con node
   desde `frontend/index.html`, A97).
3. **Una cota aditiva** que no depende del detector: k · A · (L(piso) − L(t_bg)) por píxel MIR borrado en
   el radio interior, con el k (`WOOSTER_COEFF`) y el A (`NADIR_PIXEL_AREA_M2`) del módulo de cada sensor y
   el `t_bg_k` del brazo «sin». Se da con dos pisos, el declarado y el empírico (la BT MIR válida más alta
   de la escena en ese gránulo), que la acotan por abajo.
4. **Lo que MIROVA publicó** para cada pasada: referencia unificada (`scripts/referencia_mirova_unificada.py`,
   bajada del remoto de Mirova-v1; si falla la red, el snapshot, y queda escrito), pareada por sensor a ±120 s
   como en `scripts/banco_paridad.py`, después de `calidad_referencia_mirova.avisar` (A119). Las filas de
   MIROVA que no parean con ninguna pasada medida se listan aparte (A108).

## El piso del píxel saturado (explícito)

Un píxel saturado está, por definición, **al menos** en el techo del sensor: su radiancia real es igual o
mayor. Por eso el techo es un **piso** de su energía, no una estimación de ella.

| banda | piso usado en el brazo «con» | de dónde sale |
|---|---|---|
| I04, I05, M13, M15 | máximo de la LUT de temperatura de brillo **del propio gránulo** (el valor al que el L1B clampea) | el L1B; si no trae LUT, el techo declarado del pipeline: 361,77 / 423,33 K (`process_viirs.py:373`), 634 / 343 K (`process_viirs_mod.BT_LUT_MAX_MBAND`) |
| MODIS B21 | 499,9 K | `BT_SAT_MIR_K_MODIS` = 500 K del perfil menos 0,1 K, porque la defensa secundaria de `calculate_vrp` borra lo que pase de 500 K (`process_modis.py:557-561`) |
| MODIS B22, B31 | BT válida más alta de esa banda en el gránulo | el pipeline no declara techo; es una cota inferior débil |

Un píxel VIIRS que producción borró por el techo **sin** el bit vuelve con la BT que el sensor reportó.

## Población y tiempo

Listado del CMR hecho el 2026-10-16 sólo con metadatos (`probe_saturacion.py --listar`, no baja nada),
del 2026-09-28 al 2026-10-16:

| familia | pares L1B + geo | de noche | volumen |
|---|---|---|---|
| VIIRS 375 | 151 | 76 | 48 GB |
| VIIRS 750 | 151 | 76 | 27 GB |
| MODIS | 79 | 36 | 12 GB |

Nuestro JSON tiene 74 records V375, 73 V750 y 39 MODIS nocturnos en esa ventana, coherente con el listado.

Ritmo: el probe D25 V750 (run 38679955131) hizo 54 pasadas de Chillán con 3 brazos en 25 min, unos 28 s
por pasada. Un par V375 pesa el doble, se estima 60 a 75 s. El workflow reparte V375 en 6 tramos, V750 en 3
y MODIS en 2 (11 jobs, 6 a la vez), con presupuesto interno de 60 min por job (al pasarlo marca
`sin_tiempo`) y `timeout-minutes: 80`. Estimado de reloj: **60 a 90 min**. No está medido sobre V375: si un
tramo marca `sin_tiempo`, se re-despacha ese tramo con más tramos.

## Cómo se despacha

```
gh workflow run probe-s151-saturacion-chillan.yml --repo MendozaVolcanic/VRP-chile --ref main -f desde=2026-09-28
```

`hasta` vacío = hoy UTC. El resultado queda en el artefacto `s151-sat-chillan-resumen` (`resumen.json`,
`tabla.md`). Autentica sólo por `EARTHDATA_TOKEN` y falla al instante si viene vacío (A71).

## Límites (declarados antes de correr)

- **De día producción no procesa** (filtro nocturno; `ENABLE_DAYTIME_VIIRS` apagado). El VRP diurno del
  probe es lo que el procesador de hoy daría sobre ese gránulo **con sus umbrales nocturnos**, y sirve sólo
  para ver cuánto cambia al restituir los saturados. El conteo diurno sí es del L1B, pero de día el MIR suma
  luz solar reflejada: un I04 saturado diurno puede ser reflexión en nube o nieve (A76), no lava.
- La posición MODIS sale de `_interp_geo`, como en producción (1 a 3 km de corrimiento contra MxD03, #828;
  tarea 1.17). El conteo «interior» de MODIS hereda ese corrimiento.
- El bit de saturación es el que cita el pipeline; no se re-verificó contra la página renderizada de la
  Tabla C.1 en esta tarea.
- La cota aditiva usa el fondo de escena `t_bg_k`, no el fondo de vecinos de D25 que usa la magnitud V375 de
  producción: es una cota, el número de producción es el del brazo «con».
- LANCE NRT guarda 7 a 14 días; los días más viejos van por el producto Standard. Un día sin ninguno de
  los dos queda sin pares y se ve en el conteo por día.
- Observación lateral del sintético, **sin verificar** y fuera de esta tarea: una meseta uniforme de 15
  píxeles a 330 K sobre fondo de 268 K casi no se detectó (un píxel, a 5 km); un foco en campana sí. Una
  meseta no tiene contraste contextual en su interior. Puede importar para un campo de lava ancho.

## Archivos

- `saturacion.py`: lógica local (conteo, brazo «con», pisos, cota aditiva, tramos).
- `probe_saturacion.py`: el probe (búsqueda en CMR, bajada, dos brazos, borrado del gránulo).
- `evaluar_saturacion.py`: junta los tramos y cruza con MIROVA. Sin veredicto.
- `tests/test_saturacion_chillan_s151.py`: sintético VIIRS con saturados sembrados (3 con bit, 1 en el techo
  sin bit, 1 en I05, un centinela que no debe contar) que el conteo tiene que encontrar exactos; control sin
  saturados donde los dos brazos coinciden; MODIS 65533; argumentos de producción por AST; workflow.
- `.github/workflows/probe-s151-saturacion-chillan.yml`.
