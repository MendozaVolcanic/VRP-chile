# T1, T2 y T5 (fase 0 del programa por sensor): evaluador común con cobertura contra MIROVA

Sesión hija «Instrumento» de S162, 2026-10-24. Programa: `docs/superpowers/specs/2026-10-24-programa-replica-por-sensor.md`
§8.1, §8.2 y §8.5. Módulo: `scripts/evaluador_comun.py`. Pruebas: `tests/test_evaluador_comun_s162.py`. Depende de
`clase_mirova.resumir_pasadas` (PR de T4+T6), por eso el PR va apilado sobre esa rama.

## El fenómeno

NASA reprocesó el 2026-10-12 los gránulos de Suomi NPP y NOAA-21 y retiró los originales. Cuando el A/B de D25 buscó
ese día, CMR no devolvió nada de esas dos plataformas: a los tres brazos les faltó la pasada de NOAA-21 de las 05:18
sobre Chillán, una alerta de 8,44 MW que producción sí había procesado a tiempo. El hueco pasó cuatro filtros sin que
nada lo dijera, porque todos partían de nuestros records y comparaban brazos entre sí: tres brazos con el mismo hueco
son «idénticos». Para ver un hueco común hay que partir de lo que MIROVA vio.

## Qué hace el evaluador

1. **Parte de las pasadas de MIROVA** (una por pasada a ±120 s, la tabla manda: T4) y busca cada una en cada lado, los
   brazos y un control (producción).
2. **T1, falla de cobertura antes del veredicto (INVALIDO POR INSTRUMENTO)**: (a) una protegida (lectura A) sin record
   en algún brazo que el control sí tiene (basta un brazo: uno con menos cobertura sesga igual que un hueco común);
   (b) un volcán, sensor y día con pasadas de MIROVA y cero records en un brazo (también si el control tampoco tiene:
   ese día no se puede evaluar); (c) una protegida que algún brazo tiene y el control no (el control no sirve de vara).
   Los días excluidos (D-29) no cuentan y se informan. Las alertas no protegidas faltantes y las pasadas que el control
   no tiene se avisan sin invalidar, y las no observadas se agrupan por día para que un hueco común salte a la vista.
3. **T2, «no observado»**: el procesador no deja record cuando el volcán cae fuera del gránulo o la escena no sirve
   (`pipeline/process_viirs.py`, «if not np.any(roi_mask): return None»). Si ningún lado tiene la pasada, es
   `no_observado` y sale de todos los denominadores; si el control la tiene y el brazo no, es `falta_cobertura` (cuenta
   contra el instrumento, nunca contra el detector).
4. **T5**: P1b en las dos direcciones sobre pasadas que observaron los dos lados (abajo: protegida que el control
   publica con 1 MW o más y el brazo debajo; arriba: el brazo publica 1 MW o más donde el control no, por estado de
   MIROVA) y publicaciones sobre pasadas RUTINA de la tabla, separadas por si otra pasada del día alertó (VE162-03).
5. Carga real con el predicado del tablero (node, de `banco_paridad`); un volcán sin archivo en un brazo invalida.
   Sirve a VIIRS 375, VIIRS 750 y MODIS (`--sensores`).

## Caso real: V1 del A/B de D25 (`v1_d25_salida.txt`)

Brazos K, G y D de V1 (`...a3efc9fd...\scratchpad\d25\V1\`), control = producción en `1f7ebfc9e`, referencia congelada
de V1 (`C:\vrp-trabajo\s159-evaluador\experiments\_s157_prereg_d25\_congelado_v1\`), 2026-08-29 a 2026-10-18, VIIRS,
días D-29 excluidos (13, 17 a 20 de octubre). **Sin decirle nada del 12-oct**:

- **INVALIDO POR INSTRUMENTO**: las 2 protegidas de Chillán del 2026-10-12 05:18:02 (375 con 7,31 MW y 750 con 8,44),
  «falta en D, G, K».
- 42 pasadas con `falta_cobertura` en cada brazo (el informe del 12-oct contó 44 ausentes, 42 con fila de MIROVA).
- Aviso: 5 alertas no protegidas sin record en los brazos, exactamente las que listó ese informe (Isluga 375 05:12 y
  05:48, Isluga 750 05:48, Chillán 05:54 en los dos sensores).
- 6 pasadas `no_observado` en los cuatro lados; el día con más es el 2026-10-12 (2).
- Con K como control (como el evaluador sellado; `v1_control_K_salida.txt`): también INVALIDO, porque K no tiene las
  2 protegidas que producción sí; aviso de 40 pasadas que producción tiene y K no, y 44 no observadas el 2026-10-12.
- P1b de D contra producción: abajo 2 (Chillán 375 2026-10-11 05:36 y 750 2026-10-14 06:18), arriba 3 protegidas
  (se acercan a MIROVA).
- RUTINA, D publica y K no en noches con alerta de VIIRS 750: **5**, igual que VE162-03 para V1 por otro camino.

Prueba de humo MODIS (`modis_humo_salida.txt`, producción contra sí misma): COBERTURA OK; 39 de 1.092 pasadas MODIS
de MIROVA no las tiene producción (no observadas).

## Verificador con contexto limpio (Sonnet, 2026-10-24)

Las 4 afirmaciones **CONFIRMADAS**, con controles positivos propios sobre copias de producción (día entero borrado,
un sensor borrado, protegidas borradas, volcán sin archivo: todos INVALIDO) y nulos (producción contra su copia, K
contra G: OK). El filtro nocturno es el mismo para pasadas y records (ninguna pasada cambia de clase a ±120 s) y el
pareo minuto contra segundo tiene desfase máximo bajo 10 s y un solo candidato. Hallazgos aplicados en este PR:
- (gravedad 3) una protegida que faltaba en un solo brazo no invalidaba: ahora basta un brazo (una prueba fijaba el
  defecto como correcto y se reemplazó);
- (gravedad 3) un control incompleto dejaba ciego al evaluador: ahora una protegida que un brazo tiene y el control no
  invalida, y las demás se avisan;
- (gravedad 2) las no observadas se agrupan por día;
- (gravedad 2) la carga real (`cargar_lado`, `pasadas_nocturnas`) no tenía pruebas: ahora tiene dos, con un doble del
  predicado del tablero en lugar de node (se prueba la carga y los filtros, no el predicado).
Sin aplicar, declarado: (gravedad 1) P1b compara contra el control elegido; el sellado compara K contra D. Para V1 dan
los mismos dos cruces.

## Pruebas y mutaciones

- 27 pruebas, con la noche del 12-oct reconstruida como caso principal.
- Roja por aserción: la mutación E1 (la cobertura compara brazos entre sí, el defecto del 12-oct) falla por aserción.
- Mutaciones (`mutaciones_t1_t2_t5.json` → `mutaciones_t1_t2_t5_salida.txt`): **28 de 28 atrapadas por aserción** con
  control de caída. Cuatro vivas en la primera corrida (borde inferior de la ventana, P1b con el control sin record,
  record no publicado con VRP, FALSO_POSITIVO en RUTINA) pidieron cuatro pruebas nuevas.

## Límites

- El control es producción: un hueco común con producción se ve sólo como «día sin records» o como «no observado».
  Una pasada que nadie tiene puede ser fuera del gránulo o un hueco de NASA para todos; sin los logs del procesador no
  se distingue. Los logs del run (`SEARCH_DONE ... n_l1b=0`) podrían separarlo: no implementado.
- El pareo usa el minuto del record (`datetime_utc` sin segundos) contra el segundo de MIROVA: hasta 59 s de error,
  dentro de los 120 s.
- No reemplaza a los evaluadores sellados (D25 y anteriores): es para A/B nuevos. Integrarlo a un evaluador sellado
  pide adenda.
- El placebo de ganancia y el comparador d′ (T3) van en un PR aparte sobre este módulo.
