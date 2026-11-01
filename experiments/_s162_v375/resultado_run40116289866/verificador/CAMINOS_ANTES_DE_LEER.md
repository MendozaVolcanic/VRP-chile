# Caminos por los que la lectura podria estar mal (escritos ANTES de abrir evaluar_salida.txt)

Hora del servidor al inicio: Sat, 24 Oct 2026 18:42:11 GMT (header Date de `gh api -i repos/MendozaVolcanic/VRP-chile`).
Commit medido: 20719dc8f1ce118fd18a01560ee4cb6a5f961d6d.

1. Pasadas del run que faltan o que se cuentan dos veces (mismo granulo en dos carpetas s162-v375-N; mismo granulo en el lote S159 y en el nuevo; duplicados en la union).
2. Las 11 pasadas "volcan_fuera_del_granulo": si estaban de verdad fuera (bounding box del granulo vs lat/lon del volcan) o si es un fallo de lectura/geolocalizacion; si sesgan la tasa (ej. se descartan solo negativos o solo positivos).
3. El recalculo sin red que coincide porque compara lo mismo consigo mismo (brazo recalculado desde la misma grilla con el mismo codigo que produjo el numero que se compara).
4. K re-corrido que no es produccion (el brazo K del evaluador contra lo que publico el pipeline de produccion).
5. Pesos mal aplicados entre lote nuevo y lote S159 (el de S159 entra a la union con otro peso/estrato/ventana; el pre-registro dice que decide cual).
6. El veredicto B cambia segun que lote decide (solo el nuevo, solo S159, union); la regla decide por el nuevo y el umbral 4 de 434 podria estar en el borde.
7. El brazo global ganado por empate o por dos volcanes (C13 gana por Cordon Caulle y Tupungatito solamente; leave-one-volcano-out).
8. La eleccion por volcan hecha con datos de O (la validacion "en O" puede ser circular si la eleccion uso O, o si O no es independiente).
9. Una protegida perdida que el veto no cuenta (protegida definida con una definicion mas estrecha que la del pre-registro: alertas del scraper de 1 MW o mas, lectura A; o pasadas protegidas sin record).
10. Negativos que el brazo ganador enciende de mas en volcanes donde M14 calla (neg_resto, neg_pub desagregado por volcan).
11. La magnitud de los brazos (VRP de C13 vs M14 vs referencia; que la magnitud no se use como criterio, o que lo sea y este mal).
12. Que las adendas 1 y 2 cambien una regla despues del sello (diff contra el tag s162-v375-bc-sello).
13. Que el evaluador lea la caja/vara de un archivo distinto de la que sello el pre-registro (constantes en evaluar.py vs PREREGISTRO).
14. Que las pasadas cuenten por noche y no por pasada, o la unidad de las tasas (pasada vs noche vs record) no coincida con el pre-registro.
15. Que el npz de grilla no sea la grilla de la pasada que dice (nombre vs contenido), o que el JSON de resultados tenga campos de otro volcan.
