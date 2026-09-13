# Auditoría S138, eje 3: verificador limpio de los instrumentos de S137

Fecha: 2026-09-13. Rama `main` en `6b1dd91ef`. Contexto limpio: no leí los `RESULTADO_*.md`,
`COMPARACION_8_BRAZOS.txt`, `EL_*.md`, el bloque de arranque S138 ni las secciones D21/D22 del
catálogo. Todo lo que afirmo sale de un `archivo:línea` que leí o de un script mío en
`experiments/_s138_audit/eje3/` (rutas absolutas bajo
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\`).

Lo que NO pude re-correr: los tres instrumentos que procesan granules (1, 2, 3) necesitan HDF4 y
pyhdf no existe en Windows; los granules de `/tmp/{sigma137,etapa137,apendice}` no están en disco.
Para ellos verifiqué por lectura del código y sobre las salidas commiteadas, y lo digo en cada caso.

Scripts míos (todos read-only sobre el repo):

| script | qué hace |
|---|---|
| `experiments/_s138_audit/eje3/control_comparador.py` | control 9/9, 0/9, 9 indeterminados y directorio ausente del comparador |
| `experiments/_s138_audit/eje3/control_evaluar_caso.py` | `evaluar_caso` real con pasadas sintéticas: 4 km, 6 km, borde 5,0/5,001, VRP 0,0, banda NTI, post hoc A2 |
| `experiments/_s138_audit/eje3/marcador_predicado_dashboard.py` | los 8 brazos re-puntuados con el predicado que usa el dashboard (`summit`) |
| `experiments/_s138_audit/eje3/medir_figuras_apendice_copia.py` | copia del instrumento 4 con la salida en `out_figuras_rerun/` (re-corrida idéntica) |
| `experiments/_s138_audit/eje3/medir_figuras_nativo.py` | instrumento 4 sobre el PNG nativo del PDF, marcas automáticas, controles C1 a C5, panel negativo A7, posición de la alerta |

---

## 1. Los cinco instrumentos

### Instrumento 1: `experiments/_s137/sigma_dnti_4brazos.py`

**Qué calcula de verdad.** Por granule MODIS nocturno (Láscar y Villarrica, 20 días hasta
2026-08-31) llama a `pm.calculate_vrp` cuatro veces reasignando en el namespace de
`pipeline.process_modis` los flags `ENABLE_MODIS_B22_PRIMARY` y `ENABLE_UTM_REGRID`
(l. 89-91), y guarda del record `diag_sd_dnti`, `diag_mu_dnti`, `diag_n_first_pass_pixels`
(l. 109-117). Esos campos salen de `fp_diag` (`pipeline/process_modis.py:1526-1535`), que es lo
que devuelve `first_pass_tests_2_and_3`: `sd_dnti = np.std(dnti[bg_mask])`
(`pipeline/detection_context.py:493`) sobre el pool "suitable" (l. 477: sin bordes, sin dNTI o
dETI < −0,1), y `n_first_pass_pixels = sum(hot)` (l. 536) donde `hot` (l. 528-533) es
`pass_2 & pass_3 & (bt > t_bg + bt_sanity_k)`.

**Pregunta 1 (si el fenómeno estuviera roto, lo vería).** Sí para el sigma: los dos flags se
leen como globales del módulo en el momento de la llamada (`process_modis.py:502, 544, 548,
561`), y no hay otro módulo que los consuma (`grep -rn ENABLE_MODIS_B22_PRIMARY pipeline/` da
sólo `process_modis.py`; `ENABLE_UTM_REGRID` aparece también en `process_viirs*.py`, que acá no
corren). El parche llega al punto de uso (A89).

**Pregunta 2 (si el instrumento estuviera muerto, se vería distinto).** Sí: un brazo sin record
da `None` y se salta (l. 107-108, 210-211); el JSON tiene 84 filas con los 4 brazos y
`sd_dnti` nunca `None` (verificado: `none_sd=0` en los 8 grupos). Un flag que no llegara al punto
de uso habría dado los 4 brazos iguales; dan distintos.

**Caminos de error que encontré.**

1. **`n_first_pass` no cuenta "píxeles que pasan Tests 2 y 3": cuenta Tests 2 y 3 Y la compuerta
   `bt > t_bg + 3 K`** (`detection_context.py:528-533`). El título de (b) dice lo primero. Ver
   afirmación (b) y hallazgo H2.
2. **El sigma es una desviación estándar ordinaria; el instrumento 4 mide en las figuras con
   estimadores robustos sobre un campo recortado a la escala de color.** Comparar los dos es
   comparar estimadores distintos. Ver (a).
3. **Estimador del resumen.** `resumen()` toma mediana por brazo y divide medianas
   (`base_sd / sd`, l. 139-153). La mediana de los cocientes por par da otro número (abajo).
   El informe que se lea tiene que decir cuál usó.
4. `local_kernel_bg_compatible=False` fijo (l. 99): no afecta al sigma (es de magnitud), pero el
   `vrp_pc_mw` que guarda el JSON NO es el de producción para Villarrica (ver H1).

**Re-cómputo sobre el JSON commiteado** (`experiments/_s137/out_sigma/sigma_dnti_4brazos.json`,
84 granules nocturnos: Láscar 40, Villarrica 44; ventana 2026-08-12 02:00 a 2026-08-31 08:35 UTC):

```
Lascar  n=40   base med_sd=0.00790  b22 0.00169  regrid 0.00894  ambos 0.00192
Villarrica n=44 base med_sd=0.00705  b22 0.00203  regrid 0.00812  ambos 0.00235
med(base)/med(b22):  Lascar 4.69   Villarrica 3.48     (mediana de cocientes por par: 4.12 / 3.33)
med(regrid)/med(base): Lascar 1.132  Villarrica 1.152   (mediana por par: 1.159 / 1.087)
n_first_pass == 0:  base 1/84   b22 80/84   regrid 1/84   ambos 81/84
```

### Instrumento 2: `experiments/_s136/conformidad_apendice.py` (`evaluar_caso`, 8 brazos)

**Qué calcula de verdad.** Por caso del Apéndice A, todas las pasadas MODIS nocturnas de esa
fecha con `calculate_vrp` (radio 25 km, `inner_radius_km=5` uniforme, `vent = lat/lon` del
catálogo, `local_kernel_bg_compatible=FONDO_LOCAL`, l. 109-116). `evaluar_caso` (l. 143-171):
si el caso trae `nti_paper`, filtra las pasadas a `|diag_nti_max − nti_paper| ≤ 0,06` (si
ninguna queda: INDETERMINADO); "publica" = `vrp_pc_mw > 0` y centroide del cúmulo a ≤ 5 km
(l. 158-160). Positivo CONFORME si alguna pasada publica; negativo CONFORME si ninguna.

**Pregunta 1.** Con pasadas sintéticas (`control_evaluar_caso.py`, función real importada):

```
positivo, cumulo 0,5 MW a 4 km      -> CONFORME
positivo, cumulo 0,5 MW a 6 km      -> NO CONFORME (falso negativo)
positivo, 5,0 km (borde) / 5,001 km -> CONFORME / NO CONFORME
negativo, 4 km / 6 km               -> NO CONFORME (falso positivo) / CONFORME
positivo, cumulo VRP 0,0 a 0,8 km   -> NO CONFORME (falso negativo)
positivo, sin cluster / sin pasadas -> NO CONFORME (FN) / INDETERMINADO
nti_paper -0,93 y pasada con -0,80  -> INDETERMINADO
post hoc A2: cumulo a 2,9 km del punto del autor -> CONFORME; a 3,1 km -> NO CONFORME
```
El veredicto cambia con INNER_KM = 5 exactamente donde debe.

**Pregunta 2.** Sin pasadas da INDETERMINADO, no CONFORME: un instrumento muerto no fabrica
conformidad. Ninguno de los 8 brazos commiteados tiene indeterminados.

**Caminos de error que encontré.**

1. **"Publica" no es lo que ve el operador.** El dashboard devuelve 0 para cualquier record cuyo
   `distance_class` no sea `summit` (`frontend/index.html:1056`) y para centroide fuera del inner
   (l. 1060); `isValidDetection` (l. 1466-1470) exige `vrp_mw > 0` o `triggered_test1`. La
   batería no mira `distance_class`. Con el flag de producción
   `ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER=False`, la etiqueta sale del `final_hotspot`
   (máximo de MIR absoluta de la escena, `process_modis.py:294-314`), no del cúmulo. Re-puntuado
   con el predicado del dashboard (`marcador_predicado_dashboard.py`, mismos JSON):

   ```
   brazo                                        bateria     dashboard   casos que cambian
   _s136/out_apendice (B21 min, "produccion")   6/6  0/3    2/6  2/3    A1 A2 A5 A6 (pos: pub->no), A7 A9 (neg: pub->no)
   _s136/out_apendice_prosa                     2/6  3/3    2/6  3/3
   _s137/out_apendice_b22                       4/6  2/3    4/6  2/3
   _s137/out_apendice_b22_prosa                 4/6  3/3    4/6  3/3
   _s137/out_apendice_b22_sincompuerta          4/6  2/3    4/6  2/3
   _s137/out_apendice_b22_sincompuerta_prosa    4/6  3/3    4/6  3/3
   _s137/..._sincompuerta_fondolocal            6/6  2/3    5/6  3/3    A2 (pos), A4 (neg)
   _s137/..._sincompuerta_fondolocal_prosa      5/6  3/3    5/6  3/3
   ```
   En el brazo "producción", 19 de las 22 pasadas que la batería cuenta como publicadas llevan
   `far`. Ver hallazgo H1.

2. **El control de validez lee mal al paper.** El pie de la figura A6 dice, renderizado del PDF
   (`documentacion/sp426.5.pdf` p. 21, recorte a 300 dpi): *"a very small thermal anomaly
   (NTI < −0.93)"*. Es una cota superior, no un valor. El docstring (l. 18-21) y el yaml
   (`apendice_a.yaml:21`, "citado por línea de documentacion/sp426_5.txt") lo tratan como
   valor y exigen `±0,06` alrededor. Además `diag_nti_max` es el máximo del ROI de 50 km
   (`process_modis.py:1196-1197`), no del píxel del cráter. En los 8 brazos el control nunca
   detuvo un caso, así que no cambió veredictos, pero el instrumento no mide lo que dice medir.
   Ver H4.

3. **El brazo "producción" no es la configuración de producción para Villarrica.** La batería
   pasa `local_kernel_bg_compatible=False` (FONDO_LOCAL, l. 115 y 206) para los nueve;
   `volcanoes.yaml` da a Villarrica `local_kernel_bg: true` (l. 89, con
   `ENABLE_LOCAL_KERNEL_BG=True` en el perfil). Deliberado y documentado (geometría uniforme,
   l. 12-16), pero entonces "hoy (producción)" en (c) es "el algoritmo de hoy con geometría y
   fondo uniformes", no lo que corre el cron sobre Villarrica.

4. **`sin_compuerta_t23` quita la compuerta sólo en la llamada de `first_pass_tests_2_and_3`**
   (l. 220-223 envuelve `bt_sanity_k`). Las otras compuertas de temperatura quedan: NTI absoluto
   (`process_modis.py:665`), path ETI (l. 821) y el segundo paso. Correcto para lo que dice
   medir; lo anoto para que nadie lo lea como "sin compuertas".

### Instrumento 3: `experiments/_s137/probe_etapa_apendice.py`

**Qué calcula de verdad.** Envuelve `first_pass_tests_2_and_3` en el namespace de
`process_modis` (l. 145; la llamada real es por nombre, `process_modis.py:866-869`, sólo kwargs,
así que el envoltorio recibe todo), y con los mismos `nti`, `eti` del diag, `bt`, `dist_km` y
`t_bg` recalcula por su cuenta dNTI/dETI con `dc._nanmean_8neighbors_fast`, los umbrales
`min`/`max` con los C1/C2 de la llamada, y cuenta dentro del círculo de 5 km: `n_dnti`,
`n_deti`, `n_ambos`, `n_ambos_y_bt` (l. 59-102). Devuelve exactamente lo que devuelve la
original (l. 108-129).

**Pregunta 1.** Sí: el conteo `n_first_pass_escena` que copia del diag coincide con la suma que
persiste el pipeline, y en A6 05:55 B22 el desglose dice `ambos=2, ambos+BT=0, escena=0`,
que es la firma exacta de "la compuerta es la que corta".

**Pregunta 2.** Si la envoltura no se ejecutara, `CAPTURA` quedaría vacía y `imprimir` mostraría
`etapa: {}`; las 6 filas tienen `n_capturas=1`. Si el diag viniera sin `eti` (pool insuficiente)
se registra como error explícito (l. 114-116), no como cero.

**Caminos de error.** (i) Usa el círculo `dist_km <= 5` para el summit; el pipeline usa lo mismo
porque `ENABLE_ROI1_BOX_PAPER=False` (verificado en `pipeline.profile`); si alguien enciende la
caja 5×5 del paper, el probe y el pipeline dejarían de contar la misma región. (ii) Umbral
"min"/"max" sólo con los C1/C2 summit (l. 70-76): dentro de 5 km es lo que aplica; el conteo
"escena" del diag sí incluye la ROI2 con C1 0,010 y C2 10. (iii) No pude re-correrlo (granules).

### Instrumento 4: `experiments/_s137/medir_figuras_apendice.py`

**Qué calcula de verdad.** Renderiza las páginas 19 y 21 a 400 dpi, recorta el panel dNTI y dETI
de A2 y A6 con cajas fijas en coordenadas de 160 dpi, arma una tabla color→valor con la columna
central de la barra y una recta fila→valor ajustada a marcas de graduación **escritas a mano**
(l. 46-51), asigna a cada píxel el color más cercano, toma una muestra por celda 51×51 y calcula
mediana, MAD, semi-rango 16-84 y desvío con recorte 3σ (l. 125-136). Control pre-registrado:
mediana de dNTI dentro de ±0,0003.

**Un dato que el instrumento no sabía:** las figuras son PNG **embebidos de 1065×607 px**
(`fitz.extract_image`, xref 140 p. 19 y 166 p. 21). El render a 400 dpi interpola 2× un raster
que ya existe. Los rótulos de la barra son parte del raster (no hay texto extraíble en esas
coordenadas), así que las marcas sólo pueden validarse mirando la imagen.

**Re-corrida idéntica** (`medir_figuras_apendice_copia.py`, sólo cambia la carpeta de salida):
los 4 paneles dan JSON **idéntico** al commiteado (`out_figuras/figuras_apendice.json`). El
instrumento es determinista.

**Medición sobre el raster nativo** (`medir_figuras_nativo.py`, marcas detectadas por los
centros de los 5 rótulos 0,01 / 0,005 / 0 / −0,005 / −0,01; 221 colores en la barra):

```
A2 dNTI: escala [-0.00982, 0.01166] residuo 3.9e-05  celda51 mad 0.00043 pct 0.00049 r3 0.00057  sin lago 0.00060  max 0.01166
A6 dNTI: escala [-0.00983, 0.01131] residuo 6.2e-05  celda51 mad 0.00057 pct 0.00072 r3 0.00079  sin lago 0.00074  max 0.01131
A7 dNTI: escala [-0.00987, 0.00976] residuo 4.4e-05  celda51 mad 0.00066 pct 0.00062 r3 0.00062  max 0.00414   (negativo, nublado)
A3 dNTI: escala [-0.00986, 0.00972] residuo 3.6e-05  celda51 mad 0.00079 pct 0.00076 r3 0.00080  max 0.00972   (positivo)
A9, A4: la barra trae otros rótulos (7 y 8 grupos), no medidos
```
Las marcas a mano de S137 para A6, convertidas a píxeles nativos, caen a ≤ 1,3 px de los
centros de rótulo detectados (358,9 / 410,3 / 463,2 contra 358,0 / 409,0 / 462,0). Nativo y
400 dpi coinciden dentro de 0,00004.

**Controles (salida cruda):**

```
C1 sintetico, campo 51x51 gaussiano pintado con la barra de A6 y reescalado al interior (bilineal / nearest), r3 recuperado:
   sigma_true 0.0004 -> 0.00036 / 0.00040     sigma_true 0.0008 -> 0.00070 / 0.00076
   sigma_true 0.0016 -> 0.00142 / 0.00162     sigma_true 0.0030 -> 0.00262 / 0.00293
   sigma_true 0.0076 -> 0.00576 / 0.00643   (aqui ya recorta la escala +-0.01)
C2 instrumento muerto: panel uniforme -> sigma 0.0 (mediana -0.00003); ruido RGB puro -> sigma 0.0037, mediana +0.00112
C3 escala invertida sobre A6: signo cambiado -> sigma igual, mediana +0.00003 (control PASA);
                              espejada       -> sigma igual, mediana +0.00151 (control FALLA)
C5 mascara de alerta (celdas de 1 km, centro 25.5, norte arriba):
   A6: 38 px blancos, ~2.4 celdas, centroide (24.75, 25.50) -> 0.75 km rumbo 270 (junto al centro)
   A2: 140 px blancos, ~9 celdas, centroide (35.89, 24.42) -> 10.45 km rumbo 84.1 (10.24 km si la grilla fuera de 50)
       celdas dNTI saturadas: cols 33-38, filas 23-26 -> 7.3 a 12.0 km, rumbos 73 a 90; la celda (35,25) da 9.06 km / 83.7
```

**Lectura de los controles.** (1) El instrumento **discrimina**: un sigma real de 0,0076 se leería
0,006, no 0,0008; y un panel muerto da 0, no 0,0008. (2) Tiene **sesgo negativo de 5 a 12 %** por
el suavizado del reescalado (0,0008 → 0,0007). (3) El control de la mediana **no detecta un cambio
de signo** de la escala (la mediana de un fondo es ~0 en ambos sentidos) y el sigma es invariante a
la inversión; lo que valida la escala es la recta por los 5 rótulos (residuo ≤ 6×10⁻⁵ sobre un
rango de 0,021, o sea 0,3 %). Sí detecta un corrimiento (espejo). (4) El centro de la grilla es el
volcán: en A6 la alerta cae a 0,75 km del centro (el paper: grilla de 50×50 km "centred on the
volcano's summit", p. 3). (5) **Este instrumento no produce la posición 9,6 km / 83°**: no tiene
código de posición; ese número está escrito a mano en `conformidad_apendice.py:230`.

### Instrumento 5: `experiments/_s137/comparar_brazos_apendice.py`

**Qué calcula.** Lee por nombre de directorio (nunca glob) los `resultado_apendice.json`, cuenta
positivos/negativos CONFORME e indeterminados, y declara CUMPLE sólo con 6/6, 3/3 y 0
indeterminados (l. 53-65).

**Re-corrida** sobre `_s136` y `_s137` (salida cruda en §2(c)). **Controles**
(`control_comparador.py`): JSON 9/9 → `positivos 6/6 negativos 3/3 -> CUMPLE`; JSON todo mal →
`0/6 0/3 -> no cumple`; JSON todo INDETERMINADO → `0/6 0/3 indeterminados 9 -> no cumple`;
directorio sin JSON → `(ausente: ...)`, no 0/9. Sano. Único camino de error: hereda el predicado
"publica" del instrumento 2 (H1); no es defecto propio.

---

## 2. Las afirmaciones (a) a (f)

**(a) "Sigma del dNTI de MIROVA en sus figuras ~0,0008; el nuestro en la misma escena 0,0076 (B21)
y 0,0016 (B22)." CONFIRMADA con dos precisiones.** Figura A6 en nativo: r3 0,00079, MAD 0,00057,
percentil 0,00072 (sin lago 0,00074); a 400 dpi 0,00082 / 0,00064 / 0,00084. Con el sesgo del
control C1 (−5 a −12 %) el valor real del autor está en **0,0008 a 0,0009**. Los nuestros en la
misma pasada (A6 2009-06-24 05:55 UTC, `out_etapa/etapa_apendice.json`): B21 `sd_dnti`
0,007642, B22 0,001571 (y 04:10: 0,004998 / 0,002340). Precisiones: (i) son **estimadores
distintos** (std ordinaria sobre el pool suitable contra MAD/percentil/recorte sobre un campo
recortado a ±0,01); para cerrar la comparación haría falta el MAD de NUESTRO campo dNTI en esa
pasada, que ningún JSON guarda (SIN DATO, necesita el granule). Con Gauss, el recorte a ±0,01 de un
campo de sigma 0,0076 lo bajaría a ~0,006, no a 0,0008, así que el orden de magnitud del gap
sobrevive; con B22 (0,0016 contra 0,0008-0,0009) la razón es ~2, no "iguales". (ii) A7, un
negativo nublado que el paper describe como de mayor variabilidad, da 0,0006; A3 da 0,0008: el
fondo del autor está en 0,0006-0,0009 en 4 figuras de 4, no sólo en A6.

**(b) "Con B22 el sigma cae 3,5 a 4,7 veces y el primer paso queda vacío en 80 de 84." CONFIRMADA
en los números, CORREGIDA en el enunciado.** Medianas de brazo: 3,48× (Villarrica) y 4,69×
(Láscar); mediana de cocientes por par 3,33× y 4,12×. `n_first_pass == 0` en **80 de 84** con B22
(81 de 84 con B22 + regrid; 1 de 84 en base). Corrección: ese conteo es de píxeles que pasan Tests
2 y 3 **y además** la compuerta `bt > t_bg + 3 K` (`detection_context.py:528-533`). "Tests 2 y 3
solos" no está en el JSON. En las 6 pasadas del probe de etapa, con B22 "ambos" (sin compuerta) dio
0, 0, 3, 0, 0, 2 dentro de 5 km y "ambos+BT" 0 en las seis: parte del vacío es la compuerta, no
la banda. No re-corrido (granules).

**(c) "Hoy 6 de 6 y 0 de 3; B22 + sin compuerta + fondo local + prosa da 5/6 y 3/3; ninguno
cumple." CONFIRMADA bajo el predicado de la batería; CORREGIDA bajo el del dashboard.** Comparador
re-corrido (salida cruda): `B21 min (hoy) 6/6 0/3`, `B21 max 2/6 3/3`, `B22 min 4/6 2/3`,
`B22 max 4/6 3/3`, `B22 min sinBT 4/6 2/3`, `B22 max sinBT 4/6 3/3`, `B22 min sinBT loc 6/6 2/3`,
`B22 max sinBT loc 5/6 3/3`; ocho "no cumple". Con el predicado del operador (`summit`), la
producción da **2/6 y 2/3** y el brazo `B22 min sinBT loc` da **5/6 y 3/3** (tabla en §1,
instrumento 2). Dos caveats más: "hoy" es el código del 2026-09-08 (después hubo dos PRs en
`pipeline/`: #621, flag prosa OFF por defecto, y #624, estilo), y "producción" pasa fondo local
apagado para Villarrica (ver instrumento 2, camino 3).

**(d) "En A2 el autor detecta a 9,5 a 9,7 km, rumbo 83°; la batería evalúa dentro de 5 km."
CONFIRMADA en sustancia; el número exacto no lo produce ningún instrumento listado.** Mi medición
de la máscara de alerta del autor (`figura A2`, panel ALERT Mask, nativo): centroide a **10,45 km,
rumbo 84,1°** (9 celdas; 10,24 km si la grilla fuera de 50); las celdas saturadas del dNTI van de
7,3 a 12,0 km con rumbos 73° a 90°; la celda (35, 25) da 9,06 km / 83,7°. La detección del autor
está fuera de 5 km bajo cualquier convención. La evaluación primaria de la batería es
`dist_crater_km <= 5` (`conformidad_apendice.py:158-160`). El 9,6/83 está escrito a mano
(`conformidad_apendice.py:230`) y `medir_figuras_apendice.py` no computa posiciones: NO
VERIFICABLE como salida de instrumento, sí como hecho.

**(e) "En A6 05:55 el cráter cae sólo por la compuerta (268,3 contra 275,3 K); sin compuerta
detecta; con fondo del anillo VRP 0,0 por el recorte a cero; con fondo local 0,539 MW."
CONFIRMADA por las salidas commiteadas y por lectura del código.** `out_etapa`, B22, 05:55:
píxel del cráter `dNTI 0,0121 dETI 0,0140 bt 268,3217 pasa_bt False`, `t_bg + margen 275,2459`
(t_bg 272,25 + `NTI_BT_SANITY_K` 3,0; "275,3" es redondeo de 275,25), `ambos 2, ambos+BT 0`.
Brazo `b22_sincompuerta`: `n1er 2`, cúmulo de 2 px a 0,81 km, `vrp 0,0`; brazo `fondolocal`:
`0,539` (prosa: `0,51`). Mecanismo en el código: `L_bg_global` se deriva del `t_bg` del anillo
5-25 km (`process_modis.py:1023`, `BG_INNER_KM=5, BG_OUTER_KM=25`); con `local_kernel_bg_compatible`
falso se usa ese L_bg (l. 1041-1052) y `delta_L = np.maximum(hotpix_rad − L_bg, 0)` (l. 1056)
deja en 0 un píxel de 268,3 K contra un fondo de 272,25 K. Cada píxel del cúmulo vale 0 y el
cúmulo suma 0. Y ese 0 es invisible para el operador: `isValidDetection` exige `vrp_mw > 0`
(`frontend/index.html:1467`). No re-corrido (granules).

**(f) "El remuestreo a 1 km no baja el sigma: lo sube 13 a 15 %." CONFIRMADA en el número,
SOSPECHA en la atribución.** Medianas de brazo: +13,2 % Láscar, +15,2 % Villarrica (por par:
+15,9 % y +8,7 %; B22→ambos: +13,7 % y +17,2 %). Lo que se midió es NUESTRO remuestreo:
`regrid_to_utm` es vecino más cercano sin relleno, una muestra por celda y **NaN en toda celda sin
muestra** (`pipeline/regrid.py:56, 123`; `_regrid_modis_granule`, `process_modis.py:397-448`).
Fuera del nadir los centros de píxel MODIS distan más de 1 km, así que la grilla queda con huecos y
el kernel 8-vecinos promedia menos vecinos (`_nanmean_8neighbors_fast`, `detection_context.py:162`,
cuenta sólo válidos). Que el sigma suba es compatible con eso; no dice nada del remuestreo de
MIROVA, que no está especificado. Sin granules no puedo medir la fracción de celdas vacías.

---

## 3. Hallazgos propios, por gravedad

### H1. La batería mide "cúmulo a ≤ 5 km con VRP > 0"; el operador ve "summit". Con el predicado del dashboard, producción no da 6/6 y 0/3 sino 2/6 y 2/3
- `experiments/_s136/conformidad_apendice.py:158-160` contra `frontend/index.html:1056, 1060, 1466-1470`; `pipeline/process_modis.py:294-314` (etiqueta desde `final_hotspot`, flag `ENABLE_MODIS_DISTANCE_CLASS_FROM_CLUSTER=False`). SCRIPT: `marcador_predicado_dashboard.py` (tabla en §1).
- QUÉ PASA: en MODIS el píxel más caliente en MIR absoluta de la escena de 50 km suele ser un valle o una costa, no el cráter (A69/A81); la etiqueta `far` sale de ese píxel y el dashboard la usa para ocultar el record. La batería no la mira. En el brazo B21, 19 de 22 pasadas "publicadas" son `far`: A1, A2, A5 y A6 pasan a no publicados para el operador, y los falsos positivos A7 y A9 también se vuelven invisibles. Los brazos B22 casi no cambian (la banda 22 mueve el `final_hotspot`).
- CÓMO SE VE EN EL DASHBOARD: es exactamente la diferencia entre lo que la batería cuenta y lo que el operador ve. Los 3 FP "estructurales" de producción están ocultos por la etiqueta en 2 de 3 casos.
- CÓMO REPRODUCIRLO: `python experiments/_s138_audit/eje3/marcador_predicado_dashboard.py`.
- CONFIANZA: CONFIRMADO (sobre los JSON commiteados). GRAVEDAD 4: cualquier prioridad que salga de "6/6 hoy" o de "B22 pierde A6" cambia de signo según el predicado; y las comparaciones entre brazos no son a predicado constante.

### H2. "El primer paso queda vacío" incluye la compuerta de temperatura, que S137 mismo cuestiona
- `pipeline/detection_context.py:528-533` (`hot = pass_2 & pass_3 & (bt > t_bg + bt_sanity_k)`), persistido en `process_modis.py:1526`; leído por `sigma_dnti_4brazos.py:114`.
- QUÉ PASA: en cumbres heladas el píxel del cráter puede superar dNTI y dETI y quedar bajo `t_bg + 3 K`; el conteo lo cuenta como "no pasa el primer paso". La afirmación (b) atribuye el vacío a la banda; el JSON no separa banda de compuerta.
- CÓMO SE VE EN EL DASHBOARD: invisible (es de un experimento).
- CÓMO REPRODUCIRLO: en el probe de etapa, A6 2009-06-24 05:55 UTC B22: `ambos=2, ambos+BT=0, escena=0`.
- CONFIANZA: CONFIRMADO por lectura. GRAVEDAD 2.

### H3. El sigma "del autor" y el "nuestro" son estimadores distintos sobre campos distintos
- `medir_figuras_apendice.py:125-136` (MAD, percentil, recorte 3σ sobre valores recortados a la escala ±0,01) contra `detection_context.py:493` (`np.std` sobre el pool suitable, sin recorte).
- QUÉ PASA: la comparación 0,0008 contra 0,0076 mezcla instrumentos. El orden de magnitud del gap sobrevive a cualquier corrección razonable (ver (a)); el factor exacto no está medido.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: requiere el granule de A6 05:55 y calcular MAD del campo dNTI nuestro; SIN DATO en Windows.
- CONFIANZA: CONFIRMADO (la diferencia de estimadores), SOSPECHA (su magnitud). GRAVEDAD 2.

### H4. El control de validez de la batería lee "NTI < −0,93" como "NTI ≈ −0,93" y lo compara con el máximo de 50 km
- `conformidad_apendice.py:18-21, 147-157`; `apendice_a.yaml:21` (cita al `.txt`); `process_modis.py:1196-1197` (`nti_max` = máximo del ROI). PDF p. 21, pie de A6, render a 300 dpi: "(NTI < −0.93)"; igual patrón en A5 ("< −0.91") y A8 ("< −0.9").
- QUÉ PASA: el `.txt` corrompe el operador (sale ",20.93"), como ya advierte la regla A95, y el control se construyó desde ahí. Un máximo de ROI de −0,90 (B21, 05:55) pasa el control aunque el paper diga que la anomalía está bajo −0,93; el píxel del cráter en ese brazo sí cumple (−0,943, probe de etapa). En ninguno de los 8 brazos el control cambió un veredicto.
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CÓMO REPRODUCIRLO: `python -c "import fitz; print(fitz.open('documentacion/sp426.5.pdf')[20].get_text('words'))"` y buscar el token tras `(NTI`; renderizar `clip=(60,303,300,326)` a 300 dpi.
- CONFIANZA: CONFIRMADO. GRAVEDAD 2.

### H5. El brazo "producción" de la batería apaga el fondo local que producción usa en Villarrica
- `conformidad_apendice.py:115, 206` (`local_kernel_bg_compatible=FONDO_LOCAL=False`) contra `volcanoes.yaml:89` (`local_kernel_bg: true`) y `pipeline/profile.py` (`ENABLE_LOCAL_KERNEL_BG=True`); `process_modis.py:1041`.
- QUÉ PASA: deliberado (geometría uniforme), pero el rótulo "hoy (producción)" en (c) y en el comparador ("B21 min (hoy)") dice otra cosa. Para A6 el brazo `fondolocal` es, en ese eje, más cercano a producción que el brazo "hoy".
- CÓMO SE VE EN EL DASHBOARD: invisible.
- CONFIANZA: CONFIRMADO. GRAVEDAD 2.

### H6. El +13-15 % del remuestreo es una propiedad del regrid con huecos, no del "remuestreo" en general
- `pipeline/regrid.py:56, 123`; `pipeline/process_modis.py:397-448`; `detection_context.py:162-186`.
- QUÉ PASA: ver (f). Una conclusión de la forma "remuestrear no ayuda" no se sostiene sin medir primero cuántas celdas quedan vacías por pasada.
- CÓMO REPRODUCIRLO: sobre un granule, contar `np.isnan(g['band22']).mean()` a la salida de `regrid_to_utm`.
- CONFIANZA: SOSPECHA (mecanismo leído, magnitud no medida). GRAVEDAD 2.

### H7. La posición 9,6 km / 83° está escrita a mano y el instrumento que la justifica no la calcula
- `conformidad_apendice.py:230` (`POSICION_AUTOR = {"A2": (9.6, 83.0)}`); `medir_figuras_apendice.py` no tiene código de posición.
- QUÉ PASA: mi medición da 10,45 km / 84° (centroide) o 9,1 km / 84° (una celda). La conclusión no cambia (> 5 km de sobra) pero el número no es reproducible desde el repo. El radio post hoc de 3 km (l. 231) tampoco tiene justificación escrita.
- CONFIANZA: CONFIRMADO. GRAVEDAD 1.

### H8. El control de la mediana no vigila el signo de la escala
- `medir_figuras_apendice.py:18-19, 170`. Control C3: signo cambiado, mediana +0,00003, pasa.
- QUÉ PASA: el sigma es invariante al signo, así que para (a) no importa; importaría si alguien usara el instrumento para leer el SIGNO de una anomalía (por ejemplo dETI del lago). Lo que sí valida la escala es la recta por los cinco rótulos (residuo 0,3 %).
- CONFIANZA: CONFIRMADO. GRAVEDAD 1.

### Nota fuera de mi eje
A mitad de sesión `git status` mostró `experiments/_s133/auditar_guards_por_subcadena.json`
modificado; al cierre ya no aparece. No lo toqué ni corrí ese script (lo escribe otro eje corriendo
en paralelo). Al cierre el árbol sólo tiene `docs/audit_s138/` y `experiments/_s138_audit/` sin
seguimiento.

---

## 4. VERIFICADO LIMPIO

- **Comparador (instrumento 5)**: determinista, sin glob, distingue ausente de 0/9, y cumple sólo con
  6/6 + 3/3 + 0 indeterminados. `python experiments/_s138_audit/eje3/control_comparador.py`.
- **`evaluar_caso`**: el corte a 5 km funciona en ambos sentidos y en el borde (5,0 sí, 5,001 no);
  VRP 0,0 no cuenta como publicado, igual que el dashboard; sin pasadas da INDETERMINADO.
  `python experiments/_s138_audit/eje3/control_evaluar_caso.py`.
- **Medidor de figuras (instrumento 4)**: re-corrida idéntica al JSON commiteado; las marcas a mano
  coinciden con los rótulos detectados automáticamente (≤ 1,3 px nativos); nativo y 400 dpi
  coinciden en 0,00004; discrimina (0,0076 se leería 0,006), no está muerto (uniforme → 0), sesgo
  de −5 a −12 %. `python experiments/_s138_audit/eje3/medir_figuras_nativo.py`.
- **Alcance de los monkeypatch de los instrumentos 1, 2 y 3**: los flags y la función envuelta se
  leen como globales de `pipeline.process_modis` en el punto de uso (l. 502, 544, 548, 561, 866);
  ningún otro módulo los consume en MODIS.
- **Aritmética de (b) y (f)** re-computada desde el JSON: 84 granules, 40 + 44, ventana 08-12 a
  08-31, sin `None`.
- **Mecanismo de (e)** leído entero: anillo 5-25 km, `L_bg_global` l. 1023, rama local l. 1041,
  recorte l. 1056, y el 0 es invisible por `isValidDetection`.
- **Grilla del paper**: 50×50 km centrada en la cumbre (PDF p. 3 y p. 4); en A6 la alerta del
  autor cae a 0,75 km del centro.

---

## Resumen

Los cinco instrumentos hacen lo que dicen hacer, con una excepción de fondo y varias de rótulo.
La excepción de fondo es la **batería del Apéndice A**: cuenta "cúmulo a ≤ 5 km con VRP > 0",
y el operador ve sólo lo que lleva `distance_class = summit` (`frontend/index.html:1056`). En el
brazo "producción" 19 de 22 pasadas publicadas son `far`: con el predicado del dashboard la
producción da **2/6 positivos y 2/3 negativos**, no 6/6 y 0/3, y el mejor brazo de S137 queda en
5/6 y 3/3 en ambos predicados (H1, gravedad 4).

Veredictos: **(a) CONFIRMADA** (A6 nativo 0,00079; con el sesgo del control, 0,0008 a 0,0009; A7
negativo 0,0006, A3 0,0008; nuestro 0,0076 / 0,0016 en la misma pasada), con la salvedad de que se
comparan estimadores distintos (H3). **(b) CONFIRMADA en número, CORREGIDA en enunciado**: 3,48× a
4,69×, 80 de 84 vacíos, pero el vacío incluye la compuerta `bt > t_bg + 3 K` (H2). **(c)
CONFIRMADA bajo el predicado de la batería, CORREGIDA bajo el del dashboard** (H1); "producción"
además apaga el fondo local que Villarrica usa (H5). **(d) CONFIRMADA en sustancia**: la alerta del
autor en A2 está a 10,4 km / 84° (centroide) o 9,1 km (una celda), fuera de 5 km; el 9,6/83 está
escrito a mano (H7). **(e) CONFIRMADA** por salidas commiteadas y por código (`process_modis.py:1023,
1041, 1056`). **(f) CONFIRMADA en número, SOSPECHA en atribución**: es nuestro regrid con celdas
vacías, no "el remuestreo" (H6).

El control de validez de la batería lee "NTI < −0,93" del `.txt` corrupto como "≈ −0,93" y lo
compara con el máximo de 50 km (H4); no cambió veredictos. No re-corrí los instrumentos 1 a 3
(HDF4 no disponible en Windows, granules ausentes): su verificación es por lectura y sobre salidas
commiteadas.

Ruta del entregable:
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\docs\audit_s138\EJE_3_verificador_instrumentos_s137.md`.
Scripts y salidas: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s138_audit\eje3\`.
