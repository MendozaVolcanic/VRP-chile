# Mannini et al. 2019 (GRL) — presupuesto de calor de un campo fumarólico

**Cita**: Mannini, S., Harris, A.J.L., Jessop, D.E., Chevrel, M.O., & Ramsey, M.S. (2019).
*Combining Ground- and ASTER-Based Thermal Measurements to Constrain Fumarole Field Heat Budgets:
The Case of Vulcano Fossa 2000–2019*. **GRL 46, 11,868–11,877**.
[10.1029/2019GL084013](https://doi.org/10.1029/2019GL084013)

**Afiliación (A9) — NO es canon MIROVA.** Portada p. 11,868: Univ. Clermont Auvergne / LMV + Univ.
of Pittsburgh (Ramsey); escuela Harris/Clermont. **Pero el canon lo adoptó**: Campus, Aveni, Laiolo,
Massimetti & Coppola (2024, *Bull Volcanol* 86:25, `documentacion/s00445-024-01721-z.pdf`) construye
su marco de Vulcano sobre él. Ese paper —canon puro, y el que `pipeline/process_viirs.py:74` cita
para `WOOSTER_COEFF = 18.0`— es el puente que vuelve a Mannini vinculante para nosotros.

---

## 1. Qué mide y con qué fórmula

Mide el **presupuesto de calor total** de un campo fumarólico: `φ_tot = φ_diffuse + φ_vent`. Cada
término es **radiativo + convectivo**, no sólo radiativo.

> ⚠️ **El PDF no contiene ninguna ecuación numerada.** El modelo vive en el *Supporting Information
> Text S1*, que **no tenemos**: «Using these values in equations (S3) and (S4) (supporting
> information Text S1)» (p. 11,872). Atribuirle «la ecuación de Mannini 2019» es infundado.

Explícito sí queda: `ΔT = T_diffuse − T_ambient` (p. 11,870), `h_c` medido en terreno =
**24 W·m⁻²·K⁻¹** (p. 11,872; Matsushima 2003 daba 35 en Iwodake) y el balance de Sekioka & Yuhara
(1974).

| Magnitud (p. 11,872 salvo indicación) | valor |
|---|---|
| ΔT difuso (ASTER B14, 10,95–11,65 µm) | **4 °C** (24 vs 20 °C); rango 2–7 °C |
| φ_diffuse | 4–13 MW, **media 9 ± 2 MW** |
| φ_vent | 0,35–0,96 MW, **media 0,65 MW** |
| Área difusa | **63.900 m²** (Chiodini 2005: 415.000 m² y 21 MW en 1998) |
| Área de bocas | **43–147 m²**; boca individual 0,06–0,13 m² |
| T de bocas | 80–350 °C (media por campaña 139–206 °C) |
| Densidad de flujo | **140 MW/km²** → 14° del mundo (p. 11,874) |

## 2. ⭐ Núcleo diminuto, cola enorme, y la cola manda

> «although the temperature at fumarole vents is much higher than over heated surfaces, the heat
> flux from the diffuse area, which is 640 times greater in magnitude, dominates the heat budget»
> (p. 11,872)

> «φ_diffuse representing on average **93 ± 2% (1σ)** of the total heat flux» (p. 11,872)

La geometría: ~**100 m²** de bocas calientes (150–350 °C) embebidas en ~**64.000 m²** de suelo
apenas tibio (+4 K). El foco discreto aporta el **7%**: un método que aísle «el clúster» se queda
con menos de una décima parte de la energía.

Esto explica el salto de Lastarria en S129 (0,575 → 0,844 al sumar píxeles próximos). Lastarria es
el campo fumarólico Lazufre, y `volcanoes.yaml:618-620` ya lo describe sin saberlo: *«fumarolas
intensas permanentes → ring 1-3km contaminado por calor fumarólico crónico»*. Ese «contaminante»
**es la señal**: la zona difusa de Mannini, con el 93% del calor.

## 3. Cómo separan la señal del fondo — y en qué nos contradice

> «the temperature of each anomalous pixel was used for T_diffuse and, following Lee and Tag
> (1990), **the coldest value from the nearest nonanomalous pixels** to each hot pixel for
> T_ambient» (p. 11,871)

**Contradice nuestro frente 2 (fondo autorreferente, S126).** Mannini toma el **mínimo de los
vecinos NO anómalos**; nosotros, la **media aritmética de los 8 vecinos**, anómalos incluidos. Su
elección es inmune por construcción al problema de S126: el píxel caliente no entra en su propio
fondo, y los vecinos parcialmente calentados quedan excluidos *antes* de tomar el mínimo. Hay
precedente documental para desautorreferenciar el fondo, y está acá.

**Lo que NO hacen**: **no corrigen topografía, altitud ni estacionalidad** en el ΔT. Declaran el
problema sólo para `h_c`, que «will vary with climatic zone, altitude, time of day, season, and
meteorological conditions» (p. 11,874). Se lo permiten porque Vulcano es una isla de 391 m sin
relieve. En un nevado andino de 5.700 m ese supuesto no existe: **A69 es un problema que este paper
nunca enfrentó**.

**Incertidumbre declarada**: «uncertainty on the convective heat transfer coefficient, and hence
overall heat flux, will be around 30%» (p. 11,875) — coincide con el ±30% de Wooster/Laiolo.

## 4. Resolución: el campo entero es sub-píxel para nosotros

ASTER = 90 m (píxel 8.100 m²). El campo difuso (63.900 m²) ocupa ~8 píxeles; usan una caja de
**5×5 píxeles (450 × 450 m)** sobre el cráter (p. 11,871): está **resuelto**. Límite declarado:
«Given the NEΔT of ASTER of 0.3 °C, **a pixel-filling heated surface will need to be elevated by at
least 0.5 °C** above its background to be detected» (p. 11,874). Ojo al *pixel-filling*: a 375 m el
campo llena `f = 0,454` del píxel; a 1 km, `f = 0,064`.

**Cálculo propio** (no del paper: Planck + mezcla lineal de radiancia, ε = 0,95, fondo 293,15 K,
difuso 297,15 K, sobre las áreas de Mannini):

| sensor | llenado | ΔL_MIR | **VRP que le asignaríamos** | ΔNTI |
|---|---|---|---|---|
| VIIRS I4 375 m | 0,454 | 0,027 | **0,069 MW** | 0,0042 |
| MODIS B21 1 km | 0,064 | 0,006 | **0,105 MW** | 0,0008 |

Contra `pipeline/profiles/mirova_equivalent.yaml:98-99` (`c1_summit: 0.003`, `c1_scene: 0.010`): el
campo **sólo cruza el umbral summit en VIIRS 375 m**; en MODIS no cruza ninguno.

**El resultado que reencuadra A69/A82/A83**: un campo fumarólico **real, validado en terreno, 14°
del mundo en intensidad, con 9 MW de calor**, entraría a nuestro pipeline como **~0,07 MW** —
dentro del rango 0,04–0,06 MW que hoy llamamos «artefacto topográfico», y justo en el piso de
0,1 MW que estamos por decidir. No es que el artefacto se parezca a la señal: **la señal real de un
campo difuso vive en ese mismo rango**. Un piso de 0,1 MW borraría a Lazufre entero.

## 5. ⭐ ¿Aplica el método MIR de Wooster? Mannini no opina; el canon sí, y dice que no

Mannini **jamás menciona** MIR, Wooster, MODIS, VIIRS, VRP ni sub-píxel (grep sobre el texto
extraído: cero ocurrencias). Usa **sólo TIR** (11 µm) más convección. Atribuirle una posición sobre
el método MIR sería inventarla.

Quien sí la fija es **Campus/Aveni/Laiolo/Massimetti/Coppola 2024** (canon MIROVA), citando a
Mannini, p. 4 de 7:

> «Hydrothermal systems are commonly characterised by temperatures below this range [600–1500 K].
> However, Coppola et al. (2022) proved that even in a fumarolic field such as that of Vulcano,
> featuring at least a component exceeding or approximating 600 K […] the method works as a proxy of
> the flux radiated **exclusively by this hottest component** […] **omitting the contribution from
> the diffuse volcanogenic heat flux over the whole area (i.e. the DFZ)**»

Traducido: el método MIR **no mide el campo fumarólico**. Mide sólo la componente más caliente y
**omite por diseño el 93% de la energía**. No es un sesgo a calibrar: es el alcance declarado del
instrumento. El canon admite que el régimen hidrotermal está **por debajo** del rango de validez de
Wooster, y que el método se salva únicamente porque existe alguna boca cerca de 600 K.

**La cota independiente pedida** (pregunta 3), cruzando ambos papers sobre el mismo volcán: Campus
2024 reporta VRP MIROVA VIIRS375 de **0,02–1,11 MW, media ~0,2 MW** (base 0,32 MW), mientras el
calor del mismo campo era **5–14 MW** (Mannini) y llegó a **80–120 MW** en la crisis 2021–22. El VRP
MIR captura entre **1/25 y 1/600** del calor real. Para Lastarria y Peteroa, nuestra «paridad con
MIROVA» no es paridad con el volcán: ambos medimos la misma esquirla.

*(Verificado S129 con `pypdf` sobre ambos PDF; los cálculos de la §4 son reproducibles con las
constantes citadas.)*

## 6. Qué cita que no tenemos (ninguno está en `documentacion/`)

| Referencia | Por qué la queremos |
|---|---|
| **Harris (2013)**, *Thermal remote sensing of active volcanoes: A user's manual*, CUP | el modelo conceptual (Text S1) sale de acá |
| **Sekioka & Yuhara (1974)**, JGR 79(14), 2053–2058, [10.1029/JB079i014p02053](https://doi.org/10.1029/JB079i014p02053) | el balance de superficie que da `h_c` |
| **Oppenheimer, Rothery & Francis (1993)**, JVGR 55(1), 97–115, [10.1016/0377-0273(93)90092-6](https://doi.org/10.1016/0377-0273(93)90092-6) | *distribuciones térmicas en campos fumarólicos para teledetección IR* |
| **Lee & Tag (1990)**, BAMS 71(12), 1722–1730, [10.1175/1520-0477(1990)071<1722:IDOHUT>2.0.CO;2](https://doi.org/10.1175/1520-0477(1990)071<1722:IDOHUT>2.0.CO;2) | origen del fondo «vecino no anómalo más frío» (frente 2) |
| **Chiodini et al. (2005)**, JGR 110, B08204, [10.1029/2004JB003542](https://doi.org/10.1029/2004JB003542) | inventario de calor difuso de referencia |
| **Harvey et al. (2015)**, JVGR 302, 225–236 | densidad de flujo de 20 sistemas hidrotermales |
| **Wright (2002)** | **no lo citan**: el frente 5 sigue sin fuente primaria del NTI |

## 7. Qué NO dice, contra lo que se le atribuye

1. **No tiene ecuaciones** (están en el SI, ausente). No citarlo como fuente de fórmula.
2. **Nada sobre MIR, MODIS/VIIRS ni sub-píxel**: cero menciones en el texto completo.
3. **No corrige topografía ni estacionalidad** — sólo lista el problema como pendiente.
4. **No mide flujo de fluidos**: «currently unavailable for Vulcano» (p. 11,875).
5. **Inconsistencia interna sin resolver**: la p. 11,872 da la densidad de flujo difuso como «0.55
   to 1.57 kW/m²», pero 9 MW sobre 63.900 m² dan **0,14 kW/m²**, y es este último el que reproduce
   el «140 MW/km²» de la p. 11,874 y el reparto 93/7. Los 0,55–1,57 kW/m² **no cuadran con ningún
   otro número del paper**. No usar esa cifra.
6. **No es MIROVA**: es un balance de calor total. Nuestro pipeline **no tiene término convectivo**
   — verificado: `grep -rn -iE "convect|h_c|heat_transfer" pipeline/` devuelve **cero**. Medimos el
   15–19% de un fenómeno cuyo ~85% se va por convección (Campus 2024 p. 1, resumiendo a Mannini).
