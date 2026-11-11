# Auditoría S179: decisiones y planes de S172 a S178, con Fable 5.2

Fecha: 2026-11-11 (servidor). Plan pre-registrado: `docs/PLAN_AUDITORIA_S179.md` (con su adenda §9). Base: código en
main `438a60a1e`, documentos del loop en `0472cd95e`. Cuatro auditores Claude Fable 5.2 y cuatro verificadores Claude
Opus 5.5, todos a esfuerzo `high` (medido en cada transcripto, §6). Esta síntesis usa **sólo veredictos de
verificador**; lo que ningún verificador miró va rotulado «sin verificar».

Carpetas (cada una con informe, `hallazgos.csv`, scripts y salidas):
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s179_audit\` subcarpetas `a`, `b`, `c`,
`d` (auditores) y `va`, `vb`, `vc`, `vd` (verificadores).

## 1. En una pantalla

1. **Las adopciones se sostienen; ninguna afirmación central quedó refutada.** La vía en MODIS publica las 11
   alertas protegidas de MIROVA desde el encendido (K de guardia, 8). La lectura de la retrospectiva se reproduce
   byte a byte y con código propio. Los verificadores dejaron 61 veredictos (51 sobre afirmaciones de los auditores,
   algunas fundidas, y 10 hallazgos propios): 41 confirmados, 17 confirmados en parte, 1 sospecha y 2 refutados (los
   dos a favor de lo que ya estaba decidido). Conteo de los cuatro `hallazgos.csv` de verificador.
2. **El plazo de reversión pre-autorizada se gasta en la erupción de Chillán.** Las reglas de MODIS y de VIIRS cierran
   la pre-autorización al juntar 29 protegidas. Con Chillán alertando dos o tres veces por noche se juntan en 11 a 13
   días (VIIRS) o hacia el 20 de noviembre (MODIS), casi todas de un solo volcán y de señales de 2 a 37 MW. Esas 29
   no prueban nada sobre una alerta de 1 MW en un volcán tranquilo.
3. **El encendido de VIIRS 375 (#974) no está listo para mergear tal como está.** Choca con main en la ficha y su CI es
   anterior a #982 y #984; cinco condiciones que la regla sellada pone «antes del merge» no están hechas; y publicaría
   con la posición «radiante» cuando la retrospectiva decidió con «cercano», sin decirlo en el PR. Esto último pierde
   0 de 44 protegidas con la tabla de MIROVA sola y 5 de 72 con el OCR, las 5 con distancia dudosa en MIROVA.
4. **El plan de reemplazo de la historia (#981) no se puede ejecutar como está.** Deja ciega la vigilancia de las dos
   guardias (sus controles pasan de 167 y 223 pares a 0) y corre la fecha de encendido de VIIRS al 2026-11-08, lo que
   mete noches reprocesadas en el disparador de reversión.
5. **La guardia K de VIIRS lleva 1 noche verde, no 3.** Antes del 2026-11-11 00:12 UTC sólo hubo corridas en falla.

## 2. Lo que decide Nicolás, con recomendación

| # | Decisión | Recomendación | Hallazgos verificados |
|---|---|---|---|
| 1 | Qué posición publica la vía en VIIRS 375 al encender B1: «radiante» (lo que hace hoy el código) o «cercano» (lo que juzgó la retrospectiva) | Antes de «mergea #974», mirar en las imágenes de MIROVA las 5 pasadas sólo OCR (Isluga 2026-03-20 05:06, Isluga 2026-03-24 05:30, Láscar 2026-03-15 05:00 y las 2 de octubre) y escribir la regla en el cuerpo del PR. Si las 5 son la fuente lejana, radiante sirve | 551, VC-01, VD-02, VD-03, VD-04 |
| 2 | Cambiar el plazo de la reversión pre-autorizada (MODIS §4.6 y VIIRS D3), sellado | Exigir protegidas de al menos dos volcanes, o contar Chillán con tope, además de las 29; es enmienda de una regla sellada, va con rótulo y fecha | 401, DEC-12, 451 |
| 3 | Hacer antes del merge las cinco condiciones de la regla de VIIRS §5 (prueba en navegador, paso de `nrt.yml`, tiempo del NRT, excepción §12.6, aviso a consumidores) o cambiar la regla | Hacerlas: la regla sellada las pone antes, y el paso de `nrt.yml` es el que pone rojo un error de la vía | 454, DEC-15 (frente B) |
| 4 | Rebasar #974 y #983 sobre main y repetir CI y verificador en la punta nueva | Sí, antes de la frase; el merge sería de un commit que nadie revisó | 458 |
| 5 | Mecanismo de reversión | Declarar el apagado del flag como camino principal: el `git revert` del PR B ya choca en 6 archivos sobre main y en 11 con VIIRS adentro, y la regla de MODIS todavía dice «hoy es limpio» | 403, 457, VA-01 |
| 6 | Reescribir el plan de reemplazo (#981) antes de ejecutarlo | Fijar el encendido por fecha explícita y no por el mínimo de `processed_utc`, y conservar el nulo de las guardias (o declarar su fin) | 405, 552, 553, VD-01, 554 |
| 7 | Vigilancia del caso «la vía calla y K también» | Agregar al vigilante diario la comparación directa de cada protegida de MIROVA contra la vía; hoy sólo la ve el audit semanal, hasta 7 días después | 402, 410 |
| 8 | Confirmar tres decisiones sin frase registrada | #937 (ablación de MODIS, en main desde el 2026-11-03), #972 (página preliminar de los 34, enlazada desde el tablero) y la fila 4 de VIIRS 750 | DEC-15 (frente A), DEC-7 (frente D), DEC-19 (frente B) |

Ninguna de estas decisiones pide tocar `pipeline/`, `data/` ni `frontend/` hoy. La 1, la 3 y la 4 van antes de
«mergea #974»; la 2 y la 5 antes de que se agote el plazo de MODIS (hacia el 2026-11-20).

## 3. Hallazgos confirmados, por frente

Gravedad del verificador. «En parte»: el verificador corrigió cifra o alcance, nunca el sentido.

**A, MODIS** (VA: 9 de 9 confirmadas, 6 con gravedad rebajada porque otro control cubre parte del daño).
- 401 y DEC-12 (2): plazo de 29 protegidas, 11 a 13 ya juntadas, todas de Chillán; agotarlo quita la
  pre-autorización, no la detección (la candidata se sigue informando).
- 402 (2): la vigilancia da VERDE si la vía calla una protegida que K tampoco publica (3 de 11 desde el encendido).
- 403 y VA-01 (2): el revert de #934 choca; el flag se revierte limpio.
- 405 (2): con #981 la vigilancia de la guardia de MODIS queda en VIGILANCIA_CIEGA (167 pares a 0).
- 410 (2): el único aviso de MODIS muerto volcán por volcán está dentro de la vigilancia de la guardia (simulado
  con Láscar).
- 412, DEC-10, DEC-15 (1): registro y premisas de documento.
- VA-02 (SOSPECHA, 1): tras un revert, el paso NRT a estándar re-escribiría con K la última noche de la vía.

**B, VIIRS** (VB: 14 filas, dos de ellas fundidas con su decisión, más VB-01; 6 confirmadas y 8 en parte, 0
refutadas).
- 451 (3): plazo de 11 a 13 días; aportan también Cordón Caulle (2 y 3 protegidas).
- 454 y DEC-15 (3): cinco condiciones de §5 sin hacer.
- 456 (3): el día del encendido la magnitud mostrada cambia entre 0,44 y 4,09 veces según el volcán (en Chaitén y
  Lastarria puede bajar) y el tablero sólo dibuja una línea.
- 452, 453 y DEC-6 (2): las cotas de investigación disparan por azar más de lo declarado (9 a 40 % según el modelo de
  la tasa); la cota (ii) de VIIRS 750 sale de un solo caso.
- 455 (2): protegidas probadas con la vía: 6 volcanes sin ninguna en VIIRS 375 y 7 en VIIRS 750.
- 457 (2): revertir B1 con B2 adentro choca en 11 archivos.
- 460, 463, DEC-19, VB-01 (2): la vía no deja record en 4,9 % de las pasadas de VIIRS 375; el lector de V375-E no
  está en main ni lo corre nadie; la fila 4 de VIIRS 750 sin frase; la guardia K de VIIRS sin corrida verde antes del
  11-11.
- 461, 458, DEC-14 (1).

**C, instrumento y retrospectiva** (VC: 21, 15 confirmadas y 6 en parte, 0 refutadas; nada cambia un veredicto de la
lectura).
- 501, DEC-2 y VC-01 (3): el brazo «radiante» de VIIRS 375 pierde 3 protegidas sólo OCR que K publica; el brazo que
  decide («cercano») no pierde ninguna. Las dejan fuera la exención N-3 y que el comparador sólo mira la regla del
  sensor.
- 502 (2): en VIIRS 750 «P2 GANA (B 17)» baja a EMPATE (B 9) sin las pasadas miradas por nombre; la fila es 4 igual.
- 503 y DEC-3 (2): el sorteo del §7 aprobado en S174 no se corrió; con «cercano», «GANA» sale por azar en 28,1 % en
  VIIRS 375 y 8,4 % en MODIS.
- 505 (2): el candado se arma desde la misma ref que compara; efecto medido 0.
- 509 (2): el nombre del veredicto de VIIRS 375 no dice que las 26 protegidas de F26 son de Láscar.
- 504, 506, 507, 508, 510, 511, 512, 513 a 517, DEC-7, DEC-9, VC-02, VC-03 (1).

**D, planes** (VD: 8 más 4 propios; 2 refutadas).
- 551 (3, en parte): ver decisión 1.
- 553 y VD-01 (3): el reemplazo de VIIRS corre el encendido al 2026-11-08 18:04 UTC y mete noches reprocesadas en el
  disparador.
- 552 (2): el reemplazo de MODIS deja ciega la vigilancia (no tapa una REVERSION_CANDIDATA; abre un issue diario).
- 554 (2, en parte): el plan sólo mide cobertura; los meses sí tienen lectura dentro de muestra (A/B), falta la de
  fuera de muestra.
- VD-02, VD-03, VD-04 (2), DEC-1 (2, en parte), DEC-7 (2).
- **Refutadas**: DEC-14 (la lectura con candado calculó también «radiante» y dio la misma fila 6) y DEC-17 (el orden
  de encendido está escrito como recomendación y tiene respaldo en la regla).

**Sin verificar** (gravedad 2 o menos fuera del corte del plan §3; se publican con su conteo): A 404, 406 a 409, 411,
413 a 416; B 459, 462, 464 a 466; D 555 a 564. Entre ellos, para leer antes de decidir: 409 y 462 (59 y 55 perfiles
de experimento corren la vía sin decirlo), 557 y 559 (el plan de los 34 quedó viejo y su fase 4 escribe en la carpeta
de la réplica) y 560 (Pages copia 586 MB que el tablero no lee).

## 4. Control ciego (línea base roja)

Defectos conocidos que no iban en los prompts (`docs/PLAN_AUDITORIA_S179.md` §3 y §9). Ningún agente abrió el plan
ni mis carpetas de medición: 0 llamadas de herramienta con `PLAN_AUDITORIA` o `_s179_perdidas`/`_s179_chillan` en
los ocho transcriptos.

| Frente | Reencontradas | Detalle |
|---|---|---|
| A | 2 de 2 | fila 4 de MODIS sin frase (406, sin verificar); el audit semanal sin juzgar hasta 15 noches (visto, juzgado «por diseño») |
| B | 1 de 3 | concentración de la evidencia (455). No reencontró el peligro de mergear #983 antes que #974 (lo nombró D, 556) ni la exposición por día de las cotas (la midió sana: ya estaba corregida antes del sello) |
| C | 3 de 3 | banda post hoc (510), «SIN SUSTRATO no bloquea» (506), poder de C-montaje (cita 12 de 343, 51 de 166 y 32 de 440, l. 316 a 317) |
| D | 3 de 4 | #981 pisaría 22 records de la vía (563), Pages cerca del límite (560), Tupungatito antes del 02-23 (555). No reencontró las alertas diurnas; las nombró el auditor A como seguimiento para D |

Salvedad declarada en §9: las líneas de B («14 casos, 12 de Chillán») y de D (Tupungatito) estaban en el bloque S179,
que era material de partida.

## 5. Para los planes (sobreviven a verificación)

- **Regla de reversión de MODIS**: corregir «hoy es limpio» (VA-01) y nombrar el apagado del flag; registrar #959
  (412).
- **Regla de reversión de VIIRS**: plazo por volcanes (451); cotas con su incertidumbre declarada como intervalo
  (453); la cota (ii) de VIIRS 750 marcada como de un caso; hacer o mover con frase las cinco condiciones de §5 (454).
- **PR #974 y #983**: rebasar, re-correr CI y verificador; cuerpo con la regla de posición (VD-03) y con el salto de
  magnitud esperado por volcán (456).
- **Vigilante diario**: protegida de MIROVA contra la vía sin pasar por K (402); aviso de MODIS muerto también fuera
  de la vigilancia de la guardia (410).
- **#981**: encendido por fecha explícita (553, VD-01); qué pasa con el nulo de las guardias (405, 552); lectura fuera
  de muestra de los meses reemplazados (554).
- **Lector de la retrospectiva** (para una próxima lectura, no cambia la actual): informar pérdidas sólo OCR de los dos
  brazos (VD-02, VC-01); correr el sorteo con la vía (503); candado contra un manifiesto de otra ref (505).

## 6. Registro de agentes

Esfuerzo y modelo leídos en cada transcripto (`~\.claude\projects\...\subagents\agent-<id>.jsonl`): todos los turnos
con `"effort":"high"` y el modelo pedido.

| Agente | Modelo | Tokens | Duración |
|---|---|---|---|
| Auditor A | claude-fable-5-2 | 603.787 | 41 min |
| Auditor B | claude-fable-5-2 | 500.760 | 28 min |
| Auditor C | claude-fable-5-2 | 542.527 | 43 min |
| Auditor D | claude-fable-5-2 | 581.105 | 34 min |
| Verificador A | claude-opus-5-5 | 272.408 | 13 min |
| Verificador B | claude-opus-5-5 | 356.398 | 17 min |
| Verificador C | claude-opus-5-5 | 394.170 | 26 min |
| Verificador D | claude-opus-5-5 | 326.695 | 15 min |
| **Total** | | **3.577.850** | |

Dentro del estimado (2,7 a 3,8 millones). Más la ola cortada del 2026-11-10 (A y C detenidos a los ~10 minutos a
pedido de Nicolás, sin informe). Cuota semanal de todos los modelos: 37 % al relanzar, 42 % a mitad de camino.

Incidente: el auditor D escribió cuatro JSON dentro de la instantánea compartida y los movió él mismo; comprobé los
1.247 archivos de la instantánea contra los blobs de `438a60a1e`: 0 distintos.
