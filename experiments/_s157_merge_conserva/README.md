# S157: el merge de reproc-chunked conserva lo que main ya tiene

## El defecto

`reproc-chunked.yml` reprocesa un volcán partiendo la ventana en trozos, y su job `merge` los une con
`scripts/merge_chunk_stores.py --ventanas`. Cada trozo aporta sólo los records de su ventana (arreglo de
S124, para que un trozo no resucite meses viejos). Pero nada aportaba lo que queda **fuera** de las ventanas
de la corrida: el archivo `data/<perfil>/<Vol>.json` se escribía sólo con los trozos de esa corrida. Relanzar
dos trozos caídos de un volcán borraba en main todo el resto de su histórico. Pasó con NevadosDeChillan en
S157 (los relanzamientos de los runs 39363774747 y 39363796988; ese JSON lo rearma aparte la sesión dueña del
loop).

Había un segundo problema escondido: el job `merge` hace checkout del sha del **despacho**, y subía con
`pull --rebase -X theirs`. Aunque el script leyera la base del checkout, esa base podía tener horas de atraso
respecto de main (otra corrida del mismo perfil, o un rearme a mano), y rebasar un JSON unido contra otra
versión del mismo archivo es la carrera de S25.

## El arreglo

1. `merge_chunk_stores.py --base <archivo>`: los records de la base cuya fecha UTC cae fuera de todas las
   ventanas de los trozos presentes se conservan tal cual (mismo objeto, mismo orden, mismas claves de
   nivel superior); los de dentro se descartan y manda el trozo, aunque el trozo no traiga una pasada que la
   base sí tenía (es el resultado del reproceso). Un trozo caído no aporta ventana, así que su tramo queda
   como estaba. `--base` exige `--ventanas`; una base inexistente o vacía da el mismo archivo que sin base;
   una base de otro volcán se rechaza.
2. El job `merge` hace, en cada uno de sus 5 intentos: `fetch` de main, se para encima, copia la base de
   `data/<perfil>/<Vol>.json` tal como está en main, une, commitea y empuja en avance rápido. Si main se movió
   entre el fetch y el push, el push se rechaza y el intento siguiente relee la base. El script de merge se
   copia antes de pararse en main, para usar el del despacho.

Lo que no cubre: dentro de sus ventanas la corrida manda. Dos corridas del mismo perfil no deben solaparse
en fechas (el grupo de concurrencia por perfil las pone en fila, pero no evita el solape).

## Evidencia

- `tests/test_merge_chunk_stores.py`: 11 pruebas nuevas del script (12 casos) (tres ventanas con trozo sólo de la del
  medio, byte a byte; sin base igual que hoy; bordes; duplicados; trozo caído; rechazos).
- `tests/test_reproc_chunked_merge_conserva_s157.py`: corre el `run:` REAL del paso (extraído del yml) con
  `bash -e`, como GitHub, contra un repositorio de origen local. Incluye el caso en que main se mueve entre
  el fetch y el push (un `pre-push` que empuja otra versión la primera vez).
- `mutaciones.py`: batería con control sin mutación y control de caída (A110, regla S156). Trabaja sobre
  una foto congelada del árbol (A112). Resultado en `resultado_mutaciones.json`. Sólo cuenta como
  ATRAPADA una mutación que alguna prueba detecta por aserción sobre el resultado; si sólo se cae el código
  o el paso de bash (etiqueta `PASO_CAYO`), es CAIDA.

  Corrida final (la de `resultado_mutaciones.json`): control sin mutación limpio sobre 28 pruebas; 13 de 17
  mutaciones ATRAPADAS por aserción; 2 CAIDAS esperadas (el control de caída, y Y6, que deja activo el
  `bash -e` de GitHub: la prueba de perfil nuevo lo detecta, pero como caída del paso); 2 equivalentes
  declaradas antes de correr que sobreviven (S7, porque el store sólo tiene `volcano`, `updated` y
  `records`; S10, porque `merge_stores` también rechaza `--base` sin `--ventanas`).

  Dos defectos del propio instrumento, encontrados por la primera corrida y corregidos:
  - el clasificador buscaba `PASO_CAYO` en el texto completo del fallo, que trae el código fuente de
    `_correr`, así que rotulaba como caída lo que era aserción (Y5 y varias más);
  - Y3 (push forzado) sobrevivía: la prueba movía main en un `pre-push`, y ahí el servidor rechaza
    incluso un `-f` porque la referencia ya no está donde el cliente creía. Se agregó el mismo caso con
    `post-checkout` (main se mueve mientras se une), donde un `-f` sí borraría lo ganado.

- Suite completa con el árbol quieto: 2244 passed, 28 skipped, 2 xfailed.
