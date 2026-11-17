# Pregunta para Nicolás: cómo se lee R-W7 (adenda V, sellada el 2026-11-17)

Mientras no la aclares, el A/B corre y sus salidas se guardan, pero **no se calcula ningún veredicto** (así nadie mira
resultados con la regla abierta). El evaluador hoy aplica la lectura literal; la otra lectura es una línea en
`experiments/_s190_diurno/evaluar_diurno_via.py::aplicar_modificadores`.

| | |
|---|---|
| Texto sellado (ADENDA_VIA.md §4) | «R-W7: el veredicto también sin W7. Se informa; no cambia el veredicto salvo que sin W7 salga NO ADOPTAR, caso en que pasa a DECIDE NICOLÁS CON M4.» |
| La ambigüedad | No dice si R-W7 actúa siempre que sin W7 salga NO ADOPTAR, o sólo cuando con W7 el veredicto era otro (como R-CH, que sí lo dice: «si con Chillán sale ADOPTAR y sin Chillán sale NO ADOPTAR»). |
| Lectura 1, literal (la que corre hoy) | Siempre que sin W7 salga NO ADOPTAR, el sensor pasa a DECIDE NICOLÁS CON M4, aunque con W7 también saliera NO ADOPTAR. |
| Lectura 2, simétrica con R-CH | Sólo si con W7 sale ADOPTAR y sin W7 sale NO ADOPTAR, el sensor pasa a DECIDE NICOLÁS CON M4. Si con W7 ya es NO ADOPTAR, queda NO ADOPTAR. |
| Dónde difieren | Sólo cuando el brazo sale NO ADOPTAR con W7 y también sin W7, es decir, un brazo que publica de más de día en todas las ventanas. Con la 1 ese brazo sale DECIDE NICOLÁS y nunca NO ADOPTAR (es lo que le pasa al brazo sintético ruidoso, `brazos_sinteticos_salida.txt`); con la 2 sale NO ADOPTAR. En los casos ADOPTAR, DECIDE NICOLÁS y SIN CAMBIO dan lo mismo. |
| Recomendación | **Lectura 2.** R-W7 se escribió para que un ADOPTAR que dependa sólo de la erupción de Chillán en W7 no pase solo; no para rescatar a un brazo que publica de más en todas partes. Con la 1, el A/B pierde la capacidad de decir NO ADOPTAR, que es la respuesta que protege contra los reflejos solares (A98). |

Si eliges la 2, se cambia esa línea y la prueba que hoy fija la lectura literal
(`tests/test_evaluar_diurno_via_s190.py`), en un commit que cita tu respuesta, antes de calcular el veredicto.
