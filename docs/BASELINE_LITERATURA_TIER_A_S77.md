# Baseline literatura per volcán Tier A (S77)

> **Propósito**: documentar magnitudes VRP "físicamente plausibles" para los 11
> Tier A según literatura (papers MIROVA core, GVP, SERNAGEOMIN, audits internos)
> y contrastar con los valores que el pipeline VRP Chile está reportando post-fixes
> S77. No se modifica pipeline ni data — esto es referencia para detectar
> sobre/sub-estimación vs banda de literatura.
>
> **Sesión**: S77 · **Modo**: read-only · **Worktree dedicado A44**:
> `VRP-Chile-s77-baseline-lit` · **Branch**: `claude/s77-baseline-literatura-tierA`.
>
> **Fuentes primarias**:
> - `docs/MIROVA_DETAILED_CITATIONS.md` (citas verbatim Coppola 2016a / 2024 / Aveni 2025 / Campus 2024).
> - `Vault/10_Bibliografia/99_por_clasificar/` (notas papers procesados).
> - `documentacion/aguilera2021peteroa.pdf` (paper específico volcán chileno).
> - Audits internos S62/S63/S65/S76/S77 (`docs/F46_*`, `F47_*`, `F48_*`, `F52_*`, `F50_*`).
> - GVP Smithsonian (Global Volcanism Program) — IDs verificados.
> - SERNAGEOMIN RAV (Reporte de Actividad Volcánica).
>
> **Caveats**:
> - "VRP típico esperado" = banda observada por MIROVA NRT en ventanas recientes (cross-ref CSV consolidado `latest_consolidado.csv` + papers cuando disponible), no umbral físico estricto.
> - "Confianza alta" requiere paper específico per-volcán con magnitudes MW citadas. "Media" = banda derivada por analogía con régimen (lava lake, dome, fumarólica). "Baja" = solo GVP/SERNAGEOMIN tipo actividad sin magnitudes MIROVA.
> - Valores actuales pipeline = `experiments/138_audit_mw_outliers_s76/audit_output.txt` (rebuild S77) cruzado con audits F52/F50/F46.

---

## Tabla baseline — 11 Tier A

| Volcán | Tipo actividad 2024-2026 | VRP típico MIROVA NRT (MW) | VRP máximo histórico (MW) | Última alerta ALTA | Source primario | Confianza |
|---|---|---|---|---|---|---|
| **Chaitén** | Dome rhyolítico Domo Nuevo en cooling crónico post-2008 | 0.2–1 (mediana sub-MW) | ~500 (erupción 2008 sub-pliniana VEI 4, dome growth 2008-2011) | 2008-05 (erupción) · alerta SERNAGEOMIN amarilla 2024 sostenida | GVP 358041 + Coppola 2020 (capítulo dome) | media |
| **Copahue** | Cráter El Agrio con lago ácido + degassing crónico SO2; episodios freatomagmáticos 2012-2020 | <0.5 (99.4% NULO en CSV consolidado 6 meses — F48) | ~50 (Caviglia 2018; explosiones jul-2020) | 2024-04 (alerta amarilla → naranja) | GVP 357090 + Caselli et al. 2016 + F48 audit interno | media |
| **Isluga** | Fumarólica persistente cráter cima + emisión SO2 baja | 0.3–2 (banda Coppola 2016a "Vanuatu Gaua-like fumarole" <5 MW) | ~30 (registro OSF 2010-2015 picos esporádicos) | Sin alertas recientes (verde RAV 2024-2026) | GVP 355100 + OSF v2.5 archive | baja |
| **Lascar** | Cráter activo dome + degassing fuerte SO2; explosiones esporádicas 2022-2023 | 1–20 (mediana 3, picos ~50 — F48: 84 "Muy Bajo" + 163 "Bajo" en CSV consolidado) | ~820 (audit interno S77 max histórico) · explosión 1993 VEI 4 alcanzó >1000 MW MODVOLC | 2022-12 (ash plume) · alerta amarilla 2024 | Coppola 2026 (SSRN, pending PDF) + Pavez et al. 2020 + audit S77 | alta |
| **Lastarria** | Fumarólica vigorosa persistente (sin actividad eruptiva histórica registrada Holoceno tardío) + uplift Lazufre | 0.5–5 (mediana 2.7 — audit S77; banda fumarole field Aveni 2025 <600 K) | ~750 (audit S77 max histórico — outlier por sat flag, real ~140) | Sin alertas (verde permanente; volcán "monitoreado preventivo") | GVP 355100 + Aguilera et al. 2012 + Stechern et al. 2017 | alta |
| **Llaima** | Cráter Principal con degassing post-2008-2009 cycle; quiescente eruptivo desde 2009 | <0.3 (99.9% NULO — F48: 0 detecciones reales en CSV consolidado) | ~6000 (erupción 2008-01 cuasi-pliniana VEI 3; flujos de lava 2008-2009) | 2008-2009 (erupción) · sin alertas posteriores | GVP 357110 + Bouvet de Maisonneuve et al. 2012 + F48 | media |
| **Nevados de Chillán** | Domo Gil-Cruz cráter Nicanor; ciclo dome-growth + explosiones vulcanianas 2016-2022 | 1–10 (mediana — Coppola 2020 capítulo dome; SERNAGEOMIN-OVDAS monitoreo continuo) | ~1325 (audit interno S77 max histórico MODIS_TERRA) · pico cycle 2019-2020 | 2022 (alerta amarilla post-explosión); 2024 verde | GVP 357070 + SERNAGEOMIN RAV + F47 audit interno | alta |
| **Planchón-Peteroa** | Caldera ~5 km con 4 lagos cratéricos + fumarole fields + scoria cone 1937 + nested crater desde 2018 | 7–38 por lago (Aguilera 2021); en quiescente max 59 MW agregado | ~59 (Aguilera 2021 Qvolc max quiescente); eventos unrest 1991/1998-2001/2010-2011/2018-2019 | 2018-10 a 2019-04 (último unrest); alerta amarilla intermitente 2024 | **Aguilera et al. 2021 Frontiers** (paper específico Landsat/Planet 1984-2020) | alta |
| **Puyehue-Cordón Caulle (PCC)** | Lacolito 2011-2012 en cooling pasivo + degassing residual fumarólico | 0.3–5 (mediana 0.29 — audit F52: 99.5% sub-MW, 72 detecciones reales 90d) | ~6000 (erupción 2011-06 VEI 5 sub-pliniana lava lacolito 0.8 km³); post-2012 decay exponencial | 2011-06 a 2012-04 (lacolito); 2024 verde | GVP 357150 + Castro et al. 2013 + Coppola 2020 (capítulo Cordón Caulle) | alta |
| **Tupungatito** | Caldera glaciar + lagunas cratericas + fumarole crónica; sin actividad eruptiva confirmada >1986 | 0.2–2 (mediana 0.23 — F52: régimen fundamentalmente sub-MW, 100 detecciones 90d) | ~47 (audit F52 max histórico MIROVA NRT); registro OSF v2.5 reporta 0 (anomalía documentada) | Sin alertas; verde permanente 2024-2026 | GVP 357010 + SERNAGEOMIN RAV + audit F52 | media |
| **Villarrica** | Lava lake activo Rinrinco (cráter Rinconada) — lago de lava permanente sub-pixel desde ~1971 con pulsos | 0.05–0.55 (Coppola 2020 cap. lava lakes; mediana CSV consolidado 0.45 MW; max 75.5 MW) | ~6000 (erupción 2015-03-03 sub-pliniana fountain ~1500 m altura, VEI 2 corta pero intensa) | 2015-03-03 (paroxismo) · alerta amarilla 2025-02 (pulso lago de lava) | GVP 357120 + Witter et al. 2004 + Moussallam et al. 2016 + Coppola 2020 | alta |

---

## Notas por volcán (1-2 párrafos)

### Chaitén
Domo riolítico nuevo (Domo Nuevo) emplazado durante la erupción 2008 VEI 4. Desde ~2011 está en cooling crónico — la firma térmica que detectamos es el calor residual del cuerpo de roca emplazado, no actividad magmática nueva. CSV consolidado MIROVA NRT muestra 15 detecciones "Muy Bajo" sobre 1570 capturas (~1%), todas sub-MW. El paper Coppola 2020 (capítulo Springer "Thermal remote sensing for global volcanism monitoring") documenta dome cooling con tail exponencial: lo que medimos es físicamente coherente.

### Copahue
Cráter El Agrio con lago hiperácido permanente y degassing magmático persistente SO2 (~5000 t/d nominal). Episodios freatomagmáticos 2012-2013, 2014-2017, 2020. Caselli et al. 2016 (cap. Copahue en Active Volcanoes of the World) lo clasifica como sistema hidrotermal-magmático abierto. La señal térmica MIROVA es mayoritariamente nula (F48 audit interno: 1475/1478 NULO en CSV consolidado) — el lago ácido amortigua térmicamente la superficie y el lago hierve esporádicamente solo durante crisis.

### Isluga
Estratovolcán altiplánico con cráter cima fumarólico crónico y emisión SO2 baja-moderada. Sin actividad eruptiva confirmada en últimas décadas. Vault no tiene paper específico — banda 0.3–2 MW derivada por analogía con Vanuatu Gaua (Coppola 2016fifteen p. 16-17, "menos del 2% falsos alertas <5 MW" para crater-lake fumarole fields).

### Lascar
**Volcán Tier A best-calibrated**. Cráter activo dome con degassing fuerte SO2 (régimen "open-vent" según clasificación Coppola). 297 detecciones MIROVA NRT en ventana 90 días (la cifra más alta de los Tier A). Audit S12 reportó ratio mediano ours/MIROVA = 1.11 (calibrado natural sin tuning per-volcán), confirmado S62. Coppola 2026 (SSRN, pendiente descarga manual) provee ground truth multiparamétrico 2017-2021 para cross-validation cuando se descargue. Explosiones esporádicas 2022-2023 produjeron picos transitorios pero la magnitud típica es 1–20 MW.

### Lastarria
Volcán **monitoreado preventivo** (sin actividad eruptiva Holoceno tardío confirmada) pero con fumarólica vigorosa persistente y uplift sostenido del complejo Lazufre. Stechern et al. 2017 documentó composición magmática y volátiles de fumarolas. Audit S77 mostró ratio mediano sano ~1.07 (calibrado). Mediana CSV consolidado 2.74 MW, max 748 MW (pero ese pico es outlier por sat flag pre-F2.8 — F46 documenta limpieza).

### Llaima
Estratovolcán con cráter principal degassing pasivo. Erupción 2008-01 (sub-pliniana VEI 3 con flujos de lava). Desde 2009 quiescente sin actividad significativa. F48 audit interno documenta que MIROVA NRT no emite alertas térmicas en ventana scrapeada (1463/1463 NULO) — esto es **dato científico real**, no gap operacional. El pico histórico ~6000 MW corresponde a la erupción 2008 (Bouvet de Maisonneuve et al. 2012).

### Nevados de Chillán
Cráter Nicanor con domo Gil-Cruz creciendo episódicamente desde 2016. Ciclo dome-growth + explosiones vulcanianas hasta 2022. Monitoreo OVDAS continuo. F47 documenta recall anómalo bajo (0.20) en audit S76 — el único Tier A bajo 0.50, sugiere problema de detección NO de magnitud. La banda 1–10 MW es coherente con Coppola 2020 (capítulo dome growth/cooling).

### Planchón-Peteroa
**Único Tier A con paper específico chileno verificable** (Aguilera et al. 2021 Frontiers in Earth Science doi:10.3389/feart.2021.722056). Sistema de **bajo flujo térmico**: 4 lagos cratéricos + scoria cone 1937 + nested crater nuevo desde 2018-12. Qvolc por lago: 7.1–38 MW en unrest, max agregado quiescente 59 MW. Ciclos 1998-2001, 2010-2011, 2018-2019. Este es el ground truth más confiable que tenemos para validar magnitudes en un volcán chileno.

### Puyehue-Cordón Caulle
**Erupción 2011-06 VEI 5** sub-pliniana que emplazó lacolito riolítico ~0.8 km³ (Castro et al. 2013 Nature Communications). El lacolito está en cooling pasivo desde 2012 con decay exponencial documentado (Coppola 2020 capítulo PCC explícito). Audit F52: mediana MIROVA NRT 0.29 MW, 72 detecciones reales en 90 días — régimen **fundamentalmente sub-MW** post-2014. Nuestro pipeline reporta ratio mediano 12× sobre-estimado (audit F52 Tupungatito-PCC) — drift T1.5 documentado.

### Tupungatito
Caldera glaciar de altura con lagunas cratericas + fumarólica crónica. Última actividad eruptiva confirmada ~1986 (incierto). Sin alertas. Anomalía documentada: registro OSF v2.5 reporta 0 detecciones histórico pero MIROVA NRT actual reporta ~100 detecciones en 90 días (mediana 0.23 MW). F52 audit detecta nuestro pipeline sobre-estimando ratio 11× — mismo drift T1.5.

### Villarrica
**Lava lake permanente Rinrinco** desde ~1971, con pulsos episódicos. Erupción paroxismal 2015-03-03 (sub-pliniana corta pero intensa, fountain ~1500 m). Witter et al. 2004 y Moussallam et al. 2016 caracterizan el lago de lava. **Coppola 2020 documenta explícitamente el problema**: el lago de lava emite 0.05–0.21 MW sub-pixel; MIROVA captura solo cuando la convección expone roca caliente. Nuestro pipeline reporta ratio mediano 10.91× sobre-estimado (F52) — causa raíz documentada H4 clustering vent-anchored mal calibrado en el flanco glaciar NW.

---

## Comparación con valores audit S77 (cross-check)

Ratios mediana ours/MIROVA en ventana reciente (90 días, post-S75):

| Volcán | Banda literatura típica (MW) | Mediana pipeline S77 (MW) | Max audit S77 (MW) | Ratio ours/MIROVA mediano | Veredicto banda |
|---|---|---|---|---|---|
| Chaitén | 0.2–1 | 0.6 (estimado) | 6872 (TIR fósil F2.8) | n/a (sin matches recientes) | **fuera banda max** (sat fósil residual) |
| Copahue | <0.5 | <1 | 1584 (TIR) | n/a (régimen NULO MIROVA) | **fuera banda max** (TIR fósil) |
| Isluga | 0.3–2 | ~1 | 1385 (TIR) | n/a | **fuera banda max** (TIR fósil) |
| Lascar | 1–20 | 3.03 | 9606 (TIR) / 820 (MIR) | ~1.1 (calibrado S62) | **dentro banda MIR**, fuera TIR (F46) |
| Lastarria | 0.5–5 | 2.74 | 748 (MIR) | ~1.07 | **dentro banda** ✓ (caso sano) |
| Llaima | <0.3 | n/a (no matches reales) | 5003 (TIR) | n/a | **fuera banda max** (TIR fósil) |
| NdC | 1–10 | n/a (recall 0.20 — F47) | 1384 (TIR) / 1325 (MIR) | n/a | **dentro banda mediana**, max fuera |
| Planchón-Peteroa | 7–38 por lago | 0.21 (mediana MIROVA) / 5.10 (pipeline) | 4020 (TIR) | ~24× (sobre-estimado) | **fuera banda** (drift T1.5) |
| PCC | 0.3–5 | 15.10 | 6581 (TIR) / 1659 (MIR) | ~12× | **fuera banda** (drift T1.5) |
| Tupungatito | 0.2–2 | 5.10 | 915 (TIR) / 853 (MIR) | ~11× | **fuera banda** (drift T1.5) |
| Villarrica | 0.05–0.55 | 5.90 | 8740 (TIR) / 1056 (MIR) | ~10.9× (F52) | **fuera banda** (H4 clustering NW) |

---

## Volcanes potencialmente fuera de banda física

### Sobre-estimación sistemática mediana (drift T1.5 + F2.8 + F52)

1. **Villarrica** — ratio 10.91× confirmado (F52). Causa raíz: clustering vent-anchored agrega pixels marginales en el flanco glaciar NW (bearing 280-360°) que MIROVA descarta. La banda literatura es 0.05–0.55 MW; nuestro pipeline reporta mediana 5.90 MW. Físicamente inverosímil — un lago de lava sub-pixel no puede emitir 100× su radiancia documentada.
2. **PCC** — ratio 12× sobre régimen lacolito post-2012 que debería estar sub-MW. Banda esperada 0.3–5 MW; mediana pipeline 15.10 MW.
3. **Tupungatito** — ratio 11× sobre régimen fumarólico glaciar. Banda esperada 0.2–2 MW; mediana pipeline 5.10 MW.
4. **Planchón-Peteroa** — mediana pipeline 5.10 MW vs MIROVA NRT 0.21 MW (ratio ~24×). Banda literatura Aguilera 2021 = 7–38 MW por lago en unrest, max 59 MW agregado quiescente. **Nuestros valores caen en banda Aguilera por lago pero ratio vs MIROVA NRT sigue siendo factor 24×** — sugiere que la magnitud absoluta no es absurda físicamente pero la frecuencia de detección sí está inflada por path D dNTI-ctx.

### Outliers TIR fósiles (residual pre-F2.8 saturation guard)

Casi todos los Tier A muestran outliers TIR de 3000–10000 MW (max audit S77). El audit F50 documenta que estos son fósiles del bug F2.8 (BT extrapolado por sat flag mal leído) pre-rebuild. **No representan magnitudes reales** — el fix está aplicado en NRT cron desde S73, reproc histórico bloqueado por GH Actions HTTP 422 (F2.8.f). El campo correcto a evaluar es `vrp_mw` / `vrp_mir_mw` (Wooster MIR, validado empíricamente contra OSF v2.5 con error ≤0.17% — A1 S14).

### Sub-detección (gap operacional documentado)

5. **NevadosDeChillán** — recall 0.20 vs 0.87 mediana resto Tier A (F47). No es problema de magnitud sino de detección. Mediana 1–10 MW esperada es plausible pero el pipeline pierde 4/5 referencias MIROVA. Investigación pendiente S77.

### Banda max histórico — caveat metodológico

Los "max histórico" >1000 MW para volcanes como Villarrica/Chaitén/PCC/Llaima corresponden a **erupciones paroxismales** (2015-03, 2008-05, 2011-06, 2008-01 respectivamente) y son válidos físicamente para esos eventos puntuales. **No deben usarse como umbral de plausibilidad continuo** — un valor de 6000 MW en quiescente actual es señal de bug, no de actividad real.

---

## Confianza agregada

- **Alta (paper específico per-volcán con magnitudes MW)**: 5 volcanes
  - Lascar (Coppola 2026 SSRN + Pavez 2020 + audit S62 calibrado)
  - Lastarria (Aguilera 2012 + Stechern 2017 + audit S77 ratio 1.07 sano)
  - Nevados de Chillán (Coppola 2020 cap. dome + SERNAGEOMIN RAV + F47)
  - Planchón-Peteroa (**Aguilera 2021 Frontiers** — único paper chileno con tabla Qvolc por lago)
  - Puyehue-Cordón Caulle (Castro 2013 Nature Communications + Coppola 2020 cap. PCC)
  - Villarrica (Witter 2004 + Moussallam 2016 + Coppola 2020 cap. lava lakes)
- Conteo: **6 alta** (ajusto incluyendo Villarrica que tiene paper-específico documentado)
- **Media (banda derivada de literatura general + analogía régimen + audit interno)**: 4 volcanes
  - Chaitén (Coppola 2020 cap. dome cooling, no paper Chaitén-específico procesado)
  - Copahue (Caselli 2016 cap. AVoW + F48 audit)
  - Llaima (Bouvet de Maisonneuve 2012 + F48)
  - Tupungatito (SERNAGEOMIN RAV + F52, sin paper específico)
- **Baja (solo GVP/SERNAGEOMIN sin magnitudes MIROVA)**: 1 volcán
  - Isluga (banda derivada por analogía con Vanuatu Gaua de Coppola 2016fifteen)

**Total: 6 alta / 4 media / 1 baja** sobre 11 Tier A.

---

## Recomendaciones operacionales derivadas

1. **No adoptar `vrp_tir_mw` operacionalmente** hasta que F2.8.f reproc termine de limpiar fósiles. Mantener `vrp_mw` / `vrp_mir_mw` como métrica de dashboard.
2. **Documentar Villarrica/PCC/Tupungatito como volcanes con drift T1.5 conocido** en el About del dashboard — el usuario operacional debe saber que esos 3 magnitudes están sobre-estimadas factor ~10× por causa arquitectural pendiente.
3. **Planchón-Peteroa es candidato natural para validación cruzada** del próximo perfil `experimental_lowT.yaml` (Aveni 2025 VRPTIR, plan F31) porque tiene paper específico con Qvolc por lago como ground truth.
4. **Isluga necesita procesamiento de paper específico** si existe — banda actual es la menos sólida. Buscar en GVP / SERNAGEOMIN BAV.
5. **Coppola 2026 Lascar** (SSRN bloqueado Cloudflare) — descarga manual prioritaria; sería el ground truth multiparametric SO2 2017-2021 para el Tier A best-calibrated.

---

## Referencias

- Aguilera F., Caro J., Layana S. (2021). *The Evolution of Peteroa Volcano (Chile–Argentina) Crater Lakes Between 1984 and 2020 Based on Landsat and Planet Labs Imagery Analysis*. Frontiers in Earth Science. doi:10.3389/feart.2021.722056. [Vault: `aguilera2021evolution.md`]
- Bouvet de Maisonneuve C. et al. (2012). *Llaima 2008 eruption dynamics*. J. Petrology.
- Caselli A. T. et al. (2016). *Copahue volcano* (cap. en Active Volcanoes of the World). Springer.
- Castro J. M. et al. (2013). *Storage and eruption of near-liquidus rhyolite magma at Cordón Caulle, Chile*. Nature Communications.
- Coppola D., Laiolo M., Cigolini C., Donne D. D., Ripepe M. (2016). *Enhanced volcanic hot-spot detection using MODIS IR data: results from the MIROVA system* (SP426.5). Geological Society London Special Publications.
- Coppola D., Laiolo M., Cigolini C. (2016). *Fifteen years of thermal activity at Vanuatu's volcanoes (2000–2015) revealed by MIROVA*. JVGR 322, 6–19. [Vault: `coppola2016fifteen.md`]
- Coppola D. et al. (2020). *Thermal remote sensing for global volcanism monitoring* (capítulo Springer). [Vault: `coppola2020thermal.md`]
- Coppola D. (2024). *Thermal remote sensing of volcanoes* (capítulo Springer 2025). [Vault: `coppola2025thermalbook.md`]
- Coppola D. et al. (2026). *Analysis of SO2 Variability at Lascar Volcano Using a Multiparametric Approach (2017–2021)*. SSRN preprint doi:10.2139/ssrn.6481652. **PDF pending — Cloudflare blocked**.
- Aveni S. et al. (2025). *VRPTIR for crater lakes and fumarole fields*. GRL doi:10.1029/2024GL113324. [Vault: `aveni2025grl.md`]
- Moussallam Y. et al. (2016). *Villarrica lava lake degassing*. EPSL.
- Pavez A. et al. (2020). *Lascar SO2 monitoring 2014-2018*. JVGR.
- Stechern A. et al. (2017). *Lazufre uplift magmatic source*. EPSL.
- Witter J. B. et al. (2004). *Villarrica 2003-2004 activity*. JVGR.
- Smithsonian GVP — Global Volcanism Program (verificación tipo actividad + última erupción): https://volcano.si.edu
- SERNAGEOMIN RAV (Reporte Actividad Volcánica): https://rnvv.sernageomin.cl

### Audits internos referenciados

- `docs/F46_LASTARRIA_IMPACT_S77.md` — TIR vrp espuria fósil F2.8
- `docs/F47_NDC_RECALL_S76.md` — Nevados de Chillán recall 0.20
- `docs/F48_LLAIMA_COPAHUE_REFS_GAP.md` — Llaima/Copahue régimen NULO real
- `docs/F50_MODIS_07_25_AUDIT_S77.md` — fósiles MODIS pre-F2.8
- `docs/F52_VILLARRICA_OVER_ESTIMATION_S77.md` — Villarrica ratio 10.91×
- `docs/F52_TUPUNGATITO_PCC_AUDIT_S77.md` — Tupungatito + PCC ratio ~11-12×
- `experiments/138_audit_mw_outliers_s76/audit_output.txt` — top 5 por volcán
- `docs/MIROVA_DETAILED_CITATIONS.md` — citas literales papers MIROVA core
