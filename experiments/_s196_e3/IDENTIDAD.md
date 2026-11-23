# La franja diurna de MODIS en la comparación diaria: identidad nocturna y lo que cambia (S196, E3)

**Qué se cambió.** `scripts/comparacion_via_k.py` marca cada pasada (nuestra y de MIROVA) como noche o día con la
elevación solar sobre el volcán (`pipeline/store.py::_solar_elevation`, mayor que 0 es día; la misma regla que
`frontend/diurno.js`) y cuenta cada franja aparte. La noche sigue como antes (vía, K y MIROVA). El día, sólo MODIS
(#1090), compara la vía con MIROVA: la guardia K no procesa de día. Salida nueva: `resultados["<ref>|dia|MODIS"]` y la
tabla `dias`; la pestaña «Vía, K y MIROVA» de `frontend/comparacion.html` las muestra en la sección «☀ MODIS de día».

**Por qué hacía falta, además de sumar el día.** Desde S193 la regla de auditoría deja pasar el día de MODIS después del
primer record diurno (2026-11-15 12:30 UTC). La comparación de main no separaba, y el día se colaba en la noche por dos
lados: (1) una fila diurna de MIROVA con alerta o con calor lejos del volcán marcaba la fecha y le quitaba el negativo
limpio a las pasadas nocturnas MODIS de la misma fecha; (2) una pasada diurna nuestra entraba en la fila de esa noche-satélite de la franja «Noche a noche».

## Prueba de identidad

`identidad.py` corre la versión de main (`89cf56755`) y la nueva con los mismos datos (records de producción y guardias
de este checkout, caché de K, y la referencia de MIROVA bajada una vez: consolidado `90f64fcce`, OCR `e0e2f9de9` de
Mirova-v1). Salida completa en `identidad.json`.

| Prueba | Resultado |
|---|---|
| A. `--hoy 2026-11-14` (antes del primer record diurno): los 12 resultados y las 2.400 filas de noches | **idénticos** |
| B. `--hoy 2026-11-23`: las 6 ventanas «historia» (terminan antes del 15-nov) | **idénticas** |
| B. `--hoy 2026-11-23`: las 2.400 filas de noches anteriores al 15-nov | **idénticas** |
| B. Filas de noches desde el 15-nov | main 84, nueva 83: 1 distinta |
| B. Ventanas «desde la adopción» de VIIRS 375 y 750 | idénticas |
| B. Ventana «desde la adopción» de MODIS | cambia, a propósito (abajo) |

Resultado del script: `IDENTIDAD OK`.

## Lo que cambia desde el 15-nov, y por qué es la corrección

- **MODIS desde la adopción, tabla y combinado:** los negativos limpios bien callados suben de 409 a 417 en la vía y de
  404 a 412 en K. Son 8 noches-satélite tranquilas que main dejaba sin juzgar porque MIROVA tenía esa fecha una fila
  diurna FALSO_POSITIVO (calor lejos del volcán, etiqueta del scraper): Láscar 16-nov 13:10 y 21-nov 13:05 y 20:05,
  Lastarria 21-nov 20:05, Copahue 19-nov 20:25. Cada fecha anulaba las dos noches MODIS (Terra y Aqua): Láscar 4,
  Lastarria 2, Copahue 2. Aciertos, silencios, falsas alarmas, protegidas (26, 1 perdida en la vía, 5 en K) y cocientes
  no cambian; recall y precisión tampoco.
- **Pasadas MODIS «sin par» de la vía:** de 179 a 22. Las 157 que salen son las diurnas medidas, que en main quedaban
  como «sin par» porque K no tiene día (una de ellas, la protegida de Chillán del 22-nov, aparecía como «alerta sólo en
  la vía, fuera de la cuenta»).
- **La fila que desaparece:** Nevados de Chillán, MODIS_TERRA, 2026-11-15. En main se dibujaba como una noche en que
  MIROVA «miró y no vio nada» y la vía publicó 10,7 MW en la cumbre, o sea una falsa alarma nocturna. Eran dos pasadas
  distintas mezcladas en una fila: la publicación es de la pasada nocturna de las 01:35, que MIROVA no lista en su tabla
  (sin juicio), y el «no vio nada» es de la diurna de las 12:35 (fila RUTINA con 0 MW). Ahora la nocturna queda sin juicio
  y la diurna cuenta como día-satélite tranquilo bien callado.

## La franja diurna (2026-11-15 a 2026-11-23)

- 179 records MODIS diurnos en producción; 22 son escenas que la vía no pudo medir (21 por reflejo solar, 1 escena
  inválida) y quedan fuera como en la noche (#1005); quedan 157 pasadas.
- Etiquetas con la tabla de MIROVA: 151 negativos limpios, 1 alerta, 5 sin juicio. Por día-satélite: 1 acierto, 0
  silencios, 0 falsas alarmas en 146 días-satélite tranquilos, 1 protegida y 0 perdidas; cociente de VRP 1,096. Igual con
  tabla más OCR.
- La alerta es la de Nevados de Chillán, MODIS_AQUA, 2026-11-22 20:40 UTC: MIROVA 6,07 MW, la vía 6,65 MW en la cumbre a
  0,39 km.
- Con un solo día-satélite con alerta, la franja diurna no dice todavía nada de recall; lo que sí dice es que en 146
  días-satélite tranquilos la vía no publicó nada. Ojo con los 21 de reflejo solar: el día pierde cerca del 12 % de las
  escenas (21 de 179) por el corte de reflejo solar que la vía toma del código de MIROVA (D36).

## Pruebas de CI

`tests/test_comparacion_dia_modis_s196.py`: un caso de punta a punta con node y el predicado real del tablero pone en la
misma fecha una noche tranquila y una alerta diurna de MIROVA, y exige que los números nocturnos sean los mismos con y sin
el día y que el día dé un acierto protegido de la vía. Dejar entrar a la noche las filas diurnas de MIROVA, o nuestras
pasadas diurnas, hace fallar la prueba (las dos mutaciones se probaron a mano y fallan).
