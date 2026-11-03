# S173: qué pieza corrige la caída de magnitud con el cenit en Nevados de Chillán

Pedido de Nicolás (2026-11-02): las pruebas del ángulo cenital que el auditor de S172 dejó pendientes
(`experiments/_s172_chillan/auditor/INFORME.md` §10), en los tres sensores. Tres investigadores (Opus) y un
verificador limpio (Fable) por sensor. Los informes originales viven en `C:/Users/nmend/vrp-wt/s173_cenit/`; acá
están copiados sin las copias del repo ni los JSON de datos de más de 1,5 MB.

Ojo con el nombre: los encargos llamaron a D25 «geometría del borde del barrido». Es un error del coordinador. En el
catálogo D25 es el fondo de anillo regional con recorte a cero (`docs/MIROVA_DIVERGENCES.md`).

## Resultado, ya pasado por el verificador

| sensor | qué cae con el cenit | pieza | estado |
|---|---|---|---|
| VIIRS 750 | K (MIROVA plano) | fondo de anillo de K en la grilla; sin remuestreo queda 0,587 de la caída logarítmica | fondo CONFIRMADO EN PARTE; área/remuestreo SOSPECHA (pasa la condición necesaria del ATBD) |
| VIIRS 375 | K (0,745 / 0,481, 66 pares); V375-E no (0,92 / 1,00, 27) | sin aislar: no existe ablación por pieza | D17 SOSPECHA, en tensión con la tarea 1.14 §3.2 (gravedad 3) |
| MODIS | K; la vía no (producción 2026-11-02: 1,19 y 1,11 a 41° y 52°, n 2) | el recorte a cero cuando ninguna celda supera la mediana del anillo (5 de 10 oblicuas, 0 de 6 bajo 30°); D17 no extraíble del lote S162 (cenit y volcán confundidos) | CONFIRMADO EN PARTE |

## Seguimientos abiertos

- VMODIS-01 (gravedad 3): el arnés del PR #937 nunca llama a `auth()`; las 27 pasadas saldrían sin bajar. Corregir
  antes de pedir el merge.
- S1 de `ver_modis/` (gravedad 3): la regla de cirrus del tablero (`frontend/index.html`, `t_max` bajo 273,15 K y más
  de 10 MW) puede ocultar alertas reales de la vía en pasadas oblicuas; una ya cayó (2026-10-01 08:35, 11,44 MW).
  `frontend/` necesita tag y sí de Nicolás (A45).
- VV750-01 a 07 y VV375-01 a 06: defectos de instrumento de gravedad 1 a 2 (ventana efectiva de 12 noches en V750,
  controles débiles, una pasada topada por D9).
- La sombra de V375-E está vacía por diseño hasta el 2026-11-03 (`scripts/ventana_sombra.py`, `FECHA_MINIMA`).
