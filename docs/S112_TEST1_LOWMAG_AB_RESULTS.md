# S112 — A/B Test1-lowmag (magnitud "Muy Bajo" NdC)

> ## ⚠️ DECISIÓN FINAL (2026-06-17): **ADOPTADO** para VIIRS375 (supersede el "NO ADOPTAR" de abajo)
> El veredicto inicial "no adoptar" (criterio de no-inflar-RUTINA) fue **superado** tras dos hallazgos
> de ground-truth pedidos por Nicolás (A62 — el experto insistió y tenía razón):
> 1. **La señal ES real**: Sentinel-2 MSI (20m SWIR) detectó **6 hot pixels en NdC el 16-jun** (mismo
>    día que la ALERTA VIIRS375 0.06); Landsat OLI (30m) 8-9 hot pixels en mayo. El foco incandescente
>    es **sub-píxel** para VIIRS375 (375m) → marca débil 0.06; resuelto en alta-res. NO era ruido.
> 2. **Paridad VIIRS375**: MIROVA cuantifica el 0.06 en VIIRS375 con fondo local; nosotros recortábamos
>    a 0 con el fondo global (valles tibios). El anillo intermedio [2,4]km lo recupera (A/B: 05-14 0.062
>    vs 0.06; 05-02 0.027 vs 0.03).
>
> **ADOPTADO** (mirova_equivalent.yaml, tag pre-s112-intermediate-bg-adoption): `enable_test1_priority_
> weak_cluster` + `enable_test1_intermediate_bg`, gateado per-vol por `lbg_global_compatible` (Lascar/
> NdC/Lastarria). **Trade-off aceptado (Nicolás)**: recall>precisión — aparece en más noches que las
> que MIROVA clasifica ALERTA (correcto para volcán en erupción; marcar "Muy Bajo/baja confianza").
>
> **Frente follow-up (inverso)**: los 1-5 MW de VIIRS750/MODIS al cráter son **artefacto topográfico
> A69** (NTI plano; MIROVA no reporta nada ahí) → suprimir/co-validar (NTI gate). Más valioso que esto.
>
> El análisis de abajo (no-adoptar) se conserva por trazabilidad: era correcto con la evidencia
> disponible ANTES del cruce Sentinel-2/OLI/MSI. La lección de método (A62) está en project_s112_estado.

---

## (Análisis original) A/B Test1-lowmag: VEREDICTO inicial = NO ADOPTAR

**Fecha**: 2026-06-17. **Run A/B**: 27705248529 (54/54 success). **Criterio**: pre-registrado
A66/A10/A62, endurecido tras review adversarial (banda absoluta + cap de outlier + gate de
recall + RUTINA por-pasada). **Fuente de números**: `experiments/_s112_test1_lowmag/audit_t1lm_ab.py`
+ `t1lm_ab_audit.json` (NO transcritos a mano, S91). Todo flag-OFF — **operacional intacto**.

## Pregunta
¿Puede algún brazo de cuantificación reproducir la magnitud de las ALERTAS VIIRS375 de la
reactivación del cráter Nicanor de NdC (MIROVA 0.02–0.06 MW) SIN inflar las noches RUTINA?

## Resultado por brazo (NdC, 3 ALERTAS nocturnas detectables en la ventana A/B)
| Brazo | med err\|log\| | max err\|log\| | n_detect | inflación RUTINA (NdC/Lascar/Lastarria) | gate |
|---|---|---|---|---|---|
| Q0 control / Q2 global | 2.78 | 2.78 | 3 | 4/8/12 = **24** (baseline) | da 0 en ALERTAS |
| Q4 Eq.16 T_e=700/1000 | 2.78 | 2.78 | 3 | 22/24 | da 0 (usa fondo global → clip) |
| Q6 spatial-core | 2.78 | 2.78 | 3 | 22 | da 0 |
| Q5 NTI-local | 2.48 | 2.48 | **1 (FN)** | 23 | pierde detección |
| **Q3 anillo 2-4 km** | **0.05** | 0.05 | 2 | 25/15/14 = **54** | FALLA: recall, **infla** |
| **Q3 anillo 3-5 km** | **0.20** | 0.20 | 3 | 26/12/14 = **52** | FALLA: **infla** |
| **Q3 anillo 1.5-3 km** | **0.05** | 0.10 | 3 | 26/15/13 = **54** | FALLA: **infla** |

**Ningún brazo cumple todos los gates → NO ADOPTAR.**

## Por qué (fenómeno físico)
1. **El fondo global (5–25 km) en NdC es CÁLIDO, no frío** (refuta la predicción pre-registrada
   §7.1 que asumía fondo frío → 0.26): el anillo global baja a terreno de baja altitud (valles
   tibios) → su mediana sube → el exceso MIR del cráter se recorta a ~0. Por eso Q2/Q4/Q6 (todos
   sobre fondo global) dan **0**. Es el gradiente topográfico A69 otra vez (el anillo grande mezcla
   altitudes). Q4 (Eq.16) hereda el mismo fondo global → también 0.
2. **El anillo intermedio (1.5–5 km) está sobre la cumbre nevada FRÍA** → fondo frío → el cráter
   destaca → Q3 reproduce 0.03/0.06 **casi perfecto** (err 0.01–0.2). El lever ES el fondo, como se
   anticipó — pero la dirección fue la inversa a la prevista (global cálido, no frío).
3. **Pero el anillo intermedio NO discrimina**: enciende el cráter a ~0.02–0.085 MW **TODAS las
   noches** (41 de ~45 pasadas), no solo en las 3 ALERTAS. Las pasadas ALERTA y RUTINA son
   **estadísticamente idénticas** en nuestros datos:
   - VRP: ALERTA med 0.037 [0.027–0.062] vs RUTINA-infl med 0.035 [0.010–0.085] — solapan.
   - `nti_max`: ALERTA med −0.943 vs RUTINA med −0.943 (idénticas, cerca del piso −1).
   El `nti_max ≈ −0.94` en TODAS = **sin firma espectral de lava** (MIR≈TIR, ambos fríos). El
   Test1-MIR + anillo intermedio mide el **gradiente crónico cráter-vs-cumbre-fría (A69)**, que es
   ~constante cada noche — no lava fresca.

## Interpretación (clone-literal MIROVA)
El anillo intermedio reproduce las magnitudes ALERTA **por coincidencia de nivel**: sube el piso de
todo el cráter a ~0.05 MW cada noche, y las 3 ALERTAS quedan a ese mismo nivel. No hay discriminador
propio (ni magnitud ni NTI) que separe las 3 noches ALERTA de las ~40 RUTINA. **La señal de la
reactivación temprana está por debajo de la separabilidad de nuestra cuantificación VIIRS375.**
Adoptar Q3 reportaría ~0.05 MW en ~40 noches que MIROVA llama RUTINA → **sobre-reporte sistemático
vs MIROVA** (rompe el clon-literal, MISSION P1; desensibiliza al operador; anti-patrón A55 invertido:
destruiría la diferenciación ALERTA/RUTINA que MIROVA mantiene).

## Conclusión y direcciones
- **NO ADOPTAR ningún brazo.** Flags S112 quedan OFF. Es la salida honesta pre-registrada (§3 design):
  la señal está bajo el piso de separabilidad, no es una calibración fixeable.
- **El review adversarial fue decisivo (A62)**: el criterio endurecido (banda + outlier + recall +
  RUTINA) rechazó Q3 pese a su reproducción de magnitud "perfecta" — sin ese gate, Q3 se habría
  coronado ganador falso (justo los 3 HIGH del review).
- **Lever real (si existe)**: NO es el fondo de la magnitud — es la **contextualidad de la
  detección** (por qué nuestro Test1 dispara ~40 noches y MIROVA flagea 3). Pero el NTI plano
  (−0.94) sugiere que ni siquiera un test contextual NTI separaría → posible límite físico de
  VIIRS375 para esta señal. Frente A69/D11, conocido y duro. No urgente.
- **Reversión**: `lava_lake_magmatic: true` en NdC (volcanoes.yaml) era condicional a que Q4 ganara;
  Q4 perdió → revertir (queda inerte igual, pero no afirmar geología no validada).
- **Parte C** (FN detección 22-mar 0.49 MW, Test1 no disparó): pendiente, frente aparte.

## ¿Es cat-b real (MIROVA sub-reporta) o ruido topográfico? — TRIANGULACIÓN ground-truth (pedido Nicolás)
Tres fuentes independientes convergen en que **NO es señal cat-b recuperable**:
1. **Nuestro pipeline**: pasadas ALERTA y RUTINA idénticas (VRP med 0.037 vs 0.035; `nti_max`
   −0.943 ambas, cerca del piso = sin firma espectral).
2. **OCR MIROVA** (`ocr.csv`): solo 4 detecciones NdC en ~3 meses (06-12 diurna, 03-22, 03-17
   MODIS, 02-11 marcada FALSO_POSITIVO). **Ninguna en las ~40 noches RUTINA de mayo** donde Q3
   infló → MIROVA tampoco ve el cráter activo esas noches.
3. **Campo de radiancia TIF de MIROVA** (`../mirova-tif-archive`, VIIRS375 I04, eje espacial A61):
   exceso local en el cráter (loc_max<1.5km − anillo 2-4km):
   - ALERTA 05-14 05:48 (MIROVA 0.06) → **0.020**.
   - RUTINA 05-15 06:24 → **0.020** (idéntico), 05-18 → 0.017, 05-11/12/13 → 0.006–0.012.
   En el propio producto de MIROVA, la noche ALERTA es **indistinguible** de las RUTINA; una
   RUTINA iguala el exceso de la ALERTA. (Caveat A24: el TIF es campo de visualización, no VRP
   sumable; vale la comparación RELATIVA apples-to-apples, que es robusta.)

**Conclusión reforzada**: el "Muy Bajo" 0.02–0.06 MW de la reactivación temprana NdC está **en el
piso de ruido de VIIRS375** — no separable de noches RUTINA ni siquiera en los datos de MIROVA. Las
3 ALERTAS del consolidado son cruces marginales de umbral (MIROVA tolera ~5% detecciones aleatorias,
Coppola 2023 §2.5 / A76). **NO era un FN recuperable**: nuestro pipeline reportando 0 es tan correcto
como MIROVA. Recuperar la magnitud no rastrearía un evento físicamente distinguible — solo encendería
el cráter cada noche. Cierra el frente de magnitud Muy Bajo NdC con base sólida.
