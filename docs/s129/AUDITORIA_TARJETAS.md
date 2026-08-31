# Auditoría de las tarjetas del dashboard — S129

**Pedido de Nicolás**: *«las tarjetas no dicen qué dato de qué sensor están reportando… quizás un
botón que cambie las tarjetas por sensor. Audita la forma en que mostramos los datos.»*

Auditoría read-only sobre `frontend/`. **No se implementó nada.**

---

## 1. Qué muestra cada tarjeta hoy, campo por campo

| Vista | Campos de la tarjeta | Dice el sensor |
|---|---|---|
| `index.html` (`buildCards`, l.1792-1887) | nombre · región · badge de nivel · **número MW grande** · píldoras de sensor · `◉/○ N km del cráter · N px` · fecha local + UTC · frescura de monitoreo | **Parcialmente y de forma engañosa** (ver §3) |
| `mosaico.html` (`renderMosaico`, l.592-660) | nombre · región · zona · **MW (48 h)** · badge · sparkline 30 d · «Últ. detección: N h» · frescura | **No, en absoluto** |
| `diario.html` (`renderCard`, l.558-664) | nombre · región · `n det. nuestras` · `MIROVA: n alertas` · `MIROVA dist` · `Max VRP` · `mediana` · frescura · gráfico | **No en el encabezado**; sí en el gráfico (3 barras por sensor, l.424-435) |
| `comparacion.html` | No tiene tarjetas por volcán: son pestañas con scatter **ya desglosado por sensor** (l.286-298). Preview S115, sin `mirovaEqVrp`. **Intencional, no se toca.** | Sí |

## 2. De dónde sale el número

**`index.html`** — `latestDetection` (l.1399) recorre las últimas 48 h, se queda con **la última pasada
con detección summit** y devuelve `mirovaEqVrpDisplay(r, innerKm, includeFar)` (l.1096). Ese helper
elige entre dos fórmulas:

- `mirovaEqVrp` (l.972) → **`primary_cluster.vrp_mw`** (no `record.vrp_mw`; regla A10 respetada),
  con cero si `distance_class != "summit"` o si `pc.centroid_dist_km > inner_radius_km`.
- `mirovaEqVrpCore` (l.1071) → recomputa el «Núcleo F5'» sumando `anomaly_pixels` dentro de 0,75 km
  del píxel de máxima energía. **Está activo por defecto** (`USE_F5_CORE = true`, l.1018).

**Y acá aparece el hallazgo más fuerte de esta auditoría**: `mirovaEqVrpCore` l.1082-1083 filtra
`if (!(s.startsWith("VIIRS") && !s.endsWith("_750"))) return base;`. Es decir, **el número de la
tarjeta se calcula con una fórmula distinta según el sensor**: VIIRS 375 m usa el Núcleo F5';
MODIS y VIIRS 750 m usan el clúster completo. La tarjeta no dice cuál de las dos aplicó. El botón
«Magnitud» del toolbar (l.567-571) tampoco lo aclara — sólo `diario.html:100` lleva ese matiz en el
tooltip.

**`mosaico.html`** — `latestVRP` (l.369) devuelve el **máximo** de 48 h, no la última pasada. Misma
métrica nominal, criterio distinto al de `index`: para el mismo volcán y el mismo instante, las dos
vistas pueden mostrar números diferentes sin que nada lo señale. El sparkline (l.500-524) es el
máximo diario mezclando los tres sensores en una sola barra.

**`diario.html`** — `computeStats` (l.500) calcula `Max VRP` y `mediana` sobre **todos los sensores
juntos**, mientras el gráfico de abajo los separa en tres colores. El encabezado y el gráfico de la
misma tarjeta hablan idiomas distintos.

## 3. Lo que el operador no puede saber mirando la tarjeta

Las píldoras de sensor de `index.html` son la **unión de los sensores con detección válida en 48 h**
(`latestSensors`, l.1443-1457), mientras el número grande viene de **una sola pasada**. Ver tres
píldoras encendidas y «0,42 MW» no significa que los tres midieran 0,42: significa que uno de los
tres lo midió y no se dice cuál. Sobre los 11 Tier A, **el 62,9 % de los días-volcán con detección
tienen dos o más sensores activos** (3.235 de 5.145), y en esos días **la razón entre la lectura más
alta y la más baja del día tiene mediana 5,07× y percentil 90 de 41×**. El número mostrado no es
representativo del día: es uno de varios que difieren en un factor de cinco.

Peor: en **564 de esos 5.145 días (11 %) la última detección del día es MODIS**, que es justamente
donde la lectura es menos interpretable — a 1 km el foco sub-píxel débil y el gradiente topográfico
son indistinguibles (A82), y el ground truth de MIROVA para MODIS es casi inexistente fuera de
Láscar: de 96 alertas MODIS en la referencia, **88 (92 %) son de Láscar**; Chaitén tiene 3,
Villarrica 1, Nevados de Chillán 1, y los otros seis **cero**. Un «0,4 MW MODIS» en Villarrica no es
una señal débil: es una lectura **indefinida**, sin nada contra qué contrastarla.

Preguntas legítimas que la tarjeta hoy no contesta:

1. ¿De qué sensor viene el número? → no se puede saber.
2. ¿Con qué fórmula se calculó (Núcleo F5' o clúster)? → depende del sensor, y no se dice.
3. ¿Es la última pasada o el máximo del período? → depende de la vista, y no se dice.
4. ¿Hubo otras pasadas ese día y qué midieron? → invisible.
5. ¿MIROVA confirmó esta detección? → `_mirova_confirmed` se puebla en `index.html:1348-1356` pero
   **no se muestra en la tarjeta**; en `mosaico`/`diario` ni siquiera se puebla.
6. Distancia y `n px` sí están en `index` (l.1857-1866), pero faltan en `mosaico` y `diario`.

**Y hay un hallazgo que cambia la pregunta**: el filtro por sensor **ya existe** en `index.html`. La
`sensor-legend` (l.572, construida en `buildLegend`, l.3007-3031) es clickeable y propaga el toggle a
las tarjetas, la barra de alertas y el mapa (l.3022-3025), vía `isSensorVisible` (l.1474). Nicolás no
la reconoció como filtro, y con razón: está al final de un toolbar de cinco grupos, es el **único
grupo sin `<label>`** (los otros dicen «Escala», «Distancia», «Pixels», «Magnitud»), y se ve como
leyenda de gráfico. La funcionalidad está; la señal de que es un control, no.

## 4. Tres alternativas

**A — Etiquetar el número (mínima, la que más rinde por peso).** Bajo el MW, una línea:
`VIIRS 375 m · 03:41 UTC · Núcleo F5'`. La píldora del sensor que produjo el número va en sólido; las
otras, atenuadas, con `title` «detectó en las últimas 48 h, no es este número». Y ponerle
`<label>Sensores</label>` a la leyenda para que se lea como filtro.
*Gana*: contesta las preguntas 1, 2 y 4 sin cambiar ninguna métrica. *Contra*: no permite comparar
sensores lado a lado; suma dos líneas a una tarjeta de 150 px. *Costo*: bajo en `index`, medio en
`mosaico`/`diario` (hay que propagar el sensor por `latestVRP`/`computeStats`, que hoy no lo
devuelven).

**B — Botón que cambia las tarjetas por sensor (lo que propone Nicolás).** Un selector
`Todos · VIIRS 375 · VIIRS 750 · MODIS` sobre la grilla. En `index` es casi gratis: reusar
`sensorVisible` en modo exclusivo y ascender la leyenda a control con etiqueta. En `mosaico` y
`diario` hay que replicar el estado y el helper.
*Gana*: el operador puede aislar VIIRS 375 m —el sensor con ground truth real— y ver el resto como
contexto. *Contra*: es **modal**; con el filtro en MODIS una tarjeta puede quedar en «—» y leerse
como «volcán tranquilo» cuando en realidad es «este sensor no vio nada». Exige un rótulo persistente
del filtro activo y un estado explícito «sin pasada MODIS», distinto de «sin detección». *Costo*:
medio, ×3 vistas.

**C — Tarjeta de tres filas, una por sensor.** Fila por sensor con su MW, su hora y su distancia;
sin número único. Es lo que ya hace el gráfico de `diario`.
*Gana*: elimina la ambigüedad de raíz y hace visible la discrepancia de 5×, que es información
diagnóstica real. *Contra*: rompe la lectura de un vistazo de 45 tarjetas, que es el propósito de la
grilla; triplica la altura; obliga a redefinir el color del borde (¿nivel de qué sensor?). *Costo*:
alto.

**Recomendación**: A como base (contesta lo que Nicolás pidió y no puede empeorar nada), B encima si
quiere el filtro. C sólo para la vista de detalle, no para la grilla.

## 5. Carga y accesibilidad

**El filtrado por sensor no cuesta descarga.** `mosaico` y `diario` ya bajan `<vol>_recent.json`
(100 días, `scripts/build_recent_json.py:33`), que conserva todos los campos incluido `sensor` — el
dato para filtrar ya está en memoria. Ninguna de las tres propuestas agrega un fetch.

Corrección al supuesto del encargo: los JSON completos **no son de 13-17 MB**, son de **19 a 32 MB**
(PCC 32, Villarrica 28, Chaitén 25), **255 MB los 11**. El comentario de `build_recent_json.py:6` que
dice «13-17 MB» y «~171 MB» quedó desactualizado desde S120. Los `_recent` sí son livianos
(`pages-deploy.yml:73` estima ~27 MB los 11).

Accesibilidad: las píldoras y la leyenda distinguen sensores **sólo por color** (naranjo/rosado/cian,
`index.html:700-703`) — ilegible para un daltónico; cualquier propuesta debe llevar el texto del
sensor, no sólo el color. La leyenda es un `<div>` con `click`, sin `role`, sin `tabindex` y sin
estado ARIA: no se puede operar con teclado.

## 6. Verificaciones (A48)

- Fórmula por sensor: `sed -n '1071,1090p' frontend/index.html` → filtro `!s.endsWith("_750")`.
- Píldoras = unión 48 h: `sed -n '1443,1457p' frontend/index.html`.
- `index` = última detección vs `mosaico` = máximo: `index.html:1399` vs `mosaico.html:369`.
- Filtro por sensor ya existente: `grep -n sensorVisible frontend/index.html` → 12 usos, ninguno en
  `mosaico`/`diario`.
- Multi-sensor 62,9 % / mediana 5,07× / 11 % MODIS: recorrido de los 11 JSON replicando
  `mirovaEqVrp` con el `inner_radius_km` de `volcanoes.yaml`.
- Ground truth MODIS: conteo de `data/mirova/*.json` por campo `sensor` → 88/96 en Láscar.
- Tamaños: `stat` sobre `data/mirova_equivalent/*.json`.
