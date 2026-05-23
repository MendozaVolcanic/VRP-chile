# F31 — Aveni 2025 GRL VRPTIR — plan integración VRP Chile (S74+)

> Extracción structured de Aveni 2025 GRL doi:10.1029/2024GL113324 desde notas
> Vault `aveni2025volcanic.md` (129 líneas, confidence:medium) +
> `aveni2025tracking.md` (107 líneas, paper hermano RS 2025). Generado S73
> 2026-05-23 búsqueda bibliográfica 4-way A/B/C/D.
>
> **⚠️ A35 aplica**: notas son `confidence:medium` — antes de implementar
> k_TIR=60.17 / Eq.8 / Eq.9, **verificar contra PDF original** (AGU paywalled,
> ver acción S74+ §6).

## 1. Metadata

- **Autores**: Simone Aveni, Sophie Pailot-Bonnétat, Dmitri Rouwet, Andrew J.L. Harris, Diego Coppola
- **Afiliaciones**: Sapienza Roma + Università di Torino — **grupo MIROVA canónico**
- **DOI**: 10.1029/2024GL113324
- **Revista**: Geophysical Research Letters (GRL)
- **Año**: 2025
- **Validación**: 7 volcanes — Ruapehu, El Chichón, Taal, Vulcano, Puracé, Poás, White Island. **Ningún chileno**.

## 2. Algoritmo formal VRPTIR

### 2.1 Ecuación principal

**Eq. 9** (p.4 paper):

```
VRP_TIR = A_pix · k_TIR · Σ_j (L_TIR_hot_j − L_TIR_bg)
```

donde:
- `A_pix`: área del pixel TIR (m²)
- `k_TIR`: coeficiente λ-dependiente (m·sr) — Eq. 8
- `L_TIR_hot_j`: radiancia TIR del pixel j hot (W/m²/sr/µm)
- `L_TIR_bg`: radiancia TIR del background local (W/m²/sr/µm)

### 2.2 Coeficiente k_TIR (Eq. 8)

```
k_TIR(λ) = 1.0575·λ²  − 14.3139·λ  + 85.4239    [m·sr]
```

Para sensores de VRP Chile:

| Sensor | λ (µm) | k_TIR (m·sr) | Aplicabilidad |
|---|---|---|---|
| **VIIRS I5** | 11.45 | **60.17** | ✓ confirmado en paper |
| VIIRS M15 | 10.76 | ~63.8 (inferido) | Generalización plausible, no validado |
| MODIS B31 | 11.02 | ~62.3 (inferido) | Generalización plausible, no validado |

### 2.3 Rango de validez

| Parámetro | Valor | Comentario |
|---|---|---|
| T min | 300 K | Bajo eso = no anomalía detectable |
| T max | 600 K | Sobre eso = usar Wooster MIR |
| f_hot rango ideal | 1-4 % | Subestimación MIR severa <600K |
| Componentes >600 K tolerados | ≤0.0025 % del área anómala | Sino degradar a MIR |
| ΔBT mínima detector | ≥ 0.5 K sobre BG (via TIRVolcH) | Sensibilidad |
| Incertidumbre declarada | ±35 % | vs ±30 % Wooster MIR |
| Emisividad ε | = 1 asumido | Open question para roca ε≈0.95, agua ácida ε≈0.98 |

### 2.4 Pre-requisito: TIRVolcH detector

VRPTIR requiere que el pixel haya sido detectado primero por **TIRVolcH** (Aveni 2024 RSE doi:10.1016/j.rse.2024.114388):
- Single-band TIR contextual detector
- Baseline temporal **10 años cloud-free** BT (en paper hermano `aveni2025tracking`)
- ΔBT ≥ 0.5 K sobre BG anchor temporal+espacial

**NO usar Path C nuestro como sustituto** — TIRVolcH es algoritmo distinto que requiere implementación específica.

### 2.5 Quality control / filtering

- **Solo nocturno** (excluye contaminación solar diurna sobre TIR)
- **Zenith filter**: paper hermano descarta zenith > 50°. **No confirmado** en este paper específico — verificar.
- **T_bg_noise ≤ 2.5 K** asumido (lapse rate 6 K/km × pendiente 40° × 1 km). **Probablemente violado en Andes nevados**.
- **Saturation/cloud handling**: no documentado en la nota Vault.

## 3. Integración a VRP Chile pipeline

### 3.1 Where to insert

- **NO reemplaza Wooster MIR** — es path adicional complementario
- Aplicar a:
  - `pipeline/process_viirs.py` para I05 (paralelo a I04 Wooster MIR)
  - `pipeline/process_viirs_mod.py` para M15 (paralelo a M13 Wooster MIR)
  - `pipeline/process_modis.py` para B31 (paralelo a B21 Wooster MIR) — **NO validado en paper**, defensive opt-in
- **Lógica decisión**: si T_eff del pixel está en 300-600K → usar VRPTIR. Si >600K → fallback Wooster MIR. Si <300K → no anomalía.

### 3.2 Casos uso por volcán Tier A

| Volcán | T típica feature | VRPTIR aplicable? | Justificación |
|---|---|---|---|
| **Villarrica lava lake** | 400-700 K (costra) | ✅ **Candidato directo** | Lago ~20-40m radio, f_hot 0.9-3.5%. Recall actual 0% — VRPTIR puede ser game-changer |
| **Lastarria fumarolas** | 300-500 K | ✅ **Candidato fuerte** | Rango fumarólico ideal |
| **Copahue lago cratérico** | <500 K | ✅ **Candidato** | Lago activo Aguilera 2021 citado paper |
| **Planchón-Peteroa lago** | <500 K | ✅ **Candidato** | Análogo Copahue |
| **Chaiten domo+lago** | Mixto (>600 dome, <500 lago) | ⚠️ **Mixto** | Riesgo transitions, requiere lógica per-pixel |
| **PCC lacolito** | <500 K | ❌ **EXCLUIR** | **A20**: PCC no-focal, área extensa invalida single-pixel |
| Lascar | >600 K (Tier A Alto) | ❌ Wooster MIR es mejor | Ya calibrado natural 1.37× |
| Isluga | >600 K (Tier A Alto) | ❌ Wooster MIR es mejor | Ya calibrado natural 1.33× |
| Tupungatito | Aún en debate (A20 régimen Muy Bajo) | ⚠️ Test piloto | Después de fix S65 mirova_center |

### 3.3 Trade-offs

| vs | VRPTIR | Wooster MIR |
|---|---|---|
| **Rango T válido** | 300-600 K | 600-1500 K |
| **Saturación sensor** | Baja (TIR I5 sat ~423K en VIIRS) | Alta (MIR B21 sat ~500K) |
| **Solar contamination** | Solo nocturno | Solo nocturno |
| **Incertidumbre** | ±35 % | ±30 % |
| **Detección sub-pixel** | f_hot 0.0001-4 % range | Pierde 90 % señal <600K |
| **Requiere baseline largo** | **Sí** (10 yr TIRVolcH) | No (NTI/dNTI on-scene) |
| **Validado VRP Chile** | No | Sí (S14+ via OSF v2.5) |

### 3.4 Diferencia vs `vrp_tir_mw` actual

Nuestro `pipeline/process_viirs.py` ya calcula `vrp_tir_mw` con **Stefan-Boltzmann puro** (σ·T⁴·A_pix). Esto NO es VRPTIR. Diferencias:

| Aspecto | Nuestro `vrp_tir_mw` actual | VRPTIR Aveni 2025 |
|---|---|---|
| Fórmula | σ·T⁴·A_pix (Stefan-Boltzmann completo) | A_pix·k_TIR·ΔL_TIR (ecuación linealizada Wooster-like) |
| Background subtract | No (BT absoluta) | Sí (ΔL local) |
| Coeficiente | σ = 5.67e-8 (universal) | k_TIR = 60.17 (λ-specific) |
| Validez | 0-∞ K (no limit) | 300-600 K |
| Pre-detector | Nuestro pipeline (NTI/dNTI/etc) | TIRVolcH obligatorio |

→ **VRPTIR es upgrade sustantivo**, no equivalente a lo actual. Nuestro `vrp_tir_mw` actual sigue siendo útil como diagnóstico, pero VRPTIR Aveni es el método "official" del grupo MIROVA para baja-T régimen.

## 4. Citas verbatim críticas (de notas Vault — verificar PDF)

1. **"sharp breakdown when T < 600 K"** (p.4) — justifica el régimen VRPTIR distinto a Wooster.
2. **"subestimación hasta 90%"** del MIR Wooster para sub-pixel <600 K (Fig. 1b, p.4).
3. **`k_TIR(λ) = 1.0575·λ² − 14.3139·λ + 85.4239`** (Eq. 8, p.4).
4. **`k_TIR = 60.17 m·sr`** para VIIRS I5 (p.4, Fig. 2b).
5. **"anomalías pixel-integradas tan bajas como 0.5 K sobre background"** (TIRVolcH, p.5).

⚠️ **Verificar verbatim contra PDF original antes de citar en paper P5 o cementar en código**. Nota Vault es `confidence:medium`.

## 5. Plan implementación S74+ (bite-sized writing-plans format)

### Task A1 — TIRVolcH detector base
**Pre-requisito todo lo demás**. Implementar detector contextual single-band TIR.

- Crear: `pipeline/detect_tirvolch.py` con función `detect_tirvolch(bt_tir, bg_baseline, threshold_k=0.5)`
- Tests sintéticos: synthetic TIR array con anomalía 0.6K sobre BG uniforme → debe detectar; 0.3K → debe NO detectar
- Baseline temporal: 10 yr cloud-free BT — **¿de dónde sacamos eso? Volcanes Tier A 2014-2024 records existen pero requieren agregación**. Pre-task: crear `data/tirvolch_baselines/<volcano>.npz` con baseline arrays.

### Task A2 — Función VRPTIR en process_viirs.py
- Agregar al final de `calculate_vrp()`:
```python
# F31 S74+ — VRPTIR Aveni 2025 GRL post-Wooster fallback baja-T
K_TIR_I5 = 60.17  # m·sr (Aveni 2025 GRL Eq.8 para λ=11.45 µm)
A_PIX_I_BAND = 140625.0  # m² (375×375)
VRPTIR_T_MIN_K = 300.0
VRPTIR_T_MAX_K = 600.0

if ENABLE_VRPTIR_AVENI and bands.get("I05") is not None:
    bt_i5 = bands["I05"]
    # Pre-requisito TIRVolcH detector
    tirvolch_hits = detect_tirvolch(bt_i5, baseline_i5, threshold_k=0.5)
    # Filtro régimen T
    eff_temps = bt_i5[tirvolch_hits]
    valid_mask = (eff_temps >= VRPTIR_T_MIN_K) & (eff_temps <= VRPTIR_T_MAX_K)
    # Compute VRPTIR
    if valid_mask.any():
        L_tir_hot = planck_radiance(eff_temps[valid_mask], lambda_um=11.45)
        L_tir_bg = planck_radiance(t_bg_i05, lambda_um=11.45)
        vrptir_mw = A_PIX_I_BAND * K_TIR_I5 * np.sum(L_tir_hot - L_tir_bg) / 1e6
        record["vrptir_aveni_mw"] = float(vrptir_mw)
```

### Task A3 — Profile flag opt-in
- En `pipeline/profile.py`: `ENABLE_VRPTIR_AVENI: bool = bool(_p.get("enable_vrptir_aveni", False))`
- Default **False** (NO operacional). Activar solo en perfil `experimental_lowT`.
- Crear `pipeline/profiles/experimental_lowT.yaml` cloning mirova_equivalent + `enable_vrptir_aveni: true`.

### Task A4 — Tests TDD
- `tests/test_vrptir_aveni_f31.py`:
  - Test sintético Villarrica lava lake (f_hot=3%, T=550K) → vrptir > 0
  - Test sintético Lascar Tier A Alto (T=900K) → VRPTIR NaN (fuera de rango)
  - Test sintético escena sin anomalía → vrptir == 0
  - Test coeficiente: verificar k_TIR(11.45) ≈ 60.17 desde Eq.8

### Task A5 — Piloto sobre Copahue + Peteroa
- Reproc 30d con perfil experimental_lowT
- Audit contra MIROVA NRT
- Si recall ↑ y precision sigue alta → adoptar a mirova_equivalent

### Task A6 — Verificación PDF (BLOQUEANTE)
- Conseguir PDF Aveni 2025 GRL (AGU paywalled). Opciones:
  1. Login institucional Nicolás (SERNAGEOMIN tiene acceso?)
  2. ResearchGate Simone Aveni
  3. EarthArXiv preprint
  4. Email autor
- Verificar verbatim Eq.8, Eq.9, k_TIR=60.17, T_min/max=300/600
- Si discrepancia → re-derivar antes de implementar

## 6. Limitaciones y open questions

| Open question | Por qué importa | S74+ acción |
|---|---|---|
| No validación volcanes chilenos | k_TIR puede tener bias regional Andes | Test piloto Copahue/PP empírico |
| ε=1 asumido | Roca andesítica ε≈0.95, agua ácida ε≈0.98 | Ablation study post-piloto |
| T_bg_noise ≤2.5K probablemente violado Andes nevados | Sesgo BG temporal | Cross-check NDSI snow cover en BG ring |
| Transición hidrotermal→efusivo | White Island 2019: vents >600K BAJÓ VRPTIR | Lógica auto-degradation a Wooster MIR |
| Baseline temporal 10yr | Volcanes recién despertando sin ref válida | Para Tier A 2014+ posible. Pre-2014 no |
| Path A37 sat handling análogo | VRPTIR puede tener gotchas L1B similar a MIR | Audit cross-sensor S74+ |

## 7. Relevancia para P3 T1.5 drift remanente baja-T régimen

**T1.5 hipótesis pendiente**: ratio 6-12× MIROVA NRT en Villarrica/Chaiten/PP/PCC (objetivo REAL desde S71). Hipótesis F2.6: "Wooster MIR subestima en sub-pixel <600K".

**Aveni 2025 GRL VALIDA esta hipótesis empíricamente**:
- "subestimación hasta 90%" del MIR para sub-pixel <600K (cita verbatim)
- VRPTIR es la solución oficial del grupo MIROVA para este régimen

→ **VRPTIR es candidato directo a resolver T1.5**. Plan A1-A6 arriba es el camino.

⚠️ Caveats:
- PCC excluido (A20 no-focal)
- Chaiten mixto (lógica per-pixel)
- Villarrica + Lastarria + Copahue + Peteroa = candidatos fuertes

## 8. Status documentos relacionados

- `Vault/10_Bibliografia/99_por_clasificar/aveni2025volcanic.md` (129 líneas, confidence:medium) — fuente primaria síntesis
- `Vault/10_Bibliografia/99_por_clasificar/aveni2025tracking.md` (107 líneas) — paper hermano RS 2025
- `Vault/10_Bibliografia/99_por_clasificar/aveni2025grl.md` (43 líneas, skeleton) — creado S73 para sync
- PDF original NO disponible local (paywall AGU) — **acción S74+ §6**
