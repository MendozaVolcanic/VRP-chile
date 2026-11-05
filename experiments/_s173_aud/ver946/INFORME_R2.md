# Segunda ronda, PR #946 (punta 5facd4a8b)

Worktree `D:/vrp-trabajo/wt/ver946` en `5facd4a8b`. Diff leído completo: `git diff 7df31d9f1 5facd4a8b` (leer_retro.py, dos baterías, mutar_leer_retro.py y su salida; `armar_manifiesto.py` y `armar_montaje.py` no cambian).

## Veredicto: MERGEABLE CON CAMBIOS (gravedad máxima 1 en esta ronda)

Suite relevante (4 archivos): **110 pasan en 354 s** (`pytest_r2.txt`). Pre-registro sellado: sha256 LF en `origin/loop/activo` = `b58a2254…3c91`, igual al del sello; el PR no lo toca.

## Afirmaciones del autor

| afirmación | resultado |
|---|---|
| VPR946-01 arreglado | ARREGLADO: `c_cenit_osf` y `controles_cenit` entran a `ctl` (fila 1 si rojo), C-cenit sin pares es rojo; pruebas con rojo y control OK. Límite en R2-02 y R2-03 |
| 02 arreglado | ARREGLADO: X1 y X2 atrapadas; queda X2b (R2-01, g1) |
| 03 arreglado | ARREGLADO: G1 atrapada |
| 04 y 11 arreglados | ARREGLADOS (tipos y fecha leída; K sin DM) |
| 05 en parte | CONFIRMADO en parte: tag vacío, tag por origen y diff por tag con aserción; C-montaje sigue pendiente |
| 06 a 10, 12, 13 anotados | CONFIRMADO: están en el cuerpo del PR, sin código |
| 12 de 12 atrapadas | REPETÍ X1, X2, G1, G3: las cuatro ahora se atrapan por aserción (sin caídas); las otras 8 del autor: no repetidas, SIN VERIFICAR |

## Mi mutación nueva
X2b (main no pasa `a.osf` a `rutas_referencias`): SOBREVIVE. La prueba de main no usa `--osf`.

## ¿Rompió algo el arreglo de cenit?
- Con OSF sin ninguna pasada R25 el candado queda rojo por `c_cenit_osf` (consistente con C-via y C-cobertura R25, que ya caían).
- No encontré un control que quede rojo de más con datos sintéticos; tampoco puedo descartarlo con datos reales: `controles_cenit` dio SIN SUSTRATO en MODIS, V375 y V750 sintéticos, así que su rama real nunca corrió (R2-02). Un error interno queda como "OK (sin sustrato)".
- C-cenit se mide sobre el conjunto de los tres sensores (R2-03).

Archivos: `hallazgos_r2.csv`, `probe_r2.py`, `mut_r2.py`, `mut_r2_leer.txt`.
