# Caminos previos (verificador 2; escritos antes de comparar nada con el INFORME del lector)

Partí de los 12 de `s167_diurno_verif\CAMINOS_PREVIOS.md` y agrego los míos (13 a 22).

1. Referencia congelada distinta de la sellada (sha256 de los 4 CSV vs `sustrato_k.json`).
2. Versión equivocada de `objetivos_adenda1_sha256.txt` (la de 4b86059 apunta a 038c6904b; la vigente es la de af5af6a17).
3. Ventana W2..W6 faltante, duplicada o mezclada entre runs; commit de salidas equivocado.
4. Días excluidos por cortes de NASA: ¿se excluyó algo? ¿la consulta CMR fue completa (paginación, caja, productos)?
5. Opción e-ii mal pasada al evaluador.
6. Regla §6.3 aplicada por interpretación y no por letra (en particular: VIIRS 750 ADOPTAR da DECIDE NICOLÁS; ¿el evaluador lo hace por la rama correcta?).
7. Variantes de robustez §6.4: ¿el global de cada variante sigue la letra? Ojo: el §6.4 dice "si el principal es ADOPTAR o NO ADOPTAR y alguna variante da otro, DECIDE NICOLÁS"; el principal global ya es DECIDE NICOLÁS, así que las variantes no agregan nada, pero 'tabla sola' y 'otra como negativo' caen en e-ii en un sensor. Ese hecho debe informarse a Nicolás.
8. Reflejo solar (§7, A76): las 2 publicaciones de VIIRS 375 de 1 MW o más en negativos y la de Chillán 10-10 18:54 V750.
9. Estrato fuera de las etiquetas (A118), denominadores que se mueven (A90), mezcla de regímenes (A104: #535 es de 2026-08-28, W2 y W3 y parte de W4 caen antes).
10. Instrumento muerto: batería y mutaciones pasan por la razón equivocada (A92, A110, A116).
11. CRLF/autocrlf deformando sha256.
12. Evaluador local distinto del sellado.
13. **Árbol de código mutado en vuelo**: otro proceso (mutar.py del verificador anterior, PID 4492) modifica archivos de `s167_diurno_verif\codigo` mientras corre; copiar de ahí da un evaluador mutado (lo detecté: 42129 bytes contra 42161 y sha distinto). Rehice el árbol con `git archive` limpio.
14. **P2 EMPATE en V375 (neto 0, B 9)**: el caso b se cumple con neto 0. ¿El 0 es neto de verdad o es cancelación de +2 y -2 de naturaleza distinta (publicaciones de 1 MW o más en negativos contra alertas bajo 1 MW recuperadas)? Mira la composición.
15. **D con X=14 de 36**: D usa Q_d = 5/2246; ¿X cuenta pasadas o bloques? (el pre-registro declara el límite de independencia). Con 36 alertas agrupadas en 30 volcán-días, ¿D sigue cumpliendo con una unidad por bloque?
16. **I4 de V750 falla 17 de 2.499 (umbral 22)**: pasa por 5 pasadas. ¿El cálculo de p_sup y el umbral 22 son los sellados? ¿Las 17 son todas RUTINA 0,0 MW (no alerta), es decir no sesgan a favor del brazo?
17. **Las 2 protegidas recuperadas de V750 son Chillán 10-10 18:18 y 10-01 18:42**, ambas con V375 recuperando lo mismo: ¿una sola erupción (Chillán), no evidencia independiente de que el brazo discrimina? W6 concentra 5 de 9 y 2 de 2 recuperadas.
18. **Recuperación 9 de 26 protegidas**: 17 no publicadas, 13 (V375) y 4 (V750) de reflejo probable. ¿Recuperar es publicar con cualquier magnitud y quedan recuperadas con magnitud ridícula? Razón de magnitud 0,93 y 1,07 medianas.
19. **Placebo (I6) SIN SUSTRATO** en todos los casos a y b: I6 no valida la prueba de signos en estos datos; ¿es suficiente protección?
20. **La lectura usa evaluar_con_exclusion con lista vacía**: equivale a evaluar sin exclusión; ¿es lo mismo que el `main()` sellado? El verificador anterior re-corrió ambos.
21. **La hora local/UTC del día** (día = elevación solar > 0 en el volcán a la hora de la pasada): las pasadas 17:24 a 20:12 UTC están a plena luz en Chile; verificar que ninguna "diurna" sea crepúsculo con elevación apenas > 0 en el borde.
22. **Disco**: mutar.py y pytest escriben temporales; usar TMP propio y vigilar `df`.
