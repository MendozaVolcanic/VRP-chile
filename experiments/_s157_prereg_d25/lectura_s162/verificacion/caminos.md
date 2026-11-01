# Caminos por los que la lectura de D25 (lectura_s162/README.md) podría estar mal

Escrito ANTES de releer el README, el evaluador o las salidas. Hora del servidor: Sat, 24 Oct 2026 13:22:00 GMT.
Worktree: C:\vrp-trabajo\s159-evaluador, HEAD e634f819f, tag s161-d25-lectura apunta a a7418e01d.

## (g) Evaluador y artefactos

1. El evaluar_d25.py del worktree (HEAD e634f819f) no es byte a byte el del tag a7418e01d (sha256 distinto al declarado).
2. El evaluador importa módulos auxiliares (scripts/, banco_paridad, clase_mirova, etc.) que SÍ cambiaron entre el tag y el HEAD, o que viven en main y no en la rama; el sha256 de un solo archivo no cubre eso.
3. Los artefactos bajados en scratchpad\d25\{V1,V2a,V2b,S17} no corresponden a los run id declarados (otro intento, otro run, otra ventana de fechas). Verificar run id, intento, fechas de los records dentro de los JSON y el nombre del artefacto.
4. V1 = "intento 2 del run 39530508296": el intento 1 puede haber dejado artefactos con el mismo nombre; que se haya bajado el del intento 1.
5. Los tres perfiles (control, gemelo, on) de un mismo brazo no cubren las mismas pasadas (cobertura dispareja, A108): un brazo con pasadas de menos infla o desinfla el neto.
6. Los perfiles del artefacto son de un commit del pipeline distinto al que el pre-registro fija (tag de despacho).

## (a) Veredicto combinado DECIDE NICOLÁS

7. La tabla del §8 d del PREREGISTRO tiene una fila que, con los resultados declarados (P1 CUMPLE, P2 BLOQUEA en un estrato, M MEJORA en un estrato), lleva a CUMPLE o NO CUMPLE y el lector la saltó.
8. El lector aplicó la tabla del §8 d de la versión original y una adenda la modificó (ADENDA_SIGNOS_P2, ADENDA_CALIBRACION_P2, NOTA_D46, NOTA_D47) o viceversa.
9. El combinador de veredictos del evaluador (código) no coincide con la tabla sellada (el código decide una cosa y el texto otra).
10. "Ninguna fila lleva a CUMPLE ni NO CUMPLE" depende de qué estratos "deciden"; si la definición de estrato que decide (NOTA_ESTRATO_203?) está mal aplicada, cambia la fila.

## (b) P1 CUMPLE en V1 y V2, P1b dos protegidas de Chillán

11. P1 se evaluó contra la lista de protegidas de la ventana equivocada (la lista de V1 usada en V2 o al revés).
12. P1 sólo mira pasadas con alerta de 1 MW o más del scraper; si el umbral de "protegida" o la lectura (A vs B) cambió por adenda, el conteo cambia.
13. P1b: "dos protegidas que cruzan 1 MW hacia abajo" puede ser una lista del gemelo y no del brazo on, o contar cruces en las dos direcciones, o depender del redondeo exacto en 1,00 MW.
14. El P1 del evaluador no tiene control positivo: si la lista de protegidas estuviera vacía por un bug del loader (nombres de volcán con variantes A14, Nevados de Chillán con espacios), P1 daría CUMPLE trivialmente.
15. V2 es V2a + V2b: si las dos mitades se solaparon o dejaron un hueco de días, P1 en V2 está sobre un universo distinto al pre-registrado.

## (c) P2 BLOQUEA en V1 VIIRS 750 (neto +6, 26 noches) y V2 VIIRS 375 sólo con SN (neto +1)

16. P2 por prueba de signos por bloque (D-45): el umbral por celda 0,67 y la agrupación por bloque pueden aplicarse con otro tamaño de bloque del sellado.
17. "neto +6 en 26 noches": el signo del neto (a favor de on o en contra) puede estar invertido en el texto respecto al JSON.
18. La regla SN (alerta VIIRS 375 de 0,05 MW o menos cuenta como "no vio nada") y la original se pueden haber intercambiado en la lectura de V2 (SN decide, original informa; el README dice "sólo con SN").
19. La calibración "simetrica" pasada por línea de comandos puede no ser la que el sellado manda para P2 (ADENDA_CALIBRACION_P2).
20. P2 en V2 VIIRS 375: con V2a y V2b separados el neto puede cambiar según se sumen bloques o se evalúen aparte.
21. El resultado de P2 depende de qué estrato de cenit se usa (NOTA_ESTRATO_203: ≤40°, 40 a 60, todo); la lectura puede mezclar.

## (d) M MEJORA sólo en V1 VIIRS 750 cenit ≤ 40°; NEUTRO en los demás porque d mejora y d′ no

22. d y d′ (distancia del cúmulo y distancia alternativa) pueden estar definidas con anclas distintas (A93, A107: radio escalar no identifica el objeto) y el texto puede haber invertido cuál mejora.
23. La regla de M (las dos tienen que mejorar para MEJORA) puede estar en el código con OR y no con AND, o al revés que el sellado.
24. "Los demás estratos que deciden" puede incluir estratos sin sustrato que el código marca INDECIDIBLE y el texto llama NEUTRO.

## (e) Tabla sola en V1 da el mismo veredicto; el envoltorio sólo cambia VENTANAS

25. v1_solo_tabla.py cambia algo más que VENTANAS (parchea una función, un flag, la ruta de los CSV, la regla SN).
26. "Mismo veredicto" puede ser mismo veredicto combinado pero con filas de la tabla distintas (P2 pasa de BLOQUEA a otra cosa y el combinado no se mueve).
27. VENTANAS en memoria puede no ser lo que el evaluador consulta (lo lee de un archivo o lo reconstruye dentro de una función), y el envoltorio no tiene efecto: el "mismo veredicto" sería un no-op (A116).

## (f) Brazo 17 a 19 de octubre INDECIDIBLE; s17_sensibilidad.py sólo vacía la exclusión de D-29

28. El envoltorio toca además las fechas, el tmp, los nombres de perfil o la calibración.
29. INDECIDIBLE puede salir de un error (archivo faltante, perfil vacío) y no de la regla de sustrato mínimo (SIN DATO ≠ INDECIDIBLE).
30. Vaciar la exclusión de D-29 cambia el universo de las otras ventanas si el envoltorio se usara con V1/V2 (no aplica si sólo se usa con S17, verificar).

## Generales

31. Las salidas en lectura_s162\salidas\ no son las que produjo el comando que el README declara (otro --calibracion, otro --tmp con caché vieja).
32. El evaluador es no determinista (argsort, A/B con empates, A152): dos corridas iguales dan JSON distintos; una diferencia bit a bit no sería error de la lectura.
33. Los JSON de salida tienen hora o ruta embebida; la comparación bit a bit tiene que ignorar eso y decirlo.
34. El README cita números (26 noches, +6, +1, 2 protegidas) que no salen de ningún script sino de una lectura manual (A91 / integridad de números).
35. Caché del evaluador en --tmp: una corrida en un tmp previo con artefactos viejos puede haber dejado parquet/pickle que el evaluador reutiliza.
