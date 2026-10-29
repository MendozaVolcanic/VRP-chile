# Verificador limpio del sello de MOD-D fase 4 (MODIS): informe

Fecha del servidor: 2026-10-29. Verificador con contexto limpio (no leyó los informes `verificador/` previos del pre-registro; sólo el código, el pre-registro y las salidas commiteadas).

## Qué se verificó

- Commit: `314cec80922703edfdafa3ba803de4829e4730f4` (`git rev-parse HEAD`), rama `claude/s168-modd-f4-sello`.
- Carpeta: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\elated-bell-62d203\experiments\_s166_modd_f4\`.
- Mis scripts y salidas: `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\elated-bell-62d203\experiments\_s168\modd_f4_verificador\`.
- Árbol de `experiments/_s166_modd_f4/` sin cambios al final (`git status --short` sólo muestra `?? experiments/_s168/`).

## Qué corrí

| comando | salida |
|---|---|
| `sha256sum` de los 4 archivos | `c01e0824…` (evaluar_f4.py), `395f276e…` (probar), `98d8d65b…` (vacío), `180aa8a8…` (mutar): los cuatro coinciden con §13 |
| `python probar_evaluar_f4.py` (6 min) | `bateria_vs.txt`: 63 de 63 OK; las líneas OK/RESUMEN son idénticas a `probar_evaluar_f4_salida.txt` (diff vacío) |
| `python probar_evaluar_f4.py --modulo evaluar_vacio.py` | `vacio_vs.txt`: 63 FALLA ASERCION, 0 CAE; idéntica a `probar_evaluar_f4_contra_vacio_salida.txt` |
| `python mutar_evaluar_f4.py --solo M70,M82 --paralelo 1` (TMP y TEMP en `D:\vrp-trabajo\temporales\s168_verif`) | `mutar_solo_M70_M82_salida.txt`: IDENTIDAD VIVA, CONTROL_ROTA ROTA, CONTROL_CAIDA CAE (58 caen), M70 ATRAPADA por E53, M82 ATRAPADA por E58, código 0 |
| `vs_traza.py M70 E53` / `vs_traza.py M82 E58` | `vs_m70_E53.txt`, `vs_m82_E58.txt`: la causa original de cada falla |
| `vs_clasificador_mixto.py` | `vs_clasificador_mixto_salida.txt`: cómo clasifica el medidor una mutación que hace caer casi todo |
| `vs_adhoc.py` + `vs_adhoc_complemento.py` | `vs_adhoc_salida.txt`, `vs_adhoc_complemento_salida.txt`: 10 mutaciones propias de reglas y constantes que el medidor no muta, contra la batería entera (subconjunto más complemento) |

No corrí las 82 completas: no encontré razón concreta para dudar de la salida commiteada. Sí leí todas sus líneas: 82 de 82 ATRAPADA, y en ninguna línea hay escenarios que caigan (`caen: -` en las 82).

## VERIFICADO

**(d) Cuadre de §13 con los artefactos.** Batería 63 de 63 y vacío 63 de 63 por aserción, 0 caen: reproducidos hoy, salida idéntica a la commiteada. Las 82 líneas de mutación están en la salida commiteada, todas ATRAPADA con `caen: -`. Controles: identidad VIVA, caída CAE con 58 escenarios (reproducido), rota ROTA (reproducido). Los cuatro sha256 coinciden. §13 dice «salió con código 0»: coincide con mi corrida de `--solo` (rc=0). §13 y §13 bis no contienen guiones largos ni medios (`grep -c` da 0; los `.py` y `.txt` de la carpeta tampoco).

**(a) Arreglos de gravedad 3 existen en el código y tienen escenario y mutación que los vigilan** (todo ATRAPADA por aserción en la salida commiteada):

| hallazgo | dónde está en el código | escenario y mutación |
|---|---|---|
| VF4-01 | `evaluar_f4.py:438` (elegible exige no VETADO contra V), `:712` y `:677` (otra posición publica una protegida: DECIDE NICOLÁS) | E39, E40, E54, E57; M47, M48, M71, M74 |
| VF4-02 | `:476` (`n_pob == n_grillas_censo`, conjunto sale de la población); `main` no pasa otro total | E11, E41, E51, E55; M13, M49, M72 |
| VF4-03 | `:615` (`sin_medir`), `:642` (campo `k_difiere_de_guardado` debe ser bool) | E42, E51, E60; M50, M51, M67, M78 |
| VF4-04 | un escenario por regla (E43 a E49) | M55 a M66, todas con su escenario |
| N-01 | `:468` (selladas con grilla del censo) | E59; M76, M77 |
| N-02 | `mutar_evaluar_f4.py:187-192` (NO VALE y `sys.exit(1)`) | el código existe; el camino rojo no tiene prueba propia (ver VS-03) |

**(c) M82.** La mutación reemplaza `fallas.append(...)` por `pass` (`evaluar_f4.py:610`; el texto aparece exactamente una vez). Falla E58 por aserción pura: `vs_m82_E58.txt` muestra «sin publicación de K del runner en la sellada: rojo» con `__context__: None`, o sea sin excepción detrás. Es una mutación válida del defecto que §8.6 prohíbe (aceptar en silencio una sellada sin publicación de K del runner): ninguna otra rama la cubre, porque `control_k_produccion` sólo mira filas evaluables (`:643`) y las selladas no lo son.

**(b) E53 y M70.** E53 (`probar_evaluar_f4.py:792`) nunca convierte una falla en un pase: el evaluador sin mutar pasa E53, y si el evaluador real cayera con ValueError ahí, E53 falla, que es lo correcto. M70 sigue atrapada por la razón que dice el documento: `vs_m70_E53.txt` muestra `ValueError('math domain error')` del `math.log10(0)` de `chillan` (`evaluar_f4.py:343`).

## Hallazgos

Gravedad 3: **ninguno**.

| id | gravedad | hallazgo | evidencia | recomendación |
|---|---|---|---|---|
| VS-01 | 2 | El medidor clasifica ATRAPADA cualquier mutación con al menos un escenario que falla por aserción, aunque los demás caigan por excepción: `ATRAPADA` si código 1 y hay `fallan`; el código de la batería es 1 si hay alguna aserción, sin mirar las caídas. Con E53 atrapando `ValueError`, un evaluador que cae con `ValueError` en todo sale ATRAPADA con 58 caídas. Demostrado: el mismo CONTROL_CAIDA con `raise ValueError` sale **ATRAPADA** y con `raise RuntimeError` sale CAE. El control de caída sólo da CAE porque usa RuntimeError. En las 82 mutaciones commiteadas esto no ocurre (`caen: -` en todas), por eso no cambia la cifra, pero el instrumento no lo impide. | `mutar_evaluar_f4.py:~160` (mapa de clases), `probar_evaluar_f4.py:939` (`1 if asercion else 2`), `vs_clasificador_mixto_salida.txt` | Clasificar ATRAPADA sólo si `caen` está vacío; con caídas mezcladas, otra clase (`ATRAPADA_CON_CAIDAS`) que no cuente y se liste. Y un segundo control de caída con `ValueError`. |
| VS-02 | 2 | M70 es la única de las 82 que no se atrapa por aserción pura: el evaluador mutado cae con `ValueError` y E53 lo convierte en aserción. Con el criterio literal del dueño («no porque el evaluador mutado se caiga»), son 81 por aserción y 1 por caída reclasificada. No hay forma de atraparla distinto, porque la regla que M70 vigila (no caer con `log10(0)`) sólo tiene la caída como señal observable; y la falla es ruidosa, no un veredicto equivocado. Además `except (ValueError, ZeroDivisionError)` cubre todo `correr(...)`: cualquier otro `ValueError` del evaluador en ese escenario (numpy, `rng.choice`) también contaría como aserción, y nada en ese camino puede lanzar `ZeroDivisionError`. | `vs_m70_E53.txt` (`__context__: ValueError('math domain error')`), `probar_evaluar_f4.py:792` | Escribir en §13 «81 por aserción y 1 (M70) por caída convertida a propósito»; acotar el `except` a `ValueError` con mensaje `math domain error`. Decisión del dueño si acepta M70 así. |
| VS-03 | 2 | Un brazo del control del contador no tiene escenario: `no_pasan` (los 50 cúmulos inyectados tienen que publicar con el predicado). Mutación propia que lo borra (`A6`) queda VIVA con toda la batería. N02 no lo cubre porque con el predicado real los 50 sí publican. La mutación del N-02 (el medidor devuelve código 1 y NO VALE) tampoco tiene prueba que lo ejercite. | `vs_adhoc_complemento_salida.txt` línea A6; `evaluar_f4.py` `control_contador` (`not no_pasan`) | Escenario con un predicado que no publique el cúmulo inyectado y que espere INDECIDIBLE; una prueba de que el medidor sale con 1 si un control sale mal. |
| VS-04 | 1 | La constante `N_GRILLAS_CENSO = 5321` no está protegida: E41 y E51 usan mundos chicos y E51 sobrescribe la constante con `n`. Mutarla a 5322 (`A1`) queda VIVA. Una constante mal escrita daría INDECIDIBLE con la población real (falla ruidosa), no un veredicto equivocado. | `vs_adhoc_complemento_salida.txt` línea A1; `probar_evaluar_f4.py:733` | Una aserción `EV.N_GRILLAS_CENSO == 5321` en E41. |
| VS-05 | 1 | `control_posicion` acepta cero pasadas con alertados (`"OK" if n and not malas`): quitar `n` (`A3`) queda VIVA. En la corrida real n es grande. | `vs_adhoc_complemento_salida.txt` línea A3 | Escenario sin cúmulos que espere INDECIDIBLE. |
| VS-06 | 1 | Chillán: los empates (`db == dk`) se apartan de los pares, y el pre-registro no lo dice (§9 habla de «pares con las dos magnitudes»). Tratar los empates como pares (`A8`) queda VIVA. Chillán acompaña al veredicto, no entra. | `evaluar_f4.py:346`, `vs_adhoc_complemento_salida.txt` línea A8 | Una línea en §9 y un escenario. |
| VS-07 | 1 | Mutaciones propias A4 (`bool(con_grilla)` en la identidad) y A10 (`sin_pasada_nuestra_no_medida` en `rojo_solo_en_e`) quedan VIVAS, pero son casi equivalentes: sin `con_grilla` la fracción de «otro gránulo» da 1,0 y deja rojo igual, y sin la guarda de A10 el evaluador cae con TypeError (ruidoso). Se anotan para que nadie las crea atrapadas. | `vs_adhoc_complemento_salida.txt` líneas A4 y A10 | Ninguna. |
| VS-08 | 1 | `--traza` está leído en `probar_evaluar_f4.py` (`"--traza" in sys.argv`) pero argparse lo rechaza («unrecognized arguments», código 2): la opción es inalcanzable. | primera corrida de mi `vs_mutar_uno.py`: código 2 | Agregar `ap.add_argument("--traza", action="store_true")`. |

Mutaciones propias atrapadas, como contraste de que el instrumento sí muerde: A2 (quitar `distinto` de `control_k_produccion`) por E29, A5 (control del predicado siempre OK) por E19, A7 (quitar un externo requerido) por E33, A9 (la P1b contraria decide) por E08.

## SIN DATO

- Que las 82 mutaciones completas den hoy lo mismo: no se re-corrieron; se verificaron controles, M70, M82, la batería y el vacío.
- Las cifras de población del §4 y §5 (23 protegidas, 2 a 7 gránulos, 5.321 grillas): son datos del arnés y la población, que no existen todavía.
- El arnés, la identidad contra grillas, los externos, el humo y el HEAD de los días de E: pertenecen al candado del §11.
- Que con la corrida real se cumplan las predicciones del §10.

## Veredicto del verificador

Se puede sellar. No hay hallazgo de gravedad 3. Las condiciones del dueño se cumplen con una salvedad: M70 (VS-02) es atrapada por una caída convertida en aserción; si el dueño exige el criterio literal, el titular honesto es «81 de 82 por aserción pura». VS-01 y VS-03 son huecos de instrumento que conviene cerrar en el mismo commit o declarar, y ninguno cambia el veredicto con datos plausibles.
