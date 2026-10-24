# S162 MOD-B: resultado del A/B de MxD03 sobre K (tarea 1.30, D-19)

2026-10-24 (UTC). Pre-registro sellado (D-48): `experiments/_s159/mxd03_prereg/PREREGISTRO_MXD03.md`. Código del tag
`s162-mxd03-tag` (`ffbb36248`, `pipeline/` = `origin/main` `80b819828`). Runs: humo 40111997157, t1 40112510038, t2
40122029477, t3 40126381034. Artefactos de las tres tandas juntos en `D:\vrp-trabajo\temporales\s162_mxd03\tandas\`
(sin el humo, para que el control de duplicados no cuente doble). Evaluación con `vara_mxd03.py --evaluar` y
`evaluar_mxd03.py --art --vara --ref`, salidas en esta carpeta (`evaluar_mxd03_salida.txt`, `resultado_mxd03.json`,
`vara_resultado.json`, `detalle_salida.txt`). **Pendiente: verificador con contexto limpio del resultado.**

## En una pantalla

1. **Veredicto sellado: CUMPLE SIN DAÑO.** Ubicar los píxeles MODIS con MxD03 no pierde ninguna protegida (P1), deja la
   suma bajo 1 MW en empate con el nulo bajo 35° (P2: ΔX = −1 contra un ruido de 4) y no detiene la vara VIIRS (que da
   **MXD03 MAS CERCA**). Los 13 controles en verde.
2. **Censo completo**: 5.465 de 5.465 pasadas en las 24 partes, 0 errores; K igual a `data/` y K2 igual a K en todas
   (nada que re-correr en un commit viejo); control de geometría 2,581 km = S151; re-etiquetado desde la referencia
   congelada sin diferencias.
3. **La posición mejora contra un sensor independiente**: bajo 35°, el píxel MODIS más caliente queda 0,73 km más cerca
   del objeto que ve VIIRS 375 esa noche con MxD03 que con `_interp_geo` (IC 0,49 a 1,10 km; 51 de 65; Terra y Aqua del
   mismo signo; el nulo de pares de traslaciones llega a 0,29 km como máximo).
4. **Sobre 35° (informa)**: ΔX = −4 (MxD03 publica 4 de menos en negativos o 1 bajo 1 MW de más; 8 pasadas cambian, 5 de
   Cordón Caulle y Chaitén a 59-65°). La vara descriptiva sobre 50° se invierte (−4,8 km, n 4: SIN PODER).
5. **Lo que condiciona la adopción** (§6 P4, sin cambiar el veredicto): el cúmulo se mueve más de 0,01 km en 158
   pasadas, 48 de ellas protegidas, así que el pre-registro exige una **auditoría espacial A61** de esas protegidas antes
   de adoptar. Y el signo de P2 sin Cordón Caulle difiere del de P2 (+1 contra −1, ruido 2): se informa en la primera
   línea, como manda el §6.

## Pruebas (§6 del pre-registro)

| prueba | resultado |
|---|---|
| P1 veto | **SIN PÉRDIDA**: 0 de las protegidas que K publica se apagan con X |
| P1b | ninguna protegida cruza bajo 1 MW |
| P2 ≤ 35° (decide) | **EMPATE**: ΔX = −1; ΔR de las 20 semillas entre −4 y +2, ruido (segundo mayor) 4; S(K) 34; n 1.861 |
| P2 sobre 35° (informa) | ΔX = −4; S(K) 15; n 3.185 |
| P2 sin Cordón Caulle ≤ 35° (informa) | EMPATE, ΔX = +1, ruido 2; **signo distinto del de P2** |
| P3 vara VIIRS (detiene) | **MXD03 MAS CERCA** (n 65, 57 noches): no detiene |
| M magnitud (informa) | NEUTRO: mediana de d 0,000, IC [−0,0024; +0,0066], ĝ = 1,00 (n 79; Láscar 71, Chillán 7) |
| P4 el cúmulo se mueve | 158 movidos, 48 protegidas → **auditoría A61 requerida antes de adoptar**; 19 cambios de clase, todos en negativos limpios, `sin_info` y una bajo 1 MW |
| P5 atribución | 17 pasadas con cambio de publicación, con X_fondo y X_det; identidades exactas en las 17 |
| P6 fuera del censo decisor | 2 cambios, los dos en `sin_info` (Cordón Caulle 2026-06-26 07:40 y Láscar 2026-04-05 08:00, K publica y X no) |

## Lectura

El cambio es inocuo para la réplica, que es lo único que el A/B decide (§1, «CUMPLE SIN DAÑO no debe leerse como
mejora»). Lo que sí agrega es que la posición mejora contra un sensor independiente, y que donde cambia la publicación
casi siempre es en negativos limpios de Cordón Caulle y Chaitén vistos muy de lado. Según la tabla del §10, un CUMPLE
SIN DAÑO abre el ciclo de adopción por fidelidad literal (Coppola 2026, a confirmar por MOD-A), con tag defensivo, flag
`enable_modis_geo_mxd03` con TDD que reproduzca X record por record, auditoría A61 de las 48 protegidas movidas, el sí
de Nicolás (A45), D35 y las marcas A113 en el catálogo, FICHA SDA, marca visible en las tres vistas y aviso a OVDAS. La
sesión recomendó adoptar MxD03 **dentro del paquete MODIS** (MOD-D) salvo que se atrase más de un mes: con este
veredicto la pieza queda lista para eso.
