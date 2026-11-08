# Respuestas de S176 a las dos preguntas de Nicolás (2026-11-08 17:30 UTC)

Fuentes: `origin/main` en `a7a6ae360`, CSV de Mirova-v1 bajados a las 17:27 UTC (mismo paso que `audit-weekly.yml`), copia en
`C:\Users\nmend\vrp-temporales\s176\main\`. Salidas literales en esta carpeta. Ningún número fue transcrito sin salida de script.

## 1. Por qué el tablero no muestra datos de los otros volcanes

El tablero en línea (revisado en navegador, 2026-11-08 17:3x UTC) tiene 45 tarjetas: 8 con detección, 3 con «sin detección» (Copahue,
Llaima, Villarrica, que sí se procesan) y **34 con «sin datos (no monitoreado)»**.

- Los volcanes son 45, no 43: 11 Tier A y 34 fuera del NRT (`volcanoes.yaml`).
- El NRT (`nrt.yml`) corre sólo los 11. Los 34 corren en la **sombra** `sombra-34.yml` desde el 2026-11-03, una vez al día, y escriben en
  `data/sombra_34/`.
- `frontend/index.html` (`loadVolcano`, línea 985) no pide datos para un volcán sin `hasMirova`: es a propósito desde S18, y `sombra-34.yml`
  lo declara en su cabecera. El rótulo «no monitoreado» es inexacto: se procesan, pero no se publican.
- Medido en `data/sombra_34/`: 34 volcanes, 1.339 records nocturnos, 5 noches (11-03 a 11-07), 17 con detección, en 12 volcanes.
- Compuerta del plan (`docs/superpowers/plans/2026-11-02-nrt-34-volcanes.md`, S172, por indicación de Nicolás: «lanzar los 34 que faltan
  cuando ya sepamos que estamos funcionando igual que MIROVA»): Compuerta B estimada ~2026-12-29, publicación ~2027-01-05.
- La corrida del 11-07 falló en un volcán, Lanín, por corte de NASA (#960, según la bitácora de S175). La del 11-03 también figura en rojo, causa SIN VERIFICAR. Cron 13:07 UTC; la de hoy aún no corría a las 17:30.

## 2. Paridad de magnitud y demás, por sensor

### Producción, audit local con los datos de hoy (`audit_local_20261108.txt`)

No es el audit oficial, que corre el lunes 2026-11-09. Ventana 2026-09-09 a 2026-11-08. Veredicto local: FUERA_DE_BANDA, 2 flags, Chillán VIIRS 375
0,602 y Tupungatito VIIRS 375 0,466. Razón = nuestro máximo publicado de la noche / máximo de MIROVA.

### Producción contra sombra, misma pasada, 2026-11-03 a 11-07 (`magnitud_prod_vs_sombra_salida.txt`)

EXPLORATORIO, SIN VERIFICADOR, no decide adopción. Cinco noches; Chillán pesa 12 de 32, 12 de 14 y 6 de 6.

Instrumento: `magnitud_prod_vs_sombra.py`. P1, si lo medido estuviera roto: producción sale con 0,50 sobre las mismas pasadas, así que no es una
vara que siempre dé 1. P2, si el instrumento estuviera muerto: los negativos limpios dan distinto de 0 en producción, 7 de 91 y 4 de 132.

Posición: SIN MEDIR en esta respuesta; S175 retiró «mismo foco» (302) y «foco a 1 a 2,5 km» (351).

### Corrección del verificador limpio (SE SOSTIENE EN PARTE)

`C:\Users\nmend\vrp-temporales\s176_verpr\medicion\INFORME.md`: magnitud confirmada (VIIRS 375 0,504 y 0,993, n 31; VIIRS 750 0,482 y 1,000, n 14). Corrige: producción publica 35 de 38 y no 36; con la regla D-9, en negativos publica producción 10 de 95 y la sombra 3 de 95, no 0; «ninguna pierde alertas de 1 MW» vale sólo de noche; MODIS 1,00 es el mismo código en las dos columnas.

## 3. Pregunta de Nicolás: «porque no publicamos simplemente la sombra con todos los volcanes?» (17:40 UTC)

Salida: `detecciones_sombra34_salida.txt`. Verificador limpio en curso: `C:\Users\nmend\vrp-temporales\s176_verpr\medicion\INFORME.md`.

- Las 17 detecciones de los 34 quedan, medidas desde el volcán: 0 a 5 km o menos, 3 a 10 km o menos, y hasta 33,7 km. Son señal real o ruido, pero no están en el cráter.
- Dos pares son el mismo foco visto desde dos volcanes: Guallatiri y Parinacota (0,11 km, 11-07 05:24) e Irruputuncu y Olca-Paruma (0,16 km, 11-05 05:18).
- Los 34 no tienen `inner_radius_km` (decisión D5 del plan), así que sus records salen con `distance_class: null`. Qué son esos focos: SIN VERIFICAR.
- Los 34 no tienen referencia de MIROVA: el 0,99 de los 11 no se puede medir en ellos.
- La sombra corre una vez al día con atraso de horas. Publicarla como NRT requiere encender las vías en el perfil (A45), no sólo leer otra carpeta.
