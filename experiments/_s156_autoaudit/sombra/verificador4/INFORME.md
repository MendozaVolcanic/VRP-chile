# Verificador 4 (contexto limpio): decisiones c, d y e de la vigilancia de la sombra

Cambio revisado: `ecf87db6d..66171d296` en `D:\vrp-trabajo\worktrees\s156-sombra-verif` (sólo lectura, sin tocar).
Todos mis archivos están en `D:\vrp-trabajo\temporales\s156_sombra\verificador4\`. Copia para mutar:
`D:\vrp-trabajo\temporales\s156_sombra\verificador4\copia\` (git archive del commit, restaurada al terminar).

## Veredicto por afirmación

| Afirmación | Veredicto | Script y salida |
|---|---|---|
| E1. La cota SE se deriva bien | **CONFIRMADO en lo que decide, PARCIAL en el denominador** | `e1_minimas_fuera_del_denominador.py`; cálculos de Wilson en este informe |
| E2. (c), (d) y (e) fieles y sin efectos laterales | **PARCIAL** (tres efectos laterales, uno contra la letra de la regla) | `e2_casos_borde.py` → `e2_casos_borde_salida.txt` |
| E3. Corrida real VERDE, PCC juzgada, 60 retro, muy_bajo vacío, sin avisos | **CONFIRMADO** (idéntica al JSON del autor salvo `generated_utc`) | `e3\salida.txt`, `e3\sombra_latest.json` |
| E4. 62 de 62 por fallo de prueba | **CONFIRMADO** (las 62 por AssertionError, ninguna por caída); **7 de mis 15 nuevas sobreviven** | `mutar_v4.py`, `reclasificar.py` → `mutar_v4_reclasificado.txt` |

### E1, detalle

Caminos por los que podía estar mal y lo que medí:

1. **¿SE cambia los negativos?** No. `reglas_d9.SE.cambian` es sólo `{'pos->minima': 33}` en V1 y `{'pos->minima': 45}` en V2 (contra SN, que sí mueve `sin_info->neg_limpio`). Entonces pérdidas SE = suma SE menos negativos: 28 − 21 = **7** (V1) y 49 − 37 = **12** (V2). Exactas.
2. **¿C0 sigue en 0 pérdidas con SE (o sea, ¿sigue siendo diferencial?)** Sí: suma SE de C0 = 734 (V1) y 863 (V2), iguales a sus negativos publicados.
3. **¿Las 33 y 45 estaban todas en el denominador de Muy Bajo de la lectura A?** **No todas.** El contador `cambian` de `p2_tres_reglas` recorre todas las claves, sin el filtro de `suma_errores`:
   - **V1** (`excluir_snpp` activo): con la etiqueta original, K pierde 3 Muy Bajo «solo OCR de Suomi NPP» (total 40 contra decide 37); con SE, 1 (29 contra 28). Así que al menos **2 de las 33** estaban fuera del 194, y el denominador real es **≥ 163**, sólo con los JSON. Con la referencia congelada de V1, de las 33 mínimas nocturnas de VIIRS 375 de la ventana, 5 son solo OCR: el denominador queda entre **163 y 166** (supone que cada mínima de la referencia es una clave de la tabla; lo apoya que el conteo calza exacto, 33 = 33).
   - **V2** (`solo_tabla`, sin filtro Suomi NPP, pero `decide_sensor` exige VIIRS desde 2026-04-01): de las 45 mínimas de la referencia congelada de V2, **7 son de marzo** y no estaban en el 388. Denominador ≈ **350**, no 343 (mismo supuesto; 45 = 45).
   - Ninguna puede ser protegida (una pasada protegida no es mínima por construcción en `aplicar_regla_minimas`) ni de otro sensor (`SENSORES_MINIMA = ("VIIRS375",)`).
4. **¿El menor denominador es el lado conservador?** Sí: con k fijo, la cota superior de Wilson baja al crecer n. 7/161 da 0,0870; 7/163 da 0,0860; 7/166 da 0,0845. V2 (12/343 = 0,0601; 12/350 = 0,0590) no decide porque se toma la mayor. **La diferencia es despreciable y el texto de la regla («el menor posible, la cota más alta») es correcto.** Lo único inexacto es que la marca y el comentario dicen «entre 161 y 194»: el rango real es 163 a 166 en V1, y el de V2 nunca llega a 343.
5. Nota menor: el A/B de V1 excluye las Muy Bajo «solo OCR de Suomi NPP»; la vigilancia no. Es un desajuste de población chico y no cambia la cota.

### E2, detalle (salida de `e2_casos_borde.py`)

- **(d) formato de fecha.** `"2026-10-20 05:54"` y `"... 05:54:00"` se reconocen; `"2026-10-20T05:54"`, `"...T05:54:00Z"` y `"2026-10-20 5:54"` **no**, y tampoco una variante de nombre (`Puyehue-Cordon Caulle`, A14). Falla hacia el lado seguro (la pasada vuelve a disparar), pero **en silencio**: la salida no avisa que una entrada del archivo no calzó con ninguna pasada, y el workflow comentará el issue todos los días.
- **(d) persistencia.** Tres noches seguidas que la sombra publica y K calla dan persistencia; si la primera está juzgada, **la persistencia desaparece** (`[]`). La juzgada sale de `vivas`, y con ello de la persistencia, del (i) y del retrospectivo, no sólo de la reversión. La decisión dice «no vuelven a disparar», no «dejan de existir para los demás disparadores».
- **(d) retrospectivo.** Con la juzgada, el retrospectivo baja de 2 a 1 pasadas y de 2 a 1 protegidas vistas. En la corrida real: **247 → 246 pasadas y 61 → 60 protegidas vistas** (comparado contra `sombra_latest_2026-10-19_lectura_decidida.json`). O sea, el «60» de E3 es un subconteo de lo que la sombra vio, y es incoherente con la duración, donde la juzgada sí cuenta.
- **(e) la candidata número 29.** 28 protegidas vistas y la 29.ª es candidata: `vistas 29, cumplida True, CANDIDATA_FUERA_DE_PLAZO`. La regla (§4, «hasta ver 29 protegidas A nocturnas») incluye la 29.ª en la vigilancia, así que esa pasada debería estar pre-autorizada. Igual con 20 vistas antes da `REVERSION_CANDIDATA`.
- **(e) plazo por fecha de corrida.** Una candidata del 2027-02-14 (día 119) da `REVERSION_CANDIDATA` si se evalúa ese día y `CANDIDATA_FUERA_DE_PLAZO` si se evalúa el 2027-02-16 (OCR atrasado, workflow caído). El plazo se juzga con `hoy` y con el total de vistas, no con la fecha y el orden de la pasada. Consecuencia adicional: una candidata en plazo que nadie anotó como juzgada cambia de clase cuando vence el plazo y abre un segundo issue, con otro prefijo, por la misma pasada.
- **(e) juzgada posterior con plazo cumplido:** VERDE, cuenta para la duración (29, cumplida). Correcto.
- **Deduplicación de títulos.** Ningún prefijo de clase es prefijo del título de otra (`e2` punto 7). Correcto. El `simular_issue.py` del autor no prueba esto: su `gh` falso devuelve `FAKE_NUM` sin mirar el prefijo.
- `imprimir` y el cuerpo del issue de fuera de plazo siguen rotulando la pasada como «REVERSIÓN CANDIDATA ... Confirmar en la cabecera ... antes de revertir». Cosmético, pero contradice el título en el caso en que justamente no hay pre-autorización.

### E3, detalle

`correr_sombra.py` con la referencia del 2026-10-19: rc 0, `VERDE`, avisos `[]`, `muy_bajo {}`, duración 0 de 29 (vence 2027-02-15), retrospectivo 60 protegidas vistas y 0 pérdidas, PCC VIIRS 750 2026-10-10 05:54 como «ya juzgada». Las 19 claves coinciden con `sombra_latest_2026-10-19_final.json` salvo `generated_utc`.

### E4, detalle

- El criterio del autor (`returncode == 1` y «failed» sin «error») **no distingue** una prueba que falla por aserción de una que falla porque el script lanza una excepción. Reclasifiqué leyendo el tipo de la última línea de cada traceback en el junit: **las 62 son AssertionError**. Confirmado.
- Mis 15 mutaciones sobre las líneas cambiadas (y el workflow): **8 atrapadas, 7 sobreviven**:
  - `V4_vistas_cuenta_no_protegidas` (la duración cuenta Muy Bajo): el plazo se cumpliría antes y la pre-autorización caería antes. **Ninguna prueba lo ve.**
  - `V4_fuera_de_plazo_sin_reversion` (`if duracion["cumplida"]` sin exigir reversión): pasado el plazo, cada VERDE sale como candidata fuera de plazo y abre issue. Ninguna prueba cubre «plazo cumplido sin candidata».
  - `V4_plazo_29_estricto` (`> 29`): no hay prueba en el borde de 29.
  - `V4_juzgadas_clave_sin_sensor`: una juzgada de VIIRS 750 silenciaría la misma hora en otro sensor.
  - Tres del workflow: quitar el issue de fuera de plazo, ponerle el prefijo de la reversión (se comentaría en el issue de reversión) o decir que «hay reversión pre-autorizada». La única prueba (`test_el_workflow_tiene_el_issue_de_fuera_de_plazo`) busca dos cadenas y la segunda también está en la rama de reversión.
  - `V4_leer_juzgadas_siempre_vacio` cuenta como atrapada (1 falla por aserción) aunque además provoca un KeyError en otra prueba.

## Hallazgos propios, por gravedad

1. **MEDIA (contra la letra de la regla).** El plazo de (e) se evalúa con la fecha de la corrida y el total de vistas, no por pasada: la protegida número 29, si es candidata, sale fuera de plazo, y una candidata del día 119 vista el día 121 también. Arreglo simple: una candidata está en plazo si su `instante_utc` es anterior a `vence` y hay menos de 29 protegidas vistas ANTES de ella. Agregar las pruebas del borde (29.ª y día 119/121).
2. **MEDIA.** Una pasada juzgada sale de la persistencia, del (i) y del retrospectivo, no sólo de la reversión: rompe una racha de tres noches (oculta un INVESTIGAR) y deja el retrospectivo en 60 cuando la sombra vio 61. Recomiendo excluirla sólo de `reversion` (y de la lista de pérdidas protegidas del retrospectivo) o decir explícitamente en la regla que sale de todo.
3. **MEDIA (afirmación falsa en el README).** `experiments/_s156_autoaudit/sombra/README.md` dice que la falsa alarma de (i) con evaluación diaria «quedó resuelto por la decisión (c)». No: Wilson inferior de 1 de 1 es 0,2065 y de 1 de 2 es 0,0945, las dos sobre la cota nueva 0,0870 (más baja que la vieja, 0,1298). Monte Carlo con las tasas de Muy Bajo por volcán medidas en la sombra (2026-10-02 a 10-18) y K perdiendo como en el A/B: **P(algún INVESTIGAR por (i) en 120 días) = 0,58** con la regla nueva, contra 0,68 con la vieja (`falsa_alarma_muy_bajo.py` → `falsa_alarma_muy_bajo_salida.txt`; supone independencia y tasa constante). La decisión (c) arregla la coherencia con D-9, no la falsa alarma.
4. **BAJA.** Entradas del archivo de juzgadas con «T», con hora sin cero o con una variante de nombre no calzan y no hay aviso. Recomiendo normalizar la fecha al leer y avisar por cada entrada que no calzó con ninguna pasada de la ventana.
5. **BAJA.** Docstring obsoleto en `pasadas_de_alerta` (`scripts/vigilancia_sombra.py:136-137`): «Sí cuenta en el disparador (i), porque la cota del A/B se midió con la etiqueta original». Contradice (c) y el código (`p["minima"]` se excluye en la línea 243). Es texto sin marcar (A113).
6. **BAJA.** Rango del denominador citado («161 a 194», «343 a 388») más ancho que el real (163 a 166 en V1; ≈350 en V2). No cambia la cota que decide.
7. **BAJA.** Rótulo «REVERSIÓN CANDIDATA ... antes de revertir» en `imprimir` y en el cuerpo del issue de fuera de plazo.
8. **BAJA (pruebas).** 7 mutaciones sobrevivientes (E4), y el criterio de `mutar_vigilancia.py` no separa aserción de caída.

## ¿Impide mergear?

Nada de esto produce una reversión indebida ni deja ciega la vigilancia hoy (la corrida real es correcta). El hallazgo 1 sí contradice la regla pre-registrada en el caso borde, y conviene arreglarlo y probarlo antes de mergear, o que Nicolás diga explícitamente que el plazo se mide al día de la corrida. Los hallazgos 2 y 3 piden, como mínimo, corregir el README y decidir el alcance de «juzgada».
