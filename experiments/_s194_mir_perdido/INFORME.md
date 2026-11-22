# Marca «cráter no medido» en el tablero (S194, Codex C1-102 y C1-V202)

Base: `origin/main` 852279400 (2026-11-22, datos hasta 2026-11-22 09:33 UTC). Script:
`experiments/_s194_mir_perdido/medir_mir_perdido.py --modulo`; salida íntegra en `medir_mir_perdido_salida.txt` y
`resultado.json`. Ningún número de este informe está transcrito a mano de otra fuente.

## El fenómeno

El infrarrojo medio (MIR, cerca de 4 µm) es la banda que ve el calor. A veces llega sin dato en uno o más píxeles sobre
el cráter: una línea de barrido perdida o un píxel con calibración fallida en VIIRS, o las dos bandas MIR saturadas en
MODIS. La vía «código MIROVA» interpola la grilla con los vecinos antes de buscar anomalías, y los vecinos son más
fríos. Si el foco caía en el hueco, la pasada sale «sin anomalía» (foco aislado) o con sólo una parte de la potencia
(foco con vecinos tibios; en el gránulo sintético del verificador, 11,5 MW en vez de 464). Para el operador, «no se
pudo medir el cráter» y «el cráter está frío» son cosas distintas.

La vía ya lo anota en `diag_codigo_mirova` (#1060, ficha v1.47; separado por causa desde #1077, ficha v1.61). El
tablero no lo leía.

## Lo medido

1. **Las claves existen en los datos guardados, pero sólo en lo procesado desde el 2026-11-20.** De 77.172 records,
   543 las traen: 329 con el conteo sin separar (procesados del 2026-11-20 02:18 al 2026-11-21 17:22 UTC) y 214 con
   las claves separadas por causa (procesados el 2026-11-22). La historia desde 2025-02-15 no las tiene: SIN DATO.
2. **Hueco real de MIR (`px_mir_hueco_crater > 0`): 0 de 214 records.** El caso de C1-102 y C1-V202 no aparece todavía
   en datos reales; sigue siendo un mecanismo confirmado en el código y reproducido con un gránulo sintético.
3. **Bow-tie: 27 de 214 records** (13 VIIRS 375, 14 VIIRS 750); en los 27 el total inválido es todo bow-tie
   (`px_mir_invalido_crater == px_bowtie_crater`). El tablero hoy los muestra 25 «sin anomalía», 1 «anomalía no
   publicada», 1 publicada.
4. **Sin separar con inválido > 0: 70 records** (33 VIIRS 375, 37 VIIRS 750); hoy 63 «sin anomalía», 4 publicadas, 3
   «anomalía no publicada».
5. **Barrido sin posición sobre el cráter: 6 records**, los 6 ya rotulados «escena sin datos» (motivo_vacio
   `escena_invalida`).
6. **MIR saturada (VIIRS): 1 record real**, Nevados de Chillán, NOAA-20 375 m, 2026-11-22 06:48 UTC, publicado con
   25,806 MW en la cumbre, 1 píxel saturado.

## Qué se marca y por qué

- **Se marca** el hueco de MIR (`px_mir_hueco_crater`), el barrido sin posición (`crater_sin_posicion`) y, con otro
  texto, la MIR saturada (`px_saturados_crater`: la potencia de esos píxeles es un mínimo; Codex F1V-101 y F4-104).
- **No se marca el bow-tie.** El borde de cada barrido de VIIRS repite el suelo que ya midió el barrido vecino y VIIRS
  lo descarta a bordo: no se pierde información (ficha v1.61; aquí 27 de 27). Marcarlo pondría «cráter no medido» en
  27 pasadas que sí lo midieron.
- **No se marca el conteo sin separar** (70 records): mezcla bow-tie y hueco y no se pueden separar; con 27 de 27
  bow-tie en lo separado y 105 de 105 en el probe S192, casi seguro son relleno. El pipeline dice que el paso del
  tablero debe leer el hueco, no el total (`mirova_v750_codigo.py`, `dato_faltante_crater`).
- **No se marca el hueco de TIR**: su efecto es otro (S191, tir_perdida) y no hay texto verificado para el operador.

Con este criterio, hoy llevan la marca 7 records: los 6 de barrido sin posición (ya «escena sin datos»; la marca agrega
que fue el cráter lo que quedó sin posición) y el de Chillán saturado. `frontend/crater_no_medido.js` da lo mismo que
el predicado en Python en los 77.172 records (0 distintos) y en los 7 casos sintéticos.

## Dónde se ve

Módulo común `frontend/crater_no_medido.js` (como `cumbre.js`). Sólo display: no cambia valor, nivel, clase ni
frescura.

| Vista | Dónde | Texto |
|---|---|---|
| index | tabla «Últimas pasadas», las dos ramas (sin anomalía y publicada), en la celda «Zona» | «⊘ cráter no medido: MIR sin dato en 2 píxeles» |
| index | popup del mapa | la misma línea |
| index | tarjeta del volcán: la pasada nocturna más reciente de 48 h con la marca, salvo que la detección de la tarjeta sea otra pasada más nueva; no exige detección | «⊘ Pasada del 2026-11-22 06:48 UTC (VIIRS_NOAA20_750): cráter no medido: ...» |
| mosaico | tarjeta, igual que index | igual |
| diario | conteo del período en la línea de detecciones | «(⊘ 1 pasada con el cráter sin medir entero o la MIR saturada)» |

## Verificación

- `tests/test_tablero_crater_no_medido_s194.py`: 8 pruebas, cada una con su control (el mismo record sin la marca no
  avisa; bow-tie, sin separar y TIR no avisan). Mutaciones a mano: 20 de 20 atrapadas por aserción
  (`mutaciones_salida.txt`).
- Navegador real (servidor estático sobre una copia del sitio en `D:\vrp-trabajo\temporales\s194_mir_perdido\sitio`,
  capturas en `D:\vrp-trabajo\temporales\s194_mir_perdido\`): Chillán saturado y Tupungatito sin posición son
  records reales sin tocar; para el hueco de MIR, como ningún record real lo trae, se inyectó en la copia
  `px_mir_hueco_crater` en dos records reales (Villarrica NOAA-20 750 m 06:48, «sin anomalía»; Láscar NOAA-21 750 m
  05:42, publicado 0,242 MW). Index (tarjeta, tabla, popup), mosaico y diario muestran la marca; el record vecino sin
  marca no la muestra; sin errores de JavaScript (sólo 404 de archivos que la copia parcial no trae).

## Qué no cubre

- La historia anterior al 2026-11-20 no tiene las claves; esas pasadas no se marcan y eso no dice que el cráter se haya
  medido. Recuperarlas exige reprocesar (A45, decisión de Nicolás).
- El gráfico de evolución no distingue la pasada con el cráter no medido de la que no vio nada.
- Qué habría hecho MIROVA con un hueco: SIN DATO (el `.m` publicado recibe la grilla ya remuestreada).
- Saturación en MODIS: no tiene bit; la doble saturación llega como hueco de MIR y entra por esa vía.
