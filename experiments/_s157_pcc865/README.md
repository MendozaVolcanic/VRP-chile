# S157, issue #865: por qué K no publica PCC en VIIRS 750 el 2026-10-10 05:54 UTC

Investigación de sólo lectura. No toca `pipeline/` ni `data/`. Decisión de Nicolás del 2026-10-19: no revertir,
investigar.

## El fenómeno, primero

Esa madrugada MIROVA vio en Puyehue-Cordón Caulle una anomalía de 1,19 MW (alerta protegida, Muy Bajo/LOW) a 7,8 km
del centro de su grilla. En el píxel de 750 m es una señal tenue: el NTI máximo de la escena es −0,906, cerca del piso,
y el píxel más tibio está a 277,7 K contra 271,85 K del fondo. Lo que la delata no es la temperatura sino el contraste
con los vecinos: dos píxeles contiguos, uno al lado del otro en la misma columna del barrido, brillan un poco más en el
infrarrojo medio que lo que su infrarrojo térmico predice.

El detector compara cada píxel con el promedio de sus 8 vecinos (dNTI, dETI). Cuando la anomalía ocupa DOS píxeles
contiguos, cada uno entra en el promedio del otro y le baja el contraste. Coppola 2016a prevé justo eso con el
«segundo pase» (recalcular excluyendo los ya detectados), pero el segundo pase necesita una semilla: algún píxel que
haya pasado el primero.

## Mecanismo, con evidencia (probe por etapa, A75)

`probe_etapas_pcc.py` (run 39511620897, artefacto copiado en `probe_out/`) bajó el mismo granule
(VJ202MOD.A2026283.0554.021.2026283113526) y corrió el procesador cuatro veces cambiando sólo los dos flags de K que
llegan a VIIRS 750. Control: el brazo K reproduce el record de producción y el brazo C0 el de la sombra (los dos `True`).

| brazo | conectiva | Test 1 | 1.er pase | 2.º pase | cúmulo | tablero (node) |
|---|---|---|---|---|---|---|
| K (producción) | max | no | 0 | 0 | ninguno | no publica |
| C0 (sombra) | min | sí | 2 | 8 | 1,886 MW, 4 px, `ctx_cluster` | publica |
| min sin Test 1 | min | no | 2 | 8 | 1,886 MW, 4 px, `ctx_cluster` | publica |
| max con Test 1 | max | sí | 0 | 0 | 2,629 MW, 24 px, `test1_roi` | publica |

La palanca es la **conectiva**: `min` sin Test 1 da exactamente lo de C0. El Test 1 dispara en C0 pero no hace el
cúmulo publicado (sale de la ruta contextual); sólo publicaría en el brazo que lo junta con `max`.

Qué test falla, píxel por píxel (umbrales de la cumbre, PCC tiene `inner_radius_km` 20; mu y sigma del pool del primer
pase, iguales en los cuatro brazos: dNTI 0,0028313, dETI 0,00083119):

| píxel (fila, col) | BT (K) | dNTI | umbral K (max) | falta | dETI | umbral K | compuerta BT 274,85 |
|---|---|---|---|---|---|---|---|
| 2736, 1989 (pico, 0,22 km del ancla) | 277,70 | 0,01332 (4,70 sigma) | 0,01415 (5 sigma) | 0,00083 (5,9 %) | 0,00537 | 0,00416 pasa | pasa |
| 2735, 1989 (contiguo) | 276,20 | 0,01204 (4,25 sigma) | 0,01415 | 0,00211 (14,9 %) | 0,00725 | 0,00416 pasa | pasa |

Con `min` el umbral es el piso C1 = 0,003 y los dos pasan holgados. **Lo único que falla en K es el Test 2 (dNTI) del
primer pase**: el Test 3, la compuerta de BT y el tablero no intervienen. Y el segundo pase no rescata porque arranca
sin semilla: si los dos píxeles se excluyeran mutuamente del promedio, su dNTI subiría a 0,01476 y 0,01422, sobre el
umbral del segundo pase (0,01410), por 4,7 % y 0,9 %.

Corrección a lo que decía el issue: el cúmulo de C0 **no lo abrió el Test 1** (sale de la ruta contextual, fuente
`ctx_cluster`; el Test 1 integrado disparó pero no aporta píxeles ni magnitud a ese record).

## ¿Caso aislado o clase? (`buscar_clase.py`, 2026-01-10 a 2026-10-19)

K = histórico reprocesado con K (`data/_s154_reproc_k_historico/`) más los records con `regimen` de producción; C0 =
producción en el tag `pre-s153-adopcion-k` más la sombra. Pareo por volcán y sensor a ±120 s, predicado del tablero con
node, protegida = lectura A.

- **Protegidas VIIRS 750: K pierde 1 de 155**, y es ésta. En VIIRS 375 K pierde 5 de 159 que C0 publica (fuera del
  alcance de este issue, SIN REVISAR).
- **Bajo 1 MW: 20 de 138** alertas VIIRS 750 que C0 publica y K no (Isluga 11, PCC 6, Planchón 2, Chillán 1; 18 desde
  abril). En 10 el record de K está vacío como en éste (misma firma; el margen píxel a píxel NO está medido); en las
  otras 10 K tiene píxeles que el tablero no publica (otro mecanismo).

## Palanca y costo (`costo_palanca_v750.py`, sobre la tabla del A/B de meses de S151)

Esa tabla tiene los dos brazos sin Test 1 y distintos sólo en la conectiva, o sea «K con `min` en VIIRS 750». De abril
a agosto de 2026: `min` publica 4 alertas más (151 a 155 de 200; 0 protegidas, las 64 las publican los dos) y **314
negativos limpios más** (41 a 355 de 3.828, 1,1 % a 9,3 %). PCC es el peor: 21 a 152 de 341 (6,2 % a 44,6 %). Volver
VIIRS 750 a `min` cambia una protegida en diez meses por unos 60 negativos limpios publicados al mes.

## Lo no verificado

- El margen píxel a píxel de las otras 19 pérdidas bajo 1 MW (sólo la firma del record).
- El costo en negativos de encender el Test 1 en VIIRS 750 con `max` (el brazo que también publicaría aquí): ningún
  A/B lo aisló.
- Las 5 protegidas de VIIRS 375 que K pierde.

## Archivos

`comparar_records.py` (y `_salida.txt`): los dos records campo por campo. `probe_etapas_pcc.py` y
`.github/workflows/probe-s157-pcc865.yml`: el probe (se dispara por push a esta rama). `probe_out/`: su salida.
`predicado_brazos.py`: el predicado del tablero sobre los brazos. `buscar_clase.py`: la clase. `costo_palanca_v750.py`:
el costo.
