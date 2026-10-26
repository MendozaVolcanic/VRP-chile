# S158: por qué VIIRS 750 publica menos de lo que MIROVA alerta con el detector K

> Investigación de sólo lectura, rama `s158-v750-recall`, cortada de `main` en `8471add4` (toda la serie de
> `data/mirova_equivalent/` es K desde el 2025-02-15). No toca `pipeline/` ni `data/`. Cada número de este informe sale
> de un script de esta carpeta y de su salida commiteada al lado (`*_salida.txt`).

## Por qué

El auto-audit semanal (#864) marcó el recall de VIIRS 750 en 73,3 % (n = 30 noches, banda 79,5 %), y el banco de
paridad con K da 0,77 por pasada contra 0,93 en VIIRS 375. Antes de buscar una palanca hay que saber en qué etapa se
pierde cada alerta: si el detector no vio nada, si vio algo y quedó lejos del cráter, o si vio el cráter y el tablero
lo ocultó. Y había una sospecha sin verificar, del probe de saturación de #880: píxeles con M15 (la banda térmica) en
sentinela y M13 (la del infrarrojo medio) sano. El lector los deja en NaN, y sin M15 el píxel no tiene NTI y no puede
alertar aunque esté caliente.

## Qué se midió, sin red

Ventana 2026-03-01 a 2026-10-21, la del banco de paridad; referencia de MIROVA del snapshot del repo (consolidado
`bbf50461`, OCR `ed8be00e`, los sha de blob van en la salida). Lectura A (alerta del scraper; `ALERTA_SIN_GEOMETRIA_OCR`
fuera), regla SN de D-9 aplicada explícitamente (en VIIRS 750 no toca ninguna pasada: el script lo comprueba con una
aserción). «Publica» = predicado del tablero ejecutado con node desde `frontend/index.html` (A97), con cada condición
por separado.

| script | salida | qué responde |
|---|---|---|
| `listar_perdidas.py` | `listar_perdidas_salida.txt`, `perdidas_v750.json` | cada alerta perdida, su mecanismo y su detalle |
| `anatomia.py` | `anatomia_salida.txt` | de qué etapa sale el píxel y si queda bajo el fondo; mismo conteo en publicadas y en negativos |
| `noches.py` | `noches_salida.txt` | cuántas pérdidas dejan la noche del volcán sin ninguna publicación (A94) |

### 1. El recall se reproduce

324 pasadas de VIIRS 750 con alerta de MIROVA y record nuestro a ±2 min; publicamos 249 y perdemos **75** (recall
0,7685, idéntico al del banco). Hay además **1** alerta sin record nuestro (Láscar, 2026-03-11 06:18, OCR, 2,0 MW): es
cobertura, no detección, y es **protegida**; su noche la publican VIIRS 750 en otra pasada, VIIRS 375 y MODIS
(`noches_salida.txt`). Los 10.756 records nocturnos de la ventana llevan la marca de K (0 sin marca).

### 2. Dos mecanismos, y uno domina

| mecanismo | pasadas | protegidas (≥ 1 MW) |
|---|---:|---:|
| **M3**: el detector alerta un píxel en el cráter, pero su magnitud queda en 0,0 MW y el tablero lo oculta (`isValidDetection` pide `pc.vrp_mw > 0`) | **55** | 0 |
| **M1**: el detector no alerta ningún píxel en toda la escena | **20** | 1 |

Ninguna pérdida cae en las otras condiciones del predicado (alerta sólo lejos, artefacto del tablero, cúmulo fuera
del inner). La única protegida es Puyehue Cordón Caulle del 2026-10-10 05:54 (1,19 MW), que es #865, ya explicado y
cerrado; no se reabre.

**M3 tiene el patrón de D25, el cráter en 0,0 MW** (`docs/MIROVA_DIVERGENCES.md`, D25, registrada en S138). Físicamente: en una cumbre
fría el píxel del cráter es apenas más tibio que sus vecinos inmediatos, lo que basta para que su NTI resalte y el
segundo pase lo acepte; pero su temperatura en el infrarrojo medio queda **por debajo** de la mediana del anillo de 5 a
25 km, que está lleno de terreno más bajo y más tibio. La resta píxel menos fondo sale negativa, se recorta a cero, y
el tablero no publica un cúmulo de 0 MW. MIROVA, que según el paper toma como fondo la media de los vecinos del píxel (D25), publica
en esas mismas pasadas entre 0,09 y 0,60 MW (mediana 0,24). Lo que sigue describe el patrón; **que el fondo por vecinos
devuelva estas alertas no está medido acá** (eso es lo que mide el A/B de D25 que corre la sesión dueña del loop). Medido (`anatomia_salida.txt`):

- las 55 tienen el píxel más cercano al cráter con BT de M13 igual o menor que `t_bg_k` (en las 249 publicadas pasa en
  6, todas con otro píxel más tibio en el cúmulo). Ojo: esto es consecuencia de la fórmula y no una medición
  independiente, porque con un solo fondo y el exceso recortado a cero, un cúmulo de 0,0 MW implica BT bajo el fondo
  (verificador);
- 54 de las 55 salen **sólo** de la recaptura del segundo pase, sin ningún píxel del primero;
- medianas: fondo 265,8 K en M3 contra 265,5 K en publicadas, pero BT del píxel del cráter 263,7 K contra 270,8 K.
  Esto sí es información: **el fondo es el mismo y lo que cambia es el píxel**, más frío en las perdidas. No es que el
  anillo de esas pasadas esté más tibio que en las publicadas, sino que el píxel que alerta queda bajo un fondo de
  nivel normal.

El mismo patrón aparece donde MIROVA no vio nada: 68 de 5.994 negativos limpios (1,1 %), contra 55 de 324 positivas
(17 %). Pero ese contraste mide sobre todo cuán seguido el detector alerta algo: **condicionado a que haya algún píxel
alertado, M3 es 55 de 304 en positivas (18 %) contra 68 de 183 en negativos limpios (37 %)**. O sea que despegar del
cero a todas las M3 publicaría proporcionalmente más pasadas donde MIROVA calla que donde alerta, lo mismo que midió
S145 en el bloque de D25 del catálogo. Pesa más en unos volcanes que en otros: es M3 en 18 de las 41 positivas de Isluga, 11 de las 13 de Tupungatito,
4 de las 9 de Planchón Peteroa y 11 de las 167 de Láscar.

**M1**: 11 de las 20 tienen cenit de 35° o más y 9 están bajo 35° (mediana 43°, contra 21° en M3 y 24° en las
publicadas); el máximo de M13 de la escena está a una mediana de 23,6 km del cráter y el NTI máximo es −0,92. El cenit
se correlaciona, pero no explica las 20. Con los campos persistidos no se puede separar
entre señal bajo el umbral, geometría oblicua (D17) o un píxel del foco sin NTI: eso es lo que mide el probe de abajo.

### 3. En noches, el operador casi no pierde nada (A94)

De las 75 pasadas perdidas, **74** caen en una noche en que el mismo volcán sí publica por otra vía: 59 sólo por
VIIRS 375, 12 por otra pasada de VIIRS 750 y 3 por MODIS y VIIRS 375. Sólo **una** deja la noche del volcán sin
ninguna publicación: Planchón Peteroa, 2026-08-15 05:06, M1, 0,09 MW. Y la cobertura no depende de cómo se define
la noche: en 74 de las 75 **la misma pasada** (mismo satélite, ±2 min) publica en banda I, VIIRS 375 (55 de 55 en M3,
19 de 20 en M1).

## Probe L1B: M15 en sentinela junto al cráter (escrito ANTES de correr)

`probe_m15.py` (detalle en su docstring), pasadas de `seleccionar_pasadas.py` (`pasadas.json`, sin elegir a mano):
grupo **P**, las 75 perdidas con record; grupo **C**, por cada una la positiva publicada del mismo volcán y satélite más
cercana en el tiempo, sin repetir (52: en Isluga, Tupungatito y Planchón Peteroa no alcanzan). 127 pasadas, 116
gránulos. Workflow `.github/workflows/probe-s158-v750-m15.yml` en la rama de disparo `s158-v750-probe` (no se mergea),
grupo de concurrencia propio, autenticación sólo por `EARTHDATA_TOKEN` (A71).

Por pasada: ventana = píxeles a `inner_radius_km` o menos del ancla de detección. Cuenta los sentinelas de M15 y M13
por código, las máscaras 4 (Saturation), 256 (Bowtie_Deleted) y 2048 (Dead_Detector) de M15, la BT cruda de M15 sobre
342,5 K, y `nti_perdido` (M13 válido y M15 NaN según el lector del pipeline). Dice si el píxel de M13 más caliente de
la ventana tiene `nti_perdido`, y a qué distancia está el píxel válido más cercano de cada perdido. Luego corre el
procesador de producción dos veces: **control** tal cual y **relleno**, donde cada `nti_perdido` recibe en M15 la media
de sus vecinos 3×3 válidos (el contrafactual «si el lector no hubiera borrado ese M15»), y aplica el predicado del
tablero a los dos records.

**Por qué puede ser inocente.** El UserGuide de VIIRS L1B (agosto de 2021, §2.3) dice que el borrado del bowtie se hace
a bordo para las bandas M de ganancia simple, y que la agregación de las de doble ganancia (M13 lo es) se hace en
tierra. Si M13 conserva el píxel duplicado del bowtie y M15 no, ese terreno lo ve el barrido vecino y no se pierde
nada. La cobertura y el código 65533 lo distinguen.

**Controles.** C-SIN (`prueba_probe_m15.py`, corrido local: OK; 4 mutaciones del contador, el relleno y la cobertura
atrapadas por aserción, corridas a mano y sin script commiteado; el verificador aplicó 5 propias y las 5 fallan por
aserción); C-P1 (el control reproduce el record persistido: si falla, la pasada se informa y no se
interpreta); C-NULO (sin ningún `nti_perdido` en la escena, relleno = control exacto); y el grupo C, donde el relleno
no debería apagar publicaciones.

**Regla de lectura.** Una pasada P con C-P1 en verde:
- **el lector decide** si publica con relleno y no con control;
- **toca** si tiene al menos un `nti_perdido` en la ventana; **toca el foco** si el más caliente de M13 lo tiene.
El agregado compara «toca» entre P y C: si la tasa es parecida, los sentinelas no explican la pérdida aunque estén.

**Predicciones.** PM-1: casi todos los `nti_perdido` son 65533 con máscara 256 y tienen un píxel válido más cerca que
la mitad del espaciado típico (duplicado del bowtie), y sólo aparecen fuera del nadir. PM-2: el lector decide en 0 a
2 de las 75. PM-3: M3 no cambia con el relleno (su causa es el fondo, D25).

## Resultado del probe (run 39597022719, 2026-10-21, `806c50c2`; mini probe de M13, run 39600656583)

Salidas: `analizar_probe_salida.txt` (`analizar_probe.py resultado`), artefactos en `resultado/` y `resultado_m13/`.

- **Cobertura.** 125 de 127 pasadas medidas. Faltan 2 del grupo P, Isluga 05:48 y Chillán 05:54 del 2026-10-12, ambas
  de Suomi NPP: CMR no devolvió el L1B (los jobs 2 y 3 salieron en rojo sólo por eso, salida 2 de S141). Las dos son
  pérdidas de 0,24 y 0,40 MW (M3 y M1).
- **Controles.** C-SIN en verde en los 4 runners. C-P1 en verde en **125 de 125**: el control reproduce el record
  persistido, y el control publica en las 52 de C y en ninguna de las 73 de P, igual que el tablero.
- **El lector no borra el NTI de ningún píxel con M13 válido.** En la escena entera de cada uno de los 125 gránulos hay
  **0** píxeles con M13 válido y M15 NaN (una dirección: M15 NaN implica M13 NaN). En la ventana del cráter los dos
  conjuntos coinciden exactamente en las 125 (`n − m13_valido == n − m15_valido ==` número de 65533, verificador). No hay
  ningún píxel con la máscara 4 (Saturation), ninguno con la 2048 (Dead_Detector) ni ninguno con M15 sobre 342,5 K.
- **Los sentinelas de M15 son el bowtie y aparecen igual en P que en C.** Todos los sentinelas de la ventana son 65533
  (Bowtie_Deleted, con máscara 256), 1.280 píxeles en 24 pasadas de P y 1.036 en 12 de C. Aparecen en **todas** las
  pasadas con cenit de 35° o más (P 24 de 24, C 12 de 12) y en **ninguna** bajo 35°. Es geometría del barrido, no
  una propiedad de las pasadas que perdemos.
- **Por qué el «M13 sano» de #880 no era cierto** (mini probe, los tres gránulos de mayor cenit de `pasadas.json`,
  todos de Chillán, 65° a 68°). En el L1B de NASA, M13, que es la banda de doble ganancia, viene como entero de 32 bits
  con sus propios códigos: `valid_max` 327670, `flag_values` 327677 (Missing_EV), 327678 (Bowtie_Deleted) y 327679
  (Cal_Fail), `_FillValue` 327680. En el **100 %** de los píxeles de esas escenas donde M15 trae 65533 (1,32 a 1,34
  millones por escena), M13 trae **327678** con el flag 256. El probe de #880 buscó en M13 los sentinelas de 16 bits
  (65532 a 65535), no encontró ninguno y lo leyó como «M13 sano». Las dos bandas están borradas en el mismo píxel, como
  dice el UserGuide, y ese terreno lo cubre el barrido vecino.
- **El contrafactual no tuvo nada que rellenar**, así que el brazo relleno nunca se ejercitó sobre datos reales y C-NULO
  pasa de forma trivial; no hay control positivo del brazo en un gránulo real (no cambia la conclusión, que sale de los
  conteos). Como no hay ningún `nti_perdido`, el brazo relleno es idéntico al
  control en las 125 (C-NULO 125 de 125), y **el lector decide en 0 de 73** pérdidas medidas. PM-1 se cumple en lo que
  predecía (65533, máscara 256, sólo fuera del nadir); su parte de cobertura no se pudo medir porque no hubo perdidos.
  PM-2 (0 a 2) se cumple con 0. PM-3 se cumple: ninguna M3 cambia.

**Respuesta.** Ninguna de las alertas de VIIRS 750 que K no publica se pierde por el lector de M15. La pérdida es de
D25 (55 de 75: el cráter en 0,0 MW por el fondo del anillo) y de pasadas en que el detector no alerta ningún píxel (20 de 75, más frecuentes con cenit alto, pero
9 de ellas bajo 35°). Y
para el operador casi no hay pérdida: 74 de las 75 caen en noches que otro sensor u otra pasada sí publica.

**Hallazgo lateral, latente y sin efecto hoy.** `FLAG_DNS` de `pipeline/process_viirs_mod.py` es el conjunto de 16
bits (65532 a 65535). Para M13 no atrapa ningún código real; los códigos de M13 se descartan sólo porque la LUT vale
−999,9 en ellos y el lector borra toda BT negativa. Si un gránulo viniera sin LUT de M13, la rama de inversión de Planck
los leería como radiancia válida (327678 × 0,00162 ≈ 530 W m⁻² sr⁻¹ µm⁻¹). Los tres gránulos del mini probe traen la LUT de M13 (327.681 entradas), y en los 125 del probe el lector dejó M13 en NaN en todos
los píxeles con M15 = 65533 de la escena, y exactamente en ellos dentro de la ventana del cráter (en la escena entera,
la igualdad exacta sólo está medida en los 3 del mini probe), que es lo que hace la rama de la LUT. Queda
como seguimiento; acá no se toca `pipeline/`.

## Verificador con contexto limpio (2026-10-21, en primer plano)

Re-corrió sin red `listar_perdidas.py`, `analizar_probe.py` y `prueba_probe_m15.py` (salidas idénticas byte a byte) y
comprobó los números de `anatomia` y `noches`. Confirmó el predicado del tablero (node sobre `frontend/index.html`),
que los 27 sha de los records descienden de la adopción de K (`34cea39e`), el monkeypatch del lector
(`process_viirs_mod.py:494`), la lectura de M13 = 327678 y el hallazgo lateral contra el código. Refutó o rebajó
cuatro frases, ya corregidas arriba: el «cenit alto» de M1 (9 de 20 bajo 35°; la mediana era la superior, ahora
`statistics.median`), «BT ≤ fondo» presentado como medición (es tautológico), el contraste con negativos sin
condicionar (18 % contra 37 %), y la igualdad «exacta» de M13 y M15 en la escena entera. Agregó la alerta protegida sin
record y la cobertura por la misma pasada en banda I, hoy calculadas por `noches.py` y `anatomia.py`.

## Lo que esto no decide

No propone ningún cambio. M3 cae en el frente de D25, cuyo A/B corre la sesión dueña del loop; este informe no lo
toca ni lo adelanta. Los volcanes de los 34 sin cron no entran.
