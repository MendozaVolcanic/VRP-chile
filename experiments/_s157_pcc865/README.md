# S157, issue #865: por qué K no publica PCC en VIIRS 750 el 2026-10-10 05:54 UTC

Investigación de sólo lectura. No toca `pipeline/` ni `data/`. Decisión de Nicolás del 2026-10-19: no revertir,
investigar.

## El fenómeno, primero

Esa madrugada MIROVA vio en Puyehue-Cordón Caulle una anomalía de 1,19 MW (alerta protegida; clase «Bajo» en su
tabla, «Thermal anomaly: LOW» en la cabecera de la imagen) a 7,83 km del centro de su grilla. En el píxel de 750 m es
una señal tenue: el NTI máximo de la escena es −0,906, cerca del piso, y el pico de la anomalía está a 277,7 K contra
271,85 K del fondo (el píxel más tibio del ROI, 281,53 K, está a 13,38 km y no es la anomalía). Lo que la delata no es
la temperatura sino el contraste con los vecinos: dos píxeles contiguos de la misma columna brillan un poco más en el
infrarrojo medio que lo que su infrarrojo térmico predice.

El detector compara cada píxel con el promedio de sus 8 vecinos (dNTI, dETI). Cuando la anomalía ocupa DOS píxeles
contiguos, cada uno entra en el promedio del otro y le baja el contraste. Coppola 2016a prevé justo eso con el
«segundo pase» (recalcular excluyendo los ya detectados). En nuestro código ese pase corre aunque el primero quede
vacío (`enable_second_pass_conditioned: false`), pero si no hay píxeles activos no excluye a nadie del promedio: el
dNTI sale igual que en el primer pase, el umbral `max` también, y vuelve a fallar.

## Mecanismo, con evidencia (probe por etapa, A75)

`probe_etapas_pcc.py` (run 39511620897, artefacto copiado en `probe_out/`) bajó el mismo granule
(VJ202MOD.A2026283.0554.021.2026283113526) y corrió el procesador cuatro veces cambiando sólo los dos flags de K que
llegan a VIIRS 750. Control: el brazo K reproduce el record de producción y el brazo C0 el de la sombra (los dos `True`).

| brazo | conectiva | Test 1 | 1.er pase | activos tras el 2.º pase (recaptura) | cúmulo | tablero (node) |
|---|---|---|---|---|---|---|
| K (producción) | max | no | 0 | 0 (0) | ninguno | no publica |
| C0 (sombra) | min | sí | 2 | 8 (6) | 1,886 MW, 4 px, `ctx_cluster` | publica |
| min sin Test 1 | min | no | 2 | 8 (6) | 1,886 MW, 4 px, `ctx_cluster` | publica |
| max con Test 1 | max | sí | 0 | 0 (0) | 2,629 MW, 24 px, `test1_roi` | publica |

La palanca es la **conectiva**: `min` sin Test 1 da exactamente lo de C0. El Test 1 dispara en C0 pero no hace el
cúmulo publicado (sale de la ruta contextual); sólo publicaría en el brazo que lo junta con `max`.

Qué test falla, píxel por píxel (umbrales de la cumbre, PCC tiene `inner_radius_km` 20; mu y sigma del pool del primer
pase, iguales en los cuatro brazos: dNTI 0,0028313, dETI 0,00083119):

| píxel (fila, col) | BT (K) | dNTI | umbral K (max) | falta | dETI | umbral K | compuerta BT 274,85 |
|---|---|---|---|---|---|---|---|
| 2736, 1989 (pico, 0,22 km del ancla) | 277,70 | 0,01332 (4,70 sigma) | 0,01415 (5 sigma) | 0,00083 (5,9 %) | 0,00537 | 0,00416 pasa | pasa |
| 2735, 1989 (contiguo) | 276,20 | 0,01204 (4,25 sigma) | 0,01415 | 0,00211 (14,9 %) | 0,00725 | 0,00416 pasa | pasa |

Con `min` el umbral es el piso C1 = 0,003 y los dos pasan holgados. **Lo único que falla en K es el Test 2 (dNTI) del
primer pase**: el Test 3, la compuerta de BT y el tablero no intervienen. El segundo pase no rescata porque, sin
píxeles activos, recalcula el mismo dNTI contra el mismo umbral. Si los dos píxeles se excluyeran mutuamente del
promedio (lo que pasa en C0, donde el primer pase sí los marca), su dNTI subiría a 0,01476 y 0,01422, sobre el umbral
del segundo pase con `max` (0,01410), por 4,7 % y 0,9 %: la anomalía queda a un pelo de pasar en los dos sentidos.

Corrección a lo que decía el issue: el cúmulo de C0 **no lo abrió el Test 1** (sale de la ruta contextual, fuente
`ctx_cluster`; el Test 1 integrado disparó pero no aporta píxeles ni magnitud a ese record).

## ¿Caso aislado o clase? (`buscar_clase.py`, 2026-01-10 a 2026-10-19)

K = histórico reprocesado con K (`data/_s154_reproc_k_historico/`) más los records con `regimen` de producción; C0 =
producción en el tag `pre-s153-adopcion-k` más la sombra. Pareo por volcán y sensor a ±120 s, predicado del tablero con
node, protegida = lectura A.

Sólo pasadas nocturnas (el pareo de `vigilancia_sombra.pasadas_de_alerta` salta las diurnas).

- **Protegidas VIIRS 750: K pierde 1 de 155**, y es ésta. «De 155» incluye 1 sin record en ningún lado (Láscar,
  2026-03-11, 2,0 MW) y 5 de enero sin record de C0; entre las que tienen los dos records, la única pérdida es ésta.
  En VIIRS 375 K pierde 5 de 159 que C0 publica (fuera del alcance de este issue, SIN REVISAR).
- **Bajo 1 MW: 20 de 138** alertas VIIRS 750 que C0 publica y K no (Isluga 11, PCC 6, Planchón 2, Chillán 1; 18 desde
  abril). En 10 el record de K está vacío y en 10 K tiene píxeles que el tablero no publica. **No es el mismo mecanismo
  que el caso principal**: en 18 de los 20 el primer pase de C0 también estaba vacío y C0 publicó por el segundo pase
  sin semilla (sin compuerta de BT, contra el piso 0,003). En el caso principal C0 sí tuvo 2 píxeles en el primer pase.
- **Salvedad de régimen (A104, A85)**: el C0 de esta comparación no es un solo detector. Hasta el 2026-10-14 sale del
  tag y la mayoría de esos records los escribió código anterior (sin `processed_utc`), mientras que K es un reproceso
  uniforme. Parte de las 20 puede venir de cambios de código y no de K. Puede explicar también por qué el A/B de meses
  de S151 (abajo, mismo código en los dos brazos) ve sólo 4 alertas bajo 1 MW perdidas entre abril y agosto y esta
  búsqueda cuenta 18 desde abril hasta octubre (SIN VERIFICAR).

## Palanca y costo (`costo_palanca_v750.py`, sobre la tabla del A/B de meses de S151)

Esa tabla tiene los dos brazos sin Test 1 y distintos sólo en la conectiva, o sea «K con `min` en VIIRS 750». De abril
a agosto de 2026: `min` publica 4 alertas más (151 a 155 de 200; 0 protegidas, las 64 las publican los dos) y **314
negativos limpios más** (41 a 355 de 3.828, 1,1 % a 9,3 %). PCC es el peor: 21 a 152 de 341 (6,2 % a 44,6 %). Volver
VIIRS 750 a `min` cambia una protegida en diez meses por unos 60 negativos limpios publicados al mes. Los brazos son
`_s146_ab_sin_test1` (B) y `_s147_ab_sin_test1_max` (F), corridos en septiembre; lo que cambió después en VIIRS 750 está
tras flags apagados o es sólo de MODIS, así que «B es K con `min`» se sostiene, sin estar demostrado.

## Verificador con contexto limpio

Confirmó el probe (flags que llegan, envoltorios en la llamada correcta, control), los márgenes, que el Test 1 no hace
el cúmulo de C0, los números de la clase (re-corrida idéntica) y la lectura del costo. Refutó tres frases de la
primera versión, ya corregidas arriba: que el segundo pase «necesita semilla» (corre igual, sólo que sin activos no
cambia nada), que la alerta fuera «Muy Bajo» (es «Bajo»; Muy Bajo es la de VIIRS 375 de la misma pasada, 0,39 MW) y
que 277,7 K fuera el píxel más tibio (lo es de la anomalía; el del ROI es 281,53 K a 13,38 km). Agregó las salvedades
de la clase (pasadas nocturnas, pasadas sin record, C0 heterogéneo, mecanismo distinto en las 20 de bajo 1 MW).

## Lo no verificado

- El margen píxel a píxel de las 20 pérdidas bajo 1 MW (sólo los diagnósticos del record), y cuántas son efecto de K
  y cuántas de la heterogeneidad del C0.
- El costo en negativos de encender el Test 1 en VIIRS 750 con `max` (el brazo que también publicaría aquí): ningún
  A/B lo aisló.
- Las 5 protegidas de VIIRS 375 que K pierde.

## Archivos

`comparar_records.py` (y `_salida.txt`): los dos records campo por campo. `probe_etapas_pcc.py` y
`.github/workflows/probe-s157-pcc865.yml`: el probe (se dispara por push a esta rama). `probe_out/`: su salida.
`predicado_brazos.py`: el predicado del tablero sobre los brazos. `buscar_clase.py`: la clase. `costo_palanca_v750.py`:
el costo.
