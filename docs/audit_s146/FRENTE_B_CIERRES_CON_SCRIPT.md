# Auditoría S146, frente B: los cierres que citan un script

> Auditor: Claude Fable 5.1, sesión del 2026-09-20. Sólo lectura sobre el repo. Todo lo que este
> informe afirma sale de un comando corrido o de un archivo leído en esta sesión. Lo que no se pudo
> verificar está marcado SOSPECHA o SIN DATO.
>
> Raíz de todas las rutas: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\`.
> Scripts y salidas de esta auditoría:
> `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\experiments\_s146_auditoria\frente_B\`
> (notas crudas en `NOTAS_EN_CURSO.md` de esa misma carpeta).

## Por qué importa este frente

Un cierre con script parece el más sólido de todos: tiene un número y un archivo detrás. Por eso
mismo es el que menos se vuelve a mirar. D26 cayó en S145 justamente así: el texto hablaba de los
Tests 2 y 3 y el script sólo leía las variables del Test 2. La pregunta de este frente es una sola,
repetida cierre por cierre: **¿el script mide lo que la frase dice?**

## 1. Cobertura (primero)

**Cómo se identificaron.** Tres vías, porque la primera sola falla:

1. El censo de S145 (`experiments/_s145_censo_cierres/censo_cierres.json`): de 89 afirmaciones, 39
   con respaldo, y de ésas sólo **11** marcan `script` o `archivo_linea`. Varias de esas 11 son
   falsos positivos del patrón (`store.py`, `fetch.py` nombrados como código, no como medición).
2. Un barrido propio más ancho (`b00_identificar_cierres_con_script.py`: ventana de 10 líneas, más
   palabras de cierre, rutas `experiments/`, `scripts/`, `tests/`, `scratchpad/`): **63 líneas** de
   cierre con alguna ruta, **29** con ruta a experimento, script o test.
3. **El control positivo falló en la vía 2, y eso es un hallazgo de método**: D26 no aparece en el
   barrido por rutas, porque el catálogo nunca cita `que_rama_manda.py` por nombre. Dice "S136 midió
   que..." (`docs/MIROVA_DIVERGENCES.md:2359`). Salida cruda:
   `CONTROL POSITIVO D26 (que_rama_manda.py) aparece: False []`. Un cierre puede apoyarse en un
   script sin nombrarlo, así que hubo que seguir a mano las citas indirectas ("SNNN midió", "A/B
   corrido", "probe") de las secciones D del catálogo y de las reglas A de `CLAUDE.md`.

**Resultado.** 38 cierres con medición detrás identificados (25 auditados, 13 no tocados).

| estado | cuántos | cuáles |
|---|---|---|
| **script o test corrido en esta sesión** (tal cual si sólo imprime, o copia con la salida redirigida a mi carpeta si escribe sobre un archivo versionado) | **11** | D26 (control), D16, sustrato K1 del GAP #A, A82 barrido AUC, A81/A94 impacto neto, A12 y D5 (libro de cuentas), A99, D14/S127, S98 ancla, guard GAP #A, H12 kernel |
| **sólo leído** (el script existe pero necesita artefactos de CI que no están en disco, o baja datos de un remoto) | **9** | A85/S118, D18, S143 A/B, S135 A/B, D19 H1, A98 banco, A104, A10 matiz S132, A90 (far a summit) |
| **sin script que correr** (el respaldo citado no existe en el repo, o es prosa) | **5** | A83, A84, D9/F2.1 "0 FP residuales" S116, D20, H_S20 Regla D (éste se midió sobre los datos) |
| **no tocados**, por tiempo, declarados | **13** | A/B de S133 (área y B22), D12/C2 de S122 (`refute_d12.py`), A54 (composición de FP de S86), A66 y A67 (R3 nadir fijo, `audit_viirs_nadir_promote_r3.py`), A103 (`sensibilidad.py` de S142), A109 y A110 (S144), paridad "78 de 78 noches" de S145, D10 ctxpeak, y las hipótesis antiguas de `HYPOTHESIS_LOG.md` (H_S21 `41_DIAGNOSIS`, factor 42, `51_p31_ab`, `120_audit_tif`) |
| ya reconocidos antes de esta auditoría, no recontados | 2 | D26 (control positivo), D13 (S145) |

Los 13 no tocados quedan **SIN DATO**: no se afirma nada de ellos, ni a favor ni en contra.

**Conteo por veredicto de los 25 auditados**: MIDE LO QUE DICE 11 · MÁS ESTRECHO 9 (uno es el control
D26) · NO CORRE o script ausente 3 · mecanismo sin sustrato hoy 1 · salida persistida distinta del
texto 1. Ningún script citado falló al ejecutarse: los que no corrí fue por falta de artefactos, no
por error.

## 2. Tabla

Gravedad de 1 a 5 = cuánto trabajo futuro apaga el cierre si está mal. Confianza = en mi veredicto.

| id | cierre (archivo:línea) | script citado | qué afirma el texto | qué mide el script | veredicto | conf. | grav. |
|---|---|---|---|---|---|---|---|
| ctrl | `docs/MIROVA_DIVERGENCES.md:2353-2359` D26 | `experiments/_s136/que_rama_manda.py` (cita indirecta) | efecto nulo bajo `min` en los Tests 2 y 3 | l. 41: sólo `diag_mu_dnti` y `diag_sd_dnti` (Test 2) | MÁS ESTRECHO (ya reconocido, control) | alta | n/a |
| B-01 | `docs/MIROVA_DIVERGENCES.md:1857-1900` D16 | `experiments/_s124_f70/04_tabla_brazos.py` | "la grilla UTM NO explica el sub-reporte", CERRADA, NO REABRIR | razón de magnitud **sólo VIIRS 375**, 61 días, n de 1 a 40 por volcán, grilla mal centrada (D17), sin bow tie | MÁS ESTRECHO | alta | **4** |
| B-04 | `docs/MIROVA_DIVERGENCES.md:1304-1313 y 1365-1370`; `CLAUDE.md` A82 | `experiments/_s114_audit/discriminant_sweep.py` | foco real y artefacto son "el mismo objeto en todos los ejes medibles", físicamente irreducible | predecir la etiqueta ALERTA de MIROVA en MODIS con **Láscar como único positivo** y escalares persistidos | MÁS ESTRECHO | alta | **4** |
| B-05 | `CLAUDE.md` A99; `docs/audit_s139/MAGNITUD_DESCOMPOSICION_OSF.md:187-188` | `experiments/_s139_audit/magnitud/04_fondo_y_test1.py` | a igual conteo la razón es 0,995, el déficit no es de fórmula ni calibración, "no volver a buscar en k, A, banda, Planck" | 0,995 = 1,14 × 0,873: dos factores opuestos que se compensan, en 343 pares de V375, 233 de un píxel | MÁS ESTRECHO | media | **3** |
| B-06 | `docs/MIROVA_DIVERGENCES.md:2194 y 2219-2222` D20 | ninguno (prosa en `docs/AUDIT_S128.md:654-659`) | banda 31 contra 32 "numéricamente despreciable", "en el dNTI se cancela" | se comparó contra el margen a K1 (0,14), no contra el piso C1 = 0,003 que gobierna MODIS; la cancelación no se midió | MÁS ESTRECHO | media | **3** |
| B-03 | `docs/MIROVA_DIVERGENCES.md:1440-1453`; `CLAUDE.md` A85 | `experiments/_s118_c2ab/analyze.py` | 0 robos de cluster en 214 noches focales: la selección anclada al vent es robusta | un record por noche (el de más píxeles, sensores mezclados); 214 incluye noches donde el robo es imposible por construcción; OCR congelado | MÁS ESTRECHO | media | **3** |
| B-08 | `CLAUDE.md` A83; `docs/AUDIT_S116_FOLLOWUP.md:5` | `experiments/_s116_followup/c2_discriminator.json` (sin `.py`) | ningún discriminante físico separa cat-b de artefacto, agotado | no hay script; el json declara que "artefacto" = no confirmado por MIROVA | NO CORRE (script ausente) | alta | **3** |
| B-09 | `CLAUDE.md:989-1000` A84 | `scratchpad/probe_ctx_cluster_s117.py` | `ctx_cluster` de Llaima y Lastarria indistinguibles, NO re-anclar | el archivo no existe en el repo | NO CORRE (script ausente) | alta | **3** |
| B-11 | `docs/HYPOTHESIS_LOG.md:1516-1525` S143 | `experiments/_s143_evaluador/evaluar.py` | no adoptar D22 ni D25 | lo mide bien y con alcance declarado, pero el criterio que lo tumba (5 pérdidas) fue declarado incapaz de decidir por su propio verificador | MIDE LO QUE DICE (cierre frágil por criterio) | media | **3** |
| B-02 | `docs/MIROVA_DIVERGENCES.md:1341-1358`; `CLAUDE.md:119` | `experiments/_s130_ab_sustrato/medir_sustrato_k1.py` | píxeles K1 (NTI > -0,8) en 0,09 % de MODIS: sustrato estructural, no repetir el A/B | cuenta `n_nti_path`, que es NTI > K1 **y además** `bt > t_bg + 3 K` | MÁS ESTRECHO (parcial) | alta en el hecho, baja en el tamaño | 2 |
| B-10 | `docs/MIROVA_DIVERGENCES.md:1704-1765` D14, registro S127 | `experiments/_s126_cloudmask/02_veredicto.py` | costo chico, "ningún volcán sale de banda" | magnitud en 2 volcanes con muestra (n = 8 y 35), sólo V375, 3 de 11 volcanes | MÁS ESTRECHO (leve, declarado en parte) | alta | 2 |
| B-13 | `docs/MIROVA_DIVERGENCES.md:2150-2156` D19 H1 | `experiments/_s135_probe_etapas/` | H1 refutada: `keep_peak` no descarta el cráter | una pasada (Villarrica 2026-07-01), asimétrico por diseño, declarado | MÁS ESTRECHO (declarado) | media | 2 |
| B-07 | `docs/HYPOTHESIS_LOG.md:716-727` | `pipeline/store.py:416-445` | CONFIRMADA y RESUELTA por la Regla D (recall 0,25 a 0,69) | hoy 0 de 16.149 records tienen `vrp_vent_mw > 0`: la regla no tiene sobre qué actuar | mecanismo sin sustrato hoy | alta | 1 |
| B-12 | `CLAUDE.md` A104 | `experiments/_s142_linea_base/linea_base_post535.py` | V375 62,1 % antes y 87,1 % después | el `RESULTADOS.md` persistido hoy dice 62,6 % de 358 y 86,5 % de 325 | salida persistida distinta del texto | alta | 1 |
| B-14 | `docs/MIROVA_DIVERGENCES.md:480-493` S116 Hilo 2 | json sin script | 0 FP contextuales residuales, A/B F2.1 no accionable | sin script; decide "cat-b real" por posición, que A83 declara incapaz de separar | NO CORRE (script ausente) | media | 2 |
| ok | `docs/MIROVA_DIVERGENCES.md:2067-2092` D18 | `experiments/_s130_d18/veredicto_d18.py` | A/B NO ADOPTAR, casi inerte | 6 volcanes, 88 días, sensores mezclados; el texto dice "los seis" | MIDE LO QUE DICE (sólo leído) | media | 2 |
| ok | `docs/MIROVA_DIVERGENCES.md:1249` S98 | `tests/test_detection_anchor.py` | ancla al cráter, guard anti revert | 10 tests pasan; mide función y config, el cableado lo verifiqué aparte | MIDE LO QUE DICE | alta | 1 |
| ok | `CLAUDE.md:119` | `tests/test_guard_gap_a_pool_musigma_s128.py` | GAP #A reabierto, con guard | 5 tests pasan | MIDE LO QUE DICE | alta | 1 |
| ok | `CLAUDE.md` A94 y A81 | `experiments/_s136/impacto_neto.py` | la etiqueta `far` cuesta 1 noche de 946 | hoy 4 ocultas de 973 (3 de NdC), 95,0 a 95,4 % | MIDE LO QUE DICE | alta | 2 |
| ok | `CLAUDE.md` A12, D5 | `scripts/libro_de_cuentas.py` | Láscar 16,9 K, Isluga 8,3 K, D5 0,73 | reproduce 16,9 / 8,3 / 0,741 | MIDE LO QUE DICE | alta | 1 |
| ok | `CLAUDE.md` A98 | `experiments/_s139_audit/eje2/banco_noches.py` | 874 de 877 noches | predicado del operador con node, controles, negativos limpios, ventana declarada | MIDE LO QUE DICE (sólo leído) | media | 2 |
| ok | `CLAUDE.md` A10 matiz | `experiments/_s131_audit/magnitud/04_display_f5_vs_pc.py` | 0,68 contra 0,58, coinciden en 5,7 %, 1.609 pares | el json persistido dice exactamente eso | MIDE LO QUE DICE (sólo leído) | media | 1 |
| ok | `CLAUDE.md` A90 | `experiments/_s130_a81/medir_far_summit.py` | tasa plana 15 a 17 % | json persistido: 15,1 a 17,2 % por mes. El "2.579" no sale de ningún script | MIDE LO QUE DICE (con una cifra a mano) | media | 1 |
| ok | `docs/HYPOTHESIS_LOG.md:736-743` H12 | `tests/test_detection_context.py:251` | kernel con media aritmética | test pasa, el código usa `_nanmean_ignore_self` | MIDE LO QUE DICE | alta | 1 |
| ok | `docs/MIROVA_DIVERGENCES.md` D19, S135 | `experiments/_s135_ab_d1d2/evaluar_ab.py` | ningún brazo cumple | sólo leí `RESULTADO_FINAL.md`; el brazo B cae por 0,016 de paridad, ya explicado por A100 | MIDE LO QUE DICE (sólo leído) | baja | 2 |

## 3. Los que caen, por gravedad, con la salida cruda

### B-01 (gravedad 4). D16: "la grilla UTM NO explica el sub-reporte", cerrada y con NO REABRIR

**El fenómeno.** MIROVA no trabaja sobre el barrido crudo del satélite: primero remuestrea la
escena a una malla de celdas iguales. Nosotros integramos sobre el píxel tal como viene, que se
estira hacia el borde de la pasada. D16 probó si imitar esa malla acercaba nuestra magnitud a la de
MIROVA y concluyó que no, con candado.

**Lo que el script mide.** Lo corrí y reproduce la tabla del catálogo:

```
volcan                  n   control         A         B         C
Lascar                 32     0.47      0.46      0.58      0.58
Isluga                 40     0.70*     0.69      0.81*     0.81*
Lastarria              27     0.36      0.34      0.34         --
Copahue                 1     1.02*     1.07*     1.07*     1.02*
NevadosDeChillan        2     1.31*     1.31*     1.31*     1.31*
PuyehueCordonCaulle    21     0.75*     0.64      0.64         --
```

Pero `04_tabla_brazos.py:38` filtra `Sensor == "VIIRS375"` y la línea 59 descarta MODIS y VIIRS 750,
aunque los brazos sí procesaron los tres sensores (conté en `data/_f70_a/Lascar.json`: MODIS 116,
VIIRS 217, VIIRS 750 212). La ventana es de 61 días de invierno (l. 18) y dos volcanes tienen n de
1 y 2. La grilla además se centró en el punto equivocado (D17, mismo catálogo) y no se trató el bow
tie de MODIS, que es justo el sensor cuyo remuestreo describe el paper.

**Por qué es grave.** El título generaliza a "la grilla UTM" y manda no reabrir, mientras la nota
S130 de D17 (`docs/MIROVA_DIVERGENCES.md:1922-1938`) dice lo contrario: que el mecanismo geométrico
**sí** quedó probado por el eje del ángulo y que el brazo fiel sería bow tie más remuestreo. Las dos
secciones conviven. Además D16 (l. 1893-1894) sigue afirmando "recall 96 a 96 %, 0 de 19 eventos
ancla perdidos", y `docs/S124_F70_VEREDICTO.md:97-99` reconoce que ningún script commiteado produce
esos números. Lo que el experimento respalda es más chico: *una malla de 375 m centrada en el
centroide, sin bow tie, no mejora la razón de VIIRS 375 en 61 días*.

### B-04 (gravedad 4). A82 y el cierre S114 de D11: "el mismo objeto en todos los ejes medibles"

**El fenómeno.** A 1 km de píxel, un foco pequeño real y una ladera tibia por altitud se parecen. El
cierre dice que se probó todo y que ningún número del record los separa, así que es físicamente
irreducible y no se reabre.

**Lo que el script mide.** `discriminant_sweep.py` corre hoy:

```
POS (Lascar far->summit, foco real): n=72
NEG (nevados RUTINA far->summit, A69): n=785
v375_coval_mag             0.888 ...  <== SEPARA
dT                         0.738 ...  ~ debil
diag_sigma_bg_k            0.640
...
diag_nti_max               0.508
```

Tres estrecheces, leídas en el código:

1. **La clase "foco real" es un solo volcán** (l. 79-80: `if x["vol"] == "Lascar"`). Clase y volcán
   quedan confundidos: cualquier cosa que distinga a Láscar del resto (altitud, desierto) se lee
   como poder de separación, y cualquier cosa que no, como "no separa focos".
2. **La clase "artefacto" es "MIROVA no publicó ALERTA MODIS esa noche"** (l. 78 y 81). La regla A54
   del mismo `CLAUDE.md` dice que cerca de la mitad de lo que MIROVA no publica es calor real. Un
   AUC de 0,5 es justo lo que se espera si la clase negativa está llena de focos reales. El script
   mide "predecir la etiqueta de MIROVA", no "real contra artefacto".
3. La lista `NEVADOS` (l. 28-29) incluye a Lastarria, Isluga, Planchón-Peteroa y Puyehue, que no son
   nevados. Y las variables son sólo los escalares que el record persiste, de a uno.

Para la misión (clonar a MIROVA) predecir su etiqueta es una pregunta legítima. Lo que no se sostiene
es la redacción física: "el mismo objeto", "su única diferencia no deja huella en el dato". A82 ya
fue rebajada dos veces (S124 por geometría, S138 por banda y compuerta); ésta es una tercera vía,
independiente: **el diseño de las clases**. A83 (B-08) hereda el mismo problema y además no tiene
script.

### B-05 (gravedad 3). A99: "a igual conteo la razón es 0,995"

**El fenómeno.** Nuestra magnitud queda en ~0,7 de la de MIROVA. S139 lo descompuso y concluyó que
el déficit es de cuántos píxeles se suman, no de la fórmula, y cerró con "no hay que volver a buscar
el déficit en k, en A, en la banda I04 ni en Planck".

**Lo que el script dice hoy** (`04_fondo_y_test1.py`, corrido):

```
igual conteo:
{'n': 342.0, 'R': 0.995, 'Fn': 1.0, 'Fhot': 1.14, 'Fbg': 0.873, ...}
```

El 0,995 es el **producto de dos factores opuestos**: nuestro nivel caliente queda 14 % arriba del de
MIROVA y nuestro fondo resta 13 % de más. El propio encabezado del script plantea la duda ("si F_ex
~1 ahí es porque ambos coinciden o porque se compensan") y la salida contesta: se compensan. La regla
A99 y el documento recogieron el 0,995 y no la compensación. El subconjunto es además angosto: sólo
VIIRS 375, clase 1 del OSF v2.5, 343 pares de 1.499, 233 de un solo píxel, con Villarrica en 8 pares
y Nevados de Chillán en 1 (contado sobre `02_pares.csv`).

Confianza media: que el factor 1,14 venga de la fórmula, del remuestreo o de la banda es SIN DATO.
Lo que sí está verificado es que "coincide por píxel" no es lo que el script muestra.

### B-06 (gravedad 3). D20: banda 31 en vez de 32, "numéricamente despreciable"

No hay script de S128; la cuantificación es una frase ("lo cuantifiqué con Planck"). La comparación
se hizo contra el margen al umbral K1 (~0,14). Pero el umbral que gobierna MODIS, según la propia
medición de S136 que reproduje hoy (`MODIS 12166 (100.0%)` manda el piso), es **C1 = 0,003** sobre el
dNTI. Y "en el dNTI se cancela porque es casi uniforme" está argumentado, no medido: el corrimiento
depende de la temperatura, y un píxel más tibio que sus vecinos no lo cancela.

`b03_d20_banda31_vs_32.py` (Planck isotermo; su control reproduce los 0,0001 y 0,0054 de S128):

```
T_vecinos  dT   dNTI_b31   dNTI_b32   diferencia   diferencia/C1(0.003)
      270   10    0.01995    0.02153    -0.00158      -0.53
      280   10    0.02437    0.02659    -0.00222      -0.74
      280   15    0.03831    0.04191    -0.00360      -1.20
```

Con gradientes de ladera de 10 a 15 K (los que A69 describe), la diferencia entre bandas es de la
mitad a más de un piso C1 entero. No prueba que cambie detecciones reales (eso es SIN DATO: pide
gránulos), pero "despreciable" se midió contra la vara equivocada. El catálogo dice que un A/B
"tendría que mostrar un efecto que el cálculo dice que no existe": ese cálculo no miró el umbral
que manda.

### B-03 (gravedad 3). A85 y el RESUELTO S118: "0 robos de cluster en 214 noches focales"

Sólo leído (los artefactos del run 28312968093 no están en disco, y el script escribe en `docs/`).
En `experiments/_s118_c2ab/analyze.py`:

- l. 112-123: se elige **un record por noche**, el de más píxeles, mezclando sensores, y por separado
  en cada brazo. Un robo en una pasada MODIS queda tapado si otra pasada de esa noche tiene un cúmulo
  más grande dentro del radio.
- l. 148-165: `n_nights` suma toda noche con record en la línea base, **aunque el cúmulo de la base
  ya estuviera fuera del radio** o el brazo no tenga record. En esas noches el robo no puede ocurrir
  por construcción, y cuentan dentro del 214. El denominador efectivo es SIN DATO: `results.json`
  sólo guarda `n_nights` y `n_steal`.
- l. 40: usa `data/mirova_reference/registro_vrp_ocr.csv`, el OCR congelado (`wc -l` hoy: 236 líneas
  contra 967 del snapshot vivo).

"0 de 214" puede ser cierto, pero el 214 no es el número de oportunidades de robo. A85 generaliza a
regla ("la selección anclada al vent es robusta") desde 5 volcanes y ventanas de 14 días alrededor
de alertas.

### B-08, B-09 y B-14 (gravedad 3, 3 y 2). Tres cierres cuyo script no existe

- **A83** ("no existe un discriminante físico, agotado"): el respaldo es
  `experiments/_s116_followup/c2_discriminator.json`. La carpeta tiene tres `.json` y ningún `.py`;
  el nombre sólo aparece en `docs/AUDIT_S116_FOLLOWUP.md:5`. El json declara su etiqueta:
  `'tp_label': 'ALERTA_TERMICA ... RUTINA/FP no cuentan'`, o sea el mismo diseño de clases de B-04.
- **A84** ("NO re-anclar `ctx_cluster`"): cita `scratchpad/probe_ctx_cluster_s117.py`. No existe:
  `ls scratchpad` falla, `find` y `git ls-files` no devuelven nada. La otra pata (A/B de S106) sólo
  la leí: descarta el brazo B con Llaima a 2.263 m y recall 1 de 1, y el criterio "offN a 0" del
  brazo ganador es cierto por construcción, porque el ancla se fija al vent.
- **S116 Hilo 2** ("0 FP contextuales residuales"): mismo json sin script, y decide "son cat-b real"
  por posición sobre el cráter, que es justo el eje que A69 y A84 dicen que el artefacto comparte.

Regla de esta auditoría: "verificado" no vale si el script no corre. Los tres vuelven a **SOSPECHA**.
No están refutados.

### B-11 (gravedad 3). S143: "no adoptar" D22 ni D25

El evaluador es el instrumento más cuidado que vi (procedencia por sha, cobertura pareja, negativos
limpios, verificador aparte) y su alcance está escrito: VIIRS 375, 9 volcanes, junio a agosto. No es
un caso de medición estrecha. Lo anoto porque el cierre es frágil por otra vía: el brazo literal baja
la publicación en negativos limpios de 0,917 a 0,547 y lleva la magnitud de 0,773 a 0,945, y cae sólo
por 5 "pérdidas" que el verificador (`VERIFICADOR_VEREDICTO.md`, H1) declara que **no son otro
objeto**. El repo lo sabe (A107; `docs/CIERRE_FRENTE_KEEP_PEAK_S144.md` §5.2 lo deja reabrible). El
riesgo es que en los resúmenes quede sólo "A/B D22/D25: NO ADOPTAR".

### B-02 (gravedad 2). El sustrato K1 del GAP #A

La copia del script corre y reproduce (el corpus creció desde S130):

```
MODIS          12181       11    0.09%
VIIRS750       23833       28    0.12%
VIIRS375       24023      320    1.33%
```

Lee `n_nti_path`, que el código define así (`pipeline/process_modis.py:662-668`, igual en los otros
dos procesadores):

```python
nti_path_hot = (roi_mask & ~np.isnan(nti) & ~np.isnan(bt_mir)
                & (nti > NTI_K1_NIGHT) & (bt_mir > (t_bg + NTI_BT_SANITY_K)))   # 3.0 K
```

No es "píxeles con NTI > -0,8" como dice el texto: es eso **y** la compuerta de 3 K, de la misma
familia que D22. Para la pregunta "¿el flag es inerte hoy?" el script mide exactamente lo correcto.
Para "acota el alcance del GAP #A contra el paper a menos del 0,1 %" y "el sustrato es estructural,
no repetir" es más estrecho. Cuánto más: SIN DATO. Mi expectativa física es que poco (de noche un
NTI sobre -0,8 casi siempre viene con un píxel bien sobre el fondo), y por eso gravedad 2.

### B-10, B-13, B-07, B-12 (gravedad 2, 2, 1, 1)

- **B-10, D14/S127.** La copia de `02_veredicto.py` reproduce todo (176 de 181 noches ciegas;
  `Villarrica 8 0.764 ✓ 0.832 ✓`, `Lascar 35 0.434 ✗ 0.501 ✗`, `NevadosDeChillan (muestra
  insuficiente)`). "Ningún volcán sale de banda" son dos volcanes, uno de los cuales ya estaba fuera
  en los dos brazos. El cierre de fondo (la cita del paper) no depende de esto.
- **B-13, D19 H1.** Refutada con una pasada. Está declarado en el texto; lo anoto por el n.
- **B-07, Regla D de S20.** "CONFIRMADA y RESUELTA" con recall 0,25 a 0,69. El código sigue en
  `pipeline/store.py:437`, pero el perfil corre con `vent_path=off` y medí `vrp_vent>0: 0` en
  Tupungatito (5.328 records), Chaitén (6.095) y Láscar (4.726). El problema que resolvía lo cubren
  hoy otros frentes (A46, A81); el cierre es histórico.
- **B-12, A104.** `CLAUDE.md` dice 62,1 % y 87,1 %. El `RESULTADOS.md` persistido dice hoy
  `VIIRS375 | antes_535_misma_longitud | 62,6 % de 358` y `despues_571 | 86,5 % de 325`
  (`tasks/BLOQUE_ARRANQUE_S143.md:16` citaba "87,1 % de 295"). La salida se regeneró con más datos.
  La conclusión no cambia. La comparación es temporal (agosto contra septiembre), no un A/B.

## 4. VERIFICADO LIMPIO

Esto se revisó y está bien. Que quede escrito, porque un informe que sólo lista defectos hace dudar
de lo que sí funciona.

- **Ningún script citado que intenté correr falló.** Los once corren hoy sobre el corpus actual y
  reproducen sus números dentro de lo que explica el crecimiento del corpus.
- **A12 corregida (Láscar 16,9 K, Isluga 8,3 K)**: reproduce, y aguanta el cambio de denominador
  (`b02_a12_delta_t.py`: sólo detecciones summit da Isluga 8,5 y Láscar 19,1). Isluga sigue bajo 12 K.
- **D5 = 0,73**: el libro de cuentas da 0,741 hoy. `flags_true` 28, coeficientes de Wooster y tabla
  de `inner_radius_km`: OK.
- **A94 y A81 (impacto neto de la etiqueta `far`)**: 4 noches ocultas de 973, 3 de Nevados de
  Chillán. La unidad (noche) está declarada y es la correcta.
- **A98 (banco de S139)**: usa el predicado del dashboard ejecutado con node, trae controles de todo
  y nada, negativos limpios y ventana. Es el estándar al que deberían subir los demás.
- **A10 matiz S132** y **A90**: las salidas persistidas dicen lo que el texto dice.
- **S98 ancla, guard del GAP #A, H12 kernel**: 16 tests corridos, 16 pasan, y miden lo que dicen.
- **D18**: el texto acota a "los seis" y el script estratifica por volcán y trae control de
  instrumento antes de leer.
- **El control positivo se redescubrió**: `b01_control_d26.py` da `V375 deti ... manda_sigma=7.4%` y
  `V750 deti ... manda_sigma=16.6%` en cumbre, igual que `docs/audit_s145/`.

## 5. Patrones, para el verificador

1. **Citas indirectas.** El cierre más famoso (D26) no nombra su script. Un censo por rutas no lo ve.
2. **Clases definidas por la etiqueta de MIROVA pero redactadas como física** (B-04, B-08, B-14).
   Es el patrón con más alcance: sostiene A82, A83, parte de A80 y el "agotado" de D11.
3. **Igualdad por compensación** (B-05): un cociente cerca de 1 no dice que los factores coincidan.
4. **La vara equivocada** (B-06): "despreciable" contra K1 cuando manda C1.
5. **Denominadores con casos imposibles adentro** (B-03).
6. **Respaldo que no está en el repo** (B-08, B-09, B-14): json sin script, script en `scratchpad/`.
7. **Un sensor, generalizado** (B-01, B-05, B-10): casi siempre VIIRS 375, casi siempre invierno 2026.

Límites de esta auditoría: 13 cierres sin tocar (tabla de cobertura); los A/B de CI sólo se leyeron;
B-05 y B-06 tienen confianza media porque mi contraste es aritmético y no sobre gránulos.
