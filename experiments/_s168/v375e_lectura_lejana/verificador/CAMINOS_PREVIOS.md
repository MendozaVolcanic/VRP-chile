# Caminos previos (escritos antes de abrir lectura_salida.txt ni lectura.json)

Hora de servidor: ver cabecera del INFORME. Escrito tras leer solo el pre-registro (PREREGISTRO_E.md completo) y los metadatos de la corrida (hora_inicio.txt, exit.txt).

1. Procedencia: la lectura corrio sobre el arbol de trabajo, no sobre el tag; el worktree podia tener cambios sin commitear o el commit 7a548be11 podia diferir del tag en codigo (diff tag..HEAD en experiments/_s162_v375, scripts, pipeline, frontend, volcanoes.yaml, tests).
2. Dependencias fuera del repo: los cuatro artefactos de run (D:/C:) no estan versionados; pudieron cambiar entre la lectura y la mia (se comparan sha).
3. Azar sin semilla: la prueba de signos usa 10.000 sorteos con semilla 162 solo si >20 bloques; el remuestreo por bloque de evaluador_comun y los IC de curva_cenit pueden usar semillas distintas o ninguna.
4. Salida 0 con C3 caido o con un control en 0 de 0 (VA168-01, VA168-07): C8 podria pasar vacio.
5. Veto y marca N-3: que la lista de protegidas que no vetan (OCR SNPP antes de 2026-10-09) este bien aplicada; que una protegida "comun" (la callan los tres brazos) se mezcle con la que depende de la posicion.
6. Marca A104 del paso 6: que tramos cuentan (T, O1, O2; un tramo sin pasadas no cuenta); una discordancia en T (no solo O1/O2) podria o no disparar la marca; el texto dice "O1 u O2".
7. Pesos: alerta bajo 1 MW pesa ~5, negativo limpio ~2; el error de posicion cuenta protegida sin publicar, bajo 1 MW sin publicar, publicacion en negativo limpio, publicacion en far_tabla; "P1 que veta" vs "P1 de evaluar.py".
8. M (9.5): pares con magnitud >0 en ambos; modo "decide" solo sobre la union; A104 de M compara estado de (c) CUMPLE vs NO CUMPLE, no veredicto crudo (VA168-04), pero 9.5 dice "otro estado de (c)" ambiguo.
9. Tabla 9.7: filas de la RP no previstas (p.ej. SE QUEDA RADIANTE con marca A104, ELEGIDO con A104 y criterio que no cumple, DECIDE NICOLAS combinado con NO CUMPLE de otro criterio); y que (d) informa pero "falta la sombra".
10. Equivalencia: salida 4 vs 0; la cifra con vara vieja; pasadas FAR con 'sin matlab' usan regla independiente.
11. Interpretacion posterior: cualquier frase final del tipo "el paquete cumple/no cumple" que requiera una regla no escrita (p.ej. que hacer cuando el brazo elegido es radiante pero pierde protegidas en (a) por perdidas comunes que no son N-3; o como se combina el estado de la retrospectiva con la sombra futura; o que una `far_tabla` SIN DATO < 10% pero > 0).
