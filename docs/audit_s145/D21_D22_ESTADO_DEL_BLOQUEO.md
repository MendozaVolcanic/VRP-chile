# D21 y D22: por qué están bloqueadas y qué haría falta para desbloquearlas

> Auditoría de lectura, S145, 2026-09-20. Read-only: no se tocó `pipeline/`, no se hizo commit,
> no se corrió ningún A/B ni workflow. Toda afirmación numérica sale de una salida de herramienta
> citada acá; lo que no se verificó se dice como tal.

---

## 0. Cobertura: qué alcancé a revisar y qué no

**Revisado entero**:

- `docs/MIROVA_DIVERGENCES.md`, entradas D21 (l. 2232 y siguientes), D22 (l. 2257 y siguientes) y
  D11 (l. 1259 y siguientes), más los encabezados de D23 a D29 que las tocan.
- `experiments/_s136/apendice_a.yaml` (definición de la batería), `RESULTADO_APENDICE_A.md`
  (el resultado de S136) y el criterio de aprobación dentro de `conformidad_apendice.py`.
- `experiments/_s137/RESULTADO_BATERIA_B22.md`, `RESULTADO_FONDO_LOCAL.md` y
  `COMPARACION_8_BRAZOS.txt` (los ocho brazos).
- `docs/AUDIT_S138.md`, resumen ejecutivo y tabla de decisiones del dueño (§D).
- `docs/audit_s138/EJE_5_bateria_apendice_instrumento.md`: encabezados de todo el archivo, más
  §0 a §4 completos (cómo se midió, el instrumento corregido, el pre-registro del A/B).
- `docs/HYPOTHESIS_LOG.md`, entradas `H_S143_D22_D25` y `H_S144_DIRECCION`, completas.
- `experiments/_s133/resultado_ab_b22.json`: veredicto completo del A/B real de la banda 22.
- Estado efectivo de los flags leyendo `pipeline.profile` (no el YAML).
- `pipeline/profiles/_s142_ab_*.yaml` (los seis brazos del A/B de S143).
- `.github/workflows/probe-s136-conformidad-apendice.yml` (dónde corre la batería).
- `docs/audit_s145/PARIDAD_Y_OBJETIVOS_S145.md` §4 y `tasks/BLOQUE_ARRANQUE_S140.md` §histórico.

**NO revisado** (y por lo tanto no afirmo nada sobre su contenido):

- §5 de `EJE_5_bateria_apendice_instrumento.md`, los hallazgos H1 a H12 en detalle. Leí los
  títulos de los doce y el cuerpo de H1. Lo que cito de H2 a H12 viene de su título y del
  resumen ejecutivo de `AUDIT_S138.md`, no del cuerpo.
- `docs/audit_s139/EJE_4_adversarial_plan.md` entero (sólo las líneas que aparecieron por grep,
  incluida H403).
- **El PDF del paper.** No volví a renderizar ninguna página (A95). Las citas verbatim de la p. 3
  y la p. 7 las tomo de D21 y D22 tal como están escritas, donde constan como verificadas contra
  página renderizada en S137 y S138. Es la única cadena de esta auditoría que descansa en otro
  documento.
- Los JSON crudos de las salidas de la batería (`experiments/_s137/out_apendice_*`). Los conteos
  por brazo salen de `COMPARACION_8_BRAZOS.txt`, que es la tabla que generó
  `comparar_brazos_apendice.py` sobre esos JSON.
- El pre-registro y el evaluador de S143 en detalle (`docs/PREREGISTRO_AB_D22_D25_S143.md`,
  `experiments/_s143_evaluador/`). Uso el resumen de la entrada del `HYPOTHESIS_LOG`, que sí
  cita sus números y su verificador.

---

## 1. Qué es exactamente "la batería"

Es el banco de pruebas del **Apéndice A de Coppola et al. 2016a**, donde el propio autor publica
nueve escenas MODIS con su veredicto: en seis su algoritmo detecta y en tres no. La idea es medir
la fidelidad contra la referencia del autor, no contra el consolidado de MIROVA, cuyo silencio
puede ser alcance operacional y no ausencia de señal (A54).

**Cuántos casos: nueve.** Verificado:

```
$ grep -c "caso:" experiments/_s136/apendice_a.yaml
9
```

| caso | volcán | fecha | el autor |
|---|---|---|---|
| A1 | Bezymianny | 2012-01-08 | detecta |
| A2 | Eyjafjallajökull | 2010-04-07 | detecta |
| A3 | Erta Ale | 2009-08-16 | detecta |
| A4 | Dubbi | 2013-07-03 | **no** detecta |
| A5 | Ubinas | 2008-04-03 | detecta |
| A6 | Villarrica | 2009-06-24 | detecta |
| A7 | Tolbachik | 2012-11-20 | **no** detecta |
| A8 | Etna | 2010-02-08 | detecta |
| A9 | Stromboli | 2010-01-19 | **no** detecta |

**El criterio de aprobación: 6 de 6 positivos y 3 de 3 negativos, los nueve.** Está fijado en S136
y las dos sesiones siguientes lo repiten sin moverlo ("Criterio fijado en S136, no se mueve",
`experiments/_s137/RESULTADO_BATERIA_B22.md`).

El predicado por caso, leído en el código (`experiments/_s136/conformidad_apendice.py`, función
`evaluar_caso`, contenido verificado hoy):

```python
publica = [p for p in pasadas
           if (p.get("vrp_pc_mw") or 0) > 0 and p.get("dist_crater_km") is not None
           and p["dist_crater_km"] <= INNER_KM]
```

con `INNER_KM = 5.0` (el ROI1 uniforme del paper, D18) y `RADIUS_KM = 25.0`. Un positivo es
CONFORME si **alguna** pasada nocturna de esa fecha UTC publica un cúmulo con VRP > 0 dentro de
5 km de la coordenada del catálogo; un negativo es CONFORME si **ninguna** publica. Hay además un
control de validez: donde el paper da un NTI (A5, A6, A8), alguna pasada debe caer a `TOL_NTI =
0.06` de ese valor, o el caso queda INDETERMINADO en vez de NO CONFORME.

**Dónde vive el código**:

- Datos y veredictos del autor: `experiments/_s136/apendice_a.yaml`.
- Probe: `experiments/_s136/conformidad_apendice.py`. Elige brazo por variables de entorno:
  `APENDICE_PROSA`, `APENDICE_B22`, `APENDICE_SIN_COMPUERTA`, `APENDICE_FONDO_LOCAL`.
- Corre en GitHub Actions: `.github/workflows/probe-s136-conformidad-apendice.yml` (MODIS necesita
  HDF4, no corre en Windows).
- Comparación de brazos: `experiments/_s137/comparar_brazos_apendice.py`.
- Tests: `tests/test_conformidad_apendice_s136.py` y `tests/test_probe_etapa_apendice_s137.py`.

**Es sólo MODIS.** Ninguno de los nueve casos dice nada de VIIRS 375 ni de la banda M. Lo declara
el propio `RESULTADO_APENDICE_A.md` en sus límites.

---

## 2. Los brazos probados, y en qué falló cada uno

Los ocho brazos están medidos y viven en `experiments/_s137/COMPARACION_8_BRAZOS.txt`, generado
por script sobre los JSON de cada run (regla S91). Los ejes son tres: banda MIR primaria (B21 de
hoy contra B22 del paper, D21), compuerta de temperatura en los Tests 2 y 3 (con o sin, D22) y
fondo de la magnitud (anillo regional de hoy contra los vecinos del píxel, D25); más la conectiva
de los Tests 2 y 3 (`min`, la fórmula, contra `max`, la prosa, que es la contradicción interna del
paper que S136 documentó).

| brazo | qué cambia respecto de producción | positivos | negativos | por qué no cumple |
|---|---|---|---|---|
| B21 `min` (**producción**) | nada | **6/6** | **0/3** | publica en los tres negativos del autor: Dubbi, Tolbachik y Stromboli. Es sobre-detección pura del camino contextual |
| B21 `max` | sólo la conectiva | 2/6 | 3/3 | cura los tres negativos apagando cuatro positivos, entre ellos Villarrica y Ubinas, que son las anomalías débiles reales |
| B22 `min` | sólo D21 | 4/6 | 2/3 | cura Tolbachik y Stromboli, pierde Eyjafjallajökull y Villarrica, y sigue publicando en Dubbi |
| B22 `max` | D21 + conectiva | 4/6 | **3/3** | cura los tres negativos, pero sigue perdiendo Eyjafjallajökull y Villarrica |
| B22 sin compuerta `min` | D21 + D22 | 4/6 | 2/3 | **idéntico al B22 `min` en conteo**: quitar la compuerta sola no devuelve ningún caso |
| B22 sin compuerta `max` | D21 + D22 + conectiva | 4/6 | 3/3 | igual que B22 `max`: la compuerta sola no mueve el conteo |
| B22 sin compuerta, fondo local, `min` | D21 + D22 + D25 | **6/6** | 2/3 | recupera los seis positivos pero sigue publicando en Dubbi. Además su "conforme" en A2 es otro objeto (cúmulo a 1,2 km al norte de la cumbre; la figura A2 del autor pone su detección a ~9,6 km al este) |
| **B22 sin compuerta, fondo local, `max`** | los tres + conectiva | **5/6** | **3/3** | **el mejor: 8 de 9**. El único fallo es Eyjafjallajökull, y es de la evaluación, no de la detección |

**Lo medido y lo supuesto, separado**:

- **Medido** (runs verdes, salidas commiteadas): los conteos de la tabla; que con B22 el sigma del
  dNTI cae de 0,0079 a 0,0017 en Láscar y de 0,0071 a 0,0020 en Villarrica, y el primer paso queda
  vacío en 80 de 84 escenas (`experiments/_s137/RESULTADO_SIGMA_DNTI.md`, citado por D21); que en
  la escena exacta de la figura A6 el cráter de Villarrica pasa de 100 píxeles de primer paso con
  B21 a 0 con B22, a 2 quitando la compuerta, y su VRP de 0,0 MW a 0,539 MW al cambiar el fondo
  (`RESULTADO_FONDO_LOCAL.md`).
- **Supuesto, declarado como tal en el propio documento**: que la anomalía de Eyjafjallajökull del
  7-abr-2010 sea la erupción de flanco de Fimmvörðuháls. S137 lo escribe como hipótesis no
  verificada; S138 la midió sobre las figuras y ubicó el objeto del autor a 10,7 a 11,5 km, con lo
  que la hipótesis queda respaldada pero el número exacto de 9,6 km no lo produce ningún script
  (EJE 5, H7, leído sólo en su título).
- **Supuesto y luego refutado**: la atribución de S137 de que la compuerta es lo que pierde a
  Villarrica A6. S138 la corrigió: la palanca es el fondo del anillo (D25), no la compuerta.

**Fuera de la batería, hay dos A/B reales que también miden estos ejes.** No hay que descubrirlos
de nuevo:

1. **S133, D21 sobre datos reales de MODIS.** Láscar y Villarrica, agosto 2026, pareo por gránulo.
   Veredicto leído hoy del JSON (`experiments/_s133/resultado_ab_b22.json`): `adoptar = False`.
   Por criterio: C1 (fondo) **falla** en los dos volcanes, C2 (detección) **pasa** con 0 pasadas
   perdidas de las que MIROVA publicó, C3 (magnitud) **falla** con razón ON/OFF de 0,107 en Láscar
   (n = 5 pares) y 0,256 en Villarrica (n = 14), C4 (control de saturación de B22) **pasa**.
   **El matiz que importa**: C3b, la paridad contra MIROVA, tuvo n = 2 en Láscar OFF y **n = 0** en
   los otros tres casilleros. O sea que ese A/B midió que la magnitud **cambia**, no si el cambio
   acerca o aleja de MIROVA. Esa pregunta quedó sin responder.
2. **S143, D22 y D25 sobre datos reales de VIIRS 375.** Nueve volcanes, 2026-06-01 a 2026-08-31,
   seis brazos, dos tramos, cobertura pareja verificada. Veredicto: **no adoptar**, ningún brazo
   cumple los tres criterios. Y la atribución del verificador con contexto limpio es lo que más
   pesa acá: **todo el descenso de la sobre-publicación viene de apagar `keep_peak`** (−0,373);
   **D22 y D25 empujan en contra, +0,202 y +0,052, con intervalos lejos de cero**. El brazo con
   compuerta pierde 25 noches. Es decir: en el único sensor donde D22 se midió sobre producción,
   quitar la compuerta **cuesta unos 20 puntos de sobre-publicación**.

---

## 3. Los flags: estado efectivo, leído de `pipeline.profile`

```
$ VRP_PROFILE=mirova_equivalent python -c "import pipeline.profile as p; ..."
[VRP profile=mirova_equivalent] anomaly_K=5.0 nsigma_mir=3.0 vent_K=1.0 nti_k1=-0.8 ...
ENABLE_MODIS_B22_PRIMARY = False
NTI_BT_SANITY_K = 3.0
ENABLE_TESTS_23_NO_BT_GATE_VIIRS375 = False
ENABLE_TESTS_23_NO_BT_GATE = <NO EXISTE>
ENABLE_LOCAL_KERNEL_BG = True
ENABLE_TEST1_K1_RETIRE_FROM_HOT_MASK = False
ENABLE_TEST1_NTI_INTEGRAL = False
ENABLE_UTM_REGRID = False
PATH_D_ONLY_CAP_MW = 5.0
ENABLE_SECOND_PASS_CONDITIONED = False
```

Y en `pipeline/profile.py` (contenido verificado por grep hoy):

```
486:ENABLE_TESTS_23_NO_BT_GATE_VIIRS375: bool = bool(
487:    _p.get("enable_tests_23_no_bt_gate_viirs375", False))
497:ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS375
505:ENABLE_VRP_BG_NEIGHBOR_MEAN_VIIRS750
611:ENABLE_MODIS_B22_PRIMARY: bool = bool(_cfg.get("enable_modis_b22_primary",
     _p.get("enable_modis_b22_primary", False)))
```

Lo que esto dice, y es el hallazgo más concreto de esta auditoría:

- **D21 tiene flag y es sano.** `ENABLE_MODIS_B22_PRIMARY` se lee de la raíz **y** de `paths:`, así
  que no cae en la trampa A89 de la clave escrita en la sección equivocada. Está en `False`
  (banda 21 primaria, lo que el paper no hace). Cableado verificado: `process_modis.py` lo importa
  y lo pasa a `merge_mir_bands` en tres llamadas (`rad_mir`, `bt_mir`, `rad_mir_for_nti`); el
  docstring de `merge_mir_bands` dice que `b22_primary=True` "sigue a Coppola 2016a SP426.5
  l.141-144". Tiene test: `tests/test_b22_primaria_modis_s132.py`.
- **D22 tiene flag sólo para VIIRS 375.** `ENABLE_TESTS_23_NO_BT_GATE_VIIRS375` existe y está en
  `False`. **`ENABLE_TESTS_23_NO_BT_GATE` sin sufijo NO EXISTE**: no hay forma de quitar la
  compuerta en MODIS ni en VIIRS 750 desde el perfil. El parámetro `apply_bt_gate` sí existe en
  `detection_context.py` (l. 221, 345, 437, con el gate real en la l. 546:
  `gate_bt = (bt > t_bg + bt_sanity_k) if apply_bt_gate else np.isfinite(bt)`), pero ningún flag de
  perfil lo alcanza para esos dos sensores.
- **D25 (el fondo por vecinos, que es la palanca real detrás de A6) tampoco existe para MODIS.**
  Hay `_VIIRS375` y `_VIIRS750` (este último recién escrito en S145, commit `d70199136`, apagado).
  Para MODIS no hay.
- **Corrección de citas**: el catálogo dice `mirova_equivalent.yaml:44` para `nti_bt_sanity_k`;
  hoy está en la **l. 48**. Y el encabezado de D11 cita `detection_context.py:532`; el gate está
  hoy en la **l. 546**. El contenido es el que dicen; los números se movieron (A101).

---

## 4. Por qué está bloqueado, en orden de lo que pesa

**(a) El criterio de la batería es hoy inalcanzable para el brazo correcto.** El mejor brazo da
8 de 9 y el noveno, Eyjafjallajökull, **falla por la evaluación**: el objeto del autor está a
unos 11 km de la cumbre del catálogo y la batería evalúa dentro de una caja de 5 km. Mientras el
predicado mida distancia a la cumbre, ese brazo **no puede** llegar a 6/6 por más correcto que
sea. Exigir 9 de 9 con un instrumento que no puede dar 9 de 9 es un criterio que se autobloquea.

**(b) El instrumento mide otra cosa que la que dice medir.** Es el hallazgo de S138 (EJE 5, leído
en §0 a §4 y en los títulos de §5): el "conforme" no verifica **qué** objeto publicamos, sólo que
publicamos algo dentro de 5 km. De los seis conformes de producción, **0 son verificables como el
objeto del autor y 2 son con certeza otro objeto**; la batería mezcla pasadas de hasta dos noches
locales cuando el autor muestra una sola; el conteo cambia con el radio (producción baja de 6/6 a
4/6 con 3 km); y **4 de los 8 brazos, incluida la línea base de producción, no persisten la
posición del cúmulo**, así que ni siquiera se pueden reevaluar por objeto. Con el predicado real
del dashboard, producción da 2 de 6 y 2 de 3, no 6 de 6 y 0 de 3.

**(c) D22 no es separable de D19 y D25, y donde se midió sobre producción, empeora.** El segundo
pase (`second_pass_adjacent`) corre sin compuerta y sin condición de activos previos
(`ENABLE_SECOND_PASS_CONDITIONED = False`, verificado arriba) y rescata el píxel que la compuerta
rechazó: 14 % de los records VIIRS375 y 17 % de los VIIRS750 se detectan sólo ahí. Por eso **un
brazo que quite sólo la compuerta no devuelve ninguna alerta**, y por eso los dos brazos "sinBT"
de la batería dan exactamente el mismo conteo que sus pares sin ese cambio. Y cuando sí se corrió
el A/B acoplado en VIIRS 375 (S143), D22 salió empujando la sobre-publicación **+0,202**.

**(d) Falta sustrato de código para el A/B que D21 y D22 necesitan.** El pre-registro de S138 §4
define cinco brazos (control, B22, B22 sin compuerta, + fondo local, + prosa) sobre los 11 Tier A
en MODIS. **Dos de las tres correcciones no existen como flag en MODIS**: la compuerta y el fondo
por vecinos. Implementarlas es tocar `pipeline/process_*.py` y `detection_context.py` (la
constante aparece en unos 13 lugares de los tres sensores), lo que exige A45: tag defensivo y
confirmación explícita de Nicolás. Nadie lo pidió todavía.

**(e) El estrato donde vive el fenómeno no tiene muestra MODIS.** Medido en S138 (holdout
jun-ago 2026, 11 Tier A): MIROVA publicó alertas **MODIS** sólo en Láscar, 15 noches, y **cero en
el estrato nevado**, que es justo donde D22 pretende curar el artefacto A69. En toda la historia
del CSV: Láscar 77 noches MODIS, Chaitén 3, Villarrica 2, Nevados de Chillán 1. Un A/B MODIS que
mida recall contra MIROVA-MODIS tendría n = 15 en un volcán y n = 0 donde importa. El pre-registro
lo resuelve definiendo la noche contra **cualquier** sensor de MIROVA, pero eso todavía no se
aprobó (es la decisión S138-D).

**(f) El frente está formalmente pausado, y por una regla, no por olvido.** `AUDIT_S138.md` lo
dice en su resumen ejecutivo: seis contradicciones confirmadas entre fuentes, más de tres, así que
A51 manda consolidar antes de cualquier A/B. Después, en S139 y S140, el frente **se reemplazó**
por el plan de paridad aprobado (`tasks/BLOQUE_ARRANQUE_S140.md`: "El frente D21/D22 pausado se
reemplazó por el plan de paridad aprobado"). Las decisiones S138-A, S138-B y S138-C nunca se
tomaron: siguen en la tabla del dueño con recomendación y sin respuesta.

**(g) D11 no tiene bloqueo propio.** Su condicionamiento es derivado: el "irreducible a 1 km" y el
"todos los ejes agotados" de S114 valen sólo bajo banda 21 primaria y compuerta de 3 K. Se
desbloquea solo el día que D21 y D22 se resuelvan en un sentido o en el otro. No hay nada que
hacerle directamente.

---

## 5. Qué falta concretamente, por divergencia

### D21 (banda 22 primaria)

1. **Un brazo que nadie probó**: **B22 + fondo por vecinos, CON la compuerta y con la conectiva de
   hoy**. Los ocho brazos existentes son `{B21, B22} × {min, max} × {nada, sinBT, sinBT+loc}`:
   **no hay ninguno con `loc` sin `sinBT`**. Como los dos brazos "sinBT" dan conteo idéntico a sus
   pares sin ese cambio, el brazo faltante probablemente daría el mismo 6/6 y 2/3 del séptimo,
   pero eso es **predicción mía, no medición**, y responde la pregunta que hoy no se puede
   contestar: cuánto del resultado pone la compuerta y cuánto el fondo. El sustrato para correrlo
   ya existe: es el workflow `probe-s136-conformidad-apendice.yml` con `APENDICE_B22=1` y
   `APENDICE_FONDO_LOCAL=1`, sin `APENDICE_SIN_COMPUERTA`. Cuesta un run.
2. **Un criterio que hay que revisar porque es inalcanzable**: evaluar A2 contra la posición del
   autor y no contra la cumbre (propuesta §3 punto 2 de EJE 5, nunca implementada). Sin eso el
   brazo bueno arrastra un falso negativo estructural para siempre.
3. **Datos que no existen**: la posición del cúmulo (`pc_lat`, `pc_lon`), el conteo de píxeles y
   el camino que disparó, persistidos en **todos** los brazos. Hoy faltan en 4 de 8, incluida la
   línea base, así que ni los resultados ya corridos se pueden reevaluar por objeto.
4. **Un A/B con poder suficiente**: el de S133 existe y dio NO ADOPTAR, pero con n = 5 y n = 14
   pares y **n = 0 o 2** contra MIROVA. Midió que la magnitud cae a un décimo y a un cuarto, no si
   eso acerca o aleja de MIROVA. Para decidir hace falta ventana más larga o más volcanes, y el
   estrato nevado de MODIS no tiene alertas de MIROVA para servir de referencia (punto (e)).
5. **Una decisión del dueño**: S138-C, si el A/B corre en los tres sensores o MODIS primero
   (D21 es sólo MODIS). Recomendación escrita en S138: los tres.

### D22 (compuerta `bt > t_bg + 3 K`)

1. **Código que no existe**: el flag para quitar la compuerta en **MODIS y en VIIRS 750**. Hoy
   sólo hay `_VIIRS375`. Sin eso, D22 **no se puede A/B-ear en MODIS**, que es el sensor de la
   batería y del caso A6. Escribirlo es A45 (tag defensivo + confirmación de Nicolás).
2. **Un criterio que hay que revisar**: "quitar sólo la compuerta" no es un brazo válido. Está
   medido dos veces, por caminos distintos: en la batería (conteo idéntico) y en producción (el
   segundo pase rescata el píxel). Cualquier brazo futuro tiene que llevar D22 + D25 juntos, y
   entonces lo que se está midiendo ya no es D22 sola.
3. **Lo que falta medir, y es lo que el catálogo dice que no se sabe**: cuántos falsos positivos
   devuelve quitarla. **En VIIRS 375 ya se sabe: +0,202 de sobre-publicación** (S143, con
   intervalo lejos de cero). En MODIS y VIIRS 750 sigue sin medirse, y no se puede medir sin el
   punto 1.
4. **Una decisión del dueño**: S138-B, si la formulación de flags se reformula ahora que la
   atribución está corregida (flags para el fondo y el segundo pase, no para la compuerta sola).

### D11

Nada propio. Se desbloquea cuando D21 y D22 cierren. Mientras tanto su encabezado ya está
correctamente condicionado en el catálogo y no hay que tocarlo.

### El camino barato que está escrito y sin usar

Las preguntas **2 y 3** del borrador de correo a Coppola cierran D21 y D22 respectivamente
(`docs/audit_s139/BORRADOR_CORREO_COPPOLA.md`, tabla de uso interno). El correo está redactado con
13 preguntas y **nunca se envió**. S139 ya lo señaló: estas divergencias nacieron de ambigüedades
de texto, y once preguntas cortas cierran o acotan nueve de ellas. Ninguna cantidad de relectura
del PDF ni de A/B resuelve una ambigüedad que sólo el autor puede desambiguar. Es, con diferencia,
lo más barato que queda por hacer en este frente.

---

## 6. Una nota de método

Tres cierres de este frente heredaron la lectura con que se derivaron, que es exactamente lo que
A95 describe. S136 midió y cerró bajo la conectiva `min`. S137 atribuyó la pérdida de Villarrica a
la compuerta y S138 mostró que era el fondo. S114 declaró la detección MODIS fiel y "todos los
ejes agotados" sin haber mirado los pasos previos a los Tests. Ninguno de los tres estaba mal
medido: los tres midieron bien algo distinto de lo que dijeron. El instrumento que los sostiene,
la batería, es el que S138 encontró midiendo otra cosa. Antes de correr cualquier brazo nuevo
conviene arreglar el instrumento, porque el criterio de nueve sobre nueve y el instrumento que lo
evalúa son el bloqueo, más que los brazos.
