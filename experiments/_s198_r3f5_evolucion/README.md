# S198: la marca «cráter no medido» en los gráficos del tablero (Codex ronda 3, R3F5-101 y R3F5-V101)

## El fenómeno

A veces el infrarrojo medio (MIR, la banda que ve el calor) llega sin dato sobre el cráter, o el barrido que lo cruza
viene sin posición, o la MIR satura. La vía lo anota en `diag_codigo_mirova` y desde #1095 (S194) el tablero lo avisa en
la tabla de pasadas, el popup, las tarjetas de 48 h y el conteo del diario. Los gráficos no lo leían: la evolución de
index dibujaba esa pasada como «se midió, nada» y su recuadro decía «sin anomalía»; el minigráfico de mosaico contaba el
día como observado; el gráfico del diario no lo mostraba. Pasadas las 48 h, el operador no podía distinguir «no se pudo
medir el cráter» de «el cráter está frío». El verificador de la ronda 3 lo confirmó con gravedad 3.

Aparte (R3F5-V101): 14 records traen `t_bg_k = 0` (fondo no estimado). La tabla de index lo mostraba como -273,1 °C y la
tarjeta habría leído un ΔT de 259 a 279 K como «material caliente expuesto».

## Qué cambia (sólo display; no cambia detecciones, potencia publicada, nivel ni clase)

- Evolución de index: estado `no_medido` (raya naranja en la fila «no se pudo medir»), tooltip y recuadro con el texto de
  la marca; una pasada publicada con la marca lleva también la raya y «la potencia puede ser mayor».
- Minigráfico de mosaico: el día cuya pasada no midió el cráter no cuenta como observado; tooltip y raya naranja.
- Gráfico del diario: raya naranja arriba del día (llena: no medido; hueca: MIR saturada).
- Fondo 0 K: «sin fondo» en la tabla, «sin fondo estimado: ΔT no calculable» en la tarjeta, sin contraste en el popup y
  en `agua.js`.
- Todo sale de `frontend/crater_no_medido.js` (A102): `esNoMedido`, `marcasGrafico`, `plugin` y `fondoK`.

## Medición sobre los datos reales

`medir_marcas.js` corre con node las funciones reales extraídas de index y mosaico sobre `data/mirova_equivalent` y
`data/sombra_34` (la extracción sigue el método del verificador de la ronda 3). Misma raíz de datos para antes y después.

| | antes (frontend de main `aff1be71b`) | después |
|---|---:|---:|
| marcas «cráter no medido» en los records | 38 | 38 |
| con escena vacía (ya «sin datos») | 28 | 28 |
| dibujadas como «nada» o potencia sin aviso | 10 | **0** |
| recuadro «sin anomalía» con la marca | 9 | **0** |
| días de mosaico con la marca y sin aviso | 1 de 1 | **0 de 1** |
| fondos 0 K que la tabla muestra como «sin fondo» | 0 de 14 | **14 de 14** |
| control sintético (hueco de MIR de 3 píxeles) | `nada` | `no_medido` |

Salidas: `antes_salida.txt`, `despues_salida.txt` y el detalle por record en `antes.json` y `despues.json`.
Comandos (desde la raíz del árbol):

    node experiments/_s198_r3f5_evolucion/medir_marcas.js <raiz_con_el_frontend_de_main> experiments/_s198_r3f5_evolucion/antes.json <raiz_de_este_arbol>
    node experiments/_s198_r3f5_evolucion/medir_marcas.js <raiz_de_este_arbol> experiments/_s198_r3f5_evolucion/despues.json

Prueba: `tests/test_tablero_crater_no_medido_r3f5.py` (6 pruebas, cada una con su control; las 6 fallan con el frontend
de main). Verificado también en navegador real (servidor local): raya naranja `255,171,64` en la evolución de Mentolat
(2026-11-22 07:05) con el control vacío a 6 px; marca hueca de saturación en el diario y el mosaico de Chillán
(2026-11-22); sin errores de JavaScript.
