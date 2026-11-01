# Caminos por los que la regla o el evaluador podrian decidir mal (escritos ANTES de abrir evaluar_diurno_k.py)

Origen: lista del encargo + lectura del PREREGISTRO.md (unico documento leido hasta aqui; NO he leido evaluar_diurno_k.py, ni tests, ni MISSION).
Cada camino es una HIPOTESIS a comprobar, no un hallazgo.

K1. Denominador que se achica en silencio: alertas (sobre todo las 10 bajo 1 MW de V375) sin record del brazo salen de n y de X de la prueba D y de P2; I4 solo cubre protegidas (a) y un agregado (c).
K2. El control sintetico ("observado, no publica") inventa errores del control: toda alerta_mb que el brazo publica cuenta -1 a favor por construccion, y el control nunca puede acertar de dia.
K3. Caso e-i decide un intercambio (protegida recuperada vs publicaciones de mas) que el criterio no dice: P>=1 basta (1 protegida, quiza reflejo) con Q_d <= Q_n; puede dar ADOPTAR con P2 en PIERDE y con decenas de publicaciones de mas.
K4. Q_n (noche de K) como vara del dia: poblacion distinta (otro ambiente de fondo, otro n), medida sobre el control que en la corrida real es otro codigo; Q_n con denominador pequeno o cero.
K5. Poblacion "otra" (RUTINA en dia con alerta, FALSO_POSITIVO, solo OCR sin alerta) no entra al criterio: publicaciones del brazo ahi son gratis. Sin tope.
K6. Un negativo se define por dia UTC sin alerta: dias con huecos de la tabla de MIROVA (12 y 13 oct dentro de W6) pueden dar "negativos" falsos o quitar alertas.
K7. Frontera dia/noche: elevacion solar > 0 vs el filtro del pipeline; pasadas de crepusculo que caigan en ninguno o en ambos.
K8. Ventana que mezcla regimenes: W2 con OCR recien calibrado (A119), referencia congelada en 047bd5692 vs codigo del tag de despacho distinto del de la produccion usada para Q_n y para p_sup.
K9. Referencia congelada no es la del sustrato (sha256 de los 4 CSV) o el evaluador no la exige.
K10. D (binomial) supone independencia; los positivos y negativos vienen en bloques volcan-dia (varias pasadas por dia); Q_d tiene sobredispersion; n de D incluye o excluye cosas distintas que P.
K11. Prueba de signos por bloque aplicada a una asimetria estructural (casi todo discordante es +1; los -1 son <=10): GANA casi imposible, PIERDE casi seguro; la tabla 6.2 solo usa GANA/neto, no PIERDE.
K12. Caso a (P2 GANA => ADOPTAR) sin mirar P, D ni Q_n, ni proteccion.
K13. Caso b con neto<=0: en V750 (0 alertas_mb) exige cero publicaciones de mas; con P=1 y Q_d=0 D cumple por definicion: basta una protegida (quiza de reflejo, o del OCR) para ADOPTAR.
K14. Compuertas que no pueden fallar: I2 (palanca actuo) y I6 (placebos) -> SIN SUSTRATO tratado como pase; I6(c) con tolerancia de 4/40; I6(a) exige GANA "cuando toca >=5 bloques" pero un brazo con Q_d alta puede no dar GANA aun con la mitad apagada.
K15. R1 "por construccion" nunca falla si I5 esta en verde: es redundante, o falla en el orden equivocado (INDECIDIBLE antes que INVALIDO).
K16. Robustez 6.4: variantes (b) y (c) pueden ser iguales al principal sin avisar (archivo de reflejo con claves que no pisan nada); variante que da INVALIDO/INDECIDIBLE/DECIDE se trata mal; solo se aplica si el principal es ADOPTAR/NO ADOPTAR.
K17. Variante "tabla sola" y regla SN (D-9): alertas V375 <=0.05 MW pasan a RUTINA = negativos; si el brazo publica ahi es error (cuenta +1) aunque MIROVA si alerto en el CSV.
K18. Veredicto global: ADOPTAR de un sensor y SIN CAMBIO del otro => ADOPTAR de un flag que enciende ambos; "SIN CAMBIO" = brazo no publica ninguna diurna del sensor, pero puede haber perdido cobertura (no hay records) y salir "sin cambio".
K19. Cifras del preregistro (sustrato 3, nulo 5.1, costos 8) y de la Tabla 1 / codigo de MIROVA (2.2) no coinciden con sus salidas/fuentes.
K20. Se pierde alguna proteccion de la adenda/pre-registro original (G3 noches intactas, H2a, tope por volcan, etc.) al reemplazar G1/G2.
K21. Nulo estructural: usa produccion nocturna como "control" y un brazo sintetico que publica al azar sin estructura (no correlacionada con volcan/dia/nube); subestima la tasa de ADOPTAR falso de un brazo real con errores agrupados.
K22. El evaluador y el preregistro difieren (tabla vs codigo): lo que el 6.2 dice vs lo que decidir() hace en bordes (<=, <, X=0, Q=0, n=0).
K23. Seguridad de la ejecucion: sha-codigo, rutas de ref, "--recorte" que reduce poblacion en la corrida real; entradas no validadas (ventanas que faltan se omiten en silencio).
