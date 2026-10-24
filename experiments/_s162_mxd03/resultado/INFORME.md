# S162 MOD-B: resultado del A/B de MxD03 sobre K (tarea 1.30, D-19)

2026-10-24 (UTC). Pre-registro sellado (D-48): `experiments/_s159/mxd03_prereg/PREREGISTRO_MXD03.md`. Código del tag
`s162-mxd03-tag` (`ffbb36248`, `pipeline/` = `origin/main` `80b819828`). Runs: humo 40111997157, t1 40112510038, t2
40122029477, t3 40126381034. Artefactos de las tres tandas juntos en `D:\vrp-trabajo\temporales\s162_mxd03\tandas\`
(sin el humo, para que el control de duplicados no cuente doble). Evaluación con `vara_mxd03.py --evaluar` y
`evaluar_mxd03.py --art --vara --ref`, salidas en esta carpeta (`evaluar_mxd03_salida.txt`, `resultado_mxd03.json`,
`vara_resultado.json`, `detalle_salida.txt`). **Verificado con contexto limpio** (Fable alto, `verificador/INFORME_VERIFICADOR.md`): R1, R3 y R4 CONFIRMADOS, R2
CONFIRMADO EN PARTE; el CUMPLE SIN DAÑO se sostiene con código independiente del evaluador. Ver la sección «Lo que dijo
el verificador» al final.

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

## Lo que dijo el verificador (2026-10-24)

`verificador/INFORME_VERIFICADOR.md` (caminos sellados a las 20:33:02 GMT, sha256 `ad03b0a0…`). Confirmó con un recuento
propio: 5.465 de 5.465 clave por clave contra la población del tag, 0 errores ni duplicados, un único commit (el del tag)
en los 3 runs; K = data/ y K2 = K en las 5.465; P1 sin pérdida (48 de 48 protegidas con cúmulo en K y en X); P2 ≤ 35°
EMPATE para cualquier ruido de 1 o más; la vara MXD03 MAS CERCA por cinco caminos distintos; la tabla del §10 rearmada a
mano; los scripts del autor reproducen `resultado_mxd03.json` y `vara_resultado.json` byte a byte. Matices que hay que
leer junto al veredicto (ninguno lo mueve):
- **«13 controles»**: son 12 que pueden fallar. «vara_cruda» siempre da OK (`evaluar_mxd03.py`, l. 471): es un registro,
  no un control.
- **VRB-02, la vara**: con la referencia VIIRS de **otra noche** (placebo, 5 semillas) da el mismo MXD03 MAS CERCA (dd 0,83
  a 0,95 km, 51 de 65). La vara mide «más cerca del cráter de Láscar», donde casi siempre está el calor, y no «más cerca
  del calor de esa noche». No es un sesgo de construcción del estadístico; es un límite de lo que esta vara puede decir.
- **VRB-03, M**: la mediana 0,000 esconde dispersión: 17 de 79 alertas cambian la magnitud más de 10 % y 6 más de 30 %
  (hasta X/K 0,48); hay 38 d < 0, 39 d > 0 y 2 d = 0.
- **R4, más fuerte de lo resumido**: los 158 movidos son todos los records con cúmulo en K y en X, y las 48 protegidas
  con cúmulo quedan **todas más cerca del cráter con X** (mediana 1,46 km, máximo 2,49). El +1 de P2 sin Cordón Caulle
  es una sola bajo 1 MW de Láscar (2026-04-02 07:45) que X apaga por el fondo (0,011 a 0,000 MW), no por la posición.
- **VRB-01**: el módulo del nulo R llega a 103.470 km en 2 gránulos con relleno de MxD03 y el control del módulo lo
  acepta; afecta sólo a un negativo que nadie publica (Lastarria 2026-04-23 01:50). Defecto del control, sin efecto.
- **VRB-05**: la rama de re-corrida en el `codigo_sha` (control 4) **nunca se ejercitó**, ni en las tandas ni en el
  humo: no hubo ningún record que decide con K distinto de `data/`. `RESPUESTA_VERIFICADOR.md` decía que el humo la
  ejercitaba: era falso, se corrige aquí. VRB-06: el nulo de P2 no está centrado (todo es Cordón Caulle). VRB-07: en el
  borde del barrido `_interp_geo` corre el píxel 10 a 16 km (15 records, cenit 63 a 75°).
- **Seguimientos para la adopción**: `_interp_geo` interpola el relleno −999 sin enmascararlo (SOSPECHA); 36 records en 8
  gránulos donde X pierde píxeles que no tienen geolocalización MxD03 y K sí conserva: la adopción tiene que declararlo.
