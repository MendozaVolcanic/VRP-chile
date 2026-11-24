# Cenit del satélite y medición: cifras con la vía «código MIROVA» (2026-11-15)

Repo leído (sólo lectura): `C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\s184-graficos-como-mirova-0704e1`, rama `claude/s184-tanda2-cenit-ultima-pasada`, commit `7bf9ef8d9`. Datos: `data/mirova_equivalent/<Volcan>.json` (nuestro) y `data/mirova/<Volcan>.json` (referencia MIROVA, generada 2026-11-14T17:04Z).

## Ventana y criterios

- **Vía encendida**: los 73.524 records de los 11 volcanes (todos los sensores, día y noche) tienen `via_codigo_mirova: true`; el primero de cada sensor es del 2025-02-15 en los 11. No hay records sin la vía que excluir.
- **Ventana usada**: 2026-03-01 al 2026-11-14 (pasadas nocturnas nuestras de 2026-03-01 01:35 a 2026-11-14 08:35 UTC). Se parte en marzo porque antes la tabla de MIROVA no es comparable (hitos de `scripts/calidad_referencia_mirova.py`). Sensibilidad con la ventana completa de la vía (desde 2025-02-15) al final.
- **Nocturna**: nuestra pasada con `solar_zenith_deg` > 90. Alertas MIROVA con `dia: true` excluidas (108 en el archivo completo).
- **Alerta MIROVA**: VRP > 0, deduplicada por (hora, sensor) prefiriendo `consolidado` sobre `ocr`. Alertas VIIRS 375 de 0,05 MW o menos no cuentan (regla D-9; 173 en el archivo completo).
- **Valor publicado**: réplica de `mirovaEqVrp` de `frontend/index.html` (`primary_cluster.vrp_mw` si `distance_class` es «summit» y `centroid_dist_km` ≤ `inner_radius_km`; sin cúmulo, `vrp_mw`).
- **Acierto (recall)**: alguna pasada nuestra del mismo sensor dentro de ±60 min con valor publicado > 0. «Estricto»: la pasada más cercana, a 10 min o menos, con valor > 0 (descarta aciertos con otro satélite de la misma noche, A109).
- **Cenit del par**: el nuestro (misma pasada). **El JSON de MIROVA no trae geometría** (campos: hora, sensor, VRP, distancia, clasificación, fuente, día). Ninguna alerta quedó sin pasada nuestra en la ventana.
- **Razón nuestra/MIROVA**: sólo aciertos con fuente `consolidado` (el OCR no sirve para magnitud, nota del propio JSON).

## 1 y 2. Recall y razón de magnitud por tramo de cenit (11 volcanes)

| Sensor | Tramo | Aciertos / alertas | Recall | Estricto | Pares razón | Razón mediana (p25 a p75) |
|---|---|---|---|---|---|---|
| MODIS | 0-20 | 50 / 53 | 0,943 | 50 | 50 | 0,968 (0,822 a 1,069) |
| MODIS | 20-40 | 42 / 42 | 1,000 | 42 | 42 | 1,035 (0,891 a 1,135) |
| MODIS | 40-55 | 22 / 23 | 0,957 | 22 | 22 | 1,109 (0,958 a 1,214) |
| MODIS | 55-70 | 15 / 15 | 1,000 | 15 | 14 | 1,049 (0,837 a 1,288) |
| MODIS | todos | 129 / 133 | 0,970 | 129 | 128 | 1,004 (0,882 a 1,142) |
| VIIRS 375 | 0-20 | 445 / 452 | 0,985 | 417 | 302 | 1,000 (0,970 a 1,033) |
| VIIRS 375 | 20-40 | 482 / 486 | 0,992 | 448 | 331 | 1,000 (0,978 a 1,020) |
| VIIRS 375 | 40-55 | 420 / 429 | 0,979 | 399 | 314 | 1,000 (0,977 a 1,014) |
| VIIRS 375 | 55-70 | 262 / 270 | 0,970 | 255 | 210 | 1,000 (0,975 a 1,025) |
| VIIRS 375 | >70 | 0 / 1 | SIN DATO (n=1) | 0 | 0 | SIN DATO |
| VIIRS 375 | todos | 1609 / 1638 | 0,982 | 1519 | 1157 | 1,000 (0,975 a 1,021) |
| VIIRS 750 | 0-20 | 134 / 143 | 0,937 | 131 | 117 | 1,000 (0,953 a 1,028) |
| VIIRS 750 | 20-40 | 130 / 131 | 0,992 | 128 | 112 | 1,001 (0,993 a 1,014) |
| VIIRS 750 | 40-55 | 95 / 99 | 0,960 | 92 | 83 | 0,999 (0,981 a 1,002) |
| VIIRS 750 | 55-70 | 38 / 39 | 0,974 | 38 | 34 | 0,997 (0,983 a 1,000) |
| VIIRS 750 | todos | 397 / 412 | 0,964 | 389 | 346 | 1,000 (0,981 a 1,010) |

Ni el recall ni la razón caen con el cenit en ningún sensor. La caída de S130 (VIIRS 375 de 0,740 a 0,253, `docs/SINTOMAS.md` §1) era una diferencia entre K y MIROVA; con la vía la razón es 1,00 en todos los tramos.

### Por volcán (aciertos/alertas y razón mediana)

| Volcán | Sensor | 0-20 | 20-40 | 40-55 | 55-70 |
|---|---|---|---|---|---|
| Nevados de Chillán | MODIS | 10/10, 0,975 | 11/11, 0,995 | 13/14, 1,114 | 15/15, 1,049 |
| Nevados de Chillán | VIIRS 375 | 24/24, 0,986 | 29/29, 0,989 | 27/27, 0,955 | 38/38, 1,000 |
| Nevados de Chillán | VIIRS 750 | 16/16, 1,028 | 26/26, 1,000 | 24/24, 0,999 | 31/31, 0,999 |
| Láscar | MODIS | 39/41, 0,971 | 31/31, 1,038 | 9/9, 0,967 | sin alertas |
| Láscar | VIIRS 375 | 71/72, 1,000 | 98/98, 1,000 | 113/114, 1,000 | 31/32, 0,999 |
| Láscar | VIIRS 750 | 54/55, 0,999 | 63/63, 1,000 | 51/51, 1,001 | 3/3, 0,988 |

Los otros 9 volcanes están en `res_desde_0301.json` (clave `por_volcan_tramo`); ninguno muestra caída de la razón con el cenit. La dispersión mayor de MODIS en 40-70° (p25 a p75 de 0,84 a 1,29) viene sobre todo de Chillán (1,114 y 1,049 con n de 13 y 15).

## 3. Lo que sí cambia con el cenit: cuánto se ve (nosotros y MIROVA por igual)

Que la razón sea 1 dice que medimos lo mismo que MIROVA, no que la mirada oblicua sea inocua. Fracción de pasadas nocturnas nuestras con valor publicado > 0 y mediana de ese valor (MW), misma ventana:

| Volcán | Sensor | 0-20 | 20-40 | 40-55 | 55-70 |
|---|---|---|---|---|---|
| Láscar | MODIS | 44/94 = 0,47; 1,01 | 34/115 = 0,30; 1,29 | 9/137 = 0,07; 0,76 | 0/125 = 0,00 |
| Láscar | VIIRS 375 | 95/140 = 0,68; 0,81 | 124/186 = 0,67; 0,76 | 136/242 = 0,56; 0,48 | 56/321 = 0,17; 0,14 |
| Láscar | VIIRS 750 | 90/150 = 0,60; 0,89 | 98/192 = 0,51; 1,11 | 83/246 = 0,34; 0,86 | 7/348 = 0,02; 0,25 |
| Nevados de Chillán | MODIS | 11/109 = 0,10; 15,1 | 11/135 = 0,08; 21,9 | 14/154 = 0,09; 18,3 | 17/156 = 0,11; 3,0 |
| Nevados de Chillán | VIIRS 375 | 26/177 = 0,15; 5,2 | 35/244 = 0,14; 9,3 | 30/234 = 0,13; 10,6 | 44/378 = 0,12; 11,2 |
| Nevados de Chillán | VIIRS 750 | 19/178 = 0,11; 17,8 | 27/249 = 0,11; 20,5 | 25/238 = 0,10; 13,6 | 36/419 = 0,09; 13,3 |
| Isluga | VIIRS 375 | 111/153 = 0,72; 0,22 | 113/187 = 0,60; 0,21 | 104/223 = 0,47; 0,23 | 83/320 = 0,26; 0,27 |
| Lastarria | VIIRS 375 | 70/143 = 0,49; 0,10 | 78/198 = 0,39; 0,09 | 65/248 = 0,26; 0,08 | 48/299 = 0,16; 0,08 |
| Planchón-Peteroa | VIIRS 375 | 81/186 = 0,43; 0,18 | 70/197 = 0,35; 0,15 | 40/270 = 0,15; 0,08 | 7/376 = 0,02; 0,07 |

MIROVA en los mismos pares (mediana de su VRP, fuente consolidado, cenit nuestro): Láscar VIIRS 375 0,725 / 0,57 / 0,36 / 0,14 MW (n 44, 64, 83, 25); Láscar MODIS 0,99 / 1,31 / 0,64 (n 41, 31, 9; 0 alertas sobre 55°). Su caída es la misma que la nuestra.

Límites: el denominador incluye pasadas nubladas y el estado de actividad cambia en 8 meses; esta tabla no separa nube, atmósfera ni actividad del efecto geométrico (SIN DATO para esa separación). La mediana «agrupada» de MIROVA para los 11 volcanes sube con el cenit en MODIS (1,28 a 6,73 MW) porque los tramos altos los llena Chillán: no leerla sin estratificar.

## 4. Qué tan seguido la pasada es oblicua (cenit > 40°)

| Sensor | Pasadas nocturnas oblicuas | Fracción | Entre pasadas con valor > 0 |
|---|---|---|---|
| MODIS | 3395 / 6007 | 0,565 | 41 / 143 = 0,287 |
| VIIRS 375 | 7017 / 11359 | 0,618 | 955 / 2189 = 0,436 |
| VIIRS 750 | 7452 / 11909 | 0,626 | 194 / 605 = 0,321 |

Última pasada nocturna de cada noche y volcán (todos los sensores juntos; noche = fecha UTC de la hora menos 12 h): oblicua en 1536 de 2849 noches-volcán (0,539). La última es MODIS en 2756 de 2849, VIIRS 375 en 87 y VIIRS 750 en 6. No verifiqué si el tablero define «última pasada» por sensor o en conjunto.

## Sensibilidad: ventana completa de la vía (2025-02-15 a 2026-11-14)

MODIS 145/149 = 0,973 (estricto 145), razón 1,004 (n 144); VIIRS 375 1773/1807 = 0,981 (estricto 1679), razón 1,000 (n 1284); VIIRS 750 437/453 = 0,965 (estricto 429), razón 1,000 (n 383). Igual que desde marzo.

## SIN DATO

- Cenit de MIROVA propio: su JSON no lo guarda; se usó el nuestro.
- Magnitud «núcleo F5'» que el tablero puede mostrar en VIIRS 375 (`mirovaEqVrpDisplay`): no medida; las razones son con `primary_cluster.vrp_mw`.
- Separación de nube, atmósfera y actividad en la caída de detección con el cenit.

## Lectura geológica

Cuando el satélite mira de lado, el píxel que cae sobre el cráter cubre más terreno y la radiación atraviesa más atmósfera (geometría de barrido conocida; su tamaño no se midió aquí). Una fuente pequeña, como la del cráter de Láscar o las de Isluga, Lastarria y Planchón-Peteroa, queda diluida en un píxel más grande y frío, y su señal se acerca al umbral o lo cruza hacia abajo. Eso es lo que muestran los números: en Láscar la fracción de pasadas con calor publicado baja en VIIRS 375 de 0,68 cerca del nadir a 0,17 sobre 55°, y en MODIS de 0,47 a 0 sobre 55°; el VRP de las detecciones también baja (0,81 a 0,14 MW en VIIRS 375). MIROVA ve exactamente lo mismo en esas pasadas (0,73 a 0,14 MW), y con la vía nuestra razón contra MIROVA es 1,00 en todos los tramos y el recall no cae (0,94 a 1,00). Una fuente intensa, como Chillán (detecciones de 3 a 22 MW de mediana según tramo y sensor), se ve igual de seguido a cualquier cenit (0,09 a 0,15 de las pasadas). Para el turno: una pasada oblicua que no muestra calor, o muestra menos, en un volcán de señal pequeña no es evidencia de que la actividad bajó; conviene mirar la pasada más cercana al nadir. Y esto pasa seguido: más de la mitad de las pasadas nocturnas tiene cenit sobre 40°, y en 54 % de las noches la última pasada del volcán es oblicua (casi siempre MODIS). Los números no separan cuánto de la caída es tamaño de píxel, atmósfera o nubes.

## Reproducir

```bash
S="experiments/_s184_cenit"   # los *_pares.json no se versionan: se regeneran con el comando
R="."   # raíz del repo
python -I "$S/cenit_via.py" "$R" "$S/res_desde_0301.json" 2026-03-01        # recall, razón, fracción oblicua
python -I "$S/cenit_absoluto.py" "$R" "$S/res_desde_0301_pares.json" "$S/abs_desde_0301.json" 2026-03-01
python -I "$S/cenit_via.py" "$R" "$S/res_desde_0215.json" 2025-02-15        # sensibilidad
```

Salidas: `res_desde_0301.json` (tablas 1, 2, 4 y por volcán), `res_desde_0301_pares.json` (2183 pares, uno por alerta), `abs_desde_0301.json` (tabla 3), `res_desde_0215.json` (sensibilidad).
