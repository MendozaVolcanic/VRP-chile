# Plan S53+ — implementar VRPTIR (Aveni 2025 GRL) para resolver over-detection magnitud Villarrica

> Documento creado S52 cierre (2026-05-17) tras búsqueda exhaustiva online +
> hallazgo Aveni 2025 GRL **"Volcanic Radiative Power Retrieval From
> Moderate-to-Low-Temperature Features Using a Single TIR Band"**
> (DOI 10.1029/2024GL113324, Aveni + Coppola + Harris + Rouwet —
> Torino + Sapienza + LMV + INGV = MIROVA core).

## Hallazgo que cambia el plan

El paper Aveni 2025 GRL — disponible local en
`documentacion/Geophysical Research Letters - 2025 - Aveni - Volcanic Radiative Power Retrieval From Moderate-to-Low-Temperature Features.pdf`
— introduce **Equation 9: VRPTIR** específicamente diseñada para sistemas
con T efectiva 300-600 K (crater lakes, fumarolas, hidrotermales):

```
VRPTIR = A_pix × k_TIR × Σ_j=1..N (L_TIR_hot_j − L_TIR_bg)
```

Donde **k_TIR = 60.17 μm·sr** para banda 11.45 μm (= VIIRS I05 + MODIS B31).

**Citas literales del paper relevantes**:
- p3: "the relations governing the MIR method [Wooster] undergo a sharp
  breakdown when T < 600 K. This results in a substantial underestimation
  of the Volcanic Radiative Power (VRP) at active volcanic systems
  associated with low-to-moderate temperature surfaces, such as at
  fumarole fields, crater lakes or cooling lava flows".
- p5: "Uncertainty on VRPTIR is ±35%".
- Validado contra ground truth en: **Ruapehu, El Chichón, Taal, Vulcano,
  Puracé, Poás, White Island**.

## Por qué resuelve el gap MW Villarrica observado S52

| | MIROVA reporta | VRP-chile (Wooster MIR) | Ratio |
|---|---:|---:|---:|
| Mediana 5 alertas comunes | 0.21 MW | 6.63 MW | 32× |

**Hipótesis**: Villarrica lava lake oculto sub-pixel tiene **T efectiva
integrada 300-500 K** (mezcla lava 1000K + nieve 270K en pixel 375m).
Wooster MIR está calibrado para T > 600 K y diverge fuera del rango. MIROVA
aplica VRPTIR (Eq.9 Aveni 2025) que es válido en ese rango → reporta
0.1-0.3 MW.

Nuestro `pc.vrp_mw` aplica Wooster MIR sum sobre todos los pixels del
cluster → magnitud inflada 30×.

**Implementar VRPTIR como path alternativo cuando T_eff < 600 K resuelve
el gap MW operacional.**

## MISSION.md compliance check (3 preguntas)

1. **¿Está en papers MIROVA core?** **SÍ — Aveni 2025 GRL, autoría Coppola +
   Aveni + Harris (Torino + Sapienza + LMV)**. Lista oficial CLAUDE.md ya
   incluye "Aveni 2024 RSE TIRVolcH" como autoridad MIROVA; Aveni 2025 GRL
   es del mismo grupo, mismo método extendido.
2. Q2 no necesaria (Q1 sí).

**Veredicto**: Implementación PASA MISSION.md.

## Plan implementación S53-S56

### S53 — Investigación profunda + design doc (~3h)

- [ ] Re-leer Aveni 2025 GRL completo (1064 líneas markdown)
- [ ] Verificar Coppola 2024 chapter §2.3 si referencia VRPTIR o anuncia
- [ ] Re-leer Coppola 2024 chapter Eq.16 (Stefan-Boltzmann TIR previo) —
      ¿VRPTIR la deprecia o complementa?
- [ ] Comparar Eq.9 VRPTIR vs nuestro código actual
      `pipeline/process_viirs.py:870` (`vrp_w5 = ... SIGMA * (hotpix5^4 - t_bg_i05^4)`)
      → ya usamos Stefan-Boltzmann TIR pero con `SIGMA = 5.67e-8` y cuarta
      potencia, NO con k_TIR=60.17 y diferencia lineal radiancias
- [ ] **Hipótesis preliminar**: ya tenemos `vrp_tir_mw` calculado pero con
      Stefan-Boltzmann (Coppola 2024 Eq.16, también de Aveni grupo) NO con
      VRPTIR Eq.9 (Aveni 2025 GRL). Verificar.
- [ ] Design doc `docs/superpowers/specs/2026-05-1X-vrptir-implementation.md`
      con: motivación, fórmula Eq.9 literal, casos de aplicación,
      criterio activación path TIR vs MIR, tests sintéticos

### S54 — Implementación TDD (~4h)

- [ ] Tests sintéticos `tests/test_vrptir_aveni2025.py`:
  - test pixel monocomponente T=400K → VRPTIR esperado ±35%
  - test pixel mixed f_hot=0.001 + T_hot=1000K → underestimación esperada
  - test rango T válido [300-600K], rechazo fuera
  - test 5 casos canónicos Villarrica reales (BT desde records actuales)
- [ ] Implementar función `compute_vrptir_eq9(bt_i05, t_bg_i05, pixel_areas)`
      en `pipeline/process_viirs.py`
- [ ] Path análogo en `pipeline/process_modis.py` (B31)
- [ ] Flag profile `enable_vrptir_low_temperature` (default OFF inicialmente)
- [ ] Criterio activación: cuando `t_max_i05 < 600 K` → usar VRPTIR para
      reportar pc.vrp_mw_low_T además del Wooster MIR

### S55 — A/B reproc validation (~30 min disparar + 1h analizar)

- [ ] Workflow A/B: `_vrptir_enabled` vs `_vrptir_disabled` window 30d
- [ ] Métricas:
  - ratio MW vs MIROVA (esperado: cae de 30× a <3×)
  - recall mantiene (esperado: sin regresión)
  - F1 mantiene (esperado: mejora o igual)
- [ ] R2 pixel-level: comparar 5 alertas MIROVA conocidas vs VRPTIR estimate

### S56 — Decisión adopción + dashboard (~2h)

- [ ] Si A/B valida: activar `enable_vrptir_low_temperature: true` en
      `mirova_equivalent.yaml`
- [ ] Frontend: mostrar 2 valores: "VRP MIR (Wooster)" y "VRP TIR (VRPTIR
      crater lake)" con explicación qué usar cuándo
- [ ] Doc `docs/HYPOTHESIS_LOG.md`: H_S55_VRPTIR_ADOPTED entry
- [ ] Actualizar `tasks/backlog_no_mirova.md`: REMOVER "Test 1 integrated
      VRP" porque AHORA SÍ hay fórmula MIROVA-compliant (Aveni 2025 GRL Eq.9)

## Riesgos / pendientes

1. **Verificar primero que vrp_tir_mw actual NO es ya VRPTIR**: nuestro
   código usa Stefan-Boltzmann (Eq.16 Coppola 2024 chapter), no Eq.9 Aveni
   2025. Necesario verificar literal en código.
2. **Criterio activación T<600K** puede no aplicar a Lascar (cráter activo
   T>800K fumarólico). Verificar per-vol.
3. **Uncertainty ±35%** VRPTIR Aveni 2025 vs ±30% MIROVA NRT. Suficiente.
4. **k_TIR=60.17** es solo para banda 11.45 μm. VIIRS I05 (11.45) y MODIS
   B31 (11.03) — para B31 podría necesitar otro k según Eq.8 paper:
   `k_TIR = 1.0575·λ² − 14.3139·λ + 85.4239` → λ=11.03 → k=46.61.

## Contraste con plan previo S53-S57 (subagente)

El plan previo del subagente proponía 4 hipótesis H_VI_1 a H_VI_4 y
experimentos secuenciales. **Este nuevo plan reemplaza el anterior** porque
H_VI_3 (Dozier sub-pixel two-component) ya tiene fórmula concreta y
publicada por mismo grupo MIROVA (Aveni 2025 GRL Eq.9), que es más
simple y directa que el two-component Dozier completo.

Los experimentos E1 (inner=2km) y E2 (cluster size) del plan anterior
quedan como **investigaciones secundarias** después de validar VRPTIR.

## Update tasks/backlog_no_mirova.md

Entry #2 "Test 1 integrated VRP — fórmula para magnitud sub-pixel summit"
debe actualizarse: **PROPUESTA EXISTE** (Aveni 2025 GRL Eq.9), pendiente
implementación S53-S56.
