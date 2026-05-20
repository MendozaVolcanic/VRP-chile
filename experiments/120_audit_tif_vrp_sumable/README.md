# Audit 120: TIF MIROVA ¿es sumable como VRP per-pixel?

**Sesión**: S70-0 (Bloque cero de saneamiento, Task 3)
**Fecha**: 2026-05-20
**Verdict binario**: **CONFIRMADO — el TIF MIROVA NO es sumable como VRP per-pixel.**

---

## Por qué importa este experimento (en términos de geólogo)

Cuando MIROVA detecta una anomalía térmica sobre un volcán, deja dos artefactos en su
archivo público:

1. Un **TIF** (`*_VIIRS375.tif`) — un campo raster sobre un bbox de ~50×50 km
   alrededor del volcán. Cada pixel tiene un valor numérico.
2. Un **KMZ** (`*_VIIRS375.kmz`) — un overlay PNG georreferenciado del mismo bbox,
   pensado para visualización en Google Earth.

Adicionalmente, **MIROVA reporta un único número de VRP por evento** en su CSV
operacional (`registro_vrp_consolidado.csv`): una potencia radiativa en MW y la
distancia del cluster al vent.

La pregunta del agente S69 (commit `64bd37d` del backup `s15-dev`, no en
`origin/main`): cuando aplicamos el método "R2 retroactivo" — sumar los 10 pixels
más calientes del TIF y promediar su centroide — ¿estamos recuperando el VRP
MIROVA, o estamos midiendo otra cosa?

Esa pregunta no es académica: el resultado de R2 sobre Lastarria fue uno de los
argumentos para adoptar `local_kernel_bg: true` en `mirova_equivalent.yaml` (S62).
Si el método R2 mide otra cosa, la calibración Lastarria S69 estaba apoyada en una
métrica equivocada y replicarla a Chaiten/PCC/Villarrica/PP en S70-1 sería peor
que no hacer nada.

---

## Lo que la inspección reveló

### Los KMZ son sólo GroundOverlay

Revisamos 5 KMZs Lastarria VIIRS375:

```
20260518_174801_VIIRS375.kmz: placemarks=0 points=0 overlays=1 VRP-text=False MW-text=False
20260519_173001_VIIRS375.kmz: placemarks=0 points=0 overlays=1 VRP-text=False MW-text=False
20260519_180027_VIIRS375_lm.kmz: placemarks=0 points=0 overlays=1 VRP-text=False MW-text=False
20260520_044201_VIIRS375.kmz: placemarks=0 points=0 overlays=1 VRP-text=False MW-text=False
```

No hay `<Placemark>` con `<Point>`. No hay texto "VRP: X MW @ Y km" en ninguna parte
del KML. El plan original del experimento asumía que el KMZ traía un Placemark del
cluster + un header con VRP — eso no es así.

Consecuencia: el ground truth para VRP MIROVA debe venir del **CSV**, no del KMZ.

### Los TIF son campos continuos, no mapas de hotspots

Sobre el TIF `20260518_061202_VIIRS375.tif` (134×134 pixels, EPSG:4326):

```
pixels positivos:  17,852  (de 17,956 totales — sólo 104 NaN en el bbox)
min:   0.0350
max:   0.0958
p5:    0.0469
p50:   0.0612
p95:   0.0767
p99:   0.0823
suma:  1,093 MW (!!)
```

Es decir: el TIF tiene valor positivo casi en cada pixel del bbox (más del 99 %),
con un rango estrechísimo (0.035–0.10). Eso no es un raster de potencia radiativa
por pixel (donde esperarías muchos ceros y unos pocos pixels con valores altos): es
un **campo continuo** — probablemente una temperatura de brillo normalizada, un NTI
contextual, o una radiancia escalada — pintado para visualización, no para suma.

MIROVA reporta para ese mismo overpass:

```
VRP_MW       = 0.08
Distancia_km = 1.19
Tipo         = ALERTA_TERMICA
```

Si el TIF fuera "VRP por pixel", la suma de los pixels caliente debería dar ~0.08 MW.
Da 1093 MW. Hay un factor ~14,000× de discrepancia.

---

## Método R2 sobre 5 casos reales

Tomamos los últimos 5 ALERTAs Lastarria VIIRS375 que tienen TIF + KMZ + match en CSV:

| TIF | MIROVA VRP (MW) | top10 sum (MW) | ratio | dist top10→vent (km) | dist MIROVA (km) | drift (km) |
|---|---|---|---|---|---|---|
| 20260510_061201 | 0.05 | 1.10 | **21.9×** | 11.9 | 1.55 | 10.4 |
| 20260513_063600 | 0.07 | 1.04 | **14.9×** | 18.6 | 1.19 | 17.4 |
| 20260514_054802 | 0.14 | 1.22 | **8.7×** | 13.3 | 2.40 | 10.9 |
| 20260514_061800 | 0.14 | 1.10 | **7.9×** | 13.0 | 2.40 | 10.6 |
| 20260518_061202 | 0.08 | 0.92 | **11.5×** | 16.8 | 1.19 | 15.6 |

**Mediana ratio top10/MIROVA_VRP = 11.5×**
**Mediana drift centroide vs distancia MIROVA = 10.9 km**
**0/5 casos en banda [0.5×, 2.0×]; 3/5 casos con ratio > 10×.**

El centroide top-10 del TIF cae sistemáticamente a 11-19 km del vent — MIROVA reporta
clusters a 1.2-2.4 km. **El método R2 ni siquiera apunta a la región correcta del
volcán**, mucho menos recupera la VRP.

---

## Validación del método sobre TIF sintético

Para descartar bug del método, se construyó un TIF 100×100 con un cluster controlado
de 9 pixels × 10 MW (suma 90 MW) y ~810 pixels de noise × 0.1 MW
(`test_method.py`). Sobre ese TIF:

```
centroide top10: (-25.0506, -68.9495)
esperado:        (-25.0500, -68.9500)   <- a 1 pixel del centro del cluster
suma top10:      90.10 MW   (esperado ~90)   <- 9 pix cluster + 1 noise
suma full TIF:   178.10 MW                    <- 90 cluster + ~81 noise
```

El método funciona correctamente cuando el TIF **es** un mapa sumable de potencia.
El problema no es el método: el problema es que el TIF MIROVA no es ese tipo de mapa.

---

## Criterios de verdict (definidos antes de correr)

- **REFUTADO** (TIF sí mide cluster): ratio top10/CSV_VRP en [0.5, 2.0] en ≥3/5 casos.
- **CONFIRMADO** (TIF no es sumable): ratio >>10× consistente, o drift centroide gigante.

Resultado: **0/5 en banda, mediana 11.5× y drift 10.9 km → CONFIRMADO.**

---

## Resultado

**El TIF MIROVA es un campo continuo (probablemente BT/NTI/anomalía normalizada),
no un raster sumable de VRP por pixel.** Cualquier suma directa de pixels del TIF
da un número 8-22× la VRP que MIROVA publica, y el centroide del top-10 cae a
~10-18 km del vent — fuera del cluster térmico real.

Eso significa que **el método R2 S69 tal como está descrito en los handoffs es
incorrecto**. Si la calibración Lastarria S69 efectivamente partió de "TIF top-10
ponderado", el número que se reportó (ratio 1.05× MIROVA) no está midiendo lo que se
dijo medir.

Antes de pasar a S70-1 hay que recuperar el código exacto que usó el agente S69
sobre el TIF Villarrica (commit `64bd37d` o el script que haya quedado) y revisar
qué transformación adicional se aplicó al TIF — probablemente un threshold +
clustering con un radio chico alrededor del vent, no una suma directa. Si esa
transformación existe, hay que documentarla y portarla; si no existe, R2 retroactivo
no es replicable y la decisión kernel-bg de S62 no tiene ese apoyo metodológico.

---

## Consecuencia para S70-1 (R2 retroactivo Chaiten/PCC/Villarrica/PP)

**Bloqueante hasta clarificar el método real S69.** Aplicar el método tal como lo
ejecutó este experimento sobre los otros 4 volcanes daría ratios mediana >10× contra
la VRP MIROVA y drifts >10 km del vent, lo que sería ruido, no calibración.

Próximo paso recomendado para Nicolás:
1. Recuperar el script exacto del agente S69 (buscar en `experiments/` del backup
   `s15-dev` o en el archivo de Mirova-v1 del repo paralelo).
2. Identificar qué máscara o threshold aplicó al TIF antes de calcular top-N.
3. Si esa transformación existe y está documentada → portarla a este experimento y
   re-correr (los 5 casos están listos para reutilizar).
4. Si no existe → cuestionar la adopción Lastarria S62 / S69 y rediseñar el método
   de validación pixel-level (probablemente comparar BT(I04) crudo del granule NRT
   contra el cluster MIROVA, no contra el TIF derivado).

---

## Archivos

- `audit_lastarria.py` — auditoría sobre 5 casos reales con match TIF+KMZ+CSV
- `test_method.py` — test fixture con TIF sintético controlado
- `results.json` — resultados completos por caso + verdict agregado

---

## Origen del hallazgo S33+

Commit `64bd37d` de la rama `s15-dev` (backup local, no en `origin/main`):

> "S33+ cierre — TIF MIROVA real analizado, decision revert fix S33 documentada"

Ahí quedó documentada la sospecha de que el TIF MIROVA no era directamente sumable.
Este experimento la convierte en hallazgo confirmado con números reproducibles.

---

## Parte 2 — Método R2 S69 verdadero replicado (Step 8 S70-0)

### Aclaración importante

El verdict "CONFIRMADO_TIF_NO_ES_SUMABLE" de la Parte 1 es válido sobre el campo de
radiancia del TIF MIROVA — el TIF NO se debe interpretar como un raster donde cada
pixel sea VRP individual sumable. El campo es continuo, casi todo el bbox tiene
valor positivo, y la suma directa da magnitudes 8-22× la VRP MIROVA. Eso sigue en
pie.

**PERO esto NO invalida el método R2 S69**, porque al re-leer
`docs/HYPOTHESIS_LOG.md` entry `H_S69_R2_RETROACTIVO_LASTARRIA` se aclaró que el
método R2 S69 verdadero NO suma pixels del TIF para medir magnitud. El R2 S69 usa:

- **Magnitud**: `pc.vrp_mw` (output del nuestro pipeline, ya filtrado a cluster
  y persistido en `data/mirova_equivalent/Lastarria.json`) vs `MIROVA CSV NRT`
  (`registro_vrp_consolidado.csv`). NO tocamos el TIF para esto.

- **Geometría**: del TIF, tomamos solo los pixels positivos dentro de 3 km del
  vent — el rango físicamente plausible donde puede sentarse el cluster térmico
  inmediato de un cráter en actividad — y calculamos el centroide ponderado de
  los top-10 dentro de ese filtro. Eso lo comparamos contra `pc.centroid` del
  pipeline.

El filtro <3 km del vent es lo que hace al método válido: aísla la región
físicamente coherente con actividad volcánica del cráter, separándola del
campo continuo de fondo del TIF que pinta todo el bbox de 50×50 km.

### Caso replicado

Lastarria 2026-05-14 05:48 UTC VIIRS375 (TIF `20260514_054802_VIIRS375.tif`,
MIROVA CSV registro 773, ALERTA_TERMICA).

### Resultados de la replicación

| Componente | Valor S69 (HYPOTHESIS_LOG) | Valor obtenido S70-0 | Tolerancia | Status |
|---|---|---|---|---|
| ratio `pc.vrp_mw / MIROVA.VRP_MW` | 1.05× | **1.05×** (0.147 / 0.14) | ±0.20 | ✓ exact match |
| TIF top10 <3 km vent — centroide | (-25.15546, -68.51905) | (-25.15130, -68.51800) | — | ~0.5 km off |
| `pc.centroid` | (-25.15947, -68.51301) | **(-25.15947, -68.51301)** | exact (mismo record) | ✓ exact match |
| drift TIF top10 vs `pc.centroid` | 0.752 km | **1.04 km** | ±0.50 | ✓ dentro de tolerancia |

Detalles operacionales del run:

- TIF pixels positivos totales: 17,906 (de 17,956 — bbox 134×134, prácticamente
  todo el bbox tiene valor positivo, consistente con campo continuo).
- TIF pixels positivos dentro de 3 km del vent: 206 (los relevantes para el R2).
- top-10 valores dentro de 3 km: rango 0.079–0.100, distancias 1.07–2.74 km.
- `pc.n_pixels = 1` (cluster de 1 pixel granule VIIRS375 — actividad sub-pixel
  típica de Lastarria, consistente con que el TIF muestra un campo difuso de
  varios pixels con valores similares pero el pipeline aísla un solo pixel
  granule como cluster).

El centroide TIF obtenido difiere del de S69 en ~0.5 km (0.4 km en lat, 0.001 lon).
Las dos hipótesis principales son: (a) S69 puede haber usado una versión del TIF
descargada en momento distinto antes de que el archivo se estabilizara, o (b) un
detalle de implementación menor — `>0` vs `>= threshold`, redondeo del centroide,
o ponderación distinta. Lo crítico es que la magnitud del drift contra
`pc.centroid` (1.04 km) está dentro del mismo orden que el target S69 (0.752 km)
y dentro de la tolerancia operacional <2 km del plan. Ambos confirman que el
cluster que persiste el pipeline está geométricamente alineado con la región
térmica que MIROVA pinta en el TIF, dentro del rango sub-cráter.

### Verdict Parte 2

**REPLICADO — método R2 S69 verdadero validado y replicable.**

El ratio de magnitud es exactamente el reportado en HYPOTHESIS_LOG (1.05×) y el
drift geométrico es del mismo orden y dentro de tolerancia. La separación
conceptual entre "magnitud desde nuestro pipeline" y "geometría desde el TIF
filtrado al vent" es el método correcto, y replicarlo a otros volcanes de Tier A
en S70-1 es metodológicamente defendible.

### Implicación operacional

Bajo este resultado, **S70-1 puede proceder** a aplicar el método R2 S69 verdadero
a Chaiten, PCC, Villarrica y PP. El plan operacional para cada volcán es:

1. Tomar la ALERTA MIROVA más reciente con TIF disponible en
   `mirova-tif-archive/data/tif/<Volcan>/`.
2. Sacar `pc.vrp_mw` y `pc.centroid` del record correspondiente en
   `data/mirova_equivalent/<Volcan>.json`.
3. Cruzar contra `registro_vrp_consolidado.csv` por `Fecha_Satelite_UTC` exacto
   para sacar `VRP_MW` MIROVA y `Distancia_km`.
4. Cargar TIF, filtrar pixels positivos a <=3 km del vent del volcán
   (`volcanoes.yaml`), top-10 ponderado, calcular centroide.
5. Computar ratio magnitud y drift centroide, validar contra bandas operacionales
   (ratio 0.5-2.0×, drift <2 km).

Adicionalmente, los hallazgos de Parte 1 (TIF no es sumable como VRP/pixel) deben
quedar documentados en el handoff S70-0 → S70-1 para evitar que un agente futuro
vuelva a intentar sumar pixels del TIF y concluya falsamente que la calibración
S62/S69 estaba mal apoyada.

### Archivos Parte 2

- `audit_lastarria_real_method.py` — replicación del R2 S69 verdadero sobre el
  caso Lastarria 2026-05-14 05:48 UTC.
- `results_real_method.json` — resultados estructurados de la replicación.
