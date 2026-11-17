# S190: auditoría del centro de los 45 volcanes

Pedido: Nicolás notó que el centro de Mentolat está corrido (el volcán está un poco más al sur). Se auditó el centro de
los 45 volcanes de `volcanoes.yaml` y se corrigen los que tienen fuente clara.

## Por qué importa el centro

En la vía «código MIROVA» el centro hace dos cosas. Primero, apoya la grilla UTM de 51 × 51 km del volcán y su caja
ROI (`pipeline/grillas_mirova.yaml`, `x0`, `y0`): la caja sensible de VIIRS 750 es de 7 × 7 celdas alrededor de ese
punto, unos 2,6 km a cada lado, así que un centro corrido 3 km deja el cráter en el borde de la zona donde la vía mira
con más sensibilidad. Segundo, es el punto desde donde se mide la distancia de cada alerta. En los 34 que no son Tier
A el pipeline no clasifica (no tienen `inner_radius_km` y dejan `distance_class: null`); el tablero los rotula
«cumbre» si el centroide del cúmulo queda a 5 km o menos (`frontend/index.html`, `inner_radius_km: 5` para la sombra
de los 34), con la distancia que se guardó al procesar.

## Fuentes y orden de autoridad

1. **Los 11 Tier A**: el KMZ y los TIF de MIROVA (A5, ya adoptado). No se tocan. Comprobado: 8 tienen la grilla a
   0,09 km del yaml (redondeo del TIF); Lascar, PlanchonPeteroa y Tupungatito a 0,23, 1,83 y 2,85 km, que son los
   puntos propios de MIROVA ya documentados en la cabecera de `pipeline/grillas_mirova.yaml` (INFORME GEO de S159).
   La RNVV difiere de nuestro centro en varios Tier A (PCC 7,9 km, Tupungatito 2,0 km), pero ahí manda MIROVA y la
   distancia se mide desde `vent_lat/vent_lon`, verificado por Nicolás.
2. **Los 34**: la ficha RNVV de SERNAGEOMIN (`WEBRNVV/fichas_nuevas_json/_lista.json`), contrastada con el GVP del
   Smithsonian (WFS público `webservices.volcano.si.edu/geoserver/GVP-VOTW/ows`, capas
   `Smithsonian_VOTW_Holocene_Volcanoes` y `Smithsonian_VOTW_Pleistocene_Volcanoes`, consultadas el 2026-11-17).

**Reserva sobre la RNVV**: 29 de sus 43 fichas traen las coordenadas con 2 decimales o menos (0,01° es 1,1 km en latitud y
unos 0,85 km en longitud a 40° S). Una diferencia de 1,1 km puede ser sólo redondeo de la ficha. Por eso la regla
exige que una segunda fuente independiente esté de acuerdo.

**Regla**: se cambia el centro sólo si la RNVV está a más de 1 km del nuestro **y** la RNVV y el GVP están a 1 km o
menos entre sí. Si la RNVV está lejos pero el GVP coincide con nuestro centro, queda **DUDOSO** y no se toca.

## De dónde salieron nuestros centros

`git log -S` en `volcanoes.yaml`: los 34 entraron en `d1d8952f7` (2026-04-05, «Expand to 45 volcanoes»), con `gvp_id`
y sin fuente declarada. La tabla muestra que 17 de los 34 coinciden con el GVP de hoy a 0,0 km: salieron del GVP
redondeado. Donde no coinciden, el GVP corrigió sus coordenadas después (Mentolat, Callaqui, Michinmahuida,
Corcovado) o el `gvp_id` apuntaba a otro edificio. Laguna del Maule la fijó Nicolás en `5c71e207a` (2026-04-16,
centro de la laguna). La grilla de los 34 sale del yaml por la regla de S172 (`abd27e198`,
`experiments/_s172_sombra34/generar_grillas_34.py`).

Tres `gvp_id` del yaml estaban mal: MacaCay traía 358055 (Cay, 17 km al este) y su centro es el de Macá (358056);
Tolhuaca traía 357106 y AntillancaCasablanca 358001, números que el GVP no tiene (son 357093 y 357153). Se corrigen.

## Tabla

Generada por `auditar_centros.py --md` (los números del texto salen de sus líneas RESUMEN) sobre el `volcanoes.yaml` de `origin/main` antes del cambio (`db04d930c`).
Rumbo: de nuestro centro hacia el de la RNVV. Alertas: records con `vrp_mw > 0` en `data/historia_34` más
`data/sombra_34`; «a cumbre» y «a lejos» cuentan los que cambiarían de rótulo en el tablero (centroide contra 5 km) si
se midiera desde el centro RNVV. Control del instrumento: la distancia recalculada desde el centro viejo difiere de la
guardada en 0,123 km o menos en todos (el cuantizado de la grilla).

| Volcán | Nuestro centro | RNVV | GVP | Nuestro a RNVV (km, rumbo) | Nuestro a GVP (km) | RNVV a GVP (km) | Alertas | A cumbre | A lejos | Recomendación |
|---|---|---|---|---|---|---|---|---|---|---|
| PuyehueCordonCaulle | -40,5900; -72,1170 | -40,5227; -72,1454 | -40,590; -72,117 | 7,86 N (342°) | 0,00 | 7,86 |  |  |  | Tier A: KMZ de MIROVA, no se toca |
| Villarrica | -39,4200; -71,9300 | -39,4198; -71,9375 | -39,420; -71,930 | 0,64 O (272°) | 0,00 | 0,64 |  |  |  | Tier A: KMZ de MIROVA, no se toca |
| Lascar | -23,3690; -67,7320 | -23,3600; -67,7300 | -23,370; -67,730 | 1,02 N (12°) | 0,23 | 1,11 |  |  |  | Tier A: KMZ de MIROVA, no se toca |
| Antuco | -37,4060; -71,3490 | -37,4100; -71,3500 | -37,406; -71,349 | 0,45 S (191°) | 0,00 | 0,45 | 0 | 0 | 0 | se queda |
| Copahue | -37,8560; -71,1830 | -37,8568; -71,1697 | -37,856; -71,183 | 1,17 E (94°) | 0,00 | 1,17 |  |  |  | Tier A: KMZ de MIROVA, no se toca |
| DescabezadoGrande | -35,5800; -70,7500 | -35,5900; -70,7500 | -35,580; -70,750 | 1,11 S (180°) | 0,00 | 1,11 | 0 | 0 | 0 | DUDOSO: se queda |
| CerroAzulQuizapu | -35,6530; -70,7610 | no está | -35,653; -70,761 |   | 0,00 |  | 1 | 0 | 0 | sin RNVV: se queda |
| LagunaDelMaule | -36,0568; -70,5014 | -36,0600; -70,5100 | -36,058; -70,492 | 0,85 SO (246°) | 0,85 | 1,63 | 0 | 0 | 0 | se queda |
| NevadoDeLongavi | -36,1930; -71,1610 | -36,2000; -71,1600 | -36,196; -71,164 | 0,78 S (173°) | 0,43 | 0,59 | 0 | 0 | 0 | se queda |
| NevadosDeChillan | -36,8630; -71,3770 | -36,8671; -71,3778 | -36,868; -71,378 | 0,46 S (189°) | 0,56 | 0,10 |  |  |  | Tier A: KMZ de MIROVA, no se toca |
| Callaqui | -37,9200; -71,4500 | -37,9300; -71,4500 | -37,928; -71,446 | 1,11 S (180°) | 0,90 | 0,41 | 0 | 0 | 0 | CAMBIAR a RNVV |
| Lonquimay | -38,3800; -71,5800 | -38,3790; -71,5860 | -38,379; -71,586 | 0,53 O (282°) | 0,53 | 0,00 | 0 | 0 | 0 | se queda |
| Tolhuaca | -38,3100; -71,6450 | no está | -38,310; -71,645 |   | 0,00 |  | 2 | 0 | 0 | sin RNVV: se queda |
| Llaima | -38,6920; -71,7290 | -38,6921; -71,7295 | -38,692; -71,729 | 0,04 O (256°) | 0,00 | 0,04 |  |  |  | Tier A: KMZ de MIROVA, no se toca |
| Sollipulli | -38,9700; -71,5200 | -38,9800; -71,5200 | -38,970; -71,520 | 1,11 S (180°) | 0,00 | 1,11 | 0 | 0 | 0 | DUDOSO: se queda |
| Quetrupillan | -39,4960; -71,7220 | -39,5000; -71,7200 | -39,496; -71,722 | 0,48 S (159°) | 0,00 | 0,48 | 1 | 0 | 0 | se queda |
| Lanin | -39,6330; -71,5030 | -39,6400; -71,5000 | -39,637; -71,502 | 0,82 S (162°) | 0,45 | 0,37 | 1 | 0 | 0 | se queda |
| MochoChoshuenco | -39,9270; -72,0270 | -39,9300; -72,0300 | -39,927; -72,027 | 0,42 SO (217°) | 0,00 | 0,42 | 0 | 0 | 0 | se queda |
| CarranLosVenados | -40,3500; -72,0700 | -40,3700; -72,0700 | -40,350; -72,070 | 2,22 S (180°) | 0,00 | 2,22 | 5 | 0 | 0 | DUDOSO: se queda |
| AntillancaCasablanca | -40,7700; -72,1500 | -40,7800; -72,1600 | -40,783; -72,150 | 1,39 SO (217°) | 1,45 | 0,91 | 2 | 1 | 0 | CAMBIAR a RNVV |
| Osorno | -41,1000; -72,4930 | -41,1051; -72,4965 | -41,105; -72,496 | 0,64 SO (208°) | 0,61 | 0,05 | 0 | 0 | 0 | se queda |
| Calbuco | -41,3300; -72,6140 | -41,3265; -72,6137 | -41,330; -72,618 | 0,39 N (4°) | 0,33 | 0,53 | 1 | 0 | 0 | se queda |
| YateHornopiren | -41,7600; -72,3900 | -41,7581; -72,3976 | -41,755; -72,396 | 0,66 O (289°) | 0,75 | 0,37 | 1 | 0 | 0 | se queda |
| Huequi | -42,3770; -72,5780 | -42,3800; -72,5800 | -42,377; -72,578 | 0,37 SO (206°) | 0,00 | 0,37 | 1 | 0 | 0 | se queda |
| Michinmahuida | -42,7900; -72,4400 | -42,8000; -72,4500 | -42,799; -72,445 | 1,38 SO (216°) | 1,08 | 0,42 | 1 | 0 | 0 | CAMBIAR a RNVV |
| Chaiten | -42,8330; -72,6460 | -42,8400; -72,6500 | -42,835; -72,651 | 0,84 SO (203°) | 0,49 | 0,58 |  |  |  | Tier A: KMZ de MIROVA, no se toca |
| CorcovadoYanteles | -43,1830; -72,8000 | -43,1900; -72,7900 | -43,189; -72,794 | 1,12 SE (134°) | 0,83 | 0,34 | 0 | 0 | 0 | CAMBIAR a RNVV |
| Melimoyu | -44,0800; -72,8800 | -44,0700; -72,8700 | -44,080; -72,880 | 1,37 NE (36°) | 0,00 | 1,37 | 0 | 0 | 0 | DUDOSO: se queda |
| Mentolat | -44,6700; -73,0800 | -44,7000; -73,0800 | -44,693; -73,077 | 3,34 S (180°) | 2,58 | 0,81 | 1 | 0 | 0 | CAMBIAR a RNVV |
| MacaCay | -45,1000; -73,2000 | -45,1050; -73,1693 | -45,100; -73,170 | 2,47 E (103°) | 2,35 | 0,56 | 1 | 0 | 0 | CAMBIAR a RNVV |
| Hudson | -45,9000; -72,9700 | -45,9000; -72,9700 | -45,900; -72,970 | 0,00 N (0°) | 0,00 | 0,00 | 0 | 0 | 0 | se queda |
| Tinguiririca | -34,8140; -70,3520 | -34,8200; -70,3400 | -34,814; -70,352 | 1,28 SE (121°) | 0,00 | 1,28 | 146 | 1 | 0 | DUDOSO: se queda |
| PlanchonPeteroa | -35,2400; -70,5680 | -35,2400; -70,5700 | -35,223; -70,568 | 0,18 O (270°) | 1,89 | 1,90 |  |  |  | Tier A: KMZ de MIROVA, no se toca |
| Lastarria | -25,1680; -68,5070 | no está | -25,168; -68,507 |   | 0,00 |  |  |  |  | Tier A: KMZ de MIROVA, no se toca |
| Isluga | -19,1500; -68,8300 | -19,1600; -68,8200 | -19,150; -68,830 | 1,53 SE (137°) | 0,00 | 1,53 |  |  |  | Tier A: KMZ de MIROVA, no se toca |
| Taapaca | -18,1000; -69,5000 | -18,1100; -69,5100 | -18,100; -69,500 | 1,53 SO (224°) | 0,00 | 1,53 | 260 | 2 | 0 | DUDOSO: se queda |
| Parinacota | -18,1660; -69,1420 | -18,1600; -69,1400 | -18,166; -69,142 | 0,70 N (18°) | 0,00 | 0,70 | 263 | 1 | 0 | se queda |
| Guallatiri | -18,4200; -69,0900 | -18,4204; -69,0929 | -18,420; -69,092 | 0,31 O (261°) | 0,21 | 0,11 | 340 | 0 | 0 | se queda |
| Irruputuncu | -20,7300; -68,5500 | -20,7300; -68,5600 | -20,730; -68,550 | 1,04 O (270°) | 0,00 | 1,04 | 388 | 0 | 2 | DUDOSO: se queda |
| OlcaParuma | -20,9420; -68,5030 | no está | -20,939; -68,413 |   | 9,35 |  | 286 | 0 | 0 | sin RNVV: se queda |
| Ollague | -21,3000; -68,1800 | -21,3100; -68,1800 | -21,300; -68,180 | 1,11 S (180°) | 0,00 | 1,11 | 308 | 0 | 1 | DUDOSO: se queda |
| SanPedro | -21,8800; -68,4000 | -21,8900; -68,3900 | -21,888; -68,391 | 1,52 SE (137°) | 1,29 | 0,25 | 284 | 2 | 1 | CAMBIAR a RNVV |
| Putana | -22,5570; -67,8530 | no está | -22,557; -67,853 |   | 0,00 |  | 379 | 0 | 0 | sin RNVV: se queda |
| SanJose | -33,7890; -69,8970 | -33,7900; -69,8900 | -33,789; -69,895 | 0,66 E (100°) | 0,18 | 0,48 | 225 | 0 | 1 | se queda |
| Tupungatito | -33,4000; -69,8000 | -33,3996; -69,8213 | -33,425; -69,797 | 1,98 O (271°) | 2,79 | 3,62 |  |  |  | Tier A: KMZ de MIROVA, no se toca |

## Qué se cambia (PR)

Siete volcanes, al centro de la ficha RNVV. Dos están en el límite de la regla: en Callaqui y CorcovadoYanteles el
centro viejo ya estaba a menos de 1 km del GVP de hoy (0,90 y 0,83 km) y lo que se mueve es un paso del redondeo de
la ficha; se cambian igual porque el GVP también se corrió en esa dirección y las dos fuentes quedan a 0,41 y 0,34 km
entre sí.

| Volcán | Antes | Después (RNVV) | Desplazamiento | Tanda |
|---|---|---|---|---|
| Callaqui | -37,92; -71,45 | -37,93; -71,45 | 1,11 km S | 4, sin despachar |
| AntillancaCasablanca | -40,77; -72,15 | -40,78; -72,16 | 1,39 km SO | 5, sin despachar |
| Michinmahuida | -42,79; -72,44 | -42,80; -72,45 | 1,38 km SO | 6, sin despachar |
| CorcovadoYanteles | -43,183; -72,80 | -43,19; -72,79 | 1,12 km SE | 6, sin despachar |
| Mentolat | -44,67; -73,08 | -44,70; -73,08 | 3,34 km S | 7, sin despachar |
| MacaCay | -45,10; -73,20 | -45,10501; -73,169326 (Macá) | 2,47 km E | 7, sin despachar |
| SanPedro | -21,88; -68,40 | -21,89; -68,39 | 1,52 km SE | 2, aplicada |

Archivos: `volcanoes.yaml` (lat, lon y tres `gvp_id`), `pipeline/grillas_mirova.yaml` (`x0`, `y0`, `centro_lat`,
`centro_lon` recalculados con la función `entrada` del generador de S172, vía `regenerar_grillas.py`),
`frontend/index.html` (la copia de coordenadas del tablero, que mide la distancia del píxel en cumbre),
`frontend/experimental/index.html` (su copia del laboratorio, que tenía los mismos centros viejos) y
`experiments/_s172_sombra34/vecinos.yaml` (regenerado con su script: cambian tres distancias, 24,5 a 24,9, 20,2 a 21,4
y 17,5 a 16,4 km; ninguna caja ni ningún volcán de la lista). Prueba: `tests/test_centros_rnvv_s190.py`.

## Dudosos para Nicolás (no se tocan)

En los ocho la RNVV está a más de 1 km y el GVP coincide con nuestro centro (0,0 km), así que las dos fuentes no se
ponen de acuerdo. Casi todos difieren en exactamente 0,01° de latitud o longitud, el grano de la ficha.

| Volcán | RNVV a nuestro | Geología |
|---|---|---|
| DescabezadoGrande | 1,11 km S | la ficha es «Grupo Descabezados», no el Descabezado Grande solo |
| Sollipulli | 1,11 km S | caldera de 4 km llena de hielo: el «centro» depende de qué se mire |
| CarranLosVenados | 2,22 km S | campo de conos y maares de unos 160 km²: no tiene un centro único |
| Melimoyu | 1,37 km NE | sin alertas guardadas |
| Tinguiririca | 1,28 km SE | 146 alertas, 1 pasaría a cumbre |
| Taapaca | 1,53 km SO | complejo de domos alargado E-O; 2 pasarían a cumbre |
| Irruputuncu | 1,04 km O | 2 pasarían a lejos |
| Ollague | 1,11 km S | 1 pasaría a lejos |

Si Nicolás prefiere la RNVV en alguno, el cambio es el mismo procedimiento de este PR.

## ¿Hay que reprocesar lo ya aplicado?

- **Tanda 1** (Taapaca, Parinacota, Guallatiri, Irruputuncu, OlcaParuma): ninguno cambia de centro. No.
- **Tanda 2** (Ollague, SanPedro, Putana, SanJose, Tinguiririca): sólo **SanPedro**. De sus 284 alertas, 2 pasarían a
  cumbre y 1 a lejos sólo por la distancia, pero además la grilla y la caja ROI se corren 1,5 km, así que la detección
  misma puede cambiar. Para que la historia de SanPedro sea de la geometría nueva hay que reprocesarla (sólo ese
  volcán). No se reprocesó.
- **Tanda 3** en curso (DescabezadoGrande, CerroAzulQuizapu, LagunaDelMaule, NevadoDeLongavi, Antuco): ninguno cambia.
  No.
- **Tandas 4 a 7**: seis de los siete cambios caen ahí. Si se despachan antes del merge, su historia sale con el centro
  viejo y habría que repetirlas.
- **Sombra diaria** (`data/sombra_34/`): toma el centro nuevo sola desde la primera corrida después del merge; los
  records anteriores de esos siete conservan la distancia medida desde el centro viejo (en conjunto 5 alertas fuera de
  SanPedro; 1 de AntillancaCasablanca pasaría de lejos a cumbre).
