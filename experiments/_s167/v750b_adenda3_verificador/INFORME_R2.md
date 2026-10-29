# Verificador corto, segunda pasada: adenda 3 de V750-B (fe4802a2a)

Fecha 2026-10-29. Sólo lectura. Árbol: `git -c core.autocrlf=false archive fe4802a2a` en
D:\vrp-trabajo\temporales\s167_ver_v750b_ad3_r2\ (TMP en `tmp\`, 1 proceso a la vez; C: 27 GB y D: 6,0 GB libres, sobre
el piso de 3 GB).

## Veredicto: SELLABLE

## Comprobado

- Diff `5b924379d` a `fe4802a2a`: sólo `experiments/_s162_v750b/adenda3/` (8 archivos) y `tasks/LOOP_VIIRS750.md`.
  Contra `s162-v750b-adenda2-sellada`, nada de lo sellado de V750-B cambia fuera de `adenda3/`; `pipeline/`, `data/`,
  `frontend/`, `scripts/`, `tests/`, `.github/`, `docs/` y `volcanoes.yaml`: diff vacío.
- sha256 LF de `adenda1/leer_v750b.py` (`11e0ee91...`) y `adenda1/cobertura_cajas_v750b.py` (`f250a926...`) iguales a los
  del tag `s162-v750b-adenda2-sellada`; el analizador sigue en `83b7159b...`.
- Batería 12 de 12 (`run1\`). Rojo contra el analizador sellado: 12 de 12 por aserción (`run_rojo\`). Rojo contra el
  lector de `5b924379d`: fallan exactamente N9, N10 y N11 (`run_rojo5b\`). Nulo: 14 de 14 atrapadas por aserción
  (A13 salta la compuerta: falla N9 y N10; A14 `--salida`: falla N11), identidad PASA, control CAÍDA (`mut.log`).
- VA3-01 repetido por mi cuenta (N1 sin la caja B5 de la protegida de Láscar, `vexp\`): el lector nuevo sale 3 y no da
  veredicto; la salida es idéntica a la de `adenda1/leer_v750b.py` salvo la codificación de consola (el nuevo fuerza
  UTF-8). Con `--leer-con-faltantes`, lee con la marca "[LEÍDO CON FALTANTES DE LA ADENDA: ...]"; el sellado hace lo
  mismo, y el nuevo marca 2 líneas más (el encabezado y la lista de la adenda 3).
- El reemplazo del paso del analizador no cambia nada más: el lector sellado de la adenda 1 se carga con
  `importlib` sin copiarlo y sólo se le reasigna `ANALIZADOR`, de modo que su compañero, sus salidas 2 y 3, la marca y
  la salida 5 son los suyos. Los cinco reemplazos de texto sobre el analizador son los mismos de antes (el diff del
  lector no toca esa parte). Comparación sellado (adenda 1 más analizador sellado) contra lector nuevo en N0, N1, N2, N5
  y N7, normalizando las marcas: 0 líneas distintas en N0 y N2; en N1, N5 y N7 sólo cambian P1 y elegibles/ROI.
- VA3-02 (N11 y A14), VA3-03 (los rojos de comportamiento N1, N5, N7 y N9 se separan del texto) y VA3-04 (N8 usa la
  carpeta temporal; el analizador ajeno sólo aporta el texto y las rutas siguen siendo las de la carpeta sellada): cerrados.
- Sin guiones largos ni medios en los cuatro archivos (conteo en Python).

## No comprobado

- Ninguna lectura con datos reales; la codificación de consola bajo cp1252 sólo se vio en el sellado (mojibake ajeno).
- La mutación equivalente que señalé en VA3-03 (`P1_todas` por `P1` en `elig_todas`, canal "tabla") sigue sin atraparse
  ni declararse; es equivalente y de gravedad 1, no condiciona el sello.
