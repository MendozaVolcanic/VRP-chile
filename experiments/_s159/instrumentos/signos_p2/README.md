# P2 con la prueba de signos por bloque (D-45): implementación, candados, placebos y mediciones

Vara: `experiments/_s157_prereg_d25/ADENDA_SIGNOS_P2.md` (quinta adenda, sellada por Nicolás el 2026-10-22, commit
`c13cf5808`). Todo con datos sintéticos o brazos armados desde producción; nada del A/B. El veredicto de D25 no se leyó.

## Estado (se actualiza a medida que avanzo)

1. Pruebas nuevas escritas y guardadas rojas contra `c13cf5808`: hecho (ver «Pruebas rojas»).
2. Implementación: pendiente.
3. Candados: pendiente.
4. Verdes con el árbol quieto: pendiente.
5. Placebos: pendiente.
6. Mediciones sintéticas: pendiente.

## Pruebas rojas

`rojo_signos_p2.py` copia el evaluador de `c13cf5808` (idéntico al de `bcfdc7c76`, que nombra la adenda: `c13cf5808`
sólo agrega la adenda) a `experiments/_mut_rojo/`, corre `tests/test_evaluar_d25_signos_p2_s161.py` con
`D25_EVALUADOR_DIR` apuntando ahí, y clasifica cada falla leyendo el XML de JUnit. Salida: `rojo_signos_p2.txt` y
`rojo_signos_p2.xml`.
