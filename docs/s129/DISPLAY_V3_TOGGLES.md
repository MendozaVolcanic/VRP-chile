# S129 · V3 — Los toggles y sus promesas

Auditoría read-only de `frontend/index.html`, `diario.html` y `mosaico.html`. Método: por
cada control seguí su `addEventListener`, anoté qué funciones de render llama, y lo resté
del conjunto de funciones que **leen la variable** de ese control (mapeo línea→función con
un script propio sobre el archivo, no a ojo).

---

## 1. La promesa rota de mayor impacto

**La barra «Estado actual» (`#alert-summary`, `index.html:3043`) queda congelada cuando el
operador toca «Solo cráter / Incluir lejanas» o «Magnitud: Cluster / Núcleo F5'».**

`buildAlertSummary()` cuenta cuántos volcanes hay en Alto / Moderado / Bajo / Muy Bajo /
Sin datos, y lo hace con `latestVRP(d.records, includeFarDistance, innerKm)`
(`index.html:3053`), que a su vez pasa por `mirovaEqVrpDisplay` (`index.html:1409`) — o sea
depende de **los dos** toggles. Pero los tres únicos llamadores de `buildAlertSummary()` son
la leyenda de sensores (`:3026`), el arranque (`:3642`) y el poll de 5 min, que además
**sólo re-renderiza si llegó dato nuevo** (`:3676`, `if (changed.length === 0) return`).

Verificado: el handler de distancia (`:3505-3523`) llama `buildCards`, `buildOverviewMap`,
`renderDetail`; el de magnitud (`:3542`) llama esos tres más `buildNRTTable`. Ninguno llama
`buildAlertSummary`.

La barra está **arriba de los controles** (`:528` vs `:530`) y es lo primero que se lee. Al
pasar de Núcleo F5' a Cluster, la magnitud de un volcán de halo glaciar sube ~10×
(Villarrica, `docs/F5_CALIBRATION_S95.md`) y puede cruzar el umbral de nivel: las tarjetas
cambian de color, el contador de arriba no. **Dos lecturas contradictorias del estado del
sistema en la misma pantalla, y la de arriba puede quedar mal durante horas.**

---

## 2. Inventario de controles

| Vista | Etiqueta en pantalla | id | Variable | Default |
|---|---|---|---|---|
| index | `Período` (select, 10 opciones) | `days-select` | `currentDays` | 30 d |
| index | `Lineal` / `Logarítmica` | `btn-linear`/`btn-log` | `logScale` | lineal |
| index | `🎯 Solo cráter` / `📍 Incluir lejanas` | `btn-summit-only`/`btn-include-far` | `includeFarDistance` | solo cráter |
| index | `⊙ Solo principal` / `⊛ Todos los pixels` | `btn-primary-pixel`/`btn-all-pixels` | `onlyPrimaryPixel` | principal |
| index | `▣ Cluster` / `◎ Núcleo F5'` | `btn-mag-cluster`/`btn-mag-core` | `USE_F5_CORE` | Núcleo |
| index | leyenda MODIS / VIIRS375 / VIIRS750 / MIROVA ref. | `sensor-legend` | `sensorVisible` | los 4 visibles |
| index | `🔥 Anomalías` | `hotspot-layer-btn` | `showHotspots` | apagado |
| index | `Todos los volcanes` (select) | `hotspot-volcano-filter` | (lee del DOM) | todos |
| index | `⬚ Footprint` | `footprint-btn` | `useFootprintMarkers` | punto |
| index | pestañas VRP / Distancia / VRE / MIROVA | `.chart-tabs` | `activeTab` (local) | VRP |
| diario | `🎯 Solo cráter` / `📍 Incluir lejanas` | mismos ids | `includeFarDistance` | solo cráter |
| diario | `📈 Escala: Lineal` | `btn-scale` | `currentScale` | lineal |
| diario | `▣ Magnitud: Cluster` | `btn-mag` | `USE_F5_CORE` | Núcleo |
| mosaico | `▣ Cluster` | `btn-mag` | `USE_F5_CORE` | Núcleo |

---

## 3. La matriz control × panel (index.html)

✅ depende y se refresca · ❌ **depende y NO se refresca** · ⊘ el panel no lee la variable
(exento estructural) · — no aplica.

| Control | Barra alertas | Tarjetas | Mapa gral (marcadores) | Capa anomalías | Tabla NRT global | Stats detalle | Métricas/sensor | Gráf. principal | Gráf. secundario | Mapa detalle | Tabla detalle |
|---|---|---|---|---|---|---|---|---|---|---|---|
| **Solo cráter / lejanas** | ❌ | ✅ | ✅ | ⊘ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Magnitud Cluster/Núcleo** | ❌ | ✅ | ✅ | ⊘ | ✅ | ✅ | ✅ | ✅ | ✅ | ⊘ | ✅ |
| **Leyenda de sensores** | ✅ | ✅ | ✅ | ✅ | ⊘ | ⊘ | ⊘ | ✅ | ✅ | ⊘ | ⊘ |
| Período | — | ⊘ | ⊘ | ✅ | ⊘ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| Escala lin/log | — | — | — | — | — | — | — | ✅ | ✅ | — | — |
| Solo principal / todos px | — | — | — | ⊘ | — | — | — | — | — | ✅ | — |
| Footprint | — | — | — | ✅ | — | — | — | — | — | ✅ | — |
| Capa 🔥 Anomalías | — | — | — | ✅ | — | — | — | — | — | — | — |
| Filtro por volcán (mapa) | — | — | — | ✅ | — | — | — | — | — | — | — |

Las tres filas en negrita son los hallazgos. Los `❌` salen del set-difference:
`includeFarDistance` se lee en `buildAlertSummary:3053` y `buildNRTTable:3297`, y ninguno de
los dos está en el handler `:3505-3523`; `USE_F5_CORE` llega a la barra vía
`latestVRP→latestDetection:1409` y el handler `:3542` no la re-renderiza.

**Los `⊘` de la fila de sensores son la segunda familia**: no es que falte un
`buildNRTTable()` en el handler — es que **la tabla NRT global no lee `sensorVisible` en
ninguna línea**, y el **mapa de anomalías del detalle** tampoco. `hotspots` se arma en
`index.html:2456` con `.filter(r => (r.vrp_mw ?? r.vrp_mir_mw ?? 0) > 0)` y nada más.
Apagar MODIS lo saca de las tarjetas, la barra, los gráficos y la capa del mapa general,
pero **el mapa del volcán que estás mirando sigue dibujando sus puntos naranjas**, y la
tabla «Últimas detecciones NRT» sigue listando filas `MODIS_*`. Dado que MODIS aporta ~450
puntos por volcán a 15-25 km sin confirmación MIROVA (contexto S129), apagarlo es
exactamente el gesto que un operador haría — y el panel donde más importa es el que lo
ignora. Verificado con `grep -n "isSensorVisible" index.html`: 9 ocurrencias, ninguna entre
las líneas 2456-2660 ni 3276-3378.

---

## 4. Persistencia — negativo limpio

No queda ningún desajuste de clave. Extraje todas las llamadas de lectura/escritura de las
cuatro vistas y las pareé: `vrp_log_scale`, `vrp_include_far`, `vrp_footprint_markers`,
`vrp_f5_core`, `vrp_sensors_v3`, `diario_include_far`, `diario_f5_core`,
`mosaico_f5_core` — todas se escriben y se leen con el mismo string. El caso histórico
(`vrp_sensors` escrito vs `vrp_sensors_v3` leído) está corregido y documentado en
`index.html:3019`. `vrp_post_s38_only` sólo se borra, nunca se lee.

Dos precisiones sobre el enunciado del encargo: **es `sessionStorage`, no `localStorage`**
(`index.html:773-791`), o sea la config muere al cerrar la pestaña — decisión deliberada
según el comentario. Y las claves **no se comparten entre vistas**: «🎯 Solo cráter» en
`index` guarda en `vrp_include_far` y en `diario` en `diario_include_far`, así que el mismo
control con la misma etiqueta puede estar en estados opuestos en dos pestañas abiertas.
`mosaico` directamente **no tiene** el control y fuerza summit (`eqVrpDisplay:366` llama
`mirovaEqVrp(r, innerKm, false)`).

Inconsistencias menores de qué se persiste: en `index` no se persisten `onlyPrimaryPixel`
ni `showHotspots` ni `days-select`; en `diario` no se persiste la escala mientras sí las
otras dos.

## 5. Estado inicial — correcto en las tres vistas

`index` sincroniza los botones con los flags persistidos en `:3560-3576` (escala, distancia,
magnitud), el footprint en `:3472`, y la leyenda aplica la clase `dim` al construirse
(`:3012`). `diario` sincroniza en dos `DOMContentLoaded` (`:701`, `:721`) y sus toggles
recargan la página, lo que los hace **inmunes por construcción** al bug de propagación.
`mosaico` corrige la etiqueta en `_syncMagBtn()` antes de renderizar. No encontré ningún
caso de «el botón dice una cosa y el filtro hace otra» al cargar.

## 6. Controles sin afordancia — y una etiqueta que promete de más

- **`sensor-legend`** (`:572`): tiene `cursor:pointer` (`:54`) pero **ningún `title`** y,
  a diferencia de los otros cuatro grupos, **ningún `<label>` que lo nombre** — los demás
  dicen «Escala », «Distancia », «Pixels », «Magnitud »; éste sólo flota a la derecha con
  `margin-left:auto`. Es el control más potente de la barra y el único que no se anuncia.
- **`hotspot-legend`** (`:589`): tres puntos de colores VIIRS375 / VIIRS750 / MODIS,
  visualmente casi idénticos a los de `sensor-legend`, y **no es clickeable**. Dos leyendas
  gemelas, una filtra y la otra no.
- **Etiqueta que promete de más**: en `index` el botón dice `◎ Núcleo F5'` y su tooltip
  (`:566`) no menciona el alcance; pero `mirovaEqVrpCore:1082` devuelve el valor base si el
  sensor no es VIIRS I-band. En un volcán dominado por MODIS/VIIRS750 el toggle **no cambia
  nada** y no hay forma de saber por qué. `diario.html:100` sí lo dice: «(solo VIIRS375)».
- **Tooltip falso al usuario**: el `title` del grupo Distancia (`index.html:557`) afirma que
  «Las detecciones lejanas siguen visibles en el mapa y en la tabla pero atenuadas». En la
  tabla sí (`:2246`); **en el mapa no** desde S26 B, que hace `return` en `:2539`. El
  contexto S129 ya marcaba el comentario de código `:809-811`; esto es la misma afirmación
  falsa pero **visible al operador**.

## 7. Lo que verifiqué y no es bug

- `buildOverviewMap()` termina llamando `updateHotspotLayer()` (`:3272`), así que la leyenda
  de sensores y el toggle de distancia **sí** alcanzan la capa de anomalías del mapa
  general de forma transitiva. Un `grep` del nombre no lo mostraba (A89).
- El toggle de escala de `diario` no actualiza el gráfico del modal (`charts` no contiene
  `modalChart`, `:747`), pero el modal es un overlay fijo `inset:0 / z-index:2000`
  (`diario.html:69`) que tapa la barra de controles: **inalcanzable en la práctica**.
- `Período` no re-renderiza tarjetas ni tabla NRT, y está bien: ambas usan ventanas fijas
  (`CARD_COUNT_WINDOW_DAYS = 7`, decisión F30 Bug 11b; cutoff de 7 d en `:3287`).
- `comparacion.html` tiene sus propios controles (3 pestañas, 2 selects, toggle PCC) pero es
  preview declarado; fuera de alcance por regla del proyecto.
