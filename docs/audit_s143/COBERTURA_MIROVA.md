# Cobertura de lo que MIROVA publica, y lo que publicamos de más

> Generado por `experiments/_s143_cobertura/cobertura_mirova.py` desde
> `experiments/_s142_linea_base/linea_base_post535.json` (2026-09-17T23:05:10+00:00). Ningún
> número escrito a mano (S91). Ventana: **2026-09-01 a 2026-09-17**, 17 noches, régimen
> posterior al PR #571 (A104: una ventana que cruce el #535 mezcla dos regímenes y no se
> puede leer). Referencia de MIROVA: CONS `{'sha': 'c09e0e8b07cc491e353491d05fdbe27fa7fd8f89', 'fecha_commit': '2026-09-17T23:01:08Z'}`,
> OCR `{'sha': 'f9805ad397dcaaa291833551e5d09508eda38b09', 'fecha_commit': '2026-09-17T11:32:09Z'}`. Publicar = predicado del dashboard
> ejecutado con node.

**Las dos cuentas van separadas a propósito.** La primera es la que da credibilidad: de lo
que MIROVA publicó, cuánto publicamos también. La segunda es lo que publicamos donde MIROVA
miró y no vio nada: ahí conviven señal real sub-umbral (A54) y artefacto topográfico (A69),
y esta tabla no los separa. Lo que mejora la detección y MIROVA no tiene va al perfil
`experimental`, nunca mezclado con la serie operacional.

## 0. Lo que hoy NO reproducimos (la lista que hay que dejar en cero)

- **Isluga, VIIRS750**: reproducimos 0.0 % de 1 pasadas con alerta (n<20, no se interpreta la tasa; son casos para mirar uno a uno).
- **PuyehueCordonCaulle, VIIRS750**: reproducimos 70.0 % de 10 pasadas con alerta (n<20, no se interpreta la tasa; son casos para mirar uno a uno).
- **Villarrica, VIIRS750**: reproducimos 0.0 % de 1 pasadas con alerta (n<20, no se interpreta la tasa; son casos para mirar uno a uno).

## 1. Por sensor

| sensor | reproducimos, por pasada | reproducimos, por noche de volcán | publicamos de más, por pasada | alertas de MIROVA sin record nuestro |
|---|---|---|---|---|
| MODIS | 100.0 % de 1 (n<20) | 100.0 % de 1 (n<20) | 11.2 % de 385 | 0 |
| VIIRS375 | 100.0 % de 129 | 100.0 % de 68 | 86.5 % de 325 | 0 |
| VIIRS750 | 68.8 % de 16 (n<20) | 91.7 % de 12 (n<20) | 21.0 % de 562 | 0 |
| CUALQUIERA | 96.6 % de 146 | 100.0 % de 71 | 34.8 % de 1272 | 0 |

## 2. Por volcán (VIIRS 375, que es donde vive el frente abierto)

| volcán | reproducimos, por pasada | reproducimos, por noche | publicamos de más, por pasada |
|---|---|---|---|
| Chaiten | 100.0 % de 8 (n<20) | 100.0 % de 6 (n<20) | 90.3 % de 31 |
| Copahue | sin casos | sin casos | 86.0 % de 50 |
| Isluga | 100.0 % de 32 | 100.0 % de 14 (n<20) | 66.7 % de 6 (n<20) |
| Lascar | 100.0 % de 18 (n<20) | 100.0 % de 9 (n<20) | 89.5 % de 19 (n<20) |
| Lastarria | 100.0 % de 9 (n<20) | 100.0 % de 7 (n<20) | 83.3 % de 18 (n<20) |
| Llaima | sin casos | sin casos | 80.4 % de 51 |
| NevadosDeChillan | 100.0 % de 3 (n<20) | 100.0 % de 3 (n<20) | 93.3 % de 45 |
| PlanchonPeteroa | 100.0 % de 8 (n<20) | 100.0 % de 5 (n<20) | 82.8 % de 29 |
| PuyehueCordonCaulle | 100.0 % de 27 | 100.0 % de 10 (n<20) | 94.4 % de 18 (n<20) |
| Tupungatito | 100.0 % de 20 | 100.0 % de 10 (n<20) | 92.9 % de 14 (n<20) |
| Villarrica | 100.0 % de 4 (n<20) | 100.0 % de 4 (n<20) | 84.1 % de 44 |

## 3. Controles del instrumento

- Identidad del predicado (node contra el dashboard): **True**.
- Con un predicado que publica todo: recall 1,0 y publicación de más 1,0 por construcción.
- Con uno que no publica nada: 0,0 y 0,0. Las dos cotas se calculan en cada corrida, así que
  una tasa pegada a un extremo se distingue de un instrumento roto.

## 4. Cómo leer esto

1. **Una tasa con n < 20 no se interpreta**: va marcada y sirve para saber que falta muestra,
   no para concluir. VIIRS 750 en el régimen actual tiene pocas alertas.
2. **La segunda columna no es precisión.** No hay forma de decir, sin mirar caso a caso, si una
   publicación en negativo limpio es calor real que MIROVA no alcanza a ver o ruido del
   gradiente topográfico. El A/B abierto (D22 y D25) ataca exactamente esa cuenta.
3. **Las alertas de MIROVA sin record nuestro** son el número más grave si deja de ser cero:
   significa que ni siquiera procesamos esa pasada.
