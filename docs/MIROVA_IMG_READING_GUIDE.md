# Cómo leer las imágenes de mirovaweb.it correctamente

> Documento creado tras múltiples errores de interpretación en sesiones S27-S29.
> Leer ANTES de descargar/analizar imágenes online.

## Ubicación de las imágenes

URL pattern verificado:
```
https://www.mirovaweb.it/OUTPUTweb/MIROVA/{SENSOR}/VOLCANOES/{VolcanName}/{VolcanName}_{SENSOR}_{Plot}.png
```
- SENSOR: `VIIRS375`, `VIIRS750`, `MODIS`
- Plots: `Latest10NTI`, `Dist`, `VRP`, `logVRP`
- VolcanName usa el formato MIROVA. NevadosDeChillan = `ChillanNevadosde` (apellido invertido).

Por volcán × sensor hay **4 plots**. Total para Tier A 11 × 3 sensores × 4 = 132 imágenes.

## Anatomía de cada plot

### Header común (todos los plots)

```
[VolcanName] - [Title] - [SENSOR]
Last Update: DD-MMM-YYYY HH:MM:SS    Thermal anomaly: [STATUS]
```

- **Status posibles**: `NONE`, `VERY LOW`, `LOW`, `MODERATE`, `HIGH`. Color verde/amarillo/naranja/rojo.
- **Última lectura**: caja arriba a la izquierda con miniatura NTI + `VRP=X MW` o `VRP=NaN MW`. NaN = sin detección o nube.
- Una `★` verde marca la última detección en los plots temporales.

### Plot `Dist` (Distance vs Time)

**Eje Y**: km del vent (0–25 km).
**Eje X**: dos paneles temporales **DIFERENTES** — leer cuál estás mirando ANTES de concluir nada.

| Panel | Rango temporal | Uso |
|---|---|---|
| **"Last Month"** (arriba) | ~30 días | **El que importa para auditoría reciente** |
| **"Last Year"** (abajo) | 365 días | Contexto histórico — comprime 365d en mismo eje X que mes |

**Líneas verticales (stems)** = una detección por línea.

**Colores**:
- 🔴 **ROJO**: detección dentro del threshold MIROVA (típicamente <3km, <5km, <7km, <20km según el volcán). Estos NO son automáticamente "alertas reales" — son **candidatos cercanos**. MIROVA los re-categoriza después como ALERTA_TERMICA o FALSO_POSITIVO.
- ⚫ **NEGRO**: detección fuera del threshold. Son **candidatos lejanos**, casi siempre FPs.

**Threshold del volcán** aparece en la leyenda del plot (ej `<5km` Lascar, `<20km` PCC, `<3km` Lastarria/Planchón). Coincide con `inner_radius_km` de nuestro `volcanoes.yaml`.

### Plot `VRP` (Radiative Power vs Time)

**Eje Y**: VRP en Watts (notación `×10^6` = MW). Cuidado con la escala — varía por volcán.

**Stems verticales** = barras de magnitud por detección. Mismo código colores rojo/negro.

Última lectura: caja arriba con `VRP = N MW`.

### Plot `logVRP`

Mismo que `VRP` pero escala log. Útil para ver detecciones débiles que en lineal se aplastan al cero.

### Plot `Latest10NTI`

Grid de 10 thumbnails de los últimos 10 granules procesados. Cada uno:
- Imagen NTI (Normalized Thermal Index) cropeada al cráter.
- Etiqueta `VRP = N MW` debajo.
- Fecha + ZEN (zenith angle) + AZI (azimuth).

`VRP=NaN MW` = sin detección (nubes, fuera de pasada, no anomalía).

## Reglas de oro para no equivocarse

### Regla 1 — SIEMPRE lee el panel "Last Month", no el "Last Year"

El panel anual comprime tanto que cualquier densidad >50% en el eje temporal **se ve como saturación visual**. Cuando ves "decenas de stems rojos al día" en Last Year, casi siempre son **~1 detección real cada pocos días** repartida en 365 días.

**Ejemplo error**: en S27 leí Lastarria Last Year y dije "MIROVA detecta diariamente" → falso. El CSV mostró 71 alertas en 90d = 1 cada 1.3 días en promedio, NO diario.

### Regla 2 — Rojo NO significa "alerta real"

Rojo solo significa **distancia <threshold**. La separación real ALERTA vs FP la hace MIROVA después y aparece en el CSV consolidado (`Tipo_Registro`).

**Distribución típica** (según CSV):
- ALERTAS reales: bunching cerca del vent (<2 km usualmente).
- FPs cercanos: en zonas pobladas/lagos pero dentro del threshold.
- FPs lejanos (negros): >threshold.

Para distinguir alerta vs FP en una imagen Dist NO se puede a simple vista — solo lo dice el CSV. Las imágenes muestran **candidatos**, no veredictos.

### Regla 3 — `Thermal anomaly: MODERATE/LOW/HIGH` ≠ "actividad real ahora"

El status arriba lo calcula MIROVA con todas las detecciones recientes (incluidas FPs). Un volcán con muchos FPs persistentes puede mostrar `LOW/MODERATE` en el header sin tener actividad volcánica real.

**Ejemplo**: Llaima muestra `MODERATE 11-22 MW` pero el CSV consolidado tiene **0 alertas reales** y **36 FPs**. Las stems rojas que ves en el plot son los FPs.

### Regla 4 — VRP del header (caja arriba izquierda) = última lectura nominal

El `VRP=N MW` del header es solo el de la pasada más reciente. NO es promedio ni representativo del nivel del volcán. Si la última pasada cayó sobre un FP, mostrará VRP alto sin que haya actividad.

### Regla 5 — Cruzar SIEMPRE con CSV consolidado

Las imágenes son útiles para **patrones temporales** (frecuencia, persistencia, magnitudes típicas). Para clasificar individual ALERTA vs FP, el CSV es la única fuente confiable.

## Workflow recomendado para análisis

1. **CSV primero**: contar alertas reales (`Tipo_Registro=ALERTA_TERMICA`) por volcán × sensor × período.
2. **Imagen Dist Last Month**: validar que la densidad de stems coincide con el conteo CSV.
3. **Imagen VRP Last Month**: ver magnitud típica de detecciones.
4. **Latest10NTI**: confirmar visualmente que las detecciones están en el cráter (no en lago/salar/ciudad).
5. **Si hay duda**: bajar el plot anual, contar manualmente stems rojos vs negros, comparar con CSV.

## Errores históricos documentados

- **S27**: leer Lastarria Last Year saturado → concluir "diario" → corrección Nicolás → regla 1.
- **S29**: agent leyó "Llaima MODERATE 22 MW" del header → asumir actividad real → corrección Nicolás 2026-05-01 → regla 3 + 5.

## Notas técnicas

- Las imágenes son raster PNG 850×590 px aprox.
- Latest10NTI pesa más (~400 KB) por las thumbnails.
- Update frequency: ~6h (cada nueva pasada VIIRS).
- No hay API estructurada; solo PNGs raster. El CSV scraper de Mirova-v1 sí tiene los valores numéricos.
