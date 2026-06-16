# AUDIT_S110 — Síntesis papers-first D11 (por qué MIROVA es inmune al valle con el mismo C1)

**Fecha**: 2026-06-16. **Pedido Nicolás (S110)**: papers-first + "todos los papers relacionados"
antes de brainstormear el frente D11 (detección MODIS A69-inmune). 4 subagentes paralelos sobre
`documentacion/` (A26) + verificación de código (A48: no aceptar claim de subagente sin verificar).
Complementa `AUDIT_S110_NDC_PATH_DIAGNOSTIC.md` (el probe que aisló la rama C1).

## Punto de partida (probe S110, run 27617831259)
El leak topográfico de NdC entra 100% por el **piso absoluto C1** del first-pass (Coppola Tests 2&3,
dNTI∧dETI contextual), nunca por la rama estadística μ+C2σ. El valle pasa C1 en dNTI **y** dETI
(dETI valle ≈ 0.0125, NO ~0). MIROVA usa el mismo C1=0.003/0.010 (Tabla 1) y es inmune.

## Hallazgos por agente (con cita)

### Agent 1 — Coppola 2016a SP426.5 (`sp426_5.txt`)
- **La supresión de topografía en MIROVA es ESPECTRAL (NTI→ETI), no el filtro espacial.** Apéndice A
  trata literalmente Villarrica (Chile) y Ubinas (Perú) — cumbre nevada fría + valle tibio bajo.
  L805-818: el gradiente "is strongly reduced by performing the spatial filters (dNTI/dETI)", pero el
  mecanismo físico es que un valle homogéneo tiene NTI≈NTI_app → **ETI≈0** ("the warm lake surface
  almost disappears in the ETI map", Villarrica L814-818).
- **C1 vs μ+C2σ (L330-339)**: C1 es para escenas MUY homogéneas (piso mínimo); el detector primario
  en escenas variables es μ+C2σ. Que el valle ate por C1 con μ+C2σ arriba = el σ de escena está
  inflado por heterogeneidad nieve/valle → μ+C2σ se va alto → C1 queda como único umbral activo.
- **Background contextual = media aritmética de 8 vecinos inmediatos** (L243-244). μ/σ de los Tests
  sobre TODOS los "suitable pixels" de la escena (L327-329); unsuitable = borde + dNTI/dETI < -0.1.
- **NO hay** modelo de elevación, máscara DEM, ni filtro de superficie. Supresión = espectral + estadística.
- Hipótesis: nuestro dETI del valle NO debería superar 0.003-0.010 si el ETI cancelara bien. Auditar ETI/NTIbk.

### Agent 2 — Coppola 2023 Frontiers + 2025 cap.11 Springer (`coppola2023_frontiers.md`, `coppola2024_chapter.txt`)
- **MIROVA NO suprime FP no-volcánicos algorítmicamente — es supervisión MANUAL post-hoc** (Coppola
  2023 §2.5; cap.11 §4.1). Tolera ~5% FP que son **aleatorios espacio-temporales** (§4.1.4). Un leak
  topográfico SISTEMÁTICO y persistente (mismo valle cada noche) NO encaja → MIROVA no lo genera en detección.
- **"Insensible al calor difuso"** (§2.3): mecanismo = VRP/MIR (L_MIR≈αT⁴, 600-1500K) pondera el
  sub-pixel chico muy caliente; el área grande apenas tibia aporta poco. Es filtro de MAGNITUD, no de detección.
- **Dual-ROI que ENDURECE con la distancia** (§2.1): summit 5×5km C1=0.003/5σ; escena 50×50km
  C1=0.010 **y 10σ** (no 5σ). MIROVA reporta `max Dist` pero **no recorta por radio duro** — la defensa
  contra lejanas es el umbral más estricto (10σ), no un geofence.
- **Referencia temporal por píxel (ALICE/RST, cap.11 §2.6)**: `⊗(x,y,t)=[V−μ(x,y)]/σ(x,y)` con μ/σ
  multianuales del MISMO mes y hora. Un valle tibio permanente entra en su propio μ → no dispara.
  MIROVA NO lo usa (es espacial), pero el cap.11 lo nombra como la familia que resuelve este caso.

### Agent 3 — Massimetti tesis/Stromboli + Campus 2024 (`THESIS_MASSIMETTI`, `campus2024`, `massimetti2024`)
- Estos textos cubren el sistema **SWIR Sentinel-2** y el **método MIR de magnitud** — NO el test
  dNTI/dETI MODIS (ese está en Coppola 2016a). Confirman background = media de vecinos.
- **Geofencing 5km** en el sistema SWIR (Stromboli 2024 §3.2: "within 5 km from summit to exclude
  fires"; Sabancaya 5km; Vulcano 1km). NOTA: esto es el producto SWIR, distinto del MODIS-MIR de
  Agent 2 (que dice "no hard radius, threshold harden"). Productos distintos del mismo grupo.
- Umbral SWIR es **por-clúster (>9 px contiguos), no piso de escena** — MIROVA evita el piso uniforme.

### Agent 4 — Sistemas competidores (`HotLINK`, Laiolo/Reath/Coppola/Morelli, `Torrisi2023`, BIBLIOGRAPHY)
- Corrección de IDs: los `S0377027*` NO son NHI (son Laiolo 2017, Reath 2019, Coppola 2016 Vanuatu,
  Morelli 2022). NHI no está como PDF; su def está en `coppola2024_chapter.txt` L990-1047.
- **HotLINK** (CNN U-Net, USGS-AVO): aprende la FIRMA ESPACIAL (foco compacto vs campo difuso), solo
  MIR+TIR norm., **sin canal de elevación**, nocturno + tendencia temporal. Entrenado en volcanes
  glaciados (Veniaminof). Reconoce explícitamente "snow melting off rocky areas, solar-heated" como FP. −12% FP / +22% hotspots vs MIROVA.
- **NHI** (Genzano/Marchese): índice SWIR umbral fijo; defensa anti-valle = alta resolución 20-30m, no física. ~15% FP.
- **RST/ALICE (Tramutoli) + TIRVolcH (Aveni)**: **fondo persistente por píxel** (μ/σ multianual por
  mes+hora; RES=OBS−REF, Z>7). Resuelve el valle crónico de raíz. TIRVolcH validado en Copahue.
- **Recomendación Agent 4 (por viabilidad)**: #1 fondo persistente por píxel estacional sobre dNTI
  (menor riesgo arquitectural, alinea con A69); #2 nocturno-only; #3 compacidad de cluster; #4 ML (máx riesgo).

## Verificación de código (A48 — el claim de Agent 1 NO se acepta a ciegas)
`compute_nti_and_nti_app` (detection_context.py:536) y `compute_eti_scene_quadratic` (:610) **se ven
FIELES a Coppola Eq 1-5**: NTI=(L_MIR−L_TIR)/(L_MIR+L_TIR); NTI_app con rad_mir_app=Planck(λ_MIR,
BT_TIR); NTI_bk = regresión cuadrática scene-wide por-imagen con refit iterativo (excluye outliers
3σ). **No hay bug evidente.** Por tanto el dETI≈0.0125 del valle NO es claramente "ETI roto" — puede
ser **textura real del valle** (parches sub-píxel) que desvía localmente de la regresión, que el ETI
cancela en promedio (gradiente de gran escala) pero el dETI contextual capta.

## Convergencia → candidatos D11 (para brainstorming, MISSION)

**Dos familias:**
- **(A) Clon-literal MIROVA** — hacer que el test contextual no dispare en el valle SIN referencia
  temporal:
  - A1. **dETI absoluto del valle**: ¿ETI cancela (ETI≈0) o no? → requiere PROBE REFINADO que vuelque
    NTI/NTI_app/NTI_bk/ETI absolutos por píxel valle vs cráter. Decide si es regresión o textura.
  - A2. **Rama scene 10σ estricta** (Agent 2): el valle no es pico contextual 10σ. PERO el probe mostró
    que el binding es C1 (OR `dNTI>C1`), no μ+C2σ → endurecer C2 NO ayuda salvo que se cambie el OR.
  - A3. **Compacidad de cluster** (Agent 4 #3 / HotLINK sin ML): exigir foco compacto vs campo difuso.
- **(B) Departure de clon-literal (documentada, como el honest-anchor)** — **fondo persistente por
  píxel estacional** (ALICE/RST/TIRVolcH; convergencia Agent 2 + Agent 4). Resuelve el valle crónico
  de raíz; alinea con A69/S104. Pero NO es lo que hace MIROVA (es TIRVolcH, mismo grupo, otro sistema).

**Implicación MISSION**: (A) es preferido (clon-literal). (B) es fallback robusto si (A) no basta,
documentado como divergencia deliberada. El probe refinado (A1) es el siguiente paso decisivo: dice
si el ETI cancela el valle o no, y por ende si el fix es espectral (clon-literal) o temporal (B).

**Tensión entre agentes a resolver**: Agent 1 (raíz=ETI espectral) vs Agent 2 (raíz=no genera el leak,
dual-ROI 10σ) vs Agent 3 (geofence SWIR) vs Agent 4 (fondo temporal). El probe refinado + el dato de
que el binding es C1 (no μ+C2σ) son los árbitros.
