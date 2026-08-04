# C2 Paso 0 (S122) — VEREDICTO: el blob path-D MODIS NO tiene núcleo → C2 NO viable, D12 irreducible a 1 km

> Análisis read-only `experiments/_s122_c2_paso0/paso0.py` (S91, números del script).
> Data: `data/mirova_equivalent/` (versionado). Los píxeles del blob son **invariantes al
> ancla** — verificado S122: el ancla honesta solo cambia `distance_class` (far→summit),
> deja `pc.vrp`, `anomaly_pixels` y todo lo demás idéntico (record PCC 2025-02-27:
> baseline far / reproc summit, ambos pc.vrp=117.09, 82 px, max_px=2.453). Por eso el
> baseline sirve y es reproducible sin depender del scratchpad efímero del run 29582035729.

## Pregunta del Paso 0 (design 2026-07-17-c2-ctxpeak-modis-ab-design.md)

El A/B del ancla honesta MODIS (S121) falló por **magnitud** (destape de blobs path-D
contextual: PCC 117 MW, Tupun 23, NdC 20 — 0% MIROVA). C2 se propuso como un mecanismo
NUEVO (peak-of-kernel) que reduzca el blob a su núcleo de radiancia. **Paso 0 decide si
existe ese núcleo ANTES de codear**: ¿hay 1-2 píxeles pico (foco real → C2 viable) o es
un campo plano (sin núcleo → D12 irreducible a 1 km, A82/A83 → cerrar)?

## Resultado (números del script, ventana 2025-02-15..05-15, path-D-only pc.vrp>5 MODIS)

| Vol | n recs | pc.vrp med/max | píxel PICO med/max | frac top-1 px | max bt MIR |
|---|---|---|---|---|---|
| **Láscar (CURA, activo real)** | 8 | 6.6 / 29.3 | 3.67 / 4.52 | ~2.9% | 287–290 K |
| NevadosDeChillan | 6 | 8.2 / 20.0 | 2.72 / 3.87 | ~2.4% | 292–294 K |
| PuyehueCordonCaulle | 30 | 21.1 / **233** | 2.31 / 3.01 | ~1.9% | 286–294 K |
| Tupungatito | 21 | 10.0 / 27.1 | 3.28 / 4.26 | ~3.6% | 286–291 K |

**Separabilidad peak-of-kernel (píxel pico):** Láscar [2.23, 4.52] MW vs nevados
[1.42, 4.26] MW → **solapamiento [2.23, 4.26] MW (casi total)**.

## Interpretación física (por qué NO hay núcleo)

A 1 km, la anomalía de Láscar es **sub-píxel y débil**: su píxel MIR más caliente en las
noches reales apenas llega a 287–290 K (~14–17 °C de temperatura de brillo). No hay
material incandescente resoluble. La señal se reparte como un **campo tibio difuso** sobre
60–80 píxeles, sin dominante. Ese campo es **físicamente indistinguible** del campo difuso
del lacolito PCC o del cirrus: muchos píxeles apenas tibios que superan levemente a sus 8
vecinos (por eso los toma el path-D dNTI contextual), ninguno con núcleo.

- **Blobs planos**: el píxel pico aporta ~2–3% del total en TODOS los casos (un foco de
  lava real daría 50–90% en 1 píxel). No hay núcleo que aislar.
- **peak-only colapsa TODO <5 MW**: 8/8 Láscar, 30/30 PCC, 21/21 Tupun, 6/6 NdC. Suprimir
  el artefacto PCC (117 MW → pico 2.5 MW) **también** mata las noches reales de Láscar
  (blobs hasta 179 MW → pico 3.7 MW).
- **Sin umbral separador**: el píxel-pico de la cura (Láscar) y del destape (nevados)
  solapan casi por completo. Ningún peak-of-kernel separa uno del otro.

## VEREDICTO

**C2 (peak-of-kernel) NO es viable. Cerrar el frente de fix de magnitud path-D MODIS.**

Es A82/A83 en el eje de **magnitud**: a 1 km el foco débil real y el blob difuso son el
mismo objeto; solo el eje **espacial** (qué volcán, dónde) los separa, no un discriminante
de magnitud per-record. El destape del ancla honesta MODIS (D12) no se puede neutralizar
con un mecanismo de magnitud porque no existe el núcleo que ese mecanismo necesitaría.

**Consecuencia para D12**: el ancla honesta MODIS cura 76 noches reales de FN de Láscar
PERO viene atada al destape de magnitud path-D, y ese destape es **irreducible a 1 km**.
Los dos no son separables ni por el gate de posición (S111, ortogonal — AUDIT_S121_D12_AB)
ni por un fix de magnitud (C2, este Paso 0). **D12 se cierra como irreducible a resolución
MODIS.** El recall de Láscar lo cubre **VIIRS375** (A77): a 375 m el foco sub-píxel sí es
resoluble; a 1 km MODIS es el instrumento equivocado para esta señal.

## Refutación adversarial (S122, A62 — pedido de Nicolás antes de cerrar)

Nicolás (geólogo del volcán) pidió refutar antes de cerrar. Tres ataques
(`experiments/_s122_c2_paso0/refute_d12.py`) — los tres CONFIRMAN, no refutan:

1. **Cross-sensor (decisivo):** concentración del blob por resolución en Láscar —
   MODIS 1km: frac top-1 píxel **mediana 5.3%**, solo 25/301 con núcleo real (>40%).
   VIIRS375: **mediana 85.8%**, 355/365 con núcleo. VIIRS750: 100%, 388/392. El foco de
   Láscar ES real y concentrado (VIIRS lo resuelve como 1 píxel dominante) pero a 1 km MODIS
   lo desparrama en blob difuso → no hay pico que un peak-of-kernel MODIS pueda aislar.
   Confirma C2-no-viable + A77 (VIIRS375 = instrumento correcto) + valida que la cura es real.
2. **Hueco propio (cerrado):** `t_max_k` (píxel más caliente de la escena) = max_bt del blob
   (~286-289 K) en todos los path-D MODIS de la ventana → no hay núcleo caliente oculto fuera
   de `anomaly_pixels`. El blob es genuinamente frío y plano.
3. **Espacial (A61):** el píxel pico de los blobs path-D de Láscar está a **21-24 km del
   cráter** (Salar de Atacama), no en el volcán → campo difuso que llena el ROI de 25 km, sin
   núcleo crateriano a 1 km.

El contraste MODIS 5% vs VIIRS375 86% top-1 es además una demostración cuantitativa limpia
del límite sub-píxel — citeable para el paper (coincide con el caveat de Reath 2019 líneas
623-631, ver `M2_AVTOD_INTEGRATION_S122.md`).

## NO reabrir (anti-A8)

- C2 peak-of-kernel MODIS (este Paso 0 lo refuta con datos).
- Cualquier discriminante de magnitud per-record para el far→summit / destape MODIS
  (A82/A83 agotado, ahora también en el eje de magnitud).
- El ancla honesta MODIS sin fix de magnitud (S121: destapa 117 MW; y no hay fix posible).
