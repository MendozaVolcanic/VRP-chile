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
cobertura, no detección. Los 10.756 records nocturnos de la ventana llevan la marca de K (0 sin marca).

### 2. Dos mecanismos, y uno domina

| mecanismo | pasadas | protegidas (≥ 1 MW) |
|---|---:|---:|
| **M3**: el detector alerta un píxel en el cráter, pero su magnitud queda en 0,0 MW y el tablero lo oculta (`isValidDetection` pide `pc.vrp_mw > 0`) | **55** | 0 |
| **M1**: el detector no alerta ningún píxel en toda la escena | **20** | 1 |

Ninguna pérdida cae en las otras condiciones del predicado (alerta sólo lejos, artefacto del tablero, cúmulo fuera
del inner). La única protegida es Puyehue Cordón Caulle del 2026-10-10 05:54 (1,19 MW), que es #865, ya explicado y
cerrado; no se reabre.

**M3 es D25, el cráter en 0,0 MW** (`docs/MIROVA_DIVERGENCES.md`, D25, registrada en S138). Físicamente: en una cumbre
fría el píxel del cráter es apenas más tibio que sus vecinos inmediatos, lo que basta para que su NTI resalte y el
segundo pase lo acepte; pero su temperatura en el infrarrojo medio queda **por debajo** de la mediana del anillo de 5 a
25 km, que está lleno de terreno más bajo y más tibio. La resta píxel menos fondo sale negativa, se recorta a cero, y
el tablero no publica un cúmulo de 0 MW. MIROVA, que según el paper toma como fondo la media de los vecinos del píxel (D25), publica
en esas mismas pasadas entre 0,09 y 0,60 MW (mediana 0,24). Medido (`anatomia_salida.txt`):

- las 55 tienen el píxel más cercano al cráter con BT de M13 igual o menor que `t_bg_k` (en las 249 publicadas pasa en
  6, todas con otro píxel más tibio en el cúmulo);
- 54 de las 55 salen **sólo** de la recaptura del segundo pase, sin ningún píxel del primero;
- medianas: fondo 265,8 K en M3 contra 265,5 K en publicadas, pero BT del píxel del cráter 263,7 K contra 270,8 K.

El mismo patrón aparece donde MIROVA no vio nada: 68 de 5.994 negativos limpios (1,1 %), contra 55 de 324 positivas
(17 %). Pesa más en unos volcanes que en otros: es M3 en 18 de las 41 positivas de Isluga, 11 de las 13 de Tupungatito,
4 de las 9 de Planchón Peteroa y 11 de las 167 de Láscar.

**M1**: las 20 son de cenit alto (mediana 44°, contra 21° en M3 y 24° en las publicadas), con el máximo de M13 de la
escena a una mediana de 23,7 km del cráter y NTI máximo de −0,917. Con los campos persistidos no se puede separar
entre señal bajo el umbral, geometría oblicua (D17) o un píxel del foco sin NTI: eso es lo que mide el probe de abajo.

### 3. En noches, el operador casi no pierde nada (A94)

De las 75 pasadas perdidas, **74** caen en una noche en que el mismo volcán sí publica por otra vía: 59 sólo por
VIIRS 375, 12 por otra pasada de VIIRS 750 y 3 por MODIS y VIIRS 375. Sólo **una** deja la noche del volcán sin
ninguna publicación: Planchón Peteroa, 2026-08-15 05:06, M1, 0,09 MW.

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
atrapadas por aserción); C-P1 (el control reproduce el record persistido: si falla, la pasada se informa y no se
interpreta); C-NULO (sin ningún `nti_perdido` en la escena, relleno = control exacto); y el grupo C, donde el relleno
no debería apagar publicaciones.

**Regla de lectura.** Una pasada P con C-P1 en verde:
- **el lector decide** si publica con relleno y no con control;
- **toca** si tiene al menos un `nti_perdido` en la ventana; **toca el foco** si el más caliente de M13 lo tiene.
El agregado compara «toca» entre P y C: si la tasa es parecida, los sentinelas no explican la pérdida aunque estén.

**Predicciones.** PM-1: casi todos los `nti_perdido` son 65533 con máscara 256 y tienen un píxel válido más cerca que
la mitad del espaciado típico (duplicado del bowtie), y sólo aparecen fuera del nadir. PM-2: el lector decide en 0 a
2 de las 75. PM-3: M3 no cambia con el relleno (su causa es el fondo, D25).

## Resultado del probe

(pendiente)

## Lo que esto no decide

No propone ningún cambio. M3 cae en el frente de D25, cuyo A/B corre la sesión dueña del loop; este informe no lo
toca ni lo adelanta. Los volcanes de los 34 sin cron no entran.
