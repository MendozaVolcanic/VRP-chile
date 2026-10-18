# Segundo instrumento para F y K (REGLA_ADOPCION.md §4.3)

Fecha: 2026-10-18. Carpeta: `C:\Users\nmend\AppData\Local\Temp\claude\r3_fk\`. No se tocó el repo.

## Qué se hizo

Un evaluador nuevo, `C:\Users\nmend\AppData\Local\Temp\claude\r3_fk\segundo_instrumento.py`, escrito
desde el texto y no desde el código del evaluador oficial. No importa `evaluar_fk`, `banco_paridad`,
`clase_mirova`, `referencia_mirova_unificada` ni nada de `pipeline/`. Reimplementa:

- **noche**: elevación solar menor o igual a 0 en las coordenadas de `volcanoes.yaml`, con un cálculo
  propio (ecuaciones de la NOAA), porque los dos flags diurnos de producción están apagados;
- **referencia**: los CSV congelados (`_congelado_v1`, `_congelado_v2`), con la unión que describe el
  docstring de `referencia_mirova_unificada.py` (consolidado, OCR, capa histórica, respaldo; gana la
  primera capa que trae la clave), lectura propia de nombres de volcán y de sensor ("VIIRS" a secas es
  750 m), y en V2 sin filas OCR (tabla sola) y VIIRS sólo desde el 2026-04-01;
- **etiquetas por pasada**, a ±120 s: alerta, protegida A (alerta de 1 MW o más), protegida B (cualquier
  fila no RUTINA de 1 MW o más), negativo limpio (RUTINA del consolidado con VRP 0 y la noche de ese
  volcán y sensor sin alerta ni falso positivo), solo OCR de Suomi NPP (sólo V1);
- **"publica"**: el predicado del tablero ejecutado con node, extrayendo por nombre las funciones de
  `frontend/index.html` con un extractor propio, y con las guardas de `latestDetection` (cumbre,
  detección válida, sensor visible, no artefacto, magnitud de display mayor que 0). Control sintético:
  da `[1, 0, 0, 0]` en los cuatro casos esperados.

Salidas: `salida.txt`, `resultado.json`, `pasadas_V1.jsonl` y `pasadas_V2.jsonl` (cada pasada con su
etiqueta y la decisión de cada brazo), y `controles.py` con `controles_salida.txt`.

## Resultado: coincide en todo, número por número y pasada por pasada

| ventana | sensor | qué | evaluador oficial (v1.log / v2.log) | segundo instrumento |
|---|---|---|---|---|
| V1 | MODIS | sustrato: pasadas, alertas, protegidas A, negativos limpios | 944, 8, 4, 893 | 944, 8, 4, 893 |
| V1 | VIIRS 375 | sustrato | 1944, 260, 21 (9 solo OCR SNPP), 832 | igual |
| V1 | VIIRS 750 | sustrato | 1932, 42, 12 (2 solo OCR SNPP), 1303 | igual |
| V1 | los tres | P1 lectura A, K: pérdidas netas | 0, 0, 0 | 0, 0, 0 |
| V1 | VIIRS 375 | P1 A, K: solo OCR SNPP (no deciden) | Tupungatito 09-28 05:18 y 09-29 04:54 | las mismas dos |
| V1 | MODIS | P1 A, K: recuperada | Chillán 10-01 08:35 (5,18 MW) | la misma |
| V1 | VIIRS 375 | P1 lectura B, K y F: perdidas | 12 | las mismas 12 |
| V1 | MODIS | P2 C0 / K | 4+110 = 114 / 3+7 = 10 | 114 / 10 |
| V1 | VIIRS 375 | P2 C0 / K (con SNPP) | 0+734 = 734 / 16+21 = 37 (40) | 734 / 37 (40) |
| V1 | VIIRS 750 | P2 C0 / K | 10+321 = 331 / 14+12 = 26 | 331 / 26 |
| V1 | MODIS | §9 C0 / K: recall, protegidas A, negativos | 3/8, 3/4, 110/893 / 5/8, 4/4, 7/893 | igual |
| V1 | VIIRS 375 | §9 C0 / K | 260/260, 21/21, 734/832 (88,2 %) / 239/260, 19/21, 21/832 (2,5 %) | igual |
| V1 | VIIRS 750 | §9 C0 / K | 32/42, 12/12, 321/1303 / 28/42, 12/12, 12/1303 | igual |
| V2 | MODIS | sustrato | 2443, 65, 39, 2254 | igual |
| V2 | VIIRS 375 | sustrato | 3396, 426, 38, 1010 | igual |
| V2 | VIIRS 750 | sustrato | 3373, 117, 42, 1829 | igual |
| V2 | los tres | P1 A, K: pérdidas netas | 0, 0, 0 | 0, 0, 0 |
| V2 | MODIS | P1 A, K: recuperadas | 33 (Láscar) | las mismas 33 |
| V2 | VIIRS 375 / 750 | P1 lectura B, K: pendientes | 30 / 1 | las mismas 30 / 1 |
| V2 | MODIS | P2 C0 / K | 25+243 = 268 / 5+20 = 25 | 268 / 25 |
| V2 | VIIRS 375 | P2 C0 / K | 0+863 = 863 / 26+37 = 63 | 863 / 63 |
| V2 | VIIRS 750 | P2 C0 / K | 22+398 = 420 / 26+20 = 46 | 420 / 46 |
| V2 | MODIS | §9 C0 / K | 7/65, 6/39, 243/2254 / 60/65, 39/39, 20/2254 | igual |
| V2 | VIIRS 375 | §9 C0 / K | 426/426, 38/38, 863/1010 (85,4 %) / 400/426, 38/38, 37/1010 (3,7 %) | igual |
| V2 | VIIRS 750 | §9 C0 / K | 95/117, 42/42, 398/1829 / 91/117, 42/42, 20/1829 | igual |

También coinciden F y G de V1 (todas sus filas de P2 y §9) y las protegidas B por sensor. Las listas
de pasadas de P1 (recuperadas, solo OCR SNPP, perdidas de B) se compararon como conjuntos contra las
líneas de los logs: iguales en los 27 casos. **No hay diferencias que explicar.**

## Controles: ¿coincide por la razón correcta?

1. **K calla porque no detecta, no por un cambio de esquema.** En los negativos limpios de VIIRS 375
   que C0 publica y K no (713 en V1, 826 en V2), en K cae la guarda de cumbre en 710 y 822, y en 661 y
   786 de ellos K no tiene ningún píxel anómalo ni cúmulo. En C0, 675 de 713 y 783 de 826 llevaban
   `triggered_test1`: lo que C0 publicaba ahí lo publicaba el Test 1 integrado, que K no tiene. Es el
   mecanismo que el pre-registro describe (§1).
2. **Noche.** Ninguna pasada que mi cálculo llama nocturna trae en el record un cenit solar menor que
   90°. Los conteos de pasadas salen iguales a los del evaluador, que usa otra implementación.
3. **Nombres.** Ninguna fila de los ocho CSV congelados queda fuera por nombre de volcán no reconocido.
4. **Sensibilidad al pareo.** A ±60 s todo queda igual. A ±300 s sólo cambia MODIS: V1 gana 1 alerta
   Muy Bajo y 23 negativos (P2 C0 117, K 11), V2 gana 60 negativos (P2 C0 274, K 26). VIIRS no se mueve.
   Ningún veredicto cambia.

## Lo que este segundo instrumento NO puede ver

- **Comparte los insumos**: la misma referencia congelada, los mismos records unidos y el mismo
  `index.html`. Un defecto en la unión de intentos, en los CSV congelados o en el propio predicado del
  tablero pasaría igual por los dos. Lo independiente es el cálculo, no los datos.
- **Comparte las definiciones**, porque las dos salen del mismo texto: el ±120 s, la noche por fecha
  UTC, "negativo limpio" exige la noche entera sin alerta. El control 4 muestra que el ±120 s deja fuera
  algunas filas MODIS de MIROVA que caen 3 a 5 minutos de nuestra hora (MIROVA rotula MODIS con el inicio
  del gránulo de 5 minutos); no cambia el resultado, pero es una elección común a los dos.
- **Guardas redundantes en esta muestra**: quitar la guarda de cumbre o la de artefacto no cambia ningún
  conteo de negativos de VIIRS 375; el trabajo lo hacen `isValidDetection` y el control de radio interior
  dentro de `mirovaEqVrp`. El predicado sí está vivo (C0 734 contra K 21 con el mismo predicado, y el
  control sintético da 0 en el caso lejano y en el cúmulo sin energía).
- No reproduje P3 (magnitud) ni P4 (movimiento del cúmulo): la tarea pedía P1, P2 y la tabla de §9.
