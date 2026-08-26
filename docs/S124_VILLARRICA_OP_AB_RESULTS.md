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

---

# ADENDA (misma sesión) — corrección de método y cierre del 08-17

Nicolás preguntó qué causaba el 08-17 y si la comparación cubría todos los
volcanes y los 3 sensores. Las dos preguntas destaparon un **defecto de mi
cruce**, no del pipeline.

## A. El 08-17 y el 29-05 NO eran detecciones perdidas: eran pasadas DIURNAS

La ALERTA de MIROVA que reporté como perdida es de las **19:06 UTC** con el sol
a **+27,8°** sobre el horizonte (verificado con `pipeline.store._solar_elevation`,
la misma función del pipeline). Nuestro sistema es **nocturno por diseño**: de día
la reflexión solar contamina la banda MIR de 3,7-4 µm y el NTI deja de significar
lo que creemos. No hay nada que detectar ahí — y el **mismo 1,86 MW con la misma
distancia 0,84 km** reaparece esa noche (08-18 05:48, sol −60,9°), donde el A/B
lee 1,00 MW. Es la misma detección publicada dos veces por MIROVA.

Igual el 29-05 MODIS (19:55 UTC, sol **+15,1°**). Las 5 ALERTAS diurnas de
Villarrica en la ventana:

| fecha UTC | sensor | VRP | elev. solar |
|---|---|---|---|
| 2026-05-29 19:55 | MODIS | 1,83 | +15,1° |
| 2026-06-03 19:06 | VIIRS375 | 0,39 | +20,5° |
| 2026-08-17 19:06 | VIIRS375 | 1,86 | +27,8° |
| 2026-08-21 18:54 | VIIRS375 | 1,56 | +30,3° |
| 2026-08-22 18:36 | VIIRS375 | 0,53 | +32,5° |

Mi cruce binaba por fecha UTC y metía esas pasadas diurnas en el denominador,
penalizándonos por no ver lo que decidimos no mirar. Esto es lo mismo que ya
documenta **A76** (MIROVA publica artefactos solares diurnos en su producto
per-volcán) llegando por otra puerta: el CSV consolidado.

## B. Con referencia NOCTURNA: un solo FN en toda la ventana

| serie | sensor | n | recall | ratio |
|---|---|---|---|---|
| producción (congelada) | VIIRS375 | 21 | 100 % | 0,99× |
| **A/B (uniforme)** | VIIRS375 | 21 | **100 %** | **0,86×** |
| producción (congelada) | VIIRS750 | 6 | 83,3 % | **4,86×** |
| **A/B (uniforme)** | VIIRS750 | 6 | **83,3 %** | **0,88×** |

**Único FN real de la ventana**: 2026-08-13 VIIRS750, MIROVA 0,41 MW — lo pierden
**las dos** series. No es regresión del flip.

## C. Los otros 10 ya corren el algoritmo destino

`nrt.yml:158` corre `mirova_equivalent` para los 10; `nrt.yml:184-196` corre
`mirova_equivalent_villarrica_test1` **solo** para Villarrica. No hay A/B que
hacer para los demás: el flip mueve a Villarrica hacia lo que la flota ya usa.
Paridad de la flota en la misma ventana, referencia nocturna:

- **VIIRS375** (n=584): recall 95-100 % casi en todos. Ratios 0,36-1,29. El A/B
  de Villarrica (0,86×) queda **en familia** con Lascar 0,53 / Isluga 0,55 /
  Tupungatito 0,71 / PCC 0,76 / PP 0,89 / Chaitén 1,22.
- **VIIRS750**: sensor sistemáticamente más débil en toda la flota — Isluga 2,26,
  PP 6,78, Tupungatito 7,48 fuera de banda. El A/B de Villarrica (0,88×) sería
  **de los mejores de la flota**; la serie congelada (4,86×) está entre los peores.
- **MODIS**: **no hay evidencia para Villarrica**. Cero ALERTAS nocturnas MODIS
  en la ventana (la única, 29-05, era diurna). El único volcán con MODIS nocturno
  es Láscar (n=42, recall 14,3 % — el frente D12 abierto, ajeno a esta decisión).

## D. MODIS de Villarrica: sin ground truth, pero el comportamiento espacial decide

Sin referencia MIROVA se compara el comportamiento de los dos brazos. Las
detecciones MODIS más fuertes del perfil congelado están **fuera del edificio**:

| fecha | producción | A/B |
|---|---|---|
| 2026-06-17 06:55 | 89,8 MW @ **7,1 km** (4 px) | 4,2 MW @ **1,35 km** (7 px) |
| 2026-07-12 21:35 | 52,7 MW @ **10,0 km** (4 px) | 3,0 MW @ **3,29 km** (13 px) |
| 2026-06-29 02:50 | 45,6 MW @ **17,9 km** (3 px) | 0,3 MW @ **1,28 km** (1 px) |
| 2026-06-21 21:25 | 43,1 MW @ **22,8 km** (3 px) | 4,8 MW @ **1,73 km** (14 px) |

Máximo summit intra-5 km: producción **28,8 MW**, A/B **5,0 MW** (el máximo que
MIROVA reportó en toda la ventana fue 2,21 MW). El uniforme ancla al edificio;
el congelado se va al campo lejano. Es el patrón far→summit de **A46/A82**.

## E. Hallazgo colateral: la auditoría semanal automática no filtra el sol

`scripts/auto_audit_weekly.py` cruza contra CONS ∪ OCR **sin filtrar elevación
solar**, así que arrastra el mismo defecto. En la flota son **82 de 1338 ALERTAS
(6,1 %)** diurnas en la ventana; por volcán llega a 20 % (NdC) y 17,5 %
(Lastarria). Impacto medido sobre la ventana rodante real de 60 días:

| sensor | hoy | con filtro nocturno | banda |
|---|---|---|---|
| VIIRS375 | 95,7 % | 96,1 % | ≥93,4 |
| VIIRS750 | 82,6 % | 84,1 % | ≥79,5 |

**No da vuelta ningún veredicto hoy**, pero come ~1,5 pp de margen — y VIIRS750
sólo tiene 3,1 pp de holgura sobre su banda. Es deuda latente: el día que se
estreche, abre un issue por un problema que no existe. Fix barato y correcto.
