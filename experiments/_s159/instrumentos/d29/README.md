# D-29 en el evaluador de D25 (sesión nocturna S160, 2026-10-22)

**Qué**: Nicolás selló el 2026-10-21 (D-29, `tasks/LOOP_OBJETIVOS.md` §5): «D25 se evalúa sin el 17 al 20 de octubre
ni el 13 parcial, declarados en el veredicto». Hasta `c44709e27` el evaluador no excluía ningún día: la ventana V1 iba
del 2026-08-29 al 2026-10-18 entera, y la cobertura comparaba los brazos contra producción, que sí tiene el 17 y el 18
(NRT de su momento). Sin la exclusión, V1 podía quedar INDECIDIBLE por cobertura o mezclar días con y sin datos.

**Cómo** (`experiments/_s157_prereg_d25/evaluar_d25.py`): `DIAS_EXCLUIDOS["V1"]` = 13, 17, 18, 19 y 20 de octubre
(el 19 y el 20 caen fuera de V1 y se listan para que la regla diga lo mismo que la decisión); `filtrar_dias` saca esas
fechas de las tablas K-brazo, de los crudos de cada brazo y de la referencia de cobertura; la cabecera de V1 y la
primera línea del veredicto combinado dicen «EVALUADO SIN ... (D-29)».

**Interpretación, a la vista de Nicolás**: «el 13 parcial» se excluye entero, en los tres brazos por igual. Excluir
pasada por pasada dependería de qué le faltó a cada brazo, y eso no es simétrico.

**Pruebas**: `tests/test_evaluar_d25_dias_d29_s160.py`, 5 de 5 rojas por aserción antes (`rojo_d29.txt`), 36 de 36
verdes con las del evaluador (`verde_d29.txt`). Mutaciones (`mutar_d29.py`, `mutaciones_d29.txt`): 4 de 4 atrapadas
por aserción (filtro que no filtra, cobertura sin filtrar, veredicto sin declarar, sin el 13). Control del instrumento:
la primera versión del lector daba 0 de 4 porque buscaba el tipo de excepción en el resumen de `pytest -q`, que no lo
trae; con el XML de JUnit da 4 de 4, y una copia sin mutar pasa 5 de 5. `probar_evaluar_d25.py`: 31 de 31
(`probar_evaluar_d25_salida_d29.txt`). Suite completa con el árbol quieto: 2.378 pasan, 29 omitidas, 1 xfail, 0 fallas
(`suite_d29.txt`; `git status` igual antes y después).

**Falta**: un verificador con contexto limpio de este cambio, junto con el de D-42 (calibración de P2), antes del tag
de lectura. No se leyó ningún dato real del A/B.
