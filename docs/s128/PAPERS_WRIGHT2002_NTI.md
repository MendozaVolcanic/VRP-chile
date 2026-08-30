# Wright et al. (2002) — MODVOLC, el origen del NTI

*Automated volcanic eruption detection using MODIS*, RSE 82:135-155.
DOI 10.1016/S0034-4257(02)00030-5. **A9 — NO es canon MIROVA** (HIGP, Hawái): es la
infraestructura conceptual del NTI, pero donde difiera de Coppola manda Coppola.

## 1. Qué mide y con qué fórmula

**El paper NO numera la ecuación.** Aparece en prosa (p. 140):

> "normalised by the sum of the radiance's (i.e. MODIS band [22 − 32/22 + 32], or
> [21 − 32/21 + 32], where the Band 22 detectors were saturated). This approach, which,
> for convenience, we term a normalised thermal index (NTI)"

Es `(L_MIR − L_TIR)/(L_MIR + L_TIR)` sobre **radiancia cruda de L1B**, no sobre BT — y eso
fue **restricción de cómputo** ("no more than eight mathematical operations and five bands",
p. 137), no elección física: "Restrictions on the number of mathematical operations
available prevented conversion ... to brightness temperatures ... while the necessity for
the algorithm to run as a point operation meant that contextual analysis could not be
performed" (p. 138).

**Por qué normalizado y no diferencia simple.** La diferencia simple fracasa (Fig. 4): "simple
subtraction ... does not distinguish the hot lava flows from the other cover types, with the
lava pixels being particularly confused with the 'cold' cloud pixel group" (p. 138). Un
hotspot subpíxel **aplana** la pendiente de Planck entre 3,959 y 12,02 µm igual que la aplana
una nube fría: ambos colapsan al mismo ΔL. Normalizar da "an index value ... weighted to
those surfaces that emit substantial amounts of radiance at 3.959 µm" (p. 140) y rompe el
empate. **Cancela la confusión nube-fría vs lava-subpíxel, NO el fondo.**

## 2. ⚠️ Contra A69: el paper dice lo CONTRARIO

A69 afirma que "el NTI cancela la topografía". Wright dice que el NTI absoluto **depende
del fondo**:

> "As the NTI is based on absolute radiance values, variations in geography and season will
> influence its value, as MODIS Bands 21, 22, and 32 are all sensitive to variations in the
> ambient background temperature." (p. 141)

Lo cuantifica: en superficie homogénea el NTI asintótico es **≈ −0,86 a 25 °C y ≈ −0,97 a
−35 °C** (p. 144), y las variaciones de fondo "can result in a difference in NTI of 50% for
a given lava lake" (p. 145). El problema del umbral global nace de ahí: el histograma de
Erta Ale está corrido a positivo respecto del de Erebus sólo por temperatura de suelo y mar
(p. 141).

Un cráter nevado a 272 K y un valle a 281 K **no tienen el mismo NTI de fondo**. El NTI
**atenúa** el gradiente (mucho más que el MIR absoluto), no lo anula; lo cancela la forma
**diferencial** (dNTI, ETI = NTI − NTI_bk), aporte de **Coppola, no de Wright**. **A69
debería decir "atenúa"**: el dato de S104 (I04−I05 plano) sigue en pie, pero no se funda acá.

## 3. El umbral fijo: −0,80

> "we determined an empirical NTI threshold of −0.80 to be appropriate for nighttime global
> volcanic hotspot detection" (p. 144)

Derivado de **histogramas de granules nocturnos completos** de volcanes de fondo
contrastante (Erebus y Erta Ale como extremos, p. 141), donde "the extreme right-hand tail
... was composed solely of hotspot pixels". Criterio: "identify as many volcanic hotspots as
possible **without resulting in false alerts**" (p. 141) — precisión sobre recall.

- A −0,84 aparecen los 2 píxeles de Erebus, pero Erta Ale daría ">100,000 alerts" (p. 144) y
  Big Island 44 alertas, de las cuales "23 of these would be false" (p. 144) → **52 % FP**.
- A −0,80: de 21 píxeles anómalos por inspección manual "MODVOLC only classified 13 as
  hotspots" (p. 152) → **recall de píxel ≈ 62 %**, a propósito: "we realise that we forgo
  the detection of low-intensity hotspots, but we find this preferential" (p. 153).

**Nuestro K1 coincide con el origen**: `nti_k1_night: -0.8`
(`pipeline/profiles/mirova_equivalent.yaml:43`). El **−0,6 diurno NO viene de Wright**:
MODVOLC 2002 es sólo nocturno, la versión diurna estaba "currently under development"
(p. 153). `NTI_K1_DAY` (`pipeline/profile.py:202`) no tiene este paper como fuente.

## 4. Bandas — discrepancia real

MODVOLC usa **21/22 y 32**: 21 y 22 "detect radiance in the same spectral interval
(3.929–3.989 µm)"; "Band 32 (which images between 11.770 and 12.270 µm)" (p. 137). Nosotros
usamos **banda 31** (`process_modis.py:495`, "E3: TIR Band 31 for NTI"). Wright 32, Coppola
2013 32, nosotros 31. **No es equivalente**: el NTI de fondo cambia con λ_TIR y el −0,80 se
calibró **con banda 32**.

La prioridad MIR además está **invertida**: Wright usa 22 primaria por radiometría (NEΔT
0,07 K vs 2,0 K, p. 137) y cae a 21 sólo si satura (SI = 65533, p. 146). Nosotros: "use Band
21 primary, Band 22 where 21 is NaN (saturated)" (`process_modis.py:477`) — ganamos rango
dinámico y perdemos ~30× de resolución radiométrica en el régimen sub-MW.

## 5. Fondo y contexto: MODVOLC no tiene ninguno

**Cero fondo, cero contexto, cero máscara de nube.** Operación puntual, umbral global fijo.

- **Frente 2 (fondo autorreferente)**: en el origen del NTI el problema **no existe**.
  Nuestro `nti_path_hot` NO es el test de Wright: es `(nti > −0.8) & (bt_mir > t_bg + 3.0K)`
  (`process_modis.py:598-604`; `NTI_BT_SANITY_K = 3.0`, verificado con
  `python -c "import pipeline.profile as p; print(p.NTI_BT_SANITY_K)"`). El término relativo
  al fondo lo agregamos nosotros, y por ahí entra la autorreferencia.
- **Frente 4 (nube apagada)**: MODVOLC tampoco filtra nube y admite el costo: "clouds
  prevent detection of hotspots, but without actual image data, it is impossible to deduce
  their impact" (p. 153). **Apoya D14.**
- **Frente 3 (grilla UTM)**: trabaja en swath y reporta lat/lon de píxel (~200 m, p. 137);
  **no hay resampleo**. La grilla es invención de MIROVA.
- **Frente 1 (piso VRP)**: prohibición explícita de cuantificar con NTI — "it should not be
  used as the basis for quantitative analysis" (p. 145). El criterio de p. 153 respalda un
  piso y **contradice** nuestra prioridad de recall sobre precisión.

## 6. Sol, nieve, terreno, saturación, geometría

- **Solar**: la única defensa es ser nocturno. Reconoce el problema — "anomalously
  reflective surfaces appearing 'hot' in daytime 4-µm imagery" (p. 138) — y lo evita en vez
  de tratarlo. **Nada sobre nieve, agua, arena ni sun glint** por nombre.
- **Terreno**: "mountain tops" sólo como superficies frías de NTI bajo (p. 138). **Ningún
  tratamiento del gradiente topográfico.**
- **Saturación**: 22 ≈ 330 K; 21 diseñada a ≈ 500 K pero calibrada sólo a ≈ 400 K tras la
  calibración lunar de nov-2000; 32 a 420 K (p. 137).
- **Geometría**: registra "satellite zenith, satellite azimuth, and solar zenith" (p. 146)
  pero **NO corrige área de píxel por ángulo de barrido**. Sí advierte el ensanchamiento
  across-track: un hotspot "is likely to be represented by one or two across-track pixels",
  sin doble conteo porque el dwell time es constante (p. 137). **Compatible con nuestro
  nadir-fijo (A66/A67).**

## 7. Qué NO dice, contra lo que se le atribuye

1. **No dice que el NTI cancele el fondo ni la topografía**: dice lo opuesto (§2).
2. **No propone el NTI como magnitud**: lo prohíbe (p. 145). Y **no usa banda 31**, usa 32.
3. **No es no-contextual por convicción, sino por presupuesto de cómputo.** Wright reconoce
   que el método espectral es superior — "The spectral comparison method is a much more
   robust way to detect hotspots than simply thresholding raw 4-µm radiance data" (p. 138) —
   y lo descarta por restricción del DAAC. **Coppola construye MIROVA sobre lo que Wright no
   pudo hacer.** Citar el −0,80 como "el umbral correcto" ignora ese párrafo entero.
4. **No valida cuantitativamente** contra terreno (salvo Rothery et al., in press, p. 152).

## 8. Bibliografía citada que NO tenemos (`ls documentacion | grep -iE` dio cero)

Sin DOIs en el paper. **Flasse & Ceccato (1996)** IJRS 17:419-424 — contextual AVHRR, raíz
de lo que Coppola sí adopta: el más relevante al frente 2. **Dozier (1981)** RSE 11:221-229
— método subpíxel. **Kaufman et al. (1998)** JGR 103:32215-32238 — MODIS fire, contextual.
**Barnes et al. (1998)** IEEE TGRS 36:1088-1100 — saturación. También Harris, Swabey &
Higgins (1995); Flynn et al. (2002); Rothery, Thorne & Flynn (in press).

## 9. Acciones

**Corregir A69** ("atenúa", no "cancela") y **abrir divergencia banda 31 vs 32** (el −0,80 se
calibró con 32). Frente 1: Wright respalda un piso. Frente 4: respalda D14.
