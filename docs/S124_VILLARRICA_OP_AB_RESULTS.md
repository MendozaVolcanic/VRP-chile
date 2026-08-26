# A/B Villarrica: perfil congelado vs operacional uniforme (issue #513)

**Run**: [32926830945](https://github.com/MendozaVolcanic/VRP-chile/actions/runs/32926830945)
(4 trozos en paralelo, 1 h 48 min) · Ventana **2026-04-01 .. 2026-08-24** ·
Data: `data/_s124_villarrica_op_ab/Villarrica.json` ·
Análisis reproducible: `experiments/_s124_villarrica_op_ab/analyze_ab.py`

> Números generados por script, no transcritos (regla S91). Criterios de cruce
> reusados **verbatim** de `scripts/auto_audit_weekly.py` (que congela el Eje 2
> de AUDIT_S119): CRÁTER = `pc.vrp_mw>0 AND pc.centroid_dist_km<=inner AND
> vrp<=50000` (A10); DASHBOARD = CRÁTER AND `distance_class in {summit, None}`;
> ground truth = loader canónico CONS ∪ OCR (A11).

## Veredicto

El operacional uniforme **mejora Villarrica en magnitud sin costar detección**.
El escalón de junio-agosto es **artefacto del perfil congelado**, no del volcán.

## 1. Recall — idéntico (no se pierde nada)

| serie | sensor | n noches MIROVA | recall cráter | recall dashboard |
|---|---|---|---|---|
| producción (congelado) | VIIRS375 | 24 | 100 % | 100 % |
| **A/B (operacional)** | VIIRS375 | 24 | **100 %** | **100 %** |
| producción (congelado) | VIIRS750 | 6 | 83,3 % | 83,3 % |
| **A/B (operacional)** | VIIRS750 | 6 | **83,3 %** | **83,3 %** |

Volumen publicado por mes prácticamente igual (41-53 noches en ambas series).
Migrar **no apaga** detecciones.

## 2. Magnitud sobre noches PAREADAS — el operacional entra en banda

Comparar medianas mensuales crudas es **inválido**: publicamos ~240 noches y
MIROVA marca 31, así que nuestra mediana la arrastran las noches débiles
sub-umbral que MIROVA no reporta (cat-b, A54). Sobre noches que MIROVA marcó:

| mes | n | MIROVA (MW) | producción | **A/B** |
|---|---|---|---|---|
| 2026-04 | 1 | 0,11 | 1,28× | **1,28×** |
| 2026-05 | 10 | 0,27 | 0,93× | **0,93×** |
| 2026-06 | 4 | 0,43 | 1,01× | **0,75×** |
| 2026-07 | 3 | 0,18 | **22,54×** | **0,80×** |
| 2026-08 | 13 | 0,90 | **2,57×** | **0,60×** |

El A/B está **en banda de paridad [0,5–2,0] los cinco meses**. La producción se
sale en julio y agosto. Global VIIRS750: 4,86× → **0,88×**; VIIRS375: 1,00× → 0,83×.

## 3. Mecanismo — por qué se infla la producción

El discriminante no es la magnitud: es el **NTI**. Ejemplo 2026-08-17 (VIIRS375,
las 4 pasadas de la noche con `nti_max` en el piso ≈ −0,948, o sea **ninguna
evidencia espectral de material caliente**):

| pasada | producción | A/B |
|---|---|---|
| 05:06 SNPP | 43 px, 2,11 MW | 1 px, 0,055 MW |
| 05:24 NOAA20 | 70 px, 3,57 MW | 1 px, 0,048 MW |
| 06:06 NOAA21 | 72 px, 2,63 MW | 1 px, 0,041 MW |

Y la contraprueba, 2026-08-24 05:36, la única pasada de la ventana con
excursión NTI real (`nti_max` = −0,735, muy sobre el piso):

| | producción | A/B | MIROVA |
|---|---|---|---|
| 05:36 NOAA21 | 1 px @ 0,058 km, 3,43 MW | **1 px @ 0,058 km, 1,90 MW** | 2,21 MW |

Es decir: **cuando hay señal espectral genuina las dos series coinciden en el
mismo píxel, sobre el cráter, y el A/B queda más cerca de MIROVA**. Divergen
solo en noches de NTI plano, donde la producción arma cúmulos de 40-70 píxeles.
Cuarenta píxeles de "anomalía" en una noche sin excursión NTI no son lava: son
el gradiente topográfico del cono nevado (cumbre fría, valle tibio de menor
altitud) entrando como si fuera anomalía — el mecanismo A69.

**Causa**: el perfil de producción está congelado en abril y nunca recibió los
supresores que el resto de la flota sí tiene — `enable_test1_contextual_filter`
+ `keep_peak` (ctxpeak, S100, adoptado justamente para curar el anillo nival de
Tupungatito 18,9×) ni `test1_intermediate_bg_ring_km: [1.5, 3.0]` (S112).
Corre el Test 1 sobre el ROI completo [5, 25] km sin filtro contextual.

## 4. Lo que queda abierto (no bloquea, pero hay que decirlo)

- **2026-08-17**: MIROVA reporta 1,86 MW y el A/B lee 0,06. Las 4 pasadas de esa
  noche tienen `nti_max` en el piso. No se puede decidir con estos datos si
  MIROVA ve algo real que perdemos o si su número viene del mismo mecanismo
  topográfico que la producción reproduce. **1 noche de 31.**
- **2026-05-29 MODIS** (MIROVA 1,83): la pierden **ambas** series. Es previo e
  independiente de esta decisión.
- El A/B lee sistemáticamente **algo bajo** en agosto (0,60×): dentro de banda,
  pero en el borde inferior.
- La posición del píxel del A/B en noches de NTI plano cae a ~2,7-3,0 km del
  cráter (no al cráter). Es el residuo irreducible A84 — cosmético, siguen
  clasificadas *summit*.

## 5. Qué NO hace este documento

**No flipea nada.** Tocar el cron de Villarrica es A45: requiere tag defensivo
y confirmación explícita de Nicolás. Esto es la evidencia para esa decisión.
