# Caminos por los que B, C y E podrían estar mal (escritos ANTES de abrir cualquier *_salida.txt)

Hora del servidor al escribirlo: Sat, 24 Oct 2026 15:49 GMT (header Date de `gh api -i repos/MendozaVolcanic/VRP-chile`).
Leído antes de escribir esto: los tres PREREGISTRO, evaluar.py, brazos.py, seleccion.py, probe_v375.py, probe-s162-v375.yml,
curva_cenit.py, linea_base_curva.py, probar_brazos.py, probar_evaluar.py (código). NO leído aún: ninguna salida *.txt.

1. PESOS DE LA UNION. `evaluar.py:620-625` pone w = N_h / n_ok_h con n_ok de la UNION. Es correcto sólo si S159 sorteó al
   azar dentro de (volcán x cenit) y con n por estrato fijado antes de ver resultados. Si S159 estratificó distinto
   (otro eje, prioridad), el peso de la unión no es el del texto. Además la Wilson sobre n efectivo de Kish no es una
   cota de estrato: con estratos pequeños y heterogéneos puede subestimar.
2. INTERVALO QUE NO PUEDE FALLAR. (a) Wilson con 0 eventos da 3,84/(n+3,84): depende sólo de n, no de dónde se sorteó.
   (b) neg_pub "censo": exacto sólo si TODAS las pasadas son ok. (c) el nulo de cenit parecido de E: orden al azar =>
   d y 1/d equiprobables => la mediana de d es 1 por construcción; "el IC contiene 1" no puede fallar salvo por azar, y
   con 37 noches su IC [0,78; 1,18] no habría detectado un sesgo del tamaño del efecto (0,77).
3. LA PRUEBA DE SIGNOS CON PESOS REALES NO ES LA SELLADA. Los bloques suman pesos reales; con un bloque de peso grande el
   nulo puede estar dominado por él; la equivalencia con la sellada se probó sólo con enteros.
4. REGLA QUE NO PUEDE DAR UN VEREDICTO. (a) "VALIDA EN O" del compuesto por volcán: si el compuesto = M14 en todo, o B <= 4
   (SIN SUSTRATO), valida por vacío, y el umbral (no empeora) es más laxo que el del global (GANA). (b) NULO SESGADO
   (punto 2c). (c) B: ENCIENDE DE MAS exige IC inferior sobre 3,85 %; con neg_pub censo y tasa baja casi no puede darse.
   (d) el orden de desempate pone CIRC (hasta 8.746 celdas) antes de SENS (1.764).
5. EL VETO RELATIVO A M14 ESCONDE PERDIDAS REALES. Un brazo que pierde lo mismo que M14 queda candidato. La elección por
   volcán en T usa veto ABSOLUTO (regla distinta a la global).
6. "DECIDE EL LOTE NUEVO" DEJA ESTRATOS SIN REPRESENTAR. `repesar` (evaluar.py:415-425) divide N_h por n del subconjunto S162;
   un estrato cuyas pasadas eran de S159 queda fuera y el veredicto no lo condiciona. En los censos (pos_prot, neg_pub), el
   lote nuevo sólo tiene las que no estaban en S159 (41 de 80 protegidas): el veto de protegidas "decide" sobre un subconjunto.
7. EL RUNNER CORRE ALGO DISTINTO DE LO QUE EL EVALUADOR RECALCULA. `probe_v375.py:81` guarda la grilla como float32 DESPUES de
   calcular con float64; el evaluador exige igualdad a 1e-6 MW en el 100 % de pasada x brazo o declara INVALIDO. Un VRP de
   decenas de MW cambia ~1e-6 con el redondeo float32; una sola diferencia invalida el instrumento. Además S162 usa
   r["port"] (float64 del runner) y S159 el recalculado: dos cálculos mezclados.
8. LA VENTANA CRUZA UN CAMBIO DE REGIMEN. Marco 2026-04-01 a 2026-10-21: #535 (2026-08-28), K (S153/S154), cese de Suomi NPP
   (2026-10-09), calidad de la tabla (A119). El K re-corrido usa el código de HOY, el K "publicado" de los records es el de
   cada fecha.
9. UN BRAZO NO ES LO QUE DICE SER. (a) SENS_PT = M14 en 9 volcanes. (b) SENS (±7.875 m) es la ROI1 física entera en umbrales de
   cumbre. (c) M13 y C13 se centran en la celda más cercana (cajas impares): "la caja impar más cercana a 5,25 km" (13 x
   375 = 4,875 km) no es 5,25. (d) CIRC con inner_radius_km 20 (PCC) es de 8.746 celdas, mayor que la ROI1 entera: casi toda la
   escena en umbrales de cumbre. (e) PIX7 queda con ROI1 distinta a la de S159 ("pixel" 21 x 21 de ROI1) y se declara equivalente.
10. SUMMIT MEDIDO DESDE EL PUNTO DE MIROVA, NO DESDE EL ANCLA DEL TABLERO. `record_sintetico` clasifica con la distancia a (X0, Y0);
    el tablero mide al ancla del cráter. En Tupungatito (cráter a 4,83 km, inner 7) y Cordón Caulle (7,58 km, inner 20) la
    clase cambia según el origen.
11. LA ETIQUETA DE NEGATIVO. En T (antes del 2026-06-13) una alerta sólo OCR "no decide": ¿la pasada queda fuera del marco o
    queda como negativo? En el segundo caso el negativo contiene alertas de MIROVA y el silencio queda mal medido.
12. PLACEBO Y NUNCA. NUNCA: "P2 sale PIERDE si hay más de 4 bloques"; si NUNCA no llega a 5 bloques discordantes el control no
    falla aunque el evaluador esté roto. PLACEBO comprueba magnitud pero no que P2 vea una pérdida real.
13. DESEMPATE: "a igual ΔE (a 1e-6)" sólo ocurre entre brazos idénticos pasada a pasada; el orden de la lista pone C13 antes
    de M14: un C13 idéntico a M14 en nueve volcanes y distinto en dos puede ganar por orden.
14. COMPARACIONES MULTIPLES: 9 brazos contra M14 con p <= 0,05 cada uno y se elige el mínimo de ΔE; sin corrección, falsos
    positivos de "GANA" ~ 1 - 0,95^9.
15. COBERTURA DE LA REFERENCIA "pendiente": ¿el veredicto lo dice en la línea del veredicto o sólo en la sección 1?
16. E 5.4: (c) "M da MEJORA con d' MEJORA o, si d no mejora, no EMPEORA" admite un paquete que no mejora la magnitud; (d) "IC
    de D del paquete entero sobre el de K" es ambiguo; (b) EMPATE incluye SIN SUSTRATO? no figura.
17. Cifras de E (96,8 %, 0,651, 1,000, n 61, "dos de cada tres puntos") deben salir de los informes de S159.
