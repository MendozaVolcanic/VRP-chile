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
