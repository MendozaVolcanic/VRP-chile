# VIIRS750 deep-dive — paridad vs MIROVA (S114, data fresca 2026-06-19)

Fuente: `viirs750_deepdive.py` + `viirs750_deepdive.json`. Ventana 2026-05-01..06-30.
Gate dashboard: `distance_class==summit` AND `pc.centroid<=inner` AND `0<pc.vrp_mw<=50000`.
Sensor VIIRS750 = M-band 750m (`VIIRS_*_750`; en el CSV `Sensor=="VIIRS"`).

## Recall final

| Universo | Recall | Detalle |
|---|---|---|
| CONS | **85.7%** | 60/70 noches ALERTA |
| CONS+OCR (A11) | **85.9%** | 61/71 — el OCR añade 1 ALERTA V750 (universo +1) que SÍ detectamos; ninguna de las 10 FN tiene OCR mismo día → OCR no recupera FN |

VIIRS750 **no tiene brecha far→summit** (det_crater == det_dash): las 10 FN son reales, no
bug de coherencia A46. (VIIRS375 99.1%, MODIS 15.8% para contexto.)

## Las 10 FN clasificadas

| Vol | Fecha | MIROVA VRP@dist | Cat | ¿Tenemos pasada al cráter? |
|---|---|---|---|---|
| Lascar | 2026-05-18 | 0.26 MW @0.75 | c | sí, 2 recs summit centroid 0.5-1.6km, pc.vrp=0 |
| Lascar | 2026-05-28 | 0.50 MW @1.50 | a | sí, 1 rec summit centroid 1.6km, pc.vrp=0 |
| Tupungatito | 2026-05-27 | 0.24 MW @4.37 | c | sí, 3 recs summit centroid 0.1-0.2km, pc.vrp=0 |
| Tupungatito | 2026-05-31 | 0.18 MW @4.80 | c | sí, 3 recs summit centroid 0.2-0.4km, pc.vrp=0 |
| PlanchonPeteroa | 2026-05-17 | 0.33 MW @1.68 | a | sí, 1 rec summit centroid 0.5km, pc.vrp=0 |
| PlanchonPeteroa | 2026-05-25 | 0.28 MW @2.37 | c | sí, 1 rec summit centroid 0.6km, pc.vrp=0 |
| Isluga | 2026-06-02 | 0.26 MW @0.75 | c | sí, 1 rec summit centroid 1.0km, pc.vrp=0 |
| Isluga | 2026-06-03 | 0.20 MW @0.75 | c | sí, 1 rec summit centroid 1.1km, pc.vrp=0 |
| Isluga | 2026-06-07 | 0.20 MW @0.75 | c | sí, 2 recs summit centroid 1.1-1.5km, pc.vrp=0 |
| Isluga | 2026-06-08 | 0.21 MW @0.75 | c | sí, 1 rec summit centroid 1.1km, pc.vrp=0 |

**Conteo: (a) 2, (b) 0, (c) 8.** Cero categoría (b) recuperable.

### Fenómeno físico (por qué son FN)
En **9 de las 10 FN** tenemos pasada VIIRS750 esa noche con un record `distance_class=summit`
y `centroid` DENTRO del inner_radius — o sea **detectamos espacialmente el píxel anómalo al
cráter** — pero `pc.vrp_mw=0`. El `nti_max` está pegado al piso (~-0.91 a -0.94; piso -1.0):
el foco térmico es **sub-píxel para 750m**, la radiancia MIR integrada no supera el umbral de
cuantificación → magnitud 0. MIROVA, integrando todo el ROI con su propio producto, cuantifica
0.18-0.50 MW. Es el límite físico de resolución del M-band (A54): vimos el cráter, no pudimos
ponerle número. La distinción (a)/(c) es **solo** el VRP MIROVA (≥0.3 = a, <0.3 = c); el
mecanismo es idéntico en todas. **8/10 son MIROVA marginal (<0.3 MW)** = ruido de borde A54.

## Los 2 far→summit VIIRS750 Tupungatito (2026-06-09)

| Hora UTC | pc.vrp | centroid | nti_max | dT | t_bg | final_hotspot src@dist |
|---|---|---|---|---|---|---|
| 06:00 | 0.152 | 6.16km | -0.925 | 19.7K | 251K | eruption @8.69km |
| 06:36 | 0.138 | 4.61km | -0.929 | 19.7K | 253K | eruption @8.31km |

**Veredicto: ARTEFACTO A69 (ring glaciar), correctamente ocultos como `far`. NO recuperar.**
- `nti_max ~-0.925` plano (piso -1.0) → A80: sin material caliente expuesto, es gradiente
  topográfico, no lava.
- `t_bg ~251K` (-22°C) = glaciar Tupungatito (5682m, glacier-covered); `dT ~19.7K` inflado por
  el contraste cráter-frío/glaciar amplificado por el píxel grande 750m (A19, opuesto a kernel-bg).
- `final_hotspot_source=eruption` apunta a 8.3-8.7km (píxel suelto lejano del campo difuso).
- **MIROVA reportó RUTINA/NULO (VRP=0) en TODOS los sensores y pasadas esa noche**, incluidas
  las pasadas VIIRS750 06:00 y 06:36 (mismas horas) → confirma A10/A62: no es lava real.
- Son RUTINA (no ALERTA) → **no afectan el recall**; el gate S100 los dejó en `far` con razón.

## Veredicto global
VIIRS750 está **calibrado y sano**. Recall 85.7%/85.9% (CONS/CONS+OCR) es real: el techo lo
fija la física de resolución 750m sobre focos sub-píxel <0.5 MW (A54), no un bug ni un gate.
**Nada accionable** — no hay categoría (b) recuperable, OCR no mueve la aguja, y los 2
far→summit Tupungatito son artefacto glaciar bien suprimido.
