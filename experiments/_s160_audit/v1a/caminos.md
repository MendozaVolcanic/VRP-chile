# caminos.md: por donde podria estar mal cada afirmacion (escrito antes de abrir archivos citados)

## 161 (placebo t1off da CUMPLE)
1. El placebo no es inerte: apagar triggered_test1 SI cambia lo que publica el tablero (deja de pasar por isSummitDetection), o sea es un cambio de detector real (equivalente a quitar el Test 1), no un placebo. Si K consiste justamente en quitar el Test 1, el "placebo" es K-light y que cumpla puede ser legitimo.
2. El instrumento del auditor (medir_k2.py) no reproduce evaluar_fk.py: arma el brazo de otra forma (otra union, otra produccion, otro ruido), y el CUMPLE sale de su armado, no de la regla.
3. La tolerancia de P2 no es 0 en la regla sellada (REGLA_ADOPCION.md la fija distinta) o el ruido se toma de un gemelo distinto del que usaron en S153.
4. El CUMPLE del placebo depende de la referencia (tabla vs combinado) o de la ventana (V1 vs V2).
5. La segunda mitad ("K real supera ese margen por mucho") puede estar mal: el margen de K contra el placebo se mide en otra metrica que la de la regla, o K y el placebo coinciden en casi todo.
6. La linea frontend/index.html:1612 puede no ser la del commit d516b9d8c, o el predicado lee triggered_test1 sólo en una rama que no aplica a VIIRS375.
7. La "huella que obliga al disfraz" (evaluar_fk.py:502-503) puede ser un chequeo que el placebo del auditor elude modificando otros campos, y entonces el placebo no es "solo una bandera".

## 162 (veredicto cambia con la referencia)
1. La regla declara de antemano que decide la tabla sola en V2 (fijado por ventana), y el combinado sólo se informa: entonces "cambia" no es defecto de la regla sino lectura secundaria; el defecto real seria que la repeticion exigida no se corrio.
2. La alerta Lastarria 2026-04-18 04:42 de 1,29 MW sólo OCR puede ser una alerta OCR con imagen de otra pasada (reference_ocr_imagen_de_otra_pasada) o de distancia dudosa: no deberia contar como protegida.
3. El estado PENDIENTE DE REPETICION puede venir de un parametro --ruido-de equivocado del auditor.
4. La fecha 2026-04-18 cae antes de 2026-06-13 (A119): la regla puede excluir el OCR por calidad en esa ventana, y el auditor forzo --solo-tabla no contra lo preregistrado.

## 163 (datos de la adopcion no estan en el repo)
1. La union evaluada puede estar en otra rama o en el README con hash, o en un artefacto de otro run.
2. El intento 2 puede estar en otra rama (s146-ab/<otro run>) que el auditor no busco.
3. "reproduce v1.json" puede ser coincidencia parcial (mismo veredicto, distintos numeros).
4. El artefacto puede vencer en otra fecha.

## Celdas FALLA R6, R11 (evaluar_fk), R17 (predicado)
- Hay que leer que piden R6, R11, R17 en el plan §3/§11 y comprobar con medicion propia; la falla puede ser de interpretacion de la fila.
- El predicado puede estar bien (lee triggered_test1 por diseño) y la FALLA ser del uso en el evaluador.

---
sha256 del contenido anterior: 6dfb9c71c2d88095c652211f32298a542ba8482329f5d05a2e820eed3006fbde ; hora servidor (date -u) Thu Oct 22 03:48:40 UTC 2026. No se edita mas.
