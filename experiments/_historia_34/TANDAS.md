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

Copia local: `D:/vrp-trabajo/temporales/historia_34/tanda2/` (fuera del repo). El script de unión
(`D:/vrp-trabajo/temporales/s187_tanda2/unir_tanda2.sh`) se probó re-uniendo la tanda 1: reprodujo byte a byte sus
cinco `.json.gz` de main. La descarga de artifacts se cortó dos veces por la red de la máquina local; se bajaron
uno por uno con reintentos (`bajar_trozos.sh`).

## Tandas 3 a 7

Nicolás autorizó despacharlas en cadena («Sí, despacha 3 a 7», 2026-11-16). Tanda 3 despachada 2026-11-16 16:22 UTC
(run 43906817147).

## Retiro de Putana y OlcaParuma (D1, opción 1a, 2026-11-17)

La lista del sistema son los 43 de la RNVV (decisión de Nicolás, 2026-11-17 ~00:20 UTC); Putana (tanda 2) y OlcaParuma
(tanda 1) no están en ella. S190 los dejó con `active: false` en `volcanoes.yaml`, borró sus `data/historia_34/` y
`data/sombra_34/`, los sacó de la matriz de `sombra-34.yml` y del tablero. Sus `.json.gz` siguen en `union/`, pero
`aplicar_historia_34.py` ya no los escribe (`INACTIVOS`). Respaldo de los cuatro JSON borrados:
`D:/vrp-trabajo/temporales/s189/respaldo_d1_rnvv/` (fuera del repo). Desde aquí las tandas cubren 32 volcanes.
