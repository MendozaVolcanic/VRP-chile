# Verificador con contexto limpio: PR #847 (G3 del A/B diurno por par, desviación D2)

Fecha: 2026-10-17. Rama `loop/diurno-g3-comparar`, commit `a278acd24`, worktree
`C:\Users\nmend\OneDrive\Escritorio\claude\Volcanologia\VRP Chile\.claude\worktrees\agent-a085354d32a0a9d07\`.
No edité el repo. Todo lo mío vive en `C:\Users\nmend\AppData\Local\Temp\claude\verif_847\`.

## Veredicto: MERGEABLE CON ARREGLOS

Lo que afirma el autor se reproduce exacto. El G3 nuevo puede fallar ante casi todo lo que la rama diurna
podría cambiar de verdad en una noche. Queda una holgura que no viene ni del ruido de máquina ni del desempate:
la categoría `borde` se admite en VIIRS y en records con listas cortas, donde el recorte top-100 que la
justifica no corre. La propia autoprueba (caso 23b) fija esa holgura como comportamiento esperado. El arreglo
es barato y no cambia el veredicto de W2 (abajo, §2 y §6).

## 1. Reproducción de W2 (afirmación 1)

Rehíce las uniones de W2a desde los insumos con `unir_intentos.py`, en los dos órdenes y por brazo
(`verif_847\w2a_12\`, `verif_847\w2a_21\`). Las 44 uniones salen **byte a byte iguales** a las del autor en
`C:\Users\nmend\AppData\Local\Temp\claude\g3_s151\w2a_{12,21}\` (`cmp`, 0 diferencias).

`g3_solo.py` sobre mis uniones más W2b (`verif_847\g3_nuevo_{12,21}.txt`):

| orden | nocturnos | igual | tolerancia | orden | borde | hotspot_escena | distinto | G3 nuevo |
|---|---|---|---|---|---|---|---|---|
| (1,2) | 2.154 / 2.154 | 1.108 | 1.017 | 15 | 13 | 1 | 0 | CUMPLE |
| (2,1) | 2.154 / 2.154 | 909 | 1.216 | 17 | 10 | 2 | 0 | CUMPLE |

El G3 viejo (el de `origin/main`, cargado tal cual con `verif_847\viejo\`, `viejo_campos.py`) da FALLA en
los dos órdenes, con los campos que D2 enumera: listas de píxeles, hotspot, ancla final, geometría de visión,
`vrp_mir_mw` y `discarded_n_pixels`; y sólo en el orden (2,1), además `final_hotspot_source`,
`discarded_reason` y `vrp_mw` en una noche (Copahue MODIS_AQUA 2026-06-18 07:30, el rescate). Coincide con D2.

Todos los pares admitidos que no son `igual`/`tolerancia` son MODIS: 27 de 27 `borde`/`orden` en los dos
órdenes, todos con listas llenas (anomaly + discarded = 100 en los dos lados), o sea con el recorte activo.
Los `hotspot_escena` son MODIS: PCC TERRA 2026-06-18 02:15 (100, 100) y Copahue (11, 11). De 1.697 records
nocturnos VIIRS, sólo 3 tienen la lista llena.

## 2. ¿El G3 nuevo puede fallar? (afirmación 2, A116)

`sembrar.py` siembra una diferencia en un record nocturno del brazo diurno de W2 orden (1,2), uno por grupo
(V375 con `f5_core_vrp_mw`, que son los 765 candidatos V375; V750; MODIS) y corre el G3 viejo y el nuevo
(`sembrar_salida.txt`):

| siembra | V375 | V750 | MODIS | viejo |
|---|---|---|---|---|
| píxel de más, con `n_anomalous_pixels` + 1 y `vrp_mir_mw` mayor | FALLA | FALLA | FALLA | FALLA |
| `vrp_mw` × 1,5 / × (1 + 1e-6) | FALLA | FALLA | FALLA | FALLA |
| `primary_cluster.vrp_mw` × 1,5 | FALLA | FALLA | FALLA | FALLA |
| `distance_class` invertida | FALLA | FALLA | FALLA | FALLA |
| `vrp_mir_mw` distinto con píxeles iguales | FALLA | FALLA | FALLA | FALLA |
| `hotspot_lat` + 0,05 sin más | FALLA | FALLA | **CUMPLE** (hotspot_escena) | FALLA |
| record nocturno desaparece / aparece | COBERTURA DESPAREJA | idem | idem | idem |
| **píxel de más sólo en la lista** (n igual) | **CUMPLE** (borde) | **CUMPLE** | **CUMPLE** | FALLA |
| **un píxel desplazado, mismo n** | **CUMPLE** (borde) | **CUMPLE** | **CUMPLE** | FALLA |
| **píxel desplazado + `vrp_mir_mw` × 1,3, mismo n** (V375) | **CUMPLE** (borde) | | | FALLA |

Los records de V375 y V750 sembrados tienen 4 y 1 píxeles (Chaitén NOAA20 2026-06-20 06:48 y NOAA21_750
2026-06-19 04:36). Con esas listas el recorte `np.argsort(-per_pixel_vrp_mw)[:100]` no recorta nada
(`pipeline/process_viirs.py:1520`, `process_viirs_mod.py:1065`, `process_modis.py:1085`), así que un
cambio en el conjunto de píxeles **no puede venir del desempate** que invoca D2: es un cambio de detección.
Hoy pasa como `borde` porque el tablero no lee los píxeles (V375 con f5, V750 y MODIS publican `pc.vrp_mw`),
y `comparar` deja pasar `vrp_mir_mw` como derivado cuando hay cúmulo. La rama diurna es VIIRS, así que esta
es justo la población que el G3 tiene que vigilar. No encontré en W2 ningún caso así (los 27 son MODIS con
lista llena), así que el arreglo no cambia el resultado.

Hotspot de escena, lado no rescatado (Copahue 2026-06-18 07:30, orden (2,1); el control es el no rescatado,
`test1`, `vrp_mw` 4,782 contra `pc.vrp_mw` 1,834): `vrp_mw` × 10, × 1.000 y en 0, y la distancia del
hotspot + 30 km, dan **CUMPLE** las cuatro (el viejo, FALLA). El tablero publica `pc.vrp_mw` cuando hay
cúmulo, así que el operador no ve la diferencia. Es LAX1 a LAX7 de `VERIFICADOR_843.md` §4, que D2 declara
heredado y sin acotar. Está bien declarado; el riesgo para este A/B es bajo porque `ENABLE_DAYTIME_MODIS`
vale `False` en los dos brazos y la categoría sólo se abre en MODIS. Lo mismo vale para el `hotspot_lat`
de MODIS de la tabla.

## 3. Autoprueba y mutaciones (afirmación 3)

Corridas en el worktree del autor, sin tocar nada mientras corrían (A112):

- `probar_evaluar_diurno.py`: **67 de 67**, rc 0 (`verif_847\probar_salida_verif.txt`).
- `tests/test_g3_diurno_comparar_s151.py`: 20 pasan.
- `mutar_evaluador.py`: **13 de 13 atrapadas**, 0 caídas, rc 0 (`verif_847\mutaciones_verif.txt`). Las seis
  `g3_*` salen con rc 1 porque la autoprueba da FALLA, no por una excepción.
- **Una caída no cuenta como atrapada.** Le agregué a una copia (`verif_847\caida\mutar_caida.py`) una sola
  mutación que mete `raise KeyError` en `noches_identicas`: el contador la informa como
  «rc=-1 -> SE CAE (no cuenta)», «0 de 1» y sale con 1 (`verif_847\caida\salida.txt`). Arreglo confirmado.
- Salvedad: la mutación `volatiles` cuenta como atrapada por un `AssertionError` al importar (rc 3). Es la
  guarda de coherencia que se buscaba, pero el `except AssertionError` atrapa cualquier aserción del import;
  conviene comprobar que el mensaje sea el de la guarda.
- El caso 23b de la autoprueba fija como **esperado** el hueco de §2: 2 píxeles en VIIRS 375 con f5, un
  píxel cambiado, G3 CUMPLE. Su docstring lo atribuye al «empate del recorte top-100», que con 2 píxeles no
  corre. Así que la autoprueba y la mutación `g3_borde_falla` vigilan que el hueco **siga abierto**.

## 4. ¿Ablanda algo que no sea ruido o desempate? (afirmación 4)

Sí, en un punto: el de §2. Contra el G3 viejo, sobre el mismo par sembrado, el viejo da FALLA y el nuevo
CUMPLE cuando cambia el conjunto de píxeles de un record VIIRS nocturno con la lista corta. D2 justifica
`borde` con el desempate del recorte top-100; ese mecanismo exige que el recorte corra. Todo lo demás que el
pre-registro exigía y que la rama diurna podría tocar (magnitud, cúmulo, clase, conteo de píxeles, Test 1,
BT máxima, versión, gránulo, cobertura) sigue dando FALLA, y con más precisión que antes (los distintos se
listan por par).

Además, sin bloquear: si node no corre, el par cuenta como `distinto` y el G3 dice «FALLA (defecto del
cableado)». Es conservador, pero el rótulo engaña; mejor «INDECIDIBLE (predicado no corrió)».

## 5. D2 en el pre-registro (afirmación 5)

Fecha (2026-10-17), rama, motivo mecánico (desempate MODIS con su `archivo:línea`, dependencia del orden de
la unión con el caso Copahue), evidencia (W2 con los dos runs, conteos que reproduje, salidas y script),
y lo que hereda sin acotar: bien escrito. El texto original del criterio 2 queda conservado con su marca.
El diff de `evaluar_diurno.py` sólo toca la cabecera, el import de `unir_intentos`, las guardas de
coherencia al importar, `noches_identicas`, `veredicto_g3` y la sección 7 de impresión: **G1 y G2 quedan
intactos**. Sin guiones largos ni medios en las líneas agregadas (0). Dos puntos menores: la evidencia de
§3 de `VERIFICADOR_843.md` y las salidas de `g3_s151\` viven en directorios sin versionar; y D2 dice que
`borde` es el desempate MODIS sin decir que hoy se admite también en VIIRS y con listas cortas.

## 6. Arreglo pedido antes de evaluar W5 y W6

En `noches_identicas`, admitir `borde` sólo cuando el recorte corrió en los dos lados
(`len(anomaly_pixels) + len(discarded_anomaly_pixels) == 100`, o el tope que use el pipeline) y, si se
quiere ser más estricto, sólo en MODIS; si no, el par es `distinto` con el motivo «conjunto de píxeles
distinto sin recorte top-100». Ajustar el caso 23b para que use listas llenas, y agregar un caso con lista
corta que tenga que dar FALLA (más una mutación que lo quite). Anotarlo en D2. Sobre W2 no cambia nada: los
27 `borde`/`orden` reales tienen la lista llena.
