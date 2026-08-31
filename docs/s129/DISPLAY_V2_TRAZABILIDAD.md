# S129 · V2 — Trazabilidad de cada número visible

Auditoría read-only de todo lo que muestra un número en las tres vistas live, **excepto las
tarjetas de `index.html`** (ya cubiertas en `AUDITORIA_TARJETAS.md`). No se implementó nada.

---

## 1 · Respuesta a la pregunta A10: sí, en tres lugares

Tres cifras visibles usan `record.vrp_mw` —la suma de toda la escena— donde el resto del
dashboard usa `primary_cluster.vrp_mw`. Ninguna se rotula como suma de escena.

| cifra | archivo:línea | qué usa | cuánto se desvía (medido) |
|---|---|---|---|
| **Gráfico «VRE acumulada» (GJ)** | `index.html:2786` | `r.vrp_mw` | **8× a 220×** el valor de la caja «VRE acumulada» de la misma pantalla |
| **Popup del mapa overview, «VRP final»** | `index.html:3146`, `3193` | `r.vrp_mw` | **21,4 %** de los popups muestran >2× el número del resto; PCC 55,9 % |
| **Tooltip y radio del scatter Distancia** | `index.html:2755`, `2901`, `2919` | `r.vrp_mw` (fallback a `pc.vrp_mw`) | mismo orden que el anterior |

El más grave es el primero, porque **es la misma magnitud calculada dos veces en la misma
vista**: la caja de estadística usa `eqVrp` (`index.html:1961-1966`), el gráfico usa la suma
cruda (`2786`). El operador ve «VRE acumulada 1.204 GJ» arriba y una curva que termina en
265.000 GJ abajo, ambas rotuladas VRE. Peor caso Nevados de Chillán 220×, mejor Láscar 8,1×.

*Verificado con* `scratchpad/tr.py` y `tr2.py` reimplementando `mirovaEqVrp` / `f5CoreMagnitude`
en Python sobre los 11 JSON operacionales (57.696 records).

---

## 2 · Tabla de trazabilidad

Convención de la columna «transformaciones»: **F5'** = Núcleo (solo VIIRS I-band) · **cap** =
piso de 50.000 MW · **far** = respeta el toggle lejanas · **art** = filtra artefacto
cirrus/difuso · **agr** = agrega sobre pasadas.

### `index.html`

| dónde se ve | campo JSON | transformaciones | archivo:línea |
|---|---|---|---|
| Barra de alertas, 5 contadores | `pc.vrp_mw` | `latestVRP`→`latestDetection`→`mirovaEqVrpDisplay`; F5' cap far art; **última** pasada de 48 h, no máximo | `3043-3062` / `1387-1441` |
| Caja «Max VRP» / «Promedio activo» | `pc.vrp_mw` | `eqVrp`; F5' cap far art; agr máx / media de la ventana | `1918-1920`, `1969-1970` |
| Caja «VRE acumulada» | `pc.vrp_mw` | `eqVrp` × 6 h × 3,6 | `1961-1966` |
| Cajas «Detecciones» / «Total granules» | conteo | `eqVrp>0` / `filtered.length` | `1971-1972` |
| Recall/Precision/F1/Ratio, ×3 sensores | `pc.vrp_mw` + CSV MIROVA | `computeMetrics`, **`mirovaEqVrp` sin F5'**; match ±60 min por bucket | `1198-1315`, `2036-2054` |
| Gráfico VRP (7 series por plataforma) | `pc.vrp_mw` | `eqVrp` + `toDailyMax`; F5' cap far art agr | `2665-2694`, `930-943` |
| **Gráfico VRE (curva)** | **`r.vrp_mw`** | ninguna salvo `isValidDetection`+sensor | **`2779-2790`** |
| **Scatter Distancia — tooltip VRP y radio** | **`r.vrp_mw`** | ninguna | **`2755`, `2901`, `2919`** |
| Scatter Distancia — eje Y | `final_hotspot_dist_km` (ancla honesta) → `hotspot_dist_km` | cascada S106; corta si `dist>innerKm` sin toggle | `2757-2765` |
| Gráfico Comparar — barra «VRP Chile» | `pc.vrp_mw` | `eqVrp`, máx diario **de los 3 sensores juntos** | `2807-2812` |
| Gráfico Comparar — línea MIROVA | `VRP_MW` del CSV | máx diario all-sensors, sin transformar | `944-958`, `2827-2836` |
| Tabla del detalle, col. VRP | `pc.vrp_mw` | `getDisplayVrp`→`eqVrp`; F5' cap far art. **Coincide con la tarjeta** (fix S106 P1.4) | `2140-2168`, `2253` |
| Tabla, col. Dist | ancla honesta → `hotspot_dist_km` → `anomaly_pixels[0]` → `vent_hotspot_dist_km`; `0,00` se imprime «cráter» | cascada, sin agregación | `2185-2196`, `2264` |
| Tabla, col. T max / T fondo | `t_max_k`\|`t_max_i04_k`, `t_bg_k` | −273,15 | `2169-2170`, `2266-2267` |
| Tabla, col. Píxeles | `pc.n_pixels` / `n_anomalous_pixels` | «cluster / total» | `2251-2253` |
| Tabla, col. Zona 🎯/📍 | `distance_class` | `isSummitDetection`; si far y toggle off → fila al 45 % | `2243-2249` |
| **Popup del mapa de detalle, «VRP MIROVA-equiv»** | **`pc.vrp_mw` crudo** | **ninguna: sin F5', sin cap** | **`2626-2627`** |
| Popup detalle, «Σ escena (diagnóstico)» | `r.vrp_mw` | rotulado explícitamente como no-VRP (S99) | `2612`, `2634-2636` |
| Popup detalle, «Este pixel» / «BT max» / «Distancia» | `anomaly_pixels[i].vrp_mw`, `.bt_k`, `.dist_km` | −273,15 en BT | `2638-2641` |
| Popup detalle, «✓ Confirmado por MIROVA @ N km» | `_mirova_confirmed`, `_mirova_dist_km` | derivados en cliente | `1320-1360`, `2626-2628` |
| Marcadores del mapa de detalle: posición | `final_hotspot_lat/lon` | cascada; **el gate de dibujo usa `r.vrp_mw>0`** (`2457`), no el clúster | `2455-2516` |
| Popup del volcán en el overview | `latestVRP` + `distanceCounts` | 🎯/📍 sobre **7 d fijos**, no la ventana del selector | `3225-3260`, `1521-1542` |
| **Popup de hotspot del overview, «VRP final»** | **`r.vrp_mw`** | ninguna | **`3146`, `3193`** |
| Tabla NRT global, col. VRP | `pc.vrp_mw` | **reimplementa** `mirovaEqVrpDisplay` a mano: F5' sí, **cap del núcleo no**, fallback a `r.vrp_mw` si `pc.vrp_mw==0` | `3298-3311`, `3350` |
| «Act: … UTC» | `d.updated` del JSON | corte a 16 caracteres | `1912-1915` |
| Reloj UTC | reloj del navegador | — | `3034-3040` |

### `diario.html`

| dónde se ve | campo JSON | transformaciones | archivo:línea |
|---|---|---|---|
| Barras del gráfico (3 buckets) | `pc.vrp_mw` | `eqVrpDisplay`; F5' cap art; **`includeFarDistance` es constante `false`** (`237`, sin control) | `414-435`, `372-375` |
| Líneas MIROVA (3 buckets) | `VRP_MW` del CSV | máx diario | `440-460` |
| Tooltip del gráfico | lo anterior | `toFixed(2)` MW | `475` |
| «Max VRP» / «mediana» de la tarjeta | `pc.vrp_mw` | `eqVrpDisplay`; **mezcla los 3 sensores**; mediana sobre máximos diarios | `500-540` |
| «MIROVA: n alertas» / «MIROVA dist» | filas del CSV con `vrp>0`; `Distancia_km` | mediana | `500-535`, `613` |
| `innerKm` del gate | **tabla hardcodeada** `INNER_RADIUS_KM` | verificada contra `volcanoes.yaml`: **los 11 coinciden hoy** | `227-231` |

### `mosaico.html`

| dónde se ve | campo JSON | transformaciones | archivo:línea |
|---|---|---|---|
| «N MW (48 h)» | `pc.vrp_mw` | `eqVrpDisplay`; F5' cap art; **máximo** de 48 h (index muestra la última) | `370-380`, `600` |
| Sparkline 30 d | `pc.vrp_mw` | máximo diario **mezclando los 3 sensores** | `500-526` |
| «Últ. detección: N h» | `datetime_utc` **del record de máximo VRP** | ver §4 | `377`, `648-651` |
| «Actualizado HH:MM UTC» | **reloj del navegador**, no `d.updated` | ninguna | `689-690`, `697-698` |

---

## 3 · Cifras que mezclan sensores sin decirlo

Cuatro, todas por agregación silenciosa: el sparkline de `mosaico` (`500-526`), «Max VRP» y
«mediana» de `diario` (`500-540`), y la barra «VRP Chile (max diario)» del gráfico Comparar de
`index` (`2807-2812`) —cuya contraparte MIROVA **sí** dice «all-sensors» en la etiqueta
(`2829`), asimetría que sugiere que la nuestra no lo hace. La medición de la auditoría de
tarjetas aplica igual acá: en el 62,9 % de los días-volcán con detección hay dos o más
sensores, y la razón entre el más alto y el más bajo del día tiene mediana 5,07×. El máximo
diario de esa mezcla es, en la práctica, «el número de VIIRS 375 m» sin que se diga.

Lo que **no** mezcla: el gráfico VRP principal de `index` (7 series separadas), las líneas
MIROVA de `diario`, y las métricas recall/precision (desglosadas desde S93).

## 4 · Cifras calculadas dos veces por caminos distintos

1. **VRE** — caja vs curva, 8-220× (§1). Es la discrepancia grande.
2. **La magnitud del popup del mapa vs la de la tabla/tarjeta**, para el mismo record: el
   popup imprime `pc.vrp_mw` crudo (`2626`). Difiere en 226-1.132 records por volcán;
   mediana 0,99× en la mayoría pero **0,59× en PCC, 0,67× en Chaitén, 0,72× en Isluga**, y
   hasta 3,16×. En VIIRS 375 m el popup y la tabla casi nunca dan lo mismo, porque la tabla
   pasó a F5' en S106 y el popup se quedó en el clúster.
3. **La tabla NRT reimplementa el helper en vez de llamarlo** (`3304-3311`). Hoy da lo mismo
   salvo dos bordes: no capa el núcleo a 50.000 MW, y si `pc.vrp_mw == 0` cae a `r.vrp_mw`
   mientras `mirovaEqVrp` sólo cae a la suma cuando **no existe** `primary_cluster`.
4. **El mapa de detalle decide qué dibujar con `r.vrp_mw > 0`** (`2457`) mientras todo lo
   demás usa el clúster. Medido: sólo **23 de 23.201** records summit dibujados tienen
   magnitud 0 en el resto del dashboard (0,1 %). Inconsistencia real, impacto despreciable.
5. **`mosaico` rotula «Últ. detección» el timestamp del máximo**, no el de la última pasada
   (`377`: `if (v > max) { max = v; ts = ... }`). Medido sobre 24.187 ventanas de 48 h con dos
   o más detecciones: en el **87,8 %** el máximo no es la detección más reciente (PCC 95,1 %).
   La etiqueta es incorrecta casi siempre.
6. **`mosaico` rotula «Actualizado» la hora en que cargó la página**, no la del dato. Un JSON
   congelado se lee como recién actualizado; `index` sí usa `d.updated`.

## 5 · Campos del JSON que no se muestran

Además de `_mirova_confirmed` —que en `index` sí se muestra, pero **sólo en el mapa** (anillo
verde `2603-2606` y línea del popup `2626`): no está en la tabla, ni en las cajas, ni en el CSV
exportado; y en `diario`/`mosaico` no se puebla, cosa que los comentarios `diario.html:334` y
`mosaico.html:326` declaran de forma explícita, así que no es un olvido—, ninguna de las tres
vistas muestra:

- **`n_hotspots_clustered`** — el conteo de regiones contiguas. Es exactamente la magnitud que
  MIROVA publica como `n_hotspots`, y el glosario del proyecto documenta que confundirla con
  `n_anomalous_pixels` produce el «factor 42». Tenemos el campo comparable y mostramos el que
  no lo es.
- **`product_version`** (`standard` / `nrt`) — el operador no puede saber si el número que mira
  vino de LANCE NRT o del producto estándar.
- **`nti_max`** y **`test1_k_observed`** — sólo salen en el CSV exportado (`3700`, `3703`).
  `nti_max` es el discriminante que las reglas A78/A80 usan para no creerle a una magnitud
  summit en un nevado; el operador no lo tiene a la vista.
- **`n_cloud_masked`**, **`n_excluded_water`**, **`sensor_zenith_deg`**, **`solar_zenith_deg`**,
  **`diag_vrp_floor_mw`** / **`diag_vrp_raw_mw`** (cuándo actuó el piso de VRP), y toda la
  familia `diag_*`.
- El **CSV exportado no contiene el número que el dashboard muestra**: lleva `vrp_mw` y
  `primary_cluster_vrp_mw`, pero no el Núcleo F5' ni el resultado de `eqVrp`. Quien descarga
  «los datos del gráfico» no puede reproducir el gráfico.

## 6 · Lo medido y lo inferido

**Medido** sobre los 11 JSON operacionales (57.696 records, script propio en scratchpad,
reimplementando los helpers del frontend en Python): los factores 8-220× de la VRE, el 21,4 %
de popups del overview >2×, el 0,1 % de fantasmas del mapa, el 87,8 % de etiquetas «Últ.
detección» incorrectas en `mosaico`, y la coincidencia exacta de `INNER_RADIUS_KM` de `diario`
con `volcanoes.yaml` (11/11).

**Inferido**: el impacto operativo de no mostrar `product_version` o `nti_max`. Y la
afirmación «`_mirova_confirmed` nunca se despliega» del encargo **no se confirma**: se
despliega en el mapa de `index`, aunque no en la tabla ni fuera de esa vista.
