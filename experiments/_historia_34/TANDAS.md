# Bitácora de las tandas de la historia de los 34

Plan: `docs/superpowers/plans/2026-11-13-historia-34-volcanos-via.md`. Una fila por despacho; los números salen del
informe de `unir_trozos.py` y de la API de Actions (suma de `completed_at - started_at` de los jobs `reproc`).

## Piloto (2026-11-14)

| campo | valor |
|---|---|
| run | 43614240705 (main `ce8b20ca5`, `reproc-historia-via.yml`) |
| volcanes y ventana | Calbuco y Parinacota, 2025-03-01 a 2025-03-31 |
| trozos | 4 de 4 en verde, todos con intento 1 |
| runner | 90 min (14 + 19 + 31 + 26), o sea 1,45 min por volcán y día; Tupungatito dio 1,46 (run 43146587816). La tabla de costo del plan (~520 h para los 34) se mantiene |
| unión | Calbuco 355 records, Parinacota 270; 31 días cada uno, 0 huecos, todas las marcas `true` |
| ensayo del aplicador | 355 y 270 nuevos, 0 tras el corte; sin escribir (modo ensayo) |
| detecciones | Calbuco 1 (0,16 MW a 29 km del centro). Parinacota 14, casi todas a 18 a 32 km de los volcanes; la mayor, 6,03 MW (MODIS Aqua, 03-19 07:40), a 10,7 km de Guallatiri. Mismo patrón de detecciones lejanas que la sombra diaria; el radio de cumbre del tablero (5 km) las deja fuera de la cumbre |
| se aplica | NO: el piloto sólo mide. Su ventana vuelve a correr en la tanda 1 (Parinacota) y la 6 (Calbuco); la carpeta del piloto no se mezcla con la de esas tandas, porque `unir_trozos.py` rehúsa una clave repetida |

Copia local: `D:/vrp-trabajo/temporales/historia_34/piloto/` (fuera del repo).

## Decisiones (Nicolás, 2026-11-14, «Sí, parte la tanda 1» sobre las recomendaciones del §2)

- H1: los 34 de `data/sombra_34/` (lo que ya muestra el tablero).
- H2: tandas de norte a sur, las del §5 Tarea 5.
- H3: una sola aprobación para aplicar las 7 tandas, cada una con su tag defensivo y sólo si su ensayo da 0 huecos y
  0 caídas a K. El merge de cada PR de unión sigue pidiendo «mergea #N».

## Antes de la tanda 1

- `FileExistsError` en `partial_*`: en el run 43467764489 (S182) tumbó 3 de 34 jobs enteros (todas las descargas del job,
  0 `DOWNLOAD_DONE`), y a Mentolat en la sombra el 2026-11-03. Causa SIN VERIFICAR; S182 propuso una sesión aparte para
  diagnosticarlo. Con 165 trozos por tanda, una tasa así dejaría ~15 trozos para relanzar en cada una.

## Tanda 1 (Taapaca, Parinacota, Guallatiri, Irruputuncu, OlcaParuma; 2025-02-15 a 2026-11-02)

- Run 43620748875 (main `f7e7aa5c6`, despachado 2026-11-14 17:22 UTC tras esperar el rerun de S182 en el mismo grupo):
  165 trozos. CANCELADO a las ~19:36 UTC con 27 en verde (sus artifacts quedan) y 138 sin correr, porque S184 halló que
  `FileExistsError` NO es pasajero: falla todo job que cae en AWS us-west-2, y el arreglo #1007 (`dc0a1de3f`) entró a
  main a las 19:34 UTC. Un rerun habría usado el commit viejo.
- Run 43633062404 (main `dc0a1de3f`): los 138 trozos restantes, con ventanas `Volcan@a:b` exactas
  (`D:/vrp-trabajo/temporales/historia_34/tanda1/ventanas_relanzar.txt`); el planificador los reproduce idénticos y
  sin solaparse con los 27 (comprobado antes de despachar). La unión se arma con los dos runs.
- Unión (#1012): 5 volcanes, 626 días cada uno, 0 huecos, todas las marcas `:true`; ensayo del aplicador con 5.389
  (Guallatiri), 5.573 (Irruputuncu), 5.603 (OlcaParuma), 5.384 (Parinacota) y 5.494 (Taapaca) records nuevos, 0 tras
  el corte.
- **Aplicada** el 2026-11-16 tras el merge de #1000 (`8c94743d1`, 04:11 UTC): run 43802322235 de
  `aplicar-reemplazo.yml`, tag `pre-historia-34-tanda1`, commit `bec44eb16` en main (5 archivos en `data/historia_34/`).

## Tanda 2 (Ollague, SanPedro, Putana, SanJose, Tinguiririca; 2025-02-15 a 2026-11-02)

| campo | valor |
|---|---|
| run | 43806164818 (main `9a7f37bcc`), despachado 2026-11-16 04:47 UTC (Nicolás: «Despacha ahora») |
| trozos | 165 de 165 en verde, todos con intento 1; ningún relanzamiento |
| runner | 67,5 h (suma de `completed_at - started_at` de los 165 jobs), 24,6 min por trozo en promedio (máximo 43,5); pared 04:48 a 16:20 UTC, 11 h 32 min |
| unión | 626 días por volcán, 0 huecos, 0 records fuera de ventana, todas las marcas `:true`. Ollague 5.673 records, Putana 5.602, SanJose 6.398, SanPedro 5.708, Tinguiririca 6.485 |
| ensayo del aplicador | 29.866 nuevos (los cinco de arriba), 0 tras el corte; los 5 de la tanda 1 dan 0 nuevos y todos «ya estaban» |
| se aplica | tras el merge del PR de esta unión. Ojo D1 (`tasks/DECISIONES_34_S187.md` en `loop/activo`): Putana es candidata a salir si la lista final es la de la RNVV |
| aplicada | 2026-11-16 tras el merge de #1026: run 43934376861 de `aplicar-reemplazo.yml`, commit `43ac1c5e6` en main. Putana salió después con D1 (sección de abajo) |

Copia local: `D:/vrp-trabajo/temporales/historia_34/tanda2/` (fuera del repo). El script de unión
(`D:/vrp-trabajo/temporales/s187_tanda2/unir_tanda2.sh`) se probó re-uniendo la tanda 1: reprodujo byte a byte sus
cinco `.json.gz` de main. La descarga de artifacts se cortó dos veces por la red de la máquina local; se bajaron
uno por uno con reintentos (`bajar_trozos.sh`).

## Tandas 3 a 7

Nicolás autorizó despacharlas en cadena («Sí, despacha 3 a 7», 2026-11-16). Tanda 3 despachada 2026-11-16 16:22 UTC
(run 43906817147).

⚠️ S190 (2026-11-17): el run 43906817147 NO era la tanda 3. Procesó otra vez los cinco de la tanda 2: lo despachó
`despachar.sh`, programado antes de que Nicolás pidiera «Despacha ahora» para la tanda 2, y nadie lo canceló. Unido y
ensayado contra main dio 0 records nuevos en los cinco (la vía es reproducible corrida a corrida). La tanda 3 real es el
run 44037264576 (sección siguiente). Carpeta del duplicado: `D:/vrp-trabajo/temporales/historia_34/tanda2_duplicado_run43906817147`.

## Tanda 3 (DescabezadoGrande, CerroAzulQuizapu, LagunaDelMaule, NevadoDeLongavi, Antuco; 2025-02-15 a 2026-11-02)

| campo | valor |
|---|---|
| run | 44037264576 (main `3239a4db8`), despachado 2026-11-17 07:15 UTC por `cadena_3a7_s190b.sh` |
| trozos | 165 de 165 en verde. 6 cayeron en el intento 1 por fallas de búsqueda en CMR de NASA (DescabezadoGrande 5, NevadoDeLongavi 1) y pasaron con `gh run rerun --failed` (intento 2, mismo commit) |
| runner | 76,2 h (suma de `completed_at - started_at` de los 165 jobs vigentes), 27,7 min por trozo en promedio (máximo 53,6); pared 07:16 a 21:14 UTC, con la ronda de relanzamiento |
| unión | 626 días por volcán, 0 huecos, 0 records fuera de ventana, todas las marcas `:true`. Antuco 6.718 records, CerroAzulQuizapu 6.497, DescabezadoGrande 6.499, LagunaDelMaule 6.643, NevadoDeLongavi 6.538 |
| ensayo del aplicador | 32.895 nuevos (los cinco de arriba), 0 tras el corte; los 8 activos de las tandas 1 y 2 dan 0 nuevos y todos «ya estaban»; Putana y OlcaParuma, saltados (`active: false`) |
| se aplica | tras el merge del PR de esta unión, con tag `pre-historia-34-tanda3` |
| aplicada | 2026-11-18 tras el merge de #1044: run 44206439159 de `aplicar-reemplazo.yml` (tag `pre-historia-34-tanda3` sobre `251f80487`), commit `73a33807f` en main |

Copia local: `D:/vrp-trabajo/temporales/historia_34/tanda3/` (fuera del repo). Tanda 4 (Callaqui, Lonquimay, Tolhuaca,
Sollipulli, Quetrupillan) despachada por la cadena el 2026-11-17 23:25 UTC.

## Tanda 4 (Callaqui, Lonquimay, Tolhuaca, Sollipulli, Quetrupillan; 2025-02-15 a 2026-11-02)

| campo | valor |
|---|---|
| run | 44199313624 (main `aa0d81b80`), despachado 2026-11-17 23:26 UTC por `cadena_3a7_s190b.sh` |
| trozos | 165 de 165 en verde. 11 se tomaron de un intento posterior tras fallas pasajeras (relanzados con `gh run rerun --failed`, mismo commit, por `cadena_4a7_s190c.sh`): Callaqui 22 a 27 y Sollipulli 8 del intento 2; Lonquimay 4 y Quetrupillan 16, 17 y 20 del intento 3 |
| runner | 86,4 h (suma de `completed_at - started_at` de los 165 jobs vigentes), 31,4 min por trozo en promedio (máximo 67,2); pared 2026-11-17 23:27 a 2026-11-18 19:45 UTC |
| unión | 626 días por volcán, 0 huecos, 0 records fuera de ventana, todas las marcas `:true`. Callaqui 6.816 records, Lonquimay 6.879, Quetrupillan 6.951, Sollipulli 6.858, Tolhuaca 6.883 |
| ensayo del aplicador | 34.387 nuevos (los cinco de arriba), 0 tras el corte; los 13 activos de las tandas 1 a 3 dan 0 nuevos y todos «ya estaban» |
| se aplica | tras el merge del PR de esta unión, con tag `pre-historia-34-tanda4` |
| aplicada | 2026-11-19 tras el merge de #1054: run 44528546156 de `aplicar-reemplazo.yml` (tag `pre-historia-34-tanda4` sobre `e72ba3c3a`), commit `4e6e873fa` en main |

Copia local: `D:/vrp-trabajo/temporales/historia_34/tanda4/` (fuera del repo). Tanda 5 (Lanin, MochoChoshuenco,
CarranLosVenados, AntillancaCasablanca, Osorno) despachada por la cadena el 2026-11-19 11:10 UTC (run 44512397201).

## Tanda 5 (Lanin, MochoChoshuenco, CarranLosVenados, AntillancaCasablanca, Osorno; 2025-02-15 a 2026-11-02)

Números de `D:\vrp-trabajo\temporales\s191\tanda5_numeros.py` (salida en `tanda5_numeros.txt`, al lado).

| campo | valor |
|---|---|
| run | 44512397201 (main `fa3ac287f`), despachado 2026-11-19 11:10 UTC por `cadena_4a7_s190c.sh` |
| trozos | 165 de 165 en verde. 27 se tomaron del intento 2 tras fallas pasajeras (contados por el nombre del artifact). Causas, de `D:\vrp-trabajo\temporales\s190\t5_fallas.txt` (26 fallas a las 15:20 UTC): 19 en «Install deps» por la caída del espejo de Ubuntu del 2026-11-19 12:08 UTC, y 7 de MochoChoshuenco en el reproceso, que el modo estricto corta con salida 3 ante una descarga fallida de LAADS (ejemplo, job 135520546869: VNP03MOD del 2026-05-06). La 27.ª (Osorno 32) cayó después y su causa no se revisó. Relanzados con `gh run rerun --failed`, mismo commit, por `cadena_5a7_s190d.sh`: Lanin 13, 16 a 22, 24, 25, 27 a 30 y 33; MochoChoshuenco 1 a 4, 23, 24 y 26 a 30; Osorno 32 |
| runner | 76,7 h (suma de `completed_at - started_at` de los 165 jobs `reproc` vigentes), 27,9 min por trozo en promedio (máximo 40,1); pared 2026-11-19 11:12 a 2026-11-20 01:21 UTC, con un reinicio del PC a las 23:17 UTC que no afectó al run |
| unión | 626 días por volcán, 0 huecos, 0 records fuera de ventana, todas las marcas `:true`. AntillancaCasablanca 7.144 records, CarranLosVenados 7.078, Lanin 6.890, MochoChoshuenco 7.025, Osorno 7.148 |
| ensayo del aplicador | 35.285 nuevos (los cinco de arriba), 0 tras el corte; los 18 activos de las tandas 1 a 4 dan 0 nuevos y todos «ya estaban» |
| se aplica | tras el merge del PR de esta unión, con tag `pre-historia-34-tanda5` |
| aplicada | 2026-11-20 tras el merge de #1062 (02:00 UTC): run 44658784431 de `aplicar-reemplazo.yml` (tag `pre-historia-34-tanda5` sobre `0e6126871`), commit `da372acd1` en main, por la sesión «s192» (local_841efdd9) |

Copia local: `D:/vrp-trabajo/temporales/historia_34/tanda5/` (fuera del repo). Tanda 6 (Calbuco, YateHornopiren,
Huequi, Michinmahuida, CorcovadoYanteles) despachada por la cadena el 2026-11-20 01:27 UTC (run 44653724540).

## Tanda 6 (Calbuco, YateHornopiren, Huequi, Michinmahuida, CorcovadoYanteles; 2025-02-15 a 2026-11-02)

Números de `D:\vrp-trabajo\temporales\s192\tanda6\tanda6_numeros.py` (salida en `numeros.log`, al lado).

| campo | valor |
|---|---|
| run | 44653724540 (main), despachado 2026-11-20 01:27 UTC por `cadena_5a7_s191.sh` |
| trozos | 165 de 165 con artifact. 2 se tomaron del intento 2 (CorcovadoYanteles 1 y 2), relanzados por la cadena a las 14:54 UTC. Al relanzar, con la API de GitHub dando 502, GitHub creó 12 trabajos para esos dos trozos: 2 corrieron en verde y subieron su artifact y 10 quedaron «queued» para siempre con el run ya «completed success». La cadena leyó uno de esos fantasmas como rojo, no pudo relanzar («cannot be retried») y se detuvo a las 15:50 UTC sin despachar la tanda 7; por eso la lista de jobs vigentes da 165 success y 1 sin conclusión, y el runner suma 164 jobs. Lo despachó aparte S192 con `D:\vrp-trabajo\temporales\s192\tanda7\cadena_7_s192.sh`, que cuenta rojos por trozo (alguna copia en success) |
| runner | 78,5 h (suma de `completed_at - started_at` de los 164 jobs `reproc` vigentes con fin), 28,7 min por trozo en promedio (máximo 39,0); pared 2026-11-20 01:28 a 15:28 UTC |
| unión | 626 días por volcán, 0 huecos, 0 records fuera de ventana, todas las marcas `:true`. Calbuco 7.163 records, CorcovadoYanteles 7.393, Huequi 7.351, Michinmahuida 7.360, YateHornopiren 7.336 |
| ensayo del aplicador | 36.603 nuevos (los cinco de arriba), 0 tras el corte; los 23 activos de las tandas 1 a 5 dan 0 nuevos y todos «ya estaban» |
| se aplica | tras el merge del PR de esta unión, con tag `pre-historia-34-tanda6` |
| fondo nulo | esta tanda se procesó con el código anterior a #1065 (fondo nulo, opción a): sus pasadas MODIS sin fondo entran publicadas y se cuentan junto con las demás antes del reemplazo que sigue a ese merge |

Copia local: `D:/vrp-trabajo/temporales/historia_34/tanda6/` (fuera del repo). Tanda 7 (Melimoyu, MacaCay, Mentolat,
Hudson) despachada por S192 el 2026-11-20 15:55 UTC (run 44768057665).

## Retiro de Putana y OlcaParuma (D1, opción 1a, 2026-11-17)

La lista del sistema son los 43 de la RNVV (decisión de Nicolás, 2026-11-17 ~00:20 UTC); Putana (tanda 2) y OlcaParuma
(tanda 1) no están en ella. S190 los dejó con `active: false` en `volcanoes.yaml`, borró sus `data/historia_34/` y
`data/sombra_34/`, los sacó de la matriz de `sombra-34.yml` y del tablero. Sus `.json.gz` siguen en `union/`, pero
`aplicar_historia_34.py` ya no los escribe (`INACTIVOS`). Respaldo de los cuatro JSON borrados:
`D:/vrp-trabajo/temporales/s189/respaldo_d1_rnvv/` (fuera del repo). Desde aquí las tandas cubren 32 volcanes.
