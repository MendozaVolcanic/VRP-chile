# A/B de la caja de 5 × 5 km, brazo G: lectura PRELIMINAR (S148)

> ⚠️ **ESTO NO ES EL VEREDICTO.** El run **35548604513** terminó con 22 de 22 reprocesos en verde,
> pero la cobertura de la ventana completa salió despareja por el mismo corte de NASA del 18 al 20
> de septiembre (A64): al brazo G le faltan 23 pasadas de Copahue, al brazo H 23 de Planchón
> Peteroa y 37 de Puyehue Cordón Caulle, y al control B las 71 que ya se sabían. Regla
> pre-registrada: INDECIDIBLE hasta reparar. Reparaciones despachadas: run **35558196104**
> (control B) y run **35572961810** (brazos G y H, mismo código del pipeline que el run original,
> comprobado con `git diff` sobre `pipeline/`, `scripts/run_pipeline.py` y `volcanoes.yaml`).
>
> Lo de abajo es una lectura sobre el tramo donde la cobertura es **exacta** (2026-09-01 a
> 2026-09-17, 2022 pasadas contra 2022). **El brazo H no se pudo leer ni en ese tramo**: le
> faltan 13 pasadas dentro de él, y el instrumento se niega a leer sin cobertura exacta.

## 1. El fenómeno que se quería medir

MIROVA mira con ojo permisivo sólo una caja de 5 × 5 km sobre la cumbre, y con ojo estricto todo
el resto de la escena. La réplica mira con ojo permisivo un círculo que va de 3 a 20 km según el
volcán. En la corona que sobra, la réplica deja pasar píxeles apenas tibios que MIROVA le exigiría
el doble para alertar. La hipótesis era que ahí vive parte de lo que publicamos donde MIROVA
calla. S130 la había cerrado como "redistribuye, no recorta", pero la midió con el Test 1
integrado encendido, que publica por su cuenta y satura la métrica (A114). Por eso se repitió
sin el Test 1.

## 2. Lo medido: la caja no apaga nada de lo que se publica

Instrumentos: `experiments/_s147_lectura/lectura_por_tramo.py` (tasas) y
`experiments/_s148_caja/lectura_caja.py` (Q1 a Q4, nuevo). Salida cruda:
`experiments/_s148_caja/preliminar_caja_salida.txt`.

VIIRS 375, brazo G (caja, conectiva de fórmula) contra el control B:

| predicción | qué decía | lo medido en el tramo |
|---|---|---|
| **Q1** | de los negativos limpios publicados **fuera** de la caja, se apaga la mitad o más | **0 de 51** |
| **Q2** (control interno) | los de **dentro** de la caja cambian 5 o menos | **0 de 44** |
| **Q3** | los positivos de fuera de la caja sobreviven en 85 % o más | **sin sustrato**: 0 de 125 positivos publicados caen fuera de la caja (ver §4) |
| **Q4** | el recall por pasada aguanta | 125 de 129 en los dos brazos |

Las siete filas de la tabla de tasas (negativos limpios, nadir, medio, borde, borde con fondo
frío, recall, razón borde sobre nadir) salen **idénticas** entre G y B, y lo mismo pasa en
VIIRS 750 (30 de 562) y en MODIS (34 de 385).

**Un cero así se mide antes de creerlo (A116), y este se sostiene:**

- **El flag sí actúa.** Leído desde `pipeline.profile` con el perfil del brazo,
  `ENABLE_ROI1_BOX_PAPER` vale True. Y los records cambian: `diag_n_dnti_ctx_path` difiere en 605
  de 2022, `diag_n_first_pass_pixels` en 274, `anomaly_pixels` en 164. La caja mueve la
  detección; lo que no mueve es la decisión de publicar, en ninguna de las 2022 pasadas.
- **El instrumento puede dar distinto de cero sobre estos mismos datos.** Corrido con el brazo F
  (la conectiva) como control positivo: apaga **51 de 51** negativos de fuera de la caja y 34 de
  44 de dentro. Corrido con el control contra sí mismo: cero en todas las filas.

## 3. Lectura física

El pre-registro había declarado las dos salidas posibles, y salió la segunda: *"Si en cambio
sobreviven, es que pasan por la rama del sigma, y entonces la palanca es la conectiva y no la
caja."* Los mismos 51 negativos que la caja no toca, la conectiva de prosa los apaga todos.

**El mecanismo de por qué sobreviven queda SIN VERIFICAR, y mi primera explicación no se
sostuvo.** Supuse que de noche el umbral adaptativo quedaba por debajo del piso aun con el
multiplicador estricto, de modo que subir el piso no cambiaba nada. Medido sobre los 1618 pares
de media y sigma que los records del brazo G persisten en VIIRS 375 (`diag_mu_dnti`,
`diag_sd_dnti`, `diag_mu_deti`, `diag_sd_deti`), el adaptativo estricto (media más 10 sigmas)
queda bajo el piso de 0,010 en sólo **556 de 1618**; en el resto el que gobierna bajo `min` es el
piso, así que subirlo de 0,003 a 0,010 **debería** haber apagado píxeles con exceso chico. Que no
apague ninguna publicación deja tres caminos abiertos, ninguno medido: (a) esos píxeles tienen un
exceso mayor que 0,010, contra la pista del pre-registro (mediana de +0,31 K); (b) publican por el
segundo pase, que corre sin condicionar (ver `docs/audit_s148/MEDICION_H2_H3_CONECTIVA.md`) y
habría que ver si respeta la caja; (c) la caja se aplica a un test y no al otro. Hay que trazarlo
en el código (A6) antes de escribir que "la caja es inerte" como propiedad del método y no sólo
como resultado de este A/B.

Consecuencia para la propuesta de réplica literal: **con `min`, en este tramo la caja no cambia
nada de lo que el operador ve, también sin el Test 1.** Falta saber si es una propiedad del
método o un defecto del cableado (el párrafo anterior). Si la caja aporta algo junto con `max`,
lo dirá el brazo H cuando tenga cobertura.

## 4. Una discrepancia con el pre-registro que queda abierta

El pre-registro de la caja (§2) cuenta, sobre el run 35521542153, 43 de 135 positivos y 63 de 105
negativos con el cúmulo **fuera** de la caja. El instrumento nuevo da **0 de 125** positivos y 51
de 95 negativos sobre este tramo. El lado de los negativos es compatible (ventana más corta). El
de los positivos no: acá los positivos publicados están pegados al cráter (mediana de la
distancia del cúmulo por volcán entre 0,12 y 1,17 km; Puyehue Cordón Caulle 0,22 km). No encontré
el script que produjo el "43 de 135", así que no sé qué posición ni qué centro usó.
**SIN VERIFICAR**: puede ser otra definición de posición (píxel más caliente, no centroide del
cúmulo), otro centro, u otra población. No cambia la lectura de Q1 y Q2, pero deja a Q3 sin
sustrato, y hay que resolverlo antes del veredicto.

## 5. Lo que falta

- La ventana completa con los tres brazos reparados, y el evaluador completo.
- El brazo H, que es el único donde la caja puede mostrar efecto.
- Resolver la discrepancia del §4.
- Un verificador con contexto limpio sobre `lectura_caja.py` antes de usarlo para el veredicto.
