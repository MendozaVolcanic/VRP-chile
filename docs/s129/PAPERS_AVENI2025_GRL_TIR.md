# Aveni et al. 2025 (GRL) — VRP<sub>TIR</sub> de una sola banda TIR

**Cita**: Aveni, Pailot‑Bonnétat, Rouwet, Harris & Coppola (2025), **GRL 52, e2024GL113324**,
doi:10.1029/2024GL113324. Canon MIROVA (Sapienza + Torino, Coppola último autor). 13 pp.
PDF en `documentacion/` + texto extraído en `aveni2025_crater_lakes.md`.

---

## Veredicto sobre D3

**No justifica reabrir D3 como está planteada, y la premisa del handoff es falsa en dos puntos.**
Primero: el paper **sí se leyó** — está implementado verbatim en `pipeline/vrptir.py` desde S74
(Eq.8 y Eq.9, k<sub>TIR</sub>=60,17, rango 300–600 K, docstring que dice "VERIFICADO contra PDF
original"). Segundo, y más importante: **su rango de validez declarado empieza en ~300 K y nosotros
vivimos por debajo.** Verificado sobre nuestros datos: de 21.554 registros VIIRS con `t_max_i05_k`,
la mediana es **279,2 K**, el p95 **288,4 K**, y sólo el **0,02 %** llega a 300 K. Aplicar la Eq.9
en nuestros once volcanes sería usarla fuera del dominio que sus propios autores le fijan.

Pero D3 **debería cerrarse por una razón distinta a la que dice el `CLAUDE.md`**: hoy el VRP TIR es
prácticamente un campo muerto. `vrp_tir_mw > 0` en **28 de 24.225** registros (0,12 %), y cuando
dispara da mediana 84 MW y máximo 4.817 MW — o sea, cuando no es cero es saturación, no señal.
Discutir qué constante usar en un campo que se emite el 0,12 % de las veces es optimizar ruido.

---

## 1. La ecuación y su constante (verbatim, con página)

**Eq. 8, p. 4**: «*k*<sub>TIR</sub> = 1.0575 × λ² − 14.3139 × λ + 85.4239».

**Eq. 9, p. 4**: «VRP<sub>TIR</sub> = A<sub>pix</sub> · k<sub>TIR</sub> · Σ<sup>N<sub>pix</sub></sup><sub>j=1</sub> ( L<sup>TIR</sup><sub>hot j</sub> − L<sup>TIR</sup><sub>bg</sub> )»,
donde (pp. 4–5) «*L<sup>TIR</sup><sub>bg</sub> is the background spectral radiance (assumed to equal to
that of the surrounding hotspot‐free pixels)*».

**La constante** (pie de Fig. 2, **p. 5**): «*In the range ∼300–600 K, delimited by the vertical red
line, and for λ = 11.45, optimal k<sub>TIR</sub> has a value of 60.17 μm · sr … ± 35%*».

**Origen: empírico, no teórico.** Sale de un Monte Carlo de píxeles mixtos (p. 3): «*we synthesized
subpixel temperature distributions for 10 million different scenarios*». Y (p. 4): «*The ratio
k<sub>TIR</sub> thus represents the **empirically‐derived** constant of proportionality*». La
constante misma no se valida contra terreno; la validación de terreno (Ruapehu, ρ=0,93, R²=0,87) es
del método completo.

**Unidades**: k<sub>TIR</sub> en μm·sr; A<sub>pix</sub> en m²; VRP<sub>TIR</sub> en W.
**Rango de validez declarado**: λ ∈ [10,5–12] μm y T<sub>eff</sub> ∈ [~300, ~600] K; incertidumbre
**±35 %** (p. 5: «*Uncertainty on VRP<sub>TIR</sub> is ± 35%*»). Techo adicional (p. 5): la relación
aguanta un componente a 900 K sólo «*if the area occupied by hot vents (at T = 900 K) does not exceed
0.0025% of the total thermal anomaly captured within the pixel*».

## 2. ¿En qué régimen supera a Stefan‑Boltzmann puro?

Acá está lo que sí nos toca. **Lo que nosotros llamamos "Stefan‑Boltzmann puro" es literalmente su
Eq. 5**, la que el paper existe para refutar. Verificado en nuestro código:
`pipeline/process_viirs.py:326-328` calcula `hot_area * SIGMA * (hotpix**4 - t_bg_i05**4)`, idéntico
a la Eq. 5 (p. 3): «RP<sub>Pixel</sub> = A<sub>pix</sub> · σ · ε · ( BT⁴<sub>hot</sub> − BT⁴<sub>bg</sub> )».

El paper la califica sin ambigüedad (p. 3): «*This assumption simplifies the mixed pixel scenario to a
"pure pixel" model … where a single, homogeneous thermal component exists … **However, this is seldom
the case** (Oppenheimer, 1993)*». Y cuantifica (p. 3): «*Figure 1 illustrates how deviation from the
pure pixel assumption (Equation 5) leads to an **underestimation in RP by up to ∼50% when T ≤ 600 K,
and over 90%** when a high‐temperature thermal component occupies only a small fraction of the
pixel*». El abstract (p. 1) lo repite: «*up to a ∼90% RP underestimation of ≲600 K sources*».

**Dirección: sub‑estima, nunca sobre‑estima.** El sesgo crece cuando el foco caliente ocupa poca
fracción del píxel — exactamente nuestra situación sub‑píxel. Es comparación cuantitativa (Fig. 1b),
no afirmación cualitativa. **Pero** el eje de esa figura es T del componente caliente, no el ΔT del
píxel: nuestros 6,8–17 K de ΔT no son T<sub>eff</sub>, y el paper no simula fondos de 265–270 K.

## 3. Una sola banda TIR: qué gana, qué pierde

Gana **sensibilidad a baja temperatura** (ley de Wien, p. 1) y cubre el hueco donde el MIR se rompe
(p. 3): «*the relations governing the MIR method undergo a sharp breakdown when T < 600 K*». Pierde
el techo: sobre 600 K hay que volver a Wooster. Son complementarios, no competidores.

**No sirve de día**: el paper es tan nocturno como nosotros (p. 6): «*The algorithm processes
**nighttime** TIR scenes from the VIIRS I5 channel (11.45 μm)*». Y en conclusiones (p. 9) advierte
que las superficies medidas pueden estar tibias por «*thermal inertia, **solar irradiation**, and
other environmental processes*». El TIR no escapa al sol, sólo lo sufre distinto.

## 4. Piso de detección y límite inferior

**No dice nada de un piso en MW.** Ni 0,1 ni 2 MW: cero menciones de umbral de magnitud en 13
páginas. Lo único cercano es un umbral **térmico** heredado de TIRVolcH (p. 6): «*capable of detecting
thermal anomalies for pixel‐integrated temperatures as low as **0.5 K** above the surrounding
hot‐spot‐free background*». El canon empuja el piso **hacia abajo**, no hacia arriba: la línea de
Coppola 2014 se mantiene. **Este paper no da soporte a instalar un piso VRP.**

## 5. Fondo

Confirma la regla: el fondo son los píxeles vecinos **no alertados** (p. 3, «*surrounding pixels free
of hotspot‐contamination*»; pp. 4–5, «*surrounding hotspot‐free pixels*»). Tercer testimonio del canon
a favor de encender nuestro filtro contextual. Y un dato que nos incomoda (p. 4): el ruido de fondo
máximo asumido es «*T<sub>bg noise</sub> … set to 2.5 K, based on a ground projection of a 1 × 1 km
pixel for a surface with a 40° slope*» — la física del gradiente topográfico de A69, acotada a 2,5 K.
Nuestro artefacto de nevado excede ese supuesto.

## 6. Contradicciones, atribuciones falsas y citas nuevas

**Nos contradice** en que nuestro VRP TIR de producción es su Eq. 5, la que el paper declara sesgada
hasta −90 %. La divergencia no es "usar o no k=60,17": ambos extremos están fuera de régimen.

**Qué NO dice, contra lo que se le atribuye.** El `CLAUDE.md` lo rotula «investigación no adoptada
operacionalmente». El paper **no se presenta como exploratorio**: es método operacional exportable,
validado 12 años en Ruapehu sobre VIIRS NRT/LANCE. Tampoco es alternativa a Wooster: es su
**complemento por rango térmico**. Y **no prescribe TIR para actividad efusiva** — la Eq. 9 es
«*intended for systems dominated by temperatures typical of non‐eruptive processes*» (p. 6): lagos
cratéricos, fumarolas, híbridos. Nuestra etiqueta era correcta en la conclusión y falsa en el motivo.

**Estatus real en nuestro código** (verificado): Eq.8/9 implementadas en `pipeline/vrptir.py`;
diagnóstico opt‑in en `process_viirs.py:535`; `ENABLE_VRPTIR_AVENI = **False**` en
`mirova_equivalent` (leído de `pipeline.profile`, no del YAML — A89). No existe en
`process_modis.py` ni en `process_viirs_mod.py` (grep = 0): el VRP TIR es **sólo VIIRS I‑band**.

**Citas que no tenemos y valen** — tres son de volcanes nuestros:
- **Candela‑Becerra et al. 2020**, lago cratérico de **Copahue** con ASTER — `10.1016/j.jvolgeores.2019.106752`
- **Aguilera, Caro & Layana 2021**, lagos cratéricos de **Peteroa** 1984–2020 — `10.3389/feart.2021.722056`
- **Trunk & Bernard 2008**, calentamiento de lagos incl. **Copahue** con ASTER — `10.1016/j.jvolgeores.2008.06.020`
- **Aveni et al. 2024** TIRVolcH (detector prerrequisito) — `10.1016/j.rse.2024.114388` *(sí lo tenemos)*
- **Oppenheimer 1993** píxel puro — `10.1016/0377-0273(93)90093-7`; **Wooster et al. 2005** — `10.1029/2005JD006318`
- **Girona, Realmuto & Lundgren 2021**, unrest térmico de gran escala — `10.1038/s41561-021-00705-4` (frente 8)
- **Layana et al. 2020**, VOLCANOMS Chile — `10.3390/rs12101589`
