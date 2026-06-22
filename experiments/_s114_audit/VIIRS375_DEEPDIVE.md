# VIIRS375 deep-dive — robustez de la paridad (S114, data fresca 2026-06-19)

Fuente: `viirs375_deepdive.py` → `viirs375_deepdive.json`. Ventana 2026-05-01..2026-06-30.
Gate dashboard: `distance_class==summit` ∧ `pc.centroid_dist_km<=inner` ∧ `0<pc.vrp_mw<=50000` (A10).
Emparejado por-noche UTC (A67). Día/noche por `Fecha_Captura_Chile` UTC-4 (A76); diurno=local 10-15h.

## 1. Recall VIIRS375 (CONS fresco)
- **Todas las noches ALERTA: 214/216 = 99.1%** (confirma el dato del orquestador).
- **Solo noches con pasada nocturna: 214/215 = 99.5%** — la FN de NdC es una ALERTA puramente
  diurna (ver abajo); descontarla por A76 sube el recall a 99.5%.

## 2. Las 2 FN (CONS), clasificadas
| Vol | Fecha | MIROVA | dist | Naturaleza | Causa pipeline |
|---|---|---|---|---|---|
| **NevadosDeChillan** | 2026-06-12 | 0.32 MW Muy Bajo | 4.14 km | **Diurna A76 — perderla es CORRECTO** | la única ALERTA es a las **14:18 local (DIURNA)**; nuestras pasadas nocturnas (02:00/02:48) son RUTINA VRP=0 en MIROVA. No es FN real (somos night-only). |
| **Lastarria** | 2026-06-14 | 0.03 MW Muy Bajo | 2.40 km | **Sub-umbral real A54** | tenemos record nocturno VIIRS_NOAA21 anclado al cráter (cdist 2.14 km, `class=summit`, `fh_src=test1_roi`) pero `pc.vrp=0`: el Test1 ubicó el foco pero no cuantificó magnitud. Foco sub-píxel debilísimo (0.03 MW). **NO es bug far→summit (A46).** |

Ninguna FN es un far→summit oculto ni un centroide fuera de inner. NdC = artefacto diurno (no
cuenta); Lastarria = límite físico de cuantificación sub-píxel (A54). **Ninguna recuperable sin
bajar el piso de cuantificación VIIRS375.** Contexto NdC: A77 (reactivación junio 2026 sub-píxel,
mejor resuelta por alta-res SWIR Landsat-v1/NHI-v1, no VIIRS375).

## 3. Cruce con OCR (A11 universo CONS+OCR; A76 filtrado diurno)
- OCR ALERTA VIIRS375 filas: **45 diurnas (artefacto A76)** + 234 nocturnas.
- Noches solo-en-OCR nocturnas (no en CONS): **36** → detectamos **34**, perdimos **2**.
- **2 missed OCR nocturnas**: PCC 2026-05-05 (0.23 MW) y PCC 2026-06-12 (0.12 MW), ambas "conf
  alta" dist=0. Procesamos las pasadas (records existen) pero sin trigger térmico (`nti_max=None`)
  = anomalía difusa Muy Bajo del lacolito Cordón Caulle (inner=20km, A20/A54), no foco crateriano.
- **Recall CONS+OCR-nocturno: 248/251 = 98.8%.** El OCR NO baja el panorama: añade 34 TP y solo 2
  FN difusas sub-umbral. La paridad VIIRS375 es robusta también contra el universo ampliado.

**45 artefactos diurnos OCR detectados** (A76): si los "perdemos" es correcto — son reflexión
solar sobre nube cerca del mediodía solar, marcados alta-confianza por el scraper pero no señal.

## 4. Sobre-detección RUTINA (A54/A68 — solo magnitud del fenómeno)
- Noches RUTINA-only VIIRS375 (MIROVA NO alerta): **332**. Reportamos summit pc.vrp>0 en **280
  (84.3%)**. Es sobre-detección sistémica = recall real sub-umbral (A54/A68): MIROVA lo clasifica
  RUTINA, nosotros le ponemos magnitud al foco crateriano débil. Coherente con el patrón A54/A68
  (anomalía térmica físicamente real bajo el umbral de publicación MIROVA). **No es bug; no se
  propone fix** (solo se reporta la magnitud).

## Veredicto
VIIRS375 es el sensor sano: paridad **99.1% (CONS) / 99.5% (CONS nocturno) / 98.8% (CONS+OCR
nocturno)**. Las 2 FN son 1 diurna (no cuenta) + 1 sub-umbral 0.03 MW. Sin brecha far→summit.
La sobre-detección (84.3% de RUTINA) es recall sub-umbral conocido (A54/A68), no defecto.
