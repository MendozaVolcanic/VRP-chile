# Caminos de ruptura escritos antes de abrir evaluar_salida.txt (hora servidor: Sat, 24 Oct 2026 22:08:02 GMT)

1. Pasadas que faltan o se cuentan dos veces: las 1.200 de la muestra vs 1.165 ok + 35 no observadas; ids duplicados entre lotes; la misma pasada en S162 y S162b.
2. Las 35 "volcan_fuera_del_granulo": tratarlas como "calla" sesga a favor; ¿se excluyen del denominador? ¿se concentran en un volcan/sensor?
3. Control de vida: ¿compara el brazo K vs el port sobre las mismas 20 pasadas CTL? ¿"20 de 20" cuenta encendido del port, o solo que el JSON existe?
4. Conjunto que decide: debe ser neg_resto de B2 + neg_pub de S162. Revisar que no entran neg_pub de B2 ni S162b duplicados.
5. Pesos y cota conservadora: suma mal hecha (Wilson / Clopper-Pearson), pesos por estrato.
6. Union (K U B2): mal armada, "acuerdo" que cuenta distinto.
7. Predicado de publicacion: encendidos del port que el predicado no cuenta (M14 con regla del alertado mas cercano vs. otro criterio).
8. Regla cambiada tras el sello (Adenda 1 y Sello): ¿cambia el umbral, el conjunto o la cota?
9. Cache de brazos obsoleta/reutilizada con codigo distinto.
