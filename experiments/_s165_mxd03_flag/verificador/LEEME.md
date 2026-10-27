# Verificador limpio de los flags MxD03 de MODIS (S165, 2026-10-27)

Claude Fable 5.1, esfuerzo alto (pedido), contexto limpio: recibió sólo las afirmaciones A1 a A9 con dónde mirar, sin el
razonamiento de quien escribió el PR. Escribió `CAMINOS.md` antes de leer el cambio (sha256 en `CAMINOS.sha256`, coincide
con el archivo copiado aquí). Copia fiel de `D:\vrp-trabajo\temporales\s165_mxd03_verificador\` (sin `PLAN_copia.md`, que
es una copia del plan); no tocó el worktree del PR.

**Veredictos:** A1, A2, A4, A5, A6, A7 y A9 CONFIRMADO; A3 CONFIRMADO EN PARTE (gravedad 2); A8 CONFIRMADO EN PARTE
(gravedad 3). Informe completo en `INFORME.md`.

## Qué se hizo con cada hallazgo

| ID | gravedad | qué | respuesta |
|---|---|---|---|
| V165-01 | 2 | el flag de distancia también alcanza el filtro de píxeles y la geocerca de `store.py`, y nadie lo nombraba | escrito en el comentario del cableado en `calculate_vrp`, con la medición del verificador (0 píxeles salen de la cerca, 1 vuelve a entrar: PCC 2026-05-03 07:50, uno de los 5 records ya listados). Encender el flag sigue siendo decisión de Nicolás |
| V165-02 | 3 | EQUIVALENTE no exigía el resumen idéntico, y en 14 de 18 records K y X ya coinciden en publicación y magnitud | `equivalencia.py` exige ahora el resumen idéntico en los 18 (ON contra X, OFF contra K) |
| V165-03 | 2 | con «sin dato» encendido la pasada descartada no queda registrada como incidencia y el informe de cobertura diría «completa» | **pendiente, antes de encender el flag 2**: no cambia nada con el flag apagado y tocar el registro de incidencias es otro cambio de `pipeline/` |
| V165-04 | 1 | docstring de `equivalencia.py` decía 36 records; son 18 | corregido |
| V165-05 | 1 | el censo usa una distancia plana y mira sólo la latitud de los vecinos; el pipeline usa haversine y mira latitud y longitud | se declara; efecto esperado nulo (SOSPECHA del verificador, no medida) |
| V165-06 | 1 | el plan esperaba cubiertas bajo ~0,7 km; el dato da p99 1,89 km y máximo 2,63 km | ya estaba corregido en el docstring de `crater_cubierto`; se deja dicho aquí |

Seguimiento suyo fuera del PR: `test_guard_libro_de_pruebas_s146` falla si el repositorio y `tmp_path` están en discos
distintos (le pasó en su árbol en D:, no en el del PR).
