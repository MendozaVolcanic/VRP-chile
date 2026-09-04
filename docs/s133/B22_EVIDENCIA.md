# S133 · B22 como banda primaria: la evidencia, y por qué el riesgo era menor de lo escrito

**Resultado: divergimos del paper en el 99,99 % de los records, y la métrica con que S131
propuso vigilar el cambio no puede mostrarlo.** El efecto esperado sobre el fondo es de
0,0036 K, dos órdenes de magnitud por debajo del redondeo con que lo persistimos.

Fuente de todos los números: `experiments/_s133/b22_evidencia.json` (regla S91).
Ventana 2025-02-15 a 2026-09-03, 11 Tier A, 11.786 records MODIS y 644.835 píxeles de
anomalía.

## El fenómeno

MODIS mira la ventana de 3,9 µm con dos detectores a la vez. Son la misma banda espectral
con dos ganancias distintas: B21 es de ganancia baja y aguanta hasta ~500 K sin saturar,
pero paga ese rango con ruido, 0,183 K de NEΔT. B22 es de ganancia alta, diez veces más
fina (0,017 K), y a cambio se satura apenas la escena pasa de ~331 K.

Para un volcán en erupción con lava expuesta esa diferencia es decisiva y hay que usar B21.
Para una noche cualquiera de un volcán chileno, donde el píxel más caliente de la escena
anda por los 281 K, B22 mide lo mismo con una décima parte del ruido.

Coppola lo resuelve construyendo una banda corregida. La cita, verificada contra el texto
del PDF y no contra una nota (A35), en `documentacion/sp426_5.txt` líneas 141-144:

> "we built a corrected spectral band centred at 3.959 mm (hereby called band L21ok), by
> using the L21 or L22 radiance, depending on band 22 saturation (or not), respectively."

El «respectively» empareja L21 con saturación y L22 con no-saturación: **manda B22, y B21
entra sólo donde B22 se saturó.** El repo hace hoy exactamente lo inverso.

## Cuánto importa: casi siempre, y casi nada

Las dos mitades de esa frase son igual de importantes.

**Casi siempre**, en cuanto a cobertura. La saturación de B22 es el único caso donde el
repo y el paper coinciden, y prácticamente no ocurre: de 644.835 píxeles de anomalía, **2**
superan los 331 K, y ninguno los 335 K. Un solo record de 11.786 tiene un píxel saturado.
El máximo histórico de `t_max_k` en todo el corpus es 334,4 K. O sea, la divergencia con el
paper no es un caso de borde: es el comportamiento normal del sistema.

**Casi nada**, en cuanto a efecto medible. Acá está la corrección al bloque de arranque, que
advertía que el cambio «mueve DETECCIÓN» porque la banda primaria decide el ruido del fondo
y por lo tanto dónde caen los umbrales N·σ. El mecanismo es correcto, pero la magnitud no se
había medido. `diag_sigma_bg_k` tiene mediana de 4,586 K y su valor **mínimo** observado en
todo el corpus es 0,996 K, ya 5,4 veces el NEΔT de B21. Ese sigma no mide ruido del sensor:
mide lo heterogéneo que es el terreno del anillo, nieve parcial y roca y hielo mezclados.
Restando en cuadratura el ruido instrumental, el sigma esperado tras el cambio de banda pasa
de 4,586 a 4,582 K.

Es la forma de A87 por el lado inverso: allá un flag apagado no probaba que el problema se
hubiera ido; acá un mecanismo real no prueba que el efecto sea observable. En los dos casos
lo que faltaba era medir el mecanismo en vez de razonarlo.

## Línea base, registrada ahora

`diag_sigma_bg_k` en MODIS, mediana por volcán, n = 11.786 en total:

| volcán | mediana (K) | volcán | mediana (K) |
|---|---|---|---|
| Isluga | 3,58 | NdC | 4,27 |
| Llaima | 3,76 | Chaitén | 4,89 |
| Copahue | 3,94 | Planchón-Peteroa | 5,12 |
| Villarrica | 4,04 | Láscar | 5,51 |
| PCC | 4,08 | Tupungatito | 6,01 |
| Lastarria | 4,08 | | |

Agregado: p10 2,905 · mediana 4,586 · p90 10,564. La serie mensual está en el JSON y sube
de 3,4 K en enero de 2026 a 6,9 K en julio, que es estacionalidad de la nieve del anillo,
no deriva del sensor.

## El cableado ya está, y es correcto

A diferencia del área, este flag **sí** está conectado (A89: se verificó cómo lo lee el
código, no cómo se llama). `pipeline/profile.py:552` lo lee; `merge_mir_bands`
(`pipeline/process_modis.py:315`) lo consume en **tres** puntos, no en uno:

| línea | qué alimenta |
|---|---|
| 542 | la radiancia MIR que va al VRP |
| 546 | la temperatura de brillo, que fija los umbrales y se reporta |
| 559 | la radiancia que entra al NTI |

O sea toca magnitud, detección y NTI a la vez. La caída a B21 es segura: `calibrate()`
convierte en NaN todo DN sobre 32767, que incluye el sentinel 65533 de detector saturado
(A37: el esquema es el de MODIS, no se extrapola de VIIRS).

## Validación propuesta, no corrida

Dos brazos con `data_subdir` aislado (A47), pares por **granule**, no por fecha. Láscar
n=50 porque es el más caliente y el de sigma más alto, y Villarrica n=50 porque es el
nevado de señal débil, que es donde un sigma menor movería un umbral si lo va a mover.
Cada criterio en las unidades de su propio objeto (A91):

- **C1, el fondo, en kelvin.** Mediana pareada de σ_ON − σ_OFF. Predicción −0,0036 K.
  **Falla si |mediana| > 0,05 K**, porque eso ya no sería ruido sino desacuerdo de
  calibración entre las dos bandas, y hay que entenderlo antes de adoptar.
- **C2, la detección, en pasadas.** Número de pares que cambian `triggered_test1`.
  Predicción 0. **Falla si se pierde una pasada que MIROVA publicó** (A79: verificar el
  evento concreto, no sólo la métrica agregada). Ganar detecciones no es falla; se reporta.
- **C3, la magnitud, en MW y en razón.** Mediana de la razón ON/OFF de `pc.vrp_mw` sobre
  los pares detectados en ambos brazos, banda 0,95-1,05, porque esto es un cambio de ruido
  y no de señal. La paridad contra MIROVA debe seguir dentro de 0,5-2,0.
- **C4, el control.** Píxeles con B22 saturada en la muestra: esperado 0 en Láscar, cuyo
  máximo histórico es 294,75 K sobre 930 records. Si da 0, el A/B aísla exactamente la
  diferencia entre bandas. Comparar con máscara explícita y nunca con `!=` sobre NaN, que
  es como C4 «falló» en S132 midiendo la semántica de pandas en vez del dato.

## Lo que queda para Nicolás

El flag está implementado, cableado y apagado. La evidencia dice que encenderlo nos alinea
con el paper en prácticamente todos los records y que el efecto medible sobre el fondo es
indistinguible de cero. Lo que **no** está medido es el efecto sobre la magnitud: las dos
bandas tienen calibraciones independientes, y si difieren en un pequeño sesgo relativo eso
sí se traslada al VRP. Por eso C3 existe y por eso el A/B vale la pena aunque C1 sea un
trámite.
