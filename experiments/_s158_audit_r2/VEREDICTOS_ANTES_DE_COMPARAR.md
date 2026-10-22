# Veredictos de la segunda ronda, escritos ANTES de leer la primera

Escrito el 2026-10-21 por quien orquesta la segunda ronda, con los informes de esta ronda (`ra1/`, `ra2/`, `rb/`, `m2/`,
`a113/`, `oraculo/`, `granulos/`) y sin haber abierto `docs/AUDIT_S158.md`, `experiments/_s158_audit/f*/` ni `v*/`, ni
las ramas `s158-tupungatito` y `s158-v750-recall`. (M1 y A113 sí leyeron partes de la primera ronda por alcance; sus
veredictos sobre las 12 afirmaciones no se usan abajo salvo donde se indica.) Este archivo se commitea antes de la
comparación para que la independencia se pueda comprobar con `git log`.

| # | afirmación | veredicto R2 | evidencia R2 |
|---|---|---|---|
| 1 | Fondo V750 de producción = escalar del anillo 5-25 km con recorte a cero; con los píxeles de Etna da otra magnitud | CONFIRMADA | RA1: mediana del anillo, Planck, `np.maximum(..., 0)` en `process_viirs_mod.py:1056`; Etna 2,75 MW contra 9,89 del OSF (0,28). Gránulos: Láscar 10-08 producción 0 MW, oráculo 0,33, MIROVA 0,36; Villarrica 09-19 0,23 / 0,47 / 0,45 |
| 2 | Ese fondo deja en 0 MW cúmulos de cumbre V750 que el tablero oculta | CONFIRMADA | RA1: 595 de 2.359 cúmulos de cumbre (25,2 %), los 595 ocultos por el predicado real del tablero (node); 96 son alertas de MIROVA, 11 protegidas. La división «pre-K / K» de RA1 por fecha de observación NO es de régimen: todo el corpus fechado se procesó después del merge de K (0 de 71.968 records antes del 2026-10-18 09:57, medido aquí; RA2 H3) |
| 3 | Con el fondo por píxel del OSF sobre nuestros píxeles cambia la razón en V375 | CONFIRMADA CON MATIZ | RA2: 0,830 → 0,885 (n 2.139); sube en los de fondo de anillo (Isluga, Copahue, Láscar), baja en los cinco con kernel local; el fondo explica ~12 % de la brecha, el resto es conteo |
| 4 | La razón cae con el cenit y la caída es de conteo | CONFIRMADA (V375 y MODIS contra OSF); V750 SIN DATO contra OSF | RA2: V375 1,02 a nadir → 0,62 sobre 60°; cae NUESTRO conteo de píxeles (2,78 → 1,92), el Npix de MIROVA es plano; contra la tabla NRT cae en los tres sensores |
| 5 | Compuerta `bt > t_bg + 3 K` y segundo pase acoplados en V750 | CON MATIZ | RB: el segundo pase no depende del primero, pero recaptura sin compuerta lo que la compuerta rechazó (sintético); 1.257 records V750 existen sólo por el segundo pase; atribuirlos a la compuerta: SIN DATO |
| 6 | El `.m` corre el segundo pase siempre y sobre toda la escena | CONFIRMADA | Lectura propia (l. 228-235, sin condición; dominio 67 × 67 menos el marco, los tres BOX) y RB; con la mutación «sin segundo pase» cambia la máscara en 25 de 129 escenas sintéticas con alerta |
| 7 | Cero gránulos en una búsqueda se registra como «Cobertura: completa» | CONFIRMADA | RB: reproducido sin red; código 0 con `--estricto-cobertura`; Chaitén 10-13 y 10-18 en el log del A/B. Además (probe propio): hoy CMR devuelve 0 gránulos de todo el día para V750 de Suomi NPP y NOAA-21 el 2026-10-18 y de Suomi NPP el 10-12, aunque producción los procesó el 18-oct |
| 8 | Al A/B de D25 le falta el 2026-10-18 | CONFIRMADA, y falta más | RB: faltan 10-13 y 10-18 completos y parte del 10-12; 152 de 4.762 pasadas VIIRS (3,19 %) |
| 9 | La métrica M da MEJORA con un placebo de ganancia constante | CONFIRMADA para la regla M; CON MATIZ para el evaluador | RB: g = 1,2 da MEJORA en 4 de 4 estratos; la calibración sellada lo frena (INDECIDIBLE), la simétrica de la adenda (sin sello) lo deja pasar |
| 10 | Sobre 50° el VRP V750 del OSF no cumple la fórmula del código en parte de las filas | CONFIRMADA | RA2: 8.239 de 34.250 sobre 50° (24,1 %) no cumplen; 100 % cumple bajo 50°; MODIS y V375 cumplen siempre. La fórmula de las que no cumplen: SIN DATO |
| 11 | Rechazamos todo V750 diurno y se perdieron protegidas de Chillán | CONFIRMADA | RB: tres compuertas solares; el `.m` de día cambia umbrales y sólo rechaza sun-glint < 12°; Chillán V750: 3 de 3 protegidas diurnas sin record (V375: 9 de 9). Que sean señal y no reflejo solar: SOSPECHA |
| 12 | MIROVA cuenta píxeles, no regiones | CONFIRMADA | Lectura propia (`npix = numel(alert)`, l. 61); RA2: el OSF se comporta como conteo; nuestro conteo es MENOR que el de MIROVA (0,67 en V375, 0,50 en MODIS y V750), no mayor como decía el glosario |

## Segundo oráculo

Detección exacta en Etna; fondo de `fillmissing2` = lineal sobre Delaunay, con 67 triangulaciones posibles en esa pasada
y una igual al OSF a 3e-10. Banda de VRP ±1,3 % en Etna; entre los dos oráculos, máscaras idénticas en 600 escenas y VRP
distinto en más de 5 % en 23 de 378. Ver `oraculo/README.md`.

## Prueba con gránulos chilenos (10 de 14 pasadas; 4 SIN DATO porque CMR ya no las sirve)

El oráculo por defecto reproduce 3 de 7 alertas de MIROVA a menos de 10 %. Las dos débiles de cumbre aparecen al mover la
grilla media celda o con vecino más cercano; las dos de Cordón Caulle (7,7 km) sólo si el anillo usa umbrales de cumbre
(ROI propia del volcán); Tupungatito 08-21 (5 km) en ninguna variante. Controles negativos limpios en la configuración
por defecto. Ver `granulos/`.
