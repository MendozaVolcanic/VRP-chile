# D-46: cómo se lee el 5 % del placebo simétrico (c) de la quinta adenda

**Decidida por Nicolás el 2026-10-23** (hora del servidor ~17:50 UTC), antes del tag de lectura y sin haber abierto
V1, V2a, V2b ni el brazo del 17 al 19 de octubre. La pregunta llegó después de ver el resultado del placebo (c), que es
un control sobre producción, no el veredicto del A/B. Respuesta textual, registrada por la sesión dueña del loop (S161),
a la pregunta «¿Cómo se lee el "supera el 5 %" del placebo (c)?», con la recomendación de leerlo sobre todo (c) a la
vista: «lo que recomiendes».

1. **`ADENDA_SIGNOS_P2.md` §6 se lee así**: «(c) falsos de 5 % o menos por cola» se mide **sobre todo (c)**, por cola,
   con su intervalo de Wilson: GANA en falso 8 de 320 (2,5 %, Wilson [1,3; 4,9]) y PIERDE en falso 4 de 320 (1,2 %,
   [0,5; 3,2]), contra 2,1 % exacto esperado por cola. Pasa.
2. **Cada punto y sensor se informa al lado y no decide**, con su tasa exacta esperada y su probabilidad binomial. El
   caso que lo motivó: V2 50 % VIIRS 375, GANA en falso 3 de 40 (7,5 %, Wilson [2,6; 19,9]) contra 3,2 % esperado;
   P(3 o más de 40) = 0,136 (`experiments/_s159/instrumentos/signos_p2/binomial_v2_50.txt`).
3. POR QUÉ: con 40 semillas por celda y 16 celdas-cola, una regla bien calibrada deja al menos una celda sobre el 5 %
   sólo por azar con probabilidad **0,67** (tasas exactas de cada celda del README de `signos_p2`, binomial con
   n = 40). Leído por celda, el criterio rechazaría una regla correcta dos de cada tres veces. La tasa exacta de la
   regla, sin muestreo, es de 4,81 % o menos por cola para B de 5 a 20 (§7).
4. La ambigüedad era de la redacción de la adenda (S161), no del código: el implementador la dejó como LECTURA 6, sin
   decidirla.
