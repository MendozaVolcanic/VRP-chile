# Auditoría S124 — ¿estamos replicando bien a MIROVA, o faltan pruebas?

> Pregunta de Nicolás, 2026-08-26, a mitad de sesión. Todos los números salen de
> scripts reproducibles (regla S91); ninguno está transcrito a mano. Read-only:
> esta auditoría no tocó pipeline ni datos.

## Respuesta corta

**Replicamos bien la parte radiométrica y la lógica de detección. Nos falta una
pieza estructural: la grilla.** Está diagnosticada, documentada con citas
verbatim y aprobada por vos como frente mayor (F70, 25-ago). La fase 1 está
mergeada. Las fases 2 a 5 —que incluyen precisamente las pruebas que faltan— no
están hechas.

Y hay un hallazgo incómodo sobre mi trabajo de hoy: **el A/B que lancé esta
sesión es el brazo C de ese diseño**, el que el propio diseño predice que va a
fallar.

---

## 1. Lo que sí está verificado

| pieza del algoritmo | evidencia | estado |
|---|---|---|
| Coeficientes Wooster por sensor | calibrados S14 contra OSF v2.5, error ≤0,17 % en 48.360 filas; `test_coefficients.py` los clava | ✅ |
| Área de píxel nadir-fija | A66/A67, adoptada S102-S103; VIIRS375 pasó de 2,27× a 0,78× | ✅ |
| Detección MODIS vs Coppola 2016a | auditoría de fidelidad file:line S114: dual-ROI 5σ/10σ, Tests 2∧3 con rama OR, second-run, ETI cuadrático, kernel 8-vec aritmético | ✅ fiel |
| Cruce pixel-level contra MIROVA real | `test_r2_pixel_level.py` — **corre de verdad**, 9 pasados contra los TIF de `../mirova-tif-archive` | ✅ |
| Suite completa | **889 tests pasan** | ✅ |

Esto importa decirlo: la sospecha razonable era que el test de ground truth fuera
cobertura fantasma (se auto-saltea si el archivo de TIF no está). Lo corrí: el
archivo está y los 9 casos cruzan.

## 2. La pieza que falta — la grilla UTM

**El fenómeno.** Un píxel de satélite no es un cuadrado fijo. Lejos del nadir se
estira hasta ~10 km² en MODIS. Cuando el algoritmo pregunta *"¿este píxel está más
caliente que sus ocho vecinos?"*, la respuesta depende de la **geometría** de esos
vecinos tanto como de su temperatura. Sobre un volcán con glaciar, un vecino
elongado promedia hielo, roca y valle en proporciones distintas en cada pasada:
el fondo que se le resta al foco es un objeto diferente cada noche.

**Qué hace MIROVA.** Lo elimina *antes* de detectar. Coppola 2016a (`sp426_5.txt`
~L162): *"we cropped and resampled (into an equally spaced 1 km grid) the MODIS
Level 1B data"*, y la razón explícita ~L150-160: el esquema *"requires homogenous
pixel scale"*. Campus 2024 confirma lo mismo para VIIRS 375m.

**Qué hacemos nosotros.** Computamos sobre el swath crudo.

**Estado real, verificado con git:** `pipeline/regrid.py` existe, tiene tests
propios que pasan, y su docstring explica todo esto. Pero **nadie lo llama**: cero
referencias en el resto de `pipeline/`, cero flag en el perfil. No es un olvido —
es el plan por fases funcionando como corresponde (F70.1 entrega el módulo, F70.2
lo cablea). Lo señalo porque un lector que vea el módulo mergeado podría creer que
la grilla ya está operando, y no lo está.

## 3. Por qué esto conecta con lo que encontré hoy

El déficit que destapó la banda de paridad corregida es **bimodal**: en régimen
débil (1-2 píxeles) sub-integramos 0,4-0,7×; en campo difuso (6+ píxeles)
sobre-integramos 12× a 99×. Los dos modos son consistentes con un fondo mal
medido — y el fondo es exactamente lo que la geometría del vecindario decide.

Mi hipótesis independiente de hoy (el fondo del VRP: kernel de vecinos vs anillo
de 5-25 km) **converge con el diagnóstico del diseño F70**, que ya lo había
identificado y además nombró la pieza que a mí me faltaba: la polaridad de
`local_kernel_bg` está invertida —lo tenemos como excepción per-volcán (5 de 11)
cuando en Coppola Eq. 6 es la regla universal— y la razón por la que en S62 el
kernel global no se pudo adoptar (rompía Tupungatito, A19) puede ser justamente
que lo aplicamos **sobre swath**.

## 4. El error de método que cometí hoy

Lancé un A/B (`_s124_kernelbg_ab`, run 33006952492) sin revisar si el experimento
ya estaba diseñado. Lo estaba. Comparando contra la tabla del §5 de F70:

| brazo del diseño | grilla | kernel-bg | qué contesta |
|---|---|---|---|
| control | OFF | per-volcán | baseline |
| A | ON | per-volcán | ¿la grilla sola mejora? |
| **B** | **ON** | **global** | **la hipótesis central** |
| C | OFF | global | aísla el kernel — *"réplica del fallo S62"* |

**Mi A/B es el brazo C**, sobre 6 de los 11 volcanes. Es el brazo que el diseño
espera que **falle**, y no puede ver la hipótesis central porque el brazo B
necesita F70.2, que no está construido.

Esto es la trampa A50 en su forma pura: la respuesta estaba en el repo. Lo
rescatable es que la convergencia independiente refuerza el diagnóstico, y que el
brazo C es un control que el diseño igual necesita.

## 5. Tres afirmaciones mías de esta sesión que resultaron falsas

Las dejo escritas porque el valor de una auditoría está en lo que corrige, no en
lo que confirma.

1. **"MIROVA integra un halo que nosotros perdemos"** — refutado con el dataset de
   Campus 2024 (Vulcano): el Npix mediano de MIROVA es **1**, y el 54 % de sus
   alertas son de un solo píxel.
2. **"El apagón de julio en NdC fue ceguera por nube"** — falso. Julio tuvo **más**
   detecciones summit (68) que cualquier mes, con mediana y máximo sin cambio,
   pese al 46 % de pasadas con más de medio ROI tapado.
3. **"La cerca del frontend apaga el 7 % de los records"** — el número real es
   **31 %** (10.773 de 34.763, 17.678 MW), y la condición que yo creía que
   filtraba (el radio) es un **no-op**.

De la #2 salió además una decisión de **no** construir: la banda de observabilidad
que iba a agregar no tiene caso. De 20 huecos de ≥5 días sin detección en los 11
Tier A, **solo 1 es ciego**; a 7 días, **0 de 12**. La nube no tapa un ROI entero
por una semana; la calma volcánica sí dura eso.

## 6. Pruebas que faltan (respuesta directa a la pregunta)

**Especificadas y no hechas** — son las fases pendientes de F70:

- **F70.2**: cablear el regrid en los 3 procesadores tras flag OFF, con tests de
  integración (granule sintético; en el caso nadir trivial las detecciones deben
  ser idénticas) y medición de costo por granule.
- **F70.3**: el A/B de 4 brazos sobre los 11 Tier A, no 6.
- **F70.4**: veredicto contra los criterios **ya pre-registrados** — Tupungatito es
  el juez (B debe curarlo donde C debe romperlo); Lastarria no debe romperse;
  paridad global ≥ control; offset espacial ≤ control (A61); y verificar eventos
  concretos, no solo agregados (A79).

**No especificadas, y las agrego como hallazgo:**

- **La suite local no compila.** `tests/test_regrid_modis_f70.py` (sin commitear)
  importa `_regrid_modis_granule` de `process_modis`, función que **no existe** —
  la real es `regrid_to_utm` en `pipeline/regrid.py`. Rompe la colección entera:
  sin ignorarlo, `pytest tests/` da 0 tests. CI no lo ve porque el archivo nunca se
  pusheó. Es un test rojo de TDD escrito para F70.2, que quedó adelantado a su
  implementación.
- **No hay test que falle si el regrid se desconecta.** Cuando F70.2 entre, hace
  falta un invariante que garantice que el perfil operacional usa el sustrato que
  dice usar (mismo espíritu que el test de regresión de A63).

## 7. Veredicto

No estamos replicando mal por error ni por parches: la radiometría está calibrada
contra los datos propios de MIROVA, la lógica de detección MODIS fue auditada
línea por línea contra el paper, y el cruce pixel-level contra los TIF reales
corre y pasa. Lo que falta es **una divergencia estructural única, ya
identificada, con diseño aprobado y criterios de éxito escritos antes de correr el
experimento**.

La pregunta abierta no es *"¿qué más nos falta descubrir?"* sino *"¿construimos
F70.2 para poder correr el brazo que importa?"*.
