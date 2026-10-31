# Adenda a N-01 (§8.2 del pre-registro de MOD-D fase 4): BORRADOR, sin sellar

Escrita por S170 el 2026-10-31, después de leer la tanda t1 y antes de que nadie lea el A/B. Es para que Nicolás la
apruebe o la rechace. No cambia nada de lo que mide el runner: sólo cómo el evaluador cuenta un caso de la identidad.
Pre-registro sellado: tag `s168-modd-f4-sellado`. Candado: tag `s170-modd-f4-candado`.

## Qué pasa, como geólogo

Hay noches en que la escena MODIS alrededor del volcán no sirve. Por ejemplo, la grilla de 51 × 51 km queda con
demasiadas celdas sin dato en el infrarrojo medio. En Villarrica 2026-03-11 01:30, por ejemplo, el cráter cae en la
costura y en el borde del MxD03, y el censo anotó la grilla como incompleta, con 1.462 celdas sin dato en el MIR
(registro del censo, `ab_parte02.jsonl` de la tanda 1). El
código de MIROVA declara esa escena inválida y no busca anomalías en ella. El censo de MOD-D guardó la grilla de esas
pasadas igual, y su port llegó al mismo diagnóstico: escena inválida, ningún píxel alertado.

La vía del pipeline, leyendo el HDF en el runner, llega a lo mismo: misma grilla celda a celda, misma máscara vacía,
mismo VRP (cero), mismo motivo. **No hay desacuerdo.**

## Por qué la regla sellada lo cuenta como desacuerdo

N-01 (segunda vuelta del verificador) se escribió para otro caso: un MxD03 mal leído hace que el runner diga «volcán
fuera del gránulo» en una pasada que el censo sí cubrió, y sin la regla esa pasada desaparecería de la identidad. Para
eso, N-01 supone que **una pasada con grilla del censo es una pasada que el censo cubrió**, y cuenta como «sellada sin
explicar» toda pasada con grilla que el runner saque por un motivo sellado, salvo que la identidad la declare de otro
gránulo. Con «escena inválida», la premisa no vale: el censo guardó la grilla pero tampoco la evaluó. Con la regla
sellada la identidad queda en rojo y el veredicto sale INDECIDIBLE, aunque la vía y el censo coinciden.

## Cuántas son (con su script)

`experiments/_s168/modd_f4_candado/selladas_con_grilla.py`, salida `selladas_con_grilla_salida.txt`:
- en todo el censo, 45 de las 5.321 pasadas con grilla tienen `escena_invalida` en el port del censo;
- en t1, 24 pasadas con grilla del censo salen del runner como `escena_invalida`, y el censo llegó al mismo motivo en
  las 24. Las 24 tienen además la misma grilla, la misma máscara y el mismo VRP en la identidad (`identidad_t1_salida.txt`).

Ninguna pasada con grilla del censo salió en t1 como «volcán fuera del gránulo».

## Texto exacto de la regla nueva (se agrega al §8.2, después del párrafo de N-01)

> Una pasada con grilla del censo que el runner saca como «escena inválida» cuenta como acuerdo de la identidad, y no
> entra al tope de 1 % de otro gránulo, si se cumplen a la vez: (1) el port del censo llegó al mismo motivo en esa
> pasada; (2) es el mismo gránulo; (3) la grilla del runner es igual a la del censo celda a celda, a la precisión
> float32 con que el censo la guardó; y (4) tienen la misma máscara y el mismo VRP a 0,001 MW. Si falta cualquiera de
> las cuatro, rige N-01 tal cual. «Volcán fuera del gránulo» sigue siempre con N-01: el censo cubrió el volcán, y ése es
> justo el caso que N-01 vigila.

Implementación propuesta (si se sella): `identidad_f4.py` agrega a cada pasada el campo `motivo_censo` (el
`motivo_vacio` del port del censo, leído del jsonl del censo cuya grilla ya se verifica con
`grillas_censo_sha256.txt`). En `evaluar_f4.control_identidad`, la condición de `selladas_sin_explicar` pasa a ser la de
`regla_n01_adenda.selladas_sin_explicar` (nueva). La batería suma un escenario por cada condición, cada uno con su
mutación, y se repiten la batería y las mutaciones antes del sello nuevo.

## Prueba de que la regla nueva no acepta de más

`probar_regla_n01_adenda.py`, salida `probar_regla_n01_adenda_salida.txt`.
- **Parte A**: 9 de 9. La regla candidata sólo explica el caso del mismo motivo con la misma grilla, y NO explica
  cuando el censo llegó a OTRO motivo (ninguno, o «fuera del gránulo»), con OTRA grilla, con otra máscara, con otro
  VRP, sin el campo del censo, ni con «volcán fuera del gránulo». En todos esos casos la regla sellada también la
  marca sin explicar. Otro gránulo se sigue explicando igual que hoy.
- **Parte B**, sobre t1 real: 24 selladas sin explicar con la regla sellada, 0 con la candidata.

## Lo que esta adenda no decide

- No toca P1, P2, P2', M, Chillán ni la regla de posición. No cambia ninguna fila del runner ni ninguna publicación.
- El tope de 1 % de otro gránulo queda igual.
- Si Nicolás la rechaza, la lectura del A/B con la regla sellada sale INDECIDIBLE por la identidad, y la decisión de
  qué hacer pasa a ser suya con la lista de las 45 en la mano.
